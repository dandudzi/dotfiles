---
name: python-resilience
description: Retry strategies, circuit breakers, timeouts, backpressure, and fault-tolerant patterns for building systems that gracefully handle transient failures.
origin: ECC
model: sonnet
---

# Python Resilience Patterns

## When to Activate

- Adding retry logic to external service calls
- Implementing circuit breakers for dependent services
- Building fault-tolerant APIs with timeouts and degradation

## Core Concepts

### Transient vs Permanent Failures

Retry only transient errors. Never retry permanent failures.

| Failure Type | Examples | Retry? | Why |
|--------------|----------|--------|-----|
| Transient | Network timeout, 503, database temporarily down | YES | Will likely succeed on retry |
| Permanent | Invalid credentials, 404, malformed request, SQL syntax error | NO | Will always fail; retry wastes resources |
| Status-based | HTTP 429 (rate limit), 502 (bad gateway), 500 (server error) | Some | Depends on root cause |

### Exponential Backoff

Increase wait time between retries: 1s, 2s, 4s, 8s, 16s. Gives recovering services time.

### Jitter

Add randomness to backoff timing to prevent thundering herd (all clients retrying simultaneously).

### Bounded Retries

Cap both attempt count and total duration. Unbounded retries hide systemic problems.

## Fundamental Patterns

### Pattern 1: Retry with Exception and Status Code Handling

Use `tenacity` for production retry logic. Whitelist transient errors only and retry specific HTTP statuses.

```python
from tenacity import (
    retry, retry_if_exception_type, retry_if_result,
    stop_after_attempt, stop_after_delay, wait_exponential_jitter,
    before_sleep_log,
)
import logging, httpx

logger = logging.getLogger(__name__)

TRANSIENT_EXCEPTIONS = (ConnectionError, TimeoutError, httpx.ConnectError, httpx.ReadTimeout)
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

def is_retryable_response(response: httpx.Response) -> bool:
    return response.status_code in RETRY_STATUS_CODES

@retry(
    retry=(retry_if_exception_type(TRANSIENT_EXCEPTIONS) | retry_if_result(is_retryable_response)),
    stop=stop_after_attempt(5) | stop_after_delay(60),
    wait=wait_exponential_jitter(initial=1, max=30),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def robust_api_call(method: str, url: str, **kwargs) -> httpx.Response:
    """Retry transient errors and retryable status codes with exponential backoff."""
    return httpx.request(method, url, timeout=30, **kwargs)
```

Permanent errors (400, 401, 404) are never retried—they always fail on retry.
Combine exception-based and status-based retry conditions with `|` operator.

## Advanced Patterns

### Pattern 2: Circuit Breaker Pattern

Stop calling failing services immediately; fail fast and let service recover. Transitions: CLOSED (normal) → OPEN (fail fast after threshold) → HALF_OPEN (test recovery).

```python
from enum import Enum
from time import time
from typing import Callable, TypeVar

T = TypeVar("T")

class CircuitBreaker:
    """Prevent cascading failures by stopping calls to broken services."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        if self.state == "OPEN":
            if time() - (self.last_failure_time or 0) >= self.recovery_timeout:
                self.state = "HALF_OPEN"  # Test recovery
            else:
                raise RuntimeError("Circuit breaker OPEN")
        try:
            result = func(*args, **kwargs)
            self.failure_count = 0
            self.state = "CLOSED"
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise

breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
try:
    result = breaker.call(upstream_service.fetch)
except RuntimeError:
    return {"error": "Service unavailable, try again later"}
```

### Pattern 3: Bulkhead (Resource Isolation)

Limit concurrent connections to prevent cascading failures.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Async version with semaphore
async def limited_requests(urls: list, max_concurrent: int = 5):
    semaphore = asyncio.Semaphore(max_concurrent)
    async def bounded_request(url):
        async with semaphore:
            return await fetch(url)
    return await asyncio.gather(*[bounded_request(u) for u in urls], return_exceptions=True)

# Sync version with thread pool
executor = ThreadPoolExecutor(max_workers=5)
futures = [executor.submit(fetch, url) for url in urls]
results = [f.result() for f in futures]
```

### Pattern 4: Graceful Degradation with Caching

Return cached/default values on failure instead of failing completely.

```python
from functools import wraps
import time
from typing import TypeVar, Any, Callable

T = TypeVar("T")

def fail_safe(default: Any, cache_ttl: float = None):
    """Return default on failure; cache successful results with optional TTL."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = {}
        cache_time = {}

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                result = func(*args, **kwargs)
                if cache_ttl:
                    cache[args] = result
                    cache_time[args] = time.time()
                return result
            except Exception:
                # Return cached if fresh, else default
                if cache_ttl and args in cache and time.time() - cache_time[args] < cache_ttl:
                    return cache[args]
                return default
        return wrapper
    return decorator

@fail_safe(default=[], cache_ttl=300)
def get_recommendations(user_id: str) -> list:
    """Return cached recommendations (up to 5 min old) or empty list on failure."""
    return fetch_recommendations(user_id)
```

### Pattern 5: Idempotency Keys

Safe retries via request deduplication using idempotency keys.

```python
import uuid

class IdempotentClient:
    """Deduplicates requests using idempotency keys; safe for retries."""
    def __init__(self):
        self.processed = {}

    def create_order(self, user_id: str, items: list, idempotency_key: str = None) -> dict:
        key = idempotency_key or str(uuid.uuid4())
        if key in self.processed:
            return self.processed[key]
        try:
            order = {"id": str(uuid.uuid4()), "user_id": user_id, "items": items}
            self.processed[key] = order
            return order
        except Exception:
            raise  # Don't cache errors

client = IdempotentClient()
order = client.create_order("123", ["A", "B"], "req-456")
order_retry = client.create_order("123", ["A", "B"], "req-456")
assert order["id"] == order_retry["id"]  # Same result, not duplicate
```

## Decision Matrix: When to Use What

| Scenario | Pattern | Reason |
|----------|---------|--------|
| One call fails transiently | Retry | Likely succeeds on retry |
| Many calls failing to same service | Circuit Breaker | Prevent overwhelming service |
| Network timeouts | Retry + Timeout | Transient; backoff helps |
| Service down (503) | Circuit Breaker | Fail fast, let service recover |
| Non-critical data needed | Graceful Degradation | Return cached/default instead of failing |

## Best Practices

```python
# CORRECT: Whitelist transient errors, bounded retries, exponential backoff
@retry(
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    stop=stop_after_attempt(3) | stop_after_delay(30),
    wait=wait_exponential_jitter(initial=1, max=10),
)
def call_api(url: str) -> dict:
    return httpx.get(url, timeout=30).json()

# CORRECT: Circuit breaker prevents cascading failures
breaker = CircuitBreaker(failure_threshold=5)
result = breaker.call(upstream_service.fetch, data)

# CORRECT: Graceful degradation for non-critical paths
@fail_safe(default=[])
def get_recommendations(user_id: str) -> list:
    return fetch_recommendations(user_id)

# WRONG: Retry permanent errors (404, 401, invalid password)
@retry(stop=stop_after_attempt(3))
def login(username: str, password: str) -> dict:
    return api.login(username, password)  # Will always fail if wrong

# WRONG: No timeout on network calls (can hang indefinitely)
def hanging_request(url: str):
    return httpx.get(url)  # Missing timeout

# WRONG: Swallow exceptions silently
try:
    result = api_call()
except Exception:
    return None  # Silent failure, impossible to debug
```

## Anti-Patterns to Avoid

```python
# WRONG: Retrying non-idempotent operations (may transfer twice)
@retry(stop=stop_after_attempt(3))
def transfer_money(from_account: str, to_account: str, amount: float):
    api.transfer(from_account, to_account, amount)

# WRONG: Unbounded exponential backoff (can wait forever)
@retry(wait=wait_exponential())  # Grows exponentially without cap
def slow_retry():
    pass

# WRONG: No timeout blocks indefinitely
def unprotected_api_call(url: str):
    import requests
    return requests.get(url)  # Can hang forever

# WRONG: Catch all exceptions silently (hides bugs)
try:
    result = operation()
except:
    result = None  # Bare except, impossible to debug

# WRONG: Blocking sleep in async event loop
async def blocking_retry():
    import time
    time.sleep(1)  # BLOCKS event loop; use await asyncio.sleep(1)
```

Use **python-patterns** for decorators and error handling; **async-python-patterns** for timeouts with asyncio.
