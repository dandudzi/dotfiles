---
name: coding-workflow
description: Orchestrate code changes through an adaptive, test-first workflow. Use only when asked to plan coding task.
---

Use only when explicitly asked to use this skill by saying `plan the work`/`plan`. Anything else like `fix it`/`do it`/`approved` or similar should not trigger this workflow.

# Coding Workflow

Own the outcome as the main orchestration agent. Use subagents for work delegation:

- Assign read-only discovery and context exploration,
- Acceptance-test writing,
- Implementation,
- Review like security, performance, or architecture.

Read `CONTEXT.md` file if exist to communicate with DDD domain language.

## Orchestrated Path

1. **Isolate and claim.** Create or reuse one dedicated branch and worktree for the entire task before spawning subagents. Use for that `create-git-worktree` and `create-git-branch` skills. Enter the dedicated worktree, and verify the current directory before creating the plan or any other work artifact.
   - Give every subagent the same worktree root.
   - Keep branch switching, worktree management, staging, committing, stashing, resetting, and cleanup under main-agent ownership.
2. **Explore.** Use subagent that should use `read-task-context` skill to understand work scope. Then make local review by assigning a generic subagent that will make read-only repository and runtime investigation. Request concise evidence with file or symbol references, relevant commands, risks, and unresolved questions.
3. **Plan and approve.** Convert the evidence into observable acceptance criteria plan.
   1. Create plan in `./.plans/<task-slug>.md`.
   2. Record plan in form of 4 sections:
      2.1. High level, short overview of what should be delivered.
      2.2. Scope of changes in form of tests that plays the role of requirements. Those tests are required to be implemented in next steps. Use `plan-test` skill to create this list. Always print to user plan in format that skill enforce.
      2.3. Architectural changes using `architecture-change` skill.
      2.4. Optional section with dropped ideas and review findings to not be implemented.
   3. Spawn subagent that will review plan using `review-plan` skill.
   4. Then request an explicit human approval by showing complete plan. Always print to user full file even if there was small change.
   5. Iterate with human until plan is approved.
4. **Test first implementation.** Assign subagent to implement the plan. Explicitly pass to it created plan in step 3. Request it to utilise `implementing-code` and `test-writing` skills.
5. **Verify.** Spawn dedicated subagents that will make read-only verifications:
  - Generic code style reviewer.
  - Checking rules defined in `review-code-rules` skill.
  - Consistency checker - that compares list of implemented and edited tests. In case of difference between plan vs current implemented state, it need to flag the differences. Those difference needs to me reviewed with user in next step.
  - Domain reviewer - spawn if repository using DDD approach. That checks if changes follows DDD practices. In case `CONTEXT.md` should be updated it should be reviewed with user in next step.
  - Security reviewer that will make static review.
  - Other subagents if context requires.
6. Using skill `print-what-delivered`.
7. **Review with user** any review suggestions that was found in verify step and they are not duplication of dropped suggestions, from previous iterations, defined in plan. Ask for approval, dropping or moving separate task for each suggestions. Before moving forward make sure all decisions are resolved, then in this order:
   7.1. Dropped review findings write to section in the plan so they can be de duplicated in next iterations.
   7.2. Next task findings should be delegated to new subagent that will use `create-task-in-backlog` skill.
   7.3. For changes approved. First commit current state using `create-git-commit` skill and back to step 3 to start and plan new the iteration.
2. **Resolve and finish.** Evaluate that all changes are committed and newly added tests passing. Then use `create-git-pr` skill to create pull request.
