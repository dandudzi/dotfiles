---
name: linear-progress-issue
description: Coordinate one `gpt-5.6-terra` subagent at medium reasoning effort to progress an issue previously verified by `linear-link-work` through Backlog, Todo, In Progress, and Done, or cancel it when explicitly requested. Use after linking when planning, starting, completing, or canceling repository work.
---

# Linear Progress Issue

Keep the Linear state aligned with actual work progress. The primary agent decides when a lifecycle event has occurred and delegates Linear state management to one `gpt-5.6-terra` subagent at medium reasoning effort.

## Workflow

1. Read `## Linear scope` from the applicable `AGENTS.md`; require the allowed team and stable project ID/slug.
2. Accept one verified issue key from `linear-link-work`. If the user supplies an unverified key, run `linear-link-work` first; never search for, select, or create an issue here. Select the transition supported by the current work state:
   - `Backlog` to `Todo` when the work is accepted, sufficiently understood, and ready to start;
   - `Todo` to `In Progress` immediately before substantive work begins;
   - `In Progress` to `Done` only after the requested outcome is complete and relevant verification passes;
   - any nonterminal state to `Canceled` only when the user explicitly requests cancellation of that issue.
3. Delegate state management to exactly one `gpt-5.6-terra` subagent with medium reasoning effort. Give it the issue key, repository path, exact Linear scope, intended state, and evidence supporting the transition. Reuse that subagent for later transitions during the same active work when possible.
4. Require the subagent to retrieve the issue and verify its team and project before reading further or writing; retrieve the team's workflow states and require the exact `Backlog`, `Todo`, `In Progress`, `Done`, and `Canceled` names or IDs; verify the requested transition from the current state; update only the issue state; retrieve the result; and return the confirmed issue key, team, project, and state.
5. Verify the returned result against the local scope and report the issue key and confirmed state with the work progress or completion result.

## Rules

- Follow `Backlog` → `Todo` → `In Progress` → `Done` one transition at a time; never skip, reverse, or reopen a state unless the user explicitly authorizes the exact transition.
- The primary agent must not perform the Linear state write itself; stop if subagent delegation is unavailable.
- Use only one subagent for this workflow, with model `gpt-5.6-terra` and reasoning effort `medium`.
- Treat a request to work on an issue verified by `linear-link-work` as authorization for forward transitions only when the corresponding lifecycle event actually occurs.
- Require separate explicit authorization for `Canceled`, even when cancellation appears reasonable from context.
- Make no state change for planning text, proposed work, failed verification, or an issue already in the correct state.
- Stop on missing scope, an unverified or mismatched issue, missing workflow states, or a state outside this workflow.
- Defer all issue discovery, selection, and creation to `linear-link-work`.
- Change no other issue fields and create no comments under this skill.
