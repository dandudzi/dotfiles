---
name: repo-indexer
description: >
  Automatically index git repositories using the jcodemunch MCP when starting work
  in an existing codebase. Trigger this skill whenever Claude begins a session in a
  git repository, opens or navigates to a project directory, or the user wants to
  explore, search, or understand a codebase — even if they don't mention indexing.
  Specific triggers: finding classes/methods/symbols, viewing project structure or
  architecture, searching across the codebase, starting work on a bug or feature in
  a repo, auditing code, or any task that benefits from AST-aware code navigation.
  Also trigger when the user explicitly says "index this repo", "set up jcodemunch",
  or "make sure the repo is indexed". Do NOT trigger for: standalone scripts not in
  a repo, conceptual programming questions, creating new projects from scratch,
  reviewing pasted diffs or clipboard code, editing config files without needing
  codebase context, or reading individual files outside a git repository.
model: haiku
---

# Repo Indexer

Index the current git repository with jcodemunch so that all code navigation tools
(`search_symbols`, `get_symbol`, `get_repo_outline`, `get_file_tree`, `get_file_outline`,
`search_text`) are available and up to date.

## Why This Matters

jcodemunch provides AST-aware code navigation that's faster and more precise than
grep/glob for finding classes, methods, and understanding project structure. But the
tools only work on indexed repos. Indexing incrementally on every session ensures the
index stays fresh as the codebase evolves — new files, renamed symbols, and deleted
code are all picked up.

## Workflow

### 1. Detect the repository root

Determine the git repository root for the current working directory:

```bash
git rev-parse --show-toplevel
```

If this fails, you're not in a git repo — skip indexing and proceed normally.
Do NOT search for repositories elsewhere on the filesystem. Only index the repo
you're currently inside of.

### 2. Index with jcodemunch

Call `index_folder` with:
- **path**: the repo root from step 1
- **incremental**: `true` — this re-indexes only changed files, keeping it fast
- **use_ai_summaries**: `true` — generates helpful symbol descriptions

This works whether the repo has been indexed before or not. If it's the first time,
it does a full index. If it's already indexed, it picks up changes since the last run.

### 3. Confirm to the user

After indexing completes, briefly confirm with something like:

> "Indexed `<repo-name>` with jcodemunch (X files, Y symbols). Code navigation tools are ready."

Include any notable stats from the response (file count, symbol count, skipped files).
If the response includes `discovery_skip_counts` or `no_symbols_files` with significant
entries, mention them so the user is aware of gaps.

### 4. Proceed with the task

Once indexed, prefer jcodemunch tools over Grep/Glob for code navigation:

- **Symbol lookup** → `search_symbols` / `get_symbol`
- **Project structure** → `get_repo_outline` / `get_file_tree`
- **File API surface** → `get_file_outline`
- **Full-text search** → `search_text`

Fall back to Grep/Glob only when jcodemunch results are insufficient.

## Edge Cases

- **Monorepos**: Index from the git root. jcodemunch handles large repos fine with
  incremental indexing.
- **Submodules**: The git root detection handles the top-level repo. If the user is
  working specifically in a submodule, index that submodule's path instead.
- **No git repo**: If `git rev-parse` fails, don't attempt indexing. Just proceed
  with standard Grep/Glob tools.
