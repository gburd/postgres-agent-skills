---
title: Enable Row Security for Multi-Tenant Data
impact: CRITICAL
impactDescription: Database-enforced isolation; a code bug can no longer leak another tenant's rows
tags: rls, row-level-security, multi-tenant, isolation
---

## Enable Row Security for Multi-Tenant Data

Filtering by tenant only in application code means one missing `WHERE` clause —
or one SQL-injection — exposes everyone's data. Row-level security (RLS) moves
the filter into the database, where it cannot be forgotten.

**Incorrect:**

```sql
-- isolation depends on every query remembering the filter
select * from orders where tenant_id = $1;   -- forget this once -> full leak
```

**Correct:**

```sql
alter table orders enable row level security;
-- owners bypass RLS by default; FORCE makes the policy apply to them too
alter table orders force row level security;

-- the policy is an implicit WHERE added to every query on the table
create policy tenant_isolation on orders
  using (tenant_id = current_setting('app.tenant_id')::bigint);

-- the app sets the tenant for the transaction, then queries normally
set local app.tenant_id = '42';
select * from orders;        -- only tenant 42's rows
```

Set the tenant with `SET LOCAL` inside the transaction so it is safe under a
transaction-mode pooler (see `conn-pool-modes`). Managed platforms often expose
their own identity function (for example an `auth.uid()`-style helper) — the
mechanism is identical; substitute it for `current_setting(...)`. Keep RLS fast
with `security-rls-performance`.

Reference: [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
