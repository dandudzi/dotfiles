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
		-- Put the accent on the glyph while keeping one dark pill background.
		color = colors.mauve,
		padding_left = 5,
		padding_right = settings.paddings,
		background = { color = colors.background, height = 40, corner_radius = 15 },
	},
	label = {
		string = "0",
		color = colors.lavender, -- Match the active app label.
		padding_left = 5,
		padding_right = 10,
		-- Use the bar's label font and size, with bold weight for the attention count.
		font = { family = settings.font.text, style = settings.font.style_map["Bold"], size = 18.0 },
		background = { color = colors.background, height = 40, corner_radius = 15, drawing = true },
	},
	-- Match the app pill's height, rounding, and spacing.
	-- Remove the inherited border so the number's fill matches the icon's height.
	background = { color = colors.background, height = 40, corner_radius = 15, border_width = 0 },
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
