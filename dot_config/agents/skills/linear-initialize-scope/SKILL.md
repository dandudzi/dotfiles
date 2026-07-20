---
name: linear-initialize-scope
description: Connect a repository to an existing Linear project by discovering projects through the Linear MCP server, verifying the selected team and project, and adding a confirmed `## Linear scope` section to the repository-root `AGENTS.md`. Use when the user asks to initialize, configure, enable, or connect Linear issue tracking for a repository.
---

# Linear Initialize Scope

Connect one repository to a verified Linear team and project without changing Linear itself.

## Workflow

1. Resolve the repository root. Require an existing `AGENTS.md` at that root; stop rather than create one or edit a nested file.
2. Require Linear MCP read operations for listing and retrieving projects and teams, plus listing issue statuses and labels. Call the project-list operation with archived projects excluded to verify availability and authentication. If the server, tools, or authentication are unavailable, stop without editing and give concise setup guidance; do not accept unverified manual identifiers.
3. Page through all visible non-archived projects. Show compact choices with each project's name, state, team or teams, and stable identifier. If the result is too large for a useful choice, ask for search text and show the matching projects. Always ask which project to connect; never infer it from the repository name.
4. Retrieve the selected project. Use its only team when exactly one is attached; ask the user to choose when several are attached; stop when none is attached.
5. Retrieve the selected team and verify that the project belongs to it. Capture the current team name and UUID, project name and UUID, and project lead. Stop if the IDs are missing, the relationship does not match, or the project has no lead.
6. Verify that the team has workflow states named exactly `Backlog`, `Todo`, `In Progress`, `Done`, and `Canceled`, and labels named exactly `Bug`, `Feature`, `Improvement`, and `Tech Debt`. Stop and report every missing prerequisite without creating or changing Linear data.
7. Inspect any existing `## Linear scope` section. Treat UUIDs as authoritative:
   - If UUIDs and names match, report that the repository is already connected and make no edit.
   - If UUIDs match but names differ, show the name refresh and require confirmation.
   - If UUIDs differ or valid UUIDs are absent, show the existing and proposed scopes and require explicit replacement confirmation.
8. Preview the exact Markdown below and require final confirmation separate from project selection before editing:

   ```markdown
   ## Linear scope

   - Team: `<team name>` (`<team UUID>`)
   - Project: `<project name>` (`<project UUID>`)
   ```

9. Add the section at the end of the root `AGENTS.md`, or replace only the existing `## Linear scope` section after the required confirmation. Preserve all unrelated content and formatting.
10. Read the result back and report the repository path, selected team, selected project, and whether the section was added, refreshed, replaced, or already current.

## Guardrails

- Treat invocation as authorization for read-only Linear discovery only.
- Write only the confirmed repository-root `AGENTS.md` section.
- Never configure the MCP server, create or mutate Linear data, choose a project without the user, or continue after failed verification.
