# Agent Tool Map

Use this map when editing shared instructions, skills, and agent prompts.

## Shared Folder

Canonical shared folder: `~/.config/agents`

Important files:

- `global.md`: portable global instructions linked into each tool.
- `skills/`: portable `SKILL.md` skill folders.
- `agents/`: shared Claude/OpenCode Markdown agents.
- `hooks/`: hook scripts called by tool-specific hook config.
- `mcp.md`: MCP intent notes, not active config.

## Codex

Global instructions: `~/.codex/AGENTS.md` can point to `~/.config/agents/global.md`.

Skills: Codex scans `~/.agents/skills` and project `.agents/skills`; symlink `~/.agents/skills` to `~/.config/agents/skills`.

Custom agents: Codex custom agents use TOML files under `~/.codex/agents/` or project `.codex/agents/`. Do not directly link Claude/OpenCode Markdown agents into Codex custom agents.

## Claude Code

Global instructions: `~/.claude/CLAUDE.md` can point to `~/.config/agents/global.md`.

Skills: `~/.claude/skills` can point to `~/.config/agents/skills`.

Subagents: `~/.claude/agents` can point to `~/.config/agents/agents`. Agent files are Markdown with YAML frontmatter and should include at least `name` and `description`.

## OpenCode

Global rules: `~/.config/opencode/AGENTS.md` can point to `~/.config/agents/global.md`.

Skills: OpenCode can read Agent Skills from `~/.agents/skills`; avoid adding another skill symlink unless duplicate discovery has been tested.

Agents: `~/.config/opencode/agents` can point to `~/.config/agents/agents`. Keep shared frontmatter compatible with Claude Code unless creating an OpenCode-only agent.

## Compatibility Rule

When one file must work in multiple tools, use the smallest common format. When a tool requires a different schema, create a wrapper or adapter outside the shared core and document why.
