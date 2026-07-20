---
name: linear-progress-issue
description: Coordinate one `gpt-5.6-terra` subagent at medium reasoning effort to progress a linked Linear issue or subissue, manage evidenced scoped relations, and mark work Done only after its commits and verification land on `origin/master`. Use after `linear-link-work` when planning, starting, relating, completing, or canceling repository work.
---

# Linear Progress Issue

Keep Linear state and relations aligned with actual work. The primary agent decides when an event has occurred and delegates Linear writes to one `gpt-5.6-terra` subagent at medium reasoning effort.

## Setup

1. Read `## Linear scope` from the applicable `AGENTS.md`; require the allowed team and stable project ID/slug.
2. Accept one verified key plus the parent/child and relation snapshots from `linear-link-work`. If the user supplies an unverified key, run `linear-link-work` first; never discover, select, or create an issue here.
3. Delegate state and relation management to exactly one `gpt-5.6-terra` subagent with medium reasoning effort. Give it the key, repository path, exact scope, snapshots, intended writes, evidence, and the IDs of relations the agent created during this active work. Reuse that subagent for later writes during the same active work when possible.
4. Require the subagent to verify the issue, parent, children, and every relation target against the allowed team and project before reading further or writing. Stop and request an exact scope override for an external target.
5. Retrieve the team's workflow states and require exact `Backlog`, `Todo`, `In Progress`, `Done`, and `Canceled` names or IDs. Re-fetch affected issues and relations after every write to detect automation.

## State Progression

- Move `Backlog` to `Todo` when work is accepted, sufficiently understood, and ready to start. After an approved split is verified, move the parent to `Todo`.
- Move `Todo` to `In Progress` immediately before substantive work begins. When any required child starts, also move a nonterminal parent to `In Progress`, one valid transition at a time.
- Keep an actively blocked issue in `Todo` before implementation or `In Progress` if implementation already began.
- Move `In Progress` to `Done` only after the completion contract below is proven.
- Move a nonterminal issue to `Canceled` only when the user explicitly requests cancellation of that exact issue.
- Follow `Backlog` → `Todo` → `In Progress` → `Done` one transition at a time. Never skip, reverse, reopen, cancel, or newly mark Duplicate without the required explicit authorization.

## Completion Contract

Before requesting `Done`, require the primary agent and delegate to verify all of the following:

1. Refresh the literal authoritative branch with `rtk git fetch origin master`. Stop if `origin/master` is unavailable or cannot be refreshed; keep the issue `In Progress`.
2. Identify every commit belonging to the active issue from its required Linear key and recorded work context. Account for direct commits, merge commits, and squash results; do not rely on message search alone when the recorded branch, PR, or worktree shows additional commits.
3. Prove every required commit, merge commit, or squash result is reachable from the refreshed `origin/master`, using ancestry checks against the exact landed identities. For a squash, require the landed commit or linked merged PR to identify the key unambiguously.
4. Confirm no issue-related changes remain uncommitted in a recorded worktree, reachable only from an unmerged local or remote branch, or attached to an open PR. Work present only locally, on a feature branch, or in an open PR is not Done.
5. Verify the landed code satisfies every acceptance criterion. Run the relevant tests, builds, linters, or checks against the landed revision, preferably in a clean checkout or isolated worktree pinned to refreshed `origin/master`; record the commands and results.
6. Re-fetch relations and confirm there is no active `blockedBy` target. An active blocker prevents `Done` even if the code landed.

If any commit identity, landing, clean-work state, acceptance criterion, landed-revision check, PR state, or blocker status cannot be proven, make no transition and keep the issue `In Progress`.

For a parent issue, additionally require every implementation outcome to belong to a child, every non-canceled required child to be `Done`, every canceled child to have explicit cancellation approval, and every child's associated commits to satisfy the same `origin/master` contract. Run the parent's aggregate acceptance criteria against the landed revision. Only then move the parent to `Done`.

## Relation Management

- Treat a blocker as active until its target is re-fetched in `Done` or explicitly `Canceled`.
- Automatically add an evidenced `blockedBy`, `blocks`, or `relatedTo` relation when both endpoints are in the allowed team and project. Create the correct blocking direction and re-fetch both endpoints to verify it.
- Treat `relatedTo` as context only; it never blocks starting or completing work.
- Prevent `Done` while an active `blockedBy` relation remains.
- When a blocking issue lands and reaches `Done`, re-fetch affected relations and report downstream issues that are now unblocked. Do not start or transition them automatically.
- Follow an existing in-scope `duplicateOf` relation to its canonical issue after `linear-link-work` validates the scope. Require user approval before writing a newly discovered duplicate relation or Duplicate transition.
- Automatically remove only a relation whose ID was recorded as agent-created during the same active work and is subsequently proven incorrect. Require user approval before removing any pre-existing or user-created relation.
- Change no relation that points outside the allowed team or project without an exact user scope override.

## Delegated Write Contract

Require the subagent to retrieve and verify the current issue and relevant relations, validate the requested transition or relation change and its evidence, perform only the authorized writes, retrieve the result, and return confirmed keys, team, project, states, relation direction, and relation IDs. The primary agent verifies the returned result against local scope and reports it with the work evidence.

## Rules

- The primary agent must not perform Linear writes itself; stop if the required delegation is unavailable.
- Use only one subagent for this workflow, with model `gpt-5.6-terra` and reasoning effort `medium`.
- Treat work on a verified issue as authorization only for forward transitions whose lifecycle events actually occur and for evidenced in-scope blocking or related relations.
- Make no state change for planning text, proposed work, failed landing or verification, or an issue already in the correct state.
- Require the active issue or child key in every commit message. For a squash merge, require the resulting commit or linked merged PR to identify the key unambiguously.
- Stop on missing scope, an unverified or mismatched issue, missing workflow states, or a state outside this workflow.
- Defer issue discovery and creation to `linear-link-work` and `linear-create-issue`. Create no comments and change no unrelated fields.
