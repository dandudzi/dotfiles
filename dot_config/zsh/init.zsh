# 📺 ZSH setup
# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

export CONFIG_HOME="$HOME/.config"
# allows you to use commands in your prompt that are dynamically evaluated each time the prompt is displayed.
setopt prompt_subst
# allows zsh to use bash like completion scripts
#autoload bashcompinit && bashcompinit
# initilize zshrc completion system
autoload -U compinit
# initilize autocomolete
zmodload zsh/complist
compinit
_comp_options+=(globdots)
# making sure that hidden directories and files will be matched
setopt globdots
# You may need to manually set your language environment
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

#🔑 bindings for autocompletion in prompt
bindkey '^q' autosuggest-execute
bindkey '^w' autosuggest-accept
bindkey '^y' autosuggest-toggle

#🗄️ better history
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
# Append history instead of overwriting
setopt APPEND_HISTORY
# Immediately append commands to the history file
setopt INC_APPEND_HISTORY
# Share history across all sessions
setopt SHARE_HISTORY
# Ignore duplicate commands in the history
setopt HIST_IGNORE_ALL_DUPS
# Remove unnecessary blanks from commands in the history
setopt HIST_REDUCE_BLANKS
# Remove command lines beginning with a space from history
setopt hist_ignore_space
# dont execute Immediately command grabbed from history
setopt HIST_VERIFY

# allows in interactive mode to use # commands
setopt interactivecomments
# allow to do something like this echo 'Don''t'
setopt RC_QUOTES
# Disables the audible beep when list ambiguous completions
setopt NO_LIST_BEEP
# Activates spelling correction for commands.
setopt CORRECT
# sort files in a numerically logical order instead of pure lexicographical
setopt numeric_glob_sort

# automatically pushes old directory on directory stack
setopt autopushd
# make sure that there are no duplication in directory stack
setopt pushdignoredups
# allow to use pushd without argument as going to HOME directory
setopt PUSHD_TO_HOME

# can use ** as grabbing all files in directories recursively
setopt globstarshort

# when symlink is set cd to directory to avoid confusion
setopt chaselinks

#🖥️ zsh settings
ZSH_THEME="spaceship"

#⚠️jira plugins require setup https://github.com/ohmyzsh/ohmyzsh/tree/master/plugins/jira
plugins=(zsh-vi-mode spaceship-vi-mode chezmoi fzf mise alias-finder aliases aws common-aliases gradle docker mvn docker-compose gpg-agent jira kubectl python rust safe-paste spring sublime fzf-tab fzf-tab-source)
# enable alias finder for all coommands 
zstyle ':omz:plugins:alias-finder' autoload yes # disabled by default
zstyle ':omz:plugins:alias-finder' longer yes # disabled by default
zstyle ':omz:plugins:alias-finder' exact yes # disabled by default
zstyle ':omz:plugins:alias-finder' cheaper yes # disabled by default

#🚀 spaceship settings
SPACESHIP_TIME_SHOW=true
SPACESHIP_EXIT_CODE_SHOW=true
SPACESHIP_KUBECTL_SHOW=true
export RPS1="%{$reset_color%}"
# additional completions for zsh must be beofre sourcing ohmyzsh
fpath+=${ZSH_CUSTOM:-${ZSH:-~/.oh-my-zsh}/custom}/plugins/zsh-completions/src

# initilize fzf and fzf-tab and catppuccin with support for tmux
# must be before oh-my-zsh init
source $CONFIG_HOME/zsh/fzf.zsh

# 🚀 load ohmyzsh setting
source $ZSH/oh-my-zsh.sh
# this bindkey myst be after oh-my-zsh otherwise it will be overwritten
bindkey '^e' fzf-cd-widget

# setting vi mode 
spaceship add --after time vi_mode
SPACESHIP_VI_MODE_COLOR="magenta"
SPACESHIP_VI_MODE_INSERT="U+E0C6"
SPACESHIP_VI_MODE_NORMAL="U+E0C5"
# make sure that vi mode status is updated
function zvm_after_select_vi_mode() {
  eval spaceship_vi_mode_enable
}

# make sure that pygmentize is not used by any alias
alias_p="P"
unalias $alias_p

#🗒️ source aliases 
source $CONFIG_HOME/zsh/alias.zsh

#📝 Preferred editor for local and remote sessions
 if [[ -n $SSH_CONNECTION ]]; then
   export EDITOR='vim'
 else
   export EDITOR='nvim'
 fi

#🐱 Set up theme Catpuccin
source $CONFIG_HOME/zsh/themes/catppuccin_macchiato-zsh-syntax-highlighting.zsh
export EXA_COLORS="catppuccin"

#🍻 Source brew autou ubpdate script
source $CONFIG_HOME/zsh/brew.zsh

#🎖️ Command used in command line
source $CONFIG_HOME/zsh/command.zsh

# make sure that special-dirs like './' or '../' are not listed in completion
zstyle ':completion:*' special-dirs false

#🗣️ autosuggestiontions setup to not suggest bif buffers
export ZSH_AUTOSUGGEST_BUFFER_MAX_SIZE=20

# ripgrep config 
export RIPGREP_CONFIG_PATH="~/.config/ripgrep/config"

#📢 zsh autosuggestiontions
source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh
eval "$(zoxide init zsh)"
eval "$(mise activate zsh)"
