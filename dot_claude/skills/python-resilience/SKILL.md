---
name: python-resilience
description: Retry strategies, circuit breakers, timeouts, backpressure, and fault-tolerant patterns for building systems that gracefully handle transient failures.
origin: ECC
---

# Python Resilience Patterns

## When to Activate

- Adding retry logic to external service calls
- Implementing timeouts for network operations
- Building fault-tolerant microservices and APIs
- Handling rate limiting and backpressure
- Creating infrastructure decorators for common failure modes
- Designing circuit breakers for upstream dependencies

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

### Pattern 1: Basic Retry with Tenacity

Use `tenacity` library for production-grade retry logic.

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
import httpx

TRANSIENT_ERRORS = (ConnectionError, TimeoutError, OSError, httpx.TimeoutException)

@retry(
    retry=retry_if_exception_type(TRANSIENT_ERRORS),
    stop=stop_after_attempt(5),
    wait=wait_exponential_jitter(initial=1, max=30),
)
def fetch_data(url: str) -> dict:
    """Fetch data with automatic retry on transient failures."""
    response = httpx.get(url, timeout=30)
    response.raise_for_status()
    return response.json()
```

### Pattern 2: Retry Only Appropriate Errors

Whitelist retryable exceptions. Permanent errors never succeed on retry.

```python
from tenacity import retry, retry_if_exception_type
import httpx

# Define what's retryable
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    httpx.ConnectError,
    httpx.ReadTimeout,
)

@retry(
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10),
)
def resilient_api_call(endpoint: str) -> dict:
    """API call retrying only on network issues."""
    response = httpx.get(endpoint, timeout=10)
    response.raise_for_status()
    return response.json()

# These will NOT be retried (they always fail if they fail once)
try:
    resilient_api_call("https://api.example.com/invalid")
except httpx.HTTPStatusError as e:
    # 404 or 401 or 400 - permanent failure, no retry
    pass
```

### Pattern 3: HTTP Status Code Retries

Retry specific HTTP status codes that indicate transient issues.

```python
from tenacity import retry, retry_if_result, stop_after_attempt, wait_exponential_jitter
import httpx

# Status codes indicating transient failures
RETRY_STATUS_CODES = {429, 502, 503, 504}

def should_retry_response(response: httpx.Response) -> bool:
    """Check if response indicates a retryable error."""
    return response.status_code in RETRY_STATUS_CODES

@retry(
    retry=retry_if_result(should_retry_response),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10),
)
def http_request(method: str, url: str, **kwargs) -> httpx.Response:
    """Make HTTP request retrying on transient status codes."""
    return httpx.request(method, url, timeout=30, **kwargs)

# Don't raise on bad status, let retry logic decide
response = http_request("GET", "https://api.example.com/data")
if response.status_code == 200:
    return response.json()
```

### Pattern 4: Combined Exception and Status Retry

Handle both network exceptions and HTTP status codes.

```python
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential_jitter,
    before_sleep_log,
)
import logging
import httpx

logger = logging.getLogger(__name__)

TRANSIENT_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    httpx.ConnectError,
    httpx.ReadTimeout,
)
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

def is_retryable_response(response: httpx.Response) -> bool:
    return response.status_code in RETRY_STATUS_CODES

@retry(
    retry=(
        retry_if_exception_type(TRANSIENT_EXCEPTIONS) |
        retry_if_result(is_retryable_response)
    ),
    stop=stop_after_attempt(5) | stop_after_delay(60),
    wait=wait_exponential_jitter(initial=1, max=30),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def robust_http_call(method: str, url: str, **kwargs) -> httpx.Response:
    """HTTP call with comprehensive retry handling."""
    return httpx.request(method, url, timeout=30, **kwargs)
```

## Advanced Patterns

### Pattern 5: Timeout Handling

Set timeouts on all network operations to prevent hanging.

```python
import asyncio
import httpx
from functools import wraps
from typing import TypeVar, Callable

T = TypeVar("T")

def with_timeout(seconds: float):
    """Decorator to add timeout to async functions."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
        return wrapper
    return decorator

@with_timeout(30)
async def fetch_with_timeout(url: str) -> dict:
    """Fetch URL with 30 second timeout."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Sync version
def sync_timeout(seconds: float):
    """Add timeout to sync functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Operation timed out after {seconds}s")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
        return wrapper
    return decorator
```

### Pattern 6: Circuit Breaker Pattern

Stop calling failing service immediately; fail fast and let service recover.

```python
from enum import Enum
from time import time, sleep
from typing import Callable, TypeVar

T = TypeVar("T")

class CircuitState(Enum):
    CLOSED = "closed"      # Working normally
    OPEN = "open"          # Stop trying, fail immediately
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise RuntimeError("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Reset on success."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Track failure and open circuit if threshold reached."""
        self.failure_count += 1
        self.last_failure_time = time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        return (
            self.last_failure_time is not None and
            time() - self.last_failure_time >= self.recovery_timeout
        )

# Usage
breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

def external_api_call() -> dict:
    """Call external API."""
    import httpx
    return httpx.get("https://api.example.com").json()

try:
    result = breaker.call(external_api_call)
except RuntimeError as e:
    # Circuit is open, fail fast
    return {"error": "Service unavailable, try again later"}
```

### Pattern 7: Bulkhead Pattern (Semaphore Limiting)

Isolate resources to prevent one failure from affecting others.

```python
import asyncio
from typing import List

async def limited_requests(urls: List[str], max_concurrent: int = 5):
    """Execute requests with concurrency limit (bulkhead)."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_request(url: str) -> dict:
        async with semaphore:
            # Only N requests run at once
            return await fetch(url)

    tasks = [bounded_request(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Thread pool version for sync code
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=5)  # Bulkhead

def sync_limited_requests(urls: list) -> list:
    """Thread pool limits concurrency."""
    futures = [executor.submit(fetch, url) for url in urls]
    return [f.result() for f in futures]
```

### Pattern 8: Graceful Degradation

Return cached/default values instead of failing completely.

```python
from functools import wraps
from typing import TypeVar, Any, Callable, Optional

T = TypeVar("T")

def fail_safe(default: Any, cache_ttl: Optional[float] = None):
    """Return default value on failure; optionally cache successful results."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = {}
        cache_time = {}

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            import time

            # Try main function
            try:
                result = func(*args, **kwargs)
                # Cache successful result
                if cache_ttl:
                    cache[args] = result
                    cache_time[args] = time.time()
                return result
            except Exception as e:
                # Try returning cached value
                if cache_ttl and args in cache:
                    elapsed = time.time() - cache_time[args]
                    if elapsed < cache_ttl:
                        return cache[args]

                # Return default
                return default

        return wrapper
    return decorator

@fail_safe(default=[])  # Return empty list if recommendations fail
async def get_recommendations(user_id: str) -> list[str]:
    """Get recommendations; degraded mode returns nothing."""
    return await fetch_recommendations(user_id)

@fail_safe(default={"cached": True}, cache_ttl=300)
async def get_user_data(user_id: str) -> dict:
    """Return cached data (up to 5 mins old) if fresh data unavailable."""
    return await fetch_user_data(user_id)
```

### Pattern 9: Idempotency Keys

Enable safe retries by deduplicating requests using idempotency keys.

```python
import uuid
from typing import Optional

class IdempotentClient:
    """Client ensuring idempotent requests."""

    def __init__(self):
        self.processed = {}  # Track processed idempotency keys

    def create_order(
        self,
        user_id: str,
        items: list,
        idempotency_key: Optional[str] = None,
    ) -> dict:
        """Create order with idempotency key for safe retries."""
        # Generate or use provided key
        key = idempotency_key or str(uuid.uuid4())

        # Check if already processed
        if key in self.processed:
            return self.processed[key]

        # Process request
        try:
            order = {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "items": items,
            }
            # Store result
            self.processed[key] = order
            return order
        except Exception:
            # Don't cache errors; only successful results
            raise

# Usage: Client can retry with same idempotency key safely
client = IdempotentClient()
order = client.create_order(user_id="123", items=["A", "B"], idempotency_key="req-456")
# Retry with same key returns same result, not a duplicate order
order_retry = client.create_order(user_id="123", items=["A", "B"], idempotency_key="req-456")
assert order["id"] == order_retry["id"]  # Same order
```

## Retry vs Circuit Breaker Decision Matrix

| Scenario | Use | Why |
|----------|-----|-----|
| Transient, isolated failures (one call fails) | Retry | Likely to succeed on retry |
| Cascading failures (many calls failing to same service) | Circuit Breaker | Prevent overwhelming failing service |
| Occasional timeouts | Timeout + Retry | Transient issue, retry helps |
| Service completely down (503) | Circuit Breaker | Don't retry; fail fast, let service recover |
| Flaky network, high latency | Timeout + Exponential Backoff | Give service time, don't retry immediately |

## Best Practices

### Do This

```python
# GOOD: Specific exception, bounded retries, exponential backoff
@retry(
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    stop=stop_after_attempt(3) | stop_after_delay(30),
    wait=wait_exponential_jitter(initial=1, max=10),
)
def call_api(url: str) -> dict:
    return httpx.get(url).json()

# GOOD: Timeout on all network calls
response = httpx.get(url, timeout=30)

# GOOD: Circuit breaker for dependent services
breaker = CircuitBreaker(failure_threshold=5)
result = breaker.call(upstream_service.fetch, data)

# GOOD: Graceful degradation for non-critical paths
@fail_safe(default=[])
def get_recommendations(user_id: str) -> list:
    return fetch_recommendations(user_id)

# GOOD: Log failures for monitoring
@retry(
    ...,
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def monitored_call():
    ...
```

### Don't Do This

```python
# BAD: Retry permanent errors (invalid credentials)
@retry(stop=stop_after_attempt(3))
def login(username: str, password: str) -> dict:
    return api.login(username, password)  # Won't help if password wrong

# BAD: Infinite retries
@retry()  # No stop condition
def flaky_operation():
    ...

# BAD: Retry without timeout (hangs indefinitely)
def hanging_request(url: str):
    return httpx.get(url)  # No timeout; can hang forever

# BAD: Retry immediately without backoff
@retry(wait=wait_fixed(0))  # Retry instantly, might overwhelm service
def bad_retry():
    ...

# BAD: Swallow exceptions silently
try:
    result = api_call()
except Exception:
    return None  # Silent failure, hard to debug

# GOOD: Explicit error handling
try:
    result = api_call()
except Exception as e:
    logger.error(f"API call failed: {e}")
    raise
```

## Anti-Patterns

```python
# ANTI-PATTERN 1: Retrying non-idempotent operations
@retry(stop=stop_after_attempt(3))
def transfer_money(from_account: str, to_account: str, amount: float):
    # Retrying on failure might transfer twice!
    api.transfer(from_account, to_account, amount)

# ANTI-PATTERN 2: Infinite exponential backoff
@retry(wait=wait_exponential())  # Can grow very large
def slow_retry():
    ...

# ANTI-PATTERN 3: No timeout on network calls
def unprotected_api_call(url: str):
    import requests
    return requests.get(url)  # Can hang forever

# ANTI-PATTERN 4: Catching and ignoring all exceptions
try:
    result = operation()
except:
    result = None  # Bare except, swallows everything

# ANTI-PATTERN 5: Retry sleep in sync code blocks event loop
async def blocking_retry():
    import time
    time.sleep(1)  # BLOCKS event loop
    # Use await asyncio.sleep(1) instead
```

## Agent Support

- **python-expert** — Decorator patterns and type hints for resilience code
- **nodejs-expert** — Comparison with Node.js retry/circuit breaker libraries

## Skill References

- **python-patterns** — Decorators, error handling, context managers
- **async-python-patterns** — Timeouts with asyncio.wait_for, async retries
- **postgresql-patterns** — Connection pool resilience and transaction handling
