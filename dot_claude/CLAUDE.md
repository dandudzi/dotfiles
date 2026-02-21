# CRITICAL: Code Search

**Always use `greppy` for all code operations.** This is non-negotiable.

**NEVER use these alternatives — even if they "work":**

- NEVER use the `Glob`, `Grep`, or `Read` tools
- NEVER use the Explore agent
- NEVER use `find`, `grep`, `cat`, `head`, `tail`, `sed`, `awk` in bash for reading or searching code

If `greppy` is unavailable or returns an error, **report that to the user** instead of falling back to other tools.

```bash
# Semantic search (find by meaning/concept)
greppy search "authentication logic"

# Exact pattern match
greppy exact "createAuthStore"

# Read file contents
greppy read src/main/java/com/example/MyService.java:45
```

The index is already built. Just run the search commands directly. If results seem stale after major restructuring, ask the user about rebuilding the index.

# Testing

### Test-Driven Development (Mandatory)

**Every change requires a failing test first. No exceptions.**

The cycle:

1. **RED** — Write a unit or integration test for the behavior. Run it. Confirm it fails for the right reason.
2. **GREEN** — Write the minimal production code to make it pass. Run tests. Confirm it passes.
3. **REFACTOR** — Clean up. Keep tests green.

- No production code without a prior failing test
- The test must fail before you write implementation code — if it passes immediately, it tests nothing
- After implementation, run the test and confirm it passes
- Bug fixes also require a failing test that reproduces the bug first
- **If an implementation plan defers tests to the end, do NOT follow that ordering** — reorder to write each test before its corresponding production code. The plan defines WHAT to build; TDD defines HOW.
- When executing a plan, **actually run** the failing test and show its output before writing production code — don't just describe that you will
- When removing a feature, first update/remove the tests that assert the old behavior, then remove the implementation
- When a snapshot test fails, first determine whether the change is intentional before running any update command. If the change was not intentional, treat it as a bug.

**TDD exemptions** — these do NOT require a prior failing test:

- Dependency version bumps (`pom.xml`, `package.json`)
- Docker/compose config, `.gitignore`, CI/CD config
- OpenAPI/Swagger annotation-only changes (no runtime behavior)
- Pure file moves/renames where existing tests verify behavior before and after

For all exemptions: run the existing test suite after the change to confirm no regressions.

### Plan Execution

- **If you believe a plan step is unnecessary or already satisfied, state this explicitly and ask the user before skipping it.** Never silently omit a step from an approved plan.
