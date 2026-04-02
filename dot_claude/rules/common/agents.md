# Agent Delegation

## Quick Routing (no orchestrator needed)

### Code Review
- `.java`, `.kt` → `java-reviewer`
- `.py` → `python-reviewer`
- `.ts`, `.tsx`, `.js`, `.jsx` → `code-reviewer`
- TDD → `tdd-guide`

### By Technology
- React components → `react-expert`
- Next.js pages/routes/RSC → `nextjs-expert`
- TypeScript/JavaScript/Node.js → `typescript-expert`
- Database design, queries, migrations → `database-architect`
- Docker, containers → `docker-expert`
- Cloud infrastructure (AWS/GCP/Azure) → `cloud-architect`
- AI/LLM integration → `ai-engineer`

### By Workflow Step
- Planning + architecture → `architect`
- API reference, user guides, release notes → `docs-agent`
- Metrics, tracing, SLOs, OTel instrumentation → `observability-expert`
- Security review → `security-auditor`
- CI/CD, deployment → `deployment-engineer`

### Testing Specialists
- Vitest unit/component tests → `vitest-expert`
- Playwright E2E tests → `playwright-expert`

## When to Use the Orchestrator

Invoke the `orchestrator` agent when:
- Task spans 2+ domains or requires multiple specialists
- Unclear which agent(s) to use
- Cross-cutting concerns (security + performance + architecture)
- Complex tasks (10+ files, architectural decisions)

For simple, single-domain tasks, route directly to the specialist — skip the orchestrator.

## Subagent Limit

Spawn at most **3 subagents** at the same time. Use them for:
- Parallel independent queries (research, code analysis)
- Complex tasks exceeding context (delegating to specialized agent types)
- Work that doesn't duplicate your own efforts

Don't spawn unnecessary subagents for trivial tasks — do the work directly.

## Agent Size Limit

When creating or editing agent files (`~/.claude/agents/*.md`), keep them under **1500 words**. Include only essentials: role, key rules, and constraints. Omit verbose examples, redundant explanations, and boilerplate.
