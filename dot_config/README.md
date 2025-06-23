# Step by step insatllation process

1. Loggin to AppStore so we can download apps from it
1. Create new ssh key based on github mail [link](https://github.com/flameshot-org/flameshot/issues/3572#issuecomment-2167705873)
1. Run sh -c `"$(curl -fsLS get.chezmoi.io)" -- init --apply git@github.com:dandudzi/dotfiles.git`
1. Download raw script that will checkout this repo [.dotfilesCheckout.sh](https://github.com/dandudzi/.dotfiles/blob/master/.dotfilesCheckout.sh)
1. Set up Github [gpg](https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key)
1. Apply `Vivaldi` theme from path `~/.config/vivaldi/`
1. Add wallpapers from path `~/.config/images/wallpapers`
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
        - `hide labels before click`
        - scroling shortcut `⌘+⇧+j`
        - enable `hyper`
        - eneble `Automatic scroll deactivation`
        - browser labele `fast`
    1. Raycast

## Issues

- [flameshot if cannot open on mac](https://github.com/flameshot-org/flameshot/issues/3572#issuecomment-2089076723)

# 🔨 other tools I use that I could forgot I can

1. `pinentry-mac`           -- use with gpg to provide passphrase
1. `LuaRocks`               -- use as package manager for Lua modules
1. `imagemagick`            -- software suite for converting, editing, and processing images
1. `pandoc`                 -- use for converting files between formats like markdow, pdf
1. `mas`                    -- Mac app store cli
1. `chafa`                  -- convert images to ASCII
