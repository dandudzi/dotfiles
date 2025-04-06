local function exec(command)
	local handle = io.popen(command)
	local result = handle:read("*a")
	handle:close()
	return result
end

device_name = exec('system_profiler SPHardwareDataType | grep "Model Identifier"')
if string.find(device_name, "MacBook") ~= nil then
	require("items.widgets.battery")
end

require("items.widgets.volume")
require("items.widgets.wifi")
require("items.widgets.memory_pressure")
require("items.widgets.total_memory")
require("items.widgets.cpu")
