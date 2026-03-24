#!/bin/bash
# unified-read-router.sh — PreToolUse:Read
# Routes Read calls by file extension. Denies first Read (suggests MCP), allows retry (for Edit).
# Uses deny-first-allow-retry: first Read of a code/doc/data file is denied with MCP suggestion.
# If model retries same file (needs Read before Edit), second attempt is allowed.
# Allows everything else.

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/log.sh" 2>/dev/null
hook_guard "unified-read-router"
hook_timer_start 2>/dev/null

# Fail-open: if jq missing, allow everything
command -v jq &>/dev/null || exit 0

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -z "$FILE_PATH" ] && exit 0

# ── SAFETY: reject /dev, /proc paths ────────
case "$FILE_PATH" in
  /dev/*|/proc/*) exit 0 ;;
esac

# ── SAFETY: resolve symlinks, reject outside $HOME ──────
if [ -L "$FILE_PATH" ]; then
  RESOLVED=$(readlink -f "$FILE_PATH" 2>/dev/null)
  if [ -n "$RESOLVED" ] && [[ ! "$RESOLVED" =~ ^"$HOME" ]]; then
    exit 0
  fi
fi

BASENAME="${FILE_PATH##*/}"
EXT="${FILE_PATH##*.}"
EXT_LOWER=$(printf '%s' "$EXT" | tr '[:upper:]' '[:lower:]')

# ── Helper: safe line count ──────
count_lines() {
  local file="$1" max="$2"
  [ -f "$file" ] || { echo 0; return; }
  local count
  count=$(head -"$((max + 1))" "$file" 2>/dev/null | wc -l)
  echo "${count:-0}"
}

# ── DENY-FIRST, ALLOW-RETRY mechanism ────────
# First Read of a routed file → deny (suggest MCP). Second Read → allow (needed for Edit).
# Marker: /tmp/read-deny-<md5 of filepath>. Created on first deny, removed on retry allow.
FILE_HASH=$(echo "$FILE_PATH" | md5 -q 2>/dev/null || echo "$FILE_PATH" | md5sum 2>/dev/null | cut -c1-32)
DENY_MARKER="/tmp/read-deny-${FILE_HASH}"
if [ -f "$DENY_MARKER" ]; then
  rm -f "$DENY_MARKER"
  log_hook_event "unified-read-router" "decision" "allow" "route=edit_retry" "file=$BASENAME" 2>/dev/null
  exit 0
fi

# ── GLOBAL EXCEPTIONS (always allow) ────────
case "$BASENAME" in
  CLAUDE.md|MEMORY.md|README.md|conftest.py) log_hook_event "unified-read-router" "decision" "allow" "route=global_exception" "file=$BASENAME" 2>/dev/null; exit 0 ;;
esac
case "$FILE_PATH" in
  */.vbw-planning/*|*/.planning/*|*/.claude/*) log_hook_event "unified-read-router" "decision" "allow" "route=global_exception" "file=$BASENAME" 2>/dev/null; exit 0 ;;
  *-PLAN.md|*-SUMMARY.md|*-UAT.md|*-CONTEXT.md) log_hook_event "unified-read-router" "decision" "allow" "route=global_exception" "file=$BASENAME" 2>/dev/null; exit 0 ;;
esac

# ── ROUTE 1: Code files ─────────────
case "$EXT_LOWER" in
  py|js|jsx|ts|tsx|go|rs|java|php|dart|cs|c|cpp|cc|cxx|hpp|hh|hxx|h|ex|exs|rb|rake|sql|xml|xul)
    # Small-file exception for headers/C/SQL only
    case "$EXT_LOWER" in
      h|hpp|hh|hxx|sql|c)
        LINE_COUNT=$(count_lines "$FILE_PATH" 50)
        [ "$LINE_COUNT" -lt 50 ] 2>/dev/null && { log_hook_event "unified-read-router" "decision" "allow" "route=small_file" "ext=$EXT_LOWER" "file=$BASENAME" 2>/dev/null; exit 0; }
        ;;
    esac
    # MCP unavailable fallback
    [ -d "$HOME/.code-index" ] || { log_hook_event "unified-read-router" "fallback" "allow" "reason=code_index_missing" "ext=$EXT_LOWER" 2>/dev/null; exit 0; }
    # DENY first Read — create marker so retry is allowed (for Edit workflow)
    touch "$DENY_MARKER"
    log_hook_event "unified-read-router" "decision" "block" "route=code" "ext=$EXT_LOWER" "file=$BASENAME" 2>/dev/null
    jq -n \
      --arg reason "BLOCKED: Use jCodeMunch instead of Read for $BASENAME" \
      --arg context "get_symbol for functions, search_symbols for definitions, get_file_content(start_line, end_line) for sliced edits. If you need to Read before Edit, retry this Read — second attempt is allowed." \
      '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason,"additionalContext":$context}}'
    exit 0
    ;;
esac

# ── ROUTE 2: Doc files ──────────────
case "$EXT_LOWER" in
  md|markdown|mdx|rst|txt|adoc|ipynb|html|svg|xhtml)
    LINE_COUNT=$(count_lines "$FILE_PATH" 50)
    [ "$LINE_COUNT" -lt 50 ] 2>/dev/null && { log_hook_event "unified-read-router" "decision" "allow" "route=small_file" "ext=$EXT_LOWER" "file=$BASENAME" 2>/dev/null; exit 0; }
    [ -d "$HOME/.doc-index/local" ] || { log_hook_event "unified-read-router" "fallback" "allow" "reason=doc_index_missing" "ext=$EXT_LOWER" 2>/dev/null; exit 0; }
    touch "$DENY_MARKER"
    log_hook_event "unified-read-router" "decision" "block" "route=doc" "ext=$EXT_LOWER" "lines=$LINE_COUNT" "file=$BASENAME" 2>/dev/null
    jq -n \
      --arg reason "BLOCKED: Use jDocMunch instead of Read for $BASENAME ($LINE_COUNT lines)" \
      --arg context "search_sections to find, get_section for content. If you need to Read before Edit, retry this Read — second attempt is allowed." \
      '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason,"additionalContext":$context}}'
    exit 0
    ;;
esac

# ── ROUTE 3: Data files (json/jsonc) ─────
case "$EXT_LOWER" in
  json|jsonc)
    [ -f "$FILE_PATH" ] || exit 0
    LINE_COUNT=$(count_lines "$FILE_PATH" 100)
    [ "$LINE_COUNT" -lt 100 ] 2>/dev/null && { log_hook_event "unified-read-router" "decision" "allow" "route=small_file" "ext=$EXT_LOWER" "file=$BASENAME" 2>/dev/null; exit 0; }
    touch "$DENY_MARKER"
    log_hook_event "unified-read-router" "decision" "block" "route=data" "ext=$EXT_LOWER" "lines=$LINE_COUNT" "file=$BASENAME" 2>/dev/null
    jq -n \
      --arg reason "BLOCKED: $BASENAME is $LINE_COUNT lines. Use context-mode for large JSON." \
      --arg context "ctx_execute_file for analysis, ctx_index then ctx_search for queries. If you need to Read before Edit, retry this Read — second attempt is allowed." \
      '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason,"additionalContext":$context}}'
    exit 0
    ;;
esac

# ── ROUTE 4: Everything else → allow ──────
log_hook_event "unified-read-router" "decision" "allow" "route=unknown_ext" "ext=$EXT_LOWER" "file=$BASENAME" 2>/dev/null
exit 0
