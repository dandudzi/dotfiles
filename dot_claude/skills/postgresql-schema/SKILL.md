---
name: postgresql-schema
description: PostgreSQL schema design, data types, indexing patterns, constraints, transaction isolation, JSONB, and upserts.
origin: ECC
model: sonnet
---

# PostgreSQL Schema

## When to Activate

- Designing PostgreSQL schemas
- Selecting appropriate data types
- Creating indexes for performance
- Building JSONB query strategies
- Implementing upserts and constraints

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

### Data Type Gotchas

```sql
-- VARCHAR(n) silently errors on overflow
CREATE TABLE users (name VARCHAR(50));
INSERT INTO users VALUES ('This very long name exceeds fifty characters limit');  -- ERROR

-- FIX: Use TEXT with CHECK constraint
CREATE TABLE users (name TEXT NOT NULL CHECK (LENGTH(name) <= 50));

-- CHAR(n) pads with spaces, queries need TRIM
CREATE TABLE users (code CHAR(10));
SELECT * FROM users WHERE code = 'ABC';  -- No match, expects 'ABC       '

-- FIX: Use TEXT
CREATE TABLE users (code TEXT NOT NULL);

-- TIMESTAMP without timezone is ambiguous across regions
CREATE TABLE events (happened_at TIMESTAMP);

-- FIX: Always use TIMESTAMPTZ
CREATE TABLE events (happened_at TIMESTAMPTZ NOT NULL);

-- FLOAT for money causes precision loss
INSERT INTO orders (total) VALUES (0.1 + 0.2);  -- Stores ~0.30000000000000004

-- FIX: Use NUMERIC for exact arithmetic
CREATE TABLE orders (total NUMERIC(10,2) NOT NULL);
INSERT INTO orders VALUES (0.30);  -- Stores exactly 0.30
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
CREATE INDEX ON orders (status, total, created_at DESC);

-- WRONG: Range before equality prevents use of range column
CREATE INDEX ON orders (created_at, user_id);  -- Can't use for WHERE user_id = ?
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
-- FIX with NULLS NOT DISTINCT (PG15+)
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
```

## Transaction Isolation Levels

Choose isolation levels based on consistency vs concurrency trade-offs.

```sql
-- READ COMMITTED: Default in PostgreSQL (prevents dirty reads)
BEGIN ISOLATION LEVEL READ COMMITTED;
-- Sees committed data at statement start

-- REPEATABLE READ: Snapshot isolation
BEGIN ISOLATION LEVEL REPEATABLE READ;
-- Consistent snapshot for entire transaction; prevents non-repeatable reads

-- SERIALIZABLE: Serialization isolation (highest safety)
BEGIN ISOLATION LEVEL SERIALIZABLE;
-- Behaves as if transactions ran serially

-- Example: SERIALIZABLE for critical financial operations
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT balance FROM accounts WHERE id = 123;
-- ... check balance ...
UPDATE accounts SET balance = balance - amount WHERE id = 123;
COMMIT;

-- Example: REPEATABLE READ for reports
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT SUM(revenue) FROM orders WHERE date >= '2024-01-01';
SELECT SUM(expenses) FROM expenses WHERE date >= '2024-01-01';
COMMIT;
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
WHERE users.updated_at < EXCLUDED.updated_at;

-- Upsert on composite key
INSERT INTO user_stats (user_id, date, clicks, impressions)
VALUES (123, '2024-01-15', 50, 1000)
ON CONFLICT (user_id, date) DO UPDATE SET
    clicks = user_stats.clicks + EXCLUDED.clicks,
    impressions = user_stats.impressions + EXCLUDED.impressions;
```

## Common Gotchas

- **NULL in UNIQUE allows duplicates**: Use `UNIQUE NULLS NOT DISTINCT` (PostgreSQL 15+)
- **Foreign keys don't auto-index**: Create indexes on referencing columns explicitly
- **Sequences have gaps**: Normal behavior from rollbacks/crashes. Never "fix" gaps
- **LIKE is case-sensitive**: Use `ILIKE` or `LOWER()` for case-insensitive matching
- **CHECK constraints allow NULL**: Combine with `NOT NULL` if required
- **Missing indexes on foreign keys**: Always index referencing columns for fast lookups

## Agent Support

- **sql-expert** — Query optimization and complex SQL patterns
- **postgresql-specific** — PostgreSQL internals and extensions
