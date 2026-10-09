---
title: Always Use timestamptz, Never Bare timestamp
impact: HIGH
impactDescription: Eliminates an entire class of timezone and DST data bugs
tags: timestamptz, timestamp, timezone, datetime, correctness
---

## Always Use timestamptz, Never Bare timestamp

`timestamp` (without time zone) stores wall-clock numbers with no reference
point: the same column can mean two different instants depending on who wrote
it. `timestamptz` stores an absolute instant (UTC internally) and converts for
display. Store instants as `timestamptz`; the storage size is identical.

**Incorrect:**

```sql
create table events (occurred_at timestamp);   -- which zone? nobody knows
-- a server in a different zone, or a DST change, now means a different instant
insert into events values ('2024-03-10 02:30:00');
```

**Correct:**

```sql
create table events (occurred_at timestamptz not null default now());
-- stored as an absolute instant; rendered in the session's time zone
insert into events (occurred_at) values ('2024-03-10 02:30:00-05');
```

Reserve bare `timestamp` for a genuine wall-clock-without-zone concept (a
recurring "09:00 local" alarm). Also avoid `BETWEEN` on timestamps for "a given
day" — it includes the upper bound; use `>= day AND < day + interval '1 day'`.

Reference: [Date/Time Types](https://www.postgresql.org/docs/current/datatype-datetime.html) · [Don't use timestamp without time zone (wiki)](https://wiki.postgresql.org/wiki/Don%27t_Do_This#Don.27t_use_timestamp_.28without_time_zone.29)
