# Repository Guidelines

## Project Structure & Module Organization

This repository is a config placement for one machine, managed as part of a broader dotfiles setup through `chezmoi`. It is organized by tool rather than by application: `nvim` contains editor config, `sketchybar` contains bar items and helpers, `tmux` contains terminal multiplexer config plus bundled plugins, and `scripts` contains standalone utilities with their own local docs or build files. Treat bundled plugin and dependency directories as vendored unless you are intentionally syncing upstream code.

Standing chezmoi authorization: The user explicitly accepts the configured auto-commit and auto-push behavior for future interactions. Once a configuration change and exact target path are authorized, its exact-path `chezmoi add <path>` persistence is also authorized. Do not request separate confirmation for the resulting commit or push; first verify the source worktree is clean and never include unrelated paths.

## Codex Configuration

The `agents` directory is the canonical configuration area for Codex on this machine. Keep global instructions in `agents/global.md`, skills in `agents/skills`, and execution-policy rules in `agents/rules`.

Keep these links so Codex reads the managed files without duplicate copies: `~/.codex/AGENTS.md` links to `agents/global.md`, `~/.agents/skills` links to `agents/skills`, and `~/.codex/rules/default.rules` links to `agents/rules/default.rules`.

Active MCP servers, hooks, permissions, models, and provider settings belong in Codex's native configuration. Inspect existing entries before editing and preserve unrelated settings. Keep secrets, OAuth state, credentials, caches, logs, histories, and runtime state out of `agents`. Do not recreate Claude Code or OpenCode configuration unless explicitly requested.

## Commit & Pull Request Guidelines

Changes here are meant to become part of the `chezmoi`-managed dotfiles set. Before adding or moving config files in this live `~/.config` tree, locate the `chezmoi` source with `chezmoi source-path` or use `chezmoi add` after the live edit so the change is not a machine-only leftover. Prefer editing the `chezmoi` source directly when the mapping is clear, then apply or verify the rendered target.

Do not run `chezmoi add` for native tool files outside `~/.config` from this repository, even if a tool installer creates or changes them. Examples that must stay unmanaged unless explicitly requested by exact path include `~/.claude/settings.json` and `~/Library/Application Support/`. Only capture files outside `~/.config` when the user explicitly asks to manage that exact file or directory.

Keep related changes grouped by tool, and describe them by config area, for example `nvim: tweak LSP defaults` or `tmux: adjust session picker bindings`. For visual changes, record what was reloaded or checked so the corresponding `chezmoi` update is easy to review and apply.

When adding or changing configuration, include a concise nearby comment explaining why the setting or change exists whenever the file format supports comments. Document the intent or tradeoff instead of merely restating what the setting does.
