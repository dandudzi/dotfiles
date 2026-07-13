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

- Edit the chezmoi source directly when its mapping is clear.
- Edit template sources directly; do not replace them by adding rendered files.
- After an approved live-file change or new file, run `rtk chezmoi add <exact-target>`.
- Review `rtk chezmoi diff <exact-target>` before running `rtk chezmoi apply <exact-target>`.
- Never run unscoped `add` or `apply`.
- Treat `chezmoi add` as potentially committing and pushing automatically.
- Do not use `forget` or `destroy` without explicit approval.

Verify with `rtk chezmoi status <exact-target>`, `rtk chezmoi diff <exact-target>`, and source-repository `rtk git status --short`. Report whether chezmoi committed or pushed the change.
