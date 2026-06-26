# Repository Guidelines

## Project Structure & Module Organization
This repository is a config placement for one machine, managed as part of a broader dotfiles setup through `chezmoi`. It is organized by tool rather than by application: `nvim` contains editor config, `sketchybar` contains bar items and helpers, `tmux` contains terminal multiplexer config plus bundled plugins, and `scripts` contains standalone utilities with their own local docs or build files. Treat bundled plugin and dependency directories as vendored unless you are intentionally syncing upstream code.

## Shared AI Agent Configuration
The `agents` directory is the canonical shared configuration area for Codex, Claude Code, and OpenCode. Use it for portable global instructions, Agent Skills, Claude/OpenCode-compatible agent prompts, shared hook scripts, and MCP intent notes. The live global instruction files and shared skill or agent directories may be symlinks into this folder.

Do not assume tool-specific active settings are shared just because the shared folder exists. Before changing MCP servers, hooks, permissions, models, or provider settings, inspect the current tool-specific config files and preserve existing entries. Keep secrets, OAuth state, credentials, caches, logs, histories, and machine-local runtime state out of `agents`.

MCP configs are not one universal file across these tools. Keep reusable MCP names, commands, URLs, and non-secret notes in `agents/mcp.md`, then update each active tool wrapper in its native schema when requested. Do not claim MCP servers are shared unless Codex, Claude Code, and OpenCode have each been checked or configured explicitly.

## Commit & Pull Request Guidelines
Changes here are meant to become part of the `chezmoi`-managed dotfiles set. Before adding or moving config files in this live `~/.config` tree, locate the `chezmoi` source with `chezmoi source-path` or use `chezmoi add` after the live edit so the change is not a machine-only leftover. Prefer editing the `chezmoi` source directly when the mapping is clear, then apply or verify the rendered target. Keep related changes grouped by tool, and describe them by config area, for example `nvim: tweak LSP defaults` or `tmux: adjust session picker bindings`. For visual changes, record what was reloaded or checked so the corresponding `chezmoi` update is easy to review and apply.
