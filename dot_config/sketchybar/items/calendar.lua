local icons = require("icons")
local settings = require("settings")
local colors = require("colors")

-- Padding item required because of bracket
-- sbar.add("item", { position = "right", width = settings.group_paddings })

local cal = sbar.add("item", {
	icon = {
		color = colors.flamingo,
		padding_left = 8,
		padding_right = 0,
		string = icons.calendar,
		font = {
			size = 16.0,
			family = settings.font.text,
			style = settings.font.style_map["Regular"],
		},
	},
	label = {
		color = colors.white,
		padding_right = 8,
		padding_left = 8,
		align = "right",
		font = {
			size = 17.0,
			style = settings.font.style_map["Regular"],
		},
	},

	position = "right",
	update_freq = 30,
	background = {
		color = colors.transparent,
	},
})

local time = sbar.add("item", {
	icon = {
		color = colors.orange,
		padding_left = 8,
		padding_right = 0,
		string = icons.time,
		font = {
			size = 16.0,
			family = settings.font.text,
			style = settings.font.style_map["Regular"],
		},
	},
	label = {
		color = colors.white,
		padding_right = 8,
		padding_left = 8,
		align = "right",
		font = {
			size = 17.0,
			style = settings.font.style_map["Bold"],
		},
	},

	position = "right",
	update_freq = 30,
	background = {
		color = colors.transparent,
	},
})
-- Double border for calendar using a single item bracket
sbar.add("bracket", { cal.name, time.name }, {
	background = {
		color = colors.background,
	},
})

-- Padding item required because of bracket
-- sbar.add("item", { position = "right", width = settings.group_paddings })

cal:subscribe({ "forced", "routine", "system_woke" }, function(env)
	cal:set({ label = os.date("%a. %d %b.") })
end)

time:subscribe({ "forced", "routine", "system_woke" }, function(env)
	time:set({ label = os.date("%H:%M") })
end)
