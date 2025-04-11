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

# functions to go or copy paths
cx() { cd "$@" && lg; }
fls() { cd "$(eval $(dd_fd_command_directory) | fzf)" && l; }
fp() { echo "$(eval $(dd_fd_command_files) | fzf)" | pbcopy }
fv() { nvim "$(eval $(dd_fd_command_files) | fzf)" }

# yazi wraper to change directory on exit
function y() {
	local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
	yazi "$@" --cwd-file="$tmp"
	if cwd="$(command cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
		builtin cd -- "$cwd"
	fi
	rm -f -- "$tmp"
}

function sesh-sessions() {
  {
    exec </dev/tty
    exec <&1
    local session
    session=$(sesh list -t -c | fzf --height 40% --reverse --border-label ' sesh ' --border --prompt '⚡  ')
    zle reset-prompt > /dev/null 2>&1 || true
    [[ -z "$session" ]] && return
    sesh connect $session
  }
}

zle     -N             sesh-sessions
bindkey -M emacs '\es' sesh-sessions
bindkey -M vicmd '\es' sesh-sessions
bindkey -M viins '\es' sesh-sessions 

function extract() {
    if [ -f $1 ]; then
        case $1 in
            *.tar.bz2)  tar -jxvf $1                        ;;
            *.tar.gz)   tar -zxvf $1                        ;;
            *.tar)      tar -xvf $1                         ;;
            *.tbz2)     tar -jxvf $1                        ;;
            *.tgz)      tar -zxvf $1                        ;;
            *.zip)      unzip $1                            ;;
            *.ZIP)      unzip $1                            ;;
            *.rar)      unar x $1                          ;;
            *)          echo "'$1' cannot be extracted/mounted via extract()" ;;
        esac
    else
        echo "'$1' is not a valid file"
    fi
}



