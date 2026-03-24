---
name: continuous-learning-v2
description: Instinct-based learning system that observes sessions via hooks, creates atomic instincts with confidence scoring, and evolves them into skills/commands/agents. v2.1 adds project-scoped instincts to prevent cross-project contamination.
origin: ECC
version: 2.1.0
model: sonnet
---

# Continuous Learning v2.1

Automatic learning system that captures session patterns as atomic "instincts" (small behaviors with 0.3–0.9 confidence scores). v2.1 adds project-scoped instincts — framework-specific patterns stay in their projects, universal patterns shared globally.

## When to Activate

- Setting up observation hooks for automatic learning
- Reviewing or evolving learned instincts into skills/commands
- Exporting, importing, or promoting instincts

## What's New in v2.1

**v2.1** adds project-scoped instincts: React patterns stay in your React project, Python conventions in your Python project. New commands: `/promote` (project → global), `/projects` (list projects). Instincts auto-promote when seen in 2+ projects with confidence >= 0.8.

Previous **v2** improvements: Switched to PreToolUse/PostToolUse hooks (100% reliability vs v1's 50-80% skill activation). Introduced atomic "instincts" with 0.3-0.9 confidence scoring instead of full skills. Background observer agent replaces main context analysis.

## The Instinct Model

An instinct is a small learned behavior:

```yaml
---
id: prefer-functional-style
trigger: "when writing new functions"
confidence: 0.7
domain: "code-style"
source: "session-observation"
scope: project
project_id: "a1b2c3d4e5f6"
project_name: "my-react-app"
---

# Prefer Functional Style

## Action
Use functional patterns over classes when appropriate.

## Evidence
- Observed 5 instances of functional pattern preference
- User corrected class-based approach to functional on 2025-01-15
```

**Properties:**
- **Atomic** -- one trigger, one action
- **Confidence-weighted** -- 0.3 = tentative, 0.9 = near certain
- **Domain-tagged** -- code-style, testing, git, debugging, workflow, etc.
- **Evidence-backed** -- tracks what observations created it
- **Scope-aware** -- `project` (default) or `global`

## How It Works

```
Session Activity (in a git repo)
      |
      | Hooks capture prompts + tool use (100% reliable)
      | + detect project context (git remote / repo path)
      v
+---------------------------------------------+
|  projects/<project-hash>/observations.jsonl  |
|   (prompts, tool calls, outcomes, project)   |
+---------------------------------------------+
      |
      | Observer agent reads (background, Haiku)
      v
+---------------------------------------------+
|          PATTERN DETECTION                   |
|   * User corrections -> instinct             |
|   * Error resolutions -> instinct            |
|   * Repeated workflows -> instinct           |
|   * Scope decision: project or global?       |
+---------------------------------------------+
      |
      | Creates/updates
      v
+---------------------------------------------+
|  projects/<project-hash>/instincts/personal/ |
|   * prefer-functional.yaml (0.7) [project]   |
|   * use-react-hooks.yaml (0.9) [project]     |
+---------------------------------------------+
|  instincts/personal/  (GLOBAL)               |
|   * always-validate-input.yaml (0.85) [global]|
|   * grep-before-edit.yaml (0.6) [global]     |
+---------------------------------------------+
      |
      | /evolve clusters + /promote
      v
+---------------------------------------------+
|  projects/<hash>/evolved/ (project-scoped)   |
|  evolved/ (global)                           |
|   * commands/new-feature.md                  |
|   * skills/testing-workflow.md               |
|   * agents/refactor-specialist.md            |
+---------------------------------------------+
```

## Project Detection

The system automatically detects your current project:

1. **`CLAUDE_PROJECT_DIR` env var** (highest priority)
2. **`git remote get-url origin`** -- hashed to create a portable project ID (same repo on different machines gets the same ID)
3. **`git rev-parse --show-toplevel`** -- fallback using repo path (machine-specific)
4. **Global fallback** -- if no project is detected, instincts go to global scope

Each project gets a 12-character hash ID (e.g., `a1b2c3d4e5f6`). A registry file at `~/.claude/homunculus/projects.json` maps IDs to human-readable names.

## Quick Start

### 1. Enable Observation Hooks

Add to `~/.claude/settings.json` (if plugin): use `${CLAUDE_PLUGIN_ROOT}/skills/continuous-learning-v2/hooks/observe.sh`, or (if manual): `~/.claude/skills/continuous-learning-v2/hooks/observe.sh`. Attach to both PreToolUse and PostToolUse hooks with matcher `*`.

### 2. Initialize Directory Structure

The system creates directories automatically on first use, but you can also create them manually:

```bash
# Global directories
mkdir -p ~/.claude/homunculus/{instincts/{personal,inherited},evolved/{agents,skills,commands},projects}

# Project directories are auto-created when the hook first runs in a git repo
```


## Commands

- `/instinct-status` — Show all instincts (project + global) with confidence
- `/evolve` — Cluster instincts into skills/commands, suggest promotions
- `/instinct-export` — Export instincts by scope/domain
- `/instinct-import <file>` — Import instincts with scope control
- `/promote [id]` — Promote project instincts to global
- `/projects` — List projects and instinct counts

## Configuration

Edit `config.json`: set `observer.enabled` to `true` to activate background analysis. Default interval is 5 minutes with 20 minimum observations. Project scoping, thresholds, and promotion criteria are code-configured in `instinct-cli.py` and `observe.sh`.

## File Structure

```
~/.claude/homunculus/
+-- identity.json           # Your profile, technical level
+-- projects.json           # Registry: project hash -> name/path/remote
+-- observations.jsonl      # Global observations (fallback)
+-- instincts/
|   +-- personal/           # Global auto-learned instincts
|   +-- inherited/          # Global imported instincts
+-- evolved/
|   +-- agents/             # Global generated agents
|   +-- skills/             # Global generated skills
|   +-- commands/           # Global generated commands
+-- projects/
    +-- a1b2c3d4e5f6/       # Project hash (from git remote URL)
    |   +-- project.json    # Per-project metadata mirror (id/name/root/remote)
    |   +-- observations.jsonl
    |   +-- observations.archive/
    |   +-- instincts/
    |   |   +-- personal/   # Project-specific auto-learned
    |   |   +-- inherited/  # Project-specific imported
    |   +-- evolved/
    |       +-- skills/
    |       +-- commands/
    |       +-- agents/
    +-- f6e5d4c3b2a1/       # Another project
        +-- ...
```

## Scope Decision Guide

**Project scope:** Language/framework conventions, file structure preferences, code style, error handling strategies (e.g., "Use React hooks", "Prefer dataclasses", "Tests in `__tests__`").

**Global scope:** Security practices, general best practices, tool workflows, git practices (e.g., "Validate user input", "Write tests first", "Conventional commits").

## Instinct Promotion

Auto-promote instincts when seen in 2+ projects with confidence >= 0.8. Use `/promote [id]` to promote manually or `/evolve` to see candidates. Preview with `--dry-run`.

## Confidence Scoring

Scores range 0.3 (tentative, suggested) to 0.9 (near-certain, core). Confidence increases when patterns repeat, user doesn't correct behavior, or similar instincts agree. Decreases when explicitly corrected, unobserved for extended periods, or contradicted.


## Backward Compatibility

v2.1 supports v2.0 and v1: global instincts, learned skills from v1, and stop hooks all work. Gradual migration supported — run both in parallel.

## Privacy

Observations stay local. Project instincts are isolated. Only patterns (not raw observations) are exported. No code or conversation content is shared — you control all exports and promotions.

---

*Instinct-based learning: teaching Claude your patterns, one project at a time.*
