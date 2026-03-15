---
name: postgresql-patterns
description: PostgreSQL schema design, data types, indexing, constraints, and performance patterns for building robust, scalable databases.
origin: ECC
---

# PostgreSQL Patterns

## When to Activate

- Designing PostgreSQL schemas
- Selecting appropriate data types
- Creating indexes for performance
- Building JSONB query strategies
- Implementing upserts and constraints
- Optimizing query patterns with window functions and CTEs

## Data Types Selection Matrix

Choose the right type for your data. Mismatches cause bloat, silent failures, or precision loss.

| Use Case | Type | Why | Anti-Pattern |
|----------|------|-----|--------------|
| Identifier (auto-increment) | `BIGINT GENERATED ALWAYS AS IDENTITY` | Space-efficient, no external generation needed | `SERIAL` (deprecated), `UUID` for single-table IDs |
| Global uniqueness (distributed) | `UUID` with `gen_random_uuid()` or `uuidv7()` | Mergeable across systems, opaque | BIGINT without distribution consideration |
| Text/strings | `TEXT` | Flexible, no truncation issues | `CHAR(n)`, `VARCHAR(n)` (length limits cause errors) |
| Money/decimals | `NUMERIC(p,s)` | Exact arithmetic, no rounding errors | `REAL`, `DOUBLE PRECISION` for money (precision loss) |
| Whole numbers | `BIGINT` | Safe default, 64-bit range | `INTEGER` unless space critical, `SMALLINT` rarely needed |
| Floating point | `DOUBLE PRECISION` | Standard precision, minimal storage | `REAL` unless space critical, `NUMERIC` if exact arithmetic needed |
| Timestamps | `TIMESTAMPTZ` | Always include timezone | `TIMESTAMP` (ambiguous), `TIMETZ` (deprecated) |
| Dates only | `DATE` | No timezone confusion | `TIMESTAMP` for date-only storage |
| Key-value pairs | `JSONB` with GIN index | Indexable, queryable, compresses well | `JSON` (unindexable), `HSTORE` (string-only values) |
| Arrays of values | `TEXT[]` or `INTEGER[]` indexed with GIN | Efficient containment queries | Separate table for simple lists (slower to query) |
| Ranges/intervals | `DATERANGE`, `TSTZRANGE`, `NUMRANGE` with GiST | Overlap queries, scheduled/versioned data | Multiple columns for start/end (no overlap detection) |

### PostgreSQL Data Type Gotchas

```sql
-- WRONG: VARCHAR(n) silently errors on overflow
CREATE TABLE users (name VARCHAR(50));
INSERT INTO users VALUES ('This very long name exceeds fifty characters limit');  -- ERROR

-- RIGHT: Use TEXT with CHECK constraint (enforces, doesn't truncate)
CREATE TABLE users (
    name TEXT NOT NULL CHECK (LENGTH(name) <= 50)
);

-- WRONG: CHAR(n) pads with spaces, queries need TRIM
CREATE TABLE users (code CHAR(10));
SELECT * FROM users WHERE code = 'ABC';  -- No match unless code is 'ABC       '

-- RIGHT: Use TEXT
CREATE TABLE users (code TEXT NOT NULL);
SELECT * FROM users WHERE code = 'ABC';  -- Matches exactly

-- WRONG: TIMESTAMP without timezone is ambiguous
CREATE TABLE events (happened_at TIMESTAMP);
-- Is this UTC? Local? Ambiguous in multi-timezone systems.

-- RIGHT: Always include timezone
CREATE TABLE events (happened_at TIMESTAMPTZ NOT NULL);

-- WRONG: Use FLOAT for money
CREATE TABLE orders (total REAL);
INSERT INTO orders VALUES (0.1 + 0.2);  -- Stores ~0.30000000000000004

-- RIGHT: Use NUMERIC for exact arithmetic
CREATE TABLE orders (total NUMERIC(10,2) NOT NULL);
INSERT INTO orders VALUES (0.1 + 0.2);  -- Stores exactly 0.30
```

## Indexing Patterns

Index for access paths you actually query, not speculatively.

### Index Type Decision Matrix

| Pattern | Type | When | Example |
|---------|------|------|---------|
| Equality (`=`), range (`>`, `<`), sorting | B-tree | Default for most queries | `CREATE INDEX ON users (email)` |
| JSONB containment (`@>`), arrays (`@>`) | GIN | Frequent semi-structured queries | `CREATE INDEX ON profiles USING GIN (attrs)` |
| Range overlap (`&&`), geometry | GiST | Scheduling, spatial data | `CREATE INDEX ON bookings USING GiST (booking_range)` |
| Fuzzy text (`LIKE %pattern%`) | GIN + `pg_trgm` | Text search within larger strings | `CREATE INDEX ON items USING GIN (description gin_trgm_ops)` |
| Full-text search (`@@`) | GIN | Text search documents | `CREATE INDEX ON docs USING GIN (to_tsvector('english', body))` |
| Time-series (ordered, large) | BRIN | Huge tables where data correlates with insertion order | `CREATE INDEX ON logs USING BRIN (created_at)` |
| Subset of rows | Partial | Hot subsets (e.g., active users) | `CREATE INDEX ON users (id) WHERE is_active = true` |
| Multiple columns (prefix) | Composite | Queries on column combinations | `CREATE INDEX ON orders (user_id, created_at)` |
| Column + other values | Covering | Index-only scans without table visit | `CREATE INDEX ON users (email) INCLUDE (name, phone)` |
| Expression value (computed) | Expression | Queries on lower/upper/extracted values | `CREATE INDEX ON users (LOWER(email))` |

### Composite Index Ordering

Column order matters for composite indexes. Equality columns first, then range/sort.

```sql
-- Query: WHERE user_id = ? AND created_at > ?
-- GOOD: Equality first, range second
CREATE INDEX ON orders (user_id, created_at);

-- Query: WHERE status = 'paid' AND total > 100 AND created_at DESC
-- GOOD: Equality first, range second, sort last
CREATE INDEX ON orders (status, total, created_at DESC);

-- Query: WHERE a = ? AND b = ? AND c > ?
-- GOOD: Both equalities, then range
CREATE INDEX ON events (a, b, c);

-- WRONG: Range before equality prevents use of range column
CREATE INDEX ON orders (created_at, user_id);  -- Can't use for WHERE user_id = ? AND created_at > ?
```

## Common Gotchas

```sql
-- GOTCHA 1: NULL in UNIQUE allows duplicates
CREATE TABLE users (email TEXT UNIQUE);
INSERT INTO users VALUES (NULL);
INSERT INTO users VALUES (NULL);  -- Both inserted! Multiple NULLs allowed
-- FIX: Use NULLS NOT DISTINCT (PostgreSQL 15+)
CREATE TABLE users (email TEXT UNIQUE NULLS NOT DISTINCT);

-- GOTCHA 2: Foreign keys don't auto-index the referencing column
CREATE TABLE orders (
    user_id BIGINT REFERENCES users(id)
);
-- SELECT * FROM users WHERE id = 123; -- Fast (uses PK index)
-- SELECT * FROM orders WHERE user_id = 123; -- SLOW (no index!)
-- FIX: Create index explicitly
CREATE INDEX ON orders (user_id);

-- GOTCHA 3: Sequences have gaps (expected behavior)
CREATE TABLE users (id BIGINT GENERATED ALWAYS AS IDENTITY);
INSERT INTO users (name) VALUES ('Alice');  -- id = 1
INSERT INTO users (name) VALUES ('Bob');    -- id = 2
ROLLBACK;  -- Transaction rolls back
INSERT INTO users (name) VALUES ('Charlie'); -- id = 5 (gap at 2-4)
-- This is normal, not a bug. Don't try to "fix" gaps.

-- GOTCHA 4: LIKE without proper case handling
SELECT * FROM users WHERE name LIKE 'john';  -- Case-sensitive, finds 'john' not 'John'
-- FIX: Use LOWER or ILIKE
SELECT * FROM users WHERE LOWER(name) LIKE 'john';  -- Case-insensitive

-- GOTCHA 5: UNIQUE constraint allows multiple NULLs by default
CREATE TABLE users (secondary_email TEXT UNIQUE);
INSERT INTO users VALUES (1, NULL);
INSERT INTO users VALUES (2, NULL);  -- Both allowed
-- FIX: Add NOT NULL if email is required, or use NULLS NOT DISTINCT
ALTER TABLE users ALTER COLUMN secondary_email SET NOT NULL;

-- GOTCHA 6: CHECK constraints allow NULL (three-valued logic)
CREATE TABLE orders (total NUMERIC(10,2) CHECK (total > 0));
INSERT INTO orders (total) VALUES (NULL);  -- Allowed! NULL passes CHECK
-- FIX: Combine with NOT NULL
CREATE TABLE orders (
    total NUMERIC(10,2) NOT NULL CHECK (total > 0)
);
```

## JSONB Patterns

JSONB is indexable, queryable, and compresses well. Use for optional/semi-structured data only.

### JSONB Indexing Strategy

```sql
-- Basic GIN index (supports containment, key existence, full-text)
CREATE INDEX ON profiles USING GIN (attrs);

-- For containment-heavy queries, use jsonb_path_ops (smaller, faster containment)
CREATE INDEX ON profiles USING GIN (attrs jsonb_path_ops);
-- Trade-off: loses support for ? and ?| operators (key existence)

-- Extract and index scalar values separately
ALTER TABLE profiles ADD COLUMN theme TEXT GENERATED ALWAYS AS (attrs->>'theme') STORED;
CREATE INDEX ON profiles (theme);  -- B-tree for fast equality
```

### JSONB Query Patterns

```sql
-- Containment: "attrs contains this key-value pair"
SELECT * FROM profiles WHERE attrs @> '{"theme":"dark"}';

-- Key existence: "attrs has this key"
SELECT * FROM profiles WHERE attrs ? 'theme';

-- Any key: "attrs contains any of these keys"
SELECT * FROM profiles WHERE attrs ?| ARRAY['theme', 'language'];

-- All keys: "attrs contains all of these keys"
SELECT * FROM profiles WHERE attrs ?& ARRAY['theme', 'language'];

-- Path extraction: "get nested value"
SELECT attrs->'settings'->>'notifications' AS notifications FROM profiles;

-- Array containment within JSONB
SELECT * FROM profiles WHERE attrs->'tags' @> '["admin"]'::jsonb;
```

## Window Functions

Use window functions for ranking, running totals, and comparisons without grouping.

```sql
-- Rank sales by month
SELECT
    month,
    revenue,
    ROW_NUMBER() OVER (ORDER BY revenue DESC) AS rank,
    RANK() OVER (ORDER BY revenue DESC) AS rank_with_ties,
    DENSE_RANK() OVER (ORDER BY revenue DESC) AS dense_rank,
    LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
    LEAD(revenue) OVER (ORDER BY month) AS next_month_revenue,
    revenue - LAG(revenue) OVER (ORDER BY month) AS change_from_prev
FROM monthly_sales;

-- Running total by partition
SELECT
    user_id,
    date,
    amount,
    SUM(amount) OVER (PARTITION BY user_id ORDER BY date) AS running_total
FROM transactions;

-- Percentile within group
SELECT
    user_id,
    score,
    PERCENT_RANK() OVER (ORDER BY score) AS percentile,
    NTILE(4) OVER (ORDER BY score) AS quartile
FROM user_scores;
```

## CTE vs Subquery Decision Matrix

| Scenario | Use | Why |
|----------|-----|-----|
| Multiple references to same subquery | CTE | Avoid repetition, improve readability |
| Single use, simple filter | Subquery | Less code |
| Recursive/hierarchical data | Recursive CTE | Only option for tree traversal |
| Multiple steps (pipeline) | Multiple CTEs | Easier to read than nested subqueries |
| Large intermediate result | CTE with materialization | Can materialize CTEs with `WITH ... AS MATERIALIZED` |

```sql
-- GOOD: CTE for clarity and reuse
WITH active_users AS (
    SELECT * FROM users WHERE is_active = true
),
user_orders AS (
    SELECT user_id, COUNT(*) as order_count FROM orders
    GROUP BY user_id
)
SELECT u.name, uo.order_count
FROM active_users u
JOIN user_orders uo ON u.id = uo.user_id;

-- GOOD: Recursive CTE for hierarchy
WITH RECURSIVE org_tree AS (
    SELECT id, name, manager_id, 0 as level FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, ot.level + 1
    FROM employees e
    JOIN org_tree ot ON e.manager_id = ot.id
)
SELECT * FROM org_tree ORDER BY level, name;

-- BAD: Nested subqueries hard to read
SELECT u.name FROM users u
WHERE u.id IN (
    SELECT user_id FROM orders
    WHERE id IN (
        SELECT order_id FROM order_items WHERE price > 100
    )
);

-- GOOD: CTE version is clearer
WITH expensive_items AS (
    SELECT order_id FROM order_items WHERE price > 100
),
relevant_orders AS (
    SELECT DISTINCT user_id FROM orders WHERE id IN (SELECT order_id FROM expensive_items)
)
SELECT name FROM users WHERE id IN (SELECT user_id FROM relevant_orders);
```

## Upsert Patterns

INSERT ON CONFLICT handles insert-or-update efficiently.

```sql
-- Basic upsert: ignore if conflict
INSERT INTO users (email, name) VALUES ('alice@example.com', 'Alice')
ON CONFLICT (email) DO NOTHING;

-- Update only changed columns
INSERT INTO users (email, name, updated_at)
VALUES ('alice@example.com', 'Alice Updated', now())
ON CONFLICT (email) DO UPDATE SET
    name = EXCLUDED.name,
    updated_at = EXCLUDED.updated_at
WHERE users.updated_at < EXCLUDED.updated_at;  -- Only if newer

-- Complex upsert: only update if value actually changed
INSERT INTO users (email, name, score)
VALUES ('alice@example.com', 'Alice', 100)
ON CONFLICT (email) DO UPDATE SET
    name = CASE WHEN users.name != EXCLUDED.name THEN EXCLUDED.name ELSE users.name END,
    score = GREATEST(users.score, EXCLUDED.score)
;

-- Upsert on composite key
INSERT INTO user_stats (user_id, date, clicks, impressions)
VALUES (123, '2024-01-15', 50, 1000)
ON CONFLICT (user_id, date) DO UPDATE SET
    clicks = user_stats.clicks + EXCLUDED.clicks,
    impressions = user_stats.impressions + EXCLUDED.impressions;
```

## Transaction Isolation Levels

Choose isolation levels based on consistency vs concurrency trade-offs.

```sql
-- READ UNCOMMITTED: Least isolation, highest concurrency (default in many DBs)
BEGIN ISOLATION LEVEL READ UNCOMMITTED;
-- PostgreSQL treats as READ COMMITTED

-- READ COMMITTED: Default in PostgreSQL
BEGIN ISOLATION LEVEL READ COMMITTED;
-- Sees committed data at statement start; prevents dirty reads

-- REPEATABLE READ: Snapshot isolation
BEGIN ISOLATION LEVEL REPEATABLE READ;
-- Consistent snapshot for entire transaction; prevents non-repeatable reads

-- SERIALIZABLE: Serialization isolation (highest safety)
BEGIN ISOLATION LEVEL SERIALIZABLE;
-- Behaves as if transactions ran serially; prevents all anomalies

-- Example: Use SERIALIZABLE for critical financial operations
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT balance FROM accounts WHERE id = 123;
-- ... check balance ...
UPDATE accounts SET balance = balance - amount WHERE id = 123;
COMMIT;

-- Example: Use REPEATABLE READ for reports
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT SUM(revenue) FROM orders WHERE date >= '2024-01-01';
SELECT SUM(expenses) FROM expenses WHERE date >= '2024-01-01';
COMMIT;
```

## Constraints

Declare intent with constraints. Database enforces at commit time.

```sql
-- Primary Key: unique + not null + indexed
CREATE TABLE users (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY
);

-- Foreign Key with referential action
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
);
-- ON DELETE CASCADE: delete order if user deleted
-- ON DELETE RESTRICT: prevent user deletion if orders exist
-- ON DELETE SET NULL: set user_id to NULL if user deleted

-- UNIQUE constraint (allows multiple NULLs by default)
CREATE TABLE users (
    email TEXT UNIQUE  -- Multiple NULLs allowed
);
-- Fix with NULLS NOT DISTINCT (PG15+)
CREATE TABLE users (
    email TEXT UNIQUE NULLS NOT DISTINCT
);

-- CHECK constraint (enforces row-level rule)
CREATE TABLE orders (
    total NUMERIC(10,2) NOT NULL CHECK (total > 0),
    status TEXT CHECK (status IN ('pending', 'paid', 'cancelled'))
);

-- EXCLUDE constraint (prevents overlapping values)
CREATE TABLE room_bookings (
    room_id INTEGER,
    booking_period TSTZRANGE,
    EXCLUDE USING gist (room_id WITH =, booking_period WITH &&)
);
-- Prevents double-booking same room
```

## Anti-Patterns

```sql
-- ANTI-PATTERN 1: CHAR(n) for variable-length strings
-- Wastes space, requires TRIM in queries
CREATE TABLE users (code CHAR(10));
-- FIX: Use TEXT with CHECK
CREATE TABLE users (code TEXT CHECK (LENGTH(code) = 10));

-- ANTI-PATTERN 2: SELECT * (exposes internal structure)
SELECT * FROM users;
-- FIX: Select specific columns
SELECT id, name, email FROM users;

-- ANTI-PATTERN 3: TIMESTAMP without timezone
CREATE TABLE events (happened_at TIMESTAMP);
-- FIX: Always use TIMESTAMPTZ
CREATE TABLE events (happened_at TIMESTAMPTZ);

-- ANTI-PATTERN 4: Implicit casts in WHERE (defeats indexes)
CREATE TABLE users (id BIGINT);
SELECT * FROM users WHERE id = '123';  -- Implicit cast, may not use index
-- FIX: Cast explicitly to document intent
SELECT * FROM users WHERE id = 123::BIGINT;

-- ANTI-PATTERN 5: Missing FK indexes
CREATE TABLE orders (user_id BIGINT REFERENCES users(id));
-- Queries by user_id are slow
-- FIX: Create index
CREATE INDEX ON orders (user_id);

-- ANTI-PATTERN 6: Retrying on sequence gaps
-- DON'T: Try to fill gaps in IDENTITY sequences
-- Gaps are normal and expected from rollbacks/crashes

-- ANTI-PATTERN 7: Using SERIAL for distributed systems
-- SERIAL is single-node only
CREATE TABLE users (id SERIAL);
-- FIX: Use BIGINT GENERATED ALWAYS AS IDENTITY or UUID
CREATE TABLE users (id BIGINT GENERATED ALWAYS AS IDENTITY);
```

## Monitoring Queries

```sql
-- Find missing indexes on foreign keys
SELECT
    tc.table_name,
    kcu.column_name,
    (SELECT COUNT(*) FROM pg_indexes WHERE tablename = tc.table_name) AS index_count
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE tablename = tc.table_name
    AND indexdef LIKE '%' || kcu.column_name || '%'
);

-- Find unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(relid) DESC;

-- Find table bloat
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Find long-running queries
SELECT pid, usename, application_name, state, query_start, state_change
FROM pg_stat_activity
WHERE state = 'active'
AND query NOT LIKE '%pg_stat_activity%'
ORDER BY query_start;
```

## Query Performance Framework

### EXPLAIN ANALYZE Workflow

Always run `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) <your query>` to understand actual query execution:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT o.*, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'pending';
```

**Key things to look for:**

- **Sequential scans on large tables** (>10k rows): Indicates missing index. If you see `Seq Scan on orders (cost=0.00..50000.00)` on a large table, create an index on the filtered column.
- **Rows estimate vs actual rows mismatch**: If `Rows: 1000 (actual time=...)` shows actual is vastly different from estimate, stats are stale. Run `ANALYZE table_name` after bulk inserts/deletes to update statistics.
- **Nested loop joins with large row counts**: `Nested Loop (cost=...)` is fine for small inner sets, dangerous for large ones. Consider a hash join by creating better indexes.
- **Buffer statistics**: High `shared hit ratio` (>99%) is good (cache hits); high `read ratio` indicates evictions or missing indexes (cache misses).

**After bulk operations**, always update statistics:

```sql
ANALYZE table_name;  -- Recompute statistics for the table
ANALYZE;             -- Recompute all table statistics
```

### Index Strategy

Choose the right index type for your query pattern:

- **B-tree**: Default for equality (`=`), range (`<`, `>`, `BETWEEN`), ordering (`ORDER BY`), prefix patterns (`LIKE 'prefix%'`)
- **GIN** (Generalized Inverted Index): Multi-value columns — arrays, JSONB, full-text search (`tsvector`). Use `jsonb_path_ops` for containment-heavy queries.
- **GiST** (Generalized Search Tree): Geometric types, full-text search, range overlaps (`&&`)
- **Partial index**: Index only a subset of rows. `CREATE INDEX ON orders (status) WHERE status = 'pending'` is dramatically smaller and faster for filtered queries.
- **Composite index column order**: Equality predicates first, then range predicates. For `WHERE user_id = ? AND created_at > ?`, use `CREATE INDEX ON orders (user_id, created_at)`.
- **Covering index** (Index-Only Scan): `CREATE INDEX ON orders (customer_id) INCLUDE (status, total)` includes non-key columns so the index satisfies the query without visiting the heap.

```sql
-- Partial index example: only active orders
CREATE INDEX active_orders_idx ON orders (id) WHERE status = 'active';

-- Covering index example: avoid heap fetch
CREATE INDEX orders_customer_idx ON orders (customer_id) INCLUDE (status, total);

-- Composite with range: equality first
CREATE INDEX orders_user_time_idx ON orders (customer_id, created_at);
```

### Common Anti-Patterns

- **SELECT \***: Fetches unnecessary columns, inflates I/O, and prevents index-only scans. Always select specific columns.
- **Functions on indexed columns in WHERE**: `WHERE LOWER(email) = 'alice@example.com'` defeats the index. Create a functional index instead: `CREATE INDEX ON users (LOWER(email))`.
- **CTE inlining**: In PostgreSQL 12+, CTEs are inlined by default (not a materialization fence). If you need the CTE result materialized, add `MATERIALIZED` keyword: `WITH temp AS MATERIALIZED (SELECT ...)`.
- **N+1 query pattern**: Looping in application code and running a query per row. Use `JOIN` or `IN (subquery)` to fetch all rows in one query.

### Connection Pooling with PgBouncer

PgBouncer sits between your application and PostgreSQL, reusing connections efficiently:

**Pool modes:**
- **Transaction mode** (recommended): Connection returned to pool after each transaction. Fits most applications.
- **Session mode**: Connection held for entire client session. Required for prepared statements, advisory locks, temp tables. Needs higher connection count.

**Sizing formula:**
```
max_connections (PostgreSQL) = PgBouncer pool_size × number_of_app_servers
```

**Key settings:**
```ini
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25  # Start conservative, monitor and adjust
```

**Monitor pool health:**
```sql
-- From PgBouncer admin console
SHOW POOLS;   -- Current active/waiting connections
SHOW STATS;   -- Requests, bytes, timing stats
```

## Row-Level Security (RLS)

Row-level security (RLS) lets the database enforce who can see which rows, moving authorization from application code to the database.

### Setup

```sql
-- Enable RLS on a table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Force even the table owner to go through policies
-- (critical for FORCE ROLE testing)
ALTER TABLE orders FORCE ROW LEVEL SECURITY;

-- Disable RLS (careful!)
ALTER TABLE orders DISABLE ROW LEVEL SECURITY;
```

### Policy Patterns

**Tenant isolation (multi-tenant SaaS):**
```sql
-- Only rows matching the current tenant can be accessed
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- At connection time, set the tenant context
SET app.tenant_id = 'acme-corp-uuid';
SELECT * FROM orders;  -- Only acme-corp's orders are visible
```

**User-owned rows:**
```sql
-- Users can only see/modify their own documents
CREATE POLICY user_rows ON documents
  USING (owner_id = current_user_id())
  WITH CHECK (owner_id = current_user_id());
-- USING: applies to SELECT and UPDATE
-- WITH CHECK: applies to INSERT and UPDATE
```

**Read-only for non-owners:**
```sql
-- Anyone can read published articles, but only owner can modify
CREATE POLICY read_published ON articles
  FOR SELECT USING (status = 'published');

CREATE POLICY owner_modify ON articles
  FOR UPDATE USING (author_id = current_user_id());
```

### Performance Considerations

- **RLS adds the policy predicate to every query**: The policy `WHERE tenant_id = current_setting(...)` is appended to all queries on that table. **Index the policy column** (tenant_id, owner_id, etc.) to avoid full table scans.
- **SECURITY DEFINER functions bypass RLS**: Functions defined with `SECURITY DEFINER` execute with the function owner's privileges, bypassing RLS checks. Use sparingly and review carefully.
- **Test as application role**: Set your session to the application's actual role and verify policies work: `SET ROLE app_user; SELECT * FROM orders;`

**Always test with FORCE ROW LEVEL SECURITY and the application's actual role to catch gaps.**

## Agent Support

- **sql-expert** — Query optimization and complex SQL patterns
- **postgresql-specific** — PostgreSQL internals and extensions (when available)

## Skill References

- **python-resilience** — Handling database connection failures with retries
- **async-python-patterns** — Async database operations with asyncpg
