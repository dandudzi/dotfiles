# Shared Agent Config Guidelines

## Purpose
This folder is the canonical shared configuration area for AI coding agents used on this machine, including Codex, Claude Code, and OpenCode. Store reusable instructions, portable Agent Skills, shared agent prompts, shared hook scripts, and MCP intent here when they are meant to be reused across more than one agent tool.

## Organization
Keep portable content in neutral locations first, then link it into tool-specific paths when the file format is shared. Prefer direct symlinks for shared global instructions, shared `SKILL.md`-based skills, and shared Claude/OpenCode Markdown agents. Keep tool-specific settings, permissions, model choices, credentials, caches, logs, and session state out of this shared folder unless they are intentionally safe to version and reuse.

## Shared Surfaces
Docs checked on 2026-06-24 against official Codex, Claude Code, OpenCode, and Open Agent Skills documentation. Use this table as the compatibility map before adding symlinks.

| Shared surface | Canonical location here | Codex | Claude Code | OpenCode |
| --- | --- | --- | --- | --- |
| Durable instructions | `global.md` | Link to `~/.codex/AGENTS.md` for global guidance or repo `AGENTS.md` for project guidance. Codex also supports nested `AGENTS.md` and `AGENTS.override.md`. | Link to `~/.claude/CLAUDE.md`, project `CLAUDE.md`, or `.claude/CLAUDE.md`. | Link to `~/.config/opencode/AGENTS.md` for global rules or project `AGENTS.md` for project rules. OpenCode also falls back to Claude `CLAUDE.md` when its own rule file is absent. |
| Portable skills | `skills/<name>/SKILL.md` | Link `~/.agents/skills` or repo `.agents/skills` to this folder. Codex scans `.agents/skills` and `~/.agents/skills`, and supports symlinked skill folders. | Link `~/.claude/skills` or project `.claude/skills` to this folder. Claude Code skills use `SKILL.md` and can add Claude-specific frontmatter when needed. | Prefer relying on OpenCode support for `~/.agents/skills`; only link `~/.config/opencode/skills` if duplicate discovery has been tested and is safe. |
| Shared skill references and scripts | `skills/<name>/references`, `skills/<name>/scripts`, `assets/` | Keep referenced files beside `SKILL.md`; Codex loads them when the selected skill instructs it to. | Keep files beside the skill and reference them from `SKILL.md`; avoid tool-specific assumptions unless the skill declares them. | Keep files beside the skill and reference them from `SKILL.md`; OpenCode loads skills on demand through its skill tool. |
| Shared agent prompts | `agents/<role>.md` | Codex custom agents are TOML files, so these Markdown files are not directly linkable to Codex agents. | Link `~/.claude/agents` or project `.claude/agents` to this folder. Keep `name` and `description` frontmatter unique. | Link `~/.config/opencode/agents` or project `.opencode/agents` to this folder. Keep frontmatter to the Claude/OpenCode-compatible subset unless tested. |
| Shared hook scripts | `hooks/<script>` | Call these scripts from Codex hooks configured in `~/.codex/config.toml`, `~/.codex/hooks.json`, or trusted project `.codex` config. | Call these scripts from Claude hooks configured in `~/.claude/settings.json`, project `.claude/settings.json`, or plugin hooks. | Call these scripts from OpenCode plugins in `~/.config/opencode/plugins` or `.opencode/plugins`. Hook config formats differ, so link scripts, not one universal hook config. |
| MCP server intent | `mcp.md` | Configure in `~/.codex/config.toml` or trusted project `.codex/config.toml` under `mcp_servers`. Do not share tokens. | Configure project-shared MCP in `.mcp.json`; user/local MCP and OAuth state live in `~/.claude.json` and should not be shared. | Configure under `mcp` in `~/.config/opencode/opencode.json` or project `opencode.json`. Do not share secret headers or local-only state. |
| Tool settings, permissions, models | Tool-specific config outside this shared core | Use `~/.codex/config.toml` or project `.codex/config.toml` when safe. Keep auth/provider/local state out of this folder. | Use `.claude/settings.json` for shareable settings and `.claude/settings.local.json` for private local settings. Do not version `~/.claude.json`. | Use `~/.config/opencode/opencode.json` or project `opencode.json`. Keep provider credentials and machine-local overrides private. |

Treat `global.md` and `SKILL.md` with `name` and `description` frontmatter as the most portable units across the three tools. Treat Claude/OpenCode Markdown agents as shareable when their frontmatter stays compatible. Treat MCP config, hook config, permissions, model choices, auth, caches, logs, histories, and runtime state as tool-specific unless explicitly designed as a safe wrapper around shared content.

## Existing Config Handling
Before moving or linking any live tool config, inspect the existing target path and preserve current entries. Do not overwrite current MCP servers, hooks, settings, skills, or agents just to make the layout look consistent. If a target already exists, merge deliberately or stop and ask for direction.

For MCP specifically, `mcp.md` is only the canonical shared intent file. Active MCP servers must still be represented in each tool's native config format. Codex, Claude Code, and OpenCode do not share one MCP schema, so a complete MCP-sharing change means checking current tool configs, recording the non-secret shared intent here, and then updating each requested tool wrapper without copying tokens or OAuth state.

## Chezmoi
This directory lives under the rendered `~/.config` tree, so new files added here must also be captured in the upstream `chezmoi` source. Use `chezmoi add ~/.config/agents/<path>` after live edits, or edit the corresponding source path directly when the mapping is clear.
