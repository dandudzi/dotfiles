---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---
# TypeScript/JavaScript Testing

> This file extends [common/testing.md](../common/testing.md) with TypeScript/JavaScript specific content.

## Unit Testing

Use **Vitest** for all new projects. Use **Jest** only for legacy codebases that already use it.

```typescript
import { describe, it, expect, vi } from 'vitest'

describe('calculateTotal', () => {
  it('applies discount to subtotal', () => {
    expect(calculateTotal(100, 0.1)).toBe(90)
  })
})
```

## Mocking

- **Module mocks**: Use `vi.mock()` / `jest.mock()` for internal dependencies
- **API mocks**: Use **MSW** (Mock Service Worker) for HTTP requests — avoid mocking fetch/axios directly
- **Timer mocks**: Use `vi.useFakeTimers()` for debounce, throttle, and timeout tests

```typescript
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

const server = setupServer(
  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({ id: params.id, name: 'Test User' })
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

## Test File Organization

```
src/
├── utils/
│   ├── format.ts
│   └── format.test.ts      # Co-located unit tests
├── __tests__/
│   └── integration/         # Integration tests in dedicated folder
└── e2e/
    └── checkout.spec.ts     # Playwright E2E tests
```

- Co-locate unit tests next to source files (`*.test.ts`)
- Group integration tests in `__tests__/integration/`
- Group E2E tests in `e2e/` with `*.spec.ts` extension

## E2E Testing

Use **Playwright** as the E2E testing framework for critical user flows.

## Mocking Strategy

- **Unit tests:** Use `vi.mock()` for internal module dependencies
- **HTTP requests:** Use **MSW** (Mock Service Worker) — never mock fetch/axios directly
- **Timers:** Use `vi.useFakeTimers()` for debounce, throttle, timeout tests

> **Vitest forks pool limitation:** When using `--pool=forks`, `process.nextTick` mocking is not supported. Use `--pool=threads` or explicitly exclude `'nextTick'` from the `toFake` option: `vi.useFakeTimers({ toFake: ['setTimeout', 'setInterval'] })`

## Agent Support

- **vitest-expert** — Vitest configuration, patterns, and mocking
- **playwright-expert** — Playwright E2E testing

## Skill Reference

- `e2e-testing` skill — Playwright patterns, Page Object Model, CI/CD integration
- `tdd-workflow` skill — TDD enforcement and coverage requirements
