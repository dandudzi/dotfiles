#🍻 Update brew once per day
BREW_UPDATE_FILE="$HOME/.brew_last_update"
# Run only if last update was over 24 hours ago
if [ ! -f "$BREW_UPDATE_FILE" ] || [ $(date +%s) -gt $(($(cat "$BREW_UPDATE_FILE") + 86400)) ]; then
  echo "Updating Homebrew... 🍺"
  brew update && brew upgrade && brew cleanup
  date +%s >"$BREW_UPDATE_FILE" # Save current timestamp
fi
