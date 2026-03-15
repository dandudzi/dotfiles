---
name: ddd-context-mapping
description: >
  DDD context mapping: analyze bounded context pairs, select relationship
  patterns (partnership, customer/supplier, ACL, conformist), assess coupling
  risk, and design integration strategies. Use when defining how services
  or bounded contexts communicate and depend on each other.
---

## When to Activate

Trigger on phrases like:
- "context map", "context mapping"
- "anti-corruption layer", "ACL", "integration pattern"
- "upstream downstream", "context relationship"
- "how should service A talk to service B"
- "shared kernel", "conformist", "open host service"
- "coupling between services", "service integration strategy"

## Context Pair Analysis Process

For each pair of bounded contexts that need to interact:

### Step 1: Establish Direction

- Which context needs data/behavior FROM the other?
- Could either context exist without the other?
- Is the dependency one-way or bidirectional?

Asymmetric dependency: Customer/Supplier or Conformist
Symmetric dependency: Partnership or Shared Kernel
No dependency needed: design the integration away

### Step 2: Assess Power Balance

- **Upstream has power**: Can change model without asking downstream; downstream must adapt
- **Downstream has power**: Can negotiate contract (customer/supplier)
- **Equal**: Partnership — must coordinate changes

### Step 3: Assess Model Compatibility

- Same language, same concepts: Shared Kernel or Conformist
- Similar concepts, different names: Conformist with light mapping
- Fundamentally different models: Anti-Corruption Layer required
- External/legacy system: ACL always recommended

## Relationship Pattern Reference

### Partnership
Two contexts succeed or fail together; tight alignment is appropriate.
- Coordination: joint planning, synchronized releases
- Risk: deployment coupling, coordination overhead

### Shared Kernel
Both contexts share a small, stable subset of the model.
- Keep ruthlessly small — only concepts with genuine shared meaning
- Changes require both teams to agree
- Anti-pattern: using shared kernel for convenience

### Customer/Supplier
Clear dependency direction; downstream can influence upstream's roadmap.
- Downstream is a "customer" — submits requirements, upstream prioritizes them
- Downstream may add ACL if upstream model is messy

### Anti-Corruption Layer (ACL)
Translates between external/legacy model and your internal domain model.

```java
// Keeps external types isolated; domain types propagate inward
public class StripePaymentACL {
    public PaymentResult translate(StripePaymentIntent intent) {
        return new PaymentResult(
            PaymentId.of(intent.getId()),
            mapStatus(intent.getStatus()),
            Money.of(intent.getAmount(), intent.getCurrency())
        );
    }
}
```

Use when: integrating third-party APIs, legacy systems, or hostile upstream models.

### Open Host Service / Published Language
One context serves many consumers via versioned, well-documented protocol.
- Maintain backward compatibility across versions
- Consumers can add their own ACL if needed

### Conformist
Downstream adopts upstream model without translation.
- Cost: zero translation layer
- Risk: tight coupling — upstream changes break downstream
- Acceptable when upstream model is clean and stable

## Coupling Risk Assessment

Rate each context pair (1=low, 5=high):

| Risk Factor | Questions | Weight |
|-------------|-----------|--------|
| Change frequency | How often does upstream change its API/model? | 30% |
| Blast radius | If upstream breaks, how many consumers affected? | 25% |
| Model impedance | How different are the two models? | 25% |
| Team alignment | Do teams coordinate well? | 20% |

Score 1-2: Conformist or Customer/Supplier acceptable
Score 3: Customer/Supplier with lightweight ACL
Score 4-5: Full ACL required; consider event-driven decoupling

## Integration Strategy

### Synchronous vs Asynchronous

| Factor | Synchronous REST/gRPC | Asynchronous Events |
|--------|----------------------|---------------------|
| Coupling | Temporal + behavioral | Temporal decoupling |
| Complexity | Low | Higher (eventual consistency) |
| Failure mode | Cascading failures | Consumer can lag |
| Use for | Queries, strong consistency | State changes, notifications |

### Event-Driven Integration

```
[Orders] publishes: OrderPlaced, OrderCancelled
[Inventory] subscribes to: OrderPlaced (reserve stock), OrderCancelled (release)
[Fulfillment] subscribes to: StockReserved (begin picking)
```

Each context translates incoming events through its own ACL.

## Context Map Template

```
[Auth Service] --(OHS/Published Language)--> [Orders] (ACL)
[Auth Service] --(OHS)--> [Inventory] (conformist)
[Orders] --(OHS)--> [Fulfillment] (ACL)
[Orders] --(events)--> [Inventory]
[Orders] --(customer/supplier)--> [Billing]
[Payment Gateway (external)] --(ACL in Orders)--> [Orders]
```

## Integration with DDD Skill Ecosystem

- **domain-driven-design**: Entry point; routes here after strategic design
- **ddd-strategic-design**: Defines bounded contexts being mapped
- **ddd-tactical-patterns**: Aggregates and domain events within each context
- **event-sourcing**: Event schema for event-driven context integration
- **microservices-patterns**: Deployment and resilience for context integrations
