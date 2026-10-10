#!/bin/sh

# SketchyBar starts outside the interactive shell and needs Homebrew on PATH.
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export PATH
queue_helper="$HOME/.config/tmux/scripts/codex-next-waiting.sh"

case "${1:---count}" in
  --count)
    if command -v tmux >/dev/null 2>&1 && [ -f "$queue_helper" ]; then
      /bin/sh "$queue_helper" --count 2>/dev/null
    else
      printf '0\n'
    fi
    ;;
  --click)
    command -v tmux >/dev/null 2>&1 || exit 0
    target="$(tmux list-panes -a -f '#{==:#{@codex_waiting},1}' -F '#{pane_id}' 2>/dev/null | sed -n '1p')"
    [ -n "$target" ] || exit 0

    # A menu-bar click has no tmux client context; select the most recently used one.
    client="$(tmux list-clients -F '#{client_activity} #{client_name}' 2>/dev/null | sort -rn | sed -n '1s/^[^ ]* //p')"
    [ -n "$client" ] || exit 0
    session="$(tmux display-message -p -t "$target" '#{session_id}' 2>/dev/null)" || exit 0
    tmux switch-client -c "$client" -t "$session" &&
      tmux select-window -t "$target" &&
      tmux select-pane -t "$target" || exit 0
    /bin/sh "$queue_helper" --clear-pane "$target"
    /usr/bin/osascript -e 'tell application "kitty" to activate'
    ;;
  *) exit 2 ;;
esac
