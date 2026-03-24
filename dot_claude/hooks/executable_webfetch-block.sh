#!/bin/bash
# webfetch-block.sh — PreToolUse:WebFetch hook
# Blocks all WebFetch calls and suggests using context-mode fetch_and_index instead.
#
# Event: PreToolUse | Matcher: WebFetch
# Output: Plain text message (exit 2 = block)
# Logging: JSONL event to ~/.claude/hooks/hook-events.jsonl

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/log.sh" 2>/dev/null
hook_guard "webfetch-block"
hook_timer_start 2>/dev/null

# Fail-open: if jq is missing, allow the call
command -v jq &>/dev/null || exit 0

# Extract the input JSON from stdin
INPUT=$(cat)
# Extract URL from the input
URL=$(echo "$INPUT" | jq -r '.tool_input.url // empty' 2>/dev/null)

# No URL found — allow (let WebFetch report its own error)
[ -z "$URL" ] && exit 0

# Extract domain from URL for logging (privacy — don't log full URL)
# Handles http://, https://, file:// URLs. For file:// URLs, domain will be empty.
URL_DOMAIN=$(echo "$URL" | sed -E 's|https?://([^/]+).*|\1|')

# Log the block decision
log_hook_event "webfetch-block" "decision" "block" "url_domain=$URL_DOMAIN" 2>/dev/null

# Output the block message (< 60 tokens, stderr for exit 2)
printf >&2 'BLOCKED: Use context-mode instead of WebFetch to avoid dumping raw HTML into context.\n'
printf >&2 'Run: mcp__plugin_context-mode_context-mode__ctx_fetch_and_index(url="%s")\n' "$URL"
printf >&2 'Then search: mcp__plugin_context-mode_context-mode__ctx_search(queries=[...], source="%s")\n' "$URL_DOMAIN"

exit 2
