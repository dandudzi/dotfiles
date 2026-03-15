# Python Versions Strategy

This document provides guidelines for selecting Python versions across different project types and deployment contexts.

## Minimum Version Baseline

- **General libraries & applications**: Python 3.11+ (released October 2022)
- **High-performance/cutting-edge features**: Python 3.12+ (released October 2023)
- **Legacy/maintenance projects**: Python 3.9+ (EOL October 2025)

## Version Selection by Project Type

### Data Science & Machine Learning

- **Minimum**: Python 3.10+
- **Recommended**: Python 3.11+ with numpy 2.0+, pandas 2.x, scikit-learn 1.3+
- **Rationale**: NumPy 2.0 dropped 3.9 support; better performance in 3.11+
- **Special consideration**: GPU libraries (CUDA, PyTorch) may have version constraints

### Django Projects

- **Django 4.2 LTS**: Python 3.10-3.12
- **Django 5.x**: Python 3.10+ (recommends 3.11+)
- **Production deployment**: Use Django 4.2 LTS unless 5.x features are required
- **Async support**: Django 5.x + Python 3.11+ for optimal async/ASGI performance

### FastAPI & Async APIs

- **Minimum**: Python 3.11+ (exception groups, better error messages)
- **Recommended**: Python 3.12+ for production async workloads
- **Dependencies**: Pydantic v2 requires 3.7+, but use with 3.11+
- **SQLAlchemy async**: 2.0+ works best with Python 3.11+

### CLI Tools & Scripts

- **Minimum**: Python 3.11+
- **Rationale**: Exception groups, improved traceback formatting
- **Packaging**: Use `uv` with Python 3.11+ for optimal dependency resolution

### Web Servers (ASGI)

- **FastAPI**: Python 3.11+ (async/timeout handling)
- **Starlette**: Python 3.7+, but 3.11+ recommended
- **ASGI servers**: Uvicorn 0.24+, Gunicorn 21+ with `uvicorn.workers.UvicornWorker`

## Version Constraints in Dependencies

### Pinning Strategy

```toml
# pyproject.toml
[project]
requires-python = ">=3.11,<4"  # Prevent 4.0 issues

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "mypy>=1.5",
    "ruff>=0.1",
]
```

### Compatibility Matrix Testing

Use `tox` or GitHub Actions matrix to test against multiple versions:

```yaml
# .github/workflows/test.yml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
```

## Feature Availability by Version

### Python 3.11 (October 2022 - October 2027)

**Key features:**
- Exception groups with `except*` syntax
- `asyncio.TaskGroup` for structured concurrency
- `tomllib` for TOML parsing
- Performance improvements (10-60% faster in many scenarios)
- Better error messages with `traceback` module

**When to use**: Most new projects; required for exception groups in async code

### Python 3.12 (October 2023 - October 2028)

**Key features:**
- PEP 688: Per-interpreter GIL (experimental)
- Improved `asyncio` with timeout context managers
- Better error locations in tracebacks
- Performance improvements (5-20% in typical workloads)
- `sys.monitoring` replaces deprecated sys.settrace patterns

**When to use**: Performance-critical async applications; new async patterns

### Python 3.10 (October 2021 - October 2026)

**When to use**: Supporting legacy systems; Django 4.2 only requirement

## Async Support Timeline

| Version | Async Readiness | ASGI Ready | Recommended |
|---------|-----------------|-----------|-------------|
| 3.9     | Good            | Yes       | Avoid       |
| 3.10    | Good            | Yes       | Minimum LTS |
| 3.11    | Excellent       | Yes       | Standard    |
| 3.12    | Best            | Yes       | Production  |

## Breaking Changes & Upgrades

### Python 3.9 → 3.10
- No major breaking changes for well-written code
- Type hint syntax simplified (use `list[T]` instead of `List[T]`)

### Python 3.10 → 3.11
- Exception groups: `except*` is new syntax (old `except` still works)
- `asyncio` module cleaned up (old APIs still available)
- Small breaking changes in `httplib`, `doctest`

### Python 3.11 → 3.12
- No major breaking changes for application code
- Library upgrades recommended (numpy, pandas, scipy)
- GIL changes are experimental; standard behavior unchanged

## CI/CD & Docker Recommendations

### Dockerfile

```dockerfile
# Use official Python slim image
FROM python:3.12-slim-bookworm

# Multi-stage build for requirements
FROM python:3.12-slim-bookworm as builder
RUN pip install uv
COPY pyproject.toml uv.lock* ./
RUN uv pip install --system -r requirements.txt

FROM python:3.12-slim-bookworm
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ /app/src/
WORKDIR /app
CMD ["python", "-m", "uvicorn", "src.main:app"]
```

### GitHub Actions

```yaml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      - run: pip install -e .[dev]
      - run: pytest
```

## Deprecation & EOL

| Version | Released    | EOL         | Status      |
|---------|-------------|-------------|-------------|
| 3.9     | 2020-10-05  | 2025-10-05  | EOL Soon    |
| 3.10    | 2021-10-04  | 2026-10-04  | LTS Support |
| 3.11    | 2022-10-03  | 2027-10-24  | Stable      |
| 3.12    | 2023-10-02  | 2028-10-02  | Latest      |
| 3.13    | 2024-10-07  | 2029-10-07  | Dev         |

## Agent Support & Skills Reference

- **Agent**: python-expert
- **Related agents**: django-pro, fastapi-pro, python-reviewer
- **Skills**: async-python-patterns, python-testing, python-packaging, python-performance

## Decision Tree

```
Are you starting a NEW project?
  YES → Use Python 3.12+ (or 3.11 if team has constraints)
  NO → Check existing version
    Maintaining 3.9? → Plan upgrade path to 3.11+
    Maintaining 3.10? → Consider 3.11+ for async features
    Using 3.11+? → Upgrade to 3.12 if async-heavy

Is this a Django project?
  YES → Check Django version
    4.2 LTS → Support 3.10-3.12
    5.x → Require 3.10+, recommend 3.11+

Is this async-heavy (FastAPI, queues, WebSockets)?
  YES → Python 3.11+ minimum, 3.12+ preferred

Are you deploying to production?
  YES → Test against target version(s) before deploying
  Use at least 2 Python versions in CI/CD matrix
```

## Questions for Your Project

1. What Python version is required by your primary dependency (Django, FastAPI, etc.)?
2. What is your supported Python version range?
3. Do you have async workloads (ASGI, WebSockets, background tasks)?
4. What is your maintenance/support window?
5. Are you deploying Docker images? (Pin version in Dockerfile)

For questions about version strategy, consult the **python-expert** agent or applicable framework agent (django-pro, fastapi-pro).
