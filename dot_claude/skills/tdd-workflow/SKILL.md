---
name: tdd-workflow
description: Use this skill when writing new features, fixing bugs, or refactoring code. Enforces test-driven development with 80%+ coverage including unit, integration, and E2E tests.
origin: ECC
model: sonnet
---

# Test-Driven Development Workflow

## When to Activate

- Writing new features or functionality
- Fixing bugs or issues
- Refactoring existing code

## The TDD Cycle

Every change requires a failing test first. No exceptions.

### RED → GREEN → REFACTOR

1. **RED** — Write a test for the behavior. Run it. Confirm it fails for the right reason.
2. **GREEN** — Write the minimal production code to make it pass. Run tests. Confirm it passes.
3. **REFACTOR** — Clean up while keeping tests green.

### Enforcement Rules

- No production code without a prior failing test
- The test must fail before you write implementation code — if it passes immediately, it tests nothing
- After implementation, run the test and confirm it passes
- Bug fixes also require a failing test that reproduces the bug first
- **If an implementation plan defers tests to the end, do NOT follow that ordering** — reorder to write each test before its corresponding production code. The plan defines WHAT to build; TDD defines HOW.
- When executing a plan, **actually run** the failing test and show its output before writing production code — don't just describe that you will
- When removing a feature, first update/remove the tests that assert the old behavior, then remove the implementation
- **Stop and ask for help if changes cascade.** If a change breaks many existing tests and the only way to make them pass is to restructure or rearchitect the codebase to support one additional flow, STOP immediately. Do not attempt the rearchitecture autonomously. Present the situation to the user: what broke, how many tests failed, and why an architectural change appears necessary. Let the user decide whether to proceed, simplify the requirement, or take a different approach.

### TDD Exemptions (closed list)

These do NOT require a prior failing test:

- Dependency version bumps (`pom.xml`, `package.json`)
- Docker/compose config, `.gitignore`, CI/CD config
- OpenAPI/Swagger annotation-only changes (no runtime behavior)
- Pure file moves/renames where existing tests verify behavior before and after

**This list is closed.** You may NOT self-authorize new exemptions. If you believe a situation requires skipping TDD, state this explicitly and ask the user before proceeding.

**If a project has no test runner or test files for the affected code,** state this explicitly to the user. Do not silently skip TDD — ask whether to add a test framework or proceed without tests.

For all exemptions: run the existing test suite after the change to confirm no regressions.

## Coverage Requirements

- Minimum 80% code coverage (unit + integration + E2E combined)
- All edge cases covered
- Error scenarios tested
- Boundary conditions verified


## Test Double Strategy

**Never mock what you can use for real.** Prefer the highest-fidelity test double available:

1. **Real infrastructure first** — If the project has test containers, in-memory databases, or similar test infra, use them. Write integration tests that hit real databases over unit tests that stub repositories.
2. **Mock only at trust boundaries** — External HTTP services (OAuth providers, third-party APIs), cross-module ports in hexagonal/DDD architecture, and things you genuinely cannot run locally.
3. **Integration tests must go full-stack** — Do NOT mock application services in controller/endpoint integration tests. Let requests flow through the real service → repository → database. Only mock external adapters.
4. **When a mock IS appropriate**, prefer the narrowest scope: mock the specific port/adapter, not the entire service.

### Acceptable Mocks

- External API clients (OAuth2, payment gateways, email services)
- Cross-module ports that enforce bounded-context isolation
- Time, randomness, and other non-deterministic sources

### Not Acceptable (when real infra exists)

- Repositories / data-access layers when a test database is available
- Application services in integration tests
- Domain services that have no external dependencies

### Mock Examples (for trust-boundary cases only)

Use these patterns ONLY when real infrastructure is unavailable or the dependency is a genuine external service:

```typescript
// External API — acceptable to mock (trust boundary)
jest.mock('@/lib/openai', () => ({
  generateEmbedding: jest.fn(() => Promise.resolve(
    new Array(1536).fill(0.1)
  ))
}))

// External cache service — acceptable when no test Redis available
jest.mock('@/lib/redis', () => ({
  searchMarketsByVector: jest.fn(() => Promise.resolve([
    { slug: 'test-market', similarity_score: 0.95 }
  ])),
  checkRedisHealth: jest.fn(() => Promise.resolve({ connected: true }))
}))
```

## Practical Workflow

1. **RED** — Write test(s) for desired behavior (happy path, edge cases, errors). Run. Confirm failure.
2. **GREEN** — Write minimal production code to pass tests. Run. Confirm all pass.
3. **REFACTOR** — Improve while keeping tests green (remove duplication, improve naming, optimize).
4. **Verify** — Check coverage ≥80%+. Run full suite. Commit.

## Test Types

### Unit Tests
- Individual functions and utilities
- Component rendering logic
- Pure functions and helpers
- Test in isolation, fast feedback

### Integration Tests
- API endpoints (full request → response)
- Database operations (real DB or test containers)
- Service interactions (real dependencies, mocked boundaries)
- Let requests flow through real service layers

### E2E Tests
- Critical user flows end-to-end
- Browser automation via Playwright or similar
- Complete workflows across UI and API

## Testing Patterns

### Unit Test (Jest/Vitest)
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from './Button'

describe('Button Component', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})
```

### API Integration Test
```typescript
import { NextRequest } from 'next/server'
import { GET } from './route'

describe('GET /api/markets', () => {
  it('returns markets successfully', async () => {
    const request = new NextRequest('http://localhost/api/markets')
    const response = await GET(request)
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data.success).toBe(true)
    expect(Array.isArray(data.data)).toBe(true)
  })

  it('validates query parameters', async () => {
    const request = new NextRequest('http://localhost/api/markets?limit=invalid')
    const response = await GET(request)
    expect(response.status).toBe(400)
  })
})
```

### E2E Test (Playwright)
```typescript
import { test, expect } from '@playwright/test'

test('user can search and filter markets', async ({ page }) => {
  await page.goto('/')
  await page.click('a[href="/markets"]')
  await expect(page.locator('h1')).toContainText('Markets')

  await page.fill('input[placeholder="Search markets"]', 'election')
  await page.waitForTimeout(600)

  const results = page.locator('[data-testid="market-card"]')
  await expect(results).toHaveCount(5, { timeout: 5000 })
  await expect(results.first()).toContainText('election', { ignoreCase: true })
})
```

## Test File Organization

Unit tests co-located with source files (`Component.test.tsx`). Integration tests in `app/api/`. E2E tests in `e2e/`.

## Common Mistakes

- **Test implementation, not behavior** — Test what users see (rendered output, API responses), not internal state.
- **Brittle selectors** — Use `data-testid` and semantic queries; avoid CSS class names.
- **Coupled tests** — Each test owns its data; never rely on execution order.

## Plan Execution

- **If you believe a plan step is unnecessary or already satisfied, state this explicitly and ask the user before skipping it.** Never silently omit a step from an approved plan.
- **Verification commands in a plan are mandatory.** Run them, show their output, and confirm they pass before declaring the task complete. Do not skip or defer verification steps.

## Continuous Testing

Run tests in watch mode during development. Run full suite with coverage in CI/CD before merge.

## TDD Schools

| School | Approach | When to Use |
|--------|----------|------------|
| **Chicago (Classicist)** | Real objects; mock only at boundaries | Default; our standard |
| **London (Mockist)** | Mock all collaborators | Reveals design issues early; risk: brittle tests |
| **Outside-In** | E2E test → drive inward | New features |
| **Inside-Out** | Domain models → API surface | Complex domain logic |
| **BDD** | Gherkin (Given-When-Then) | Stakeholder collaboration |

## Legacy Code Techniques

- **Characterization Tests**: Write tests documenting current behavior before refactoring. Commit. Now you have a safety net.
- **Seams Model**: Extract seams (inject dependencies) to enable testing without full rewrites.
- **Golden Master Testing**: Capture baseline output, use as regression test for large transformations.
- **Incremental Adoption**: Characterize → extract → test extracted piece → replace → repeat.

## Multi-Language Support

| Language | Test Runner | Framework |
|----------|-------------|-----------|
| TypeScript/JS | Vitest / Jest | vi.fn() / jest.fn() |
| Python | pytest | unittest.mock / pytest-mock |
| Java | JUnit 5 | Mockito / TestContainers |
| C# | xUnit / NUnit | Moq |
| Go | testing/T | testify/mock |

## Test Metrics Beyond Coverage

- **Mutation Score**: >70% mutants killed (stryker, mutmut, pitest)
- **Speed**: Unit <5s, integration <30s, full suite <5min
- **Flake Rate**: <1%; fix or quarantine intermittent failures immediately

## Property-Based Testing

Generate hundreds of inputs to find edge cases. Use for: pure functions, parsers, serializers, transformations.

Libraries: `fast-check` (TypeScript), `hypothesis` (Python), `junit-quickcheck` (Java).

## Eval-Driven TDD

Integrate eval-driven development into TDD flow for AI/ML features:

1. Define capability + regression evals before implementation
2. Run baseline and capture failure signatures
3. Implement minimum passing change
4. Re-run tests and evals; report pass@1 and pass@3

Release-critical paths should target pass@3 stability before merge.
