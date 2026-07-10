#!/bin/sh

# Codex appends its agent-turn-complete JSON payload as the final argument.
payload="${1:-}"
script_dir="${0%/*}"

# A Codex process launched inside tmux keeps the pane ID in its environment.
# Mark that exact pane before forwarding the event to the existing desktop
# Computer Use notification handler.
if [ -n "${TMUX_PANE:-}" ] && tmux display-message -p -t "$TMUX_PANE" >/dev/null 2>&1; then
  /bin/sh "$script_dir/codex-next-waiting.sh" \
    --mark-pane "$TMUX_PANE"
fi

exec "$HOME/.codex/computer-use/Codex Computer Use.app/Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient" \
  turn-ended "$payload"
