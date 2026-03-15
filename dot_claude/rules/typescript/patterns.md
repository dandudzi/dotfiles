---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---
# TypeScript/JavaScript Patterns

> This file extends [common/patterns.md](../common/patterns.md) with TypeScript/JavaScript specific content.

## API Response Format

> **Canonical definition:** See `api-design-principles` skill for the full API response envelope with structured error objects. The simplified form below is for quick reference.

```typescript
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: unknown
  }
  meta?: {
    total: number
    page: number
    limit: number
  }
}
```

## Result Pattern (Typed Errors)

Avoid throwing for expected failures — return typed results instead:

```typescript
type Result<T, E = string> =
  | { ok: true; value: T }
  | { ok: false; error: E }

function parseConfig(raw: string): Result<Config, 'invalid_json' | 'missing_field'> {
  try {
    const parsed = JSON.parse(raw)
    if (!parsed.host) return { ok: false, error: 'missing_field' }
    return { ok: true, value: parsed as Config }
  } catch {
    return { ok: false, error: 'invalid_json' }
  }
}
```

> **Production projects:** Consider the [`neverthrow`](https://github.com/supermacro/neverthrow) library — zero dependencies, exhaustive Result/ResultAsync types, async support, and pipeline chaining. It is the production-standard library for this pattern in 2025.

## Discriminated Unions

Model state machines and variants with a shared `kind`/`type` discriminant:

```typescript
type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: string }

function renderState(state: AsyncState<User>) {
  switch (state.status) {
    case 'idle':    return null
    case 'loading': return <Spinner />
    case 'success': return <UserCard user={state.data} />
    case 'error':   return <ErrorBanner message={state.error} />
  }
}
```

## Branded Types

Prevent accidental misuse of structurally identical primitives:

```typescript
type UserId = string & { readonly __brand: 'UserId' }
type OrderId = string & { readonly __brand: 'OrderId' }

function createUserId(id: string): UserId {
  return id as UserId
}

function getUser(id: UserId): Promise<User> { /* ... */ }

// getUser(orderId) — compile error: OrderId is not assignable to UserId
```

## Server Actions with useActionState (Next.js 15 / React 19)

Use `useActionState` for form state management with Server Actions:

```typescript
'use client'
import { useActionState } from 'react'
import { createUser } from './actions'

type FormState = { error?: string; success?: boolean }

export function CreateUserForm() {
  const [state, action, isPending] = useActionState<FormState, FormData>(
    createUser,
    {}
  )

  return (
    <form action={action}>
      <input name="email" type="email" required />
      {state.error && <p>{state.error}</p>}
      <button type="submit" disabled={isPending}>
        {isPending ? 'Creating...' : 'Create User'}
      </button>
    </form>
  )
}
```

## Custom Hooks Pattern

```typescript
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])

  return debouncedValue
}
```

## Repository Pattern

```typescript
interface Repository<T> {
  findAll(filters?: Filters): Promise<T[]>
  findById(id: string): Promise<T | null>
  create(data: CreateDto): Promise<T>
  update(id: string, data: UpdateDto): Promise<T>
  delete(id: string): Promise<void>
}
```

## Agent Support

- **typescript-expert** — Type design, generics, utility types
- **react-expert** — Custom hooks, component composition
- **nextjs-expert** — App Router, RSC, server actions
- **rest-expert** — REST API design patterns

## Skill Reference

- `api-design-principles` skill — Canonical API response format, REST conventions, and production API patterns
- `backend-patterns` skill — Backend architecture and database optimization
