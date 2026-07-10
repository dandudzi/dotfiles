#!/bin/bash
set -euo pipefail

echo "🔧 Installing SbarLua (Lua 5.5 + sketchybar module)..."

INSTALL_DIR="$HOME/.local/share/sketchybar_lua"

if [ -s "$INSTALL_DIR/sketchybar.so" ] && [ -x "$INSTALL_DIR/lua" ]; then
  echo "✅ SbarLua is already installed, skipping."
  exit 0
fi

mkdir -p "$INSTALL_DIR"

TMPDIR_SBAR=$(mktemp -d)
trap 'rm -rf "$TMPDIR_SBAR"' EXIT

git clone https://github.com/FelixKratz/SbarLua.git "$TMPDIR_SBAR"
cd "$TMPDIR_SBAR"
make install
cp lua-5.5.0/src/lua "$INSTALL_DIR/lua"
chmod +x "$INSTALL_DIR/lua"

if [ ! -s "$INSTALL_DIR/sketchybar.so" ] || [ ! -x "$INSTALL_DIR/lua" ]; then
  echo "❌ SbarLua installation did not produce the expected artifacts." >&2
  exit 1
fi

echo "✅ SbarLua installed!"
