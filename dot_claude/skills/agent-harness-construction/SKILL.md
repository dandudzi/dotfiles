---
name: agent-harness-construction
description: Design and optimize AI agent action spaces, tool definitions, and observation formatting for higher completion rates.
origin: ECC
model: opus
---

# Agent Harness Construction

## When to Activate

- Designing or refining tool definitions for an AI agent
- Improving agent completion rates, reducing retries, or optimizing cost
- Building observation formatting for tool responses
- Architecting ReAct, function-calling, or hybrid agent loops

## Core Model

Agent output quality is constrained by:
1. Action space quality — tools available and how they're defined
2. Observation quality — what the agent sees after each action
3. Recovery quality — how errors guide the agent toward correction
4. Context budget quality — how efficiently context window is used

## Action Space Design

### Tool Definition Pattern

```json
{
  "name": "search_codebase",
  "description": "Search for symbols, files, or text patterns in the repository. Use for finding definitions, usages, or specific code patterns.",
  "parameters": {
    "query": { "type": "string", "description": "Search query: symbol name, regex, or natural language" },
    "scope": { "type": "string", "enum": ["symbols", "files", "text"], "description": "What to search" },
    "max_results": { "type": "integer", "default": 10, "description": "Maximum results to return" }
  }
}
```

**Rules:**
1. Use stable, explicit tool names — `search_codebase` not `do_search`
2. Keep inputs schema-first and narrow — no catch-all `options` objects
3. Return deterministic output shapes — always same fields, nullable not absent
4. Avoid catch-all tools unless isolation is impossible

### Granularity Rules

| Risk Level | Granularity | Example |
|-----------|-------------|---------|
| High-risk (deploy, migrate, permissions) | Micro-tools | `create_migration`, `apply_migration`, `rollback_migration` |
| Common operations (edit, read, search) | Medium tools | `edit_file`, `search_codebase` |
| Batch operations where latency dominates | Macro-tools | `run_test_suite`, `batch_lint` |

## Observation Design

Every tool response should follow this structure:

```json
{
  "status": "success",
  "summary": "Found 3 usages of UserService.create() in src/",
  "data": { "matches": [...] },
  "next_actions": ["Read src/services/user.ts to see implementation", "Check test coverage"],
  "artifacts": ["src/services/user.ts:42", "src/controllers/auth.ts:18"]
}
```

**Error responses must include recovery guidance:**

```json
{
  "status": "error",
  "summary": "File not found: src/old-path/user.ts",
  "root_cause": "File was moved during recent refactor",
  "retry_hint": "Search for 'UserService' to find the new location",
  "stop_condition": "If file is deleted (not moved), skip this step"
}
```

## Error Recovery Contract

For every error path, include:
- **Root cause hint** — why it failed (not just "error occurred")
- **Safe retry instruction** — what to try differently
- **Explicit stop condition** — when to give up instead of retrying

## Context Budgeting

1. Keep system prompt minimal and invariant
2. Move large guidance into skills loaded on demand
3. Prefer references to files over inlining long documents
4. Compact at phase boundaries, not arbitrary token thresholds
5. Truncate large observation payloads — show summary + first N items + "use X for full results"

## Architecture Patterns

| Pattern | Best For | Trade-off |
|---------|----------|-----------|
| **ReAct** | Exploratory tasks, uncertain paths | Flexible but higher token cost |
| **Function-calling** | Structured deterministic flows | Efficient but rigid |
| **Hybrid** (recommended) | ReAct planning + typed tool execution | Balances flexibility and cost |

## Benchmarking

Track these metrics to evaluate harness quality:
- **Completion rate** — % of tasks completed successfully
- **Retries per task** — lower is better (target: <2 avg)
- **pass@1 and pass@3** — first-try vs three-try success rates
- **Cost per successful task** — total tokens / successful completions

## Anti-Patterns

- Too many tools with overlapping semantics (agent wastes tokens choosing)
- Opaque tool output with no recovery hints (agent retries blindly)
- Error-only output without next steps (agent gets stuck)
- Context overloading with irrelevant references (drowns signal in noise)
- Missing `description` on tool parameters (agent guesses wrong values)
- Returning raw data dumps instead of summaries (blows context budget)
