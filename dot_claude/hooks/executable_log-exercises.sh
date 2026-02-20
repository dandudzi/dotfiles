#!/bin/bash
set -euo pipefail

STATE_FILE="$HOME/.claude/fitness-state.json"

if [ ! -f "$STATE_FILE" ]; then
    echo "Error: State file not found" >&2
    exit 1
fi

# Update totals
jq '.totals.pushups += 10 | .totals.squats += 10 | .totals.situps += 10 | .rounds_completed += 1' \
    "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"

# Read updated values
PUSHUPS=$(jq '.totals.pushups' "$STATE_FILE")
SQUATS=$(jq '.totals.squats' "$STATE_FILE")
SITUPS=$(jq '.totals.situps' "$STATE_FILE")
ROUNDS=$(jq '.rounds_completed' "$STATE_FILE")

# Calculate percentages
PCT_P=$(echo "scale=1; $PUSHUPS * 100 / 10000" | bc)
PCT_SQ=$(echo "scale=1; $SQUATS * 100 / 10000" | bc)
PCT_SI=$(echo "scale=1; $SITUPS * 100 / 10000" | bc)

# Build progress bars (10 chars wide)
progress_bar() {
    local pct=$1
    local filled=$(echo "scale=0; $pct / 10" | bc)
    local empty=$((10 - filled))
    local bar=""
    for ((i=0; i<filled; i++)); do bar+="#"; done
    for ((i=0; i<empty; i++)); do bar+="-"; done
    echo "$bar"
}

BAR_P=$(progress_bar "$PCT_P")
BAR_SQ=$(progress_bar "$PCT_SQ")
BAR_SI=$(progress_bar "$PCT_SI")

echo "=== 10K Challenge Progress ==="
echo "Push-ups: $PUSHUPS / 10,000  [$BAR_P]  ${PCT_P}%"
echo "Squats:   $SQUATS / 10,000  [$BAR_SQ]  ${PCT_SQ}%"
echo "Sit-ups:  $SITUPS / 10,000  [$BAR_SI]  ${PCT_SI}%"
echo ""
echo "Rounds completed: $ROUNDS / 1,000"
echo "Rounds remaining: $((1000 - ROUNDS))"

if [ "$ROUNDS" -ge 1000 ]; then
    echo ""
    echo "CONGRATULATIONS! You completed the 10K Challenge!"
fi
