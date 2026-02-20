#!/usr/bin/env python3
"""Stop gaming session — quit GeForce NOW, disable gaming mode, power off Nanoleaf, quit app."""
import argparse
import subprocess
import sys


def run_osascript(script: str) -> str:
    p = subprocess.run(
        ["osascript", "-"],
        input=script,
        text=True,
        capture_output=True,
    )
    if p.returncode != 0:
        err = (p.stderr or p.stdout).strip()
        raise RuntimeError(err or f"osascript failed with code {p.returncode}")
    return (p.stdout or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Stop gaming session")
    ap.add_argument("--ui-timeout", type=float, default=10.0)
    args = ap.parse_args()

    # 1) Quit GeForce NOW
    try:
        run_osascript('tell application "GeForceNOW" to quit')
        print("GeForceNOW quit")
    except RuntimeError:
        print("GeForceNOW not running, skipping")

    # 2) Open Nanoleaf Desktop, disable gaming, then power off the strip
    subprocess.run(["open", "-a", "Nanoleaf Desktop"], check=True)

    applescript = f"""\
set UI_TIMEOUT to {args.ui_timeout}
set PROC_NAME to "Nanoleaf Desktop"

tell application "System Events"
    -- Wait for process
    set t0 to (current date)
    repeat while (not (exists process PROC_NAME)) and (((current date) - t0) < UI_TIMEOUT)
        delay 0.2
    end repeat
    if not (exists process PROC_NAME) then error "Timeout: process didn't appear"

    tell process PROC_NAME
        set frontmost to true

        -- Wait for window
        set t1 to (current date)
        repeat
            if (count of windows) > 0 then exit repeat
            if (((current date) - t1) > UI_TIMEOUT) then error "Timeout: window didn't appear"
            delay 0.2
        end repeat

        set w to window 1

        -------------------------------------------------------
        -- STEP A: Navigate to Gaming and disable the toggle --
        -------------------------------------------------------
        set t2 to (current date)
        set clicked to false
        repeat
            set allEls to entire contents of w
            repeat with e in allEls
                set r to ""
                try
                    set r to (value of attribute "AXRole" of e) as text
                end try
                if r is "AXLink" then
                    set d to ""
                    try
                        set d to (value of attribute "AXDescription" of e) as text
                    end try
                    if d contains "Gaming" then
                        try
                            perform action "AXPress" of e
                        on error
                            click e
                        end try
                        set clicked to true
                        exit repeat
                    end if
                end if
            end repeat
            if clicked then exit repeat
            if (((current date) - t2) > UI_TIMEOUT) then error "Timeout: Gaming link not found"
            delay 0.2
        end repeat

        delay 1.5

        -- Find banner checkbox (gaming toggle)
        set t3 to (current date)
        set cb to missing value
        repeat
            set allEls to entire contents of w
            set bannerFound to false
            repeat with e in allEls
                set r to ""
                try
                    set r to (value of attribute "AXRole" of e) as text
                end try
                if r is "AXGroup" and not bannerFound then
                    set sr to ""
                    try
                        set sr to (value of attribute "AXSubrole" of e) as text
                    end try
                    if sr is "AXLandmarkBanner" then
                        set bannerFound to true
                        try
                            set bannerKids to entire contents of e
                        on error
                            set bannerKids to {{}}
                        end try
                        repeat with k in bannerKids
                            try
                                if ((value of attribute "AXRole" of k) as text) is "AXCheckBox" then
                                    set cb to k
                                    exit repeat
                                end if
                            end try
                        end repeat
                        exit repeat
                    end if
                end if
            end repeat
            if cb is not missing value then exit repeat
            if (((current date) - t3) > UI_TIMEOUT) then error "Timeout: gaming toggle not found"
            delay 0.2
        end repeat

        -- Turn OFF gaming if currently on
        set v to missing value
        try
            set v to value of attribute "AXValue" of cb
        end try
        set needsPress to false
        try
            if v is 1 then set needsPress to true
        end try
        try
            if v is true then set needsPress to true
        end try
        try
            if (v as text) is "1" then set needsPress to true
        end try
        try
            if (v as text) is "true" then set needsPress to true
        end try
        if needsPress then
            perform action "AXPress" of cb
            log "Gaming mode disabled"
        else
            log "Gaming mode already off"
        end if

        delay 0.5

        ---------------------------------------------------------
        -- STEP B: Navigate to Dashboard and power off the strip
        ---------------------------------------------------------
        set t4 to (current date)
        set clicked to false
        repeat
            set allEls to entire contents of w
            repeat with e in allEls
                set r to ""
                try
                    set r to (value of attribute "AXRole" of e) as text
                end try
                if r is "AXLink" then
                    set d to ""
                    try
                        set d to (value of attribute "AXDescription" of e) as text
                    end try
                    if d contains "Dashboard" then
                        try
                            perform action "AXPress" of e
                        on error
                            click e
                        end try
                        set clicked to true
                        exit repeat
                    end if
                end if
            end repeat
            if clicked then exit repeat
            if (((current date) - t4) > UI_TIMEOUT) then error "Timeout: Dashboard link not found"
            delay 0.2
        end repeat

        delay 1.5

        -- Find the device power checkbox on the dashboard
        -- The device "PC Screen Mirror LS 004P" has a checkbox right after it
        -- We look for the second AXCheckBox (first is room toggle, second is device toggle)
        set t5 to (current date)
        set deviceCb to missing value
        repeat
            set allEls to entire contents of w
            set cbCount to 0
            repeat with e in allEls
                set r to ""
                try
                    set r to (value of attribute "AXRole" of e) as text
                end try
                if r is "AXCheckBox" then
                    set cbCount to cbCount + 1
                    if cbCount is 2 then
                        set deviceCb to e
                        exit repeat
                    end if
                end if
            end repeat
            if deviceCb is not missing value then exit repeat
            if (((current date) - t5) > UI_TIMEOUT) then error "Timeout: device power toggle not found"
            delay 0.2
        end repeat

        -- Turn OFF device if currently on
        set dv to missing value
        try
            set dv to value of attribute "AXValue" of deviceCb
        end try
        set needsPress to false
        try
            if dv is 1 then set needsPress to true
        end try
        try
            if dv is true then set needsPress to true
        end try
        try
            if (dv as text) is "1" then set needsPress to true
        end try
        try
            if (dv as text) is "true" then set needsPress to true
        end try
        if needsPress then
            perform action "AXPress" of deviceCb
            return "Nanoleaf powered off"
        else
            return "Nanoleaf already off"
        end if
    end tell
end tell
"""

    out = run_osascript(applescript)
    if out:
        print(out)

    # 3) Quit Nanoleaf Desktop
    try:
        run_osascript('tell application "Nanoleaf Desktop" to quit')
        print("Nanoleaf Desktop quit")
    except RuntimeError:
        pass

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise
