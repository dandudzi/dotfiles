return {
	black = 0xff181926,
	white = 0xffcad3f5,
	red = 0xffed8796,
	green = 0xffa6da95,
	blue = 0xff8aadf4,
	yellow = 0xffeed49f,
	orange = 0xfff5a97f,
	grey = 0xff939ab7,
	transparent = 0x00000000,
	maroon = 0xffee99a0,
	sky = 0xff91d7e3,
	teal = 0xff8bd5ca,
	flamingo = 0xfff0c6c6,
	lavender = 0xffb7bdf8,
	pink = 0xfff5bde6,
	mauve = 0xffc6a0f6,
	border = 0xff1e2030,
	background = 0xff24273a,
	saphire = 0xff7dc4e4,

	with_alpha = function(color, alpha)
		if alpha > 1.0 or alpha < 0.0 then
			return color
		end
		return (color & 0x00ffffff) | (math.floor(alpha * 255.0) << 24)
	end,
}
