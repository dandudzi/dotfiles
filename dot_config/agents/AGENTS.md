# Shared Agent Config Guidelines

## Purpose
This folder is the canonical shared configuration area for AI coding agents used on this machine, including Codex, Claude Code, and OpenCode. Store reusable instructions, portable Agent Skills, shared prompt assets, and adapter source files here when they are meant to be reused across more than one agent tool.

## Organization
Keep portable content in neutral locations first, then link or adapt it into tool-specific paths. Prefer shared `SKILL.md`-based skills and plain Markdown instruction files for cross-tool behavior. Keep tool-specific wrappers, settings, permissions, model choices, credentials, caches, logs, and session state out of this shared folder unless they are intentionally safe to version and reuse.

## Shared Surfaces
Docs checked on 2026-06-24 against official Codex, Claude Code, OpenCode, and Open Agent Skills documentation. Use this table as the compatibility map before adding symlinks.

| Shared surface | Canonical location here | Codex | Claude Code | OpenCode |
| --- | --- | --- | --- | --- |
| Durable instructions | `AGENTS.md` or `instructions/*.md` | Link to `~/.codex/AGENTS.md` for global guidance or repo `AGENTS.md` for project guidance. Codex also supports nested `AGENTS.md` and `AGENTS.override.md`. | Link through `~/.claude/CLAUDE.md`, project `CLAUDE.md`, or `.claude/CLAUDE.md`. Claude can import shared files from `CLAUDE.md` with `@path` syntax, so prefer a small adapter over duplicated content. | Link to `~/.config/opencode/AGENTS.md` for global rules or project `AGENTS.md` for project rules. OpenCode also falls back to Claude `CLAUDE.md` when its own rule file is absent. |
| Portable skills | `skills/<name>/SKILL.md` | Link `~/.agents/skills` or repo `.agents/skills` to this folder. Codex scans `.agents/skills` and `~/.agents/skills`, and supports symlinked skill folders. | Link or copy into `~/.claude/skills` or project `.claude/skills`. Claude Code skills use `SKILL.md` and can add Claude-specific frontmatter when needed. | Link `~/.config/opencode/skills`, project `.opencode/skills`, or rely on OpenCode support for `.agents/skills`, `~/.agents/skills`, `.claude/skills`, and `~/.claude/skills`. |
| Shared skill references and scripts | `skills/<name>/references`, `skills/<name>/scripts`, `assets/` | Keep referenced files beside `SKILL.md`; Codex loads them when the selected skill instructs it to. | Keep files beside the skill and reference them from `SKILL.md`; avoid tool-specific assumptions unless the skill declares them. | Keep files beside the skill and reference them from `SKILL.md`; OpenCode loads skills on demand through its skill tool. |
| Subagent or role prompts | `agents-src/<role>.md` plus adapters | Codex subagents are configured through Codex-specific agent config, not Claude/OpenCode agent files. Keep Codex adapters separate. | Link/adapt to `~/.claude/agents/<role>.md` or `.claude/agents/<role>.md`. | Link/adapt to `~/.config/opencode/agents/<role>.md` or `.opencode/agents/<role>.md`. OpenCode agent frontmatter differs from Claude Code. |
| MCP server intent | `mcp/<server>.md` or generated snippets | Configure in `~/.codex/config.toml` or trusted project `.codex/config.toml` under `mcp_servers`. Do not share tokens. | Configure project-shared MCP in `.mcp.json`; user/local MCP and OAuth state live in `~/.claude.json` and should not be shared. | Configure under `mcp` in `~/.config/opencode/opencode.json` or project `opencode.json`. Do not share secret headers or local-only state. |
| Tool settings, permissions, hooks, models | Tool-specific adapter files only | Use `~/.codex/config.toml` or project `.codex/config.toml` when safe. Keep auth/provider/local state out of this folder. | Use `.claude/settings.json` for shareable project settings and `.claude/settings.local.json` for private local settings. Do not version `~/.claude.json`. | Use `~/.config/opencode/opencode.json` or project `opencode.json`. Keep provider credentials and machine-local overrides private. |

Treat `SKILL.md` with `name` and `description` frontmatter as the most portable unit across the three tools. Treat instructions as portable Markdown with thin adapters. Treat agents, MCP, hooks, permissions, model choices, auth, caches, logs, histories, and runtime state as tool-specific unless explicitly designed as a safe adapter.

## Chezmoi
This directory lives under the rendered `~/.config` tree, so new files added here must also be captured in the upstream `chezmoi` source. Use `chezmoi add ~/.config/agents/<path>` after live edits, or edit the corresponding source path directly when the mapping is clear.
