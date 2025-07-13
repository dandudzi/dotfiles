# Set up fzf key bindings and fuzzy completion
source <(fzf --zsh)

# bind new key for finding directories 
bindkey '^e' fzf-cd-widget

# making sure that fd is used with fzf
export FZF_DEFAULT_COMMAND='fd --type f --strip-cwd-prefix --hidden --follow --exclude .git'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_CTRL_T_OPTS="
  --walker-skip .git,node_modules,target
  --preview 'bat -n --color=always {}'
  --bind 'ctrl-/:change-preview-window(down|hidden|)'"
export FZF_ALT_C_OPTS="--preview 'eza -1 --all --color=always --icons {}'"

#🐱 set cattpuccin
# cannot use --tmux because it breaking everything
export FZF_DEFAULT_OPTS=" --ansi \
	--color=bg+:#363a4f,bg:#24273a,spinner:#f4dbd6,hl:#ed8796 \
	--color=fg:#cad3f5,header:#ed8796,info:#c6a0f6,pointer:#f4dbd6 \
	--color=marker:#b7bdf8,fg+:#cad3f5,prompt:#c6a0f6,hl+:#ed8796 \
	--color=selected-bg:#494d64 \
	--color=border:#363a4f,label:#cad3f5"

# make sure that fzf-preview for completion uses less
zstyle ':fzf-tab:complete:*:*' fzf-preview 'less ${(Q)realpath}'
# brew installing lesspipe in strange place so this is why it is here
# ** in case version will change
export LESSOPEN="|/opt/homebrew/Cellar/lesspipe/**/bin/lesspipe.sh %s"
# make completion case insestive
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'
# disable sort when completing `git checkout`
zstyle ':completion:*:git-checkout:*' sort false
# set descriptions format to enable group support
zstyle ':completion:*:descriptions' format '[%d]'
# set list-colors to enable filename colorizing
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}
# switch group using `<` and `>`
zstyle ':fzf-tab:*' switch-group ',' '.'
# force zsh not to show completion menu, which allows fzf-tab to capture the unambiguous prefix
zstyle ':completion:*' menu no
# preview directory's content with eza when completing cd
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza -1 --all --color=always --icons $realpath'

# minimal bottom padding fot tmux
zstyle ':fzf-tab:complete:*:*' popup-pad 70 70
# apply to all command
zstyle ':fzf-tab:*' popup-min-size 70 70
# display header and colorfull prefix
zstyle ':fzf-tab:*' single-group prefix color header

# use fzf use-fzf-default-opts for all commands do not use ⚠ --tmux
zstyle ':fzf-tab:*' prefix ''
zstyle ':fzf-tab:*' use-fzf-default-opts yes
  
# make it working with tmux
zstyle ':fzf-tab:*' fzf-command ftb-tmux-popup

# additional git functions powered by fzf
source ~/.config/zsh/fzf-git.sh
