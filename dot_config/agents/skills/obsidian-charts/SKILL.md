---
name: obsidian-charts
description: Create, inspect, troubleshoot, and edit interactive charts made by the Obsidian Charts community plugin (`obsidian-charts`). Use for fenced `chart` YAML blocks, chart types and modifiers, charts linked to Markdown tables, DataviewJS or `window.renderChart` integrations, chart theming, or rendered-chart verification.
---

# Obsidian Charts

Follow the vault's `AGENTS.md`. Preserve the surrounding note, frontmatter, links, embeds, block IDs, and unknown chart properties.

## Establish context

Work from the vault root and identify the exact target note before editing. Inspect the chart block and its nearby prose immediately before a mutation.

Confirm the installed plugin and discover its current commands when Obsidian is running:

```bash
rtk obsidian plugin id=obsidian-charts
rtk obsidian commands filter=obsidian-charts
```

Treat CLI output containing `Error:` as failure. If Obsidian is unavailable, inspect `.obsidian/community-plugins.json` and `.obsidian/plugins/obsidian-charts/manifest.json`, but describe that as configuration-file evidence rather than live state. Never install, enable, update, or replace the plugin without the owner's explicit approval.

Read [references/charts-reference.md](references/charts-reference.md) before choosing a chart type, using modifiers, linking a table, adding DataviewJS, or troubleshooting rendering.

## Choose the simplest data source

1. Use a static `chart` YAML block for manually maintained data.
2. Link an existing Markdown table by block ID when the table is the source of truth.
3. Use DataviewJS and `window.renderChart` only for genuinely dynamic data and only when Dataview is already installed and enabled or the owner explicitly approves it.

Do not introduce JavaScript when a native chart block or table-backed chart is sufficient.

## Create or revise a chart

Use a fenced `chart` block with YAML content:

````markdown
```chart
type: bar
labels: [Monday, Tuesday, Wednesday]
series:
  - title: Completed
    data: [3, 5, 4]
beginAtZero: true
legendPosition: top
```
````

- Keep each series title unless the owner requests otherwise.
- Keep label count and every series data count aligned for category charts.
- Use numbers or `null` for data points; quote labels that YAML could misinterpret.
- Preserve existing chart type, data source, ordering, colors, and modifiers unless the request requires changing them.
- Preserve a linked table's block ID and exact source filename. Use `layout: rows` or `layout: columns` deliberately.
- Keep DataviewJS local to the note and narrowly scoped. Do not use arbitrary CLI `eval` as a substitute.

## Verify

Inspect the exact note again after editing. Confirm:

- the Markdown fence is balanced and contains valid YAML;
- the chart type and modifiers are supported by the installed version;
- labels, series, and numeric values remain aligned;
- linked table block IDs and source files exist;
- any required companion plugin is enabled.

When Obsidian is running, verify the chart in Reading view or Live Preview and check the developer console only when troubleshooting is necessary. If rendered verification is unavailable, report that limitation instead of claiming the chart rendered successfully.
