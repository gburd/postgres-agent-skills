---
title: Triage Load With pg_stat_statements — and Mind That It's Cumulative
impact: MEDIUM
impactDescription: Finds the queries that actually cost the most, in aggregate
tags: pg-stat-statements, monitoring, triage, cumulative, reset
---

## Triage Load With pg_stat_statements — and Mind That It's Cumulative

`pg_stat_statements` aggregates execution stats per normalised query. It is the
first place to look for "what is this database spending its time on". The
answer is usually not the slowest single query but a fast query run millions of
times — sort by *total* time to find it.

**Correct:**

```sql
create extension if not exists pg_stat_statements;  -- also needs preloading

-- biggest total cost (frequency x per-call cost)
select calls,
       round(total_exec_time)::bigint as total_ms,
       round(mean_exec_time)::bigint  as mean_ms,
       query
from   pg_stat_statements
order  by total_exec_time desc
limit  20;
```

**The trap:** these counters are cumulative since the last reset or server
start. A query that was fixed and redeployed days ago still shows its old,
expensive shape in the totals. Before trusting the top-N, check when stats were
last reset, and reset to measure a clean window after a change:

```sql
select stats_reset from pg_stat_statements_info;  -- how old is this data?
select pg_stat_statements_reset();                -- start a fresh window
-- ...let representative traffic run, then re-query the top-N
```

Reference: [pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html)
