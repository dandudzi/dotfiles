local icons = require("icons")
local colors = require("colors")
local settings = require("settings")

local ram = sbar.add("item", {
	position = "right",
	icon = {
		color = colors.pink,
		string = icons.memory_pressure,
	},
	label = {
		string = "??%",
		padding_left = 0,
		font = {
			style = settings.font.style_map["Bold"],
		},
	},
	update_freq = 30,
	updates = true,
	background = {
		color = colors.background,
	},
})

ram:subscribe({ "routine", "forced", "system_woke" }, function(env)
	sbar.exec("memory_pressure", function(output)
		local percentage = output:match("System%-wide memory free percentage: (%d+)")
		local load = 100 - tonumber(percentage)
		local new_color = colors.blue
		if load > 30 then
			if load < 60 then
				new_color = colors.yellow
			elseif load < 80 then
				new_color = colors.orange
			else
				new_color = colors.red
			end
		end
		ram:set({
			label = {
				color = new_color,
				string = load .. "%",
			},
		})
	end)
end)
