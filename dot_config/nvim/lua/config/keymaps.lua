-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
local map = LazyVim.safe_keymap_set
map({ "n" }, "<leader>xm", function()
    vim.cmd("messages")
end, { desc = "Print Messages", expr = true, silent = true })
