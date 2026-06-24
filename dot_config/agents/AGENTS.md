# Shared Agent Config Guidelines

## Purpose
This folder is the canonical shared configuration area for AI coding agents used on this machine, including Codex, Claude Code, and OpenCode. Store reusable instructions, portable Agent Skills, shared prompt assets, and adapter source files here when they are meant to be reused across more than one agent tool.

## Organization
Keep portable content in neutral locations first, then link or adapt it into tool-specific paths. Prefer shared `SKILL.md`-based skills and plain Markdown instruction files for cross-tool behavior. Keep tool-specific wrappers, settings, permissions, model choices, credentials, caches, logs, and session state out of this shared folder unless they are intentionally safe to version and reuse.

## Chezmoi
This directory lives under the rendered `~/.config` tree, so new files added here must also be captured in the upstream `chezmoi` source. Use `chezmoi add ~/.config/agents/<path>` after live edits, or edit the corresponding source path directly when the mapping is clear.
