---
name: exa-search
description: Neural search via Exa MCP for web, code, and company research. Use when the user needs web search, code examples, company intel, people lookup, or AI-powered deep research with Exa's neural search engine.
origin: ECC
---

# Exa Search

Neural search for web content, code, companies, and people via the Exa MCP server.

## When to Activate

- User needs current web information or news
- Searching for code examples, API docs, or technical references
- Researching companies, competitors, or market players
- Finding professional profiles or people in a domain
- Running background research for any development task
- User says "search for", "look up", "find", or "what's the latest on"

## MCP Requirement

Exa MCP server must be configured. Add to `~/.claude.json`:

```json
"exa-web-search": {
  "command": "npx",
  "args": ["-y", "exa-mcp-server"],
  "env": { "EXA_API_KEY": "YOUR_EXA_API_KEY_HERE" }
}
```

Get an API key at [exa.ai](https://exa.ai).
This repo's current Exa setup documents the tool surface exposed here: `web_search_exa` and `get_code_context_exa`.
If your Exa server exposes additional tools, verify their exact names before depending on them in docs or prompts.

## Core Tools

### web_search_exa
General web search for current information, news, or facts.

```
web_search_exa(query: "latest AI developments 2026", numResults: 5)
```

**Parameters:**

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `query` | string | required | Search query |
| `numResults` | number | 8 | Number of results |
| `type` | string | `auto` | Search mode |
| `livecrawl` | string | `fallback` | Prefer live crawling when needed |
| `category` | string | none | Optional focus such as `company` or `research paper` |

### get_code_context_exa
Find code examples and documentation from GitHub, Stack Overflow, and docs sites.

```
get_code_context_exa(query: "Python asyncio patterns", tokensNum: 3000)
```

**Parameters:**

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `query` | string | required | Code or API search query |
| `tokensNum` | number | 5000 | Content tokens (1000-50000) |

## Usage Patterns

### Quick Lookup
```
web_search_exa(query: "Node.js 22 new features", numResults: 3)
```

### Code Research
```
get_code_context_exa(query: "Rust error handling patterns Result type", tokensNum: 3000)
```

### Company or People Research
```
web_search_exa(query: "Vercel funding valuation 2026", numResults: 3, category: "company")
web_search_exa(query: "site:linkedin.com/in AI safety researchers Anthropic", numResults: 5)
```

### Technical Deep Dive
```
web_search_exa(query: "WebAssembly component model status and adoption", numResults: 5)
get_code_context_exa(query: "WebAssembly component model examples", tokensNum: 4000)
```

## Tips

- Use `web_search_exa` for current information, company lookups, and broad discovery
- Use search operators like `site:`, quoted phrases, and `intitle:` to narrow results
- Lower `tokensNum` (1000-2000) for focused code snippets, higher (5000+) for comprehensive context
- Use `get_code_context_exa` when you need API usage or code examples rather than general web pages

## Query Security and Rate Limiting

**Input Validation — Sanitize user-supplied queries:**
- Maximum query length: 500 characters (enforce at application boundary)
- Strip control characters and null bytes from user input before forwarding to Exa
- Log all queries with user ID / session ID for audit trail and abuse detection
- Validate query format: reject queries with only special characters or excessive whitespace

**Rate Limiting — Implement client-side limits:**
- Use exponential backoff on 429 (Too Many Requests) responses
- Cache results for identical queries with TTL: 1 hour minimum
- Track query volume per user/API key; alert on anomalies (e.g., 10x normal volume)
- NEVER expose Exa API keys in frontend code — proxy all requests through backend service
- Implement per-user/session rate limits: e.g., 10 queries/minute for free tier, 100/minute for premium

**Result Handling — Treat results as untrusted external content:**
- Sanitize content before rendering in UI (prevent XSS injection)
- If passing search results to an LLM, wrap in untrusted content delimiters (e.g., `<untrusted>...</untrusted>`)
- Validate domain/URL format in results before following or displaying
- Strip executable content (script tags, iframes) from search snippets
- Example:
  ```python
  # WRONG: Direct HTML rendering
  html = render_html(search_result.snippet)  # XSS risk!

  # CORRECT: Sanitize before rendering
  from markupsafe import escape
  safe_snippet = escape(search_result.snippet)
  html = render_html(safe_snippet)
  ```

## Related Skills

- `deep-research` — Full research workflow using firecrawl + exa together
- `market-research` — Business-oriented research with decision frameworks
