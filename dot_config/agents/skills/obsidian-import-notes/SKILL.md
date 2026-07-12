---
name: obsidian-import-notes
description: Coordinate repeatable imports of notes and attachments into an Obsidian quarantine using a SQLite import ledger. Use for Apple Notes, Notion, Raycast Notes, exports, loose files, or newly discovered note locations when separate subagents must import, review duplicates, and integrate approved notes without cluttering the vault.
---

# Obsidian Note Import

Follow the vault's `AGENTS.md` and migration plan. Process one source and run at a time. The primary agent coordinates three distinct subagents and does not perform their import, review, or integration work. Do not create a migration backup.

## SQLite ledger

Use `_Imports/imports.sqlite3` as the authoritative record of runs, discovered files, review decisions, and final destinations. Use one database writer at a time, enable foreign keys on every connection, and commit each subagent handoff in a transaction. Run an integrity check before and after each run.

Calculate each file's import fingerprint in this exact order:

```text
SHA-256(NFC(file_name) + NUL + size_bytes + NUL + source_key + NUL + lower(file_type))
```

Use the filename, integer byte size, stable source label, and lowercase extension without the dot; use `unknown` when no type exists. Store the source-relative path, a raw SHA-256 hash for exact change and collision detection, and a normalized hash for Markdown duplicate review.

The ledger retains fingerprint history and records source metadata, quarantine path, content and attachment hashes, state, review decision, approved destination, destination hash, integration time, cleanup time, and run IDs. Link a changed version to its previous fingerprint. Never use `INSERT OR REPLACE`; explicitly insert or update records so history is not silently deleted.

Treat SQLite as authoritative. A quarantine file or report without matching committed rows is an interrupted run: the importer must reconcile and resume it before review. Do not infer success from files alone.

Use `scripts/import_ledger.py` for the schema, fingerprints, classifications, and transactional handoffs. It records and verifies state; it never copies, moves, overwrites, or deletes notes.

```bash
rtk python3 ~/.config/agents/skills/obsidian-import-notes/scripts/import_ledger.py init --db "<vault>/_Imports/imports.sqlite3"
rtk python3 ~/.config/agents/skills/obsidian-import-notes/scripts/import_ledger.py classify --db "<vault>/_Imports/imports.sqlite3" --file "<source-file>" --source-key "<stable-source>" --relative-path "<source-relative-path>"
```

Run `init` once to create or verify the ledger. Run the read-only `classify` before writing a quarantine copy. Discover the importer, reviewer, integrator, cleanup, and verification handoff options with `.../import_ledger.py --help` and `<command> --help`; do not guess arguments.

## Import step by step

1. **Coordinator:** choose a stable `source_key` such as `apple-notes:icloud`, create a run ID, and start a dedicated importer subagent.
2. **Importer:** inventory the source without changing it. Record counts and compute a fingerprint for every note and attachment before conversion when possible.
3. **Importer:** query SQLite for every fingerprint:
   - exact fingerprint and raw hash already resolved, with an existing destination whose hash still matches the ledger: skip;
   - exact source match with a missing or changed recorded destination: quarantine as a conflict; never recreate or overwrite it automatically;
   - exact fingerprint already quarantined or reviewed: resume the existing item;
   - exact fingerprint with a different raw hash or path: import to quarantine as changed or conflicting content;
   - content matching an older history entry but not the latest version for that source identity: reimport as a changed reversion and link it to the latest version;
   - no exact fingerprint, but the same source, filename, file type, and source-relative path existed before: create a new fingerprint version, link the previous fingerprint, and reimport to quarantine as changed;
   - a similar prior record at a different source-relative path: mark it for conflict or duplicate review;
   - no fingerprint history: import to quarantine as new;
   - previously failed: return it to review.
4. **Importer:** if a bulk importer cannot filter first, isolate its complete output in the new quarantine run, fingerprint it there, and exclude known items from further processing. Preserve titles, dates, source URLs, original folders, attachments, and links. Commit the ledger transaction, query the rows back, verify they match quarantine, then write the import report. Do not review or integrate.
5. **Coordinator:** start a different reviewer subagent without the importer's conclusions.
6. **Reviewer:** compare quarantine, ledger, and permanent vault. Before recording review, require the ledger tool to verify that the stored quarantine path exists and its raw hash still matches. If it is missing or altered, the importer restores the exact working copy from the unchanged source to the ledger's existing quarantine path; resume that run rather than creating another. Classify every note as unchanged, changed, exact duplicate, probable duplicate, unique, conflict, or failed. For duplicates, identify the canonical note and recommend skip, merge, or retain both. For every note, provide a short content summary, assess its value as keep, uncertain, or garbage with a reason, and recommend a folder, links, tags, properties, or discard. Write `_Imports/Reviews/<run-id>.md`; do not integrate.
7. **Coordinator:** use the report as a source of truth, but walk the owner through decisions topic by topic or file by file. For each small group, state what every note contains, why it is or is not useful, and the proposed action and destination. Never replace this with a blanket “approve all recommendations” request. Ask individually about important, sensitive, lossy, ambiguous, merge, replacement, and garbage decisions. Empty, duplicate, expired, marker-only, or meaningless notes may be recommended as garbage, but require an explicit owner decision and record the reason. Record decisions incrementally before moving to the next topic.
8. **Coordinator:** after approval, start a third integrator subagent.
9. **Integrator:** apply only recorded decisions, preserve vault organization and working links, and update SQLite with the destination, destination hash, decision, and integration time. Leave unapproved items in quarantine.
10. **Integrator:** write the run report, run SQLite integrity and foreign-key checks, then rescan the same source. An identical rerun with intact destinations must produce zero new integrations; changed sources or missing and altered destinations return to review.
11. **Integrator:** after every item has a resolved terminal state and the checks pass, run `rtk obsidian delete path="<vault-relative-quarantine-file>"` for each quarantined note and attachment. Require a `Moved to trash` response and verify active paths are absent before recording `cleaned_at` in SQLite. Never use `rm`, `unlink`, or raw filesystem deletion for vault files. Never remove original source files, the ledger, reports, or integrated notes. If any item is failed, unresolved, or awaiting approval, leave the run quarantine intact.

## Improve the skill

After a real run exposes a reusable gap, propose a concise skill change and ask the owner to review it before editing. Keep source-specific facts and one-off decisions in the database, review report, or migration plan.
