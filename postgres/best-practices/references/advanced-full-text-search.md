---
title: Full-Text Search With a Generated tsvector + GIN, Not LIKE '%...%'
impact: MEDIUM
impactDescription: Index-backed search with ranking, vs an unindexable scan
tags: full-text-search, tsvector, gin, generated-column, websearch
---

## Full-Text Search With a Generated tsvector + GIN, Not LIKE '%...%'

A leading-wildcard `LIKE '%term%'` cannot use a normal index — it scans every
row — and it does not understand word boundaries, stemming, or ranking.
PostgreSQL's full-text search does. Store a `tsvector` in a generated column so
it stays in sync automatically, and index it with GIN.

**Incorrect:**

```sql
-- unindexable scan; no stemming, no ranking
select * from articles where content ilike '%postgresql%';
```

**Correct:**

```sql
alter table articles add column search tsvector
  generated always as (
    to_tsvector('english', coalesce(title,'') || ' ' || coalesce(body,''))
  ) stored;
create index on articles using gin (search);

-- match + rank; websearch_to_tsquery accepts Google-style user input
select *, ts_rank(search, q) as rank
from   articles, websearch_to_tsquery('english', 'postgres performance') q
where  search @@ q
order  by rank desc;
```

Weight fields differently with `setweight` if title should outrank body. Do not
build a `tsvector` over huge columns you never search — it costs storage and
write time. For trigram/substring matching (as opposed to word search), use
`pg_trgm` with a GIN/GiST index instead:

```sql
-- a mid-string LIKE/ILIKE is normally unindexable, even with a plain B-tree
-- on the column: select * from articles where title ilike '%postgresql%';
create extension if not exists pg_trgm;
create index on articles using gin (title gin_trgm_ops);

-- now indexable, including a leading wildcard
select * from articles where title ilike '%postgresql%';
```

`pg_trgm` breaks the string into trigrams and indexes those, so GIN can
satisfy `LIKE '%mid%'`/`ILIKE '%mid%'` and similarity (`%`) queries that a
B-tree never could — at the cost of a larger index than a plain B-tree on the
same column, since every trigram, not just the whole value, is indexed.

Reference: [Full Text Search](https://www.postgresql.org/docs/current/textsearch.html) · [FTS Tables and Indexes](https://www.postgresql.org/docs/current/textsearch-tables.html)
