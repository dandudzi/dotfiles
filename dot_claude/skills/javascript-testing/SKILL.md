---
name: javascript-testing
description: Implement comprehensive testing strategies using Vitest, Jest, and Testing Library for unit, integration, and E2E testing with mocking, fixtures, and TDD workflows.
origin: ECC
model: sonnet
---

# JavaScript Testing Patterns

## When to Activate
- Writing unit, integration, or E2E tests
- Mocking external dependencies (modules, APIs, globals)
- Testing React/Vue components and hooks

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


### Testing Classes

```typescript
describe("UserService", () => {
  let service: UserService;

  beforeEach(() => {
    service = new UserService();
  });

  it("should create and retrieve user", () => {
    const user = { id: "1", name: "John" };
    service.create(user);
    expect(service.findById("1")).toEqual(user);
  });

  it("should throw if user exists", () => {
    service.create({ id: "1", name: "John" });
    expect(() => service.create({ id: "1", name: "John" }))
      .toThrow("User already exists");
  });
});
```


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


## Async Testing

### Testing Promises and Async/Await

```typescript
describe("fetchUser", () => {
  it("should fetch user", async () => {
    const user = await fetchUser("1");
    expect(user.id).toBe("1");
  });

  it("should throw on error", async () => {
    await expect(fetchUser("invalid")).rejects.toThrow("Not found");
  });
});
```


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


## Mocking Patterns

### Mocking Functions with `vi.fn()`

```typescript
describe("OrderService", () => {
  let service: OrderService;

  beforeEach(() => {
    const logger = { info: vi.fn(), error: vi.fn() };
    const emailService = { sendConfirmation: vi.fn().mockResolvedValue(undefined) };
    service = new OrderService(logger, emailService);
  });

  it("should process order", async () => {
    await service.processOrder({ id: "123", items: [] });
    expect(logger.info).toHaveBeenCalledWith("Processing order 123");
  });
});
```


### Mocking Modules

```typescript
vi.mock("./database");

describe("getUserProfile", () => {
  it("should fetch and enrich user", async () => {
    vi.mocked(getUser).mockResolvedValue({ id: "1", name: "John" });
    const result = await getUserProfile("1");
    expect(result.profile).toBe(true);
  });
});
```


### Spying on Existing Functions

```typescript
it("should log progress", () => {
  const infoSpy = vi.spyOn(logger, "info");
  process();
  expect(infoSpy).toHaveBeenCalledWith("Starting");
  expect(infoSpy).toHaveBeenCalledTimes(2);
  infoSpy.mockRestore();
});
```


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


## Dependency Injection for Testing

```typescript
describe("UserService", () => {
  let service: UserService;
  let mockRepo: IUserRepository;

  beforeEach(() => {
    mockRepo = { findById: vi.fn(), create: vi.fn() };
    service = new UserService(mockRepo);
  });

  it("should return user", async () => {
    vi.mocked(mockRepo.findById).mockResolvedValue({ id: "1", name: "John" });
    const user = await service.getUser("1");
    expect(user.id).toBe("1");
  });
});
```


## Test Fixtures and Factories

```typescript
export function createUser(overrides?: Partial<User>): User {
  return {
    id: faker.string.uuid(),
    name: faker.person.fullName(),
    email: faker.internet.email(),
    ...overrides
  };
}

describe("UserService", () => {
  it("should process user", () => {
    const user = createUser({ email: "test@example.com" });
    expect(user.email).toBe("test@example.com");
  });
});
```


## React Component Testing

### Testing Components

```typescript
describe("Button", () => {
  it("should render with label", () => {
    render(<Button label="Click me" onClick={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Click me" })).toBeInTheDocument();
  });

  it("should call onClick on click", () => {
    const onClick = vi.fn();
    render(<Button label="Click" onClick={onClick} />);
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
```


### Testing Hooks

```typescript
describe("useCounter", () => {
  it("should initialize with default", () => {
    const { result } = renderHook(() => useCounter());
    expect(result.current.count).toBe(0);
  });

  it("should increment", () => {
    const { result } = renderHook(() => useCounter());
    act(() => result.current.increment());
    expect(result.current.count).toBe(1);
  });
});
```


## Anti-Patterns

- Test observable behavior, not implementation details. Use `screen` queries instead of `getByTestId` for accessibility.
- Always call `vi.clearAllMocks()` in `beforeEach()` to prevent test pollution.
- Test your code, not third-party libraries. Trust that lodash/other deps are tested.

## Coverage Best Practices

Configure `vitest.config.ts` with 80% thresholds for lines, functions, branches, and statements. Exclude test files and type definitions. Run `npm run test:coverage` to verify.


## Test Organization

Co-locate unit tests next to source files (`*.test.ts`), group integration tests in `__tests__/integration/`, and E2E tests in `e2e/`.

## Key Practices

- **Coverage**: Minimum 80% line + branch coverage. Use `vitest --coverage` with `@vitest/coverage-v8`.
- **Fixtures**: Use factory functions over shared mutable fixtures to prevent interdependencies.
- **Async**: Use `async/await` in test bodies; `vi.useFakeTimers()` for debounce/throttle tests.
- **HTTP**: Use **MSW** (Mock Service Worker) for HTTP mocking, never mock fetch/axios directly.
- **E2E**: Use **Playwright** for critical user flows. See `e2e-testing` skill.
