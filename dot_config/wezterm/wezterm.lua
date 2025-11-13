-- Pull in the wezterm API
local wezterm = require("wezterm")
local k = require("utils/keys")
local custom = wezterm.color.get_builtin_schemes()["Catppuccin Mocha"]
custom.cursor_bg = "#c6a0f6"
custom.background = "#24273a"

-- This will hold the ration.
local config = {
	color_schemes = {
		["my-catppuccin"] = custom,
	},
	-- setting up background
	color_scheme = "my-catppuccin",
	window_background_opacity = 0.80,
	macos_window_background_blur = 10,

	scrollback_lines = 10000,

	-- performance boost
	front_end = "OpenGL",
	max_fps = 144,
	webgpu_power_preference = "HighPerformance",
	animation_fps = 10,

	-- font settings
	font_size = 16,
	line_height = 1.2,
	font = wezterm.font_with_fallback({
		"CommitMono",
		-- fallback font for Nerd Font icons
		{ family = "Symbols Nerd Font Mono" },
	}),

	set_environment_variables = {
		LC_ALL = "en_US.UTF-8",
	},
	adjust_window_size_when_changing_font_size = false, --When set to true, this option adjusts the window size to fit the new font size whenever the font size is changed-
	enable_tab_bar = false, --disables the tab bar at the top of the WezTerm window
	native_macos_fullscreen_mode = false,
	window_decorations = "RESIZE", --disable the title bar but enable the resizable border
	use_dead_keys = false,
	default_cursor_style = "BlinkingBar",
	cursor_blink_rate = 500,
	keys = {
		-- Select window 1-9
		k.cmd_to_tmux_prefix("1", "1"),
		k.cmd_to_tmux_prefix("2", "2"),
		k.cmd_to_tmux_prefix("3", "3"),
		k.cmd_to_tmux_prefix("4", "4"),
		k.cmd_to_tmux_prefix("5", "5"),
		k.cmd_to_tmux_prefix("6", "6"),
		k.cmd_to_tmux_prefix("7", "7"),
		k.cmd_to_tmux_prefix("8", "8"),
		k.cmd_to_tmux_prefix("9", "9"),
	},
}
-- and finally, return the ration to wezterm
return config
