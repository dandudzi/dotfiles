#🍻 Update brew once per day
BREW_UPDATE_FILE="$HOME/.brew_last_update"
# Run only if last update was over 24 hours ago
if [ ! -f "$BREW_UPDATE_FILE" ] || [ $(date +%s) -gt $(($(cat "$BREW_UPDATE_FILE") + 86400)) ]; then
    echo "Updating Homebrew... 🍺"
    brew update && brew upgrade && brew cleanup
    date +%s > "$BREW_UPDATE_FILE"  # Save current timestamp
fi

# eneale brew file to be regenerated when brew install or uninstall happened
if [ -f $(brew --prefix)/etc/brew-wrap ];then
  source $(brew --prefix)/etc/brew-wrap
fi
