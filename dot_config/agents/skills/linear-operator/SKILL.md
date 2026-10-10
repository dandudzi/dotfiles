---
name: linear-operator
description: Perform approved, scoped Linear issue creation, workflow transitions, and relation mutations with read-back verification. Use for writes authorized by linear-create-issue or linear-progress-issue, or an explicit user request; not for general issue discovery.
---

# Linear Operator

Execute the authorized Linear operation directly in the current agent using this skill. No custom agent or delegation is required. Keep the authorization and verification boundaries of the former operator.

- When the user asks to start planning or work on a specific issue from an issue tracker such as Linear or Jira, claim it before planning: create or reuse its dedicated worktree, move and verify the issue in `In Progress`, then verify the agent's current directory is that worktree. Only after this claim gate may an agent create a plan, state file, test, source file, or other work artifact. Read-only issue and repository discovery may occur before the gate. Ask for approval of the implementation plan before implementation begins.

## Connection

Use the `linear_operator` MCP server for operator reads and writes. It uses `LINEAR_OPERATOR_ACCESS_TOKEN` to attribute actions to the Linear app identity. The Codex shell launcher loads that variable from the existing macOS Keychain item; never print, copy, or commit the token. A skill cannot inject per-agent MCP settings, so this connection is configured in `~/.codex/config.toml`.

Stop if the operator connection or required tools are unavailable. Do not silently switch a write to the separate `linear` OAuth connection. After changing the server configuration or replacing the token, start a new Codex process to load the connection and environment. For an authentication failure, use `refresh-agent-auth`.

## Operation Contract

- Require the exact allowed team and stable project ID or slug, repository path when relevant, verified issue keys or approved creation proposal, intended writes, approval record, and supporting evidence. For relations, include the exact endpoints, direction, and IDs of any relations created during this active work.
- Verify every issue, parent, child, duplicate, and relation endpoint against the allowed team and project before reading further or writing. Stop on a mismatch; an external target requires an exact user scope override.
- Use `linear-create-issue` for the approved creation proposal, classification, priority, assignee, Backlog state, parent linkage, and initial relations. Use `linear-progress-issue` for allowed state transitions, relation management, and completion evidence. Do not invoke this skill to infer approval missing from either workflow.
- Immediately before each mutation, re-fetch the affected issue and relevant relations, verify the current scope and state, and check the authorized write against current evidence. Earlier snapshots are discovery context, not write authorization.
- Perform only the requested issue creation, state transition, or relation mutation. Create no comments and change no unrelated fields. Cancellation, a new duplicate relation or Duplicate transition, and removal of a pre-existing or user-created relation require the authorization defined by the invoking workflow.
- While executing the Linear operation, do not edit source files, create commits, merge branches, or open or close pull requests. Use repository evidence supplied by the coding workflow and inspect it read-only when verification requires it.
- Before `Done`, enforce every completion condition in `linear-progress-issue`: refreshed authoritative origin branch, exact landed commit identities, no outstanding issue work or open PR, passing acceptance checks on the landed revision, and no active blocker. Do not assume `main` or `master`. For parents, also verify all required children and aggregate acceptance criteria. If proof is incomplete, make no completion transition and keep the issue `In Progress`.
- After each write, retrieve the issue and affected relation endpoints again. Verify the requested result and any automation before making another transition. Do not blindly retry a failed or ambiguous mutation; read current state first to prevent duplicate issues, relations, or transitions.

Return confirmed issue keys, team, project, states, parent linkage, relation direction and IDs, exact writes, verification evidence, and unresolved blockers. Record IDs of relations created during this active work so later correction follows the invoking workflow's ownership rules.
