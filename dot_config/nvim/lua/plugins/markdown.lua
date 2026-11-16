local markdownlint_args = { "--config", vim.fn.stdpath("config") .. "/.markdownlint-cli2.yaml" }

return {
    -- Use the same line-length policy for diagnostics and automatic fixes.
    {
        "mfussenegger/nvim-lint",
        opts = {
            linters = {
                ["markdownlint-cli2"] = { prepend_args = markdownlint_args },
            },
        },
    },
    {
        "stevearc/conform.nvim",
        opts = {
            formatters = {
                ["markdownlint-cli2"] = { prepend_args = markdownlint_args },
            },
        },
    },
}
