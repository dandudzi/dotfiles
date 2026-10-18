---
name: architecture-change
description: Plan architectural changes for a requested implementation, including component boundaries, dependencies, contracts, and migration. Use for the architectural changes section of coding-workflow plans or a standalone architecture-change plan.
---

# Architecture Change

Describe the structural decisions needed to implement the requested behavior. This skill produces a plan; it does not implement changes or authorize additional work.

## Establish context

- Use the task requirements and existing discovery evidence. Inspect relevant source, architecture decisions, and `CONTEXT.md` when present; distinguish observed structure from assumptions.
- Identify the affected components, their responsibilities, dependency direction, and external contracts. Follow existing domain language and repository conventions.
- Obtain the destination plan or section from the caller. When called by `coding-workflow`, populate its architectural changes section without replacing the acceptance tests or other sections.

## Choose the change

- Describe the current structure and the proposed structure, citing relevant files or symbols. Explain which requirement makes the structural change necessary.
- Prefer the smallest change that satisfies the requirements. Reuse established boundaries and abstractions unless there is evidence that they prevent the requested behavior.
- State who owns each changed responsibility, which components may depend on which others, and how data or control crosses the affected boundaries.
- Record changes to public APIs, events, persistence schemas, or integration contracts when applicable. Explain compatibility, migration order, and rollback constraints for changes that affect existing consumers or stored data.
- Consider alternatives only when there is a meaningful tradeoff. Record the chosen option and why it fits the constraints; keep speculative redesign outside the proposed scope.
- If no structural change is needed, explicitly say so and identify the existing boundary that supports the implementation. Do not invent an architectural change to fill the section.

## Write the plan section

Keep the section proportional to the change. Include:

1. **Current structure and constraint:** affected components and the limitation relevant to the request.
2. **Proposed structure:** responsibility, dependency, and contract changes, with a brief rationale.
3. **Compatibility and rollout:** migration, deployment ordering, and recovery considerations when applicable; otherwise state that none are required.
4. **Verification:** reference the acceptance tests or checks that demonstrate the new boundaries and preserve affected contracts. Keep detailed test requirements in the caller's test section.

Use a small Mermaid diagram only when it clarifies boundaries or interactions better than prose. Mark unresolved decisions and explain whether they block implementation. Do not present an unverified assumption as a settled decision.

Return the section to the caller or update the requested plan file when writing it is authorized. Follow the caller's approval process; creating this section does not approve implementation.
