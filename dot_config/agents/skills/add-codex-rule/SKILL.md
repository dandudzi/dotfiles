---
name: add-codex-rule
description: Add or edit Codex execution-policy rules in default.rules. Use when a user asks to allow, prompt for, forbid, narrow, or otherwise change command approval behavior, including package-installation rules.
---

# Add Codex Rule

1. Inspect the active rules file, its symlink, Codex version/help, and its chezmoi mapping with `chezmoi source-path` before editing.
2. Define the exact operation to match and nearby operations that must remain unmatched. Use the narrowest stable command/subcommand prefix; never match an entire tool when only one action is requested.
3. Add one direct rule:

   ```starlark
   prefix_rule(
       pattern = ["tool", "exact-subcommand"],
       decision = "prompt",
       justification = "The exact operation requires approval.",
       match = ["tool exact-subcommand"],
       not_match = ["tool list"],
   )

   ```

4. Give each rule focused `match` examples and `not_match` examples for adjacent commands such as `list`, `test`, `update`, or `publish`.
5. Validate with `codex execpolicy check` before and after editing. Check the direct form, nearby negative controls, and any stricter overlapping rule. Remember that `forbidden` wins over `prompt`, which wins over `allow`.
6. Review the exact diff, sync only the changed path with `chezmoi add`, and verify with `chezmoi status` plus `chezmoi git -- status --short` and upstream divergence.

Use only `chezmoi ...` for chezmoi source state; never access the source directory directly or change or override chezmoi configuration without explicit permission.

Do not broaden a rule merely to catch alternate flag ordering. Test and state native prefix limitations when relevant.
