---
paths:
  - "**/*.py"
  - "**/*.pyi"
---
# Python Security

> This file extends [common/security.md](../common/security.md) with Python specific content.

## Secret Management

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["OPENAI_API_KEY"]  # Raises KeyError if missing
```

## SQL Injection Prevention

Always use parameterized queries — never f-strings or `.format()` with SQL:

```python
# WRONG: SQL injection risk
cursor.execute(f"SELECT * FROM users WHERE id = '{user_id}'")

# CORRECT: Parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# CORRECT: SQLAlchemy ORM (inherently parameterized)
user = session.query(User).filter(User.id == user_id).first()
```

## Input Validation

Use **Pydantic** for validating untrusted input at API boundaries:

```python
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(ge=0, le=150)
```

## Unsafe Deserialization

- Never use `pickle.loads()` on untrusted data — it allows arbitrary code execution
- Prefer `json`, `msgpack`, or `protobuf` for serialization
- If pickle is unavoidable, use `hmac` to verify integrity before loading

## Dependency Auditing

- **pip projects:** Use **pip-audit** to scan for known vulnerabilities:
  ```bash
  pip-audit
  ```
- **uv projects:** Use **uv-secure** (pip-audit wrapper for uv):
  ```bash
  uvx uv-secure
  ```
- Run in CI to catch vulnerable transitive dependencies
- Pin dependencies in `requirements.txt` or `pyproject.toml` lockfiles

## Security Scanning

- Use **bandit** for static security analysis:
  ```bash
  bandit -r src/
  ```
  Configure via `pyproject.toml` (Bandit 1.8+):
  ```toml
  [tool.bandit]
  exclude_dirs = ["tests"]
  skips = ["B101"]  # skip assert warnings in tests
  ```

## SBOM Generation

```bash
# CycloneDX SBOM for Python projects
pip install cyclonedx-bom
cyclonedx-py environment -o sbom.json --format json

# or using syft
syft . -o cyclonedx-json > sbom.json
```

## Agent Support

- **python-reviewer** — Python-specific code review
- **owasp-top10-expert** — Security vulnerability assessment
