# Repository Guidelines

## Project Structure & Module Organization
This repository is a config placement for one machine, managed as part of a broader dotfiles setup through `chezmoi`. It is organized by tool rather than by application: `nvim` contains editor config, `sketchybar` contains bar items and helpers, `tmux` contains terminal multiplexer config plus bundled plugins, and `scripts` contains standalone utilities with their own local docs or build files. Treat bundled plugin and dependency directories as vendored unless you are intentionally syncing upstream code.

## Shared AI Agent Configuration
The `agents` directory is the canonical shared configuration area for Codex, Claude Code, and OpenCode. Use it for portable global instructions, Agent Skills, Claude/OpenCode-compatible agent prompts, shared hook scripts, and MCP intent notes. The live global instruction files and shared skill or agent directories may be symlinks into this folder.

Do not assume tool-specific active settings are shared just because the shared folder exists. Before changing MCP servers, hooks, permissions, models, or provider settings, inspect the current tool-specific config files and preserve existing entries. Keep secrets, OAuth state, credentials, caches, logs, histories, and machine-local runtime state out of `agents`.

MCP configs are not one universal file across these tools. Keep reusable MCP names, commands, URLs, and non-secret notes in `agents/mcp.md`, then update each active tool wrapper in its native schema when requested. Do not claim MCP servers are shared unless Codex, Claude Code, and OpenCode have each been checked or configured explicitly.

## Chezmoi Aliases & Sync Workflow
The interactive zsh aliases in `zsh/alias.zsh` are:

- `dot="chezmoi"`
- `dota="chezmoi add"` (copy live target state into chezmoi source state)
- `dotap="chezmoi apply"` (apply chezmoi source state to live targets)
- `doti="chezmoi init"`
- `dotat="chezmoi add --template"`
- `dote="chezmoi edit --watch"`
- `econfig="dote ~/.config"`, `ez="dote ~/.config/zsh/init.zsh"`, `ezals="dote ~/.config/zsh/alias.zsh"`, and `envim="dote ~/.config/nvim"`
- `dots="dot status"`

When working interactively with these aliases loaded, confirm a mapping with `dot source-path <path>` when needed, sync an approved live-file edit into source state with `dota <path>`, and verify with `dots <path>` plus the chezmoi source Git status. This machine has chezmoi `git.autoCommit` and `git.autoPush` enabled, so `dota` can commit and push immediately.

These aliases are unavailable in non-interactive agent shells. In agent-run commands, use their expanded forms through `rtk`, especially `rtk chezmoi source-path <path>`, `rtk chezmoi add <path>`, `rtk chezmoi status <path>`, and `rtk chezmoi diff <path>`; run `rtk git status` from the source directory reported by `rtk chezmoi source-path`. Do not run `rtk dota` or other alias names directly, and do not start an interactive shell solely to expand them. Scope every add or apply to the exact approved path. Use `dotap`/`rtk chezmoi apply` only for intentional source-to-live changes after reviewing `dot diff`/`rtk chezmoi diff`; applying may execute scripts, so never run an unscoped apply without explicit approval. Use `dotat` only when deliberately creating or replacing a template, and do not use `doti` for routine synchronization.

## Commit & Pull Request Guidelines
Changes here are meant to become part of the `chezmoi`-managed dotfiles set. Before adding or moving config files in this live `~/.config` tree, locate the `chezmoi` source with `chezmoi source-path` or use `chezmoi add` after the live edit so the change is not a machine-only leftover. Prefer editing the `chezmoi` source directly when the mapping is clear, then apply or verify the rendered target.

Do not run `chezmoi add` for native tool files outside `/Users/daniel/.config` from this repository, even if a tool installer creates or changes them. Examples that must stay unmanaged unless explicitly requested by exact path include `~/.codex/RTK.md`, `~/.claude/RTK.md`, `~/.claude/settings.json`, and `~/Library/Application Support/rtk/filters.toml`. Only capture files outside `/Users/daniel/.config` when the user explicitly asks to manage that exact file or directory.

Keep related changes grouped by tool, and describe them by config area, for example `nvim: tweak LSP defaults` or `tmux: adjust session picker bindings`. For visual changes, record what was reloaded or checked so the corresponding `chezmoi` update is easy to review and apply.
