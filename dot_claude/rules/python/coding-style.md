---
paths:
  - "**/*.py"
  - "**/*.pyi"
---
# Python Coding Style

> This file extends [common/coding-style.md](../common/coding-style.md) with Python specific content.

## Standards

- Follow **PEP 8** conventions
- Use **type annotations** on all public function signatures and class methods
- Private/internal helpers: type hints recommended but not mandatory
- Lambdas and one-liners: omit type hints when types are obvious from context
- Enforce with `mypy --strict` or `pyright` in CI

### Type Checker Selection

| Checker | Strengths | Choose when |
|---------|-----------|-------------|
| **Pyright** | 3-5x faster, weekly releases, best IDE integration (Pylance), implements typing PEPs first | New projects, fast CI feedback, VS Code |
| **mypy** | Industry standard, best plugin ecosystem, most tutorials reference it | Complex dynamic patterns, mature codebases with mypy plugins |

## Immutability

Prefer immutable data structures:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    name: str
    email: str

from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float
```

## Formatting

- **ruff format** — primary formatter for new projects (replaces black + isort; >99.9% Black-compatible, 30x faster)
- **ruff** — linting (replaces flake8/pylint)
- **black** + **isort** — legacy projects already using them; migrate to ruff when convenient

## Logging

- Use `logging` module, never `print()` in production code
- Configure structured logging (JSON) for production, human-readable for development
- Hooks warn on `print()` in edited files (see python/hooks.md)

## Agent Support

- **python-reviewer** — Python-specific code review

## Skill Reference

- `python-patterns` skill — Comprehensive Python idioms and patterns
