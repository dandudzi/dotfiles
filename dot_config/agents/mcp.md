# Codex MCP Notes

Record non-secret MCP server names, commands, URLs, and setup notes here so installations remain understandable. This file is documentation; active servers are configured in `~/.codex/config.toml` or trusted project `.codex/config.toml` under `mcp_servers`.

Keep tokens, OAuth state, secret headers, and machine-local credentials out of this file. Configure only Codex unless another tool is explicitly requested.

## Servers

### gitnexus

- Purpose: Code graph search, symbol context, and change impact analysis.
- Transport: Local stdio MCP.
- Installation: Global mise tool `npm:gitnexus`, separate from Node's global package directory so Node upgrades do not remove it.
- Command: `/opt/homebrew/bin/mise exec -- gitnexus mcp`
- Build setup: Scope `allow_builds` to `@ladybugdb/core` and `gitnexus` for the database binary and vendored grammars.
- Authentication: None.
- Updates: `mise upgrade npm:gitnexus`. Restart the MCP client after changing its launcher.

### exa

- Purpose: Web search and webpage fetch tools.
- Transport: Remote HTTP MCP.
- URL: `https://mcp.exa.ai/mcp`
- Default tools: `web_search_exa`, `web_fetch_exa`.
- Authentication: Not required for default hosted search/fetch usage. `EXA_API_KEY` or an `x-api-key` header can be added in private tool configs for higher limits or paid/agent tools.

### context7

- Purpose: Up-to-date library and API documentation lookup.
- Transport: Remote HTTP MCP, matching the active Codex setup.
- URL: `https://mcp.context7.com/mcp`
- Authentication: Optional for basic usage. When used, keep the `CONTEXT7_API_KEY` value only in private tool-specific configuration; never record it here.

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
