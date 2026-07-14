"""Regression tests for import-ledger decision revision and scoped verification."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "import_ledger.py"

V3_SCHEMA = """
CREATE TABLE schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
INSERT INTO schema_meta(key, value) VALUES ('schema_version', '3');
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    source_key TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN
        ('open', 'imported', 'reviewed', 'completed', 'failed')),
    started_at TEXT NOT NULL,
    imported_at TEXT,
    completed_at TEXT,
    cleaned_at TEXT,
    resolution_status TEXT NOT NULL DEFAULT 'pending' CHECK
        (resolution_status IN ('pending', 'resolved')),
    resolved_at TEXT
);
CREATE TABLE source_items (
    item_id INTEGER PRIMARY KEY,
    source_key TEXT NOT NULL,
    source_relative_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    UNIQUE (source_key, source_relative_path, file_name, file_type)
);
CREATE TABLE fingerprint_versions (
    version_id INTEGER PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES source_items(item_id),
    fingerprint TEXT NOT NULL CHECK (length(fingerprint) = 64),
    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
    raw_hash TEXT NOT NULL CHECK (length(raw_hash) = 64),
    normalized_hash TEXT NOT NULL CHECK (length(normalized_hash) = 64),
    previous_version_id INTEGER REFERENCES fingerprint_versions(version_id),
    first_seen_run_id TEXT NOT NULL REFERENCES runs(run_id),
    recorded_at TEXT NOT NULL
);
CREATE TABLE run_items (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    version_id INTEGER NOT NULL REFERENCES fingerprint_versions(version_id),
    classification TEXT NOT NULL CHECK (classification IN
        ('new', 'changed', 'unchanged', 'conflict', 'resume',
         'retry', 'interrupted', 'failed')),
    state TEXT NOT NULL CHECK (state IN
        ('quarantined', 'reviewed', 'integrated', 'skipped',
         'discarded', 'failed')),
    quarantine_path TEXT,
    review_classification TEXT,
    review_report TEXT,
    decision TEXT,
    destination TEXT,
    destination_hash TEXT CHECK
        (destination_hash IS NULL OR length(destination_hash) = 64),
    integrated_at TEXT,
    cleaned_at TEXT,
    review_group TEXT,
    loss_details TEXT,
    loss_acknowledged INTEGER NOT NULL DEFAULT 0 CHECK
        (loss_acknowledged IN (0, 1)),
    decision_manifest TEXT,
    PRIMARY KEY (run_id, version_id),
    CHECK (state != 'quarantined' OR quarantine_path IS NOT NULL)
);
CREATE TABLE integration_outputs (
    output_id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    version_id INTEGER NOT NULL,
    destination TEXT NOT NULL,
    destination_hash TEXT NOT NULL CHECK (length(destination_hash) = 64),
    output_role TEXT NOT NULL CHECK (output_role IN ('primary', 'additional')),
    transformation TEXT,
    integrated_at TEXT NOT NULL,
    UNIQUE (run_id, version_id, destination),
    FOREIGN KEY (run_id, version_id) REFERENCES run_items(run_id, version_id)
);
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ImportLedgerFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.vault = self.root / "vault"
        self.vault.mkdir()
        self.db = self.vault / "_Imports" / "imports.sqlite3"
        result = self.run_cli("init", "--db", self.db)
        self.assertEqual(result.returncode, 0, result.stderr)

    def run_cli(self, *args: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *(str(arg) for arg in args)],
            capture_output=True,
            text=True,
            check=False,
        )

    def json_result(self, result: subprocess.CompletedProcess[str]) -> dict:
        stream = result.stdout if result.returncode == 0 else result.stderr
        try:
            value = json.loads(stream)
        except json.JSONDecodeError as exc:
            self.fail(
                f"command did not return JSON (exit {result.returncode}): "
                f"stdout={result.stdout!r} stderr={result.stderr!r}; {exc}"
            )
        self.assertIsInstance(value, dict)
        return value

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def create_v3_database(self, *, orphan_output: bool = False) -> tuple[Path, dict]:
        db = self.root / ("legacy-orphan.sqlite3" if orphan_output else "legacy.sqlite3")
        destination_hash = sha256(b"legacy output\n")
        marker = sha256(b"legacy source")
        with sqlite3.connect(db) as connection:
            connection.executescript(V3_SCHEMA)
            connection.execute(
                """
                INSERT INTO runs(
                    run_id, source_key, status, started_at,
                    resolution_status, resolved_at
                ) VALUES ('legacy-run', 'source:legacy', 'reviewed', ?, 'resolved', ?)
                """,
                ("2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z"),
            )
            connection.execute(
                """
                INSERT INTO source_items(
                    item_id, source_key, source_relative_path, file_name, file_type
                ) VALUES (1, 'source:legacy', 'Source/legacy.md', 'legacy.md', 'md')
                """
            )
            connection.execute(
                """
                INSERT INTO fingerprint_versions(
                    version_id, item_id, fingerprint, size_bytes, raw_hash,
                    normalized_hash, first_seen_run_id, recorded_at
                ) VALUES (1, 1, ?, 14, ?, ?, 'legacy-run', ?)
                """,
                (marker, marker, marker, "2026-01-01T00:00:00Z"),
            )
            connection.execute(
                """
                INSERT INTO run_items(
                    run_id, version_id, classification, state, quarantine_path,
                    review_classification, decision, destination,
                    destination_hash, integrated_at, loss_acknowledged,
                    decision_manifest
                ) VALUES (
                    'legacy-run', 1, 'new', 'integrated',
                    '_Imports/Quarantine/legacy-run/legacy.md', 'unique',
                    'integrate', 'Notes/legacy.md', ?, ?, 1, ?
                )
                """,
                (
                    destination_hash,
                    "2026-01-01T00:00:01Z",
                    json.dumps({"owner_decision": "keep"}),
                ),
            )
            connection.execute(
                """
                INSERT INTO integration_outputs(
                    output_id, run_id, version_id, destination,
                    destination_hash, output_role, transformation, integrated_at
                ) VALUES (42, 'legacy-run', ?, 'Notes/legacy.md', ?, 'primary', ?, ?)
                """,
                (
                    999 if orphan_output else 1,
                    destination_hash,
                    json.dumps({"owner_decision": "keep"}),
                    "2026-01-01T00:00:01Z",
                ),
            )
        return db, {
            "destination_hash": destination_hash,
            "marker": marker,
        }

    def add_integrated_run(
        self,
        run_id: str,
        *,
        destination_exists: bool,
        relative_path: str | None = None,
    ) -> dict[str, object]:
        relative_path = relative_path or f"Source/{run_id}.md"
        destination = f"Notes/{run_id}.md"
        quarantine = f"_Imports/Quarantine/{run_id}/{Path(relative_path).name}"
        content = f"destination for {run_id}\n".encode()
        destination_hash = sha256(content)

        quarantine_path = self.vault / quarantine
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        quarantine_path.write_text(f"source for {run_id}\n", encoding="utf-8")
        destination_path = self.vault / destination
        if destination_exists:
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            destination_path.write_bytes(content)

        marker = sha256(run_id.encode())
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO runs(
                    run_id, source_key, status, started_at,
                    resolution_status, resolved_at
                ) VALUES (?, ?, 'reviewed', ?, 'resolved', ?)
                """,
                (run_id, f"source:{run_id}", "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z"),
            )
            cursor = connection.execute(
                """
                INSERT INTO source_items(
                    source_key, source_relative_path, file_name, file_type
                ) VALUES (?, ?, ?, 'md')
                """,
                (f"source:{run_id}", relative_path, Path(relative_path).name),
            )
            item_id = cursor.lastrowid
            cursor = connection.execute(
                """
                INSERT INTO fingerprint_versions(
                    item_id, fingerprint, size_bytes, raw_hash,
                    normalized_hash, first_seen_run_id, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    marker,
                    quarantine_path.stat().st_size,
                    sha256(quarantine_path.read_bytes()),
                    sha256(quarantine_path.read_bytes()),
                    run_id,
                    "2026-01-01T00:00:00Z",
                ),
            )
            version_id = cursor.lastrowid
            connection.execute(
                """
                INSERT INTO run_items(
                    run_id, version_id, classification, state,
                    quarantine_path, review_classification, decision,
                    destination, destination_hash, integrated_at,
                    loss_acknowledged, decision_manifest
                ) VALUES (?, ?, 'new', 'integrated', ?, 'unique', 'integrate',
                          ?, ?, ?, 1, ?)
                """,
                (
                    run_id,
                    version_id,
                    quarantine,
                    destination,
                    destination_hash,
                    "2026-01-01T00:00:01Z",
                    json.dumps({"owner_decision": "keep"}),
                ),
            )
            connection.execute(
                """
                INSERT INTO integration_outputs(
                    run_id, version_id, destination, destination_hash,
                    output_role, transformation, integrated_at
                ) VALUES (?, ?, ?, ?, 'primary', ?, ?)
                """,
                (
                    run_id,
                    version_id,
                    destination,
                    destination_hash,
                    json.dumps({"owner_decision": "keep"}),
                    "2026-01-01T00:00:01Z",
                ),
            )
        return {
            "run_id": run_id,
            "version_id": version_id,
            "relative_path": relative_path,
            "destination": destination,
            "destination_hash": destination_hash,
        }

    def add_reviewed_run(self, run_id: str) -> dict[str, object]:
        relative_path = f"Source/{run_id}.md"
        source = self.root / "source" / relative_path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"source for {run_id}\n", encoding="utf-8")
        quarantine = f"_Imports/Quarantine/{run_id}/{Path(relative_path).name}"
        quarantine_path = self.vault / quarantine
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        quarantine_path.write_bytes(source.read_bytes())
        report = self.vault / "_Imports" / "Reviews" / f"{run_id}.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(f"# Review {run_id}\n", encoding="utf-8")

        recorded = self.run_cli(
            "record-import",
            "--db",
            self.db,
            "--file",
            source,
            "--source-key",
            f"source:{run_id}",
            "--relative-path",
            relative_path,
            "--run-id",
            run_id,
            "--vault-root",
            self.vault,
            "--quarantine-path",
            quarantine,
        )
        self.assertEqual(recorded.returncode, 0, self.json_result(recorded))
        reviewed = self.run_cli(
            "review",
            "--db",
            self.db,
            "--run-id",
            run_id,
            "--relative-path",
            relative_path,
            "--vault-root",
            self.vault,
            "--classification",
            "unique",
            "--report",
            report,
        )
        self.assertEqual(reviewed.returncode, 0, self.json_result(reviewed))
        return {
            "run_id": run_id,
            "source": source,
            "source_key": f"source:{run_id}",
            "relative_path": relative_path,
            "quarantine": quarantine,
            "quarantine_path": quarantine_path,
        }

    def integrate_reviewed_run(self, run_id: str) -> dict[str, object]:
        fixture = self.add_reviewed_run(run_id)
        destination = f"Notes/{run_id}.md"
        destination_path = self.vault / destination
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        destination_path.write_text(f"destination for {run_id}\n", encoding="utf-8")
        integrated = self.run_cli(
            "integrate",
            "--db",
            self.db,
            "--run-id",
            run_id,
            "--relative-path",
            fixture["relative_path"],
            "--vault-root",
            self.vault,
            "--decision",
            "integrate",
            "--destination",
            destination,
        )
        self.assertEqual(integrated.returncode, 0, self.json_result(integrated))
        return {
            **fixture,
            "destination": destination,
            "destination_path": destination_path,
        }

    def test_integrate_rejects_quarantine_changed_after_review(self) -> None:
        fixture = self.add_reviewed_run("run-review-drift")
        fixture["quarantine_path"].write_text("changed after review\n", encoding="utf-8")
        destination = self.vault / "Notes" / "run-review-drift.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("proposed output\n", encoding="utf-8")

        result = self.run_cli(
            "integrate",
            "--db",
            self.db,
            "--run-id",
            fixture["run_id"],
            "--relative-path",
            fixture["relative_path"],
            "--vault-root",
            self.vault,
            "--decision",
            "integrate",
            "--destination",
            "Notes/run-review-drift.md",
        )
        payload = self.json_result(result)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("quarantine content hash changed", payload["error"])

    def test_terminal_decision_must_be_reopened_with_append_only_history(self) -> None:
        fixture = self.add_reviewed_run("run-reopen")
        skipped = self.run_cli(
            "integrate",
            "--db",
            self.db,
            "--run-id",
            fixture["run_id"],
            "--relative-path",
            fixture["relative_path"],
            "--vault-root",
            self.vault,
            "--decision",
            "skip",
        )
        self.assertEqual(skipped.returncode, 0, self.json_result(skipped))

        destination = self.vault / "Notes" / "run-reopen.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("approved later\n", encoding="utf-8")
        refused = self.run_cli(
            "integrate",
            "--db",
            self.db,
            "--run-id",
            fixture["run_id"],
            "--relative-path",
            fixture["relative_path"],
            "--vault-root",
            self.vault,
            "--decision",
            "integrate",
            "--destination",
            "Notes/run-reopen.md",
        )
        self.assertNotEqual(refused.returncode, 0)

        reopened = self.run_cli(
            "supersede-decision",
            "--db",
            self.db,
            "--run-id",
            fixture["run_id"],
            "--relative-path",
            fixture["relative_path"],
            "--vault-root",
            self.vault,
            "--expected-state",
            "skipped",
            "--decision",
            "reopen",
            "--reason",
            "owner changed the disposition",
        )
        reopened_payload = self.json_result(reopened)
        self.assertEqual(reopened.returncode, 0, reopened_payload)
        self.assertEqual(reopened_payload["state"], "reviewed")

        integrated = self.run_cli(
            "integrate",
            "--db",
            self.db,
            "--run-id",
            fixture["run_id"],
            "--relative-path",
            fixture["relative_path"],
            "--vault-root",
            self.vault,
            "--decision",
            "integrate",
            "--destination",
            "Notes/run-reopen.md",
        )
        self.assertEqual(integrated.returncode, 0, self.json_result(integrated))
        with self.connect() as connection:
            history = connection.execute(
                "SELECT previous_state, new_state, new_decision FROM decision_history"
            ).fetchall()
            self.assertEqual(
                [tuple(row) for row in history],
                [("skipped", "reviewed", "reopen")],
            )

    def test_identical_rerun_is_resolved_without_another_owner_decision(self) -> None:
        fixture = self.integrate_reviewed_run("run-original")
        rerun = self.run_cli(
            "record-import",
            "--db",
            self.db,
            "--file",
            fixture["source"],
            "--source-key",
            fixture["source_key"],
            "--relative-path",
            fixture["relative_path"],
            "--run-id",
            "run-identical",
            "--vault-root",
            self.vault,
        )
        rerun_payload = self.json_result(rerun)
        self.assertEqual(rerun.returncode, 0, rerun_payload)
        self.assertEqual(rerun_payload["record"]["classification"], "unchanged")
        self.assertEqual(rerun_payload["record"]["decision"], "retain")

        verified = self.run_cli(
            "verify",
            "--db",
            self.db,
            "--vault-root",
            self.vault,
            "--run-id",
            "run-identical",
        )
        payload = self.json_result(verified)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["decision_complete"])
        self.assertTrue(payload["outputs_valid"])
        cleanup_plan = self.run_cli(
            "cleanup-plan",
            "--db",
            self.db,
            "--vault-root",
            self.vault,
            "--run-id",
            "run-identical",
        )
        cleanup_payload = self.json_result(cleanup_plan)
        self.assertEqual(cleanup_plan.returncode, 0, cleanup_payload)
        self.assertEqual(cleanup_payload["remaining_count"], 0)

    def test_record_import_rejects_non_quarantine_vault_path(self) -> None:
        source = self.root / "source.md"
        source.write_text("source\n", encoding="utf-8")
        misplaced = self.vault / "Notes" / "source.md"
        misplaced.parent.mkdir(parents=True, exist_ok=True)
        misplaced.write_bytes(source.read_bytes())
        result = self.run_cli(
            "record-import",
            "--db",
            self.db,
            "--file",
            source,
            "--source-key",
            "source:misplaced",
            "--relative-path",
            "Source/source.md",
            "--run-id",
            "run-misplaced",
            "--vault-root",
            self.vault,
            "--quarantine-path",
            "Notes/source.md",
        )
        payload = self.json_result(result)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("_Imports/Quarantine/run-misplaced", payload["error"])

    def test_cleanup_rechecks_outputs_and_quarantine_hashes(self) -> None:
        fixture = self.integrate_reviewed_run("run-cleanup-recheck")
        fixture["quarantine_path"].write_text("changed before cleanup\n", encoding="utf-8")
        changed = self.run_cli(
            "cleanup-plan",
            "--db",
            self.db,
            "--run-id",
            fixture["run_id"],
            "--vault-root",
            self.vault,
        )
        changed_payload = self.json_result(changed)
        self.assertNotEqual(changed.returncode, 0)
        self.assertIn("quarantine content hash changed", changed_payload["error"])

        fixture["quarantine_path"].unlink()
        fixture["destination_path"].unlink()
        cleanup = self.run_cli(
            "cleanup",
            "--db",
            self.db,
            "--run-id",
            fixture["run_id"],
            "--vault-root",
            self.vault,
        )
        cleanup_payload = self.json_result(cleanup)
        self.assertNotEqual(cleanup.returncode, 0)
        self.assertIn("missing destination", cleanup_payload["error"])

    def supersede(self, fixture: dict[str, object], **overrides: str) -> subprocess.CompletedProcess[str]:
        expected_state = overrides.get("expected_state", "integrated")
        expected_hash = overrides.get(
            "expected_hash", str(fixture["destination_hash"])
        )
        return self.run_cli(
            "supersede-decision",
            "--db",
            self.db,
            "--run-id",
            fixture["run_id"],
            "--relative-path",
            fixture["relative_path"],
            "--vault-root",
            self.vault,
            "--expected-state",
            expected_state,
            "--expected-output-hash",
            expected_hash,
            "--decision",
            "discard",
            "--reason",
            "owner marked this item as garbage",
        )

    def test_missing_integrated_destination_can_be_superseded_to_discard_with_history(self) -> None:
        fixture = self.add_integrated_run("run-missing", destination_exists=False)

        result = self.supersede(fixture)
        payload = self.json_result(result)
        self.assertEqual(result.returncode, 0, payload)
        self.assertEqual(payload["state"], "discarded")
        self.assertEqual(payload["decision"], "discard")

        with self.connect() as connection:
            item = connection.execute(
                """
                SELECT state, decision, destination, destination_hash
                FROM run_items WHERE run_id=? AND version_id=?
                """,
                (fixture["run_id"], fixture["version_id"]),
            ).fetchone()
            self.assertEqual(tuple(item), ("discarded", "discard", None, None))
            history = connection.execute(
                """
                SELECT previous_state, previous_decision, previous_destination,
                       previous_destination_hash, new_state, new_decision, reason
                FROM decision_history WHERE run_id=? AND version_id=?
                """,
                (fixture["run_id"], fixture["version_id"]),
            ).fetchone()
            self.assertEqual(history["previous_state"], "integrated")
            self.assertEqual(history["previous_decision"], "integrate")
            self.assertEqual(history["previous_destination"], fixture["destination"])
            self.assertEqual(
                history["previous_destination_hash"], fixture["destination_hash"]
            )
            self.assertEqual(history["new_state"], "discarded")
            self.assertEqual(history["new_decision"], "discard")
            self.assertTrue(history["reason"])
            output = connection.execute(
                """
                SELECT destination, destination_hash, active
                FROM integration_outputs WHERE run_id=? AND version_id=?
                """,
                (fixture["run_id"], fixture["version_id"]),
            ).fetchone()
            self.assertEqual(output["destination"], fixture["destination"])
            self.assertEqual(output["destination_hash"], fixture["destination_hash"])
            self.assertEqual(output["active"], 0)

    def test_supersede_refuses_while_destination_still_exists(self) -> None:
        fixture = self.add_integrated_run("run-existing", destination_exists=True)

        result = self.supersede(fixture)
        payload = self.json_result(result)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination still exists", payload["error"].lower())

        with self.connect() as connection:
            item = connection.execute(
                "SELECT state, decision FROM run_items WHERE run_id=? AND version_id=?",
                (fixture["run_id"], fixture["version_id"]),
            ).fetchone()
            self.assertEqual(tuple(item), ("integrated", "integrate"))

    def test_stale_expected_state_or_hash_refuses_and_rolls_back(self) -> None:
        fixture = self.add_integrated_run("run-stale", destination_exists=False)
        before = None
        with self.connect() as connection:
            before = tuple(
                connection.execute(
                    """
                    SELECT state, decision, destination, destination_hash
                    FROM run_items WHERE run_id=? AND version_id=?
                    """,
                    (fixture["run_id"], fixture["version_id"]),
                ).fetchone()
            )

        cases = (
            ({"expected_state": "reviewed"}, "expected state"),
            ({"expected_hash": "0" * 64}, "expected output hash"),
        )
        for overrides, message in cases:
            with self.subTest(message=message):
                result = self.supersede(fixture, **overrides)
                payload = self.json_result(result)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, payload["error"].lower())
                with self.connect() as connection:
                    after = tuple(
                        connection.execute(
                            """
                            SELECT state, decision, destination, destination_hash
                            FROM run_items WHERE run_id=? AND version_id=?
                            """,
                            (fixture["run_id"], fixture["version_id"]),
                        ).fetchone()
                    )
                    self.assertEqual(after, before)
                    output_count = connection.execute(
                        """
                        SELECT count(*) FROM integration_outputs
                        WHERE run_id=? AND version_id=?
                        """,
                        (fixture["run_id"], fixture["version_id"]),
                    ).fetchone()[0]
                    self.assertEqual(output_count, 1)

    def test_run_scoped_verify_ignores_another_runs_broken_output(self) -> None:
        self.add_integrated_run("run-good", destination_exists=True)
        self.add_integrated_run("run-broken", destination_exists=False)

        result = self.run_cli(
            "verify",
            "--db",
            self.db,
            "--vault-root",
            self.vault,
            "--run-id",
            "run-good",
        )
        payload = self.json_result(result)
        self.assertEqual(result.returncode, 0, payload)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["run_id"], "run-good")
        self.assertTrue(payload["outputs_valid"])
        self.assertEqual(payload["destination_problems"], [])

    def test_artifact_drift_fails_scoped_verify_and_revision_restores_it(self) -> None:
        self.add_integrated_run("run-artifact", destination_exists=True)
        artifact = self.vault / "Views" / "Applications.base"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("views: []\n", encoding="utf-8")
        first_hash = sha256(artifact.read_bytes())

        initial = self.run_cli(
            "record-artifact",
            "--db",
            self.db,
            "--run-id",
            "run-artifact",
            "--vault-root",
            self.vault,
            "--path",
            "Views/Applications.base",
            "--role",
            "base",
            "--reason",
            "initial approved Base",
        )
        self.assertEqual(initial.returncode, 0, self.json_result(initial))

        artifact.write_text("views:\n  - type: table\n", encoding="utf-8")
        second_hash = sha256(artifact.read_bytes())
        drift = self.run_cli(
            "verify",
            "--db",
            self.db,
            "--vault-root",
            self.vault,
            "--run-id",
            "run-artifact",
        )
        drift_payload = self.json_result(drift)
        self.assertFalse(drift_payload["ok"])
        self.assertFalse(drift_payload["artifacts_valid"])
        self.assertEqual(
            drift_payload["artifact_problems"][0]["problem"],
            "artifact hash changed",
        )

        revision = self.run_cli(
            "record-artifact",
            "--db",
            self.db,
            "--run-id",
            "run-artifact",
            "--vault-root",
            self.vault,
            "--path",
            "Views/Applications.base",
            "--role",
            "base",
            "--expected-previous-hash",
            first_hash,
            "--reason",
            "owner approved revised Base",
        )
        revision_payload = self.json_result(revision)
        self.assertEqual(revision.returncode, 0, revision_payload)
        self.assertEqual(revision_payload["artifact_hash"], second_hash)

        verified = self.run_cli(
            "verify",
            "--db",
            self.db,
            "--vault-root",
            self.vault,
            "--run-id",
            "run-artifact",
        )
        verified_payload = self.json_result(verified)
        self.assertTrue(verified_payload["ok"])
        self.assertTrue(verified_payload["artifacts_valid"])
        with self.connect() as connection:
            revisions = connection.execute(
                """
                SELECT artifact_id, artifact_hash, active, previous_artifact_id
                FROM run_artifacts
                WHERE run_id='run-artifact' AND artifact_path='Views/Applications.base'
                ORDER BY artifact_id
                """
            ).fetchall()
            self.assertEqual([row["artifact_hash"] for row in revisions], [first_hash, second_hash])
            self.assertEqual([row["active"] for row in revisions], [0, 1])
            self.assertIsNone(revisions[0]["previous_artifact_id"])
            self.assertEqual(revisions[1]["previous_artifact_id"], revisions[0]["artifact_id"])

    def test_scoped_verify_exposes_independent_readiness_flags(self) -> None:
        self.add_integrated_run("run-readiness", destination_exists=False)

        result = self.run_cli(
            "verify",
            "--db",
            self.db,
            "--vault-root",
            self.vault,
            "--run-id",
            "run-readiness",
        )
        payload = self.json_result(result)
        self.assertTrue(payload["decision_complete"])
        self.assertFalse(payload["outputs_valid"])
        self.assertTrue(payload["artifacts_valid"])
        self.assertFalse(payload["cleanup_eligible"])
        self.assertFalse(payload["ok"])

    def test_init_migrates_valid_v3_to_v4_without_losing_rows_and_is_idempotent(self) -> None:
        db, expected = self.create_v3_database()

        first = self.run_cli("init", "--db", db)
        first_payload = self.json_result(first)
        self.assertEqual(first.returncode, 0, first_payload)

        with sqlite3.connect(db) as connection:
            connection.row_factory = sqlite3.Row
            self.assertEqual(
                connection.execute(
                    "SELECT value FROM schema_meta WHERE key='schema_version'"
                ).fetchone()[0],
                "4",
            )
            run = connection.execute(
                "SELECT run_id, source_key, resolution_status FROM runs"
            ).fetchone()
            self.assertEqual(tuple(run), ("legacy-run", "source:legacy", "resolved"))
            item = connection.execute(
                """
                SELECT run_id, version_id, state, decision, destination, destination_hash
                FROM run_items
                """
            ).fetchone()
            self.assertEqual(
                tuple(item),
                (
                    "legacy-run",
                    1,
                    "integrated",
                    "integrate",
                    "Notes/legacy.md",
                    expected["destination_hash"],
                ),
            )
            output = connection.execute(
                """
                SELECT output_id, destination, destination_hash, active
                FROM integration_outputs
                """
            ).fetchone()
            self.assertEqual(
                tuple(output),
                (42, "Notes/legacy.md", expected["destination_hash"], 1),
            )
            self.assertEqual(
                connection.execute("SELECT count(*) FROM decision_history").fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute("SELECT count(*) FROM run_artifacts").fetchone()[0],
                0,
            )
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])

        second = self.run_cli("init", "--db", db)
        second_payload = self.json_result(second)
        self.assertEqual(second.returncode, 0, second_payload)
        with sqlite3.connect(db) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT value FROM schema_meta WHERE key='schema_version'"
                ).fetchone()[0],
                "4",
            )
            self.assertEqual(connection.execute("SELECT count(*) FROM runs").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM run_items").fetchone()[0], 1)
            self.assertEqual(
                connection.execute("SELECT count(*) FROM integration_outputs").fetchone()[0],
                1,
            )
            self.assertEqual(
                connection.execute("SELECT count(*) FROM decision_history").fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute("SELECT count(*) FROM run_artifacts").fetchone()[0],
                0,
            )
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_init_rolls_back_v3_migration_when_output_foreign_key_is_invalid(self) -> None:
        db, _ = self.create_v3_database(orphan_output=True)

        result = self.run_cli("init", "--db", db)
        payload = self.json_result(result)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("foreign key", payload["error"].lower())

        with sqlite3.connect(db) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT value FROM schema_meta WHERE key='schema_version'"
                ).fetchone()[0],
                "3",
            )
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            self.assertNotIn("decision_history", tables)
            self.assertNotIn("run_artifacts", tables)
            output_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(integration_outputs)")
            }
            self.assertNotIn("active", output_columns)
            self.assertEqual(
                connection.execute("SELECT output_id, version_id FROM integration_outputs").fetchone(),
                (42, 999),
            )
            self.assertTrue(connection.execute("PRAGMA foreign_key_check").fetchall())

    def test_global_verify_reports_active_artifact_hash_drift(self) -> None:
        self.add_integrated_run("run-global-artifact", destination_exists=True)
        artifact = self.vault / "Views" / "Global Applications.base"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("views: []\n", encoding="utf-8")
        recorded = self.run_cli(
            "record-artifact",
            "--db",
            self.db,
            "--run-id",
            "run-global-artifact",
            "--vault-root",
            self.vault,
            "--path",
            "Views/Global Applications.base",
            "--role",
            "base",
            "--reason",
            "initial approved Base",
        )
        self.assertEqual(recorded.returncode, 0, self.json_result(recorded))

        artifact.write_text("views:\n  - type: table\n", encoding="utf-8")
        result = self.run_cli(
            "verify",
            "--db",
            self.db,
            "--vault-root",
            self.vault,
        )
        payload = self.json_result(result)
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["artifacts_valid"])
        self.assertEqual(len(payload["artifact_problems"]), 1)
        problem = payload["artifact_problems"][0]
        self.assertEqual(problem["run_id"], "run-global-artifact")
        self.assertEqual(problem["artifact_path"], "Views/Global Applications.base")
        self.assertEqual(problem["artifact_role"], "base")
        self.assertEqual(problem["problem"], "artifact hash changed")

    def test_cleanup_plan_blocks_changed_or_missing_artifact_until_revision(self) -> None:
        self.add_integrated_run("run-cleanup-artifact", destination_exists=True)
        artifact = self.vault / "Views" / "Cleanup Applications.base"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("views: []\n", encoding="utf-8")
        first_hash = sha256(artifact.read_bytes())
        recorded = self.run_cli(
            "record-artifact",
            "--db",
            self.db,
            "--run-id",
            "run-cleanup-artifact",
            "--vault-root",
            self.vault,
            "--path",
            "Views/Cleanup Applications.base",
            "--role",
            "base",
            "--reason",
            "initial approved Base",
        )
        self.assertEqual(recorded.returncode, 0, self.json_result(recorded))

        revised_content = "views:\n  - type: table\n"
        artifact.write_text(revised_content, encoding="utf-8")
        changed = self.run_cli(
            "cleanup-plan",
            "--db",
            self.db,
            "--run-id",
            "run-cleanup-artifact",
            "--vault-root",
            self.vault,
        )
        changed_payload = self.json_result(changed)
        self.assertNotEqual(changed.returncode, 0)
        self.assertIn("artifact hash changed", changed_payload["error"])

        artifact.unlink()
        missing = self.run_cli(
            "cleanup-plan",
            "--db",
            self.db,
            "--run-id",
            "run-cleanup-artifact",
            "--vault-root",
            self.vault,
        )
        missing_payload = self.json_result(missing)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("missing artifact", missing_payload["error"])

        artifact.write_text(revised_content, encoding="utf-8")
        revision = self.run_cli(
            "record-artifact",
            "--db",
            self.db,
            "--run-id",
            "run-cleanup-artifact",
            "--vault-root",
            self.vault,
            "--path",
            "Views/Cleanup Applications.base",
            "--role",
            "base",
            "--expected-previous-hash",
            first_hash,
            "--reason",
            "owner approved revised Base",
        )
        revision_payload = self.json_result(revision)
        self.assertEqual(revision.returncode, 0, revision_payload)

        restored = self.run_cli(
            "cleanup-plan",
            "--db",
            self.db,
            "--run-id",
            "run-cleanup-artifact",
            "--vault-root",
            self.vault,
        )
        restored_payload = self.json_result(restored)
        self.assertEqual(restored.returncode, 0, restored_payload)
        self.assertTrue(restored_payload["ok"])
        self.assertEqual(restored_payload["resolution_status"], "resolved")


if __name__ == "__main__":
    unittest.main()
