---
name: async-python-patterns
description: Asyncio fundamentals, async/await patterns, concurrent I/O, and event loop management for building high-performance, non-blocking Python applications.
origin: ECC
---

# Async Python Patterns

## When to Activate

- Building async web APIs (FastAPI, Quart, aiohttp)
- Implementing concurrent I/O operations (database, file, network)
- Creating web scrapers and data fetchers
- Developing real-time applications (WebSocket servers, chat systems)
- Processing multiple independent tasks simultaneously
- Optimizing I/O-bound workloads
- Building async background tasks and queues

## Concurrency Model Decision Matrix

Choose the right concurrency model for your workload.

| Workload | Model | Use | Why | Example |
|----------|-------|-----|-----|---------|
| Many concurrent I/O (network, database) | `asyncio` | Primary choice | Single-threaded event loop, no GIL overhead | Web API, web scraper |
| CPU-bound computation | `multiprocessing` | Separate Python processes | Bypass GIL, true parallelism | Data processing, ML inference |
| Mixed I/O + CPU | `asyncio.to_thread()` | Offload blocking work | Keep event loop responsive | API call + data processing |
| Simple scripts, few connections | Sync | Keep it simple | Less complexity, easier debugging | CLI tool, small script |
| High concurrency with shared state | `asyncio` + locks | Structured concurrency | Event loop prevents race conditions | Shared cache, request deduplication |

### When Async is Wrong

```python
# BAD: Mixing sync/async in same call path (hidden blocking)
async def fetch_and_process(url: str):
    data = await fetch(url)  # Non-blocking
    result = compute(data)   # BLOCKING! Stalls all tasks
    return result

# GOOD: Offload blocking work
async def fetch_and_process(url: str):
    data = await fetch(url)
    result = await asyncio.to_thread(compute, data)
    return result

# BAD: Using sync libraries in async context
async def fetch_api(url: str):
    import requests
    return requests.get(url)  # BLOCKING! Stalls event loop

# GOOD: Use async-native libraries
async def fetch_api(url: str):
    import httpx
    async with httpx.AsyncClient() as client:
        return await client.get(url)
```

## Core Concepts

### Event Loop
Single-threaded cooperative multitasking scheduler managing coroutines and I/O.

### Coroutines
Functions defined with `async def` that yield control with `await`.

### Tasks
Scheduled coroutines running concurrently on the event loop.

### Futures
Low-level objects representing eventual results of async operations.

## Fundamental Patterns

### Pattern 1: Basic Async/Await

```python
import asyncio

async def fetch_data(url: str) -> dict:
    """Fetch data asynchronously (simulate I/O)."""
    await asyncio.sleep(1)  # Yield control, don't block
    return {"url": url, "data": "result"}

async def main():
    result = await fetch_data("https://api.example.com")
    print(result)

asyncio.run(main())
```

### Pattern 2: Concurrent Execution with gather()

```python
import asyncio
from typing import List

async def fetch_user(user_id: int) -> dict:
    """Fetch single user."""
    await asyncio.sleep(0.5)
    return {"id": user_id, "name": f"User {user_id}"}

async def fetch_all_users(user_ids: List[int]) -> List[dict]:
    """Fetch multiple users concurrently."""
    # Create tasks without waiting (they start immediately)
    tasks = [fetch_user(uid) for uid in user_ids]
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    return results

async def main():
    users = await fetch_all_users([1, 2, 3, 4, 5])
    print(f"Fetched {len(users)} users")

asyncio.run(main())
```

### Pattern 3: Task Creation and Management

```python
import asyncio

async def background_task(name: str, delay: int):
    """Long-running background task."""
    print(f"{name} started")
    await asyncio.sleep(delay)
    print(f"{name} completed")
    return f"Result from {name}"

async def main():
    # Create tasks (they start running immediately)
    task1 = asyncio.create_task(background_task("Task 1", 2))
    task2 = asyncio.create_task(background_task("Task 2", 1))

    # Do other work while tasks run
    print("Main: doing other work")
    await asyncio.sleep(0.5)

    # Wait for tasks to complete
    result1 = await task1
    result2 = await task2
    print(f"Results: {result1}, {result2}")

asyncio.run(main())
```

### Pattern 4: Error Handling in Async Code

```python
import asyncio
from typing import List, Optional

async def risky_operation(item_id: int) -> dict:
    """Operation that might fail."""
    await asyncio.sleep(0.1)
    if item_id % 3 == 0:
        raise ValueError(f"Item {item_id} failed")
    return {"id": item_id, "status": "success"}

async def safe_operation(item_id: int) -> Optional[dict]:
    """Wrapper with error handling."""
    try:
        return await risky_operation(item_id)
    except ValueError as e:
        print(f"Error: {e}")
        return None

async def process_items(item_ids: List[int]):
    """Process multiple items, continuing on errors."""
    tasks = [safe_operation(iid) for iid in item_ids]
    # return_exceptions=True prevents one failure from canceling all
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful = [r for r in results if r is not None and not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]

    print(f"Success: {len(successful)}, Failed: {len(failed)}")
    return successful

asyncio.run(process_items([1, 2, 3, 4, 5, 6]))
```

### Pattern 5: Timeout Handling

```python
import asyncio

async def slow_operation(delay: int) -> str:
    """Operation that takes time."""
    await asyncio.sleep(delay)
    return f"Completed after {delay}s"

async def with_timeout():
    """Execute with timeout protection."""
    try:
        result = await asyncio.wait_for(slow_operation(5), timeout=2.0)
        print(result)
    except asyncio.TimeoutError:
        print("Operation timed out")

asyncio.run(with_timeout())
```

## Advanced Patterns

### Pattern 6: asyncio.gather() vs asyncio.wait() vs TaskGroup

Decision matrix for concurrent execution.

| Method | When | Trade-Off |
|--------|------|-----------|
| `gather(*tasks)` | Simple concurrent execution, early return on first exception | Exception stops gathering; use `return_exceptions=True` to collect all |
| `wait(tasks)` | Fine-grained control over completion (FIRST_COMPLETED, FIRST_EXCEPTION, ALL_COMPLETED) | More verbose, lower-level |
| `TaskGroup` (Python 3.11+) | Modern, structured concurrency, automatic cleanup | Requires Python 3.11+, exceptions wrapped in ExceptionGroup |

```python
import asyncio

async def task_a():
    await asyncio.sleep(1)
    return "A"

async def task_b():
    await asyncio.sleep(2)
    return "B"

# gather() - simplest, exceptions stop execution
results = await asyncio.gather(task_a(), task_b())  # [A, B]
results = await asyncio.gather(task_a(), task_b(), return_exceptions=True)  # Collect all, even errors

# wait() - fine-grained control
done, pending = await asyncio.wait([task_a(), task_b()], return_when=asyncio.FIRST_COMPLETED)
# Process done tasks, cancel pending if needed
for task in pending:
    task.cancel()

# TaskGroup (Python 3.11+) - structured concurrency
async with asyncio.TaskGroup() as tg:
    t1 = tg.create_task(task_a())
    t2 = tg.create_task(task_b())
    # Automatically awaits and handles exceptions when exiting context
```

### Pattern 7: Async Context Managers

```python
import asyncio

class AsyncDatabaseConnection:
    """Async resource management."""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.connection = None

    async def __aenter__(self):
        print("Opening connection")
        await asyncio.sleep(0.1)  # Connect
        self.connection = {"dsn": self.dsn, "connected": True}
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("Closing connection")
        await asyncio.sleep(0.1)  # Cleanup
        self.connection = None
        # Don't suppress exceptions (return False or None)

async def query_database():
    """Use async context manager."""
    async with AsyncDatabaseConnection("postgresql://localhost") as conn:
        print(f"Using connection: {conn}")
        await asyncio.sleep(0.2)  # Query
        return {"rows": 10}

asyncio.run(query_database())
```

### Pattern 8: Async Iterators and Generators

```python
import asyncio
from typing import AsyncIterator

async def async_range(start: int, end: int) -> AsyncIterator[int]:
    """Async generator yielding numbers."""
    for i in range(start, end):
        await asyncio.sleep(0.1)
        yield i

async def fetch_pages(url: str, max_pages: int) -> AsyncIterator[dict]:
    """Async generator fetching paginated data."""
    for page in range(1, max_pages + 1):
        await asyncio.sleep(0.2)  # API call
        yield {"page": page, "items": [f"item_{page}_{i}" for i in range(5)]}

async def consume_async_iterator():
    """Consume async generators."""
    async for number in async_range(1, 5):
        print(f"Number: {number}")

    print("\nFetching pages:")
    async for page_data in fetch_pages("https://api.example.com/items", 3):
        print(f"Page {page_data['page']}: {len(page_data['items'])} items")

asyncio.run(consume_async_iterator())
```

### Pattern 9: Backpressure with Semaphore

```python
import asyncio
from typing import List

async def api_call(url: str, semaphore: asyncio.Semaphore) -> dict:
    """Make rate-limited API call."""
    async with semaphore:
        print(f"Calling {url}")
        await asyncio.sleep(0.5)  # Simulate API call
        return {"url": url, "status": 200}

async def rate_limited_requests(urls: List[str], max_concurrent: int = 5):
    """Execute requests with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [api_call(url, semaphore) for url in urls]
    results = await asyncio.gather(*tasks)
    return results

async def main():
    urls = [f"https://api.example.com/item/{i}" for i in range(20)]
    results = await rate_limited_requests(urls, max_concurrent=3)
    print(f"Completed {len(results)} requests")

asyncio.run(main())
```

### Pattern 10: Mixing Sync and Async Code

```python
import asyncio

def blocking_operation(data: str) -> str:
    """Synchronous CPU-bound or I/O operation."""
    import time
    time.sleep(1)  # Block
    return f"Processed: {data}"

async def async_operation(data: str) -> str:
    """Async operation."""
    await asyncio.sleep(0.5)
    return f"Async: {data}"

async def mixed_operations():
    """Mix sync and async by offloading sync to thread pool."""
    # Run sync code without blocking event loop
    result1 = await asyncio.to_thread(blocking_operation, "data")

    # Run async code
    result2 = await async_operation("more data")

    print(f"{result1}, {result2}")

asyncio.run(mixed_operations())
```

## Production Patterns

### Real-World: Web Scraping with aiohttp

```python
import asyncio
import aiohttp
from typing import List, Dict

async def fetch_url(session: aiohttp.ClientSession, url: str) -> Dict:
    """Fetch single URL with timeout."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            text = await response.text()
            return {"url": url, "status": response.status, "length": len(text)}
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        return {"url": url, "error": str(e)}

async def scrape_urls(urls: List[str]) -> List[Dict]:
    """Scrape multiple URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

async def main():
    urls = ["https://httpbin.org/delay/1", "https://httpbin.org/status/404"]
    results = await scrape_urls(urls)
    for result in results:
        print(result)

asyncio.run(main())
```

### Real-World: Async Database Operations

```python
import asyncio
from typing import List, Optional

class AsyncDB:
    """Simulated async database client."""
    async def fetch_one(self, query: str) -> Optional[dict]:
        await asyncio.sleep(0.1)
        return {"id": 1, "name": "Example"}

    async def execute(self, query: str) -> List[dict]:
        await asyncio.sleep(0.1)
        return [{"id": 1, "name": "Item 1"}]

async def get_user_data(db: AsyncDB, user_id: int) -> dict:
    """Fetch user and related data concurrently."""
    user, orders, profile = await asyncio.gather(
        db.fetch_one(f"SELECT * FROM users WHERE id = {user_id}"),
        db.execute(f"SELECT * FROM orders WHERE user_id = {user_id}"),
        db.fetch_one(f"SELECT * FROM profiles WHERE user_id = {user_id}"),
    )
    return {"user": user, "orders": orders, "profile": profile}

async def main():
    db = AsyncDB()
    user_data = await get_user_data(db, 1)
    print(user_data)

asyncio.run(main())
```

## Common Pitfalls

### Pitfall 1: Forgetting await

```python
# WRONG - returns coroutine object, doesn't execute
result = async_function()
print(result)  # <coroutine object>

# RIGHT - actually waits for result
result = await async_function()
print(result)  # Actual result
```

### Pitfall 2: Blocking the Event Loop

```python
# WRONG - blocks entire event loop, stalls all tasks
async def bad_function():
    import time
    time.sleep(1)  # BLOCKS!

# RIGHT - yields control
async def good_function():
    await asyncio.sleep(1)  # Non-blocking
```

### Pitfall 3: Not Handling Cancellation

```python
# WRONG - ignores cancellation
async def bad_task():
    while True:
        await asyncio.sleep(1)

# RIGHT - handles cancellation gracefully
async def good_task():
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Task cancelled, cleaning up...")
        raise  # Re-raise to propagate cancellation
```

### Pitfall 4: Mixing Sync and Async Directly

```python
# WRONG - can't call async from sync context directly
def sync_function():
    result = await async_function()  # SyntaxError!

# RIGHT - use asyncio.run()
def sync_function():
    result = asyncio.run(async_function())
```

## Anti-Patterns

```python
# ANTI-PATTERN 1: Using asyncio.sleep(0) for yielding
async def bad_yield():
    await asyncio.sleep(0)  # Doesn't actually yield control

# ANTI-PATTERN 2: Creating event loop manually (unnecessary)
import asyncio
loop = asyncio.get_event_loop()
result = loop.run_until_complete(my_coroutine())
# Use asyncio.run() instead

# ANTI-PATTERN 3: Bare asyncio.gather() without return_exceptions
await asyncio.gather(task1, task2)  # First exception cancels all
# Use return_exceptions=True to collect all results and errors
await asyncio.gather(task1, task2, return_exceptions=True)

# ANTI-PATTERN 4: Event loop management in library code
# DON'T: Libraries creating/managing event loops
class MyClient:
    def __init__(self):
        self.loop = asyncio.new_event_loop()  # Wrong!

# DO: Library provides async API, caller manages event loop
class MyClient:
    async def fetch(self, url: str):
        ...
```

## Agent Support

- **python-expert** — Async design patterns and type hints
- **react-expert** — Async patterns in async frameworks (FastAPI, aiohttp)
- **nodejs-expert** — Comparison with Node.js async patterns

## Skill References

- **python-patterns** — Complementary sync patterns, decorators, concurrency models
- **python-resilience** — Timeouts and retry patterns with async
- **postgresql-patterns** — Using asyncpg for async database operations
