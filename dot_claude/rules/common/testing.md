# Testing Requirements

> **Source of truth:** The `tdd-workflow` skill (`~/.claude/skills/tdd-workflow/SKILL.md`) contains full TDD enforcement rules, exemptions, coverage policy, and test double strategy.

## Quick Reference

- **Minimum coverage:** 80%
- **Test types:** Unit, Integration, E2E (all required)
- **Workflow:** RED -> GREEN -> REFACTOR (see tdd-workflow skill)

## Troubleshooting Test Failures

1. Use **tdd-guide** agent
2. Check test isolation
3. Verify mocks are correct
4. Fix implementation, not tests (unless tests are wrong)
