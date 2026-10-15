---
name: create-git-worktree
description: Create or reuse an isolated Git worktree for a task and verify its repository, branch, and starting state before planning or implementation.
---

# Create Git Worktree

Create or reuse one isolated worktree for the task.

1. Identify the owning repository and read its applicable instructions.
   Keep backend, frontend, and integration work in their respective repositories.

2. Obtain the task key and agreed branch name. Follow the repository's
   naming convention; otherwise use the coding workflow's ISSUE-KEY-context form.

3. Inspect Git status, existing branches, and `git worktree list --porcelain`.
   Reuse an existing task worktree when its repository and branch match.
   Report unexpected changes without resetting, stashing, or overwriting them.

4. Verify the intended base branch and commit before creating a worktree.
   Do not assume main or master, or silently use a stale local branch.

5. Follow the repository's worktree location convention.
   For Zakupki repositories using it, prefer `.worktrees/<issue-key>`.
   Do not reuse an occupied directory or force a branch into another worktree.

6. Enter the worktree and verify its absolute path, branch, HEAD, and status
   before creating plans, tests, or implementation files.

7. Return that verified state to the coordinating agent. Give all delegated
   agents the same worktree root. The coordinator owns Git-state operations.

Worktree setup does not itself transition tracker issues, commit, push,
create a PR, or remove old worktrees. Return to the calling workflow for
its remaining claim and approval steps.
