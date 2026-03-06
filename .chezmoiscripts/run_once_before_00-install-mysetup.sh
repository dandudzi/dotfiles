#!/bin/bash
set -euo pipefail

check_brew() {
  if command -v brew &>/dev/null; then
    echo "✅ Homebrew is already installed!"
    return 0
  else
    echo "❌ Homebrew is NOT installed."
    return 1
  fi
}

install_if_missing() {
  local check_cmd="$1"
  local install_cmd="$2"

  # Run the check command
  if eval "$check_cmd" &>/dev/null; then
    echo "✅ Program is already installed!"
  else
    echo "🚀 Program not found. Installing now..."
    eval "$install_cmd"
  fi
}

echo "🚀 Starting setting up..."

if ! check_brew; then
  echo "🍻 Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  echo "Applying Homebrew environment settings..."
  eval "$(/opt/homebrew/bin/brew shellenv)"

  # Check again after installation
  if ! check_brew; then
    echo "🛑 Homebrew installation failed!"
    exit 1
  fi

  echo "Setup complete! Homebrew is now properly configured."
fi

echo "🔄 Updating Homebrew..."
brew update

echo "📟 Installing zsh..."
install_if_missing "zsh --version" "brew install zsh"

echo "📟 Installing Oh my zsh..."
if [ ! -d "$HOME/.oh-my-zsh" ]; then
  echo "📟 Oh My Zsh not found, installing..."
  export RUNZSH=no      #skipping running zsh after installation"
  export KEEP_ZSHRC=yes #do not change zsh file
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
else
  echo "✅ Oh My Zsh is already installed, skipping installation."
fi

echo "🚀 Setting up spaceship theme symlink..."
export ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
# Spaceship repo is managed by .chezmoiexternal.toml — only create symlink here
SPACESHIP_DIR="$ZSH_CUSTOM/themes/spaceship-prompt"
SPACESHIP_LINK="$ZSH_CUSTOM/themes/spaceship.zsh-theme"
if [ ! -L "$SPACESHIP_LINK" ] && [ -d "$SPACESHIP_DIR" ]; then
  ln -s "$SPACESHIP_DIR/spaceship.zsh-theme" "$SPACESHIP_LINK"
  echo "✅ Spaceship symlink created."
else
  echo "✅ Spaceship symlink already exists or theme not yet cloned, skipping."
fi

# Install fzf if not already installed
if ! brew list fzf >/dev/null 2>&1; then
  echo "🔎 Installing fzf..."
  brew install fzf

  echo "🔎 Running fzf install script..."
  "$(brew --prefix)/opt/fzf/install" --key-bindings --completion --no-update-rc
  echo "✅ fzf setup complete!"
else
  echo "✅ fzf is already installed."
fi

echo "🔄 Updating Homebrew..."
brew update

echo "📦 Installing CLI tools..."
trap 'echo "An error occurred, while installing brew dependencies";' ERR
brew bundle --file="~/.local/share/chezmoi/dot_config/brewfile/Brewfile"
trap - ERR

echo "✅ Setup autocompletion for mise"
mise completion zsh

echo "▦ setting up ssh to include my config"
if ! grep -qF "Include ~/.config/ssh/ssh_config" ~/.ssh/config 2>/dev/null; then
  echo "Include ~/.config/ssh/ssh_config" >> ~/.ssh/config
fi
mkdir -p ~/.ssh/control
chmod 700 ~/.ssh/control

echo "🧹 Cleaning up..."
brew cleanup
