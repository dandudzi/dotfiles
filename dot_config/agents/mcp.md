# Shared MCP Intent

Use this file to document MCP servers that should be available across Codex, Claude Code, and OpenCode.

This is not an active MCP config file. Each tool uses a different schema:

- Codex configures MCP servers in `~/.codex/config.toml` or trusted project `.codex/config.toml`.
- Claude Code uses project `.mcp.json` for shared project MCP servers and `~/.claude.json` for user or local MCP state.
- OpenCode configures MCP servers under `mcp` in `~/.config/opencode/opencode.json` or project `opencode.json`.

Keep server names, commands, URLs, and non-secret setup notes here. Keep tokens, OAuth state, secret headers, and machine-local credentials out of this file.
