---
name: obsidian-excalidraw
description: Work with drawings created by the Obsidian Excalidraw community plugin. Use for creating, opening, embedding, exporting, or programmatically modifying Excalidraw drawings and Excalidraw Automate workflows.
---

# Obsidian Excalidraw

Confirm the plugin and discover its current commands:

```bash
rtk obsidian plugin id=obsidian-excalidraw-plugin
rtk obsidian commands filter=obsidian-excalidraw-plugin
```

Creation commands depend on the active workspace and plugin settings. Use them only when that UI context is intended, then locate and verify the created file.

Modern drawings are usually Markdown files containing an `# Excalidraw Data` section with compressed scene data. Do not hand-edit or reformat that section. Inspect the actual filename before adding an embed because modern and legacy extensions differ.

For repeatable drawing changes, build a reviewed Excalidraw Automate integration. Copy immutable scene elements into its workbench, modify them there, and commit through the API. Use the API's creation or export functions rather than arbitrary CLI `eval`.

## Discover more

Use the runtime command list for installed command IDs and the Excalidraw Automate API documentation for programmatic operations. Do not rely on remembered plugin command IDs.
