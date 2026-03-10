#!/bin/bash
# Prompts Claude to re-index the current repo with jcodemunch.
# Usage:
#   SessionStart: ./jcodemunch-reindex.sh session-start  (stdout → context)
#   Stop:         ./jcodemunch-reindex.sh stop            (JSON additionalContext)
#
# Tracks last-indexed git HEAD in ~/.code-index/<repo-hash>-last-head
# to avoid redundant re-index prompts.

set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
REPO_HASH=$(echo "$REPO_ROOT" | md5 -q 2>/dev/null || echo "$REPO_ROOT" | md5sum | cut -d' ' -f1)
TRACKING_DIR="$HOME/.code-index"
TRACKING_FILE="$TRACKING_DIR/$REPO_HASH-last-head"

mkdir -p "$TRACKING_DIR"

EVENT="${1:-session-start}"

current_head=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo "unknown")

needs_reindex() {
  # Re-index if: no tracking file, HEAD changed, or working tree is dirty
  if [ ! -f "$TRACKING_FILE" ]; then
    return 0
  fi
  local last_head
  last_head=$(cat "$TRACKING_FILE" 2>/dev/null || echo "")
  if [ "$current_head" != "$last_head" ]; then
    return 0
  fi
  # Check for uncommitted changes (staged + unstaged)
  if ! git -C "$REPO_ROOT" diff --quiet HEAD 2>/dev/null; then
    return 0
  fi
  return 1
}

REPO_NAME=$(basename "$REPO_ROOT")
MSG="Re-index $REPO_NAME with jcodemunch: call index_folder with path=$REPO_ROOT, incremental=true, use_ai_summaries=true. Then update $TRACKING_FILE with the current HEAD ($current_head)."

case "$EVENT" in
  session-start)
    # Always re-index on session start
    echo "$MSG"
    ;;
  stop)
    # Only prompt if there are changes since last index
    if needs_reindex; then
      # JSON format for non-SessionStart hooks
      echo "{\"additionalContext\": \"$MSG\"}"
    fi
    ;;
esac
