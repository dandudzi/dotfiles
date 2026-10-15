---
name: setup-issue-tracker
description: Set up or update a repository-local .issue-tracker-connection with verified tracker access, team and project identifiers, acting identity, repository scope, and operating rules. Use when asked to connect a repository to an issue tracker.
---

# Setup Issue Tracker

Create a non-secret YAML file named `.issue-tracker-connection` at the repository root. It describes how agents access the tracker and which issues belong to this repository; it does not configure authentication or grant tracker mutation permissions.

## Discover and verify

1. Resolve the repository root and read its applicable instructions, especially existing tracker scope. Inspect any existing connection file before proposing changes. Do not copy configuration from another repository merely because it shares a product or project name.
2. Identify the tracker and an available access skill or MCP integration. Read the selected skill before using it. Discover the actual available MCP tool names rather than inventing them. A skill reference must identify an installed skill; a tool reference must identify a callable tool.
3. Use read-only tracker operations to verify authentication, team/workspace, project, labels, workflow states, and any configured acting identity. Reuse repository settings as candidates, but verify stable IDs and project/team membership. If access is unavailable, stop before writing and explain what connection setup is missing. Never read or persist tokens, cookies, passwords, or OAuth state in this file.
4. If the repository already unambiguously identifies its project and team, verify and reuse them. Otherwise ask the user to select from verified choices. Do not infer a project from the repository name. Ask only about unresolved scope or identity choices that affect the connection.
5. Distinguish the authenticated principal from an issue assignee or agent delegate. Verify the current principal through the integration's identity operation when available; otherwise record it as null and disclose that it could not be verified. Never assume `Telaweft Codex` is the authenticated user merely because it is the configured delegate.

## Connection format

Use YAML with `schema_version: 1`. Keep names for readability and stable IDs for disambiguation. Omit optional fields that do not apply; use null only for a known but unresolved value, explaining it to the user. Never claim an unavailable capability was verified.

The following is a shape example based on the Zakupki frontend repository's settings. Values remain candidates until verified for the target repository. Replace the access mapping with actual installed skills and discovered tools when writing the file.

```yaml
# Repository scope and access instructions; credentials live in the integration.
schema_version: 1
tracker:
  name: Linear
access:
  read:
    kind: mcp
    server: linear
    tools: {} # Map purposes to exact discovered tool names before saving.
  write:
    kind: skill
    name: linear-operator
principal:
  name: null
  id: null
team:
  name: Telaweft
  id: a3e2b46a-3b0d-4e42-8081-6d688ac6dd4c
project:
  name: Zakupki
  id: 3f06c1b9-7ace-4721-a57a-7166b070943b
scope:
  repository: dandudzi/zakupki
  include_labels: [Frontend]
  exclude_labels: ["Integration & Deploy"]
  required_labels: [Frontend]
  recommendation_exclusions:
    - issue: TEL-12
      unless: User explicitly requests low-priority asset or housekeeping work.
assignment:
  agent_delegate:
    name: Telaweft Codex
    id: null # Resolve through the tracker; do not substitute a human assignee.
principles:
  - Limit discovery and work to this repository's configured scope.
  - Read current issue details and relations before acting.
  - Search for an existing matching issue before proposing creation.
  - Follow repository instructions and the selected write skill for mutations.
  - Agent-delegate assignment is distinct from human ownership.
verification:
  checked_at: null # Set to the actual UTC verification timestamp.
  source: AGENTS.md, Linear read operations
```

For `access.read` and `access.write`, support either `kind: skill` with `name`, or `kind: mcp` with `server` and a `tools` mapping from purposes to exact tool names. Useful read purposes include `current_principal`, `list_projects`, `get_project`, `get_team`, `get_issue`, `search_issues`, `list_labels`, and `list_states`; include only supported operations. Record a verified workspace name/ID or project URL when the tracker exposes one and it helps distinguish accounts or projects.

Add `workflow` state names and IDs only when the repository's process requires them and they have been verified. Preserve tracker-specific distinctions such as assignee versus delegate, and include readiness or dependency rules only when supported by repository instructions. Do not impose Zakupki labels, identities, exclusions, or workflow states on other repositories. Record standing authorizations only when explicitly present in applicable instructions, with their source and exact scope; this file cannot create new authorization.

## Write and check

1. Build the complete proposed file from verified values. If existing connection values conflict with repository instructions or tracker data, explain the conflict and resolve it with the user before replacing them. Preserve unrelated settings; do not silently migrate or remove an existing format.
2. Write only the repository-root `.issue-tracker-connection` requested by the user. Do not edit `AGENTS.md`, other skills, MCP configuration, or tracker records. Setting up this file does not create an issue, assign a delegate, or transition workflow state. Do not commit or push unless separately authorized by the user or applicable instructions.
3. Parse the saved file as YAML using an available parser, check required fields (`schema_version`, `tracker`, `access.read`, `team`, `project`, `scope`, and `principles`), and read it back. Verify that references resolve to available skills/tools and that IDs and scope match the read-only discovery. For trackers without teams, omit `team` and record their equivalent workspace/container when applicable.
4. Report the file path, tracker, project, repository scope, access method, and any unverified optional fields. Explain that consuming skills must explicitly read this file; creating it does not automatically change their behavior.
