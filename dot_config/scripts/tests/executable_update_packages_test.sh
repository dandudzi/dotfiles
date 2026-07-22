#!/bin/sh

set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
UPDATE_SCRIPT="$SCRIPT_DIR/../update_packages.sh"
INIT_SCRIPT="$SCRIPT_DIR/../../zsh/init.zsh"
TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/update-packages-test.XXXXXX") || exit 1
FAILURES=0

cleanup() {
  rm -rf "$TEST_ROOT"
}
trap cleanup EXIT HUP INT TERM

fail() {
  echo "not ok - $1" >&2
  FAILURES=$((FAILURES + 1))
}

pass() {
  echo "ok - $1"
}

assert_eq() {
  expected=$1
  actual=$2
  message=$3
  if [ "$expected" = "$actual" ]; then
    pass "$message"
  else
    fail "$message (expected '$expected', got '$actual')"
  fi
}

assert_nonempty() {
  value=$1
  message=$2
  if [ -n "$value" ]; then
    pass "$message"
  else
    fail "$message"
  fi
}

new_fixture() {
  name=$1
  FIXTURE="$TEST_ROOT/$name"
  HOME="$FIXTURE/home"
  BIN="$FIXTURE/bin"
  LOG="$FIXTURE/commands.log"
  OUTPUT="$FIXTURE/output.log"
  mkdir -p "$HOME/.oh-my-zsh/tools" "$HOME/.config/tmux/plugins/tpm/bin" "$BIN"
  : >"$LOG"

  cat >"$BIN/fake-command" <<'EOF'
#!/bin/sh
echo "$(basename "$0") $*" >>"$TEST_COMMAND_LOG"
if [ "${FAIL_COMMAND:-}" = "$(basename "$0")" ]; then
  exit 23
fi
if [ "${HANG_COMMAND:-}" = "$(basename "$0")" ]; then
  sleep 10
fi
if [ "${PROMPT_COMMAND:-}" = "$(basename "$0")" ]; then
  printf 'fake command needs input: '
  IFS= read -r prompt_answer || exit 24
  [ "$prompt_answer" = "continue" ] || exit 25
fi
exit 0
EOF
  chmod +x "$BIN/fake-command"

  for command_name in brew chezmoi mise git; do
    ln -s fake-command "$BIN/$command_name"
  done
  ln -s "$BIN/fake-command" "$HOME/.oh-my-zsh/tools/upgrade.sh"
  ln -s "$BIN/fake-command" "$HOME/.config/tmux/plugins/tpm/bin/update_plugins"
}

run_interactive_update() {
  TEST_COMMAND_LOG="$LOG" \
    HOME="$HOME" \
    ZSH="$HOME/.oh-my-zsh" \
    PATH="$BIN:/opt/homebrew/bin:/usr/bin:/bin" \
    UPDATE_TIMEOUT=0.5s \
    UPDATE_SCRIPT_PATH="$UPDATE_SCRIPT" \
    PROMPT_COMMAND=chezmoi \
    expect -c '
      set timeout 3
      set update_script $env(UPDATE_SCRIPT_PATH)
      spawn -noecho $update_script
      expect "Run them now?"
      send "y\r"
      expect "fake command needs input:"
      send "continue\r"
      expect eof
      set result [wait]
      exit [lindex $result 3]
    ' >"$OUTPUT" 2>&1
}

run_update() {
  input=$1
  TEST_COMMAND_LOG="$LOG" \
    HOME="$HOME" \
    ZSH="$HOME/.oh-my-zsh" \
    PATH="$BIN:/opt/homebrew/bin:/usr/bin:/bin" \
    UPDATE_TIMEOUT="${UPDATE_TIMEOUT:-5m}" \
    FAIL_COMMAND="${FAIL_COMMAND:-}" \
    HANG_COMMAND="${HANG_COMMAND:-}" \
    sh -c 'printf "%b" "$1" | "$2"' sh "$input" "$UPDATE_SCRIPT" >"$OUTPUT" 2>&1
}

new_fixture recent
recent_timestamp=$(date +%s)
echo "$recent_timestamp" >"$HOME/.last_update"
if run_update 'y\n'; then
  assert_eq "" "$(cat "$LOG")" "recent checks do not run updates"
  assert_eq "$recent_timestamp" "$(cat "$HOME/.last_update")" "recent checks preserve the timer"
else
  fail "recent checks exit successfully"
fi

new_fixture decline
echo 0 >"$HOME/.last_update"
if run_update 'n\n'; then
  assert_eq "" "$(cat "$LOG")" "declining does not run updates"
  declined_timestamp=$(cat "$HOME/.last_update")
  assert_nonempty "$declined_timestamp" "declining refreshes the timer"
  if [ "$declined_timestamp" -gt 0 ] 2>/dev/null; then
    pass "declining writes a current-style timestamp"
  else
    fail "declining writes a current-style timestamp"
  fi
else
  fail "declining exits successfully"
fi

new_fixture accept
echo 0 >"$HOME/.last_update"
if run_update 'y\n'; then
  assert_nonempty "$(cat "$LOG")" "accepting runs update commands"
  accepted_timestamp=$(cat "$HOME/.last_update")
  if [ "$accepted_timestamp" -gt 0 ] 2>/dev/null; then
    pass "successful updates refresh the timer"
  else
    fail "successful updates refresh the timer"
  fi
else
  fail "successful updates exit successfully"
fi

new_fixture default-decline
echo 0 >"$HOME/.last_update"
if run_update '\n'; then
  assert_eq "" "$(cat "$LOG")" "pressing Enter uses the default no answer"
  default_decline_timestamp=$(cat "$HOME/.last_update")
  if [ "$default_decline_timestamp" -gt 0 ] 2>/dev/null; then
    pass "the default no answer refreshes the timer"
  else
    fail "the default no answer refreshes the timer"
  fi
else
  fail "the default no answer exits successfully"
fi

new_fixture failure
echo 0 >"$HOME/.last_update"
FAIL_COMMAND=brew
if run_update 'y\n'; then
  fail "failed updates return a failure status"
else
  pass "failed updates return a failure status"
fi
assert_eq 0 "$(cat "$HOME/.last_update")" "failed updates leave the timer unchanged"
unset FAIL_COMMAND

new_fixture interactive-child
echo 0 >"$HOME/.last_update"
if run_interactive_update; then
  pass "interactive update commands can read from the terminal"
else
  fail "interactive update commands can read from the terminal"
  sed 's/^/# interactive output: /' "$OUTPUT" >&2
fi

new_fixture timeout
echo 0 >"$HOME/.last_update"
HANG_COMMAND=brew
UPDATE_TIMEOUT=0.2s
start_time=$(date +%s)
if run_update 'y\n'; then
  fail "timed-out updates return a failure status"
else
  pass "timed-out updates return a failure status"
fi
elapsed=$(( $(date +%s) - start_time ))
if [ "$elapsed" -lt 3 ]; then
  pass "the timeout stops a hanging update promptly"
else
  fail "the timeout stops a hanging update promptly"
fi
assert_eq 0 "$(cat "$HOME/.last_update")" "timed-out updates leave the timer unchanged"

new_fixture startup-isolation
mkdir -p "$HOME/.config/scripts"
printf '%s\n' '#!/bin/sh' 'exit 42' >"$HOME/.config/scripts/update_packages.sh"
chmod +x "$HOME/.config/scripts/update_packages.sh"
touch "$HOME/.isCISetUpRun"
startup_block=$(sed -n '/# Skip updates until/,/^fi$/p' "$INIT_SCRIPT")
if HOME="$HOME" CONFIG_HOME="$HOME/.config" zsh -c "$startup_block
print startup-continued" >"$OUTPUT" 2>&1; then
  if grep -q '^startup-continued$' "$OUTPUT"; then
    pass "a failed updater does not abort zsh startup"
  else
    fail "a failed updater does not abort zsh startup"
  fi
else
  fail "the zsh update wrapper exits successfully after updater failure"
fi

if [ "$FAILURES" -ne 0 ]; then
  echo "$FAILURES test(s) failed" >&2
  exit 1
fi

echo "All update package tests passed"
