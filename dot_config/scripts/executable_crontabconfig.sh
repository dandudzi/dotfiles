#!/bin/bash

# Define the cron job you want to ensure is present
CRON_JOB="0 * * * * ~/.config/scripts/removeOldTmuxSessions.sh"

# Temporary file for storing the current crontab
CRON_TEMP=$(mktemp)

# Load current crontab into a temporary file
crontab -l >"$CRON_TEMP"

# Check if the specific cron job already exists
if ! grep -qF "$CRON_JOB" "$CRON_TEMP"; then
  # If not, add the new cron job
  echo "$CRON_JOB" >>"$CRON_TEMP"
  # Install the new crontab with the added job
  crontab "$CRON_TEMP"
fi

# Clean up the temporary file
command rm "$CRON_TEMP"
