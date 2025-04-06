local colors = require("colors")
local settings = require("settings")
local app_icons = require("helpers.app_icons")

local front_app = sbar.add("item", "front_app", {
	display = "active",
	icon = {
		string = app_icons["Default"],
		font = {
			family = settings.font.app_icons,
			style = settings.font.style_map["Regular"],
			size = 22,
		},
		y_offset = -1,
		color = colors.pink,
		position = "right",
	},
	label = {
		padding_left = 5,
		padding_right = 10,
		color = colors.lavender,
		font = {
			style = settings.font.style_map["Bold"],
		},
	},
	background = {
		color = colors.background,
		border_width = 1,
	},
	updates = true,
})

front_app:subscribe("front_app_switched", function(env)
	local app = env.INFO
	local lookup = app_icons[app]
	local icon = ((lookup == nil) and app_icons["Default"] or lookup)
	front_app:set({
		label = { string = env.INFO },
		icon = { string = icon },
	})
end)

front_app:subscribe("mouse.clicked", function(env)
	sbar.trigger("swap_menus_and_spaces")
end)
