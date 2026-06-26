# Hook Tool Map

Use this map when sharing hook behavior across Codex, Claude Code, and OpenCode.

## Shared Implementation

Store reusable scripts in `~/.config/agents/hooks`. Tool-specific config should call these scripts rather than duplicate logic.

Good shared hook scripts:

- Read event input from stdin, arguments, or documented environment variables.
- Exit with clear success/failure codes.
- Avoid interactive prompts.
- Avoid writing secrets to logs.
- Keep tool-specific assumptions in wrappers, not in the shared script.

## Codex

Codex hook config can live in `~/.codex/config.toml`, `~/.codex/hooks.json`, or trusted project `.codex` config depending on the installed version and intended scope.

Use Codex wrappers only to map Codex hook event data into the shared script contract.

## Claude Code

Claude Code hooks are configured in `~/.claude/settings.json`, project `.claude/settings.json`, local `.claude/settings.local.json`, or plugins.

Do not modify `settings.local.json` for shareable behavior unless the user asks for local-only setup. Preserve existing hooks by appending or merging entries.

## OpenCode

OpenCode hook-like behavior is commonly implemented through plugins in `~/.config/opencode/plugins` or project `.opencode/plugins`.

Use a small plugin wrapper to call shared scripts from `~/.config/agents/hooks`. Keep OpenCode-only plugin code separate from the shared hook implementation.

## Validation

After editing:

- Validate JSON or TOML syntax for changed config files.
- Run shared scripts directly with safe sample input.
- Read back symlink targets and wrapper paths.
- Tell the user if runtime verification requires launching an agent tool.
