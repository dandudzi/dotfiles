---
name: security-guidelines
description: Cross-language security checklists, secret management, supply chain security, deserialization safety, and security response protocol. Use during code review, design, and security audits across all languages and frameworks.
origin: rules/common/security.md
model: sonnet
---

# Security Guidelines

Cross-language security patterns. See language-specific security skills for implementation details:
- **python-security** — Python-specific patterns (bandit, pip-audit, Pydantic validation)
- **springboot-security** — Java/Spring patterns (JNDI, XXE, Jackson, OWASP dependency-check)
- **sast-configuration** — TypeScript/JS patterns (ESLint security plugin, DOMPurify, Zod, prototype pollution)

## When to Activate

- Before any commit (code-level security checklist)
- During system design (architectural security checklist)
- When reviewing code for security issues
- When setting up CI/CD security scanning
- When a potential vulnerability is discovered

## Code-Level Security Checks

Before ANY commit, verify the changed code:
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML output)
- [ ] Content Security Policy (CSP) headers set on HTML responses
- [ ] Error messages don't leak sensitive data

## Architectural Security

Verify when designing or reviewing systems:
- [ ] CSRF protection enabled on state-changing endpoints
- [ ] Authentication/authorization on all protected routes
- [ ] Rate limiting on public-facing endpoints
- [ ] CORS configured to restrict allowed origins

## Secret Management

- NEVER hardcode secrets in source code
- ALWAYS use environment variables or a secret manager
- Validate that required secrets are present at startup — fail fast if missing
- Rotate any secrets that may have been exposed

```bash
# Validate at startup (all languages follow this pattern)
if not API_KEY:
    raise RuntimeError("API_KEY not configured")
```

## Supply Chain Security

- Generate and maintain an SBOM (Software Bill of Materials) for production services
- Scan dependencies for CVEs in CI:
  - Node.js: `npm audit --audit-level=high`
  - Python: `pip-audit` or `uvx uv-secure`
  - Java: OWASP Dependency-Check (`mvn dependency-check:check`)
- Pin dependency versions in lockfiles — never use floating ranges in production
- Use `dependency-manager` agent for CVE scanning and SBOM generation

## Deserialization Security

NEVER deserialize untrusted data without validation:
- Validate structure and types before deserializing (schema-first)
- Never use native object deserialization from untrusted sources (binary formats from external input)
- Prefer JSON with schema validation (Zod, Pydantic, Jakarta Validation) over binary serialization formats
- Allowlist expected types when deserialization is unavoidable

## Security Response Protocol

If a security issue is found:
1. **STOP** — do not continue the current work
2. Use **owasp-top10-expert** agent for vulnerability assessment
3. Fix CRITICAL issues before continuing any other work
4. Rotate any secrets that may have been exposed
5. Review the entire codebase for similar patterns

## Agent Support

- **owasp-top10-expert** — OWASP vulnerability assessment and classification
- **security-auditor** — Code review time security checks (before merge)
- **threat-modeling-expert** — Design time security (before implementation)

## Skill References

- **python-security** — Python-specific security implementation patterns
- **springboot-security** — Java/Spring security implementation patterns
- **sast-configuration** — TypeScript/JS security + SAST tool configuration
