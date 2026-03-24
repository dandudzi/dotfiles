---
name: api-design-rest
description: Design robust REST APIs with resource-oriented architecture, proper HTTP semantics, pagination, filtering, and production-ready patterns including rate limiting and security headers.
model: sonnet
---

# REST API Design

> **Scope**: HTTP semantics, resource modeling, status codes, pagination, and filtering.
> For service layer patterns (auth, rate limiting, middleware, logging), see `backend-api-patterns` skill.

Build intuitive, scalable REST APIs using resource-oriented principles and HTTP semantics.

## When to Use This Skill

- Designing new REST APIs
- Reviewing REST API specifications
- Establishing REST standards for your team
- Optimizing existing REST endpoints
- Implementing pagination, filtering, and rate limiting

## Core Principles

### Resource-Oriented Architecture

- Resources are nouns (users, orders, products), not verbs
- Use HTTP methods for actions (GET, POST, PUT, PATCH, DELETE)
- URLs represent resource hierarchies
- Consistent naming conventions (plural: `/users`, not `/user`)

**HTTP Methods:**
- `GET`: Retrieve resources (idempotent, safe)
- `POST`: Create new resources
- `PUT`: Replace entire resource (idempotent)
- `PATCH`: Partial resource updates
- `DELETE`: Remove resources (idempotent)

## Resource Collection Design

```python
# Good: Resource-oriented endpoints
GET    /api/users              # List users (with pagination)
POST   /api/users              # Create user
GET    /api/users/{id}         # Get specific user
PUT    /api/users/{id}         # Replace user
PATCH  /api/users/{id}         # Update user fields
DELETE /api/users/{id}         # Delete user

# Nested resources
GET    /api/users/{id}/orders  # Get user's orders
POST   /api/users/{id}/orders  # Create order for user

# Bad: Action-oriented endpoints (avoid)
POST   /api/createUser
POST   /api/getUserById
POST   /api/deleteUser
```

## API Versioning

Choose a versioning strategy and commit to it from day one.

**URL Versioning:**
```
/api/v1/users
/api/v2/users
```

**Header Versioning:**
```
Accept: application/vnd.api+json; version=1
```

**Query Parameter Versioning:**
```
/api/users?version=1
```

## Pagination and Filtering

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int
    pages: int

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1

# FastAPI endpoint
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/api/users", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    query = build_query(status=status, search=search)
    total = await count_users(query)
    offset = (page - 1) * page_size
    users = await fetch_users(query, limit=page_size, offset=offset)

    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )
```

## Error Handling and Status Codes

```python
from fastapi import HTTPException, status
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: str

# Key status codes
STATUS_CODES = {
    "success": 200,
    "created": 201,
    "no_content": 204,
    "bad_request": 400,
    "unauthorized": 401,
    "forbidden": 403,
    "not_found": 404,
    "conflict": 409,
    "unprocessable": 422,
    "internal_error": 500
}

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    user = await fetch_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"User {user_id} not found"}
        )
    return user
```

## HATEOAS (Hypermedia as the Engine of Application State)

Include links in responses to guide clients to related resources.

```python
class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    _links: dict

    @classmethod
    def from_user(cls, user: User, base_url: str):
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            _links={
                "self": {"href": f"{base_url}/api/users/{user.id}"},
                "orders": {"href": f"{base_url}/api/users/{user.id}/orders"},
                "update": {"href": f"{base_url}/api/users/{user.id}", "method": "PATCH"},
                "delete": {"href": f"{base_url}/api/users/{user.id}", "method": "DELETE"}
            }
        )
```

## Rate Limiting

Protect your API from abuse with rate limits and proper headers.

```
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000

# When exceeded
HTTP/1.1 429 Too Many Requests
Retry-After: 60
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Try again in 60 seconds."
  }
}
```

**Rate Limit Tiers:**

| Tier | Limit | Window | Use Case |
|------|-------|--------|----------|
| Anonymous | 30/min | Per IP | Public endpoints |
| Authenticated | 100/min | Per user | Standard API access |
| Premium | 1000/min | Per API key | Paid API plans |
| Internal | 10000/min | Per service | Service-to-service |

## Cursor-Based Pagination (Scalable)

Use cursor-based pagination for large datasets to avoid performance issues.

```sql
-- SQL implementation
SELECT * FROM users
WHERE id > :cursor_id
ORDER BY id ASC
LIMIT 21;  -- fetch one extra to determine has_next
```

```json
{
  "data": [
    { "id": "abc-123", "name": "Alice" },
    { "id": "def-456", "name": "Bob" }
  ],
  "meta": {
    "has_next": true,
    "next_cursor": "eyJpZCI6MTQzfQ"
  }
}
```

**Advantages:** Consistent O(1) performance regardless of position, stable with concurrent inserts

**Trade-offs:** Cannot jump to arbitrary page, cursor is opaque

**When to use:** Large datasets, infinite scroll, feeds (primary choice for public APIs)

## Filtering, Sorting, and Search

Query parameters enable powerful data selection without creating multiple endpoints.

**Filtering Patterns:**
```
# Simple equality
GET /api/v1/orders?status=active&customer_id=abc-123

# Comparison operators (bracket notation)
GET /api/v1/products?price[gte]=10&price[lte]=100
GET /api/v1/orders?created_at[after]=2025-01-01

# Multiple values (comma-separated)
GET /api/v1/products?category=electronics,clothing

# Nested fields (dot notation)
GET /api/v1/orders?customer.country=US
```

**Sorting:**
```
# Single field (prefix - for descending)
GET /api/v1/products?sort=-created_at

# Multiple fields
GET /api/v1/products?sort=-featured,price,-created_at
```

**Search:**
```
GET /api/v1/articles?search=kubernetes%20migration

Response includes relevance:
{
  "data": [
    { "id": "1", "title": "Kubernetes Migration Guide", "relevance": 0.95 }
  ]
}
```

## Security Headers and CORS

Secure your API with explicit CORS configuration and security headers.

**CORS Configuration:**
```javascript
// Restrict origins explicitly, never use wildcard in production
const corsOptions = {
  origin: ['https://example.com', 'https://app.example.com'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  maxAge: 86400 // 24 hours
};

app.use(cors(corsOptions));
```

**Security Headers:**
```javascript
// Enforce HTTPS in production
if (process.env.NODE_ENV === "production" && !req.secure) {
  return res.redirect(`https://${req.hostname}${req.url}`);
}

// Set security headers
res.set({
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'X-Frame-Options': 'DENY',
  'X-Content-Type-Options': 'nosniff',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin'
});
```

## Best Practices

1. **Consistent Naming**: Use plural nouns for collections
2. **Stateless Requests**: Each request contains all necessary information
3. **Status Codes**: Use 2xx for success, 4xx for client errors, 5xx for server errors
4. **Plan Versioning**: Plan for breaking changes from day one
5. **Always Paginate**: Paginate large collections with sensible defaults
6. **Document APIs**: Use OpenAPI/Swagger for interactive documentation
7. **Input Validation**: Validate all inputs at schema and application levels
8. **Prevent N+1**: Use joins or DataLoaders for relationships
9. **Cache Appropriately**: Set Cache-Control and ETag headers
10. **Monitor Thoroughly**: Log all requests, track error rates, alert on anomalies

## Common Pitfalls

- **Breaking Changes**: Version from day one or use deprecation strategies
- **Inconsistent Error Formats**: Standardize all error responses
- **Missing Rate Limits**: Unprotected APIs are vulnerable to abuse
- **Poor HTTP Semantics**: POST for idempotent operations breaks client expectations
- **Tight Coupling**: Don't mirror your database schema in the API
- **Over-nesting**: Avoid resource hierarchies deeper than 2 levels
- **No Pagination**: Unbounded collections cause client timeouts and memory issues
