---
name: api-design-principles
description: Master REST and GraphQL API design principles to build intuitive, scalable, and maintainable APIs that delight developers. Use when designing new APIs, reviewing API specifications, or establishing API design standards.
---

# API Design Principles

Master REST and GraphQL API design principles to build intuitive, scalable, and maintainable APIs that delight developers and stand the test of time.

## When to Use This Skill

- Designing new REST or GraphQL APIs
- Refactoring existing APIs for better usability
- Establishing API design standards for your team
- Reviewing API specifications before implementation
- Migrating between API paradigms (REST to GraphQL, etc.)
- Creating developer-friendly API documentation
- Optimizing APIs for specific use cases (mobile, third-party integrations)

## Core Concepts

### 1. RESTful Design Principles

**Resource-Oriented Architecture**

- Resources are nouns (users, orders, products), not verbs
- Use HTTP methods for actions (GET, POST, PUT, PATCH, DELETE)
- URLs represent resource hierarchies
- Consistent naming conventions

**HTTP Methods Semantics:**

- `GET`: Retrieve resources (idempotent, safe)
- `POST`: Create new resources
- `PUT`: Replace entire resource (idempotent)
- `PATCH`: Partial resource updates
- `DELETE`: Remove resources (idempotent)

### 2. GraphQL Design Principles

**Schema-First Development**

- Types define your domain model
- Queries for reading data
- Mutations for modifying data
- Subscriptions for real-time updates

**Query Structure:**

- Clients request exactly what they need
- Single endpoint, multiple operations
- Strongly typed schema
- Introspection built-in

### 3. API Versioning Strategies

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

## REST API Design Patterns

### Pattern 1: Resource Collection Design

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

### Pattern 2: Pagination and Filtering

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

class FilterParams(BaseModel):
    status: Optional[str] = None
    created_after: Optional[str] = None
    search: Optional[str] = None

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

# FastAPI endpoint example
from fastapi import FastAPI, Query, Depends

app = FastAPI()

@app.get("/api/users", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    # Apply filters
    query = build_query(status=status, search=search)

    # Count total
    total = await count_users(query)

    # Fetch page
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

### Pattern 3: Error Handling and Status Codes

```python
from fastapi import HTTPException, status
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: str
    path: str

class ValidationErrorDetail(BaseModel):
    field: str
    message: str
    value: Any

# Consistent error responses
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

def raise_not_found(resource: str, id: str):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": "NotFound",
            "message": f"{resource} not found",
            "details": {"id": id}
        }
    )

def raise_validation_error(errors: List[ValidationErrorDetail]):
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": {"errors": [e.dict() for e in errors]}
        }
    )

# Example usage
@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    user = await fetch_user(user_id)
    if not user:
        raise_not_found("User", user_id)
    return user
```

### Pattern 4: HATEOAS (Hypermedia as the Engine of Application State)

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
                "update": {
                    "href": f"{base_url}/api/users/{user.id}",
                    "method": "PATCH"
                },
                "delete": {
                    "href": f"{base_url}/api/users/{user.id}",
                    "method": "DELETE"
                }
            }
        )
```

## GraphQL Design Patterns

### Pattern 1: Schema Design

```graphql
# schema.graphql

# Clear type definitions
type User {
  id: ID!
  email: String!
  name: String!
  createdAt: DateTime!

  # Relationships
  orders(first: Int = 20, after: String, status: OrderStatus): OrderConnection!

  profile: UserProfile
}

type Order {
  id: ID!
  status: OrderStatus!
  total: Money!
  items: [OrderItem!]!
  createdAt: DateTime!

  # Back-reference
  user: User!
}

# Pagination pattern (Relay-style)
type OrderConnection {
  edges: [OrderEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type OrderEdge {
  node: Order!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# Enums for type safety
enum OrderStatus {
  PENDING
  CONFIRMED
  SHIPPED
  DELIVERED
  CANCELLED
}

# Custom scalars
scalar DateTime
scalar Money

# Query root
type Query {
  user(id: ID!): User
  users(first: Int = 20, after: String, search: String): UserConnection!

  order(id: ID!): Order
}

# Mutation root
type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(input: UpdateUserInput!): UpdateUserPayload!
  deleteUser(id: ID!): DeleteUserPayload!

  createOrder(input: CreateOrderInput!): CreateOrderPayload!
}

# Input types for mutations
input CreateUserInput {
  email: String!
  name: String!
  password: String!
}

# Payload types for mutations
type CreateUserPayload {
  user: User
  errors: [Error!]
}

type Error {
  field: String
  message: String!
}
```

### Pattern 2: Resolver Design

```python
from typing import Optional, List
from ariadne import QueryType, MutationType, ObjectType
from dataclasses import dataclass

query = QueryType()
mutation = MutationType()
user_type = ObjectType("User")

@query.field("user")
async def resolve_user(obj, info, id: str) -> Optional[dict]:
    """Resolve single user by ID."""
    return await fetch_user_by_id(id)

@query.field("users")
async def resolve_users(
    obj,
    info,
    first: int = 20,
    after: Optional[str] = None,
    search: Optional[str] = None
) -> dict:
    """Resolve paginated user list."""
    # Decode cursor
    offset = decode_cursor(after) if after else 0

    # Fetch users
    users = await fetch_users(
        limit=first + 1,  # Fetch one extra to check hasNextPage
        offset=offset,
        search=search
    )

    # Pagination
    has_next = len(users) > first
    if has_next:
        users = users[:first]

    edges = [
        {
            "node": user,
            "cursor": encode_cursor(offset + i)
        }
        for i, user in enumerate(users)
    ]

    return {
        "edges": edges,
        "pageInfo": {
            "hasNextPage": has_next,
            "hasPreviousPage": offset > 0,
            "startCursor": edges[0]["cursor"] if edges else None,
            "endCursor": edges[-1]["cursor"] if edges else None
        },
        "totalCount": await count_users(search=search)
    }

@user_type.field("orders")
async def resolve_user_orders(user: dict, info, first: int = 20) -> dict:
    """Resolve user's orders (N+1 prevention with DataLoader)."""
    # Use DataLoader to batch requests
    loader = info.context["loaders"]["orders_by_user"]
    orders = await loader.load(user["id"])

    return paginate_orders(orders, first)

@mutation.field("createUser")
async def resolve_create_user(obj, info, input: dict) -> dict:
    """Create new user."""
    try:
        # Validate input
        validate_user_input(input)

        # Create user
        user = await create_user(
            email=input["email"],
            name=input["name"],
            password=hash_password(input["password"])
        )

        return {
            "user": user,
            "errors": []
        }
    except ValidationError as e:
        return {
            "user": None,
            "errors": [{"field": e.field, "message": e.message}]
        }
```

### Pattern 3: DataLoader (N+1 Problem Prevention)

```python
from aiodataloader import DataLoader
from typing import List, Optional

class UserLoader(DataLoader):
    """Batch load users by ID."""

    async def batch_load_fn(self, user_ids: List[str]) -> List[Optional[dict]]:
        """Load multiple users in single query."""
        users = await fetch_users_by_ids(user_ids)

        # Map results back to input order
        user_map = {user["id"]: user for user in users}
        return [user_map.get(user_id) for user_id in user_ids]

class OrdersByUserLoader(DataLoader):
    """Batch load orders by user ID."""

    async def batch_load_fn(self, user_ids: List[str]) -> List[List[dict]]:
        """Load orders for multiple users in single query."""
        orders = await fetch_orders_by_user_ids(user_ids)

        # Group orders by user_id
        orders_by_user = {}
        for order in orders:
            user_id = order["user_id"]
            if user_id not in orders_by_user:
                orders_by_user[user_id] = []
            orders_by_user[user_id].append(order)

        # Return in input order
        return [orders_by_user.get(user_id, []) for user_id in user_ids]

# Context setup
def create_context():
    return {
        "loaders": {
            "user": UserLoader(),
            "orders_by_user": OrdersByUserLoader()
        }
    }
```

## Best Practices

### REST APIs

1. **Consistent Naming**: Use plural nouns for collections (`/users`, not `/user`)
2. **Stateless**: Each request contains all necessary information
3. **Use HTTP Status Codes Correctly**: 2xx success, 4xx client errors, 5xx server errors
4. **Version Your API**: Plan for breaking changes from day one
5. **Pagination**: Always paginate large collections
6. **Rate Limiting**: Protect your API with rate limits
7. **Documentation**: Use OpenAPI/Swagger for interactive docs

### GraphQL APIs

1. **Schema First**: Design schema before writing resolvers
2. **Avoid N+1**: Use DataLoaders for efficient data fetching
3. **Input Validation**: Validate at schema and resolver levels
4. **Error Handling**: Return structured errors in mutation payloads
5. **Pagination**: Use cursor-based pagination (Relay spec)
6. **Deprecation**: Use `@deprecated` directive for gradual migration
7. **Monitoring**: Track query complexity and execution time


## Production API Patterns

Production APIs require robust implementations of rate limiting, pagination, filtering, and comprehensive design checklists.

### Rate Limiting

Rate limiting protects your API from abuse and ensures fair resource distribution.

#### Implementation with Headers

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

#### Rate Limit Tiers

| Tier | Limit | Window | Use Case |
|------|-------|--------|----------|
| Anonymous | 30/min | Per IP | Public endpoints |
| Authenticated | 100/min | Per user | Standard API access |
| Premium | 1000/min | Per API key | Paid API plans |
| Internal | 10000/min | Per service | Service-to-service |

### Advanced Pagination Patterns

While offset-based pagination suits small datasets, cursor-based pagination scales to large collections.

#### Cursor-Based Implementation (Scalable)

```sql
-- SQL implementation for cursor-based pagination
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

**Advantages:** Consistent performance regardless of position, stable with concurrent inserts
**Trade-offs:** Cannot jump to arbitrary page, cursor is opaque

#### Pagination Selection Guide

| Use Case | Recommended |
|----------|-------------|
| Admin dashboards, small datasets (<10K) | Offset-based |
| Infinite scroll, feeds, large datasets | Cursor-based |
| Public APIs | Cursor-based (primary) with offset (optional) |
| Search results | Offset-based (users expect page numbers) |

### Filtering, Sorting, and Search

Query parameters enable powerful data selection without creating multiple endpoints.

#### Filtering Patterns

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

#### Sorting

```
# Single field (prefix - for descending)
GET /api/v1/products?sort=-created_at

# Multiple fields (comma-separated)
GET /api/v1/products?sort=-featured,price,-created_at
```

#### Full-Text Search

```
# Search query parameter
GET /api/v1/articles?search=kubernetes%20migration

# Response includes relevance score (optional)
{
  "data": [
    { "id": "1", "title": "Kubernetes Migration Guide", "relevance": 0.95 }
  ]
}
```

### Security Headers and CORS

Secure your API with proper headers and CORS configuration.

#### CORS Configuration

```javascript
// Restrict CORS origins explicitly, never use wildcard in production
const corsOptions = {
  origin: ['https://example.com', 'https://app.example.com'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  maxAge: 86400 // 24 hours
};

app.use(cors(corsOptions));
```

#### Security Headers

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

### API Design Checklist

Use this comprehensive checklist when designing and implementing production APIs.

#### REST API Design

##### Resource Design
- [ ] Resources are nouns, not verbs
- [ ] Plural names for collections (`/users`, not `/user`)
- [ ] Consistent naming across all endpoints
- [ ] Clear resource hierarchy (avoid deep nesting >2 levels)
- [ ] All CRUD operations properly mapped to HTTP methods
- [ ] Kebab-case or snake_case used consistently in URLs

##### HTTP Methods & Status Codes
- [ ] GET for retrieval (safe, idempotent)
- [ ] POST for creation
- [ ] PUT for full replacement (idempotent)
- [ ] PATCH for partial updates
- [ ] DELETE for removal (idempotent)
- [ ] 200 OK for successful GET/PATCH/PUT
- [ ] 201 Created for POST (with Location header)
- [ ] 204 No Content for DELETE
- [ ] 400 Bad Request for malformed requests
- [ ] 401 Unauthorized for missing authentication
- [ ] 403 Forbidden for insufficient permissions
- [ ] 404 Not Found for missing resources
- [ ] 409 Conflict for duplicate/state conflicts
- [ ] 422 Unprocessable Entity for validation errors
- [ ] 429 Too Many Requests for rate limiting
- [ ] 500 Internal Server Error for server issues
- [ ] 503 Service Unavailable with Retry-After header

##### Pagination & Data Retrieval
- [ ] All collection endpoints paginated
- [ ] Default page size defined (e.g., 20 items)
- [ ] Maximum page size enforced (e.g., 100 items)
- [ ] Pagination metadata included (total, pages, etc.)
- [ ] Cursor-based or offset-based pattern chosen appropriately
- [ ] Filtering implemented with query parameters
- [ ] Sort parameter supported
- [ ] Search parameter for full-text search
- [ ] Sparse fieldsets supported (return only requested fields)
- [ ] Include/embed parameters for related data

##### Response Format
- [ ] Consistent envelope format (data wrapper)
- [ ] Error responses follow standard format
- [ ] Field-level validation errors detailed
- [ ] Error codes provided for programmatic handling
- [ ] Timestamps included in error responses
- [ ] Consistent field naming (camelCase or snake_case)
- [ ] No internal details leaked (stack traces, SQL errors)

##### Versioning
- [ ] Versioning strategy defined (URL path, header, or query)
- [ ] Version included in all endpoints
- [ ] Deprecation policy documented
- [ ] Sunset header included for deprecated endpoints
- [ ] Graceful migration path for breaking changes

##### Authentication & Authorization
- [ ] Authentication method defined (Bearer token, API key, etc.)
- [ ] Authorization checks on all protected endpoints
- [ ] 401 vs 403 used correctly
- [ ] Token expiration handled appropriately
- [ ] Resource-level authorization (user can only access own data)
- [ ] Role-based authorization where applicable

##### Security
- [ ] Input validation on all fields (schema-level)
- [ ] Input sanitization at application level
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (never return unsanitized HTML)
- [ ] CORS configured to restrict origins (not wildcard)
- [ ] HTTPS enforced in production
- [ ] Strict-Transport-Security header set
- [ ] X-Frame-Options header set to DENY
- [ ] X-Content-Type-Options header set to nosniff
- [ ] No hardcoded secrets in code or responses
- [ ] No sensitive data in URLs or error messages
- [ ] Rate limiting implemented
- [ ] Rate limit headers included (RateLimit-Limit, RateLimit-Remaining, etc.)

##### Documentation
- [ ] OpenAPI/Swagger spec generated and current
- [ ] All endpoints documented with examples
- [ ] Request/response examples provided
- [ ] Error responses documented
- [ ] Authentication flow documented
- [ ] Rate limits documented
- [ ] Status codes for each endpoint documented
- [ ] Deprecated endpoints clearly marked

##### Performance
- [ ] Database queries optimized (no full table scans)
- [ ] N+1 queries prevented (use joins or DataLoaders)
- [ ] Caching strategy defined
- [ ] Cache headers set appropriately (Cache-Control, ETag)
- [ ] Large responses paginated
- [ ] Response compression enabled (gzip)
- [ ] Unused fields removed from responses
- [ ] Heavy endpoints have timeouts

##### Monitoring & Observability
- [ ] Logging implemented for all requests
- [ ] Error tracking configured (Sentry, Rollbar, etc.)
- [ ] Performance metrics collected (response time, errors)
- [ ] Health check endpoint available
- [ ] Alerts configured for error rates
- [ ] Slow query alerts configured
- [ ] 5xx error rates monitored
- [ ] Rate limit breaches monitored

##### Testing
- [ ] Unit tests for business logic (80%+ coverage)
- [ ] Integration tests for endpoints
- [ ] Error scenarios tested (4xx, 5xx responses)
- [ ] Edge cases covered (empty results, large payloads)
- [ ] Performance tests for heavy endpoints
- [ ] Load testing completed for production
- [ ] Contract tests with API clients
- [ ] Security tests (SQL injection, XSS, etc.)

#### GraphQL API Design

##### Schema Design
- [ ] Schema-first approach used
- [ ] Types properly defined with clear names
- [ ] Non-null vs nullable fields decided (`!` used appropriately)
- [ ] Interfaces/unions used for polymorphism
- [ ] Custom scalars defined (DateTime, JSON, etc.)
- [ ] Enums used for restricted value sets
- [ ] Input types defined for mutations
- [ ] Mutation payload types include errors
- [ ] All fields have clear descriptions

##### Queries
- [ ] Root query type defined
- [ ] Query depth limiting implemented (max 5-10 levels)
- [ ] Query complexity analysis implemented
- [ ] Pagination using Relay cursor pattern
- [ ] DataLoaders used for all relationships
- [ ] N+1 query prevention verified
- [ ] Field-level resolver caching considered

##### Mutations
- [ ] Mutation payload types return both data and errors
- [ ] Input types defined for all mutations
- [ ] Field-level validation in input types
- [ ] Idempotency keys supported
- [ ] Optimistic response pattern considered
- [ ] Transaction handling for multi-step mutations

##### Subscriptions
- [ ] Subscription types defined
- [ ] WebSocket connection handling
- [ ] Subscription cleanup on client disconnect
- [ ] Message compression for large payloads

##### Performance & Optimization
- [ ] DataLoaders prevent N+1 queries
- [ ] Query batching enabled (if applicable)
- [ ] Persisted queries considered for mobile clients
- [ ] Response caching implemented
- [ ] Subscription throttling implemented
- [ ] Query timeout configured (typically 10-30 seconds)
- [ ] Introspection disabled in production (optional security measure)

##### Deprecation & Evolution
- [ ] Deprecated fields marked with `@deprecated` directive
- [ ] Deprecation reasons provided
- [ ] Migration path documented
- [ ] New fields added without removing old ones
- [ ] Timeline for removal communicated to clients

##### Security
- [ ] Authentication checked at resolver level
- [ ] Authorization checks on sensitive fields
- [ ] Input validation on all mutation arguments
- [ ] Query complexity limits enforced
- [ ] Rate limiting per user/API key
- [ ] Introspection access controlled
- [ ] Subscription access controlled

##### Documentation
- [ ] Schema introspection enabled
- [ ] All types documented
- [ ] All fields have descriptions
- [ ] Deprecations documented
- [ ] Examples provided in documentation
- [ ] Authentication flow documented

#### Common Sections (Both REST & GraphQL)

##### Error Handling
- [ ] All error responses have machine-readable codes
- [ ] Error messages are user-friendly (no stack traces)
- [ ] Validation errors include field names
- [ ] Detailed error information in logs (server-side)
- [ ] Correlation IDs for error tracking

##### API Contracts & Documentation
- [ ] Type definitions clear and documented
- [ ] Examples for success and error cases
- [ ] Documented rate limit policies
- [ ] Changelog maintained for API changes
- [ ] Backwards compatibility commitment documented
## Common Pitfalls

- **Over-fetching/Under-fetching (REST)**: Fixed in GraphQL but requires DataLoaders
- **Breaking Changes**: Version APIs or use deprecation strategies
- **Inconsistent Error Formats**: Standardize error responses
- **Missing Rate Limits**: APIs without limits are vulnerable to abuse
- **Poor Documentation**: Undocumented APIs frustrate developers
- **Ignoring HTTP Semantics**: POST for idempotent operations breaks expectations
- **Tight Coupling**: API structure shouldn't mirror database schema
