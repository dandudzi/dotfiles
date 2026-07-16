---
name: install-shared-mcp
description: Install, migrate, or update MCP server configuration across Codex, Claude Code, and OpenCode while preserving existing entries and secrets. Use when the user asks to add an MCP server, share MCP tools between agent environments, move MCP settings into the shared agents folder, audit current MCP setup, or generate per-tool MCP config wrappers from shared intent.
---

# Install Shared MCP

## Overview

Use this skill to add MCP servers safely across the three agent environments on this machine. Keep shared MCP intent in `~/.config/agents/mcp.md`, but write active config in each tool's native schema.

## Workflow

1. Read `~/.config/AGENTS.md`, `~/.config/agents/AGENTS.md`, and `~/.config/agents/mcp.md` before editing.
2. Inspect existing active config files before proposing or applying changes. Do not overwrite current MCP servers.
3. Identify the MCP transport, command or URL, required environment variables, and which values are secrets.
4. Record only non-secret shared intent in `~/.config/agents/mcp.md`.
5. Update the requested active tool configs in native format, preserving existing config and comments where possible.
6. Capture only exact rendered targets with `rtk chezmoi add <path>`.
7. Verify by reading back the changed files. If a tool has a safe MCP listing command available, run it only when it does not require credentials or destructive side effects.

## Guardrails

- Do not symlink one active MCP config file across Codex, Claude Code, and OpenCode. Their schemas differ.
- Use only `rtk chezmoi ...` for chezmoi source state; never access the source directory directly or change or override chezmoi configuration without explicit permission.
- Do not copy tokens, OAuth state, secret headers, or local credential paths into `agents/mcp.md`.
- Do not treat Claude `~/.claude.json` as shareable; it may contain user/local state.
- If a target active config exists, merge deliberately. If the requested change would replace unknown existing config, stop and ask.
- Prefer environment variable names in shared docs and leave actual secret values in the user's shell, keychain, or private local config.

## Tool Map

Read `references/mcp-tool-map.md` when implementing or auditing active MCP config.

## Output Standard

Report which MCP servers were found, which files changed, which secrets were intentionally omitted, and which tools still need manual authentication or restart.
