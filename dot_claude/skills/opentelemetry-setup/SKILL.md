---
name: opentelemetry-setup
description: >
  OpenTelemetry SDK instrumentation for Python and Node.js, including tracers, exporters,
  processors, sampling strategies, and context propagation. Use when setting up tracing
  in applications or migrating from vendor-specific instrumentation.
model: sonnet
---

# OpenTelemetry Setup

Trigger on: "OpenTelemetry", "OTel", "tracing", "distributed tracing", "instrumentation", "trace export".

## Tracing Fundamentals

Traces capture request flows across service boundaries. Each trace is a tree of **spans** (individual operations).

```
User Request
└── root span: http_request [0-500ms]
    ├── validate_order [50-100ms]
    ├── charge_payment [100-300ms]
    └── send_confirmation [300-400ms]
```

Span contains: name, start/end time, attributes (key-value), events (timestamped logs), status, exceptions.

## Python Instrumentation

### Manual Span Creation

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import Status, StatusCode

# Setup exporter and provider
otlp_exporter = OTLPSpanExporter(endpoint="otel-collector:4317", insecure=True)
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

# Instrument a business operation
async def process_order(order_id: str) -> dict:
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        try:
            # Nested span: validate
            with tracer.start_as_current_span("validate_order") as validate_span:
                validate_span.set_attribute("validation.type", "order_data")
                await validate_order(order_id)
                validate_span.add_event("validation_passed")

            # Nested span: payment
            with tracer.start_as_current_span("charge_payment") as payment_span:
                payment_span.set_attribute("payment.method", "card")
                result = await charge_payment(order_id)
                payment_span.set_attribute("payment.status", result.status)
                payment_span.add_event("payment_success", {"tx_id": result.tx_id})

            span.set_status(Status(StatusCode.OK))
            return {"status": "success", "order_id": order_id}
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
```

### Auto-Instrumentation (Python)

Auto-instrumentation wraps libraries without code changes.

```python
# Install: pip install opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-sqlalchemy

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from fastapi import FastAPI

app = FastAPI()

# Auto-instrument all FastAPI routes, database queries, HTTP requests
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument()
RequestsInstrumentor().instrument()

# Routes automatically traced — no manual span creation needed
@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    return await db.fetch_order(order_id)
```

## Node.js Instrumentation

### SDK Setup

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({ url: 'http://otel-collector:4317' }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
process.on('SIGTERM', () => sdk.shutdown());
```

### Manual Spans (TypeScript)

```typescript
import { trace } from '@opentelemetry/api';
import { SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('payment-service');

async function processOrder(orderId: string): Promise<any> {
  const span = tracer.startSpan('process_order');
  span.setAttribute('order.id', orderId);

  try {
    const payment = await tracer.startActiveSpan('charge_payment', async (paymentSpan) => {
      paymentSpan.setAttribute('payment.method', 'card');
      const result = await chargePayment(orderId);
      paymentSpan.addEvent('payment_success', { tx_id: result.txId });
      return result;
    });

    span.setStatus({ code: SpanStatusCode.OK });
    return { status: 'success', orderId };
  } catch (e) {
    span.recordException(e as Error);
    span.setStatus({ code: SpanStatusCode.ERROR, message: (e as Error).message });
    throw e;
  } finally {
    span.end();
  }
}
```

## Exporters

Direct exporter selection based on backend:

```python
# OTLP (OpenTelemetry Collector — recommended)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
exporter = OTLPSpanExporter(endpoint="otel-collector:4317", insecure=True)

# Jaeger (direct)
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
exporter = JaegerExporter(agent_host_name="localhost", agent_port=6831)

# Zipkin (direct)
from opentelemetry.exporter.zipkin.json import ZipkinExporter
exporter = ZipkinExporter(localip="127.0.0.1", port=9411, service_name="my-service")

# Cloud providers: AWS X-Ray, GCP Trace, Azure Monitor (use provider SDKs)
```

## Processors

Processors batch, filter, and transform spans before export.

```python
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, BatchSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

# SimpleSpanProcessor: export immediately (low latency, high overhead)
tracer_provider.add_span_processor(SimpleSpanProcessor(otlp_exporter))

# BatchSpanProcessor: export in batches every 5 seconds (recommended for production)
tracer_provider.add_span_processor(BatchSpanProcessor(
    otlp_exporter,
    max_queue_size=2048,
    max_export_batch_size=512,
    schedule_delay_millis=5000
))
```

## Sampling Strategies

### Head-Based Sampling

```python
from opentelemetry.sdk.trace.sampler import TraceIdRatioBased

# Sample 10% of all traces (decide at trace start)
sampler = TraceIdRatioBased(rate=0.1)
tracer_provider = TracerProvider(sampler=sampler)

# Trade-off: 90% blind spots, reduced cost
```

### Parent-Based Sampling

```python
from opentelemetry.sdk.trace.sampler import ParentBased, TraceIdRatioBased

# Propagate parent's decision; root spans use local rate
sampler = ParentBased(
    root=TraceIdRatioBased(0.1),  # Root: 10%
    local_parent_sampled=TraceIdRatioBased(1.0),  # Child of sampled: 100%
    local_parent_not_sampled=TraceIdRatioBased(0.0)  # Child of unsampled: 0%
)
tracer_provider = TracerProvider(sampler=sampler)
```

### Tail-Based Sampling

Decide after collection (requires OTel Collector).

```yaml
processors:
  sampling:
    policies:
      errors:
        match_type: status_code
        status_codes: [ERROR]
        sampling_percentage: 100  # Always sample errors
      health_checks:
        match_type: regexp
        regexp: 'health_check.*'
        sampling_percentage: 0  # Drop all health checks
      default:
        sampling_percentage: 10  # Everything else: 10%
```

## Context Propagation

### W3C TraceContext (HTTP Headers)

```python
from opentelemetry.propagate import inject, extract
import httpx

# Outbound: inject current trace context into headers
async def call_downstream(url: str, data: dict) -> dict:
    headers = {}
    inject(headers)  # Adds traceparent, tracestate headers
    async with httpx.AsyncClient() as client:
        return await client.post(url, json=data, headers=headers)

# Inbound: extract trace context from headers
from fastapi import Request
from opentelemetry import trace

@app.post("/process")
async def process_request(request: Request, data: dict):
    ctx = extract(dict(request.headers))
    with trace.get_tracer(__name__).start_as_current_span("process", context=ctx) as span:
        return {"status": "processed"}
```

### Baggage (Cross-Service Context)

```python
from opentelemetry.baggage import set_baggage, get_baggage

# Parent: set baggage
set_baggage("user_id", "user-123")
set_baggage("tenant_id", "acme-corp")

# Child: baggage auto-propagated in headers
user_id = get_baggage("user_id")  # "user-123"
with tracer.start_as_current_span("request") as span:
    span.set_attribute("user_id", user_id)
```

## OTel Collector Configuration

### Minimal Pipeline

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    send_batch_size: 512
    timeout: 5s
  memory_limiter:
    check_interval: 1s
    limit_mib: 512

exporters:
  otlp:
    endpoint: tempo:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp]
```

## Anti-Patterns

❌ **N+1 spans in loops**: Creating span per item in bulk operation. Consolidate to one span with count attribute.

❌ **Missing root span**: Child spans may lose context. Always start root span at entry point.

❌ **Not setting span status**: Errors invisible in UI. Call `span.set_status(ERROR)` on exception.

❌ **High-cardinality attributes**: `user_id`, `request_id` in span attributes cause cardinality explosion. Use events for unbounded data.

❌ **Missing context propagation to async tasks**: Background tasks lose trace context. Use `contextvars.copy_context()` before `asyncio.create_task()`.
