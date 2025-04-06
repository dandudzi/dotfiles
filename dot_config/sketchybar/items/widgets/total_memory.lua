local icons = require("icons")
local colors = require("colors")
local settings = require("settings")

local function exec(command)
	local handle = io.popen(command)
	local result = handle:read("*a")
	handle:close()
	return result
end

local ram = sbar.add("graph", "widgets.ram", 60, {
	position = "right",
	graph = { color = colors.blue },
	background = {
		height = 30,
		drawing = true,
	},
	icon = {
		color = colors.saphire,
		string = icons.ram,
	},
	label = {
		string = "??%",
		font = {
			size = 13,
			style = settings.font.style_map["Bold"],
		},
		align = "right",
		padding_right = 30,
		width = 30,
		y_offset = 4,
	},
	update_freq = 3,
	updates = true,
	padding_right = -20,
})

sbar.add("bracket", "widgets.ram.bracket", { ram.name }, {
	background = { color = colors.background },
})

sbar.add("item", "widgets.ram.padding", {
	position = "right",
	width = settings.group_paddings,
})

ram:subscribe({ "routine", "forced", "system_woke" }, function(env)
	sbar.exec('vm_stat | grep "page size" | sed "s/.*page size of //; s/ bytes//; s/)//"', function(output)
		local page_size = tonumber(output)
		local active_pages =
			tonumber(exec('vm_stat | grep "Pages active:" | sed "s/Pages active:[[:space:]]*//; s/[,.]//g; s/\\.//"'))
		local inactive_pages = tonumber(
			exec('vm_stat | grep "Pages inactive:" | sed "s/Pages inactive:[[:space:]]*//; s/[,.]//g; s/\\.//"')
		)
		local free_pages =
			tonumber(exec('vm_stat | grep "Pages wired" | sed "s/Pages wired down:[[:space:]]*//; s/[,.]//g; s/\\.//"'))
		local wired_pages =
			tonumber(exec('vm_stat | grep "Pages wired" | sed "s/Pages wired down:[[:space:]]*//; s/[,.]//g; s/\\.//"'))

		local total_used_pages = active_pages + inactive_pages + wired_pages
		local total_number_of_pages = total_used_pages + free_pages

		if page_size <= 0 or wired_pages <= 0 or inactive_pages <= 0 or active_pages <= 0 or free_pages <= 0 then
			ram:set({
				label = { string = "wrong data" },
			})
			return
		end
		local total_used_memory = (total_used_pages * page_size) / (1024 * 1024 * 1024)
		local total_used_memory_gb = string.format("%.2f", total_used_memory)
		local memory = (total_used_pages * 100) / total_number_of_pages
		if memory > 100 then
			memory = 100
		end
		ram:push({ memory / 100. })
		local new_color = colors.blue
		if memory > 70 then
			if memory < 80 then
				new_color = colors.yellow
			elseif memory < 90 then
				new_color = colors.orange
			else
				new_color = colors.red
			end
		end
		ram:set({
			graph = { color = new_color },
			label = { string = total_used_memory_gb .. " GB" },
		})
	end)
end)
