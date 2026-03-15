---
name: docker
description: >
  Docker and Docker Compose patterns for local development, multi-stage builds,
  container security (non-root, distroless, secrets, scanning, signing),
  networking, volume strategies, and multi-service orchestration.
---

# Docker

Docker and Docker Compose best practices for containerized development and production-hardened container images with vulnerability management, signed artifacts, and runtime enforcement.

## When to Activate

- Setting up Docker Compose for local development
- Designing multi-container architectures
- Troubleshooting container networking or volume issues
- Reviewing Dockerfiles for security and size
- Migrating from local dev to containerized workflow
- Building container images for production deployment
- Scanning images for CVEs and vulnerabilities
- Configuring non-root users and minimal base images
- Implementing secret injection at build and runtime
- Signing images and verifying in CI/CD or Kubernetes
- Securing containerized microservices at runtime

## Part 1: Docker Patterns

### Docker Compose for Local Development

#### Standard Web App Stack

\`\`\`yaml
# docker-compose.yml
services:
  app:
    build:
      context: .
      target: dev                     # Use dev stage of multi-stage Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - .:/app                        # Bind mount for hot reload
      - /app/node_modules             # Anonymous volume -- preserves container deps
    environment:
      - DATABASE_URL=postgres://postgres:postgres@db:5432/app_dev
      - REDIS_URL=redis://redis:6379/0
      - NODE_ENV=development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: npm run dev

  db:
    image: postgres:17-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app_dev
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data

  mailpit:                            # Local email testing
    image: axllent/mailpit
    ports:
      - "8025:8025"                   # Web UI
      - "1025:1025"                   # SMTP

volumes:
  pgdata:
  redisdata:
\`\`\`

#### Development vs Production Dockerfile

\`\`\`dockerfile
# Stage: dependencies
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage: dev (hot reload, debug tools)
FROM node:22-alpine AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# Stage: build
FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build && npm prune --production

# Stage: production (minimal image)
FROM node:22-alpine AS production
WORKDIR /app
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001
USER appuser
COPY --from=build --chown=appuser:appgroup /app/dist ./dist
COPY --from=build --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=build --chown=appuser:appgroup /app/package.json ./
ENV NODE_ENV=production
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/server.js"]
\`\`\`

#### Override Files

> **SECURITY:** docker-compose.override.yml is auto-loaded and often contains dev secrets.
> Add to .gitignore:
> ```
> docker-compose.override.yml
> docker-compose.*.override.yml
> .env.local
> .env.*.local
> ```

\`\`\`yaml
# docker-compose.override.yml (auto-loaded, dev-only settings)
services:
  app:
    environment:
      - DEBUG=app:*
      - LOG_LEVEL=debug
    ports:
      - "9229:9229"                   # Node.js debugger

# docker-compose.prod.yml (explicit for production)
services:
  app:
    build:
      target: production
    restart: always
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
\`\`\`

\`\`\`bash
# Development (auto-loads override)
docker compose up

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
\`\`\`

### Networking

#### Service Discovery

Services in the same Compose network resolve by service name:
\`\`\`
# From "app" container:
postgres://postgres:postgres@db:5432/app_dev    # "db" resolves to the db container
redis://redis:6379/0                             # "redis" resolves to the redis container
\`\`\`

#### Custom Networks

\`\`\`yaml
services:
  frontend:
    networks:
      - frontend-net

  api:
    networks:
      - frontend-net
      - backend-net

  db:
    networks:
      - backend-net              # Only reachable from api, not frontend

networks:
  frontend-net:
  backend-net:
\`\`\`

#### Exposing Only What's Needed

\`\`\`yaml
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"   # Only accessible from host, not network
    # Omit ports entirely in production -- accessible only within Docker network
\`\`\`

### Volume Strategies

\`\`\`yaml
volumes:
  # Named volume: persists across container restarts, managed by Docker
  pgdata:

  # Bind mount: maps host directory into container (for development)
  # - ./src:/app/src

  # Anonymous volume: preserves container-generated content from bind mount override
  # - /app/node_modules
\`\`\`

#### Common Patterns

\`\`\`yaml
services:
  app:
    volumes:
      - .:/app                   # Source code (bind mount for hot reload)
      - /app/node_modules        # Protect container's node_modules from host
      - /app/.next               # Protect build cache

  db:
    volumes:
      - pgdata:/var/lib/postgresql/data          # Persistent data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql  # Init scripts
\`\`\`

### .dockerignore

\`\`\`
node_modules
.git
.env
.env.*
dist
coverage
*.log
.next
.cache
docker-compose*.yml
Dockerfile*
README.md
tests/
\`\`\`

### Debugging

#### Common Commands

\`\`\`bash
# View logs
docker compose logs -f app           # Follow app logs
docker compose logs --tail=50 db     # Last 50 lines from db

# Execute commands in running container
docker compose exec app sh           # Shell into app
docker compose exec db psql -U postgres  # Connect to postgres

# Inspect
docker compose ps                     # Running services
docker compose top                    # Processes in each container
docker stats                          # Resource usage

# Rebuild
docker compose up --build             # Rebuild images
docker compose build --no-cache app   # Force full rebuild

# Clean up
docker compose down                   # Stop and remove containers
docker compose down -v                # Also remove volumes (DESTRUCTIVE)
docker system prune                   # Remove unused images/containers
\`\`\`

#### Debugging Network Issues

\`\`\`bash
# Check DNS resolution inside container
docker compose exec app nslookup db

# Check connectivity
docker compose exec app wget -qO- http://api:3000/health

# Inspect network
docker network ls
docker network inspect <project>_default
\`\`\`

### Anti-Patterns

\`\`\`
# BAD: Using docker compose in production without orchestration
# Use Kubernetes, ECS, or Docker Swarm for production multi-container workloads

# BAD: Storing data in containers without volumes
# Containers are ephemeral -- all data lost on restart without volumes

# BAD: Running as root
# Always create and use a non-root user

# BAD: Using :latest tag
# Pin to specific versions for reproducible builds

# BAD: One giant container with all services
# Separate concerns: one process per container

# BAD: Putting secrets in docker-compose.yml
# Use .env files (gitignored) or Docker secrets
\`\`\`

### BuildKit Optimizations

#### Enable BuildKit and Use Build Secrets

\`\`\`bash
# Enable BuildKit (faster caching, better layer reuse)
export DOCKER_BUILDKIT=1

# Build with secrets (safe, not baked into layers)
docker build --secret npmrc=/home/user/.npmrc \\
  --build-arg NPM_TOKEN=\${NPM_TOKEN} \\
  -t myapp:latest .
\`\`\`

\`\`\`dockerfile
# Dockerfile: Use secrets without exposing them
FROM node:22-alpine
WORKDIR /app

# Mount secret temporarily (not saved in layer)
RUN --mount=type=secret,id=npmrc \\
  cp /run/secrets/npmrc /root/.npmrc && \\
  npm ci && \\
  rm /root/.npmrc
\`\`\`

#### Cache Mounts for Package Managers

\`\`\`dockerfile
# Cache npm, pip, apt between builds (90% faster rebuild)
FROM node:22-alpine
WORKDIR /app

COPY package.json package-lock.json ./

# Cache persists across builds
RUN --mount=type=cache,target=/root/.npm \\
  npm ci --production=false

# BuildKit caches this layer independently
COPY . .
RUN npm run build
\`\`\`

\`\`\`dockerfile
# Python example
FROM python:3.12-slim
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/pip \\
  pip install -r requirements.txt
\`\`\`

#### Multi-Platform Builds

\`\`\`bash
# Build for multiple architectures in one command
docker buildx build --platform linux/amd64,linux/arm64 \\
  -t myapp:latest \\
  --push .

# Verify built for both platforms
docker buildx build --platform linux/amd64,linux/arm64 \\
  -t myapp:latest \\
  --output type=docker .
\`\`\`

\`\`\`dockerfile
# Dockerfile works transparently across architectures
FROM node:22-alpine
# No platform-specific code needed; buildx handles it
COPY --from=builder /app/dist ./dist
CMD ["node", "dist/server.js"]
\`\`\`

#### Inline Cache for CI/CD

\`\`\`yaml
# GitHub Actions: Build and push with inline caching
- name: Build and push with cache
  uses: docker/build-push-action@v5
  with:
    push: true
    tags: myapp:\${{ github.sha }}
    cache-from: type=gha             # Load cache from GitHub Actions
    cache-to: type=gha,mode=max      # Save cache for next run
\`\`\`

\`\`\`bash
# CLI equivalent
docker build --cache-from type=inline \\
  -t myapp:latest \\
  --build-arg BUILDKIT_INLINE_CACHE=1 \\
  .

docker push myapp:latest
\`\`\`

### Image Signing

#### Sign Images with Cosign

\`\`\`bash
# Generate signing key pair
cosign generate-key-pair

# Sign image (one-liner in CI)
cosign sign --key cosign.key myapp:latest

# Verify signature locally
cosign verify --key cosign.pub myapp:latest

# Signature stored in OCI artifact repository (transparent)
\`\`\`

#### CI/CD Integration

\`\`\`yaml
# GitHub Actions: Build, scan, sign, push
- name: Sign and push image
  run: |
    docker build -t myapp:\${{ github.sha }} .
    trivy image --severity HIGH,CRITICAL myapp:\${{ github.sha }} || exit 1

    docker push myapp:\${{ github.sha }}

    cosign sign --key \${{ secrets.COSIGN_KEY }} \\
      --key-password \${{ secrets.COSIGN_PASSWORD }} \\
      myapp:\${{ github.sha }}

- name: Verify signature before deploy
  run: |
    cosign verify --key cosign.pub \\
      myapp:\${{ github.sha }} || exit 1

    kubectl set image deployment/app app=myapp:\${{ github.sha }}
\`\`\`

#### When Signing Matters

- **Regulated environments:** Finance, healthcare, government (MUST sign)
- **Supply chain compliance:** SLSA L3+, SOC 2, ISO 27001
- **Production deployments:** Verify before pulling any image
- **Development:** Optional (adds overhead for local testing)

#### Verify in Kubernetes

\`\`\`yaml
# Kyverno policy: Reject unsigned images
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-images
spec:
  validationFailureAction: enforce
  rules:
  - name: check-signature
    match:
      resources:
        kinds:
        - Pod
    verifyImages:
    - imageReferences:
      - 'myapp:*'
      attestors:
      - name: cosign-key
        entries:
        - keys:
            publicKeys: |
              -----BEGIN PUBLIC KEY-----
              [cosign.pub contents]
              -----END PUBLIC KEY-----
\`\`\`

## Part 2: Container Security

> **Note:** This section is authoritative for security. Where Part 1 mentions security
> briefly, defer to this section for production guidance.

### Non-Root Containers

Always run containers as non-root user, even if application doesn't require privilege:

\`\`\`dockerfile
# Create unprivileged user
RUN useradd -r -u 65532 -s /sbin/nologin nonroot
USER nonroot
# Verify non-root at build time
RUN [ "$(id -u)" != "0" ] || (echo "ERROR: Container must not run as root" && exit 1)

# Or use built-in unprivileged user (distroless)
FROM gcr.io/distroless/java21:nonroot
\`\`\`

**Entrypoint script validation:**
\`\`\`bash
#!/bin/sh
if [ "$(id -u)" = "0" ]; then
  echo "FATAL: Container running as root" >&2; exit 1
fi
exec "$@"
\`\`\`

**In docker-compose.yml:**
\`\`\`yaml
services:
  app:
    build: .
    user: "65532"  # Explicit UID (65nobody)
    security_opt:
      - no-new-privileges:true
\`\`\`

**In Kubernetes:**
\`\`\`yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 65532
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
    add:
      - NET_BIND_SERVICE
\`\`\`

### Minimal Base Images

| Base Image | Size | Use Case |
|------------|------|----------|
| \`scratch\` | ~0 MB | Statically compiled Go binaries only |
| \`gcr.io/distroless/java21\` | ~190 MB | Java/Kotlin apps, no shell or package manager |
| \`gcr.io/distroless/java21:debug\` | ~450 MB | Java with busybox shell (debugging only) |
| \`alpine:latest\` | ~7 MB | Minimal, but has shell (security tradeoff) |
| \`debian:12-slim\` | ~80 MB | Familiar base with apt, security hardened |
| \`ubuntu:22.04\` | ~77 MB | Full Ubuntu, avoid for production |
| \`node:22-alpine\` | ~170 MB | Node.js minimal base |

**Distroless advantage:**
- No shell, package manager, or debug tools
- Smaller attack surface
- Smaller image = faster push/pull
- Minimal vulnerabilities to scan

### Multi-Stage Builds for Security

\`\`\`dockerfile
# Stage 1: Builder (full SDK, build tools)
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /src
COPY . .
RUN mvn clean package -DskipTests

# Stage 2: Runtime (minimal, distroless)
FROM gcr.io/distroless/java21:nonroot
WORKDIR /app

# Copy only .jar from builder; no source code, no build tools
COPY --from=builder --chown=65532:65532 /src/target/app.jar .

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
\`\`\`

**Why:**
- Builder stage discarded; no Maven, Gradle, or source code in final image
- ~1.5 GB builder → ~300 MB runtime (80% reduction)
- Scanning finds only production dependencies
- Attack surface limited to JVM + app code

### Secrets Management

#### ❌ WRONG: Secrets in Dockerfile

\`\`\`dockerfile
ENV DATABASE_PASSWORD="prod-secret-123"
ARG GITHUB_TOKEN="ghp_xxx"
\`\`\`
**Why:** Secrets baked into image layers; visible in history and registries.

#### ✓ CORRECT: Docker BuildKit Secrets

\`\`\`dockerfile
# syntax=docker/dockerfile:1.4
FROM node:22-alpine

RUN --mount=type=secret,id=npm_token \\
  npm set //registry.npmjs.org/:_authToken=\$(cat /run/secrets/npm_token) && \\
  npm install

# Secret removed after RUN; never committed to layer
\`\`\`

**Build command:**
\`\`\`bash
docker build \\
  --secret npm_token=/path/to/npm_token.txt \\
  -t app:latest .
\`\`\`

**CI/CD integration (GitHub Actions):**
\`\`\`yaml
- name: Build with secrets
  run: |
    docker build \\
      --secret npm_token=\${{ secrets.NPM_TOKEN }} \\
      --secret github_token=\${{ secrets.GITHUB_TOKEN }} \\
      -t app:latest .
\`\`\`

#### Runtime Secret Injection

**Environment variables (from secret store):**
\`\`\`yaml
# docker-compose.yml
services:
  app:
    image: app:latest
    environment:
      DATABASE_URL: postgres://user:pass@db:5432/app
      API_KEY: \${API_KEY}  # Loaded from .env (not committed)
\`\`\`

**Volume mounts (Kubernetes Secrets):**
\`\`\`yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: app:latest
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
    env:
    - name: DATABASE_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-creds
          key: password
  volumes:
  - name: secrets
    secret:
      secretName: db-creds
\`\`\`

### Image Hardening

#### Read-Only Root Filesystem

\`\`\`dockerfile
FROM gcr.io/distroless/java21:nonroot
WORKDIR /app
COPY --chown=65532:65532 app.jar .

# Create writable temp directory (if app needs it)
RUN mkdir -p /tmp && chmod 1777 /tmp

ENTRYPOINT ["java", "-jar", "app.jar"]
\`\`\`

**Run with:**
\`\`\`bash
docker run --read-only --tmpfs /tmp app:latest
\`\`\`

**Or in compose:**
\`\`\`yaml
services:
  app:
    read_only: true
    tmpfs: ["/tmp"]
\`\`\`

#### Drop Capabilities

\`\`\`bash
# Remove all capabilities; add back only what's needed
docker run \\
  --cap-drop ALL \\
  --cap-add NET_BIND_SERVICE \\
  app:latest
\`\`\`

**Dockerfile with Docker security policy:**
\`\`\`yaml
# docker-compose.yml
services:
  app:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
\`\`\`

**Kubernetes:**
\`\`\`yaml
securityContext:
  capabilities:
    drop:
      - ALL
    add:
      - NET_BIND_SERVICE
\`\`\`

### Vulnerability Scanning

#### Trivy (Fast, Accurate)

\`\`\`bash
# Install
curl https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# Scan local image
trivy image --severity HIGH,CRITICAL app:latest

# Scan with exit code (CI gate)
trivy image --exit-code 1 --severity CRITICAL app:latest

# Generate SBOM
trivy image --format cyclonedx --output sbom.json app:latest

# Scan Dockerfile
trivy config Dockerfile

# Scan Git repo
trivy repo https://github.com/user/repo.git
\`\`\`

**GitHub Actions CI gate:**
\`\`\`yaml
- name: Run Trivy scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: \${{ env.REGISTRY }}/\${{ env.IMAGE_NAME }}:\${{ env.TAG }}
    format: sarif
    output: trivy-results.sarif
    severity: HIGH,CRITICAL
    exit-code: '1'

- name: Upload Trivy results
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: trivy-results.sarif
\`\`\`

#### Grype (Syft Community)

\`\`\`bash
# Install
curl https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh

# Scan image
grype docker:app:latest

# JSON output
grype docker:app:latest -o json > vulns.json
\`\`\`

#### Docker Scout

\`\`\`bash
# Built-in to Docker CLI (requires Docker Desktop 4.17+)
docker scout cves app:latest

# Compare base image
docker scout compare --to distroless:latest app:latest
\`\`\`

### Image Signing

#### Cosign (Keyless Signing)

\`\`\`bash
# Install
curl https://raw.githubusercontent.com/sigstore/cosign/main/install.sh | sh

# Keyless sign (requires OIDC provider like GitHub)
cosign sign --key cosign.key ghcr.io/user/app:latest

# Or keyless with Sigstore (no key needed)
cosign sign ghcr.io/user/app:latest
\`\`\`

**CI/CD (GitHub Actions with Sigstore):**
\`\`\`yaml
- name: Sign image with Cosign
  uses: sigstore/cosign-installer@v3

- name: Push and sign
  run: |
    docker tag app:latest ghcr.io/\${{ github.repository }}:latest
    docker push ghcr.io/\${{ github.repository }}:latest
    cosign sign ghcr.io/\${{ github.repository }}:latest
  env:
    COSIGN_YES: true
\`\`\`

**Verify signature:**
\`\`\`bash
# Keyless verification (Sigstore)
cosign verify ghcr.io/user/app:latest

# With key
cosign verify --key cosign.pub ghcr.io/user/app:latest
\`\`\`

**Kubernetes admission webhook (enforce signed images):**
\`\`\`yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: image-signature-verification
webhooks:
- name: images.sigstore.dev
  admissionReviewVersions: ["v1"]
  clientConfig:
    service:
      name: cosign-webhook
      namespace: cosign-system
      path: "/verify"
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
\`\`\`

### SBOM Generation

#### Syft (Anchore)

\`\`\`bash
# Install
curl https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh

# Generate SBOM (CycloneDX format)
syft docker:app:latest -o cyclonedx > sbom.xml

# SPDX format
syft docker:app:latest -o spdx > sbom.spdx.json

# Attach to image (OCI spec)
syft docker:app:latest -o spdx-json | cosign attach sbom --sbom /dev/stdin ghcr.io/user/app:latest
\`\`\`

#### Docker SBOM (native)

\`\`\`bash
docker sbom app:latest --format cyclonedx
\`\`\`

### Runtime Security

#### Falco (Syscall Monitoring)

\`\`\`bash
# Deploy Falco in Kubernetes
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco

# Example rule: detect shell in container
- rule: Suspicious Shell in Container
  desc: Detects shell spawned in non-init container
  condition: >
    spawned_process and container and shell_procs
    and container.id != host
  output: >
    Suspicious shell spawned (user=%user.name container=%container.name)
  priority: WARNING
\`\`\`

#### Seccomp Profiles

\`\`\`json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "archMap": [
    {
      "architecture": "SCMP_ARCH_X86_64",
      "subArchitectures": ["SCMP_ARCH_X86", "SCMP_ARCH_X32"]
    }
  ],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "fstat"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
\`\`\`

**Apply in Kubernetes:**
\`\`\`yaml
securityContext:
  seccompProfile:
    type: Localhost
    localhostProfile: my-profile.json
\`\`\`

#### AppArmor

\`\`\`bash
# Kubernetes profile
apiVersion: v1
kind: Pod
metadata:
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: localhost/docker-default
spec:
  containers:
  - name: app
    image: app:latest
\`\`\`

### Registry Security

#### Private Registry Authentication

\`\`\`bash
# Login to private registry
docker login ghcr.io -u username -p \$GITHUB_TOKEN

# Tag and push
docker tag app:latest ghcr.io/user/app:latest
docker push ghcr.io/user/app:latest

# In Kubernetes, create imagepullsecret
kubectl create secret docker-registry ghcr-creds \\
  --docker-server=ghcr.io \\
  --docker-username=user \\
  --docker-password=\$GITHUB_TOKEN
\`\`\`

#### Image Pull Policies

\`\`\`yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  imagePullSecrets:
  - name: ghcr-creds
  containers:
  - name: app
    image: ghcr.io/user/app:latest
    imagePullPolicy: Always  # Always pull (prevent stale images)
\`\`\`

### Anti-Patterns

#### ❌ WRONG: Latest tag in production
\`\`\`yaml
image: postgres:latest  # Unpredictable, breaks reproducibility
\`\`\`

#### ✓ CORRECT: Pinned, specific version
\`\`\`yaml
image: postgres:16.2-alpine@sha256:abc123...  # Immutable
\`\`\`

---

#### ❌ WRONG: Root user
\`\`\`dockerfile
FROM ubuntu:22.04
RUN apt-get install -y myapp
# Runs as root by default
\`\`\`

#### ✓ CORRECT: Non-root + distroless
\`\`\`dockerfile
FROM gcr.io/distroless/debian12:nonroot
COPY --chown=nonroot:nonroot app /app
USER nonroot
\`\`\`

---

#### ❌ WRONG: Secrets in ENV
\`\`\`dockerfile
ENV DATABASE_PASSWORD="prod-secret"
ENV API_KEY="sk-xxx"
\`\`\`

#### ✓ CORRECT: BuildKit secrets + runtime injection
\`\`\`dockerfile
# syntax=docker/dockerfile:1.4
RUN --mount=type=secret,id=db_pass \\
  echo "Database password mounted, not committed"
\`\`\`

---

#### ❌ WRONG: No vulnerability scanning
\`\`\`bash
docker build -t app:latest .
docker push app:latest  # Unknown CVEs in image
\`\`\`

#### ✓ CORRECT: Scan before push
\`\`\`bash
docker build -t app:latest .
trivy image --exit-code 1 --severity HIGH,CRITICAL app:latest
docker push app:latest
\`\`\`

---

#### ❌ WRONG: Privileged containers
\`\`\`bash
docker run --privileged app:latest
\`\`\`

#### ✓ CORRECT: Least privilege
\`\`\`bash
docker run \\
  --cap-drop ALL \\
  --cap-add NET_BIND_SERVICE \\
  --security-opt no-new-privileges:true \\
  --read-only \\
  --tmpfs /tmp \\
  app:latest
\`\`\`

## Agent Support

This skill pairs with **docker-expert** (Dockerfile patterns, docker-compose), **owasp-top10-expert** (container breakout vulnerabilities), and **nodejs-expert** (runtime container behavior).

## Skill References

- **jvm-advanced**: Java container resource limits and GC logging
