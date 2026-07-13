---
name: obsidian-dataview
description: Create, inspect, troubleshoot, and edit Obsidian Dataview queries and metadata. Use for fenced `dataview` DQL blocks, inline Dataview expressions, inline fields, page or task metadata, LIST/TABLE/TASK/CALENDAR queries, DataviewJS, or the `dv` API.
---

# Obsidian Dataview

Follow the vault's `AGENTS.md`. Preserve surrounding prose, frontmatter types, wikilinks, embeds, task syntax, and unknown query clauses.

Read [references/dataview-reference.md](references/dataview-reference.md) before changing metadata conventions, writing a complex query, working with tasks, or using JavaScript.

## Establish context

Work from the vault root and identify the exact target note. Inspect the query and nearby metadata immediately before editing.

When Obsidian is running, confirm the plugin and discover its commands:

```bash
rtk obsidian plugin id=dataview
rtk obsidian commands filter=dataview
```

Treat CLI output containing `Error:` as failure. If Obsidian is unavailable, inspect `.obsidian/community-plugins.json`, `.obsidian/plugins/dataview/manifest.json`, and relevant non-secret settings, but report that as configuration-file evidence rather than live state. Never install, enable, update, or replace the plugin without the owner's explicit approval.

## Choose the least powerful query form

1. Use a fenced `dataview` DQL block for lists, tables, tasks, or calendars.
2. Use an inline DQL expression for one displayed value or calculation.
3. Use `dataviewjs` only when DQL cannot express the required retrieval or rendering.

Do not add or execute new DataviewJS without the owner's explicit approval. DataviewJS is arbitrary JavaScript with filesystem access; never paste or run code from an untrusted source and never use CLI `eval` as a substitute.

## Author DQL

Keep the query narrow by selecting a tag, folder, file, or link source whenever practical:

````markdown
```dataview
TABLE status AS "Status", due AS "Due"
FROM "Projects"
WHERE status != "done"
SORT due ASC
```
````

- Use exactly one query type: `LIST`, `TABLE`, `TASK`, or `CALENDAR`.
- Apply commands in intentional order: `FROM`, `WHERE`, `SORT`, `GROUP BY`, `FLATTEN`, and `LIMIT`.
- Verify field names and types from the actual notes; do not invent a metadata schema.
- Preserve existing aliases, `WITHOUT ID`, source expressions, and column order unless the request requires changing them.
- Keep broad vault-wide queries only when the result genuinely needs the whole vault.
- Remember that DQL displays and calculates data but does not rewrite source metadata. Checking a task in a rendered `TASK` query is the exception and updates its source checkbox.

For recurring or metadata-rich tasks, follow the vault's Tasks-plugin rules and use the `obsidian-tasks` skill rather than treating Dataview as the task mutation layer.

## Verify

Inspect the exact note again after editing. Confirm balanced fences, a supported query type, valid command order, resolvable sources, existing fields, and type-safe comparisons. When Obsidian is running, open the note and verify the rendered result after the Dataview index refreshes. If rendered verification is unavailable, report that limitation instead of claiming success.
