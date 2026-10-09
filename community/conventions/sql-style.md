# SQL style

SQL you write for a user should read like prose and survive schema change
without silently breaking. These rules are not aesthetic preferences; most of
them prevent a real class of bug (a dropped column shifting an `INSERT`, an
accidental cross join, an ambiguous column name). Pick a style and apply it
uniformly across a file.

## Case and naming

- **Keywords uppercase, identifiers lowercase:** `SELECT ... FROM account WHERE
  status = 'active'`. The contrast lets a reader scan structure instantly.
- **`snake_case` for every object name** — tables, columns, indexes,
  constraints. Avoid quoted mixed-case identifiers (`"myTable"`): once quoted,
  the name is forever case-sensitive and every reference must quote it.
- **Singular, descriptive names.** Suffix nothing with its type (`account`, not
  `account_tbl`). Name constraints and indexes so a failure message is readable
  (`account_email_key`, `line_item_order_fk`).

## Joins

- **Explicit `JOIN ... ON`, never comma joins.** A comma join with a forgotten
  `WHERE` predicate is a silent cross join over the whole product.

  ```sql
  -- do this
  SELECT a.email, o.order_id
  FROM   account AS a
  JOIN   "order" AS o ON o.account_id = a.account_id
  WHERE  a.status = 'active';

  -- not this
  SELECT email, order_id
  FROM   account, "order"
  WHERE  order.account_id = account.account_id;
  ```

- Spell out `INNER` / `LEFT` / `RIGHT` deliberately; `JOIN` alone means `INNER`,
  so write `INNER JOIN` only when it aids clarity but never rely on `LEFT` being
  implied.

## Qualify columns in multi-table queries

In any query touching more than one table, qualify every column with its table
or alias (`a.email`, not `email`). An unqualified column that is currently
unique becomes an ambiguous-column error — or worse, resolves to the wrong
table — the day someone adds a same-named column elsewhere.

## Aliases

Use short, meaningful aliases (`account AS a`, `line_item AS li`), not `t1`,
`t2`. Always use `AS` for both table and column aliases so intent is explicit.

## Commas: pick one convention and hold it

Either leading or trailing commas is fine; consistency is the rule. Leading
commas make it obvious when the last item was forgotten and keep diffs clean:

```sql
SELECT
    a.account_id
  , a.email
  , a.created_at
FROM account AS a;
```

## CTEs for readability

Use `WITH` to name intermediate steps and read a query top-to-bottom instead of
inside-out. Note the materialization fence: before PostgreSQL 12 a CTE was
*always* an optimization boundary (materialized, no predicate push-down). On 12+
the planner may inline it; use the explicit keyword when you need the old
behavior or want to prevent inlining:

```sql
WITH active AS MATERIALIZED (
    SELECT account_id FROM account WHERE status = 'active'
)
SELECT li.order_id, sum(li.total) AS order_total
FROM   active AS a
JOIN   "order" AS o  ON o.account_id = a.account_id
JOIN   line_item AS li ON li.order_id = o.order_id
GROUP  BY li.order_id;
```

## Never `SELECT *` in code

- It fetches columns you do not use (wasted I/O, defeats index-only scans).
- Its result shape changes silently when a column is added or dropped, breaking
  positional consumers and `INSERT ... SELECT`.
- Name the columns you want. `*` is fine only for ad-hoc interactive inspection.

## Always list columns in INSERT

```sql
-- do this: order-independent, survives a new/reordered column
INSERT INTO account (email, status) VALUES ('jane.doe@example.com', 'active');

-- not this: a schema change silently shifts values into the wrong columns
INSERT INTO account VALUES ('jane.doe@example.com', 'active');
```

## See also

`postgres/user/SKILL.md` — the query-author persona this convention serves.
`postgres/best-practices/references/query-index-types.md` — index choice for
the predicates this style keeps explicit.
`postgres/best-practices/references/monitor-explain-analyze.md` — reading the
plan a query written this way produces.
`community/conventions/pgindent.md` — the parallel C-formatting discipline.
<https://www.postgresql.org/docs/current/sql-select.html>,
<https://www.postgresql.org/docs/current/queries-with.html>,
<https://wiki.postgresql.org/wiki/Don%27t_Do_This>.
