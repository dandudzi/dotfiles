#!/bin/bash
# hooks/websearch-block.sh — Block WebSearch calls, suggest alternatives
# Event: PreToolUse, Matcher: WebSearch
# Decision: Exit 2 (block) with plain text message (< 70 tokens)
# Observability: Logs block event to hook-events.jsonl

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/log.sh" 2>/dev/null
hook_guard "websearch-block"
hook_timer_start 2>/dev/null

# Fail-open: if jq missing, allow the call
command -v jq &>/dev/null || exit 0

INPUT=$(cat)
QUERY=$(echo "$INPUT" | jq -r '.tool_input.query // empty' 2>/dev/null)

# Fail-open: if no query found, allow
[ -z "$QUERY" ] && exit 0

# Truncate query for logging (privacy, max 60 chars)
QUERY_SHORT="${QUERY:0:60}"

# Log the block decision
log_hook_event "websearch-block" "decision" "block" "query=$QUERY_SHORT" 2>/dev/null

# Block with plain text message < 70 tokens (stderr for exit 2)
cat >&2 <<'EOF'
BLOCKED: Use specialized search tools instead of WebSearch:
- Web search: mcp__exa__web_search_exa(query="...") — neural search, structured results
- Library docs: mcp__context7__resolve-library-id then mcp__context7__query-docs
- Deep research: mcp__plugin_context-mode_context-mode__ctx_fetch_and_index(url="...") then ctx_search
EOF
exit 2
