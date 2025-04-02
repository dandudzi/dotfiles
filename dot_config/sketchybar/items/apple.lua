local colors = require("colors")
local settings = require("settings")

-- Padding item required because of bracket
sbar.add("item", { width = 10 })

local apple = sbar.add("item", {
	icon = {
		font = {
			family = settings.font.icons,
			size = 24.0,
		},
		string = "",
		padding_right = 8,
		padding_left = 8,
	},
	label = { drawing = false },
	background = {
		color = colors.background,
		border_color = colors.black,
		border_width = 1,
	},
	padding_left = 1,
	padding_right = 1,
	click_script = "$CONFIG_DIR/helpers/menus/bin/menus -s 0",
})

-- Padding item required because of bracket
sbar.add("item", { width = 7 })
