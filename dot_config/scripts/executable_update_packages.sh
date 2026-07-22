#!/bin/sh

UPDATE_FILE="${UPDATE_FILE:-$HOME/.last_update}"
UPDATE_TIMEOUT="${UPDATE_TIMEOUT:-5m}"
TMUX_CATPPUCCIN_PLUGIN_PATH="$HOME/.config/tmux/plugins/tmux"

run_step() {
  label="$1"
  shift

  echo "$label"
  if ! "$@"; then
    echo "Failed: $label" >&2
    return 1
  fi
}

cleanup_tmux_plugin_tags() {
  plugin_path="$1"
  shift

  [ -d "$plugin_path/.git" ] || return 0

  for tag_name in "$@"; do
    if git -C "$plugin_path" rev-parse -q --verify "refs/tags/$tag_name" >/dev/null 2>&1; then
      git -C "$plugin_path" tag -d "$tag_name" >/dev/null 2>&1 || return 1
    fi
  done
}

perform_updates() {
  failed=0

  run_step "Updating Oh My Zsh" "$ZSH/tools/upgrade.sh" || failed=1

  if ! run_step "Updating chezmoi dependencies" env HOMEBREW_DOTFILES_SKIP_MAS=1 chezmoi update; then
    echo "chezmoi uses git@github.com:dandudzi/dotfiles.git, so this step needs valid GitHub SSH access." >&2
    failed=1
  fi

  run_step "Updating Homebrew... 🍺" brew update || failed=1
  run_step "Upgrading Homebrew formulae" brew upgrade --formula || failed=1
  run_step "Cleaning up Homebrew" brew cleanup || failed=1
  run_step "Updating Mise... 🐁" mise upgrade || failed=1
  run_step "Cleaning mutable catppuccin/tmux tags" cleanup_tmux_plugin_tags "$TMUX_CATPPUCCIN_PLUGIN_PATH" latest v2 || failed=1
  run_step " Updating tpm plugins" "$HOME/.config/tmux/plugins/tpm/bin/update_plugins" all || failed=1

  if [ "$failed" -ne 0 ]; then
    echo "One or more update steps failed; leaving $UPDATE_FILE unchanged so the update is retried next time." >&2
    return 1
  fi
}

# Keep the interactive decision outside timeout so the worker can run in its own
# process group and timeout can stop its child processes as well as the script.
if [ "${1:-}" = "--perform-update" ]; then
  perform_updates
  exit $?
fi

now=$(date +%s) || {
  echo "Could not read the current time; skipping package updates." >&2
  exit 1
}
last_update=0
if [ -r "$UPDATE_FILE" ]; then
  IFS= read -r last_update <"$UPDATE_FILE" || last_update=0
  case "$last_update" in
    ''|*[!0-9]*) last_update=0 ;;
  esac
fi

# Run only if the last update decision was over 24 hours ago.
if [ "$now" -le "$((last_update + 86400))" ]; then
  exit 0
fi

printf "Package updates are due. Run them now? [y/N] "
IFS= read -r answer || answer=
case "$answer" in
  y|Y|yes|YES) ;;
  *)
    if ! printf '%s\n' "$now" >"$UPDATE_FILE"; then
      echo "Could not update $UPDATE_FILE." >&2
      exit 1
    fi
    echo "Package updates skipped for 24 hours."
    exit 0
    ;;
esac

if timeout --kill-after=5s "$UPDATE_TIMEOUT" "$0" --perform-update; then
  if ! date +%s >"$UPDATE_FILE"; then
    echo "Updates completed, but $UPDATE_FILE could not be refreshed." >&2
    exit 1
  fi
  exit 0
else
  update_status=$?
  case "$update_status" in
    124|137)
      echo "Package updates exceeded $UPDATE_TIMEOUT; continuing shell startup." >&2
      ;;
    *)
      echo "Package updates failed with status $update_status; continuing shell startup." >&2
      ;;
  esac
  exit "$update_status"
fi
