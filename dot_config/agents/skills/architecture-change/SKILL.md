---
name: architecture-change
description: Use when plan requires bigger changes than small changes like new DDD components, changes to model, domain, scheme or API.
---

- This skill only produce output if one of the listed changes are required to accomplish plan. Print only proposed change, no narrative.

List for new or changed:

1. API - print new version of the API.
2. Model - print new state variables.
3. Scheme - print table/document scheme.
4. Events - print scheme.

List only if new:

1. New DDD files like. For them prints simplified tree. Do not print test files. New:
   1.1. Model
   1.2. Entity
   1.3. Aggregate
   1.4. Repository
   1.5. Service
   1.6. Bounded Context
   1.7. Policy/Specification
   1.8. Action, Consumer, Command, Query
   1.9. Module
   1.10. Auth roles or Permissions
   1.11. Configuration
   1.12. Contracts
2. Create diagram for new life cycle with triggers.
  - Use plain-text diagrams in a fenced text block.
  - Use Unicode arrows and branches: →, ▼, ├──, └──, │.
  - Keep each line within 80 characters.
  - Prefer top-to-bottom flow with short labels.
  - Show the main flow first.
  - Put recovery, reset, and shared transitions in separate sections.
  - Split large diagrams into small, related blocks.
  - Preserve every state, condition, transition, and side effect.
  - Define any grouped state, such as “Any open state.”
  - Do not use Mermaid unless the user requests it or the renderer supports it.
  - Print the diagram directly. Do not provide only rendering instructions.
3. When extending already existing API, interfaces or services. Print new function names.
