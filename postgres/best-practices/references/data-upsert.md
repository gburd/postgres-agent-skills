---
title: Upsert With INSERT ... ON CONFLICT, Not Check-Then-Insert
impact: MEDIUM
impactDescription: One atomic statement; no race, no duplicate-key error
tags: upsert, on-conflict, insert, concurrency, excluded
---

## Upsert With INSERT ... ON CONFLICT, Not Check-Then-Insert

Checking whether a row exists and then inserting it is a race: two sessions both
see "absent" and both insert, and one gets a duplicate-key error. `INSERT ...
ON CONFLICT` does the whole thing atomically.

**Incorrect:**

```sql
-- two sessions run this concurrently; both find nothing, both insert
select 1 from settings where user_id = 123 and key = 'theme';
insert into settings (user_id, key, value) values (123, 'theme', 'dark');
-- one succeeds, the other errors on the unique constraint
```

**Correct:**

```sql
insert into settings (user_id, key, value)
values (123, 'theme', 'dark')
on conflict (user_id, key)
do update set value = excluded.value, updated_at = now()
returning *;
```

`ON CONFLICT` needs a unique index or constraint on the conflict target —
`(user_id, key)` here. Use `DO NOTHING` for insert-or-ignore. Reference the
proposed row with the `excluded` pseudo-table in the `DO UPDATE` clause.

Reference: [INSERT ... ON CONFLICT](https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT)
