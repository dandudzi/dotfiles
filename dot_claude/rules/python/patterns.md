---
paths:
  - "**/*.py"
  - "**/*.pyi"
---
# Python Patterns

> This file extends [common/patterns.md](../common/patterns.md) with Python specific content.

## Protocol (Duck Typing)

```python
from typing import Protocol

class Repository(Protocol):
    def find_by_id(self, id: str) -> dict | None: ...
    def save(self, entity: dict) -> dict: ...
```

## Dataclass vs Pydantic Decision Matrix

| Need | Use | Why |
|------|-----|-----|
| API request/response models | Pydantic `BaseModel` | Validation, serialization, OpenAPI schema |
| Internal DTOs (no validation) | `@dataclass` | Zero overhead, simple data transfer |
| Immutable value objects | `@dataclass(frozen=True)` or Pydantic with `frozen=True` | Hashable, safe as dict keys |
| Config from env/files | Pydantic `BaseSettings` (from `pydantic-settings` package: `pip install pydantic-settings`) | Auto-loads from env vars, validates |
| Database models (SQLAlchemy) | SQLAlchemy models | ORM integration, lazy loading |
| Simple tuples with names | `NamedTuple` | Lightweight, tuple-compatible |

## Pydantic Models

Prefer Pydantic over plain dataclasses when validation, serialization, or API schemas are needed:

```python
from pydantic import BaseModel

class User(BaseModel):
    model_config = {"frozen": True}

    name: str
    email: str
    age: int | None = None

# Validated construction — raises ValidationError on bad input
user = User(name="Alice", email="alice@example.com")

# Serialization
user.model_dump()        # -> dict
user.model_dump_json()   # -> JSON string
```

## Dataclasses as DTOs

Use dataclasses for internal data transfer without validation overhead:

```python
from dataclasses import dataclass

@dataclass
class CreateUserRequest:
    name: str
    email: str
    age: int | None = None
```

## Custom Exception Hierarchy

Define a base exception per domain to enable targeted `except` clauses:

```python
class AppError(Exception):
    """Base for all application errors."""

class NotFoundError(AppError):
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} {id} not found")
        self.resource = resource
        self.id = id

class ValidationError(AppError):
    def __init__(self, field: str, message: str):
        super().__init__(f"{field}: {message}")
        self.field = field
```

## Async Patterns

```python
import asyncio

# Run independent async operations concurrently
async def fetch_dashboard(user_id: str) -> Dashboard:
    user, orders, notifications = await asyncio.gather(
        fetch_user(user_id),
        fetch_orders(user_id),
        fetch_notifications(user_id),
    )
    return Dashboard(user=user, orders=orders, notifications=notifications)
```

## functools Utilities

```python
from functools import lru_cache, singledispatch

# Cache expensive pure computations
@lru_cache(maxsize=256)
def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

# Dispatch by type instead of isinstance chains
@singledispatch
def serialize(value) -> str:
    raise TypeError(f"Cannot serialize {type(value)}")

@serialize.register(int)
def _(value: int) -> str:
    return str(value)

@serialize.register(list)
def _(value: list) -> str:
    return json.dumps(value)
```

## FastAPI Patterns

```python
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel

app = FastAPI()

class CreateUserRequest(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(request: CreateUserRequest, db=Depends(get_db)):
    user = await db.users.create(request.model_dump())
    return UserResponse(**user)
```

### Error-to-HTTP-Status Mapping

```python
from fastapi import HTTPException, status

EXCEPTION_STATUS_MAP: dict[type[Exception], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    PermissionError: status.HTTP_403_FORBIDDEN,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    ConflictError: status.HTTP_409_CONFLICT,
}

@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(status_code=status_code, content={"error": str(exc)})
```

## Context Managers & Generators

- Use context managers (`with` statement) for resource management
- Use generators for lazy evaluation and memory-efficient iteration

### Async Context Managers

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_connection(url: str):
    conn = await connect(url)
    try:
        yield conn
    finally:
        await conn.close()

async def fetch_data():
    async with managed_connection("postgres://...") as conn:
        return await conn.fetch("SELECT * FROM users")
```

## FastAPI Lifespan (Startup/Shutdown)

Use the `lifespan` context manager (FastAPI 0.93+). The legacy `@app.on_event` decorators are deprecated:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize resources (DB pool, ML model, caches)
    db_pool = await create_db_pool()
    app.state.db = db_pool
    yield
    # Shutdown: clean up resources
    await db_pool.close()

app = FastAPI(lifespan=lifespan)
```

## Pydantic Settings (Configuration)

Use `pydantic-settings` (separate package) for config from environment variables:

```python
# pip install pydantic-settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    debug: bool = False

    model_config = {"env_file": ".env"}

settings = Settings()
```

## Agent Support

- **python-reviewer** — Python-specific code review

## Skill Reference

- `python-patterns` skill — Comprehensive patterns including decorators, concurrency, and package organization
