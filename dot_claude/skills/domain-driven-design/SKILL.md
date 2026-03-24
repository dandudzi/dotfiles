---
name: domain-driven-design
description: >
  DDD viability check and routing skill. Evaluates whether DDD is appropriate
  for a domain and routes to strategic, tactical, or event-driven sub-skills.
  Use when designing complex business domains.
model: opus
---

# Domain-Driven Design

## When to Activate

Trigger on: "DDD", "domain model", "bounded context", "ubiquitous language", "aggregate", "domain-driven", "domain design", "bounded contexts", "context map".

## DDD Viability Check

Before applying DDD, evaluate at least 2 of these 4 criteria:

| Criterion | Signal | Example |
|-----------|--------|---------|
| Domain complexity | Business rules that can't be expressed as simple CRUD | Loan origination, insurance underwriting |
| Team size | 3+ developers; coordination needed | Multiple squads per domain |
| Long-term ownership | System expected to evolve for 3+ years | Core business platform |
| Rapid change frequency | Business rules change often | Pricing engine, compliance rules |

**Skip DDD if**: Simple CRUD, <3 developers, short-lived project, well-understood domain with stable rules.

### Quick Decision
```
Is your domain logic just CRUD + validation?
  YES → Use simple layered architecture (no DDD overhead)
  NO  → Does it meet ≥2 viability criteria above?
          YES → Proceed with DDD routing below
          NO  → Consider lightweight DDD (ubiquitous language + repositories only)
```

## Three-Stage Routing

### Stage 1 — Strategic Design
**Use when**: Starting a new domain, defining team boundaries, unclear where services should split.

Invoke: `ddd-strategic-design` skill

Output: Subdomain map, bounded context diagram, ubiquitous language glossary, context map.

### Stage 2 — Tactical Patterns
**Use when**: Strategic design is done; implementing aggregates, value objects, domain events.

Invoke: `ddd-tactical-patterns` skill

Output: Aggregate classes, value object types, domain event definitions, repository interfaces.

### Stage 3 — Event-Driven Architecture
**Use when**: Bounded contexts need to communicate asynchronously, or historical state replay is needed.

Invoke: `event-sourcing` skill + `cqrs-implementation` skill

Output: Event store schema, command/query segregation, projection design, saga patterns.

### Cross-Cutting
- Context integration patterns → `ddd-context-mapping` skill
- Distributed transactions across aggregates → `saga-orchestration` skill

## Glossary Template

For each bounded context, maintain a ubiquitous language glossary:

```markdown
## Ubiquitous Language: [Context Name]

| Term | Definition | Anti-Terms | Used In Code As |
|------|-----------|------------|-----------------|
| Order | A customer's confirmed purchase intent | Cart, Basket (use only outside this context) | `Order` class |
| Line Item | A single product+quantity within an Order | Product line, SKU row | `OrderLineItem` |
| Fulfil | To physically ship goods for an Order | Ship, Dispatch (too generic) | `Order.fulfil()` |
```

Rules:
- Code identifiers MUST match glossary terms (no abbreviations)
- Anti-terms must NOT appear in this context's code
- Resolve naming conflicts between contexts explicitly (don't merge)

## DDD Anti-Patterns

❌ **Anemic domain model** — Entities are just data bags; all logic in service classes
- Fix: Move invariant enforcement and business rules into aggregate methods

❌ **Premature bounded context split** — Splitting into separate services before understanding the domain
- Fix: Start with a monolith, identify natural seams, extract only when team/complexity justifies

❌ **Shared database across contexts** — Two bounded contexts reading the same table directly
- Fix: Each context owns its data; use events or APIs for cross-context data needs

❌ **God context** — One bounded context handles everything
- Fix: Apply subdomain classification to identify natural splits

## Agent Support

- Use `architect` agent for overall system architecture decisions
- Use `database-architect` agent for aggregate-to-schema mapping decisions
