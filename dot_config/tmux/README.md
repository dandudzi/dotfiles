# Codex attention workflow

This tmux feature tracks Codex panes that require attention, shows their count
as a clickable status pill, and lets you jump to a waiting pane either in queue
order or from a searchable dialog. It works across every tmux session.

## Homebrew dependencies

Install the three executables used by this configuration with Homebrew:

```sh
brew install tmux gum fzf
```

- `tmux` receives Codex's terminal bell, stores the waiting state, renders the
  status pill, and changes client/session/window/pane focus.
- `gum` renders the searchable waiting-pane picker opened by `Ctrl+Shift+K`.
- `fzf` renders the active-pane picker opened by `Ctrl+Shift+S`, including
  mouse selection.

The Codex CLI is the notification source: this feature recognizes panes whose
current command is `codex` or `codex-*`. Its installation is separate from the
three Homebrew dependencies above.

## Flow

1. Codex emits a terminal bell when a selected TUI notification needs input.
2. Tmux's `alert-bell` hook calls the helper with the emitting pane ID.
3. The helper confirms that pane is running Codex, sets its `@codex_waiting`
   pane option, and refreshes the global `@codex_waiting_count`.
4. The Catppuccin status module renders that count as the Codex pill at the
   left side of tmux's status line.
5. Selecting a waiting pane clears only that pane's waiting option and updates
   the count, so multiple panes remain independently actionable.

## Ways to react

| Action | Result | Implementation |
| --- | --- | --- |
| Click the Codex pill | Jump to the first waiting Codex pane. Other status clicks keep their normal behavior. | `tmux.conf` `MouseDown1Status` binding |
| `Ctrl+Shift+N` | Jump to the next waiting pane, clearing it from the queue. | `tmux.conf` and `codex-next-waiting.sh` |
| `Ctrl+Shift+K` | Open a 60% × 40% Gum popup listing `session:window.pane`; filter, select with `Enter`, and jump directly to that pane. Use arrow keys to move in the picker. | `tmux.conf` and `codex-next-waiting.sh --choose` |
| `Ctrl+Shift+S` | Open a 60% × 40% fzf popup listing every active `codex` or `codex-*` pane across all tmux sessions; filter, select with `Enter` or a left-click, and switch to that session, window, and pane. | `kitty.conf`, `tmux.conf`, and `codex-next-waiting.sh --choose-active` |

## Implementation map

| Live path | Responsibility |
| --- | --- |
| `~/.config/kitty/kitty.conf` | Removes Kitty's conflicting `Ctrl+Shift+S` binding so the active-picker shortcut reaches tmux. |
| `~/.config/tmux/tmux.conf` | Hooks, keyboard and mouse bindings, status placement, and initial count refresh. |
| `~/.config/tmux/scripts/codex-next-waiting.sh` | Counts, marks, clears, lists, chooses, and focuses waiting or active Codex panes. |
| `~/.config/tmux/status/codex_waiting.conf` | Catppuccin pill icon, colors, count text, and rounded-presentation settings. |
| `~/.config/tmux/tests/codex-active-picker.test.sh` | Regression coverage for the active-pane list, cross-session focus, shortcut wiring, Kitty pass-through, and left-click selection. |
| `~/.config/tmux/README.md` | This operational overview. |

These live files are persisted in chezmoi. Their managed source paths can be
resolved with `rtk chezmoi source-path <live-path>`; after an approved live
change, persist that exact file with `rtk chezmoi add <live-path>`.

## Operational notes

- Reload tmux after changing `tmux.conf` with `Prefix`, then `R`.
- The helper is executed from its live path on each action, so script-only
  changes take effect on the next action without a tmux reload.
- If no waiting pane exists, its picker remains open with an inert `No Codex pane needs attention` row.
- If no active Codex pane exists, the active-picker dialog remains open with an inert `No active Codex pane` row.
