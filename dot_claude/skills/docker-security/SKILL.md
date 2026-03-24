---
name: docker-security
description: >
  Container image hardening: non-root users, distroless images, vulnerability
  scanning (Trivy, Grype, Docker Scout), image signing with Cosign, SBOM generation,
  runtime security (Falco, Seccomp, AppArmor), and registry access control.
model: sonnet
---

# Docker Security

Hardening container images and runtime with non-root execution, minimal base images, vulnerability scanning, signed artifacts, and runtime monitoring.

## When to Activate

- Running containers as non-root user
- Choosing minimal base images (distroless, alpine, scratch)
- Scanning images for CVEs and vulnerabilities
- Signing images and verifying signatures in CI/CD
- Implementing seccomp or AppArmor policies
- Enforcing registry authentication and pull policies

## Non-Root Containers

Always run containers as non-root, even if the application doesn't require privilege:

```dockerfile
# Create unprivileged user
RUN useradd -r -u 65532 -s /sbin/nologin nonroot
USER nonroot
# Verify non-root at build time
RUN [ "$(id -u)" != "0" ] || (echo "ERROR: Container must not run as root" && exit 1)
```

**Entrypoint validation:**
```bash
#!/bin/sh
if [ "$(id -u)" = "0" ]; then
  echo "FATAL: Container running as root" >&2; exit 1
fi
exec "$@"
```

**In docker-compose.yml:**
```yaml
services:
  app:
    build: .
    user: "65532"  # Explicit UID (65nobody)
    security_opt:
      - no-new-privileges:true
```

**In Kubernetes:**
```yaml
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
```

## Minimal Base Images

| Base Image | Size | Use Case |
|------------|------|----------|
| `scratch` | ~0 MB | Statically compiled Go binaries only |
| `gcr.io/distroless/java21` | ~190 MB | Java/Kotlin apps, no shell or package manager |
| `gcr.io/distroless/java21:debug` | ~450 MB | Java with busybox shell (debugging only) |
| `alpine:latest` | ~7 MB | Minimal, has shell (security tradeoff) |
| `debian:12-slim` | ~80 MB | Familiar base with apt, security hardened |
| `node:22-alpine` | ~170 MB | Node.js minimal base |

**Distroless advantage:**
- No shell, package manager, or debug tools → smaller attack surface
- Smaller image → faster push/pull
- Fewer dependencies → fewer vulnerabilities to scan

**Multi-stage pattern for security:**
```dockerfile
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /src
COPY . .
RUN mvn clean package -DskipTests

FROM gcr.io/distroless/java21:nonroot
WORKDIR /app
# Copy only .jar from builder; no source code, no build tools
COPY --from=builder --chown=65532:65532 /src/target/app.jar .
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

Result: ~1.5 GB builder → ~300 MB runtime (80% reduction), attack surface limited to JVM + app.

## Secrets Management

**WRONG: Secrets baked into layers**
```dockerfile
ENV DATABASE_PASSWORD="prod-secret-123"
ARG GITHUB_TOKEN="ghp_xxx"
```

**CORRECT: Docker BuildKit secrets (not committed to layers)**
```dockerfile
# syntax=docker/dockerfile:1.4
FROM node:22-alpine

RUN --mount=type=secret,id=npm_token \
  npm set //registry.npmjs.org/:_authToken=$(cat /run/secrets/npm_token) && \
  npm install
```

**Build command:**
```bash
docker build \
  --secret npm_token=/path/to/npm_token.txt \
  -t app:latest .
```

**CI/CD (GitHub Actions):**
```yaml
- name: Build with secrets
  run: |
    docker build \
      --secret npm_token=${{ secrets.NPM_TOKEN }} \
      --secret github_token=${{ secrets.GITHUB_TOKEN }} \
      -t app:latest .
```

**Runtime injection via volume mounts (Kubernetes):**
```yaml
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
```

## Image Hardening

**Read-only root filesystem:**
```dockerfile
FROM gcr.io/distroless/java21:nonroot
WORKDIR /app
COPY --chown=65532:65532 app.jar .
RUN mkdir -p /tmp && chmod 1777 /tmp
ENTRYPOINT ["java", "-jar", "app.jar"]
```

Run with: `docker run --read-only --tmpfs /tmp app:latest`

Or in compose:
```yaml
services:
  app:
    read_only: true
    tmpfs: ["/tmp"]
```

**Drop all capabilities; add back only what's needed:**
```bash
docker run \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  app:latest
```

**In docker-compose.yml:**
```yaml
services:
  app:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
```

## Vulnerability Scanning

| Tool | Speed | Detail | Best For |
|------|-------|--------|----------|
| Trivy | Fast | High (DB of 30+ vuln sources) | CI/CD gate, production scans |
| Grype | Medium | High (Syft SBOM generation) | Supply chain, SBOMs |
| Docker Scout | Medium | Medium (container-native) | Docker Desktop users |

**Trivy (recommended for CI/CD):**
```bash
# Scan local image
trivy image --severity HIGH,CRITICAL app:latest

# Exit with failure on CRITICAL (CI gate)
trivy image --exit-code 1 --severity CRITICAL app:latest

# Generate SBOM (CycloneDX)
trivy image --format cyclonedx --output sbom.json app:latest

# Scan Dockerfile config
trivy config Dockerfile

# Scan Git repo
trivy repo https://github.com/user/repo.git
```

**GitHub Actions CI gate:**
```yaml
- name: Run Trivy scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ env.TAG }}
    format: sarif
    output: trivy-results.sarif
    severity: HIGH,CRITICAL
    exit-code: '1'

- name: Upload Trivy results
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: trivy-results.sarif
```

**Grype (alternative):**
```bash
grype docker:app:latest -o json > vulns.json
```

**Docker Scout (built-in):**
```bash
docker scout cves app:latest
docker scout compare --to distroless:latest app:latest
```

## Image Signing

**Cosign (keyless signing with Sigstore):**
```bash
# Sign image (no key needed, uses OIDC provider)
cosign sign ghcr.io/user/app:latest

# Or with key
cosign sign --key cosign.key ghcr.io/user/app:latest

# Verify
cosign verify ghcr.io/user/app:latest
```

**CI/CD (GitHub Actions with Sigstore):**
```yaml
- name: Sign image with Cosign
  uses: sigstore/cosign-installer@v3

- name: Push and sign
  run: |
    docker tag app:latest ghcr.io/${{ github.repository }}:latest
    docker push ghcr.io/${{ github.repository }}:latest
    cosign sign ghcr.io/${{ github.repository }}:latest
  env:
    COSIGN_YES: true
```

**Kubernetes admission webhook (enforce signed images):**
```yaml
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
```

**When to sign:**
- Regulated environments (finance, healthcare, government)
- Supply chain compliance (SLSA L3+, SOC 2, ISO 27001)
- Production deployments
- Skip for local development (adds overhead)

## SBOM Generation

**Syft (generates CycloneDX and SPDX):**
```bash
# Install
curl https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh

# Generate SBOM
syft docker:app:latest -o cyclonedx > sbom.xml
syft docker:app:latest -o spdx > sbom.spdx.json

# Attach to image (OCI spec)
syft docker:app:latest -o spdx-json | cosign attach sbom --sbom /dev/stdin ghcr.io/user/app:latest
```

**Docker native SBOM:**
```bash
docker sbom app:latest --format cyclonedx
```

## Runtime Security

**Falco (syscall monitoring):**
```bash
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco

# Example rule: detect shell in container
- rule: Suspicious Shell in Container
  desc: Detects shell spawned in non-init container
  condition: spawned_process and container and shell_procs and container.id != host
  output: Suspicious shell spawned (user=%user.name container=%container.name)
  priority: WARNING
```

**Seccomp profiles (block unnecessary syscalls):**
```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "archMap": [{"architecture": "SCMP_ARCH_X86_64"}],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "fstat"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

**Apply in Kubernetes:**
```yaml
securityContext:
  seccompProfile:
    type: Localhost
    localhostProfile: my-profile.json
```

**AppArmor profile:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: localhost/docker-default
spec:
  containers:
  - name: app
    image: app:latest
```

## Registry Security

**Private registry authentication:**
```bash
docker login ghcr.io -u username -p $GITHUB_TOKEN
docker tag app:latest ghcr.io/user/app:latest
docker push ghcr.io/user/app:latest

# Kubernetes imagepullsecret
kubectl create secret docker-registry ghcr-creds \
  --docker-server=ghcr.io \
  --docker-username=user \
  --docker-password=$GITHUB_TOKEN
```

**Pull policy in Kubernetes:**
```yaml
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
```

## Security Anti-Patterns

**WRONG: Latest tag in production**
```yaml
image: postgres:latest  # Unpredictable
```
**CORRECT: Pinned version with digest**
```yaml
image: postgres:16.2-alpine@sha256:abc123...  # Immutable
```

---

**WRONG: Root user**
```dockerfile
FROM ubuntu:22.04
RUN apt-get install -y myapp
# Runs as root
```
**CORRECT: Non-root + distroless**
```dockerfile
FROM gcr.io/distroless/debian12:nonroot
COPY --chown=nonroot:nonroot app /app
USER nonroot
```

---

**WRONG: Secrets in ENV**
```dockerfile
ENV DATABASE_PASSWORD="prod-secret"
ENV API_KEY="sk-xxx"
```
**CORRECT: BuildKit secrets**
```dockerfile
RUN --mount=type=secret,id=db_pass \
  echo "Database password mounted, not committed"
```

---

**WRONG: No scanning before push**
```bash
docker build -t app:latest .
docker push app:latest  # Unknown CVEs
```
**CORRECT: Scan as CI gate**
```bash
docker build -t app:latest .
trivy image --exit-code 1 --severity HIGH,CRITICAL app:latest
docker push app:latest
```

---

**WRONG: Privileged containers**
```bash
docker run --privileged app:latest
```
**CORRECT: Least privilege**
```bash
docker run \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --security-opt no-new-privileges:true \
  --read-only \
  --tmpfs /tmp \
  app:latest
```
