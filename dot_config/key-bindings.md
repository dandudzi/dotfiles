
# 🛠️Tools

`git-open`              -- to open remote repository
`onefetch`              -- info about git repository
`fv`                    -- search and open file in vim
`fp`                    -- copy pwd of the file
`fls`                   -- list files in directory
`cx`                    -- go to directory and list files
`⇧ + ⌘ + X`             -- take screenshot
`y`                     -- file manager
`gitstat`               -- summary of the git repository
`cd -`                  -- previous directory
`z foo<Space><⇥>`       -- show interactive completions

# 🚀 Raycast

`⌘ + Space`             -- open raycast
`⌥ + M`                 -- open llm
`✦ + ;`                 -- open snippets
`✦ + V`                 -- open vivaldi
`✦ + W`                 -- open wezterm
`⌃ + ⌘ + Space`         -- search emoji
`⇧ + ⌘ + V`             -- clipboard
`✦ + M`                 -- maximize screen
`⌃ + ⌥ + ⌘ + M`         -- almost maximize screen
`⌃ + ⌥ + ⌘ + C`         -- center
`⌃ + ⌥ + ⌘ + ←`         -- move left 1/3 2/3
`⌃ + ⌥ + ⌘ + →`         -- move right 1/3 2/3
`✦ + L`                 -- open Music app
`✦ + D`                 -- open Discord
`✦ + I`                 -- open Intellij
`✦ + ↑`                 -- volume up
`✦ + ↓`                 -- volume down
`✦ + T`                 -- start timer
`✦ + R`                 -- manage reminders
`✦ + Q`                 -- dismiss timer
`✦ + X`                 -- search via DuckDuck
`✦ + E`                 -- open sesh session
`✦ + N`                 -- open notes
`✦ + 1`                 -- connect with speakers bia bluetooth
`✦ + O`                 -- open VS code
`✦ + A`                 -- ask about webpage
`✦ + 2`                 -- ask music
`⌃ + ⌥ + ⌘ + L`         -- open download folder

# 🌐 Vivaldi

`⌥ + C`                 -- copy link
`⌃ + P`                 -- toggle UI
`⌃ + ⇧ + <1-9>`         -- pick workspace
`⌘ + E`                 -- quick commands
`⌥ + ⌘ + B`             -- open bookmark panel
`⌘ + B`                 -- create bookmark
`⌥ + ⌘ + H`             -- open history panel
`⌥ + ⌘ + K`             -- cycle tab back
`⌥ + ⌘ + J`             -- cycle tab forward
`⌘ + Z`                 -- reopen closed tab
`⌃ + ⇧ + <1-9>`         -- switch to workspace

# 🔍 Bindings

`⌃ + R`                 -- Search command history
`⌃ + T`                 -- Fuzzy find files
`⌃ + E`                 -- Fuzzy find directories

# 📺 Tmux bindings

⚠️ here bindings size matter

`sesh-sessions`         -- list sesh-sessions
`esc + s`               -- in terminal to list tmux sessions

`⌃ + b` → `x`             -- close pane
`⌃ + b` → `d`             -- close current session
`⌃ + b` → `|`             -- split horizontally
`⌃ + b` → `-`             -- split vertically
`⌃ + b` → `v`             -- toggle visual mode
  → `gl`                -- move to end of line
  → `gh`                -- move to start of the line
  → `v`                 -- toggle visual selection
    → `y`               -- yank what selected
`⌃ + <h/j/k/l>`         -- move between panes
`⌃ + b` → `<H/J/K/L>`     -- resize pane
`⌃ + b` → `⌃ + s`         -- save session
`⌃ + b` → `⌃ + r`         -- restore session
`⌃ + b` → `space`         -- which key
`⌃ + b` → `s`             -- change session
`⌃ + b` → `c`             -- create new window
`⌃ + b` → `<1-9>`         -- move to window
`⌃ + b` → `k`             -- open sesh dialog
`⌃ + b` → `j`             -- open sesh preview
`⌃ + b` → `r`             -- open previous session

# 📋 move fzf-tabs

`,` `.`                   -- switch left right fzf groups

# 🌲 git repo search

`⌃ + g` → `B`             -- search for Branches
`⌃ + g` → `E`             -- search for `git for-each-ref`
`⌃ + g` → `F`             -- search for Files
`⌃ + g` → `H`             -- search for commit Hashes
`⌃ + g` → `L`             -- search for refLogs
`⌃ + g` → `R`             -- search for Remotes
`⌃ + g` → `S`             -- search for Stashed changes
`⌃ + g` → `T`             -- search for Tags
`⌃ + g` → `W`             -- search for Worktrees

# 🐁 install developer dependencies and tools

 `mise use --global node@22`     -- use global
 `mise use node@2`               -- create in directory mise.toml file and install dependency if not installed
 `mise install`                  -- installs everything specified in mise.toml
 `mise upgrade`                  -- upgrade tools and respec the version prefix node@22 will not bump to node
 `mise upgrade --bump node`      -- will upgrade tools to the latest available version
 `mise rm node@22`               -- remove node
 `mise ls`                       -- list installed tools
 `mise ls-remote node`           -- list remote tools versions

# ♻️ direnv can load and unload environment variables depending on the current directory

`echo export FOO=foo > .envrc`   -- creates file in directory that will be loaded
`direnv allow .`                   -- allow to load the .envrc if we trust it, by default disabled

# 📱to consider

𐂷 pstree               -- shows process in tree like
⍙ delta                -- to find diff between to files
🪵 [logfiles analyzer](https://docs.lnav.org)
🙈 [json manipulator](https://jqlang.org/)
👨 devtools -- for different part of manipulation
🌐 [httpie](https://httpie.io/cli) -- network tool ⚠️  need to install
📗 [mactex](https://www.tug.org/mactex/) -- if you like to write in latex ⚠️ need to install
🚄 [bench](https://github.com/Gabriella439/bench) -- better time for commands ⚠ need to instal
📅 [meeting reminder](https://www.inyourface.app/)
📸 [image manipulation](https://imagemagick.org)
🌐 [wire shark](https://www.wireshark.org)
🪈 [pipeviewer](https://www.ivarch.com/programs/pv.shtml) --used to monitor the progress of data through a pipeline  
💽 [postgresql cli](https://www.pgcli.com)
📦 [kubernetes cli](https://k9scli.io)
💽 [database tool - DBeaver](https://dbeaver.io)
