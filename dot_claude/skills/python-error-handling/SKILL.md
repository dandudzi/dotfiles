---
name: python-error-handling
description: Exception hierarchies, input validation, custom error types, and partial failure handling for robust Python applications.
origin: ECC
model: sonnet
---

# Python Error Handling Patterns

Build robust applications with proper input validation, meaningful exceptions, and graceful failure handling.

## When to Activate

- Designing exception hierarchies
- Validating inputs at system boundaries
- Handling batch operations with partial failures

## Core Concepts

**Fail Fast** — Validate inputs early, before expensive operations.

**Meaningful Exceptions** — Use specific exception types with rich context (what failed, why, how to fix).

**Exception Hierarchy** — Base `AppError` for all app errors, domain errors (`NotFoundError`, `ValidationError`, `AuthError`), infrastructure errors (`DatabaseError`).

**Error Boundaries** — API boundary validates inputs; domain layer raises domain-specific exceptions; infrastructure layer wraps external errors.

## Fundamental Patterns

### Pattern 1: Early Input Validation

Validate all inputs at system boundaries before any processing.

```python
def process_order(order_id: str, quantity: int, discount_percent: float) -> Order:
    if not order_id or not order_id.strip():
        raise ValueError("'order_id' is required")
    if quantity <= 0:
        raise ValueError(f"'quantity' must be positive, got {quantity}")
    if not 0 <= discount_percent <= 100:
        raise ValueError(f"'discount_percent' must be 0-100, got {discount_percent}")
    return _process_validated_order(order_id, quantity, discount_percent)
```

### Pattern 2: Convert to Domain Types at Boundaries

Parse strings into typed domain objects at API boundary.

```python
from enum import Enum

class OutputFormat(Enum):
    JSON = "json"
    CSV = "csv"

def parse_output_format(value: str) -> OutputFormat:
    try:
        return OutputFormat(value.lower())
    except ValueError:
        valid = ", ".join(f.value for f in OutputFormat)
        raise ValueError(f"Invalid format '{value}'. Valid: {valid}")

def export_data(data: list[dict], format_str: str) -> bytes:
    output_format = parse_output_format(format_str)  # Fail fast
    return json.dumps(data).encode() if output_format == OutputFormat.JSON else csv_serialize(data)
```

### Pattern 3: Pydantic for Complex Validation

Use Pydantic for structured input validation with automatic error aggregation.

```python
from pydantic import BaseModel, Field, field_validator

class CreateUserInput(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.lower()

@app.post("/users")
async def create_user(user_input: CreateUserInput) -> dict:
    # Pydantic validates automatically; input is trusted here
    user = User(email=user_input.email, name=user_input.name, age=user_input.age)
    await user_repository.save(user)
    return {"id": user.id, "email": user.email}
```

### Pattern 4: Custom Exception Hierarchy

Create domain-specific exceptions with context.

```python
class AppError(Exception):
    def __init__(self, message: str, error_code: str | None = None, details: dict | None = None) -> None:
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(message)

class NotFoundError(AppError):
    def __init__(self, resource_type: str, resource_id: str) -> None:
        super().__init__(
            f"{resource_type} not found: {resource_id}",
            error_code="not_found",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )

class ValidationError(AppError):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message, error_code="validation", details={"field": field} if field else {})

# Usage
def get_user_by_id(user_id: str) -> User:
    user = database.query(User).filter_by(id=user_id).first()
    if user is None:
        raise NotFoundError("User", user_id)
    return user
```

### Pattern 5: Exception Chaining

Preserve original exceptions when re-raising to maintain debug trail.

```python
def upload_file(path: str) -> str:
    try:
        with open(path, "rb") as f:
            response = httpx.post("https://upload.example.com/files", files={"file": f})
            response.raise_for_status()
            return response.json()["url"]
    except FileNotFoundError as e:
        logger.error("file_not_found", path=path)
        raise ServiceError(f"Upload failed: file not found") from e
    except httpx.HTTPStatusError as e:
        logger.error("upload_failed", status_code=e.response.status_code)
        raise ServiceError(f"Upload failed: {e.response.status_code}") from e
```

### Pattern 6: FastAPI Exception Handlers

Define consistent error response format for API errors.

```python
@app.exception_handler(ValidationError)
async def handle_validation_error(request, exc: ValidationError):
    logger.warning("validation_error", error_code=exc.error_code)
    return JSONResponse(status_code=400, content={
        "error_code": exc.error_code,
        "message": exc.message,
        "details": exc.details,
    })

@app.exception_handler(NotFoundError)
async def handle_not_found(request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={
        "error_code": exc.error_code,
        "message": exc.message,
        "details": exc.details,
    })

@app.exception_handler(AppError)
async def handle_app_error(request, exc: AppError):
    logger.error("error", error_code=exc.error_code)
    return JSONResponse(status_code=500, content={"error_code": exc.error_code, "message": "Internal error"})
```

### Pattern 7: Batch Processing with Partial Failures

Never abort entire batch on first error. Track successes and failures separately.

```python
@dataclass
class BatchResult[T]:
    succeeded: dict[int, T]
    failed: dict[int, Exception]

def process_batch(items: list[Item]) -> BatchResult[ProcessedItem]:
    succeeded, failed = {}, {}
    for idx, item in enumerate(items):
        try:
            succeeded[idx] = process_single_item(item)
        except Exception as e:
            failed[idx] = e

    if failed:
        logger.warning("batch_failure", total=len(items), failed=len(failed))
    return BatchResult(succeeded=succeeded, failed=failed)

result = process_batch(items)
if result.failed:
    logger.error("failures", count=len(result.failed))
```

### Pattern 8: Result Type Pattern

Use explicit Result type for operations without raising exceptions.

```python
@dataclass
class Success[T]:
    value: T

@dataclass
class Failure[E]:
    error: E

Result[T, E] = Union[Success[T], Failure[E]]

def parse_integer(value: str) -> Result[int, str]:
    try:
        return Success(int(value))
    except ValueError:
        return Failure(f"Cannot parse '{value}'")

result = parse_integer("42")
if isinstance(result, Success):
    print(f"Parsed: {result.value}")
else:
    print(f"Error: {result.error}")
```

## Best Practices

**Do:**
- Raise specific exceptions with context: `raise ValueError(f"'page_size' must be 1-100, got {page_size}")`
- Use custom domain exceptions: `raise NotFoundError("User", user_id)`
- Chain exceptions: `raise ServiceError("API call failed") from original_error`
- Validate early, fail fast before expensive operations
- Log with full context: `logger.exception("operation_failed", item_id=item.id)`
- Handle batch partial failures: collect succeeded/failed separately

**Don't:**
- Bare `except:` clauses (swallows KeyboardInterrupt, SystemExit)
- Re-raise without context: `except Exception: raise`
- Generic exceptions: `raise Exception("Something failed")`
- Retry permanent errors (wrong password, authentication fails)
- Use exceptions for control flow: `try: user = get_user() except NotFoundError: user = default()`
- Log without context: `logger.error("Failed to process")`

## Anti-Patterns

- **Silent swallowing:** `try: api_call() except Exception: return None` — no logging, undebugable
- **God exceptions:** `class Error(Exception): pass` — can't distinguish failure types
- **Exceptions as control flow:** Using `except IndexError` for normal iteration
- **Missing context:** `raise ValueError("Invalid input")` — what input? what's invalid?
- **Logging PII/secrets:** Never log passwords, tokens, or sensitive data
- **Batch abort on first error:** Don't let one item failure stop entire batch

## Related Skills

- **python-observability** — Logging errors with structured context
- **python-resilience** — Retry logic and error recovery
