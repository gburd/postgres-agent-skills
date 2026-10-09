---
title: Find the Blocking Query When Things Hang
impact: MEDIUM
impactDescription: Turns "the database is stuck" into a named culprit in seconds
tags: locks, pg-locks, blocking, pg-stat-activity, contention
---

## Find the Blocking Query When Things Hang

When queries pile up waiting, you need the blocker, not the blocked. Postgres
exposes who-waits-on-whom directly; `pg_blocking_pids()` is the fast path.

**Correct:**

```sql
-- every waiting backend and the PIDs blocking it
select pid,
       pg_blocking_pids(pid) as blocked_by,
       state,
       wait_event_type, wait_event,
       left(query, 100) as query
from   pg_stat_activity
where  cardinality(pg_blocking_pids(pid)) > 0
order  by pid;

-- inspect, then (deliberately) end the blocker
select pg_cancel_backend(<pid>);     -- cancel its current query
select pg_terminate_backend(<pid>);  -- or drop the whole connection
```

The usual root cause is a long-running or idle-in-transaction session holding a
lock. Fix the cause with short transactions, timeouts, and idle-in-transaction
timeouts (see `lock-short-transactions`, `ops-timeout-hygiene`,
`conn-idle-timeout`) rather than terminating backends by hand on a schedule.

Reference: [Lock Monitoring (wiki)](https://wiki.postgresql.org/wiki/Lock_Monitoring) · [pg_stat_activity](https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ACTIVITY-VIEW)
