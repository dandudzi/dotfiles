---
name: refresh-agent-auth
description: Diagnose and renew GitHub CLI and Codex Linear credentials when authentication fails during agent work.
---

# Refresh Agent Authentication

Run `python3 ~/.config/agents/skills/refresh-agent-auth/scripts/refresh_auth.py check` when `gh` or Linear authentication fails. The script checks `gh` and the Linear operator's current macOS Keychain token. It cannot verify Codex's separate Linear MCP OAuth grant; confirm that connection with a read-only Linear tool call.

If the check reports an invalid or missing credential, run the script with `repair` in an interactive terminal. Use `repair --linear-oauth` only after the Codex Linear MCP connection itself fails authentication. GitHub renewal uses `gh auth login`; operator token replacement prompts through macOS Keychain; MCP OAuth renewal uses `codex mcp login linear`. A network or Keychain access failure is not evidence that a credential expired. Do not print, copy, or commit token values.

The operator's token comes from Keychain item `codex-linear-operator-token` for account `linear-operator`. The `codex` shell launcher reads it when a process starts. After replacement, start a new agent process to pick up the new token; an already running process keeps its inherited environment. Recheck the failing operation after renewal.
