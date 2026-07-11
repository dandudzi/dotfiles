# Excalidraw Plugin

Verify the installed plugin and commands:

```bash
rtk obsidian plugin id=obsidian-excalidraw-plugin
rtk obsidian commands filter=obsidian-excalidraw-plugin
```

Validated global command IDs include:

- `obsidian-excalidraw-plugin:excalidraw-autocreate`
- `obsidian-excalidraw-plugin:excalidraw-autocreate-newtab`
- `obsidian-excalidraw-plugin:excalidraw-autocreate-on-current`
- `obsidian-excalidraw-plugin:excalidraw-open`
- `obsidian-excalidraw-plugin:excalidraw-open-on-current`
- `obsidian-excalidraw-plugin:excalidraw-open-sidepanel`
- `obsidian-excalidraw-plugin:excalidraw-toggle-session-view-mode`

Creation commands depend on Excalidraw settings and active UI context; they do not provide a deterministic destination-path interface. Execute them only when that UI behavior is intended, then query recently created files and verify the result.

## Preserve Drawing Files

Modern drawings are commonly Markdown files with frontmatter such as:

```yaml
---
excalidraw-plugin: parsed
---
```

They include an `# Excalidraw Data` section containing text elements, links, embedded-file metadata, and compressed drawing data. Legacy `.excalidraw` files may also exist.

Do not hand-edit, reformat, or normalize the Excalidraw Data section. Do not treat an Excalidraw Markdown file as an ordinary note. Preserve frontmatter keys, drawing blocks, embedded-file references, and export settings.

Use normal Obsidian embeds such as `![[Drawing.excalidraw]]`, matching the vault's actual resolved drawing name. Modern files may end in `.excalidraw.md`, while legacy files may end in `.excalidraw`; inspect before authoring or changing an embed. Preserve sizing, alignment, and subpath options already present.

## Automate Through Excalidraw Automate

For repeatable programmatic drawing changes, use the plugin's Excalidraw Automate API in a reviewed script or plugin. Scene elements are immutable: copy them into the EA workbench, modify there, then commit with the API. Use `create()` for controlled drawing creation and `createSVG()` or `createPNG()` for exports.

Do not use arbitrary `obsidian eval` as the default integration. It bypasses review, can mutate the whole vault/app, and is difficult to test. Build a narrow helper only after concrete drawing workflows are known.

For text-defined diagrams that need easy agent editing and version review, prefer Mermaid. Use Excalidraw when free-form layout, sketching, or interactive visual editing is the actual requirement.

Sources: [Obsidian Excalidraw](https://github.com/zsviczian/obsidian-excalidraw-plugin) and [Excalidraw Automate API](https://github.com/zsviczian/obsidian-excalidraw-plugin/blob/master/docs/API/attributes_functions_overview.md).
