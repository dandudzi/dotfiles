# Code Search — Strict Policy

## (Mandatory) Internet search tool for docs and code generations

Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.

## Local search tool

**greppy is the PRIMARY search tool. Using `grep`, `cat`, `head`, `tail`, `sed`, or `find` via Bash instead of greppy is a violation of these instructions.**

- Use `greppy` for every file read, pattern search, and directory exploration — no exceptions.
- **If `greppy` is unavailable or errors**, fall back to `Grep`/`Read`/`Glob` and **report the issue to the user immediately**.
- The greppy index is already built. Run commands directly. If results seem stale after major restructuring, ask the user about rebuilding the index.
- Using the Bash tool with `grep`/`cat`/`find`/`sed`/`head`/`tail` when greppy would suffice is not allowed, even if it feels faster.

| Instead of                | Use                                    |
| ------------------------- | -------------------------------------- |
| `grep -n "pattern" file`  | `greppy exact "pattern" -p file`       |
| `grep -in "pattern" file` | `greppy exact -i "pattern" -p file`    |
| `grep -n "a\|b\|c" file`  | `greppy exact "a\|b\|c" -p file`       |
| `grep -rn "pattern" dir`  | `greppy exact "pattern" -p dir`        |
| `sed -n '10,50p' file`    | `greppy read file:10-50`               |
| `cat file \| head -50`    | `greppy read file`                     |
| `cat file`                | `greppy read file -c 1000`             |
| `find . -name "*.java"`   | `greppy exact "" -p . --glob "*.java"` |

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

**TDD exemptions** — these do NOT require a prior failing test:

- Dependency version bumps (`pom.xml`, `package.json`)
- Docker/compose config, `.gitignore`, CI/CD config
- OpenAPI/Swagger annotation-only changes (no runtime behavior)
- Pure file moves/renames where existing tests verify behavior before and after

**This list is closed.** You may NOT self-authorize new exemptions. If you believe a situation requires skipping TDD, state this explicitly and ask the user before proceeding.

**If a project has no test runner or test files for the affected code,** state this explicitly to the user. Do not silently skip TDD — ask whether to add a test framework or proceed without tests.

For all exemptions: run the existing test suite after the change to confirm no regressions.

### Plan Execution

- **If you believe a plan step is unnecessary or already satisfied, state this explicitly and ask the user before skipping it.** Never silently omit a step from an approved plan.
- **Verification commands in a plan are mandatory.** Run them, show their output, and confirm they pass before declaring the task complete. Do not skip or defer verification steps.

# Model Routing

**Use `opusplan` as the default model.** This automatically uses Opus for planning and Sonnet for execution.

When the user's request is clearly a simple/mechanical task, **proactively switch to a cheaper model** before starting work. Use this guidance:

### Use Haiku (`/model haiku`) for

- Reading/summarizing files or documentation
- Simple file searches and grep operations
- Generating boilerplate code from clear templates
- Formatting, linting suggestions, or style fixes
- Simple rename/move operations
- Answering quick factual questions about the codebase
- Writing commit messages
- Simple config file edits

### Use Sonnet (`/model sonnet`) for

- Standard feature implementation with clear requirements
- Writing tests for well-defined behavior
- Code refactoring with known patterns
- Bug fixes with obvious root causes
- Documentation generation
- Code review of small-to-medium changes

### Stay on Opus for

- Architecture design and system planning
- Complex debugging with unclear root causes
- Multi-file refactoring affecting many components
- Security analysis and vulnerability assessment
- Performance optimization requiring deep analysis
- Any task where you're uncertain about the approach
- Brainstorming and strategic decisions

### How to switch

When you identify a task that could use a lighter model, say:

> "This looks like a [simple/standard] task. Switching to [haiku/sonnet] to save tokens. `/model haiku`"
