---
name: sast-configuration
description: Static Application Security Testing tool selection, configuration, CI/CD integration, secret scanning, dependency scanning, and shift-left deployment strategies.
origin: ECC
---

# SAST Configuration

Static Application Security Testing setup, tool selection, configuration patterns, and CI/CD shift-left strategies.

## When to Activate

- Implementing SAST scanning in CI/CD pipelines
- Evaluating SAST tools (Semgrep, SonarQube, CodeQL, language-specific)
- Configuring custom security rules for domain-specific patterns
- Managing false positives and suppression workflows
- Setting up secret scanning and dependency scanning
- Establishing shift-left scanning strategy (pre-commit, PR gate, nightly deep scan)

## Tool Selection

### Semgrep (Fast, Extensible)

**Best for:** Quick feedback, custom rules, CI/CD speed
- Pattern-based rules (regex-free, precise)
- Rule reuse across languages
- Pre-built rulesets: `p/security-audit`, `p/owasp-top-ten`, `p/cwe-top-25`
- Scans in seconds; cloud or self-hosted

### SonarQube (Comprehensive)

**Best for:** Enterprise, quality gates, PR decoration
- Deep semantic analysis
- Coverage-aware issue tracking (e.g., new issues only)
- Quality gates (prevent merge if severity threshold exceeded)
- False positive voting and resolution workflow

### CodeQL (Deep Semantic Analysis)

**Best for:** Complex vulnerabilities, high assurance
- Dataflow and taint analysis
- Database queries over AST
- Detects multi-step exploitation chains
- Slower (but highly accurate); GitHub Actions native integration

### Language-Specific Tools

- **Python:** Bandit (security), Pylint (lint)
- **Java:** SpotBugs (bytecode analysis), Checkstyle (style)
- **JavaScript:** ESLint with security plugins
- **Go:** gosec (security-focused)

---

## Semgrep Configuration

### Rule Syntax

```yaml
# Detect hardcoded credentials pattern
rules:
  - id: hardcoded-api-key
    pattern-either:
      - pattern: |
          const API_KEY = "sk-..."
      - pattern: |
          password = "..."
      - patterns:
          - pattern: api_key = $KEY
          - metavariable-pattern:
              metavariable: $KEY
              pattern: '.*".*".*'
    message: "Potential hardcoded API key detected"
    languages: [python, javascript, typescript]
    severity: CRITICAL

  # Detect SQL injection (parameterized queries missing)
  - id: sql-injection-risk
    pattern: |
      db.execute("SELECT * FROM users WHERE id = " + user_input)
    message: "SQL injection risk: use parameterized queries"
    languages: [python, javascript]
    severity: HIGH
    fix: |
      db.execute("SELECT * FROM users WHERE id = ?", [user_input])

  # Metavariable for reusable patterns
  - id: insecure-hash-md5
    pattern: |
      import hashlib
      hashlib.md5($VALUE)
    message: "MD5 is cryptographically broken; use SHA-256 instead"
    languages: [python]
    severity: MEDIUM
    fix: |
      hashlib.sha256($VALUE)
```

### Rulesets

```yaml
# .semgrep.yml at repo root
rules:
  - p/security-audit            # OWASP, CWE, injection, XSS
  - p/owasp-top-ten             # Top 10 web vulnerabilities
  - p/cwe-top-25                # CWE ranking by frequency
  - ./rules/custom-rules.yml    # Organization-specific rules
  - ./rules/api-patterns.yml    # API design enforcement
```

### .semgrepignore

```
# Semgrep ignore patterns
test/
tests/
*_test.go
*.spec.ts
**/mock*
**/__fixtures__/
vendor/
node_modules/
.venv/
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

### Gitleaks (Git History)

```bash
# Scan entire history
gitleaks detect --source="local" --verbose --report-format="json" --report-path="gitleaks-report.json"

# Pre-commit hook
gitleaks protect --staged

# CI/CD (fail on secrets found)
gitleaks detect --exit-code 1
```

### truffleHog (Deep Secret Detection)

```bash
# Scan local directory
trufflehog filesystem . --json --concurrency=4

# Scan GitHub org
trufflehog github --org=myorg --include-members --json

# CI/CD integration
trufflehog github --repo=myorg/myrepo --json | grep -q '"Verified": true' && exit 1
```

### Pre-Commit Hook Integration

```yaml
# .pre-commit-config.yaml
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

---

## Dependency Scanning

### OWASP Dependency-Check

```bash
# CLI scan
dependency-check --project="MyApp" --scan ./src --format="JSON" --out="./reports"

# Maven plugin
mvn org.owasp:dependency-check-maven:check

# Gradle plugin
./gradlew dependencyCheckAnalyze
```

### Snyk

```bash
# Install
npm install -g snyk

# Test dependencies
snyk test --severity-threshold=high

# Monitor (continuous)
snyk monitor

# CI/CD (fail on critical)
snyk test --severity-threshold=critical --fail-on=upgradable
```

### GitHub Dependabot + Policies

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    versioning-strategy: "increase"

  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

### CVSS Threshold Policy

```yaml
# Fail CI if dependencies have CVSS > 7.0
deps:
  - id: check-cvss
    entry: |
      snyk test --json | jq '.vulnerabilities[] | select(.cvssScore > 7.0)' | grep -q . && exit 1 || exit 0
```

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
          fetch-depth: 0  # Full history for baseline comparisons

      # Pre-commit: Fast checks only
      - name: Semgrep (fast rulesets)
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/owasp-top-ten
            p/security-audit
          generateSarif: true

      # PR gate: Full SAST
      - name: SonarCloud analysis
        uses: SonarSource/sonarcloud-github-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}

      # Dependencies
      - name: Dependency check
        uses: dependency-check/Dependency-Check_Action@main
        with:
          path: '.'
          format: 'JSON'
          args: >-
            -s .

      # Secrets
      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  upload-sarif:
    needs: sast
    runs-on: ubuntu-latest
    steps:
      - name: Upload SARIF to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'semgrep.sarif'
        if: always()
```

### Failing on Severity Thresholds

```yaml
# Fail job if CRITICAL or HIGH found
- name: Check SAST results
  run: |
    if grep -q '"severity": "CRITICAL"' semgrep-results.json; then
      echo "CRITICAL security issues found"
      exit 1
    fi
    if grep -q '"severity": "HIGH"' semgrep-results.json; then
      # Warn but don't fail (configurable by org policy)
      echo "⚠️ HIGH severity issues found - review required"
    fi
```

---

## False Positive Management

### Inline Suppression (Semgrep)

```python
# Python: nosemgrep comment
db.execute(f"SELECT * FROM users WHERE id = {user_id}")  # nosemgrep: python.sql-injection
```

### SonarQube Suppression

```java
// Java: @SuppressWarnings for tool-specific issues
@SuppressWarnings("squid:S2077")  // SQL injection false positive (parameterized)
public void query(String safeSql) {
    // ...
}
```

### Suppression Audit Trail

```yaml
# Track suppressions in suppressions.json
suppressions:
  - id: "sql-injection-001"
    severity: "HIGH"
    file: "src/db/queries.js"
    line: 42
    reason: "False positive: using parameterized queries with Sequelize ORM"
    approved_by: "security-team"
    date: "2025-03-15"
    expires: "2025-09-15"  # Re-evaluate periodically
```

---

## Shift-Left Strategy

### Pre-Commit (Fastest, Most Frequent)

```bash
# Runs on developer machine before commit
# Time budget: <5 seconds
gitleaks protect --staged
semgrep --config=p/owasp-top-ten --json src/  # Fast rules only
```

### Pull Request Gate (Full SAST, Moderate Time)

```bash
# Runs on PR creation/update
# Time budget: 2-5 minutes
# Blocks merge until resolved
semgrep scan --config=p/owasp-top-ten --config=p/cwe-top-25
sonarcloud analysis + quality gate
snyk test --severity-threshold=high
```

### Nightly Deep Scan (Comprehensive, Slow)

```bash
# Runs daily off-peak
# Time budget: unbounded
# Creates issues/alerts, doesn't block
codeql analysis (database generation)
full dependency audit (including transitive)
license compliance check
container image scanning (Trivy)
```

---

## Anti-Patterns

```yaml
Anti-Pattern 1: Scanning only main branch
Problem: Developers don't see issues until merge (too late to fix)
Fix: Scan every PR, provide immediate feedback

Anti-Pattern 2: No false-positive process
Problem: Alert fatigue; developers ignore results
Fix: Suppression workflow + re-evaluation triggers

Anti-Pattern 3: Blocking everything
Problem: Quality gate too strict; slows development
Fix: Risk-based thresholds (CRITICAL fails, HIGH warns, MEDIUM logs)

Anti-Pattern 4: Ignoring transitive dependencies
Problem: Supply chain risk; vulnerable nested dependencies
Fix: Full dependency tree scanning (Snyk, Dependency-Check)

Anti-Pattern 5: No secret scanning in pre-commit
Problem: Credentials leaked to git history permanently
Fix: gitleaks/trufflehog pre-commit hooks mandatory

Anti-Pattern 6: SAST not integrated with code review
Problem: Findings discussed but not tracked/resolved
Fix: Automatically comment on PR with findings, link to tracking

Anti-Pattern 7: Custom rules never written
Problem: Organization-specific risks not caught
Fix: Maintain custom Semgrep/SonarQube rules for domain threats

Anti-Pattern 8: One-time scanning
Problem: New vulnerabilities emerge; risk only decreases once
Fix: Continuous scanning + re-assessment policy
```

---

## Agent Support

Use **threat-modeling-expert** to design SAST integration aligned with system risk profile.

Use **owasp-top10-expert** to prioritize SAST rules by OWASP Top 10 categories.

---

## Skill References

**stride-analysis-patterns:** Threat enumeration and STRIDE matrix construction (informs custom SAST rules).

**sast-configuration** (this skill): Complete SAST setup and CI/CD integration.
