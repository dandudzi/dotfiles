---
name: python-packaging
description: Modern Python packaging with uv, Poetry, and setuptools. pyproject.toml structure, dependency management, virtual environments, publishing to PyPI, and Docker integration.
origin: ECC
model: sonnet
---

# Python Packaging

## When to Activate

- Setting up new Python projects with uv or Poetry
- Creating pyproject.toml configuration
- Managing dependencies and version constraints
- Publishing packages to PyPI
- Building Docker images with Python
- Migrating from pip/setuptools to uv
- Setting up monorepo Python workspaces
- Handling lock files and reproducible builds

## Tool Selection

| Tool | Use Case | Speed | Maturity | Community |
|------|----------|-------|----------|-----------|
| **uv** | New projects, fast CI, monorepo | Fastest (~100x pip) | Newer (2024+) | Growing rapidly |
| **Poetry** | General purpose, lock files | ~2x pip | Mature (2018+) | Well-established |
| **pip + setuptools** | Legacy projects, minimal deps | Slowest | Most mature | Declining |
| **Hatch** | Package publishing, tool bundling | Fast | Newer | Moderate |

**Recommendation**: Use **uv** for new projects, Poetry for existing mature codebases.

## uv Workflows

### Initialize Project

```bash
# Create new project
uv init my-project
cd my-project

# Project structure
# my-project/
# ├── pyproject.toml
# ├── .python-version
# ├── src/my_project/__init__.py
# └── README.md
```

### Add Dependencies

```bash
# Add production dependency
uv add requests

# Add dev dependency
uv add --dev pytest black ruff

# Add specific version
uv add "django>=4.0,<5.0"

# Add with extras
uv add "requests[security,socks]"

# View lockfile
uv lock
```

### Run Commands

```bash
# Automatically activates venv and runs command
uv run python main.py

# Run pytest
uv run pytest tests/

# Run with arguments
uv run python -m my_module --flag value

# Interactive shell
uv venv
source .venv/bin/activate
```

### Sync & Build

```bash
# Install from lock file (CI/production)
uv sync

# Install without dev dependencies
uv sync --no-dev

# Build distribution
uv build

# Outputs: dist/my-project-0.1.0.tar.gz, dist/my-project-0.1.0-py3-none-any.whl
```

## pyproject.toml Structure

**Complete example:**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "0.1.0"
description = "A sample Python package"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
  {name = "Your Name", email = "you@example.com"}
]
keywords = ["example", "package"]
classifiers = [
  "Development Status :: 3 - Alpha",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: MIT License",
  
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
]

dependencies = [
  "requests>=2.28.0",
  "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=7.0",
  "black>=23.0",
  "ruff>=0.1.0",
  "mypy>=1.0",
]
docs = [
  "sphinx>=5.0",
  "sphinx-rtd-theme>=1.0",
]
performance = [
  "uvloop>=0.17.0",
  "orjson>=3.9.0",
]

[project.urls]
Homepage = "https://github.com/you/my-package"
Documentation = "https://docs.example.com"
Repository = "https://github.com/you/my-package.git"

[project.scripts]
my-cli = "my_package.cli:main"

[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']

[tool.ruff]
select = ["E", "F", "I", "UP"]
line-length = 100

[tool.mypy]
python_version = "3.12"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=my_package --cov-report=term-missing"
```

## Dependency Constraints

**Semantic versioning:**

```toml
dependencies = [
  "requests==2.28.1",        # Exact version (rarely used)
  "requests>=2.28.0",        # Minimum version
  "requests>=2.28.0,<3.0",   # Range
  "requests~=2.28.0",        # Compatible (~= 2.28.0, <2.29)
  "requests>=2.28",          # Minimum minor version
]
```

**For libraries** (leave upper bounds open):

```toml
# library/pyproject.toml
dependencies = [
  "requests>=2.28",          # Minimum, no upper bound
  "pydantic>=2.0",
  "sqlalchemy>=2.0",
]
```

**For applications** (pin exact versions):

```toml
# app/pyproject.toml
dependencies = [
  "requests==2.31.0",        # Exact pin
  "pydantic==2.5.0",
  "sqlalchemy==2.0.23",
]
```

## Lock Files

### When to Commit

**DO commit `uv.lock` / `poetry.lock`:**
- Applications and services
- Exact reproducibility required
- CI/production deployments

**DON'T commit lock files:**
- Public libraries (Let consumers choose versions)
- If using `--no-dev` in production anyway

```bash
# Application: commit lock file
git add uv.lock
git commit -m "Pin dependencies for production"

# Library: ignore lock file
echo "uv.lock" >> .gitignore
echo "poetry.lock" >> .gitignore
```

## Virtual Environments

**Python version pinning:**

```bash
# .python-version file
echo "3.12.1" > .python-version

# uv respects this automatically
uv sync  # Uses Python 3.12.1
```

**Auto-activation:**

```bash
# Create venv
uv venv

# Manual activation
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# uv run auto-activates
uv run python --version
```

## Publishing to PyPI

### Trusted Publishing (OIDC)

**GitHub Actions example:**

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI
on:
  push:
    tags: ['v*']

jobs:
  publish:
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/${{ github.repository }}
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Build package
        run: uv build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

### Manual Publishing

```bash
# Build distribution
uv build

# Publish to PyPI
uvx twine upload dist/* --repository pypi

# Or with uv (if supported in future)
uv publish
```

### TestPyPI Workflow

```bash
# Test on TestPyPI first
uvx twine upload dist/* --repository testpypi

# Verify in test environment
pip install --index-url https://test.pypi.org/simple/ my-package==0.1.0

# Then publish to production
uvx twine upload dist/* --repository pypi
```

## Monorepo Packaging

**Workspace structure:**

```
monorepo/
├── pyproject.toml          # Root workspace config
├── uv.lock
├── packages/
│   ├── core/
│   │   ├── pyproject.toml
│   │   └── src/
│   ├── api/
│   │   ├── pyproject.toml
│   │   └── src/
│   └── cli/
│       ├── pyproject.toml
│       └── src/
```

**Root pyproject.toml:**

```toml
[tool.uv]
workspace = ["packages/*"]

[tool.uv.sources]
core = { workspace = true }
api = { workspace = true }
cli = { workspace = true }
```

**Package-specific pyproject.toml:**

```toml
[project]
name = "my-api"
version = "0.2.0"
dependencies = [
  "core",           # Path dependency from workspace
  "fastapi>=0.100",
  "pydantic>=2.0",
]
```

**Shared constraints:**

```toml
# Root pyproject.toml
[tool.uv]
workspace = ["packages/*"]
dev-dependencies = [
  "pytest>=7.0",
  "black>=23.0",
  "ruff>=0.1.0",
]
```

## Docker Integration

### Multi-Stage Build with uv

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
RUN pip install --no-cache-dir uv

WORKDIR /build
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app

# Copy venv from builder
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY src/ /app/src/
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app"]
```

### Layer Caching Optimization

```dockerfile
# Good: Separate lockfile changes from source changes
FROM python:3.12-slim
RUN pip install uv

WORKDIR /app

# Layer 1: Dependencies (cached if pyproject.toml/uv.lock unchanged)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Layer 2: Source code (invalidates only if source changes)
COPY src/ /app/src/

CMD ["python", "-m", "my_module"]
```

### Production Install (No Dev Dependencies)

```dockerfile
RUN uv sync --frozen --no-dev

# Or with Poetry
RUN poetry install --only main --no-root
```

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| **No lock file in production** | Non-reproducible builds, dependency drift | Commit `uv.lock` or `poetry.lock` in apps |
| **Exact pinning in libraries** | Restricts users' dependency choices | Use `>=` with minimum version only |
| **Mixing pip + Poetry** | Incompatible lock files, broken installs | Pick one tool per project |
| **requirements.txt + pyproject.toml** | Duplicate source of truth | Use only pyproject.toml (uv/Poetry generate requirements.txt if needed) |
| **No Python version spec** | Runs on unsupported Python versions | Add `requires-python = ">=3.10"` |
| **Committing .venv** | Repository bloat, path issues | Add to `.gitignore` |
| **Upper bounds on all deps** | Prevents security updates | Only pin dev tools (pytest, black), use `>=` for app deps |
| **Global pip install in Docker** | No reproducibility, pollution | Use `uv sync` with lock file |

## Agent Support

- **python-reviewer**: Code quality and type safety
- **nodejs-expert**: Monorepo patterns with uv workspaces

## Skill References

- None yet
