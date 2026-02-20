#!/usr/bin/env python3
"""Nanoleaf gaming automation — optimized single-pass AppleScript."""
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
    ap = argparse.ArgumentParser(description="Nanoleaf gaming automation")
    ap.add_argument("--ui-timeout", type=float, default=10.0)
    args = ap.parse_args()

    # 1) Open Nanoleaf Desktop
    subprocess.run(["open", "-a", "Nanoleaf Desktop"], check=True)

    # 2) Navigate to Gaming and enable the toggle
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

        -- Single scan: find Gaming link and click it
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

        -- Wait for Gaming page to load
        delay 1.5

        -- Single scan: find banner checkbox in one pass
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

                -- Once we find the banner, the next AXCheckBox is our target
                if r is "AXGroup" and not bannerFound then
                    set sr to ""
                    try
                        set sr to (value of attribute "AXSubrole" of e) as text
                    end try
                    if sr is "AXLandmarkBanner" then
                        set bannerFound to true
                        -- Search inside the banner for checkbox
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
            if (((current date) - t3) > UI_TIMEOUT) then error "Timeout: toggle not found"
            delay 0.2
        end repeat

        -- Toggle if off
        set v to missing value
        try
            set v to value of attribute "AXValue" of cb
        end try

        set needsPress to false
        try
            if v is 0 then set needsPress to true
        end try
        try
            if v is false then set needsPress to true
        end try
        try
            if (v as text) is "0" then set needsPress to true
        end try
        try
            if (v as text) is "false" then set needsPress to true
        end try

        if needsPress then
            perform action "AXPress" of cb
        end if

        if needsPress then
            return "Gaming mode enabled"
        else
            return "Gaming mode already active"
        end if
    end tell
end tell
"""

    out = run_osascript(applescript)
    if out:
        print(out)

    # 3) Launch GeForce NOW
    try:
        subprocess.run(["open", "-a", "GeForceNOW"], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Gaming mode activated, but failed to launch GeForceNOW: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise
