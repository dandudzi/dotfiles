---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---
# TypeScript/JavaScript Security

> This file extends [common/security.md](../common/security.md) with TypeScript/JavaScript specific content.

## Secret Management

```typescript
// NEVER: Hardcoded secrets
const apiKey = "sk-proj-xxxxx"

// ALWAYS: Environment variables
const apiKey = process.env.OPENAI_API_KEY

if (!apiKey) {
  throw new Error('OPENAI_API_KEY not configured')
}
```

## XSS Prevention

- Never use `dangerouslySetInnerHTML` without sanitization
- Sanitize user-generated HTML with **DOMPurify** or **sanitize-html**
- Prefer text content over HTML injection

```typescript
import DOMPurify from 'dompurify'

// If HTML rendering is unavoidable, sanitize first
const clean = DOMPurify.sanitize(userInput)

// With Trusted Types API (modern browsers, CSP policy enforcement)
const clean = DOMPurify.sanitize(userInput, { RETURN_TRUSTED_TYPE: true })
```

Set a Content Security Policy header to restrict script sources and enable Trusted Types enforcement:
```
Content-Security-Policy: default-src 'self'; require-trusted-types-for 'script'
```

## Prototype Pollution

- Never use `Object.assign` or spread on untrusted input without validation
- Reject keys like `__proto__`, `constructor`, `prototype` from user input

```typescript
const FORBIDDEN_KEYS = new Set(['__proto__', 'constructor', 'prototype'])

function safeMerge<T extends Record<string, unknown>>(
  target: T,
  source: Record<string, unknown>
): T {
  const filtered = Object.fromEntries(
    Object.entries(source).filter(([key]) => !FORBIDDEN_KEYS.has(key))
  )
  return { ...target, ...filtered } as T
}
```

## Dependency Auditing

- Run `npm audit` or `pnpm audit` in CI pipelines
- Use `npm audit --audit-level=high` to fail on high/critical vulnerabilities
- Review and pin transitive dependencies when security-sensitive

## SBOM Generation

Generate a Software Bill of Materials for production services:

```bash
# CycloneDX SBOM (JSON format)
npx @cyclonedx/cyclonedx-npm --output-format json --output-file sbom.json

# or using syft
syft . -o cyclonedx-json > sbom.json
```

## Agent Support

- **owasp-top10-expert** — Security vulnerability assessment
- **typescript-expert** — Type-safe patterns to prevent runtime vulnerabilities
