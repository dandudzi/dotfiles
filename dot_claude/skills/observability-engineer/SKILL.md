---
name: observability-engineer
description: >
  Enterprise-grade observability: SLI/SLO definition, OpenTelemetry migration,
  distributed tracing, structured logging, alerting, chaos engineering, and
  compliance logging. Use when building or improving observability stacks.
---

# Observability Engineer

## When to Activate

Trigger on: "observability", "SLO", "SLI", "error budget", "OpenTelemetry", "OTel", "tracing", "alerting", "monitoring", "metrics", "Prometheus", "Grafana", "Jaeger", "Loki", "chaos engineering", "burn rate".

## SLI/SLO Framework

### Definitions

- **SLI** (Service Level Indicator): A quantitative measure of service behaviour (e.g., request latency p99, error rate, availability)
- **SLO** (Service Level Objective): A target value for an SLI over a time window (e.g., 99.9% of requests complete in <200ms over 28 days)
- **Error Budget**: The allowed amount of unreliability = 100% − SLO target (e.g., 0.1% for 99.9% SLO)

### SLI Selection by Service Type

| Service Type | Primary SLI | Secondary SLI |
|-------------|------------|---------------|
| User-facing API | Request success rate | p99 latency |
| Data pipeline | Freshness (data age) | Completeness rate |
| Async worker | Task success rate | Processing latency |
| Storage system | Durability | Read latency |

### Error Budget Calculation

```
# 28-day window
Total minutes = 28 × 24 × 60 = 40,320
Error budget minutes = 40,320 × (1 - 0.999) = 40.32 minutes

# Burn rate
burn_rate = error_rate / (1 - SLO_target)
# burn_rate > 1 = consuming budget faster than allowed
# burn_rate = 14.4 → budget exhausted in 2 hours (page immediately)
```

### Alerting Thresholds by Burn Rate

| Burn Rate | Budget consumed in | Action |
|-----------|-------------------|--------|
| 14.4× | 1 hour | Page on-call immediately |
| 6× | 6 hours | Page on-call |
| 3× | 3 days | Ticket (investigate this sprint) |
| 1× | 28 days | Normal (no alert) |

## OpenTelemetry Migration

### Architecture

```
Application (SDK)
    ↓ OTLP (gRPC/HTTP)
OTel Collector (pipeline)
    ├── Processor (batch, filter, transform)
    └── Exporter → Jaeger (traces)
                → Prometheus (metrics)
                → Loki (logs)
```

### SDK Setup (Python)
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)
```

### SDK Setup (TypeScript)
```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({ url: 'http://otel-collector:4317' }),
});
sdk.start();
```

### Auto-Instrumentation
```bash
# Python — zero code changes
opentelemetry-instrument --traces_exporter otlp --metrics_exporter otlp python app.py

# Node.js
node --require @opentelemetry/auto-instrumentations-node/register app.js
```

### Migration Checklist
- [ ] Install OTel SDK (language-specific)
- [ ] Configure OTLP exporter pointing to OTel Collector
- [ ] Enable auto-instrumentation for HTTP, DB, messaging
- [ ] Add manual spans for business-critical operations
- [ ] Set service name, version, environment as resource attributes
- [ ] Validate traces appear in backend (Jaeger/Tempo)
- [ ] Remove old vendor SDK (DataDog agent, Zipkin, etc.)

## Distributed Tracing

### Trace Analysis Workflow
1. Identify the root span (entry point request)
2. Look for gaps between spans (network latency, queue wait)
3. Find longest child span (performance bottleneck)
4. Check error spans (red spans) for exception details
5. Compare p50/p95/p99 to detect outliers

### Sampling Strategies

| Strategy | When to Use | Trade-off |
|----------|------------|-----------|
| Head-based (random 1%) | High-volume services | Misses rare errors |
| Tail-based (error/slow) | When errors must be captured | Requires OTel Collector |
| Always-on | Low-volume / critical paths | High storage cost |
| Parent-based | Distributed systems | Follows upstream decision |

### Trace Retention Policy

- **Production traces**: 7–30 days
- **Error/slow traces**: 90 days (for postmortems)
- **Traces containing PII**: 30 days max, with field-level redaction
- Configure TTL per service in Jaeger/Tempo/Zipkin
- Scrub PII from trace tags before long-term storage

### Context Propagation
Always propagate trace context across service boundaries:
```python
# HTTP: W3C TraceContext headers are injected automatically by OTel SDK
# Kafka: inject into message headers
from opentelemetry.propagate import inject
headers = {}
inject(headers)
producer.send(topic, value=payload, headers=list(headers.items()))
```

## Structured Logging

### Log Format (JSON)
```json
{
  "timestamp": "2026-03-15T20:00:00Z",
  "level": "ERROR",
  "service": "payment-api",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "message": "Payment processing failed",
  "user_id": "usr_123",
  "amount_cents": 5000,
  "error": "insufficient_funds",
  "error_detail": "Account balance below required amount"
}
```

### Log Level Guidelines

| Level | Use for | Example |
|-------|---------|---------|
| ERROR | Requires immediate action | Unhandled exception, data corruption |
| WARN | Degraded but functioning | Retry succeeded, approaching limit |
| INFO | Normal business events | Order placed, user logged in |
| DEBUG | Developer diagnostics | SQL queries, cache misses |

### NEVER Log (sensitive data)
- Passwords, API keys, tokens (even partial)
- Full credit card numbers, CVVs
- SSNs, health data, PII beyond what's needed
- JWT payloads (log only token ID/subject)
- Request bodies containing user credentials

**Recommended: structlog processor for PII redaction**

```python
import re, structlog

PII_PATTERNS = [
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN_REDACTED]'),
    (re.compile(r'(?i)(password|token|api_key)["\s:=]+\S+'), '[SECRET_REDACTED]'),
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL_REDACTED]'),
]

def redact_pii(logger, method, event_dict):
    for key, value in list(event_dict.items()):
        if isinstance(value, str):
            for pattern, replacement in PII_PATTERNS:
                value = pattern.sub(replacement, value)
            event_dict[key] = value
    return event_dict

structlog.configure(processors=[redact_pii, structlog.processors.JSONRenderer()])
```

### Correlation ID Pattern
```python
import uuid
from contextvars import ContextVar

correlation_id: ContextVar[str] = ContextVar('correlation_id')

def middleware(request):
    cid = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
    correlation_id.set(cid)
    # Include in all log statements within this request context
```

## Alerting Patterns

### Alert Design Principles
- Alert on **symptoms** (user impact), not causes (CPU high)
- Every alert must have a runbook link
- Alert fatigue kills on-call — aim for <5 alerts/week per service
- Default to PagerDuty for critical; Slack for warning

### Alert Template
```yaml
# Prometheus AlertManager
- alert: HighErrorRate
  expr: |
    sum(rate(http_requests_total{status=~"5.."}[5m])) /
    sum(rate(http_requests_total[5m])) > 0.01
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Error rate above 1%"
    runbook: "https://wiki/runbooks/high-error-rate"
    dashboard: "https://grafana/d/api-overview"
```

### Routing Matrix
| Severity | Channel | Response Time |
|----------|---------|---------------|
| Critical | PagerDuty (wake) | 5 minutes |
| High | PagerDuty (no wake) | 30 minutes |
| Medium | Slack #alerts | Next business day |
| Low | Ticket | This sprint |

## Chaos Engineering

### Fault Injection Categories
| Fault Type | Tool | What it tests |
|-----------|------|---------------|
| Network latency | tc/Toxiproxy | Timeout handling |
| Service unavailable | Chaos Mesh, Gremlin | Circuit breaker |
| CPU spike | stress-ng | Degraded performance |
| Disk full | fallocate | Storage error handling |
| Pod kill | Chaos Mesh | Restart/recovery |

### Chaos Experiment Protocol
1. Define steady state (normal SLI values)
2. Hypothesise: "If X fails, Y will handle it because Z"
3. Inject fault in staging first
4. Observe SLIs during fault
5. Verify steady state resumes after fault removed
6. Document RTO/RPO achieved vs target

### GameDay Checklist
- [ ] Notify stakeholders (chaos window announced)
- [ ] Steady-state metrics captured (baseline)
- [ ] Rollback procedure documented
- [ ] Monitoring dashboards open during experiment
- [ ] Fault injected and confirmed active
- [ ] Observation period (≥15 min)
- [ ] Fault removed, recovery confirmed
- [ ] Results documented (hypothesis: confirmed/rejected)

## Tool Reference

| Tool | Purpose | When to Use |
|------|---------|-------------|
| Prometheus | Metrics scraping + storage | Pull-based metrics from services |
| Grafana | Dashboards + alerting | Visualising metrics + SLO dashboards |
| Jaeger / Tempo | Distributed tracing | Trace analysis, latency profiling |
| Loki | Log aggregation | Structured log search, log-trace correlation |
| OTel Collector | Telemetry pipeline | Receiving, processing, routing all signals |
| Alertmanager | Alert routing | Deduplication, silencing, routing rules |
| Chaos Mesh | Kubernetes chaos | Pod-level fault injection in K8s |
| k6 / Locust | Load testing | Validate SLOs under realistic load |

## Compliance Logging

| Standard | Log Requirements | Retention |
|----------|-----------------|-----------|
| SOC2 | Auth events, admin actions, data access | 1 year |
| PCI DSS | Card data access (no card numbers), auth failures | 1 year |
| HIPAA | PHI access, disclosures, authentication | 6 years |
| GDPR | Consent, data subject requests, processing purposes | Duration + 3 years |

Compliance log format must include: who, what, when, from where, outcome.
Never log actual regulated data — log access events only.

## Anti-Patterns

❌ Over-alerting — Alerting on every metric spike creates noise; alert on user-visible symptoms only

❌ Missing correlation IDs — Logs without trace context can't be correlated to traces; always include trace_id/span_id

❌ Logging secrets — Even in DEBUG; use redaction filters in log pipeline

❌ Metric cardinality explosion — High-cardinality labels (user_id, request_id in Prometheus labels) cause OOM; use traces for high-cardinality data

❌ No runbook links — Alerts without runbooks cause confusion during incidents

❌ Single signal observability — Logs alone, or metrics alone, are insufficient; need logs + metrics + traces correlated

## Distributed Tracing — Implementation

Instrument services with OpenTelemetry to capture request flows across service boundaries, enabling diagnosis of latency and errors without code inspection.

### OpenTelemetry SDK Setup

#### TracerProvider and Span Processors

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# OTLP exporter (OpenTelemetry Collector)
otlp_exporter = OTLPSpanExporter(
    endpoint="otel-collector:4317",  # gRPC endpoint
    insecure=True
)

# Create TracerProvider
tracer_provider = TracerProvider()

# SimpleSpanProcessor: immediate export (low latency, high overhead)
# tracer_provider.add_span_processor(SimpleSpanProcessor(otlp_exporter))

# BatchSpanProcessor: batch export (high throughput, slight latency)
tracer_provider.add_span_processor(
    BatchSpanProcessor(
        otlp_exporter,
        max_queue_size=2048,
        max_export_batch_size=512,
        schedule_delay_millis=5000,  # Export every 5 seconds
    )
)

# Set as global tracer provider
trace.set_tracer_provider(tracer_provider)

# Get tracer for module
tracer = trace.get_tracer(__name__)
```

#### Alternative Exporters

```python
# Jaeger exporter (Jaeger backend)
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

# Zipkin exporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter

zipkin_exporter = ZipkinExporter(
    localip="127.0.0.1",
    port=9411,
    service_name="my-service"
)

# Cloud providers (AWS, GCP, Azure)
from opentelemetry.exporter.trace import in_memory_trace_exporter

memory_exporter = in_memory_trace_exporter.InMemoryTraceExporter()
```

### Instrumentation Patterns

#### Manual Span Creation

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)

async def process_order(order_id: str) -> dict:
    """Process order with manual instrumentation."""
    with tracer.start_as_current_span("process_order") as span:
        # Set span attributes (context about the operation)
        span.set_attribute("order.id", order_id)
        span.set_attribute("order.status", "processing")

        try:
            # Child span: validate
            with tracer.start_as_current_span("validate_order") as validate_span:
                validate_span.set_attribute("validation.type", "order_data")
                await validate_order(order_id)
                validate_span.add_event("validation_passed")

            # Child span: payment
            with tracer.start_as_current_span("charge_payment") as payment_span:
                payment_span.set_attribute("payment.method", "card")
                result = await charge_payment(order_id)
                payment_span.set_attribute("payment.status", result.status)
                payment_span.set_attribute("payment.amount", result.amount)

            # Child span: confirmation
            with tracer.start_as_current_span("send_confirmation") as confirm_span:
                await send_confirmation(order_id)
                confirm_span.add_event("email_sent", {"recipient": "customer@example.com"})

            span.set_attribute("order.status", "completed")
            span.set_status(Status(StatusCode.OK))
            return {"status": "success", "order_id": order_id}

        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
```

#### Auto-Instrumentation

```python
# Auto-instrumentation automatically wraps libraries
# Install instrumentation packages
# pip install opentelemetry-instrumentation-fastapi
# pip install opentelemetry-instrumentation-sqlalchemy
# pip install opentelemetry-instrumentation-requests

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from fastapi import FastAPI

app = FastAPI()

# Auto-instrument FastAPI (wraps all route handlers)
FastAPIInstrumentor.instrument_app(app)

# Auto-instrument database queries
SQLAlchemyInstrumentor().instrument()

# Auto-instrument HTTP requests
RequestsInstrumentor().instrument()

# Now all FastAPI routes, database queries, and HTTP requests are automatically traced
@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    # Automatically creates spans for:
    # - HTTP request entry
    # - Database query
    # - Response serialization
    return {"order_id": order_id, "status": "shipped"}
```

#### Span Attributes and Events

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)

def process_payment(order_id: str, amount: float) -> str:
    """Span with attributes and events."""
    with tracer.start_as_current_span("process_payment") as span:
        # Attributes: key-value pairs that describe the operation
        span.set_attribute("order.id", order_id)
        span.set_attribute("payment.amount", amount)
        span.set_attribute("payment.currency", "USD")
        span.set_attribute("payment.method", "card")

        try:
            # Call payment service
            response = call_payment_service(order_id, amount)

            # Events: timestamped logs within a span
            span.add_event("payment_api_called", {
                "api": "stripe",
                "latency_ms": response.latency,
                "status": response.status
            })

            if response.status == "approved":
                span.set_attribute("payment.status", "approved")
                span.add_event("payment_succeeded", {"transaction_id": response.tx_id})
                return response.tx_id

            else:
                span.set_attribute("payment.status", "declined")
                span.add_event("payment_declined", {"reason": response.reason})
                raise PaymentError(response.reason)

        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.add_event("payment_error", {"error_type": type(e).__name__})
            raise
```

### Context Propagation

#### W3C TraceContext (traceparent Header)

```python
from opentelemetry import trace
from opentelemetry.propagate import inject, extract
from opentelemetry.propagators.jaeger.jaeger import JaegerPropagator
from opentelemetry.propagators.textmap import TextMapPropagator
import httpx

tracer = trace.get_tracer(__name__)

# Propagate to downstream service
async def call_downstream_service(url: str, data: dict) -> dict:
    """Call downstream with trace context propagation."""
    headers = {}

    # Inject current trace context into headers
    # Automatically adds: traceparent, tracestate headers
    inject(headers)

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        return response.json()

# Receive from upstream service
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/process")
async def process_request(request: Request, data: dict):
    """Extract trace context from incoming request."""
    # Extract trace context from headers
    ctx = extract(dict(request.headers))

    # Set as current span context
    with trace.get_tracer(__name__).start_as_current_span(
        "process_request",
        context=ctx
    ) as span:
        span.set_attribute("request.method", request.method)
        return {"status": "processed"}
```

#### Baggage (Context Across Services)

```python
from opentelemetry.baggage import get_baggage, set_baggage

# Set baggage in parent service (e.g., user_id, tenant_id)
set_baggage("user_id", "user-123")
set_baggage("tenant_id", "acme-corp")

# Call downstream
response = call_downstream_service()

# Downstream service automatically receives baggage
# Baggage is automatically propagated in headers (W3C Baggage standard)

# In downstream service, extract baggage
user_id = get_baggage("user_id")  # "user-123"
tenant_id = get_baggage("tenant_id")  # "acme-corp"

# Use baggage in spans
with tracer.start_as_current_span("process_request") as span:
    span.set_attribute("user_id", user_id)
    span.set_attribute("tenant_id", tenant_id)
```

### Sampling Strategies

#### Head-Based Sampling (TraceIdRatioBased)

```python
from opentelemetry.sdk.trace.sampler import TraceIdRatioBased
from opentelemetry.sdk.trace import TracerProvider

# Sample 10% of all traces
sampler = TraceIdRatioBased(rate=0.1)

tracer_provider = TracerProvider(sampler=sampler)
trace.set_tracer_provider(tracer_provider)

# Trade-off: lose visibility into 90% of requests, reduce cost
```

#### ParentBased Sampler (Propagate Parent's Decision)

```python
from opentelemetry.sdk.trace.sampler import ParentBased, TraceIdRatioBased

# If parent was sampled, sample child. Otherwise, use local rate.
sampler = ParentBased(
    root=TraceIdRatioBased(0.1),  # Root spans: 10%
    local_parent_sampled=TraceIdRatioBased(1.0),  # Child of sampled: 100%
    local_parent_not_sampled=TraceIdRatioBased(0.0),  # Child of unsampled: 0%
)

tracer_provider = TracerProvider(sampler=sampler)
```

#### Tail-Based Sampling (Filter After Collection)

Tempo and OpenTelemetry Collector support tail-based sampling (see collector section).

### OpenTelemetry Collector Configuration

#### Pipeline: Receivers → Processors → Exporters

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

  jaeger:
    protocols:
      grpc:
        endpoint: 0.0.0.0:14250

processors:
  # Batch processor: reduce export overhead
  batch:
    send_batch_size: 512
    timeout: 5s

  # Sampling processor: drop spans based on rules
  sampling:
    policies:
      default:
        match_type: regexp
        regexp: '.*'
        sampling_percentage: 10
      high_traffic:
        match_type: regexp
        regexp: 'health_check.*'
        sampling_percentage: 0  # Drop all health checks
      errors:
        match_type: status_code
        status_code:
          status_codes: [ERROR]
        sampling_percentage: 100  # Sample all errors

  # Add attributes to all spans
  attributes:
    actions:
    - key: environment
      value: production
      action: insert
    - key: service.name
      from_attribute: service_name
      action: upsert

  # Memory limit processor
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128

exporters:
  otlp:
    endpoint: "tempo:4317"
    tls:
      insecure: true

  jaeger:
    endpoint: "jaeger:14250"
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp, jaeger]
      processors: [memory_limiter, attributes, batch]
      exporters: [otlp, jaeger]
```

### Trace Analysis

#### Critical Path Analysis

```python
# In Jaeger/Tempo UI:
# 1. Open trace
# 2. Look for longest-running spans (critical path)
# 3. Identify sequential vs parallel operations
# 4. Optimize sequential bottlenecks

# Example trace: process_order
# ├── validate_order: 50ms
# ├── charge_payment: 200ms (critical path)
# ├── send_confirmation: 100ms
# Optimize: parallelize send_confirmation with other spans
```

#### Identifying Slow Spans

```promql
# PromQL query to find slow operations
histogram_quantile(0.99, rate(traces_duration_seconds_bucket{operation_name="charge_payment"}[5m])) > 0.5
```

#### Error Propagation

```python
# Span with error
with tracer.start_as_current_span("process_order") as parent_span:
    try:
        with tracer.start_as_current_span("charge_payment") as child_span:
            raise PaymentError("Card declined")
    except Exception:
        # Error in child span propagates context to parent
        # Query: find all traces with charge_payment errors
        parent_span.record_exception(exception)
```

### Correlation with Logs

#### Inject Trace ID into Logs

```python
import structlog
from opentelemetry import trace

logger = structlog.get_logger()

async def process_order(order_id: str):
    """Logs automatically include trace_id."""
    # Get current trace ID
    span = trace.get_current_span()
    trace_id = span.get_span_context().trace_id
    span_id = span.get_span_context().span_id

    # Inject into structlog context
    structlog.contextvars.bind_contextvars(
        trace_id=f"0x{trace_id:032x}",
        span_id=f"0x{span_id:016x}"
    )

    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)

        logger.info("processing_started", order_id=order_id)
        # Log automatically includes: trace_id, span_id

        try:
            await validate_order(order_id)
            logger.info("order_validated")
        except Exception as e:
            logger.error("validation_failed", error=str(e))
            raise
```

#### Query Logs by Trace ID

```bash
# Loki query: find all logs for a trace
{trace_id="4bf92f3577b34da6a3ce929d0e0e4736"}

# Elasticsearch query
{
  "query": {
    "match": {
      "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
    }
  }
}
```

### Anti-Patterns (OTel-Specific)

```python
# ANTI-PATTERN 1: Tracing every SQL query in loops (N+1 spans)
for user_id in user_ids:  # 1000 users
    with tracer.start_as_current_span("fetch_user"):
        user = await db.fetch_user(user_id)
        # Creates 1000 spans! Trace becomes huge and slow.

# CORRECT: Single span for bulk operation
with tracer.start_as_current_span("fetch_all_users") as span:
    span.set_attribute("user.count", len(user_ids))
    users = await db.fetch_users_bulk(user_ids)

# ANTI-PATTERN 2: Missing root span
async def internal_helper():
    # No root span, context might be lost
    result = await downstream_service()
    return result

# CORRECT: Start root span for entry points
async def api_handler():
    with tracer.start_as_current_span("handle_request") as span:
        result = await internal_helper()
        return result

# ANTI-PATTERN 3: Not setting span.status on errors
try:
    await process()
except Exception as e:
    # Span status not set, looks like success in UI
    logger.error(str(e))

# CORRECT: Set status to ERROR
try:
    await process()
except Exception as e:
    span.record_exception(e)
    span.set_status(Status(StatusCode.ERROR))
    raise

# ANTI-PATTERN 4: Missing context propagation to async tasks
import asyncio

async def process_order(order_id: str):
    # Context lost in background task!
    asyncio.create_task(send_confirmation(order_id))

# CORRECT: Use copy_context() to preserve trace context
from contextvars import copy_context

async def process_order(order_id: str):
    ctx = copy_context()
    asyncio.create_task(ctx.run(send_confirmation, order_id))

# ANTI-PATTERN 5: High-cardinality span attributes
with tracer.start_as_current_span("http_request") as span:
    span.set_attribute("user_id", request.user_id)  # Millions of values!
    span.set_attribute("request_id", uuid.uuid4())  # Unique per request!
    # Each combination creates new metric series → cardinality explosion

# CORRECT: Use events for high-cardinality data
with tracer.start_as_current_span("http_request") as span:
    span.set_attribute("request.method", request.method)  # Bounded: [GET, POST, ...]
    span.add_event("user_request", {"user_id": request.user_id})  # Events are OK
```

## Agent Support

- Use `observability-engineer` agent for complex observability stack design
- Use `opentelemetry-expert` agent for deep OTel SDK/configuration questions
- Use `incident-responder` agent during active production incidents

## Skill References

- `metrics-stack` — Prometheus server config, PromQL, alerting rules, Grafana dashboards, and dashboard-as-code
- `python-observability` — Python-specific structured logging and OTel integration
