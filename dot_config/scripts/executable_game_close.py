#!/usr/bin/env python3
import argparse
import subprocess
import sys
import textwrap


def sh(*args: str) -> None:
    subprocess.run(list(args), check=True)


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--open-timeout", type=float, default=10.0)
    ap.add_argument("--ui-timeout", type=float, default=20.0)
    args = ap.parse_args()

    # 1) Open both apps
    sh("open", "-a", "Nanoleaf Desktop")
 
    # 2..6) Wait + interact with Nanoleaf GUI via Accessibility
    applescript = """
    set PROC_NAME to "Nanoleaf Desktop"
    set OPEN_TIMEOUT to {open_timeout}
    set UI_TIMEOUT to {ui_timeout}
    set TARGET_LABEL to "Gaming Gaming"

    tell application "System Events"
        set t0 to (current date)

        repeat while (not (exists process PROC_NAME)) and (((current date) - t0) < OPEN_TIMEOUT)
            delay 0.2
        end repeat

        if not (exists process PROC_NAME) then
            error "Timeout: process didn't appear"
        end if

        tell process PROC_NAME
            set frontmost to true

            -- Wait for a window
            set t1 to (current date)
            repeat
                if (count of windows) > 0 then exit repeat
                if (((current date) - t1) > UI_TIMEOUT) then error "Timeout: window didn't appear"
                delay 0.2
            end repeat

        set w to window 1

        -- Find AXLink with matching title/description/label
        set t2 to (current date)
        set targetEl to missing value

        repeat
            set allEls to entire contents of w
            set targetEl to missing value

            repeat with e in allEls
                set roleVal to ""
                try
                    set roleVal to (value of attribute "AXRole" of e) as text
                end try

                if roleVal is "AXLink" then
                    set t to ""
                    set d to ""
                    set l to ""
                    try
                        set t to (value of attribute "AXTitle" of e) as text
                    end try
                    try
                        set d to (value of attribute "AXDescription" of e) as text
                    end try
                    try
                        set l to (value of attribute "AXLabel" of e) as text
                    end try

                    ignoring case
                        if (t is TARGET_LABEL) or (t contains TARGET_LABEL) or ¬
                           (d is TARGET_LABEL) or (d contains TARGET_LABEL) or ¬
                           (l is TARGET_LABEL) or (l contains TARGET_LABEL) then
                            set targetEl to e
                            exit repeat
                        end if
                    end ignoring
                end if
            end repeat

            if targetEl is not missing value then exit repeat

            if (((current date) - t2) > UI_TIMEOUT) then
                -- dump link titles/descriptions to help diagnose what attribute actually matches
                set dumpTxt to ""
                repeat with e in allEls
                    try
                        if ((value of attribute "AXRole" of e) as text) is "AXLink" then
                            set t to ""
                            set d to ""
                            try
                                set t to (value of attribute "AXTitle" of e) as text
                            end try
                            try
                                set d to (value of attribute "AXDescription" of e) as text
                            end try
                            set dumpTxt to dumpTxt & "AXLink: " & t & " | " & d & linefeed
                        end if
                    end try
                end repeat
                error "Timeout: couldn't find '" & TARGET_LABEL & "'" & linefeed & dumpTxt
            end if

            delay 0.2
        end repeat

        -- Press it
        try
            perform action "AXPress" of targetEl
        on error
            click targetEl
        end try

        set t3 to (current date)
        set bannerEl to missing value

        repeat
            set allEls to entire contents of w
            set bannerEl to missing value

            repeat with e in allEls
                try
                    if ((value of attribute "AXRole" of e) as text) is "AXGroup" then
                        set sr to ""
                        try
                            set sr to (value of attribute "AXSubrole" of e) as text
                        end try

                        if sr is "AXLandmarkBanner" then
                            set bannerEl to e
                            exit repeat
                        end if
                    end if
                end try
            end repeat

            if bannerEl is not missing value then exit repeat
            if (((current date) - t3) > UI_TIMEOUT) then error "Timeout: banner (AXLandmarkBanner) didn't appear"
            delay 0.2
        end repeat
        -- 2) Find deeply nested AXCheckBox inside the banner
        set t4 to (current date)
        set cb to missing value

        repeat
            set cb to missing value

            try
                set bannerKids to entire contents of bannerEl
            on error
                set bannerKids to {{}}
            end try

            repeat with e in bannerKids
                try
                    if ((value of attribute "AXRole" of e) as text) is "AXCheckBox" then
                        set cb to e
                        exit repeat
                    end if
                end try
            end repeat

            if cb is not missing value then exit repeat
            if (((current date) - t4) > UI_TIMEOUT) then error "Timeout: checkbox not found in banner"
            delay 0.2
        end repeat

        -- 3) If checkbox is disabled, wait until enabled; then if unchecked, check it
       set v to missing value
        try
            set v to value of attribute "AXValue" of cb
        end try

        set shouldUncheck to false

        -- checked: 1, mixed: 2
        try
            if (v as integer) is not 0 then
                set shouldUncheck to true
            end if
        end try

        -- checked: true
        try
            if (v as boolean) is true then
                set shouldUncheck to true
            end if
        end try

        -- string fallback
        set vText to ""
        try
            set vText to v as text
        end try

        ignoring case
            if vText is "1" then
                set shouldUncheck to true
            else if vText is "2" then
                set shouldUncheck to true
            else if vText is "true" then
                set shouldUncheck to true
            end if
        end ignoring

        if shouldUncheck then
            perform action "AXPress" of cb
        end if


        return "Clicked: " & TARGET_LABEL
        end tell
    end tell
    """.format( open_timeout=args.open_timeout,
        ui_timeout=args.ui_timeout,
    )

    out = run_osascript(applescript)
    if out:
        print(out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise

