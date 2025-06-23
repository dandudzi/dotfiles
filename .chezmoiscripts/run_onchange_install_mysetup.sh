#!/bin/bash

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

echo "🚀 Starting seting up..."

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
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
else
  echo "✅ Oh My Zsh is already installed, skipping installation."
fi

echo "📟 Making our zsh config as deafult..."
[ -f "$HOME/.zshrc.pre-oh-my-zsh" ] && mv "$HOME/.zshrc.pre-oh-my-zsh" "$HOME/.zshrc"

echo "🚀 Installing spaceship plugin for ohmyzsh..."
export ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
# Define the theme path
SPACESHIP_DIR="$ZSH_CUSTOM/themes/spaceship-prompt"
SPACESHIP_LINK="$ZSH_CUSTOM/themes/spaceship.zsh-theme"
# Check if the repository already exists before cloning
if [ ! -d "$SPACESHIP_DIR/.git" ]; then
  echo "🚀 Cloning Spaceship theme..."
  git clone https://github.com/spaceship-prompt/spaceship-prompt.git "$SPACESHIP_DIR" --depth=1
else
  echo "✅ Spaceship theme already exists, skipping clone."
fi

# Ensure the symlink exists
if [ ! -L "$SPACESHIP_LINK" ]; then
  echo "🚀 Creating symlink for Spaceship theme..."
  ln -s "$SPACESHIP_DIR/spaceship.zsh-theme" "$SPACESHIP_LINK"
else
  echo "✅ Symlink for Spaceship theme already exists, skipping."
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

echo "✅ Setup autocomplition for mise"
mise completion zsh

echo "🧹 Cleaning up..."
brew cleanup
