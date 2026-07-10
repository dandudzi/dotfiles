# Kitty, tmux, and Neovim workflow review

Last researched: 2026-07-10

This is the living research, decision, and interview document for improving the
Kitty setup and evaluating a careful migration away from local tmux usage.

No configuration recommendation in this file is approved for implementation
until it has been discussed in the interview queue. Changes should be made one
small, reversible step at a time and verified before moving to the next item.

## Status legend

- `Observed`: verified in the current local configuration or effective runtime.
- `Documented`: verified against current upstream documentation.
- `Inference`: likely based on configuration, but needs confirmation from Daniel.
- `Decision needed`: must be answered before choosing an implementation.
- `Candidate`: a possible solution, not an approved change.
- `Completed`: approved, implemented, verified, and recorded below.

## Executive conclusions

1. **The current setup is tmux-first, not Kitty-first.** Kitty immediately runs
   `tmux new-session -A -s main`. Kitty is primarily the renderer and macOS
   window; tmux owns projects, windows, panes, scrollback, copy mode, navigation,
   status information, and live process persistence.

2. **Dropping tmux is not a single-line change.** It requires replacements for
   sesh, zoxide-backed project discovery, tmux popups, cross-Neovim navigation,
   copy mode, the status bar, the which-key menu, and detached processes.

3. **sesh cannot currently become the Kitty backend.** Installed sesh 2.26.2 is
   a tmux session manager. Native Kitty support is an open enhancement request,
   [sesh issue #393](https://github.com/joshmedeski/sesh/issues/393), not a
   released feature.

4. **The safest likely destination is hybrid.** Use Kitty-native windows,
   layouts, sessions, shell integration, and scrollback for local interactive
   work. Retain tmux only where live detached processes or remote persistence
   are genuinely needed.

5. **Neovim already contains part of the replacement.** LazyVim ships native
   split navigation, persistence.nvim sessions, project-aware pickers, and
   Snacks terminals. The only explicit Neovim-to-tmux dependency is
   `vim-tmux-navigator`, but replacing its edge-crossing behavior needs care.

6. **The migration must begin by learning actual behavior, not editing config.**
   The first interview must determine whether closing Kitty and reattaching to
   still-running processes is essential. Kitty session files restore structure
   and commands; they do not keep processes alive like a detached tmux server.

## Verified environment

| Component | Installed version or state |
| --- | --- |
| Kitty | 0.47.4, current stable as of this review |
| tmux | 3.7b |
| Neovim | 0.12.4 |
| LazyVim | generation/version 8, current commit pinned in `lazy-lock.json` |
| sesh | 2.26.2 |
| fzf | 0.74.0 |
| Shell | zsh with Oh My Zsh, Spaceship, vi-mode, fzf-tab, and zoxide |
| Terminal theme | Catppuccin Macchiato across Kitty, tmux, and shell |

Kitty parsed the current configuration with zero bad lines.

## Current architecture

```text
macOS
└── Kitty OS window
    └── tmux server/session: main
        ├── tmux sessions selected by sesh
        │   ├── configured sessions from sesh.toml
        │   ├── active tmux sessions
        │   └── zoxide directories
        ├── tmux windows selected by Cmd+1 through Cmd+9
        └── tmux panes
            ├── zsh + fzf-tab tmux popup
            ├── Neovim + vim-tmux-navigator
            ├── Yazi
            ├── tests/builds/servers (needs interview confirmation)
            └── SSH/other commands (needs interview confirmation)
```

### Ownership today

| Concern | Current owner |
| --- | --- |
| Top-level GUI window | Kitty |
| Project/session namespace | sesh + tmux + zoxide |
| Terminal windows/tabs/panes | tmux |
| Pane layouts and resizing | tmux |
| Live detach/reattach | tmux |
| Shell history | zsh |
| Terminal history and selection | tmux copy mode, with some Kitty fallback |
| Editor buffers and editor layout | Neovim + persistence.nvim |
| Cross-editor/pane navigation | vim-tmux-navigator on both sides |
| Shell completion UI | fzf-tab in a tmux popup |
| Rendering, fonts, colors, macOS integration | Kitty |

## Detailed local findings

### Kitty

Source: [kitty.conf](./kitty.conf)

- `shell tmux new-session -A -s main` means every normal Kitty window attaches
  to the same tmux session.
- `tab_bar_style hidden` is coherent with tmux owning windows, but it will hide
  important context if Kitty tabs later become projects or workspaces.
- `Cmd+1` through `Cmd+9` send raw `Ctrl+B` plus a number to tmux. These mappings
  must be redesigned if Kitty tabs or sessions replace tmux windows.
- `shell_integration enabled` is present, but Kitty launches tmux rather than
  zsh. Automatic zsh integration is therefore not injected into the zsh shells
  created by tmux.
- `scrollback_lines 10000` is secondary while tmux owns a 50,000-line history.
  It becomes important once zsh/Neovim run directly under Kitty.
- `allow_remote_control no` is a good secure default. Some seamless
  Kitty/Neovim navigation candidates require a socket and remote control, so
  their permissions must be reviewed before adoption.
- `confirm_os_window_close 0` is relatively safe while tmux keeps processes
  alive. Without tmux it can close active local processes without confirmation.
- `background_opacity 0.9` is active, while the nearby comment saying Kitty has
  no native blur is obsolete. Current Kitty supports `background_blur`.
- `text_composition_strategy 0.1 0` is much thinner/lower contrast than the
  current macOS platform default and should be visually reviewed.
- The file contains a generated commented default template from line 109 to the
  end, with active settings buried inside it. It should eventually be reduced
  to intentional settings plus small includes, but cleanup should happen only
  after behavior has been captured.

Useful features already available without configuration changes:

- `Ctrl+Shift+F3`: Kitty command palette; `F12` toggles unmapped actions.
- `Ctrl+Shift+E`: open a visible URL with hints.
- `Ctrl+Shift+P`, then `F`: insert a visible path.
- `Ctrl+Shift+P`, then `N`: open a visible `path:line` location.
- `Ctrl+Shift+P`, then `C` or `D`: choose a file or directory.
- `Ctrl+Shift+H`: show Kitty scrollback. Its usefulness is limited while tmux
  controls the pane history.

### tmux

Source: [tmux.conf](../tmux/tmux.conf)

The effective configuration was inspected in a temporary isolated tmux server,
without touching the live session.

Observed responsibilities:

- 50,000-line history and vi-style copy mode.
- System clipboard integration through `set-clipboard`, tmux-yank, and `pbcopy`.
- Splits preserving `pane_current_path`.
- Mouse selection, scrolling, pane selection, border dragging, and resizing.
- Extended keys, focus events, hyperlinks, passthrough, true color, and titles.
- Catppuccin status bar showing application, session, directory, user, and host.
- Prefix highlighting to show copy/prefix state.
- tmux-which-key on `Prefix+Space` as a discoverability layer.
- tmux-fzf and sesh project/session selectors.
- `Ctrl+h/j/k/l` navigation that detects Neovim/fzf and either forwards the key
  or moves to another tmux pane.
- `Cmd+1` through `Cmd+9` from Kitty ultimately select tmux windows 1 through 9.
- `detach-on-destroy off` and `destroy-unattached off` keep sessions/processes
  alive after the terminal client goes away.

Important nuance: tmux-resurrect and tmux-continuum are not configured. The
current setup preserves live processes after closing/detaching Kitty, but does
not restore those live processes across a machine reboot.

### sesh and project switching

Sources: [sesh.toml](../sesh/sesh.toml),
[tmux.conf](../tmux/tmux.conf), and [command.zsh](../zsh/command.zsh)

Observed entry points:

- `Prefix+j`: large fzf selector combining active tmux sessions, configured
  sessions, zoxide directories, and filesystem search.
- `Prefix+k`: smaller gum-based session picker.
- `Prefix+r`: switch to the last sesh session.
- `Alt+s` from zsh vi insert/command/emacs maps: run `sesh-sessions`.

Configured sessions:

| Name | Path/command | Migration note |
| --- | --- | --- |
| Downloads | `~/Downloads`, starts `yazi` | Easy Kitty session candidate; native Kitty graphics may improve previews |
| Config | starts shell alias `econfig` | Kitty session must use the expanded chezmoi command or an interactive zsh; aliases are not executables |
| Vim Kata | fixed exercise directory, starts `nvim` | Easy Kitty session candidate; pair with Neovim persistence only if desired |

sesh also exposes more projects than these three because it combines zoxide and
active tmux sessions. Replacing only the three static entries would remove the
current frecency-based project workflow.

Current upstream status:

- sesh is explicitly a smart **tmux** session manager.
- Native Kitty integration is not released; issue #393 is open and assigned.
- A migration therefore needs either Kitty session files, a Kitty-native
  zoxide/fzf wrapper, a Neovim project picker, or a combination of them.

### zsh and fzf

Sources: [init.zsh](../zsh/init.zsh), [fzf.zsh](../zsh/fzf.zsh),
[fzf-git.sh](../zsh/fzf-git.sh), and [command.zsh](../zsh/command.zsh)

- `fzf-tab` is explicitly configured to run `ftb-tmux-popup`. This must change
  before tmux is removed or shell completion presentation will break/change.
- fzf-git calls `fzf --tmux 90%,70%`. Modern fzf can fall back outside tmux,
  but the resulting layout and behavior must be tested.
- The shell has direct fzf workflows for files, directories, Git, history, and
  sesh. Kitty `choose-files` overlaps some file/directory use cases, but should
  not automatically replace familiar shell workflows.
- `KITTY_CONFIG_DIRECTORY` is assigned the path to `kitty.conf`, but Kitty
  expects a directory. It is not exported and is currently mostly inert.
- zsh vi-mode and a custom `zle-keymap-select` function manage cursor shape.
  Any manual Kitty shell integration inside tmux should use `no-cursor` to avoid
  two cursor managers. After direct zsh launch, this still needs a conflict test.
- zoxide is initialized late in the shell configuration and is central to the
  dynamic project list consumed by sesh.

### Neovim and LazyVim

Sources: [lazyvim.json](../nvim/lazyvim.json),
[options.lua](../nvim/lua/config/options.lua),
[keymaps.lua](../nvim/lua/config/keymaps.lua), and
[tmux-navigator.lua](../nvim/lua/plugins/tmux-navigator.lua)

Observed behavior:

- LazyVim's picker is explicitly set to fzf-lua.
- Both the fzf and Snacks picker extras are selected, but the explicit picker
  setting makes fzf-lua the primary LazyVim picker. This overlap should be
  reviewed separately rather than changed as part of the tmux migration.
- `vim-tmux-navigator` replaces LazyVim's native `Ctrl+h/j/k/l` window mappings.
- Removing `vim-tmux-navigator` would reveal LazyVim's native mappings:
  `Ctrl+h/j/k/l` -> `<C-w>h/j/k/l` inside Neovim.
- LazyVim already configures terminal-mode `Ctrl+h/j/k/l` navigation for
  non-floating Snacks terminal windows.
- LazyVim provides Snacks terminals:
  - `<leader>ft`: terminal rooted at the project root.
  - `<leader>fT`: terminal at Neovim's current working directory.
  - `Ctrl+/`: toggle the root terminal.
- persistence.nvim is installed and saves buffers, Neovim window arrangement,
  current directory, tabs, help windows, globals, and folds.
- Existing persistence mappings:
  - `<leader>qs`: restore the current-directory session.
  - `<leader>qS`: select a session.
  - `<leader>ql`: restore the last session.
  - `<leader>qd`: stop saving the current session.
- LazyVim project root detection prefers LSP roots, then `.git`/`lua`, then cwd.
  Kitty must launch Neovim in the correct project directory for persistence and
  pickers to select the intended project state.
- LazyVim checks changed files on `FocusGained`, which pairs well with native
  Kitty window focus events.

Potential division of responsibility after migration:

| State | Suggested owner |
| --- | --- |
| Live terminal processes | Kitty while open; optional tmux for persistent jobs |
| Terminal window/tab layout | Kitty sessions/layouts |
| Project directory | Kitty session or project launcher |
| Editor buffers and editor splits | persistence.nvim |
| Short-lived shell inside editor | Snacks terminal |
| Long-running build/server | separate Kitty window, or retained tmux if detachment is required |

Avoid asking Kitty session restore and persistence.nvim to own the same editor
layout. Kitty should launch one Neovim process in the correct cwd;
persistence.nvim should restore editor-internal state.

## Migration dependency matrix

| Capability | Current implementation | Candidate replacement | Risk or open question |
| --- | --- | --- | --- |
| Live process survival after closing Kitty | detached tmux server | retain a small tmux use case, or accept process termination | Critical interview question |
| Restore after reboot | not currently provided for live processes | Kitty session files + persistence.nvim restart commands/state | Restarts processes; does not resume them |
| Dynamic project discovery | sesh + zoxide + fzf | custom zoxide/fzf Kitty launcher; possibly Snacks projects | No released sesh Kitty backend |
| Static project layouts | sesh startup commands + tmux | Kitty `.kitty-session` files | Straightforward |
| Project switching | tmux sessions | Kitty `goto_session`, OS windows, tabs, or custom launcher | Must choose project namespace model |
| Last project | `sesh last` | `goto_session -1` or launcher history | Kitty history covers Kitty sessions, not arbitrary zoxide dirs |
| Terminal splits | tmux panes | Kitty `splits` layout | Keymap and navigation redesign |
| Working-directory inheritance | tmux `pane_current_path` | Kitty shell integration + `new_window_with_cwd` | Requires direct/working shell integration |
| Neovim/terminal edge navigation | vim-tmux-navigator | smart-splits.nvim Kitty integration or a smaller custom bridge | Remote-control permissions and current plugin edge cases |
| Pane resizing | tmux keys/mouse | Kitty resize mode, split actions, mouse border drag | Exact preferred keys unknown |
| Pane zoom | tmux `Prefix+z` | Kitty stack/toggle layout or split maximize | Behavior is similar, not identical |
| Copy mode | tmux vi copy mode + tmux-yank | Kitty scrollback pager, hints, native selection, optional kitty-scrollback.nvim | Need to learn actual copy/search habits |
| Long scrollback | tmux 50k history | Kitty scrollback lines and/or pager history | Memory, search, and editor preference |
| Status bar | Catppuccin tmux status | Kitty tab bar/title/session name; optional custom tab bar | Which status fields are truly used? |
| Which-key discovery | tmux-which-key | Kitty command palette | Command palette is global Kitty actions, not a hierarchical clone |
| Shell completion popup | ftb-tmux-popup | normal fullscreen/height fzf-tab UI or another overlay | Appearance and ergonomics change |
| Fuzzy project/file selection | fzf/sesh | keep fzf, Kitty choose-files, Snacks projects, or combine | Avoid replacing familiar workflows unnecessarily |
| Cmd+number switching | raw tmux prefix+number | `goto_tab`, `nth_window`, or session selection | Depends on project namespace decision |
| Remote SSH persistence | tmux over SSH | retain remote tmux; optionally use `kitten ssh` around it | Kitty sessions are not a remote daemon |
| Clipboard across local/SSH | tmux set-clipboard + yank | Kitty clipboard protocol/OSC 52 with ask policy | Test through remote tmux if retained |
| Yazi images | tmux passthrough | native Kitty graphics | Likely improves after removing local tmux |

## Candidate target architectures

### Candidate A: hybrid local Kitty, tmux only for persistence

```text
Kitty session/project
├── Neovim window (persistence.nvim owns editor state)
├── local shell/test window
├── local server/log window when termination is acceptable
└── optional tmux window only for a job or remote host that must detach
```

Advantages:

- Unlocks Kitty graphics, shell integration, scrollback, hints, sessions, drag
  and drop, modern keyboard handling, and native layouts.
- Preserves tmux where its process daemon is actually valuable.
- Supports gradual migration and an immediate rollback path.

Costs:

- Two models remain, although no longer nested for every local command.
- Project switching must know how to focus Kitty sessions and persistent tmux
  jobs separately.

This is the current research recommendation, subject to interview answers.

### Candidate B: fully Kitty-native local workflow

Use Kitty OS windows or sessions as projects, Kitty tabs/windows as process
groups, persistence.nvim for editor state, and Snacks terminals for short-lived
editor-adjacent shells.

Advantages:

- Simplest terminal stack and best protocol compatibility.
- No tmux plugins, status, key tables, passthrough, or nested scrollback.

Costs:

- Closing Kitty terminates local processes.
- sesh cannot be reused as-is.
- Cross-Neovim/Kitty navigation needs a new integration.
- A project launcher must replace the zoxide/sesh experience.

### Candidate C: retain current tmux-first workflow and improve Kitty around it

Keep tmux as the main workspace manager, manually enable Kitty shell integration
inside zsh, add a direct-zsh quick-access terminal, and use Kitty hints/SSH/file
transfer where passthrough permits.

This gains productivity with the least risk but does not achieve the goal of
removing local tmux.

## Project namespace models to discuss

Kitty provides several layers, and choosing the wrong one will recreate the
current duplication.

### Model 1: one Kitty OS window per project

- Closest to a desktop workspace.
- Kitty sessions naturally map to OS windows.
- macOS window switching and Mission Control become part of navigation.
- `goto_session` can focus/switch project sessions.

### Model 2: one Kitty tab per project inside one OS window

- Closest to tmux sessions/windows in one terminal.
- Requires a visible or searchable tab/session UI.
- `tab_bar_filter` can show only tabs for the active Kitty session.
- Cmd+number can select tabs.

### Model 3: one Kitty session per project with multiple tabs/windows

- Best for projects with editor, server, test, and log roles.
- Can save or hand-author structured `.kitty-session` files.
- Needs a clear decision about whether switching sessions hides, closes, or
  leaves other project processes running.

The interview must establish how Daniel mentally distinguishes a **project**, a
tmux **session**, a tmux **window**, and a tmux **pane** today.

## Neovim navigation candidates

### Candidate: remove cross-terminal navigation

Remove `vim-tmux-navigator`; allow LazyVim's native `Ctrl+h/j/k/l` mappings to
operate only inside Neovim. Use different Kitty shortcuts for Kitty windows.

- Lowest complexity and smallest security surface.
- Changes muscle memory at Neovim edges.

### Candidate: smart-splits.nvim with Kitty

Current smart-splits.nvim supports Kitty, Neovim, tmux, WezTerm, and Zellij. It
sets a Kitty user variable while Neovim is focused so conditional Kitty mappings
can pass `Ctrl+h/j/k/l` into Neovim; at an editor edge it asks Kitty to focus a
neighboring window.

Risks to evaluate before adoption:

- Requires a Kitty listening socket and remote-control permissions.
- Password/action restrictions must be used instead of casually enabling
  unrestricted global control.
- Kitty edge/wrap behavior differs by layout.
- A May 2026 issue reports edge/split behavior regressions in smart-splits 2.1;
  the exact installed version should be chosen and tested deliberately.
- Remote Neovim navigation requires `kitten ssh`, socket forwarding, matching
  configuration on the host, and trust in that host.

Source: [smart-splits.nvim](https://github.com/mrjones2014/smart-splits.nvim).

### Candidate: custom minimal bridge

Use Kitty conditional mappings plus a small Neovim Lua function that moves
inside Neovim and only asks Kitty to focus a neighbor at an editor edge.

- Smaller dependency surface.
- Becomes custom code we must own, test, and secure.

No navigation candidate is approved yet.

## Earlier Kitty productivity findings retained

Phase 1 covers only improvements that leave the tmux-first architecture intact:

1. **Completed:** replace the generated 3,000-line Kitty template with a small,
   annotated configuration while preserving every active directive.
2. Learn the Kitty command palette and current hint shortcuts.
3. Try `kitten ssh`, keeping transfer confirmation and clipboard-read prompts.
4. Consider native blur and review the unusually thin text composition setting.
5. Keep `allow_remote_control no` throughout Phase 1.

The following earlier findings are deliberately deferred until a Phase 2
profile launches zsh directly instead of tmux:

- Enable and verify Kitty shell integration.
- Add long-command notifications after prompt marks work.
- Configure a direct-zsh macOS quick-access terminal.
- Revisit close confirmation using Kitty's knowledge of active commands.

## Proposed migration stages

These stages are a research sequence, not authorization to implement them.

### Stage 0: interview and baseline

- Answer the interview queue below one question at a time.
- Record daily entry points, project topology, and persistence expectations.
- Capture current shortcuts that must survive.
- Define rollback and acceptance tests.

### Stage 1: improvements that do not remove tmux

- Compact and annotate `kitty.conf` without changing effective behavior.
- Learn command palette/hints.
- Review `kitten ssh` and tmux-independent visual settings one at a time.
- Keep tmux startup and remote-control policy unchanged.

### Stage 2: one experimental Kitty-native project

- Keep the normal Kitty startup unchanged.
- Launch a separate experimental Kitty instance/profile without automatic tmux.
- Enable shell integration, notifications, direct-zsh quick access, and
  command-aware close safety only within the direct-zsh workflow.
- Recreate one low-risk project, likely Vim Kata or Downloads.
- Test zsh, Neovim, Yazi, clipboard, scrollback, fzf-tab, window creation, and
  closing behavior.

### Stage 3: navigation and project switching

- Choose native-only navigation or a reviewed Kitty/Neovim bridge.
- Replace sesh for the experiment with Kitty sessions and/or zoxide/fzf.
- Decide OS-window versus tab versus session project namespaces.
- Rebuild Cmd+number and last-project switching.

### Stage 4: persistence boundary

- Classify processes into disposable, restartable, and must-remain-live.
- Move disposable/restartable work to Kitty-native windows.
- Keep tmux only for must-remain-live or remote work if any exists.

### Stage 5: make Kitty-native local work the default

- Remove automatic tmux startup only after the experimental profile passes.
- Keep a separate explicit command/profile for persistent tmux work.
- Remove unused tmux plugins and Neovim integration only after rollback period.
- Remove any transitional Kitty settings only after the rollback period.

## Acceptance tests for a tmux-free local profile

- New terminal starts direct zsh with full shell integration.
- zsh vi-mode cursor remains correct.
- fzf-tab completion works and remains readable without a tmux popup.
- fzf history, files, directories, and fzf-git work.
- Yazi previews and returns the selected directory correctly.
- Neovim starts in the intended project root.
- `<leader>qs`, `<leader>qS`, and `<leader>ql` restore the expected editor state.
- `Ctrl+h/j/k/l` behavior matches the chosen navigation model.
- New Kitty windows inherit cwd locally and over the chosen SSH workflow.
- Clipboard copy/paste works in shell, Neovim, Yazi, and SSH.
- Scrollback search/copy can replace the actually used tmux copy-mode actions.
- Project picker covers configured projects, zoxide projects, active projects,
  last-project switching, and project closing.
- Closing one window, one project, and the entire app each have understood and
  safe process behavior.
- A long build/server is either deliberately terminated, automatically
  restartable, or placed in the retained persistence layer.

## Interview queue

We will ask these one at a time. Answers and decisions should be recorded in
the decision log.

### 1. Process persistence — first question

When you close all Kitty windows or detach from tmux, do you expect commands,
servers, editors, SSH connections, or agent sessions to keep running so you can
reattach later? Which processes have you actually recovered this way in the
last few weeks?

Why this is first: it determines whether fully removing tmux is realistic or a
hybrid persistence boundary is required.

### 2. Project mental model

What does one tmux session represent: a repository, a task, a client, a broad
context, or something else? What do tmux windows and panes represent inside it?

### 3. Daily entry points

Which do you use and how often: opening Kitty, `Prefix+j`, `Prefix+k`, `Alt+s`,
`Prefix+r`, Cmd+number, `ta`, `ts`, or other commands?

### 4. Typical project topology

For a normal coding project, which panes/windows do you create: Neovim, shell,
tests, dev server, logs, database, AI agent, SSH, Yazi, or something else?

### 5. Navigation muscle memory

Must `Ctrl+h/j/k/l` move seamlessly from a Neovim split into an adjacent
terminal split, or would separate Kitty and Neovim navigation keys be acceptable?

### 6. Copy mode and scrollback

How do you search, select, and copy old output today? Which tmux copy-mode keys
are used beyond entering with `Prefix+v`, selecting with `v`, and copying with
`y`?

### 7. Status bar value

Which tmux status fields do you actually read: session, window name, current
command, directory, prefix state, user, host, or something else?

### 8. Popup behavior

Is the tmux-popup presentation of fzf-tab, sesh, tmux-fzf, and which-key
important, or is a Kitty overlay/full-window picker acceptable?

### 9. Remote workflow

Which hosts use SSH, whether remote tmux is required, whether sessions survive
network drops, and whether using `kitten ssh` is acceptable.

### 10. Project restoration

Should switching to a project merely open the correct directory, restore the
Neovim buffers/layout, start known commands, or restore an exact multi-process
workspace?

### 11. macOS window model

Would one macOS Kitty window per project fit Mission Control and Cmd+Tab habits,
or should all projects remain inside one Kitty OS window as tabs/sessions?

### 12. Close safety

Should Kitty warn before closing windows with a running command once tmux no
longer protects those processes?

## Decision log

| Date | Topic | Decision | Evidence/answer | Implementation status |
| --- | --- | --- | --- | --- |
| 2026-07-10 | Phase ordering | Finish tmux-independent Kitty recommendations before starting the tmux replacement experiment | Daniel explicitly separated the work into Phase 1 and Phase 2 | Recorded |
| 2026-07-10 | Direct-zsh features | Defer shell integration, notifications, quick access, and command-aware close behavior until Phase 2 | These features should be evaluated after switching the experimental profile away from tmux | Deferred to Phase 2 |
| 2026-07-10 | Kitty config cleanup | Use one compact annotated `kitty.conf`; retain the separate theme include and every active value | Zero bad lines before and after; normalized effective directives match | Completed |
| 2026-07-10 | Initial architecture | Pending interview | Research completed; no architecture change | Not started |

## Sources

Primary/current sources used for this research:

- [Kitty configuration](https://sw.kovidgoyal.net/kitty/conf/)
- [Kitty shell integration](https://sw.kovidgoyal.net/kitty/shell-integration/)
- [Kitty sessions](https://sw.kovidgoyal.net/kitty/sessions/)
- [Kitty layouts](https://sw.kovidgoyal.net/kitty/layouts/)
- [Kitty remote control](https://sw.kovidgoyal.net/kitty/remote-control/)
- [Kitty changelog](https://sw.kovidgoyal.net/kitty/changelog/)
- [LazyVim general configuration](https://www.lazyvim.org/configuration/general)
- [LazyVim utility plugins](https://www.lazyvim.org/plugins/util)
- [vim-tmux-navigator](https://github.com/christoomey/vim-tmux-navigator)
- [smart-splits.nvim](https://github.com/mrjones2014/smart-splits.nvim)
- [sesh](https://github.com/joshmedeski/sesh)
- [Open sesh native Kitty request](https://github.com/joshmedeski/sesh/issues/393)

Context7 and Exa were both used to verify current documentation and upstream
state. Local effective tmux and Neovim configuration was inspected in addition
to reading the source files.
