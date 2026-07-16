---
name: persist-config-with-chezmoi
description: Persist configuration changes through chezmoi. Use whenever creating, editing, moving, or deleting files under ~/.config, or when the user explicitly requests managing another exact dotfile path.
---

# Persist Config with Chezmoi

- Run shell commands through `rtk`.
- Keep changes under `~/.config` persistent in chezmoi.
- Never manage files outside `~/.config` unless the user explicitly requests the exact path.
- Never add credentials, OAuth state, caches, logs, histories, or runtime state.

Before changing a managed file, inspect its source with `rtk chezmoi source-path <target>` and `rtk chezmoi diff <target>`.

- Interact with source state only through `rtk chezmoi ...`; never access or modify the source directory directly.
- Never change or override chezmoi configuration without explicit permission.
- For templates, use `rtk chezmoi edit <exact-target>`; never replace a template by adding its rendered file.
- After an approved live-file change or new file, run `rtk chezmoi add <exact-target>`.
- Review `rtk chezmoi diff <exact-target>` before running `rtk chezmoi apply <exact-target>`.
- Never run unscoped `add` or `apply`.
- Before `add`, run `rtk chezmoi git -- status --short`; auto-commit stages the whole source tree and may push unrelated changes.
- Do not use `forget` or `destroy` without explicit approval.

Verify with `rtk chezmoi status <exact-target>`, `rtk chezmoi diff <exact-target>`, and `rtk chezmoi git -- status --short`. Report whether chezmoi committed or pushed the change.
