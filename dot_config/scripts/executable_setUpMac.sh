#!/bin/bash

echo '⌚️ Configuring your mac. Hang tight.'
# More options can be found [here](https://www.defaults-write.com/?s=wvous-bl-corner)

# Close System Preferences just in case
osascript -e 'tell application "System Preferences" to quit'

# Enable tab in modal dialogs - tab works everywhere
defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

# Scrollbars visible when scrolling
defaults write NSGlobalDomain AppleShowScrollBars -string "WhenScrolling"

# Expand save panel by default - when picking directory to save
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode -bool true
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode2 -bool true

# Disable the “Are you sure you want to open this application?” dialog
defaults write com.apple.LaunchServices LSQuarantine -bool false

# Reveal IP address, hostname, OS version, etc. when clicking the clock in the login window
sudo defaults write /Library/Preferences/com.apple.loginwindow AdminHostInfo HostName

# Set minimal autohide/show delay for hidden dock
defaults write com.apple.dock autohide-delay -float 0
defaults write com.apple.dock autohide-time-modifier -float 0.5

# Automatically hide and show the Dock
defaults write com.apple.dock autohide -bool true

# Make Dock icons of hidden applications translucent
defaults write com.apple.dock showhidden -bool true

# make cursor running faster
defaults write -g KeyRepeat -int 1
defaults write -g InitialKeyRepeat -int 20

# disable smart quotes - converstion from straight to currly quotes -> better for coding
defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false

# prevent from converting double hypnes -- to dash
defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false

# Show indicator lights for open apps in Dock
defaults write com.apple.dock show-process-indicators -bool true

# Hot corners
# # Possible values:
# #  0: no-op
# #  2: Mission Control
# #  3: Show application windows
# #  4: Desktop
# #  5: Start screen saver
# #  6: Disable screen saver
# #  7: Dashboard
# # 10: Put display to sleep
# # 11: Launchpad
# # 12: Notification Center
# # Bottom left >> Put display to sleep
defaults write com.apple.dock wvous-bl-corner -int 12
defaults write com.apple.dock wvous-ul-corner -int 2
defaults write com.apple.dock wvous-br-corner -int 4
defaults write com.apple.dock wvous-ur-corner -int 3

# === Finder ===

# Show Finder path bar:
defaults write com.apple.finder ShowPathbar -bool true

# show hidden files in Finder:
defaults write com.apple.finder AppleShowAllFiles -bool true

# show file extensions in Finder:
defaults write NSGlobalDomain AppleShowAllExtensions -bool true

# Allow text selection in Quick Look
defaults write com.apple.finder QLEnableTextSelection -bool true

# Finder: allow quitting via ⌘ + Q; doing so will also hide desktop icons
defaults write com.apple.finder QuitMenuItem -bool true

# When performing a search, search the current folder by default
defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"

# Avoid creating .DS_Store files on network or USB volumes
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

# Always open everything in Finder's list view.
# Use list view in all Finder windows by default
# Four-letter codes for the other view modes: `icnv`, `clmv`, `Flwv`
defaults write com.apple.finder FXPreferredViewStyle -string "Nlsv"

# Expand the following File Info panes:
# “General”, “Open with”, and “Sharing & Permissions”
defaults write com.apple.finder FXInfoPanesExpanded -dict General -bool true OpenWith -bool true Privileges -bool true

# Enable the automatic update check
defaults write com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true

# Check for software updates weekly (`dot update` includes software updates)
defaults write com.apple.SoftwareUpdate ScheduleFrequency -string 7

# Download newly available updates in background
defaults write com.apple.SoftwareUpdate AutomaticDownload -bool true

# Install System data files & security updates
defaults write com.apple.SoftwareUpdate CriticalUpdateInstall -bool true

# Turn on app auto-update
defaults write com.apple.commerce AutoUpdate -bool true

echo '🛫 Restarting apps...'
killall Finder
killall Dock
killall SystemUIServer

echo '✅ Done setting up MacOs!'
