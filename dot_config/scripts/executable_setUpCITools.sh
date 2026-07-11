#!/bin/bash

_setup_ci_tools() {
  local sentinel="$HOME/.isCISetUpRun"
  local lock_dir="$HOME/.isCISetUpRun.lock"
  local sketchybar_dir="$HOME/.config/sketchybar"
  local brew_shellenv
  local chezmoi_source
  local git_email
  local lua_version

  if [ -f "$sentinel" ]; then
    return 0
  fi

  if ! mkdir "$lock_dir" 2>/dev/null; then
    echo "⚠️ First-shell setup is already running in another shell." >&2
    return 1
  fi
  trap 'rmdir "$HOME/.isCISetUpRun.lock" 2>/dev/null || true' EXIT

  echo "📲 Checking Xcode Command Line Tools"
  if ! xcode-select -p >/dev/null 2>&1; then
    echo "📲 Requesting Xcode Command Line Tools installation"
    xcode-select --install || true
    echo "❌ Xcode Command Line Tools are required. Finish installing them and open a new shell." >&2
    return 1
  fi

  echo "Applying Homebrew environment settings..."
  if [ ! -x /opt/homebrew/bin/brew ]; then
    echo "❌ Homebrew is required at /opt/homebrew/bin/brew." >&2
    return 1
  fi
  brew_shellenv="$(/opt/homebrew/bin/brew shellenv)" || return 1
  eval "$brew_shellenv" || return 1

  echo "⏳ Rebuilding bat cache"
  bat cache --build || return 1

  echo "📊 Setting up SketchyBar"
  (
    cd "$sketchybar_dir" || exit 1
    mise trust || exit 1
    mise install || exit 1

    lua_version="$(lua -v 2>&1)" || exit 1
    if printf '%s\n' "$lua_version" | grep -q "Lua 5.1"; then
      echo "❌ SketchyBar requires a Lua version newer than 5.1; found: $lua_version" >&2
      exit 1
    fi

    mkdir -p "$HOME/Library/Fonts" || exit 1
    curl -fL https://github.com/kvndrsslr/sketchybar-app-font/releases/download/v2.0.28/sketchybar-app-font.ttf \
      -o "$HOME/Library/Fonts/sketchybar-app-font.ttf" || exit 1
    sketchybar --load-font "Symbols Nerd Font" || exit 1
    sketchybar --load-font "Symbols Nerd Font Mono" || exit 1
    sketchybar --load-font "CommitMono" || exit 1
    brew services restart sketchybar || exit 1
  ) || return 1

  echo "🐁 Installing mise tools"
  (cd "$HOME" && mise install) || return 1

  echo "🔒 Checking Bitwarden SSH agent"
  export SSH_AUTH_SOCK="$HOME/.bitwarden-ssh-agent.sock"
  if [ ! -S "$SSH_AUTH_SOCK" ]; then
    echo "❌ Bitwarden SSH agent is required at $SSH_AUTH_SOCK." >&2
    return 1
  fi

  echo "🖥️ Building programs for scripts"
  make -C "$HOME/.config/scripts/hidapitester" || return 1
  make -C "$HOME/.config/scripts/m1ddc" || return 1

  echo "▦ Configuring the chezmoi source Git identity"
  chezmoi_source="$(chezmoi source-path)" || return 1
  git -C "$chezmoi_source" rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 1
  git -C "$chezmoi_source" config user.signingkey \
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICwFmLNYerRzGP9de3D3jblBa6orRzAlQcMUbANqoLK5" || return 1
  git_email="$(git config --global user.email)" || return 1
  if [ -z "$git_email" ]; then
    echo "Global Git email is not configured." >&2
    return 1
  fi
  git -C "$chezmoi_source" config user.email "$git_email" || return 1

  touch "$sentinel" || return 1
  echo "✅ First-shell setup completed successfully"
}

if ! (
  _setup_ci_tools
); then
  echo "⚠️ First-shell setup is incomplete; $HOME/.isCISetUpRun was not created." >&2
fi

unset -f _setup_ci_tools
