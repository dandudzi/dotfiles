#!/usr/bin/env python3
"""Report structured tool-call usage from local Codex rollout JSONL sessions.

The parser intentionally reads only event metadata needed for statistics; it
does not include prompts, tool arguments, or tool outputs in its report.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_SESSIONS_DIR = Path.home() / ".codex" / "sessions"
TOOL_CALL_TYPES = {"function_call", "custom_tool_call"}


def tool_provider(name: str) -> str:
    """Return the configured tool/server name from a Codex tool-call name."""
    if name.startswith("mcp__"):
        parts = name.split("__", 2)
        return parts[1] if len(parts) > 1 and parts[1] else "mcp"
    return name.split(".", 1)[0]


def event_month(event: dict[str, Any], session_path: Path) -> str | None:
    """Get a month from the structured timestamp, then from Codex's path layout."""
    timestamp = event.get("timestamp")
    if isinstance(timestamp, str) and len(timestamp) >= 7:
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime("%Y-%m")
        except ValueError:
            pass
    parts = session_path.parts
    for index in range(len(parts) - 1):
        if len(parts[index]) == 4 and parts[index].isdigit() and len(parts[index + 1]) == 2:
            return f"{parts[index]}-{parts[index + 1]}"
    return None


def build_report(sessions_dir: Path) -> dict[str, Any]:
    """Scan session files and return aggregate, privacy-preserving statistics."""
    tool_calls: Counter[str] = Counter()
    tool_sessions: defaultdict[str, set[Path]] = defaultdict(set)
    month_calls: Counter[str] = Counter()
    month_sessions: defaultdict[str, set[Path]] = defaultdict(set)
    files_scanned = records_read = invalid_json_lines = tool_calls_total = 0

    for session_path in sorted(sessions_dir.rglob("*.jsonl")):
        if not session_path.is_file():
            continue
        files_scanned += 1
        try:
            lines = session_path.open(encoding="utf-8", errors="replace")
        except OSError as error:
            print(f"warning: cannot read {session_path}: {error}", file=sys.stderr)
            continue
        with lines:
            for line in lines:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    invalid_json_lines += 1
                    continue
                if not isinstance(event, dict):
                    continue
                payload = event.get("payload")
                if not isinstance(payload, dict) or payload.get("type") not in TOOL_CALL_TYPES:
                    continue
                name = payload.get("name")
                if not isinstance(name, str) or not name:
                    continue
                records_read += 1
                tool_calls_total += 1
                tool_calls[name] += 1
                tool_sessions[name].add(session_path)
                month = event_month(event, session_path)
                if month:
                    month_calls[month] += 1
                    month_sessions[month].add(session_path)

    tools = [
        {
            "name": name,
            "calls": calls,
            "sessions": len(tool_sessions[name]),
            "provider": tool_provider(name),
        }
        for name, calls in sorted(tool_calls.items(), key=lambda item: (-item[1], item[0]))
    ]
    months = [
        {"month": month, "tool_calls": month_calls[month], "sessions": len(month_sessions[month])}
        for month in sorted(month_calls)
    ]
    return {
        "sessions_dir": str(sessions_dir),
        "files_scanned": files_scanned,
        "records_read": records_read,
        "invalid_json_lines": invalid_json_lines,
        "tool_calls_total": tool_calls_total,
        "tools": tools,
        "months": months,
    }


def as_markdown(report: dict[str, Any]) -> str:
    """Render a compact, copyable report without exposing session content."""
    lines = [
        "# Codex tool usage",
        "",
        f"- Sessions scanned: {report['files_scanned']}",
        f"- Tool calls: {report['tool_calls_total']}",
        f"- Invalid JSONL lines skipped: {report['invalid_json_lines']}",
        "",
        "## Tools",
        "",
        "| Tool | Provider | Calls | Sessions |",
        "| --- | --- | ---: | ---: |",
    ]
    lines.extend(
        f"| `{tool['name']}` | {tool['provider']} | {tool['calls']} | {tool['sessions']} |"
        for tool in report["tools"]
    )
    lines.extend(["", "## By month", "", "| Month | Calls | Sessions |", "| --- | ---: | ---: |"])
    lines.extend(
        f"| {month['month']} | {month['tool_calls']} | {month['sessions']} |"
        for month in report["months"]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sessions-dir",
        type=Path,
        default=DEFAULT_SESSIONS_DIR,
        help=f"Codex session directory (default: {DEFAULT_SESSIONS_DIR})",
    )
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="Write the report to this file instead of stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.sessions_dir.is_dir():
        print(f"error: sessions directory does not exist: {args.sessions_dir}", file=sys.stderr)
        return 2
    report = build_report(args.sessions_dir)
    output = json.dumps(report, indent=2) + "\n" if args.format == "json" else as_markdown(report)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
