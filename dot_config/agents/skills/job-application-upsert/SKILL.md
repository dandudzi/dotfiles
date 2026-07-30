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
- Populate `application-key`, `source-job-id`, and `posting-status` from the posting packet when known.

## Resolve identity before writing

Inspect candidate records through the Base and their application notes. Compare in this strict priority:

1. Exact **source job ID**.
2. Exact normalized **canonical job URL**.
3. Exact **company + exact job title + location**.
4. A fuzzy company/title comparison only as a possible match. Never merge, reopen, or replace a fuzzy match without user **confirmation**.

Use `source-job-id` or the normalized canonical URL as `application-key`; otherwise derive a stable key from normalized company, exact job title, and location. Do not use a company name alone as a duplicate.

## Choose the action

- For an exact match, update only newly captured or explicitly requested fields and preserve user-written notes, interview notes, and stage unless the user asks to change them.
- For an exact record in a terminal stage, offer reopen; reopen only with the user's confirmation and preserve the prior outcome in the note.
- For an explicit Seen request, create or update a minimal record with `stage: Seen`. Populate identity, company, job-title, location, job-link, found-via, date-found, and posting-status when available; do not add research, CV fit, or question-bank content.
- For no match, create a note from the template with `stage: Wishlist` unless the user supplies another stage.
- For a fuzzy candidate, return its path and differences, request confirmation, and make no mutation.

## Write and verify

Read the exact template or existing note immediately before changing it. Use `rtk obsidian property:set` with typed values for frontmatter, then use a focused Markdown patch only for the relevant body section. Never rewrite the whole template or unknown frontmatter.

After every create, update, reopen, or Seen operation, read the application through `rtk obsidian read`, then query `rtk obsidian base:query path="Personal/Job Search/Job Applications.base" view="All jobs" format=json`. Verify the application path, identity fields, exact `job-title`, seniority `role`, and stage. Return the action, application path, matching method, and fields changed.
