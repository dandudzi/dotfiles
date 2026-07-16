---
name: linear-link-work
description: Link repository work to Linear. Use for substantive work when the applicable AGENTS.md contains a `## Linear scope` section, even if the user does not mention Linear.
---

# Linear Link Work

Before substantive work, bind it to a verified issue or subissue in the locally allowed Linear project.

## Workflow

1. Read `## Linear scope` from the applicable `AGENTS.md`; stop if the team or stable project ID/slug is missing.
2. If given an issue key, retrieve it and verify its team and project before reading further.
3. Otherwise, search using both the allowed team and project ID. Prefer a matching subissue over its parent.
4. Use one clear match. If several are plausible, ask the user to choose.
5. If none match, use `linear-create-issue` with the request and local scope. Stop if that skill is unavailable or returns no key; never create the issue here.
6. Verify the returned issue, state its key, then begin the work.

## Rules

- Stop on a missing or mismatched project or team; do not read further or write to that issue.
- Stay inside the local scope unless the user explicitly overrides it for an exact target.
- Keep this skill read-only. Other Linear writes require explicit authorization.
- Use one issue key per logical work unit.
- Prefix every requested commit with the key, for example `TEL-123: summary`; never commit without a verified key or without commit authorization.
- Report the issue key with the completed work, verification, and commit hash when applicable.
