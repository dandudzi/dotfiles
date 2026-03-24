---
name: api-design-graphql
description: Design robust GraphQL APIs with schema-first development, efficient resolvers, N+1 prevention using DataLoaders, and production-ready patterns.
model: sonnet
---

# GraphQL API Design

Build intuitive, scalable GraphQL APIs using schema-first principles and efficient resolver patterns.

## When to Use This Skill

- Designing new GraphQL APIs
- Reviewing GraphQL schema specifications
- Establishing GraphQL standards for your team
- Optimizing GraphQL resolvers and query performance
- Implementing DataLoaders and N+1 prevention

## Core Principles

### Schema-First Development

- Design your schema before writing resolvers
- Types define your domain model
- Queries for reading data
- Mutations for modifying data
- Subscriptions for real-time updates
- Clients request exactly what they need
- Single endpoint, multiple operations
- Strongly typed schema with introspection built-in

## Schema Design

```graphql
# schema.graphql

# Clear type definitions
type User {
  id: ID!
  email: String!
  name: String!
  createdAt: DateTime!

  # Relationships with pagination
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

# Relay-style pagination pattern
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

# Payload types with errors
type CreateUserPayload {
  user: User
  errors: [Error!]
}

type Error {
  field: String
  message: String!
}
```

## Resolver Design

```python
from typing import Optional, List
from ariadne import QueryType, MutationType, ObjectType

query = QueryType()
mutation = MutationType()
user_type = ObjectType("User")

@query.field("user")
async def resolve_user(obj, info, id: str) -> Optional[dict]:
    """Resolve single user by ID."""
    return await fetch_user_by_id(id)

@query.field("users")
async def resolve_users(
    obj, info,
    first: int = 20,
    after: Optional[str] = None,
    search: Optional[str] = None
) -> dict:
    """Resolve paginated user list with cursor-based pagination."""
    offset = decode_cursor(after) if after else 0

    # Fetch one extra to determine hasNextPage
    users = await fetch_users(
        limit=first + 1,
        offset=offset,
        search=search
    )

    has_next = len(users) > first
    if has_next:
        users = users[:first]

    edges = [
        {"node": user, "cursor": encode_cursor(offset + i)}
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
    """Resolve user's orders with DataLoader for N+1 prevention."""
    loader = info.context["loaders"]["orders_by_user"]
    orders = await loader.load(user["id"])
    return paginate_orders(orders, first)

@mutation.field("createUser")
async def resolve_create_user(obj, info, input: dict) -> dict:
    """Create new user with error handling."""
    try:
        validate_user_input(input)
        user = await create_user(
            email=input["email"],
            name=input["name"],
            password=hash_password(input["password"])
        )
        return {"user": user, "errors": []}
    except ValidationError as e:
        return {
            "user": None,
            "errors": [{"field": e.field, "message": e.message}]
        }
```

## DataLoader (N+1 Prevention)

Batch load related data to prevent N+1 queries.

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

        # Group by user_id
        orders_by_user = {}
        for order in orders:
            user_id = order["user_id"]
            if user_id not in orders_by_user:
                orders_by_user[user_id] = []
            orders_by_user[user_id].append(order)

        # Return in input order
        return [orders_by_user.get(user_id, []) for user_id in user_ids]

def create_context():
    return {
        "loaders": {
            "user": UserLoader(),
            "orders_by_user": OrdersByUserLoader()
        }
    }
```

## Best Practices

1. **Schema First**: Design schema before writing resolvers
2. **Avoid N+1**: Always use DataLoaders for relationships
3. **Input Validation**: Validate at schema and resolver levels
4. **Error Handling**: Return structured errors in mutation payloads, not top-level
5. **Cursor Pagination**: Use Relay-style cursor-based pagination
6. **Deprecation**: Use `@deprecated` directive for API evolution
7. **Complexity Analysis**: Track query complexity to prevent expensive operations
8. **Field-Level Auth**: Check permissions on sensitive fields in resolvers
9. **Timeout Queries**: Set maximum execution time (10-30 seconds typical)
10. **Type Safety**: Use non-null (`!`) appropriately for field contracts
11. **Introspection**: Enable in development, disable in production (optional security measure)
12. **Monitoring**: Track query patterns, execution time, and error rates

## Rate Limiting (GraphQL)

Rate limiting for GraphQL requires tracking actual work done, not just request count.

```python
from typing import Dict

class GraphQLRateLimiter:
    """Rate limit based on query complexity."""

    def __init__(self, max_complexity_per_minute: int = 1000):
        self.max_complexity = max_complexity_per_minute
        self.user_complexity: Dict[str, int] = {}

    def check_complexity(self, user_id: str, query_complexity: int) -> bool:
        """Check if user has complexity budget remaining."""
        current = self.user_complexity.get(user_id, 0)
        if current + query_complexity > self.max_complexity:
            return False

        self.user_complexity[user_id] = current + query_complexity
        return True

    def reset_at_minute_boundary(self):
        """Reset counters at minute boundaries."""
        self.user_complexity.clear()
```

Response headers for rate limiting:
```
X-RateLimit-Limit: 1000
X-RateLimit-ComplexityRemaining: 850
X-RateLimit-ComplexityUsed: 150
X-RateLimit-Reset: 1640000060
```

## Security Headers

```javascript
// Set security headers for GraphQL endpoint
const securityHeaders = {
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'X-Frame-Options': 'DENY',
  'X-Content-Type-Options': 'nosniff',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Content-Security-Policy': "default-src 'none'; script-src 'self'"
};

// Apply to all responses
app.use((req, res, next) => {
  Object.entries(securityHeaders).forEach(([key, value]) => {
    res.setHeader(key, value);
  });
  next();
});

// Enable HTTPS in production
if (process.env.NODE_ENV === "production" && !req.secure) {
  return res.redirect(`https://${req.hostname}${req.url}`);
}
```

## Common Pitfalls

- **N+1 Queries**: Always use DataLoaders for relationships
- **Query Bombs**: No query complexity limit allows resource exhaustion
- **No Timeout**: Queries can run forever; set max execution time
- **Deep Nesting**: Allow clients to request deeply nested structures; limit depth to 5-10 levels
- **Missing Validation**: Validate input at both schema and resolver levels
- **Wildcard Introspection**: Enable introspection in production; disable for security
- **Large Payloads**: Pagination required; use filtering to limit response size
- **Mutation Errors**: Don't return top-level errors for mutations; use payload types
- **No Deprecation Path**: Mark deprecated fields so clients can migrate
- **Tight Schema Coupling**: Schema shouldn't mirror database structure exactly

## Migration from REST

If migrating from REST to GraphQL:

1. Run REST and GraphQL in parallel during transition
2. Update client libraries gradually, one at a time
3. Keep API versions aligned during overlap period
4. Document breaking changes clearly
5. Provide GraphQL schema documentation with examples
6. Consider gateway pattern to coexist with REST endpoints
