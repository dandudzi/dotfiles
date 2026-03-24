---
name: deployment-patterns
description: Deployment workflows, CI/CD pipeline patterns, Docker containerization, health checks, rollback strategies, and production readiness checklists for web applications.
origin: ECC
model: sonnet
---

# Deployment Patterns

Production deployment workflows and CI/CD best practices for web applications.

## Deployment Strategies

**Rolling:** Gradually replace instances with zero downtime; both versions coexist (requires backward compatibility).

**Blue-Green:** Run two identical environments; switch traffic atomically for instant rollback. Needs 2x infrastructure during deployment.

**Canary:** Route small traffic percentage to new version first, expanding gradually if metrics pass. Requires traffic splitting and monitoring.

## Docker

### Multi-Stage Dockerfile (Node.js)

```dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production=false

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build && npm prune --production

FROM node:22-alpine AS runner
WORKDIR /app
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001
USER appuser

COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/package.json ./

ENV NODE_ENV=production
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
CMD ["node", "dist/server.js"]
```

### Docker Best Practices

- Use specific version tags (not `:latest`)
- Multi-stage builds to minimize image size
- Run as non-root user
- Copy dependency files first for layer caching
- Use `.dockerignore` to exclude `node_modules`, `.git`, tests
- Add `HEALTHCHECK` instruction
- Set resource limits in docker-compose or k8s
- Never store secrets in image; use env vars or secrets manager

## CI/CD Pipeline

### GitHub Actions (Standard Pipeline)

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage
          path: coverage/

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Deploy to production
        run: |
          # Platform-specific deployment command
          # Railway: railway up
          # Vercel: vercel --prod
          # K8s: kubectl set image deployment/app app=ghcr.io/${{ github.repository }}:${{ github.sha }}
          echo "Deploying ${{ github.sha }}"
```


## Health Checks

### Health Check Endpoint

```typescript
// Simple health check
app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok" });
});

// Detailed health check (for internal monitoring)
app.get("/health/detailed", async (req, res) => {
  const checks = {
    database: await checkDatabase(),
    redis: await checkRedis(),
    externalApi: await checkExternalApi(),
  };

  const allHealthy = Object.values(checks).every(c => c.status === "ok");

  res.status(allHealthy ? 200 : 503).json({
    status: allHealthy ? "ok" : "degraded",
    timestamp: new Date().toISOString(),
    version: process.env.APP_VERSION || "unknown",
    uptime: process.uptime(),
    checks,
  });
});

async function checkDatabase(): Promise<HealthCheck> {
  try {
    await db.query("SELECT 1");
    return { status: "ok", latency_ms: 2 };
  } catch (err) {
    return { status: "error", message: "Database unreachable" };
  }
}
```

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 30
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 2

startupProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 0
  periodSeconds: 5
  failureThreshold: 30    # 30 * 5s = 150s max startup time
```

## Environment Configuration

### Twelve-Factor App Pattern

```bash
# All config via environment variables — never in code
DATABASE_URL=postgres://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
API_KEY=${API_KEY}           # injected by secrets manager
LOG_LEVEL=info
PORT=3000

# Environment-specific behavior
NODE_ENV=production          # or staging, development
APP_ENV=production           # explicit app environment
```

### Configuration Validation

```typescript
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "staging", "production"]),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),
});

// Validate at startup — fail fast if config is wrong
export const env = envSchema.parse(process.env);
```

## Rollback

```bash
# Kubernetes
kubectl rollout undo deployment/app

# Vercel
vercel rollback

# Railway
railway up --commit <previous-sha>

# Database migrations
npx prisma migrate resolve --rolled-back <migration-name>
```

Ensure: previous images tagged, migrations backward-compatible, feature flags available to disable features, error rate monitoring in place, rollback tested in staging.

## Monitoring & Observability

**Metrics to Export:**
- Request rate (requests/sec)
- Latency (p50, p95, p99 response times)
- Error rate (5xx, 4xx counts)
- Deployment frequency (deploys/week)
- Lead time for changes (time from commit to production)
- Mean time to recovery (MTTR on incidents)

**Alerting Strategy:**
- Alert on error rate > 1% (or SLO burn rate > acceptable)
- Alert on p99 latency > 500ms
- Alert on pod restart loops (liveness probe failures)
- Alert on disk usage > 80% (prevents out-of-space crashes)

**Log Aggregation:** Ship logs to centralized system (ELK, Datadog, CloudWatch). Structure logs as JSON for machine parsing: `{ "timestamp", "level", "message", "trace_id", "user_id", "duration_ms" }`. Never log PII.

## Production Readiness Checklist

**Application:** All tests pass, no hardcoded secrets, error handling complete, structured logging (no PII), health check endpoint ready

**Infrastructure:** Reproducible Docker builds (pinned versions), environment variables validated at startup, resource limits set (CPU/memory), auto-scaling configured (min/max), SSL/TLS enabled

**Monitoring:** Metrics exported (request rate, latency, errors), alerts for error rate threshold, log aggregation ready, uptime monitoring on health endpoint

**Security:** CVE scanning enabled, CORS configured, rate limiting on public endpoints, auth verified, security headers (CSP, HSTS, X-Frame-Options) set

**Operations:** Rollback plan tested, migrations tested with production data, runbook for failures, on-call defined

## Supply Chain Security

**Image Scanning:** Use Trivy in CI; fail on CRITICAL/HIGH (or HIGH only in regulated environments).

**SBOM Generation:** `syft myapp:latest -o spdx-json > sbom.spdx.json` or `cosign generate-sbom`

**Image Signing:** `cosign sign --key cosign.key myapp:latest` and verify before deployment

**Dependency Scanning:** Enable Dependabot (GitHub) or Snyk (multi-cloud) for automated CVE PRs

**SLSA Framework:** Maturity levels: L1 (provenance) → L2 (signed) → L3 (hermetic) → L4 (reproducible). Practical L3: GitHub Actions + slsa-ghrunner + cosign + Kyverno admission controller.
