---
name: stride-analysis-patterns
description: STRIDE threat enumeration, data flow diagram construction, threat categorization with concrete examples, DFD notation, risk scoring, and mitigation mapping.
origin: ECC
---

# STRIDE Analysis Patterns

STRIDE threat modeling, threat enumeration, DFD construction, risk scoring, and security control mapping for system security assessment.

## When to Activate

- Conducting threat modeling for new systems or architecture changes
- Enumerating threats for a specific component or data flow
- Building data flow diagrams (DFDs) with security boundaries
- Mapping security controls to threat categories
- Scoring threats using DREAD or CVSS methodologies
- Documenting assumptions and out-of-scope threats
- Establishing threat model review and update cadence

---

## STRIDE Categories with Examples

### Spoofing (False Identity)

**Threat:** Attacker impersonates a legitimate user or system.

**Web API Examples:**
- Session token theft → attacker acts as authenticated user
- JWT with `alg: none` → attacker forges token without signing
- Weak CORS validation → malicious site impersonates legitimate domain
- Domain spoofing → attacker registers `myapp-clone.com`

**Mitigations:**
- Multi-factor authentication (MFA) for login
- Secure session management (HttpOnly, Secure, SameSite cookies)
- JWT signature validation + algorithm pinning (disallow `alg: none`)
- Certificate pinning for API clients
- HTTPS only + HSTS headers
- CORS properly scoped to trusted origins
- Login audit logs + impossible travel detection

---

### Tampering (Unauthorized Modification)

**Threat:** Attacker modifies data in transit or at rest.

**Web API Examples:**
- MITM attack over HTTP → attacker intercepts and modifies request/response
- Unvalidated input → attacker changes `user_id=1` to `user_id=999` in URL
- Weak signing → attacker modifies JWT payload without detection
- Unsigned database backups → attacker restores modified data
- HTTP form submission → attacker changes price, quantity before POST

**Mitigations:**
- HTTPS (TLS 1.3+) mandatory for all endpoints
- Input validation (type, format, range, allowlist)
- Message signing (HMAC, JWT with RS256, request signatures)
- Database transaction logs + immutable audit trail
- Checksums for critical data (e.g., order total = sum(items))
- Code signing for deployments
- Read-only filesystem where applicable

---

### Repudiation (Deny Accountability)

**Threat:** Attacker denies performing an action; system lacks proof.

**Web API Examples:**
- User claims they never requested password reset (no audit trail)
- Attacker transfers funds, then claims account was hacked (no logs)
- Admin makes unauthorized changes (no who/when/what recorded)
- API endpoint modified without approval (no change tracking)

**Mitigations:**
- Structured audit logs (actor, action, resource, timestamp, IP, user-agent)
- Immutable audit trail (append-only, tamper-evident)
- Non-repudiation tokens (cryptographic proof of action)
- Digital signatures for critical transactions
- User consent logs (e.g., "User agreed to ToS on 2025-03-15 at 14:32 UTC")
- Email/SMS confirmations for sensitive operations
- Retention policy (logs kept for 7+ years in regulated industries)

---

### Information Disclosure (Exposure of Secrets)

**Threat:** Attacker gains access to sensitive data.

**Web API Examples:**
- Verbose error messages → stack trace leaks database schema
- IDOR (Insecure Direct Object Reference) → attacker accesses `/api/users/999` (other user)
- Path traversal → `GET /files/../../etc/passwd` leaks system files
- Exposed environment variables in logs
- GraphQL introspection enabled in production → schema leak
- S3 bucket publicly readable → attacker downloads all objects
- API responses include sensitive fields (SSN, credit card, password hash)

**Mitigations:**
- Input validation + path traversal prevention (regex allowlist)
- Authorization checks on EVERY endpoint (verify user owns resource)
- Generic error messages ("Not found" vs "User doesn't have permission to view this")
- No secrets in logs (redact API keys, tokens, PII)
- Encrypt sensitive data at rest (AES-256) and in transit (HTTPS)
- Minimal API responses (return only required fields)
- Disable GraphQL introspection in production
- S3 bucket policies: private + IAM-based access
- Database encryption; separate key management
- DLP (Data Loss Prevention) tools to detect exfiltration

---

### Denial of Service (DoS)

**Threat:** Attacker makes system unavailable to legitimate users.

**Web API Examples:**
- Unbounded query: `GET /api/users?limit=999999` exhausts database
- Regex ReDoS: `^(a+)+b$` on user input with 100 "a"s hangs CPU
- Slowloris attack: send incomplete HTTP requests slowly, hold connections
- Rate limiting missing → brute force password in seconds
- Billion laughs attack (XXE): deeply nested XML expands to huge size
- Distributed amplification: send small request that generates 1000x response

**Mitigations:**
- Rate limiting (per IP, per user, per API key)
- Request timeouts (connection, read, write)
- Pagination with max limits (e.g., `limit <= 1000`)
- Input size limits (max body, max query string, max file upload)
- Regex validation (avoid catastrophic backtracking; use regex tester)
- WAF (Web Application Firewall) rules for common attacks
- DDoS protection (Cloudflare, AWS Shield)
- Resource limits (CPU, memory per request)
- Circuit breaker (fail fast if backend saturated)
- Caching (reduce load on expensive operations)

---

### Elevation of Privilege (Unauthorized Escalation)

**Threat:** Attacker gains higher permissions than intended.

**Web API Examples:**
- IDOR + no authorization check → attacker modifies other user's profile
- JWT with `alg: none` → attacker creates forged admin token
- SQL injection in `WHERE` clause → bypass authorization logic
- Weak permission checks → attacker with "view" permission executes "delete"
- Path traversal in admin panel → attacker accesses restricted files
- SSRF → attacker forces server to access internal admin endpoints
- Race condition → attacker completes two actions before validation runs

**Mitigations:**
- RBAC (Role-Based Access Control) with explicit deny
- ABAC (Attribute-Based Access Control) for fine-grained rules
- JWT signature validation + `alg` pinning (reject `alg: none`)
- Parameterized queries (prevent SQL injection)
- Authorization middleware on every protected endpoint
- Least privilege (default deny, explicit allow)
- SSRF protection (allowlist internal IPs/domains, block metadata services)
- Idempotency tokens for critical operations (prevent race conditions)
- Separate authentication + authorization (verify identity, then permissions)
- Privilege separation (minimize code running as admin)

**SQL Injection Mitigation (Critical for Database Access):**
- Use parameterized queries / prepared statements (primary defense)
  - Java: `PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id = ?"); ps.setLong(1, userId);`
  - Python: `cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))`
  - Node.js: `db.query("SELECT * FROM users WHERE id = $1", [userId])`
- NEVER concatenate user input into SQL strings
- ORM as secondary layer (Hibernate, SQLAlchemy, Prisma) — still requires parameterized queries internally
- Validate input type/range before query execution (defense in depth)

---

## Threat Enumeration Template

### Component × STRIDE Matrix

Use this to systematically enumerate threats:

```
┌──────────────┬────────┬──────────┬────────┬─────────┬───┬──────┐
│ Component    │ Spoof  │ Tamper   │ Repud. │ Disclose│DoS│ Elevate
├──────────────┼────────┼──────────┼────────┼─────────┼───┼──────┤
│ API Gateway  │ Token  │ Request  │ No log │ Verbose │RRL│ JWT  │
│              │ forgery│ modif.   │        │ errors  │   │ alg  │
├──────────────┼────────┼──────────┼────────┼─────────┼───┼──────┤
│ Auth Service │ Brute  │ Hash     │ Audit  │ PII in  │ ─ │ Priv │
│              │ force  │ collision│ logs   │ logs    │   │ esc  │
├──────────────┼────────┼──────────┼────────┼─────────┼───┼──────┤
│ Database     │ Creds  │ SQL inj. │ No     │ IDOR    │Disk│ Query│
│              │ leak   │          │ query  │         │fill│ as  │
│              │        │          │ log    │         │    │ admin│
└──────────────┴────────┴──────────┴────────┴─────────┴───┴──────┘
```

---

## Data Flow Diagram (DFD) Notation

### DFD Symbols

```
┌─────────────────────────────────────────────────────┐
│ External Entity (untrusted source)                  │
│ Rectangle: User, Third-party API, Mobile Client    │
└─────────────────────────────────────────────────────┘

       ┌──────────────────────────────────┐
       │ Process (system logic)            │
       │ Circle: API Gateway, Auth Service│
       │ Database Handler, Cache Service   │
       └──────────────────────────────────┘

║║║║║║║║║║║║  Data Store (file, database, cache)
║ Users DB ║  Parallel lines
║║║║║║║║║║║║

─────────────────────→  Data Flow (labeled with data type)
← ─ ─ ─ ─ ─ ─ ─ ─ ─  (arrow shows direction)

╔════════════════════╗  Trust Boundary (dashed box)
║ Process A          ║  Separates trust levels:
║ ┌──────────────┐   ║  - Inside: trusted (own code)
║ │ Process B    │   ║  - Outside: untrusted (user input)
║ └──────────────┘   ║
╚════════════════════╝
```

### Example DFD: REST API + Database

```
        ┌─────────────────┐
        │  Mobile Client  │
        │  (Untrusted)    │
        └────────┬────────┘
                 │ HTTPS (JSON)
                 │
         ╔═══════▼═════════╗ Trust Boundary: Internet
         ║                 ║
    ┌────▼─────────────┐   ║
    │  API Gateway     │   ║  Rate limit, CORS
    │  (TLS, Authz)    │   ║  Route, log requests
    └────┬─────────────┘   ║
         │                 ║
         │ Parameterized   ║
         │ SQL + JWT       ║
    ┌────▼─────────────┐   ║
    │ Auth Service     │───╫─ Verify JWT, check RBAC
    │ + Biz Logic      │   ║
    └────┬─────────────┘   ║
         │                 ║
    ║║║║▼║║║║║║║║║║║║║   ║
    ║  PostgreSQL DB  ║   ║  Encrypted at rest
    ║ (Users, Orders) ║   ║  Read-only replicas
    ║║║║║║║║║║║║║║║║║║   ║
         │                 ║
         │ Audit trail     ║
    ║║║║▼║║║║║║║║║║║║║   ║
    ║ Audit Log DB   ║   ║  Immutable, append-only
    ║║║║║║║║║║║║║║║║║║   ║
         │                 ║
         │ Cached response ║
    ┌────▼─────────────┐   ║
    │  Redis Cache     │   ║  TTL, no secrets
    │  (In-memory)     │   ║
    └──────────────────┘   ║
         │                 ║
    ┌────▼─────────────┐   ║
    │  Admin Dashboard │   ║  Behind MFA
    │  (UI)            │   ║
    └──────────────────┘   ║
         │                 ║
    ║║║║▼║║║║║║║║║║║║║   ║
    ║ Log Aggregation ║   ║  Tamper-evident, signed
    ║ (for forensics) ║   ║
    ║║║║║║║║║║║║║║║║║║   ║
         │                 ║
         └────────────────╫─ Third-party SIEM
        ┌─────────────────┐║
        │   Splunk API    │║
        │   (Untrusted)   │║
        └─────────────────╫
                          ║
         ╚═══════════════════╝
```

---

## Risk Scoring: DREAD Methodology

### DREAD Score Formula

```
RISK SCORE = (Damage + Reproducibility + Exploitability + Affected + Discoverability) / 5

Scale: 1-10 for each dimension
Result: 1.0-10.0
  ≥ 8.0 = CRITICAL
  6.0-7.9 = HIGH
  4.0-5.9 = MEDIUM
  2.0-3.9 = LOW
  < 2.0 = INFORMATIONAL
```

### Scoring Dimensions

| Dimension | 10 = Worst | 7 = Bad | 4 = Medium | 1 = Minor |
|-----------|-----------|---------|-----------|----------|
| **Damage** | Full system compromise, data breach, $1M+ loss | Data loss, core service down | Partial data leak | Info leak only |
| **Reproducibility** | Always, trivial exploit | Often, simple steps | Sometimes, moderate effort | Rare, complex |
| **Exploitability** | Automated exploit available | Basic tools (curl, Burp) | Special tools/knowledge | Expert+academic |
| **Affected** | Entire user base | Large user segment | Specific user type | Single user |
| **Discoverability** | Public exploit, obvious | Security researchers know | Hidden, requires analysis | Requires source code |

### DREAD Scoring Example

```
Threat: SQL Injection in /api/users?name parameter

Damage: 10
  → Full database read access (all user PII exposed)
  → Potential write if DBMS privileges allow
  → Incident response, reputational damage, regulatory fines

Reproducibility: 10
  → 100% reliable: name=' OR '1'='1
  → Exploitable every request

Exploitability: 9
  → No authentication required (public endpoint)
  → Simple HTTP GET with payload
  → PoC available online

Affected: 10
  → All users' data exposed
  → All user sessions potentially compromised
  → Supply chain risk (downstream partners)

Discoverability: 10
  → Automated tools flag it immediately (SAST, WAF rules)
  → Manual testing obvious
  → Vulnerability databases list it

DREAD Score = (10 + 10 + 9 + 10 + 10) / 5 = 9.8 (CRITICAL)
Immediate action: Patch, reset session tokens, notify users
```

---

## Mitigation Mapping: STRIDE → Controls

### Security Controls Catalog

```
┌──────────────────────┬──────────────────────┬────────────────┐
│ STRIDE Category      │ Control Type         │ Examples       │
├──────────────────────┼──────────────────────┼────────────────┤
│ Spoofing             │ Authentication       │ MFA, certs,    │
│                      │ + Session mgmt       │ session tokens │
├──────────────────────┼──────────────────────┼────────────────┤
│ Tampering            │ Integrity controls   │ HTTPS, signing,│
│                      │                      │ message auth   │
├──────────────────────┼──────────────────────┼────────────────┤
│ Repudiation          │ Audit + Logging      │ Immutable logs,│
│                      │ + Non-repudiation    │ digital sigs   │
├──────────────────────┼──────────────────────┼────────────────┤
│ Information          │ Encryption +         │ TLS, field-    │
│ Disclosure           │ Access Control       │ level encrypt, │
│                      │ + Data Minimization  │ RBAC, ABAC     │
├──────────────────────┼──────────────────────┼────────────────┤
│ Denial of Service    │ Resource Limits +    │ Rate limit,    │
│                      │ Resilience           │ timeouts, WAF  │
├──────────────────────┼──────────────────────┼────────────────┤
│ Elevation of         │ Authorization +      │ JWT validation,│
│ Privilege            │ Privilege Separation │ RBAC, least    │
│                      │                      │ privilege      │
└──────────────────────┴──────────────────────┴────────────────┘
```

### Mitigation Example: IDOR Vulnerability

```
Threat: IDOR in GET /api/users/{user_id}
Impact: Attacker accesses /api/users/999 (other user's profile)

Control Implementation:

1. INPUT VALIDATION (preventive)
   if (!isValidUserId(userId)) {
     throw new ValidationError("Invalid user ID");
   }

2. AUTHORIZATION CHECK (critical)
   const requestingUser = getCurrentUser(context);
   const targetUser = await db.getUserById(userId);

   if (requestingUser.id !== targetUser.id && !requestingUser.isAdmin) {
     throw new ForbiddenError("Not authorized to access this user");
   }

3. AUDIT LOGGING (detective)
   auditLog.write({
     actor: requestingUser.id,
     action: "VIEW_PROFILE",
     resource: `user/${userId}`,
     timestamp: now(),
     ip: request.ip,
     allowed: true/false
   });

4. MONITORING (responsive)
   if (auditLog.countUnauthorizedAttempts(ip) > 10) {
     alertSecurityTeam(`Possible IDOR attack from ${ip}`);
     blockIp(ip);
   }
```

---

## DFD → Threat Enumeration Workflow

1. **Draw DFD** (entities, processes, stores, flows)
2. **Identify trust boundaries** (network perimeter, privilege boundary, data classification)
3. **For each component**, ask:
   - Can it be spoofed?
   - Can its data be tampered with?
   - Can actions be denied/logged?
   - Can information be disclosed?
   - Can it be DoS'd?
   - Can privilege be escalated?
4. **Score threats** (DREAD or CVSS)
5. **Map mitigations** (controls to threats)
6. **Document assumptions** (e.g., "All API traffic over HTTPS")
7. **Identify out-of-scope** (e.g., "Physical security of data center")

---

## Anti-Patterns

```yaml
Anti-Pattern 1: Skipping trust boundary analysis
Problem: Treats internal and external systems equally; misses attack surface
Fix: Explicitly identify and document every trust boundary

Anti-Pattern 2: No re-assessment after architecture changes
Problem: Threat model becomes stale; new risks undetected
Fix: Re-run STRIDE when adding services, APIs, integrations

Anti-Pattern 3: Treating threat model as one-time exercise
Problem: New threats emerge (zero-day, supply chain); static analysis fails
Fix: Quarterly/semi-annual review; continuous monitoring for threat feeds

Anti-Pattern 4: Mitigations without verification
Problem: Controls documented but not actually implemented/tested
Fix: Verify every mitigation in code + security tests

Anti-Pattern 5: No prioritization by risk
Problem: Fix everything equally; runs out of time/budget on low-risk items
Fix: Prioritize by DREAD/CVSS score; focus on critical/high first

Anti-Pattern 6: Threat model only in PowerPoint
Problem: Not integrated into architecture; developers ignore it
Fix: Link DFD to codebase; auto-flag violations in code review

Anti-Pattern 7: No assumptions documented
Problem: Future changes violate implicit security assumptions
Fix: Explicit assumptions list (e.g., "All users are authenticated")

Anti-Pattern 8: Ignoring supply chain threats
Problem: Dependencies, third-party APIs introduce risks
Fix: Include external systems in DFD; assess dependency risks
```

---

## Filled-In STRIDE Matrix Example

### Typical REST API + PostgreSQL System

```
┌────────────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ Component          │ Spoofing     │ Tampering    │ Repudiation  │ Disclosure   │ DoS          │ Elevation    │
├────────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ API Gateway        │ JWT forgery  │ MITM request │ Logs missing │ Verbose err  │ No rate      │ JWT alg:none │
│ (Port 443)         │ (alg:none)   │ (HTTP→HTTPS) │ (audit gap)  │ leaks schema │ limit        │ → admin token│
│ Score: 9.2 HIGH    │ Fix: Validate│ Fix: HTTPS   │ Fix: Audit   │ Fix: Generic │ Fix: RRL per │ Fix: Sign +  │
│ Status: ✓ Pending  │ signature    │ 1.3+ only    │ every req    │ errors       │ IP, user     │ verify       │
│                    │              │              │              │              │              │              │
├────────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Auth Service       │ Weak session │ Weak CORS    │ Login audit  │ Token in     │ Brute force  │ Priv escalation
│ (JWT generation)   │ management   │ validation   │ trail        │ logs         │ no limit     │ (auth bypass) │
│ Score: 8.5 CRITICAL│ Fix: HttpOnly│ Fix: Origin  │ Fix: Log who │ Fix: No token│ Fix: MFA,    │ Fix: RBAC +   │
│ Status: ✓ Fixed    │ Secure tokens│ allowlist    │ when where   │ in logs      │ rate limit   │ scope checks  │
│                    │              │              │              │              │              │              │
├────────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Database           │ Stolen creds │ SQL injection│ No query log │ IDOR (no     │ Unbounded    │ Query as DB  │
│ (PostgreSQL)       │ → connect as │ in filters   │              │ authz check) │ queries      │ admin user   │
│ Score: 9.8 CRITICAL│ admin        │ Fix: Prepared│ Fix: Immutable│ Fix: Authz   │ Fix: Pagination│ Fix: App-level
│ Status: ✓ Mitigated│ Fix: IAM + MFA│ statements   │ audit trail  │ middleware   │ query limits │ RBAC layer   │
│                    │              │              │              │              │              │              │
├────────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Cache (Redis)      │ Shared env   │ Unencrypted  │ Cache hits   │ Sensitive    │ Cache        │ Cache key    │
│ (session store)    │ key access   │ over network │ not logged   │ data in cache│ stampede     │ prefix spoof  │
│ Score: 7.3 HIGH    │ Fix: RBAC    │ Fix: TLS     │ Fix: Log     │ Fix: TTL,    │ Fix: Shedding│ Fix: Keying   │
│ Status: ✓ In Prog. │              │ + encryption │ cache access │ no PII      │ algorithm    │ strategy      │
│                    │              │              │              │              │              │              │
├────────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Logs (ELK Stack)   │ Log injection│ Unencrypted  │ Logs immutable│ PII in logs  │ Log flooding │ Log deletion  │
│ (Elasticsearch)    │ → fake events│ at rest      │ (integrity)  │ (GDPR risk)  │ → disk full  │ → forensics   │
│ Score: 6.7 MEDIUM  │ Fix: Input   │ Fix: EncAtRest│ Fix: Write-  │ Fix: Redact  │ Fix: Rotate  │ Fix: Write-only
│ Status: ✓ Planned  │ sanitization │ + RBAC       │ once         │ sensitive    │ logs         │ + audit trail │
│                    │              │              │              │              │              │              │
└────────────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘

Legend:
Score: DREAD score (1.0-10.0)
Status: ✓ Mitigated | ✓ In Progress | ✓ Planned | ⚠️ Accepted Risk | ✗ Unmitigated
```

---

## Agent Support

Use **threat-modeling-expert** to conduct comprehensive threat models for new systems or major architecture changes.

Use **owasp-top10-expert** to map STRIDE threats to OWASP Top 10 vulnerability categories.

---

## Skill References

**sast-configuration:** Configure SAST rules based on STRIDE findings.

**stride-analysis-patterns** (this skill): Threat enumeration, DFD construction, risk scoring.
