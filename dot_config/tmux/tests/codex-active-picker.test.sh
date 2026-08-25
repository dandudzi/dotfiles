#!/bin/sh

set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
script="$repo_root/tmux/scripts/codex-next-waiting.sh"
test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT

mkdir "$test_dir/bin"

export TEST_GUM_INPUT="$test_dir/gum-input"
export TEST_LOG="$test_dir/log"
export PATH="$test_dir/bin:$PATH"

: > "$TEST_GUM_INPUT"
: > "$TEST_LOG"

printf '%s\n' '#!/bin/sh' 'case "$1" in' '  list-panes) printf "%s\\t%s\\t%s\\n" "zsh" "main:1.1" "%1" "codex" "main:2.1" "%2" "codex-resume" "remote:3.2" "%3" ;;' '  display-message) case "$5" in "#{session_name}") printf "%s\\n" "remote" ;; "#{session_name}:#{window_index}") printf "%s\\n" "remote:3" ;; esac ;;' '  switch-client|select-window|select-pane|set-option) printf "tmux:%s:%s\\n" "$1" "$3" >> "$TEST_LOG" ;;' 'esac' > "$test_dir/bin/tmux"
printf '%s\n' '#!/bin/sh' 'sed -n "1,2p" > "$TEST_GUM_INPUT"' 'printf "%s\\t%s\\n" "remote:3.2" "%3"' > "$test_dir/bin/gum"
chmod +x "$test_dir/bin/tmux" "$test_dir/bin/gum"

sh "$script" --choose-active

expected_choices="$(printf '%s\t%s\n' 'main:2.1' '%2'; printf '%s\t%s\n' 'remote:3.2' '%3')"
expected_focus="$(printf '%s\n' 'tmux:switch-client:remote' 'tmux:select-window:remote:3' 'tmux:select-pane:%3')"

if [ "$(sed -n '1,2p' "$TEST_GUM_INPUT")" != "$expected_choices" ]; then
  printf '%s\n' 'expected Gum to receive only active Codex panes' >&2
  exit 1
fi

if [ "$(sed -n '1,3p' "$TEST_LOG")" != "$expected_focus" ] || [ -n "$(sed -n '4p' "$TEST_LOG")" ]; then
  printf '%s\n' 'expected the selected pane to receive focus without clearing its waiting state' >&2
  exit 1
fi

if ! rg -q 'bind-key -n C-S-s .*--choose-active' "$repo_root/tmux/tmux.conf"; then
  printf '%s\n' 'expected Ctrl+Shift+S to open the active Codex picker' >&2
  exit 1
fi

if ! rg -qx 'map ctrl\+shift\+s' "$repo_root/kitty/kitty.conf"; then
  printf '%s\n' 'expected Kitty to pass Ctrl+Shift+S through to tmux' >&2
  exit 1
fi
