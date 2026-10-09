---
title: Write Row-Security Policies That Stay Fast
impact: HIGH
impactDescription: Keeps a policy from running a function once per row
tags: rls, performance, policy, security-definer, volatility
---

## Write Row-Security Policies That Stay Fast

A policy expression runs for every row the query touches. If it calls a
function per row, or references an unindexed column, RLS turns a fast query
slow. Two habits keep policies cheap.

**Incorrect:**

```sql
-- current_setting() / a helper function is evaluated once per row
create policy p on orders
  using (user_id = current_setting('app.user_id')::bigint);  -- per row
```

**Correct:**

```sql
-- wrap the stable sub-expression in a scalar subquery so it runs once
create policy p on orders
  using (user_id = (select current_setting('app.user_id')::bigint));

-- and index the column the policy filters on
create index on orders (user_id);
```

For checks that need to read another table, use a `SECURITY DEFINER` function
in a non-exposed schema with `set search_path = ''`, and revoke `EXECUTE` from
roles that should not call it directly. `SECURITY DEFINER` bypasses RLS on the
tables it reads — that is the point, and the hazard — so always re-check the
caller's identity inside the function body.

Reference: [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) · [CREATE POLICY](https://www.postgresql.org/docs/current/sql-createpolicy.html)
