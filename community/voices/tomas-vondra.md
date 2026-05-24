# Voice: Tomas Vondra

Distilled patterns from Tomas Vondra's reviews, commits, and conference
talks. Use as a stylistic reviewer simulation; cite the specific
sub-section when feeding insights into
`generic/workflows/pre-review-by-committers.md`.

This is a distillation, not a biography. Tomas is
`Tomas Vondra <tomas@vondra.me>` (formerly `tomas.vondra@enterprisedb.com`),
the project's primary owner of extended statistics, BRIN, and a large
share of parallel-query costing. He maintains a rare
deep-and-public benchmarking practice.

## Recurring positions

### "Benchmarking is hard"

Vondra's blog post "Benchmarking is hard, sometimes"
(<https://vondra.me/posts/benchmarking-is-hard-sometimes/>) is the
canonical methodology reference for the project — Andres explicitly
links it from the **Profiling Postgres Perils** slide deck. The
post's recurring lesson: small environmental changes (CPU power
states, core pinning, kernel version, filesystem mount options,
ASLR layout, even time-of-day temperature) move pgbench numbers more
than most patches do. Apparent regressions are often noise; apparent
wins are often artefacts.

What the agent should do: when posting a benchmark result, include
(a) hardware spec (CPU, RAM, NUMA layout, kernel, distro), (b) tunable
state (`/sys/devices/system/cpu/cpufreq/`, `/sys/kernel/mm/transparent_hugepage/enabled`),
(c) at least 3 runs in alternating order, (d) the run-to-run standard
deviation, (e) `pg_stat_statements` / wait-event data showing what
the dominant cost is. Without (a)–(e), Vondra's typical reply is "this
might just be noise; can you alternate the runs and see if the result
holds?"

### Performance cliffs > average performance

Vondra's recurring talk "Where do performance cliffs come from?"
(SFPUG 2025-04-08, Malmö 2025-04-24, POSETTE 2024) frames a methodology
that informs many of his reviews: a feature that makes the average case
2× faster but introduces a 100× cliff on a corner case is usually a
regression. Look for the cliff explicitly.

What the agent should do: enumerate the parameter space (data size,
client count, working set vs. RAM, predicate selectivity, number of
partitions/joins, etc.) and run at the *edges*, not just the centre.
A change that touches the planner or buffer manager almost always has
a parameter combination where it underperforms; find it before he does.

### Extended statistics: the planner needs more than per-column

Vondra is the author of `CREATE STATISTICS` (multi-column / functional
dependency / MCV-list extended stats). Recurring positions in this
area:

- A new selectivity-estimation patch that ignores extended statistics
  is incomplete. Patches must call into `dependencies_clauselist_selectivity`
  / `statext_*` in the appropriate order.
- The ordering of stat-kind application matters; functional dependencies
  apply before MCV-list, MCV-list applies before per-column histograms.
  See `src/backend/statistics/dependencies.c` and `mcv.c`.
- Adding a new statistic kind: `pg_statistic_ext_data`, the build path
  in `analyze.c`, and the apply path in `clausesel.c` must all line up
  — and the catalog version must bump.

What the agent should do: when adding any selectivity logic, search
`statext_clauselist_selectivity` callers and confirm the new logic
either runs before or after the right stat kind. If you don't know,
say so on the thread.

### Partition pruning: the right pruning is the right time

Recurring objections on partition-pruning patches:

- Plan-time pruning vs. execution-time pruning: do not conflate.
  `partprune.c` runs at plan time on Const, at exec time on Param/Var.
- Pruning on `IN (subquery)` or `= ANY (array)` requires the array's
  type and the partition key's type to be compatible, not just
  coercible.
- Pruning must not change visibility (a pruned partition's tuples
  must not become visible due to plan reuse across snapshots).

### Parallel-query costing

Vondra has touched parallel-query costing extensively (parallel
hash-join sizing, parallel GIN build, parallel append, parallel
bitmap heap scan). Recurring objections:

- `parallel_setup_cost` and `parallel_tuple_cost` are knobs, not
  truths; if your patch makes the optimal `parallel_workers` setting
  depend on a variable you cannot estimate, the costing model needs
  to be rethought, not the GUC default.
- Memory budgeting under parallel workers (`work_mem` per worker) is
  load-bearing; commit `b85c4700fc5` "Fix hashjoin memory balancing
  logic" (Tomas Vondra) is the recent canonical example of the kind
  of bug he hunts in this area.
- Parallel-aware vs. parallel-restricted vs. parallel-safe: the
  three-state `proparallel` flag matters; mis-tagging a function is
  a correctness bug, not a performance bug.

### EXPLAIN visibility for new behaviour

Recurring pattern: any new I/O or memory behaviour gets EXPLAIN
instrumentation. See his recent run of EXPLAIN (IO) commits:

- `681daed9316` "Add EXPLAIN (IO) infrastructure with BitmapHeapScan
  support" (Tomas Vondra).
- `3b1117d6e2e` "Add EXPLAIN (IO) instrumentation for SeqScan".
- `e157fe6f76e` "Add EXPLAIN (IO) instrumentation for TidRangeScan".
  Discussion:
  <https://postgr.es/m/flat/a177a6dd-240b-455a-8f25-aca0b1c08c6e%40vondra.me>.

What the agent should do: a patch that adds a new code path which can
become a performance bottleneck must add the corresponding EXPLAIN /
`auto_explain` / `pg_stat_*` visibility in the same series.

### The real cost of random I/O

Blog post "The real cost of random I/O"
(<https://vondra.me/posts/the-real-cost-of-random-io/>, 2026-02-26)
re-examines `random_page_cost` on modern SSDs and NVMe.
Recurring position in -hackers threads: the historical 4.0 default is
no longer the right shape on flash-only hardware, but the right new
default is data-dependent and can't be a single number. Patches that
adjust `random_page_cost` defaults globally will be sent back; patches
that instrument actual random vs. sequential I/O *per query* are
welcomed.

## Code-review style

- Posts well-formatted reproduction scripts with a single bash block.
- Always shows a graph of TPS over `-c` (client count) when discussing
  scalability; insists you do too.
- Calls out `noise vs. signal` early in a thread to set expectations.
- Uses `pgbench -f <file>` over `-S/-N` when the workload shape matters.
- Will request a flame graph if your story is "function X is hot".

## When Tomas is the right voice to simulate

Always relevant for:

- Anything in `src/backend/optimizer/path/`, `src/backend/optimizer/util/`.
- Anything in `src/backend/statistics/`, `src/backend/access/brin/`,
  `src/backend/access/gin/`.
- Anything in `src/backend/access/heap/` that touches scan costing.
- Performance-claimed patches that affect more than one operator.
- Partitioning, partition-wise join/agg, partition pruning.
- Anything calling `add_path` or modifying the path tree.

Less relevant when:

- Pure parser / type-system changes (Tom).
- Pure WAL / logical replication mechanics (Heikki / Andres).
- Pure JIT / atomics (Andres).

## Sources

- Blog: **Benchmarking is hard, sometimes** —
  <https://vondra.me/posts/benchmarking-is-hard-sometimes/>. The
  gold-standard methodology post; cited from Andres's
  Profiling Postgres Perils slide deck.
- Blog: **The real cost of random I/O** (2026-02-26) —
  <https://vondra.me/posts/the-real-cost-of-random-io/>.
- Blog: **How are committers selected?** (2026-05-05) —
  <https://vondra.me/posts/how-are-committers-selected/>.
- Talks index: <https://vondra.me/talks/>. Specifically (with
  publicly-linked PDFs/videos):
  - 2026 "Estimating percentiles" (Nordic PgDay 2026, FOSDEM PgDay 2026)
    [PDFs at `/pdf/estimating-percentiles-{nordic,fosdem}-pgday-2026.pdf`].
  - 2025 "Performance Archaeology" (POSETTE 2025 — YouTube
    `IY7Nl2sY9fQ`).
  - 2025 "Where do performance cliffs come from?" (SFPUG, Malmö —
    YouTube `j0ISi1KVulU`).
  - 2024 "Performance Archaeology" (pgconf.eu 2024 — PDF).
  - 2024 "Where do the performance cliffs come from?" (POSETTE 2024,
    pgconf.be 2024 — YouTube `UzdAelm-QSY`).
  - 2024 "Postgres vs. Linux Filesystems" (FOSDEM 2024).
  - 2023 "Postgres vs. Linux Filesystems" (pgconf.eu 2023 — YouTube).
  - 2014 "Performance Archaeology" (pgconf.eu 2014, original).
  - 2012 "PostgreSQL vs. SSD" (Prague PG Developer Day 2012).
- Commit `e157fe6f76e` "Add EXPLAIN (IO) instrumentation for
  TidRangeScan" — Discussion:
  <https://postgr.es/m/flat/a177a6dd-240b-455a-8f25-aca0b1c08c6e%40vondra.me>.
- Commit `681daed9316` "Add EXPLAIN (IO) infrastructure with
  BitmapHeapScan support".
- Commit `b85c4700fc5` "Fix hashjoin memory balancing logic".
- Tomas's domain `vondra.me`. Hackers Message-IDs of the form
  `<n>@vondra.me` are typically his.
- Cross-reference: `community/voices/andres-freund.md` — explicit cite
  of "Benchmarking is hard sometimes" in his profiling-perils talk.
- Cross-reference: `generic/workflows/perf-testing.md` for the
  methodology turned into an actionable workflow.
