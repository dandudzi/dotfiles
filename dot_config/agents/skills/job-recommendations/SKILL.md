---
name: job-recommendations
description: Present related job opportunities from a parsed posting packet without adding them to the Obsidian tracker. Use after a posting parse or when a user asks to review similar roles.
---

# Present related jobs

Accept `related-opportunities` from a posting packet and the original job identity. If none are available, say so without searching or creating records.

## Screen recommendations

Deduplicate the supplied opportunities by source job ID, canonical job URL, then company + exact title + location. For each remaining opportunity, use the read-only duplicate contract from `job-application-upsert`: query `Personal/Job Search/Job Applications.base`, then classify it as `new`, `exact match`, or `possible fuzzy match`. Do not treat a company match alone as a duplicate.

Rank by the original posting's seniority, location, work type, and technology overlap. Show at most ten unless the user asks for all. Include company, exact job title, location, source URL, and duplicate classification; show the existing stage and application path for exact matches where available.

## Present only

Do **not automatically** create tracker records, mutate an application, invoke `job-application-upsert` in write mode, or recurse into another recommendation search. Ask the user to select specific opportunities if they want to process them. Only then may a later `job-search-save` run parse the selected posting as a new, separate request.
