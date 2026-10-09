---
name: postgres-best-practices
description: >
  PostgreSQL best practices for Postgres running anywhere — schema, queries,
  indexing, security, concurrency, data access, monitoring, operations, and
  advanced features. Load this skill BEFORE writing or changing anything that
  touches a Postgres database: creating or altering tables and columns
  (including choosing types), schema design, migrations and online DDL, row
  security policies, indexes, triggers, functions, queues and scheduled jobs,
  full-text and JSONB queries, partitioning, logical replication, connection
  pooling, and extension upgrades. Also load it when diagnosing slow queries,
  high CPU, timeouts, EXPLAIN plans, connection exhaustion, locking,
  deadlocks, bloat, autovacuum/wraparound trouble, or rows visible to the
  wrong tenant. Schema, migration, security, and SQL authoring tasks all need
  these rules — even a one-column change or a single query.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
  abstract: >
    PostgreSQL best-practice ruleset for AI coding agents and the developers
    who run them. Rules are grouped into nine impact-ordered categories, from
    critical (query performance, connection management, security) through
    schema, concurrency, data access, monitoring, operations, to advanced
    features. Each rule names the antipattern, shows the fix in runnable SQL,
    explains why it matters, and cross-references the canonical PostgreSQL
    documentation that informed it. Written from scratch and dedicated to the
    public domain (CC0-1.0); ideas drawn from the PostgreSQL manual, the
    project wiki, and the wider community, re-expressed in original words.
---

# PostgreSQL Best Practices (shared rule library)

A best-practice ruleset for Postgres running anywhere — managed service,
container, bare metal. Each rule is short, example-driven, and anchored to the
canonical PostgreSQL documentation so you can trace it back to the source.

This is the **shared library** the role personas cite: `../user`, `../dba`,
`../overseer`, `../replication`, `../triage`, and `../developer` each point into
these rules rather than duplicating them. You can also load it directly when a
task spans roles.

This library is deliberately *not* tied to any hosting product. Where a cloud
platform adds its own identity function or pooler, the rule shows the standard
Postgres mechanism and notes where a platform substitutes its own.

## When to apply

Reach for these rules whenever you:

- author or review SQL — queries, DML, DDL;
- design a schema or pick a column type;
- write a migration, especially one that runs against a live database;
- add or choose an index;
- write or audit a row security policy or privilege grant;
- diagnose slow queries, timeouts, locking, deadlocks, bloat, or connection
  exhaustion;
- operate the database — vacuum, autovacuum, replication, extension upgrades.

Even a single-column change or a one-line query benefits: the correctness
antipatterns (bare `timestamp`, `NOT IN (subquery)`, `serial`) bite hardest in
"trivial" changes.

## Rule categories, by impact

| # | Category | Impact | Prefix |
|---|----------|--------|--------|
| 1 | Query performance | CRITICAL | `query-` |
| 2 | Connection management | CRITICAL | `conn-` |
| 3 | Security | CRITICAL | `security-` |
| 4 | Schema design & correctness | HIGH | `schema-` |
| 5 | Concurrency & locking | MEDIUM-HIGH | `lock-` |
| 6 | Data access patterns | MEDIUM | `data-` |
| 7 | Monitoring & diagnostics | MEDIUM | `monitor-` |
| 8 | Operations & maintenance | MEDIUM-HIGH | `ops-` |
| 9 | Advanced features | LOW-MEDIUM | `advanced-` |

## How to use

Each rule lives in `references/{prefix}-{name}.md`. Load the ones relevant to
the task; the index is in [`references/_sections.md`](references/_sections.md).
Every rule file follows the same shape:

- a one-line statement of the rule;
- **Incorrect** — the antipattern, in runnable SQL;
- **Correct** — the fix, in runnable SQL;
- a short "why it matters";
- `Reference:` — the canonical PostgreSQL doc (or project wiki) that informed it.

## The short version

If you read nothing else, these are the rules that prevent the most pain:

- Index the columns you filter and join on; index every foreign key.
- Use `timestamptz`, `text`, `numeric`, and `bigint generated always as
  identity`. Never bare `timestamp`, `char(n)`, `money`, `serial`, or `int`
  for keys.
- Never `NOT IN (subquery)` — a single NULL silently empties the result. Use
  `NOT EXISTS`.
- Run schema migrations online: `CREATE INDEX CONCURRENTLY`, add nullable
  columns, set a short `lock_timeout` and retry.
- Keep transactions short; set `statement_timeout` and
  `idle_in_transaction_session_timeout`.
- Pool connections; know your pool mode (transaction vs session) and its
  prepared-statement caveats.
- Enable `pg_stat_statements`, but remember it is cumulative — check its reset
  time before trusting the top-N.
- Before bumping an extension, read its upgrade notes; some versions require a
  `REINDEX`.

## Attribution & license

Written from scratch and dedicated to the public domain under
[CC0-1.0](../LICENSE). The rule topics were informed by the PostgreSQL manual
(PostgreSQL License), the PostgreSQL project wiki (CC-BY-SA-3.0 — ideas only,
no text reused), and the wider community's accumulated practice. No text was
copied from any copyleft or proprietary source; each rule is original
expression. Canonical references are cited per rule so you can connect each
rule to its origin.
