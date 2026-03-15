---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---
# TypeScript Best Practices

> Extends [common/coding-style.md](./coding-style.md) with TypeScript-specific guidance.

## Type Safety First

Make types work for you, not against you. Explicit types on public APIs, inferred types locally.

### Public APIs Must Have Types

```typescript
// WRONG: Exported function without explicit types
export function formatUser(user) {
  return `${user.firstName} ${user.lastName}`
}

// CORRECT: Explicit types on public APIs
interface User {
  firstName: string
  lastName: string
}

export function formatUser(user: User): string {
  return `${user.firstName} ${user.lastName}`
}
```

Let TypeScript infer obvious local variable types:

```typescript
// WRONG: Unnecessary type annotations
const message: string = "Hello";
const count: number = 5;
const items: Array<string> = [];

// CORRECT: Let TypeScript infer
const message = "Hello";
const count = 5;
const items = [];
```

## Interfaces vs. Type Aliases

**Use `interface` for:**
- Object shapes that may be extended or implemented
- Public API contracts
- Class implementations

**Use `type` for:**
- Union types
- Intersections
- Tuples
- Mapped types
- Utility types
- When you need more flexibility

```typescript
// Interface - open for extension
interface User {
  id: string
  email: string
}

interface Admin extends User {
  permissions: string[]
}

// Type - for unions and complex patterns
type UserRole = 'admin' | 'member' | 'guest'
type UserWithRole = User & {
  role: UserRole
}
```

## Never Use `any`

Always use a more specific type:

```typescript
// WRONG: Defeats TypeScript entirely
function process(data: any): any {
  return data.something.nested
}

// CORRECT: Use unknown for untrusted input
function process(data: unknown): ProcessedData {
  if (typeof data !== 'object' || data === null) {
    throw new Error('Invalid input')
  }
  return parseData(data)
}

// CORRECT: Use generics when you need flexibility
function process<T extends { something: { nested: unknown } }>(data: T): T {
  return data
}
```

## Exhaustive Type Checking

Ensure all union variants are handled:

```typescript
type State = { status: 'idle' } | { status: 'loading' } | { status: 'done'; data: unknown }

function render(state: State): JSX.Element {
  switch (state.status) {
    case 'idle':
      return null
    case 'loading':
      return <Spinner />
    case 'done':
      return <Result data={state.data} />
    // TypeScript error if we forget a case!
  }
}
```

## Avoid Non-Null Assertions (!)

Use type guards instead:

```typescript
// WRONG: Non-null assertion bypasses type safety
function getValue(key: string) {
  const value = map.get(key)!
  return value.toUpperCase()
}

// CORRECT: Type guard
function getValue(key: string): string {
  const value = map.get(key)
  if (!value) {
    throw new Error(`Missing key: ${key}`)
  }
  return value.toUpperCase()
}
```

## Type-Safe Environment Variables

Always validate at startup:

```typescript
// src/env.ts
import { z } from 'zod'

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']),
  DATABASE_URL: z.string().url(),
  API_KEY: z.string().min(1),
})

export const env = envSchema.parse(process.env)
// Throws immediately if env vars are invalid
```

## Generic Constraints

Write reusable, type-safe code with constraints:

```typescript
// Constraint: must have length property
function getLength<T extends { length: number }>(value: T): number {
  return value.length
}

// Constraint: must be an array element type
function getFirstItem<T extends readonly unknown[]>(arr: T): T[0] {
  return arr[0]
}

// Constraint: must extend object
function merge<T extends object, U extends object>(a: T, b: U): T & U {
  return { ...a, ...b }
}
```

## Immutable Types

Use `Readonly<T>` and `readonly` for immutability contracts:

```typescript
interface Config {
  readonly apiUrl: string
  readonly timeout: number
}

function updateConfig(config: Readonly<Config>, timeout: number): Config {
  return {
    ...config,
    timeout
  }
}

// Arrays
const items: readonly string[] = []
// Cannot mutate: items.push() — compile error
```

## Type Guard Functions

Use custom type guards for safe narrowing:

```typescript
interface Dog { breed: string }
interface Cat { color: string }

function isDog(animal: Dog | Cat): animal is Dog {
  return 'breed' in animal
}

function makeSound(animal: Dog | Cat) {
  if (isDog(animal)) {
    console.log(animal.breed) // narrowed to Dog
  }
}
```

## Assertion Functions

Use assertion functions to narrow types in control flow:

```typescript
function assertIsString(value: unknown): asserts value is string {
  if (typeof value !== 'string') {
    throw new Error('Expected string')
  }
}

function processString(value: unknown) {
  assertIsString(value)
  // value is now known to be string
  console.log(value.toUpperCase())
}
```

## Error Types

Always extend Error class:

```typescript
class ValidationError extends Error {
  constructor(
    message: string,
    public readonly field: string
  ) {
    super(message)
    this.name = 'ValidationError'
  }
}

try {
  throw new ValidationError('Email is required', 'email')
} catch (error: unknown) {
  if (error instanceof ValidationError) {
    console.error(`Field ${error.field}: ${error.message}`)
  }
}
```

## Strict Mode

Always enable strict mode in tsconfig:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

## Agent Support

- **typescript-expert** — Advanced type system, generics, complex type patterns
- **react-expert** — Type-safe React patterns and hooks
- **nextjs-expert** — Next.js type-safe patterns

## Skill References

- **typescript-advanced-types** — Conditional types, mapped types, template literals
- **typescript-scaffold** — Project setup and configuration
- **modern-javascript** — Runtime patterns that benefit from types
