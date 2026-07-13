---
name: obsidian-import-notes
description: Coordinate repeatable, privacy-aware imports of notes and attachments into an Obsidian quarantine using a SQLite ledger. Use for Apple Notes, Notion, Raycast Notes, exports, loose files, mixed notes that need splitting, lossy conversions, duplicate attachments, or newly discovered note locations when separate subagents must import, review, and integrate owner-approved content.
---

# Obsidian Note Import

Follow the vault's `AGENTS.md` and migration plan. Keep raw exports unchanged and inventory them before conversion. Import only into source- and run-specific quarantine, never directly into permanent vault folders. Keep the ledger, review reports, and quarantine separate from permanent notes. Process one source and run at a time. The primary agent coordinates three distinct subagents and does not perform their import, review, or integration work. Do not create a migration backup.

## SQLite ledger

Use `_Imports/imports.sqlite3` as the authoritative record of runs, discovered files, review decisions, and final destinations. Use one database writer at a time, enable foreign keys on every connection, and commit each subagent handoff in a transaction. Run an integrity check before and after each run.

Calculate each file's import fingerprint in this exact order:

```text
SHA-256(NFC(file_name) + NUL + size_bytes + NUL + source_key + NUL + lower(file_type))
```

Use the filename, integer byte size, stable source label, and lowercase extension without the dot; use `unknown` when no type exists. Store the source-relative path, a raw SHA-256 hash for exact change and collision detection, and a normalized hash for Markdown duplicate review.

The ledger retains fingerprint history and records source metadata, quarantine path, hashes, review groups, loss details and acknowledgment, structured decisions, one or more integration outputs, cleanup, and run IDs. Link a changed version to its previous fingerprint. Never use `INSERT OR REPLACE`; explicitly insert or update records so history is not silently deleted.

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
4. **Importer:** if a bulk importer cannot filter first, isolate its complete output in the new quarantine run, fingerprint it there, and exclude known items from further processing. Preserve titles, dates, source URLs, original folders, attachments, and links. Choose a stable canonical source representation and validate every converted body against it; reconcile attachment totals, saved files, URLs, missing items, orphan markers, and unknown identifiers. Record loss details with the affected item. Commit the ledger transaction, query the rows back, verify they match quarantine, then write the import report. Do not accept file counts alone as conversion proof. Do not review or integrate.
5. **Coordinator:** start a different reviewer subagent without the importer's conclusions.
6. **Reviewer:** compare quarantine, ledger, and permanent vault. Before recording review, require the ledger tool to verify that the stored quarantine path exists and its raw hash still matches. If it is missing or altered, return it to the importer for reconciliation. Classify every item, group each parent note with its embeds, attachments, duplicates, and missing assets under one review group, and recommend their joint disposition. Identify mixed notes that need semantic splitting. Use filenames and fuzzy similarity only to flag possible matches for review; never merge, overwrite, delete, or permanently place content based on them alone. Summarize actual content and value, but redact credentials, codes, phone numbers, addresses, and account identifiers from owner-facing reports. Record loss details. Write `_Imports/Reviews/<run-id>.md`; do not integrate.
7. **Coordinator:** walk the owner through small topics or files. Present content, value, privacy or staleness, loss, and the proposed action and destination; never request blanket approval. Ask individually about sensitive, lossy, ambiguous, merge, replacement, split, and garbage decisions. For a mixed note, propose the smallest coherent sections and obtain keep, discard, sanitize, or destination decisions for every section. Require explicit acceptance before resolving a lossy item. Record decisions incrementally.
8. **Coordinator:** after approval, start a third integrator subagent.
9. **Integrator:** apply only recorded decisions. For split or sanitized notes, write a JSON decision manifest describing included, excluded, sanitized, and destination sections by label and reason without copying private values; record every output path and hash with `--additional-destination` when one source creates multiple notes. For an approved merge into an already tracked destination, stage the complete merged file, write a privacy-safe decision manifest, and use `merge-destination` with the verified current destination hash so the file replacement and every shared output hash update succeed or roll back together. Never place credentials in Markdown. Require `--acknowledge-loss` for any terminal decision on a lossy item. Leave unapproved items in quarantine.
10. **Integrator:** write the run report, verify SQLite, foreign keys, every output hash, review-group counts, and loss acknowledgments, then rescan the same source. An identical rerun with intact outputs must produce zero new integrations; changed sources or missing or altered outputs return to review.
11. **Integrator:** run the ledger's read-only `cleanup-plan` to verify resolution, losses, output hashes, and obtain exact active quarantine paths. Confirm the Obsidian CLI can see the running app; launch Obsidian when authorized rather than assigning this operational step to the owner. Use `rtk obsidian delete path="<vault-relative-quarantine-file>"` for each listed working copy. Require `Moved to trash` and active-path absence before recording cleanup. Never use raw filesystem deletion. Preserve original sources, outputs, ledger, and reports. If the CLI cannot trash folders, leave empty quarantine directories and record them instead of bypassing Obsidian.

Keep source-specific extraction commands out of this skill. Put reusable Apple Notes, Notion, or Raycast extraction behavior in a source-specific skill or script that produces the same inventory, canonical-validation, quarantine, and ledger handoff contract.

## Improve the skill

After a real run exposes a reusable gap, propose a concise skill change and ask the owner to review it before editing. Keep source-specific facts and one-off decisions in the database, review report, or migration plan.
