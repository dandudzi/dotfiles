# Codex Config Guidelines

## Purpose
This folder is the canonical managed configuration area for Codex on this machine. Preserve the existing folder layout so live Codex paths can remain symlinks into one source of configuration.

## Organization
- `global.md`: global instructions, linked from `~/.codex/AGENTS.md`.
- `skills/<name>/SKILL.md`: skills, exposed through `~/.agents/skills`.
- `rules/default.rules`: execution policy, linked from `~/.codex/rules/default.rules`.

No custom agent definitions are maintained here. Keep reusable workflows in skills, including `linear-operator` for authorized Linear writes. Keep credentials, OAuth state, caches, logs, histories, and runtime state outside this folder.

## Skill Design
Keep each skill concise and focused on one tool, format, or workflow. Put durable safety rules and general operating practices in the applicable `AGENTS.md`, not in every skill.

- Include a small set of common operations with a short explanation of what each one does.
- Teach agents how to discover current commands, options, and documentation instead of copying large command references.
- Split unrelated formats or plugins into separate skills so only relevant instructions load.
- Avoid catch-all plugin inventories and broad alternatives or safety reference files unless the user explicitly requests them.
- Keep essential instructions in `SKILL.md`; add references only when the domain genuinely needs detailed material.

## Note Import Design
Keep note migrations repeatable and the destination vault organized.

- Preserve raw exports and inventory them before conversion.
- Do not create migration backups unless the user changes this rule.
- Place every imported note in source- and run-specific quarantine; never import directly into permanent vault folders.
- The primary agent coordinates three distinct subagents: one imports to quarantine, another independently reviews duplicates and recommends placement, and a third integrates only owner-approved decisions.
- Use `_Imports/imports.sqlite3` as the import ledger. Compute each SHA-256 fingerprint from NFC filename, byte size, stable source label, and lowercase file type, in that order with unambiguous separators.
- Retain fingerprint history. An exact fingerprint and content-hash match is unchanged; a prior record with the same source, filename, file type, and source-relative path but a different fingerprint is a changed version that must be reimported to quarantine.
- Store source-relative paths and separate content hashes so same-size content changes and fingerprint collisions become review items rather than silent skips. Use one database writer at a time and transactional subagent handoffs.
- Treat SQLite as authoritative. Quarantine or report files without matching committed rows indicate an interrupted run that the importer must reconcile before review.
- Never merge, overwrite, delete, or permanently place an imported note based only on a filename or fuzzy duplicate match.
- After conversion, check each note for exact and probable duplicates. Review with the owner topic by topic or file by file: summarize the actual content, assess its value, and recommend keep, organize, uncertain, or garbage with a reason and destination when applicable. Never ask for blanket approval of all recommendations. Important, sensitive, lossy, ambiguous, merge, replacement, and garbage decisions require individual approval; record decisions incrementally.
- Keep the ledger, review reports, and quarantine out of permanent content folders. Integrate notes only after independent review and owner approval.
- Never remove vault files with raw filesystem deletion. Use `obsidian delete path="<vault-relative-path>"` so Obsidian applies its configured trash behavior; verify `Moved to trash` and active-path absence.
- After a run is fully resolved and verified, move its quarantined working copies through Obsidian trash. Verify their active-path absence before recording cleanup in SQLite. Preserve original sources, the ledger, reports, and integrated notes.

## Existing Config Handling
Inspect live target paths and existing Codex settings before editing. Preserve unrelated MCP servers, hooks, permissions, models, skills, and agents. Do not add Claude Code or OpenCode wrappers, compatibility files, or symlinks unless the user explicitly requests them.

## Chezmoi
This directory lives under the rendered `~/.config` tree. Use the `persist-config-with-chezmoi` skill for exact-path persistence. Verify source cleanliness before operations that may auto-commit or auto-push. Never capture secrets or runtime state. Native tool files outside `~/.config` require explicit authorization for their exact path.
