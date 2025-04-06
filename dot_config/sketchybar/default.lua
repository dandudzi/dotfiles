local settings = require("settings")
local colors = require("colors")

-- Equivalent to the --default domain
sbar.default({
	updates = "when_shown",
	icon = {
		font = {
			family = settings.font.icons,
			size = 24.0,
		},
		color = colors.white,
		padding_left = settings.paddings,
		padding_right = settings.paddings,
		background = {
			height = 40,
			image = { corner_radius = 9 },
		},
	},
	label = {
		font = {
			family = settings.font.text,
			size = 18.0,
		},
		color = colors.white,
		padding_left = settings.paddings,
		padding_right = settings.paddings,
		background = {
			height = 40,
		},
	},
	background = {
		height = 40,
		border_width = 2,
		border_color = colors.transparent,
		color = colors.transparent,
		corner_radius = 15,
		image = {
			border_color = colors.grey,
			border_width = 1,
		},
	},
	popup = {
		background = {
			border_width = 2,
			corner_radius = 9,
			border_color = colors.border,
			color = colors.background,
			shadow = { drawing = true },
		},
		blur_radius = 50,
	},
	padding_left = 5,
	padding_right = 5,
	scroll_texts = true,
})
