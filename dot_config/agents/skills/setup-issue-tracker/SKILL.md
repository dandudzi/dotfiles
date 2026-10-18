---
name: setup-issue-tracker
description: Set up or update a repository-local .issue-tracker-connection with verified tracker access. Use when asked to connect a repository to an issue tracker.
---

# Setup Issue Tracker

Create a non-secret YAML file named `.issue-tracker-connection` at the repository root. It describes how agents access the tracker and which issues belong to this repository.

## Connection format

Example file context

```yaml
tracker:
  name: Linear
access:
  kind: mcp/skill
  name: linear
principal:
  name: Telaweft Codex
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
```
