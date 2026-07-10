#!/bin/sh

UPDATE_FILE="$HOME/.last_update"
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

# Run only if the last update was over 24 hours ago.
if [ ! -f "$UPDATE_FILE" ] || [ "$(date +%s)" -gt "$(( $(cat "$UPDATE_FILE") + 86400 ))" ]; then
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

  if [ "$failed" -eq 0 ]; then
    date +%s >"$UPDATE_FILE"
  else
    echo "One or more update steps failed; leaving $UPDATE_FILE unchanged so the update is retried next time." >&2
  fi
fi
