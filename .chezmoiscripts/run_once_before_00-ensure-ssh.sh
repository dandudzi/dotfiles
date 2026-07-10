#!/bin/bash
set -euo pipefail

SSH_DIR="$HOME/.ssh"
SSH_CONFIG="$SSH_DIR/config"

umask 077

if [[ -L "$SSH_DIR" && ! -e "$SSH_DIR" ]]; then
  echo "❌ $SSH_DIR is a broken symlink." >&2
  exit 1
fi

if [[ -e "$SSH_DIR" && ! -d "$SSH_DIR" ]]; then
  echo "❌ $SSH_DIR exists but is not a directory." >&2
  exit 1
fi

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [[ -L "$SSH_CONFIG" ]]; then
  echo "❌ $SSH_CONFIG is a symlink; refusing to change its target." >&2
  exit 1
fi

if [[ -e "$SSH_CONFIG" && ! -f "$SSH_CONFIG" ]]; then
  echo "❌ $SSH_CONFIG exists but is not a regular file." >&2
  exit 1
fi

touch "$SSH_CONFIG"
chmod 600 "$SSH_CONFIG"
