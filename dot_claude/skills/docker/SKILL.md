---
name: docker
description: >
  Docker and Docker Compose patterns for local development, multi-stage builds,
  dev/prod workflows, health checks, resource limits, BuildKit optimizations,
  and debugging. For container security, see docker-security skill.
model: sonnet
---

# Docker

Docker and Docker Compose patterns for containerized development and production workflows.

## When to Activate

- Setting up Docker Compose for local development
- Designing multi-container architectures with services
- Troubleshooting container networking or volume issues
- Building multi-stage Dockerfiles for dev and production
- Optimizing build performance with BuildKit
- Debugging container issues and networking


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

#### Multi-Stage Dockerfile

\`\`\`dockerfile
# Stage: dependencies
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage: dev (hot reload)
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

# Stage: production (optimized)
FROM node:22-alpine AS production
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./
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

BAD: Using docker compose in production without orchestration. Use Kubernetes, ECS, or Docker Swarm.

BAD: Storing data in containers without volumes. Containers are ephemeral.

BAD: Using :latest tag. Pin to specific versions for reproducible builds.

BAD: One giant container with all services. Separate concerns: one process per container.

For security anti-patterns, see the **docker-security** skill.

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


## Related Skills

- **docker-security**: Non-root users, distroless images, vulnerability scanning, image signing, SBOM generation, runtime security
- **jvm-advanced**: Java container resource limits and GC logging
