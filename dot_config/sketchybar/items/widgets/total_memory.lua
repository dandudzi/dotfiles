local icons = require("icons")
local colors = require("colors")
local settings = require("settings")

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
-- Function to parse vm_stat output
local function parse_vm_stat(vm_stat_output)
	local stats = {}

	-- Split the output into lines
	for line in vm_stat_output:gmatch("[^\r\n]+") do
		-- Match the relevant lines using patterns
		local page_size = line:match("page size of (%d+) bytes")
		if page_size then
			stats.page_size = tonumber(page_size)
		end

		local active = line:match("Pages active:%s*([%d%.]+)")
		if active then
			stats.active_pages = tonumber(active)
		end

		local inactive = line:match("Pages inactive:%s*([%d%.]+)")
		if inactive then
			stats.inactive_pages = tonumber(inactive)
		end

		local free = line:match("Pages free:%s*([%d%.]+)")
		if free then
			stats.free_pages = tonumber(free)
		end

		local wired = line:match("Pages wired down:%s*([%d%.]+)")
		if wired then
			stats.wired_pages = tonumber(wired)
		end

		local speculative = line:match("Pages speculative:%s*([%d%.]+)")
		if speculative then
			stats.speculative_pages = tonumber(speculative)
		end
		local compressed = line:match("Pages occupied by compressor:%s*([%d%.]+)")
		if compressed then
			stats.compressed_pages = tonumber(compressed)
		end
	end

	return stats
end

ram:subscribe({ "routine", "forced", "system_woke" }, function(env)
	sbar.exec("vm_stat", function(output)
		local stats = parse_vm_stat(output)
		local page_size = stats.page_size
		local active_pages = stats.active_pages
		local inactive_pages = stats.inactive_pages
		local free_pages = stats.free_pages
		local wired_pages = stats.wired_pages
		local speculative_pages = stats.speculative_pages
		local compressed_pages = stats.compressed_pages

		local total_used_pages = active_pages + inactive_pages + wired_pages + speculative_pages
		local total_number_of_pages = total_used_pages + free_pages + compressed_pages

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
