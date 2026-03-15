---
name: python-error-handling
description: Exception hierarchies, input validation, custom error types, and partial failure handling for robust Python applications.
origin: ECC
---

# Python Error Handling Patterns

Build robust applications with proper input validation, meaningful exceptions, and graceful failure handling.

## When to Activate

- Designing exception hierarchies for applications
- Validating user input and API parameters
- Converting external data to domain types
- Implementing partial failure handling for batch operations
- Building user-friendly error messages and responses
- Handling different failure modes in service calls

## Core Concepts

### Fail Fast

Validate inputs early, before expensive operations. Report all validation errors at once when possible.

### Meaningful Exceptions

Use appropriate exception types with rich context. Messages should explain:
- What failed
- Why it failed
- How to fix it (for user-facing errors)

### Exception Hierarchy

Design custom exceptions following domain boundaries:
- Base `AppError` for all application errors
- Domain errors (`NotFoundError`, `ValidationError`, `AuthError`)
- Infrastructure errors (`DatabaseError`, `ExternalServiceError`)

### Error Boundaries

Catch exceptions at appropriate layers:
- API boundary: Validate inputs, return error responses
- Domain layer: Raise domain-specific exceptions
- Infrastructure layer: Wrap external errors with domain context

## Fundamental Patterns

### Pattern 1: Early Input Validation

Validate all inputs at system boundaries before any processing.

```python
def process_order(
    order_id: str,
    quantity: int,
    discount_percent: float,
) -> Order:
    """Process an order with comprehensive validation.

    Args:
        order_id: Unique order identifier.
        quantity: Number of items (must be > 0).
        discount_percent: Discount percentage (0-100).

    Raises:
        ValueError: If any input is invalid.
    """
    # Validate required fields
    if not order_id or not order_id.strip():
        raise ValueError("'order_id' is required and cannot be empty")

    # Validate numeric ranges
    if quantity <= 0:
        raise ValueError(f"'quantity' must be positive, got {quantity}")

    if not 0 <= discount_percent <= 100:
        raise ValueError(
            f"'discount_percent' must be 0-100, got {discount_percent}"
        )

    # Validation passed, proceed safely
    return _process_validated_order(order_id, quantity, discount_percent)
```

### Pattern 2: Convert to Domain Types at Boundaries

Parse strings and external data into typed domain objects immediately.

```python
from enum import Enum

class OutputFormat(Enum):
    """Supported output formats."""
    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"

def parse_output_format(value: str) -> OutputFormat:
    """Parse string to OutputFormat enum.

    Args:
        value: Format string from user input.

    Returns:
        Validated OutputFormat enum member.

    Raises:
        ValueError: If format is not recognized.
    """
    try:
        return OutputFormat(value.lower())
    except ValueError:
        valid_formats = ", ".join(f.value for f in OutputFormat)
        raise ValueError(
            f"Invalid format '{value}'. Valid options: {valid_formats}"
        )

# Usage at API boundary
def export_data(data: list[dict], format_str: str) -> bytes:
    """Export data in specified format.

    Args:
        data: Data to export.
        format_str: Output format string.

    Returns:
        Serialized data.

    Raises:
        ValueError: If format is invalid.
    """
    output_format = parse_output_format(format_str)  # Fail fast
    # Rest of function uses typed OutputFormat enum
    if output_format == OutputFormat.JSON:
        return json.dumps(data).encode()
    elif output_format == OutputFormat.CSV:
        return csv_serialize(data)
    else:
        return parquet_serialize(data)
```

### Pattern 3: Pydantic for Complex Validation

Use Pydantic models for structured input validation with automatic error aggregation.

```python
from pydantic import BaseModel, Field, field_validator, ValidationError

class CreateUserInput(BaseModel):
    """Input model for user creation with validation."""

    email: str = Field(..., min_length=5, max_length=255)
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Validate email format."""
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """Normalize name (strip, title case)."""
        return v.strip().title()

# Usage at API boundary
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/users")
async def create_user(user_input: CreateUserInput) -> dict:
    """Create user with validation.

    Pydantic automatically validates and aggregates errors.
    """
    try:
        # Input is already validated by Pydantic
        user = User(email=user_input.email, name=user_input.name, age=user_input.age)
        await user_repository.save(user)
        return {"id": user.id, "email": user.email}
    except ValidationError as e:
        # Return detailed validation errors to client
        raise HTTPException(status_code=422, detail=e.errors())
```

### Pattern 4: Custom Exception Hierarchy

Create domain-specific exceptions that carry context.

```python
class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(message)

class ValidationError(AppError):
    """Input validation failed."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(
            message,
            error_code="validation_error",
            details={"field": field} if field else {},
        )

class NotFoundError(AppError):
    """Requested resource not found."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        super().__init__(
            f"{resource_type} not found: {resource_id}",
            error_code="not_found_error",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )

class AuthError(AppError):
    """Authentication or authorization failed."""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="auth_error")

class ExternalServiceError(AppError):
    """Call to external service failed."""

    def __init__(
        self,
        service_name: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        super().__init__(
            f"External service '{service_name}' error",
            error_code="external_service_error",
            details={
                "service": service_name,
                "status_code": status_code,
                "response_body": response_body,
            },
        )

# Usage
def get_user_by_id(user_id: str) -> User:
    """Get user or raise NotFoundError."""
    user = database.query(User).filter_by(id=user_id).first()
    if user is None:
        raise NotFoundError("User", user_id)
    return user
```

### Pattern 5: Exception Chaining

Preserve the original exception when re-raising to maintain the debug trail.

```python
import httpx
import structlog

logger = structlog.get_logger()

class ServiceError(Exception):
    """High-level service operation failed."""
    pass

def upload_file(path: str) -> str:
    """Upload file and return URL.

    Args:
        path: Path to file to upload.

    Returns:
        URL of uploaded file.

    Raises:
        ServiceError: If upload fails.
    """
    try:
        with open(path, "rb") as f:
            response = httpx.post(
                "https://upload.example.com/files",
                files={"file": f},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["url"]
    except FileNotFoundError as e:
        logger.error("file_not_found", path=path)
        raise ServiceError(f"Upload failed: file not found at '{path}'") from e
    except httpx.HTTPStatusError as e:
        logger.error(
            "upload_failed",
            status_code=e.response.status_code,
            path=path,
        )
        raise ServiceError(
            f"Upload failed: server returned {e.response.status_code}"
        ) from e
    except httpx.RequestError as e:
        logger.error("network_error", path=path, error_type=type(e).__name__)
        raise ServiceError(f"Upload failed: network error") from e
```

### Pattern 6: FastAPI Exception Handlers

Define consistent error response format for API errors.

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import structlog

app = FastAPI()
logger = structlog.get_logger()

# Define consistent error response shape
class ErrorResponse(BaseModel):
    """Standard API error response."""
    error_code: str
    message: str
    details: dict | None = None

# Register exception handlers
@app.exception_handler(ValidationError)
async def handle_validation_error(request, exc: ValidationError):
    """Handle validation errors with 400 status."""
    logger.warning(
        "validation_error",
        error_code=exc.error_code,
        details=exc.details,
    )
    return JSONResponse(
        status_code=400,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )

@app.exception_handler(NotFoundError)
async def handle_not_found(request, exc: NotFoundError):
    """Handle not found errors with 404 status."""
    logger.warning("resource_not_found", details=exc.details)
    return JSONResponse(
        status_code=404,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )

@app.exception_handler(AuthError)
async def handle_auth_error(request, exc: AuthError):
    """Handle auth errors with 401 status."""
    logger.warning("authentication_failed")
    return JSONResponse(
        status_code=401,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
        },
    )

@app.exception_handler(AppError)
async def handle_app_error(request, exc: AppError):
    """Handle generic app errors with 500 status."""
    logger.error("unexpected_error", error_code=exc.error_code, details=exc.details)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": exc.error_code,
            "message": "Internal server error",
        },
    )
```

### Pattern 7: Batch Processing with Partial Failures

Never let one bad item abort an entire batch. Track successes and failures separately.

```python
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class BatchResult[T]:
    """Results from batch processing operation."""

    succeeded: dict[int, T]  # index -> result
    failed: dict[int, Exception]  # index -> error

    @property
    def success_count(self) -> int:
        """Number of successful items."""
        return len(self.succeeded)

    @property
    def failure_count(self) -> int:
        """Number of failed items."""
        return len(self.failed)

    @property
    def all_succeeded(self) -> bool:
        """Whether all items succeeded."""
        return len(self.failed) == 0

def process_batch(items: list[Item]) -> BatchResult[ProcessedItem]:
    """Process items, capturing individual failures.

    Args:
        items: Items to process.

    Returns:
        BatchResult with succeeded and failed items by index.
    """
    succeeded: dict[int, ProcessedItem] = {}
    failed: dict[int, Exception] = {}

    for idx, item in enumerate(items):
        try:
            result = process_single_item(item)
            succeeded[idx] = result
        except Exception as e:
            failed[idx] = e

    if failed:
        logger.warning(
            "batch_partial_failure",
            total=len(items),
            succeeded=len(succeeded),
            failed=len(failed),
            failed_indices=list(failed.keys()),
        )

    return BatchResult(succeeded=succeeded, failed=failed)

# Caller handles partial results
result = process_batch(items)
if result.all_succeeded:
    logger.info("batch_completed", count=result.success_count)
else:
    logger.error(
        "batch_with_failures",
        succeeded=result.success_count,
        failed=result.failure_count,
    )
    # Handle failures: retry, log for manual review, etc.
```

### Pattern 8: Result Type Pattern

Explicit success/failure type for operations without raising exceptions.

```python
from typing import TypeVar, Generic, Union
from dataclasses import dataclass

T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type

@dataclass
class Success[T]:
    """Operation succeeded."""
    value: T

@dataclass
class Failure[E]:
    """Operation failed."""
    error: E

Result[T, E] = Union[Success[T], Failure[E]]

def parse_integer(value: str) -> Result[int, str]:
    """Parse string to integer.

    Returns:
        Result with parsed int or error message.
    """
    try:
        return Success(int(value))
    except ValueError:
        return Failure(f"Cannot parse '{value}' as integer")

# Usage (no try/except needed)
result = parse_integer("42")
if isinstance(result, Success):
    print(f"Parsed: {result.value}")
else:
    print(f"Error: {result.error}")

# Works well with map operations
def double(x: int) -> Result[int, str]:
    if x > 1000:
        return Failure("Value too large")
    return Success(x * 2)

result = parse_integer("10").map(lambda v: double(v))
```

## Best Practices

### Do This

```python
# GOOD: Specific exception with context
raise ValueError(f"'page_size' must be 1-100, got {page_size}")

# GOOD: Custom domain exception with details
raise NotFoundError("User", user_id)

# GOOD: Exception chaining to preserve context
raise ServiceError("API call failed") from original_error

# GOOD: Validate early, fail fast
def process(data):
    if not validate(data):
        raise ValidationError("Invalid data")
    return expensive_operation(data)

# GOOD: Log full context with exceptions
logger.exception("operation_failed", operation_name="sync_data", item_id=item.id)

# GOOD: Partial failures in batch operations
result = BatchResult(succeeded=[], failed=[])
for item in items:
    try:
        result.succeeded.append(process(item))
    except Exception as e:
        result.failed.append(e)
```

### Don't Do This

```python
# BAD: Bare except clause swallows all exceptions
try:
    result = operation()
except:
    result = None  # Silent failure, impossible to debug

# BAD: Re-raising without context
except Exception:
    raise  # Lost the error chain

# BAD: Generic Exception with no context
raise Exception("Something failed")

# BAD: Retrying permanent errors
@retry(stop=stop_after_attempt(3))
def login(username: str, password: str):
    return api.login(username, password)  # Won't help if password wrong

# BAD: Exception as control flow
try:
    user = get_user_by_id(user_id)
except NotFoundError:
    user = create_default_user()  # Don't use exceptions for normal flow

# BAD: Logging without context
logger.error("Failed to process")  # Which item? What error?
```

## Anti-Patterns

```python
# ANTI-PATTERN 1: Swallowing exceptions silently
try:
    result = api_call()
except Exception:
    return None  # No logging, no context

# ANTI-PATTERN 2: God exception classes (catch all)
class Error(Exception):
    pass
# Now impossible to distinguish between different failure types

# ANTI-PATTERN 3: Exception as control flow
try:
    while True:
        item = queue.pop()
except IndexError:
    break  # Using exception for normal iteration

# ANTI-PATTERN 4: Missing error context
raise ValueError("Invalid input")  # What input? What's invalid?

# ANTI-PATTERN 5: Logging passwords or PII
logger.error(f"Login failed for {username} with password {password}")

# ANTI-PATTERN 6: Abort batch on first error
def process_batch(items):
    for item in items:
        process(item)  # One failure stops entire batch
```

## Agent Support

- **python-expert** — Pydantic configuration, type hints, dataclass patterns
- **rest-expert** — HTTP status codes, error response formats, API design

## Skill References

- **python-observability** — Logging errors with structured context
- **python-resilience** — Retry logic and error recovery patterns
