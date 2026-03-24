#!/bin/bash
# mcp-observe.sh — PreToolUse:mcp__exa__*|mcp__context7__*
# Observability only — never blocks, logs Exa and Context7 usage.
# Paired with webfetch-block/websearch-block to track redirect effectiveness:
# if model uses Exa/Context7 instead of WebSearch/WebFetch, the redirect worked.

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/log.sh" 2>/dev/null
hook_guard "mcp-observe"
hook_timer_start 2>/dev/null

# Fail-open: if jq missing, silently allow
command -v jq &>/dev/null || exit 0

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
[ -z "$TOOL" ] && exit 0

# Extract query (different field names across tools)
QUERY=$(echo "$INPUT" | jq -r '.tool_input.query // .tool_input.libraryName // .tool_input.libraryId // empty' 2>/dev/null)
QUERY_SHORT="${QUERY:0:60}"

log_hook_event "mcp-observe" "decision" "allow" \
  "tool=$TOOL" \
  "query=$QUERY_SHORT" 2>/dev/null

exit 0
