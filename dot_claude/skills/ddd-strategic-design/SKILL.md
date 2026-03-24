---
name: ddd-strategic-design
description: >
  DDD strategic design patterns: subdomain classification, bounded context
  definition, ubiquitous language glossary, and context relationships.
  Use when mapping business domains, defining service boundaries, or
  establishing shared language between technical and business stakeholders.
model: opus
---

## When to Activate

Trigger on phrases like:
- "define bounded context", "map the domain", "identify subdomains"
- "core domain", "supporting domain", "generic subdomain"
- "ubiquitous language", "domain glossary"
- "context map", "anti-corruption layer", "shared kernel"
- "strategic DDD", "domain boundaries"

## Subdomain Classification

Every domain area falls into one of three categories:

### Core Domain
The competitive differentiator — where your business wins or loses.
- **Characteristics**: high complexity, unique to your business, high value
- **Investment**: your best engineers, maximum attention, most rigorous design
- **Examples**: pricing algorithm, recommendation engine, fraud detection
- **DDD intensity**: FULL — aggregates, value objects, domain events, rich model

### Supporting Subdomain
Necessary but not differentiating.
- **Characteristics**: business-specific but not competitive, moderate complexity
- **Investment**: solid engineering, but not your A-team
- **Examples**: reporting, notifications, user profile management
- **DDD intensity**: SELECTIVE — use DDD where complexity warrants it

### Generic Subdomain
Commodity functionality — buy or use OSS.
- **Characteristics**: well-understood, solved by existing software, low complexity
- **Investment**: minimal — integrate, don't build
- **Examples**: email sending, authentication, payment processing, file storage
- **DDD intensity**: NONE — delegate to SaaS/OSS

### Classification Decision Matrix

Is this where we win in the market?
  YES: Core Domain (full DDD)
  NO: Is the logic specific to our business?
    YES: Supporting Domain (selective DDD)
    NO: Generic Domain (buy/use OSS)

## Bounded Context Definition

A bounded context is the explicit boundary within which a domain model applies.

### Boundary Identification Process

1. **Find language boundaries** — where does the same word mean different things?
   - "Order" in sales vs. fulfillment vs. billing
   - Different meanings = different bounded contexts

2. **Find team boundaries** — one team owns one context
   - Avoid shared ownership; it creates coordination overhead

3. **Find data consistency boundaries** — what must be consistent together?
   - Strongly consistent data = likely same context
   - Eventually consistent data = likely different contexts

4. **Find rate-of-change boundaries** — things that change together belong together

### Bounded Context Checklist

- [ ] One team owns this context
- [ ] The model within is internally consistent
- [ ] Terms have single, unambiguous meanings inside the boundary
- [ ] External concepts enter only through translation (ACL or published events)
- [ ] Context has a clear, named responsibility

### Context Size Guidelines

Too large: multiple teams, internal terminology conflicts, deploy cycle conflicts, 10+ aggregates with cross-dependencies
Too small: one class or table, no domain logic, pure CRUD, every operation crosses the boundary

## Ubiquitous Language

The shared vocabulary used by both domain experts and developers within a bounded context.

### Building the Glossary

For each key term, capture:
- **Definition**: one precise sentence
- **Synonyms to avoid**: standardise on one name
- **Context**: which bounded context this belongs to
- **Attributes**: key properties
- **Behaviour**: what it can do / what happens to it
- **Invariants**: rules that must always hold
- **Related terms**: links to other glossary entries

### Language Hygiene Rules

- No synonyms inside a context — pick one word, use it everywhere
- Code = language — class/method/variable names must match the glossary
- Evolve together — when domain experts change terminology, update code too
- Explicit translation at boundaries — never let terms bleed across contexts

## Context Relationships

### Relationship Patterns

**Partnership**: Two teams coordinate changes together. Use when tight coupling is acceptable.

**Shared Kernel**: Share a small, explicitly agreed-upon model subset. Keep it minimal and stable.

**Customer/Supplier (Upstream/Downstream)**: Upstream sets the terms. Downstream uses ACL if upstream is messy.

**Anti-Corruption Layer (ACL)**: Translation layer insulating your model from external or legacy models. Use when integrating third-party APIs or hostile upstream models.

**Open Host Service / Published Language**: Upstream exposes a versioned, well-documented protocol for multiple downstreams.

**Conformist**: Downstream adopts upstream's model without translation. Warning: creates tight coupling.

### Context Map Template

    [Sales] --(OHS/Published Language)--> [Inventory] (downstream, ACL)
    [Sales] --(OHS)--> [Fulfillment] (downstream, conformist)
    [Fulfillment] <--(partnership)--> [Shipping]
    [Billing] --(customer/supplier)--> [Accounting]
    [All contexts] --> [Auth Service] (generic, conformist)

## Strategic Design Deliverables

1. **Subdomain map** — classified list of all domain areas (core/supporting/generic)
2. **Bounded context list** — named contexts with responsibilities and team ownership
3. **Ubiquitous language glossary** — per-context term definitions
4. **Context map** — relationships and integration patterns between contexts

## Integration with Other DDD Skills

- **domain-driven-design** — viability check and entry point; routes here for strategic work
- **ddd-tactical-patterns** — aggregate design, value objects, domain events within a context
- **ddd-context-mapping** — deeper analysis of specific context pairs and coupling risk
- **event-sourcing** — event-driven integration between bounded contexts
