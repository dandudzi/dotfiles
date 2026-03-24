---
name: backend-data-patterns
description: Database optimization, caching strategies (Redis, in-memory, cache-aside), transaction management, and background job patterns.
origin: ECC
model: sonnet
---

# Backend Data Patterns

## When to Activate

- Optimizing database queries (N+1 prevention, indexing, connection pooling)
- Implementing caching layers (Redis, in-memory, HTTP cache)
- Managing distributed transactions and data consistency
- Building background jobs and async processing queues
- Handling transaction isolation and optimistic/pessimistic locking

## Database Patterns

### Query Optimization

```typescript
// ✅ Select only needed columns
const { data } = await supabase
  .from('markets')
  .select('id, name, status, volume')
  .eq('status', 'active')
  .order('volume', { ascending: false })
  .limit(10)

// ❌ BAD: Select everything with * — expensive, transfers unnecessary data
const { data } = await supabase.from('markets').select('*')
```

### N+1 Query Prevention

```typescript
// ❌ BAD: N+1 query problem — loops query database per record
const markets = await getMarkets()
for (const market of markets) {
  market.creator = await getUser(market.creator_id)  // N queries
}

// ✅ GOOD: Batch fetch — single query for all related records
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
  const { data, error } = await supabase.rpc('create_market_with_position', {
    market_data: marketData,
    position_data: positionData
  })

  if (error) throw new Error('Transaction failed')
  return data
}

// SQL function handles transaction atomicity automatically
CREATE OR REPLACE FUNCTION create_market_with_position(
  market_data jsonb,
  position_data jsonb
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
BEGIN
  INSERT INTO markets VALUES (market_data);
  INSERT INTO positions VALUES (position_data);
  RETURN jsonb_build_object('success', true);
EXCEPTION
  WHEN OTHERS THEN
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
    const cached = await this.redis.get(`market:${id}`)
    if (cached) {
      return JSON.parse(cached)
    }

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

  // Try cache first
  const cached = await redis.get(cacheKey)
  if (cached) return JSON.parse(cached)

  // Cache miss — fetch from DB
  const market = await db.markets.findUnique({ where: { id } })
  if (!market) throw new Error('Market not found')

  // Populate cache asynchronously (don't await)
  redis.setex(cacheKey, 300, JSON.stringify(market)).catch(console.error)

  return market
}
```

### Read-Through Cache Pattern

```typescript
class ReadThroughCache<T> {
  constructor(
    private loader: (key: string) => Promise<T>,
    private redis: RedisClient
  ) {}

  async get(key: string, ttlSeconds = 300): Promise<T> {
    const cached = await this.redis.get(key)
    if (cached) {
      return JSON.parse(cached)
    }

    // Load from source and populate cache
    const data = await this.loader(key)
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
    // Write to database first — ensures durability
    await this.db.set(key, value)
    // Then update cache
    await this.redis.set(key, JSON.stringify(value))
  }

  async delete(key: string): Promise<void> {
    // Delete from database first
    await this.db.delete(key)
    // Then invalidate cache
    await this.redis.del(key)
  }
}
```

### Cache Decision Matrix

| Layer | Use Case | Pros | Cons |
|-------|----------|------|------|
| **In-Memory (node-cache)** | Small, hot datasets <100MB | Fast, no network latency | Not shared across instances, memory pressure |
| **Redis** | Shared cache across services | Distributed, complex data types, TTL | Network latency, extra infrastructure |
| **CDN (CloudFlare/Cloudfront)** | Static assets, JSON responses | Geographic distribution | Hard to invalidate, not for personalized data |

### Event-Driven Cache Invalidation

```typescript
class CacheInvalidator {
  constructor(private redis: RedisClient, private eventBus: EventBus) {
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

## Transaction Management

### Unit of Work Pattern

```typescript
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
      this.changes = []
      throw error
    }
  }
}

// Usage: Transfer funds atomically
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

// Usage: Fetch current version, attempt update with conflict detection
const market = await db.markets.findUnique({ where: { id } })
try {
  await updateMarketOptimistic(market.id, { name: 'New Name' }, market.version)
} catch (error) {
  console.log('Version conflict, retrying...')
}
```

### Pessimistic Locking

```typescript
async function updateMarketPessimistic(id: string, updates: Partial<Market>) {
  return db.transaction(async (trx) => {
    // SELECT FOR UPDATE — lock row until transaction ends
    const market = await trx.markets
      .where({ id })
      .forUpdate()
      .first()

    if (!market) throw new Error('Not found')

    await trx.markets.where({ id }).update(updates)
    return market
  })
}
```

### Saga Pattern (Distributed Transactions)

```typescript
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
      // Compensate in reverse order — undo completed steps
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
  () => paymentService.charge(userId, amount),
  () => paymentService.refund(transactionId)
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

  // Cache result with 24-hour expiration
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

interface IndexJob {
  marketId: string
}

const indexQueue = new JobQueue<IndexJob>()

export async function POST(request: Request) {
  const { marketId } = await request.json()
  await indexQueue.add({ marketId })
  return NextResponse.json({ success: true, message: 'Job queued' })
}
```

---

**Activate for**: Database optimization, caching implementation, transaction coordination, background processing, and data consistency patterns.
