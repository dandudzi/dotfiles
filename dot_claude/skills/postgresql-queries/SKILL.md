---
name: postgresql-queries
description: PostgreSQL query patterns, window functions, CTEs, performance optimization, monitoring, RLS, and anti-patterns.
origin: ECC
model: sonnet
---

# PostgreSQL Queries

## When to Activate

- Writing complex queries with window functions
- Deciding between CTEs and subqueries
- Optimizing query performance
- Monitoring long-running queries
- Implementing row-level security
- Identifying query anti-patterns

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
| Large intermediate result | CTE with materialization | Can materialize with `MATERIALIZED` keyword |

```sql
-- CTE for clarity and reuse
WITH active_users AS (
    SELECT * FROM users WHERE is_active = true
),
user_orders AS (
    SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id
)
SELECT u.name, uo.order_count
FROM active_users u
JOIN user_orders uo ON u.id = uo.user_id;

-- Recursive CTE for hierarchy
WITH RECURSIVE org_tree AS (
    SELECT id, name, manager_id, 0 as level FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, ot.level + 1
    FROM employees e
    JOIN org_tree ot ON e.manager_id = ot.id
)
SELECT * FROM org_tree ORDER BY level, name;

-- CTE clarity vs nested subqueries
-- Instead of: SELECT u.name FROM users u WHERE u.id IN (SELECT user_id FROM orders WHERE id IN (SELECT order_id FROM order_items WHERE price > 100))
WITH expensive_items AS (
    SELECT order_id FROM order_items WHERE price > 100
),
relevant_orders AS (
    SELECT DISTINCT user_id FROM orders WHERE id IN (SELECT order_id FROM expensive_items)
)
SELECT name FROM users WHERE id IN (SELECT user_id FROM relevant_orders);
```

## Query Performance Framework

### EXPLAIN ANALYZE Workflow

Always run `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) <your query>` to understand actual query execution. Key signals:

- **Sequential scans on large tables** (>10k rows): Missing index. Create index on filtered column.
- **Rows estimate vs actual mismatch**: Stats are stale. Run `ANALYZE table_name` after bulk operations.
- **Nested loop joins with large row counts**: Dangerous at scale. Create better indexes or use hash join.
- **Buffer statistics**: High `shared hit ratio` (>99%) is good; high `read ratio` indicates evictions or missing indexes.

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT o.*, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'pending';

-- After bulk operations, always update statistics:
ANALYZE table_name;  -- Recompute for one table
ANALYZE;             -- Recompute all statistics
```

### Index Strategy for Query Optimization

- **B-tree**: Default for equality (`=`), range (`<`, `>`, `BETWEEN`), ordering, prefix patterns
- **GIN**: Multi-value columns — arrays, JSONB, full-text. Use `jsonb_path_ops` for containment-heavy queries
- **GiST**: Geometric types, full-text search, range overlaps (`&&`)
- **Partial index**: Index only a subset. `CREATE INDEX ON orders (status) WHERE status = 'pending'` is smaller and faster
- **Composite column order**: Equality predicates first, then range. For `WHERE user_id = ? AND created_at > ?`, use `CREATE INDEX ON orders (user_id, created_at)`
- **Covering index**: `CREATE INDEX ON orders (customer_id) INCLUDE (status, total)` satisfies query without heap visit

```sql
-- Partial index example: only active orders
CREATE INDEX active_orders_idx ON orders (id) WHERE status = 'active';

-- Covering index example: avoid heap fetch
CREATE INDEX orders_customer_idx ON orders (customer_id) INCLUDE (status, total);

-- Composite with range: equality first
CREATE INDEX orders_user_time_idx ON orders (customer_id, created_at);
```

### Connection Pooling with PgBouncer

PgBouncer sits between application and PostgreSQL, reusing connections efficiently.

**Pool modes:**
- **Transaction mode** (recommended): Connection returned to pool after each transaction
- **Session mode**: Connection held for entire client session. Required for prepared statements, advisory locks, temp tables

**Sizing:**
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
SHOW POOLS;   -- Current active/waiting connections
SHOW STATS;   -- Requests, bytes, timing stats
```

## Monitoring Queries

```sql
-- Find missing indexes on foreign keys
SELECT tc.table_name, kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE tablename = tc.table_name
    AND indexdef LIKE '%' || kcu.column_name || '%'
);

-- Find unused indexes (idx_scan = 0 means never used)
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

## Row-Level Security (RLS)

Row-level security lets the database enforce who can see which rows, moving authorization from application code to the database.

### Setup

```sql
-- Enable RLS on a table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Force even the table owner to go through policies
ALTER TABLE orders FORCE ROW LEVEL SECURITY;

-- Disable RLS
ALTER TABLE orders DISABLE ROW LEVEL SECURITY;
```

### Policy Patterns

**Tenant isolation (multi-tenant SaaS):**
```sql
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- At connection time, set the tenant context
SET app.tenant_id = 'acme-corp-uuid';
SELECT * FROM orders;  -- Only acme-corp's orders are visible
```

**User-owned rows:**
```sql
CREATE POLICY user_rows ON documents
  USING (owner_id = current_user_id())
  WITH CHECK (owner_id = current_user_id());
-- USING: applies to SELECT and UPDATE
-- WITH CHECK: applies to INSERT and UPDATE
```

**Read-only for non-owners:**
```sql
CREATE POLICY read_published ON articles
  FOR SELECT USING (status = 'published');

CREATE POLICY owner_modify ON articles
  FOR UPDATE USING (author_id = current_user_id());
```

### RLS Performance & Testing

- **Index the policy column**: RLS appends the policy predicate to all queries. Always index policy columns (tenant_id, owner_id, etc.)
- **SECURITY DEFINER bypasses RLS**: Functions with `SECURITY DEFINER` execute with owner's privileges, bypassing checks. Use sparingly
- **Test as application role**: Verify policies work: `SET ROLE app_user; SELECT * FROM orders;`

Always test with `FORCE ROW LEVEL SECURITY` and the application's actual role to catch gaps.

## Anti-Patterns

- **SELECT ***: Fetches unnecessary columns, prevents index-only scans. Always select specific columns
- **Functions on indexed columns in WHERE**: `WHERE LOWER(email) = '...'` defeats indexes. Use functional indexes instead
- **Implicit casts in WHERE**: `WHERE id = '123'` (string) doesn't use index. Cast explicitly: `WHERE id = 123::BIGINT`
- **CTE inlining**: In PostgreSQL 12+, CTEs are inlined by default. Add `MATERIALIZED` if result must be cached: `WITH temp AS MATERIALIZED (...)`
- **N+1 query pattern**: Looping in application code and running one query per row. Use `JOIN` or `IN (subquery)` instead
- **CHAR(n) for variable-length strings**: Wastes space, requires TRIM in queries. Use TEXT with CHECK constraint
- **TIMESTAMP without timezone**: Ambiguous across regions. Always use TIMESTAMPTZ
- **Missing FK indexes**: Foreign key columns slow down lookups. Always create indexes on referencing columns
- **Retrying on sequence gaps**: Gaps from rollbacks/crashes are normal. Never try to "fix" them
- **SERIAL for distributed systems**: Single-node only. Use `BIGINT GENERATED ALWAYS AS IDENTITY` or UUID
- **REAL for money**: Precision loss. Use NUMERIC(precision, scale)
- **LIKE is case-sensitive**: Use `ILIKE` or `LOWER()` for case-insensitive matching

## Agent Support

- **sql-expert** — Query optimization and complex SQL patterns
- **postgresql-specific** — PostgreSQL internals and extensions
