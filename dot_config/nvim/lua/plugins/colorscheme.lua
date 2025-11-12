local colorscheme = require("lazyvim.plugins.colorscheme")
return {
    {
        "LazyVim/LazyVim",
        opts = {
            -- catppuccin catppuccin-latte, catppuccin-frappe, catppuccin-macchiato, catppuccin-mocha
            colorscheme = "catppuccin-macchiato",
            -- colorscheme = "catppuccin",
            -- colorscheme = "eldritch",
            -- colorscheme = "catppuccin-frappe",
            -- colorscheme = "Duskfox",
            -- colorscheme = "Nightfox",
            -- colorscheme = "Carbonfox",
            -- colorscheme = "gruvbox",
        },
    },
    {
        "catppuccin",
        opts = {
            transparent_background = true,
        },
    },
}
