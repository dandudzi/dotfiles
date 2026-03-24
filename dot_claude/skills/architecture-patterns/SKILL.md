---
name: architecture-patterns
description: Implement proven backend architecture patterns including Clean Architecture, Hexagonal Architecture, and Domain-Driven Design. Use when architecting complex backend systems or refactoring existing applications for better maintainability.
model: opus
---

# Architecture Patterns

Master Clean Architecture, Hexagonal Architecture, and Domain-Driven Design to build maintainable, testable systems.

## When to Use This Skill

- Designing new backend systems or refactoring monolithic applications
- Migrating from tightly coupled to loosely coupled architectures
- Establishing testable, technology-independent domain logic

## Core Concepts

### Clean Architecture
**Layers:** Entities → Use Cases → Adapters → Frameworks (dependencies point inward).
**Goal:** Business logic independent of frameworks; testable without UI, database, or external services.

### Hexagonal Architecture
**Design:** Domain Core at center, Ports (interfaces) define interactions, Adapters (implementations) provide storage, messaging, etc.
**Benefit:** Swap implementations for testing; technology-agnostic domain.

### Domain-Driven Design
**Strategic:** Bounded Contexts (separate models per domain), Ubiquitous Language (shared terminology).
**Tactical:** Entities (identity), Value Objects (immutable attributes), Aggregates (consistency), Repositories (persistence), Domain Events (state changes).

## Clean Architecture Pattern

### Directory Structure

```
app/
├── domain/           # Entities & business rules
│   ├── entities/
│   │   ├── user.py
│   │   └── order.py
│   ├── value_objects/
│   │   ├── email.py
│   │   └── money.py
│   └── interfaces/   # Abstract interfaces
│       ├── user_repository.py
│       └── payment_gateway.py
├── use_cases/        # Application business rules
│   ├── create_user.py
│   ├── process_order.py
│   └── send_notification.py
├── adapters/         # Interface implementations
│   ├── repositories/
│   │   ├── postgres_user_repository.py
│   │   └── redis_cache_repository.py
│   ├── controllers/
│   │   └── user_controller.py
│   └── gateways/
│       ├── stripe_payment_gateway.py
│       └── sendgrid_email_gateway.py
└── infrastructure/   # Framework & external concerns
    ├── database.py
    ├── config.py
    └── logging.py
```

### Example: User Entity & Repository

```python
# domain/entities/user.py — no dependencies
@dataclass
class User:
    id: str
    email: str
    created_at: datetime

    def can_place_order(self) -> bool:
        return self.is_active

# domain/interfaces/user_repository.py — port
class IUserRepository(ABC):
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

# use_cases/create_user.py — use case orchestrates logic
class CreateUserUseCase:
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def execute(self, email: str, name: str) -> User:
        existing = await self.user_repository.find_by_email(email)
        if existing:
            raise ValidationError("Email already exists")

        user = User(id=str(uuid.uuid4()), email=email,
                   created_at=datetime.now())
        return await self.user_repository.save(user)

# adapters/repositories/postgres_user_repository.py — adapter
class PostgresUserRepository(IUserRepository):
    async def save(self, user: User) -> User:
        await self.pool.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)",
            user.id, user.email
        )
        return user
```

## Hexagonal Architecture Example

```python
# Domain service (no infrastructure dependencies)
class OrderService:
    def __init__(self, orders: OrderPort, payments: PaymentPort):
        self.orders = orders
        self.payments = payments

    async def place_order(self, order: Order) -> OrderResult:
        if not order.is_valid():
            return OrderResult(success=False, error="Invalid order")
        payment = await self.payments.charge(order.total)
        if not payment.success:
            return OrderResult(success=False, error="Payment failed")
        return OrderResult(success=True, order=await self.orders.save(order))

# Ports (interfaces)
class OrderPort(ABC):
    @abstractmethod
    async def save(self, order: Order) -> Order:
        pass

class PaymentPort(ABC):
    @abstractmethod
    async def charge(self, amount: Money) -> PaymentResult:
        pass

# Adapters (swap these for testing)
class StripeAdapter(PaymentPort):
    async def charge(self, amount: Money) -> PaymentResult:
        try:
            charge = stripe.Charge.create(amount=amount.cents)
            return PaymentResult(success=True)
        except stripe.error.CardError:
            return PaymentResult(success=False)

class MockAdapter(PaymentPort):
    async def charge(self, amount: Money) -> PaymentResult:
        return PaymentResult(success=True)
```

## Domain-Driven Design Example

```python
# Value Objects (immutable, no identity)
@dataclass(frozen=True)
class Email:
    value: str
    def __post_init__(self):
        if "@" not in self.value:
            raise ValueError("Invalid email")

@dataclass(frozen=True)
class Money:
    amount: int
    currency: str
    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(self.amount + other.amount, self.currency)

# Entities (with identity, mutable)
class Order:
    def __init__(self, id: str, customer_id: str):
        self.id = id
        self.customer_id = customer_id
        self.items = []
        self._events = []

    def add_item(self, product: Product, qty: int):
        self.items.append(OrderItem(product, qty))
        self._events.append(ItemAddedEvent(self.id))

    def submit(self):
        if not self.items:
            raise ValueError("Cannot submit empty order")
        self._events.append(OrderSubmittedEvent(self.id))

# Aggregates (consistency boundary)
class Customer:
    def __init__(self, id: str, email: Email):
        self.id = id
        self.email = email
        self.addresses = []

    def add_address(self, addr: Address):
        if len(self.addresses) >= 5:
            raise ValueError("Max 5 addresses")
        self.addresses.append(addr)

# Repository persists aggregates, not individual entities
class OrderRepository:
    async def save(self, order: Order):
        await self._persist(order)
        await self._publish_events(order._events)
        order._events.clear()
```

---

## Best Practices

**Repository Pattern:** Standard interface (findById / create / update / delete) over storage. Business logic depends on the interface, not the implementation.

**API Response Format:**
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "pagination": { "page": 1, "total": 100 }
}
```
Map exceptions to HTTP status at controller only: `ValidationError` → 400, `AuthError` → 401/403, `NotFoundError` → 404, unexpected → 500.

**Exception Hierarchy:** Define base exception per module, subclass for variants: `BaseError` → `ValidationError`, `NotFoundError`, `AuthError`. Never throw raw built-in exceptions from business logic.

**DTOs:** Separate request/response types at API boundary using Pydantic/Zod/Jakarta Validation. Domain entities flow inside; DTOs are the external contract.

**Dependency Injection:** Constructor injection only. Program to interfaces, not implementations.

**Async Concurrency:** Run independent ops concurrently — `Promise.all()`/`asyncio.gather()`/`CompletableFuture.allOf()`. Apply timeouts to all external I/O.

## Testing Strategy

**Unit Tests:** Test business logic (use cases, value objects, entities) with mocks or test doubles for dependencies. No database, no HTTP. Fast.

**Integration Tests:** Test adapters + repositories against real PostgreSQL (via testcontainers or test fixture). Verify persistence and retrieval.

**E2E Tests:** Test full request → use case → adapter → database → response flow. Small set to verify critical paths only (create, read, update flows).

**Example Test Structure:**
```python
# Test domain logic (pure, no mocks needed)
def test_user_can_place_order():
    user = User(id="1", email="test@example.com")
    assert user.can_place_order() is True

# Test use case with mocked repository
@pytest.mark.asyncio
async def test_create_user_duplicate_email(mock_repo):
    mock_repo.find_by_email.return_value = User(id="1", email="test@example.com")
    use_case = CreateUserUseCase(mock_repo)
    with pytest.raises(ValidationError):
        await use_case.execute("test@example.com", "John")

# Integration test with testcontainers
@pytest.mark.asyncio
async def test_postgres_user_repository(postgres_pool):
    repo = PostgresUserRepository(postgres_pool)
    user = User(id=str(uuid.uuid4()), email="test@example.com", created_at=datetime.now())
    saved = await repo.save(user)
    assert saved.id == user.id
    fetched = await repo.find_by_email(user.email)
    assert fetched.email == user.email
```

## Common Mistakes

**Mixing layers:** Domain logic touches database or HTTP. Fix: Inject repository interfaces into use cases, not implementations.

**Fat entities:** Entities with 20+ fields become hard to reason about. Fix: Split into multiple entities or use value objects for complex attributes.

**No validation:** Accepting invalid data into aggregates. Fix: Validate in value object constructors and aggregate methods.

**Service layer explosion:** Every use case becomes a 500-line god service. Fix: Break into smaller, focused use cases; compose them for complex workflows.
