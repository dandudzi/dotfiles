#!/bin/bash
#🍻 Update brew once per day
IS_CI_SET_UP_RUN="$HOME/.isCISetUpRun"
# Run only if last update was over 24 hours ago
if [ ! -f "$IS_CI_SET_UP_RUN" ]; then

  echo "📲 installing xcode-select tools"
  xcode-select --install

  echo "Applying Homebrew environment settings..."
  eval "$(/opt/homebrew/bin/brew shellenv)"

  echo "⏳rebuilt bat cache"
  bat cache --build

  echo "📊 setup sketchybar"
  curl -L https://github.com/kvndrsslr/sketchybar-app-font/releases/download/v2.0.28/sketchybar-app-font.ttf -o $HOME/Library/Fonts/sketchybar-app-font.ttf
  (git clone https://github.com/FelixKratz/SbarLua.git /tmp/SbarLua && cd /tmp/SbarLua/ && make install && rm -rf /tmp/SbarLua/)

  sketchybar --load-font "Symbols Nerd Font"
  sketchybar --load-font "Symbols Nerd Font Mono"
  sketchybar --load-font "CommitMono"

  brew services restart sketchybar

  echo "🐁 mise installation of tools"
  mise install

  echo "🔒make bitwarden as ssh service"
  export SSH_AUTH_SOCK="$HOME/.bitwarden-ssh-agent.sock"

  echo "🖥️build programs for scripts"
  make -C ~/.config/scripts/hidapitester
  make -C ~/.config/scripts/m1ddc

  echo "▦ add dedicated chezmoi ssh sign key"
  chezmoi cd
  git config user.signingkey "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICwFmLNYerRzGP9de3D3jblBa6orRzAlQcMUbANqoLK5"
  cd ~

  touch "$IS_CI_SET_UP_RUN"
fi
