---
name: python-patterns
description: Pythonic idioms, PEP 8 standards, type hints, and best practices.
origin: ECC
model: sonnet
---

# Python Development Patterns

## When to Activate

- Writing new Python code or refactoring existing Python modules
- Reviewing Python code for idioms, style, or type hint correctness
- Setting up Python project structure or coding standards

## Core Principles

**Readability** — Code should be obvious. Use clear names and explicit patterns.

**Explicit > Implicit** — Avoid magic. Show intent via configuration, not hidden side effects.

**EAFP > LBYL** — Prefer try/except over condition checks.

```python
# GOOD: Readable, explicit, EAFP
def get_active_users(users: list[User]) -> list[User]:
    return [u for u in users if u.is_active]

try:
    value = dictionary[key]
except KeyError:
    value = default_value

# BAD
def get_active_users(u):
    return [x for x in u if x.a]

if key in dictionary:
    value = dictionary[key]
else:
    value = default_value
```

## Type Hints

Annotate all public functions and class methods. Use `list[str]` (3.10+) or `List[str]` (3.9-). Use `mypy --strict` in CI.

```python
# Built-in types (3.10+) vs typing module (3.9)
def process(items: list[str]) -> dict[str, int]:
    return {i: len(i) for i in items}

# Type aliases for complex types
JSON = dict[str, Any] | list[Any] | str | int | float | bool | None

# Generics: TypeVar for polymorphism
T = TypeVar('T')
def first(items: list[T]) -> T | None:
    return items[0] if items else None

# Protocol for structural subtyping (duck typing)
from typing import Protocol
class Drawable(Protocol):
    def draw(self) -> None: ...
def render(items: list[Drawable]):
    for item in items:
        item.draw()
```

## Error Handling

Catch specific exceptions; chain to preserve tracebacks. Define custom hierarchy for your domain.

```python
# GOOD: Specific, chained exceptions
try:
    with open(path) as f:
        return Config.from_json(f.read())
except FileNotFoundError as e:
    raise ConfigError(f"Config not found: {path}") from e
except json.JSONDecodeError as e:
    raise ConfigError(f"Invalid JSON: {path}") from e

# BAD: Bare except silently swallows
except:
    return None

# Custom exception hierarchy
class AppError(Exception): pass
class ValidationError(AppError): pass
class NotFoundError(AppError): pass
```

## Context Managers

Use `with` for guaranteed cleanup. Prefer `@contextmanager` for simple cases, class-based `__enter__/__exit__` for complex logic.

```python
# File I/O
with open(path, 'r') as f:
    content = f.read()

# Decorator-based: simple
from contextlib import contextmanager
@contextmanager
def timer(name: str):
    start = time.perf_counter()
    yield
    print(f"{name} took {time.perf_counter() - start:.4f}s")

with timer("processing"):
    do_work()

# Class-based: complex state
class Transaction:
    def __enter__(self):
        self.conn.begin()
        return self
    def __exit__(self, exc_type, *args):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        return False
```

## Comprehensions and Generators

Use list comprehensions for simple transforms; generators for lazy evaluation and large datasets.

```python
# GOOD: Comprehension for simple transforms
names = [user.name for user in users if user.is_active]

# BAD: Manual loop boilerplate
names = []
for user in users:
    if user.is_active:
        names.append(user.name)

# GOOD: Generator for lazy evaluation (avoids large intermediate lists)
total = sum(x * x for x in range(1_000_000))
# BAD: Creates entire list in memory
total = sum([x * x for x in range(1_000_000)])

# GOOD: Generator function for large data
def read_large_file(path: str) -> Iterator[str]:
    with open(path) as f:
        for line in f:
            yield line.strip()

# BAD: Too complex for comprehension; use function instead
result = [x * 2 for x in items if x > 0 if x % 2 == 0]
```

## Data Classes and Named Tuples

Use `@dataclass` for mutable data containers. Use `NamedTuple` for immutable, lightweight tuples.

```python
from dataclasses import dataclass, field

@dataclass
class User:
    id: str
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if "@" not in self.email:
            raise ValueError(f"Invalid email")

# Immutable NamedTuple
from typing import NamedTuple
class Point(NamedTuple):
    x: float
    y: float
    def distance(self, other: 'Point') -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
```

## Decorators

Use `@functools.wraps` to preserve metadata. Parameterized decorators return a decorator factory.

```python
import functools, time

# Simple decorator
def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__}: {time.perf_counter() - start:.4f}s")
        return result
    return wrapper

# Parameterized (decorator factory)
def repeat(times: int):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return [func(*args, **kwargs) for _ in range(times)]
        return wrapper
    return decorator

# Class-based with state
class CountCalls:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func, self.count = func, 0
    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.func(*args, **kwargs)
```

## Concurrency

I/O-bound → `ThreadPoolExecutor`, CPU-bound → `ProcessPoolExecutor`, high-concurrency I/O → `asyncio`.

```python
import concurrent.futures, asyncio

# I/O-bound (network, disk)
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(fetch_url, url) for url in urls]
    results = {url: f.result() for url, f in zip(urls, futures)}

# CPU-bound
with concurrent.futures.ProcessPoolExecutor() as executor:
    results = list(executor.map(compute, datasets))

# High-concurrency I/O with asyncio
async def fetch_all(urls: list[str]):
    tasks = [fetch_async(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

## Package Organization

Organize by domain/feature, not by type. Keep files to 200-400 lines max; extract when approaching 800. Use `__init__.py` to export the public API.

```
myproject/
├── src/mypackage/
│   ├── __init__.py          # Public API exports
│   ├── users/               # Domain-based modules
│   │   ├── models.py
│   │   ├── service.py
│   │   └── router.py
│   ├── posts/
│   │   ├── models.py
│   │   ├── service.py
│   │   └── router.py
│   └── utils.py
├── tests/
│   ├── conftest.py
│   ├── test_users.py
│   └── test_posts.py
└── pyproject.toml

# mypackage/__init__.py — export public API only
from mypackage.users.models import User
from mypackage.posts.models import Post
__all__ = ["User", "Post"]

# Import order: stdlib, third-party, local (use ruff format or isort)
import os
from pathlib import Path
import requests
from mypackage.models import User
```

## Memory and Performance

Use `__slots__` to reduce memory overhead. Use generators for large datasets. Avoid string concatenation in loops; use `str.join()` or `io.StringIO`.

```python
# __slots__ reduces memory usage; omit __dict__
class Point:
    __slots__ = ['x', 'y']
    def __init__(self, x: float, y: float):
        self.x, self.y = x, y

# Generators for large data: lazy evaluation, constant memory
def read_lines(path: str) -> Iterator[str]:
    with open(path) as f:
        for line in f:
            yield line.strip()

# BAD: O(n²) string concatenation in loop
result = ""
for item in items:
    result += str(item)

# GOOD: O(n) with join
result = "".join(str(item) for item in items)

# GOOD: StringIO for large builds
from io import StringIO
buffer = StringIO()
for item in items:
    buffer.write(str(item))
result = buffer.getvalue()
```

## Python Tooling

Use `ruff` (formatter + linter) for new projects, `mypy --strict` for type checking, `pytest` for testing.

```bash
# Formatting & linting (modern: ruff replaces black + isort + flake8)
ruff format .
ruff check . --fix

# Type checking (strict mode)
mypy . --strict

# Testing with coverage
pytest --cov=mypackage --cov-report=html

# Security scanning
bandit -r .
pip-audit

# pyproject.toml essentials
[project]
name = "mypackage"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = ["requests>=2.31.0", "pydantic>=2.0.0"]

[project.optional-dependencies]
dev = ["pytest>=7.4.0", "pytest-cov>=4.1.0", "ruff>=0.1.0", "mypy>=1.5.0"]

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.10"
disallow_untyped_defs = true
warn_return_any = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=mypackage --cov-report=term-missing"
```

## Anti-Patterns to Avoid

```python
# BAD: Mutable default arguments
def append_to(item, items=[]):
    items.append(item)
    return items

# GOOD: Use None and rebuild
def append_to(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

# BAD: type() for type checking; BAD: == for None
if type(obj) == list and value == None:
    process(obj)

# GOOD: isinstance and is
if isinstance(obj, list) and value is None:
    process(obj)

# BAD: Wildcard imports obscure what's in scope
from os.path import *

# GOOD: Explicit imports
from os.path import join, exists

# BAD: Bare except silently swallows all errors
try:
    risky_operation()
except:
    pass

# GOOD: Specific exception with logging
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
```

Python prioritizes readability and explicitness. When in doubt, choose clarity over cleverness.

---

## Quick Decision Matrix

| Choice | Use | Why |
|--------|-----|-----|
| Type checker: **Pyright** | New projects, fast CI | 3-5x faster than mypy, best IDE integration, implements PEPs first |
| Type checker: **mypy** | Legacy codebases | Industry standard, plugin ecosystem |
| Data model: **Pydantic** | API request/response | Validation, serialization, OpenAPI schema generation |
| Data model: **@dataclass** | Internal DTOs, no validation | Zero overhead, simple transfer objects |
| Data model: **@dataclass(frozen=True)** | Immutable value objects | Hashable, safe as dict keys |
| Data model: **NamedTuple** | Lightweight immutable tuples | Tuple-compatible, no overhead |
| Caching: **@lru_cache** | Pure function results | Cache expensive computations |
| Dispatch: **@singledispatch** | Type-based dispatch | Extensible polymorphism without OOP |

## Advanced Patterns

**FastAPI Lifespan (startup/shutdown, FastAPI 0.93+)**
```python
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app):
    await db.connect()  # Startup
    yield
    await db.disconnect()  # Shutdown
app = FastAPI(lifespan=lifespan)
```

**Pydantic Settings (config from env with validation)**
```python
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    database_url: str
    api_key: str
    debug: bool = False
    class Config:
        env_file = ".env"
settings = Settings()  # Raises ValidationError if required vars missing
```

**Structured Logging (JSON for production, human-readable for dev)**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("User created", extra={"user_id": user.id, "email": user.email})
```
