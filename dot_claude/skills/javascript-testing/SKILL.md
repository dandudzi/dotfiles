---
name: javascript-testing
description: Implement comprehensive testing strategies using Vitest, Jest, and Testing Library for unit, integration, and E2E testing with mocking, fixtures, and TDD workflows.
origin: ECC
---

# JavaScript Testing Patterns

## When to Activate
- Setting up test infrastructure for new projects
- Writing unit tests for functions and classes
- Creating integration tests for APIs and databases
- Testing async code and promises
- Mocking external dependencies (modules, APIs, globals)
- Testing React/Vue components and hooks
- Implementing test-driven development (TDD)
- Debugging flaky or failing tests

## Test Framework Setup

### Vitest Configuration (Recommended)

```typescript
// vitest.config.ts  (Vitest 4.x)
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true, // Use describe/it without imports
    environment: "node", // or "jsdom" for browser APIs
    setupFiles: ["./src/test/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      exclude: [
        "**/*.d.ts",
        "**/*.config.ts",
        "**/dist/**",
        "**/.test.ts"
      ],
      lines: 80,
      functions: 80,
      branches: 80,
      statements: 80
    },
    include: ["**/*.test.ts", "**/*.spec.ts"]
  }
});
```

**Use when**: Need fast test execution (Vite-native), parallelization, and modern TypeScript support.

## Unit Testing Patterns

### Testing Pure Functions

```typescript
// sum.ts
export function sum(a: number, b: number): number {
  return a + b;
}

export function divide(a: number, b: number): number {
  if (b === 0) throw new Error("Division by zero");
  return a / b;
}

// sum.test.ts
describe("sum", () => {
  it("should add two positive numbers", () => {
    expect(sum(2, 3)).toBe(5);
  });

  it("should handle negative numbers", () => {
    expect(sum(-2, -3)).toBe(-5);
  });

  it("should handle zero", () => {
    expect(sum(0, 5)).toBe(5);
  });
});

describe("divide", () => {
  it("should return correct result", () => {
    expect(divide(10, 2)).toBe(5);
  });

  it("should throw on division by zero", () => {
    expect(() => divide(10, 0)).toThrow("Division by zero");
  });
});
```

**Use when**: Testing deterministic functions with no side effects.

### Testing Classes

```typescript
// UserService.ts
export class UserService {
  private users = new Map<string, User>();

  create(user: User): User {
    if (this.users.has(user.id)) {
      throw new Error("User already exists");
    }
    this.users.set(user.id, user);
    return user;
  }

  findById(id: string): User | undefined {
    return this.users.get(id);
  }

  update(id: string, updates: Partial<User>): User {
    const user = this.users.get(id);
    if (!user) throw new Error("User not found");
    const updated = { ...user, ...updates };
    this.users.set(id, updated);
    return updated;
  }
}

// UserService.test.ts
describe("UserService", () => {
  let service: UserService;

  beforeEach(() => {
    service = new UserService();
  });

  it("should create user and retrieve it", () => {
    const user = { id: "1", name: "John", email: "john@example.com" };
    service.create(user);

    expect(service.findById("1")).toEqual(user);
  });

  it("should throw error if user exists", () => {
    const user = { id: "1", name: "John", email: "john@example.com" };
    service.create(user);

    expect(() => service.create(user)).toThrow("User already exists");
  });

  it("should update user", () => {
    const user = { id: "1", name: "John", email: "john@example.com" };
    service.create(user);

    const updated = service.update("1", { name: "Jane" });

    expect(updated.name).toBe("Jane");
    expect(updated.email).toBe("john@example.com");
  });
});
```

**Use when**: Isolating class state with beforeEach for clean test instances.

### Parametrized Tests

```typescript
describe("Calculator", () => {
  // Test multiple inputs with test.each
  describe.each([
    { a: 1, b: 1, expected: 2 },
    { a: 2, b: 3, expected: 5 },
    { a: -1, b: 1, expected: 0 },
    { a: 0, b: 0, expected: 0 }
  ])("add($a, $b)", ({ a, b, expected }) => {
    it(`should return ${expected}`, () => {
      expect(add(a, b)).toBe(expected);
    });
  });
});
```

**Use when**: Testing the same function with many input variations.

## Async Testing

### Testing Promises and Async/Await

```typescript
// api.ts
export async function fetchUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) throw new Error("Not found");
  return response.json();
}

// api.test.ts
describe("fetchUser", () => {
  // Using async/await
  it("should fetch user", async () => {
    const user = await fetchUser("1");
    expect(user.id).toBe("1");
  });

  // Testing rejection
  it("should throw on error response", async () => {
    await expect(fetchUser("invalid")).rejects.toThrow("Not found");
  });

  // Testing with timeout
  it("should timeout", async () => {
    vi.useFakeTimers();
    const promise = fetchUser("1");
    vi.advanceTimersByTime(5000);
    await expect(promise).rejects.toThrow();
    vi.useRealTimers();
  });
});
```

**Use when**: Testing code that uses promises or async/await.

### Testing Timers

```typescript
describe("debounce", () => {
  it("should debounce function calls", () => {
    vi.useFakeTimers();
    const fn = vi.fn();
    const debounced = debounce(fn, 300);

    debounced();
    debounced();
    debounced();

    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(299);
    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(fn).toHaveBeenCalledOnce();

    vi.useRealTimers();
  });
});
```

**Use when**: Testing functions with delays or intervals.

## Mocking Patterns

### Mocking Functions with `vi.fn()`

```typescript
// orders.ts
export class OrderService {
  constructor(private logger: Logger, private emailService: EmailService) {}

  async processOrder(order: Order): Promise<void> {
    this.logger.info(`Processing order ${order.id}`);
    await this.emailService.sendConfirmation(order);
    this.logger.info(`Order ${order.id} sent`);
  }
}

// orders.test.ts
describe("OrderService", () => {
  let service: OrderService;
  let logger: Logger;
  let emailService: EmailService;

  beforeEach(() => {
    logger = {
      info: vi.fn(),
      error: vi.fn()
    };
    emailService = {
      sendConfirmation: vi.fn().mockResolvedValue(undefined)
    };
    service = new OrderService(logger, emailService);
  });

  it("should process order and log steps", async () => {
    await service.processOrder({ id: "123", items: [] });

    expect(logger.info).toHaveBeenCalledWith("Processing order 123");
    expect(emailService.sendConfirmation).toHaveBeenCalled();
    expect(logger.info).toHaveBeenLastCalledWith("Order 123 sent");
  });

  it("should handle email failure", async () => {
    emailService.sendConfirmation.mockRejectedValueOnce(
      new Error("Email failed")
    );

    await expect(service.processOrder({ id: "123", items: [] }))
      .rejects.toThrow("Email failed");
  });
});
```

**Use when**: Injecting mock implementations as dependencies.

### Mocking Modules

```typescript
// database.ts
export async function getUser(id: string) {
  // Real database call
  const result = await db.query("SELECT * FROM users WHERE id = ?", [id]);
  return result[0];
}

// services.ts
import { getUser } from "./database";

export async function getUserProfile(id: string) {
  const user = await getUser(id);
  return { ...user, profile: true };
}

// services.test.ts
import { vi } from "vitest";

vi.mock("./database");

describe("getUserProfile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch and enrich user", async () => {
    const mockUser = { id: "1", name: "John" };
    vi.mocked(getUser).mockResolvedValue(mockUser);

    const result = await getUserProfile("1");

    expect(result).toEqual({ ...mockUser, profile: true });
    expect(getUser).toHaveBeenCalledWith("1");
  });
});
```

**Use when**: Replacing entire module implementations.

### Spying on Existing Functions

```typescript
// logger.ts
export const logger = {
  info: (msg: string) => console.log(`INFO: ${msg}`),
  error: (msg: string) => console.error(`ERROR: ${msg}`)
};

// service.ts
import { logger } from "./logger";

export function process() {
  logger.info("Starting");
  // ... work ...
  logger.info("Done");
}

// service.test.ts
import { vi } from "vitest";
import { logger } from "./logger";

describe("process", () => {
  it("should log progress", () => {
    const infoSpy = vi.spyOn(logger, "info");

    process();

    expect(infoSpy).toHaveBeenCalledWith("Starting");
    expect(infoSpy).toHaveBeenCalledWith("Done");
    expect(infoSpy).toHaveBeenCalledTimes(2);

    infoSpy.mockRestore();
  });
});
```

**Use when**: Observing calls to real functions without replacing them.

### Mocking Global Functions

```typescript
describe("withTimeout", () => {
  it("should reject on timeout", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(() =>
      new Promise(() => { }) // Never resolves
    ));

    const promise = withTimeout(fetch("/data"), 1000);

    vi.advanceTimersByTime(1000);

    await expect(promise).rejects.toThrow("Timeout");
  });
});
```

**Use when**: Replacing built-in or global APIs.

## Dependency Injection for Testing

```typescript
// user.service.ts
export interface IUserRepository {
  findById(id: string): Promise<User | null>;
  create(user: User): Promise<User>;
}

export class UserService {
  constructor(private repo: IUserRepository) {}

  async getUser(id: string): Promise<User> {
    const user = await this.repo.findById(id);
    if (!user) throw new Error("Not found");
    return user;
  }
}

// user.service.test.ts
describe("UserService", () => {
  let service: UserService;
  let mockRepo: IUserRepository;

  beforeEach(() => {
    mockRepo = {
      findById: vi.fn(),
      create: vi.fn()
    };
    service = new UserService(mockRepo);
  });

  it("should return user", async () => {
    const mockUser = { id: "1", name: "John" };
    vi.mocked(mockRepo.findById).mockResolvedValue(mockUser);

    const user = await service.getUser("1");

    expect(user).toEqual(mockUser);
  });

  it("should throw if not found", async () => {
    vi.mocked(mockRepo.findById).mockResolvedValue(null);

    await expect(service.getUser("999")).rejects.toThrow("Not found");
  });
});
```

**Use when**: Testing classes with external dependencies.

## Test Fixtures and Factories

```typescript
// user.fixture.ts
import { faker } from "@faker-js/faker";

export function createUser(overrides?: Partial<User>): User {
  return {
    id: faker.string.uuid(),
    name: faker.person.fullName(),
    email: faker.internet.email(),
    createdAt: faker.date.past(),
    ...overrides
  };
}

export function createUsers(count: number): User[] {
  return Array.from({ length: count }, () => createUser());
}

// user.service.test.ts
import { createUser } from "./user.fixture";

describe("UserService", () => {
  it("should process user", () => {
    const user = createUser({ email: "test@example.com" });

    expect(user.email).toBe("test@example.com");
    expect(user.id).toBeDefined();
  });

  it("should handle multiple users", () => {
    const users = createUsers(5);
    expect(users).toHaveLength(5);
  });
});
```

**Use when**: Creating consistent test data across multiple tests.

## React Component Testing

### Testing Components

```typescript
// Button.tsx
interface Props {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

export function Button({ label, onClick, disabled }: Props) {
  return (
    <button onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
}

// Button.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Button } from "./Button";

describe("Button", () => {
  it("should render with label", () => {
    render(<Button label="Click me" onClick={vi.fn()} />);

    expect(screen.getByRole("button", { name: "Click me" }))
      .toBeInTheDocument();
  });

  it("should call onClick on click", () => {
    const onClick = vi.fn();
    render(<Button label="Click" onClick={onClick} />);

    fireEvent.click(screen.getByRole("button"));

    expect(onClick).toHaveBeenCalledOnce();
  });

  it("should be disabled when prop is true", () => {
    render(<Button label="Disabled" onClick={vi.fn()} disabled />);

    expect(screen.getByRole("button")).toBeDisabled();
  });
});
```

**Use when**: Testing component rendering and user interactions.

### Testing Hooks

```typescript
// useCounter.ts
export function useCounter(initial = 0) {
  const [count, setCount] = useState(initial);
  return {
    count,
    increment: () => setCount(c => c + 1),
    decrement: () => setCount(c => c - 1),
    reset: () => setCount(initial)
  };
}

// useCounter.test.ts
import { renderHook, act } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { useCounter } from "./useCounter";

describe("useCounter", () => {
  it("should initialize with default value", () => {
    const { result } = renderHook(() => useCounter());
    expect(result.current.count).toBe(0);
  });

  it("should increment", () => {
    const { result } = renderHook(() => useCounter());

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });

  it("should reset", () => {
    const { result } = renderHook(() => useCounter(10));

    act(() => {
      result.current.increment();
      result.current.reset();
    });

    expect(result.current.count).toBe(10);
  });
});
```

**Use when**: Testing custom React hooks in isolation.

## Anti-Patterns

```typescript
// BAD: Testing implementation details
it("should update internal state", () => {
  // Testing internal component state, not behavior
  const { result } = renderHook(() => useState(0));
  expect(result.current[0]).toBe(0);
});

// GOOD: Test observable behavior
it("should increment displayed count", () => {
  render(<Counter />);
  fireEvent.click(screen.getByRole("button"));
  expect(screen.getByText("1")).toBeInTheDocument();
});

// BAD: Using getByTestId excessively
it("should render form", () => {
  render(<UserForm />);
  expect(screen.getByTestId("name-input")).toBeInTheDocument();
});

// GOOD: Use accessible queries
it("should render form", () => {
  render(<UserForm />);
  expect(screen.getByLabelText("Name")).toBeInTheDocument();
});

// BAD: Not cleaning up mocks
describe("Service", () => {
  it("test 1", () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true });
    // Mock persists
  });

  it("test 2", () => {
    // Sees previous mock!
  });
});

// GOOD: Clear mocks between tests
describe("Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("test 1", () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true });
  });

  it("test 2", () => {
    // Fresh start
  });
});

// BAD: Testing third-party code
it("should use lodash", () => {
  expect(_.isEmpty({})).toBe(true);
});

// GOOD: Test your code, trust the library
it("should handle empty collections", () => {
  const result = myFunction([]);
  expect(result).toBeEmpty();
});
```

## Coverage Best Practices

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.d.ts",
        "src/**/*.test.ts",
        "src/**/*.mock.ts"
      ],
      lines: 80,
      functions: 80,
      branches: 80,
      statements: 80,
      ignoreEmpty: true
    }
  }
});

// Run coverage
// npm run test:coverage
```

**Use when**: Setting coverage thresholds to maintain code quality.

## Agent Support
- **vitest-expert** — Vitest configuration, mocking strategies, and advanced patterns
- **react-expert** — React component and hook testing strategies
- **typescript-expert** — Type-safe test patterns and assertion helpers

## Skill References
- **modern-javascript-patterns** — Async/functional patterns used in tests
- **typescript-advanced-types** — Type utilities for test fixtures and mocking
