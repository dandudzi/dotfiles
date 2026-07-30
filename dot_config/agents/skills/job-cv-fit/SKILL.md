---
name: job-cv-fit
description: Compare the user's current CV with a captured job posting, score fit, identify hard versus presentation gaps, and update only the CV fit section of an Obsidian job-application note. Use for CV-match, application-readiness, and tailored-CV requests.
---

# Job CV Fit

## Inputs and boundaries

Require an exact application-note path and a complete captured posting. Read the CV at the exact vault-relative path `Personal/Job Search/Attachments/CV_Dudziak_Daniel.pdf`; extract its full text before analysing. If the CV or a complete posting is unavailable, stop and state the missing input.

Read [the scoring methodology](references/cv-comparison-instructions.md) and [the output template](references/cv-comparison-template.md) before drafting. Use exact CV and posting language whenever the analysis quotes or rewrites it. Do not claim experience not supported by the CV.

Patch only `## CV fit` in the application note. Do not change frontmatter, the posting, company research, interview research, notes, or question bank.

## Analyse

1. Catalogue the posting's required and preferred qualifications, responsibilities, technologies, seniority, domain, and implicit expectations.
2. Catalogue the CV's skills, evidence, scope, outcomes, domains, and seniority signals.
3. Complete every section of the output template. Keep hard gaps separate from presentation gaps, give numeric scores, and preserve the defined scoring weights.
4. Offer only 3–6 high-impact bullet rewrites. Quote the original CV bullet and state a concrete replacement that is truthful and tailored to the posting.
5. Include no invented red flags or interview questions. Write `*None identified.*` where the evidence supports none.

## Update and verify

1. Inspect the note immediately before writing. Replace only the content after `## CV fit` up to the next heading at the same or higher level, retaining that heading.
2. Apply a focused Markdown patch. Do not rewrite the full note.
3. Read the note through Obsidian CLI, for example `rtk obsidian read path="Personal/Job Search/Applications/<note>.md"`.
4. Confirm the CV-fit section follows the output template, has no unresolved placeholders, and leaves adjacent sections unchanged. Treat CLI output containing `Error:` as a failed verification.

Report the score, meaningful hard gaps, presentation gaps, and updated note path.
