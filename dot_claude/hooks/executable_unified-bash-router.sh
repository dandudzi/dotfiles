#!/bin/bash
# unified-bash-router.sh — PreToolUse:Bash
# Routes Bash commands: allow-list → RTK rewrite → unknown passthrough
# NEVER blocks (all paths exit 0). May rewrite via JSON updatedInput.

# Fail-open: if jq missing, allow everything
command -v jq &>/dev/null || exit 0

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
[ -z "$CMD" ] && exit 0

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/log.sh" 2>/dev/null
hook_guard "unified-bash-router"
hook_timer_start 2>/dev/null

# ── SAFETY: Subshell commands bypass allow-list ─────────────
# Backticks and $() can't be structurally classified — allow through, log.
# Note: && and || are NOT guarded — RTK handles chained commands correctly.
case "$CMD" in
  *'`'*|*'$('*)
    log_hook_event "unified-bash-router" "decision" "allow_passthrough" "route=subshell" "cmd=${CMD:0:80}" 2>/dev/null
    exit 0
    ;;
esac

# ── Strip leading env-var assignments (KEY=VALUE) ─────────────
CMD_BASE=$(echo "$CMD" | sed 's/^[A-Z_][A-Z0-9_]*=[^ ]* *//')
[ -z "$CMD_BASE" ] && CMD_BASE="$CMD"

# ── STEP 1: Structural allow-list (fast exit, no subprocess) ─
# git write operations
case "$CMD_BASE" in
  "git status"*) ;; # NOT a write op — fall through to RTK
  "git add "*|"git commit "*|"git push"*|"git pull"*) exit 0 ;;
  "git checkout "*|"git branch"*|"git stash"*|"git merge "*) exit 0 ;;
  "git tag "*|"git remote "*|"git fetch"*|"git rebase "*) exit 0 ;;
  "git config "*|"git init"*|"git clone "*) exit 0 ;;
esac

# git read with explicit bounds
case "$CMD_BASE" in
  *"git diff --stat"*|*"git diff --name"*) exit 0 ;;
  *"git log -"[0-9]*|*"git log --oneline"*) exit 0 ;;
  *"git log -n "[0-9]*) exit 0 ;;
esac

# filesystem utils
case "$CMD_BASE" in
  "ls"*) ;; # ls falls through to RTK (rtk ls compresses output)
  "mkdir "*|"rmdir "*|"touch "*|"chmod "*|"mv "*|"cp "*) exit 0 ;;
  "cd "*|"wc "*|"head "*|"tail "*|"basename "*|"dirname "*) exit 0 ;;
  "pwd"|"which "*|"echo "*|"date"*|"id"|"whoami") exit 0 ;;
esac

# package management
case "$CMD_BASE" in
  "npm install"*|"npm ci"*|"pip install"*|"uv "*) exit 0 ;;
  "npx "*|"pnpm install"*|"yarn install"*|"yarn add"*) exit 0 ;;
esac

# tiny inline utils
case "$CMD_BASE" in
  "cat "*|"jq "*) exit 0 ;;
  "python"*"-c "*|"python3"*"-c "*) exit 0 ;;
  "python"*"-m pip"*|"python3"*"-m pip"*) exit 0 ;;
  "python"*"-m json.tool"*|"python3"*"-m json.tool"*) exit 0 ;;
esac

# output redirected — check original CMD
case "$CMD" in
  *" > "*|*" >> "*) exit 0 ;;
esac

# infrastructure commands
case "$CMD_BASE" in
  *"jmunch-ready"*|*"jmunch-session"*|*"md5"*|"rtk "*) exit 0 ;;
esac

# ── STEP 2: RTK rewrite ──────────────
if command -v rtk &>/dev/null; then
  RTK_VERSION=$(rtk --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
  SKIP_RTK=0
  if [ -n "$RTK_VERSION" ]; then
    MAJOR=$(echo "$RTK_VERSION" | cut -d. -f1)
    MINOR=$(echo "$RTK_VERSION" | cut -d. -f2)
    [ "$MAJOR" -eq 0 ] && [ "$MINOR" -lt 23 ] && SKIP_RTK=1
  fi

  if [ "$SKIP_RTK" -eq 0 ]; then
    REWRITTEN=$(rtk rewrite "$CMD" 2>/dev/null) || REWRITTEN=""

    if [ -n "$REWRITTEN" ] && [ "$CMD" != "$REWRITTEN" ]; then
      ORIGINAL_INPUT=$(echo "$INPUT" | jq -c '.tool_input')
      UPDATED_INPUT=$(echo "$ORIGINAL_INPUT" | jq --arg cmd "$REWRITTEN" '.command = $cmd')

      log_hook_event "unified-bash-router" "decision" "rewrite" "route=rtk_rewrite" "cmd=${CMD:0:80}" 2>/dev/null

      jq -n \
        --argjson updated "$UPDATED_INPUT" \
        '{
          "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "RTK auto-rewrite",
            "updatedInput": $updated
          }
        }'
      exit 0
    fi
  fi
fi

# ── STEP 3: Unknown command → allow and observe ─────────────
log_hook_event "unified-bash-router" "unknown" "allow_passthrough" "cmd=${CMD:0:80}" 2>/dev/null
exit 0
