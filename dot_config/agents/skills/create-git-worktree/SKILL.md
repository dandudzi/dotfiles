---
name: create-git-worktree
description: Create or reuse an isolated Git worktree for a task and verify its repository, branch, and starting state before planning or implementation.
---

# Create Git Worktree

Create or reuse one isolated worktree for the task.

1. Obtain the task key and agreed branch name.
2. Inspect Git status, existing branches, and `git worktree list --porcelain`.
   Reuse an existing task worktree when its repository and branch match.
   Report unexpected changes without resetting, stashing, or overwriting them.
   Do not assume main or master, or silently use a stale local branch.
3. Create worktree in `.worktrees/<issue-key>`.
4. Enter the worktree and verify its absolute path, branch, HEAD, and status
   before creating plans, tests, or implementation files.
5. Return that verified state to the coordinating agent. Give all delegated
   agents the same worktree root. The coordinator owns Git-state operations.
