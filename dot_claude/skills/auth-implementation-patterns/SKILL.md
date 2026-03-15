---
name: auth-implementation-patterns
description: Authentication and authorization patterns including OAuth2, OIDC, JWT, sessions, RBAC, and multi-tenancy across TypeScript, Python, and JavaScript frameworks.
origin: ECC
---

# Authentication & Authorization Patterns

## When to Activate

- Selecting between sessions vs JWT vs opaque tokens
- Implementing OAuth2/OIDC flows
- Designing multi-tenant authentication
- Setting up NextAuth.js, Auth.js, or FastAPI auth
- Implementing role-based access control (RBAC)
- Handling token refresh and key rotation
- Preventing session fixation, CSRF, and token theft

## Auth Strategy Selection

**Decision matrix:**

| Strategy | Use Case | Pros | Cons |
|----------|----------|------|------|
| **Session Cookies** | Server-rendered apps, traditional monoliths | Simple, revocable, no client storage | Server state, CSRF risk, harder to scale |
| **JWT (Short-lived)** | SPAs, mobile apps, APIs | Stateless, scalable, cross-domain | Token theft via XSS, no instant revocation |
| **Opaque Tokens** | APIs, mobile, high security | Revocable, server-controlled, minimal data leak | Requires token validation on each request |
| **OAuth2 + PKCE** | Third-party logins, social auth | User convenience, delegated auth | Complex flow, dependency on provider |

**Recommendation**: Hybrid for modern web apps:
- **Backend-for-frontend (BFF)**: Session cookies for SPA + opaque refresh tokens
- **Mobile/native**: OAuth2 + PKCE → access token + refresh token
- **Microservices**: JWT with short expiry + refresh token family rotation

## OAuth2 Flows

### Authorization Code + PKCE (SPAs/Mobile)

```
Client → Auth Server: code_challenge, client_id, redirect_uri
         ↓
Auth Server → User: Login form
         ↓
User → Auth Server: Credentials
         ↓
Auth Server → Client: authorization_code
         ↓
Client → Auth Server: authorization_code, code_verifier, client_secret
         ↓
Auth Server → Client: access_token, refresh_token, id_token
```

**TypeScript (React + PKCE)**:

```typescript
import { generateCodeChallenge, generateCodeVerifier } from 'pkce';

const verifier = generateCodeVerifier();
const challenge = await generateCodeChallenge(verifier);

// Step 1: Redirect to auth server
window.location.href = `https://auth.example.com/authorize?` +
  `client_id=${CLIENT_ID}` +
  `&code_challenge=${challenge}` +
  `&code_challenge_method=S256` +
  `&redirect_uri=${REDIRECT_URI}`;

// Step 2: Handle callback
const code = new URLSearchParams(window.location.search).get('code');
const response = await fetch('https://auth.example.com/token', {
  method: 'POST',
  body: new URLSearchParams({
    code,
    code_verifier: verifier,
    client_id: CLIENT_ID,
    client_secret: CLIENT_SECRET,
    grant_type: 'authorization_code'
  })
});

const { access_token, refresh_token } = await response.json();
```

### Client Credentials (Machine-to-Machine)

```typescript
// No user involved, service-to-service auth
const response = await fetch('https://auth.example.com/token', {
  method: 'POST',
  body: new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: SERVICE_CLIENT_ID,
    client_secret: SERVICE_CLIENT_SECRET,
    scope: 'api:read api:write'
  })
});

const { access_token } = await response.json();
```

### Device Flow (Smart TVs, IoT)

```typescript
// Step 1: Request device code
const deviceResponse = await fetch('https://auth.example.com/device', {
  method: 'POST',
  body: new URLSearchParams({
    client_id: CLIENT_ID,
    scope: 'user:read'
  })
});
const { device_code, user_code, verification_uri } = await deviceResponse.json();

// Step 2: Display user_code to user, poll for token
const tokenResponse = await poll(
  'https://auth.example.com/token',
  {
    grant_type: 'urn:ietf:params:oauth:grant-type:device_code',
    device_code,
    client_id: CLIENT_ID
  },
  interval=5000
);
```

## OIDC (OpenID Connect)

**ID Token** (user identity): Contains user claims (sub, name, email, aud, iat, exp)
**Access Token** (API authorization): Bearer token for API requests
**UserInfo Endpoint**: Retrieve additional user details

**Claims mapping example:**

```typescript
// ID Token structure
interface IDToken {
  iss: string;       // Issuer (https://auth.example.com)
  sub: string;       // Subject (unique user ID)
  aud: string;       // Audience (client_id)
  iat: number;       // Issued at
  exp: number;       // Expiration
  auth_time: number; // Authentication time
  name: string;
  email: string;
  email_verified: boolean;
  custom_claims?: Record<string, any>;
}

// Verify and decode
import jwt from 'jsonwebtoken';

const decoded = jwt.verify(idToken, publicKey, {
  issuer: 'https://auth.example.com',
  audience: CLIENT_ID
});
```

## Session Management (Cookies)

**Secure cookie flags:**

```typescript
// Express.js example
app.use(session({
  store: new RedisStore(),
  cookie: {
    httpOnly: true,        // Not accessible via JavaScript
    secure: true,          // HTTPS only
    sameSite: 'strict',    // Prevent CSRF
    maxAge: 1000 * 60 * 60 * 24 // 24 hours
  }
}));
```

**Session fixation prevention:**

```typescript
// Regenerate session ID after login
req.session.regenerate((err) => {
  if (err) return next(err);
  req.session.userId = user.id;
  res.redirect('/dashboard');
});
```

## JWT Patterns

### Token Structure

```
header.payload.signature

header: { alg: "RS256", typ: "JWT" }
payload: { sub: "user123", role: "admin", exp: 1234567890 }
signature: HMACSHA256(header.payload, secret)
```

### RS256 (Asymmetric, Recommended)

```typescript
import jwt from 'jsonwebtoken';

// Issue token (use private key)
const token = jwt.sign(
  { sub: user.id, role: user.role },
  privateKey,
  {
    algorithm: 'RS256',
    expiresIn: '15m',
    issuer: 'https://auth.example.com'
  }
);

// Verify token (use public key, can be cached)
const decoded = jwt.verify(token, publicKey, {
  algorithms: ['RS256'],
  issuer: 'https://auth.example.com'
});
```

### Short-lived Access Token + Refresh Token

```typescript
// Access token: 15 minutes
const accessToken = jwt.sign(
  { sub: user.id, type: 'access' },
  privateKey,
  { expiresIn: '15m', algorithm: 'RS256' }
);

// Refresh token: 30 days (stored in secure HTTP-only cookie)
const refreshToken = jwt.sign(
  { sub: user.id, type: 'refresh', tokenFamily: uuid() },
  privateKey,
  { expiresIn: '30d', algorithm: 'RS256' }
);

// Client-side refresh flow
if (tokenExpired) {
  const newAccessToken = await fetch('/api/refresh', {
    method: 'POST',
    credentials: 'include' // Send refresh token cookie
  });
}
```

### Token Family Rotation (Detect Token Theft)

```typescript
// Server maintains token families
const tokenFamilies = new Map<string, { currentToken: string; rotationCount: number }>();

app.post('/api/refresh', (req, res) => {
  const { tokenFamily } = jwt.verify(refreshToken, publicKey);

  // Detect reuse of old refresh token
  if (tokenFamilies.get(tokenFamily)?.rotationCount > storedCount) {
    // Token was replayed; user was compromised
    await invalidateAllTokens(user.id);
    return res.status(401).json({ error: 'Token reuse detected' });
  }

  // Issue new token pair
  const newFamily = uuid();
  const newAccessToken = jwt.sign({ ...claims, tokenFamily: newFamily }, privateKey);
  const newRefreshToken = jwt.sign({ ...claims, tokenFamily: newFamily }, privateKey);

  tokenFamilies.set(newFamily, { currentToken: newRefreshToken, rotationCount: 0 });
  res.json({ accessToken: newAccessToken, refreshToken: newRefreshToken });
});
```

## NextAuth.js Setup

```typescript
// [...nextauth].ts
import NextAuth from 'next-auth';
import GithubProvider from 'next-auth/providers/github';
import CredentialsProvider from 'next-auth/providers/credentials';
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from '@/lib/db';

export const authOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    GithubProvider({
      clientId: process.env.GITHUB_ID!,
      clientSecret: process.env.GITHUB_SECRET!
    }),
    CredentialsProvider({
      async authorize(credentials) {
        const user = await prisma.user.findUnique({
          where: { email: credentials?.email }
        });
        if (!user) return null;

        const isValid = await bcrypt.compare(credentials!.password, user.password);
        return isValid ? { id: user.id, email: user.email } : null;
      }
    })
  ],
  session: { strategy: 'jwt' },
  callbacks: {
    jwt({ token, user }) {
      if (user) {
        token.sub = user.id;
        token.role = user.role;
      }
      return token;
    },
    session({ session, token }) {
      session.user.id = token.sub;
      session.user.role = token.role;
      return session;
    }
  }
};

export default NextAuth(authOptions);
```

## FastAPI Auth

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData(BaseModel):
    sub: str
    role: str

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["RS256"])
        user_id = payload.get("sub")
        role = payload.get("role")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return TokenData(sub=user_id, role=role)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = jwt.encode(
        {
            "sub": user.id,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(minutes=15)
        },
        SECRET_KEY,
        algorithm="RS256"
    )
    return {"access_token": token, "token_type": "bearer"}

@app.get("/protected")
async def protected_route(current_user: TokenData = Depends(get_current_user)):
    return {"user_id": current_user.sub, "role": current_user.role}
```

## RBAC (Role-Based Access Control)

**Granular roles:**

```typescript
// Don't: Boolean flags
user.isAdmin, user.canWrite

// Do: Role-based with permissions
interface User {
  roles: ['admin', 'editor', 'viewer'];
  permissions: ['post:read', 'post:write', 'post:delete', 'user:manage'];
}

// Permission mapping
const rolePermissions = {
  admin: ['post:*', 'user:*', 'settings:*'],
  editor: ['post:read', 'post:write'],
  viewer: ['post:read']
};

// Middleware
function requirePermission(permission: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as User;
    if (!user.permissions.includes(permission)) {
      return res.status(403).json({ error: 'Forbidden' });
    }
    next();
  };
}

app.post('/posts', requirePermission('post:write'), createPost);
```

**Resource-level authorization:**

```typescript
@Post('/posts/:id/publish')
@RequirePermission('post:publish')
async publishPost(@Param('id') id: string, @Req() req) {
  const post = await Post.findById(id);

  // Check ownership or org membership
  if (post.authorId !== req.user.id && !req.user.isOrgAdmin) {
    throw new ForbiddenException('Cannot publish this post');
  }

  return post.publish();
}
```

## Multi-Tenancy

**Tenant isolation in JWT claims:**

```typescript
interface Token {
  sub: string;      // user ID
  tenantId: string; // tenant/organization ID
  iat: number;
  exp: number;
}

// Middleware enforces tenant boundary
app.use((req, res, next) => {
  const token = req.user as Token;
  const requestedTenantId = req.params.tenantId;

  if (token.tenantId !== requestedTenantId) {
    throw new ForbiddenException('Invalid tenant');
  }
  next();
});
```

**Row-level security (Database):**

```sql
-- PostgreSQL RLS example
CREATE POLICY tenant_isolation ON posts
  USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- Before query, set tenant context
SET app.current_tenant = '550e8400-e29b-41d4-a716-446655440000';
SELECT * FROM posts; -- Only returns rows for this tenant
```

**Subdomain routing:**

```typescript
// auth.example.com → tenant A
// acme.example.com → tenant B

app.use((req, res, next) => {
  const subdomain = req.subdomains[0];
  const tenant = await Tenant.findBySubdomain(subdomain);
  req.tenantId = tenant.id;
  next();
});
```

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| **Storing tokens in localStorage** | XSS vulnerability exposes token | Use HTTP-only cookies + refresh token rotation |
| **Long-lived JWTs without revocation** | Compromised token active until expiry | Use short-lived tokens (15m) + refresh tokens |
| **No PKCE for public clients** | Authorization code interception attack | Always use PKCE for SPAs, mobile apps |
| **Storing secrets in JWT** | Token can be decoded by client | Use opaque tokens for sensitive data |
| **No token family rotation** | Cannot detect token theft | Implement family rotation + sudden rotation = reset all tokens |
| **Session without HttpOnly flag** | JavaScript can steal session cookie | Set `httpOnly: true` on all auth cookies |
| **Hardcoded JWT secrets** | Compromise exposes all tokens | Use environment variables + key rotation strategy |
| **No expiry on ID tokens** | Token usable indefinitely | Set `exp` claim, verify expiry on every request |

## Agent Support

- **oauth-oidc-expert**: Delegated auth and provider setup
- **nodejs-expert**: Node.js/Express session patterns
- **react-expert**: SPA auth flows and token refresh

## Skill References

- None yet
