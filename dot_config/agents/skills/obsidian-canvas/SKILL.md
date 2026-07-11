---
name: obsidian-canvas
description: Create, inspect, and edit Obsidian Canvas files using the JSON Canvas format. Use for `.canvas` nodes, edges, groups, file cards, text cards, links, embeds, layout, or Canvas validation.
---

# Obsidian Canvas

Canvas files are JSON with top-level `nodes` and `edges` arrays. Nodes require unique IDs, types, positions, and dimensions. Edges require unique IDs and valid `fromNode` and `toNode` references.

## Create or edit

Use direct JSON editing when the destination path and layout must be deterministic. Preserve unknown fields and use stable opaque IDs rather than array positions.

Validate syntax:

```bash
rtk jq empty "Board.canvas"
```

Also check for duplicate node or edge IDs and dangling edge references; JSON syntax alone is insufficient. Open the result in Obsidian for visual verification.

Use file nodes when cards should participate in backlinks and Graph view. Text-only cards do not create backlinks.

## Discover more

Run `rtk obsidian commands filter=canvas` to discover UI commands. The standard new-Canvas command depends on the active workspace location, so prefer direct JSON when an exact path is required. Consult JSON Canvas 1.0 for the current node and edge schema.
