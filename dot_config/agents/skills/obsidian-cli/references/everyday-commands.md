# Everyday Obsidian CLI Commands

Use exact vault-relative paths and run shell commands through `rtk`.

## Inspect, Read, and Search

```bash
rtk obsidian vault
rtk obsidian files ext=md
rtk obsidian files folder="Imports" total
rtk obsidian folders
rtk obsidian file path="Folder/Note.md"
rtk obsidian read path="Folder/Note.md"
rtk obsidian outline path="Folder/Note.md" format=json
rtk obsidian search query="Apple Notes" format=json
rtk obsidian search:context query="Apple Notes" format=json
rtk obsidian search query="TODO" total
```

Use `file=<name>` only when wikilink resolution is wanted and the name is unambiguous. `search` returns paths; `search:context` returns matching lines. Use `rg` for literal offline searches or hidden configuration.

`folders total` includes the vault root `/`; `vault` reports only non-root folder count.

## Create and Capture

```bash
rtk obsidian create path="Inbox/New note.md" content="# New note"
rtk obsidian create path="Projects/Trip.md" template="Project"
rtk obsidian append path="Inbox/New note.md" content="New paragraph"
rtk obsidian prepend path="Inbox/New note.md" content="Intro"
rtk obsidian open path="Inbox/New note.md" newtab
```

Without `overwrite`, `create` protects an existing file. `prepend` inserts after frontmatter. Use a focused file patch for middle-of-note edits.

## Daily Notes and Templates

```bash
rtk obsidian daily:path
rtk obsidian daily:read
rtk obsidian daily:append content="- [ ] Review inbox"
rtk obsidian daily:prepend content="## Focus"
rtk obsidian templates total
rtk obsidian template:read name="Project"
rtk obsidian template:read name="Project" title="Trip" resolve
```

Prefer `create path="..." template="..."` over `template:insert`, which targets the active file.

## Properties, Aliases, and Tags

```bash
rtk obsidian properties format=json
rtk obsidian properties path="Folder/Note.md" format=json
rtk obsidian property:read name=status path="Folder/Note.md"
rtk obsidian property:set name=status value=active type=text path="Folder/Note.md"
rtk obsidian property:set name=reviewed value=true type=checkbox path="Folder/Note.md"
rtk obsidian property:remove name=temporary path="Folder/Note.md"
rtk obsidian aliases path="Folder/Note.md" verbose
rtk obsidian tags counts sort=count format=json
rtk obsidian tag name="#project" verbose
```

Property types are `text`, `list`, `number`, `checkbox`, `date`, and `datetime`. Use property commands instead of regex edits to frontmatter.

## Tasks

```bash
rtk obsidian tasks todo format=json
rtk obsidian tasks path="Notes Migration.md" todo format=json
rtk obsidian tasks daily total
rtk obsidian tasks verbose
rtk obsidian task ref="Notes Migration.md:31"
rtk obsidian task ref="Notes Migration.md:31" done
```

Line references can shift; re-query before mutation. For Tasks-plugin recurrence, done dates, dependencies, or `onCompletion`, discover and use the plugin command.

## Links and Vault Health

```bash
rtk obsidian backlinks path="Folder/Note.md" counts format=json
rtk obsidian links path="Folder/Note.md" total
rtk obsidian unresolved verbose format=json
rtk obsidian unresolved total
rtk obsidian orphans total
rtk obsidian deadends total
```

Run these before and after migration or structural changes. Review results; do not auto-fix them.

## Bases

```bash
rtk obsidian bases
rtk obsidian base:query path="Projects.base" format=json
rtk obsidian base:query path="Projects.base" view="Active" format=json
rtk obsidian base:create path="Projects.base" view="Active" name="New project"
```

`base:views` uses the active Base and has no documented path parameter in 1.12.7. Prefer `base:query path=...` for deterministic automation.

## Move, Rename, and Delete

```bash
rtk obsidian backlinks path="Old/Note.md" format=json
rtk obsidian move path="Old/Note.md" to="Archive/Note.md"
rtk obsidian rename path="Archive/Note.md" name="Renamed note"
rtk obsidian unresolved verbose format=json
rtk obsidian delete path="Archive/Renamed note.md"
```

Move and rename can update links when the vault setting is enabled. `delete` uses trash. Never add `permanent` without explicit authorization.

Source: [Official Obsidian CLI documentation](https://obsidian.md/help/cli), checked against Obsidian 1.12.7.
