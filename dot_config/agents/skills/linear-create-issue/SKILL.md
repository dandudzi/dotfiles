---
name: linear-create-issue
description: Create one scoped Linear backlog issue or subissue with a Bug, Improvement, or Feature label, an explicit priority, and the project lead assigned, through a delegated subagent. Use when `linear-link-work` finds no matching issue or when the user explicitly requests a new issue for repository work.
---

# Linear Create Issue

Delegate the Linear write. The primary agent must not create the issue itself.

## Workflow

1. Read `## Linear scope` from the applicable `AGENTS.md`; require the allowed team and stable project ID/slug.
2. Treat invocation by the user or by `linear-link-work` after no match as authorization for exactly one create operation.
3. Delegate to one subagent with the request, repository path, and exact Linear scope. Stop if delegation is unavailable.
4. Require the subagent to:
   - inspect only the allowed Linear project for project context, its current lead, and a current duplicate;
   - stop if the project has no lead;
   - inspect relevant code, docs, tests, and diff for repository context;
   - return an existing matching key if a duplicate appeared;
   - use a subissue only when a clear in-project parent exists; otherwise create a top-level issue;
   - choose exactly one existing team label: Bug for broken or regressed behavior, Feature for a new capability, or Improvement for an enhancement to existing behavior; default to Improvement when no category clearly dominates, and stop rather than create a missing label;
   - choose and explicitly set the priority from evidence in the request and repository context: Urgent for active critical incidents, High for time-sensitive blockers, Medium for normal planned work, or Low for optional cleanup; default to Medium when no stronger signal exists;
   - create one issue in the allowed team and project, set the chosen label and priority, set its state to `Backlog`, assign the project lead as its issue assignee, and use a concise title plus a description covering context, intended outcome, and relevant paths or acceptance notes;
   - retrieve the result, verify its key, team, project, label, `Backlog` state, priority, and assignee, and return them to the primary agent.
5. Verify the returned issue against the local scope and return its key to the caller.

## Rules

- Never read or write outside the allowed team and project.
- Stop on missing scope, a project without a lead, an unavailable classification label, mismatched verification, or a result without a project.
- Permit no other Linear writes; comments, updates, and status changes need separate authorization.
