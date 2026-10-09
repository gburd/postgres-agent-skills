---
title: Partition Large Tables — When It Actually Helps
impact: MEDIUM-HIGH
impactDescription: Partition pruning and instant drop of old data; not a universal speedup
tags: partitioning, range, list, hash, pruning, time-series
---

## Partition Large Tables — When It Actually Helps

Declarative partitioning splits one logical table into physical partitions.
Its wins are **partition pruning** (scan only the relevant partitions) and
**instant data lifecycle** (`DROP`/`DETACH` a partition instead of a
long `DELETE`). It is not a blanket "make big tables fast" switch — a query
whose predicate doesn't match the partition key still scans everything, now
with extra planning overhead.

**Incorrect:**

```sql
-- 500M-row events table; dropping a year of data takes hours and bloats
delete from events where created_at < '2023-01-01';
```

**Correct:**

```sql
create table events (
  id         bigint generated always as identity,
  created_at timestamptz not null,
  data       jsonb
) partition by range (created_at);

create table events_2024_01 partition of events
  for values from ('2024-01-01') to ('2024-02-01');

-- queries that filter on created_at prune to the matching partitions
select * from events where created_at >= '2024-01-15';

-- lifecycle is instant and lock-light
drop table events_2023_01;          -- vs a multi-hour DELETE
```

Partition when the table is large *and* queries filter on the partition key,
or you need cheap time-based retention. Attach/detach with `CONCURRENTLY`
(PG 14+) to avoid long locks. Note the partition key must be part of any
primary key or unique constraint.

Reference: [Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
