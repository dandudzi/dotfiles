---
name: sast-configuration
description: Static Application Security Testing tool selection, configuration, CI/CD integration, secret scanning, dependency scanning, and shift-left deployment strategies.
origin: ECC
model: sonnet
---

# SAST Configuration

## When to Activate

- Implementing SAST scanning in CI/CD pipelines
- Evaluating and configuring SAST tools (Semgrep, SonarQube, CodeQL)
- Establishing shift-left scanning strategy (pre-commit, PR gate, nightly deep scan)

## Tool Selection

| Tool | Best For | Key Features |
|------|----------|--------------|
| **Semgrep** | Fast feedback, custom rules | Pattern-based, multi-language rulesets (`p/security-audit`, `p/owasp-top-ten`), seconds-fast |
| **SonarQube** | Enterprise quality gates | Deep semantic analysis, PR decoration, coverage-aware tracking |
| **CodeQL** | Complex vulnerability chains | Dataflow/taint analysis, AST queries, slow but highly accurate |
| **Language-specific** | Python: Bandit; Java: SpotBugs; JS: ESLint + security plugins; Go: gosec |

---

## Semgrep Configuration

### Rule Syntax

```yaml
rules:
  - id: hardcoded-api-key
    pattern-either:
      - pattern: const API_KEY = "sk-..."
      - pattern: password = "..."
    message: "Potential hardcoded API key detected"
    languages: [python, javascript, typescript]
    severity: CRITICAL

  - id: sql-injection-risk
    pattern: db.execute("SELECT * FROM users WHERE id = " + user_input)
    message: "SQL injection risk: use parameterized queries"
    languages: [python, javascript]
    severity: HIGH
    fix: db.execute("SELECT * FROM users WHERE id = ?", [user_input])

  - id: insecure-hash-md5
    pattern: hashlib.md5($VALUE)
    message: "MD5 is broken; use SHA-256"
    languages: [python]
    severity: MEDIUM
```

### Rulesets & Ignore Patterns

```yaml
# .semgrep.yml
rules:
  - p/security-audit
  - p/owasp-top-ten
  - p/cwe-top-25
  - ./rules/custom-rules.yml
```

```
# .semgrepignore
test/ tests/ *_test.go *.spec.ts **/mock* **/__fixtures__/ vendor/ node_modules/ .venv/
```

---

## SonarQube Configuration

### Quality Gate Example

```yaml
# sonar-project.properties
sonar.projectKey=myapp
sonar.projectName=MyApp
sonar.sources=src

# Code coverage
sonar.coverage.exclusions=**/*_test.js,**/node_modules/**
sonar.javascript.lcov.reportPaths=coverage/lcov.info

# Quality gate: fail build if thresholds exceeded
sonar.qualitygate.wait=true
sonar.qualitygate.timeout=300
```

### Quality Gate Rules

```
Conditions (prevent merge if ANY triggered):
- New issues > 5 → FAIL
- Security hotspots unreviewed > 0 → FAIL (in regulated environments)
- Code coverage < 80% → WARN (or FAIL)
- New blocker issues > 0 → FAIL
- Duplicated lines > 20% → WARN
```

### GitHub PR Decoration

```yaml
# GitHub Actions: Run SonarQube, decorate PR with findings
- name: Run SonarQube analysis
  uses: SonarSource/sonarcloud-github-action@master
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}

- name: Check quality gate
  uses: SonarSource/sonarcloud-github-action@master
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
  with:
    args: -Dsonar.qualitygate.wait=true
```

---

## Secret Scanning

**Gitleaks** (git history) and **truffleHog** (deep detection) both integrate via `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
        stages: [commit]
  - repo: https://github.com/trufflesecurity/trufflehog.git
    rev: v3.63.0
    hooks:
      - id: trufflehog
        args: ['filesystem', '.', '--json']
```

Run pre-commit: `gitleaks protect --staged` (local) or `gitleaks detect --exit-code 1` (CI).

---

## Dependency Scanning

**Tools:** OWASP Dependency-Check, Snyk, GitHub Dependabot. Run in CI to fail on HIGH/CRITICAL CVEs.

**Semgrep dependency scan:** Use `snyk test --severity-threshold=high` on every PR.

**Dependabot policy:**
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
```

**CVSS threshold:** Fail CI if CVSS > 7.0 using `snyk test --json` jq filtering.

---

## CI/CD Integration Patterns

### GitHub Actions: Multi-Stage Scanning

```yaml
name: Security Scanning
on: [push, pull_request]

jobs:
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: p/owasp-top-ten p/security-audit
          generateSarif: true
      - name: SonarCloud
        uses: SonarSource/sonarcloud-github-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
      - name: Dependencies
        uses: dependency-check/Dependency-Check_Action@main
        with:
          path: '.'
          format: JSON
      - name: Secrets
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: semgrep.sarif
        if: always()
```

**Severity threshold:** Fail on CRITICAL, warn on HIGH (configurable).

```bash
grep -q '"severity": "CRITICAL"' semgrep-results.json && exit 1
```

---

## False Positive Management

**Inline suppression:** Semgrep `# nosemgrep: rule-id`, SonarQube `@SuppressWarnings("squid:S2077")`

**Suppression audit trail** (suppressions.json):
```yaml
- id: sql-injection-001
  severity: HIGH
  file: src/db/queries.js
  reason: False positive (parameterized queries with ORM)
  approved_by: security-team
  expires: 2025-09-15
```

---

## Shift-Left Strategy

| Stage | Scope | Time Budget | Action |
|-------|-------|-------------|--------|
| **Pre-Commit** | Secrets + fast rules | <5s | `gitleaks protect --staged`, `semgrep p/owasp-top-ten` |
| **PR Gate** | Full SAST + deps | 2-5m | SonarCloud + quality gate, `snyk test --severity-threshold=high` |
| **Nightly** | Deep scan + audit | unbounded | CodeQL, full dep audit, license check, Trivy container scan |

---

## Anti-Patterns to Avoid

1. **Scanning only main branch** → Scan every PR for immediate feedback
2. **No false-positive process** → Implement suppression workflow + re-evaluation triggers
3. **Blocking everything** → Risk-based thresholds: CRITICAL fails, HIGH warns, MEDIUM logs
4. **Ignoring transitive dependencies** → Use Snyk/Dependency-Check for full tree scanning
5. **No secret scanning pre-commit** → Enforce gitleaks/trufflehog hooks
6. **SAST not integrated with code review** → Auto-comment findings on PRs, link to tracking
7. **Custom rules never written** → Maintain domain-specific rules for org threats
8. **One-time scanning** → Continuous scanning with re-assessment policy

---

## Agent Support & References

Use **threat-modeling-expert** for SAST integration aligned with risk profile, **owasp-top10-expert** for OWASP prioritization. See **stride-analysis-patterns** for threat enumeration.

---

## TypeScript/JavaScript Security Patterns

**Secrets:** Use `process.env.API_KEY`, never hardcode. Fail fast if missing.

**XSS:** Sanitize with DOMPurify before insertion. Set CSP header `require-trusted-types-for 'script'`.

**Prototype Pollution:** Reject `__proto__`, `constructor`, `prototype` keys from untrusted objects.
```typescript
const FORBIDDEN_KEYS = new Set(['__proto__', 'constructor', 'prototype'])
const filtered = Object.fromEntries(
  Object.entries(source).filter(([key]) => !FORBIDDEN_KEYS.has(key))
)
```

**SQL Injection:** Use parameterized queries (Prisma ORM) or tagged templates, never concatenate.
```typescript
const user = await db.user.findUnique({ where: { id: userId } })
const user = await db.query`SELECT * FROM users WHERE id = ${userId}`
```

**Input Validation:** Use Zod at system boundaries. Reject 400 on failure.
```typescript
const UserInput = z.object({ email: z.string().email() })
try { const data = UserInput.parse(req.body) } catch { res.status(400).json({ error: 'Invalid' }) }
```

**Dependency Auditing:** Run `npm audit --audit-level=high` in CI. Fail on HIGH/CRITICAL. Generate SBOM: `npx @cyclonedx/cyclonedx-npm --output-format json`.

**ESLint security config:**
```json
{ "plugins": ["security"],
  "rules": { "security/detect-non-literal-regexp": "error", "security/detect-unsafe-regex": "error" } }
```
