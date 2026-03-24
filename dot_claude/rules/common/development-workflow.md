---
paths:
  - "**/*.java"
  - "**/*.kt"
  - "**/*.kts"
  - "**/*.c"
  - "**/*.cpp"
  - "**/*.cc"
  - "**/*.cxx"
  - "**/*.h"
  - "**/*.hpp"
  - "**/*.py"
  - "**/*.go"
  - "**/*.cs"
  - "**/*.lua"
  - "**/*.js"
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.jsx"
  - "**/*.rb"
  - "**/*.rs"
  - "**/*.swift"
  - "**/*.php"
  - "**/*.scala"
  - "**/*.ex"
  - "**/*.exs"
  - "**/*.sh"
  - "**/*.bash"
  - "**/Makefile"
---

# Development Workflow

## Feature Implementation Workflow

0. **Research & Reuse** _(mandatory before any new implementation)_
   Use `search-first` skill to search GitHub, registries, and existing MCP/skills; confirm API behavior via Context7 before implementing.

1. **Plan First**
   Use `architect` agent with `brainstorming` skill to generate planning docs (PRD, architecture, system_design, tech_doc, task_list).
   - Use `docs-agent` to draft API reference and user-facing doc outline alongside the plan.
   - Use `observability-expert` to define SLIs/SLOs, metrics, and tracing strategy for the feature.

2. **TDD Approach**
   Use `tdd-guide` agent: write tests first (RED) → implement (GREEN) → refactor (REFACTOR) → verify 80%+ coverage.

2.5. **Observability**
   Use `observability-expert` to add instrumentation: OTel spans, structured log fields, and metrics for the new code paths. Verify correlation IDs propagate across service boundaries.

3. **Code Review**
   Use `code-reviewer` agent immediately after writing code; address CRITICAL/HIGH issues, fix MEDIUM when possible.

3.5. **Security Check**
   Use `security-auditor` agent; verify security.md checklist and address CRITICAL issues before commit.

3.7. **Docs**
   Use `docs-agent` to finalize documentation: update API reference, user guide, and release notes for the feature.

4. **Commit & Push**
   Use `deployment-engineer` agent for CI/CD changes; use detailed commit messages following conventional commits.

## Git Operations

### Commit Message Format

```
<type>: <description>

<optional body>
```

Types: feat, fix, refactor, docs, test, chore, perf, ci

Note: Attribution disabled globally via ~/.claude/settings.json.
