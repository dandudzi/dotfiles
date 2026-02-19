---
name: code-search
description: Semantic code search for finding code by meaning. Use when searching for concepts, logic, patterns, or asking "where is X handled" or "find code that does Y".
allowed-tools: Bash(greppy:*)
---

# Code Search Skill

## When to Use This Skill

Use `greppy search` for:

- Finding code by concept ("authentication logic", "error handling")
- Exploring unfamiliar codebases
- Searching by intent, not exact text

Use `greppy exact` for:

- Specific strings, function names, imports
- TODOs, FIXMEs, exact patterns

Use `greppy read` for:

- Reading file contents after finding a match
- Viewing context around a specific line

## Commands

### Semantic Search

```bash
greppy search "your query" -n 10
```

### Exact Match

```bash
greppy exact "pattern"
```

### Read File

```bash
greppy read file.py:45 # Context around line 45
greppy read file.py:30-80 # Lines 30-80
```
