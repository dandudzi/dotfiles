-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
local map = LazyVim.safe_keymap_set
map({ "n" }, "<leader>xm", function()
    vim.cmd("messages")
end, { desc = "Print Messages", expr = true, silent = true })

vim.api.nvim_create_user_command("NextNumberedFile", function()
    local buf = vim.api.nvim_get_current_buf()
    local name = vim.fn.expand("%:t")
    local dir = vim.fn.expand("%:p:h")

    local num, rest = name:match("^(%d%d)_(.+)$")
    if not num then
        vim.notify("Filename does not match NN_xxxx format", vim.log.levels.ERROR)
        return
    end

    local next_num = string.format("%02d", tonumber(num) + 1)
    local pattern = dir .. "/" .. next_num .. "_*"

    local matches = vim.fn.glob(pattern, false, true)
    if #matches == 0 then
        vim.notify("No file starting with " .. next_num .. "_ found", vim.log.levels.WARN)
        return
    end
    -- open first match (sorted by glob)
    vim.cmd("edit " .. vim.fn.fnameescape(matches[1]))

    -- close previous buffer without saving
    vim.api.nvim_buf_delete(buf, { force = true }) -- open next file
end, {})

vim.keymap.set("n", "<leader>1", ":NextNumberedFile<CR>", { silent = true })
