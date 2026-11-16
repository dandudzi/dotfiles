local markdownlint_args = { "--config", vim.fn.stdpath("config") .. "/.markdownlint-cli2.yaml" }

return {
    -- Disable Markdown linting without changing linters for other file types.
    {
        "mfussenegger/nvim-lint",
        opts = function(_, opts)
            opts.linters_by_ft.markdown = {}
        end,
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
