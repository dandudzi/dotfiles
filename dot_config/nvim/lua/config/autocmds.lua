-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- Add any additional autocmds here
-- with `vim.api.nvim_create_autocmd`
--
-- Or remove existing autocmds by their group name (which is prefixed with `lazyvim_` for the defaults)
-- e.g. vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")

-- Keep Markdown free of automatic formatting, diagnostic messages, and spell checks.
vim.api.nvim_create_autocmd("FileType", {
    group = vim.api.nvim_create_augroup("markdown_no_autoformat", { clear = true }),
    pattern = "markdown",
    callback = function(event)
        vim.b[event.buf].autoformat = false
        vim.diagnostic.enable(false, { bufnr = event.buf })
        vim.opt_local.spell = false
    end,
})
