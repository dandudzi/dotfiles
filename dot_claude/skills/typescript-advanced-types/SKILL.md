---
name: typescript-advanced-types
description: Master TypeScript's advanced type system including conditional types, mapped types, template literals, and utility types for building type-safe applications.
origin: ECC
model: sonnet
---

# TypeScript Advanced Types

## When to Activate
- Designing type-safe libraries, forms, or API clients
- Building discriminated unions or state machines
- Creating complex type inference logic

## Conditional Types

**Pattern**: `T extends U ? X : Y`

```typescript
type IsString<T> = T extends string ? true : false;
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
type ToArray<T> = T extends any ? T[] : never;
type Result = ToArray<string | number>; // string[] | number[]
```

## Mapped Types

**Pattern**: `{ [K in keyof T]: ... }`

```typescript
type Readonly<T> = { readonly [P in keyof T]: T[P] };
type Partial<T> = { [P in keyof T]?: T[P] };
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};
type PickByType<T, U> = {
  [K in keyof T as T[K] extends U ? K : never]: T[K];
};
type OnlyNumbers = PickByType<{ id: number; name: string; age: number }, number>;
// { id: number; age: number }
```

## Template Literal Types

**Pattern**: `` `${Literal}${Type}` ``

```typescript
type EventName = "click" | "focus" | "blur";
type Handler = `on${Capitalize<EventName>}`; // "onClick" | "onFocus" | "onBlur"
type Upper = Uppercase<"hello">; // "HELLO"

type Path<T> = T extends object
  ? { [K in keyof T]: K extends string ? `${K}` | `${K}.${Path<T[K]>}` : never }[keyof T]
  : never;
type ConfigPath = Path<{ server: { host: string }; db: { url: string } }>;
// "server" | "db" | "server.host" | "db.url"
```

## Infer Keyword

**Pattern**: `infer X` inside conditional types to extract type components

```typescript
type ElementType<T> = T extends (infer U)[] ? U : never;
type Num = ElementType<number[]>; // number

type PromiseType<T> = T extends Promise<infer U> ? U : never;
type FuncParams<T> = T extends (...args: infer P) => any ? P : never;
```

## Utility Types

**Built-in helpers** (implement with conditional + mapped types):

```typescript
type Partial<T> = { [K in keyof T]?: T[K] };
type Required<T> = { [K in keyof T]-?: T[K] };
type Pick<T, K extends keyof T> = { [P in K]: T[P] };
type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;
type Exclude<T, U> = T extends U ? never : T;
type Extract<T, U> = T extends U ? T : never;
type NonNullable<T> = T extends null | undefined ? never : T;
type Record<K extends keyof any, T> = { [P in K]: T };
```

## Discriminated Unions

**Pattern**: Union types with shared literal property for type-safe narrowing

```typescript
type AsyncState<T> =
  | { status: "success"; data: T }
  | { status: "error"; message: string }
  | { status: "loading" };

function handle<T>(state: AsyncState<T>) {
  switch (state.status) {
    case "success": console.log(state.data); break;
    case "error": console.log(state.message); break;
    case "loading": console.log("Waiting...");
  }
}
```

## Const Assertion

**Pattern**: `as const` to preserve literal types

```typescript
const colors = ["red", "green", "blue"] as const; // readonly ["red", "green", "blue"]
const config = { apiUrl: "https://api.example.com", timeout: 5000 } as const;
type Colors = (typeof colors)[number]; // "red" | "green" | "blue"
type ConfigKeys = keyof typeof config; // "apiUrl" | "timeout"
```

## Variance (Covariance & Contravariance)

How type compatibility works in different contexts:

```typescript
// Covariant: subtype accepted where supertype expected
interface Animal { name: string }
interface Dog extends Animal { breed: string }
interface Container<T> { get(): T }
const dogContainer: Container<Dog> = { get: () => ({ name: "Rex", breed: "Lab" }) };
const animalContainer: Container<Animal> = dogContainer; // OK

// Contravariant: supertype required where subtype expected
type Callback<T> = (value: T) => void;
const animalCallback: Callback<Animal> = (a) => console.log(a.name);
const dogCallback: Callback<Dog> = animalCallback; // OK

// Invariant: exact type required (arrays are invariant)
const dogs: Dog[] = [{ name: "Rex", breed: "Lab" }];
const animals: Animal[] = dogs; // Error in strict mode
```

## Type Narrowing and Guards

**Pattern**: Progressively refine union types with guards

```typescript
function processValue(value: string | number | boolean) {
  if (typeof value === "string") {
    console.log(value.toUpperCase()); // value: string
  } else if (typeof value === "number") {
    console.log(value.toFixed(2)); // value: number
  }
}

function isDog(animal: Dog | Cat): animal is Dog {
  return "breed" in animal;
}

function assertIsString(value: unknown): asserts value is string {
  if (typeof value !== "string") throw new Error("Not a string");
}
```

## Generics and Constraints

**Pattern**: Reusable types that adapt to input

```typescript
function identity<T>(value: T): T { return value; }
function getLength<T extends { length: number }>(value: T): number { return value.length; }
function merge<T extends object, U extends object>(obj1: T, obj2: U): T & U {
  return { ...obj1, ...obj2 };
}
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}
```

## Anti-Patterns

```typescript
// BAD: Over-using any
function process(data: any): any { return data.something.nested; }
// GOOD: Use generics with constraints
function process<T extends { something: { nested: unknown } }>(data: T) {
  return data.something.nested;
}

// BAD: Non-null assertion (!)
const value = maybeValue!.property;
// GOOD: Type guard
if (maybeValue !== null) { const value = maybeValue.property; }

// BAD: Unsafe casting
const data = response as User;
// GOOD: Type guard or validation
function isUser(data: unknown): data is User {
  return typeof data === "object" && "id" in data && "name" in data;
}

// BAD: Overly nested conditionals
type Nightmare<T> = T extends A ? T extends B ? T extends C ? D : C : B : A;
// GOOD: Break into steps
type Step1<T> = T extends A ? B : C;
type Step2<T> = T extends D ? E : F;
```

## Real-World Examples

**Type-safe form validation:**
```typescript
type ValidationRule<T> = { validate: (v: T) => boolean; message: string };
type FieldValidation<T> = { [K in keyof T]?: ValidationRule<T[K]>[] };

class FormValidator<T extends Record<string, any>> {
  validate(data: T, rules: FieldValidation<T>): Record<keyof T, string[]> { /* ... */ }
}
```

**Type-safe event emitter:**
```typescript
type Events = {
  "user:created": { id: string; name: string };
  "user:deleted": { id: string };
};

class Emitter<T extends Record<string, any>> {
  on<K extends keyof T>(event: K, fn: (data: T[K]) => void): void { }
  emit<K extends keyof T>(event: K, data: T[K]): void { }
}
```

**Type-safe API client:**
```typescript
type API = {
  "/users": {
    GET: { response: User[] };
    POST: { body: CreateUser; response: User };
  };
  "/users/:id": { GET: { params: { id: string }; response: User } };
};

class Client {
  request<Path extends keyof API, Method extends keyof API[Path]>(
    path: Path,
    method: Method,
    options?: any
  ): Promise<any> { }
}
```

## Decision Matrix

| Situation | Choice | Why |
|-----------|--------|-----|
| Object structure, properties | `interface` | Better error messages, auto-completion |
| Union types, complex logic | `type` | More flexible, supports unions + intersections |
| Static object with readonly | `as const` + `typeof` | Preserves literal types |
| Extract parts from generic | `infer` in conditional | Cleaner than overloads |
| Transform existing type | Mapped type | DRY, single source of truth |
| State machine | Discriminated union | Type-safe narrowing with switch |
| Narrowing unions | Type guards | Safe pattern matching |

## Key Principles

- Prefer **type guards** over non-null assertions (`!`)
- Use `Readonly<T>` to enforce immutability at type level
- Always enable `"strict": true` in tsconfig
- Build Result types instead of throwing for expected failures:
  ```typescript
  type Result<T, E = string> =
    | { ok: true; value: T }
    | { ok: false; error: E };
  ```
- Use **branded types** to prevent accidental misuse of structurally identical primitives:
  ```typescript
  type UserId = string & { readonly __brand: 'UserId' };
  ```

## Agent Support
- **typescript-expert** — Type design and complex logic
- **react-expert** — Type-safe React patterns
- **nextjs-expert** — Next.js type-safe patterns

## Skill References
- **modern-javascript** — Runtime patterns with types
- **typescript-scaffold** — TypeScript project setup
- TypeScript Handbook (official)
- Type Challenges (interactive practice)
