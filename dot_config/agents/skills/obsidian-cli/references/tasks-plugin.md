# Tasks Plugin

Use this reference when Tasks is enabled. Verify first:

```bash
rtk obsidian plugin id=obsidian-tasks-plugin
rtk obsidian tasks todo format=json
```

## Distinguish Core CLI from Tasks Semantics

The CLI `tasks` and `task` commands inventory and change Markdown checkbox statuses. They do not promise Tasks-plugin behavior such as recurrence generation, Done dates, dependencies, custom status transitions, or `onCompletion`.

Use core CLI mutation only for a plain checkbox whose only intended change is the status character and when Tasks plugin settings cannot add completion behavior. If the relevant plugin settings are unknown, use Tasks semantics instead. Re-query immediately before using a `path:line` reference.

For recurring or metadata-rich tasks, use the Tasks plugin UI or its API. Tasks 8.x exposes:

```typescript
interface TasksApiV1 {
  createTaskLineModal(): Promise<string>;
  editTaskLineModal(taskLine: string): Promise<string>;
  executeToggleTaskDoneCommand(line: string, path: string): string;
}
```

Access it from plugin code through `app.plugins.plugins["obsidian-tasks-plugin"].apiV1`. `executeToggleTaskDoneCommand` returns transformed Markdown that respects recurrence and completion preferences and may contain both the completed task and its next recurrence. Preview the result, re-read the source, abort if it changed, and apply an authorized exact-line replacement atomically while preserving indentation and newline style. A reviewed plugin should use Obsidian's collision-aware file processing. Do not invoke the API through arbitrary CLI `eval` during routine vault work. Build a narrow helper/plugin if programmatic completion becomes frequent.

The plugin's editor commands include `edit-task` and `toggle-done`, but editor-context commands may not appear in `obsidian commands` or execute deterministically without an active editor and cursor. Discover namespaced command IDs at runtime rather than hardcoding them. Prefer manual UI completion when exact editor and cursor context cannot be established safely.

## Author Task Lines

Preserve the configured task format and token order. Do not convert Emoji-format tasks to Dataview-format tasks, or vice versa, without an explicit vault-wide migration.

Common Emoji-format example:

```markdown
- [ ] Prepare import report 🔁 every week 📅 2026-07-18
```

Do not invent recurrence rules, IDs, dependencies, priorities, or dates. Preserve unknown metadata when editing the description.

## Author Query Blocks

Tasks queries are fenced `tasks` blocks rendered by the plugin:

````markdown
```tasks
not done
due before tomorrow
sort by due
```
````

An empty `tasks` block queries the whole vault. Add narrow filters deliberately. Boolean combinators `AND`, `OR`, and `NOT` remain uppercase. Add `explain` while debugging a query, then remove it only if requested.

CLI and `rg` can inspect query source but cannot evaluate the rendered result. Validate by opening the note in Obsidian with Tasks enabled.

## Complete Safely

1. Read the exact source line and surrounding task context.
2. Determine whether it is recurring, dependent, custom-status, or configured for completion dates.
3. For plain tasks, use `rtk obsidian task ref="<path>:<line>" done` and verify.
4. For plugin-semantic tasks, use Tasks UI or a reviewed API integration.
5. If `onCompletion` may delete, archive, or move content, require explicit authorization for those side effects.
6. Verify the source file directly first, then re-query after the Obsidian index catches up. Check the completed line, Done date, next recurrence, dependencies, and any affected paths.

Sources: [Tasks queries](https://publish.obsidian.md/tasks/Queries/About+Queries), [status behavior](https://publish.obsidian.md/tasks/Editing/Toggling+and+Editing+Statuses), and [Tasks API](https://publish.obsidian.md/tasks/Advanced/Tasks+Api).
