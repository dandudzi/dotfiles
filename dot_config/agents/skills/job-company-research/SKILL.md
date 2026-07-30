---
name: job-company-research
description: Research a company and the context for one job application using current, cited sources. Use when an Obsidian job-application note needs its Company & Role Research section completed or refreshed after a complete posting has been captured.
---

# Job Company Research

## Inputs and boundaries

Require an exact application-note path, company name, job title, and complete captured posting. Read the note and isolate the section headed `## Company & Role Research` (allow its existing decorative prefix only when locating it). Do not research or infer posting responsibilities or qualifications when the posting is absent or incomplete; report the missing input instead.

Treat the captured posting as the sole source of truth for role responsibilities and qualifications. Do not use company research to fill those fields. Do not change frontmatter, the job-posting section, CV fit, interview sections, question bank, or any other content.

## Research

Search current primary sources first: the company site, careers pages, investor relations or filings, reputable reporting, and official engineering or product publications. Use review platforms only for clearly labelled employee-sentiment data. For every material claim, retain a direct URL and publication or access date. Prefer recent evidence; label older evidence with its date rather than presenting it as current.

Produce concise, factual subsections:

- **Company overview** — business, product, market, location/scale or ownership only when sourced.
- **Culture and values** — separate stated values from independently reported employee sentiment.
- **Market and competitors** — position, differentiation, and named competitors with sources.
- **Current challenges** — material risks, changes, or uncertainty; do not manufacture concerns.
- **Role responsibilities** — extract only from the captured posting; quote or closely preserve its wording.
- **Required and preferred qualifications** — extract only from the captured posting and label the distinction.
- **Review signals** — include ratings only with their source and access date; otherwise say `Not found in reviewed sources`.
- **Sources and gaps** — list each source as a Markdown link and state evidence that could not be verified.

Use `Not found in reviewed sources` or `Limited public information` for gaps. Never invent facts, ratings, competitors, challenges, responsibilities, or qualifications.

## Update and verify

1. Inspect the application note immediately before writing. Replace only the content between the Company & Role Research heading and the next heading at the same or higher level. Preserve the heading and all surrounding content.
2. Make a focused Markdown patch; do not rewrite the note or use a broad search-and-replace.
3. Read the exact note through Obsidian CLI, for example `rtk obsidian read path="Personal/Job Search/Applications/<note>.md"`.
4. Confirm the research section contains the cited findings, posting-derived role fields, and explicit gaps, while adjacent sections are unchanged. Treat CLI output containing `Error:` as a failed verification.

Report the note path, source links, major unknowns, and whether the section was created or refreshed.
