---
name: update-shared-hooks
description: Add, migrate, or update shared hook scripts and wire them into Codex, Claude Code, and OpenCode with tool-specific hook wrappers. Use when the user asks to share hooks, install pre/post tool-use automation, change hook scripts in the shared agents folder, audit hook configuration, or preserve one hook implementation across all three agent environments.
---

# Update Shared Hooks

## Overview

Use this skill to keep hook logic in one shared script while configuring each agent tool with its own supported hook mechanism. Shared implementation belongs in `~/.config/agents/hooks`.

## Workflow

1. Read `~/.config/AGENTS.md` and `~/.config/agents/AGENTS.md`.
2. Inspect existing hook config files and plugin folders before editing.
3. Put reusable hook implementation in `~/.config/agents/hooks/<script>`.
4. Add only thin tool-specific wrappers or config entries that call the shared script.
5. Preserve existing hooks and plugin behavior. Merge instead of replacing.
6. Keep secrets and machine-local paths out of shared hook scripts unless the user explicitly accepts local-only behavior.
7. Validate syntax for edited config files and run the hook script directly with safe sample input when possible.
8. Capture only exact rendered targets with `rtk chezmoi add <path>`.

## Guardrails

- Do not symlink one universal hook config across all tools. Hook config formats differ.
- Use only `rtk chezmoi ...` for chezmoi source state; never access the source directory directly or change or override chezmoi configuration without explicit permission.
- Do not overwrite existing `settings.json`, `config.toml`, `hooks.json`, `opencode.json`, or plugin files without inspecting them.
- Make shared hook scripts executable only when required, and preserve file mode through chezmoi if needed.
- Prefer deterministic scripts with clear stdin/stdout behavior. Avoid interactive prompts inside hooks.
- If a hook can block agent operation, add failure behavior deliberately and document it.

## Tool Map

Read `references/hook-tool-map.md` before wiring a shared script into active hook config.

## Output Standard

Report the shared script path, every active hook wrapper changed, how existing hooks were preserved, and what validation was run.
