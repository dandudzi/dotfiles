# Agent Orchestration

## Available Agents

Located in `~/.claude/agents/`:

### Core Workflow

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| architect | System design | Architectural decisions, complex trade-offs |
| code-reviewer | Code review | After writing or modifying code (model: sonnet) |
| tdd-guide | Test-driven development | New features, bug fixes — enforces write-tests-first |

### Language Reviewers

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| java-reviewer | Java/Kotlin code review | Java/Spring Boot projects |
| python-reviewer | Python code review | Python projects |

### Technology Experts

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| api-documenter | API documentation | OpenAPI 3.1 specs, interactive docs, multi-language code examples |
| css-expert | CSS/Tailwind patterns | Styling, layout, responsive design |
| database-architect | Database strategy and schema | DB selection, schema design, migrations |
| dependency-manager | Dependency security | CVE scanning, SBOM generation, supply chain security, license compliance |
| django-pro | Django framework | ORM, DRF, Celery, Django Channels |
| docker-expert | Docker/containerization | Dockerfile, Compose, container issues |
| documentation-engineer | Documentation automation | API doc automation, multi-version management, link validation |
| expo-expert | Expo/React Native | Mobile app development |
| fastapi-pro | FastAPI framework | Async FastAPI, Pydantic v2, SQLAlchemy async |
| java-architect | Java architecture | DDD, Spring Boot 3.x, WebFlux, reactive microservices, JVM tuning |
| javascript-expert | JavaScript (ES2022+) | Modern JS, async patterns, Node.js runtime (model: sonnet) |
| nextjs-expert | Next.js framework | App Router, RSC, Next.js patterns |
| nodejs-expert | Node.js runtime | Node.js server, tooling, runtime issues |
| oauth-oidc-expert | OAuth 2.0 / OIDC | Authentication flows, token management |
| opentelemetry-expert | OpenTelemetry | Observability, tracing, metrics |
| owasp-top10-expert | OWASP Top 10 | Security vulnerability assessment |
| playwright-expert | Playwright E2E testing | Browser automation, E2E tests |
| python-expert | Python (3.12+) | Asyncio, type hints, Pythonic patterns |
| react-expert | React patterns | Components, hooks, state management |
| rest-expert | REST API design | API design, endpoints, HTTP semantics |
| sql-expert | SQL queries | Query optimization, schema design |
| sqlite-expert | SQLite specifics | SQLite-specific patterns and limits |
| tauri-expert | Tauri desktop apps | Desktop app development with Tauri |
| terraform-specialist | Terraform / IaC | Infrastructure as code, state, modules |
| typescript-expert | TypeScript type system | Type design, generics, utility types |
| vitest-expert | Vitest testing | Vitest configuration, patterns, mocking |

### Infrastructure & Cloud

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| cloud-architect | Multi-cloud architecture | Landing zones, IAM strategy, DR, FinOps |
| deployment-engineer | CI/CD and GitOps | Pipeline design, progressive delivery |
| kubernetes-architect | Kubernetes design | Cluster architecture, RBAC, GitOps |
| monorepo-architect | Monorepo strategy | Turborepo/Nx/Bazel, workspace structure |
| observability-engineer | Observability stack | Prometheus, Grafana, SLOs, alerting |

### Security & Reliability

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| incident-responder | Incident triage and response | SEV classification, war room, postmortem |
| threat-modeling-expert | Threat modeling | STRIDE, DFD, risk scoring, mitigations |

### AI & LLM

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| ai-engineer | LLM apps and RAG systems | API integration, RAG, agentic systems, evals |

### Documentation & Knowledge

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| knowledge-synthesizer | Workflow pattern extraction | Multi-agent session analysis, best practice synthesis, gap identification |
| research-analyst | Technology research | Evidence-based tech evaluation, source credibility, competitive analysis |
| technical-writer | Technical documentation | End-user guides, admin manuals, tutorials, WCAG AA accessibility |

### Planned (Not Yet Implemented)

These agents are referenced in workflow rules but don't have files yet:

- **planner** — Implementation planning (referenced in development-workflow.md)
- **security-reviewer** — Security analysis (referenced in common/security.md)
- **build-error-resolver** — Fix build errors (referenced in common/performance.md)

## Immediate Agent Usage

No user prompt needed:
1. Code just written/modified — Use **code-reviewer** agent
2. Bug fix or new feature — Use **tdd-guide** agent
3. Architectural decision — Use **architect** agent
4. Java/Spring code — Delegate to **java-reviewer** agent
5. Security concern — Use **owasp-top10-expert** agent

## Parallel Task Execution

ALWAYS use parallel Task execution for independent operations:

```markdown
# GOOD: Parallel execution
Launch 3 agents in parallel:
1. Agent 1: Security analysis of auth module
2. Agent 2: Performance review of cache system
3. Agent 3: Type checking of utilities

# BAD: Sequential when unnecessary
First agent 1, then agent 2, then agent 3
```

## Multi-Perspective Analysis

For complex problems, use split role sub-agents:
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker
