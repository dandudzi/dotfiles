#🛠️ tools
# git-open to open remote repository
# fv -> search and open file in vim
# fp -> copy pwd of the file
# fls -> list files in directory
# cx -> go to directory and list files
# shift + cmd + x -> 🖼️ take screenshot
# y -> file manager
# gitstat -> summary of the git repository

#🔍 bindings
# <c-r> # Search command history
# <c-t> # Fuzzy find files
# <c-e> # Fuzzy find directories

#📺 Tmux bindings
# <prefix> ?		# list all commands
# <prefix> w       	# go thourhg all windows
# <prefix> x       	# close pane
# <prefix> &       	# close window
# <prefix> d       	# detach from seesion
# <prefix> |       	# split horizonatly
# <prefix> -       	# split verticaly
# <prefix> [ -> shift-v -> y  #copy to clipboard
# <prefix> ]		# paste between panes
# <prefix> <c-[/]> 	# move panes between spaces
# <prefix> h/j/k/l 	# move between panes
# <prefix> shift + f	# search actions
# <prefix> <c-s>	# save session
# <prefix> <c-r>	# restore session
# <prefix> space	# which key
# <prefix> <c-s>	# save session
# <prefix> <c-r>	# restore session

#📋 move fzf-tabs
# <- ',' '.' ->

#🐁 install developer dependcies and tools
# mise exec node@22 -- node -v  //install node
# mise use --global node@22     //use global
# mise use node@22              //create in directory mise.toml file and install dependency if not installed
# mise install                  //installs everything specified in mise.toml
# mise upgrade                  //upgrade tools and respec the version prefix node@22 will not bump to node 23
# mise upgrade --bump node      //will upgrade tools to the latest available version
# mise rm node@22               //remove node
# mise ls                       //list installed tools
# mise ls-remote node           //list remote tools versions

#𐂷 pstree       shows process in tree like
#⍙ delta -- to find diff between to files
#🪵 [logfiles analyzer](https://docs.lnav.org)
#🙈 [json manipulator](https://jqlang.org/)
#👨 devtools for different part of manipulation
#🕸️ [httpie](https://httpie.io/cli) network tool ⚠️  need to install
#📗 [mactex](https://www.tug.org/mactex/) if you like to write in latex ⚠️ need to install
#🚄 [bench](https://github.com/Gabriella439/bench) better time for commands ⚠ need to instal
alias shrug="echo '¯\_(ツ)_/¯' | pbcopy"

# Get week number
alias week='date +%V'

#🔎 search aliases
alias rgi="rg --invert-match"           # invert search text in files
alias rgf="rg --fixed-strings"          # search fixed string

#🩳 aliases
#🪛 tools aliases
alias tree=pstree
alias cat=bat
alias lals="cat ~/.zshrc_als"
alias vi="nvim"
alias vim="nvim"
alias testBrewInstall="./install-mysetup.sh --skipInitial --skipMac --skipAppStore" 

#🛜 networking
alias fig="find . -print | grep -iw"
alias lport="sudo lsof -i -P -n | grep LISTEN"
alias nm="nmap -sC -sV -oN nmap"
alias ip="dig +short myip.opendns.com @resolver1.opendns.com"
alias localip="ipconfig getifaddr en0"
alias reloaddns="dscacheutil -flushcache && sudo killall -HUP mDNSResponder"

#🎬 Git
alias go="git-open"
alias g="git"
alias st="status"
alias avv="branch -avv"
alias vv="branch -vv"
alias amen="commit --amend"

alias ga="git add -p" #add only parts of the files to be staged
alias gadd="git add"

alias glog="git log --oneline --decorate --graph --all"
alias glall='git log --graph --pretty="%Cred%h%Creset -%C(auto)%d%Creset %s %Cgreen(%ar) %C(bold blue)<%an>%Creset" --all'
alias glpa="git log --stat --patch"
alias glg="git log --graph --abbrev-commit --decorate --format=format:'%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%s%C(reset) %C(dim white)- %an%C(reset)%C(bold yellow)%d%C(reset)' --all'"
alias gsh="git show --pretty=short --show-signature"
alias gshort="git shortlog"

alias gpf="git push --force-with-lease"
alias gcon="git mergetool --no-prompt" #resolve conflict with git
alias gr="git rebase"           #this is like cherry-pick but for manny commits
alias gcp="git cherry-pick"

alias gc="git commit -m"
alias gca="git commit -a -m" #add files to be staged and commit

alias gpu="git pull origin"

alias gst="git status"

alias gdiff="git diff"

alias gco="git checkout"
alias gunstg="git restore --staged" #unstage files
alias grest="git restore"
alias gbl="git blame --ignore-rev"  #ingore noisy commits

alias gs="git switch"
alias gsc="git switch -c"
alias gb="git branch"
alias gba="git branch -a" #list all branches even remote

alias gwipe="git reset --hard && git clean --force -df"
alias gitstat="onefetch"

#🌳 eza aliases
alias lt='eza -l --sort=modified'      # Sort by modification time
alias l='eza -l --icons $eza_params'                # Simple long list with icons
alias ls='eza -al --icons $eza_paras'
alias lg='eza --git-ignore $eza_params'
alias ll='eza --all --header --long $eza_params'
alias llm='eza --all --header --long --sort=modified $eza_params'
alias la='eza -lbhHigUmuSa'
alias lx='eza -lbhHigUmuSa@'
alias ltree='eza --tree $eza_params'

#🪟 tmux aliasses
alias ta="tmux attach -t"                       # Attach new tmux session to already running named session
alias tkss="tmux kill-session -t"               # Terminate named running tmux session
alias tksv="tmux kill-server"                   # Terminate all running tmux sessions
alias tl="tmux list-sessions"                   # Displays a list of running tmux sessions
alias tmuxconf="$EDITOR $ZSH_TMUX_CONFIG"       # Open .tmux.conf file with an editor
alias ts="tmux new-session -s"                  # Create a new named tmux session

#🐍 make sure that we are using python3 instead of python2
alias python=python3
alias pip=pip3

#🔴 chezmoi aliases
alias dot="chezmoi"
alias dotap="chezmoi -v apply"
alias dota="chezmoi add"
alias dotat="chezmoi add --template"
alias dote="chezmoi edit"
alias ez="dot ~/.config/zsh/zshrc"
alias ezals="dot ~/.config/zsh/alias.zshrc"
alias envim="dot ~/.config/nvim/"

# Dirs
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."
alias .....="cd ../../../.."
alias ......="cd ../../../../.."
