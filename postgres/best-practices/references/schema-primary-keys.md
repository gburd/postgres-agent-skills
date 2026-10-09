---
title: Prefer identity and UUIDv7 Over serial and UUIDv4
impact: HIGH
impactDescription: Sequential keys preserve index locality and insert speed
tags: primary-key, identity, serial, uuid, uuidv7, fragmentation
---

## Prefer identity and UUIDv7 Over serial and UUIDv4

For a single-database primary key, `bigint generated always as identity` is the
SQL-standard choice: 8 bytes, sequential, and it refuses accidental inserts
into the identity column. `serial` still works but is legacy. If you need keys
that are unique across systems or safe to expose, use a *time-ordered* UUID
(v7), not random v4 — random keys scatter inserts across the index and cause
write amplification and bloat.

**Incorrect:**

```sql
create table users  (id serial primary key);                 -- legacy
create table orders (id uuid default gen_random_uuid()        -- v4 = random
                     primary key);                            -- scattered inserts
```

**Correct:**

```sql
-- local, sequential, SQL-standard
create table users (id bigint generated always as identity primary key);

-- distributed / externally-exposed: time-ordered UUID keeps index locality.
-- PostgreSQL 18+ ships uuidv7(); earlier versions need an extension.
create table orders (id uuid default uuidv7() primary key);
```

A sequential key clusters recent rows at the right edge of the B-tree, so
inserts touch few pages and the index stays dense. Random v4 keys touch random
pages on every insert.

Reference: [Identity Columns](https://www.postgresql.org/docs/current/ddl-identity-columns.html) · [UUID Functions](https://www.postgresql.org/docs/current/functions-uuid.html) · [Don't use serial (wiki)](https://wiki.postgresql.org/wiki/Don%27t_Do_This#Don.27t_use_serial)
