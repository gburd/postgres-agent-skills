# Rule sections

Rules are grouped by filename prefix. Impact ordering runs from CRITICAL
(fix first) to LOW-MEDIUM (fix when the critical work is done).

## 1. Query performance (`query-`)
**Impact:** CRITICAL
Missing indexes, wrong index type, bad plans. The single most common source of
Postgres performance problems.

- `query-missing-indexes` — index WHERE and JOIN columns
- `query-composite-indexes` — multi-column indexes and column order
- `query-covering-indexes` — INCLUDE columns for index-only scans
- `query-partial-indexes` — index only the rows you query
- `query-index-types` — B-tree vs GIN vs GiST vs BRIN vs Hash vs SP-GiST
- `query-not-in-null` — the `NOT IN (subquery)` NULL trap

## 2. Connection management (`conn-`)
**Impact:** CRITICAL
Connection pooling, limits, timeouts. Critical for any app with real
concurrency.

- `conn-pooling` — pool, don't open a connection per request
- `conn-pool-modes` — transaction vs session pooling
- `conn-prepared-statements` — prepared statements under a pooler
- `conn-limits` — size `max_connections` to RAM, not optimism
- `conn-idle-timeout` — reclaim idle and idle-in-transaction connections

## 3. Security (`security-`)
**Impact:** CRITICAL
Row security, least privilege. A bug here leaks data across tenants.

- `security-rls-basics` — enable row security for multi-tenant data
- `security-rls-performance` — write policies that stay fast
- `security-privileges` — least privilege; never run the app as superuser

## 4. Schema design & correctness (`schema-`)
**Impact:** HIGH
Type choice, keys, constraints. The foundation; mistakes here are expensive to
unwind later.

- `schema-data-types` — text/numeric/boolean over varchar(n)/float/strings
- `schema-timestamptz` — always `timestamptz`, never bare `timestamp`
- `schema-primary-keys` — identity and UUIDv7 over serial and UUIDv4
- `schema-constraints` — add constraints idempotently (no ADD IF NOT EXISTS)
- `schema-foreign-key-indexes` — Postgres does not index FKs for you
- `schema-partitioning` — when and how to partition large tables
- `schema-enum-vs-lookup` — enum vs lookup table trade-offs
- `schema-lowercase-identifiers` — unquoted snake_case for portability

## 5. Concurrency & locking (`lock-`)
**Impact:** MEDIUM-HIGH
Transactions, deadlocks, lock contention.

- `lock-short-transactions` — hold locks for milliseconds, not API calls
- `lock-deadlock-prevention` — lock in a consistent order
- `lock-skip-locked` — SKIP LOCKED work queues
- `lock-advisory` — advisory locks for app-level mutual exclusion

## 6. Data access patterns (`data-`)
**Impact:** MEDIUM
Round-trip elimination, bulk loading, pagination.

- `data-n-plus-one` — batch with ANY(array) or a JOIN
- `data-batch-inserts` — multi-row INSERT and COPY
- `data-pagination` — keyset pagination over OFFSET
- `data-upsert` — INSERT ... ON CONFLICT done right

## 7. Monitoring & diagnostics (`monitor-`)
**Impact:** MEDIUM
See what the database is actually doing.

- `monitor-explain-analyze` — read EXPLAIN (ANALYZE, BUFFERS)
- `monitor-pg-stat-statements` — triage top queries (and its cumulative trap)
- `monitor-bloat` — detect table and index bloat
- `monitor-locks` — find the blocking query

## 8. Operations & maintenance (`ops-`)
**Impact:** MEDIUM-HIGH
Keeping a live database healthy over its lifetime.

- `ops-migration-safety` — online DDL without locking out the app
- `ops-timeout-hygiene` — lock_timeout / statement_timeout / idle timeouts
- `ops-autovacuum` — tune autovacuum; watch XID wraparound
- `ops-extension-upgrades` — upgrade extensions without breaking the database
- `ops-logical-replication` — the restrictions that bite in production

## 9. Advanced features (`advanced-`)
**Impact:** LOW-MEDIUM
Postgres features that replace bolt-on infrastructure.

- `advanced-full-text-search` — tsvector + GIN over LIKE '%...%'
- `advanced-jsonb-indexing` — GIN operator classes and expression indexes
