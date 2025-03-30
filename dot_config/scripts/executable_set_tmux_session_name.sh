#!/bin/bash

# Get the current directory name or a specific project file
PROJECT_NAME=$(basename "$(pwd)")

# Set the tmux session name
tmux rename-session "$PROJECT_NAME"
