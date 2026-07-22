---
name: coding-workflow
description: Orchestrate repository code changes through an adaptive, test-first workflow. Use when implementing features, fixing bugs, refactoring, or otherwise changing executable behavior; scale from a compact single-agent loop for small changes to an isolated, plan-approved multi-agent workflow for substantive, risky, cross-cutting, long-running, or explicitly delegated work. Do not use for read-only explanation, diagnosis, research, or review.
---

# Coding Workflow

Own the outcome as the main agent. Scale coordination to the task; use subagents only when bounded delegation materially improves confidence or speed.

## Select a Path

- Use the compact path for small, low-risk changes within one ownership area that can be verified directly.
- Use the orchestrated path for substantive, risky, cross-cutting, long-running, or explicitly delegated work.
- If uncertain, explore read-only and choose before editing.

## Agent Roster

- On Codex, use `gpt-5.6-terra` for every subagent. Use medium effort for `explorer`, `verifier`, `linear-operator`, and unnamed fallback work; use high effort for test design, implementation, and judgment-heavy review.
- Use `explorer` for read-only discovery, `test-writer` for acceptance tests, one or more `implementer` agents for disjoint production assignments, and `verifier` for read-only checks.
- Always use `correctness-reviewer` on the integrated orchestrated change. Add `security-reviewer` for trust boundaries, authorization, validation, secrets, data exposure, or dependency risk; add `performance-reviewer` for hot paths, queries, I/O, concurrency, memory, or resource use; add `architecture-reviewer` for public APIs, module boundaries, schemas, dependencies, migrations, or compatibility.
- Use the named agent when available. Otherwise spawn a general subagent with the same contract, Terra model, and role-appropriate effort.

## Invariants

- Write tests before implementing any code change or new functionality, and ensure the tests cover the changed behavior.
- Prioritize functional and end-to-end tests over unit tests.
- Use unit tests primarily for edge cases that are impractical to cover at a higher level.
- Minimize mocks; test real behavior and integration boundaries whenever practical.
- Never weaken, delete, or bypass a test merely to make an implementation pass unless the requested behavior intentionally supersedes it.
- If meaningful automated coverage is genuinely impractical, stop before implementation, explain the limitation and proposed substitute, and obtain the user's explicit waiver.

## Compact Path

1. Read applicable repository instructions and inspect the implementation, tests, dependencies, runtime path, and verification commands.
2. Define observable acceptance criteria.
3. Add or update the highest practical test first and confirm the expected failure. For a behavior-preserving refactor, add or update characterization coverage and establish a passing baseline; do not manufacture a failure.
4. Implement the smallest change that satisfies the criteria.
5. Run focused tests, then relevant broader tests and applicable lint, type-check, build, and formatting checks.
6. Inspect the diff and report pre-change evidence, final verification, and unrelated failures separately.

## Orchestrated Path

1. **Isolate.** Inspect repository status, base branch, and existing worktrees. Create or reuse one dedicated branch and worktree for the entire task before spawning subagents. Record its path, branch, HEAD, and initial status.
   - Give every subagent the same worktree root.
   - Keep branch switching, worktree management, staging, committing, stashing, resetting, and cleanup under main-agent ownership.
   - Recheck branch, HEAD, and status at phase boundaries. Stop on unexpected drift rather than overwriting it.
   - If required uncommitted work cannot be transferred safely, or Git isolation is unavailable, ask the user before using another arrangement.
2. **Explore.** Spawn `explorer` for read-only repository and runtime investigation. Request concise evidence with file or symbol references, relevant commands, risks, and unresolved questions. Add explorers only for genuinely independent surfaces.
3. **Plan and approve.** Convert the evidence into observable acceptance criteria, scope boundaries, design decisions, and the smallest useful agent set.
   - Follow the repository's planning convention when present; otherwise use `.agents/plans/<task-slug>.md`.
   - Record scope, decisions, assignments, non-overlapping file ownership, dependency order, testing strategy, verification commands, progress, discoveries, and unresolved findings.
   - Keep the main agent as the plan's sole writer.
   - Present the plan for explicit human approval. Before approval, allow only workspace setup, exploration, and plan updates.
4. **Test first.** Spawn `test-writer` with ownership of the planned acceptance tests. Have it write them and prove they fail for the expected behavioral reason. Reject setup failures or tests that encode the wrong contract. For behavior-preserving refactors, require characterization coverage and a recorded passing baseline.
5. **Implement.** Spawn one or more `implementer` agents only for approved, bounded assignments.
   - Parallelize only independent files or components; sequence overlapping work.
   - Give each coding agent the worktree root, plan path, exact scope, owned files, acceptance criteria, relevant commands, and the prohibition on Git-state operations.
   - Keep acceptance-test ownership with the test agent. Implementers may add focused coverage but may not weaken the acceptance tests.
   - Require each agent to report changed files, decisions, tests, and blockers.
6. **Integrate and verify.** Inspect the combined diff against the approved plan. Spawn `verifier` to run check-only formatting, linting, type checking, focused tests, integration or end-to-end tests, the relevant full suite, and builds. Delegate any required edits back to the owning `implementer`.
7. **Review by risk.** Always spawn `correctness-reviewer`. Add `security-reviewer`, `performance-reviewer`, and `architecture-reviewer` only when their roster triggers apply. Reviewers report evidence, severity, location, and reproduction steps without editing files.
8. **Resolve and finish.** Evaluate findings against evidence and acceptance criteria. Record accepted, rejected, and scope-expanding findings in the plan; obtain approval before expanding scope. Delegate accepted fixes to the owning `implementer`, rerun focused checks, and repeat relevant verification and review until all criteria pass and no blocking finding remains.
   - Inspect the final diff and repository status.
   - Remove the transient plan unless repository policy requires it to remain.
   - Commit only the completed task files on the dedicated branch.
   - Present the commit, diff summary, acceptance evidence, test results, reviewer findings, and remaining risks.
   - Never merge or push unless explicitly requested.
