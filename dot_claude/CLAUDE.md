# Operating Principles

1. **Tool-Route First** — Use jCodeMunch (code), jDocMunch (docs), context-mode (large outputs).
2. **Test-Driven** — Every change needs failing test first (`tdd-workflow` skill).
3. **Agent-First** — Delegate complex work; run independent agents in parallel.
4. **Research Before Code** — Search GitHub, Context7, registries before implementing.
5. **Security Always** — No hardcoded secrets, validate inputs.

## Privacy

- Redact logs: strip secrets, tokens, passwords, JWTs.
- Review command output before sharing (remove sensitive data).
- Never paste credentials, API keys, or auth tokens in responses.

## Tool Routing

When specialized tools available, use them as primary (never raw `Read`/`Bash`):

| File Type | Primary Tool | Fallback |
|-----------|--------------|----------|
| Code (.py, .js, .ts, .go, etc.) | jCodeMunch | Read (small files only) |
| Docs (.md, .rst, .txt) | jDocMunch | Read (<50 lines) |
| Large data/JSON/HTML (>100 lines) | context-mode | Read (config files only) |
| Command output (tests, logs, builds) | context-mode | Bash (predictable output) |

Use Context7 MCP for library/API documentation and code generation.

## jCodeMunch Rules (when available)

- `index_folder` (incremental) at session start and after compaction.
- `get_symbol` for functions/classes; `search_symbols` for definitions.
- **Sliced edit workflow:** `get_symbol` → `get_file_content(start_line, end_line)` → Edit (saves ~85% context).
- Full `Read` if 6+ functions in one file or for non-code files (JSON, config).
- Fallback: `claude-mem` when index unavailable; subagents must follow same rules.

## jDocMunch Rules (when available)

- `index_local` at session start and after compaction.
- `search_sections` and `get_toc` before `get_section` reads.
- Full `Read` only for small docs (<50 lines) or non-indexed types.
- Subagents: direct to sections via `search_sections` with jDocMunch instructions.

## context-mode Rules (when available)

- **Command output:** `ctx_execute` for large outputs (tests, git log, curl, build) instead of Bash.
- **Data files:** `ctx_execute_file` for JSON/HTML >100 lines; `ctx_index`+`ctx_search` for batch queries.
- **Bash remains correct for:** git status/add/commit/push, file management, package installs, output redirects.

# Testing

TDD rules, test double strategy, coverage requirements, and plan execution rules are in the **tdd-workflow** skill (`~/.claude/skills/tdd-workflow/SKILL.md`). That skill is the single source of truth for all testing policy.

**Cascading breakage rule:** If a change breaks many tests and the only fix is rearchitecting the codebase to support one new flow — STOP and ask for help. Do not attempt large-scale restructuring autonomously.


# Auto-Compact Instructions

Preserve: file modifications (exact paths), error messages (verbatim), debugging steps, code patterns and architectural decisions.
