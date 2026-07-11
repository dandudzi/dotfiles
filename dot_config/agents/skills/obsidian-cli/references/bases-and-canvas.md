# Bases and Canvas

## Bases

A `.base` file is valid YAML describing filters, formulas, property presentation, summaries, and views. Its rows come from vault files; note data belongs in Markdown frontmatter rather than the Base file.

Prefer CLI for queries and item creation:

```bash
rtk obsidian bases
rtk obsidian base:query path="Projects.base" format=json
rtk obsidian base:query path="Projects.base" view="Active" format=json
rtk obsidian base:create path="Projects.base" view="Active" name="New project"
```

`base:create` creates a new item represented by a Markdown note in an existing Base view; it does not create a `.base` definition file.

Use typed `property:set` to change the Markdown data displayed by a Base. When editing a `.base` definition directly:

1. Read the entire file.
2. Preserve unknown keys and plugin-added view configuration.
3. Keep formula expressions quoted as YAML strings.
4. Apply the smallest patch.
5. Inspect the top-level `views` list and query every affected named view with `base:query`.

Check that a new path does not exist and do not overwrite it. Validate YAML with an available local parser, then use `base:query` for Obsidian-specific semantics. If no local YAML parser is available, treat a successful query of every view as the minimum validation.

Global filters and view filters are combined with `AND`. `base:views` targets the active Base in Obsidian 1.12.7, so do not use it for unattended path-targeted validation.

## Canvas

Obsidian Canvas uses the open JSON Canvas `.canvas` format. The top level contains `nodes` and `edges` arrays.

Every node has a unique `id`, `type`, `x`, `y`, `width`, and `height`. Common node types:

- `text` with `text` Markdown.
- `file` with a vault-relative `file` and optional `subpath`.
- `link` with `url`.
- `group` with optional `label` and background settings.

Every edge has a unique `id` plus valid `fromNode` and `toNode` IDs. Preserve optional sides, endings, colors, labels, and unknown extension fields.

For deterministic creation or editing:

1. Inventory existing `*.canvas` files.
2. Parse the entire file as JSON.
3. Check unique node/edge IDs and valid edge references.
4. Preserve unknown fields and make a minimal structural patch.
5. For a new file, confirm the destination is absent and create it without overwrite. Use stable opaque IDs, not array positions.
6. Validate syntax with `rtk jq empty "Board.canvas"`, then use `jq -e` or a reviewed helper to reject duplicate IDs and edges whose endpoints are absent.
7. Open the Canvas in Obsidian and inspect it visually. If GUI verification is unavailable, report that limitation instead of claiming rendering success.

`canvas:new-file` creates a Canvas relative to active UI context and has no documented path parameter. Use direct validated JSON when an exact destination is required.

Text-only Canvas cards do not create backlinks. Use file nodes when the content must participate in the vault graph. Embed a Canvas with `![[Board.canvas]]`; embedded canvases show shapes but not the text inside cards.

Sources: [Bases syntax](https://obsidian.md/help/bases/syntax), [Canvas help](https://obsidian.md/help/plugins/canvas), and [JSON Canvas 1.0](https://jsoncanvas.org/spec/1.0/).
