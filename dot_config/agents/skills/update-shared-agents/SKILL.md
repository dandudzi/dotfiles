---
name: update-shared-agents
description: Update shared global instructions, reusable Agent Skills, and Claude/OpenCode-compatible agent prompt files across Codex, Claude Code, and OpenCode. Use when the user asks to change AGENTS.md or CLAUDE.md behavior, add or edit shared agents, move agent prompts into the shared agents folder, audit symlinks, or preserve one global instruction source across all three tools.
---

# Update Shared Agents

## Overview

Use this skill to maintain one shared source for portable AI-agent behavior while respecting each tool's different agent formats. The shared folder is `~/.config/agents`.

## Workflow

1. Read `~/.config/AGENTS.md` and `~/.config/agents/AGENTS.md` first.
2. Inspect the current live target paths before changing symlinks or files.
3. Decide whether the requested change belongs in `global.md`, `skills/<name>/SKILL.md`, `agents/<role>.md`, or a tool-specific wrapper.
4. Preserve the one-shared-folder model. Do not create separate per-tool shared folders unless the user explicitly requests that split.
5. For shared Markdown agents, keep frontmatter compatible with Claude Code and OpenCode unless the user accepts tool-specific divergence.
6. For Codex custom agents, use a separate TOML adapter only when requested; do not pretend the Claude/OpenCode Markdown agent file is directly compatible.
7. Capture rendered-dotfile changes with `chezmoi add` and verify symlink targets by reading them back.

## Canonical Locations

- Global instructions: `~/.config/agents/global.md`
- Portable skills: `~/.config/agents/skills/<name>/SKILL.md`
- Shared Claude/OpenCode agents: `~/.config/agents/agents/<role>.md`
- Shared hook scripts: `~/.config/agents/hooks/<script>`
- MCP intent: `~/.config/agents/mcp.md`

## Guardrails

- Do not overwrite existing live files without inspecting them.
- Do not move credentials, OAuth files, caches, histories, logs, sessions, model defaults, or permission settings into the shared folder.
- Do not link OpenCode skills to an extra path if it would cause duplicate skill discovery; prefer the existing shared `~/.agents/skills` path unless tested.
- Keep user-facing instructions concise and durable. Put operational details for future agents in `AGENTS.md`, not in every prompt file.

## Tool Map

Read `references/agent-tool-map.md` before changing symlink targets or agent prompt formats.

## Output Standard

Report the canonical file changed, all symlinked tool paths affected, any tool-specific adapters needed, and any existing config intentionally left untouched.
