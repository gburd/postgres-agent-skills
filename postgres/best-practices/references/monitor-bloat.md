---
title: Watch for Table and Index Bloat
impact: MEDIUM
impactDescription: Catches wasted space and slow scans before they hurt
tags: bloat, vacuum, pgstattuple, dead-tuples, reindex
---

## Watch for Table and Index Bloat

Postgres marks updated and deleted rows dead rather than removing them in place;
autovacuum reclaims the space for reuse but does not shrink the file. Heavy
update/delete churn, or a long-running transaction that holds back the
cleanup horizon, lets dead space accumulate — scans read more pages than they
need to.

**Correct:**

```sql
-- quick signal: dead tuples relative to live, and last (auto)vacuum
select relname,
       n_live_tup, n_dead_tup,
       round(100 * n_dead_tup / nullif(n_live_tup + n_dead_tup, 0), 1) as dead_pct,
       last_autovacuum
from   pg_stat_user_tables
order  by n_dead_tup desc
limit  20;

-- precise (but heavier) measurement of a specific relation
create extension if not exists pgstattuple;
select * from pgstattuple('orders');
select * from pgstatindex('orders_pkey');
```

If a table is genuinely bloated: first make sure autovacuum can keep up (see
`ops-autovacuum`) and that no long-idle transaction is pinning the horizon (see
`conn-idle-timeout`). To reclaim space already lost, prefer an online repack
tool (e.g. `pg_repack`) over `VACUUM FULL`, which takes an exclusive lock and
rewrites the whole table. For index bloat, `REINDEX CONCURRENTLY`.

Reference: [Routine Vacuuming](https://www.postgresql.org/docs/current/routine-vacuuming.html) · [pgstattuple](https://www.postgresql.org/docs/current/pgstattuple.html)
