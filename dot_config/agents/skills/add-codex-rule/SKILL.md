---
name: add-codex-rule
description: Add or edit Codex execution-policy rules in default.rules. Use when a user asks to allow, prompt for, forbid, narrow, or otherwise change command approval behavior, including package-installation rules and RTK-wrapped commands.
---

# Add Codex Rule

1. Inspect the active rules file, its symlink, Codex version/help, and its exact chezmoi source before editing.
2. Define the exact operation to match and nearby operations that must remain unmatched. Use the narrowest stable command/subcommand prefix; never match an entire tool when only one action is requested.
3. Add equivalent rules for both forms:

   ```starlark
   pattern = ["tool", "exact-subcommand"]
   pattern = ["rtk", "tool", "exact-subcommand"]
   ```

4. Give each rule focused `match` examples and `not_match` examples for adjacent commands such as `list`, `test`, `update`, or `publish`.
5. Validate direct and RTK forms with `rtk codex execpolicy check`, including positive matches, negative controls, and any stricter overlapping rule. Remember that `forbidden` wins over `prompt`, which wins over `allow`.
6. Review the exact diff, sync only the changed path with `rtk chezmoi add`, and verify chezmoi status plus source-repository status and upstream divergence.

Do not broaden a rule merely to catch alternate flag ordering. State prefix-matching limitations explicitly when the native policy cannot express the requested boundary safely.
