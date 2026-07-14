#!/usr/bin/env python3
"""Deterministic SQLite ledger for the obsidian-import-notes workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 4
TERMINAL_STATES = {"integrated", "skipped", "discarded"}
GENERATED_KEYS = {"import_run", "imported_at", "destination"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
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

CREATE TABLE IF NOT EXISTS source_items (
    item_id INTEGER PRIMARY KEY,
    source_key TEXT NOT NULL,
    source_relative_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    UNIQUE (source_key, source_relative_path, file_name, file_type)
);

CREATE TABLE IF NOT EXISTS fingerprint_versions (
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

CREATE INDEX IF NOT EXISTS idx_fingerprint_versions_fingerprint
    ON fingerprint_versions(fingerprint);

CREATE TABLE IF NOT EXISTS run_items (
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
    review_group TEXT,
    loss_details TEXT,
    loss_acknowledged INTEGER NOT NULL DEFAULT 0 CHECK
        (loss_acknowledged IN (0, 1)),
    decision TEXT,
    decision_manifest TEXT,
    destination TEXT,
    destination_hash TEXT CHECK
        (destination_hash IS NULL OR length(destination_hash) = 64),
    integrated_at TEXT,
    cleaned_at TEXT,
    PRIMARY KEY (run_id, version_id),
    CHECK (state != 'quarantined' OR quarantine_path IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS integration_outputs (
    output_id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    version_id INTEGER NOT NULL,
    destination TEXT NOT NULL,
    destination_hash TEXT NOT NULL CHECK (length(destination_hash) = 64),
    output_role TEXT NOT NULL CHECK (output_role IN ('primary', 'additional')),
    transformation TEXT,
    integrated_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    UNIQUE (run_id, version_id, destination),
    FOREIGN KEY (run_id, version_id) REFERENCES run_items(run_id, version_id)
);

CREATE INDEX IF NOT EXISTS idx_integration_outputs_item
    ON integration_outputs(run_id, version_id);

CREATE INDEX IF NOT EXISTS idx_integration_outputs_active_item
    ON integration_outputs(run_id, version_id, active);

CREATE TABLE IF NOT EXISTS decision_history (
    history_id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    version_id INTEGER NOT NULL,
    previous_state TEXT NOT NULL,
    previous_decision TEXT,
    previous_destination TEXT,
    previous_destination_hash TEXT CHECK
        (previous_destination_hash IS NULL OR length(previous_destination_hash) = 64),
    new_state TEXT NOT NULL,
    new_decision TEXT NOT NULL,
    reason TEXT NOT NULL CHECK (length(trim(reason)) > 0),
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (run_id, version_id) REFERENCES run_items(run_id, version_id)
);

CREATE INDEX IF NOT EXISTS idx_decision_history_item
    ON decision_history(run_id, version_id, history_id);

CREATE TRIGGER IF NOT EXISTS decision_history_no_update
BEFORE UPDATE ON decision_history
BEGIN
    SELECT RAISE(ABORT, 'decision history is append-only');
END;

CREATE TRIGGER IF NOT EXISTS decision_history_no_delete
BEFORE DELETE ON decision_history
BEGIN
    SELECT RAISE(ABORT, 'decision history is append-only');
END;

CREATE TABLE IF NOT EXISTS run_artifacts (
    artifact_id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    artifact_path TEXT NOT NULL,
    artifact_hash TEXT NOT NULL CHECK (length(artifact_hash) = 64),
    artifact_role TEXT NOT NULL,
    reason TEXT NOT NULL CHECK (length(trim(reason)) > 0),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    previous_artifact_id INTEGER REFERENCES run_artifacts(artifact_id),
    recorded_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_run_artifacts_active_path
    ON run_artifacts(run_id, artifact_path, active, artifact_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_run_artifacts_one_active
    ON run_artifacts(run_id, artifact_path) WHERE active = 1;

CREATE TRIGGER IF NOT EXISTS run_artifacts_deactivate_only
BEFORE UPDATE ON run_artifacts
WHEN NOT (
    OLD.active = 1 AND NEW.active = 0
    AND NEW.artifact_id IS OLD.artifact_id
    AND NEW.run_id IS OLD.run_id
    AND NEW.artifact_path IS OLD.artifact_path
    AND NEW.artifact_hash IS OLD.artifact_hash
    AND NEW.artifact_role IS OLD.artifact_role
    AND NEW.reason IS OLD.reason
    AND NEW.previous_artifact_id IS OLD.previous_artifact_id
    AND NEW.recorded_at IS OLD.recorded_at
)
BEGIN
    SELECT RAISE(ABORT, 'artifact revisions are append-only');
END;

CREATE TRIGGER IF NOT EXISTS run_artifacts_no_delete
BEFORE DELETE ON run_artifacts
BEGIN
    SELECT RAISE(ABORT, 'artifact revisions are append-only');
END;
"""


class LedgerError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_bytes(path: Path, data: bytes, mode: int) -> None:
    """Replace one file atomically while preserving its permission bits."""
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.merge-", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def file_type(path: Path) -> str:
    suffix = path.suffix.lower().removeprefix(".")
    return suffix or "unknown"


def normalized_markdown(data: bytes) -> bytes:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    lines = text.split("\n")
    if lines and lines[0] == "---":
        try:
            closing = lines.index("---", 1)
        except ValueError:
            closing = -1
        if closing > 0:
            frontmatter = []
            for line in lines[1:closing]:
                key = line.split(":", 1)[0].strip() if ":" in line else ""
                is_generated_top_level = (
                    line == line.lstrip(" \t") and key in GENERATED_KEYS
                )
                if not is_generated_top_level:
                    frontmatter.append(line)
            if any(line.strip() for line in frontmatter):
                lines = ["---", *frontmatter, "---", *lines[closing + 1 :]]
            else:
                lines = lines[closing + 1 :]
    normalized = "\n".join(line.rstrip(" \t") for line in lines).rstrip("\n") + "\n"
    return normalized.encode("utf-8")


def metadata(path: Path, source_key: str, relative_path: str) -> dict[str, Any]:
    if not path.is_file():
        raise LedgerError(f"file does not exist: {path}")
    name = unicodedata.normalize("NFC", path.name)
    kind = file_type(path)
    size = path.stat().st_size
    source = unicodedata.normalize("NFC", source_key)
    payload = "\0".join((name, str(size), source, kind)).encode("utf-8")
    data = path.read_bytes()
    normalized = normalized_markdown(data) if kind == "md" else data
    return {
        "file": str(path),
        "file_name": name,
        "size_bytes": size,
        "source_key": source,
        "file_type": kind,
        "source_relative_path": unicodedata.normalize("NFC", relative_path),
        "fingerprint": sha256_bytes(payload),
        "raw_hash": sha256_bytes(data),
        "normalized_hash": sha256_bytes(normalized),
    }


def connect(db_path: Path, create: bool = False) -> sqlite3.Connection:
    if not create and not db_path.is_file():
        raise LedgerError(f"ledger does not exist: {db_path}")
    if create:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, isolation_level=None, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}


def table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        is not None
    )


def ensure_v3_output_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS integration_outputs (
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
        )
        """
    )


def migrate_v1_to_v2(connection: sqlite3.Connection) -> None:
    columns = table_columns(connection, "run_items")
    additions = {
        "review_group": "TEXT",
        "loss_details": "TEXT",
        "loss_acknowledged": "INTEGER NOT NULL DEFAULT 0 CHECK (loss_acknowledged IN (0, 1))",
        "decision_manifest": "TEXT",
    }
    for name, definition in additions.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE run_items ADD COLUMN {name} {definition}")
    connection.execute(
        """
        INSERT OR IGNORE INTO integration_outputs(
            run_id, version_id, destination, destination_hash,
            output_role, transformation, integrated_at
        )
        SELECT run_id, version_id, destination, destination_hash,
               'primary', decision, integrated_at
        FROM run_items
        WHERE state='integrated' AND destination IS NOT NULL
          AND destination_hash IS NOT NULL AND integrated_at IS NOT NULL
        """
    )


def migrate_v2_to_v3(connection: sqlite3.Connection) -> None:
    columns = table_columns(connection, "runs")
    if "resolution_status" not in columns:
        connection.execute(
            "ALTER TABLE runs ADD COLUMN resolution_status TEXT NOT NULL "
            "DEFAULT 'pending' CHECK (resolution_status IN ('pending', 'resolved'))"
        )
    if "resolved_at" not in columns:
        connection.execute("ALTER TABLE runs ADD COLUMN resolved_at TEXT")
    connection.execute(
        """
        UPDATE runs SET
            resolution_status='resolved',
            resolved_at=COALESCE(resolved_at, completed_at, cleaned_at)
        WHERE NOT EXISTS (
            SELECT 1 FROM run_items
            WHERE run_items.run_id=runs.run_id
              AND (
                  state NOT IN ('integrated', 'skipped', 'discarded')
                  OR decision IS NULL
              )
        )
        """
    )


def migrate_v3_to_v4(connection: sqlite3.Connection) -> None:
    columns = table_columns(connection, "integration_outputs")
    if "active" not in columns:
        connection.execute(
            "ALTER TABLE integration_outputs ADD COLUMN active INTEGER NOT NULL "
            "DEFAULT 1 CHECK (active IN (0, 1))"
        )


def execute_schema(connection: sqlite3.Connection) -> None:
    """Execute the schema statement-by-statement inside the caller's transaction."""
    statement = ""
    for line in SCHEMA.splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            if statement.strip():
                connection.execute(statement)
            statement = ""
    if statement.strip():
        raise LedgerError("ledger schema contains an incomplete SQL statement")


def ensure_schema(connection: sqlite3.Connection) -> None:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_meta'"
    ).fetchone()
    if row is None:
        raise LedgerError("ledger schema is not initialized")
    version = connection.execute(
        "SELECT value FROM schema_meta WHERE key='schema_version'"
    ).fetchone()
    if version is None or int(version["value"]) != SCHEMA_VERSION:
        raise LedgerError("unsupported ledger schema version")


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[None]:
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()


def row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def latest_state(connection: sqlite3.Connection, version_id: int) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT run_id, classification, state, quarantine_path
        FROM run_items
        WHERE version_id = ?
        ORDER BY rowid DESC
        LIMIT 1
        """,
        (version_id,),
    ).fetchone()


def classify(connection: sqlite3.Connection, meta: dict[str, Any]) -> dict[str, Any]:
    latest = connection.execute(
        """
        SELECT fv.*, si.source_key, si.source_relative_path,
               si.file_name, si.file_type
        FROM fingerprint_versions fv
        JOIN source_items si ON si.item_id = fv.item_id
        WHERE si.source_key = ? AND si.source_relative_path = ?
          AND si.file_name = ? AND si.file_type = ?
        ORDER BY fv.version_id DESC
        LIMIT 1
        """,
        (
            meta["source_key"],
            meta["source_relative_path"],
            meta["file_name"],
            meta["file_type"],
        ),
    ).fetchone()
    if latest is not None:
        if (
            latest["fingerprint"] == meta["fingerprint"]
            and latest["raw_hash"] == meta["raw_hash"]
        ):
            state = latest_state(connection, latest["version_id"])
            if state is None:
                kind = "interrupted"
            elif state["state"] in TERMINAL_STATES:
                kind = "unchanged"
            elif state["state"] in {"quarantined", "reviewed"}:
                kind = "resume"
            else:
                kind = "retry"
            return {
                **meta,
                "classification": kind,
                "matched_version_id": latest["version_id"],
                "previous_version_id": latest["version_id"],
                "matched_run": row_dict(state),
            }
        reason = "source identity differs from its latest recorded version"
        if latest["fingerprint"] == meta["fingerprint"]:
            reason = "same fingerprint metadata with different raw content"
        return {
            **meta,
            "classification": "changed",
            "matched_version_id": None,
            "previous_version_id": latest["version_id"],
            "reason": reason,
        }
    exact_rows = connection.execute(
        """
        SELECT fv.version_id
        FROM fingerprint_versions fv
        WHERE fv.fingerprint = ?
        LIMIT 1
        """,
        (meta["fingerprint"],),
    ).fetchall()
    if exact_rows:
        return {
            **meta,
            "classification": "conflict",
            "matched_version_id": None,
            "previous_version_id": None,
            "reason": "fingerprint already belongs to another source-relative path",
        }
    similar = connection.execute(
        """
        SELECT si.item_id, si.source_relative_path
        FROM source_items si
        WHERE si.source_key = ? AND si.file_name = ? AND si.file_type = ?
        LIMIT 1
        """,
        (meta["source_key"], meta["file_name"], meta["file_type"]),
    ).fetchone()
    if similar is not None:
        return {
            **meta,
            "classification": "conflict",
            "matched_version_id": None,
            "previous_version_id": None,
            "reason": f"similar prior item at {similar['source_relative_path']}",
        }
    return {
        **meta,
        "classification": "new",
        "matched_version_id": None,
        "previous_version_id": None,
    }


def init_command(args: argparse.Namespace) -> dict[str, Any]:
    db_path = Path(args.db).expanduser().resolve()
    connection = connect(db_path, create=True)
    try:
        with transaction(connection):
            if not table_exists(connection, "schema_meta"):
                execute_schema(connection)
                connection.execute(
                    "INSERT INTO schema_meta(key, value) VALUES('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
            else:
                existing = connection.execute(
                    "SELECT value FROM schema_meta WHERE key='schema_version'"
                ).fetchone()
                if existing is None:
                    raise LedgerError("existing ledger has no schema version")
                version = int(existing["value"])
                if version not in {1, 2, 3, SCHEMA_VERSION}:
                    raise LedgerError("existing ledger has an unsupported schema version")
                foreign_keys = list(connection.execute("PRAGMA foreign_key_check"))
                if foreign_keys:
                    raise LedgerError(
                        "foreign key violations prevent schema migration: "
                        + json.dumps([tuple(row) for row in foreign_keys])
                    )
                if version <= 2:
                    ensure_v3_output_table(connection)
                if version == 1:
                    migrate_v1_to_v2(connection)
                    migrate_v2_to_v3(connection)
                elif version == 2:
                    migrate_v2_to_v3(connection)
                if version <= 3:
                    migrate_v3_to_v4(connection)
                execute_schema(connection)
                foreign_keys = list(connection.execute("PRAGMA foreign_key_check"))
                if foreign_keys:
                    raise LedgerError(
                        "foreign key violations prevent schema migration: "
                        + json.dumps([tuple(row) for row in foreign_keys])
                    )
                if version != SCHEMA_VERSION:
                    connection.execute(
                        "UPDATE schema_meta SET value=? WHERE key='schema_version'",
                        (str(SCHEMA_VERSION),),
                    )
        return {"ok": True, "db": str(db_path), "schema_version": SCHEMA_VERSION}
    finally:
        connection.close()


def classify_command(args: argparse.Namespace) -> dict[str, Any]:
    connection = connect(Path(args.db).expanduser().resolve())
    try:
        ensure_schema(connection)
        meta = metadata(Path(args.file).expanduser().resolve(), args.source_key, args.relative_path)
        return {"ok": True, **classify(connection, meta)}
    finally:
        connection.close()


def source_item_id(connection: sqlite3.Connection, meta: dict[str, Any]) -> int:
    row = connection.execute(
        """
        SELECT item_id FROM source_items
        WHERE source_key = ? AND source_relative_path = ?
          AND file_name = ? AND file_type = ?
        """,
        (
            meta["source_key"],
            meta["source_relative_path"],
            meta["file_name"],
            meta["file_type"],
        ),
    ).fetchone()
    if row is not None:
        return int(row["item_id"])
    cursor = connection.execute(
        """
        INSERT INTO source_items(
            source_key, source_relative_path, file_name, file_type
        ) VALUES (?, ?, ?, ?)
        """,
        (
            meta["source_key"],
            meta["source_relative_path"],
            meta["file_name"],
            meta["file_type"],
        ),
    )
    return int(cursor.lastrowid)


def ensure_run(connection: sqlite3.Connection, run_id: str, source_key: str) -> None:
    row = connection.execute(
        "SELECT source_key FROM runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    if row is None:
        connection.execute(
            "INSERT INTO runs(run_id, source_key, status, started_at) VALUES(?, ?, 'open', ?)",
            (run_id, source_key, now()),
        )
    elif row["source_key"] != source_key:
        raise LedgerError("run ID already belongs to another source key")


def resolve_vault_path(vault_root: Path, value: str) -> Path:
    candidate = (vault_root / value).resolve()
    try:
        candidate.relative_to(vault_root.resolve())
    except ValueError as exc:
        raise LedgerError(f"vault-relative path escapes the vault: {value}") from exc
    return candidate


def require_quarantine_path(value: str, run_id: str) -> None:
    expected = ("_Imports", "Quarantine", run_id)
    parts = Path(value).parts
    if len(parts) <= len(expected) or parts[: len(expected)] != expected:
        raise LedgerError(
            "quarantine path must be under "
            f"_Imports/Quarantine/{run_id}/"
        )


def verified_quarantine(
    vault_root: Path,
    item: sqlite3.Row,
    *,
    allow_absent: bool = False,
) -> Path | None:
    value = item["quarantine_path"]
    if not value:
        if allow_absent:
            return None
        raise LedgerError(
            "item has no quarantine path; return it to the importer for reconciliation"
        )
    path = resolve_vault_path(vault_root, value)
    if not path.is_file():
        if allow_absent and not path.exists():
            return None
        raise LedgerError(
            "quarantine file is missing; return the item to the importer for reconciliation"
        )
    if raw_hash(path) != item["raw_hash"]:
        raise LedgerError(
            "quarantine content hash changed; return the item to the importer for reconciliation"
        )
    return path


def latest_resolution(
    connection: sqlite3.Connection, version_id: int
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT run_id, version_id, state, decision, destination, destination_hash,
               loss_details, loss_acknowledged
        FROM run_items
        WHERE version_id = ?
          AND state IN ('integrated', 'skipped', 'discarded')
          AND decision IS NOT NULL
          AND NOT (state='skipped' AND decision='retain')
        ORDER BY rowid DESC
        LIMIT 1
        """,
        (version_id,),
    ).fetchone()


def resolution_outputs(
    connection: sqlite3.Connection, resolution: sqlite3.Row
) -> list[sqlite3.Row]:
    rows = connection.execute(
        """
        SELECT destination, destination_hash
        FROM integration_outputs
        WHERE run_id=? AND version_id=? AND active=1
        ORDER BY CASE output_role WHEN 'primary' THEN 0 ELSE 1 END, output_id
        """,
        (resolution["run_id"], resolution["version_id"]),
    ).fetchall()
    if rows:
        return rows
    if resolution["destination"] and resolution["destination_hash"]:
        return [resolution]
    return []


def record_import_command(args: argparse.Namespace) -> dict[str, Any]:
    db_path = Path(args.db).expanduser().resolve()
    source_path = Path(args.file).expanduser().resolve()
    vault_root = Path(args.vault_root).expanduser().resolve()
    connection = connect(db_path)
    try:
        ensure_schema(connection)
        with transaction(connection):
            meta = metadata(source_path, args.source_key, args.relative_path)
            result = classify(connection, meta)
            classification = result["classification"]
            if classification == "resume":
                raise LedgerError(
                    f"resume existing run {result['matched_run']['run_id']} instead of creating a new run"
                )
            ensure_run(connection, args.run_id, meta["source_key"])
            if classification == "unchanged":
                version_id = int(result["matched_version_id"])
                prior_resolution = latest_resolution(connection, version_id)
                destination_problem = None
                if prior_resolution is None:
                    destination_problem = "no completed owner decision is recorded"
                elif prior_resolution["state"] == "integrated":
                    outputs = resolution_outputs(connection, prior_resolution)
                    if not outputs:
                        destination_problem = "the integrated item has no recorded outputs"
                    for output in outputs:
                        destination = resolve_vault_path(vault_root, output["destination"])
                        if not destination.is_file():
                            destination_problem = (
                                f"recorded output is missing: {output['destination']}"
                            )
                            break
                        if raw_hash(destination) != output["destination_hash"]:
                            destination_problem = (
                                f"recorded output hash changed: {output['destination']}"
                            )
                            break
                if destination_problem:
                    classification = "conflict"
                    result["matched_version_id"] = version_id
                    result["reason"] = destination_problem
            if classification == "unchanged":
                version_id = int(result["matched_version_id"])
                state = "skipped"
                quarantine_path = None
                if prior_resolution is None:
                    raise LedgerError("unchanged item has no prior resolution")
                decision = (
                    "retain"
                    if prior_resolution["state"] == "integrated"
                    else prior_resolution["decision"]
                )
                destination = prior_resolution["destination"]
                destination_hash = prior_resolution["destination_hash"]
                loss_details = prior_resolution["loss_details"]
                loss_acknowledged = int(prior_resolution["loss_acknowledged"])
            else:
                if not args.quarantine_path:
                    raise LedgerError(
                        f"classification {classification} requires --quarantine-path"
                    )
                require_quarantine_path(args.quarantine_path, args.run_id)
                quarantine = resolve_vault_path(vault_root, args.quarantine_path)
                if not quarantine.is_file():
                    raise LedgerError(f"quarantine file does not exist: {quarantine}")
                if raw_hash(quarantine) != meta["raw_hash"]:
                    raise LedgerError("quarantine content does not match the source file")
                item_id = source_item_id(connection, meta)
                if classification in {"interrupted", "retry"} or (
                    classification == "conflict"
                    and result.get("matched_version_id") is not None
                ):
                    version_id = int(result["matched_version_id"])
                else:
                    cursor = connection.execute(
                        """
                        INSERT INTO fingerprint_versions(
                            item_id, fingerprint, size_bytes, raw_hash,
                            normalized_hash, previous_version_id,
                            first_seen_run_id, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item_id,
                            meta["fingerprint"],
                            meta["size_bytes"],
                            meta["raw_hash"],
                            meta["normalized_hash"],
                            result["previous_version_id"],
                            args.run_id,
                            now(),
                        ),
                    )
                    version_id = int(cursor.lastrowid)
                state = "quarantined"
                quarantine_path = args.quarantine_path
                decision = None
                destination = None
                destination_hash = None
                loss_details = args.loss_details
                loss_acknowledged = 0
            prior = connection.execute(
                "SELECT state FROM run_items WHERE run_id = ? AND version_id = ?",
                (args.run_id, version_id),
            ).fetchone()
            if prior is None:
                connection.execute(
                    """
                    INSERT INTO run_items(
                        run_id, version_id, classification, state,
                        quarantine_path, loss_details, loss_acknowledged,
                        decision, destination, destination_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        args.run_id,
                        version_id,
                        classification,
                        state,
                        quarantine_path,
                        loss_details,
                        loss_acknowledged,
                        decision,
                        destination,
                        destination_hash,
                    ),
                )
            connection.execute(
                "UPDATE runs SET status='imported', imported_at=? WHERE run_id=?",
                (now(), args.run_id),
            )
            refresh_resolution_status(connection, args.run_id)
        row = connection.execute(
            """
            SELECT ri.*, fv.fingerprint, fv.raw_hash, fv.normalized_hash,
                   fv.previous_version_id
            FROM run_items ri
            JOIN fingerprint_versions fv ON fv.version_id = ri.version_id
            WHERE ri.run_id = ? AND ri.version_id = ?
            """,
            (args.run_id, version_id),
        ).fetchone()
        return {"ok": True, "record": row_dict(row)}
    finally:
        connection.close()


def run_item(connection: sqlite3.Connection, run_id: str, relative_path: str) -> sqlite3.Row:
    rows = connection.execute(
        """
        SELECT ri.*, fv.raw_hash, si.source_relative_path
        FROM run_items ri
        JOIN fingerprint_versions fv ON fv.version_id = ri.version_id
        JOIN source_items si ON si.item_id = fv.item_id
        WHERE ri.run_id = ? AND si.source_relative_path = ?
        """,
        (run_id, unicodedata.normalize("NFC", relative_path)),
    ).fetchall()
    if len(rows) != 1:
        raise LedgerError(f"expected one run item, found {len(rows)}")
    return rows[0]


def refresh_review_status(connection: sqlite3.Connection, run_id: str) -> str:
    states = [
        row["state"]
        for row in connection.execute(
            "SELECT state FROM run_items WHERE run_id=?", (run_id,)
        )
    ]
    if any(state == "failed" for state in states):
        status = "failed"
    elif any(state == "quarantined" for state in states):
        status = "imported"
    else:
        status = "reviewed"
    connection.execute(
        "UPDATE runs SET status=? WHERE run_id=?", (status, run_id)
    )
    return status


def refresh_resolution_status(connection: sqlite3.Connection, run_id: str) -> str:
    unresolved = connection.execute(
        """
        SELECT count(*) FROM run_items
        WHERE run_id=? AND (
            state NOT IN ('integrated', 'skipped', 'discarded')
            OR decision IS NULL
        )
        """,
        (run_id,),
    ).fetchone()[0]
    status = "resolved" if unresolved == 0 else "pending"
    connection.execute(
        """
        UPDATE runs SET
            resolution_status=?,
            resolved_at=CASE WHEN ?='resolved' THEN COALESCE(resolved_at, ?) ELSE NULL END
        WHERE run_id=?
        """,
        (status, status, now(), run_id),
    )
    return status


def review_command(args: argparse.Namespace) -> dict[str, Any]:
    connection = connect(Path(args.db).expanduser().resolve())
    vault_root = Path(args.vault_root).expanduser().resolve()
    report = Path(args.report).expanduser().resolve()
    if not report.is_file():
        raise LedgerError(f"review report does not exist: {report}")
    try:
        ensure_schema(connection)
        with transaction(connection):
            item = run_item(connection, args.run_id, args.relative_path)
            if item["state"] != "quarantined":
                raise LedgerError(f"cannot review item in state {item['state']}")
            verified_quarantine(vault_root, item)
            state = "failed" if args.classification == "failed" else "reviewed"
            connection.execute(
                """
                UPDATE run_items
                SET state=?, review_classification=?, review_report=?,
                    review_group=COALESCE(?, review_group),
                    loss_details=COALESCE(?, loss_details)
                WHERE run_id=? AND version_id=?
                """,
                (
                    state,
                    args.classification,
                    str(report),
                    args.review_group,
                    args.loss_details,
                    args.run_id,
                    item["version_id"],
                ),
            )
            run_status = refresh_review_status(connection, args.run_id)
        return {
            "ok": True,
            "run_id": args.run_id,
            "state": state,
            "run_status": run_status,
        }
    finally:
        connection.close()


def load_decision_manifest(value: str | None) -> str | None:
    if value is None:
        return None
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise LedgerError(f"decision manifest does not exist: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LedgerError(f"decision manifest is not valid JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise LedgerError("decision manifest must be a JSON object")
    return json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def integrate_command(args: argparse.Namespace) -> dict[str, Any]:
    connection = connect(Path(args.db).expanduser().resolve())
    vault_root = Path(args.vault_root).expanduser().resolve()
    try:
        ensure_schema(connection)
        with transaction(connection):
            item = run_item(connection, args.run_id, args.relative_path)
            if item["state"] != "reviewed":
                raise LedgerError(f"cannot decide item in state {item['state']}")
            verified_quarantine(vault_root, item)
            loss_acknowledged = bool(item["loss_acknowledged"] or args.acknowledge_loss)
            if item["loss_details"] and not loss_acknowledged:
                raise LedgerError(
                    "lossy item requires explicit --acknowledge-loss before a terminal decision"
                )
            decision_manifest = load_decision_manifest(args.decision_manifest)
            if args.additional_destination and decision_manifest is None:
                raise LedgerError(
                    "multiple integration outputs require --decision-manifest"
                )
            outputs: list[dict[str, str]] = []
            if args.decision in {"integrate", "update", "retain"}:
                if not args.destination:
                    raise LedgerError("integration decision requires --destination")
                destination_values = [args.destination, *args.additional_destination]
                if len(set(destination_values)) != len(destination_values):
                    raise LedgerError("integration output destinations must be unique")
                for index, value in enumerate(destination_values):
                    destination = resolve_vault_path(vault_root, value)
                    if not destination.is_file():
                        raise LedgerError(f"destination does not exist: {destination}")
                    outputs.append(
                        {
                            "destination": value,
                            "destination_hash": raw_hash(destination),
                            "output_role": "primary" if index == 0 else "additional",
                        }
                    )
                destination_hash = outputs[0]["destination_hash"]
                state = "integrated"
                integrated_at = now()
            else:
                destination_hash = None
                if args.additional_destination:
                    raise LedgerError(
                        "additional destinations are valid only for integration decisions"
                    )
                if args.destination:
                    destination = resolve_vault_path(vault_root, args.destination)
                    if not destination.is_file():
                        raise LedgerError(f"destination does not exist: {destination}")
                    destination_hash = raw_hash(destination)
                integrated_at = None
                state = "discarded" if args.decision == "discard" else "skipped"
            connection.execute(
                """
                UPDATE run_items SET
                    state=?, decision=?, decision_manifest=?,
                    loss_acknowledged=?, destination=?, destination_hash=?, integrated_at=?
                WHERE run_id=? AND version_id=?
                """,
                (
                    state,
                    args.decision,
                    decision_manifest,
                    int(loss_acknowledged),
                    args.destination,
                    destination_hash,
                    integrated_at,
                    args.run_id,
                    item["version_id"],
                ),
            )
            if outputs:
                for output in outputs:
                    connection.execute(
                        """
                        INSERT INTO integration_outputs(
                            run_id, version_id, destination, destination_hash,
                            output_role, transformation, integrated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            args.run_id,
                            item["version_id"],
                            output["destination"],
                            output["destination_hash"],
                            output["output_role"],
                            decision_manifest,
                            integrated_at,
                        ),
                    )
            resolution_status = refresh_resolution_status(connection, args.run_id)
        return {
            "ok": True,
            "run_id": args.run_id,
            "state": state,
            "destination": args.destination,
            "destination_hash": destination_hash,
            "outputs": outputs,
            "loss_acknowledged": loss_acknowledged,
            "resolution_status": resolution_status,
        }
    finally:
        connection.close()


def supersede_decision_command(args: argparse.Namespace) -> dict[str, Any]:
    connection = connect(Path(args.db).expanduser().resolve())
    vault_root = Path(args.vault_root).expanduser().resolve()
    reason = args.reason.strip()
    if not reason:
        raise LedgerError("--reason must not be empty")
    try:
        ensure_schema(connection)
        with transaction(connection):
            item = run_item(connection, args.run_id, args.relative_path)
            if item["state"] != args.expected_state:
                raise LedgerError(
                    f"expected state {args.expected_state}, found {item['state']}"
                )
            outputs = connection.execute(
                """
                SELECT output_id, destination, destination_hash
                FROM integration_outputs
                WHERE run_id=? AND version_id=? AND active=1
                ORDER BY output_id
                """,
                (args.run_id, item["version_id"]),
            ).fetchall()
            if item["state"] not in TERMINAL_STATES:
                raise LedgerError("only a terminal decision can be superseded")
            if item["state"] == "integrated":
                if (
                    not args.expected_output_hash
                    or len(args.expected_output_hash) != 64
                ):
                    raise LedgerError(
                        "integrated supersession requires --expected-output-hash"
                    )
                if item["destination_hash"] != args.expected_output_hash:
                    raise LedgerError(
                        "expected output hash does not match the current decision"
                    )
                if not outputs:
                    raise LedgerError("integrated decision has no active output records")
                live_destinations = [
                    output["destination"]
                    for output in outputs
                    if resolve_vault_path(vault_root, output["destination"]).exists()
                ]
                if live_destinations:
                    raise LedgerError(
                        "destination still exists; supersession never changes vault files: "
                        + ", ".join(live_destinations)
                    )
            elif outputs:
                raise LedgerError("non-integrated decision has active output records")
            if args.decision == "reopen":
                state = "reviewed"
                stored_decision = None
            else:
                state = "discarded" if args.decision == "discard" else "skipped"
                stored_decision = args.decision
            recorded_at = now()
            connection.execute(
                """
                INSERT INTO decision_history(
                    run_id, version_id, previous_state, previous_decision,
                    previous_destination, previous_destination_hash,
                    new_state, new_decision, reason, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    args.run_id,
                    item["version_id"],
                    item["state"],
                    item["decision"],
                    item["destination"],
                    item["destination_hash"],
                    state,
                    args.decision,
                    reason,
                    recorded_at,
                ),
            )
            connection.execute(
                """
                UPDATE integration_outputs SET active=0
                WHERE run_id=? AND version_id=? AND active=1
                """,
                (args.run_id, item["version_id"]),
            )
            connection.execute(
                """
                UPDATE run_items SET
                    state=?, decision=?, decision_manifest=NULL,
                    destination=NULL, destination_hash=NULL, integrated_at=NULL
                WHERE run_id=? AND version_id=?
                """,
                (state, stored_decision, args.run_id, item["version_id"]),
            )
            resolution_status = refresh_resolution_status(connection, args.run_id)
        return {
            "ok": True,
            "run_id": args.run_id,
            "version_id": item["version_id"],
            "state": state,
            "decision": args.decision,
            "deactivated_outputs": len(outputs),
            "resolution_status": resolution_status,
        }
    finally:
        connection.close()


def record_artifact_command(args: argparse.Namespace) -> dict[str, Any]:
    connection = connect(Path(args.db).expanduser().resolve())
    vault_root = Path(args.vault_root).expanduser().resolve()
    artifact_path = unicodedata.normalize("NFC", args.path)
    artifact = resolve_vault_path(vault_root, artifact_path)
    role = args.role.strip()
    reason = args.reason.strip()
    if not role:
        raise LedgerError("--role must not be empty")
    if not reason:
        raise LedgerError("--reason must not be empty")
    if args.expected_previous_hash and len(args.expected_previous_hash) != 64:
        raise LedgerError("--expected-previous-hash must be a SHA-256 hash")
    try:
        ensure_schema(connection)
        with transaction(connection):
            run = connection.execute(
                "SELECT run_id FROM runs WHERE run_id=?", (args.run_id,)
            ).fetchone()
            if run is None:
                raise LedgerError(f"run does not exist: {args.run_id}")
            if not artifact.is_file():
                raise LedgerError(f"artifact does not exist: {artifact}")
            artifact_hash = raw_hash(artifact)
            previous = connection.execute(
                """
                SELECT artifact_id, artifact_hash
                FROM run_artifacts
                WHERE run_id=? AND artifact_path=? AND active=1
                ORDER BY artifact_id DESC LIMIT 1
                """,
                (args.run_id, artifact_path),
            ).fetchone()
            if previous is None:
                if args.expected_previous_hash:
                    raise LedgerError("expected previous artifact, but none is recorded")
                previous_id = None
            else:
                if not args.expected_previous_hash:
                    raise LedgerError(
                        "artifact already exists; provide --expected-previous-hash to revise it"
                    )
                if previous["artifact_hash"] != args.expected_previous_hash:
                    raise LedgerError(
                        "expected previous hash does not match the active artifact revision"
                    )
                if previous["artifact_hash"] == artifact_hash:
                    raise LedgerError("artifact content is unchanged")
                previous_id = int(previous["artifact_id"])
                connection.execute(
                    "UPDATE run_artifacts SET active=0 WHERE artifact_id=?",
                    (previous_id,),
                )
            cursor = connection.execute(
                """
                INSERT INTO run_artifacts(
                    run_id, artifact_path, artifact_hash, artifact_role,
                    reason, active, previous_artifact_id, recorded_at
                ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    args.run_id,
                    artifact_path,
                    artifact_hash,
                    role,
                    reason,
                    previous_id,
                    now(),
                ),
            )
            artifact_id = int(cursor.lastrowid)
        return {
            "ok": True,
            "run_id": args.run_id,
            "artifact_id": artifact_id,
            "artifact_path": artifact_path,
            "artifact_hash": artifact_hash,
            "role": role,
            "previous_artifact_id": previous_id,
        }
    finally:
        connection.close()


def merge_destination_command(args: argparse.Namespace) -> dict[str, Any]:
    connection = connect(Path(args.db).expanduser().resolve())
    vault_root = Path(args.vault_root).expanduser().resolve()
    staged_file = Path(args.staged_file).expanduser().resolve()
    destination = resolve_vault_path(vault_root, args.destination)
    original_data: bytes | None = None
    original_mode: int | None = None
    destination_replaced = False
    try:
        ensure_schema(connection)
        if not staged_file.is_file():
            raise LedgerError(f"staged merged file does not exist: {staged_file}")
        if not destination.is_file():
            raise LedgerError(f"destination does not exist: {destination}")
        if len(args.expected_destination_hash) != 64:
            raise LedgerError("--expected-destination-hash must be a SHA-256 hash")
        decision_manifest = load_decision_manifest(args.decision_manifest)
        if decision_manifest is None:
            raise LedgerError("shared-destination merge requires --decision-manifest")
        with transaction(connection):
            item = run_item(connection, args.run_id, args.relative_path)
            if item["state"] != "reviewed":
                raise LedgerError(f"cannot merge item in state {item['state']}")
            verified_quarantine(vault_root, item)
            loss_acknowledged = bool(
                item["loss_acknowledged"] or args.acknowledge_loss
            )
            if item["loss_details"] and not loss_acknowledged:
                raise LedgerError(
                    "lossy item requires explicit --acknowledge-loss before a terminal decision"
                )
            references = connection.execute(
                """
                SELECT output_id, run_id, version_id, destination_hash
                FROM integration_outputs
                WHERE destination=? AND active=1
                ORDER BY output_id
                """,
                (args.destination,),
            ).fetchall()
            if not references:
                raise LedgerError(
                    "destination has no existing integration output; use integrate instead"
                )
            current_hash = raw_hash(destination)
            if current_hash != args.expected_destination_hash:
                raise LedgerError("destination changed after merge approval")
            stale_references = [
                dict(row)
                for row in references
                if row["destination_hash"] != current_hash
            ]
            if stale_references:
                raise LedgerError(
                    "existing destination references are already inconsistent: "
                    + json.dumps(stale_references, ensure_ascii=False)
                )
            merged_data = staged_file.read_bytes()
            merged_hash = sha256_bytes(merged_data)
            if merged_hash == current_hash:
                raise LedgerError("staged merge does not change the destination")
            original_data = destination.read_bytes()
            original_mode = destination.stat().st_mode & 0o7777
            atomic_write_bytes(destination, merged_data, original_mode)
            destination_replaced = True
            if raw_hash(destination) != merged_hash:
                raise LedgerError("destination hash does not match the staged merge")
            integrated_at = now()
            connection.execute(
                """
                UPDATE integration_outputs
                SET destination_hash=?
                WHERE destination=? AND active=1
                """,
                (merged_hash, args.destination),
            )
            connection.execute(
                """
                UPDATE run_items
                SET destination_hash=?
                WHERE destination=? AND state='integrated'
                """,
                (merged_hash, args.destination),
            )
            connection.execute(
                """
                UPDATE run_items SET
                    state='integrated', decision='update', decision_manifest=?,
                    loss_acknowledged=?, destination=?, destination_hash=?, integrated_at=?
                WHERE run_id=? AND version_id=?
                """,
                (
                    decision_manifest,
                    int(loss_acknowledged),
                    args.destination,
                    merged_hash,
                    integrated_at,
                    args.run_id,
                    item["version_id"],
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
                    args.run_id,
                    item["version_id"],
                    args.destination,
                    merged_hash,
                    decision_manifest,
                    integrated_at,
                ),
            )
            resolution_status = refresh_resolution_status(connection, args.run_id)
        return {
            "ok": True,
            "run_id": args.run_id,
            "state": "integrated",
            "destination": args.destination,
            "previous_destination_hash": args.expected_destination_hash,
            "destination_hash": merged_hash,
            "refreshed_existing_outputs": len(references),
            "resolution_status": resolution_status,
        }
    except Exception:
        if destination_replaced and original_data is not None and original_mode is not None:
            try:
                atomic_write_bytes(destination, original_data, original_mode)
            except OSError as rollback_error:
                raise LedgerError(
                    f"merge failed and destination rollback failed: {rollback_error}"
                ) from rollback_error
        raise
    finally:
        connection.close()


def active_artifact_problems(
    connection: sqlite3.Connection,
    vault_root: Path,
    run_id: str | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT artifact_id, run_id, artifact_path, artifact_hash, artifact_role
        FROM run_artifacts
        WHERE active=1
    """
    params: tuple[Any, ...] = ()
    if run_id is not None:
        query += " AND run_id=?"
        params = (run_id,)
    query += " ORDER BY artifact_id"
    problems = []
    for artifact_row in connection.execute(query, params):
        artifact = resolve_vault_path(vault_root, artifact_row["artifact_path"])
        if not artifact.is_file():
            problems.append({**dict(artifact_row), "problem": "missing artifact"})
        elif raw_hash(artifact) != artifact_row["artifact_hash"]:
            problems.append(
                {**dict(artifact_row), "problem": "artifact hash changed"}
            )
    return problems


def scoped_output_records(
    connection: sqlite3.Connection,
    run_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = [
        dict(row)
        for row in connection.execute(
            """
            SELECT run_id, version_id, destination, destination_hash
            FROM integration_outputs
            WHERE run_id=? AND active=1
            ORDER BY output_id
            """,
            (run_id,),
        )
    ]
    problems: list[dict[str, Any]] = []
    retained = connection.execute(
        """
        SELECT rowid AS observation_rowid, version_id
        FROM run_items
        WHERE run_id=? AND state='skipped' AND decision='retain'
        ORDER BY rowid
        """,
        (run_id,),
    ).fetchall()
    for observation in retained:
        resolution = connection.execute(
            """
            SELECT run_id, version_id, destination, destination_hash
            FROM run_items
            WHERE version_id=? AND state='integrated' AND decision IS NOT NULL
              AND rowid < ?
            ORDER BY rowid DESC
            LIMIT 1
            """,
            (observation["version_id"], observation["observation_rowid"]),
        ).fetchone()
        if resolution is None:
            problems.append(
                {
                    "run_id": run_id,
                    "version_id": observation["version_id"],
                    "problem": "retained item has no prior integrated decision",
                }
            )
            continue
        outputs = resolution_outputs(connection, resolution)
        if not outputs:
            problems.append(
                {
                    "run_id": run_id,
                    "version_id": observation["version_id"],
                    "problem": "retained item has no active prior output",
                }
            )
            continue
        records.extend(
            {
                "run_id": run_id,
                "version_id": observation["version_id"],
                "destination": output["destination"],
                "destination_hash": output["destination_hash"],
                "retained_from_run_id": resolution["run_id"],
            }
            for output in outputs
        )
    return records, problems


def output_problems(
    connection: sqlite3.Connection,
    vault_root: Path,
    run_id: str | None = None,
) -> list[dict[str, Any]]:
    if run_id is None:
        records = [
            dict(row)
            for row in connection.execute(
                """
                SELECT run_id, version_id, destination, destination_hash
                FROM integration_outputs WHERE active=1 ORDER BY output_id
                """
            )
        ]
        problems: list[dict[str, Any]] = []
    else:
        records, problems = scoped_output_records(connection, run_id)
    for record in records:
        destination = resolve_vault_path(vault_root, record["destination"])
        if not destination.is_file():
            problems.append({**record, "problem": "missing destination"})
        elif raw_hash(destination) != record["destination_hash"]:
            problems.append({**record, "problem": "destination hash changed"})
    if run_id is not None:
        missing_output_items = connection.execute(
            """
            SELECT ri.run_id, ri.version_id, ri.destination,
                   ri.destination_hash
            FROM run_items ri
            WHERE ri.run_id=? AND ri.state='integrated'
              AND NOT EXISTS (
                  SELECT 1 FROM integration_outputs io
                  WHERE io.run_id=ri.run_id
                    AND io.version_id=ri.version_id
                    AND io.active=1
              )
            ORDER BY ri.rowid
            """,
            (run_id,),
        )
        problems.extend(
            {**dict(item), "problem": "integrated item has no active output"}
            for item in missing_output_items
        )
    return problems


def cleanup_readiness(
    connection: sqlite3.Connection,
    vault_root: Path,
    run_id: str,
) -> dict[str, Any]:
    rows = connection.execute(
        """
        SELECT ri.*, fv.raw_hash
        FROM run_items ri
        JOIN fingerprint_versions fv ON fv.version_id=ri.version_id
        WHERE ri.run_id=? ORDER BY ri.rowid
        """,
        (run_id,),
    ).fetchall()
    if not rows:
        raise LedgerError("run has no items")
    unresolved = [row["state"] for row in rows if row["state"] not in TERMINAL_STATES]
    if unresolved:
        raise LedgerError(f"run has unresolved states: {sorted(set(unresolved))}")
    if any(row["decision"] is None for row in rows):
        raise LedgerError("run has terminal items without recorded owner decisions")
    if any(row["loss_details"] and not row["loss_acknowledged"] for row in rows):
        raise LedgerError("run has lossy items without owner acknowledgment")

    destination_problems = output_problems(connection, vault_root, run_id)
    if destination_problems:
        raise LedgerError(
            "integration outputs failed verification: "
            + json.dumps(destination_problems, ensure_ascii=False)
        )
    artifact_problems = active_artifact_problems(connection, vault_root, run_id)
    if artifact_problems:
        raise LedgerError(
            "run artifacts failed verification: "
            + json.dumps(artifact_problems, ensure_ascii=False)
        )

    existing_paths = []
    absent_paths = []
    for row in rows:
        if not row["quarantine_path"]:
            continue
        path = verified_quarantine(vault_root, row, allow_absent=True)
        (existing_paths if path is not None else absent_paths).append(
            row["quarantine_path"]
        )
    return {
        "rows": rows,
        "existing_paths": existing_paths,
        "absent_paths": absent_paths,
    }


def cleanup_plan_command(args: argparse.Namespace) -> dict[str, Any]:
    connection = connect(Path(args.db).expanduser().resolve())
    vault_root = Path(args.vault_root).expanduser().resolve()
    try:
        ensure_schema(connection)
        readiness = cleanup_readiness(connection, vault_root, args.run_id)
        existing_paths = readiness["existing_paths"]
        absent_paths = readiness["absent_paths"]
        return {
            "ok": True,
            "run_id": args.run_id,
            "resolution_status": "resolved",
            "quarantine_paths": existing_paths,
            "already_absent_paths": absent_paths,
            "remaining_count": len(existing_paths),
        }
    finally:
        connection.close()


def cleanup_command(args: argparse.Namespace) -> dict[str, Any]:
    connection = connect(Path(args.db).expanduser().resolve())
    vault_root = Path(args.vault_root).expanduser().resolve()
    try:
        ensure_schema(connection)
        with transaction(connection):
            readiness = cleanup_readiness(connection, vault_root, args.run_id)
            remaining = readiness["existing_paths"]
            if remaining:
                raise LedgerError(
                    "quarantine paths still exist; move them through Obsidian trash first: "
                    + ", ".join(remaining)
                )
            cleaned_at = now()
            connection.execute(
                "UPDATE run_items SET cleaned_at=? WHERE run_id=?",
                (cleaned_at, args.run_id),
            )
            connection.execute(
                """
                UPDATE runs
                SET status='completed', completed_at=COALESCE(completed_at, ?), cleaned_at=?
                WHERE run_id=?
                """,
                (cleaned_at, cleaned_at, args.run_id),
            )
        return {"ok": True, "run_id": args.run_id, "cleaned_at": cleaned_at}
    finally:
        connection.close()


def verify_command(args: argparse.Namespace) -> dict[str, Any]:
    connection = connect(Path(args.db).expanduser().resolve())
    try:
        ensure_schema(connection)
        if args.run_id and not args.vault_root:
            raise LedgerError("run-scoped verification requires --vault-root")
        if args.run_id:
            run = connection.execute(
                "SELECT run_id FROM runs WHERE run_id=?", (args.run_id,)
            ).fetchone()
            if run is None:
                raise LedgerError(f"run does not exist: {args.run_id}")
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        foreign_keys = [dict(row) for row in connection.execute("PRAGMA foreign_key_check")]
        counts = {}
        for table in (
            "runs",
            "source_items",
            "fingerprint_versions",
            "run_items",
            "integration_outputs",
        ):
            counts[table] = connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        item_scope = " AND run_id=?" if args.run_id else ""
        item_params = (args.run_id,) if args.run_id else ()
        unresolved = connection.execute(
            """
            SELECT count(*) FROM run_items
            WHERE state NOT IN ('integrated', 'skipped', 'discarded')
            """ + item_scope,
            item_params,
        ).fetchone()[0]
        undecided = connection.execute(
            """
            SELECT count(*) FROM run_items
            WHERE decision IS NULL
            """ + item_scope,
            item_params,
        ).fetchone()[0]
        unacknowledged_lossy_terminal = connection.execute(
            """
            SELECT count(*) FROM run_items
            WHERE state IN ('integrated', 'skipped', 'discarded')
              AND loss_details IS NOT NULL AND loss_acknowledged=0
            """ + item_scope,
            item_params,
        ).fetchone()[0]
        review_group_count = connection.execute(
            "SELECT count(DISTINCT review_group) FROM run_items "
            "WHERE review_group IS NOT NULL" + item_scope,
            item_params,
        ).fetchone()[0]
        if args.run_id:
            resolution_counts = {
                row["resolution_status"]: row["count"]
                for row in connection.execute(
                    """
                    SELECT resolution_status, count(*) AS count
                    FROM runs WHERE run_id=? GROUP BY resolution_status
                    """,
                    (args.run_id,),
                )
            }
        else:
            resolution_counts = {
                row["resolution_status"]: row["count"]
                for row in connection.execute(
                    """
                    SELECT resolution_status, count(*) AS count
                    FROM runs GROUP BY resolution_status
                    """
                )
            }
        destination_problems = []
        artifact_problems = []
        if args.vault_root:
            vault_root = Path(args.vault_root).expanduser().resolve()
            destination_problems = output_problems(
                connection, vault_root, args.run_id
            )
            artifact_problems = active_artifact_problems(
                connection, vault_root, args.run_id
            )
        result = {
            "ok": (
                integrity == ["ok"]
                and not foreign_keys
                and not unacknowledged_lossy_terminal
                and not destination_problems
                and not artifact_problems
            ),
            "integrity_check": integrity,
            "foreign_key_check": foreign_keys,
            "counts": counts,
            "unresolved_items": unresolved,
            "unacknowledged_lossy_terminal": unacknowledged_lossy_terminal,
            "review_group_count": review_group_count,
            "resolution_counts": resolution_counts,
            "destination_problems": destination_problems,
            "artifacts_valid": not artifact_problems,
            "artifact_problems": artifact_problems,
        }
        if not args.run_id:
            return result

        item_count = connection.execute(
            "SELECT count(*) FROM run_items WHERE run_id=?", (args.run_id,)
        ).fetchone()[0]
        decision_complete = (
            item_count > 0
            and unresolved == 0
            and undecided == 0
            and unacknowledged_lossy_terminal == 0
        )
        outputs_valid = not destination_problems
        artifacts_valid = not artifact_problems
        cleanup_eligible = (
            integrity == ["ok"]
            and not foreign_keys
            and decision_complete
            and outputs_valid
            and artifacts_valid
        )
        result.update(
            {
                "ok": cleanup_eligible,
                "run_id": args.run_id,
                "decision_complete": decision_complete,
                "outputs_valid": outputs_valid,
                "artifacts_valid": artifacts_valid,
                "cleanup_eligible": cleanup_eligible,
            }
        )
        return result
    finally:
        connection.close()


def add_db(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", required=True, help="SQLite ledger path")


def add_file_identity(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--file", required=True, help="Source file path")
    parser.add_argument("--source-key", required=True, help="Stable logical source label")
    parser.add_argument("--relative-path", required=True, help="Source-relative path")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create or verify the ledger schema")
    add_db(init)
    init.set_defaults(handler=init_command)

    classify_parser = subparsers.add_parser("classify", help="Classify one source file read-only")
    add_db(classify_parser)
    add_file_identity(classify_parser)
    classify_parser.set_defaults(handler=classify_command)

    record = subparsers.add_parser("record-import", help="Record an importer handoff")
    add_db(record)
    add_file_identity(record)
    record.add_argument("--run-id", required=True)
    record.add_argument("--vault-root", required=True)
    record.add_argument("--quarantine-path")
    record.add_argument("--loss-details")
    record.set_defaults(handler=record_import_command)

    review = subparsers.add_parser("review", help="Record an independent review")
    add_db(review)
    review.add_argument("--run-id", required=True)
    review.add_argument("--relative-path", required=True)
    review.add_argument("--vault-root", required=True)
    review.add_argument(
        "--classification",
        required=True,
        choices=("unique", "changed", "exact_duplicate", "probable_duplicate", "conflict", "failed"),
    )
    review.add_argument("--report", required=True)
    review.add_argument("--review-group")
    review.add_argument("--loss-details")
    review.set_defaults(handler=review_command)

    integrate = subparsers.add_parser("integrate", help="Record an owner-approved decision")
    add_db(integrate)
    integrate.add_argument("--run-id", required=True)
    integrate.add_argument("--relative-path", required=True)
    integrate.add_argument("--vault-root", required=True)
    integrate.add_argument(
        "--decision",
        required=True,
        choices=("integrate", "update", "retain", "skip", "discard"),
    )
    integrate.add_argument("--destination")
    integrate.add_argument(
        "--additional-destination",
        action="append",
        default=[],
        help="Additional output path for an approved split; repeat as needed",
    )
    integrate.add_argument(
        "--decision-manifest",
        help="JSON object recording included, excluded, sanitized, and split sections",
    )
    integrate.add_argument(
        "--acknowledge-loss",
        action="store_true",
        help="Record explicit owner acceptance of known source loss",
    )
    integrate.set_defaults(handler=integrate_command)

    supersede = subparsers.add_parser(
        "supersede-decision",
        help="Record a replacement for an integrated decision without changing vault files",
    )
    add_db(supersede)
    supersede.add_argument("--run-id", required=True)
    supersede.add_argument("--relative-path", required=True)
    supersede.add_argument("--vault-root", required=True)
    supersede.add_argument("--expected-state", required=True)
    supersede.add_argument("--expected-output-hash")
    supersede.add_argument(
        "--decision", required=True, choices=("skip", "discard", "reopen")
    )
    supersede.add_argument("--reason", required=True)
    supersede.set_defaults(handler=supersede_decision_command)

    artifact = subparsers.add_parser(
        "record-artifact", help="Record or revise a run-owned vault artifact"
    )
    add_db(artifact)
    artifact.add_argument("--run-id", required=True)
    artifact.add_argument("--vault-root", required=True)
    artifact.add_argument("--path", required=True)
    artifact.add_argument("--role", required=True)
    artifact.add_argument("--expected-previous-hash")
    artifact.add_argument("--reason", required=True)
    artifact.set_defaults(handler=record_artifact_command)

    merge_destination = subparsers.add_parser(
        "merge-destination",
        help="Atomically merge one reviewed item into a tracked destination",
    )
    add_db(merge_destination)
    merge_destination.add_argument("--run-id", required=True)
    merge_destination.add_argument("--relative-path", required=True)
    merge_destination.add_argument("--vault-root", required=True)
    merge_destination.add_argument("--destination", required=True)
    merge_destination.add_argument("--staged-file", required=True)
    merge_destination.add_argument("--expected-destination-hash", required=True)
    merge_destination.add_argument("--decision-manifest", required=True)
    merge_destination.add_argument(
        "--acknowledge-loss",
        action="store_true",
        help="Record explicit owner acceptance of known source loss",
    )
    merge_destination.set_defaults(handler=merge_destination_command)

    cleanup_plan = subparsers.add_parser(
        "cleanup-plan",
        help="Verify cleanup gates and list active quarantine paths read-only",
    )
    add_db(cleanup_plan)
    cleanup_plan.add_argument("--run-id", required=True)
    cleanup_plan.add_argument("--vault-root", required=True)
    cleanup_plan.set_defaults(handler=cleanup_plan_command)

    cleanup = subparsers.add_parser("cleanup", help="Record verified Obsidian-trash cleanup")
    add_db(cleanup)
    cleanup.add_argument("--run-id", required=True)
    cleanup.add_argument("--vault-root", required=True)
    cleanup.set_defaults(handler=cleanup_command)

    verify = subparsers.add_parser("verify", help="Check ledger integrity and counts")
    add_db(verify)
    verify.add_argument(
        "--vault-root",
        help="When supplied, verify every recorded integration output hash",
    )
    verify.add_argument(
        "--run-id",
        help="Limit output and artifact verification to one migration run",
    )
    verify.set_defaults(handler=verify_command)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.handler(args)
    except (LedgerError, sqlite3.Error, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
