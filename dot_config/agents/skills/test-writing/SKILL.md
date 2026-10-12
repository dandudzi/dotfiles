---
name: test-writing
description: Design, write, and run automated tests for requested behavior, bug regressions, missing coverage, or behavior-preserving refactors. Use when adding or improving tests; a read-only test review does not authorize writing them.
---

# Test Writing

Write tests that distinguish correct behavior from a plausible defect. Use
`coding-workflow` for repository changes; this skill supplies test design and
verification guidance within that workflow.

## Discover the Test Surface

- Inspect repository instructions, nearby tests, runner configuration, and CI
  commands. Reuse the existing framework, fixtures, and naming conventions.
- Check installed runner versions and local help before choosing flags. Use
  Context7 for version-aware framework documentation when needed.
- Identify the public entry point and observable outcome: response, rendered
  state, persisted data, emitted event, or documented error.
- Run the relevant existing tests before editing. Record baseline failures
  separately from failures introduced by the new tests.

## Common Operations

- **Regression test:** reproduce the reported trigger through a real entry
  point and assert the intended outcome. Confirm the unfixed code fails that
  assertion, rather than failing because of missing dependencies or bad setup.
- **Missing coverage:** map the requested acceptance criteria to scenarios.
  Cover the successful path and relevant boundaries or failure paths without
  inventing new product requirements.
- **Refactor coverage:** capture externally observable behavior with passing
  tests before restructuring code. Keep tests independent of private methods
  and internal layout so they survive a behavior-preserving refactor.

## Choose Meaningful Scenarios

- Prefer functional, integration, or end-to-end tests when they exercise the
  behavior reliably. Use unit tests for precise edge cases that are impractical
  to reach at that level.
- Derive expected results from requirements, contracts, or independently
  calculated examples. Do not compute the expected value with the same helper
  being tested or copy its implementation into the test.
- Choose cases that expose plausible mistakes: an excluded boundary, incorrect
  ordering, lost persistence, duplicate handling, or a relevant error path.
  Include only cases supported by the requested behavior.
- Assert effects that matter to the caller. A successful exit, mocked call,
  snapshot, or coverage percentage alone may not establish correctness.
- Keep real internal logic and integration boundaries where practical. Stub
  external services, clocks, or randomness only at the boundary that needs
  control; make assertions about resulting behavior rather than mock mechanics.

## Make Tests Reliable

- Isolate mutable state using the repository's test database, transactions,
  temporary directories, or per-test resources. Clean up resources owned by
  the test and avoid dependence on execution order.
- Use fixed clocks, seeded randomness, and stable fixtures when those values
  affect assertions. Wait for an observable condition in asynchronous tests
  instead of relying on arbitrary sleeps.
- Keep each test's failure diagnostic: name the scenario, make setup readable,
  and assert the relevant values or state. Parameterize cases when their setup
  and expected behavior share the same structure.

## Verify and Report

Run the new tests, then the relevant existing suite and required checks. For a
test written before a fix, report the expected behavioral failure. For passing
coverage, inspect which plausible defect its assertions would detect; when
uncertain, verify with a temporary local fault and restore it before delivery.

Report the scenarios covered, exact commands and outcomes, baseline failures,
and any material behavior that remains unverified. A request limited to writing
tests does not authorize fixing production code or changing product behavior.
