---
name: add-codex-rule
description: Add or edit Codex execution-policy rules in default.rules. Use when a user asks to allow, prompt for, forbid, narrow, or otherwise change command approval behavior, including package-installation rules and RTK-wrapped commands.
---

# Add Codex Rule

1. Inspect the active rules file, its symlink, Codex version/help, and its chezmoi mapping with `rtk chezmoi source-path` before editing.
2. Define the exact operation to match and nearby operations that must remain unmatched. Use the narrowest stable command/subcommand prefix; never match an entire tool when only one action is requested.
3. Add equivalent direct and RTK rules. Use the existing `rtk_prefix_rule(...)` helper for the RTK form, not a bare `prefix_rule(...)`:

   ```starlark
   prefix_rule(
       pattern = ["tool", "exact-subcommand"],
       decision = "prompt",
       justification = "The exact operation requires approval.",
       match = ["tool exact-subcommand"],
       not_match = ["tool list"],
   )

   rtk_prefix_rule(
       pattern = ["rtk", "tool", "exact-subcommand"],
       decision = "prompt",
       justification = "The exact operation through RTK requires approval.",
       match = ["rtk tool exact-subcommand"],
       not_match = ["rtk tool list"],
   )
   ```

   The helper preserves the underlying rule decision through one documented global modifier and the positional `run`, `proxy`, `err`, `test`, or `summary` wrappers, including one modifier before or after a wrapper. Never add a blanket allow, prompt, or forbidden rule for those wrapper names.
4. Give each rule focused `match` examples and `not_match` examples for adjacent commands such as `list`, `test`, `update`, or `publish`.
5. Validate with `rtk codex execpolicy check` before and after editing. Check the direct form, canonical RTK form, one global modifier, one positional wrapper, modifier-before-wrapper, wrapper-before-modifier, nearby negative controls, and any stricter overlapping rule. Remember that `forbidden` wins over `prompt`, which wins over `allow`.
6. Review the exact diff, sync only the changed path with `rtk chezmoi add`, and verify with `rtk chezmoi status` plus `rtk chezmoi git -- status --short` and upstream divergence.

Use only `rtk chezmoi ...` for chezmoi source state; never access the source directory directly or change or override chezmoi configuration without explicit permission.

Do not broaden a rule merely to catch alternate flag ordering. Stacked modifiers, reordered combinations, and `run -c` command strings are outside the helper's native prefix coverage; test and state those limitations when relevant.
