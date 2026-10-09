---
title: Apply Least Privilege — Never Run the App as Superuser
impact: HIGH
impactDescription: Shrinks the blast radius of a bug or injection to one role's grants
tags: privileges, roles, least-privilege, grant, public-schema
---

## Apply Least Privilege — Never Run the App as Superuser

Grant each role only what it needs. An application connecting as a superuser
(or with blanket `ALL`) turns any injection or logic bug into a
drop-everything incident.

**Incorrect:**

```sql
grant all privileges on all tables in schema public to app_user;
-- one injected `drop table ... cascade` and it is gone
```

**Correct:**

```sql
-- revoke the permissive defaults first
revoke all on schema public from public;

-- a read role
create role app_read nologin;
grant usage on schema public to app_read;
grant select on public.products, public.categories to app_read;

-- a write role with no DELETE and only the tables it needs
create role app_write nologin;
grant usage on schema public to app_write;
grant select, insert, update on public.orders to app_write;
grant usage on sequence public.orders_id_seq to app_write;

-- the login role inherits from the task roles
create role app_user login password 'use-a-secret-manager';
grant app_write to app_user;
```

Grant on *specific* objects, not `ALL TABLES IN SCHEMA`, and use `ALTER DEFAULT
PRIVILEGES` to cover future objects deliberately rather than by accident.

Reference: [GRANT](https://www.postgresql.org/docs/current/sql-grant.html) · [Privileges](https://www.postgresql.org/docs/current/ddl-priv.html)
