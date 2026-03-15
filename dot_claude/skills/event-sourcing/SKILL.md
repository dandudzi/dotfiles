---
name: event-sourcing
description: >
  Event sourcing patterns and infrastructure: aggregate design, domain event
  emission, snapshotting, schema evolution, idempotent handlers, and event
  store implementation (PostgreSQL, EventStoreDB, DynamoDB).
  Use when building event-sourced systems or choosing event store technology.
---

# Event Sourcing

## When to Activate

Trigger on: "event sourcing", "event stream", "aggregate", "snapshots", "schema evolution", "event replay", "event-sourced", "idempotent handler", "append-only", "event store".

Also trigger when:
- Designing event sourcing infrastructure
- Choosing between event store technologies
- Implementing custom event stores
- Optimizing event storage and retrieval
- Setting up event store schemas
- Planning for event store scaling

## Part 1: Aggregate Design

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

## Domain Event Patterns

### Naming Conventions

- Past tense verbs: `OrderPlaced`, `PaymentProcessed`, `ItemShipped`
- Avoid: `OrderCreated` (too generic), `UpdateOrder` (command, not event)
- Include aggregate type: `OrderItemAdded` not just `ItemAdded`

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

- Emit events AFTER validating invariants, BEFORE persisting
- One command → one or more events (usually one)
- Events describe what happened, not what to do next
- Never emit events from read-only operations

## Part 2: Snapshotting and Schema Evolution

### Snapshotting Strategy

#### When to Snapshot

- Aggregate has accumulated >500 events
- Reconstruction latency is noticeable (>100ms to rebuild)
- Aggregate has periods of high-frequency updates

#### Snapshot Format

```python
@dataclass
class Snapshot:
    aggregate_id: UUID
    aggregate_type: str
    version: int            # event version AT TIME of snapshot
    state: dict             # full serialised state
    created_at: datetime
```

#### Rebuilding from Snapshot + Tail

```python
def load_aggregate(aggregate_id: UUID) -> Order:
    snapshot = store.get_latest_snapshot(aggregate_id)

    if snapshot:
        order = Order.from_snapshot(snapshot.state)
        # Load only events AFTER the snapshot
        events = store.get_events(aggregate_id, after_version=snapshot.version)
    else:
        events = store.get_events(aggregate_id)
        order = Order.from_events(events)

    for event in events:
        order._handle(event)

    return order
```

#### Snapshot Frequency

- Rule of thumb: snapshot every N events where N = (avg events per load) × 10
- Never delete events after snapshotting — snapshots are a performance optimisation, not a replacement

### Schema Evolution

#### Versioning Strategies

| Strategy | How | When |
|----------|-----|------|
| **Weak schema** | Optional fields, ignore unknown fields | Additive changes only |
| **Upcasting** | Transform old events to new format on read | Field renames, structural changes |
| **Event splitting** | Old event type → two new event types | When one event means two things |
| **Copy-and-replace** | New event type, deprecate old | Breaking semantic changes |

#### Upcasting Example

```python
class OrderPlacedUpcaster:
    """Transforms v1 OrderPlaced to v2 format on read."""

    def can_upcast(self, event: dict) -> bool:
        return event["event_type"] == "OrderPlaced" and event.get("schema_version", 1) == 1

    def upcast(self, event: dict) -> dict:
        # v1 had flat customer fields; v2 nests them
        return {
            **event,
            "schema_version": 2,
            "payload": {
                **event["payload"],
                "customer": {
                    "id": event["payload"].pop("customer_id"),
                    "email": event["payload"].pop("customer_email"),
                }
            }
        }
```

#### Migration Runbook

1. Deploy new code that writes new event format (but still reads old)
2. Verify new events are written correctly in staging
3. Add upcaster for old events (reads transparently convert)
4. Deploy to production
5. (Optional) Background migration of old events to new format
6. After all old events migrated, remove upcaster

## Part 3: Idempotency

### Idempotency Keys

Every command must carry an idempotency key:

```python
@dataclass
class PlaceOrderCommand:
    idempotency_key: UUID   # client-generated, stable for retries
    order_details: OrderDetails
    customer_id: UUID
```

### Deduplication Store

```python
class IdempotencyStore:
    def check_and_set(self, key: UUID, result: dict) -> tuple[bool, dict]:
        """Returns (is_duplicate, result).
        If duplicate, returns stored result. If new, stores and returns result."""
        if existing := self.store.get(str(key)):
            return True, existing
        self.store.set(str(key), result, ttl=86400)  # 24h TTL
        return False, result
```

### At-Least-Once vs Exactly-Once

| Pattern | Guarantee | Implementation |
|---------|-----------|----------------|
| At-least-once | Event delivered ≥1 time | Simple; handler must be idempotent |
| Exactly-once | Event delivered exactly 1 time | Requires distributed transactions or outbox pattern |
| Idempotent consumer | At-least-once + idempotent handler | Recommended default |

## Part 4: Event Store Infrastructure

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

### PostgreSQL Event Store Schema

```sql
-- Events table
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id VARCHAR(255) NOT NULL,
    stream_type VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    event_data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    version BIGINT NOT NULL,
    global_position BIGSERIAL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_stream_version UNIQUE (stream_id, version)
);

-- Index for stream queries
CREATE INDEX idx_events_stream_id ON events(stream_id, version);

-- Index for global subscription
CREATE INDEX idx_events_global_position ON events(global_position);

-- Index for event type queries
CREATE INDEX idx_events_event_type ON events(event_type);

-- Index for time-based queries
CREATE INDEX idx_events_created_at ON events(created_at);

-- Snapshots table
CREATE TABLE snapshots (
    stream_id VARCHAR(255) PRIMARY KEY,
    stream_type VARCHAR(255) NOT NULL,
    snapshot_data JSONB NOT NULL,
    version BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscriptions checkpoint table
CREATE TABLE subscription_checkpoints (
    subscription_id VARCHAR(255) PRIMARY KEY,
    last_position BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Python EventStore Implementation

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, List
from uuid import UUID, uuid4
import json
import asyncpg

@dataclass
class Event:
    stream_id: str
    event_type: str
    data: dict
    metadata: dict = field(default_factory=dict)
    event_id: UUID = field(default_factory=uuid4)
    version: Optional[int] = None
    global_position: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class EventStore:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def append_events(
        self,
        stream_id: str,
        stream_type: str,
        events: List[Event],
        expected_version: Optional[int] = None
    ) -> List[Event]:
        """Append events to a stream with optimistic concurrency."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Check expected version
                if expected_version is not None:
                    current = await conn.fetchval(
                        "SELECT MAX(version) FROM events WHERE stream_id = $1",
                        stream_id
                    )
                    current = current or 0
                    if current != expected_version:
                        raise ConcurrencyError(
                            f"Expected version {expected_version}, got {current}"
                        )

                # Get starting version
                start_version = await conn.fetchval(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM events WHERE stream_id = $1",
                    stream_id
                )

                # Insert events
                saved_events = []
                for i, event in enumerate(events):
                    event.version = start_version + i
                    row = await conn.fetchrow(
                        """
                        INSERT INTO events (id, stream_id, stream_type, event_type,
                                          event_data, metadata, version, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        RETURNING global_position
                        """,
                        event.event_id,
                        stream_id,
                        stream_type,
                        event.event_type,
                        json.dumps(event.data),
                        json.dumps(event.metadata),
                        event.version,
                        event.created_at
                    )
                    event.global_position = row['global_position']
                    saved_events.append(event)

                return saved_events

    async def read_stream(
        self,
        stream_id: str,
        from_version: int = 0,
        limit: int = 1000
    ) -> List[Event]:
        """Read events from a stream."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, stream_id, event_type, event_data, metadata,
                       version, global_position, created_at
                FROM events
                WHERE stream_id = $1 AND version >= $2
                ORDER BY version
                LIMIT $3
                """,
                stream_id, from_version, limit
            )
            return [self._row_to_event(row) for row in rows]

    async def read_all(
        self,
        from_position: int = 0,
        limit: int = 1000
    ) -> List[Event]:
        """Read all events globally."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, stream_id, event_type, event_data, metadata,
                       version, global_position, created_at
                FROM events
                WHERE global_position > $1
                ORDER BY global_position
                LIMIT $2
                """,
                from_position, limit
            )
            return [self._row_to_event(row) for row in rows]

    async def subscribe(
        self,
        subscription_id: str,
        handler,
        from_position: int = 0,
        batch_size: int = 100
    ):
        """Subscribe to all events from a position."""
        # Get checkpoint
        async with self.pool.acquire() as conn:
            checkpoint = await conn.fetchval(
                """
                SELECT last_position FROM subscription_checkpoints
                WHERE subscription_id = $1
                """,
                subscription_id
            )
            position = checkpoint or from_position

        while True:
            events = await self.read_all(position, batch_size)
            if not events:
                await asyncio.sleep(1)  # Poll interval
                continue

            for event in events:
                await handler(event)
                position = event.global_position

            # Save checkpoint
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO subscription_checkpoints (subscription_id, last_position)
                    VALUES ($1, $2)
                    ON CONFLICT (subscription_id)
                    DO UPDATE SET last_position = $2, updated_at = NOW()
                    """,
                    subscription_id, position
                )

    def _row_to_event(self, row) -> Event:
        return Event(
            event_id=row['id'],
            stream_id=row['stream_id'],
            event_type=row['event_type'],
            data=json.loads(row['event_data']),
            metadata=json.loads(row['metadata']),
            version=row['version'],
            global_position=row['global_position'],
            created_at=row['created_at']
        )


class ConcurrencyError(Exception):
    """Raised when optimistic concurrency check fails."""
    pass
```

### EventStoreDB Usage

```python
from esdbclient import EventStoreDBClient, NewEvent, StreamState
import json

# Connect
client = EventStoreDBClient(uri="esdb://localhost:2113?tls=false")

# Append events
def append_events(stream_name: str, events: list, expected_revision=None):
    new_events = [
        NewEvent(
            type=event['type'],
            data=json.dumps(event['data']).encode(),
            metadata=json.dumps(event.get('metadata', {})).encode()
        )
        for event in events
    ]

    if expected_revision is None:
        state = StreamState.ANY
    elif expected_revision == -1:
        state = StreamState.NO_STREAM
    else:
        state = expected_revision

    return client.append_to_stream(
        stream_name=stream_name,
        events=new_events,
        current_version=state
    )

# Read stream
def read_stream(stream_name: str, from_revision: int = 0):
    events = client.get_stream(
        stream_name=stream_name,
        stream_position=from_revision
    )
    return [
        {
            'type': event.type,
            'data': json.loads(event.data),
            'metadata': json.loads(event.metadata) if event.metadata else {},
            'stream_position': event.stream_position,
            'commit_position': event.commit_position
        }
        for event in events
    ]

# Subscribe to all
async def subscribe_to_all(handler, from_position: int = 0):
    subscription = client.subscribe_to_all(commit_position=from_position)
    async for event in subscription:
        await handler({
            'type': event.type,
            'data': json.loads(event.data),
            'stream_id': event.stream_name,
            'position': event.commit_position
        })

# Category projection ($ce-Category)
def read_category(category: str):
    """Read all events for a category using system projection."""
    return read_stream(f"$ce-{category}")
```

### DynamoDB Event Store

```python
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import json
import uuid

class DynamoEventStore:
    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def append_events(self, stream_id: str, events: list, expected_version: int = None):
        """Append events with conditional write for concurrency."""
        with self.table.batch_writer() as batch:
            for i, event in enumerate(events):
                version = (expected_version or 0) + i + 1
                item = {
                    'PK': f"STREAM#{stream_id}",
                    'SK': f"VERSION#{version:020d}",
                    'GSI1PK': 'EVENTS',
                    'GSI1SK': datetime.utcnow().isoformat(),
                    'event_id': str(uuid.uuid4()),
                    'stream_id': stream_id,
                    'event_type': event['type'],
                    'event_data': json.dumps(event['data']),
                    'version': version,
                    'created_at': datetime.utcnow().isoformat()
                }
                batch.put_item(Item=item)
        return events

    def read_stream(self, stream_id: str, from_version: int = 0):
        """Read events from a stream."""
        response = self.table.query(
            KeyConditionExpression=Key('PK').eq(f"STREAM#{stream_id}") &
                                  Key('SK').gte(f"VERSION#{from_version:020d}")
        )
        return [
            {
                'event_type': item['event_type'],
                'data': json.loads(item['event_data']),
                'version': item['version']
            }
            for item in response['Items']
        ]

# Table definition (CloudFormation/Terraform)
"""
DynamoDB Table:
  - PK (Partition Key): String
  - SK (Sort Key): String
  - GSI1PK, GSI1SK for global ordering

Capacity: On-demand or provisioned based on throughput needs
"""
```

## Part 5: Testing Patterns

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

❌ Event sourcing everything — Not every aggregate needs event sourcing; use it for aggregates where history matters or audit is required

❌ Mutable events — Events are immutable facts; never update or delete events (use compensating events instead)

❌ Large aggregates — Aggregates with 50+ fields or 10+ child entities are too large; split them

❌ Missing idempotency — Handlers that process the same event twice must produce the same result; ensure all projections/handlers are idempotent

❌ Tight coupling via events — Events should be self-contained; projections should not call back into aggregates

❌ Don't update or delete events — They're immutable facts

❌ Don't store large payloads — Keep events small

❌ Don't skip optimistic concurrency — Prevents data corruption

❌ Don't ignore backpressure — Handle slow consumers

## Agent Support

- Use `architect` agent for complex event sourcing design decisions
- Use `database-architect` agent for event store technology selection
- Use `saga-orchestration` skill for cross-aggregate workflow coordination

## Skill References

- `cqrs-implementation` — command/query separation paired with event sourcing
- `domain-driven-design` — entry point for DDD routing
- `ddd-tactical-patterns` — aggregate and domain event implementation details
- `ddd-strategic-design` — strategic DDD patterns for bounded contexts
- `ddd-context-mapping` — context mapping and integration patterns
- `saga-orchestration` — distributed transaction coordination
