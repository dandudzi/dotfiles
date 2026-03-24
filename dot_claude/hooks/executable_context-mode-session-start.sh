#!/usr/bin/env bash
# Version-agnostic context-mode session-start wrapper.
# Resolves the latest installed version from the plugin cache at runtime.
# Survives context-mode upgrades without any settings.json changes.

CACHE_DIR="$HOME/.claude/plugins/cache/context-mode/context-mode"

# Find the latest semantic version directory
LATEST=$(ls -d "$CACHE_DIR"/[0-9]* 2>/dev/null | sort -V | tail -1)

if [ -z "$LATEST" ]; then
  echo "context-mode not found in plugin cache at: $CACHE_DIR" >&2
  exit 0  # non-blocking — don't break session if context-mode is missing
fi

HOOK="$LATEST/hooks/sessionstart.mjs"

if [ ! -f "$HOOK" ]; then
  echo "context-mode sessionstart hook not found at: $HOOK" >&2
  exit 0
fi

exec node "$HOOK"
