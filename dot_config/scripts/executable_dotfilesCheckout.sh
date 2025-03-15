#!/bin/bash

 # Define the dotfiles directory
DOTFILES_DIR="$HOME/.dotfiles"

# Check if the dotfiles repository already exists
if [ ! -d "$DOTFILES_DIR" ]; then
	echo "🔂 Dotfiles are not coppied to local machine. Starting installing... "
	echo "🍽️ Setting git config to clone repository"
	echo "[user]" >> .gitconfig
	echo "name = Daniel Dudziak" >> .gitconfig
	echo "email = 20063579+dandudzi@users.noreply.github.com" >> .gitconfig

	echo "🍽️ Setting alias for dotfiles"
	echo "alias dotfiles='/usr/bin/git --git-dir=$HOME/.dotfiles --work-tree=$HOME'" >> .zshrc
	source ~/.zshrc

	echo "🍽️ Cloning repo"
	git clone --bare git@github.com:dandudzi/.dotfiles.git $HOME/.dotfiles

	echo "🍽️ Move files to backup directory"
	mkdir -p .dotfiles-backup
	dotfiles checkout 2>&1 | egrep "\s+" | awk '{print $1}' | grep -v -E "error:|Please" | xargs -I{} mv {} .dotfiles-backup/{}

	echo "🍽️ Checkout bare repository and adjust settings"
	dotfiles checkout
	dotfiles config --local core.fsmonitor false
	dotfiles config --local status.showUntrackedFiles no

	echo "✅ Dotfiles setup completed."
else
	echo "✅ Dotfiles repository already exists"
fi
