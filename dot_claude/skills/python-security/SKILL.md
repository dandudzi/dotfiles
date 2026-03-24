---
name: python-security
description: Python security best practices including secret management, SQL injection prevention, input validation, unsafe deserialization, dependency auditing, and SBOM generation. Use during Python development and security reviews.
model: sonnet
---

# Python Security

## When to Activate

- Writing or reviewing Python code that handles user input, secrets, or SQL queries
- Setting up dependency auditing or security scanning for Python projects
- Reviewing deserialization patterns or SBOM generation in Python

Python-specific security patterns. See `security-guidelines` skill for cross-language security checklists and architectural guidelines.

## Secret Management

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["OPENAI_API_KEY"]  # Raises KeyError if missing — fail fast
```

Never hardcode secrets in source code. Use environment variables or a secret manager. Validate that required secrets are present at startup.

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

Reject and return 400 on validation failure — never process invalid data.

## Unsafe Deserialization

- Never use native Python object deserialization (`pickle`) on untrusted data — it allows arbitrary code execution
- Prefer `json`, `msgpack`, or `protobuf` for serialization
- If native serialization is unavoidable, use `hmac` to verify integrity before loading
- Prefer schema-first deserialization (Pydantic, JSON with strict validation) over binary formats

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
- Pin dependencies in `requirements.txt` or `pyproject.toml` lockfiles — never use floating ranges in production

## Security Scanning

Use **bandit** for static security analysis:

```bash
bandit -r src/
```

Configure via `pyproject.toml` (Bandit 1.8+):

```toml
[tool.bandit]
exclude_dirs = ["tests"]
skips = ["B101"]  # skip assert warnings in tests
```

Integrate in CI — fail on HIGH severity findings.

## SBOM Generation

```bash
# CycloneDX SBOM for Python projects
pip install cyclonedx-bom
cyclonedx-py environment -o sbom.json --format json

# or using syft
syft . -o cyclonedx-json > sbom.json
```

Include SBOM in release artifacts for supply chain transparency.

## Agent Support

- **python-reviewer** — Python-specific code review
- **security-auditor** — OWASP vulnerability assessment and threat modeling
- **security-auditor** — Security review at code review time

## Skill References

- **security-guidelines** — Cross-language security checklists and response protocol
- **python-patterns** — Pydantic validation patterns
