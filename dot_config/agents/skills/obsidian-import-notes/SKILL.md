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

Use the filename, integer byte size, stable source label, and lowercase extension without the dot; use `unknown` when no type exists. Store the source-relative path and a separate content hash for changed-content detection, collision detection, and duplicate review.

The ledger retains fingerprint history and records source metadata, quarantine path, content and attachment hashes, state, review decision, approved destination, destination hash, integration time, cleanup time, and run IDs. Link a changed version to its previous fingerprint. Never use `INSERT OR REPLACE`; explicitly insert or update records so history is not silently deleted.

Treat SQLite as authoritative. A quarantine file or report without matching committed rows is an interrupted run: the importer must reconcile and resume it before review. Do not infer success from files alone.

## Import step by step

1. **Coordinator:** choose a stable `source_key` such as `apple-notes:icloud`, create a run ID, and start a dedicated importer subagent.
2. **Importer:** inventory the source without changing it. Record counts and compute a fingerprint for every note and attachment before conversion when possible.
3. **Importer:** query SQLite for every fingerprint:
   - exact fingerprint and content hash already integrated: skip;
   - exact fingerprint already quarantined or reviewed: resume the existing item;
   - exact fingerprint with a different content hash or path: import to quarantine as changed or conflicting content;
   - no exact fingerprint, but the same source, filename, file type, and source-relative path existed before: create a new fingerprint version, link the previous fingerprint, and reimport to quarantine as changed;
   - a similar prior record at a different source-relative path: mark it for conflict or duplicate review;
   - no fingerprint history: import to quarantine as new;
   - previously failed: return it to review.
4. **Importer:** if a bulk importer cannot filter first, isolate its complete output in the new quarantine run, fingerprint it there, and exclude known items from further processing. Preserve titles, dates, source URLs, original folders, attachments, and links. Commit the ledger transaction, query the rows back, verify they match quarantine, then write the import report. Do not review or integrate.
5. **Coordinator:** start a different reviewer subagent without the importer's conclusions.
6. **Reviewer:** compare quarantine, ledger, and permanent vault. Classify every note as unchanged, changed, exact duplicate, probable duplicate, unique, conflict, or failed. For duplicates, identify the canonical note and recommend skip, merge, or retain both. For unique notes, provide a short summary and recommend a folder, links, tags, and properties. Write `_Imports/Reviews/<run-id>.md`; do not integrate.
7. **Coordinator:** present the review report and ask the owner for decisions. Batch routine placements when reviewable; ask individually about merges, replacements, deletions, and ambiguous duplicates.
8. **Coordinator:** after approval, start a third integrator subagent.
9. **Integrator:** apply only recorded decisions, preserve vault organization and working links, and update SQLite with the destination, destination hash, decision, and integration time. Leave unapproved items in quarantine.
10. **Integrator:** write the run report, run SQLite integrity and foreign-key checks, then rescan the same source. An identical rerun must produce zero new integrations; changed or conflicting items return to review.
11. **Integrator:** after every item has a resolved terminal state and the checks pass, run `rtk obsidian delete path="<vault-relative-quarantine-file>"` for each quarantined note and attachment. Require a `Moved to trash` response and verify active paths are absent before recording `cleaned_at` in SQLite. Never use `rm`, `unlink`, or raw filesystem deletion for vault files. Never remove original source files, the ledger, reports, or integrated notes. If any item is failed, unresolved, or awaiting approval, leave the run quarantine intact.

## Improve the skill

After a real run exposes a reusable gap, propose a concise skill change and ask the owner to review it before editing. Keep source-specific facts and one-off decisions in the database, review report, or migration plan.
