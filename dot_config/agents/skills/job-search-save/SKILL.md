---
name: job-search-save
description: Save a job posting through the complete Obsidian job-search workflow. Use when a user provides a LinkedIn or company posting URL, pasted posting text, or asks to add, track, wishlist, research, or assess a role.
---

# Save a job posting

Coordinate the specialist skills. Preserve the user's application history and report progress that can be resumed.

## Vault contract

Use these exact vault-relative paths. Do not substitute an external tracker:

- `Personal/Job Search/Job Applications.base`
- `Personal/Job Search/Templates/Job Application.md`
- `Personal/Job Search/Applications`
- `Personal/Job Search/Interview Questions/Interview Questions.md`
- `Personal/Job Search/Templates/Interview Question.md`

## Workflow

1. Invoke `job-posting-parse` with the URL or pasted text. Require its structured posting packet; if it cannot establish a company and job title, ask only for those missing facts and stop before storage.
2. Invoke `job-application-upsert` with the packet. It must duplicate-check, then create, update, reopen, or record `Seen` as appropriate. Default a new saved role to `Wishlist`; use `Seen` only when the user explicitly asks to mark it seen.
3. After a canonical application note exists, invoke `job-company-research` and `job-cv-fit` independently. Pass the application path, posting packet, and current CV context to each.
4. Determine the interview stage from the user's request or the application record. If neither identifies a stage, ask the user and mark interview research `skipped` until answered; do not silently broaden it to general research. Invoke `job-interview-research` with the company, exact job title, stage, and application path. Keep candidate questions separate from the application's questions to ask the interviewer.
5. Invoke `job-recommendations` with the packet's related opportunities and the original application identity. Present recommendations only.

Do not let a research, CV, interview, or recommendation failure undo a successful upsert. If parsing fails, do not create a speculative application. If upsert fails, collect non-mutating research only when it remains useful; otherwise stop dependent writes.

## Completion report

Return the application path and a compact phase table: parse, duplicate/upsert, company research, CV fit, interview research, and recommendations. Mark each phase `complete`, `skipped`, or `failed`, include the failure reason, and state the next resumable skill and input. Identify whether the record was created, updated, reopened, or marked Seen.
