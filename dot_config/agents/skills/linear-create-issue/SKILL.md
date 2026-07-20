---
name: linear-create-issue
description: Create one scoped Linear backlog issue or an approved parent/subissue batch, plus approved initial relations, through one delegated `gpt-5.6-terra` subagent at medium reasoning effort. Use when `linear-link-work` finds no matching issue, the user requests a new repository issue, or the user approves a proposed issue decomposition.
---

# Linear Create Issue

Delegate the Linear writes. The primary agent must not create issues or relations itself.

## Workflow

1. Read `## Linear scope` from the applicable `AGENTS.md`; require the allowed team and stable project ID/slug.
2. Choose one authorized mode:
   - create one issue when invoked by the user or by `linear-link-work` after no match;
   - create a parent/subissue batch only after the user approves the complete decomposition proposal from `linear-link-work`.
3. For a decomposition, require the approved proposal to list every child's title, outcome, acceptance criteria, one existing classification label, explicit priority, dependency order, and expected Git deliverable. Include a new parent only if the approved proposal explicitly contains it. Require another proposal and approval before creating grandchildren.
4. Delegate the entire authorized create operation to exactly one `gpt-5.6-terra` subagent with medium reasoning effort. Give it the request, repository path, exact Linear scope, approval record, and proposed structure and relations. Stop if delegation with that model and effort is unavailable.
5. Require the subagent to inspect only the allowed project for project context, its current lead, current duplicates, the proposed parent, and proposed relation targets; stop if the project has no lead or any target is out of scope.
6. Require the subagent to inspect relevant repository code, docs, tests, and diff. Return an existing matching key instead of creating a duplicate. A newly discovered duplicate relation still requires user approval before it is written.
7. For every created issue or child:
   - use the allowed team and project, set `parentId` for a child, set state to `Backlog`, and assign the project lead;
   - set the proposal's explicit priority;
   - apply exactly one existing team classification label: Bug, Feature, Improvement, or Tech Debt; never create a missing label;
   - use a concise title and a description containing context, intended outcome, acceptance criteria, relevant paths, dependency order, and expected Git deliverable.
8. Create only approved, evidenced initial `blockedBy`, `blocks`, or `relatedTo` relations among in-scope issues. Use the direction in the proposal, treat `relatedTo` as context only, and record each relation ID as agent-created during this active work.
9. Retrieve the parent, every child, and both endpoints of each created relation. Verify keys, team, project, parent linkage, labels, `Backlog` state, priorities, assignee, relation direction, and relation IDs. Detect and report any parent/subissue automation.
10. Return the verified structure and relation snapshot to `linear-link-work`; let `linear-progress-issue` move the parent to `Todo` after all children are verified and later to `In Progress` when any required child starts.

## Classification and Priority

- Use Bug for broken or regressed behavior, Feature for a new capability, Improvement for an enhancement, and Tech Debt for internal remediation that does not primarily change user-facing behavior. Reuse the parent's label when it accurately classifies the child; otherwise use the explicitly approved label. Default a single new issue to Improvement only when no category dominates.
- Use Urgent for active critical incidents, High for time-sensitive blockers, Medium for normal planned work, and Low for optional cleanup. Default a single new issue to Medium when no stronger signal exists.

## Rules

- Never read or write outside the allowed team and project. Stop and request an exact scope override when a parent, child, duplicate, or relation target falls outside it.
- Use only one subagent for the workflow, with model `gpt-5.6-terra` and reasoning effort `medium`.
- Treat approval of a decomposition as authorization only for the exact proposed batch and its listed initial relations. Rejected or partially approved proposals create nothing until a complete replacement proposal is approved.
- After splitting, put all implementation work on children. Create another approved child for any remaining parent-level implementation.
- Stop on missing scope, missing project lead, unavailable classification label, mismatched verification, or a result without a project.
- Permit no writes beyond the authorized issues and initial relations. Delegate later state and relation changes to `linear-progress-issue`; comments and other field changes need separate authorization.
