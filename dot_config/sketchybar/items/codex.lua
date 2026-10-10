local colors = require("colors")
local settings = require("settings")
local helper = '/bin/sh "$HOME/.config/sketchybar/helpers/codex.sh"'

-- Share tmux's attention queue so both pills describe the same waiting panes.
local codex = sbar.add("item", "codex", {
	position = "left",
	update_freq = 2,
	icon = {
		string = "󰚩",
		color = colors.black,
		padding_left = 10,
		padding_right = 8,
		background = { color = colors.mauve, corner_radius = 15 },
	},
	label = {
		string = "0",
		color = colors.white,
		padding_left = 8,
		padding_right = 10,
		font = { family = settings.font.numbers },
	},
	background = { color = colors.background, corner_radius = 15 },
})

local function refresh()
	sbar.exec(helper .. " --count", function(output)
		codex:set({ label = output:match("^%s*(%d+)") or "0" })
	end)
end

codex:subscribe({ "routine", "forced", "system_woke" }, refresh)
codex:subscribe("mouse.clicked", function(env)
	if env.BUTTON == "left" then
		sbar.exec(helper .. " --click", refresh)
	end
end)
refresh()
