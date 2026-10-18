---
name: create-task-in-backlog
description: Use to create issue in the backlog.
---

1. Established if repository contains `.issue-tracker-connection` file and you can use defined connection. If not stop the work and asked user to setup connection with `setup-issue-tracker` skill.
2. Obtain context like description and summary from main agent.
3. Search current backlog for relevant issues and make sure that similar task doesn't exist.
4. Use defined connection to create issue with defined details in `.issue-tracker-connection` like user to be assigned - principal, tags/labels to be used and destination project. Set parent if asked to create child issue. Set issue type/label to categorize work by `Task/Story/Bug`
5. Link relevant issues with this issue e.g. `blocking`/`blockedBy`
6. Return issue key and link to the newly created issue.
