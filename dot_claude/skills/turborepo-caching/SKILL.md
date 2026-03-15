---
name: turborepo-caching
description: Turborepo build caching, remote cache setup, affected-only execution, and task pipeline configuration for monorepo performance optimization.
origin: ECC
---

# Turborepo Caching

## When to Activate

- Configuring task pipelines in turbo.json
- Setting up remote caching (Turborepo Cloud or self-hosted)
- Optimizing cache inputs and outputs
- Implementing affected-only CI builds
- Debugging cache misses or stale artifacts
- Designing multi-language monorepo task runners
- Preparing Docker builds with layer caching

## Pipeline Configuration

**File**: `turbo.json`

```json
{
  "globalEnv": ["NODE_ENV", "APP_ENV"],
  "globalDependencies": ["package.json", ".env.base"],
  "pipeline": {
    "build": {
      "outputs": ["dist/**", ".next/**"],
      "cache": true,
      "dependsOn": ["^build", "generate"]
    },
    "test": {
      "outputs": ["coverage/**"],
      "cache": false,
      "inputs": ["src/**", "test/**", "tsconfig.json"]
    },
    "lint": {
      "outputs": [],
      "cache": true,
      "dependsOn": ["^build"]
    },
    "generate": {
      "outputs": ["generated/**"],
      "cache": true
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

**Key fields:**
- `outputs`: Glob patterns to cache (must be relative to package root)
- `cache: false`: Disable caching for non-deterministic tasks (dev servers, tests)
- `dependsOn`: Array of task dependencies; `^` prefix means upstream packages
- `inputs`: File globs and env vars to hash for cache key
- `persistent: true`: Keep task running across invocations (dev servers only)

## Remote Caching Setup

### Turborepo Cloud (Official)

```bash
# Connect to Turborepo Cloud
turbo login

# Link to your team
turbo link

# Verify connection
turbo run build --dry-run
```

### Self-Hosted (MinIO/S3)

```bash
# Environment variables
export TURBO_API="https://cache.example.com"
export TURBO_TOKEN="<your-secret-token>"
export TURBO_TEAM="your-team"

# Alternative: MinIO
export TURBO_API="https://minio.example.com"
export AWS_ACCESS_KEY_ID="minioadmin"
export AWS_SECRET_ACCESS_KEY="minioadmin"
```

**Docker example** (with remote cache warming):

```dockerfile
FROM node:20 AS cache
WORKDIR /app
COPY . .
ENV TURBO_API="https://cache.example.com"
ENV TURBO_TOKEN="$TURBO_CACHE_TOKEN"
RUN turbo run build --filter='./packages/*' 2>&1 | head -50

FROM node:20
WORKDIR /app
COPY . .
RUN npm ci
RUN npx turbo run build --force
```

## Cache Inputs & Invalidation

**Stable inputs** (global):

```json
{
  "globalEnv": ["NODE_ENV", "CI", "TURBO_CACHE_TOKEN"],
  "globalDependencies": [
    "package.json",
    "package-lock.json",
    ".npmrc",
    "tsconfig.json"
  ]
}
```

**Per-task inputs**:

```json
{
  "pipeline": {
    "build": {
      "inputs": ["src/**", "!src/**/*.test.ts", "tsconfig.json"],
      "outputs": ["dist/**"]
    },
    "test": {
      "inputs": ["src/**", "test/**"],
      "cache": false
    }
  }
}
```

**Avoid volatile inputs:**
- Timestamps, commit SHAs, random tokens
- Node version (use `.nvmrc` + `globalDependencies` instead)
- Build timestamps (move to runtime metadata)

## Affected-Only Execution

**Filter by package:**

```bash
# Build only changed packages and dependents
turbo run build --filter='...[origin/main]'

# Build specific package + dependents
turbo run build --filter='@myapp/web...'

# Include dependencies of changed packages
turbo run build --filter='{./packages/*}...'
```

**In CI with git diff:**

```bash
# GitHub Actions example
- name: Determine affected packages
  run: |
    turbo run build --filter='...[origin/${{ github.base_ref }}]'
```

**Task graph with `--dry-run`:**

```bash
turbo run build --filter='@myapp/web' --dry-run --graph
```

## Multi-Language Task Runners

**Node.js + Python monorepo:**

```json
{
  "pipeline": {
    "build": {
      "outputs": ["dist/**", "build/**"]
    },
    "py:test": {
      "outputs": [],
      "cache": false
    },
    "@myapp/api#build": {
      "outputs": ["bin/**"]
    }
  }
}
```

**Custom task runner:**

```bash
# turbo.json tasks can invoke any script
{
  "pipeline": {
    "compile:rs": {
      "outputs": ["target/release/**"]
    }
  }
}

# In package.json
"scripts": {
  "compile:rs": "cargo build --release"
}
```

## Docker Pruning

**Prune monorepo for smaller Docker images:**

```bash
# Create minimal source tree with dependencies
turbo prune --scope=@myapp/api --docker

# Output: ./out/
# - full/: all source
# - json/: package.json + lockfiles only
# - pnpm-lock.yaml: locked dependencies
```

**Dockerfile with pruning:**

```dockerfile
FROM node:20 AS pruner
WORKDIR /app
COPY . .
RUN npm install -g turbo
RUN turbo prune --scope=@myapp/api --docker

FROM node:20 AS installer
WORKDIR /app
COPY --from=pruner /app/out/json .
RUN npm ci

FROM node:20
WORKDIR /app
COPY --from=pruner /app/out/full .
COPY --from=installer /app/node_modules ./node_modules
RUN npm run build
```

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| `outputs: ["dist"]` | Missing files from cache | Use `dist/**` glob with trailing `/**` |
| `inputs: ["src"]` | Wrong granularity | Use `src/**` with specific file extensions |
| No `dependsOn` for sequential tasks | Parallel execution breaks build order | Add `dependsOn: ["^build"]` explicitly |
| Caching test task | Non-deterministic output | Set `cache: false` for test/lint/type-check |
| Volatile `globalEnv` vars | Excessive cache misses | Use build-time constants, not runtime values |
| Committing `.turbo/` cache | Repository bloat | Add to `.gitignore` |

## Agent Support

- **monorepo-architect**: Use for cache strategy design and tool selection
- **nodejs-expert**: Performance tuning and Node.js-specific optimizations

## Skill References

- None yet
