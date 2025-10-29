# 📺 ZSH setup
# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"
# Expore toolbox scripts
export PATH="$PATH:$HOME/Library/Application Support/JetBrains/Toolbox/scripts"
# Export IDE CE edition scripts
export PATH="$PATH:/Applications/IntelliJ IDEA CE.app/Contents/MacOS"

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

# change terminal config path
KITTY_CONFIG_DIRECTORY="$CONFIG_HOME/kitty/kitty.conf"

#⚠️jira plugins require setup https://github.com/ohmyzsh/ohmyzsh/tree/master/plugins/jira
plugins=(
  direnv              # Directory-based environment variables

  fzf                 # Fuzzy finder general utility
  fzf-tab             # FZF-based tab completion
  fzf-tab-source      # Source plugins for fzf-tab

  aliases             # General aliases
  common-aliases      # Additional common aliases
  alias-finder        # Discover command aliases
  safe-paste          # Safe pasting of input
  
  aws                 # AWS management
  kubectl             # kubectl command enhancements
  docker              # Docker command enhancements
  docker-compose      # Docker-compose enhancements
  gradle              # Gradle build tool
  mvn                 # Maven build tool
  jira                # JIRA integration
  gpg-agent           # GPG agent support
  chezmoi             # Manage dotfiles
  kitty               # Kitty terminal configurations
  sublime             # Enhance sublime integrations
  python              # Python environment and commands
  rust                # Rust programming language tools
  spring              # Spring framework tools

  mise                # UI enhancements or interaction tweaks
  
  spaceship-vi-mode   # Enhances vi-mode for Spaceship prompt
  vi-mode             # vi-style command editing
)

# enable alias finder for all coommands 
zstyle ':omz:plugins:alias-finder' autoload yes # disabled by default
zstyle ':omz:plugins:alias-finder' longer yes # disabled by default
zstyle ':omz:plugins:alias-finder' exact yes # disabled by default
zstyle ':omz:plugins:alias-finder' cheaper yes # disabled by default

VI_MODE_SET_CURSOR=true
VI_MODE_RESET_PROMPT_ON_MODE_CHANGE=true
VI_MODE_CURSOR_NORMAL=1
VI_MODE_CURSOR_VISUAL=1
VI_MODE_CURSOR_INSERT=5
VI_MODE_CURSOR_OPPEND=5

#🚀 spaceship settings
SPACESHIP_TIME_SHOW=true
SPACESHIP_EXIT_CODE_SHOW=true
SPACESHIP_KUBECTL_SHOW=true
SPACESHIP_GIT_BRANCH_ASYNC=true
SPACESHIP_EXEC_TIME_ELAPSED=1
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
SPACESHIP_VI_MODE_NORMAL="󰛐 "
SPACESHIP_VI_MODE_INSERT="󰷢 "

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
source $CONFIG_HOME/scripts/update_packages.sh

#🎖️ Command used in command line
source $CONFIG_HOME/zsh/command.zsh

#🍻 Source script that runs only once to setUp CI tools
source $CONFIG_HOME/scripts/setUpCITools.sh

#🕒 schedule cron jobs if not enabled
source $CONFIG_HOME/scripts/crontabconfig.sh

# make sure that special-dirs like './' or '../' are not listed in completion
zstyle ':completion:*' special-dirs false

#🗣️ autosuggestiontions setup to not suggest bif buffers
export ZSH_AUTOSUGGEST_BUFFER_MAX_SIZE=20
# ripgrep config 
export RIPGREP_CONFIG_PATH="$HOME/.config/ripgrep/config"
# make bitwarden ssh agend
export SSH_AUTH_SOCK="$HOME/.bitwarden-ssh-agent.sock"
#📢 zsh autosuggestiontions
source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh
# make sure that spaceship propmpt is refreshed
eval spaceship_vi_mode_enable
eval "$(zoxide init zsh)"
eval "$(mise activate zsh)"

function zle-keymap-select() {
  # Call the spaceship functionality
  spaceship::core::refresh_section "vi_mode"
  
  # Original functionality - ensure it's sourced first
  typeset -g VI_KEYMAP=$KEYMAP

  if _vi-mode-should-reset-prompt; then
    zle reset-prompt
  fi
  
  zle -R
  _vi-mode-set-cursor-shape-for-keymap "${VI_KEYMAP}"
}

# Bind the combined function
zle -N zle-keymap-select
