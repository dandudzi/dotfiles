# Codex Config Guidelines

## Purpose

This folder is the canonical managed configuration area for Codex on this machine. Preserve the existing folder layout so live Codex paths can remain symlinks into one source of configuration.

## Organization

- `global.md`: global instructions, linked from `~/.codex/AGENTS.md`.
- `skills/<name>/SKILL.md`: skills, exposed through `~/.agents/skills`.
- `rules/default.rules`: execution policy, linked from `~/.codex/rules/default.rules`.

No custom agent definitions are maintained here. Keep reusable workflows in skills, including `linear-operator` for authorized Linear writes. Keep credentials, OAuth state, caches, logs, histories, and runtime state outside this folder.

## Chezmoi

This directory lives under the rendered `~/.config` tree. Use the `persist-config-with-chezmoi` skill for exact-path persistence. Verify source cleanliness before operations that may auto-commit or auto-push. Never capture secrets or runtime state. Native tool files outside `~/.config` require explicit authorization for their exact path.
