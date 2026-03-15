---
name: python-design-patterns
description: Creational, structural, and behavioral design patterns in Python with focus on Pythonic idioms, dataclasses, protocols, and modern Python 3.9+ features.
origin: ECC
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

### Pattern 1: Factory Method

Centralize object creation with flexible `create_*` functions.

```python
from abc import ABC, abstractmethod
from enum import Enum

class DatabaseType(Enum):
    POSTGRES = "postgres"
    MYSQL = "mysql"
    SQLITE = "sqlite"

class Database(ABC):
    @abstractmethod
    def query(self, sql: str) -> list:
        pass

class PostgresDB(Database):
    def query(self, sql: str) -> list:
        return f"Executing on PostgreSQL: {sql}"

class MySQLDB(Database):
    def query(self, sql: str) -> list:
        return f"Executing on MySQL: {sql}"

class SQLiteDB(Database):
    def query(self, sql: str) -> list:
        return f"Executing on SQLite: {sql}"

# Factory function
def create_database(db_type: DatabaseType) -> Database:
    """Create appropriate database driver."""
    factories = {
        DatabaseType.POSTGRES: PostgresDB,
        DatabaseType.MYSQL: MySQLDB,
        DatabaseType.SQLITE: SQLiteDB,
    }
    db_class = factories[db_type]
    return db_class()

# Usage
db = create_database(DatabaseType.POSTGRES)
print(db.query("SELECT * FROM users"))

# Class method factory
class DatabaseClassMethod:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    @classmethod
    def from_postgres(cls, host: str, user: str, password: str):
        """Construct PostgreSQL connection."""
        connection_string = f"postgresql://{user}:{password}@{host}"
        return cls(connection_string)

    @classmethod
    def from_sqlite(cls, path: str):
        """Construct SQLite connection."""
        return cls(f"sqlite:///{path}")

# Usage
db = DatabaseClassMethod.from_postgres("localhost", "admin", "secret")
```

### Pattern 2: Builder Pattern

Construct complex objects step-by-step with fluent API.

**WRONG: Many constructor parameters**
```python
class Request:
    def __init__(self, method, url, headers, timeout, retries, auth):
        # 6 parameters = confusing combinations
        self.method = method
        self.url = url
        self.headers = headers
        self.timeout = timeout
        self.retries = retries
        self.auth = auth

# Unclear which params are required
request = Request("GET", "http://api.example.com", {}, 30, 3, None)
```

**CORRECT: Builder with fluent API**
```python
class Request:
    def __init__(self, method: str, url: str):
        self.method = method
        self.url = url
        self.headers = {}
        self.timeout = 30
        self.retries = 0
        self.auth = None

    def set_headers(self, headers: dict) -> "Request":
        """Add headers; return self for chaining."""
        self.headers = headers
        return self

    def set_timeout(self, seconds: int) -> "Request":
        self.timeout = seconds
        return self

    def set_retries(self, count: int) -> "Request":
        self.retries = count
        return self

    def set_auth(self, auth_tuple: tuple) -> "Request":
        self.auth = auth_tuple
        return self

    def build(self) -> "Request":
        """Finalize and return."""
        return self

# Usage: Clear and chainable
request = (Request("GET", "http://api.example.com")
    .set_headers({"Accept": "application/json"})
    .set_timeout(60)
    .set_retries(3)
    .build())
```

**Alternative: Dataclass Builder**
```python
from dataclasses import dataclass, field

@dataclass
class RequestBuilder:
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    timeout: int = 30
    retries: int = 0
    auth: tuple | None = None

    def build(self) -> "RequestBuilder":
        """Validate and return."""
        if not self.method or not self.url:
            raise ValueError("method and url required")
        return self

# Usage
request = RequestBuilder(
    method="GET",
    url="http://api.example.com",
    timeout=60,
    retries=3,
)
```

### Pattern 3: Singleton

Ensure only one instance exists.

**WRONG: Multiple instances**
```python
class Config:
    def __init__(self):
        self.data = {}

config1 = Config()
config2 = Config()
config1.data["debug"] = True
print(config2.data.get("debug"))  # None (different instances!)
```

**CORRECT: Module-level singleton**
```python
# config.py
class _Config:
    def __init__(self):
        self.data = {}

# Create single instance
config = _Config()

# Usage: import and use
from config import config
config.data["debug"] = True

# All files get the same instance
```

**Alternative: Metaclass Singleton**
```python
class Singleton(type):
    """Metaclass ensuring single instance."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Database(metaclass=Singleton):
    def __init__(self):
        self.connection = None

# Usage
db1 = Database()
db2 = Database()
assert db1 is db2  # Same instance
```

**Alternative: @lru_cache for function singletons**
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_database() -> "Database":
    """Singleton database factory."""
    return Database()

db1 = get_database()
db2 = get_database()
assert db1 is db2  # Same cached instance
```

## Structural Patterns

### Pattern 4: Decorator

Add behavior to functions/classes without modifying them.

**Function Decorator with Arguments**
```python
from functools import wraps
from typing import Callable, TypeVar, Any
import time
import logging

logger = logging.getLogger(__name__)
T = TypeVar("T")

def retry_on_exception(max_attempts: int = 3, delay: float = 1):
    """Decorator: retry function on exception."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry_on_exception(max_attempts=3, delay=1)
def unstable_api_call(url: str) -> dict:
    """Automatically retried on exception."""
    import httpx
    return httpx.get(url).json()

# Usage
result = unstable_api_call("http://api.example.com")
```

**Class Decorator**
```python
def validate_inputs(cls):
    """Decorator: validate __init__ inputs."""
    original_init = cls.__init__

    @wraps(original_init)
    def new_init(self, *args, **kwargs):
        # Validation before initialization
        if not kwargs.get("name"):
            raise ValueError("name is required")
        original_init(self, *args, **kwargs)

    cls.__init__ = new_init
    return cls

@validate_inputs
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

# Usage
user = User(name="Alice", email="alice@example.com")
# User(name="", email="bob@example.com")  # Raises ValueError
```

**Stacking Decorators**
```python
def log_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def time_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        print(f"Took {time.time() - start:.4f}s")
        return result
    return wrapper

@log_calls
@time_execution
def process_data(data):
    import time
    time.sleep(1)
    return len(data)

# Usage: decorators applied bottom-up
process_data([1, 2, 3])
# Output:
# Calling process_data
# Took 1.0001s
```

### Pattern 5: Adapter

Wrap incompatible interfaces to work together.

```python
from abc import ABC, abstractmethod

# Target interface (what we want)
class PaymentProcessor(ABC):
    @abstractmethod
    def process_payment(self, amount: float) -> bool:
        pass

# Existing interface (what we have)
class StripeAPI:
    """External API with different interface."""
    def charge_card(self, amount_cents: int, token: str) -> dict:
        return {"status": "success", "amount": amount_cents}

# Adapter
class StripeAdapter(PaymentProcessor):
    """Adapt Stripe API to PaymentProcessor interface."""
    def __init__(self, stripe_api: StripeAPI, token: str):
        self.stripe = stripe_api
        self.token = token

    def process_payment(self, amount: float) -> bool:
        """Convert float dollars to Stripe's integer cents."""
        amount_cents = int(amount * 100)
        result = self.stripe.charge_card(amount_cents, self.token)
        return result["status"] == "success"

# Usage
stripe = StripeAPI()
processor = StripeAdapter(stripe, token="tok_123")
success = processor.process_payment(19.99)
```

**Alternative: Delegation with \_\_getattr\_\_**
```python
class LegacyAPI:
    """Old interface."""
    def get_user_info(self, user_id: int):
        return {"id": user_id, "name": f"User {user_id}"}

class ModernAPI:
    """Expected interface."""
    def __init__(self, legacy: LegacyAPI):
        self._legacy = legacy

    def __getattr__(self, name: str):
        """Delegate missing attributes to legacy."""
        return getattr(self._legacy, name)

    def get_user(self, user_id: int):
        """Modern method name."""
        return self._legacy.get_user_info(user_id)

# Usage
legacy = LegacyAPI()
modern = ModernAPI(legacy)
user = modern.get_user(123)
```

### Pattern 6: Facade

Simplify complex subsystems with a unified interface.

```python
# Complex subsystem
class EmailService:
    def send(self, to: str, body: str) -> bool:
        print(f"Sending email to {to}")
        return True

class SMSService:
    def send(self, phone: str, message: str) -> bool:
        print(f"Sending SMS to {phone}")
        return True

class SlackService:
    def post(self, channel: str, message: str) -> bool:
        print(f"Posting to {channel}")
        return True

# Facade: unified notification API
class NotificationFacade:
    def __init__(self):
        self.email = EmailService()
        self.sms = SMSService()
        self.slack = SlackService()

    def notify_user(self, user: dict, message: str):
        """Notify user via all channels."""
        self.email.send(user["email"], message)
        self.sms.send(user["phone"], message)
        self.slack.post(user["slack_channel"], message)

# Usage: simple interface hides complexity
notifier = NotificationFacade()
notifier.notify_user(
    {"email": "alice@example.com", "phone": "+1234567890", "slack_channel": "#alerts"},
    "System alert"
)
```

## Behavioral Patterns

### Pattern 7: Strategy

Encapsulate algorithms as interchangeable strategies.

**WRONG: if/elif chains**
```python
def calculate_discount(user_type: str, amount: float) -> float:
    if user_type == "premium":
        return amount * 0.2
    elif user_type == "regular":
        return amount * 0.1
    elif user_type == "guest":
        return 0
    else:
        raise ValueError(f"Unknown user type: {user_type}")

# Adding new type = modifying function
```

**CORRECT: Strategy objects**
```python
from abc import ABC, abstractmethod
from typing import Protocol

# Strategy interface
class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, amount: float) -> float:
        pass

class PremiumDiscount(DiscountStrategy):
    def calculate(self, amount: float) -> float:
        return amount * 0.2

class RegularDiscount(DiscountStrategy):
    def calculate(self, amount: float) -> float:
        return amount * 0.1

class GuestDiscount(DiscountStrategy):
    def calculate(self, amount: float) -> float:
        return 0

# Injected strategy
class Order:
    def __init__(self, amount: float, discount_strategy: DiscountStrategy):
        self.amount = amount
        self.strategy = discount_strategy

    def get_total(self) -> float:
        discount = self.strategy.calculate(self.amount)
        return self.amount - discount

# Usage
premium_order = Order(100, PremiumDiscount())
regular_order = Order(100, RegularDiscount())

print(premium_order.get_total())  # 80
print(regular_order.get_total())  # 90

# New strategy = new class, no function changes
```

**Using Protocol for Type Safety (Python 3.8+)**
```python
from typing import Protocol

class DiscountStrategy(Protocol):
    """Protocol (structural typing)."""
    def calculate(self, amount: float) -> float: ...

# Any class with matching method works
class VIPDiscount:
    def calculate(self, amount: float) -> float:
        return amount * 0.3

# Type checker accepts it (duck typing + static checking)
strategy: DiscountStrategy = VIPDiscount()
```

### Pattern 8: Observer

Implement publish/subscribe event system.

```python
from typing import Callable, Any

class EventBus:
    """Publish-subscribe event system."""
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}

    def subscribe(self, event: str, callback: Callable):
        """Register listener for event."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable):
        """Unregister listener."""
        if event in self._listeners:
            self._listeners[event].remove(callback)

    def emit(self, event: str, data: Any = None):
        """Trigger event."""
        if event in self._listeners:
            for callback in self._listeners[event]:
                callback(data)

# Usage
bus = EventBus()

def on_user_created(user_data):
    print(f"User created: {user_data['name']}")

def send_welcome_email(user_data):
    print(f"Sending welcome email to {user_data['email']}")

bus.subscribe("user_created", on_user_created)
bus.subscribe("user_created", send_welcome_email)

# Emit event
bus.emit("user_created", {"name": "Alice", "email": "alice@example.com"})
# Output:
# User created: Alice
# Sending welcome email to alice@example.com
```

**Weak References for Memory Safety**
```python
import weakref

class EventBus:
    """Observer with weak references (prevents memory leaks)."""
    def __init__(self):
        self._listeners: dict[str, list] = {}

    def subscribe(self, event: str, obj: object, method_name: str):
        """Subscribe via weak reference."""
        if event not in self._listeners:
            self._listeners[event] = []

        # Weak reference to method
        weak_ref = weakref.WeakMethod(getattr(obj, method_name))
        self._listeners[event].append(weak_ref)

    def emit(self, event: str, data: Any = None):
        """Trigger event, removing dead references."""
        if event not in self._listeners:
            return

        # Filter out dead references
        alive = []
        for weak_ref in self._listeners[event]:
            callback = weak_ref()
            if callback:
                callback(data)
                alive.append(weak_ref)

        self._listeners[event] = alive
```

### Pattern 9: Command

Encapsulate requests as objects for queuing/undo.

```python
from abc import ABC, abstractmethod
from typing import Any

class Command(ABC):
    @abstractmethod
    def execute(self) -> Any:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass

class AddItemCommand(Command):
    """Add item to shopping cart."""
    def __init__(self, cart: list, item: str):
        self.cart = cart
        self.item = item

    def execute(self) -> None:
        self.cart.append(self.item)

    def undo(self) -> None:
        self.cart.remove(self.item)

class RemoveItemCommand(Command):
    """Remove item from shopping cart."""
    def __init__(self, cart: list, item: str):
        self.cart = cart
        self.item = item

    def execute(self) -> None:
        self.cart.remove(self.item)

    def undo(self) -> None:
        self.cart.append(self.item)

class CommandHistory:
    """Manage command execution and undo."""
    def __init__(self):
        self._history: list[Command] = []

    def execute(self, command: Command) -> None:
        command.execute()
        self._history.append(command)

    def undo(self) -> None:
        if self._history:
            command = self._history.pop()
            command.undo()

# Usage
cart = []
history = CommandHistory()

history.execute(AddItemCommand(cart, "Apple"))
history.execute(AddItemCommand(cart, "Banana"))
print(cart)  # ['Apple', 'Banana']

history.undo()
print(cart)  # ['Apple']

history.undo()
print(cart)  # []
```

### Pattern 10: Template Method

Define algorithm skeleton; subclasses fill in steps.

```python
from abc import ABC, abstractmethod

class ReportGenerator(ABC):
    """Template for report generation."""

    def generate(self) -> str:
        """Template method: defines algorithm steps."""
        header = self._generate_header()
        body = self._generate_body()
        footer = self._generate_footer()
        return f"{header}\n{body}\n{footer}"

    @abstractmethod
    def _generate_header(self) -> str:
        pass

    @abstractmethod
    def _generate_body(self) -> str:
        pass

    def _generate_footer(self) -> str:
        """Hook method: optional override."""
        return "Report generated automatically"

class PDFReport(ReportGenerator):
    def _generate_header(self) -> str:
        return "PDF_HEADER"

    def _generate_body(self) -> str:
        return "PDF_BODY_CONTENT"

class HTMLReport(ReportGenerator):
    def _generate_header(self) -> str:
        return "<html><head>Report</head>"

    def _generate_body(self) -> str:
        return "<body>Content</body>"

    def _generate_footer(self) -> str:
        return "</html>"

# Usage
pdf = PDFReport()
print(pdf.generate())
# PDF_HEADER
# PDF_BODY_CONTENT
# Report generated automatically

html = HTMLReport()
print(html.generate())
# <html><head>Report</head>
# <body>Content</body>
# </html>
```

## Python-Specific Patterns

### Pattern 11: Context Manager

Manage resource acquisition/release safely.

```python
from contextlib import contextmanager
from typing import Iterator

# Class-based
class DatabaseConnection:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None

    def __enter__(self):
        """Acquire resource."""
        print(f"Connecting to {self.connection_string}")
        self.conn = f"Connection to {self.connection_string}"
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release resource (even on exception)."""
        print(f"Closing connection")
        self.conn = None
        return False  # Propagate exception if any

# Usage
with DatabaseConnection("postgres://localhost") as conn:
    print(f"Using {conn}")
    # Connection closed automatically even if exception

# Decorator-based
@contextmanager
def transaction(connection: str) -> Iterator[str]:
    """Context manager as decorator."""
    print(f"BEGIN transaction on {connection}")
    try:
        yield connection  # Code in with block runs here
    except Exception as e:
        print(f"ROLLBACK on {connection}")
        raise
    else:
        print(f"COMMIT on {connection}")

# Usage
with transaction("db_connection") as conn:
    print(f"Executing queries on {conn}")
```

### Pattern 12: Descriptor

Control attribute access with \_\_get\_\_, \_\_set\_\_, \_\_delete\_\_.

```python
class ValidatedString:
    """Descriptor: validate string attribute."""
    def __init__(self, name: str):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.name, "")

    def __set__(self, obj, value: str):
        if not isinstance(value, str):
            raise TypeError(f"{self.name} must be string")
        if len(value) == 0:
            raise ValueError(f"{self.name} cannot be empty")
        obj.__dict__[self.name] = value

class User:
    name = ValidatedString("name")
    email = ValidatedString("email")

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

# Usage
user = User("Alice", "alice@example.com")
print(user.name)  # Alice

user.name = "Bob"  # __set__ called
# user.name = ""  # Raises ValueError
# user.name = 123  # Raises TypeError
```

**Property as Descriptor**
```python
class Temperature:
    def __init__(self, celsius: float):
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        """Getter: read access."""
        return self._celsius

    @celsius.setter
    def celsius(self, value: float):
        """Setter: write access."""
        if value < -273.15:
            raise ValueError("Below absolute zero")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        """Computed property."""
        return self._celsius * 9/5 + 32

# Usage
temp = Temperature(0)
print(temp.celsius)     # 0
print(temp.fahrenheit)  # 32
temp.celsius = 100
print(temp.fahrenheit)  # 212
```

### Pattern 13: \_\_init_subclass\_\_ for Plugins

Register subclasses automatically.

```python
class Plugin(ABC):
    """Base class with automatic subclass registration."""
    subclasses = {}

    def __init_subclass__(cls, name: str = None, **kwargs):
        """Called when subclass is defined."""
        super().__init_subclass__(**kwargs)
        # Register by name
        plugin_name = name or cls.__name__
        cls.subclasses[plugin_name] = cls

    @abstractmethod
    def execute(self) -> None:
        pass

class MailPlugin(Plugin, name="mail"):
    def execute(self):
        print("Sending email")

class SlackPlugin(Plugin, name="slack"):
    def execute(self):
        print("Posting to Slack")

# Usage: no manual registry needed
print(Plugin.subclasses)
# {'mail': <class MailPlugin>, 'slack': <class SlackPlugin>}

# Dynamic loading
plugin_name = "mail"
plugin_class = Plugin.subclasses[plugin_name]
plugin = plugin_class()
plugin.execute()
```

### Pattern 14: Dataclass Patterns

Modern immutable objects and builders.

```python
from dataclasses import dataclass, field, asdict
from typing import ClassVar

@dataclass(frozen=True)  # Immutable
class Point:
    x: float
    y: float

    def distance_from_origin(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5

# Usage
p1 = Point(3, 4)
# p1.x = 5  # Raises FrozenInstanceError

# Dataclass with defaults
@dataclass
class Config:
    debug: bool = False
    timeout: int = 30
    retries: int = 3
    tags: list = field(default_factory=list)  # Mutable default

    @classmethod
    def production(cls) -> "Config":
        """Factory method."""
        return cls(debug=False, timeout=60)

# Dataclass with class variable
@dataclass
class APIRequest:
    API_VERSION: ClassVar[str] = "v1"
    endpoint: str
    method: str = "GET"

    def full_url(self) -> str:
        return f"/api/{self.API_VERSION}/{self.endpoint}"

# Usage
req = APIRequest("/users", "POST")
print(req.full_url())  # /api/v1/users
print(asdict(req))  # {'endpoint': '/users', 'method': 'POST'}
```

## Anti-Patterns

### Don't Overuse Singleton

**WRONG: Singleton for shared state**
```python
class DatabasePool(metaclass=Singleton):
    # Hard to test (can't create multiple instances)
    # Hard to compose (global state)
    pass
```

**CORRECT: Dependency Injection**
```python
def create_app(db_pool: DatabasePool):
    # Easy to test (pass mock)
    # Easy to compose (explicit dependency)
    return app

# Test
app = create_app(MockDatabasePool())
```

### Don't Abuse Inheritance

**WRONG: Deep inheritance chains**
```python
class Animal:
    pass

class Mammal(Animal):
    pass

class Carnivore(Mammal):
    pass

class Feline(Carnivore):
    pass

class Tiger(Feline):
    pass
```

**CORRECT: Composition over inheritance**
```python
@dataclass
class Animal:
    diet: str  # "herbivore", "carnivore", "omnivore"
    reproduction: str  # "mammal", "reptile"
    family: str  # "feline", "canine"

tiger = Animal(diet="carnivore", reproduction="mammal", family="feline")
```

### Don't Create Abstract Base Classes with Only One Subclass

**WRONG: Unnecessary abstraction**
```python
class PaymentProcessor(ABC):
    @abstractmethod
    def process(self, amount: float): pass

class StripeProcessor(PaymentProcessor):
    def process(self, amount: float):
        return stripe.charge(amount)

# Only one implementation; abstraction adds complexity
```

**CORRECT: Add abstraction when multiple implementations exist**
```python
class StripeProcessor:
    def process(self, amount: float):
        return stripe.charge(amount)

# Add abstraction later if second processor needed
```

## Anti-Patterns: Best Practices

```python
# WRONG: Overly complex patterns
class FactoryFactoryBuilderSingleton:
    pass

# CORRECT: Use simplest pattern that solves the problem
def create_object(**kwargs):
    return MyClass(**kwargs)
```

## Agent Support

- **python-expert** — Type hints for patterns, Protocol usage
- **typescript-expert** — Comparison with TypeScript patterns
- **react-expert** — Observer pattern in React (state management)

## Skill References

- **python-resilience** — Decorator patterns for retry/timeout
- **python-code-style** — Immutability, composition
- **python-performance** — Caching strategies (functools.lru_cache)
