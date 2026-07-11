---
name: obsidian-tasks
description: Manage Markdown tasks with the Obsidian Tasks community plugin. Use for Tasks query blocks, recurrence, due dates, priorities, custom statuses, completion behavior, or safely toggling plugin-managed tasks.
---

# Obsidian Tasks

Confirm the plugin is enabled:

```bash
rtk obsidian plugin id=obsidian-tasks-plugin
```

## Work with tasks

- Inspect the exact source line and nearby context before changing it.
- Use `rtk obsidian tasks path="Note.md" todo format=json` to list incomplete checkboxes in one note with stable, structured output.
- Use `rtk obsidian task ref="Note.md:12" done` only for a plain checkbox when no recurrence, Done date, dependency, custom status, or `onCompletion` behavior applies.
- For plugin-managed completion, use the Tasks UI with the correct editor context or a reviewed integration with `apiV1.executeToggleTaskDoneCommand()`. The returned Markdown may include the next recurrence and must be applied atomically.

Author Tasks queries as fenced `tasks` blocks:

````markdown
```tasks
not done
due before tomorrow
sort by due
```
````

Preserve the vault's existing task format and metadata order. Verify the source file first, then the rendered query after Obsidian reindexes.

## Discover more

Run `rtk obsidian help tasks` and `rtk obsidian help task` for current CLI options. Run `rtk obsidian commands filter=obsidian-tasks-plugin` to discover commands exposed by the installed plugin; editor commands may still require an active cursor.
