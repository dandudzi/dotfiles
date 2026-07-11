-- Add the sketchybar module to the package cpath
package.cpath = package.cpath .. ";" .. os.getenv("HOME") .. "/.local/share/sketchybar_lua/?.so"

local helpers_ok, helpers_exit_type, helpers_exit_code = os.execute("(cd helpers && make)")
if not helpers_ok then
  error(
    ("Failed to build SketchyBar helpers (%s: %s)"):format(
      tostring(helpers_exit_type),
      tostring(helpers_exit_code)
    )
  )
end
