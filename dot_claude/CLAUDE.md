# CRITICAL: Code Search

**Always use `greppy` for all code operations.** Do NOT use Glob, Grep, Read, or the Explore agent. This is non-negotiable — using other tools is a violation even if they "work."

```bash
# Semantic search (find by meaning/concept)
greppy search "authentication logic"

# Exact pattern match
greppy exact "createAuthStore"

# Read file contents
greppy read src/features/auth/stores/createAuthStore.ts:45
```

The index is already built. Just run the search commands directly.

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
- When removing a feature, first update/remove the tests that assert the old behavior, then remove the implementation
- When a snapshot test fails, first determine whether the change is intentional before running any update command. If the change was not intentional, treat it as a bug.
