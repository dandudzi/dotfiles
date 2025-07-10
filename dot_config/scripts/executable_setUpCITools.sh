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
  export SSH_AUTH_SOCK=/Users/daniel/.bitwarden-ssh-agent.sock

  touch "$IS_CI_SET_UP_RUN"
fi
