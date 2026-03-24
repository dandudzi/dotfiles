---
name: ddd-tactical-patterns
description: >
  DDD tactical patterns: invariant-first aggregate design, immutable value
  objects, domain event emission, repository patterns, and domain service
  boundaries. Use when implementing business logic within a bounded context.
model: opus
---

## When to Activate

Trigger on phrases like:
- "aggregate", "aggregate root", "entity", "value object"
- "domain event", "emit event", "event-driven domain"
- "invariant", "business rule enforcement"
- "repository pattern DDD", "domain repository"
- "tactical DDD", "implement domain model"

## Aggregates

An aggregate is a cluster of domain objects treated as a single unit with a clearly defined boundary and a single root entity.

### Invariant-First Design

Design aggregates around invariants (rules that must always be true), not data relationships.

1. List all business invariants: "Order must have at least one item", "Cannot add items to a confirmed order"
2. Group objects that must enforce invariants together
3. Identify the aggregate root (entry point; enforces all invariants)

### Aggregate Rules

- **Small aggregates**: Aim for 1-4 entities; large aggregates cause contention
- **Reference by ID**: Never hold object references to other aggregates — use IDs only
- **Transactional boundary**: One aggregate per transaction; use sagas for cross-aggregate consistency
- **Protect invariants**: All state changes go through aggregate root methods; no direct property mutation

### Java Implementation Pattern

```java
public class Order {
    private final OrderId id;
    private final CustomerId customerId;
    private final List<LineItem> lineItems = new ArrayList<>();
    private OrderStatus status = OrderStatus.PENDING;
    private final List<DomainEvent> events = new ArrayList<>();

    public static Order place(CustomerId customerId, List<LineItemRequest> items) {
        if (items == null || items.isEmpty()) {
            throw new DomainException("Order must have at least one item");
        }
        var order = new Order(OrderId.generate(), customerId);
        items.forEach(req -> order.lineItems.add(LineItem.from(req)));
        order.events.add(new OrderPlaced(order.id, customerId, Instant.now()));
        return order;
    }

    public void confirm() {
        if (status != OrderStatus.PENDING) {
            throw new DomainException("Only pending orders can be confirmed");
        }
        this.status = OrderStatus.CONFIRMED;
        this.events.add(new OrderConfirmed(this.id, Instant.now()));
    }

    public List<DomainEvent> releaseEvents() {
        var released = List.copyOf(events);
        events.clear();
        return released;
    }
}
```

## Value Objects

Immutable objects defined entirely by their attributes (no identity).

### When to Use Value Objects

- Measurements: Money, Distance, Weight
- Identifiers: OrderId, CustomerId (wrap primitives for type safety)
- Descriptive concepts: Address, EmailAddress, PhoneNumber
- Date/time ranges: DateRange, TimeSlot

### Value Object Pattern

```java
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        Objects.requireNonNull(amount, "amount required");
        Objects.requireNonNull(currency, "currency required");
        if (amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new DomainException("Money cannot be negative");
        }
        amount = amount.setScale(2, RoundingMode.HALF_UP);
    }

    public Money add(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new DomainException("Cannot add different currencies");
        }
        return new Money(this.amount.add(other.amount), this.currency);
    }
}
```

## Domain Events

Facts about something that happened in the domain.

### Domain Event Rules

- Named in past tense: OrderPlaced, PaymentFailed, CustomerDeactivated
- Immutable: events are facts — never modify them after creation
- Rich payload: include all data consumers need; avoid requiring lookups
- Raised by aggregate root

### Event Pattern

```java
public record OrderPlaced(
    OrderId orderId,
    CustomerId customerId,
    Money total,
    Instant occurredAt
) implements DomainEvent {}
```

### Publishing Pattern

Aggregates collect events; publish after successful persistence:

```java
// In application service after saving aggregate:
var events = order.releaseEvents();
eventPublisher.publishAll(events);
```

## Repositories

### Repository Rules

- One repository per aggregate root (not per entity)
- Interface defined in domain layer; implementation in infrastructure layer
- Returns fully reconstituted aggregates (not lazy-loaded fragments)
- Only aggregate-root-level operations (no querying by child entity ID)

### Repository Pattern

```java
// Domain layer - interface only
public interface OrderRepository {
    Optional<Order> findById(OrderId id);
    void save(Order order);
    void delete(OrderId id);
}
```

## Domain Services

Use when business logic doesn't belong to a single aggregate:
- Operation involves multiple aggregates
- Calculation requires domain knowledge but no identity
- Complex coordination spanning entities

```java
// Domain service - pure domain logic, no infrastructure dependencies
public class PricingService {
    public Money calculateTotal(Order order, CustomerTier tier) {
        var base = order.subtotal();
        var discount = discountPolicy.calculate(tier, base);
        return base.subtract(discount);
    }
}
```

## Integration with DDD Skill Ecosystem

- **domain-driven-design**: Entry point and viability check; routes here for implementation
- **ddd-strategic-design**: Bounded context boundaries that contain these aggregates
- **ddd-context-mapping**: How aggregates in different contexts communicate
- **event-sourcing**: Persisting domain events as the storage model
