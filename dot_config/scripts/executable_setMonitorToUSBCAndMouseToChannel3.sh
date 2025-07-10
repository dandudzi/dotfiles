#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title WorkMac
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🤖

# Documentation:
# @raycast.author Dudziak
# @raycast.authorURL https://raycast.com/Dudziak

./hidapitester/hidapitester --vidpid 046D:B020 --usagePage 0xFF43 --usage 0x0202 --open --length 20 --send-output 0x11,0x00,0x0C,0x1C,0x02
./m1ddc/m1ddc set input 49
osascript -e 'tell application "System Events" to keystroke "q" using {control down, command down}'
