# Global Agent Instructions

These instructions apply across Codex, Claude Code, and OpenCode when their global instruction paths are symlinked to this file.

## Shared Working Rules
- Treat this machine's `~/.config` tree as chezmoi-managed. When adding or moving config files, capture changes in chezmoi instead of leaving machine-only files behind.
- Prefer portable `SKILL.md` skills for reusable workflows that apply across multiple tools.
- Keep secrets, tokens, OAuth state, histories, logs, caches, sessions, and generated runtime state out of shared agent configuration.
- When tool behavior differs, keep the shared intent here and use the smallest tool-specific wrapper required by that tool.

## Verification
- Before changing durable config, check whether the target path is managed by chezmoi.
- After creating or moving shared config, verify the symlink target and chezmoi source path.

@/Users/daniel/.codex/RTK.md

@RTK.md
