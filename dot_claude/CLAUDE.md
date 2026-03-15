# Operating Principles

1. **Tool-Route First** — Use jCodeMunch for code, jDocMunch for docs, context-mode for large outputs. Never let raw data flood context.
2. **Test-Driven** — Every change needs a failing test first. See `tdd-workflow` skill for enforcement rules.
3. **Agent-First** — Delegate complex work to specialized agents. Run independent agents in parallel.
4. **Research Before Code** — Search GitHub, Context7, and package registries before writing new code.
5. **Security Always** — No hardcoded secrets, validate inputs, never compromise.

## Privacy

- Always redact logs before sharing — strip secrets, tokens, passwords, JWTs
- Review command output before including in responses — remove sensitive data
- Never paste credentials, API keys, or auth tokens into conversation context

# Code Search — Strict Policy

## (Mandatory) Internet search tool for docs and code generations

Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.

## Code Navigation — jCodeMunch (MANDATORY when available)

When jCodeMunch MCP tools (`mcp__jcodemunch__*`) are available in a project, they are the **primary tool for all code exploration**. Do NOT use `Read` on code files unless you explicitly need full file context.

Supported languages: Python (`.py`), JavaScript (`.js`, `.jsx`), TypeScript (`.ts`, `.tsx`), Go (`.go`), Rust (`.rs`), Java (`.java`), PHP (`.php`), Dart (`.dart`), C# (`.cs`), C (`.c`), C++ (`.cpp`, `.cc`, `.cxx`, `.hpp`, `.hh`, `.hxx`, `.h`), Elixir (`.ex`, `.exs`), Ruby (`.rb`, `.rake`), SQL (`.sql`), XML/XUL (`.xml`, `.xul`)

### Rules

- **ALWAYS** use `get_symbol` to fetch specific functions/classes — never read an entire file to find one function
- **ALWAYS** use `search_symbols` instead of `Grep` when looking for function/class definitions — skip `get_file_outline` when you already know the name
- **ALWAYS** run `index_folder` (incremental) at the start of each session to keep the index fresh
- **ALWAYS** re-run `index_folder` after compaction/autocompact to refresh the index with any files changed during the session
- **Sliced edit workflow (CRITICAL):** To edit a function, do NOT read the full file. Instead: `get_symbol` (find line range) → `get_file_content(start_line=line-4, end_line=end_line+3)` → `Edit`. This saves ~85% vs full Read.
- For 6+ functions in the same file, full `Read` is cheaper — skip jCodeMunch
- Fall back to `Read` ONLY for non-code files (JSON, MD, HTML, config) or when full file context is explicitly required
- When delegating to subagents, direct them to specific symbols and include jCodeMunch instructions + sliced edit workflow in prompts
- Subagents MUST follow these same rules — include jCodeMunch instructions in agent prompts

### When Read is correct

- Non-code files (JSON, MD, HTML, YAML, config)
- Full file context needed (imports, globals, module-level flow)
- Very small files (<50 lines)
- Files not yet indexed (newly created before next `index_folder`)
- Editing 6+ functions in the same file (batch edit — full Read is cheaper)

### Why this matters

Reading a full file consumes the entire content as tokens. `get_symbol` returns only the function body — typically 85-98% fewer tokens. This preserves context window for conversation history and reasoning.

## Documentation Navigation — jDocMunch (MANDATORY when available)

When jDocMunch MCP tools (`mcp__jdocmunch__*`) are available in a project, they are the **primary tool for exploring documentation files** (`.md`, `.mdx`, `.rst`). Do NOT use `Read` on large documentation files unless you explicitly need the full document.

### Rules

- **ALWAYS** use `search_sections` to find relevant documentation sections — never read an entire doc to find one section
- **ALWAYS** use `get_toc` or `get_toc_tree` to understand a document's structure before reading it
- **ALWAYS** use `get_section` to retrieve specific sections by ID — not full file reads
- **ALWAYS** run `index_local` at the start of each session to keep the doc index fresh
- **ALWAYS** re-run `index_local` after compaction/autocompact to refresh the index with any docs changed during the session
- Fall back to `Read` ONLY for small docs (<50 lines), non-indexed file types, or when full document context is explicitly required
- When delegating to subagents, direct them to specific sections (e.g., "search for 'authentication' in docs using jDocMunch `search_sections`") rather than telling them to read whole files
- Subagents MUST follow these same rules — include jDocMunch instructions in agent prompts

### When Read is correct

- Small documentation files (<50 lines)
- Non-doc files (JSON, YAML, config, code)
- Full document context needed (cross-references, overall structure)
- Files not yet indexed (newly created before next `index_local`)
- CLAUDE.md and other instruction files (always read fully)

## Command Output & Data File Navigation — context-mode (when available)

When context-mode MCP tools (`mcp__context-mode__*`) are available, use them for **large command outputs** and **large data files** instead of letting raw content flood the context window.

### Command Output Isolation (primary use case)

Use `ctx_execute(language="shell", code="...")` instead of `Bash` for commands that produce large output:

- **Test suites:** `ctx_execute(language="shell", code="pytest ...")` — not `Bash("pytest ...")`
- **git log/diff (unbounded):** `ctx_execute(language="shell", code="git log ...")` — not `Bash("git log")`
- **Recursive search:** `ctx_execute(language="shell", code="find . -name ...")` — not `Bash("find ...")`
- **API calls:** `ctx_execute(language="shell", code="curl ...")` — not `Bash("curl ...")`
- **Build output:** `ctx_execute(language="shell", code="make ...")` — not `Bash("make ...")`

Outputs >5KB are automatically filtered by intent — only relevant portions enter context (98% savings).

**When Bash IS correct:** git status/add/commit/push, file management (ls/mkdir/mv/cp), package installs, inline one-liners, commands with output redirected to a file.

### Data File Rules

- **Large JSON/HTML files (>100 lines):** Use `ctx_execute_file(path, language, code)` — file content available as `FILE_CONTENT` variable in code, raw content never enters context
- **Index a file for search:** Use `ctx_index(path="file.json", source="label")` — indexes without reading into context
- **Batch operations:** Use `ctx_batch_execute(commands=[...], queries=[...])` — runs commands AND searches results in one call (queries is required)
- **Search previous outputs:** Use `ctx_search(queries=["terms"])` to find data from earlier in the session
- **Index external docs:** Use `ctx_fetch_and_index` for URLs, then `ctx_search` to query
- **Small config JSON** (package.json, tsconfig.json, <100 lines): Direct Read is fine

### Four-tier navigation

1. Code files (.py/.js/.ts/.go/.rs/.java/.rb + more) → jCodeMunch
2. Doc files (.md/.mdx/.rst/.txt/.adoc/.html + more) → jDocMunch
3. Data files (.json/.html, large) → context-mode (`ctx_execute_file`)
4. Command outputs (tests, logs, builds) → context-mode (`ctx_execute`)

### When Bash/Read is correct (not context-mode)

- Small commands with predictable output (git status, ls, pwd, echo)
- Git operations that modify state (add, commit, push, checkout)
- Package installs (npm install, pip install)
- Small JSON/HTML files (<100 lines) or config files
- Files that need full context for editing (e.g., append-only files)
- Code files → use jCodeMunch instead
- Doc files → use jDocMunch instead

# Testing

TDD rules, test double strategy, coverage requirements, and plan execution rules are in the **tdd-workflow** skill (`~/.claude/skills/tdd-workflow/SKILL.md`). That skill is the single source of truth for all testing policy.

## Knowledge Capture

- Debugging notes, personal preferences, temporary context → auto memory (`~/.claude/projects/.../memory/`)
- Team/project knowledge (architecture decisions, API changes, runbooks) → follow the project's existing docs structure
- If the current task already produces the relevant docs, comments, or examples, do not duplicate the same knowledge elsewhere
- If there is no obvious project doc location, ask before creating a new top-level doc

# Auto-Compact Instructions

When compacting, preserve:

- All file modifications with exact paths
- Error messages verbatim
- Debugging steps taken
- Code patterns and architectural decisions

@RTK.md
