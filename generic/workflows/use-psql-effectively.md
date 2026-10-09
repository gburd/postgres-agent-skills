# Workflow: Use psql effectively

`psql` is the reference client and far more capable than a bare SQL prompt.
Most of the leverage is in **meta-commands** (backslash commands run by the
client, not the server) and in its scripting mode.

## Inputs

- `task`: what you are doing with psql — exploring an unfamiliar schema,
  writing a repeatable maintenance script, or automating psql inside a shell
  pipeline. Changes which section below matters most.

## Steps

### 1. Inspect the schema

- `\d` lists tables, views, sequences; `\d name` describes one object; `\d+ name`
  adds storage, size, description, and index detail.
- `\dt` tables, `\di` indexes, `\dv` views, `\dm` materialized views, `\ds`
  sequences, `\dn` schemas, `\df` functions, `\dx` extensions. Append `+` for more
  detail, or a pattern: `\dt public.*`, `\df *trunc*`.
- `\sf funcname` prints a function's full source (`\sf+` with line numbers);
  `\sv viewname` shows a view's definition.
- `\l` lists databases, `\du` lists roles, `\dp` / `\z` show table privileges.

### 2. Read wide output and watch it

- `\x` toggles **expanded** output (one column per line) — essential for wide
  rows. `\x auto` picks expanded vs. tabular per result automatically; set it in
  `~/.psqlrc`.
- `\watch 5` re-runs the last query every 5 seconds — a live dashboard for
  `pg_stat_activity`, replication lag, or a counter.
- `\timing on` reports execution time for every statement.

### 3. Generate and run SQL (`\gexec`)

`\gexec` takes the result of the current query as **SQL text and executes each
row**. This replaces hand-written loops for bulk DDL/maintenance:

```sql
SELECT format('ANALYZE %I.%I;', schemaname, relname)
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
\gexec
```

### 4. Move data (`\copy`)

`\copy` runs `COPY` through the **client**, so it reads/writes files on *your*
machine (no server-side file access or superuser needed) — the normal way to
import/export CSV:

```psql
\copy orders TO '${TMPDIR:-/tmp}/orders.csv' WITH (FORMAT csv, HEADER)
\copy orders FROM '${TMPDIR:-/tmp}/orders.csv' WITH (FORMAT csv, HEADER)
```

### 5. Variables and conditionals

- `\set name value` defines a variable; interpolate it as `:name`,
  `:'name'` (quoted as a **string literal**), or `:"name"` (quoted as an
  **identifier**). Use the right form to avoid injection and quoting bugs:
  ```psql
  \set tbl orders
  \set cutoff '2024-01-01'
  SELECT count(*) FROM :"tbl" WHERE created_at > :'cutoff';
  ```
- Pass from the shell with `psql -v tbl=orders ...`.
- `\if` / `\elif` / `\else` / `\endif` do client-side branching in scripts
  (often on a variable or a query result captured with `\gset`).
- `\e` opens the current query buffer in `$EDITOR`; `\e file` edits a file then
  runs it.

### 6. Format output (`\pset`)

`\pset` controls presentation: `\pset format` (aligned, csv, html, ...),
`\pset null '∅'`, `\pset pager off`, `\pset border 2`. `\a` toggles aligned,
`\t` toggles tuples-only (no header/footer) — handy for scripting.

### 7. Configure `~/.psqlrc`

Put your defaults here so every session starts configured:

```psql
\set QUIET on
\x auto
\timing on
\pset null '∅'
\set ON_ERROR_STOP on
\set COMP_KEYWORD_CASE upper
\unset QUIET
```

### 8. Script and automate

- `psql -c "SELECT ..."` runs one command and exits; `psql -f script.sql` runs a
  file.
- For machine-readable output: `-A` (unaligned), `-t` (tuples only),
  `-F ','` (field separator) — together they emit clean CSV-ish rows for a shell
  pipeline. `-q` suppresses chatter; `-X` ignores `~/.psqlrc` for reproducible
  runs.
- **`ON_ERROR_STOP`** is mandatory in scripts: `psql -v ON_ERROR_STOP=1 -f
  migrate.sql` makes psql **exit non-zero on the first error** instead of
  plowing on and leaving a half-applied change. Wrap multi-statement migrations
  in a single transaction so a failure rolls back cleanly.
- `\errverbose` re-prints the last server error with full detail (SQLSTATE,
  schema, constraint) — the first thing to run after a cryptic failure.

## Outputs

A psql session or script configured for the task at hand: the right
meta-commands for schema exploration, or a `-v ON_ERROR_STOP=1` script that
fails loudly instead of leaving a half-applied migration.

## See also

`postgres/user/SKILL.md`, `postgres/dba/SKILL.md`,
`postgres/best-practices/references/monitor-explain-analyze.md` (`\timing`,
`\watch` on `pg_stat_activity`),
`postgres/best-practices/references/ops-autovacuum.md` (`\gexec` for bulk
`ANALYZE`),
<https://www.postgresql.org/docs/current/app-psql.html>,
<https://wiki.postgresql.org/wiki/Psqlrc>.
