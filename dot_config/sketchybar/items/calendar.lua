local settings = require("settings")
local colors = require("colors")

-- Padding item required because of bracket
sbar.add("item", { position = "right", width = settings.group_paddings })

local cal = sbar.add("item", {
	icon = {
		color = colors.white,
		padding_left = 8,
		padding_right = 10,
		font = {
			size = 15.0,
		},
	},
	label = {
		color = colors.white,
		padding_right = 8,
		width = 49,
		align = "right",
	},

	position = "right",
	update_freq = 30,
	background = {
		color = colors.background,
	},
})

-- Double border for calendar using a single item bracket
sbar.add("bracket", { cal.name }, {
	background = {
		color = colors.transparent,
		height = 30,
	},
})

-- Padding item required because of bracket
sbar.add("item", { position = "right", width = settings.group_paddings })

cal:subscribe({ "forced", "routine", "system_woke" }, function(env)
	cal:set({ icon = os.date("%a. %d %b."), label = os.date("%H:%M") })
end)
