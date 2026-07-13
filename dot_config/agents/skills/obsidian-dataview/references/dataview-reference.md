# Obsidian Dataview reference

This reference targets the installed Dataview plugin version `0.5.68`. Recheck `.obsidian/plugins/dataview/manifest.json`, `.obsidian/plugins/dataview/data.json`, and the official documentation when the installed version changes.

## Indexed data

Dataview indexes:

- YAML frontmatter properties;
- inline page fields such as `[rating:: 5]` or `(published:: 1845)`;
- implicit file fields under `file`, including path, name, folder, links, tags, timestamps, lists, and tasks;
- fields attached to list items and tasks.

It does not treat arbitrary paragraph text as queryable data. Add a field only when the owner wants a durable metadata convention, and preserve the existing style when the vault already uses frontmatter or inline fields.

Field names containing spaces are normalized to lowercase hyphenated names in DQL. Use `row["Field With Space"]` when explicit access is clearer or when a field conflicts with a DQL keyword.

## DQL structure

Every DQL query has exactly one output type. All other clauses are optional:

````markdown
```dataview
<LIST | TABLE | TASK | CALENDAR> <fields>
FROM <source>
WHERE <expression>
SORT <field> <ASC | DESC>
GROUP BY <expression>
FLATTEN <expression>
LIMIT <number>
```
````

Commands execute in written order. `LIST`, `TABLE`, and `CALENDAR` operate on pages; `TASK` operates on task records.

### Sources

- Tag: `FROM #project`
- Folder: `FROM "Projects"` without a trailing slash
- Exact file: `FROM "Projects/Index.md"`
- Incoming links to a note: `FROM [[Project Hub]]`
- Outgoing links from a note: `FROM outgoing([[Project Hub]])`
- Links to the current note: `FROM [[]]`
- Combine sources with `and`, `or`, negation, and parentheses.

### Common examples

List recently modified notes:

````markdown
```dataview
LIST
FROM "Notes"
WHERE file.mtime >= date(today) - dur(7 days)
SORT file.mtime DESC
```
````

Show open tasks carrying a typed due date:

````markdown
```dataview
TASK
FROM "Projects"
WHERE !completed AND due AND typeof(due) = "date"
SORT due ASC
```
````

Add metadata to one task without changing the page schema:

```markdown
- [ ] Review proposal [due:: 2026-07-20] [area:: work]
```

Inline DQL displays one value with the configured `=` prefix, for example `` `= this.status` ``. The current vault also enables inline JavaScript with `$=`, but apply the same approval and trust boundary as fenced DataviewJS.

## DataviewJS

Use a fenced `dataviewjs` block only for a requirement DQL cannot meet. The `dv` API can query the index and render output:

````markdown
```dataviewjs
const pages = dv.pages('"Projects"').where(page => page.status !== "done");
dv.table(["Project", "Status"], pages.map(page => [page.file.link, page.status]));
```
````

DataviewJS runs arbitrary JavaScript and has filesystem access. Require explicit owner approval before introducing or executing it, keep queries narrowly scoped, avoid external network access and file writes, and reject untrusted snippets. Prefer `dv.pages`, `dv.page`, `dv.list`, `dv.table`, `dv.taskList`, and `dv.view` only as needed.

## Current vault settings

At the time this skill was created, the vault enabled DQL, DataviewJS, inline DQL, and inline JavaScript. The inline prefixes were `=` and `$=`, refresh was enabled at 2500 ms, HTML rendering was enabled, and automatic task-completion metadata tracking was disabled. Treat these as configuration-file observations, not permanent assumptions.

## Primary documentation

- Dataview overview: `https://blacksmithgu.github.io/obsidian-dataview/`
- DQL, JavaScript, and inline queries: `https://blacksmithgu.github.io/obsidian-dataview/queries/dql-js-inline/`
- Query structure: `https://blacksmithgu.github.io/obsidian-dataview/queries/structure/`
- Query types: `https://blacksmithgu.github.io/obsidian-dataview/queries/query-types/`
- Data commands: `https://blacksmithgu.github.io/obsidian-dataview/queries/data-commands/`
- Sources: `https://blacksmithgu.github.io/obsidian-dataview/reference/sources/`
- JavaScript API: `https://blacksmithgu.github.io/obsidian-dataview/api/intro/`
