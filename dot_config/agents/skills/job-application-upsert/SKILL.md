---
name: job-application-upsert
description: Safely duplicate-check, create, update, reopen, or mark Seen an Obsidian job-application record from a parsed posting packet. Use for any change to the Job Applications Base or application note.
---

# Upsert a job application

Own record identity and tracker mutations. Work in the active vault and use the Obsidian CLI; treat any CLI output containing `Error:` as a failure.

## Vault contract

- Query `Personal/Job Search/Job Applications.base`, normally with the `All jobs` view.
- Create from `Personal/Job Search/Templates/Job Application.md` only under `Personal/Job Search/Applications`.
- Keep the existing `role` property as seniority. Store the exact posting title in `job-title`.
- Populate `application-key`, `source-job-id`, `canonical-job-url`, and `posting-status` from the posting packet when known.

Map packet pointers directly: `source-job-id` to `source-job-id`, `source.canonical-job-url` to `canonical-job-url`, `company` to `company`, `job-title` to `job-title`, and `seniority` to `role`. Preserve `source.canonical-job-url` as a frontmatter value even when its URL is also represented by `job-link`.

## Resolve identity before writing

Inspect candidate records through the Base and their application notes. Compare in this strict priority:

1. Exact namespaced **source job ID** identity in `application-key` (`source.kind` or canonical host plus the ID). A bare source job ID is never sufficient across different sources.
2. Exact normalized **canonical job URL**.
3. Exact **company + exact job title + location**.
4. A fuzzy company/title comparison only as a possible match. Never merge, reopen, or replace a fuzzy match without user **confirmation**.

Namespace a `source-job-id` in `application-key` with `source.kind` (for example, `linkedin:1234`). When the ID is unavailable, namespace the canonical URL with its host (for example, `careers.example.com:https://careers.example.com/jobs/1234`). Otherwise derive a stable key from normalized company, exact job title, and location. Do not use a company name alone as a duplicate.

Before any mutation, normalize and reject every application path. It must be an exact direct child `.md` path of `Personal/Job Search/Applications`: no absolute path, `..`, separator, slash or backslash in the filename, or control character. Resolve and read the normalized path through Obsidian; for an existing note, verify `type: job-application` before updating, reopening, or marking Seen. Reject a nonconforming path or type instead of falling back to a nearby file.

## Choose the action

- Treat `Wishlist` (and legacy `Whishlist`), `Applied`, `Recruiter Screen`, `Technical Rounds`, `Final Round`, `Offer`, and `Negotiating` as active stages. Treat `Accepted`, `Rejected`, `Ghosted`, `Dropped by me`, `Withdrawn by company`, and `Seen` as terminal stages.
- For an exact match in an active stage, update only newly captured or explicitly requested fields and preserve user-written notes, interview notes, and stage unless the user asks to change them.
- For an exact record in a terminal stage, offer reopen; reopen only with the user's confirmation and preserve the prior outcome in the note.
- For an explicit Seen request with an exact or confirmed existing record in any other stage, return that record and leave its stage and content unchanged. When no match exists, create a minimal record with `stage: Seen`. Populate identity, company, job-title, location, job-link, found-via, date-found, and posting-status when available; do not add research, CV fit, or question-bank content.
- For no match, create a note from the template with `stage: Wishlist` unless the user supplies another stage.
- For a fuzzy candidate, return its path and differences, request confirmation, and make no mutation.

## Write and verify

Read the exact template or existing note immediately before changing it. Keep the exact parsed job title in `job-title`; create a separate single-line title for the rendered Markdown heading: sanitize externally supplied text, remove control characters, and escape Markdown link, embed, and heading syntax. For a new note, render `{{title}}` with that display title and `{{date:YYYY-MM-DD}}` from the current date before `rtk obsidian create`; verify the created note contains no unresolved template placeholders (`{{...}}`). Use `rtk obsidian property:set` with typed values for frontmatter, then use a focused Markdown patch only for the relevant body section. Never rewrite the whole template or unknown frontmatter.

Apply the workflow's shared safe Markdown renderer to every external or untrusted string and URL before inserting it into Markdown. Render multiline values in a collision-safe fenced code block longer than any backtick run. Render single-line values only after flattening line breaks, removing control characters, and escaping Markdown metacharacters so they are inert and cannot create headings, HTML, links, wikilinks, embeds, lists, tables, or code. Validate source URLs as public HTTPS, percent-encode unsafe delimiters, and expose them only through an agent-authored link label. Only agent-authored headings, list markers, table structure, and link labels may remain active Markdown.

For new records and exact updates, fill only empty or agent-managed content in `## Job posting`: `### Overview`, `### Responsibilities`, `### Required qualifications`, `### Preferred qualifications`, `### Complete captured description`, `### Benefits`, and `### Source URL`. Persist the source URL as `job-link` and `canonical-job-url`. Store the full description as inert literal text through the shared renderer's collision-safe fence; wikilinks, embeds, remote media, and heading boundaries cannot activate. Render every other posting-derived field with the same shared safe renderer. Make section boundary detection independent of untrusted headings by locating only the trusted template headings before inserting content. Do not overwrite user edits in these sections unless the user explicitly requests a refresh. For `completeness: incomplete`, store only available captured text and the incomplete reason; do not invent role fields. For `completeness: complete`, verify that `### Complete captured description` is populated after writing.

After every create, update, reopen, or Seen operation, read the application through `rtk obsidian read`, then query `rtk obsidian base:query path="Personal/Job Search/Job Applications.base" view="All jobs" format=json`. Verify the application path, identity fields, exact `job-title`, seniority `role`, canonical URL, and stage. When completeness is complete, also verify the complete captured description. Return the action, application path, matching method, and fields changed.
