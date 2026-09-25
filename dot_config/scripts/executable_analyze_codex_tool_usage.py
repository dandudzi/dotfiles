#!/usr/bin/env python3
"""Report configured MCP tool-call usage from local Codex rollout JSONL sessions.

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

# This is the reviewed method inventory for the MCPs configured in Codex. Older
# session logs store bare method names, so it is intentionally explicit rather
# than treating every structured tool call as an MCP call.
MCP_METHODS = {
    "context7": {"query_docs", "resolve_library_id"},
    "exa": {"web_fetch_exa", "web_search_exa"},
    "gitnexus": {
        "api_impact", "check", "context", "cypher", "detect_changes", "explain", "group_list",
        "group_sync", "impact", "list_repos", "pdg_query", "query", "rename", "route_map",
        "shape_check", "tool_map", "trace",
    },
    "linear": {
        "create_attachment", "create_attachment_from_upload", "create_issue_label", "delete_attachment",
        "delete_comment", "delete_diff_comment", "delete_status_update", "extract_images", "get_agent_skill",
        "get_attachment", "get_diff", "get_diff_threads", "get_document", "get_issue", "get_issue_status",
        "get_milestone", "get_notifications", "get_project", "get_release", "get_release_note",
        "get_status_updates", "get_team", "get_template", "get_triage_responsibility", "get_user",
        "get_workspace", "list_agent_skills", "list_comments", "list_custom_views", "list_cycles", "list_diffs",
        "list_documents", "list_issue_labels", "list_issue_statuses", "list_issues", "list_milestones",
        "list_project_labels", "list_projects", "list_release_notes", "list_release_pipelines", "list_releases",
        "list_teams", "list_templates", "list_users", "mark_notification", "merge_diff",
        "prepare_attachment_upload", "resolve_diff_thread", "restore_issue_label", "restore_project_label",
        "retire_issue_label", "retire_project_label", "save_comment", "save_diff_comment", "save_document",
        "save_issue", "save_issue_label", "save_milestone", "save_project", "save_project_label", "save_release",
        "save_release_note", "save_status_update", "search_documentation", "share_issue", "submit_diff_review",
        "unshare_issue", "update_diff",
    },
    "mermaid": {"generate_mermaid_diagram"},
    "playwright": {
        "browser_click", "browser_close", "browser_console_messages", "browser_drag", "browser_drop",
        "browser_evaluate", "browser_file_upload", "browser_fill_form", "browser_find", "browser_handle_dialog",
        "browser_hover", "browser_navigate", "browser_navigate_back", "browser_network_request",
        "browser_network_requests", "browser_press_key", "browser_resize", "browser_run_code_unsafe",
        "browser_select_option", "browser_snapshot", "browser_tabs", "browser_take_screenshot", "browser_type",
        "browser_wait_for",
    },
    "serena": {
        "activate_project", "delete_memory", "edit_memory", "find_declaration", "find_implementations",
        "find_referencing_symbols", "find_symbol", "get_current_config", "get_diagnostics_for_file",
        "get_symbols_overview", "initial_instructions", "insert_after_symbol", "insert_before_symbol",
        "list_memories", "onboarding", "open_dashboard", "read_memory", "rename_memory", "rename_symbol",
        "replace_in_files", "replace_symbol_body", "safe_delete_symbol", "search_for_pattern", "write_memory",
    },
}
BARE_METHOD_PROVIDERS = {
    method: provider for provider, methods in MCP_METHODS.items() for method in methods
}


def tool_provider(name: str) -> str | None:
    """Return the configured MCP provider for a call name, or None when excluded."""
    if name.startswith("mcp__"):
        parts = name.split("__", 2)
        if len(parts) != 3 or parts[1] not in MCP_METHODS or parts[2] not in MCP_METHODS[parts[1]]:
            return None
        return parts[1]
    return BARE_METHOD_PROVIDERS.get(name)


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
    provider_calls: Counter[str] = Counter()
    provider_sessions: defaultdict[str, set[Path]] = defaultdict(set)
    month_calls: Counter[str] = Counter()
    month_sessions: defaultdict[str, set[Path]] = defaultdict(set)
    files_scanned = mcp_tool_call_records = invalid_json_lines = tool_calls_total = 0

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
                provider = tool_provider(name)
                if provider is None:
                    continue
                mcp_tool_call_records += 1
                tool_calls_total += 1
                tool_calls[name] += 1
                tool_sessions[name].add(session_path)
                provider_calls[provider] += 1
                provider_sessions[provider].add(session_path)
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
    providers = [
        {"name": name, "calls": calls, "sessions": len(provider_sessions[name])}
        for name, calls in sorted(provider_calls.items(), key=lambda item: (-item[1], item[0]))
    ]
    return {
        "sessions_dir": str(sessions_dir),
        "files_scanned": files_scanned,
        "mcp_tool_call_records": mcp_tool_call_records,
        "invalid_json_lines": invalid_json_lines,
        "tool_calls_total": tool_calls_total,
        "tools": tools,
        "providers": providers,
        "months": months,
    }


def as_markdown(report: dict[str, Any]) -> str:
    """Render a compact, copyable report without exposing session content."""
    lines = [
        "# Codex MCP tool usage",
        "",
        f"- Sessions scanned: {report['files_scanned']}",
        f"- MCP tool calls: {report['tool_calls_total']}",
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
    lines.extend(["", "## MCP calls by server", "", "| MCP server | Calls | Sessions |", "| --- | ---: | ---: |"])
    lines.extend(
        f"| {provider['name']} | {provider['calls']} | {provider['sessions']} |"
        for provider in report["providers"]
    )
    lines.extend(["", "```text"])
    maximum = max((provider["calls"] for provider in report["providers"]), default=0)
    for provider in report["providers"]:
        width = max(1, round(provider["calls"] / maximum * 30)) if maximum else 0
        lines.append(f"{provider['name']:<10} {'#' * width} {provider['calls']}")
    lines.extend(["```", "", "## By month", "", "| Month | Calls | Sessions |", "| --- | ---: | ---: |"])
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
