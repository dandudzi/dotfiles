---
name: obsidian-cli
description: Operate and automate local Obsidian vaults through the official desktop CLI. Use for app-aware vault inspection, search, notes, daily notes, tasks, properties, tags, links, Bases, templates, recovery, plugins, themes, workspaces, or developer diagnostics, and when choosing between Obsidian CLI, direct Markdown access, Obsidian URI, or Headless Sync.
---

# Obsidian CLI

Use the official `obsidian` CLI when Obsidian's index, link resolution, properties, plugins, commands, or UI state add value. Use direct file tools when an operation is plain offline Markdown work.

## Follow the Safe Workflow

1. Read the applicable `AGENTS.md` and preserve vault-specific rules.
2. Classify the request as read-only, content-changing, structural, administrative, or destructive.
3. Preflight with `rtk command -v obsidian` and `rtk obsidian version`.
4. Establish the target vault. Prefer running from its root. Otherwise place `vault="<name>"` immediately after `obsidian` and before the command.
5. Use exact vault-relative `path=` for automation. Use `file=` only when wikilink-style name resolution is intentional.
6. Inspect the target and related state before changing anything.
7. Run the narrowest authorized command.
8. Verify with a matching read/query command and report affected paths or exceptions.

Never rely on the active file or active vault for unattended mutation. On unfamiliar or version-dependent syntax, run `rtk obsidian help <command>` instead of guessing.

## Choose the Interface

- Use CLI for search, backlinks, tags, tasks, typed properties, Bases, templates, recovery, registered commands, plugin state, and link-aware moves.
- Use direct files or `rg` for offline reads, literal searches, focused middle-of-note patches, bulk staging imports, and attachment copying.
- Use Obsidian URI for opening, focusing, searching, or simple cross-app capture when structured output is unnecessary.
- Use Headless Sync only for syncing an Obsidian Sync vault without the desktop app; it is not a note automation CLI.
- Consider MCP or a custom plugin only for persistent cross-client or event-driven integration.

Read [references/everyday-commands.md](references/everyday-commands.md) for common operations. Read [references/alternatives-and-safety.md](references/alternatives-and-safety.md) before structural, bulk, Tasks-plugin, or fallback work. Read [references/admin-developer-commands.md](references/admin-developer-commands.md) only for recovery, plugins, UI, Sync, or development.

## Apply Command Conventions

```bash
rtk obsidian <command> key=value flag
rtk obsidian vault="Vault Name" <command> key=value
```

- Quote values containing spaces.
- Encode multiline content as `\n` and tabs as `\t`.
- Prefer `format=json` for structured results, then TSV when JSON is unavailable.
- Use `total` when only a count is needed.
- Use `search:context ... format=json` for matching lines; plain `search` returns matching paths.
- Use `--copy` only when clipboard output is explicitly useful.

## Guard Mutations

- Inspect, mutate, then verify. Re-read immediately before a content-changing operation.
- Prefer `append`, `prepend`, and typed `property:set` over full-note overwrite.
- Create without `overwrite` unless replacement is explicitly requested.
- Use CLI `move` or `rename` instead of shell `mv` when links must be updated. Confirm automatic link updating and validate unresolved links afterward.
- Re-query a task immediately before using a line-based `task ref="<path>:<line>"`.
- Do not assume core CLI task toggles implement Tasks-plugin recurrence, completion-date, dependency, or custom-status behavior. Use the plugin's registered command when those semantics matter.
- Treat orphans and dead ends as findings, not automatic defects.
- Never use `delete permanent`, restore history, change Sync state, install/uninstall plugins or themes, execute arbitrary `command` IDs, run `eval`, or use `dev:cdp` without explicit authorization.

## Handle Failures

The CLI controls a running Obsidian desktop instance. If the binary exists but cannot find Obsidian, distinguish that from a missing CLI. Use filesystem fallbacks only when semantically equivalent.

If Obsidian is visibly running but the CLI still cannot connect, a sandbox may be blocking IPC. Request narrowly scoped permission for read-only CLI access instead of repeatedly relaunching the app.

Do not trust exit status alone: Obsidian CLI 1.12.7 can print `Error:` and still exit with status 0. Inspect output and verify the result.

Runtime help is authoritative. Do not copy undocumented compatibility flags from older examples. In validated 1.12.7 behavior:

- `tasks todo` is already vault-wide; an `all` flag is undocumented and unnecessary.
- `search:context query="..." format=json` returns files, matching lines, and text.
- `search ... matches` is undocumented and ignored.
- `create` opens a note only with `open`; there is no documented `silent` flag.

If an indexed result is unexpectedly empty, confirm the correct vault, exact path, enabled plugin, and index readiness before falling back.
