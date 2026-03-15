---
name: tdd-workflow
description: Use this skill when writing new features, fixing bugs, or refactoring code. Enforces test-driven development with 80%+ coverage including unit, integration, and E2E tests.
origin: ECC
---

# Test-Driven Development Workflow

This skill governs how all code changes are made — enforcement rules, the development cycle, test double strategy, and practical patterns.

## When to Activate

- Writing new features or functionality
- Fixing bugs or issues
- Refactoring existing code
- Adding API endpoints
- Creating new components

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

### Coverage Thresholds (example config)
```json
{
  "jest": {
    "coverageThresholds": {
      "global": {
        "branches": 80,
        "functions": 80,
        "lines": 80,
        "statements": 80
      }
    }
  }
}
```

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

### Step 1: Define Behavior as User Journeys
```
As a [role], I want to [action], so that [benefit]
```

### Step 2: Derive Test Cases from Each Journey

```typescript
describe('Semantic Search', () => {
  it('returns relevant markets for query', async () => {
    // Arrange-Act-Assert
  })

  it('handles empty query gracefully', async () => {
    // Edge case
  })

  it('falls back to substring search when Redis unavailable', async () => {
    // Fallback behavior
  })

  it('sorts results by similarity score', async () => {
    // Ordering logic
  })
})
```

### Step 3: RED — Run Tests, Confirm They Fail
```bash
npm test  # All new tests should fail
```

### Step 4: GREEN — Write Minimal Implementation
```typescript
export async function searchMarkets(query: string) {
  // Only enough code to pass the tests
}
```

### Step 5: Run Tests, Confirm They Pass
```bash
npm test  # All tests green
```

### Step 6: REFACTOR — Improve While Staying Green
- Remove duplication
- Improve naming
- Optimize performance
- Enhance readability

### Step 7: Verify Coverage
```bash
npm run test:coverage  # Verify 80%+ achieved
```

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

```
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   └── Button.test.tsx          # Unit tests
│   └── MarketCard/
│       ├── MarketCard.tsx
│       └── MarketCard.test.tsx
├── app/
│   └── api/
│       └── markets/
│           ├── route.ts
│           └── route.test.ts         # Integration tests
└── e2e/
    ├── markets.spec.ts               # E2E tests
    ├── trading.spec.ts
    └── auth.spec.ts
```

## Common Mistakes

### Test implementation details vs user-visible behavior
```typescript
// WRONG — testing internal state
expect(component.state.count).toBe(5)

// CORRECT — test what users see
expect(screen.getByText('Count: 5')).toBeInTheDocument()
```

### Brittle selectors vs semantic selectors
```typescript
// WRONG — breaks on CSS changes
await page.click('.css-class-xyz')

// CORRECT — resilient to restyling
await page.click('button:has-text("Submit")')
await page.click('[data-testid="submit-button"]')
```

### Coupled tests vs independent tests
```typescript
// WRONG — tests depend on execution order
test('creates user', () => { /* ... */ })
test('updates same user', () => { /* depends on previous test */ })

// CORRECT — each test owns its data
test('creates user', () => {
  const user = createTestUser()
  // ...
})
test('updates user', () => {
  const user = createTestUser()
  // ...
})
```

## Plan Execution

- **If you believe a plan step is unnecessary or already satisfied, state this explicitly and ask the user before skipping it.** Never silently omit a step from an approved plan.
- **Verification commands in a plan are mandatory.** Run them, show their output, and confirm they pass before declaring the task complete. Do not skip or defer verification steps.

## Continuous Testing

```bash
# Watch mode during development
npm test -- --watch

# Pre-commit hook
npm test && npm run lint
```

```yaml
# CI/CD (GitHub Actions)
- name: Run Tests
  run: npm test -- --coverage
- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

## Advanced TDD Schools

Brief overview of approaches — helps choose the right strategy:

- **London School (Mockist)**: Mock all collaborators at unit level. Maximises isolation, reveals design issues early. Risk: brittle tests that test implementation.
- **Chicago School (Classicist)**: Use real objects; mock only at trust boundaries (external services, DB, filesystem). Our default.
- **Outside-In TDD**: Start with E2E/acceptance test (failing), drive inward to unit tests. Good for new features.
- **Inside-Out TDD**: Build domain models first, surface API later. Good for complex domain logic.
- **ATDD (Acceptance TDD)**: Tests come from acceptance criteria in user stories.
- **BDD**: Gherkin syntax (Given-When-Then) for business-readable tests. Use with Cucumber/Jest-Cucumber when stakeholders write tests.

When to use which:
- Default: Chicago School (classicist) + outside-in for new features
- Complex domain logic: inside-out
- Stakeholder collaboration: BDD/ATDD

## Legacy Code Techniques

Making untested code testable without full rewrites:

- **Characterization Tests**: Write tests that document *current* behaviour before touching code. Commit them. Now you have a safety net.
- **Seams Model**: A seam is a place where you can change program behaviour without editing that code (constructor injection, interface extraction, virtual methods).
- **Golden Master Testing**: Capture full output from legacy code to a file. Run it as regression. Useful for rendering, reporting, or complex transformations.
- **Approval Testing**: Like golden master but with structured diff tools (ApprovalTests library).
- **Incremental Adoption**: (1) Characterise → (2) extract small piece → (3) write tests for extracted piece → (4) replace original with tested version → repeat.

Reference: Michael Feathers, "Working Effectively with Legacy Code"

## Multi-Language Support

The RED-GREEN-REFACTOR cycle is universal. Framework mapping:

| Language | Test Runner | Mocking | Coverage |
|----------|-------------|---------|----------|
| TypeScript/JS | Vitest / Jest | vi.fn() / jest.fn() | c8 / istanbul |
| Python | pytest | unittest.mock / pytest-mock | coverage.py |
| Java | JUnit 5 | Mockito | JaCoCo |
| C# | xUnit / NUnit | Moq | Coverlet |
| Go | testing/T | testify/mock | go test -cover |

Language-specific agents:
- Java: use `java-reviewer` agent (JUnit 5, Mockito, TestContainers)
- Python: use `python-reviewer` agent (pytest, fixtures, parametrize)
- TypeScript: use `vitest-expert` agent (vi.mock, MSW, testing-library)

## Test Metrics Beyond Coverage

80% line coverage is the floor, not the goal. Additional metrics:

- **Mutation Score**: Run Stryker (JS) or mutmut (Python) to validate test quality. Target >70% mutants killed. Coverage without mutation testing can hide weak tests.
- **Test Execution Speed**: Unit <5s, integration <30s, full suite <5min. Slow tests → fewer runs → less confidence.
- **Test Maintenance Ratio**: Lines of test code / lines of production code. >2:1 suggests over-specified tests (testing implementation, not behaviour).
- **Cycle Time**: Time from first failing test to green. Long cycles indicate insufficient decomposition.
- **Flake Rate**: Track intermittent failures. >1% flake rate degrades team trust. Fix or quarantine immediately.

Tools: `stryker-mutator` (JS/TS), `mutmut` (Python), `pitest` (Java), `codecov` (trends).

## Property-Based Testing

Generate hundreds of inputs automatically to find edge cases humans miss.

When to use: pure functions, parsers, serializers, mathematical operations, data transformations.

```typescript
// Vitest + fast-check example
import fc from "fast-check";

test("encode then decode is identity", () => {
  fc.assert(
    fc.property(fc.string(), (s) => {
      expect(decode(encode(s))).toBe(s);
    })
  );
});
```

```python
# pytest + hypothesis example
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_is_idempotent(xs):
    assert sorted(sorted(xs)) == sorted(xs)
```

Libraries: `fast-check` (TypeScript), `hypothesis` (Python), `junit-quickcheck` (Java).
