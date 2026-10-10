
`sketchybar --load-font "Symbols Nerd Font"` to initilize fonts that are not default one during the installation

Copy and modified based on the [FelixKratz](https://github.com/FelixKratz/dotfiles/tree/master/.config/sketchybar) dotiles

The Codex pill after the active app shows the same attention count as tmux,
including zero. It refreshes every two seconds, on startup, and after wake.
Left-click jumps to the first waiting pane through the most recently active
attached tmux client, clears its notification, and brings Kitty forward.
With no waiting pane or attached client, clicking does nothing.
