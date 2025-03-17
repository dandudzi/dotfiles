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

# Default values for the flags
skipInitial=false
skipBrew=false
skipMac=false
skipAppStore=false
while [[ "$#" -gt 0 ]]; do
  case "$1" in
  --skipInitial)
    skipInitial=true
    shift
    ;;
  --skipBrew)
    skipBrew=true
    shift
    ;;
  --skipMac)
    skipMac=true
    shift
    ;;
  --skipAppStore)
    skipAppStore=true
    shift
    ;;
  *)
    echo "Unknown option: $1"
    exit 1
    ;;
  esac
done

echo "skipInitial: $skipInitial"
echo "skipBrew: $skipBrew"
echo "skipMac: $skipMac"
echo "skipAppStore: $skipAppStore"

echo "🚀 Starting seting up..."

if $skipInitial; then
  echo "⏩ Skipping initial setup..."
else
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
fi

if $skipBrew; then
  echo "⏩ Skipping Homebrew setup..."
else
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

  # Install fzf-tab plugin
  FZF_TAB_DIR="$HOME/.oh-my-zsh/custom/plugins/fzf-tab"
  if [ ! -d "$FZF_TAB_DIR" ]; then
    echo "✅ Installing fzf-tab..."
    git clone https://github.com/Aloxaf/fzf-tab "$FZF_TAB_DIR"
  else
    echo "✅ fzf-tab is already installed. Updating..."
    cd "$FZF_TAB_DIR" && git pull
  fi

  echo "🔄 Updating Homebrew..."
  brew update
  # List of CLI tools to install
  BREW_PACKAGES=(
    htop
    wget
    tmux
    mise
    tldr
    zsh-syntax-highlighting
    bat
    git-delta
    git-open
    neovim
    eza
    zsh-autosuggestions
    pstree
    lnav
    sqlite
    stats
    jq
    ripgrep
    nmap
    coreutils
    fd
    gpg
    pinentry-mac
    zoxide
    font-jetbrains-mono-nerd-font
    onefetch
  )

  # List of GUI applications (casks)
  CASK_PACKAGES=(
    google-chrome
    visual-studio-code
    spotify
    intellij-idea-ce
    sublime-text
    docker
    steam
    skype
    clipy
    rectangle
    discord
    bitwarden
    flameshot
    discord
    devtoys
    caffeine
  )

  echo "📦 Installing CLI tools..."
  brew install "${BREW_PACKAGES[@]}"

  echo "🖥️ Installing GUI applications..."
  brew install --cask "${CASK_PACKAGES[@]}"
  brew install --cask --no-quarantine stretchly

  echo "✅ Setup autocomplition for mise"
  mise completion zsh

  echo "✅ installing yazi"
  brew install yazi --HEAD

  echo "✅ installing TPM for tmux"
  TPM_DIR="$HOME/.tmux/plugins/tpm"
  # todo change this path

  if [ ! -d "$TPM_DIR" ]; then
    echo "TPM not found. Cloning..."
    git clone https://github.com/tmux-plugins/tpm "$TPM_DIR"
    tmux source ~/.tmux.conf
  else
    echo "TPM already exists at $TPM_DIR."
  fi

  echo "✅ Setup theme for various tools"
  mkdir -p "$(bat --config-dir)/themes"
  cp ~/.themes/bat/* $(bat --config-dir)/themes
  bat cache --build

  ya pack -a yazi-rs/flavors:catppuccin-macchiato
  mkdir ~/.config/yazi/
  cp ~/.themes/yazi/* ~/.config/yazi/

  echo "🧹 Cleaning up..."
  brew cleanup
fi

if $skipMac; then
  echo "⏩ Skipping macOS-specific setup..."
else
  echo "🎧 Start setting up MacBook"
  ~/.setUpMac.sh
fi

if $skipAppStore; then
  echo "⏩ Skipping appstore setup..."
else
  echo "🎧 Start installing AppStoreApps"
  echo "🏪 Install via brew required dependencies"
  brew install mas
  echo "📖 Install Kindle"
  mas install 302584613
  echo "📝 Install Goodnotes"
  mas install 1444383602
  echo "📖 Install HP smart"
  mas install 1474276998
  echo "📖 Install MS Excel"
  mas install 462058435
  echo "📖 Install MS Word"
  mas install 462054704
fi
echo "✅ All programs installed successfully!"
echo "⚠️ Login to new shell terminal to apply all changes"
