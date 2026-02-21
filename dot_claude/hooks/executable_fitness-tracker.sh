#!/bin/bash
set -euo pipefail

STATE_FILE="$HOME/.claude/fitness-state.json"
NOW=$(date +%s)

command -v jq >/dev/null 2>&1 || {
  echo "jq is required but not installed" >&2
  exit 1
}

# Initialize state file if it does not exist
if [ ! -f "$STATE_FILE" ]; then
  cat >"$STATE_FILE" <<INIT
{
  "interaction_count": 0,
  "interactions_since_last_reminder": 0,
  "last_reminder_timestamp": $NOW,
  "pending_reminder": false,
  "pending_confirmation": false,
  "totals": {
    "pushups": 0,
    "squats": 0,
    "situps": 0
  },
  "rounds_completed": 0,
  "challenge_started": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
INIT
fi

# Read current state
STATE=$(cat "$STATE_FILE")
INTERACTION_COUNT=$(echo "$STATE" | jq '.interaction_count')
SINCE_LAST=$(echo "$STATE" | jq '.interactions_since_last_reminder')
LAST_REMINDER_TS=$(echo "$STATE" | jq '.last_reminder_timestamp')
PENDING_REMINDER=$(echo "$STATE" | jq -r '.pending_reminder')
PENDING_CONFIRMATION=$(echo "$STATE" | jq -r '.pending_confirmation')

# Increment counters
INTERACTION_COUNT=$((INTERACTION_COUNT + 1))
SINCE_LAST=$((SINCE_LAST + 1))

# Phase: Confirmation follow-up (confirmation was asked last time, now done)
if [ "$PENDING_CONFIRMATION" = "true" ]; then
  echo "$STATE" | jq \
    --argjson ic "$INTERACTION_COUNT" \
    --argjson sl "$SINCE_LAST" \
    '.interaction_count = $ic | .interactions_since_last_reminder = $sl | .pending_confirmation = false' \
    >"$STATE_FILE"
  exit 0
fi

# Phase: Ask about completion (reminder was shown last time)
if [ "$PENDING_REMINDER" = "true" ]; then
  echo "$STATE" | jq \
    --argjson ic "$INTERACTION_COUNT" \
    --argjson now "$NOW" \
    '.interaction_count = $ic | .interactions_since_last_reminder = 0 | .last_reminder_timestamp = $now | .pending_reminder = false | .pending_confirmation = true' \
    >"$STATE_FILE"

  cat <<'CONFIRM'
[FITNESS CHALLENGE - CHECK COMPLETION]
On the previous interaction, the user was reminded to do exercises (10 push-ups, 10 squats, 10 sit-ups). Before addressing their current message, briefly ask: "Did you complete your exercise round?"

If yes: run `bash $HOME/.claude/hooks/log-exercises.sh` and show the output.
If no/skip: acknowledge briefly and move on.
Then address whatever the user actually asked about.
CONFIRM
  exit 0
fi

# Phase: Check if it is time for a new reminder
TIME_ELAPSED=$((NOW - LAST_REMINDER_TS))

if [ "$SINCE_LAST" -ge 10 ] || [ "$TIME_ELAPSED" -ge 1800 ]; then
  echo "$STATE" | jq \
    --argjson ic "$INTERACTION_COUNT" \
    --argjson sl "$SINCE_LAST" \
    '.interaction_count = $ic | .interactions_since_last_reminder = $sl | .pending_reminder = true' \
    >"$STATE_FILE"

  # Fire macOS notification
  osascript -e 'display notification "Time for exercises! 10 push-ups, 10 squats, 10 sit-ups!" with title "10K Challenge" sound name "Ping"' 2>/dev/null || true

  cat <<'REMIND'
[FITNESS CHALLENGE REMINDER]
It is time for a round of exercises! Briefly tell the user:
"Quick reminder -- time for your exercise round! 10 push-ups, 10 squats, 10 sit-ups. Let me know on your next message if you completed them."
Then continue with your normal response to their prompt. Do NOT wait for exercise confirmation now.
REMIND
  exit 0
fi

# No action needed -- just update counters
echo "$STATE" | jq \
  --argjson ic "$INTERACTION_COUNT" \
  --argjson sl "$SINCE_LAST" \
  '.interaction_count = $ic | .interactions_since_last_reminder = $sl' \
  >"$STATE_FILE"
exit 0
