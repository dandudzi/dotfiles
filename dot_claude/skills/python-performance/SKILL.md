---
name: python-performance
description: Profiling tools, bottleneck detection, data structure selection, vectorization, concurrency strategies, caching, C extension optimization, and memory optimization for high-performance Python systems.
origin: ECC
---

# Python Performance Optimization

## When to Activate

- Profiling CPU-bound and memory-bound code
- Detecting and eliminating N+1 database queries
- Optimizing data structure choices (list vs deque vs set vs dict)
- Vectorizing NumPy/pandas operations
- Implementing caching strategies
- Choosing concurrency model (asyncio, threads, processes)
- Optimizing memory footprint with `__slots__` and generators
- Integrating C extensions for hot paths

## Profiling Tools

### CPU Profiling: cProfile

For wall-clock time and function call counts:

```python
import cProfile
import pstats
from io import StringIO

def expensive_function():
    """Simulate CPU-intensive work."""
    total = 0
    for i in range(1_000_000):
        total += i ** 2
    return total

# Method 1: Programmatic profiling
pr = cProfile.Profile()
pr.enable()
expensive_function()
pr.disable()

# Sort by cumulative time, show top 10 functions
s = StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(10)
print(s.getvalue())

# Method 2: Command line
# python -m cProfile -s cumtime script.py
```

### Memory Profiling: memory_profiler

Track memory allocation line-by-line:

```python
from memory_profiler import profile

@profile
def memory_intensive():
    """Track memory per line."""
    x = [i for i in range(1_000_000)]  # Allocate ~40MB
    y = [i * 2 for i in x]             # Allocate another ~40MB
    return sum(y)

# Run: python -m memory_profiler script.py
```

### Line-Level Profiling: line_profiler

Measure execution time per line in hot functions:

```python
from line_profiler import LineProfiler

def slow_operation():
    """Process list slowly."""
    result = []
    for i in range(100_000):
        result.append(i * 2)  # Slow: list append in loop
    return result

lp = LineProfiler()
lp.add_function(slow_operation)
lp.enable()
slow_operation()
lp.disable()
lp.print_stats()
```

### Sampling Profiler: py-spy

Non-invasive sampling (no code changes needed):

```bash
# Profile running process
py-spy record -o profile.svg --pid=<PID>

# Profile script
py-spy record -o profile.svg python script.py

# Shows call stacks sampled at regular intervals
```

### Comprehensive: scalene

CPU + memory + GPU profiling in one tool:

```bash
pip install scalene
scalene script.py

# Outputs CPU time, memory allocations, GPU usage per line
```

## Common Bottlenecks & Solutions

### Bottleneck 1: N+1 Database Queries

**WRONG: Query in loop**
```python
# Queries DB 1 + N times (bad!)
users = db.query(User).all()
for user in users:
    print(user.posts)  # DB query per user
```

**CORRECT: Eager loading**
```python
# Single query with join
users = db.query(User).options(
    joinedload(User.posts)
).all()
for user in users:
    print(user.posts)  # Already loaded
```

### Bottleneck 2: List Comprehension Copy

**WRONG: Copy entire list**
```python
# Creates full list in memory
data = [expensive_process(x) for x in huge_list]
for item in data:
    use(item)  # Memory spike for entire list
```

**CORRECT: Generator (lazy evaluation)**
```python
# Processes one item at a time
data = (expensive_process(x) for x in huge_list)
for item in data:
    use(item)  # Minimal memory footprint
```

### Bottleneck 3: O(n²) Algorithms

**WRONG: Nested loop with list lookup**
```python
# O(n²) - 1 million items = 1 trillion operations
existing_ids = [1, 2, 3, 4, 5]
for new_id in new_ids:
    if new_id in existing_ids:  # O(n) per check
        process(new_id)
```

**CORRECT: Set lookup**
```python
# O(n) - 1 million items = 1 million operations
existing_ids = {1, 2, 3, 4, 5}
for new_id in new_ids:
    if new_id in existing_ids:  # O(1) per check
        process(new_id)
```

### Bottleneck 4: Blocking I/O in Async Code

**WRONG: Blocking call in async function**
```python
import asyncio
import requests

async def fetch_all(urls):
    results = []
    for url in urls:
        # Blocks entire event loop!
        response = requests.get(url)
        results.append(response.json())
    return results
```

**CORRECT: Async I/O**
```python
import asyncio
import httpx

async def fetch_all(urls):
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        # Concurrent requests
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

## Data Structure Selection

| Use Case | Structure | Why | Example |
|----------|-----------|-----|---------|
| Frequent lookups by key | `dict` | O(1) average | `user_by_id = {1: "Alice", 2: "Bob"}` |
| Membership checking | `set` | O(1) average | `if item in valid_items` |
| Ordered queue (FIFO) | `deque` | O(1) popleft | `from collections import deque` |
| Stack (LIFO) | `list` | O(1) pop | `stack.pop()` |
| Numeric arrays | `array` | Compact, faster | `from array import array` |
| Large numeric data | `numpy.ndarray` | Vectorized ops | `np.array([1, 2, 3])` |
| Tabular data | `pandas.DataFrame` | Powerful ops | `df.groupby().sum()` |

**Example: dict vs list performance**
```python
import time

# dict lookup: O(1)
user_by_id = {i: f"user_{i}" for i in range(1_000_000)}
start = time.time()
for i in range(100_000):
    user = user_by_id[i]
print(f"dict lookup: {time.time() - start:.4f}s")  # ~0.01s

# list lookup: O(n)
users = [f"user_{i}" for i in range(1_000_000)]
start = time.time()
for i in range(100_000):
    user = users[i]
print(f"list index: {time.time() - start:.4f}s")   # ~0.001s (fast for index)

# membership in list: O(n)
start = time.time()
for i in range(1_000):
    if i in users:  # Linear search
        pass
print(f"list 'in': {time.time() - start:.4f}s")    # ~2s

# membership in set: O(1)
user_set = set(users)
start = time.time()
for i in range(1_000):
    if str(i) in user_set:  # Hash lookup
        pass
print(f"set 'in': {time.time() - start:.4f}s")     # ~0.0001s
```

## NumPy & Pandas Optimization

### Vectorization (Eliminate Loops)

**WRONG: Python loop**
```python
import numpy as np

# Slow: loops in Python interpreter
data = np.array([1, 2, 3, 4, 5])
result = []
for x in data:
    result.append(x * 2 + 1)
```

**CORRECT: Vectorized**
```python
# Fast: executed in C
result = data * 2 + 1
```

### DataFrame Operations

**WRONG: apply() with Python function**
```python
import pandas as pd

df = pd.DataFrame({"x": range(1_000_000)})

# Slow: Python function called 1M times
result = df["x"].apply(lambda x: x * 2 + 1)
```

**CORRECT: Vectorized operation**
```python
# Fast: vectorized in C
result = df["x"] * 2 + 1
```

### Chunked Processing

**WRONG: Load entire file into memory**
```python
# Fails for large files (>available RAM)
df = pd.read_csv("huge_file.csv")  # 50GB
process_data(df)
```

**CORRECT: Process in chunks**
```python
# Process 100K rows at a time
for chunk in pd.read_csv("huge_file.csv", chunksize=100_000):
    process_data(chunk)  # Memory-efficient
```

### Data Type Selection

**WRONG: Default dtypes (wasteful)**
```python
# int64 = 8 bytes per value
df = pd.read_csv("data.csv")  # Loads integers as int64
memory = df.memory_usage(deep=True).sum() / 1e9  # ~10GB for 1B integers
```

**CORRECT: Specific dtypes**
```python
# int8 = 1 byte per value (if range fits)
dtypes = {
    "id": "int32",        # Fits 0-2B values
    "category": "int8",   # Fits 0-255 categories
    "score": "float32",   # Sufficient precision
}
df = pd.read_csv("data.csv", dtype=dtypes)
memory = df.memory_usage(deep=True).sum() / 1e9  # ~1GB
```

## Concurrency for Performance

### I/O-Bound: asyncio

Best for network, file, database I/O:

```python
import asyncio
import httpx

async def fetch_all(urls):
    """Fetch multiple URLs concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

# 10 URLs: async ~1s (parallel), sync ~10s (sequential)
```

### CPU-Bound: ProcessPoolExecutor

Best for compute-heavy tasks:

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def cpu_intensive(n):
    """Heavy computation."""
    return sum(i * i for i in range(n))

with ProcessPoolExecutor(max_workers=4) as executor:
    # Runs on separate processes (bypasses GIL)
    results = list(executor.map(cpu_intensive, [1_000_000] * 10))
```

### Mixed: ThreadPoolExecutor

For mixed I/O and light compute:

```python
from concurrent.futures import ThreadPoolExecutor

def mixed_workload(task_id):
    """I/O + light compute."""
    import requests
    response = requests.get(f"http://api.example.com/{task_id}")
    return response.json()["value"] * 2  # Light processing

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(mixed_workload, range(100)))
```

## Caching Strategies

### Function-Level: functools.lru_cache

For pure functions with repeated calls:

```python
from functools import lru_cache, cache
import time

@lru_cache(maxsize=128)
def fibonacci(n):
    """Cache results of recursive calls."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Without cache: fib(35) takes 29M calls
# With cache: fib(35) takes 36 calls
start = time.time()
result = fibonacci(35)
print(f"Time: {time.time() - start:.4f}s")
print(f"Cache info: {fibonacci.cache_info()}")
```

### Expensive Computations: joblib.Memory

Persist cached results to disk:

```python
from joblib import Memory

# Cache to disk
memory = Memory(location="/tmp/cache", verbose=1)

@memory.cache
def expensive_computation(x):
    """Results cached to disk."""
    import time
    time.sleep(5)  # Simulate expensive operation
    return x * 2

# First call: 5 seconds, saves result
result1 = expensive_computation(42)

# Second call: instant, loads from cache
result2 = expensive_computation(42)
```

### Distributed: Redis Cache

Share cache across processes/servers:

```python
import redis
import json
from functools import wraps

redis_client = redis.Redis(host="localhost", decode_responses=True)

def cached_redis(ttl=300):
    """Cache function results in Redis."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__name__}:{args}:{kwargs}"

            # Try cache
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)

            # Compute and cache
            result = func(*args, **kwargs)
            redis_client.setex(key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cached_redis(ttl=3600)
def fetch_user(user_id):
    """Cached for 1 hour."""
    return {"id": user_id, "name": f"User {user_id}"}
```

## C Extension Optimization

### Cython: Write Python, Compile to C

For hot loops:

```python
# fast_math.pyx
def sum_squares(long[:] data):
    """Compile to C for speed."""
    cdef long total = 0
    cdef long x
    for x in data:
        total += x * x
    return total
```

Compile and use:
```python
import pyximport
pyximport.install()
from fast_math import sum_squares

import numpy as np
data = np.arange(1_000_000, dtype=np.int64)
result = sum_squares(data)  # ~100x faster than Python loop
```

### ctypes: Use Existing C Libraries

```python
from ctypes import CDLL, c_double
import math

# Load system math library
libm = CDLL("libm.so.6")
libm.sin.argtypes = [c_double]
libm.sin.restype = c_double

# Call C function
angle = 3.14159 / 2
result = libm.sin(angle)  # Uses optimized C implementation
```

## Memory Optimization

### __slots__: Reduce Object Size

**WRONG: __dict__ overhead**
```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
# Each instance carries __dict__ (48 bytes overhead)
print(sys.getsizeof(p.__dict__))  # 288 bytes
```

**CORRECT: __slots__**
```python
class Point:
    __slots__ = ["x", "y"]

    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
# No __dict__, only storage for x, y
# 10M instances: 10GB (dict) → 240MB (__slots__)
```

### Generators Over Lists

**WRONG: Entire list in memory**
```python
def get_numbers(n):
    """Returns all numbers at once."""
    return [i for i in range(n)]

# 1 billion integers: 8GB RAM
numbers = get_numbers(1_000_000_000)
```

**CORRECT: Generator (lazy)**
```python
def get_numbers(n):
    """Yields one number at a time."""
    for i in range(n):
        yield i

# ~0 MB (generated on demand)
for num in get_numbers(1_000_000_000):
    process(num)
```

### Weakref for Caches

Prevent memory leaks in caches:

```python
import weakref

class CacheWithWeakref:
    def __init__(self):
        # Weak references don't prevent garbage collection
        self._cache = weakref.WeakValueDictionary()

    def add(self, key, obj):
        self._cache[key] = obj

    def get(self, key):
        return self._cache.get(key)

cache = CacheWithWeakref()
obj = {"id": 1}
cache.add("obj_1", obj)
result = cache.get("obj_1")  # Works

del obj  # Object deleted; cache reference removed automatically
result = cache.get("obj_1")  # None (obj was garbage collected)
```

## Anti-Patterns

### Premature Optimization

**WRONG: Optimize before profiling**
```python
# Complex code for "speed" without measurement
class OptimizedList:
    def __init__(self):
        self._data = []
        self._cache = None

    def append(self, item):
        self._data.append(item)
        self._cache = None  # Complex invalidation logic

# Takes 2x longer than built-in list!
```

**CORRECT: Profile first**
```python
import cProfile
import pstats

# 1. Measure
pr = cProfile.Profile()
pr.enable()
my_function()
pr.disable()

# 2. Find bottleneck
ps = pstats.Stats(pr).sort_stats('cumulative')
ps.print_stats(5)

# 3. Optimize only the hot path
```

### Profiling in Wrong Environment

**WRONG: Profile on development machine**
```python
# My laptop: 16GB RAM, 12 cores
# Production: 2GB RAM, 2 cores
# Results don't match!
```

**CORRECT: Profile in production-like environment**
```bash
# Use similar CPU, memory, disk as production
docker run -m 2g -c 2 python script.py
```

### Optimizing Cold Paths

**WRONG: Optimize rarely-called code**
```python
# get_user() called 1M times: 90% of time
# init_database() called 1 time: 10% of time
@optimized  # Micro-optimize init
def init_database():
    pass

@not_optimized  # Should optimize this!
def get_user(user_id):
    pass
```

**CORRECT: Optimize hot paths**
```python
# Focus optimization on get_user()
# 99% speedup possible vs 1% from init
```

### Copying Large Objects Unnecessarily

**WRONG: Unnecessary deep copy**
```python
import copy

def process_data(data):
    # Expensive copy for no reason
    working_copy = copy.deepcopy(data)
    return working_copy["value"]

# 100MB object copied: 100MB+ allocation
result = process_data(huge_dict)
```

**CORRECT: Reference or shallow copy**
```python
def process_data(data):
    # Use reference directly
    return data["value"]

# No allocation
result = process_data(huge_dict)
```

## Best Practices Checklist

- [ ] Profile before optimizing (use cProfile, memory_profiler, py-spy)
- [ ] Identify bottleneck: I/O, CPU, or memory?
- [ ] Choose right tool: asyncio (I/O), ProcessPoolExecutor (CPU), generators (memory)
- [ ] Select appropriate data structures: dict for lookup, set for membership, deque for queue
- [ ] Vectorize with NumPy/pandas; avoid Python loops
- [ ] Cache expensive computations (functools.lru_cache, joblib.Memory)
- [ ] Use __slots__ for large numbers of instances
- [ ] Prefer generators to lists for streaming data
- [ ] Profile in production-like environment
- [ ] Measure impact: is 5% faster worth 50% more complexity?

## Agent Support

- **python-expert** — Type hints for performance code, decorator patterns
- **numpy-expert** — Vectorization and advanced NumPy optimization
- **nodejs-expert** — Comparison with Node.js async/profiling
- **rust-expert** — Cython and C extension integration

## Skill References

- **python-concurrency** — Threading, asyncio, multiprocessing patterns
- **python-design-patterns** — Decorator, caching strategies
- **python-resilience** — Timeouts and failure handling in performance code
