---
name: linear-progress-issue
description: Progress a verified Linear issue through Backlog, Todo, In Progress, and Done, or cancel it when explicitly requested. Use when planning, starting, completing, or canceling repository work tied to a specific Linear issue.
---

# Linear Progress Issue

Keep the Linear state aligned with actual work progress.

## Workflow

1. Read `## Linear scope` from the applicable `AGENTS.md`; require the allowed team and stable project ID/slug.
2. Resolve one issue key from the user or a verified `linear-link-work` result. Retrieve the issue and verify its team and project before reading further or writing.
3. Retrieve the team's workflow states and use their exact names or IDs. Require `Backlog`, `Todo`, `In Progress`, `Done`, and `Canceled` to exist.
4. Select the transition supported by the current work state:
   - `Backlog` to `Todo` when the work is accepted, sufficiently understood, and ready to start;
   - `Todo` to `In Progress` immediately before substantive work begins;
   - `In Progress` to `Done` only after the requested outcome is complete and relevant verification passes;
   - any nonterminal state to `Canceled` only when the user explicitly requests cancellation of that issue.
5. Update only the issue state, then retrieve the issue and verify the resulting state, team, and project.
6. Report the issue key and confirmed state with the work progress or completion result.

## Rules

- Follow `Backlog` → `Todo` → `In Progress` → `Done` one transition at a time; never skip, reverse, or reopen a state unless the user explicitly authorizes the exact transition.
- Treat a request to work on a specific verified issue as authorization for forward transitions only when the corresponding lifecycle event actually occurs.
- Require separate explicit authorization for `Canceled`, even when cancellation appears reasonable from context.
- Make no state change for planning text, proposed work, failed verification, or an issue already in the correct state.
- Stop on missing scope, an unverified or mismatched issue, missing workflow states, or a state outside this workflow.
- Change no other issue fields and create no comments under this skill.
