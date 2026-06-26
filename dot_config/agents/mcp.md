# Shared MCP Intent

Use this file to document MCP servers that should be available across Codex, Claude Code, and OpenCode.

This is not an active MCP config file. Each tool uses a different schema:

- Codex configures MCP servers in `~/.codex/config.toml` or trusted project `.codex/config.toml`.
- Claude Code uses project `.mcp.json` for shared project MCP servers and `~/.claude.json` for user or local MCP state.
- OpenCode configures MCP servers under `mcp` in `~/.config/opencode/opencode.json` or project `opencode.json`.

Keep server names, commands, URLs, and non-secret setup notes here. Keep tokens, OAuth state, secret headers, and machine-local credentials out of this file.

## Servers

### exa

- Purpose: Web search and webpage fetch tools.
- Transport: Remote HTTP MCP.
- URL: `https://mcp.exa.ai/mcp`
- Default tools: `web_search_exa`, `web_fetch_exa`.
- Authentication: Not required for default hosted search/fetch usage. `EXA_API_KEY` or an `x-api-key` header can be added in private tool configs for higher limits or paid/agent tools.

### context7

- Purpose: Up-to-date library and API documentation lookup.
- Transport: Local stdio MCP via npm package.
- Command: `npx -y @upstash/context7-mcp`
- Authentication: Optional for basic usage. `CONTEXT7_API_KEY` can be added in private tool configs for higher limits or private repositories.
