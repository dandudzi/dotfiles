# Administrative and Developer Commands

Load this only for recovery, Sync, plugins, UI state, or development.

## Recovery and History

```bash
rtk obsidian diff path="Folder/Note.md"
rtk obsidian diff path="Folder/Note.md" from=1
rtk obsidian history path="Folder/Note.md"
rtk obsidian history:read path="Folder/Note.md" version=1
rtk obsidian history:list
rtk obsidian sync:history path="Folder/Note.md" total
rtk obsidian sync:read path="Folder/Note.md" version=1
```

Inspect before `history:restore` or `sync:restore`. Restoration replaces current state and requires explicit authorization.

## Registered Commands

```bash
rtk obsidian commands
rtk obsidian commands filter=tasks
rtk obsidian command id="<command-id>"
rtk obsidian hotkey id="<command-id>" verbose
```

Command actions may mutate content or depend on active file, selection, cursor, or workspace. Establish context before execution.

## Plugins, Themes, and Snippets

```bash
rtk obsidian plugins filter=community versions format=json
rtk obsidian plugins:enabled filter=community versions format=json
rtk obsidian plugin id="obsidian-tasks-plugin"
rtk obsidian themes versions
rtk obsidian theme
rtk obsidian snippets
rtk obsidian snippets:enabled
```

Enable, disable, install, uninstall, restricted-mode, theme, and snippet commands are administrative mutations. Require explicit intent and verify state.

## Workspace and Developer Diagnostics

```bash
rtk obsidian workspace ids
rtk obsidian tabs ids
rtk obsidian recents
rtk obsidian plugin:reload id="my-plugin"
rtk obsidian dev:errors
rtk obsidian dev:console level=error
rtk obsidian dev:screenshot path="screenshot.png"
rtk obsidian dev:dom selector=".workspace-leaf" text
rtk obsidian dev:css selector=".workspace-leaf" prop=background-color
```

Use reload → errors → console → visual/DOM verification for plugin development.

Treat `eval code="..."`, `dev:cdp`, arbitrary `command id=...`, plugin/theme installation, Sync toggles, restore, restart, and workspace deletion as privileged. Do not run them during routine vault management.

Source: [Official Obsidian CLI documentation](https://obsidian.md/help/cli), checked against Obsidian 1.12.7.
