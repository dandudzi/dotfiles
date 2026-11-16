-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- Add any additional autocmds here
-- with `vim.api.nvim_create_autocmd`
--
-- Or remove existing autocmds by their group name (which is prefixed with `lazyvim_` for the defaults)
-- e.g. vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")

-- Keep Markdown autoformat off while allowing spelling and language checks.
vim.api.nvim_create_autocmd("FileType", {
    group = vim.api.nvim_create_augroup("markdown_no_autoformat", { clear = true }),
    pattern = "markdown",
    callback = function(event)
        vim.b[event.buf].autoformat = false
        vim.diagnostic.enable(true, { bufnr = event.buf })
        vim.opt_local.spell = true
    end,
})
