---
name: python-design-patterns
description: Creational, structural, and behavioral design patterns in Python with focus on Pythonic idioms, dataclasses, protocols, and modern Python 3.9+ features.
origin: ECC
model: sonnet
---

# Python Design Patterns

## When to Activate

- Implementing flexible object creation (Factory, Builder, Singleton)
- Wrapping incompatible interfaces (Adapter, Decorator, Facade)
- Encapsulating complex behavior (Strategy, Observer, Command, Template Method)
- Building plugin architectures (\_\_init_subclass\_\_, Registry pattern)
- Working with context managers and resource management
- Designing property getters/setters with descriptors
- Using dataclasses effectively for immutable/frozen objects

## Creational Patterns

### Factory Patterns

Centralize object creation. Use factory functions for simple cases, class methods for parameterized construction.

```python
from abc import ABC, abstractmethod
from enum import Enum

class DatabaseType(Enum):
    POSTGRES = "postgres"
    SQLITE = "sqlite"

class Database(ABC):
    @abstractmethod
    def query(self, sql: str) -> list: pass

class PostgresDB(Database):
    def query(self, sql: str) -> list:
        return f"Executing on PostgreSQL: {sql}"

class SQLiteDB(Database):
    def query(self, sql: str) -> list:
        return f"Executing on SQLite: {sql}"

# Factory function
def create_database(db_type: DatabaseType) -> Database:
    factories = {DatabaseType.POSTGRES: PostgresDB, DatabaseType.SQLITE: SQLiteDB}
    return factories[db_type]()

db = create_database(DatabaseType.POSTGRES)

# Class method factory (for parameterized construction)
class Database:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    @classmethod
    def from_postgres(cls, host: str, user: str, password: str):
        """Construct from credentials."""
        return cls(f"postgresql://{user}:{password}@{host}")

db = Database.from_postgres("localhost", "admin", "secret")
```

**Decision:** Use dict-based factory for enums; class methods for builder-like construction; avoid Abstract Factory unless multiple families needed.

### Builder Pattern

Construct complex objects step-by-step with fluent API. Use dataclasses with defaults for modern Python.

```python
from dataclasses import dataclass, field

@dataclass
class Request:
    method: str
    url: str
    headers: dict = field(default_factory=dict)  # Mutable default safe
    timeout: int = 30
    retries: int = 0
    auth: tuple | None = None

    def validate(self) -> None:
        if not self.method or not self.url:
            raise ValueError("method and url required")

# Fluent-style construction (readable alternative)
request = Request(
    method="GET",
    url="http://api.example.com",
    headers={"Accept": "application/json"},
    timeout=60,
    retries=3
)
request.validate()
```

**Why:** Dataclasses reduce boilerplate vs. manual builder classes. Named params ≈ fluent API.

### Singleton

Ensure only one instance exists. Prefer module-level instances (simplest) or `@lru_cache` (testable).

```python
# Option 1: Module-level singleton (PREFERRED)
class _Config:
    def __init__(self):
        self.data = {}

config = _Config()  # Single instance at module load

# Option 2: @lru_cache for factories
from functools import lru_cache

@lru_cache(maxsize=1)
def get_database():
    """Singleton with lazy initialization."""
    return Database()

# Option 3: Metaclass (if inheritance needed)
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Database(metaclass=Singleton): pass
```

**Why:** Module singletons are testable (reassign); lru_cache is lazy; metaclass for complex inheritance.

## Structural Patterns

### Decorator

Add behavior without modifying original. Key: use `@wraps` to preserve metadata.

```python
from functools import wraps
import time

def retry(max_attempts: int = 3, delay: float = 1):
    """Parameterized decorator: retry on exception."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1: raise
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=3)
def unstable_call(url: str):
    return httpx.get(url).json()

# Stack decorators: applied bottom-up
@log_calls
@time_execution
def process(data):
    return len(data)
```

**For class __init__ validation:** Use dataclass validation or `__post_init__` instead of decorator.

### Adapter

Wrap incompatible interfaces to work together.

```python
class StripeAPI:
    def charge_card(self, amount_cents: int, token: str) -> dict:
        return {"status": "success"}

# Adapter converts Stripe → PaymentProcessor interface
class StripeAdapter:
    def __init__(self, stripe: StripeAPI, token: str):
        self.stripe = stripe
        self.token = token

    def process_payment(self, amount: float) -> bool:
        result = self.stripe.charge_card(int(amount * 100), self.token)
        return result["status"] == "success"

processor = StripeAdapter(StripeAPI(), "tok_123")
success = processor.process_payment(19.99)
```

**For partial delegation:** Use `__getattr__` to forward missing methods to wrapped object.

### Facade

Simplify complex subsystems with a unified interface.

```python
class NotificationFacade:
    def __init__(self):
        self.email = EmailService()
        self.sms = SMSService()
        self.slack = SlackService()

    def notify_user(self, user: dict, message: str):
        """Single method hides three underlying services."""
        self.email.send(user["email"], message)
        self.sms.send(user["phone"], message)
        self.slack.post(user["slack_channel"], message)

notifier = NotificationFacade()
notifier.notify_user({"email": "alice@example.com", "phone": "+1234567890", "slack_channel": "#alerts"}, "Alert")
```

## Behavioral Patterns

### Strategy

Encapsulate algorithms as interchangeable objects. Replaces if/elif chains with composition.

```python
from typing import Protocol

# Protocol for type-safe duck typing
class DiscountStrategy(Protocol):
    def calculate(self, amount: float) -> float: ...

class PremiumDiscount:
    def calculate(self, amount: float) -> float:
        return amount * 0.2

class GuestDiscount:
    def calculate(self, amount: float) -> float:
        return 0

class Order:
    def __init__(self, amount: float, strategy: DiscountStrategy):
        self.amount = amount
        self.strategy = strategy

    def get_total(self) -> float:
        discount = self.strategy.calculate(self.amount)
        return self.amount - discount

premium = Order(100, PremiumDiscount())
guest = Order(100, GuestDiscount())
print(premium.get_total())  # 80
```

**Why:** New strategies don't require modifying Order. Replaces if/elif conditionals.

### Observer

Implement publish/subscribe for decoupled event handling.

```python
from typing import Callable, Any

class EventBus:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}

    def subscribe(self, event: str, callback: Callable):
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event: str, data: Any = None):
        for callback in self._listeners.get(event, []):
            callback(data)

bus = EventBus()
bus.subscribe("user_created", lambda user: print(f"User: {user['name']}"))
bus.emit("user_created", {"name": "Alice"})
```

**For method subscriptions:** Use `weakref.WeakMethod` to prevent memory leaks when unsubscribing is unreliable.

### Command

Encapsulate requests as objects for undo/redo. Especially useful for UI actions and transaction queues.

```python
from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self): pass
    @abstractmethod
    def undo(self): pass

class AddItemCommand(Command):
    def __init__(self, cart: list, item: str):
        self.cart, self.item = cart, item
    def execute(self): self.cart.append(self.item)
    def undo(self): self.cart.remove(self.item)

class CommandHistory:
    def __init__(self):
        self._history = []
    def execute(self, cmd: Command):
        cmd.execute()
        self._history.append(cmd)
    def undo(self):
        if self._history:
            self._history.pop().undo()

cart = []
h = CommandHistory()
h.execute(AddItemCommand(cart, "Apple"))
print(cart)  # ['Apple']
h.undo()
print(cart)  # []
```

### Template Method

Define algorithm skeleton; subclasses implement abstract steps.

```python
from abc import ABC, abstractmethod

class ReportGenerator(ABC):
    def generate(self) -> str:
        """Template: fixed sequence of steps."""
        return f"{self._header()}\n{self._body()}\n{self._footer()}"

    @abstractmethod
    def _header(self) -> str: pass
    @abstractmethod
    def _body(self) -> str: pass
    def _footer(self) -> str:
        return "Report generated"  # Hook: optional override

class PDFReport(ReportGenerator):
    def _header(self) -> str: return "PDF_HEADER"
    def _body(self) -> str: return "PDF_BODY"

class HTMLReport(ReportGenerator):
    def _header(self) -> str: return "<html>"
    def _body(self) -> str: return "<body>Content</body>"
    def _footer(self) -> str: return "</html>"

pdf = PDFReport()
print(pdf.generate())
```

## Python-Specific Patterns

### Context Manager

Manage resource acquisition/release safely with `__enter__/__exit__` or `@contextmanager`.

```python
from contextlib import contextmanager

# Class-based
class DatabaseConnection:
    def __init__(self, url: str):
        self.url = url
        self.conn = None

    def __enter__(self):
        self.conn = f"Connected to {self.url}"
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn = None  # Cleanup always runs, even on exception
        return False  # Don't suppress exceptions

with DatabaseConnection("postgres://localhost") as conn:
    print(conn)

# Decorator-based (simpler for simple cases)
@contextmanager
def transaction(connection_string: str):
    print(f"BEGIN {connection_string}")
    try:
        yield connection_string
    except Exception:
        print("ROLLBACK")
        raise
    else:
        print("COMMIT")

with transaction("db") as conn:
    pass
```

### Descriptor

Control attribute access via `__get__`, `__set__`, `__delete__`. Primary use: validation.

```python
class ValidatedString:
    def __init__(self, name: str):
        self.name = name
    def __get__(self, obj, objtype=None):
        return obj.__dict__.get(self.name, "") if obj else self
    def __set__(self, obj, value: str):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{self.name} must be non-empty string")
        obj.__dict__[self.name] = value

class User:
    name = ValidatedString("name")
    def __init__(self, name: str):
        self.name = name

user = User("Alice")
user.name = "Bob"  # Calls __set__

# Use @property for computed/validated properties (simpler alternative)
class Temperature:
    def __init__(self, celsius: float):
        self._celsius = celsius
    @property
    def celsius(self) -> float: return self._celsius
    @celsius.setter
    def celsius(self, value: float):
        if value < -273.15: raise ValueError("Below absolute zero")
        self._celsius = value
    @property
    def fahrenheit(self) -> float: return self._celsius * 9/5 + 32
```

### __init_subclass__ for Plugins

Auto-register subclasses without manual registry.

```python
from abc import ABC, abstractmethod

class Plugin(ABC):
    subclasses = {}
    def __init_subclass__(cls, name: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.subclasses[name or cls.__name__] = cls
    @abstractmethod
    def execute(self): pass

class MailPlugin(Plugin, name="mail"):
    def execute(self): print("Mail")

class SlackPlugin(Plugin, name="slack"):
    def execute(self): print("Slack")

# No registry needed; dynamic loading
plugin = Plugin.subclasses["mail"]()
plugin.execute()
```

### Dataclass Patterns

Modern immutable objects, builders, and type-safe configuration.

```python
from dataclasses import dataclass, field, asdict
from typing import ClassVar

@dataclass(frozen=True)  # Immutable; hashable
class Point:
    x: float
    y: float

@dataclass  # Mutable with defaults
class Config:
    debug: bool = False
    timeout: int = 30
    tags: list = field(default_factory=list)  # Prevents shared default
    API_VERSION: ClassVar[str] = "v1"  # Class-level constant

cfg = Config(timeout=60)
print(asdict(cfg))  # Convert to dict
```

## Anti-Patterns

- **Don't overuse Singleton:** Hard to test (no multiple instances), hard to mock. Use dependency injection instead: `create_app(db_pool: DatabasePool)`. Test with mock: `create_app(MockDatabasePool())`.
- **Don't abuse inheritance:** Prefer composition. Instead of `Animal -> Mammal -> Carnivore -> Feline -> Tiger`, use `@dataclass Animal(diet, reproduction, family)`.
- **Don't add abstraction with only 1 impl:** Wait for 2nd implementation. Premature abstraction adds complexity without benefit.
- **Don't nest patterns:** Avoid `FactoryFactoryBuilderSingleton`. Use simplest pattern: `def create_object(**kwargs): return MyClass(**kwargs)`.

## Related Skills

- **python-resilience** — Decorator retry/timeout patterns
- **python-performance** — Caching with functools.lru_cache
