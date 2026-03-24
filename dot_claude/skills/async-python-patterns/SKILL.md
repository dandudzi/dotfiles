---
name: async-python-patterns
description: Asyncio fundamentals, async/await patterns, concurrent I/O, and event loop management for building high-performance, non-blocking Python applications.
origin: ECC
model: sonnet
---

# Async Python Patterns

## When to Activate

- Building concurrent I/O operations (web APIs, database, file, network)
- Creating web scrapers, data fetchers, and real-time applications
- Processing multiple independent tasks with asyncio, gather(), or TaskGroup

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
# WRONG: Blocking code stalls event loop
async def fetch_and_process(url: str):
    data = await fetch(url)
    result = compute(data)  # BLOCKS! Use asyncio.to_thread() instead
    return result

# RIGHT: Use async-native libraries and offload blocking work
async def fetch_and_process(url: str):
    data = await fetch(url)
    result = await asyncio.to_thread(compute, data)  # Offload to thread pool
    return result
```

## Core Concepts

**Event Loop:** Single-threaded cooperative scheduler managing coroutines and I/O.
**Coroutines:** Functions defined with `async def`, yield control with `await`.
**Tasks:** Scheduled coroutines running on the event loop.
**Futures:** Low-level objects representing eventual async results.

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

async def fetch_user(user_id: int) -> dict:
    await asyncio.sleep(0.5)
    return {"id": user_id, "name": f"User {user_id}"}

async def main():
    # Run all tasks concurrently
    results = await asyncio.gather(
        fetch_user(1), fetch_user(2), fetch_user(3)
    )
    print(f"Fetched {len(results)} users")

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

### Pattern 4: Error Handling with gather()

```python
import asyncio

async def risky_op(item_id: int) -> dict:
    await asyncio.sleep(0.1)
    if item_id % 3 == 0:
        raise ValueError(f"Item {item_id} failed")
    return {"id": item_id, "status": "success"}

async def main():
    # return_exceptions=True allows continue-on-error
    results = await asyncio.gather(
        *(risky_op(i) for i in [1, 2, 3, 4, 5, 6]),
        return_exceptions=True
    )
    errors = [r for r in results if isinstance(r, Exception)]
    print(f"Errors: {len(errors)}")

asyncio.run(main())
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

### Pattern 6: Task Coordination (gather vs wait vs TaskGroup)

```python
import asyncio

async def task_a():
    await asyncio.sleep(1)
    return "A"

async def task_b():
    await asyncio.sleep(2)
    return "B"

# gather() - simplest
results = await asyncio.gather(task_a(), task_b(), return_exceptions=True)

# TaskGroup (Python 3.11+) - structured concurrency with auto cleanup
async with asyncio.TaskGroup() as tg:
    t1 = tg.create_task(task_a())
    t2 = tg.create_task(task_b())
    # Awaits all, handles exceptions on exit

# wait() - fine-grained control (rarely needed)
done, pending = await asyncio.wait(
    [task_a(), task_b()],
    return_when=asyncio.FIRST_COMPLETED
)
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

### Pattern 8: Async Generators

```python
import asyncio
from typing import AsyncIterator

async def fetch_pages(url: str, max_pages: int) -> AsyncIterator[dict]:
    """Async generator yielding paginated data."""
    for page in range(1, max_pages + 1):
        await asyncio.sleep(0.2)  # Simulate API call
        yield {"page": page, "items": [f"item_{page}_{i}" for i in range(5)]}

async def main():
    async for page_data in fetch_pages("https://api.example.com", 3):
        print(f"Page {page_data['page']}: {len(page_data['items'])} items")

asyncio.run(main())
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

### Real-World: Web Scraping

```python
import asyncio
import aiohttp

async def fetch_url(session: aiohttp.ClientSession, url: str) -> dict:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            return {"url": url, "status": resp.status, "length": len(await resp.text())}
    except aiohttp.ClientError as e:
        return {"url": url, "error": str(e)}

async def scrape_urls(urls: list[str]) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*(fetch_url(session, url) for url in urls))
        return results

asyncio.run(scrape_urls(["https://httpbin.org/delay/1", "https://httpbin.org/status/404"]))
```

### Real-World: Async Database Operations

```python
import asyncio

async def get_user_data(db, user_id: int) -> dict:
    """Fetch user, orders, and profile concurrently."""
    user, orders, profile = await asyncio.gather(
        db.fetch_one(f"SELECT * FROM users WHERE id = {user_id}"),
        db.execute(f"SELECT * FROM orders WHERE user_id = {user_id}"),
        db.fetch_one(f"SELECT * FROM profiles WHERE user_id = {user_id}"),
    )
    return {"user": user, "orders": orders, "profile": profile}
```

## Common Pitfalls

1. **Forgetting await** — Returns unawaited coroutine. Use `result = await async_func()`.
2. **Blocking event loop** — Use `await asyncio.sleep()`, not `time.sleep()`.
3. **Ignoring cancellation** — Wrap long tasks: `try/except asyncio.CancelledError: raise`.
4. **Mixed sync/async** — Use `asyncio.run(async_func())` only at entry point.

## Anti-Patterns

- Don't manually create event loops; use `asyncio.run()` at entry point
- Don't use `asyncio.gather()` without `return_exceptions=True` for error resilience
- Libraries should expose async APIs, not manage event loops
- Don't mix `sync` and `async` without using threads: `await asyncio.to_thread()`

**Agent Support:** python-expert, python-resilience
**Related:** python-patterns, python-resilience (timeouts/retries), postgresql-patterns (asyncpg)
