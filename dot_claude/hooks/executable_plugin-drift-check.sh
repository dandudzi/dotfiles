#!/bin/bash
# plugin-drift-check.sh — SessionStart hook
# Verifies context-mode plugin still covers expected matchers.
# Always exit 0 (informational, never blocks session start).

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/lib/log.sh" 2>/dev/null
hook_guard "plugin-drift-check"
hook_timer_start 2>/dev/null

CACHE_DIR="$HOME/.claude/plugins/cache/context-mode/context-mode"
LATEST=$(ls -d "$CACHE_DIR"/[0-9]* 2>/dev/null | sort -V | tail -1)

# Plugin not installed — warn
if [ -z "$LATEST" ]; then
  echo "WARNING: context-mode plugin not found. Context-mode routing may not work."
  log_hook_event "plugin-drift-check" "drift" "warn" "reason=plugin_missing" 2>/dev/null
  exit 0
fi

HOOKS_JSON="$LATEST/hooks/hooks.json"

# hooks.json missing — warn
if [ ! -f "$HOOKS_JSON" ]; then
  echo "WARNING: context-mode plugin hooks.json missing at $HOOKS_JSON"
  log_hook_event "plugin-drift-check" "drift" "warn" "reason=hooks_json_missing" 2>/dev/null
  exit 0
fi

# Check required matchers are still registered
REQUIRED_MATCHERS="Bash Read WebFetch Grep Agent Task"
MISSING=""

for matcher in $REQUIRED_MATCHERS; do
  if ! grep -q "\"$matcher\"" "$HOOKS_JSON" 2>/dev/null; then
    MISSING="$MISSING $matcher"
  fi
done

if [ -n "$MISSING" ]; then
  log_hook_event "plugin-drift-check" "drift" "warn" "missing=${MISSING# }" 2>/dev/null
  echo "WARNING: context-mode plugin hooks.json is missing matchers:$MISSING"
  echo "The compound matcher was removed because the plugin covered these."
  echo "Action: Check ~/.claude/plugins/cache/context-mode/ or reinstall the plugin."
fi

exit 0
