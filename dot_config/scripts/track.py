#!/usr/bin/env python3
"""Fitness tracker dialog — replaces kitty-dependent do_track() with osascript."""

import json
import os
import re
import subprocess
import sys
import time

STATE_FILE = os.path.expanduser("~/.fitness-state.json")
PROMPT_FILE = os.path.expanduser("~/.fitness-prompt.json")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SUPPRESS_FOCUS_MODES = {"Do Not Disturb", "Sleep", "Work"}


def get_active_focus():
    """Return the active Focus Mode name, or None."""
    try:
        result = subprocess.run(
            ["shortcuts", "run", "Get Focus Mode"],
            capture_output=True, text=True, timeout=5
        )
        name = result.stdout.strip()
        return name if name and name != "None" else None
    except subprocess.TimeoutExpired:
        return None


def check_triggers(state, prompt_data, now=None):
    """Check if it's time to trigger a workout prompt.

    Returns (should_trigger, reason, remaining_min).
    """
    if now is None:
        now = int(time.time())

    dur_min = state.get("duration_between_sets_min", 30)
    dur_prompts = state.get("duration_between_sets_prompts", 10)
    last_ts = state.get("last_reminder_timestamp", 0)
    count = prompt_data.get("count", 0)

    elapsed = now - last_ts
    time_trigger = elapsed >= dur_min * 60
    last_checked = prompt_data.get("last_checked_count", 0)
    prompt_trigger = count > 0 and (count // dur_prompts) > (last_checked // dur_prompts)

    if time_trigger and prompt_trigger:
        return (True, "time+prompts", 0)
    elif time_trigger:
        return (True, "time", 0)
    elif prompt_trigger:
        return (True, "prompts", 0)
    else:
        remaining = max(0, (dur_min * 60 - elapsed) // 60)
        return (False, "not_yet", remaining)


def build_summary(state):
    """Human-readable progress string."""
    ex = state.get("exercise", {})
    goal = state.get("goal", 10000)
    rounds = state.get("rounds_completed", 0)
    pushups = ex.get("pushups", 0)
    squats = ex.get("squats", 0)
    situps = ex.get("situps", 0)
    avg = ((pushups + squats + situps) / 3 / goal * 100) if goal else 0
    lines = [
        f"Rounds: {rounds}",
        f"Pushups: {pushups}/{goal} ({pushups/goal*100:.1f}%)",
        f"Squats:  {squats}/{goal} ({squats/goal*100:.1f}%)",
        f"Situps:  {situps}/{goal} ({situps/goal*100:.1f}%)",
        f"Average: {avg:.1f}%",
    ]
    return "\n".join(lines)


def build_dialog_script(state):
    """AppleScript dialog with progress info and text input for sets."""
    summary = build_summary(state)
    default_sets = state.get("number_of_sets", 10)
    # Escape for AppleScript string (double backslashes and quotes)
    escaped = summary.replace("\\", "\\\\").replace('"', '\\"')
    prompt_text = f"Time to work out!\\n\\n{escaped}\\n\\nSets to log:"
    return (
        f'tell application "System Events"\n'
        f'activate\n'
        f'display dialog "{prompt_text}" '
        f'default answer "{default_sets}" '
        f'buttons {{"Log", "Snooze 1 min"}} default button "Snooze 1 min" '
        f'giving up after 300 '
        f'with title "Fitness Tracker"\n'
        f'end tell'
    )


def parse_dialog_output(output):
    """Parse osascript dialog output like 'button returned:Log, text returned:10, gave up:false'."""
    button = ""
    text = ""
    gave_up = False
    for part in output.split(", "):
        if part.startswith("button returned:"):
            button = part.split(":", 1)[1]
        elif part.startswith("text returned:"):
            text = part.split(":", 1)[1]
        elif part.startswith("gave up:"):
            gave_up = part.split(":", 1)[1].strip().lower() == "true"
    return button, text, gave_up


def show_dialog(state):
    """Show osascript dialog and return (button, text, gave_up)."""
    script = build_dialog_script(state)
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None, None, True
    return parse_dialog_output(result.stdout.strip())


def reset_prompt_counter(prompt_file):
    """Reset the prompt counter to 0."""
    with open(prompt_file, "w") as f:
        json.dump({"count": 0, "last_checked_count": 0}, f)


def do_track(state_file=None, prompt_file=None):
    """Main orchestration: check triggers, show dialog, handle response."""
    if state_file is None:
        state_file = STATE_FILE
    if prompt_file is None:
        prompt_file = PROMPT_FILE

    if not os.path.exists(state_file):
        print("No local state. Run 'fitness-track -r' first.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(prompt_file):
        with open(prompt_file, "w") as f:
            json.dump({"count": 0, "last_checked_count": 0}, f)

    with open(state_file) as f:
        state = json.load(f)
    with open(prompt_file) as f:
        prompt_data = json.load(f)

    triggered, reason, remaining = check_triggers(state, prompt_data)

    # Update last_checked_count so next check knows where we left off
    prompt_data["last_checked_count"] = prompt_data.get("count", 0)
    with open(prompt_file, "w") as f:
        json.dump(prompt_data, f)

    if not triggered:
        print(f"Not time yet. Next check in ~{remaining} min.")
        return

    focus = get_active_focus()
    if focus and focus in SUPPRESS_FOCUS_MODES:
        state["last_reminder_timestamp"] = int(time.time())
        with open(state_file, "w") as f:
            json.dump(state, f)
        print(f"Focus mode active ({focus}), skipping reminder.")
        return

    script = build_dialog_script(state)
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        return

    button, text, gave_up = parse_dialog_output(result.stdout.strip())

    if gave_up or button == "Snooze 1 min":
        return

    if button == "Log":
        sets = text.strip() if text.strip() else str(state.get("number_of_sets", 10))
        fitness_track = os.path.join(SCRIPT_DIR, "fitness-track")
        subprocess.run([fitness_track, "-l", sets], capture_output=True, text=True)
        reset_prompt_counter(prompt_file)


if __name__ == "__main__":
    do_track()
