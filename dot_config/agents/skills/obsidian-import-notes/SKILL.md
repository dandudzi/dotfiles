---
name: obsidian-import-notes
description: Coordinate repeatable, privacy-aware imports of notes and attachments into an Obsidian quarantine using a SQLite ledger. Use for Apple Notes, Notion, Raycast Notes, exports, loose files, mixed notes that need splitting, lossy conversions, duplicate attachments, or newly discovered note locations when separate subagents must import, review, and integrate owner-approved content.
---

# Obsidian Note Import

Follow the vault's `AGENTS.md` and migration plan. Process one source and run at a time. The primary agent coordinates distinct importer, reviewer, and integrator subagents; it does not perform their phase work. Do not create a migration backup.

## Invariants

- Preserve raw exports and inventory them before conversion.
- Write imports only below `_Imports/Quarantine/<run-id>/`, never directly into permanent folders.
- Keep quarantine, reports, and `_Imports/imports.sqlite3` separate from permanent notes.
- Use one database writer at a time, enable foreign keys on every connection, and commit each handoff in one transaction.
- Treat SQLite as authoritative for runs, file identities and hashes, decisions, outputs, artifacts, and cleanup. Keep archive manifests and conversion reconciliation in the hash-tracked importer report.
- Treat a file or report without matching committed ledger state as interrupted work that the importer must reconcile.
- Preserve decision history. Reopen or supersede a terminal decision; never overwrite it.
- Run scoped verification before cleanup and an integrity check before and after every run.

## SQLite ledger

Calculate each file's import fingerprint in this exact order:

```text
SHA-256(NFC(file_name) + NUL + size_bytes + NUL + source_key + NUL + lower(file_type))
```

Use the filename, integer byte size, stable source label, and lowercase extension without the dot; use `unknown` when no type exists. Store the source-relative path, raw SHA-256 hash, and normalized Markdown hash. Link changed versions to their latest predecessor. Never use `INSERT OR REPLACE`.

Use `scripts/import_ledger.py` for schema, classification, and transactional handoffs. It records and verifies state; it does not copy, move, overwrite, or delete notes.

```bash
rtk python3 ~/.config/agents/skills/obsidian-import-notes/scripts/import_ledger.py init --db "<vault>/_Imports/imports.sqlite3"
rtk python3 ~/.config/agents/skills/obsidian-import-notes/scripts/import_ledger.py classify --db "<vault>/_Imports/imports.sqlite3" --file "<source-file>" --source-key "<stable-source>" --relative-path "<source-relative-path>"
```

Run `init` once. Run read-only `classify` before creating a quarantine copy. Discover every mutating command with `.../import_ledger.py <command> --help`; do not guess arguments. Treat a nonzero exit or JSON containing `"ok": false` as failure.

Classify each item as follows:

- Reuse an exact resolved version only when every recorded output still matches; the new run records `retain` without another owner decision or integration.
- Resume an exact quarantined or reviewed version in its existing run.
- Quarantine missing or altered outputs as conflicts; never recreate or overwrite them automatically.
- Link changed content, reversions, and new versions of the same source identity to the latest version.
- Flag similar names or paths only for duplicate review. Never merge by filename or fuzzy similarity.
- Return failed or interrupted work to importer reconciliation.

## Phases

### 1. Import

The coordinator chooses a stable `source_key` such as `apple-notes:icloud`, creates the run ID, and starts the importer.

The importer records the canonical source identity, byte size, raw hash, member manifest, and unpacked-only host artifacts in `_Imports/Reports/<run-id>-importer.md`. Exclude host artifacts from completeness unless present in the canonical archive. Preserve titles, dates, source URLs, original folders, attachments, and links. Validate converted bodies against a stable source representation and reconcile attachments, URLs, missing items, orphan markers, and unknown identifiers. Record item-specific loss in SQLite.

If a bulk importer cannot filter first, isolate all output in the run quarantine, fingerprint it there, and stop processing known items. Commit the handoff, read it back, verify quarantine hashes, then register the importer report with `record-artifact`. Do not review or integrate.

### 2. Independent review

The coordinator starts a reviewer without the importer's conclusions. The reviewer verifies every quarantine hash, compares it with the ledger and permanent vault, and groups each parent with embeds, attachments, duplicates, and missing assets. Identify mixed notes that need semantic splitting.

Write `_Imports/Reviews/<run-id>.md`, record every classification and review group, and register the report with `record-artifact`. Separate source facts from inference and proposed design. Redact credentials, codes, phone numbers, addresses, and account identifiers from owner-facing text. Return missing or altered quarantine to the importer. Do not integrate.

### 3. Owner decisions

Present one file or coherent topic per decision card: source identity, content, value, privacy or staleness, known loss, recommendation, and proposed destination or transformation. Use only **keep/import**, **garbage/do not import**, or **defer** as owner-facing dispositions; do not say bare **skip**.

Decide duplicates, conflicts, placeholders, sensitive content, merges, and lossy conversions individually. Batch only homogeneous ordinary items and list every member and exclusion. For a mixed note, obtain a disposition, sanitization, and destination decision for each smallest coherent section. Require explicit loss acceptance. Record decisions incrementally. Use `supersede-decision --decision reopen` before replacing a terminal decision.

### 4. Integration

After approval, start the integrator. It applies only the latest recorded decision and re-verifies quarantine immediately before integration. Leave unapproved items quarantined and never place credentials in Markdown.

For split or sanitized notes, provide a privacy-safe JSON decision manifest listing included, excluded, sanitized, and destination sections by label and reason. Record additional outputs with repeated `--additional-destination`. For a shared destination, stage the complete result and use `merge-destination` with its verified current hash. Require `--acknowledge-loss` for every lossy terminal decision.

Register each derived Base, dashboard, index, manifest, and `_Imports/Reports/<run-id>-integrator.md` with `record-artifact`, using a role and reason that identify its phase and scope. Do not revise phase reports or attach a shared artifact to an arbitrary item.

Run scoped `verify`, then rescan the source. An identical rerun with intact outputs must create no new files or integrations. Changed sources and missing or altered outputs return to review. Report unrelated ledger-wide problems separately.

### 5. Cleanup

Write and register `_Imports/Reports/<run-id>-cleanup.md`, then run read-only `cleanup-plan`. It must confirm decisions, loss acknowledgments, output and artifact hashes, quarantine hashes, and exact active quarantine paths.

Confirm the Obsidian CLI can see the running app; launch Obsidian when authorized. Trash each listed working copy with:

```bash
rtk obsidian delete path="<vault-relative-quarantine-file>"
```

Require `Moved to trash` and active-path absence, then run `cleanup`, which rechecks outputs and artifacts before completing the run. Never delete vault files through the raw filesystem. Preserve sources, outputs, ledger, and reports. If Obsidian cannot trash empty folders, leave and report them.

Keep source-specific extraction commands out of this skill. Put reusable source behavior in a source-specific skill or script that produces the same inventory, canonical-validation, quarantine, and ledger handoff contract.

## Improve the skill

After a real run exposes a reusable gap, propose a concise change and ask the owner to review it before editing. Keep source-specific facts and one-off decisions in SQLite, a phase report, or the migration plan.
