---
name: linear-create-issue
description: Create one scoped Linear issue or subissue through a delegated subagent. Use when `linear-link-work` finds no matching issue or when the user explicitly requests a new issue for repository work.
---

# Linear Create Issue

Delegate the Linear write. The primary agent must not create the issue itself.

## Workflow

1. Read `## Linear scope` from the applicable `AGENTS.md`; require the allowed team and stable project ID/slug.
2. Treat invocation by the user or by `linear-link-work` after no match as authorization for exactly one create operation.
3. Delegate to one subagent with the request, repository path, and exact Linear scope. Stop if delegation is unavailable.
4. Require the subagent to:
   - inspect only the allowed Linear project for project context and a current duplicate;
   - inspect relevant code, docs, tests, and diff for repository context;
   - return an existing matching key if a duplicate appeared;
   - use a subissue only when a clear in-project parent exists; otherwise create a top-level issue;
   - create one issue in the allowed team and project with a concise title and a description covering context, intended outcome, and relevant paths or acceptance notes;
   - retrieve the result, verify its key, team, and project, and return them to the primary agent.
5. Verify the returned issue against the local scope and return its key to the caller.

## Rules

- Never read or write outside the allowed team and project.
- Stop on missing scope, mismatched verification, or a result without a project.
- Permit no other Linear writes; comments, updates, and status changes need separate authorization.
