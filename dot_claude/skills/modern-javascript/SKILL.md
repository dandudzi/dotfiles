---
name: modern-javascript
description: Master ES2024+ features, functional programming patterns, async flows, and modern object/module patterns for writing clean, efficient JavaScript code.
origin: ECC
model: sonnet
---

# Modern JavaScript Patterns

## When to Activate
- Refactoring to ES6+ or optimizing async/await flows
- Writing immutable, functional code
- Building modern module systems

## ES2024+ Core Features

### ES2024 Features

```javascript
// Object.groupBy() — group array items by key
const byDept = Object.groupBy(items, item => item.dept);

// Promise.withResolvers() — expose resolve/reject outside constructor
const { promise, resolve, reject } = Promise.withResolvers();
button.addEventListener("click", () => resolve("clicked"));
const result = await promise;
```

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


### Logical Assignment Operators

```javascript
let value = null;
value ??= "default"; // Assign if null/undefined
let status = "";
status ||= "inactive"; // Assign if falsy
let flag = true;
flag &&= false; // Assign if truthy
```


### Class Fields and Private Methods

```javascript
class User {
  id; name;                    // Public fields
  #password;                   // Private field
  static count = 0;            // Static field

  constructor(id, name, pwd) {
    this.id = id;
    this.name = name;
    this.#password = pwd;
  }

  #hashPassword() { return `hash_${this.#password}`; } // Private method
  static createGuest() { return new User(0, "Guest", ""); }
}
```


### Top-Level `await`

```javascript
// src/config.js - Can use await at module level
const config = await fetch("/config.json").then(r => r.json());
const db = await initializeDatabase(config);

export { config, db };

// src/main.js
import { config, db } from "./config.js"; // Waits for await to complete
```


### Array Methods: `at()` and Modern Operations

```javascript
const arr = [1, 2, 3, 4, 5];
arr.at(-1);  // 5 (negative indexing)
arr.map(x => x * 2);  // Immutable transform
arr.filter(x => x > 2);  // Immutable filter
[[1, 2], [3, 4]].flat();  // Flatten
users.flatMap(u => u.tags);  // Map and flatten in one step
```


### `structuredClone()` - Deep Copying

```javascript
const copy1 = { ...original };  // Shallow copy
const copy2 = [...array];       // Shallow copy
const deepCopy = structuredClone(complexObject);  // Deep copy (handles circular refs)
```


## Functional Programming Patterns

### Immutable Array Operations

```javascript
const users = [{ id: 1, name: "John", active: true }, ...];

users.map(u => u.name);  // Transform to new array
users.filter(u => u.active);  // Filter to new array
[...users].sort((a, b) => a.name.localeCompare(b.name));  // Sort new copy
users.reduce((count, u) => count + (u.active ? 1 : 0), 0);  // Aggregate

// Chain operations
users.filter(u => u.active).map(u => u.name).sort().join(", ");
```


### Function Composition and Partial Application

```javascript
const compose = (...fns) => x => fns.reduceRight((acc, fn) => fn(acc), x);
const pipe = (...fns) => x => fns.reduce((acc, fn) => fn(acc), x);

// Currying - convert to single-arg functions
const multiply = a => b => a * b;
const double = multiply(2);

// Partial application
const partial = (fn, ...args) => (...more) => fn(...args, ...more);
const add = (a, b, c) => a + b + c;
const add5 = partial(add, 5);
```


### Pure Functions and Error Handling

```javascript
// WRONG: Mutates input
function addItemImpure(cart, item) { cart.items.push(item); }

// CORRECT: Returns new object
function addItemPure(cart, item) {
  return { ...cart, items: [...cart.items, item], total: cart.total + item.price };
}

// Custom error classes
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.field = field;
  }
}

// Error chaining (ES2022)
try { await riskyOperation(); }
catch (error) { throw new Error("Failed", { cause: error }); }
```


## Async Patterns

### Promise Combinators

```javascript
Promise.all([p1, p2, p3]);  // Fail on first error
Promise.allSettled([p1, p2, p3]);  // Wait for all to complete
Promise.any([p1, p2, p3]);  // First success
Promise.race([p1, timeout(5000)]);  // First to complete
```


### Async Iteration

```javascript
async function* fetchPages(url) {
  let page = 1;
  while (true) {
    const data = await fetch(`${url}?page=${page}`).then(r => r.json());
    if (data.length === 0) break;
    yield data;
    page++;
  }
}

for await (const page of fetchPages("/api/users")) { console.log(page); }
```


### AbortController for Cancellation

```javascript
const controller = new AbortController();

const response = await fetch("/api/data", { signal: controller.signal });

// Cancel after timeout or user interaction
setTimeout(() => controller.abort(), 5000);
button.addEventListener("click", () => controller.abort());
```


## Module Patterns

### ESM vs CJS - Tree-Shaking Friendly Exports

```javascript
// Named exports (tree-shakeable)
export const PI = 3.14159;
export function add(a, b) { return a + b; }

import { add, PI } from "./utils/math.js";

// Dynamic imports (code-splitting)
button.addEventListener("click", async () => {
  const { expensive } = await import("./heavy.js");
});
```


### Barrel Files

```javascript
// GOOD: Subdirectory barrel files
// src/hooks/index.js
export { useCounter } from "./useCounter.js";
export { useLocalStorage } from "./useLocalStorage.js";

// BAD: Root-level barrel files kill tree-shaking
// src/index.js - avoid this
export * from "./utils";
```


### Computed Properties and Shorthand

```javascript
const name = "John", age = 30;
const user = { name, age };  // Property shorthand

const field = "email";
const obj = { name, [field]: "x@y.com", [`get_${field}`]() { return this[field]; } };

const entries = Object.entries({ a: 1, b: 2 });  // [["a", 1], ...]
const doubled = Object.fromEntries(entries.map(([k, v]) => [k, v * 2]));  // { a: 2, ... }
```


## Performance Optimization

### Debouncing and Throttling

```javascript
// Debounce - delay until inactivity
const debounce = (fn, delay) => {
  let timeoutId;
  return (...args) => { clearTimeout(timeoutId); timeoutId = setTimeout(() => fn(...args), delay); };
};

// Throttle - limit frequency
const throttle = (fn, limit) => {
  let inThrottle;
  return (...args) => { if (!inThrottle) { fn(...args); inThrottle = true; setTimeout(() => inThrottle = false, limit); } };
};
```


## Anti-Patterns to Avoid

```javascript
// BAD: var (function scope), GOOD: const/let (block scope)
var i = 0; for (var j = 0; j < 5; j++) { }
console.log(j); // 5 (leaked!)
let i = 0; for (let j = 0; j < 5; j++) { }
console.log(j); // ReferenceError

// BAD: Mutate arguments, GOOD: Return new object
function bad(cart) { cart.items.push(item); }
function good(cart) { return { ...cart, items: [...cart.items, item] }; }

// BAD: == type coercion, GOOD: === strict equality
if (count == "5") { }  // True (BAD)
if (count === 5) { }   // Correct
```

## Agents and Patterns
- **typescript-advanced-types** — Type system features for modern patterns
- **javascript-testing** — Testing modern async and functional code
