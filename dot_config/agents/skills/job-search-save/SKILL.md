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

1. Invoke `job-posting-parse` with the URL or pasted text. Require its structured posting packet. If company or exact job title is absent, ask only for those missing facts and stop before storage.
2. Invoke `job-company-verification` before any tracker mutation. Pass only the company, captured posting, public URLs, and recruiter identity/contact domain supplied with the job. Require its structured verification packet. This phase is passive: never submit an application, contact anyone, log in, upload a CV, download attachments, or disclose personal data.
3. Invoke `job-application-upsert` with the posting packet. It must duplicate-check, then create, update, reopen, or record `Seen` as appropriate. Default a new saved role to `Wishlist`; use `Seen` only when the user explicitly asks to mark it seen. Saving a local tracker record does not authorize contact, application submission, or data disclosure.
4. If the upsert action or resulting stage is `Seen`, skip company research, CV fit, and interview research. Continue only with a present-only recommendation phase when related opportunities are available, and report the verification assessment without writing research into the minimal Seen record.
5. If packet `completeness` is `incomplete`, retain the partial application record, invoke `job-company-research` only to store the verification packet and independently sourced company facts, and skip company role fields and `job-cv-fit`. Ask the user for the full pasted description, include `incomplete-reasons`, and mark the next action as rerun `job-posting-parse` followed by the skipped phases. Do not infer missing responsibilities or qualifications.
6. Otherwise invoke `job-company-research` with the company, exact job title, posting details relevant to public research, public context, and the verification packet. Never pass CV context to company research. Invoke `job-cv-fit` independently with only the application path, posting packet, and current CV context.
7. Determine the interview stage from the user's request or the application record. If neither identifies a stage, ask the user and mark interview research `skipped` until answered; do not silently broaden it to general research. Invoke `job-interview-research` with the company, exact job title, stage, and application path. Keep candidate questions separate from the application's questions to ask the interviewer.
8. Invoke `job-recommendations` with the packet's related opportunities and the original application identity. Present recommendations only.

Do not let a verification, research, CV, interview, or recommendation failure undo a successful upsert. If verification fails, label it `inconclusive`, explain why, and continue only with local tracker work; never imply the job is safe. If verification returns `high-risk`, prominently recommend no engagement or data sharing and require explicit user direction before any future action beyond passive research and local recordkeeping. If parsing fails, do not create a speculative application. If upsert fails, collect non-mutating research only when it remains useful; otherwise stop dependent writes.

## Completion report

Return the application path and a compact phase table: parse, company verification, duplicate/upsert, company research, CV fit, interview research, and recommendations. Mark each phase `complete`, `skipped`, or `failed`, include the failure reason, and state the next resumable skill and input. Report the verification assessment, confidence, decisive red flags, data-sharing guidance, and limitations even when other enrichment is skipped. For incomplete packets, identify the request for a full pasted description; for Seen records, identify enrichment as intentionally skipped. Identify whether the record was created, updated, reopened, or marked Seen.
