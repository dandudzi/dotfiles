local colors = require("colors")
local settings = require("settings")

local front_app = sbar.add("item", "front_app", {
	display = "active",
	icon = { drawing = false },
	label = {
		padding_left = 10,
		padding_right = 10,
		font = {
			size = 18,
		},
	},
	background = {
		border_color = colors.border,
		border_width = 4,
	},
	updates = true,
})

front_app:subscribe("front_app_switched", function(env)
	front_app:set({ label = { string = env.INFO } })
end)

front_app:subscribe("mouse.clicked", function(env)
	sbar.trigger("swap_menus_and_spaces")
end)
