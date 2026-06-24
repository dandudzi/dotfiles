# Repository Guidelines

## Project Structure & Module Organization
This repository is a config placement for one machine, managed as part of a broader dotfiles setup through `chezmoi`. It is organized by tool rather than by application: `nvim` contains editor config, `sketchybar` contains bar items and helpers, `tmux` contains terminal multiplexer config plus bundled plugins, and `scripts` contains standalone utilities with their own local docs or build files. Treat bundled plugin and dependency directories as vendored unless you are intentionally syncing upstream code.

## Commit & Pull Request Guidelines
Changes here are meant to become part of the `chezmoi`-managed dotfiles set. When you add a new config file, make sure it is captured in the upstream `chezmoi` source rather than treated as a machine-only leftover. Keep related changes grouped by tool, and describe them by config area, for example `nvim: tweak LSP defaults` or `tmux: adjust session picker bindings`. For visual changes, record what was reloaded or checked so the corresponding `chezmoi` update is easy to review and apply.
