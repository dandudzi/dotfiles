# Obsidian Charts reference

This reference targets the installed `obsidian-charts` plugin version 3.9.0. Recheck `.obsidian/plugins/obsidian-charts/manifest.json` and the official documentation when the installed version changes.

The documentation URL `https://charts.phib.ro/Meta/Charts/Charts+Documentation` currently returns a not-found page. Use the plugin's official documentation source at `https://github.com/phibr0/obsidian-charts/tree/master/docusaurus/docs` as the primary reference.

## Native chart blocks

Charts use YAML inside a fenced `chart` block. The common structure is:

````markdown
```chart
type: line
labels: [Monday, Tuesday, Wednesday]
series:
  - title: First series
    data: [1, 2, 3]
  - title: Second series
    data: [3, 2, 1]
```
````

The documentation lists these chart types:

| Type | Good use | Notes |
| --- | --- | --- |
| `bar` | Compare categories | Supports horizontal and stacked layouts |
| `line` | Trends and ordered values | Supports fill, tension, gaps, and best-fit options |
| `pie` | Part-to-whole composition | Usually use `width` and `labelColors` |
| `doughnut` | Part-to-whole composition | Same data shape as pie |
| `radar` | Compare multiple dimensions | Use `rMax` to cap the radial axis |
| `polarArea` | Compare magnitudes around a circle | Usually use `width` and `labelColors` |
| `sankey` | Visualize flows between named nodes | Consult the dedicated official example before editing its specialized data shape |

Do not invent undocumented types such as `scatter` or `bubble` for native chart blocks. For unsupported Chart.js configurations, use the plugin API only when a safe, existing JavaScript integration is appropriate.

## Modifiers

Common modifiers documented by the plugin:

- Any chart: `width`, `legend`, `legendPosition`, `transparency`.
- Line: `fill`, `bestFit`, `bestFitTitle`, `bestFitNumber`, `spanGaps`, `tension`.
- Bar and line: `beginAtZero`, `indexAxis`, `stacked`, `xTitle`, `yTitle`, `xReverse`, `yReverse`, axis `Min`, `Max`, `Display`, and `TickDisplay` variants, and `time`.
- Radar and polar area: `rMax`.
- Pie, doughnut, radar, and polar area examples commonly use `labelColors`.

Constraints and defaults:

- `width`: any CSS width; default `100%`.
- `legend`: boolean; default `true`.
- `legendPosition`: `top`, `left`, `bottom`, or `right`; default `top`.
- `fill`, `bestFit`, `spanGaps`, `beginAtZero`, and `stacked`: boolean; default `false`.
- `bestFitNumber`: zero-based series index; default `0`.
- `tension`: number from `0` to `1`; default `0`.
- `indexAxis`: `x` or `y`; default `x`.
- `transparency`: number from `0.0` to `1.0`; default `0.25`.
- Axis minimum overrides `beginAtZero`.

## Charts backed by Markdown tables

Add a block ID directly after the table, then reference it from the chart:

````markdown
| Month | Planned | Actual |
| --- | ---: | ---: |
| Jan | 10 | 8 |
| Feb | 12 | 13 |
^monthly-data

```chart
type: bar
id: monthly-data
layout: columns
beginAtZero: true
```
````

- Add `file: Note name` when the table is in another note.
- Set `layout` to `rows` or `columns` according to the table orientation.
- Use `select: [name]` to include specific rows or columns.
- Preserve the table block ID because other embeds or links may use it.

## DataviewJS and the plugin API

When Charts and Dataview are both enabled, render a standard Chart.js payload with:

```javascript
window.renderChart(chartData, this.container);
```

Use a `dataviewjs` block, not a plain Dataview query, for API rendering. Validate queried values before placing them in labels or datasets, and keep the JavaScript limited to reading vault data and building the chart payload. Prefer emitting a native `chart` block from DataviewJS when its simpler schema is sufficient.

## Theming

Plugin settings can define chart colors. When the plugin's Theming option is enabled, CSS variables such as `--chart-color-1` can define palette entries. Do not add or change CSS snippets unless the owner requests that styling change; reuse existing vault theme variables where practical.

## Official documentation source

- Basic usage: `https://github.com/phibr0/obsidian-charts/blob/master/docusaurus/docs/Basic%20Usage.mdx`
- Chart types: `https://github.com/phibr0/obsidian-charts/tree/master/docusaurus/docs/Chart%20Types`
- Modifiers: `https://github.com/phibr0/obsidian-charts/blob/master/docusaurus/docs/Modifiers.mdx`
- Markdown tables: `https://github.com/phibr0/obsidian-charts/blob/master/docusaurus/docs/Chart%20from%20Table.mdx`
- Dataview integration: `https://github.com/phibr0/obsidian-charts/blob/master/docusaurus/docs/Dataview%20Integration.mdx`
- Customization: `https://github.com/phibr0/obsidian-charts/blob/master/docusaurus/docs/Customization.md`
