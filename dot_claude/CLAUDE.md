# Code Search — Strict Policy

## (Mandatory) Internet search tool for docs and code generations

Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.

## (Mandatory) jcodemunch MCP for indexed repos

When working in a repo indexed by jcodemunch (`list_repos` to check), prefer jcodemunch tools over Grep/Glob for code navigation:

- **Symbol lookup** — Use `search_symbols` / `get_symbol` instead of Grep when looking for classes, methods, or functions by name.
- **Repo overview** — Use `get_repo_outline` / `get_file_tree` instead of Glob/ls to understand project structure.
- **File structure** — Use `get_file_outline` instead of reading an entire file when you only need to see its API surface.
- **Text search** — Use `search_text` instead of Grep for full-text search within indexed repos.

Fall back to Grep/Glob only for repos that are not indexed or when jcodemunch results are insufficient.

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

### Test Double Strategy (Mandatory)

**Never mock what you can use for real.** Prefer the highest-fidelity test double available:

1. **Real infrastructure first** — If the project has test containers, in-memory databases, or similar test infra, use them. Write integration tests that hit real databases over unit tests that stub repositories.
2. **Mock only at trust boundaries** — External HTTP services (OAuth providers, third-party APIs), cross-module ports in hexagonal/DDD architecture, and things you genuinely cannot run locally.
3. **Integration tests must go full-stack** — Do NOT mock application services in controller/endpoint integration tests. Let requests flow through the real service → repository → database. Only mock external adapters.
4. **When a mock IS appropriate**, prefer the narrowest scope: mock the specific port/adapter, not the entire service.

**Acceptable mocks:**
- External API clients (OAuth2, payment gateways, email services)
- Cross-module ports that enforce bounded-context isolation
- Time, randomness, and other non-deterministic sources

**Not acceptable (when real infra exists):**
- Repositories / data-access layers when a test database is available
- Application services in integration tests
- Domain services that have no external dependencies

### Plan Execution

- **If you believe a plan step is unnecessary or already satisfied, state this explicitly and ask the user before skipping it.** Never silently omit a step from an approved plan.
- **Verification commands in a plan are mandatory.** Run them, show their output, and confirm they pass before declaring the task complete. Do not skip or defer verification steps.

# Model Routing

**Use `sonnet` as the default model.**

When the user's request is clearly a simple/mechanical task, **proactively switch to a cheaper model** before starting work. Use this guidance:

### Use Sonnet (`/model sonnet`) for

- Reading/summarizing files or documentation
- Simple file searches and grep operations
- Generating boilerplate code from clear templates
- Formatting, linting suggestions, or style fixes
- Simple rename/move operations
- Answering quick factual questions about the codebase
- Writing commit messages
- Simple config file edits
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

@RTK.md
