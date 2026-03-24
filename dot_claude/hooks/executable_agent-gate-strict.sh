#!/bin/bash
# agent-gate-strict.sh — PreToolUse:Agent
# BLOCKS agents without tool routing instructions. 3-tier classification.
# Uses JSON hookSpecificOutput deny + exit 0 for blocks (NOT exit 2).

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/log.sh" 2>/dev/null
hook_guard "agent-gate-strict"
hook_timer_start 2>/dev/null

# Fail-open: if jq missing, allow
command -v jq &>/dev/null || exit 0

INPUT=$(cat)
SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty' 2>/dev/null)
PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)

# No prompt = allow (might be a resume)
[ -z "$PROMPT" ] && { log_hook_event "agent-gate-strict" "decision" "allow" "tier=no_prompt" "subagent_type=$SUBAGENT_TYPE" 2>/dev/null; exit 0; }

# ── TIER 1: Exempt agents ───────────────────────────────────
case "$SUBAGENT_TYPE" in
  claude-code-guide) log_hook_event "agent-gate-strict" "decision" "allow" "tier=exempt" "subagent_type=$SUBAGENT_TYPE" 2>/dev/null; exit 0 ;;
esac

# ── TIER 2: Doc-only agents ─────────────────────────────────
case "$SUBAGENT_TYPE" in
  docs-agent)
    if echo "$PROMPT" | grep -qi "jdocmunch\|mcp__jdocmunch\|search_sections\|get_section"; then
      log_hook_event "agent-gate-strict" "decision" "allow" "tier=doc" "subagent_type=$SUBAGENT_TYPE" 2>/dev/null
      exit 0
    fi
    log_hook_event "agent-gate-strict" "decision" "block" "tier=doc" "subagent_type=$SUBAGENT_TYPE" 2>/dev/null
    jq -n \
      --arg reason "BLOCKED: Agent prompt must include jDocMunch instructions" \
      --arg context "search_sections to find doc sections, get_section for content by ID. Read ONLY for small docs (<50 lines) or CLAUDE.md." \
      '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason,"additionalContext":$context}}'
    exit 0
    ;;
esac

# ── TIER 3: All other agents ────────────────────────────────
HAS_CODE="no"
echo "$PROMPT" | grep -qi "jcodemunch\|mcp__jcodemunch\|get_symbol\|search_symbols\|get_file_outline" && HAS_CODE="yes"

HAS_DOCS="no"
echo "$PROMPT" | grep -qi "jdocmunch\|mcp__jdocmunch\|search_sections\|get_section" && HAS_DOCS="yes"

[ "$HAS_CODE" = "yes" ] && [ "$HAS_DOCS" = "yes" ] && { log_hook_event "agent-gate-strict" "decision" "allow" "tier=code" "subagent_type=$SUBAGENT_TYPE" 2>/dev/null; exit 0; }

MISSING=""
[ "$HAS_CODE" = "no" ] && [ "$HAS_DOCS" = "no" ] && MISSING="jCodeMunch AND jDocMunch"
[ "$HAS_CODE" = "no" ] && [ "$HAS_DOCS" = "yes" ] && MISSING="jCodeMunch"
[ "$HAS_CODE" = "yes" ] && [ "$HAS_DOCS" = "no" ] && MISSING="jDocMunch"

log_hook_event "agent-gate-strict" "decision" "block" "tier=code" "missing=$MISSING" "subagent_type=$SUBAGENT_TYPE" 2>/dev/null

CONTEXT=""
[ "$HAS_CODE" = "no" ] && CONTEXT="Code: Use jCodeMunch MCP — get_symbol for functions, search_symbols for definitions, get_file_content(start_line, end_line) for sliced edits. No raw Read on code files."
[ "$HAS_DOCS" = "no" ] && CONTEXT="$CONTEXT Docs: Use jDocMunch MCP — search_sections to find, get_section for content. Read only for <50 line docs."

jq -n \
  --arg reason "BLOCKED: Agent prompt missing $MISSING instructions. Add to prompt." \
  --arg context "$CONTEXT" \
  '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason,"additionalContext":$context}}'
exit 0
