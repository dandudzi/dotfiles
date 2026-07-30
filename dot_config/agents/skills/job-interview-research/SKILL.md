---
name: job-interview-research
description: Find sourced, candidate-reported interview questions for a company, role, seniority, and interview stage, then create or refresh the linked Obsidian preparation note. Use for stage-specific interview preparation after a job application has been captured.
---

# Job Interview Research

## Inputs and boundaries

Require an exact application-note path, company, job title, seniority when known, and one stage: `screening`, `technical`, `system-design`, `behavioural`, `take-home`, `final`, or `general`. Ask for the stage when it is absent; use `general` only when the user explicitly wants cross-stage research.

Read the application note and identify `## Company interview questions`. Distinguish this section from `## Questions to ask the interviewer`: this skill records questions companies ask candidates, reported by candidates, and must not alter the user's interviewer-question bank.

Use the template at `Personal/Job Search/Templates/Interview Question.md` to create or update one prep note under `Personal/Job Search/Interview Questions/`, named `Company — Role — Stage.md` with filesystem-safe title components. Preserve its frontmatter and template structure. Do not edit unrelated application-note sections.

## Research

Search candidate-reported evidence across company-specific Reddit threads, LeetCode Discuss, GeeksForGeeks, personal interview write-ups, public GitHub repositories, and other credible candidate-experience sources. Record the direct URL, source type, and post or publication date for each usable result. Include only questions explicitly reported by candidates; do not turn generic preparation advice into claimed questions.

Keep every question stage-specific:

- **Screening:** motivation, background, culture, logistics.
- **Technical:** coding, SQL, algorithms, language-specific exercises.
- **System design:** architecture, modelling, scale, trade-offs.
- **Behavioural:** experience and competency questions.
- **Take-home:** assignment format and evaluation evidence.
- **Final:** only evidence that sources attribute to late-stage interviews.

Discard evidence for another stage rather than padding the results. Search adjacent seniority levels separately and label them as adjacent evidence, never as the requested level. Split dated findings into recent (last 12 months) and older; identify undated evidence as undated.

## Write the prep note

Populate the template with the company, role, stage, date, candidate-reported questions, and a source audit. Include:

- **What to expect** — only sourced format, duration, or round information; state when evidence is thin.
- **Recent questions** and **older or undated questions** — preserve source attribution beside every question.
- **Adjacent-level evidence** — separate one level below and above when available.
- **Source audit** — every source class searched, its result (including no usable result), URLs used, and recency limits.
- **Gaps** — say `No candidate-reported questions found for this stage` when appropriate.

Do not add questions to ask the interviewer, generic study plans, fabricated GitHub resources, or unsourced company-process claims.

## Link and verify

1. Inspect the application note and any existing prep note before writing. Create the prep note with Obsidian CLI from the interview-question template when absent; otherwise make a focused update to its generated research content.
2. Replace only the body of `## Company interview questions` with an embed or link to the prep note, for example `![[Personal/Job Search/Interview Questions/Company — Role — Stage]]`. Do not modify `## Questions to ask the interviewer`.
3. Read both exact paths through Obsidian CLI. Confirm the prep note preserves template metadata, every included question has a direct source, the source audit and recency labels are present, and the application note points to the expected prep note.
4. Treat CLI output containing `Error:` as failure and report it without claiming completion.

Report the application note, prep-note path, stage, source count, recency limits, and evidence gaps.
