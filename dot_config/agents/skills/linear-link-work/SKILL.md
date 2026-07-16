---
name: linear-link-work
description: Link substantive repository work to scoped Linear issues. Use for any implementation, fix, refactor, documentation change, investigation, or commit when the applicable AGENTS.md contains a `## Linear scope` section, even when the user does not mention Linear.
---

# Linear Link Work

Bind each substantive repository work item to a verified Linear issue or subissue before starting the work. Keep issue creation separate in the `linear-create-issue` skill.

## Read the local scope

1. Read the applicable `AGENTS.md` files and locate `## Linear scope`.
2. Require an allowed team and a stable allowed project ID or slug. Prefer IDs when both names and IDs are present.
3. Treat the declared team and project as a hard boundary for Linear reads and issue selection.
4. Stop and report missing or ambiguous scope instead of searching the whole workspace.
5. Cross the boundary only when the user explicitly overrides it for an exact team, project, or issue in the current request.

## Resolve the work item

Establish one active issue key before substantive work begins.

### When the user provides an issue key

1. Retrieve the issue using its identifier.
2. Verify its team and project against the local scope before reading comments or related context.
3. Stop and report the mismatch if the issue has no project, belongs to another project, or belongs to another team.
4. Use the issue only after both checks pass.

### When no issue key is provided

1. Search using the allowed project ID and allowed team on every query.
2. Compare candidates with the requested outcome and relevant repository area.
3. Prefer the most specific matching subissue over its parent issue.
4. Use a single clear match and state its key before continuing.
5. If several candidates are plausible, show the candidates and ask the user to choose.
6. If no suitable issue exists, use the `linear-create-issue` skill and pass it the current request and local Linear scope.
7. If `linear-create-issue` is unavailable or does not return an issue key, stop before implementation or committing. Do not create the issue directly from this skill.
8. Retrieve and scope-check the issue returned by `linear-create-issue` before using it.

## Keep Linear access scoped

- Always filter issue searches with the allowed project ID and team.
- Limit an initial out-of-scope identifier lookup to the fields needed to detect the mismatch.
- Never read comments, related issues, or other details after a scope mismatch.
- Never comment on or update an out-of-scope issue without an explicit exact override.
- Keep this skill read-only. Delegate missing-issue creation to `linear-create-issue`; require explicit authorization for every other Linear write.

## Bind the repository work

- State the active issue or subissue key before starting substantive work.
- Use one key for each logical work unit and resolve another key if the work separates into an independent unit.
- Use the most specific applicable subissue key.
- Prefix every requested commit subject with the active key, for example: `TEL-123: concise change summary`.
- Include the key in a created branch or pull-request title; prefer Linear's suggested branch name when available.
- Never create a commit without an active, scope-verified issue key.
- Do not create a commit unless the user otherwise authorized committing.

## Report the linkage

Report the active issue key, issue title, project, completed work, verification, and commit hash when a commit was created. Do not comment on the issue or change its status merely because local work finished.
