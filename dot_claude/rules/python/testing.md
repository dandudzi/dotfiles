---
paths:
  - "**/*.py"
  - "**/*.pyi"
---
# Python Testing

> This file extends [common/testing.md](../common/testing.md) with Python specific content.

## Framework

Use **pytest** as the testing framework.

## Coverage

```bash
pytest --cov=src --cov-report=term-missing
```

## Test Organization

Use `pytest.mark` for test categorization:

```python
import pytest

@pytest.mark.unit
def test_calculate_total():
    ...

@pytest.mark.integration
def test_database_connection():
    ...
```

### File Layout

```
src/
├── users/
│   ├── service.py
│   └── models.py
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   └── test_users_service.py
├── integration/
│   └── test_users_api.py
└── e2e/
    └── test_checkout_flow.py
```

## Fixtures & conftest.py

Define reusable fixtures in `conftest.py` at the appropriate scope:

```python
import pytest

@pytest.fixture
def sample_user():
    return {"name": "Alice", "email": "alice@example.com"}

@pytest.fixture(scope="session")
def db_connection():
    conn = create_connection()
    yield conn
    conn.close()
```

## Parametrize

Use `@pytest.mark.parametrize` to test multiple inputs without duplication:

```python
@pytest.mark.parametrize("input_val,expected", [
    (0, True),
    (1, True),
    (-1, False),
    (100, True),
])
def test_is_non_negative(input_val, expected):
    assert is_non_negative(input_val) == expected
```

## Mocking Strategy

Choose the right tool for each scenario:

| Scenario | Tool | Why |
|----------|------|-----|
| Environment variables | `monkeypatch.setenv()` | Simple, auto-reverts |
| Simple attribute override | `monkeypatch.setattr()` | No import gymnastics |
| Complex dependency replacement | `unittest.mock.patch()` | Spec enforcement, call tracking |
| HTTP requests | `responses` or `httpx_mock` | Intercepts at transport level |
| Database | Real DB with fixtures (preferred) or `unittest.mock` | Prefer real over mocked |

**Key rules:**
- Patch where the name is **used**, not where it is defined
- Prefer real dependencies (DB fixtures, test servers) over mocks when practical
- Use `autospec=True` with `unittest.mock.patch` to catch API drift

```python
def test_fetch_user(monkeypatch):
    monkeypatch.setenv("API_URL", "http://test.local")

    def mock_get(url):
        return MockResponse(json={"name": "Alice"})

    monkeypatch.setattr("myapp.client.requests.get", mock_get)
    assert fetch_user("123").name == "Alice"
```

## Async Testing

Use **pytest-asyncio** for testing async code:

```python
import pytest

@pytest.mark.asyncio
async def test_async_fetch():
    result = await fetch_data("test-id")
    assert result.status == "ok"
```

> **pytest-asyncio strict mode (0.24.0+):** The default mode is now `strict`, which requires explicit async fixture scope declarations. To use auto mode, add to `pyproject.toml`:
> ```toml
> [tool.pytest.ini_options]
> asyncio_mode = "auto"
> ```
> Strict mode is preferred for test isolation; use `auto` mode only if migrating a large async test suite.

## Agent Support

- **python-reviewer** — Python-specific code review

## Skill Reference

- `python-testing` skill — Detailed pytest patterns, fixtures, and coverage
- `tdd-workflow` skill — TDD enforcement and coverage requirements
