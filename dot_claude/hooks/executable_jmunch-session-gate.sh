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

RETRY_AT=2
MAX_BLOCKS=4

# Read stdin once — we need it for both sentinel hash and tool name
INPUT=$(cat)
CWD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null)
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
    exit 0
  fi
fi

# Extract tool name from the already-read input
TOOL=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

# Always allow: jCodeMunch/jDocMunch tools (needed to CREATE the sentinel)
case "$TOOL" in
  mcp__jcodemunch__*|mcp__jdocmunch__*) exit 0 ;;
esac

# Always allow: ToolSearch (needed to fetch deferred tool schemas for jmunch)
case "$TOOL" in
  ToolSearch) exit 0 ;;
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

# At RETRY_AT, re-emit the full indexing instructions (second chance trigger)
if [ "$BLOCKS" -eq "$RETRY_AT" ]; then
  echo "BLOCKED ($BLOCKS/$MAX_BLOCKS): Indexes still missing — retrying index trigger.

**MANDATORY — run BOTH of these NOW before any other tool call:**
1. Fetch schemas: ToolSearch(\"select:mcp__jcodemunch__index_folder,mcp__jdocmunch__index_local\")
2. Run BOTH in parallel:
   - mcp__jcodemunch__index_folder(path=\".\", incremental=true, use_ai_summaries=false)
   - mcp__jdocmunch__index_local(path=\".\", use_ai_summaries=false)

Tell the user: \"Index refresh was missed at session start — running it now.\"
Auto-bypass in $((MAX_BLOCKS - BLOCKS)) more blocked calls."
  exit 2
fi

# Standard block message
echo "BLOCKED ($BLOCKS/$MAX_BLOCKS): jCodeMunch/jDocMunch indexes not yet refreshed this session.
Run BOTH of these IMMEDIATELY before doing any other work:
  1. mcp__jcodemunch__index_folder(path='.', incremental=true, use_ai_summaries=false)
  2. mcp__jdocmunch__index_local(path='.', use_ai_summaries=false)
Do NOT respond to the user first. Run the indexes NOW.
Auto-bypass in $((MAX_BLOCKS - BLOCKS)) more blocked calls."
exit 2
