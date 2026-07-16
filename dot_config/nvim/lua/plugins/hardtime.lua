return {
    "m4xshen/hardtime.nvim",
    enabled = false, -- Keep disabled unless deliberately practicing movement habits.
    dependencies = {
        "MunifTanjim/nui.nvim",
        "nvim-lua/plenary.nvim",
    },
    event = "VeryLazy",
    opts = {
        hints = {
            ["[dcyvV][ia][%(%)]"] = {
                message = function(keys)
                    return "Use " .. keys:sub(1, 2) .. "b instead of " .. keys
                end,
                length = 3,
            },
            ["[dcyvV][ia][%{%}]"] = {
                message = function(keys)
                    return "Use " .. keys:sub(1, 2) .. "B instead of " .. keys
                end,
                length = 3,
            },
        },
    },
}
