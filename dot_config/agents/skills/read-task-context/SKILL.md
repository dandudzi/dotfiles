---
name: read-task-context
description: Use when asked to read task context from issue tracker.
---

1. Established if repository contains `.issue-tracker-connection` file and you can use defined connection. If not stop the work and asked user to setup connection with `setup-issue-tracker` skill.
2. Obtain issue key.
3. Get context of the issue. Compress it and pass only relevant information to main agent or print to user.
