---
name: event-sourcing
description: >
  Event sourcing patterns and infrastructure: aggregate design, domain event
  emission, snapshotting, schema evolution, idempotent handlers, and event
  store implementation (PostgreSQL, EventStoreDB, DynamoDB).
  Use when building event-sourced systems or choosing event store technology.
model: opus
---

# Event Sourcing

## When to Activate

Trigger on: "event sourcing", "event stream", "aggregate", "snapshots", "schema evolution", "event replay", "idempotent", "append-only", "event store".

## Aggregate Design

### Aggregate Boundary Checklist

- [ ] Aggregate encapsulates a consistency boundary (all invariants enforced within one aggregate)
- [ ] No cross-aggregate transactions (use sagas/process managers instead)
- [ ] Aggregate root is the only entry point (no direct access to child entities)
- [ ] Aggregate size: prefer small (1-5 entities); large aggregates = design smell

### Invariant Enforcement

```python
class Order:
    def add_item(self, item: OrderItem) -> None:
        # Enforce invariant before emitting event
        if self.status != OrderStatus.DRAFT:
            raise DomainError("Can only add items to draft orders")
        if self._total_after(item) > self.credit_limit:
            raise DomainError("Order exceeds credit limit")

        # Emit event (state change happens via event application)
        self._apply(OrderItemAdded(order_id=self.id, item=item))

    def _apply(self, event: DomainEvent) -> None:
        self._pending_events.append(event)
        self._handle(event)  # update in-memory state
```

### State-From-Events Reconstruction

```python
@classmethod
def from_events(cls, events: list[DomainEvent]) -> "Order":
    order = cls.__new__(cls)
    order._pending_events = []
    for event in events:
        order._handle(event)
    return order
```

## Domain Events

### Naming: Past tense verbs

Use `OrderPlaced`, `PaymentProcessed`, `ItemShipped` (not `OrderCreated` or `UpdateOrder`). Include aggregate type: `OrderItemAdded` not `ItemAdded`.

### Required Event Fields

```python
@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID          # globally unique, for idempotency
    aggregate_id: UUID      # which aggregate this belongs to
    aggregate_type: str     # "Order", "Payment", etc.
    version: int            # position within the aggregate stream
    occurred_at: datetime   # when the event happened (not stored_at)
    event_type: str         # "OrderPlaced", "PaymentProcessed"
    payload: dict           # event-specific data
```

### Emission Rules

Emit AFTER validating invariants. One command → one or more events. Events describe outcomes, not next actions.

## Snapshotting and Schema Evolution

### Snapshots

When: aggregate >500 events, reconstruction >100ms, high-frequency updates.

Format:

```python
@dataclass
class Snapshot:
    aggregate_id: UUID
    aggregate_type: str
    version: int            # event version AT TIME of snapshot
    state: dict             # full serialised state
    created_at: datetime
```

Rebuilding: Load snapshot + tail events after snapshot version. Snapshot every N events where N = (avg events/load) × 10. Never delete events.

### Schema Evolution: Versioning Strategies

| Strategy | How | When |
|----------|-----|------|
| **Weak schema** | Optional fields, ignore unknown fields | Additive changes only |
| **Upcasting** | Transform old events to new format on read | Field renames, structural changes |
| **Event splitting** | Old event type → two new event types | When one event means two things |
| **Copy-and-replace** | New event type, deprecate old | Breaking semantic changes |

Migration: Deploy new format writer first. Add upcaster (reads transparently convert). Background-migrate old events. Remove upcaster after migration.

## Idempotency

### Idempotency Keys

Every command must carry an idempotency key:

```python
@dataclass
class PlaceOrderCommand:
    idempotency_key: UUID   # client-generated, stable for retries
    order_details: OrderDetails
    customer_id: UUID
```

### Deduplication

Store each idempotency_key → result with 24h TTL. Return stored result if key exists.

### Delivery Guarantees

Use at-least-once + idempotent handlers (default). At-exactly-once requires distributed transactions or outbox pattern.

## Event Store Infrastructure

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Event Store                       │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Stream 1   │  │   Stream 2   │  │   Stream 3   │ │
│  │ (Aggregate)  │  │ (Aggregate)  │  │ (Aggregate)  │ │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤ │
│  │ Event 1     │  │ Event 1     │  │ Event 1     │ │
│  │ Event 2     │  │ Event 2     │  │ Event 2     │ │
│  │ Event 3     │  │ ...         │  │ Event 3     │ │
│  │ ...         │  │             │  │ Event 4     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────┤
│  Global Position: 1 → 2 → 3 → 4 → 5 → 6 → ...     │
└─────────────────────────────────────────────────────┘
```

### Event Store Requirements

| Requirement       | Description                        |
| ----------------- | ---------------------------------- |
| **Append-only**   | Events are immutable, only appends |
| **Ordered**       | Per-stream and global ordering     |
| **Versioned**     | Optimistic concurrency control     |
| **Subscriptions** | Real-time event notifications      |
| **Idempotent**    | Handle duplicate writes safely     |

### Technology Comparison

| Technology       | Best For                  | Limitations                      |
| ---------------- | ------------------------- | -------------------------------- |
| **EventStoreDB** | Pure event sourcing       | Single-purpose                   |
| **PostgreSQL**   | Existing Postgres stack   | Manual implementation            |
| **Kafka**        | High-throughput streaming | Not ideal for per-stream queries |
| **DynamoDB**     | Serverless, AWS-native    | Query limitations                |
| **Marten**       | .NET ecosystems           | .NET specific                    |

### PostgreSQL Schema

```sql
CREATE TABLE events (
    id UUID PRIMARY KEY, stream_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL, event_data JSONB NOT NULL,
    version BIGINT NOT NULL, global_position BIGSERIAL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_stream_version UNIQUE (stream_id, version)
);
CREATE INDEX idx_events_stream_id ON events(stream_id, version);
CREATE INDEX idx_events_global_position ON events(global_position);

CREATE TABLE snapshots (
    stream_id VARCHAR(255) PRIMARY KEY, snapshot_data JSONB NOT NULL,
    version BIGINT NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE subscription_checkpoints (
    subscription_id VARCHAR(255) PRIMARY KEY,
    last_position BIGINT NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### PostgreSQL Implementation (Python)

```python
class EventStore:
    async def append_events(self, stream_id: str, events, expected_version=None):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                if expected_version is not None:
                    current = await conn.fetchval(
                        "SELECT COALESCE(MAX(version), 0) FROM events WHERE stream_id = $1",
                        stream_id
                    )
                    if current != expected_version:
                        raise ConcurrencyError(f"Expected {expected_version}, got {current}")

                for i, event in enumerate(events):
                    await conn.execute(
                        "INSERT INTO events (stream_id, event_type, event_data, version) VALUES ($1, $2, $3, $4)",
                        stream_id, event.type, json.dumps(event.data), expected_version + i
                    )
        return events

    async def read_stream(self, stream_id: str, from_version: int = 0, limit: int = 1000):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM events WHERE stream_id = $1 AND version >= $2 ORDER BY version LIMIT $3",
                stream_id, from_version, limit
            )
```

### EventStoreDB Usage

```python
from esdbclient import EventStoreDBClient, NewEvent, StreamState

client = EventStoreDBClient(uri="esdb://localhost:2113?tls=false")

# Append with optimistic concurrency
new_events = [NewEvent(type=e['type'], data=json.dumps(e['data']).encode()) for e in events]
client.append_to_stream(stream_name, events=new_events, current_version=expected_revision)

# Read stream; subscribe with checkpoint
events = client.get_stream(stream_name, stream_position=from_revision)
subscription = client.subscribe_to_all(commit_position=from_position)
```

### DynamoDB: Use PK=STREAM#{id}, SK=VERSION#{n} with GSI for global ordering.

## Testing Patterns

### Given/When/Then Style

```python
def test_order_item_added():
    # Given: an order in DRAFT status
    order = Order.from_events([
        OrderCreated(order_id=ORDER_ID, customer_id=CUSTOMER_ID),
    ])

    # When: adding an item
    order.add_item(OrderItem(product_id=PRODUCT_ID, quantity=2))

    # Then: an OrderItemAdded event was emitted
    assert len(order.pending_events) == 1
    event = order.pending_events[0]
    assert isinstance(event, OrderItemAdded)
    assert event.product_id == PRODUCT_ID
```

### Projection Testing

```python
def test_order_total_projection():
    events = [
        OrderCreated(order_id=ORDER_ID),
        OrderItemAdded(product_id=P1, quantity=2, unit_price=1000),
        OrderItemAdded(product_id=P2, quantity=1, unit_price=500),
    ]

    projection = OrderTotalProjection()
    for event in events:
        projection.handle(event)

    assert projection.get_total(ORDER_ID) == 2500
```

## Anti-Patterns

❌ Event sourcing everything — Use only for aggregates where history matters or audit required.
❌ Mutable events — Never update/delete; use compensating events instead.
❌ Large aggregates — >50 fields or >10 child entities signals design problem.
❌ Missing idempotency — Handlers must be idempotent; same event processed twice = same result.
❌ Tight coupling via events — Events are self-contained; projections don't call back into aggregates.
❌ Large payloads — Keep events small and focused.
❌ Skip concurrency control — Optimistic versioning prevents data corruption.
❌ Ignore backpressure — Handle slow consumers gracefully.

## Related Skills

`cqrs-implementation`, `domain-driven-design`, `ddd-tactical-patterns`, `saga-orchestration`
