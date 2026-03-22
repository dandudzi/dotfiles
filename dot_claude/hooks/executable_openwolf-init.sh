#!/usr/bin/env bash
# SessionStart hook: run "openwolf init" if this is a git repo and .wolf/ doesn't exist

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if [ ! -d ".wolf" ]; then
    openwolf init 2>&1
  fi
fi
