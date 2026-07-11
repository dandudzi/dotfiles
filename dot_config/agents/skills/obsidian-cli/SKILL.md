---
name: obsidian-cli
description: Use the official Obsidian desktop CLI for general vault operations and command discovery. Trigger for reading, searching, creating, opening, moving, or updating properties in local Obsidian notes.
---

# Obsidian CLI

Follow the vault's `AGENTS.md`. Run from the vault root so the CLI targets the intended vault, and use exact vault-relative `path=` values. Obsidian must be running.

## Common actions

```bash
rtk obsidian read path="Projects/Plan.md"
```

Read one exact note through Obsidian. Prefer this when app-level file resolution matters.

```bash
rtk obsidian search:context query="migration" format=json
```

Search the indexed vault and return matching files, lines, and text as structured data.

```bash
rtk obsidian create path="Inbox/New note.md" content="# New note"
```

Create a note only if the path is absent. Add `open` only when the user wants to see it immediately.

```bash
rtk obsidian property:set name=status value=active type=text path="Projects/Plan.md"
```

Set a typed frontmatter property without rewriting the entire frontmatter block.

```bash
rtk obsidian move path="Inbox/Plan.md" to="Projects/Plan.md"
```

Move a note through Obsidian so internal links can be updated when that vault setting is enabled.

```bash
rtk obsidian open path="Projects/Plan.md" newtab
```

Open an exact file in the running desktop app.

## Discover more

- Run `rtk obsidian help` to list command groups.
- Run `rtk obsidian help <command>` before using unfamiliar options.
- Run `rtk obsidian` for the interactive TUI with autocomplete when working manually.
- Run `rtk obsidian commands filter=<prefix>` to discover core or plugin command IDs.
- Run `rtk obsidian plugins:enabled versions format=json` to inspect active plugins.

Prefer `format=json` for automation. Treat output containing `Error:` as failure even when the process exits successfully.
