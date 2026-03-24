#!/bin/bash
# ~/.claude/hooks/grep-observe.sh — PreToolUse:Grep
# Observability only — never blocks, just logs usage patterns.

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/log.sh" 2>/dev/null
hook_guard "grep-observe"
hook_timer_start 2>/dev/null

# Fail-open: if jq missing, silently allow
command -v jq &>/dev/null || exit 0

INPUT=$(cat)
PATTERN=$(echo "$INPUT" | jq -r '.tool_input.pattern // empty' 2>/dev/null)
[ -z "$PATTERN" ] && exit 0

SEARCH_PATH=$(echo "$INPUT" | jq -r '.tool_input.path // "."' 2>/dev/null)
GLOB_FILTER=$(echo "$INPUT" | jq -r '.tool_input.glob // empty' 2>/dev/null)

# Truncate pattern for privacy (no full regex in logs)
PATTERN_SHORT="${PATTERN:0:40}"

log_hook_event "grep-observe" "decision" "allow" \
  "pattern=$PATTERN_SHORT" \
  "path=$SEARCH_PATH" \
  "glob=$GLOB_FILTER" 2>/dev/null

exit 0
