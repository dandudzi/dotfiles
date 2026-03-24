---
name: python-testing
description: Python testing strategies using pytest, TDD methodology, fixtures, mocking, parametrization, and coverage requirements.
origin: ECC
model: sonnet
---

# Python Testing Patterns

## When to Activate

- Writing new Python code (TDD: red-green-refactor)
- Designing test suites and coverage strategies
- Configuring pytest infrastructure

## Core Testing Philosophy

### Test-Driven Development (TDD)

Always follow the TDD cycle:

1. **RED**: Write a failing test for the desired behavior
2. **GREEN**: Write minimal code to make the test pass
3. **REFACTOR**: Improve code while keeping tests green

```python
# Step 1: Write failing test (RED)
def test_add_numbers():
    result = add(2, 3)
    assert result == 5

# Step 2: Write minimal implementation (GREEN)
def add(a, b):
    return a + b

# Step 3: Refactor if needed (REFACTOR)
```

### Coverage Requirements

- **Target**: 80%+ code coverage
- **Critical paths**: 100% coverage required
- Use `pytest --cov` to measure coverage

```bash
pytest --cov=mypackage --cov-report=term-missing --cov-report=html
```

## pytest Fundamentals

### Basic Test Structure

```python
import pytest

def test_addition():
    """Test basic addition."""
    assert 2 + 2 == 4

def test_string_uppercase():
    """Test string uppercasing."""
    text = "hello"
    assert text.upper() == "HELLO"

def test_list_append():
    """Test list append."""
    items = [1, 2, 3]
    items.append(4)
    assert 4 in items
    assert len(items) == 4
```

### Assertions

```python
assert result == expected              # Equality
assert result != unexpected            # Inequality
assert result  # Truthy
assert not result  # Falsy
assert item in collection              # Membership
assert result > 0                      # Comparisons
assert isinstance(result, str)         # Type checking

# Exception testing
with pytest.raises(ValueError):
    raise ValueError("error")

with pytest.raises(ValueError, match="invalid input"):
    raise ValueError("invalid input provided")

with pytest.raises(ValueError) as exc_info:
    raise ValueError("error message")
assert str(exc_info.value) == "error message"
```

## Fixtures

```python
import pytest

# Basic fixture
@pytest.fixture
def sample_data():
    return {"name": "Alice", "age": 30}

# Setup/teardown with yield
@pytest.fixture
def database():
    db = Database(":memory:")
    db.create_tables()
    yield db
    db.close()

# Fixture scopes
@pytest.fixture(scope="module")  # Once per module
def module_db():
    db = Database(":memory:")
    db.create_tables()
    yield db
    db.close()

@pytest.fixture(scope="session")  # Once per session
def shared_resource():
    resource = ExpensiveResource()
    yield resource
    resource.cleanup()

# Parametrized fixture
@pytest.fixture(params=[1, 2, 3])
def number(request):
    return request.param

# Autouse fixture
@pytest.fixture(autouse=True)
def reset_config():
    Config.reset()
    yield
    Config.cleanup()

# Shared fixtures in tests/conftest.py
@pytest.fixture
def client():
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_headers(client):
    response = client.post("/api/login", json={"username": "test", "password": "test"})
    token = response.json["token"]
    return {"Authorization": f"Bearer {token}"}

def test_with_fixtures(sample_data, database, client):
    assert sample_data["name"] == "Alice"
    result = database.query("SELECT * FROM users")
    assert len(result) > 0
```

## Parametrization

```python
# Basic parametrization
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
])
def test_uppercase(input, expected):
    assert input.upper() == expected

# With IDs for readability
@pytest.mark.parametrize("input,expected", [
    ("valid@email.com", True),
    ("invalid", False),
], ids=["valid-email", "missing-at"])
def test_email_validation(input, expected):
    assert is_valid_email(input) is expected

# Parametrized fixtures for multiple backends
@pytest.fixture(params=["sqlite", "postgresql"])
def db(request):
    return Database(request.param)

def test_db_operations(db):
    result = db.query("SELECT 1")
    assert result is not None
```

## Markers

```python
@pytest.mark.slow
def test_slow_operation():
    time.sleep(5)

@pytest.mark.integration
def test_api_integration():
    response = requests.get("https://api.example.com")
    assert response.status_code == 200
```

Run selectively:
```bash
pytest -m "not slow"           # Skip slow tests
pytest -m integration          # Only integration tests
pytest -m "unit and not slow"  # Unit but not slow
```

Configure in pytest.ini:
```ini
[pytest]
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

## Mocking and Patching

```python
from unittest.mock import patch, Mock

# Mock function with return value
@patch("mypackage.external_api_call")
def test_with_mock(api_call_mock):
    api_call_mock.return_value = {"status": "success"}
    result = my_function()
    api_call_mock.assert_called_once()
    assert result["status"] == "success"

# Mock with exception
@patch("mypackage.api_call")
def test_api_error(api_call_mock):
    api_call_mock.side_effect = ConnectionError("Network error")
    with pytest.raises(ConnectionError):
        api_call()

# Mock with autospec (catches API drift)
@patch("mypackage.DBConnection", autospec=True)
def test_autospec(db_mock):
    db = db_mock.return_value
    db.query("SELECT 1")
    db_mock.assert_called_once()

# Mock properties
@pytest.fixture
def mock_config():
    config = Mock()
    type(config).debug = PropertyMock(return_value=True)
    return config

# Mocking strategy: patch where the name is used, not where it's defined
# Prefer real dependencies (DB fixtures, test servers) over mocks when practical
```

## Testing Async Code

Use `pytest-asyncio` with `@pytest.mark.asyncio` and strict mode:

```python
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "strict"

# Test async functions
@pytest.mark.asyncio
async def test_async_add():
    result = await async_add(2, 3)
    assert result == 5

# Async fixtures
@pytest.fixture
async def async_client():
    app = create_app()
    async with app.test_client() as client:
        yield client

@pytest.mark.asyncio
async def test_api_endpoint(async_client):
    response = await async_client.get("/api/data")
    assert response.status_code == 200

# Mock async functions
@pytest.mark.asyncio
@patch("mypackage.async_api_call")
async def test_async_mock(api_call_mock):
    api_call_mock.return_value = {"status": "ok"}
    result = await my_async_function()
    api_call_mock.assert_awaited_once()
    assert result["status"] == "ok"
```

## Testing Exceptions and Side Effects

```python
# Test expected exceptions
with pytest.raises(ZeroDivisionError):
    divide(10, 0)

with pytest.raises(ValueError, match="invalid input"):
    validate_input("invalid")

# Test exception attributes
with pytest.raises(CustomError) as exc_info:
    raise CustomError("error", code=400)
assert exc_info.value.code == 400

# File operations with tmp_path (built-in fixture)
def test_with_tmp_path(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")
    result = process_file(str(test_file))
    assert result == "hello world"
    # auto-cleaned up

# tmpdir (older fixture)
def test_with_tmpdir(tmpdir):
    test_file = tmpdir.join("test.txt")
    test_file.write("data")
    result = process_file(str(test_file))
    assert result == "data"
```

## Test Organization

```
tests/
├── conftest.py       # Shared fixtures
├── unit/
│   ├── test_models.py
│   └── test_services.py
├── integration/
│   └── test_api.py
└── e2e/
    └── test_user_flow.py
```

Use pytest markers for categorization:

```python
@pytest.mark.unit
def test_calculate():
    assert add(2, 3) == 5

@pytest.mark.integration
def test_database():
    assert db.query() is not None

class TestUserService:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = UserService()

    def test_create_user(self):
        user = self.service.create_user("Alice")
        assert user.name == "Alice"
```

Run selectively: `pytest -m unit` or `pytest -m "not integration"`

## Best Practices

DO: Follow TDD (red-green-refactor) | Test one behavior per test | Use descriptive names | Use fixtures | Mock external dependencies | Test edge cases | Aim for 80%+ coverage on critical paths | Keep tests fast with marks

DON'T: Test implementation details | Use complex conditionals in tests | Share state between tests | Catch exceptions (use pytest.raises) | Over-specify mocks

## Common Patterns

```python
# API endpoints (FastAPI/Flask)
@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()

def test_get_user(client):
    response = client.get("/api/users/1")
    assert response.status_code == 200
    assert response.json["id"] == 1

# Database operations
@pytest.fixture
def db_session():
    session = Session(bind=engine)
    session.begin_nested()
    yield session
    session.rollback()

def test_create_user(db_session):
    user = User(name="Alice", email="alice@example.com")
    db_session.add(user)
    db_session.commit()
    retrieved = db_session.query(User).filter_by(name="Alice").first()
    assert retrieved.email == "alice@example.com"

# Class methods
class TestCalculator:
    @pytest.fixture
    def calculator(self):
        return Calculator()

    def test_add(self, calculator):
        assert calculator.add(2, 3) == 5
```

## Configuration

pyproject.toml:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--cov=mypackage",
    "--cov-report=term-missing",
]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

## Running Tests

```bash
pytest                                  # All tests
pytest tests/test_utils.py              # Specific file
pytest tests/test_utils.py::test_func   # Specific test
pytest -v                               # Verbose
pytest --cov=mypackage --cov-report=html  # Coverage
pytest -m "not slow"                    # Skip slow tests
pytest -x                               # Stop on first failure
pytest --lf                             # Last failed tests
pytest -k "test_user"                   # Pattern matching
pytest --pdb                            # Debugger on failure
```

## Quick Reference

| Pattern | Usage |
|---------|-------|
| `pytest.raises()` | Expected exceptions |
| `@pytest.fixture()` | Reusable fixtures |
| `@pytest.mark.parametrize()` | Multiple inputs |
| `@patch()` | Mock functions |
| `tmp_path` | Temp directory |
| `pytest --cov` | Coverage report |

**Key:** Follow TDD (red-green-refactor), aim for 80%+ coverage, test behavior not internals, keep tests isolated and fast.

