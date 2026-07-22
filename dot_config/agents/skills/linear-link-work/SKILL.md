---
name: linear-link-work
description: Resolve and verify one Linear issue or subissue for repository work, inspect its scoped relations and decomposition needs, then hand its key and relation snapshot to `linear-progress-issue` before substantive work begins. Use for substantive work when the applicable AGENTS.md contains a `## Linear scope` section, even if the user does not mention Linear.
---

# Linear Link Work

Before substantive work, bind it to a verified issue or subissue in the locally allowed Linear project.

## Workflow

1. Read `## Linear scope` from the applicable `AGENTS.md`; stop if the team or stable project ID/slug is missing.
2. If given an issue key, retrieve it and verify its team and project before reading further. Otherwise, delegate discovery to a read-only subagent with the work request and allowed team and project ID. Require the subagent to search within both constraints, verify its selection, and retrieve the relation data defined in step 5. Keep raw search results in the subagent context; return only the selected issue key, a concise rationale, the verified team and project, and the relevant parent/child and relation snapshots.
3. Use one clear match. Prefer an existing subissue whose outcome matches the work over its parent. If several are plausible, ask the user to choose.
4. If no issue matches, invoke `linear-create-issue` with the request and local scope. Stop if that skill is unavailable or returns no verified key; never create the issue here.
5. For a supplied issue key, retrieve its `blockedBy`, `blocks`, `relatedTo`, `duplicateOf`, parent, and children relations. For delegated discovery, use the subagent's returned snapshots instead of repeating its search or retrieval in the primary context. Include relation IDs, target keys, target states, team, and project; stop and request an exact scope override before reading a related target outside the allowed team or project.
6. If an existing `duplicateOf` relation points to an in-scope canonical issue, validate that its scope covers the work and restart selection from that issue. Treat a suspected but unrecorded duplicate as a proposed relation requiring user approval through `linear-progress-issue`.
7. Detect a large issue when it contains multiple outcomes that can be implemented or verified independently. Before creating anything, propose the smallest useful decomposition. For every proposed subissue include its title, outcome, acceptance criteria, one existing classification label, explicit priority, dependency order, and expected Git deliverable.
8. Wait for approval of the complete decomposition. After approval, invoke `linear-create-issue` once for the approved batch. Require a new proposal and approval before any deeper nesting.
9. Re-fetch the parent and every child after creation and after state transitions to detect parent/subissue automation. Assign all implementation to children; if implementation remains at parent level, propose another child rather than implementing it on the parent.
10. State the active issue or subissue key and hand the verified key, parent/child snapshot, relation snapshot, repository path, and exact Linear scope to `linear-progress-issue`. Do not begin substantive work until that skill confirms the allowed starting state; after confirmation, use `coding-workflow` for every code change.

## Rules

- Keep this skill read-only. Delegate creation to `linear-create-issue` and all state or ongoing relation writes to `linear-progress-issue`.
- Stop on a missing or mismatched project or team. Stay inside the local scope unless the user explicitly overrides it for an exact target.
- Treat `relatedTo` as context only. Do not let it change selection, ordering, or completion.
- Keep an issue with an active blocker in `Todo` before implementation or `In Progress` if implementation already began; never advance it to `Done`.
- Use one issue key per logical work unit. After splitting, use the active child's key for commits and progress reporting, not the parent key.
- Require the active key in every commit message, for example `TEL-123: summary`. For a squash merge, require the resulting commit or linked merged PR to identify the key unambiguously.
- Report the active key with completed work, verification, and landed commit identity when applicable.
