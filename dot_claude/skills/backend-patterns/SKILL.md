---
name: backend-patterns
description: Backend architecture patterns, API design, database optimization, and server-side best practices for Node.js, Express, and Next.js API routes.
origin: ECC
---

# Backend Development Patterns

Backend architecture patterns and best practices for scalable server-side applications.

## When to Activate

- Designing REST or GraphQL API endpoints
- Implementing repository, service, or controller layers
- Optimizing database queries (N+1, indexing, connection pooling)
- Adding caching (Redis, in-memory, HTTP cache headers)
- Setting up background jobs or async processing
- Structuring error handling and validation for APIs
- Building middleware (auth, logging, rate limiting)

## API Design Patterns

### RESTful API Structure

```typescript
// ✅ Resource-based URLs
GET    /api/markets                 # List resources
GET    /api/markets/:id             # Get single resource
POST   /api/markets                 # Create resource
PUT    /api/markets/:id             # Replace resource
PATCH  /api/markets/:id             # Update resource
DELETE /api/markets/:id             # Delete resource

// ✅ Query parameters for filtering, sorting, pagination
GET /api/markets?status=active&sort=volume&limit=20&offset=0
```

### Repository Pattern

```typescript
// Abstract data access logic
interface MarketRepository {
  findAll(filters?: MarketFilters): Promise<Market[]>
  findById(id: string): Promise<Market | null>
  create(data: CreateMarketDto): Promise<Market>
  update(id: string, data: UpdateMarketDto): Promise<Market>
  delete(id: string): Promise<void>
}

class SupabaseMarketRepository implements MarketRepository {
  async findAll(filters?: MarketFilters): Promise<Market[]> {
    let query = supabase.from('markets').select('*')

    if (filters?.status) {
      query = query.eq('status', filters.status)
    }

    if (filters?.limit) {
      query = query.limit(filters.limit)
    }

    const { data, error } = await query

    if (error) throw new Error(error.message)
    return data
  }

  // Other methods...
}
```

### Service Layer Pattern

```typescript
// Business logic separated from data access
class MarketService {
  constructor(private marketRepo: MarketRepository) {}

  async searchMarkets(query: string, limit: number = 10): Promise<Market[]> {
    // Business logic
    const embedding = await generateEmbedding(query)
    const results = await this.vectorSearch(embedding, limit)

    // Fetch full data
    const markets = await this.marketRepo.findByIds(results.map(r => r.id))

    // Sort by similarity
    return markets.sort((a, b) => {
      const scoreA = results.find(r => r.id === a.id)?.score || 0
      const scoreB = results.find(r => r.id === b.id)?.score || 0
      return scoreA - scoreB
    })
  }

  private async vectorSearch(embedding: number[], limit: number) {
    // Vector search implementation
  }
}
```

### Middleware Pattern

```typescript
// Request/response processing pipeline
export function withAuth(handler: NextApiHandler): NextApiHandler {
  return async (req, res) => {
    const token = req.headers.authorization?.replace('Bearer ', '')

    if (!token) {
      return res.status(401).json({ error: 'Unauthorized' })
    }

    try {
      const user = await verifyToken(token)
      req.user = user
      return handler(req, res)
    } catch (error) {
      return res.status(401).json({ error: 'Invalid token' })
    }
  }
}

// Usage
export default withAuth(async (req, res) => {
  // Handler has access to req.user
})
```

## Database Patterns

### Query Optimization

```typescript
// ✅ GOOD: Select only needed columns
const { data } = await supabase
  .from('markets')
  .select('id, name, status, volume')
  .eq('status', 'active')
  .order('volume', { ascending: false })
  .limit(10)

// ❌ BAD: Select everything
const { data } = await supabase
  .from('markets')
  .select('*')
```

### N+1 Query Prevention

```typescript
// ❌ BAD: N+1 query problem
const markets = await getMarkets()
for (const market of markets) {
  market.creator = await getUser(market.creator_id)  // N queries
}

// ✅ GOOD: Batch fetch
const markets = await getMarkets()
const creatorIds = markets.map(m => m.creator_id)
const creators = await getUsers(creatorIds)  // 1 query
const creatorMap = new Map(creators.map(c => [c.id, c]))

markets.forEach(market => {
  market.creator = creatorMap.get(market.creator_id)
})
```

### Transaction Pattern

```typescript
async function createMarketWithPosition(
  marketData: CreateMarketDto,
  positionData: CreatePositionDto
) {
  // Use Supabase transaction
  const { data, error } = await supabase.rpc('create_market_with_position', {
    market_data: marketData,
    position_data: positionData
  })

  if (error) throw new Error('Transaction failed')
  return data
}

// SQL function in Supabase
CREATE OR REPLACE FUNCTION create_market_with_position(
  market_data jsonb,
  position_data jsonb
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
BEGIN
  -- Start transaction automatically
  INSERT INTO markets VALUES (market_data);
  INSERT INTO positions VALUES (position_data);
  RETURN jsonb_build_object('success', true);
EXCEPTION
  WHEN OTHERS THEN
    -- Rollback happens automatically
    RETURN jsonb_build_object('success', false, 'error', SQLERRM);
END;
$$;
```

## Caching Strategies

### Redis Caching Layer

```typescript
class CachedMarketRepository implements MarketRepository {
  constructor(
    private baseRepo: MarketRepository,
    private redis: RedisClient
  ) {}

  async findById(id: string): Promise<Market | null> {
    // Check cache first
    const cached = await this.redis.get(`market:${id}`)

    if (cached) {
      return JSON.parse(cached)
    }

    // Cache miss - fetch from database
    const market = await this.baseRepo.findById(id)

    if (market) {
      // Cache for 5 minutes
      await this.redis.setex(`market:${id}`, 300, JSON.stringify(market))
    }

    return market
  }

  async invalidateCache(id: string): Promise<void> {
    await this.redis.del(`market:${id}`)
  }
}
```

### Cache-Aside Pattern

```typescript
async function getMarketWithCache(id: string): Promise<Market> {
  const cacheKey = `market:${id}`

  // Try cache
  const cached = await redis.get(cacheKey)
  if (cached) return JSON.parse(cached)

  // Cache miss - fetch from DB
  const market = await db.markets.findUnique({ where: { id } })

  if (!market) throw new Error('Market not found')

  // Update cache
  await redis.setex(cacheKey, 300, JSON.stringify(market))

  return market
}
```

## Error Handling Patterns

### Centralized Error Handler

```typescript
class ApiError extends Error {
  constructor(
    public statusCode: number,
    public message: string,
    public isOperational = true
  ) {
    super(message)
    Object.setPrototypeOf(this, ApiError.prototype)
  }
}

export function errorHandler(error: unknown, req: Request): Response {
  if (error instanceof ApiError) {
    return NextResponse.json({
      success: false,
      error: error.message
    }, { status: error.statusCode })
  }

  if (error instanceof z.ZodError) {
    return NextResponse.json({
      success: false,
      error: 'Validation failed',
      details: error.errors
    }, { status: 400 })
  }

  // Log unexpected errors
  console.error('Unexpected error:', error)

  return NextResponse.json({
    success: false,
    error: 'Internal server error'
  }, { status: 500 })
}

// Usage
export async function GET(request: Request) {
  try {
    const data = await fetchData()
    return NextResponse.json({ success: true, data })
  } catch (error) {
    return errorHandler(error, request)
  }
}
```

### Retry with Exponential Backoff

```typescript
async function fetchWithRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  let lastError: Error

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error

      if (i < maxRetries - 1) {
        // Exponential backoff: 1s, 2s, 4s
        const delay = Math.pow(2, i) * 1000
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
  }

  throw lastError!
}

// Usage
const data = await fetchWithRetry(() => fetchFromAPI())
```

## Authentication & Authorization

### JWT Token Validation

```typescript
import jwt from 'jsonwebtoken'

interface JWTPayload {
  userId: string
  email: string
  role: 'admin' | 'user'
}

export function verifyToken(token: string): JWTPayload {
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as JWTPayload
    return payload
  } catch (error) {
    throw new ApiError(401, 'Invalid token')
  }
}

export async function requireAuth(request: Request) {
  const token = request.headers.get('authorization')?.replace('Bearer ', '')

  if (!token) {
    throw new ApiError(401, 'Missing authorization token')
  }

  return verifyToken(token)
}

// Usage in API route
export async function GET(request: Request) {
  const user = await requireAuth(request)

  const data = await getDataForUser(user.userId)

  return NextResponse.json({ success: true, data })
}
```

### Role-Based Access Control

```typescript
type Permission = 'read' | 'write' | 'delete' | 'admin'

interface User {
  id: string
  role: 'admin' | 'moderator' | 'user'
}

const rolePermissions: Record<User['role'], Permission[]> = {
  admin: ['read', 'write', 'delete', 'admin'],
  moderator: ['read', 'write', 'delete'],
  user: ['read', 'write']
}

export function hasPermission(user: User, permission: Permission): boolean {
  return rolePermissions[user.role].includes(permission)
}

export function requirePermission(permission: Permission) {
  return (handler: (request: Request, user: User) => Promise<Response>) => {
    return async (request: Request) => {
      const user = await requireAuth(request)

      if (!hasPermission(user, permission)) {
        throw new ApiError(403, 'Insufficient permissions')
      }

      return handler(request, user)
    }
  }
}

// Usage - HOF wraps the handler
export const DELETE = requirePermission('delete')(
  async (request: Request, user: User) => {
    // Handler receives authenticated user with verified permission
    return new Response('Deleted', { status: 200 })
  }
)
```

## Rate Limiting

### Simple In-Memory Rate Limiter

```typescript
class RateLimiter {
  private requests = new Map<string, number[]>()

  async checkLimit(
    identifier: string,
    maxRequests: number,
    windowMs: number
  ): Promise<boolean> {
    const now = Date.now()
    const requests = this.requests.get(identifier) || []

    // Remove old requests outside window
    const recentRequests = requests.filter(time => now - time < windowMs)

    if (recentRequests.length >= maxRequests) {
      return false  // Rate limit exceeded
    }

    // Add current request
    recentRequests.push(now)
    this.requests.set(identifier, recentRequests)

    return true
  }
}

const limiter = new RateLimiter()

export async function GET(request: Request) {
  const ip = request.headers.get('x-forwarded-for') || 'unknown'

  const allowed = await limiter.checkLimit(ip, 100, 60000)  // 100 req/min

  if (!allowed) {
    return NextResponse.json({
      error: 'Rate limit exceeded'
    }, { status: 429 })
  }

  // Continue with request
}
```

## Background Jobs & Queues

### Simple Queue Pattern

```typescript
class JobQueue<T> {
  private queue: T[] = []
  private processing = false

  async add(job: T): Promise<void> {
    this.queue.push(job)

    if (!this.processing) {
      this.process()
    }
  }

  private async process(): Promise<void> {
    this.processing = true

    while (this.queue.length > 0) {
      const job = this.queue.shift()!

      try {
        await this.execute(job)
      } catch (error) {
        console.error('Job failed:', error)
      }
    }

    this.processing = false
  }

  private async execute(job: T): Promise<void> {
    // Job execution logic
  }
}

// Usage for indexing markets
interface IndexJob {
  marketId: string
}

const indexQueue = new JobQueue<IndexJob>()

export async function POST(request: Request) {
  const { marketId } = await request.json()

  // Add to queue instead of blocking
  await indexQueue.add({ marketId })

  return NextResponse.json({ success: true, message: 'Job queued' })
}
```

## Logging & Monitoring

### Structured Logging

```typescript
interface LogContext {
  userId?: string
  requestId?: string
  method?: string
  path?: string
  [key: string]: unknown
}

class Logger {
  log(level: 'info' | 'warn' | 'error', message: string, context?: LogContext) {
    const entry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      ...context
    }

    console.log(JSON.stringify(entry))
  }

  info(message: string, context?: LogContext) {
    this.log('info', message, context)
  }

  warn(message: string, context?: LogContext) {
    this.log('warn', message, context)
  }

  error(message: string, error: Error, context?: LogContext) {
    this.log('error', message, {
      ...context,
      error: error.message,
      stack: error.stack
    })
  }
}

const logger = new Logger()

// Usage
export async function GET(request: Request) {
  const requestId = crypto.randomUUID()

  logger.info('Fetching markets', {
    requestId,
    method: 'GET',
    path: '/api/markets'
  })

  try {
    const markets = await fetchMarkets()
    return NextResponse.json({ success: true, data: markets })
  } catch (error) {
    logger.error('Failed to fetch markets', error as Error, { requestId })
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}
```

## Middleware Patterns

### Request Validation Middleware

```typescript
import { z } from 'zod'

const createMarketSchema = z.object({
  name: z.string().min(1).max(255),
  status: z.enum(['active', 'archived']),
  volume: z.number().min(0)
})

export function validateBody(schema: z.ZodSchema) {
  return async (req: Request, res: Response, next: Function) => {
    try {
      const validated = schema.parse(await req.json())
      req.body = validated
      next()
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({
          error: 'Validation failed',
          details: error.flatten()
        })
      }
      throw error
    }
  }
}

// Usage
app.post('/markets', validateBody(createMarketSchema), createMarket)
```

### Authentication Middleware

```typescript
// JWT extraction and validation
export async function authMiddleware(req: Request, res: Response, next: Function) {
  const token = req.headers.authorization?.replace('Bearer ', '')

  if (!token) {
    return res.status(401).json({ error: 'Missing token' })
  }

  try {
    const user = await verifyToken(token)
    req.user = user
    next()
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' })
  }
}

// Session lookup (for cookie-based auth)
export async function sessionMiddleware(req: Request, res: Response, next: Function) {
  const sessionId = req.cookies.sessionId

  if (!sessionId) {
    return res.status(401).json({ error: 'No session' })
  }

  const session = await redis.get(`session:${sessionId}`)
  if (!session) {
    return res.status(401).json({ error: 'Session expired' })
  }

  req.session = JSON.parse(session)
  next()
}
```

### Authorization Middleware (RBAC)

```typescript
export function requireRole(...roles: string[]) {
  return (handler: Handler) => async (req: Request, res: Response) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Insufficient permissions' })
    }
    return handler(req, res)
  }
}

// Usage
export const DELETE = requireRole('admin', 'moderator')(
  async (req: Request) => {
    return NextResponse.json({ success: true })
  }
)
```

### Error Handling Middleware

```typescript
// Centralized error formatter
export function errorMiddleware(err: Error, req: Request, res: Response, next: Function) {
  const status = err instanceof ApiError ? err.statusCode : 500
  const message = err instanceof ApiError ? err.message : 'Internal server error'

  // Log server errors
  if (status >= 500) {
    console.error('[ERROR]', {
      timestamp: new Date().toISOString(),
      message: err.message,
      stack: err.stack,
      path: req.path,
      method: req.method
    })
  }

  return res.status(status).json({
    success: false,
    error: message,
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  })
}

// Async error wrapper (catches thrown errors in async handlers)
export function asyncHandler(fn: Handler): Handler {
  return (req: Request, res: Response, next: Function) => {
    Promise.resolve(fn(req, res)).catch(next)
  }
}

// Usage
app.get('/data', asyncHandler(async (req, res) => {
  const data = await fetchData()  // If throws, errorMiddleware catches it
  return res.json(data)
}))
```

### Request Logging Middleware

```typescript
export function loggingMiddleware(req: Request, res: Response, next: Function) {
  const correlationId = req.headers['x-correlation-id'] || crypto.randomUUID()
  const startTime = Date.now()

  res.on('finish', () => {
    const duration = Date.now() - startTime
    console.log(JSON.stringify({
      level: 'info',
      timestamp: new Date().toISOString(),
      correlationId,
      method: req.method,
      path: req.path,
      status: res.statusCode,
      duration_ms: duration,
      user_id: req.user?.id,
      ip: req.ip
    }))
  })

  req.correlationId = correlationId
  next()
}
```

### Rate Limiting Middleware

```typescript
// Sliding window counter
class SlidingWindowLimiter {
  private requests = new Map<string, number[]>()

  isAllowed(key: string, maxRequests: number, windowMs: number): boolean {
    const now = Date.now()
    const times = this.requests.get(key) || []

    // Remove timestamps outside window
    const valid = times.filter(t => now - t < windowMs)

    if (valid.length >= maxRequests) {
      return false
    }

    valid.push(now)
    this.requests.set(key, valid)
    return true
  }
}

// Token bucket (allows burst traffic)
class TokenBucketLimiter {
  private buckets = new Map<string, { tokens: number; lastRefill: number }>()

  isAllowed(key: string, capacity: number, refillRate: number): boolean {
    const now = Date.now()
    let bucket = this.buckets.get(key) || { tokens: capacity, lastRefill: now }

    // Refill tokens based on elapsed time
    const elapsed = (now - bucket.lastRefill) / 1000
    bucket.tokens = Math.min(capacity, bucket.tokens + (refillRate * elapsed))
    bucket.lastRefill = now

    if (bucket.tokens < 1) {
      return false
    }

    bucket.tokens -= 1
    this.buckets.set(key, bucket)
    return true
  }
}

export function rateLimitMiddleware(limiter: SlidingWindowLimiter) {
  return (req: Request, res: Response, next: Function) => {
    const key = req.user?.id || req.ip
    const allowed = limiter.isAllowed(key, 100, 60000)  // 100 req/min

    if (!allowed) {
      return res.status(429).json({ error: 'Rate limit exceeded' })
    }

    next()
  }
}
```

## Transaction Management

### Unit of Work Pattern

```typescript
// Tracks all changes and commits them atomically
class UnitOfWork {
  private changes: Array<() => Promise<void>> = []

  async add(operation: () => Promise<void>) {
    this.changes.push(operation)
  }

  async commit() {
    try {
      for (const change of this.changes) {
        await change()
      }
    } catch (error) {
      // Rollback on error
      this.changes = []
      throw error
    }
  }
}

// Usage
export async function transferFunds(fromId: string, toId: string, amount: number) {
  const uow = new UnitOfWork()

  await uow.add(() => db.accounts.update(fromId, { balance: db.raw('balance - ?', [amount]) }))
  await uow.add(() => db.accounts.update(toId, { balance: db.raw('balance + ?', [amount]) }))
  await uow.add(() => db.transactions.create({ fromId, toId, amount }))

  await uow.commit()
}
```

### Optimistic Locking

```typescript
// Add version field to entities
interface Market {
  id: string
  name: string
  version: number  // Increment on each update
}

async function updateMarketOptimistic(id: string, updates: Partial<Market>, currentVersion: number) {
  const result = await db.markets.update(
    { id, version: currentVersion },  // WHERE clause includes version
    { ...updates, version: currentVersion + 1 }
  )

  if (result.rowsAffected === 0) {
    throw new Error('Market was updated by another process (stale version)')
  }

  return result
}

// Usage: fetch current version, attempt update
const market = await db.markets.findUnique({ where: { id } })
try {
  await updateMarketOptimistic(market.id, { name: 'New Name' }, market.version)
} catch (error) {
  // Retry with fresh data
  console.log('Version conflict, retrying...')
}
```

### Pessimistic Locking

```typescript
// SELECT FOR UPDATE - lock row until transaction ends
async function updateMarketPessimistic(id: string, updates: Partial<Market>) {
  return db.transaction(async (trx) => {
    // Lock the row
    const market = await trx.markets
      .where({ id })
      .forUpdate()
      .first()

    if (!market) throw new Error('Not found')

    // Update locked row
    await trx.markets.where({ id }).update(updates)

    return market
  })
}
```

### Saga Pattern (Distributed Transactions)

```typescript
// Orchestrates multi-step transactions with compensating actions
class Saga {
  private steps: Array<{ forward: () => Promise<void>; compensate: () => Promise<void> }> = []

  addStep(forward: () => Promise<void>, compensate: () => Promise<void>) {
    this.steps.push({ forward, compensate })
  }

  async execute() {
    const completed: number[] = []

    try {
      for (let i = 0; i < this.steps.length; i++) {
        await this.steps[i].forward()
        completed.push(i)
      }
    } catch (error) {
      // Compensate in reverse order
      for (let i = completed.length - 1; i >= 0; i--) {
        try {
          await this.steps[completed[i]].compensate()
        } catch (compensateError) {
          console.error('Compensation failed:', compensateError)
        }
      }
      throw error
    }
  }
}

// Usage: Order placement with payment and inventory
const saga = new Saga()

saga.addStep(
  () => paymentService.charge(userId, amount),  // forward
  () => paymentService.refund(transactionId)    // compensate
)

saga.addStep(
  () => inventoryService.reserve(itemId, quantity),
  () => inventoryService.release(itemId, quantity)
)

await saga.execute()
```

### Idempotency Keys

```typescript
// Prevents duplicate operations from retries
export async function createOrderIdempotent(
  idempotencyKey: string,
  data: CreateOrderDto
) {
  // Check if request already processed
  const existing = await redis.get(`idempotency:${idempotencyKey}`)
  if (existing) {
    return JSON.parse(existing)
  }

  // Process request
  const order = await db.orders.create(data)

  // Cache result with expiration (24 hours)
  await redis.setex(
    `idempotency:${idempotencyKey}`,
    86400,
    JSON.stringify(order)
  )

  return order
}

// Usage: Client provides Idempotency-Key header
export async function POST(request: Request) {
  const idempotencyKey = request.headers.get('Idempotency-Key')
  if (!idempotencyKey) {
    return res.status(400).json({ error: 'Missing Idempotency-Key' })
  }

  const data = await request.json()
  const order = await createOrderIdempotent(idempotencyKey, data)
  return NextResponse.json(order)
}
```

## Advanced Caching Strategies

### Read-Through Cache Pattern

```typescript
class ReadThroughCache<T> {
  constructor(
    private loader: (key: string) => Promise<T>,
    private redis: RedisClient
  ) {}

  async get(key: string, ttlSeconds = 300): Promise<T> {
    // Check cache
    const cached = await this.redis.get(key)
    if (cached) {
      return JSON.parse(cached)
    }

    // Load from source on miss
    const data = await this.loader(key)

    // Populate cache
    await this.redis.setex(key, ttlSeconds, JSON.stringify(data))

    return data
  }
}
```

### Write-Through Cache Pattern

```typescript
class WriteThroughCache<T> {
  constructor(
    private db: Database,
    private redis: RedisClient
  ) {}

  async set(key: string, value: T): Promise<void> {
    // Write to database first
    await this.db.set(key, value)

    // Then update cache
    await this.redis.set(key, JSON.stringify(value))
  }

  async delete(key: string): Promise<void> {
    // Delete from database
    await this.db.delete(key)

    // Then invalidate cache
    await this.redis.del(key)
  }
}
```

### TTL Strategy

```typescript
// Short TTL for volatile data (user sessions: 5-10 min)
await redis.setex(`session:${userId}`, 300, JSON.stringify(session))

// Medium TTL for computed data (search results: 1-30 min)
await redis.setex(`search:${query}`, 1800, JSON.stringify(results))

// Long TTL for reference data (categories: 1-24 hours)
await redis.setex(`categories`, 86400, JSON.stringify(categories))

// Very long for static data (config: 1 week)
await redis.setex(`config:${key}`, 604800, JSON.stringify(config))
```

### Event-Driven Cache Invalidation

```typescript
// Listen to domain events and invalidate relevant caches
class CacheInvalidator {
  constructor(private redis: RedisClient, private eventBus: EventBus) {
    this.setup()
  }

  private setup() {
    this.eventBus.on('MarketCreated', (event) => {
      this.redis.del('markets:list')
    })

    this.eventBus.on('MarketUpdated', (event) => {
      this.redis.del(`market:${event.marketId}`)
      this.redis.del('markets:list')
    })

    this.eventBus.on('UserUpdated', (event) => {
      this.redis.del(`user:${event.userId}`)
    })
  }
}
```

### Redis Data Structures

```typescript
// Strings: counters, sessions
await redis.incr('api:requests:today')
await redis.setex(`session:${id}`, 3600, JSON.stringify(user))

// Hashes: objects (more efficient than JSON strings)
await redis.hset(`user:${id}`, 'name', 'John', 'email', 'john@example.com')
const user = await redis.hgetall(`user:${id}`)

// Sorted Sets: leaderboards, time-series
await redis.zadd('leaderboard', score, userId)
const top10 = await redis.zrange('leaderboard', 0, 9, 'WITHSCORES')

// Lists: queues, activity streams
await redis.rpush(`queue:${jobType}`, JSON.stringify(job))
const job = await redis.lpop(`queue:${jobType}`)
```

### Cache Decision Matrix

```
In-Memory (node-cache):
  Use: Small, hot datasets (< 100MB)
  Pros: Fast, no network latency
  Cons: Not shared across instances, memory pressure
  Example: Feature flags, config caches

Redis (distributed):
  Use: Shared cache across services
  Pros: Distributed, supports complex data types, TTL
  Cons: Network latency, extra infrastructure
  Example: Sessions, user data, search results

CDN Cache (CloudFlare, Cloudfront):
  Use: Static assets, JSON responses
  Pros: Geographic distribution, edge caching
  Cons: Hard to invalidate, not suitable for personalized data
  Example: Public APIs, static content
```

**Remember**: Backend patterns enable scalable, maintainable server-side applications. Choose patterns that fit your complexity level.
