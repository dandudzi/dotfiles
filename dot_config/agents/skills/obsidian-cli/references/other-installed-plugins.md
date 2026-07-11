# Other Installed Plugins

Always verify current status and version with `plugins`, `plugins:enabled`, and `plugin id=<id>`. Do not assume an installed plugin is enabled.

## Tag Wrangler

Tag Wrangler renames, merges, searches, and creates tag pages through the Tags pane and tag context menus. It exposes no reliable global CLI command in the current vault.

Use `tags` and `tag` for read-only inventory. For rename or merge:

1. Back up and inventory all matching tags.
2. Finish or pause background sync.
3. Identify tag-page aliases and nested subtags.
4. Use Tag Wrangler's UI so it can parse tags and warn about merges.
5. Re-scan tags and affected files afterward.

Tag renames can be partially applied if files change during the operation and do not have a general undo. Never emulate them with an unreviewed global text replacement.

## Iconize

Iconize stores visual file/folder settings and can optionally read an `icon` frontmatter property. Do not edit its `data.json` directly.

If frontmatter integration is enabled and the user requests a note icon, use a typed property:

```bash
rtk obsidian property:set name=icon value=IbBell type=text path="Folder/Note.md"
```

Icon IDs depend on installed icon packs. Confirm the desired ID in Iconize before writing. Folder icons and rule-based icons should be configured through the plugin UI.

## Importer

Importer is GUI-driven and may be installed but disabled. Enable or run it only for an explicit import request. Preserve original exports, use a staging folder, and validate counts, timestamps, attachments, and links before reorganizing.

## Editing Toolbar

Editing Toolbar changes editor UI and command access; it does not define a durable vault format. It may be installed but disabled. Do not enable it merely for automation because direct CLI/file operations do not depend on it.

Sources: [Tag Wrangler](https://github.com/pjeby/tag-wrangler) and [Iconize](https://florianwoelki.github.io/obsidian-iconize/).
