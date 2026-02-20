#!/bin/bash
set -euo pipefail

STATE_FILE="$HOME/.claude/fitness-state.json"

if [ ! -f "$STATE_FILE" ]; then
    echo "No fitness data yet. Complete your first exercise round to start tracking!"
    exit 0
fi

if ! jq empty "$STATE_FILE" 2>/dev/null; then
    echo "Error: State file is corrupted" >&2
    exit 1
fi

PUSHUPS=$(jq '.totals.pushups' "$STATE_FILE")
SQUATS=$(jq '.totals.squats' "$STATE_FILE")
SITUPS=$(jq '.totals.situps' "$STATE_FILE")
ROUNDS=$(jq '.rounds_completed' "$STATE_FILE")

TARGET=10000
ROUNDS_REMAINING=$((1000 - ROUNDS))

PUSHUPS_PCT=$((PUSHUPS * 1000 / TARGET))
SQUATS_PCT=$((SQUATS * 1000 / TARGET))
SITUPS_PCT=$((SITUPS * 1000 / TARGET))

format_bar() {
    local pct_x10=$1
    local filled=$((pct_x10 * 10 / 100))
    printf "["
    for ((i=0; i<filled; i++)); do printf "#"; done
    for ((i=filled; i<10; i++)); do printf "-"; done
    printf "]"
}

format_pct() {
    local pct_x10=$1
    local whole=$((pct_x10 / 10))
    local frac=$((pct_x10 % 10))
    printf "%d.%d%%" "$whole" "$frac"
}

printf "=== 10K Challenge Progress ===\n"
printf "Push-ups: %s / 10,000  %s  %s\n" "$PUSHUPS" "$(format_bar $PUSHUPS_PCT)" "$(format_pct $PUSHUPS_PCT)"
printf "Squats:   %s / 10,000  %s  %s\n" "$SQUATS" "$(format_bar $SQUATS_PCT)" "$(format_pct $SQUATS_PCT)"
printf "Sit-ups:  %s / 10,000  %s  %s\n" "$SITUPS" "$(format_bar $SITUPS_PCT)" "$(format_pct $SITUPS_PCT)"
printf "\nRounds completed: %s / 1,000\n" "$ROUNDS"
printf "Rounds remaining: %s\n" "$ROUNDS_REMAINING"
