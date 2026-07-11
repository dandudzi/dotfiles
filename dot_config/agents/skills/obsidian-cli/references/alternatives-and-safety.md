# Alternatives and Safety

## Choose the Right Surface

| Need | Preferred surface | Reason or fallback |
| --- | --- | --- |
| Indexed search, backlinks, tags, tasks, properties, Bases | Official CLI | Uses the running app's index and resolution rules. |
| Offline read or literal/bulk text scan | Filesystem and `rg` | Works without Obsidian; does not reproduce app semantics. |
| Focused middle-of-note edit | Minimal filesystem patch | CLI has no general patch command. |
| Bulk import and attachment staging | Filesystem, then CLI validation | Efficient and preserves sources. |
| Rename or move linked files | CLI `move` or `rename` | Can update internal links. |
| Open, focus, search, or capture from another app | Obsidian URI | Simple action with little structured output. |
| Plugin-owned behavior | `commands` then `command id=...` | Preserves plugin semantics but may depend on UI state. |
| Reusable atomic in-app transformation | Plugin API | Use `Vault.process()`, `processFrontMatter()`, and `FileManager.renameFile()`. |
| Sync without desktop Obsidian | `ob` Headless Sync | Transport only, not note automation. |
| Persistent cross-client access | Audited MCP or plugin | Add only when repeated workflows justify it. |

## Protect Vault Semantics

- Preserve YAML types, wikilinks, Markdown links, embeds, heading links, block IDs, Base definitions, Canvas files, and fenced Tasks queries.
- Do not rewrite frontmatter with regex. Use `property:*` or a format-preserving YAML edit.
- Treat `.base` as view configuration and note properties as data. Validate with `base:query`.
- Use CLI or `FileManager.renameFile()` for linked moves. Raw filesystem moves bypass link updating.
- Do not run concurrent bulk writers. Re-read before a patch and verify afterward.
- Keep migration sources unchanged and stage imports before normalization.

## Respect Tasks Plugin Behavior

Core CLI inventory covers Markdown checkboxes. Core `task ... done` changes a status character but does not promise Tasks-plugin recurrence, completion dates, dependencies, custom statuses, or `onCompletion` actions.

When those semantics matter:

1. Inspect enabled plugins and registered commands.
2. Find the command with `rtk obsidian commands filter=tasks`.
3. Confirm required active-file or cursor context.
4. Execute only with mutation authorization.
5. Re-query the source and any generated recurring task.

## Preflight Structural Changes

1. Inventory exact affected paths.
2. Inspect backlinks, outgoing links, embeds, and properties.
3. Check `diff`, `history`, or `sync:history` where available.
4. Present a dry-run plan for multi-file work.
5. Apply the smallest authorized change.
6. Verify content, paths, unresolved links, and attachments.

Use trash, never permanent deletion. Orphans and dead ends may be intentional.

## Handle Availability and Errors

- If `rtk command -v obsidian` fails, the CLI is missing or unregistered.
- If `rtk obsidian version` cannot find Obsidian, the binary exists but the desktop app is unavailable.
- If a command is unknown, inspect `rtk obsidian help <command>`.
- If a feature fails, check whether its plugin is enabled.
- Treat output containing `Error:` as failure even if exit status is 0.
- Confirm the vault and allow indexing to finish before replacing an empty indexed query with raw search.

Never silently use filesystem operations when the request depends on link updating, template resolution, plugin behavior, typed properties, or indexed results.

Sources: [CLI](https://obsidian.md/help/cli), [URI](https://obsidian.md/help/uri), [Vault API](https://docs.obsidian.md/Plugins/Vault), [safe rename](https://docs.obsidian.md/Reference/TypeScript+API/FileManager/renameFile), and [Tasks behavior](https://publish.obsidian.md/tasks/Editing/Toggling+and+Editing+Statuses).
