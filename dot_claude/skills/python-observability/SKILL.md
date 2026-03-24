---
name: python-observability
description: Structured logging, metrics collection, distributed tracing, and health checks for production Python applications.
origin: ECC
model: sonnet
---

# Python Observability Patterns

Instrument Python applications with structured logs, metrics, and traces to diagnose production issues.

## When to Activate

- Adding structured logging or metrics collection
- Setting up distributed tracing across services
- Building health check endpoints or designing alerting

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
import httpx

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

def set_correlation_id(cid: str | None = None) -> str:
    cid = cid or str(uuid.uuid4())
    correlation_id.set(cid)
    structlog.contextvars.bind_contextvars(correlation_id=cid)
    return cid

# Middleware: extract or generate correlation ID
async def correlation_id_middleware(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    set_correlation_id(cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response

# Propagate to downstream services
async def call_downstream(endpoint: str, data: dict) -> dict:
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

```python
import structlog

logger = structlog.get_logger()

# DEBUG: internal diagnostics
logger.debug("cache_hit", key=user_id, ttl_seconds=3600)

# INFO: normal operations (requests, completions)
logger.info("order_created", order_id="ORD-123", total=99.99)

# WARNING: recoverable anomalies (retries, degraded behavior)
logger.warning("rate_limit_approaching", current=950, limit=1000)

# ERROR: failures requiring investigation (exceptions, unavailable services)
logger.error("payment_failed", order_id="ORD-123", error_type="stripe_error")
```

Use INFO for user errors (wrong password), ERROR for system failures only.

### Pattern 4: Prometheus Metrics - Four Golden Signals

```python
from prometheus_client import Counter, Histogram, Gauge
from functools import wraps
import time

# Latency: histogram with percentile buckets
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint", "status"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2.5, 5],
)

# Traffic: total request count
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

# Errors: error count
ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP errors",
    ["method", "endpoint", "error_type"],
)

# Saturation: resource utilization
DB_CONNECTIONS_USED = Gauge(
    "db_connections_used",
    "Active database connections",
)

def track_metrics(func):
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        start = time.perf_counter()
        try:
            response = await func(request, *args, **kwargs)
            status = str(response.status_code)
            return response
        except Exception as e:
            ERROR_COUNT.labels(method=request.method, endpoint=request.url.path, error_type=type(e).__name__).inc()
            raise
        finally:
            duration = time.perf_counter() - start
            REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=status).inc()
            REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path, status=status).observe(duration)
    return wrapper
```

### Pattern 5: Bounded Cardinality in Metrics

Never use unbounded values (user IDs, request paths with IDs) as metric labels—they explode storage.

```python
from prometheus_client import Counter

# WRONG: Unbounded label (millions of unique values)
REQUEST_COUNT_BAD = Counter("http_requests_total", "Requests", ["user_id"])

# CORRECT: Only bounded labels [free, standard, premium]
REQUEST_COUNT = Counter("http_requests_total", "Requests", ["user_tier"])
REQUEST_COUNT.labels(user_tier="premium").inc()

# For per-user metrics, use structured logs instead
logger.info("user_request", user_id="user-12345", endpoint="/api/data")
```

### Pattern 6: Health Check Endpoints

```python
from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

async def check_database() -> bool:
    try:
        result = await db.execute("SELECT 1")
        return result is not None
    except Exception:
        return False

@app.get("/health/live")
async def liveness() -> dict:
    """Liveness: is the app running? Kubernetes restarts on failure."""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness() -> dict:
    """Readiness: can app handle traffic? Check dependencies."""
    db_ok = await check_database()

    if not db_ok:
        raise HTTPException(status_code=503, detail={"status": "not_ready", "database": "down"})

    return {"status": "ready", "database": "ok"}
```

### Pattern 7: Distributed Tracing with OpenTelemetry

> For full OTel SDK setup, exporters, sampling strategies, and collector pipelines, use the `opentelemetry-setup` skill. The snippet below shows minimal usage; see that skill for production configuration.

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Configure exporter (Jaeger, Zipkin, etc.)
jaeger_exporter = JaegerExporter(agent_host_name="localhost", agent_port=6831)
trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(trace_provider)

tracer = trace.get_tracer(__name__)

async def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)

        with tracer.start_as_current_span("validate_order"):
            await validate_order(order_id)

        with tracer.start_as_current_span("charge_payment"):
            payment_result = await charge_payment(order_id)
            span.set_attribute("payment.status", payment_result.status)
```

### Pattern 8: Timing Context Manager

```python
from contextlib import contextmanager
import time
import structlog

logger = structlog.get_logger()

@contextmanager
def timed_operation(operation_name: str, **fields):
    start = time.perf_counter()
    logger.debug("operation_started", operation=operation_name, **fields)

    try:
        yield
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error("operation_failed", operation=operation_name, duration_ms=elapsed_ms, error_type=type(e).__name__, **fields)
        raise
    else:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info("operation_completed", operation=operation_name, duration_ms=elapsed_ms, **fields)

# Usage
with timed_operation("fetch_user_orders", user_id="user-123"):
    orders = await order_repository.get_by_user("user-123")
```

## Advanced Patterns

### Pattern 9: Alert Design - RED Metrics

Alert on Rate, Errors, and Duration—not symptoms like CPU or disk usage.

```yaml
# Prometheus alerting rules
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
```

## Anti-Patterns

```python
# WRONG: Log PII (passwords, tokens)
logger.info("user_login", user_email=email, password_hash=password)

# CORRECT: Log IDs only
logger.info("user_login", user_id=user.id, email_domain=email.split("@")[1])

# WRONG: Use print() instead of logger
print("Error occurred:", error)

# CORRECT: Use logger with context
logger.error("operation_failed", error_type=type(e).__name__, operation="sync_data")

# WRONG: Missing correlation IDs
result = await downstream_service()

# CORRECT: Propagate correlation ID
result = await downstream_service(headers={"X-Correlation-ID": correlation_id.get()})

# WRONG: Unbounded metric labels (/user/1, /user/2, /user/3...)
REQUEST_COUNT.labels(endpoint=request.url.path).inc()

# CORRECT: Use bounded labels only
REQUEST_COUNT.labels(endpoint_pattern="/user/{id}").inc()

# WRONG: Sparse context in logs
logger.error("Failed to process")

# CORRECT: Full context
logger.error("item_processing_failed", item_id=item.id, error_type=type(e).__name__)
```

## Related Skills

**python-error-handling**, **python-resilience**, **opentelemetry-setup**
