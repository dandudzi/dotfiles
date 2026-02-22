# Check if dsg (destructive command guard) is installed
if ! command -v dcg &>/dev/null; then
    echo "\033[1;33m⚠  dcg (destructive command guard) is not installed.\033[0m"
    echo "   Install: curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/destructive_command_guard/main/install.sh -o /tmp/dsg_install.sh && bash /tmp/dsg_install.sh --easy-mode"
fi
