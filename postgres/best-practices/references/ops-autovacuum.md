---
title: Tune Autovacuum and Watch XID Wraparound
impact: MEDIUM-HIGH
impactDescription: Keeps plans accurate, space reclaimed, and the database writable
tags: autovacuum, analyze, wraparound, freeze, statistics
---

## Tune Autovacuum and Watch XID Wraparound

Autovacuum does two essential jobs: reclaiming dead-tuple space and keeping
planner statistics current (`ANALYZE`), and freezing old rows to prevent
transaction-ID (XID) wraparound. Leave it on. Tune it per-table for hot tables,
and monitor wraparound age — if freezing falls far enough behind, Postgres will
refuse new writes to protect data.

**Incorrect:**

```sql
-- turning autovacuum off "because it causes IO" — this is how you get
-- bloat, bad plans, and eventually a wraparound-forced shutdown
alter table orders set (autovacuum_enabled = false);
```

**Correct:**

```sql
-- make a high-churn table vacuum/analyze sooner than the global defaults
alter table orders set (
  autovacuum_vacuum_scale_factor  = 0.05,   -- vacuum at 5% dead (default 20%)
  autovacuum_analyze_scale_factor = 0.02    -- analyze at 2% changed (default 10%)
);

-- watch wraparound headroom: how close any table is to the freeze limit
select datname, age(datfrozenxid) as xid_age
from   pg_database order by xid_age desc;

-- analyze after a big bulk load so plans use fresh stats immediately
analyze orders;
```

Signs autovacuum is behind: rising `n_dead_tup` (see `monitor-bloat`), growing
`age(datfrozenxid)`, or warnings about wraparound in the log. The usual blocker
is a long-running or idle transaction pinning the horizon — fix that first (see
`conn-idle-timeout`).

Reference: [Routine Vacuuming](https://www.postgresql.org/docs/current/routine-vacuuming.html) · [Automatic Vacuuming](https://www.postgresql.org/docs/current/runtime-config-autovacuum.html)
