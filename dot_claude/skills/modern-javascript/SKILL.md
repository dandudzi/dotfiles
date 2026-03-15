---
name: modern-javascript
description: Master ES2024+ features, functional programming patterns, async flows, and modern object/module patterns for writing clean, efficient JavaScript code.
origin: ECC
---

# Modern JavaScript Patterns

## When to Activate
- Refactoring legacy JavaScript to ES6+ syntax
- Implementing functional programming patterns
- Optimizing async/await flows
- Building immutable data structures
- Writing modern module-based code
- Improving code readability with optional chaining and nullish coalescing
- Implementing error handling with custom Error classes

## ES2024+ Core Features

### ES2024 — New in ECMAScript 2024

```javascript
// Object.groupBy() — group array items by a key
const items = [
  { name: "Alice", dept: "eng" },
  { name: "Bob", dept: "eng" },
  { name: "Carol", dept: "design" },
];

const byDept = Object.groupBy(items, item => item.dept);
// { eng: [{ name: "Alice", ... }, { name: "Bob", ... }], design: [...] }

// Map.groupBy() — same but returns a Map (preserves insertion order)
const byDeptMap = Map.groupBy(items, item => item.dept);
byDeptMap.get("eng"); // [{ name: "Alice", ... }, ...]

// Promise.withResolvers() — expose resolve/reject outside the constructor
const { promise, resolve, reject } = Promise.withResolvers();

// Pass resolve to an event listener
button.addEventListener("click", () => resolve("clicked"));

const result = await promise; // resolves when button is clicked
// Eliminates the "deferred promise" anti-pattern
```

**Use when**: Grouping collections without `reduce` boilerplate; replacing manual deferred-promise wrappers.

### Optional Chaining (`?.`)

```javascript
const user = { profile: { name: "John" } };

// Safe property access
const city = user?.profile?.address?.city; // undefined (not error)
const country = user?.profile?.country; // undefined

// Safe method calls
const result = obj.method?.(); // undefined if method doesn't exist

// Safe array/computed access
const first = arr?.[0];
const value = obj?.[computedKey];
```

**Use when**: Accessing nested properties that might be null/undefined without defensive checks.

### Nullish Coalescing (`??`)

```javascript
// Only replaces null or undefined
const value1 = null ?? "default"; // "default"
const value2 = undefined ?? "default"; // "default"
const value3 = 0 ?? "default"; // 0 (NOT "default")
const value4 = "" ?? "default"; // "" (NOT "default")

// Different from ||
const count = 0 || 10; // 10 (wrong)
const count = 0 ?? 10; // 0 (correct)

// Chaining
const setting = userConfig?.theme ?? systemConfig?.theme ?? "light";
```

**Use when**: Defaulting false-y values that are legitimate (0, "", false) should stay unchanged.

### Logical Assignment Operators

```javascript
// Nullish assignment: assign only if null/undefined
let value = null;
value ??= "default"; // value = "default"

let count = 0;
count ??= 10; // count = 0 (unchanged)

// OR assignment: assign if falsy
let status = "";
status ||= "inactive"; // status = "inactive"

// AND assignment: assign if truthy
let permissions = { admin: false };
permissions.admin &&= true; // no change
permissions.admin = true;
permissions.admin &&= false; // permissions.admin = false
```

**Use when**: Conditionally updating variables in a concise way.

### Class Fields and Private Methods

```javascript
class User {
  // Public field (available on instance)
  id;
  name;

  // Private field (hidden from outside)
  #password;
  #token;

  // Static field (shared across all instances)
  static count = 0;

  constructor(id, name, password) {
    this.id = id;
    this.name = name;
    this.#password = password;
    User.count++;
  }

  // Public method
  getDisplayName() {
    return this.name.toUpperCase();
  }

  // Private method (only accessible inside class)
  #hashPassword(password) {
    return `hash_${password}`;
  }

  // Getter
  get email() {
    return this.#getEmail();
  }

  // Static method
  static createGuest() {
    return new User(0, "Guest", "");
  }
}
```

**Use when**: Encapsulating data and hiding implementation details from outside code.

### Top-Level `await`

```javascript
// src/config.js - Can use await at module level
const config = await fetch("/config.json").then(r => r.json());
const db = await initializeDatabase(config);

export { config, db };

// src/main.js
import { config, db } from "./config.js"; // Waits for await to complete
```

**Use when**: Initializing async resources at module load time (ESM only).

### Array Methods: `at()` and Modern Operations

```javascript
const arr = [1, 2, 3, 4, 5];

// at() - negative indexing
const last = arr.at(-1); // 5
const secondToLast = arr.at(-2); // 4

// Immutable operations (don't mutate original)
const doubled = arr.map(x => x * 2);
const filtered = arr.filter(x => x > 2);
const flattened = [[1, 2], [3, 4]].flat();

// flatMap - map then flatten
const users = [
  { name: "John", tags: ["admin", "user"] },
  { name: "Jane", tags: ["user"] }
];
const allTags = users.flatMap(u => u.tags);
// ["admin", "user", "user"]

// Array.from with mapping
const doubled = Array.from({ length: 5 }, (_, i) => (i + 1) * 2);
// [2, 4, 6, 8, 10]
```

**Use when**: Safely accessing array elements or transforming arrays immutably.

### `structuredClone()` - Deep Copying

```javascript
// Simple shallow copy
const copy1 = { ...original };
const copy2 = [...array];

// Deep copy (handles nested objects)
const deepCopy = structuredClone(complexObject);

// Handles circular references
const obj = { name: "John" };
obj.self = obj;
const clone = structuredClone(obj); // Works!

// Serializable types only (no functions, DOM nodes)
const cloneable = {
  name: "John",
  age: 30,
  created: new Date(),
  tags: ["admin", "user"]
};
const cloned = structuredClone(cloneable);
```

**Use when**: Creating independent deep copies without JSON.parse/stringify limitations.

## Functional Programming Patterns

### Immutable Array Operations

```javascript
const users = [
  { id: 1, name: "John", active: true },
  { id: 2, name: "Jane", active: false },
  { id: 3, name: "Bob", active: true }
];

// Transform immutably
const names = users.map(u => u.name); // Create new array
const active = users.filter(u => u.active); // Create new array
const sorted = [...users].sort((a, b) => a.name.localeCompare(b.name));

// Reduce for aggregation
const totalActive = users.reduce((count, u) => count + (u.active ? 1 : 0), 0);

// Group by property
const byStatus = users.reduce((groups, user) => ({
  ...groups,
  [user.active ? "active" : "inactive"]: [...(groups[user.active ? "active" : "inactive"] || []), user]
}), {});

// Chain operations
const result = users
  .filter(u => u.active)
  .map(u => u.name)
  .sort()
  .join(", ");
```

**Use when**: Transforming data without side effects, enabling easy testing and composition.

### Function Composition and Partial Application

```javascript
// Composition - right to left
const compose = (...fns) => x => fns.reduceRight((acc, fn) => fn(acc), x);

// Piping - left to right
const pipe = (...fns) => x => fns.reduce((acc, fn) => fn(acc), x);

// Currying - convert to single-arg functions
const multiply = a => b => a * b;
const double = multiply(2);
const triple = multiply(3);

// Partial application
const partial = (fn, ...args) => (...more) => fn(...args, ...more);
const add = (a, b, c) => a + b + c;
const add5 = partial(add, 5);
add5(3, 2); // 10

// Real-world pipeline
const processUser = pipe(
  user => ({ ...user, name: user.name.trim() }),
  user => ({ ...user, email: user.email.toLowerCase() }),
  user => ({ ...user, verified: !!user.email })
);
```

**Use when**: Building reusable, testable functions that avoid mutation.

### Pure Functions and Error Handling

```javascript
// WRONG: Mutates input
function addItemImpure(cart, item) {
  cart.items.push(item);
  cart.total += item.price;
  return cart;
}

// CORRECT: Returns new object
function addItemPure(cart, item) {
  return {
    ...cart,
    items: [...cart.items, item],
    total: cart.total + item.price
  };
}

// Error handling with custom errors
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = "ValidationError";
    this.field = field;
  }
}

function validateEmail(email) {
  if (!email.includes("@")) {
    throw new ValidationError("Invalid email format", "email");
  }
  return email;
}

// Error chaining (ES2022)
try {
  await riskyOperation();
} catch (error) {
  throw new Error("Operation failed", { cause: error });
}
```

**Use when**: Avoiding hidden bugs from mutations, providing context for debugging.

## Async Patterns

### Promise Combinators

```javascript
// Wait for ALL to succeed, fail on first error
Promise.all([fetch1(), fetch2(), fetch3()])
  .then(results => console.log(results))
  .catch(error => console.error("One failed:", error));

// Wait for ALL to settle (success or error)
Promise.allSettled([fetch1(), fetch2(), fetch3()])
  .then(results => {
    results.forEach(result => {
      if (result.status === "fulfilled") {
        console.log("Success:", result.value);
      } else {
        console.log("Error:", result.reason);
      }
    });
  });

// First to succeed
Promise.any([fetch1(), fetch2(), fetch3()])
  .then(first => console.log("First success:", first))
  .catch(error => console.error("All failed"));

// First to complete (success or error)
Promise.race([fetch1(), timeout(5000)])
  .then(result => console.log(result))
  .catch(error => console.error("Race lost"));
```

**Use when**: Coordinating multiple async operations efficiently.

### Async Iteration

```javascript
// For async iterators and generators
async function* fetchPages(url) {
  let page = 1;
  while (true) {
    const response = await fetch(`${url}?page=${page}`);
    const data = await response.json();
    if (data.length === 0) break;
    yield data;
    page++;
  }
}

// Consume with for await...of
for await (const page of fetchPages("/api/users")) {
  console.log(page);
}

// Manual iteration
const iterator = fetchPages("/api/users");
const first = await iterator.next();
const second = await iterator.next();
```

**Use when**: Streaming large datasets or paginated API responses.

### AbortController for Cancellation

```javascript
const controller = new AbortController();

const fetchWithCancel = async () => {
  try {
    const response = await fetch("/api/data", {
      signal: controller.signal
    });
    return response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      console.log("Request cancelled");
    } else {
      throw error;
    }
  }
};

// Start request
const promise = fetchWithCancel();

// Cancel after timeout
setTimeout(() => controller.abort(), 5000);

// Or cancel on user interaction
button.addEventListener("click", () => controller.abort());
```

**Use when**: Cancelling long-running requests or preventing memory leaks.

## Module Patterns

### ESM vs CJS - Tree-Shaking Friendly Exports

```javascript
// utils/math.js (good for tree-shaking)
export const PI = 3.14159;
export function add(a, b) { return a + b; }
export function subtract(a, b) { return a - b; }

// Not default export - allows selective imports
// Unused functions are eliminated by bundler

// Usage
import { add, PI } from "./utils/math.js"; // Only import what's needed
const result = add(2, 3);

// Dynamic imports (code-splitting)
button.addEventListener("click", async () => {
  const { expensive } = await import("./heavy-module.js");
  expensive();
});
```

**Use when**: Creating libraries that respect bundler optimization.

### Barrel Files - When to Use/Avoid

```javascript
// GOOD: Export from related modules
// src/hooks/index.js
export { useCounter } from "./useCounter.js";
export { useLocalStorage } from "./useLocalStorage.js";

// Usage: Clean import
import { useCounter, useLocalStorage } from "./hooks";

// BAD: Barrel file exports too much
// src/index.js - Don't do this at root
export * from "./utils";
export * from "./hooks";
export * from "./services"; // Pollutes namespace, kills tree-shaking
```

**Use when**: Organizing related exports in a subdirectory; avoid at package root.

### Computed Properties and Shorthand

```javascript
// Shorthand property names
const name = "John";
const age = 30;
const user = { name, age }; // Same as { name: name, age: age }

// Computed property names
const field = "email";
const user = {
  name: "John",
  [field]: "john@example.com", // Dynamic key
  [`get_${field}`]() {
    return this[field];
  }
};

// Shorthand methods
const calculator = {
  add(a, b) { return a + b; }, // Not: add: (a, b) => ...
  subtract(a, b) { return a - b; }
};

// Object.entries and Object.fromEntries
const obj = { a: 1, b: 2, c: 3 };
const entries = Object.entries(obj); // [["a", 1], ["b", 2], ...]

const doubled = Object.fromEntries(
  entries.map(([k, v]) => [k, v * 2])
);
// { a: 2, b: 4, c: 6 }
```

**Use when**: Writing concise, readable object manipulation code.

## Performance Optimization

### Request Batching and Debouncing

```javascript
// Debounce - delay execution until period of inactivity
function debounce(fn, delay) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

const debouncedSearch = debounce(query => {
  fetch(`/api/search?q=${query}`);
}, 300);

// Throttle - limit execution frequency
function throttle(fn, limit) {
  let inThrottle;
  return (...args) => {
    if (!inThrottle) {
      fn(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

const throttledScroll = throttle(() => {
  updateUI();
}, 100);
```

**Use when**: Reducing unnecessary function calls in response to frequent events.

## Anti-Patterns

```javascript
// BAD: Using var (function scope, hoisting issues)
var count = 0;
for (var i = 0; i < 5; i++) { }
console.log(i); // 5 (leaked!)

// GOOD: Use const/let (block scope)
let count = 0;
for (let i = 0; i < 5; i++) { }
console.log(i); // ReferenceError

// BAD: Callback hell
function fetchData(callback) {
  fetch("/api/users", {
    success: (users) => {
      users.forEach(user => {
        fetch(`/api/users/${user.id}`, {
          success: (details) => {
            callback(details);
          }
        });
      });
    }
  });
}

// GOOD: Use async/await
async function fetchData() {
  const users = await fetch("/api/users").then(r => r.json());
  const details = [];
  for (const user of users) {
    const d = await fetch(`/api/users/${user.id}`).then(r => r.json());
    details.push(d);
  }
  return details;
}

// BAD: Using arguments object
function sum() {
  let total = 0;
  for (let i = 0; i < arguments.length; i++) {
    total += arguments[i];
  }
  return total;
}

// GOOD: Use rest parameters
function sum(...numbers) {
  return numbers.reduce((a, b) => a + b, 0);
}

// BAD: Mutating function arguments
function addToCart(cart, item) {
  cart.items.push(item);
  return cart;
}

// GOOD: Return new object
function addToCart(cart, item) {
  return { ...cart, items: [...cart.items, item] };
}

// BAD: Using == (type coercion)
if (value == null) { } // Catches both null and undefined
if (count == "5") { } // Unexpected true

// GOOD: Use === (strict equality)
if (value === null || value === undefined) { }
if (count === 5) { }
```

## Agent Support
- **react-expert** — React hooks and component patterns using modern JavaScript
- **typescript-expert** — Type-safe patterns with TypeScript
- **nodejs-expert** — Node.js async patterns and module systems
- **vitest-expert** — Testing functional and async patterns

## Skill References
- **typescript-advanced-types** — Type system features for modern patterns
- **javascript-testing** — Testing modern async and functional code
