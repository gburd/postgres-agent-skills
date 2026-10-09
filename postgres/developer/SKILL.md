---
name: postgres-developer
description: >
  PostgreSQL skills for developing code that runs inside the server: patches to
  core PostgreSQL (C, the backend, executor, planner, WAL, buffer manager) and
  server-side extensions. Covers the C coding conventions, patch-series
  discipline, the build-and-test loop (cassert, meson/make, per-commit
  verification), community submission norms, the security/trust model, and the
  internals gotchas that bite. Use when writing or reviewing a patch for
  upstream PostgreSQL or an extension, or debugging backend internals.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
  persona: developer
---

# PostgreSQL — Developer (core & in-server extensions)

You write C that runs inside the postmaster: core patches, or extensions linked
into the backend. The bar is upstream's: every commit builds clean on its own,
passes `make check`, and is defensible to a reviewer who will rebase-exec your
series. This skill is the map; the tooling skills (`../../tooling/`) are how you
research and transform.

## When to apply

Writing or reviewing a patch for upstream PostgreSQL or a server-side
extension; debugging backend internals (executor, planner, WAL, buffer
manager, locking); preparing a patch series for pgsql-hackers.

## Rule of first resort: research before you code

Before `grep`/web-search/guessing, use the `agora` MCP research skill
(`../../tooling/agora/`): it indexes the pgsql-hackers archive + `master`
git history with author/thread metadata. Patch-design questions, symbol
lookups, "has this been proposed/rejected before", commit↔thread correlation —
ask it first. Half the time someone already proposed the thing; understanding
why it stalled saves the same dead end.

## Patch-series discipline (acceptance criteria, not aspirations)

- **Every commit builds clean on its own** with `-Werror` and
  `--enable-cassert --enable-injection-points`. A reviewer will
  `git rebase --exec 'make'` the series; any commit that fails is disqualifying.
- **Every commit passes `make check` on its own** (not just the tip). Bundle
  each test with the commit that introduces the feature it exercises.
- **Foundational changes precede consumers and keep every existing consumer
  correct *at that commit*.** If a change is only correct once its new consumer
  exists, put it in the commit with the consumer. (Real miss: broadening a
  relcache attr bitmap in an infra patch silently broke `heap_update`'s HOT
  decision for BRIN until a later patch rewired it; the fix was to move the one
  line into the write-path commit.)
- **Minimise churn between commits**; don't add code in one and delete it in
  another within a series.
- **Typedefs** go in `src/tools/pgindent/typedefs.list` in the commit that
  introduces the type. Run `pgindent`.
- **Each commit stands on its own as a defensible idea**, with a self-contained
  rationale in its message.
- **ASCII only** in code, comments, docs, and messages. No project codename in
  identifiers.
- **A local-only dev-setup commit** (Nix env, editor config) stays first and is
  excluded from the submitted series.

## Build & verify (mechanics that bite)

- Build with `--enable-cassert --enable-debug --enable-tap-tests`. Undefined-
  behaviour bugs only show under cassert.
- **meson caches the initdb template** (`tmp_install/initdb-template`); it is
  *not* regenerated on `git checkout`. Stale templates give false regress diffs
  and false passes. To test a commit honestly: `trash tmp_install testrun;
  meson test --suite setup` before `meson test --suite regress`.
- **ninja/make mtime traps**: a just-checked-out file may not rebuild; `touch`
  it and confirm the object recompiled.
- **Distinguish stale-build/stale-template confounds from real regressions
  before concluding anything** — this has fabricated both a false green and a
  false red.
- Bisect deterministic failures across the series to find the introducing
  commit. Reproduce isolation/TAP failures standalone with a scratch cluster
  and hand-driven `psql` sessions + injection point.
- `gdb -p <pid> -batch -ex 'bt'` for hangs; inspect `PrivateRefCountArray` for
  held buffer pins and `BufferDescriptors[n].tag` for the stuck relation/block.

## The security & trust model (this is the top review lever)

A reviewer's time is wasted most by false-positive "vulnerabilities". Internalise
the trust model so you neither write nor flag non-bugs:

- A superuser can already do anything; "superuser can cause X" is **not** a
  vulnerability. Trusted vs untrusted input is the line that matters.
- `ereport(ERROR)` does a `longjmp` to the enclosing handler; `PG_TRY`/`volatile`
  rules exist because of it. palloc memory-context pooling is not a leak.
- Signal-handler safety, locale-aware comparison, `SECURITY DEFINER` +
  `search_path` are real; most "injection" reports against stock behaviour are not.
- Report genuine issues privately to the security team only; never to a public
  list, never a public PoC.

## Internals gotchas (verified the hard way)

- **HOT determination compares actual tuple values over the indexed-attr
  bitmap**, not the SQL target list. `ExecGetAllUpdatedCols()` misses indexed
  columns mutated by BEFORE/INSTEAD triggers, `FOR PORTION OF`, exclusion
  constraints, and synthetic-`ResultRelInfo` callers (REPACK apply, logical-rep
  apply). Match `HeapDetermineColumnsInfo`, which always compares.
- **Synthetic `ResultRelInfo` callers** make any `ExecGet*Cols()` result
  non-authoritative; guard for or avoid them.
- **btree leaf-pin retention vs VACUUM cleanup lock**: setting `xs_want_itup`
  on a *plain* index scan wrongly retains the leaf pin and can block VACUUM's
  cleanup lock behind a row-lock wait → hang. Gate pin-drop on an explicit
  index-only flag, not `xs_want_itup`.
- **Catalog index consistency after a relfilenode swap**: CLUSTER/VACUUM
  FULL/REPACK's `pg_class` update is itself HOT-subject; internal access
  (`systable_getnext`) and direct SQL (executor IndexScan) must agree, or a
  `WHERE relname = ...` silently returns no row.

## Submission (deliverable is files, never a sent message)

Agents **never** send mail to any list — no `git send-email`, no SMTP, not even
a test copy, even after approval. Finish with `git format-patch` output plus a
plain-text cover letter (recipients, `In-Reply-To`, prior-thread references),
and say "ready for you to send". The human sends. GitHub is a read-only mirror —
never open PRs against upstream; patches go to pgsql-hackers + commitfest.

Commit messages, docs (SGML), comment conventions, and -hackers email style
are codified in `../../community/conventions/` and `../../community/`; follow
them — they are what reviewers expect.

Reference: [Developer FAQ](https://wiki.postgresql.org/wiki/Developer_FAQ) · [Submitting a Patch](https://wiki.postgresql.org/wiki/Submitting_a_Patch) · [So, you want to be a developer?](https://www.postgresql.org/developer/)
