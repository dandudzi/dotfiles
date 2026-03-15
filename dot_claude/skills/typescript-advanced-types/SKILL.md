---
name: typescript-advanced-types
description: Master TypeScript's advanced type system including conditional types, mapped types, template literals, and utility types for building type-safe applications.
origin: ECC
---

# TypeScript Advanced Types

## When to Activate
- Designing type-safe libraries or frameworks
- Creating reusable generic components
- Implementing complex type inference logic
- Building discriminated union state machines
- Migrating JavaScript codebases to TypeScript with strict typing
- Developing type-safe form validation or API clients

## Conditional Types

**Pattern**: `T extends U ? X : Y`

```typescript
// Basic conditional
type IsString<T> = T extends string ? true : false;

// Extract return type
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

// Nested conditions
type TypeName<T> = T extends string
  ? "string"
  : T extends number
    ? "number"
    : T extends Function
      ? "function"
      : "other";

// Distributive over unions
type ToArray<T> = T extends any ? T[] : never;
type Result = ToArray<string | number>; // string[] | number[]
```

**Use when**: You need types that adapt based on input types or need to extract information from generic parameters.

## Mapped Types

**Pattern**: `{ [K in keyof T]: ... }`

```typescript
// Make properties readonly
type Readonly<T> = { readonly [P in keyof T]: T[P] };

// Make properties optional
type Partial<T> = { [P in keyof T]?: T[P] };

// Rename properties with as
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

// Filter properties by type
type PickByType<T, U> = {
  [K in keyof T as T[K] extends U ? K : never]: T[K];
};

type OnlyNumbers = PickByType<{ id: number; name: string; age: number }, number>;
// { id: number; age: number }
```

**Use when**: Transforming object types, creating getters/setters, filtering properties, or bulk property modifications.

## Template Literal Types

**Pattern**: `` `${Literal}${Type}` ``

```typescript
// Event handler names
type EventName = "click" | "focus" | "blur";
type Handler = `on${Capitalize<EventName>}`; // "onClick" | "onFocus" | "onBlur"

// String manipulation
type Upper = Uppercase<"hello">; // "HELLO"
type Lower = Lowercase<"HELLO">; // "hello"

// Nested path building
type Path<T> = T extends object
  ? {
      [K in keyof T]: K extends string
        ? `${K}` | `${K}.${Path<T[K]>}`
        : never;
    }[keyof T]
  : never;

type ConfigPath = Path<{ server: { host: string }; db: { url: string } }>;
// "server" | "db" | "server.host" | "db.url"
```

**Use when**: Building event handlers, creating API endpoints, generating configuration paths, or string-based type patterns.

## Infer Keyword

**Pattern**: `infer X` inside conditional types

```typescript
// Extract array element
type ElementType<T> = T extends (infer U)[] ? U : never;
type Num = ElementType<number[]>; // number

// Extract promise type
type PromiseType<T> = T extends Promise<infer U> ? U : never;

// Extract function parameters
type FuncParams<T> = T extends (...args: infer P) => any ? P : never;
```

**Use when**: Extracting component parts from complex types, inferring generic parameters from actual types.

## Utility Types

**Built-in helpers** (all can be implemented with conditional + mapped types):

```typescript
// Make all properties optional
type Partial<T> = { [K in keyof T]?: T[K] };

// Make all properties required
type Required<T> = { [K in keyof T]-?: T[K] };

// Select specific properties
type Pick<T, K extends keyof T> = { [P in K]: T[P] };

// Remove specific properties
type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;

// Exclude types from union
type Exclude<T, U> = T extends U ? never : T;
type T1 = Exclude<"a" | "b" | "c", "a">; // "b" | "c"

// Extract matching types from union
type Extract<T, U> = T extends U ? T : never;
type T2 = Extract<"a" | "b" | "c", "a" | "b">; // "a" | "b"

// Remove null/undefined
type NonNullable<T> = T extends null | undefined ? never : T;

// Create object with known keys
type Record<K extends keyof any, T> = { [P in K]: T };
```

**Use when**: Transforming object shapes, working with discriminated unions, creating flexible interfaces.

## Discriminated Unions

**Pattern**: Union types with shared literal property for type narrowing

```typescript
type Success<T> = { status: "success"; data: T };
type Error = { status: "error"; message: string };
type Loading = { status: "loading" };

type AsyncState<T> = Success<T> | Error | Loading;

// Type-safe narrowing
function handle<T>(state: AsyncState<T>) {
  switch (state.status) {
    case "success":
      console.log(state.data); // Type: T (narrowed)
      break;
    case "error":
      console.log(state.message); // Type: string (narrowed)
      break;
    case "loading":
      console.log("Waiting...");
  }
}

// State machine pattern
type State =
  | { type: "idle" }
  | { type: "fetching"; id: string }
  | { type: "done"; data: any }
  | { type: "error"; error: Error };
```

**Use when**: Modeling state machines, result types (Success/Error), or any multi-variant data structure that needs type-safe handling.

## Const Assertion

**Pattern**: `as const` to preserve literal types

```typescript
// Without as const: type is string[]
const colors1 = ["red", "green", "blue"];

// With as const: type is readonly ["red", "green", "blue"]
const colors2 = ["red", "green", "blue"] as const;

// Preserve literal keys
const config = {
  apiUrl: "https://api.example.com",
  timeout: 5000,
} as const;

// Extract literal union from const
type Colors = (typeof colors2)[number]; // "red" | "green" | "blue"
type ConfigKeys = keyof typeof config; // "apiUrl" | "timeout"
```

**Use when**: Creating type-safe constants, building configuration objects, defining fixed sets of values.

## Variance Covariance & Contravariance

**Concept**: How type compatibility works in different contexts

```typescript
// Covariant (property position) - subtype can be used where supertype expected
interface Animal { name: string }
interface Dog extends Animal { breed: string }

interface Container<T> { get(): T }
const dogContainer: Container<Dog> = { get: () => ({ name: "Rex", breed: "Lab" }) };
const animalContainer: Container<Animal> = dogContainer; // OK

// Contravariant (parameter position) - supertype required where subtype expected
type Callback<T> = (value: T) => void;
const animalCallback: Callback<Animal> = (a) => console.log(a.name);
const dogCallback: Callback<Dog> = animalCallback; // OK - takes any Animal

// Invariant (usually problematic) - exact type required
const dogs: Dog[] = [{ name: "Rex", breed: "Lab" }];
const animals: Animal[] = dogs; // Error in strict mode - arrays are invariant
```

**Use when**: Designing generic interfaces, understanding assignment rules, debugging type compatibility errors.

## Type Narrowing and Guards

**Pattern**: Progressively refining union types to access specific members

```typescript
// Type guards with typeof
function processValue(value: string | number | boolean) {
  if (typeof value === "string") {
    console.log(value.toUpperCase()); // value: string
  } else if (typeof value === "number") {
    console.log(value.toFixed(2)); // value: number
  } else {
    console.log(value); // value: boolean
  }
}

// Custom type guards (predicate functions)
interface Dog { breed: string; bark: () => void }
interface Cat { color: string; meow: () => void }

function isDog(animal: Dog | Cat): animal is Dog {
  return "breed" in animal;
}

function makeSound(animal: Dog | Cat) {
  if (isDog(animal)) {
    animal.bark(); // animal: Dog
  } else {
    animal.meow(); // animal: Cat
  }
}

// Assertion functions
function assertIsString(value: unknown): asserts value is string {
  if (typeof value !== "string") {
    throw new Error("Not a string");
  }
}

// Control flow narrowing
function processValue(value: string | null) {
  if (!value) return; // value narrowed to never in rest of block
  console.log(value.toUpperCase()); // value: string
}
```

**Use when**: Working with union types, API responses, or user input that could be multiple types.

## Generics and Constraints

**Pattern**: Write reusable functions and types that adapt to input

```typescript
// Basic generic
function identity<T>(value: T): T {
  return value;
}

const str = identity("hello"); // T = string
const num = identity(42); // T = number

// Generic constraints - limit what T can be
function getLength<T extends { length: number }>(value: T): number {
  return value.length;
}

getLength("hello"); // OK
getLength([1, 2, 3]); // OK
getLength(42); // Error: number has no length

// Multi-constraint
function merge<T extends object, U extends object>(obj1: T, obj2: U): T & U {
  return { ...obj1, ...obj2 };
}

const result = merge({ a: 1 }, { b: 2 }); // { a: 1; b: 2 }

// Keyof constraint - ensure key exists in object
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { id: 1, name: "John" };
getProperty(user, "name"); // OK
getProperty(user, "email"); // Error: "email" not in user
```

**Use when**: Creating reusable library code, building type-safe form handlers, or generic data structures.

## Decision Matrix

| Situation | Choice | Why |
|-----------|--------|-----|
| Object structure, properties | `interface` | Better error messages, auto-completion |
| Union types, complex logic | `type` | More flexible, supports unions + intersections |
| Static object with readonly | `as const` + `typeof` | Preserves literal types, less boilerplate |
| Extract parts from generic | `infer` in conditional | Cleaner than multiple overloads |
| Transform existing type | Mapped type | DRY, maintainable, single source of truth |
| State machine | Discriminated union | Type-safe narrowing with switch/if |
| Narrowing union types | Type guards | Safe pattern matching without assertion |

## Anti-Patterns

```typescript
// BAD: Over-using any defeats TypeScript
function process(data: any): any {
  return data.something.nested;
}

// GOOD: Use generics with constraints
function process<T extends { something: { nested: unknown } }>(data: T) {
  return data.something.nested;
}

// BAD: Non-null assertion (!)
const value = maybeValue!.property;

// GOOD: Type guard
if (maybeValue !== null) {
  const value = maybeValue.property;
}

// BAD: Unsafe type casting
const data = response as User;

// GOOD: Type guard or validation
function isUser(data: unknown): data is User {
  return typeof data === "object" && "id" in data && "name" in data;
}

// BAD: Overly complex nested conditional types
type Nightmare<T> = T extends A
  ? T extends B
    ? T extends C
      ? T extends D
        ? never
        : D
      : C
    : B
  : A;

// GOOD: Break into intermediate types
type Step1<T> = T extends A ? B : C;
type Step2<T> = T extends D ? E : F;

// BAD: Exhausting type parameters
type TooFlexible<T, U, V, W, X, Y, Z> = { /* ... */ };

// GOOD: Limit generics, use constraints
type Better<T extends Base, U extends T> = { /* ... */ };
```

## Real-World Examples

**Type-safe form validation:**
```typescript
type ValidationRule<T> = { validate: (v: T) => boolean; message: string };
type FieldValidation<T> = { [K in keyof T]?: ValidationRule<T[K]>[] };

class FormValidator<T extends Record<string, any>> {
  validate(data: T, rules: FieldValidation<T>): Record<keyof T, string[]> {
    // Implementation
  }
}
```

**Type-safe event emitter:**
```typescript
type Events = { "user:created": { id: string; name: string }; "user:deleted": { id: string } };

class Emitter<T extends Record<string, any>> {
  on<K extends keyof T>(event: K, fn: (data: T[K]) => void): void { }
  emit<K extends keyof T>(event: K, data: T[K]): void { }
}
```

**Type-safe API client:**
```typescript
type API = {
  "/users": { GET: { response: User[] }; POST: { body: CreateUser; response: User } };
  "/users/:id": { GET: { params: { id: string }; response: User } };
};

class Client {
  request<Path extends keyof API, Method extends keyof API[Path]>(
    path: Path,
    method: Method,
    options?: APIOptions<API[Path][Method]>
  ): Promise<APIResponse<API[Path][Method]>> { }
}
```

## Agent Support
- **typescript-expert** — Type design and complex type logic
- **react-expert** — Type-safe React patterns and hooks
- **vitest-expert** — Type testing and assertion helpers
- **nextjs-expert** — Next.js type-safe patterns and type safety in App Router

## Skill References
- **modern-javascript** — Runtime patterns that benefit from types
- **typescript-scaffold** — TypeScript project setup and configuration
- TypeScript language handbook (official)
- Total TypeScript (advanced courses)
- Type Challenges (interactive practice)
