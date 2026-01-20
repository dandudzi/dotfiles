#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec /usr/bin/python3 "$DIR/game_automate.py" "$@"
