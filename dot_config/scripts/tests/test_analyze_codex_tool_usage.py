"""Regression tests for the Codex session tool-usage report."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "analyze_codex_tool_usage.py"


def event(timestamp: str, name: str, payload_type: str = "function_call") -> dict:
    return {
        "timestamp": timestamp,
        "type": "response_item",
        "payload": {"type": payload_type, "name": name},
    }


class ToolUsageReportTests(unittest.TestCase):
    def test_json_report_counts_calls_sessions_months_and_bad_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sessions_dir = Path(temporary_directory)
            first = sessions_dir / "2026" / "07" / "01" / "rollout-first.jsonl"
            second = sessions_dir / "2026" / "07" / "02" / "rollout-second.jsonl"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            first.write_text(
                "\n".join(
                    [
                        json.dumps(event("2026-07-01T10:00:00Z", "functions.exec")),
                        json.dumps(event("2026-07-01T10:01:00Z", "mcp__exa__web_search_exa")),
                        "not JSON",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            second.write_text(
                "\n".join(
                    [
                        json.dumps(event("2026-07-02T10:00:00Z", "mcp__exa__web_search_exa")),
                        json.dumps(event("2026-07-02T10:01:00Z", "functions.exec", "custom_tool_call")),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--sessions-dir", str(sessions_dir), "--format", "json"],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(completed.stdout)

        self.assertEqual(report["files_scanned"], 2)
        self.assertEqual(report["records_read"], 4)
        self.assertEqual(report["invalid_json_lines"], 1)
        self.assertEqual(report["tool_calls_total"], 4)
        self.assertEqual(
            report["tools"],
            [
                {"name": "functions.exec", "calls": 2, "sessions": 2, "provider": "functions"},
                {"name": "mcp__exa__web_search_exa", "calls": 2, "sessions": 2, "provider": "exa"},
            ],
        )
        self.assertEqual(
            report["months"],
            [{"month": "2026-07", "tool_calls": 4, "sessions": 2}],
        )


if __name__ == "__main__":
    unittest.main()
