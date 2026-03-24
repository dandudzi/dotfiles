#!/bin/bash
# PreToolUse:* hook — BLOCK all tools until jCodeMunch + jDocMunch indexes are refreshed
# Exit 2 = block the tool call with message
# Exit 0 = allow
#
# Sentinel: /tmp/jmunch-ready-<hash of cwd>
# Block counter: /tmp/jmunch-blocks-<hash of cwd>
# Hash is derived from project directory, stable across process wrappers and subagents.
#
# Recovery: At RETRY_AT blocked calls, re-emits full indexing instructions.
#           At MAX_BLOCKS blocked calls, auto-bypasses to prevent infinite lockout.
# Parallel safety: Sentinel uses append-only writes. Counter may race off-by-one
#                  across concurrent sessions — acceptable for a threshold check.
#
# Install: Copy to .claude/hooks/ in your project
# Register: PreToolUse matcher "*" in project .claude/settings.json
# Paired with: jmunch-session-start.sh, jmunch-sentinel-writer.sh

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/log.sh" 2>/dev/null
hook_guard "jmunch-session-gate"
hook_timer_start 2>/dev/null

RETRY_AT=2
MAX_BLOCKS=4

# Read stdin once — we need it for both sentinel hash and tool name
INPUT=$(cat)

# Use jq instead of python3 for JSON parsing (fail-open if jq missing)
if command -v jq &>/dev/null; then
  CWD=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
else
  CWD=""
fi
if [ -z "$CWD" ]; then
  CWD=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
fi
HASH=$(echo "$CWD" | md5 -q 2>/dev/null || echo "$CWD" | md5sum 2>/dev/null | cut -c1-32)
SENTINEL="/tmp/jmunch-ready-${HASH}"
BLOCK_COUNTER="/tmp/jmunch-blocks-${HASH}"

# If sentinel has both "code" and "doc" lines AND no "stale" marker, session is ready
if [ -f "$SENTINEL" ]; then
  HAS_CODE=$(grep -c '^code$' "$SENTINEL" 2>/dev/null | head -1 || echo 0)
  HAS_DOC=$(grep -c '^doc$' "$SENTINEL" 2>/dev/null | head -1 || echo 0)
  IS_STALE=$(grep -c '^stale$' "$SENTINEL" 2>/dev/null | head -1 || echo 0)
  if [ "${HAS_CODE:-0}" -gt 0 ] 2>/dev/null && [ "${HAS_DOC:-0}" -gt 0 ] 2>/dev/null && [ "${IS_STALE:-0}" -eq 0 ] 2>/dev/null; then
    rm -f "$BLOCK_COUNTER" 2>/dev/null
    log_hook_event "jmunch-session-gate" "decision" "allow" "reason=indexes_ready" 2>/dev/null
    exit 0
  fi
fi

# Extract tool name using jq (fail-open)
if command -v jq &>/dev/null; then
  TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
else
  TOOL=""
fi

# Always allow: MCP tools (don't need indexes, and Claude Code can't block MCP calls)
# Always allow: Agent (agent-gate-strict handles its own enforcement)
# Always allow: ToolSearch (needed to fetch deferred tool schemas)
# Always allow: Task* (task management doesn't need indexes)
case "$TOOL" in
  mcp__*|Agent|ToolSearch|Task*) log_hook_event "jmunch-session-gate" "decision" "allow" "reason=mcp_passthrough" "tool=$TOOL" 2>/dev/null; exit 0 ;;
esac

# Increment block counter (off-by-one race across parallel sessions is acceptable)
BLOCKS=0
if [ -f "$BLOCK_COUNTER" ]; then
  BLOCKS=$(cat "$BLOCK_COUNTER" 2>/dev/null || echo 0)
fi
BLOCKS=$((BLOCKS + 1))
echo "$BLOCKS" > "$BLOCK_COUNTER"

# After MAX_BLOCKS, auto-bypass to prevent infinite lockout
if [ "$BLOCKS" -ge "$MAX_BLOCKS" ]; then
  rm -f "$BLOCK_COUNTER" 2>/dev/null
  printf 'code\ndoc\n' > "$SENTINEL"
  echo "WARNING: Auto-bypassed after $MAX_BLOCKS blocked tool calls. Indexes may be stale.
Consider running them when convenient:
  1. mcp__jcodemunch__index_folder(path='.', incremental=true, use_ai_summaries=false)
  2. mcp__jdocmunch__index_local(path='.', use_ai_summaries=false)"
  exit 0
fi

# JSON deny — blocks tool call, model sees the reason and can act on it
# (exit 2 causes "hook error" for some tool types; JSON deny + exit 0 always works)
log_hook_event "jmunch-session-gate" "decision" "block" "tool=$TOOL" "blocks=$BLOCKS" 2>/dev/null
REASON="BLOCKED ($BLOCKS/$MAX_BLOCKS): jCodeMunch/jDocMunch indexes not refreshed. Run both: mcp__jcodemunch__index_folder(path='.', incremental=true, use_ai_summaries=false) and mcp__jdocmunch__index_local(path='.', use_ai_summaries=false)"
CONTEXT="Auto-bypass in $((MAX_BLOCKS - BLOCKS)) more blocked calls."

jq -n \
  --arg reason "$REASON" \
  --arg context "$CONTEXT" \
  '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason,"additionalContext":$context}}'
exit 0
