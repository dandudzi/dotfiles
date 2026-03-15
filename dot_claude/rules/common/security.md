# Security Guidelines

## Code-Level Security Checks

Before ANY commit, verify the changed code:
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] Content Security Policy (CSP) headers set on HTML responses
- [ ] Error messages don't leak sensitive data

## Architectural Security (verify when designing or reviewing systems)

- [ ] CSRF protection enabled on state-changing endpoints
- [ ] Authentication/authorization on all protected routes
- [ ] Rate limiting on public-facing endpoints
- [ ] CORS configured to restrict allowed origins

## Secret Management

- NEVER hardcode secrets in source code
- ALWAYS use environment variables or a secret manager
- Validate that required secrets are present at startup
- Rotate any secrets that may have been exposed

## Supply Chain Security

- Generate and maintain an SBOM (Software Bill of Materials) for production services
- Scan dependencies for CVEs in CI (`npm audit`, `pip-audit`, OWASP dependency-check)
- Pin dependency versions in lockfiles — never use floating ranges in production
- Use `dependency-manager` agent for CVE scanning and SBOM generation

## Security Response Protocol

If security issue found:
1. STOP immediately
2. Use **owasp-top10-expert** agent for vulnerability assessment
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review entire codebase for similar issues
