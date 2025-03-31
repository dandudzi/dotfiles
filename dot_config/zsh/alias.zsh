alias shrug="echo '¯\_(ツ)_/¯' | pbcopy"

# Get week number
alias week='date +%V'

#🔎 search aliases
alias rgi="rg --invert-match"           # invert search text in files
alias rgf="rg --fixed-strings"          # search fixed string
alias rfv="~/.config/scripts/rfv"       # fzf with rg fo searching files and its content 

#🩳 aliases
#🪛 tools aliases
alias tree=pstree
alias cat=bat
alias lals="cat ~/.config/zsh/alias.zsh"
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

alias ga="git add -p" # add only parts of the files to be staged
alias gadd="git add"

alias glog="git log --oneline --decorate --graph --all"
alias glall='git log --graph --pretty="%Cred%h%Creset -%C(auto)%d%Creset %s %Cgreen(%ar) %C(bold blue)<%an>%Creset" --all'
alias glpa="git log --stat --patch"
alias glg="git log --graph --abbrev-commit --decorate --format=format:'%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%s%C(reset) %C(dim white)- %an%C(reset)%C(bold yellow)%d%C(reset)' --all"
alias gsh="git show --pretty=short --show-signature"
alias gshort="git shortlog"

alias gpf="git push --force-with-lease"
alias gcon="git mergetool --no-prompt" #resolve conflict with git
alias gr="git rebase"           #this is like cherry-pick but for manny commits
alias gcp="git cherry-pick"

alias gc="git commit -m"
alias gca="git commit -a -m" # add files to be staged and commit

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
alias dote="chezmoi edit --watch"
alias econfig="dote ~/.config"
alias ez="dote ~/.config/zsh"
alias ezals="dote ~/.config/zsh/alias.zsh"
alias envim="dote ~/.config/nvim/"
alias dots="dot status"

# Dirs
alias cd="z"
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."
alias .....="cd ../../../.."
alias ......="cd ../../../../.."
