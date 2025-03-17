# 📺 ZSH setup
# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

export CONFIG_HOME="$HOME/.config"
# allows you to use commands in your prompt that are dynamically evaluated each time the prompt is displayed.
setopt prompt_subst
# allows zsh to use bash like completion scripts
autoload bashcompinit && bashcompinit
# initilize zshrc completion system
autoload -Uz compinit
# initilize autocomolete
compinit
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

# Disables the audible beep when list ambiguous completions
setopt NO_LIST_BEEP
# Activates spelling correction for commands.
setopt CORRECT
# sort files in a numerically logical order instead of pure lexicographical
setopt numeric_glob_sort

#🖥️ zsh settings
ZSH_THEME="spaceship"

#⚠️jira plugins require setup https://github.com/ohmyzsh/ohmyzsh/tree/master/plugins/jira
plugins=(chezmoi fzf mise alias-finder aliases aws common-aliases gradle docker mvn docker-compose gpg-agent jira kubectl python rust safe-paste spring sublime fzf-tab fzf-tab-source)

#🚀 spaceship settings
SPACESHIP_TIME_SHOW=true
SPACESHIP_EXIT_CODE_SHOW=true
SPACESHIP_KUBECTL_SHOW=true

# initilize fzf and fzf-tab and catppuccin with support for tmux
# must be before oh-my-zsh init
source $CONFIG_HOME/zsh/fzf.zsh

# 🚀 load ohmyzsh setting
source $ZSH/oh-my-zsh.sh
# this bindkey myst be after oh-my-zsh otherwise it will be overwritten
bindkey '^e' fzf-cd-widget

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
export BAT_THEME="Catppuccin Macchiato"
source $CONFIG_HOME/zsh/themes/catppuccin_macchiato-zsh-syntax-highlighting.zsh
export EXA_COLORS="catppuccin"

#🍻 Source brew 
source $CONFIG_HOME/zsh/brew.zsh

#🎖️ Command used in command line
source $CONFIG_HOME/zsh/command.zsh

#🌈 sytnax higlight setup 
source /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh

eval "$(zoxide init zsh)"
eval "$(mise activate zsh)"
