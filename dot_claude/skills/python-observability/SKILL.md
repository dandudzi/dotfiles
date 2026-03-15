---
name: python-observability
description: Structured logging, metrics collection, distributed tracing, and health checks for production Python applications.
origin: ECC
---

# Python Observability Patterns

Instrument Python applications with structured logs, metrics, and traces to diagnose production issues without deploying new code.

## When to Activate

- Adding structured logging to applications
- Implementing metrics collection with Prometheus
- Setting up distributed tracing across services
- Propagating correlation IDs through request chains
- Building health check endpoints
- Designing alerting strategies

## Core Concepts

### Four Golden Signals

Track these metrics at every service boundary:

| Signal | Metric | Purpose |
|--------|--------|---------|
| Latency | Request duration (ms) | How fast is the service? |
| Traffic | Requests per second | How much load? |
| Errors | Error rate / error count | What's failing? |
| Saturation | Resource utilization (%) | At capacity? |

### Correlation IDs

Thread a unique ID through all logs and spans for a single request. Enables answering "what happened to request X?" across all services.

### Bounded Cardinality

Keep metric label values bounded. Unbounded labels (like user IDs) explode Prometheus storage. Use only enumerated values.

## Fundamental Patterns

### Pattern 1: Structured Logging with Structlog

Configure JSON logging with consistent fields for production, human-readable for development.

```python
import logging
import structlog

def configure_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    """Configure structured logging."""
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# At application startup
configure_logging("INFO", json_format=True)
logger = structlog.get_logger()

logger.info("application_started", service_name="my_api", version="1.0.0")
```

### Pattern 2: Correlation ID Propagation

Generate a unique ID at ingress, propagate through all operations and outbound requests.

```python
from contextvars import ContextVar
import uuid
import structlog
from fastapi import Request

# Context variable for request-scoped correlation ID
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
logger = structlog.get_logger()

def set_correlation_id(cid: str | None = None) -> str:
    """Set correlation ID and bind to logger context."""
    cid = cid or str(uuid.uuid4())
    correlation_id.set(cid)
    structlog.contextvars.bind_contextvars(correlation_id=cid)
    return cid

# FastAPI middleware to extract or generate correlation ID
async def correlation_id_middleware(request: Request, call_next):
    """Middleware to set and propagate correlation ID."""
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    set_correlation_id(cid)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response

# Propagate to downstream services
import httpx

async def call_downstream(endpoint: str, data: dict) -> dict:
    """Call downstream service with correlation ID header."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint,
            json=data,
            headers={"X-Correlation-ID": correlation_id.get()},
        )
        response.raise_for_status()
        return response.json()
```

### Pattern 3: Semantic Log Levels

Use consistent log levels to enable filtering and alerting.

```python
import structlog

logger = structlog.get_logger()

# DEBUG: Internal diagnostics (variable values, internal state)
logger.debug("cache_operation", key=user_id, hit=True, ttl_seconds=3600)

# INFO: Normal operational events (request lifecycle, job completion)
logger.info("order_created", order_id="ORD-123", total=99.99, user_tier="premium")

# WARNING: Recoverable anomalies (retry attempts, degraded behavior)
logger.warning(
    "rate_limit_approaching",
    current_rate=950,
    limit=1000,
    reset_seconds=30,
)

# ERROR: Failures requiring investigation (exceptions, unavailable services)
logger.error(
    "payment_failed",
    order_id="ORD-123",
    error_type="stripe_error",
    status_code=502,
)
```

Never log expected behavior (e.g., wrong password) at ERROR level. Distinguish between user error (INFO) and system failure (ERROR).

### Pattern 4: Prometheus Metrics - Four Golden Signals

Instrument endpoints with Counter, Gauge, and Histogram metrics.

```python
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps
from fastapi import FastAPI, Request

app = FastAPI()

# Latency: Request duration distribution
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint", "status"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
)

# Traffic: Total request count
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

# Errors: Error count
ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP errors",
    ["method", "endpoint", "error_type"],
)

# Saturation: Resource utilization
DB_CONNECTIONS_USED = Gauge(
    "db_connections_used",
    "Number of active database connections",
)

# Decorator to instrument endpoints
def track_metrics(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        method = request.method
        endpoint = request.url.path
        start = time.perf_counter()

        try:
            response = await func(request, *args, **kwargs)
            status = str(response.status_code)
            return response
        except Exception as e:
            status = "500"
            ERROR_COUNT.labels(
                method=method,
                endpoint=endpoint,
                error_type=type(e).__name__,
            ).inc()
            raise
        finally:
            duration = time.perf_counter() - start
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint, status=status).observe(duration)

    return wrapper

# Use on endpoints
@app.get("/users/{user_id}")
@track_metrics
async def get_user(request: Request, user_id: str):
    return {"id": user_id}
```

### Pattern 5: Bounded Cardinality in Metrics

Never use unbounded values (user IDs, request paths with IDs) as metric labels.

```python
from prometheus_client import Counter

# BAD: Unbounded label causing metric explosion
REQUEST_COUNT_WRONG = Counter(
    "http_requests_total",
    "Total requests",
    ["user_id"],  # Millions of unique values!
)
REQUEST_COUNT_WRONG.labels(user_id="user-12345").inc()  # Creates new time series

# GOOD: Only bounded label values
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total requests",
    ["user_tier"],  # Bounded: [free, standard, premium]
)
REQUEST_COUNT.labels(user_tier="premium").inc()

# If you need per-user metrics, log instead
import structlog
logger = structlog.get_logger()
logger.info("user_request", user_id="user-12345", endpoint="/api/data")
# Query logs to answer per-user questions
```

### Pattern 6: Health Check Endpoints

Implement liveness and readiness endpoints for Kubernetes/container orchestration.

```python
from fastapi import FastAPI, HTTPException
from enum import Enum
import httpx

app = FastAPI()

class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"

async def check_database() -> bool:
    """Check if database is accessible."""
    try:
        # Example: simple query
        result = await db.execute("SELECT 1")
        return result is not None
    except Exception:
        return False

async def check_redis() -> bool:
    """Check if Redis is accessible."""
    try:
        result = await redis_client.ping()
        return result == True
    except Exception:
        return False

async def check_upstream_service() -> bool:
    """Check if upstream service is accessible."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://upstream.example.com/health", timeout=5)
            return response.status_code == 200
    except Exception:
        return False

@app.get("/health/live")
async def liveness() -> dict:
    """Liveness probe: is the application running?

    Kubernetes kills and restarts if this fails.
    Only check if the application process is alive.
    """
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness() -> dict:
    """Readiness probe: can the application handle traffic?

    Kubernetes removes from load balancer if this fails.
    Check all dependencies: database, cache, external services.
    """
    db_ok = await check_database()
    redis_ok = await check_redis()
    upstream_ok = await check_upstream_service()

    if not (db_ok and redis_ok and upstream_ok):
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "ok" if db_ok else "down",
                "redis": "ok" if redis_ok else "down",
                "upstream": "ok" if upstream_ok else "down",
            },
        )

    return {
        "status": "ready",
        "database": "ok",
        "redis": "ok",
        "upstream": "ok",
    }
```

### Pattern 7: Distributed Tracing with OpenTelemetry

Set up end-to-end request tracing across services.

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Configure tracing exporter (Jaeger, Zipkin, etc.)
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(trace_provider)

tracer = trace.get_tracer(__name__)

# Instrument operations with spans
async def process_order(order_id: str) -> Order:
    """Process order with tracing."""
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)

        # Validate order
        with tracer.start_as_current_span("validate_order"):
            await validate_order(order_id)

        # Charge payment
        with tracer.start_as_current_span("charge_payment"):
            payment_result = await charge_payment(order_id)
            span.set_attribute("payment.status", payment_result.status)

        # Send confirmation
        with tracer.start_as_current_span("send_confirmation"):
            await send_confirmation(order_id)

        return order
```

### Pattern 8: Timing Context Manager

Reusable pattern for logging operation duration and errors.

```python
from contextlib import contextmanager
import time
import structlog

logger = structlog.get_logger()

@contextmanager
def timed_operation(operation_name: str, **fields):
    """Context manager for timing and structured logging of operations."""
    start = time.perf_counter()
    logger.debug("operation_started", operation=operation_name, **fields)

    try:
        yield
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error(
            "operation_failed",
            operation=operation_name,
            duration_ms=elapsed_ms,
            error_type=type(e).__name__,
            **fields,
        )
        raise
    else:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "operation_completed",
            operation=operation_name,
            duration_ms=elapsed_ms,
            **fields,
        )

# Usage
with timed_operation("fetch_user_orders", user_id="user-123"):
    orders = await order_repository.get_by_user("user-123")
```

## Advanced Patterns

### Pattern 9: Alert Design - RED Metrics

Alert on Rate, Errors, and Duration. Avoid alerting on symptoms.

```python
# GOOD: Alert on actionable metrics (RED)
# - Rate: requests/sec drops suddenly (service down?)
# - Errors: error rate > 5% (bugs in deployment?)
# - Duration: p99 latency > 500ms (slow downstream?)

# BAD: Alert on derived/symptom metrics
# - CPU > 80% (might be normal during batch job)
# - Disk usage > 90% (is it actually a problem?)
# - Queue depth > 1000 (depends on processing rate)

# Example alerting rules (Prometheus)
alert_rules = """
groups:
- name: api_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.05
    annotations:
      summary: "Error rate > 5%"

  - alert: HighLatency
    expr: histogram_quantile(0.99, http_request_duration_seconds) > 0.5
    annotations:
      summary: "P99 latency > 500ms"

  - alert: TrafficDrop
    expr: rate(http_requests_total[5m]) < 10
    for: 5m
    annotations:
      summary: "Request rate dropped below 10/sec"
"""
```

## Anti-Patterns

```python
# ANTI-PATTERN 1: Logging PII
logger.info("user_login", user_email=email, password_hash=password)  # Don't log passwords!

# CORRECT: Log IDs, not sensitive data
logger.info("user_login", user_id=user.id, email_domain=email.split("@")[1])

# ANTI-PATTERN 2: Using print() instead of logger
print("Error occurred:", error)  # Not structured, no timestamps

# CORRECT: Use logger with context
logger.error("operation_failed", error_type=type(e).__name__, operation="sync_data")

# ANTI-PATTERN 3: Missing correlation IDs
async def internal_operation():
    # No way to trace this back to original request
    result = await downstream_service()

# CORRECT: Propagate correlation ID
async def internal_operation():
    headers = {"X-Correlation-ID": correlation_id.get()}
    result = await downstream_service(headers=headers)

# ANTI-PATTERN 4: Unbounded metric labels
REQUEST_COUNT.labels(endpoint=request.url.path).inc()  # /user/1, /user/2, /user/3...

# CORRECT: Use bounded labels
REQUEST_COUNT.labels(endpoint_pattern="/user/{id}").inc()

# ANTI-PATTERN 5: Logging without context
logger.error("Failed to process")  # Which item? Why failed?

# CORRECT: Log with full context
logger.error("item_processing_failed", item_id=item.id, error_type=type(e).__name__)

# ANTI-PATTERN 6: Alerting on every error
# Alert if ANY error occurs (creates thousands of alerts)

# CORRECT: Alert on rate or aggregate
# Alert if error rate > 5% for 5 minutes (actionable threshold)
```

## Agent Support

- **python-expert** — Structlog configuration, asyncio patterns for tracing
- **rest-expert** — Health check endpoint design, status code semantics

## Skill References

- **python-error-handling** — Structured exception context for logs
- **python-resilience** — Circuit breaker and retry patterns with logging
- **opentelemetry-expert** — Advanced tracing instrumentation
