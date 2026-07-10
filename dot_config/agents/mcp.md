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

### serena

- Purpose: Language-server-backed semantic code navigation, reference lookup, diagnostics, and symbol-level editing.
- Transport: Local stdio MCP.
- Installation: Global mise tool `pipx:serena-agent`, installed through mise's uv-backed pipx backend with Python 3.13.
- Command: `/opt/homebrew/bin/mise exec -- serena start-mcp-server --project-from-cwd --context=codex`
- Authentication: None.
- Setup note: Initialize once with `mise exec -- serena init`. Codex sessions may need to activate the current directory as a Serena project.

### playwright

- Purpose: Browser automation and web application inspection through Playwright accessibility snapshots.
- Transport: Local stdio MCP.
- Installation: Global mise tool `npm:@playwright/mcp`.
- Command: `/opt/homebrew/bin/mise exec -- playwright-mcp`
- Authentication: None. Website authentication stays in the browser profile selected for a Playwright session.
- Setup note: Browser binaries are downloaded automatically on first use when needed.

### linear

- Purpose: Read and manage Linear issues, projects, comments, cycles, and related workspace data.
- Transport: Remote Streamable HTTP MCP.
- URL: `https://mcp.linear.app/mcp`
- Authentication: OAuth 2.1 through `codex mcp login linear`; keep OAuth state out of this file.

### mermaid

- Purpose: Render Mermaid diagram definitions as SVG or PNG assets.
- Transport: Local stdio MCP.
- Installation: Global mise tool `npm:mcp-mermaid` from `hustcc/mcp-mermaid`; its reviewed package lifecycle script installs Chromium for rendering.
- Command: `/opt/homebrew/bin/mise exec -- mcp-mermaid`
- Authentication: None.
- Provenance note: Community-maintained server; Mermaid itself does not currently publish an official MCP server.
