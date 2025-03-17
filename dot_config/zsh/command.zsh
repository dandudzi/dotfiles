#👾 usefull comands setup
dd_excluded(){
	DIRS_TO_EXCLUDE=(".git" ".mvn" ".conf" ".cache" ".m2" ".docker" ".Trash" ".hawtjni" ".iterm2" ".oh-my-zsh" ".tldr" ".local")
	EXCLUDE_OPTION="--exclude"
	EXCLUDE_LIST=""
	for path in "${DIRS_TO_EXCLUDE[@]}"; do
		EXCLUDE_LIST+=" $EXCLUDE_OPTION $path"
	done
	echo $EXCLUDE_LIST
}
dd_fd_command_directory() {
	local exclude=$(dd_excluded)
	echo "fd --type d --hidden $exclude"
}
dd_fd_command_files() {
	local exclude=$(dd_excluded)
	echo "fd --type f --hidden $exclude"
}

cx() { cd "$@" && lg; }
fls() { cd "$(eval $(dd_fd_command_directory) | fzf)" && l; }
fp() { echo "$(eval $(dd_fd_command_files) | fzf)" | pbcopy }
fv() { nvim "$(eval $(dd_fd_command_files) | fzf)" }
function y() {
	local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
	yazi "$@" --cwd-file="$tmp"
	if cwd="$(command cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
		builtin cd -- "$cwd"
	fi
	rm -f -- "$tmp"
}
