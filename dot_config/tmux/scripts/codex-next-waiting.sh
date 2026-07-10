#!/bin/sh

# Pick the first window with a pending bell across every tmux session. Visiting
# it clears the flag, so pressing the binding repeatedly drains the queue.
target="$(
  tmux list-windows -a -f '#{window_bell_flag}' \
    -F '#{session_name}:#{window_index}' | sed -n '1p'
)"

if [ -z "$target" ]; then
  tmux display-message "No Codex session needs input"
  exit 0
fi

session="${target%%:*}"
tmux select-window -t "$target"
tmux switch-client -t "$session"
