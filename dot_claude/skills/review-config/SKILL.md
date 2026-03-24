---
name: review-config
description: >
  Review configuration files and directories for improvements. Reads config files,
  researches current best practices via Context7 and Exa web search, and suggests
  concrete improvements. Invoke explicitly with /review-config <path>.
disable-model-invocation: true
context: fork
model: opus
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
  - mcp__exa__web_search_exa
  - mcp__claude_ai_exa__web_search_exa
denied-tools:
  - Edit
  - Write
  - NotebookEdit
  - Agent
  - Skill
  - TaskCreate
  - TaskUpdate
  - TaskStop
  - TeamCreate
  - TeamDelete
  - CronCreate
  - CronDelete
  - SendMessage
  - EnterWorktree
  - ExitWorktree
---

# Review Config

Audit configuration files or directories against current best practices. Produces a
structured improvement report with actionable suggestions.

## Arguments

| Arg | Required | Description |
|-----|----------|-------------|
| `path` | Yes | Absolute or relative path to a config file or directory to review |

If no path is provided, ask the user which config to review.

## Workflow

### 1. Discover Config Files

- If `path` is a directory, list all files recursively (skip `.git`, `node_modules`, etc.)
- Identify config files by extension and name patterns:
  - Dotfiles: `.bashrc`, `.zshrc`, `.gitconfig`, `.editorconfig`, `.tmux.conf`, etc.
  - Named configs: `config`, `config.toml`, `settings.json`, `*.conf`, `*.yaml`, `*.yml`, `*.toml`, `*.ini`, `*.cfg`
  - Tool-specific: `Brewfile`, `Cargo.toml`, `pyproject.toml`, `package.json`, `tsconfig.json`, `Makefile`, etc.
- If `path` is a single file, review just that file

### 2. Read and Understand

- Read each config file (use `Read` for config files — they are non-code)
- Identify the tool/application each config belongs to
- Note the current settings, what they do, and any commented-out options

### 3. Research Best Practices

Use **both** Context7 and Exa web search to find current recommendations. Budget: **max 10 web searches total** across the entire review.

**Context7** — for tool documentation:
1. `resolve-library-id` for the tool (e.g., "bat", "tmux", "git")
2. `query-docs` for configuration best practices and new options

**Exa web search** — for community recommendations:
- Search for: `"<tool> config best practices <current year>"`
- Search for: `"<tool> recommended settings"` or `"<tool> dotfiles tips"`
- Prioritize recent results (last 12 months)

### 4. Analyze and Compare

For each config file, evaluate:

- **Missing useful options**: settings the user hasn't configured that would be beneficial
- **Deprecated settings**: options that have been superseded or removed in newer versions
- **Security concerns**: permissions, exposed paths, insecure defaults
- **Performance tuning**: settings that could improve performance
- **Redundant settings**: options that duplicate defaults (unnecessary clutter)
- **Consistency**: naming conventions, formatting, organization
- **Version compatibility**: settings that may not work with the installed version

### 5. Output Report

Present findings grouped by file. For each file:

```
## <file_path>

**Tool**: <tool name> | **Version detected**: <version or "unknown">

### Improvements Found

1. **<category>**: <description>
   - Current: `<current setting or "not set">`
   - Suggested: `<recommended setting>`
   - Why: <brief rationale with source>

### No Issues

If the config is already well-optimized, say so explicitly:
"No improvements found — this config follows current best practices."
```

End with a summary:

```
## Summary

- Files reviewed: N
- Improvements found: N (X critical, Y recommended, Z optional)
- Files with no issues: N
```

## Rules

- **Never modify files** — this skill is read-only. Only suggest changes.
- **Max 10 web searches** — be strategic about which tools to research
- **Skip binary files** — only review text-based configs
- **Respect privacy** — never include secrets, tokens, or passwords in the report output
- **Be honest** — if a config is already good, say "nothing to improve" rather than inventing issues
- **Cite sources** — link to documentation or articles that support each suggestion
- **Check installed version** — when possible, detect the tool version to avoid suggesting incompatible options

## Examples

```
/review-config ~/.config/bat
/review-config ~/.gitconfig
/review-config ~/projects/myapp/.env.example
/review-config /etc/nginx/
```
