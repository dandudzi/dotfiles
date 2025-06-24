#🍻 Update brew once per day
UPDATE_FILE="$HOME/.last_update"
# Run only if last update was over 24 hours ago
if [ ! -f "$UPDATE_FILE" ] || [ $(date +%s) -gt $(($(cat "$UPDATE_FILE") + 86400)) ]; then
  echo "Updating chezmoi"
  chezmoi update

  echo "Updating Homebrew... 🍺"
  brew update && brew upgrade && brew cleanup

  echo "Updating homebrew bundle file"
  brew bundle dump --file="~/.config/brewfile/Brewfile" --force
  dota ~/.config/brewfile/Brewfile

  echo " Updating tpm plugins"
  ~/.config/tmux/plugins/tpm/bin/update_plugins all

  echo "🔄 Updating chezmoi external repos and dependencies"
  chezmoi --refresh-externals apply

  date +%s >"$UPDATE_FILE" # Save current timestamp
fi
