---
title: Use Unquoted lower_snake_case Identifiers
impact: MEDIUM
impactDescription: Avoids case-sensitivity bugs across tools, ORMs, and agents
tags: naming, identifiers, case-sensitivity, snake-case, quoting
---

## Use Unquoted lower_snake_case Identifiers

Postgres folds unquoted identifiers to lower case. A quoted mixed-case name like
`"userId"` keeps its case but then must be quoted *everywhere*, forever — and
every tool, ORM, migration, and agent that forgets the quotes gets a confusing
"relation does not exist". Name things in `lower_snake_case` and never quote.

**Incorrect:**

```sql
create table "Users" ("userId" bigint primary key, "firstName" text);
select firstName from Users;   -- ERROR: column "firstname" does not exist
```

**Correct:**

```sql
create table users (user_id bigint primary key, first_name text);
select first_name from users;  -- works, no quoting, tool-friendly
```

Configure ORMs that default to camelCase to emit snake_case. If you inherit a
mixed-case schema you cannot rename, a lowercase view over it is a pragmatic
compatibility layer.

Reference: [Identifiers and Key Words](https://www.postgresql.org/docs/current/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS)
