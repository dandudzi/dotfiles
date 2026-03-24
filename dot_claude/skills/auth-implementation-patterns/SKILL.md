---
name: auth-implementation-patterns
description: Authentication and authorization patterns including OAuth2, OIDC, JWT, sessions, RBAC, and multi-tenancy across TypeScript, Python, and JavaScript frameworks.
origin: ECC
model: sonnet
---

# Authentication & Authorization Patterns

## When to Activate

- Selecting between sessions vs JWT vs opaque tokens
- Implementing OAuth2/OIDC flows
- Setting up RBAC and multi-tenancy

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

## OIDC (OpenID Connect)

ID Token contains user identity (sub, name, email, aud, iat, exp). Access Token authorizes API requests.

**Claims verification:**

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

```typescript
app.use(session({
  store: new RedisStore(),
  cookie: {
    httpOnly: true,        // Block JavaScript access
    secure: true,          // HTTPS only
    sameSite: 'strict',    // Prevent CSRF
    maxAge: 1000 * 60 * 60 * 24 // 24 hours
  }
}));

// Regenerate ID after login to prevent fixation
req.session.regenerate((err) => {
  if (err) return next(err);
  req.session.userId = user.id;
  res.redirect('/dashboard');
});
```

## JWT Patterns

Use RS256 (asymmetric) with short-lived access tokens (15m) + refresh tokens (30d).

### RS256 (Asymmetric)

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

Use role + permission model (not boolean flags). Enforce at middleware and resource level.

```typescript
interface User {
  roles: ['admin', 'editor', 'viewer'];
  permissions: ['post:read', 'post:write', 'post:delete'];
}

const rolePermissions = {
  admin: ['post:*', 'user:*'],
  editor: ['post:read', 'post:write'],
  viewer: ['post:read']
};

function requirePermission(permission: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user.permissions.includes(permission)) {
      return res.status(403).json({ error: 'Forbidden' });
    }
    next();
  };
}

app.post('/posts', requirePermission('post:write'), createPost);
```

**Resource-level check:**

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

Include tenantId in JWT claims. Enforce at middleware + database level.

```typescript
// Include tenant context in token
interface Token {
  sub: string;
  tenantId: string;
}

// Middleware validates tenant boundary
app.use((req, res, next) => {
  if (req.user.tenantId !== req.params.tenantId) {
    throw new ForbiddenException('Invalid tenant');
  }
  next();
});

// Database-level: PostgreSQL RLS
CREATE POLICY tenant_isolation ON posts
  USING (tenant_id = current_setting('app.current_tenant')::uuid);
SET app.current_tenant = '550e8400-e29b-41d4-a716-446655440000';
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

