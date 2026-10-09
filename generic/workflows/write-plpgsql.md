# Workflow: Write server-side code in PL/pgSQL

How to write a PL/pgSQL function, procedure, or trigger that is correct under
error handling, honest about its volatility, safe when it builds SQL
dynamically, and the right language choice in the first place. This is the
*authoring* side; `postgres/overseer/SKILL.md` § "Reviewing PL/pgSQL" is the
*review* side — read both if you are about to merge your own patch.

## Inputs

- `task`: what the function/procedure/trigger needs to do (business logic,
  validation, a trigger action, a batch job).
- `call_frequency` (optional): once per request vs. once per row vs. a tight
  loop — governs how much the exception-block and plan-caching sections below
  matter.

## Steps

### 1. Pick the language before you pick the syntax

PL/pgSQL is not the only option, and it is not always the right one:

| Language | Use when | Trust |
|---|---|---|
| **SQL function** | The body is a single query (or a few) with no branching. Can be *inlined* by the planner into the caller's plan — the fastest option, because there is no separate call. | Trusted |
| **PL/pgSQL** | You need control flow, exception handling, cursors, or `RETURN QUERY` — logic genuinely adjacent to data access. | Trusted |
| **PL/Python, PL/Perl** (untrusted: `plpython3u`, `plperlu`) | You need a host-language library (regex engine, HTTP client, numeric library) that SQL/PLpgSQL cannot reach. | **Untrusted** — only a superuser can create functions in the `u`-suffixed language; it can read/write the filesystem and make network calls. The trusted variants (where they exist) sandbox this away but also lose the library access that was the point. |
| **C** | Maximum performance, access to backend internals. Out of scope here — see `postgres/developer/SKILL.md`. |

A PL/pgSQL function that loops row-by-row over a query that could be one
`INSERT ... SELECT` or one `UPDATE ... FROM` is the most common smell: state
the trade-off, don't reach for PL/pgSQL by default.

```sql
-- SQL function: inlinable, no PL/pgSQL overhead
create function full_name(first text, last text)
returns text
language sql
immutable
parallel safe
as $$ select first || ' ' || last $$;
```

### 2. Label volatility honestly

The planner uses this to decide whether it may cache, reorder, skip, or
inline a call. A mislabelled function is not a style nit — it is a
correctness bug that surfaces as a wrong query result or a corrupted index.

- **`IMMUTABLE`** — same inputs always give the same output, forever, with no
  side effects and no dependency on table contents or settings. Required for
  use in an index expression or a generated column; a function that is really
  `STABLE` but marked `IMMUTABLE` and used in an index silently corrupts that
  index when its real output changes (e.g. a function that depends on
  `TimeZone`).
- **`STABLE`** — same inputs give the same output *within one statement* (may
  read the database or current settings, e.g. `now()`, a lookup table), but
  can change between statements. Safe in a `WHERE` clause the planner may
  evaluate once per statement.
- **`VOLATILE`** (the default) — may return different results on every call,
  or have side effects (writes, sequence advances). Assume this unless you can
  justify a stronger label.

```sql
create function tax_rate(country text)
returns numeric
language sql
stable          -- reads a table that can change between statements
as $$ select rate from tax_rates where tax_rates.country = tax_rate.country $$;
```

Mark `PARALLEL SAFE` / `PARALLEL RESTRICTED` / `PARALLEL UNSAFE` too, if the
function may run under a parallel worker — anything touching session state or
temp tables is not parallel-safe.

### 3. Use the PL/pgSQL idioms that exist for a reason

**`GET DIAGNOSTICS`** — inspect the outcome of the last statement without a
round trip:

```sql
update accounts set balance = balance - 100 where id = 1;
get diagnostics row_count = row_count;
if row_count = 0 then
  raise exception 'account % not found', 1;
end if;
```

**`FOUND`** — a boolean set by the last `SELECT INTO`, `UPDATE`, `DELETE`,
`INSERT ... RETURNING`, or `FETCH`; cheaper than `GET DIAGNOSTICS` when you
only need yes/no:

```sql
select 1 into strict dummy from accounts where id = 1;
if not found then
  raise exception 'account % not found', 1;
end if;
```

**`RETURN QUERY`** — stream a query's rows out of a set-returning function
without building an array or looping:

```sql
create function active_accounts()
returns setof accounts
language plpgsql
stable
as $$
begin
  return query select * from accounts where status = 'active';
end;
$$;
```

**Cursors** — for a result set too large to materialize, or when you need
`FETCH`/`MOVE` semantics (scrollable, explicit fetch size):

```sql
create function sum_large_balances(threshold numeric)
returns numeric
language plpgsql
as $$
declare
  cur cursor for select balance from accounts where balance > threshold;
  bal numeric;
  total numeric := 0;
begin
  open cur;
  loop
    fetch cur into bal;
    exit when not found;
    total := total + bal;
  end loop;
  close cur;
  return total;
end;
$$;
```

Prefer a plain query (or `RETURN QUERY`) over a cursor when you don't need
row-at-a-time control — a cursor's `FETCH` loop is slower than letting the
executor stream the whole result.

### 4. Know what plan caching costs you across calls

PL/pgSQL caches the execution plan for each distinct SQL statement in the
function body, keyed per session, and reuses it on subsequent calls. This is
usually a win (skips re-planning) but has two traps:

- **Parameter-sensitive plans.** The first call's parameter values can produce
  a plan (e.g. an index scan vs. a seq scan) that is wrong for very different
  values on a later call, because the cached plan is generic/custom-chosen
  once and then reused. If a function's performance varies wildly depending on
  which value it was first called with, suspect this.
- **Dynamic SQL built with `EXECUTE`** re-plans every call (no caching) —
  trading plan-cache risk for a parse/plan cost every invocation. That is
  sometimes the right trade: see the volatility and dynamic-SQL sections.

### 5. The `EXCEPTION` block has a real cost — know when to pay it

A `BEGIN ... EXCEPTION ... END` block establishes an internal subtransaction.
Every entry into the block that reaches the exception handler allocates a
transaction ID and performs subtransaction-commit/abort bookkeeping. Cheap
once; ruinous inside a tight per-row loop:

```sql
-- BAD: a subtransaction per row, every row, even on success
create function import_rows(ids int[])
returns void language plpgsql as $$
declare id int;
begin
  foreach id in array ids loop
    begin
      insert into t values (id);
    exception when unique_violation then
      -- handled, but this is now N subtransactions for N rows
      null;
    end;
  end loop;
end;
$$;
```

Prefer `INSERT ... ON CONFLICT DO NOTHING` (no exception block at all) or
batch the operation and catch the exception once around the batch, not once
per row. Reserve `EXCEPTION` blocks for genuinely exceptional, infrequent
paths — not as a per-iteration control-flow mechanism.

### 6. Dynamic SQL safely — never string concatenation

Building SQL text from untrusted or caller-supplied identifiers/values via
`||` concatenation is a SQL-injection surface, even inside the trusted
PL/pgSQL sandbox, because the untrusted content still reaches `EXECUTE`.
Use `format()` with `%I` (identifier) and `%L` (literal), or
`EXECUTE ... USING` for parameters:

```sql
-- WRONG: concatenation
execute 'select * from ' || table_name || ' where id = ' || id_value;

-- RIGHT: %I quotes the identifier, %L quotes the literal
execute format('select * from %I where id = %L', table_name, id_value);

-- RIGHT: USING binds a parameter the way a prepared statement would —
-- preferred when the value (not the identifier) is dynamic, because it
-- also lets the plan for the dynamic statement be reused across calls
-- with different parameter values in the current session
execute format('select * from %I where id = $1', table_name) using id_value;
```

`%I` and `%L` are not optional "nicer" syntax — they are the actual escaping
mechanism. A table/column name interpolated with plain `||` is exploitable the
moment the name comes from anywhere outside a fixed, hardcoded list.

### 7. Triggers: pick the right type and know the ordering rules

- **Row-level** (`FOR EACH ROW`) — fires once per affected row; can inspect
  `OLD`/`NEW`. The default for per-row validation or auditing.
- **Statement-level** (`FOR EACH STATEMENT`, the default if `FOR EACH ROW` is
  omitted) — fires once per statement regardless of row count; cannot see
  `OLD`/`NEW` directly (use a transition table, `REFERENCING OLD TABLE AS
  ... NEW TABLE AS ...`, for statement-level access to the changed rows).
- **`BEFORE`** — can modify `NEW` (row-level) or cancel the operation by
  returning `NULL`; runs before the row is written.
- **`AFTER`** — row is already written; cannot modify it, but can see the
  final state and is the right place for side effects (audit log, cache
  invalidation, cross-table consistency).
- **`INSTEAD OF`** — views only; replaces the write entirely with your logic
  (how an updatable view backed by multiple tables is implemented).
- **Constraint triggers** (`CREATE CONSTRAINT TRIGGER`) — `AFTER`-only,
  participate in `SET CONSTRAINTS ... DEFERRED` like a real constraint; use
  when a cross-row/cross-table invariant needs deferred checking at commit,
  not immediately.
- **Ordering** — multiple triggers of the same type/timing on the same table
  fire in alphabetical order by trigger name. If order matters, name them so
  alphabetical order matches the required sequence (`trg_01_validate`,
  `trg_02_audit`), don't rely on creation order.

```sql
create function audit_balance_change() returns trigger
language plpgsql as $$
begin
  if new.balance <> old.balance then
    insert into balance_audit(account_id, old_balance, new_balance, changed_at)
    values (new.id, old.balance, new.balance, now());
  end if;
  return new;   -- AFTER trigger return value is ignored, but required
end;
$$;

create trigger trg_audit_balance
after update on accounts
for each row
execute function audit_balance_change();
```

### 8. Runnable end-to-end example

```sql
create table accounts (id int primary key, balance numeric not null);

create function withdraw(account_id int, amount numeric)
returns void
language plpgsql
as $$
declare
  current_balance numeric;
begin
  select balance into strict current_balance
  from accounts
  where id = account_id
  for update;                       -- row lock held for the function's duration

  if current_balance < amount then
    raise exception 'insufficient funds: account % has %, requested %',
      account_id, current_balance, amount
      using errcode = 'insufficient_privilege';
  end if;

  update accounts set balance = balance - amount where id = account_id;

exception
  when no_data_found then
    raise exception 'account % does not exist', account_id;
end;
$$;
```

`SELECT ... INTO STRICT` raises `no_data_found`/`too_many_rows` automatically
if the query returns zero or more than one row — use `STRICT` whenever you
expect exactly one row, instead of a manual `FOUND` check, so the failure mode
is explicit.

## Research it on pg.ddx.io

For design rationale, edge cases, and "has this volatility/trigger-ordering
gotcha bitten someone before" — ask before guessing:

```
retrieve_context {"question": "PL/pgSQL exception block subtransaction cost", "token_budget": 4000}
hybrid_search {"query": "PL/pgSQL trigger ordering", "inbox": "pgsql-general"}   # usage/gotchas
hybrid_search {"query": "PL/pgSQL volatility planner inlining", "inbox": "pgsql-hackers"}  # implementation detail
```

Scope `hybrid_search` to `pgsql-general` for "how do I use this / what bit me"
discussion, and to `pgsql-hackers` for "why does the planner/executor behave
this way" implementation detail. See `tooling/pg-ddx-research/SKILL.md` for
the full tool reference.

## Outputs

- A function/procedure/trigger with an honest volatility label, safe dynamic
  SQL (if any), and exception handling scoped to genuinely exceptional paths.
- A one-line note on why PL/pgSQL (vs. a SQL function or PL/Python) was the
  right call, for the commit message or review.

## See also

- `postgres/overseer/SKILL.md` § "Reviewing PL/pgSQL" — the review-side
  checklist (SECURITY DEFINER + search_path, volatility audit, exception-block
  cost) for vetting someone else's function before approving it.
- `postgres/best-practices/references/security-rls-performance.md` —
  `SECURITY DEFINER` function hardening when the function bypasses RLS.
- `tooling/pg-ddx-research/SKILL.md` — the pg.ddx.io research tool reference.

## Sources

- Docs: <https://www.postgresql.org/docs/current/plpgsql.html> — the full
  PL/pgSQL chapter.
- Docs: <https://www.postgresql.org/docs/current/plpgsql-control-structures.html>
  — `GET DIAGNOSTICS`, `FOUND`, cursors.
- Docs: <https://www.postgresql.org/docs/current/plpgsql-trigger.html> —
  trigger procedures in PL/pgSQL.
- Docs: <https://www.postgresql.org/docs/current/trigger-definition.html> —
  row vs. statement, `BEFORE`/`AFTER`/`INSTEAD OF`, firing order.
- Docs: <https://www.postgresql.org/docs/current/sql-createfunction.html> —
  `IMMUTABLE`/`STABLE`/`VOLATILE`, `PARALLEL SAFE`.
- Docs: <https://www.postgresql.org/docs/current/plpgsql-statements.html#PLPGSQL-STATEMENTS-EXECUTING-DYN>
  — `EXECUTE`, `format()`, `%I`/`%L`.
- Docs: <https://www.postgresql.org/docs/current/xplang.html> — procedural
  language overview, trusted vs. untrusted.
