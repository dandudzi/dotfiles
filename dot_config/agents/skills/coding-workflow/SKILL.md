---
name: coding-workflow
description: Apply a test-first implementation workflow to repository code changes. Use when implementing features, fixing bugs, refactoring code, or otherwise changing executable behavior; do not use for read-only explanation, diagnosis, research, or review.
---

# Coding Workflow

Implement code changes through focused test evidence and the smallest practical change.

## Workflow

1. Read the applicable repository instructions. Inspect the implementation, nearby tests, and the project's documented test, lint, type-check, and build commands before editing.
2. Choose the highest practical test boundary that exercises the changed behavior. Prefer functional or end-to-end coverage over unit tests; reserve unit tests for edge cases that are impractical to cover at a higher level.
3. Establish pre-change evidence:
   - For a feature or bug fix, add or update the test first. Run it and confirm that it fails for the intended behavioral reason, not because of broken setup.
   - For a behavior-preserving refactor, run the relevant existing tests first. Add coverage before refactoring when they do not adequately protect the behavior; do not manufacture an artificial failure.
4. Implement only the smallest change needed to satisfy the requested behavior. Preserve unrelated behavior and avoid adjacent cleanup.
5. Re-run the focused tests until they pass. Then run the relevant broader test suite and any applicable lint, type-check, or build checks.
6. Report the behavioral coverage, the observed pre-change evidence, the final verification, and any unrelated pre-existing failures separately.

## Rules

- Minimize mocks. Exercise real behavior and integration boundaries whenever practical.
- Do not begin implementation without the applicable pre-change test evidence.
- If meaningful automated coverage is genuinely impractical, stop before implementation, explain the limitation and proposed substitute verification, and obtain the user's explicit waiver.
- Never weaken, delete, or bypass an existing test merely to make the implementation pass unless the requested behavior intentionally supersedes that assertion.
