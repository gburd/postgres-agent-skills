---
name: postgres-user
description: >
  PostgreSQL skills for someone who writes and runs queries against an existing
  database: SELECTs, DML, reporting, application queries. Use when writing or
  reviewing SQL, choosing how to filter/join/paginate, batching work, avoiding
  N+1 round trips, or wondering why a query is slow. This is the query-author's
  view; for schema design use postgres-dba, for reviewing someone else's design
  use postgres-overseer.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
  persona: user
---

# PostgreSQL — User (query author)

You write queries against a database someone else designed. Your job is to get
correct results efficiently without needing to change the schema. These are the
rules that matter most for that.

## When to apply

Writing or reviewing any `SELECT`/`INSERT`/`UPDATE`/`DELETE`, building a report,
wiring an application query, or chasing a slow statement you did not expect to
be slow.

## Core rules (in `../best-practices/references/`)

Read the rule file for the full antipattern/fix/why:

- **Filter and join on indexed columns** — `query-missing-indexes.md`. If a
  column you filter on is not indexed, that is a note for the DBA
  (`postgres-dba`), but first confirm the query really needs it.
- **Let composite indexes work for you** — `query-composite-indexes.md`:
  order predicates to match an existing index's leading columns.
- **Never `NOT IN (subquery)`** — `query-not-in-null.md`: one NULL silently
  empties the result. Use `NOT EXISTS`. This is a correctness bug, not a
  performance one.
- **Paginate by keyset, not OFFSET** — `data-pagination.md`: deep `OFFSET`
  pages get linearly slower; seek past the last row instead.
- **Kill N+1 round trips** — `data-n-plus-one.md`: one `= ANY($1::bigint[])`
  or a JOIN instead of a query per row.
- **Batch writes** — `data-batch-inserts.md`: multi-row `VALUES` or `COPY`.
- **Upsert atomically** — `data-upsert.md`: `INSERT ... ON CONFLICT`, never
  check-then-insert (it races).

## Diagnosing your own slow query

Before asking a DBA, read `../best-practices/references/monitor-explain-analyze.md`
and run:

```sql
explain (analyze, buffers) <your query>;
```

A `Seq Scan` on a big table with a selective filter, or a large "Rows Removed
by Filter", usually means a missing or unusable index — take that finding to
`postgres-dba` with the plan attached, rather than guessing.

## What is out of scope for you

Creating indexes, altering tables, changing server settings, and granting
privileges belong to `postgres-dba`. If a query can only be made fast by a
schema or index change, say so and hand it over with evidence (the plan),
rather than contorting the SQL.
