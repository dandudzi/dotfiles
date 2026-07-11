---
name: obsidian-bases
description: Create, inspect, query, and edit Obsidian Bases. Use for `.base` YAML, Base filters, formulas, views, summaries, Base embeds, or creating Markdown items represented in a Base.
---

# Obsidian Bases

A `.base` file defines YAML filters, formulas, properties, summaries, and views. Its rows come from vault files; store row data in note properties, not in the Base definition.

## Query and edit

```bash
rtk obsidian base:query path="Projects.base" view="Active" format=json
```

Query one named view and return its current rows. Use this after editing the Base or its note properties.

```bash
rtk obsidian base:create path="Projects.base" view="Active" name="New project"
```

Create a Markdown item in an existing Base view. This does not create a new `.base` file.

When editing `.base` directly, read the entire YAML document, preserve unknown keys, keep formula expressions quoted, and validate every affected view with `base:query`. Use typed `property:set` commands for note data.

## Discover more

Run `rtk obsidian help base:query` or `rtk obsidian help base:create` for current CLI options. Consult the official Bases syntax when changing filters, formulas, or view schemas rather than guessing field names.
