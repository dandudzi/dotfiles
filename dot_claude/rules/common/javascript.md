---
paths:
  - "**/*.js"
  - "**/*.jsx"
  - "**/*.mjs"
---
# JavaScript Best Practices

> Extends [common/coding-style.md](./coding-style.md) with JavaScript-specific guidance for ES2022+ code.

## Modern ES2022+ Features

Use modern JavaScript features to write cleaner, more readable code.

### const and let

Always use `const` by default, `let` when reassignment is needed. Never use `var`:

```javascript
// WRONG: var has function scope and hoisting issues
var count = 0
for (var i = 0; i < 5; i++) { }
console.log(i) // 5 (leaked!)

// CORRECT: const for non-reassigned values
const message = "Hello"

// CORRECT: let for reassigned values
let count = 0
for (let i = 0; i < 5; i++) { }
console.log(i) // ReferenceError
```

### Optional Chaining (?.)

Safe property access without defensive checks:

```javascript
// WRONG: Manual null checks
const city = user && user.profile && user.profile.address && user.profile.address.city

// CORRECT: Optional chaining
const city = user?.profile?.address?.city // undefined if any step is null/undefined
```

### Nullish Coalescing (??)

Only default for `null` and `undefined`, not falsy values:

```javascript
// WRONG: || treats 0 as falsy
const count = response.count || 10 // 10 if count is 0

// CORRECT: ?? only defaults for null/undefined
const count = response.count ?? 10 // 0 if count is 0
```

### Logical Assignment Operators

```javascript
// OR assignment: assign if falsy
user.status ||= 'inactive'

// AND assignment: assign if truthy
user.verified &&= true

// Nullish assignment: assign if null/undefined
config.timeout ??= 5000
```

### Destructuring

Extract variables cleanly from objects and arrays:

```javascript
// Objects
const { name, email, role = 'user' } = userData

// Arrays
const [first, second, ...rest] = items

// Renaming
const { firstName: first, lastName: last } = user

// Nested
const { profile: { address: { city } } } = user
```

## Immutability

Never mutate objects. Return new copies with changes:

```javascript
// WRONG: Mutates array
function addItem(items, item) {
  items.push(item)
  return items
}

// CORRECT: Returns new array
function addItem(items, item) {
  return [...items, item]
}

// WRONG: Mutates object
function updateUser(user, name) {
  user.name = name
  return user
}

// CORRECT: Returns new object
function updateUser(user, name) {
  return { ...user, name }
}
```

## Error Handling

Use custom error classes and handle errors comprehensively:

```javascript
// Custom error class
class ValidationError extends Error {
  constructor(message, field) {
    super(message)
    this.name = 'ValidationError'
    this.field = field
  }
}

// Async/await with try-catch
async function fetchUser(id) {
  try {
    const response = await fetch(`/api/users/${id}`)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    console.error('Failed to fetch user:', error)
    throw new Error('Failed to load user', { cause: error })
  }
}
```

## Async Patterns

### async/await Over Callbacks

```javascript
// WRONG: Callback hell
function loadData(callback) {
  fetchUsers((err, users) => {
    if (err) {
      callback(err)
    } else {
      users.forEach(user => {
        fetchDetails(user.id, (err, details) => {
          callback(err, details)
        })
      })
    }
  })
}

// CORRECT: async/await
async function loadData() {
  const users = await fetchUsers()
  for (const user of users) {
    const details = await fetchDetails(user.id)
    process(details)
  }
}
```

### Promise Combinators

```javascript
// All must succeed, fail fast
const results = await Promise.all([fetch1(), fetch2(), fetch3()])

// All must settle (success or failure)
const settled = await Promise.allSettled([fetch1(), fetch2()])

// First to succeed
const first = await Promise.any([mirror1(), mirror2()])

// First to complete
const winner = await Promise.race([fetch(), timeout(5000)])
```

### Abort Cancellation

```javascript
const controller = new AbortController()

const promise = fetch('/api/data', { signal: controller.signal })

// Cancel after timeout
setTimeout(() => controller.abort(), 5000)

// Or on user action
button.addEventListener('click', () => controller.abort())
```

## Functional Programming

### Pure Functions

Functions that don't mutate state and have no side effects:

```javascript
// WRONG: Mutates input
function processCart(cart) {
  cart.total += 100
  return cart
}

// CORRECT: Returns new object
function addDiscount(cart, amount) {
  return {
    ...cart,
    total: cart.total - amount
  }
}
```

### Array Methods (Immutable)

```javascript
const users = [
  { id: 1, name: 'John', active: true },
  { id: 2, name: 'Jane', active: false }
]

// Transform immutably
const names = users.map(u => u.name)
const active = users.filter(u => u.active)
const byId = users.reduce((map, u) => ({ ...map, [u.id]: u }), {})

// Chain operations
const result = users
  .filter(u => u.active)
  .map(u => u.name)
  .sort()
  .join(', ')
```

### Function Composition

```javascript
// Pipe: left-to-right
const pipe = (...fns) => x => fns.reduce((acc, fn) => fn(acc), x)

// Compose: right-to-left
const compose = (...fns) => x => fns.reduceRight((acc, fn) => fn(acc), x)

// Usage
const processUser = pipe(
  trim,
  toLowercase,
  validate
)
```

## Module Patterns

### ESM (Preferred)

Use ES modules for all new code:

```javascript
// Named exports (tree-shakeable)
export function add(a, b) { return a + b }
export const PI = 3.14159

// Import what you need
import { add, PI } from './math.js'

// Default exports only when returning a single main value
export default class Logger { }
```

### Dynamic Imports

Code splitting on demand:

```javascript
// Load heavy module only when needed
button.addEventListener('click', async () => {
  const { expensiveOperation } = await import('./heavy-module.js')
  expensiveOperation()
})
```

## Class Best Practices

### Private Fields

```javascript
class User {
  #password // Private field
  #token

  constructor(name, password) {
    this.name = name
    this.#password = password
  }

  #hashPassword(password) {
    return `hash_${password}`
  }

  verify(password) {
    return this.#password === password
  }
}
```

### Static Members

```javascript
class Counter {
  static count = 0

  static createGuest() {
    return new Counter()
  }

  constructor() {
    Counter.count++
  }
}
```

## Input Validation

Always validate at system boundaries:

```javascript
// Bad data - validate it
function processPayment(data) {
  if (!data.amount || typeof data.amount !== 'number') {
    throw new Error('Invalid amount')
  }
  if (!data.cardToken || typeof data.cardToken !== 'string') {
    throw new Error('Invalid card token')
  }
  // Process payment
}

// Or use schema validation
import { z } from 'zod'

const paymentSchema = z.object({
  amount: z.number().min(0.01),
  cardToken: z.string().min(1)
})

const validated = paymentSchema.parse(data)
```

## Anti-Patterns

```javascript
// WRONG: Using == (type coercion)
if (value == null) { } // Catches null and undefined
if (count == '5') { } // Unexpected true

// CORRECT: Use === (strict equality)
if (value === null || value === undefined) { }
if (count === 5) { }

// WRONG: Using arguments object
function sum() {
  let total = 0
  for (let i = 0; i < arguments.length; i++) {
    total += arguments[i]
  }
  return total
}

// CORRECT: Use rest parameters
function sum(...numbers) {
  return numbers.reduce((a, b) => a + b, 0)
}

// WRONG: Silent errors
try {
  riskyOperation()
} catch (error) {
  // Silently swallowed!
}

// CORRECT: Handle or re-throw
try {
  riskyOperation()
} catch (error) {
  console.error('Operation failed:', error)
  throw error
}
```

## Performance Optimization

### Debounce and Throttle

```javascript
function debounce(fn, delay) {
  let timeoutId
  return (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

const debouncedSearch = debounce(query => {
  fetch(`/api/search?q=${query}`)
}, 300)

// Usage
searchInput.addEventListener('input', e => {
  debouncedSearch(e.target.value)
})
```

## Agent Support

- **javascript-expert** — ES2022+ patterns and modern JavaScript
- **react-expert** — React-specific patterns with modern JavaScript
- **nodejs-expert** — Node.js runtime and async patterns
- **typescript-expert** — Type-safe JavaScript with TypeScript

## Skill References

- **modern-javascript** — ES2022+ features, async patterns, functional programming
- **javascript-testing** — Testing modern JavaScript code with Vitest/Jest
- **typescript-scaffold** — Setting up TypeScript in JavaScript projects
