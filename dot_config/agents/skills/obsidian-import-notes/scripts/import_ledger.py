#!/usr/bin/env python3
"""Deterministic SQLite ledger for the obsidian-import-notes workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 1
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
    cleaned_at TEXT
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
    decision TEXT,
    destination TEXT,
    destination_hash TEXT CHECK
        (destination_hash IS NULL OR length(destination_hash) = 64),
    integrated_at TEXT,
    cleaned_at TEXT,
    PRIMARY KEY (run_id, version_id),
    CHECK (state != 'quarantined' OR quarantine_path IS NOT NULL)
);
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
        connection.executescript(SCHEMA)
        with transaction(connection):
            existing = connection.execute(
                "SELECT value FROM schema_meta WHERE key='schema_version'"
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO schema_meta(key, value) VALUES('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
            elif int(existing["value"]) != SCHEMA_VERSION:
                raise LedgerError("existing ledger has an unsupported schema version")
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


def latest_resolution(
    connection: sqlite3.Connection, version_id: int
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT state, decision, destination, destination_hash
        FROM run_items
        WHERE version_id = ?
          AND state IN ('integrated', 'skipped', 'discarded')
          AND decision IS NOT NULL
        ORDER BY rowid DESC
        LIMIT 1
        """,
        (version_id,),
    ).fetchone()


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
                elif prior_resolution["destination"]:
                    if not prior_resolution["destination_hash"]:
                        destination_problem = "the recorded destination has no hash"
                    destination = resolve_vault_path(
                        vault_root, prior_resolution["destination"]
                    )
                    if destination_problem is None and not destination.is_file():
                        destination_problem = "the recorded destination is missing"
                    elif (
                        destination_problem is None
                        and raw_hash(destination) != prior_resolution["destination_hash"]
                    ):
                        destination_problem = "the recorded destination hash changed"
                elif prior_resolution["state"] == "integrated":
                    destination_problem = "the integrated item has no recorded destination"
                if destination_problem:
                    classification = "conflict"
                    result["matched_version_id"] = version_id
                    result["reason"] = destination_problem
            if classification == "unchanged":
                version_id = int(result["matched_version_id"])
                state = "skipped"
                quarantine_path = None
            else:
                if not args.quarantine_path:
                    raise LedgerError(
                        f"classification {classification} requires --quarantine-path"
                    )
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
            prior = connection.execute(
                "SELECT state FROM run_items WHERE run_id = ? AND version_id = ?",
                (args.run_id, version_id),
            ).fetchone()
            if prior is None:
                connection.execute(
                    """
                    INSERT INTO run_items(
                        run_id, version_id, classification, state, quarantine_path
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (args.run_id, version_id, classification, state, quarantine_path),
                )
            connection.execute(
                "UPDATE runs SET status='imported', imported_at=? WHERE run_id=?",
                (now(), args.run_id),
            )
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
            quarantine = resolve_vault_path(vault_root, item["quarantine_path"])
            if not quarantine.is_file():
                raise LedgerError(
                    "quarantine file is missing; return the item to the importer for reconciliation"
                )
            if raw_hash(quarantine) != item["raw_hash"]:
                raise LedgerError(
                    "quarantine content hash changed; return the item to the importer for reconciliation"
                )
            state = "failed" if args.classification == "failed" else "reviewed"
            connection.execute(
                """
                UPDATE run_items
                SET state=?, review_classification=?, review_report=?
                WHERE run_id=? AND version_id=?
                """,
                (state, args.classification, str(report), args.run_id, item["version_id"]),
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


def integrate_command(args: argparse.Namespace) -> dict[str, Any]:
    connection = connect(Path(args.db).expanduser().resolve())
    vault_root = Path(args.vault_root).expanduser().resolve()
    try:
        ensure_schema(connection)
        with transaction(connection):
            item = run_item(connection, args.run_id, args.relative_path)
            if item["state"] not in {"reviewed", "skipped"}:
                raise LedgerError(f"cannot decide item in state {item['state']}")
            if args.decision in {"integrate", "update", "retain"}:
                if not args.destination:
                    raise LedgerError("integration decision requires --destination")
                destination = resolve_vault_path(vault_root, args.destination)
                if not destination.is_file():
                    raise LedgerError(f"destination does not exist: {destination}")
                destination_hash = raw_hash(destination)
                state = "integrated"
                integrated_at = now()
            else:
                destination_hash = None
                if args.destination:
                    destination = resolve_vault_path(vault_root, args.destination)
                    if not destination.is_file():
                        raise LedgerError(f"destination does not exist: {destination}")
                    destination_hash = raw_hash(destination)
                integrated_at = None
                state = "discarded" if args.decision == "discard" else "skipped"
            connection.execute(
                """
                UPDATE run_items
                SET state=?, decision=?, destination=?, destination_hash=?, integrated_at=?
                WHERE run_id=? AND version_id=?
                """,
                (
                    state,
                    args.decision,
                    args.destination,
                    destination_hash,
                    integrated_at,
                    args.run_id,
                    item["version_id"],
                ),
            )
        return {
            "ok": True,
            "run_id": args.run_id,
            "state": state,
            "destination": args.destination,
            "destination_hash": destination_hash,
        }
    finally:
        connection.close()


def cleanup_command(args: argparse.Namespace) -> dict[str, Any]:
    connection = connect(Path(args.db).expanduser().resolve())
    vault_root = Path(args.vault_root).expanduser().resolve()
    try:
        ensure_schema(connection)
        with transaction(connection):
            rows = connection.execute(
                "SELECT state, quarantine_path FROM run_items WHERE run_id=?",
                (args.run_id,),
            ).fetchall()
            if not rows:
                raise LedgerError("run has no items")
            unresolved = [row["state"] for row in rows if row["state"] not in TERMINAL_STATES]
            if unresolved:
                raise LedgerError(f"run has unresolved states: {sorted(set(unresolved))}")
            undecided = connection.execute(
                "SELECT count(*) FROM run_items WHERE run_id=? AND decision IS NULL",
                (args.run_id,),
            ).fetchone()[0]
            if undecided:
                raise LedgerError(f"run has {undecided} terminal item(s) without a recorded decision")
            remaining = []
            for row in rows:
                if row["quarantine_path"]:
                    path = resolve_vault_path(vault_root, row["quarantine_path"])
                    if path.exists():
                        remaining.append(row["quarantine_path"])
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
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        foreign_keys = [dict(row) for row in connection.execute("PRAGMA foreign_key_check")]
        counts = {}
        for table in ("runs", "source_items", "fingerprint_versions", "run_items"):
            counts[table] = connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        unresolved = connection.execute(
            """
            SELECT count(*) FROM run_items
            WHERE state NOT IN ('integrated', 'skipped', 'discarded')
            """
        ).fetchone()[0]
        return {
            "ok": integrity == ["ok"] and not foreign_keys,
            "integrity_check": integrity,
            "foreign_key_check": foreign_keys,
            "counts": counts,
            "unresolved_items": unresolved,
        }
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
    integrate.set_defaults(handler=integrate_command)

    cleanup = subparsers.add_parser("cleanup", help="Record verified Obsidian-trash cleanup")
    add_db(cleanup)
    cleanup.add_argument("--run-id", required=True)
    cleanup.add_argument("--vault-root", required=True)
    cleanup.set_defaults(handler=cleanup_command)

    verify = subparsers.add_parser("verify", help="Check ledger integrity and counts")
    add_db(verify)
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
