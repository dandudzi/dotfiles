#!/bin/sh

count_waiting() {
  tmux list-panes -a -f '#{==:#{@codex_waiting},1}' -F x |
    awk 'END { print NR + 0 }'
}

update_count() {
  tmux set-option -gq @codex_waiting_count "$(count_waiting)"
}

is_codex_pane() {
  command="$(tmux display-message -p -t "$1" '#{pane_current_command}' 2>/dev/null)" ||
    return 1

  case "$command" in
    codex | codex-*) return 0 ;;
    *) return 1 ;;
  esac
}

focus_pane() {
  target="$1"
  session="$(tmux display-message -p -t "$target" '#{session_name}')"
  window="$(tmux display-message -p -t "$target" '#{session_name}:#{window_index}')"

  tmux switch-client -t "$session"
  tmux select-window -t "$window"
  tmux select-pane -t "$target"
}

focus_waiting_pane() {
  target="$1"

  focus_pane "$target"
  tmux set-option -pqu -t "$target" @codex_waiting
  update_count
}

choose_waiting_pane() {
  separator="$(printf '\t')"
  choices="$(
    tmux list-panes -a -f '#{==:#{@codex_waiting},1}' \
      -F "#{session_name}:#{window_index}.#{pane_index}${separator}#{pane_id}"
  )"

  # Gum treats an empty input stream as a request to list files. Keep the
  # dialog open with a non-pane empty-state row instead.
  if [ -z "$choices" ]; then
    choices='No Codex pane needs attention'
  fi

  target="$(
    printf '%s\n' "$choices" |
      gum filter --limit 1 --no-show-help \
        --header 'Codex panes needing attention' \
        --placeholder 'Filter panes' \
        --prompt '⚡ '
  )" || return 0

  # The pane id is kept after a tab so the menu remains readable and searchable.
  target="$(printf '%s\n' "$target" | awk -F '\t' 'NF >= 2 { print $NF; exit }')"

  if [ -z "$target" ]; then
    tmux display-message "No Codex pane needs attention"
    return 0
  fi

  focus_waiting_pane "$target"
}

active_codex_choices() {
  separator="$(printf '\t')"

  tmux list-panes -a \
    -F "#{pane_current_command}${separator}#{pane_title}${separator}#{session_name}:#{window_index}.#{pane_index}${separator}#{pane_id}" |
    awk -F "$separator" '
      $1 == "codex" || $1 ~ /^codex-/ {
        # Codex prefixes its pane title with a rotating Braille spinner while
        # a turn is running. Keep that live marker in front of the picker row.
        marker = ""
        if ($2 ~ /^(⠋|⠙|⠹|⠸|⠼|⠴|⠦|⠧|⠇|⠏)[[:space:]]/) {
          split($2, title, " ")
          marker = title[1] " "
        }
        print marker $3 FS $4
      }
    '
}

choose_active_codex_pane() {
  separator="$(printf '\t')"
  choices="$(active_codex_choices)"

  # Gum treats an empty input stream as a request to list files. Keep the
  # dialog open with a non-pane empty-state row instead.
  if [ -z "$choices" ]; then
    choices='No active Codex pane'
  fi

  target="$(
    printf '%s\n' "$choices" |
      fzf --height=100% --layout=reverse --no-info \
        --header 'Active Codex panes' \
        --ghost 'Filter active Codex panes' \
        --prompt '⚡ ' \
        --bind 'left-click:accept'
  )" || return 0

  # The pane id is kept after a tab so the menu remains readable and searchable.
  target="$(printf '%s\n' "$target" | awk -F '\t' 'NF >= 2 { print $NF; exit }')"

  if [ -z "$target" ]; then
    tmux display-message "No active Codex pane"
    return 0
  fi

  focus_pane "$target"
}

# Print or refresh the number used by the tmux session status module.
if [ "${1:-}" = "--count" ]; then
  count_waiting
  exit 0
fi

if [ "${1:-}" = "--update-count" ]; then
  update_count
  exit 0
fi

# The alert-bell hook runs in the pane which emitted the BEL. Store the alert on
# that pane so multiple Codex panes in one window remain independently jumpable.
if [ "${1:-}" = "--mark-pane" ]; then
  pane="${2:-}"
  if [ -n "$pane" ] && is_codex_pane "$pane"; then
    tmux set-option -pq -t "$pane" @codex_waiting 1
  fi
  update_count
  exit 0
fi

if [ "${1:-}" = "--clear-pane" ]; then
  pane="${2:-}"
  if [ -n "$pane" ]; then
    tmux set-option -pqu -t "$pane" @codex_waiting
  fi
  update_count
  exit 0
fi

if [ "${1:-}" = "--choose" ]; then
  choose_waiting_pane
  exit 0
fi

if [ "${1:-}" = "--choose-active" ]; then
  choose_active_codex_pane
  exit 0
fi

# Pick the first Codex pane with a pending notification across every session.
# Selecting it clears the flag, so pressing the binding repeatedly drains the
# queue even when multiple Codex panes share a window.
target="$(
  tmux list-panes -a -f '#{==:#{@codex_waiting},1}' \
    -F '#{pane_id}' | sed -n '1p'
)"

if [ -z "$target" ]; then
  tmux display-message "No Codex pane needs attention"
  exit 0
fi

focus_waiting_pane "$target"
