# Voice: Andres Freund

Distilled patterns from Andres Freund's reviews, commits, and conference
talks. Use as a stylistic reviewer simulation; cite the specific
sub-section when feeding insights into
`generic/workflows/pre-review-by-committers.md`.

This is a distillation, not a biography. Andres is
`Andres Freund <andres@anarazel.de>` (and `andres.freund@microsoft.com`),
the project's primary owner of WAL-internal performance, lock-free
infrastructure (`src/include/port/atomics/`), and the multi-year async
I/O initiative that landed in PostgreSQL 18.

## Recurring positions

### Measure first, hack second

Andres is allergic to "this should be faster" claims with no profile.
The 2026-05-21 PGConf.dev talk **Profiling Postgres Perils** opens with
"Improve Performance: Measure & Hack & Compare & Repeat" — and most of
the slide deck is about why people measure incorrectly. The recurring
review pattern: he asks for a `perf stat -ddd` capture and a
flame-graph link before commenting on a performance-claimed patch.
"Why do you think this is slow?" is a routine reply.

What the agent should do: never submit a "perf optimization" patch
without (a) a reproducible benchmark script in the email, (b) a
`perf stat -ddd` before/after, and (c) a profile pointing at the
specific bottleneck. See `generic/workflows/perf-testing.md` for the
9-pitfall checklist distilled from his slides.

### "Profiling cycles is the wrong default"

Andres's most-repeated micro-objection: people sample on `cycles` when
the bottleneck is contention, memory latency, iTLB misses, or branch
mispredictions. From the same talk:

- Under contention → off-CPU profiling, wait events, `perf probe` on
  trace events. Never raw `perf record -e cycles`.
- Other CPU bottleneck → `perf stat -ddd`, then "Top-Down" methodology
  on Intel HW. Memory latency, dTLB misses (use huge pages), iTLB
  misses (huge pages for code), branch misses (reduce branches, hint
  likelihoods).
- Virtualization hides counters → bare metal preferred; emulated cycles
  are inaccurate, especially with frequent context switches.

What the agent should do: cite which counter you sampled on, why, and
what `perf stat -ddd` reported as the dominant top-down category.

### Lock-free / atomics discipline

Andres owns `src/include/port/atomics/`. His routine review objections
on concurrency patches:

- New lock-free code without a memory-ordering analysis. `pg_atomic_*`
  has explicit `_full_barrier` / `_read_barrier` / `_write_barrier`
  variants; using the wrong one is a silent correctness bug on
  weakly-ordered hardware (ARM, POWER).
- Spinning without backoff. He pushes for `pg_spin_delay()` /
  exponential backoff; bare retry loops are a perf cliff under
  contention.
- "Atomic int" used as if it were sequentially consistent across
  multiple atomics. He insists on stating the invariant and which
  atomic operations establish/observe it.

What the agent should do: in the commit message, write an "Ordering"
paragraph that names which atomics establish the ordering and which
observe it, and cite the weakest hardware on which it was tested
(typically a buildfarm ARM animal).

### Hot-path discipline

Andres's recurring micro-review on hot-path code:

- Avoid function-call overhead in inner loops; use `static inline` or
  declare the function `pg_attribute_always_inline` if measurement
  shows the call-site cost matters.
- Avoid memory allocation in inner loops; pre-allocate, use
  `MemoryContext` reset, or stack-allocate with `palloc0`.
- Avoid system calls in inner loops; batch via pipelining (DO loops,
  prepared statements via `pgbench -M prepared`).

What the agent should do: profile the inner loop in isolation. Andres's
"Maximize benchmarked portion" rule (Amdahl): if the operation under
test is 1.5% of the workload, a 10× speedup buys 1.4% wall-clock. Wrap
small operations in `generate_series()` drivers that make the
benchmarked portion ≥50% of the workload.

### "When *not* to micro-optimize"

Andres explicitly pushes back on micro-optimizations that:

- Cannot be measured outside a synthetic benchmark.
- Sacrifice readability for sub-1% gains.
- Are platform-specific without a fallback.
- Require disabling production-relevant features (Boost, C-states,
  THP) to measure. He puts "DO NOT DO THIS IN PRODUCTION!" in
  literally that capitalisation across multiple slide sets — disabling
  Boost and disabling C-states are *measurement* techniques, never
  *deployment* techniques.

What the agent should do: state the size of the gain and the
production-relevance of the conditions under which it was measured.
"3% on bare metal with Boost disabled and HT disabled" is an honest
claim; "3% in pgbench" is misleading.

### Async I/O and io_uring

Andres is the author of the AIO infrastructure (committed across 17/18
cycle). Patterns to expect on patches in this area:

- `io_method = worker | io_uring | sync` matters: a patch must work in
  all three modes or document why it doesn't.
- Backend-local AIO state vs. shared submission: get this wrong and
  you deadlock under high concurrency.
- Don't add a new I/O path that doesn't go through `aio.c` /
  `pgaio_io_*`. The single submission path is load-bearing.

What the agent should do: read his "Path to AIO" talks (PGConf.NYC
2023, PGConf.EU 2023) and "What went wrong with AIO" (PGConf.dev
2025) before touching the AIO subsystem. URL list under Sources.

### NUMA awareness

Andres's PGConf.EU 2024 talk "NUMA vs. PostgreSQL" frames the agenda
that drove the buffer-manager patches in 18/19. Recurring positions:

- Cross-socket buffer pool access is a 3–10× latency cliff on modern
  Intel/AMD; partitioning matters.
- `numactl --interleave=all` is a benchmark-and-deploy tool, not just a
  measurement crutch.
- "Cores are not created equal" — boost speed differs by core,
  efficiency vs. performance cores differ, distance to memory differs.
  Pin to a subset (`numactl --physcpubind 1,17 <task>`) for repeatable
  microbenchmarks. This is pitfall #6 in the Profiling Perils slides.

### `pg_test_timing` and the timing instrumentation

Andres has been working out the platform-by-platform timing accuracy
story for years; the relevant in-tree tool is `src/bin/pg_test_timing/`.
The recent commit `5ba34f6dc83` "pg_test_timing: Show additional TSC
clock source debug info" (Lukas Fittl, 2026-05-16, Suggested-by Andres,
Reviewed-by Andres) lands his recommendation that the tool report the
TSC source register and warn when calibration disagrees with the OS by
>10%, suggesting `timing_clock_source = 'system'` as the workaround.
The Discussion link (`https://postgr.es/m/CAP53Pkw3Gzb+KTF5pu_o7tzbfZ7+qm2m6uDWuGtTJjZpV9yNpg@mail.gmail.com`) is the canonical thread.

## Code-review style

- Will ask for the benchmark script, not just the numbers.
- Will ask for the bare-metal hardware spec ("what CPU, what kernel,
  what `cpupower frequency-info` shows").
- Suspicious of laptop benchmarks except for showing relative shape.
- Posts annotated `perf` output inline in -hackers replies.
- Insists on `wait_event` instrumentation for any new wait point.
- Will block a patch that adds a new `LWLock` without justifying why
  an atomic / lock-free approach was rejected.

## When Andres is the right voice to simulate

Always relevant for:

- Anything in `src/backend/storage/buffer/`, `src/backend/storage/aio/`,
  `src/backend/storage/lmgr/`, `src/include/port/atomics/`.
- Performance-claimed patches anywhere.
- New `wait_event_*` additions.
- JIT / LLVM internals.
- Anything that adds or modifies `LWLock`, spinlock, or atomic usage.

Less relevant when:

- Pure SQL surface / parser changes (Tom area).
- Pure documentation patches.
- TAP-test-only patches (Michael Paquier area).

## Sources

- **Profiling Postgres Perils** (PGConf.dev 2026-05-21):
  <https://anarazel.de/talks/2026-05-21-pgconf-pgconf-profiling-postgres-perils/profiling-postgres-perils.pdf>
  Local copy: `/scratch/andres-talks/profiling-postgres-perils.pdf`.
  The 9-pitfall list (cycles-under-contention, other-CPU bottleneck,
  virtualization hides counters, repeated-runs distortion, SSD
  exhaustion, cores-not-equal, C-states, Amdahl portion, huge-pages-
  for-code) is the canonical reference.
- Talks index: <https://anarazel.de/talks/>. Specifically:
  - 2020-05-28 PGCon "AIO" (the original AIO design talk).
  - 2023-10-04 PGConf.NYC "Path to AIO".
  - 2023-12-14 PGConf.EU "Path to AIO".
  - 2024-05-29 PGConf.dev "C2C" (cross-core / cache-line).
  - 2024-10-23 PGConf.EU "NUMA vs. PostgreSQL".
  - 2025-05-15 PGConf.dev "What went wrong with AIO".
  - 2025-09-30 PGConf.NYC "AIO in PG 18 and beyond".
- Commit `5ba34f6dc83` "pg_test_timing: Show additional TSC clock
  source debug info" (Lukas Fittl, 2026-05-16). Suggested-by /
  Reviewed-by Andres. Discussion:
  <https://postgr.es/m/CAP53Pkw3Gzb+KTF5pu_o7tzbfZ7+qm2m6uDWuGtTJjZpV9yNpg@mail.gmail.com>.
- Andres's address `andres@anarazel.de`. Hackers Message-IDs of the
  form `<n>@anarazel.de` are typically his.
- Cross-reference: `generic/workflows/perf-testing.md` for the 9-pitfall
  benchmark methodology, with PDF citations.
- Cross-reference: `community/voices/tomas-vondra.md` — Andres's slide
  set explicitly cites Vondra's "Benchmarking is hard sometimes" as
  the gold-standard methodology post.
- pgsql-hackers archive (Andres as author):
  <https://www.postgresql.org/list/pgsql-hackers/> filter by author
  "Andres Freund". Individual messages addressable as
  `https://postgr.es/m/<id>`.
