#!/bin/bash

echo "🔧 Installing SbarLua (Lua 5.5 + sketchybar module)..."

INSTALL_DIR="$HOME/.local/share/sketchybar_lua"

if [ -f "$INSTALL_DIR/sketchybar.so" ] && [ -f "$INSTALL_DIR/lua" ]; then
  echo "✅ SbarLua is already installed, skipping."
  exit 0
fi

TMPDIR_SBAR=$(mktemp -d)
git clone https://github.com/FelixKratz/SbarLua.git "$TMPDIR_SBAR" \
  && cd "$TMPDIR_SBAR" \
  && make install \
  && cp lua-5.5.0/src/lua "$INSTALL_DIR/lua" \
  && chmod +x "$INSTALL_DIR/lua" \
  && rm -rf "$TMPDIR_SBAR"

echo "✅ SbarLua installed!"
