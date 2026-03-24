---
name: python-performance
description: Profiling tools, bottleneck detection, data structure selection, vectorization, concurrency strategies, caching, C extension optimization, and memory optimization for high-performance Python systems.
origin: ECC
model: sonnet
---

# Python Performance Optimization

## When to Activate

Profile before optimizing; choose concurrency model (asyncio, threads, processes); eliminate N+1 queries; select data structures strategically; vectorize NumPy/pandas; cache expensive computations; reduce memory with `__slots__` and generators.

## Profiling Tools

### CPU Profiling: cProfile

Wall-clock time and function call counts:

```python
import cProfile, pstats

pr = cProfile.Profile()
pr.enable()
expensive_function()
pr.disable()
pstats.Stats(pr).sort_stats('cumulative').print_stats(10)

# Or: python -m cProfile -s cumtime script.py
```

### Memory Profiling: memory_profiler

Line-by-line allocation tracking:

```python
from memory_profiler import profile

@profile
def memory_intensive():
    x = [i for i in range(1_000_000)]
    return sum(x)

# python -m memory_profiler script.py
```

### Line-Level Profiling: line_profiler

Per-line execution time:

```python
from line_profiler import LineProfiler
lp = LineProfiler()
lp.add_function(slow_operation)
lp.enable()
slow_operation()
lp.disable()
lp.print_stats()
```

### Sampling Profiler: py-spy

Non-invasive, no code changes:

```bash
py-spy record -o profile.svg python script.py
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

### Blocking I/O in Async Code
```python
# WRONG: Blocking call in event loop
async def fetch_all(urls):
    for url in urls:
        response = requests.get(url)  # Blocks event loop!

# CORRECT: Concurrent async I/O
async def fetch_all(urls):
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(*[client.get(url) for url in urls])
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
```python
# WRONG: Python loop
result = []
for x in data:
    result.append(x * 2 + 1)

# CORRECT: Vectorized (executed in C)
result = data * 2 + 1

# Also avoid apply() with lambda — use vectorized operations
df["result"] = df["x"] * 2 + 1  # Fast, not df["x"].apply(lambda x: x*2+1)
```

### Chunked Processing
```python
# Stream large files in chunks, not entire into memory
for chunk in pd.read_csv("huge_file.csv", chunksize=100_000):
    process_data(chunk)
```

### Data Type Selection
```python
# Use narrow dtypes: int8 (1 byte) instead of int64 (8 bytes)
df = pd.read_csv("data.csv", dtype={
    "id": "int32",       # Fits 0-2B values
    "category": "int8",  # Fits 0-255 categories
    "score": "float32",  # Sufficient precision
})
```

## Concurrency Strategies

| Type | Tool | Use Case |
|------|------|----------|
| I/O-bound | `asyncio` | Network, file, DB requests |
| CPU-bound | `ProcessPoolExecutor` | Compute-heavy tasks (bypasses GIL) |
| Mixed | `ThreadPoolExecutor` | I/O + light compute |

Quick example:
```python
# asyncio: 10 URLs in ~1s (parallel) vs ~10s (sequential)
async def fetch_all(urls):
    async with httpx.AsyncClient() as client:
        return await asyncio.gather(*[client.get(url) for url in urls])

# ProcessPoolExecutor: bypass GIL for CPU tasks
from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor() as ex:
    results = ex.map(cpu_intensive, [1_000_000] * 10)
```

## Caching Strategies

| Scope | Tool | Use Case |
|-------|------|----------|
| In-process | `functools.lru_cache` | Pure functions, repeated calls |
| Disk | `joblib.Memory` | Expensive computations, persist across runs |
| Distributed | `redis` | Multi-process/server cache |

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n):
    return n if n < 2 else fibonacci(n-1) + fibonacci(n-2)
# fib(35): 29M calls without cache → 36 calls with cache

# Distributed Redis caching
import redis, json
from functools import wraps

redis_client = redis.Redis(host="localhost", decode_responses=True)

def cached_redis(ttl=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args):
            key = f"{func.__name__}:{args}"
            if cached := redis_client.get(key):
                return json.loads(cached)
            result = func(*args)
            redis_client.setex(key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

## C Extension Optimization

**Cython** for hot loops (100x faster than Python):
```python
# fast_math.pyx: compile to C
def sum_squares(long[:] data):
    cdef long total = 0, x
    for x in data:
        total += x * x
    return total

# Use it
import pyximport; pyximport.install()
from fast_math import sum_squares
result = sum_squares(np.arange(1_000_000, dtype=np.int64))
```

**ctypes** to call existing C libraries directly.

## Memory Optimization

### __slots__: Reduce Instance Size
```python
# With __slots__: 10M instances = 240MB (vs 10GB with __dict__)
class Point:
    __slots__ = ["x", "y"]
    def __init__(self, x, y):
        self.x, self.y = x, y
```

### Generators: Stream Instead of Load
```python
# Generator: ~0MB (lazy), List: 8GB for 1B integers
def get_numbers(n):
    for i in range(n):
        yield i
for num in get_numbers(1_000_000_000):
    process(num)
```

### Weakref for Caches
```python
import weakref
cache = weakref.WeakValueDictionary()
cache["key"] = obj  # Doesn't prevent GC; entry removed when obj deleted
```

## Anti-Patterns

**Premature optimization**: Profile first (cProfile → identify bottleneck → optimize hot path only)

**Wrong profiling environment**: Profile in production-like environment, not laptop (different RAM/cores/disk)

**Optimizing cold paths**: 1M calls to `get_user()` (90% time) beats optimizing `init_database()` (1 call, 10% time)

**Unnecessary deep copy**: Use references or shallow copy; don't `copy.deepcopy(100MB_dict)` for no reason

## Best Practices

- [ ] Profile first: cProfile, memory_profiler, py-spy
- [ ] Identify bottleneck: I/O, CPU, or memory
- [ ] Choose tool: asyncio (I/O), ProcessPoolExecutor (CPU), generators (memory)
- [ ] Right data structure: dict (lookup), set (membership), deque (queue)
- [ ] Vectorize NumPy/pandas; eliminate Python loops
- [ ] Cache: functools.lru_cache, joblib.Memory, Redis
- [ ] __slots__ for large object counts
- [ ] Generators over lists for streaming
- [ ] Profile in prod-like environment
- [ ] Measure impact: is 5% speed worth 50% complexity?

## Related Skills

**python-concurrency**, **python-design-patterns**, **python-resilience**
