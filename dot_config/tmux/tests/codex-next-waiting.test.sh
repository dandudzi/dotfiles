#!/bin/sh

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../scripts" && pwd)
test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT

mkdir "$test_dir/bin"

export TEST_LOG="$test_dir/log"
export PATH="$test_dir/bin:$PATH"

printf '%s\n' '#!/bin/sh' 'case "$1" in' '  list-panes) exit 0 ;;' '  display-message) printf "%s\\n" "$2" >> "$TEST_LOG" ;;' 'esac' > "$test_dir/bin/tmux"
printf '%s\n' '#!/bin/sh' 'printf "%s\\n" "gum invoked" >> "$TEST_LOG"' > "$test_dir/bin/gum"
chmod +x "$test_dir/bin/tmux" "$test_dir/bin/gum"

sh "$script_dir/codex-next-waiting.sh" --choose

if [ "$(sed -n '1p' "$TEST_LOG")" != 'No Codex pane needs attention' ] || [ -n "$(sed -n '2p' "$TEST_LOG")" ]; then
  printf '%s\n' 'expected the empty-state message' >&2
  exit 1
fi
