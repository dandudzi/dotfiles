local colors = require("colors")
local settings = require("settings")
local helper = '/bin/sh "$HOME/.config/sketchybar/helpers/codex.sh"'

-- Share tmux's attention queue so both pills describe the same waiting panes.
local codex = sbar.add("item", "codex", {
	position = "left",
	update_freq = 2,
	icon = {
		string = "󰚩",
		-- This glyph looks oversized at the bar's default 24-point icon size.
		font = { size = 18.0 },
		color = colors.black,
		padding_left = 7,
		padding_right = 5,
		background = { color = colors.mauve, height = 32, corner_radius = 6 },
	},
	label = {
		string = "0",
		color = colors.white,
		padding_left = 5,
		padding_right = 7,
		font = { family = settings.font.numbers, size = 16.0 },
		background = { color = colors.background, height = 32, corner_radius = 6, drawing = true },
	},
	-- Keep the counter compact with lightly rounded, square-shaped corners.
	-- Remove the inherited border so the number's fill matches the icon's height.
	background = { color = colors.background, height = 32, corner_radius = 6, border_width = 0 },
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
