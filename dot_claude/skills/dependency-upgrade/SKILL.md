---
name: dependency-upgrade
description: >
  Structured dependency upgrade methodology: semver analysis, compatibility
  matrices, staged rollout with checkpoints, and per-ecosystem tooling.
  Use when upgrading major versions or running dependency campaigns.
---

# Dependency Upgrade

## When to Activate

Trigger on: "upgrade dependencies", "major version", "dependency audit", "breaking changes", "npm outdated", "outdated packages", "dependency campaign", "migrate to v", "upgrade from v".

## Semantic Versioning Matrix

| Change Type | Version Bump | Risk | Strategy |
|-------------|-------------|------|----------|
| Breaking API change | MAJOR (X.0.0) | HIGH | Staged; test matrix required |
| New backwards-compatible feature | MINOR (0.X.0) | LOW | Batch upgrades acceptable |
| Bug fix, security patch | PATCH (0.0.X) | VERY LOW | Automated (Dependabot/Renovate) |

### Version Constraint Symbols
| Symbol | Meaning | Example |
|--------|---------|---------|
| `^1.2.3` | Compatible (≥1.2.3, <2.0.0) | Most packages |
| `~1.2.3` | Patch only (≥1.2.3, <1.3.0) | Strict stability |
| `>=1.2.3 <2.0.0` | Explicit range | Maximum control |
| `1.2.3` | Exact pin | Reproducible builds |

## Pre-Upgrade Assessment

### Step 1: Audit Current State
```bash
# npm / pnpm
npm outdated          # shows current, wanted, latest
npx npm-check-updates # interactive update tool

# Python
pip list --outdated
pip-audit             # also checks CVEs

# Maven
mvn versions:display-dependency-updates

# Gradle
./gradlew dependencyUpdates

# Cargo
cargo outdated
```

### Step 2: Dependency Tree Analysis
```bash
# npm — why is this package here?
npm ls react                      # show why react is installed
npx madge --circular src/         # detect circular deps

# pnpm
pnpm why react

# Maven
mvn dependency:tree -Dincludes=com.example:library

# Python
pip show requests                 # shows who requires it
pipdeptree                       # full tree
```

### Step 3: Risk Classification
For each outdated dependency, classify:
- MAJOR version gap → HIGH risk, manual testing required
- MINOR version gap → LOW risk, automated acceptable
- PATCH version gap → VERY LOW, automate

## Compatibility Matrix Template

Document cross-package version constraints before upgrading:

```markdown
## Compatibility Matrix: React Ecosystem

| Package | v17 | v18 | v19 |
|---------|-----|-----|-----|
| react-router | ✅ v6.x | ✅ v6.x | ✅ v7.x |
| @testing-library/react | ✅ v12 | ✅ v14+ | ✅ v16+ |
| redux | ✅ v8 | ✅ v8 | ✅ v9+ |
| styled-components | ✅ v5 | ✅ v6+ | ⚠️ Check |
| next.js | ✅ v12 | ✅ v13+ | ✅ v15+ |
```

Fill this out BEFORE starting upgrades to identify blocking dependencies.

## Staged Upgrade Strategy

### 4-Stage Process

**Stage 1: Planning**
- Identify target versions
- Build compatibility matrix
- Create git branch for upgrade campaign
- Snapshot all current tests (must be green before starting)

**Stage 2: Incremental Upgrades**
- Upgrade ONE package at a time for MAJOR bumps
- Run full test suite after each upgrade
- Commit after each successful upgrade
- Document breaking changes encountered

**Stage 3: Integration Testing**
- Run E2E tests
- Manual smoke test of critical paths
- Performance comparison (before/after benchmarks)

**Stage 4: Validation**
- Security audit (`npm audit`, `pip-audit`)
- Check for duplicate package versions in lockfile
- Final test run on CI
- Update internal documentation (CHANGELOG)

### Upgrade Order for Major Campaigns
1. **Security patches first** — no breaking changes, immediate value
2. **Dev dependencies** — lower risk (build tools, linters)
3. **Test dependencies** — testing infrastructure
4. **Utility libraries** — helpers, date libraries, HTTP clients
5. **Framework dependencies last** — highest impact, most breaking changes

## Per-Ecosystem Tooling

| Ecosystem | Outdated Check | Upgrade Tool | Lock File | Audit |
|-----------|---------------|-------------|----------|-------|
| npm | `npm outdated` | `npm-check-updates` | `package-lock.json` | `npm audit` |
| pnpm | `pnpm outdated` | `pnpm update` | `pnpm-lock.yaml` | `pnpm audit` |
| Python (pip) | `pip list --outdated` | `pip install --upgrade` | `requirements.txt` | `pip-audit` |
| Python (uv) | `uv lock --upgrade-package X` | `uv sync` | `uv.lock` | `pip-audit` |
| Maven | `mvn versions:display-dependency-updates` | `mvn versions:update-dependencies` | N/A | `dependency-check-maven` |
| Gradle | `./gradlew dependencyUpdates` | Edit `build.gradle` | `gradle.lockfile` | OWASP plugin |
| Cargo | `cargo outdated` | `cargo update` | `Cargo.lock` | `cargo audit` |

## Rollback Plan

**Before starting any MAJOR upgrade campaign:**
```bash
# 1. Tag the stable state
git tag pre-upgrade-$(date +%Y%m%d)

# 2. Ensure lockfile is committed
git add package-lock.json && git commit -m "chore: snapshot lockfile before upgrade"

# 3. Create upgrade branch
git checkout -b chore/upgrade-react-v19
```

**If upgrade fails at any stage:**
```bash
# Restore lockfile to pre-upgrade state
git checkout pre-upgrade-$(date +%Y%m%d) -- package-lock.json
npm ci  # clean install from restored lockfile

# Or revert entire branch
git checkout main
git branch -D chore/upgrade-react-v19
```

**Validation gates** (must pass before proceeding to next package):
- [ ] `npm test` passes (or equivalent)
- [ ] No new `npm audit` HIGH/CRITICAL vulnerabilities
- [ ] Application starts without errors
- [ ] Smoke test of core functionality

## Anti-Patterns

❌ Upgrading all at once — Impossible to identify which upgrade caused a failure

❌ Ignoring peer dependency warnings — `npm warn peer dep` warnings often indicate incompatibilities

❌ Not committing lockfile — Lockfile must be committed; reproducible installs are critical

❌ Skipping compatibility matrix — Discovering blocking dependencies mid-upgrade wastes time

❌ Upgrading before tests are green — You can't tell if the upgrade broke something if tests were already failing

## Agent Support

- Use `dependency-manager` agent for security vulnerability scanning and SBOM generation
- Use `owasp-top10-expert` agent for vulnerability assessment of flagged packages

## Skill References

- `search-first` — research new major versions before upgrading (check breaking changes, migration guides)
- `tdd-workflow` — ensure test coverage before starting upgrades
