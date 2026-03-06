# Step by step installation process

1. Loggin to AppStore so we can download apps from it
1. Copy from Bitwarden ssh public key to download dotfiles
   1. `touch id_ed25519.pub`
   1. `chmod 600 id_ed25519.pub`
   1. `pbpaste > id_ed25519.pub`
1. If work laptop run `mv .zshrc .zshrc_work`
1. Run `sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply --force dandudzi --ssh`
   1. During the installation pick if this is work laptop or not `y/n`
1. Open wezterm to finish installing command line tools
1. Sometimes `tmux` has an issue with installing dependencies then enter it and refresh `<c-b> -> <⇧+i>`
1. Enable in Bitwarden ssh agent
1. Apply `Vivaldi` theme from path `~/.config/vivaldi/`
1. Add wallpapers from path `~/.config/images/wallpapers`
1. `<⇧-⌘-.>` to show hidden files in files/finder
1. Set up `Night shift`
1. Unbind ⌘+⇧+a - `Keyboard settings -> Shortcuts -> Services -> Text -> Search Man Pages`
1. Disable work capitalization and adding period in the end `Keyboard settings -> Text Input -> Edit`
1. Load Intellij settings from `.config/idea`
1. Add `login items` in Mac
   1. Docker
   1. Flameshot
      - change `Capture Screen` shortcut to `⌘+⇧+x`
      - change `Main color`
   1. Caffeine
   1. Homerow
      - shortcut for clicking `⌘+⇧+space`
      - `immediate click`
      - search shortcut `hyper + /`
      - `hide labels before search`
      - scrolling shortcut `⌘+⇧+j`
      - enable `hyper`
      - eneble `Automatic scroll deactivation`
      - browser label `fast`
      - scroll speed 2nd from left
   1. Raycast
      - rebind `⌘ + space` - `Keyboard->Shortcuts->Spotlight`
      - enable hyper
      - add command script directory `/.config/scripts`
1. Install OpenLeaf for LED management

## Issues

- [flameshot if cannot open on mac help](https://github.com/flameshot-org/flameshot/issues/3572#issuecomment-2089076723)

# 🔨 other tools I use that I could forgot I can

1. `LuaRocks` -- use as package manager for Lua modules
1. `imagemagick` -- software suite for converting, editing, and processing images
1. `pandoc` -- use for converting files between formats like markdow, pdf
1. `mas` -- Mac app store cli
1. `chafa` -- convert images to ASCII
