# MCP Tool Map

Use this map when installing or auditing MCP servers across Codex, Claude Code, and OpenCode.

## Shared Intent

Canonical notes live in `~/.config/agents/mcp.md`. Store server names, purpose, transport, command, URL, package name, and required environment variable names. Do not store secret values.

## Codex

Active global MCP config belongs in `~/.codex/config.toml` unless the user asks for a trusted project `.codex/config.toml`.

Expected shape:

```toml
[mcp_servers.server_name]
command = "command"
args = ["arg1", "arg2"]
env = { TOKEN = "$TOKEN" }
```

Use the exact schema supported by the installed Codex version. If unsure, check official OpenAI Codex docs before editing.

## Claude Code

Project-shared MCP config belongs in `.mcp.json`. User/local MCP and OAuth state may live in `~/.claude.json` and should not be versioned or treated as shared.

Expected project shape commonly uses `mcpServers`:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "command",
      "args": ["arg1", "arg2"],
      "env": {
        "TOKEN": "$TOKEN"
      }
    }
  }
}
```

Prefer project `.mcp.json` for shareable non-secret config. Use Claude CLI helpers only when the user requests that workflow.

## OpenCode

Active global MCP config belongs under `mcp` in `~/.config/opencode/opencode.json` unless the user asks for project `opencode.json`.

Expected shape:

```json
{
  "mcp": {
    "server-name": {
      "type": "local",
      "command": ["command", "arg1", "arg2"],
      "enabled": true
    }
  }
}
```

OpenCode supports local and remote-style MCP entries depending on version. Check official OpenCode docs before using fields that are not already present in the user's config.
