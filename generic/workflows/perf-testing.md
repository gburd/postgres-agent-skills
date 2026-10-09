# Workflow: PostgreSQL performance testing

How to run reproducible performance experiments on PostgreSQL. The
core message: **most "performance" measurements done casually are
artefacts of the methodology, not real signal**. This skill embeds
Andres Freund's 9-pitfall checklist from his PGConf.dev 2026
"Profiling Postgres Perils" talk, and Tomas Vondra's
"benchmarking is hard, sometimes" methodology.

## TL;DR — the floor for any benchmark

```sh
# 1. Build WITHOUT cassert, with debug symbols for perf to symbolicate.
./configure --enable-debug --without-llvm CFLAGS='-O2 -ggdb3'
make -s -j$(nproc) && make install

# 2. Disable everything that randomises wall-clock measurement.
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo  # Intel
# echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost        # AMD
sudo cpupower idle-set -D0
# DO NOT do this on a production system.

# 3. Pin the test to specific cores.
numactl --physcpubind=1,17 --membind=0 \
    pgbench -M prepared -S -c 8 -j 8 -T 60 -P 5 -n bench

# 4. Alternate baseline and patched runs at least 3 times each.
# 5. Report the median, not the maximum, with run-to-run variance.
# 6. Save perf data: perf stat -ddd, perf record -F 99 -ag.
```

If you can't satisfy steps 1–6, your numbers are noise.

## Reproducibility floor

Per Vondra's *Benchmarking is hard, sometimes*
(<https://vondra.me/posts/benchmarking-is-hard-sometimes/>), a
publishable PostgreSQL performance result reports:

1. **Hardware**: CPU model, core count, sockets, NUMA topology
   (`numactl --hardware`), RAM, storage type and model.
2. **OS**: kernel version, distro, mitigations
   (`cat /sys/devices/system/cpu/vulnerabilities/*`), THP setting
   (`cat /sys/kernel/mm/transparent_hugepage/enabled`),
   filesystem and mount options.
3. **CPU power state**: governor, boost on/off, C-states.
4. **PostgreSQL**: commit SHA, configure flags, `postgresql.conf`
   diff from the default.
5. **Workload**: exact pgbench / sysbench / TPC-* invocation,
   data size, run length, warm-up.
6. **Schedule**: alternation of baseline and patched runs, time
   between runs.
7. **Results**: median + run-to-run stddev (or full distribution),
   plus the dominant wait events / CPU events from
   `pg_stat_activity` / `perf stat`.

Anything less and Andres / Vondra will reply "this might just be
noise; please re-run with..."

## pgbench setup

The minimum:

```sh
# Initialise. Scale 100 ≈ 1.5 GB, scale 1000 ≈ 15 GB. Pick
# scale to hit the working-set regime you want (in-RAM, on-disk).
pgbench -i -s 100 bench

# Built-in transaction scripts (-b):
#   tpcb-like (default), simple-update, select-only.
# Read-only:
pgbench -M prepared -S -c $C -j $C -T 60 -P 5 -n bench

# Read-write:
pgbench -M prepared -c $C -j $C -T 60 -P 5 -n bench

# Custom workload:
pgbench -M prepared -f my-workload.sql -c $C -j $C -T 60 -n bench
```

Flags worth knowing:

| Flag | Meaning |
|---|---|
| `-c N` | `--client=N`, number of concurrent clients. |
| `-j N` | `--jobs=N`, number of pgbench worker threads. Set `j == c`. |
| `-T N` | `--time=N`, run duration in seconds. |
| `-t N` | `--transactions=N`, fixed transaction count instead. |
| `-M prepared` | Use prepared statements. **Always** for benchmarking — avoids re-parsing. |
| `-S` | Built-in select-only transaction. |
| `-N` | Built-in no-foreign-key TPC-B-like transaction. |
| `-P N` | Print interim TPS every N seconds (good for spotting cliffs). |
| `-n` | Don't VACUUM before run (avoids contaminating the timing). |
| `-r` | Per-script latency report. |
| `-f file` | Custom workload script. |
| `--builtin=NAME` | Pick a builtin: `tpcb-like`, `simple-update`, `select-only`. |

Pre-flight checklist for any pgbench result:

- Warm up: discard the first 10s of any run (use `-P 1` and inspect
  the per-second TPS for stabilisation).
- Match `-c` to the parallelism shape you're testing. A single-client
  run measures latency-bound work; `-c 32` on 32 cores measures
  scaling.
- Re-run with `-c 1` to baseline single-client latency.
- For write-heavy runs, `fstrim` between runs and pre-warm caches.

## `perf record` and flame graphs

```sh
# Server-wide CPU sample, frequency 99 Hz, capture call graphs.
sudo perf record -F 99 -ag -- sleep 30
sudo perf report                    # interactive
sudo perf script > out.perf
```

Flame graph (Brendan Gregg's tool):

```sh
git clone https://github.com/brendangregg/FlameGraph
./FlameGraph/stackcollapse-perf.pl out.perf > out.folded
./FlameGraph/flamegraph.pl out.folded > flame.svg
```

For PostgreSQL specifically:

- Use `-F 99` (or `-F 999` for higher resolution; mind the data
  size).
- Use `-ag` (sample all CPUs, capture call graphs).
- Build with `-fno-omit-frame-pointer` *or* with `-ggdb3` and
  modern `perf` (DWARF unwinding); the latter is slower but more
  accurate.
- Symbol resolution requires the `postgres` binary built with
  `-ggdb3`. If `perf report` shows `[unknown]`, you're missing
  symbols.

## The 9 pitfalls (Andres Freund, PGConf.dev 2026)

From "Profiling Postgres Perils" — slide PDF:
<https://anarazel.de/talks/2026-05-21-pgconf-pgconf-profiling-postgres-perils/profiling-postgres-perils.pdf>
(local: `/scratch/andres-talks/profiling-postgres-perils.pdf`).

### Pitfall 1: Profiling cycles under contention

If your workload contends on a lock, `perf record -e cycles` shows
you the *spinning* code, not the *contended* resource. Result: you
"optimise" the spinner.

Workarounds:

- **Off-CPU profiling** — `perf record -e sched:sched_switch -ag`
  + off-CPU flame graph. Or BCC `offcputime` /
  <https://github.com/iovisor/bcc>.
- **Wait events** — sample `pg_stat_activity.wait_event_type` /
  `wait_event` with a tight loop. PostgreSQL's wait-event
  taxonomy is the canonical "what is the backend blocked on".
- **`perf probe` on trace events** — register a probe at the
  contended primitive and sample.

### Pitfall 2: Other CPU bottleneck (not cycles)

`perf stat -ddd <cmd>` reveals the real story. Common other
bottlenecks:

- **Memory latency** — code waits on cache fills. Fix: hide
  latency with prefetch, improve locality.
- **Data TLB misses** — large working set. Fix: huge pages
  (`vm.nr_hugepages`, `huge_pages = try` in `postgresql.conf`).
- **Instruction TLB misses** — large code footprint. Fix: huge
  pages for *code* (see Pitfall 9).
- **Branch misses** — fix: reduce branches, use `__builtin_expect`
  on hot conditionals.

Use Intel's "Top-Down" methodology
(<https://www.intel.com/content/www/us/en/docs/vtune-profiler/cookbook/2023-0/top-down-microarchitecture-analysis-method.html>)
to classify which of frontend-bound / backend-bound / bad-speculation
/ retiring is dominant.

### Pitfall 3: Virtualization hides perf counters

In a VM, hardware perf counters may be unavailable; `perf` falls
back to "emulated cycles" (regular timer fires, captures current
IP). The emulation is inaccurate, especially with frequent context
switches.

Workaround: **bare metal preferred** for any serious profiling.
Cloud-bare-metal (AWS `*.metal`, GCP sole-tenant) is acceptable;
non-bare-metal cloud VMs are not.

### Pitfall 4: Repeated / long runs distort

A naive run-baseline-then-patched loop on a CPU with thermal
throttling, dynamic frequency scaling (Boost), or wear-levelling
SSDs will produce monotonically degrading numbers over time —
making the *second* run look slower regardless of code.

Workarounds:

- **Disable Boost** (measurement only):
  ```sh
  echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo  # Intel
  echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost          # AMD
  ```
  *DO NOT do this in production* (Andres's slide capitalisation).
  Disabling Boost reduces both peak performance and variance.
- **Swap the order** of benchmarks (run patched, then baseline,
  then patched, then baseline...).
- **Wait between runs** (10s+ for thermal recovery).

### Pitfall 5: SSD exhaustion on write-heavy

Write-heavy benchmarks fill the SSD's overprovision area; later
runs hit GC-induced write amplification, latency spikes.

Workarounds:

- **`fstrim -v /path/to/fs`** between runs.
- **Overprovision** the SSD (leave 20-30% unallocated at the LUN
  level).
- **Use a small proportion** of a large fast device (don't fill it
  up).
- **Wait minutes-to-hours** between runs to let GC complete.
- Use better SSDs (consumer NVMe is usually unsuitable for
  write-heavy benchmarking).

### Pitfall 6: Cores are not equal

Modern CPUs have:

- Different boost speeds per core (up to 15% spread observed).
- Different core types (P-cores vs. E-cores on Intel; Performance
  vs. Efficiency on Apple Silicon).
- Different memory distance per core (NUMA, even within one
  socket on chiplet designs).
- Different IRQ affinities (some cores get all the network IRQs).

Workarounds:

- **Pin to a subset** of cores: `numactl --physcpubind=1,17 <task>`.
- **Pin server and client to different cores** *on the same
  socket* (different cores avoid context-switch interference;
  same socket avoids cross-NUMA latency).
- **Disable boost** for repeatability.

### Pitfall 7: C-state power management

Modern CPUs enter low-power C-states when idle. Benefits: lower
power and temps. Cost: wake-up latency, slower benchmarks for
tight client-server ping-pong loops.

The slide deck's example: pgbench `-S -c 1` pinned to one core
where server and client share a core gives 42552 TPS, but on
*different* cores gives 40057 TPS — because shared-core context
switches are faster than waking an idle CPU from low C-state.

Workarounds:

- **Disable lower C-states** (measurement only):
  ```sh
  sudo cpupower idle-set -D0           # all cores
  sudo cpupower -c 11,12 idle-set -D0  # specific cores
  ```
  *DO NOT do this in production*. Reduces turbo headroom.
  Re-enable: `sudo cpupower idle-set -E`.
- **Use batching** (pipelining, `DO $$ ... LOOP $$ LANGUAGE plpgsql`)
  to reduce wake/idle cycles.
- **Use dedicated C test helpers** (e.g. `deform_bench` in
  `src/test/modules/`) that loop tightly without round-tripping.

### Pitfall 8: Maximize the benchmarked portion (Amdahl)

If the operation under test is 1.5% of the workload, a 10×
speedup of that operation gives 1.4% wall-clock improvement —
indistinguishable from noise. Wrap small operations in
`generate_series()` drivers that make the to-be-benchmarked
portion ≥50% of the workload.

The slide deck's worked examples (with their measured "% of
workload"):

| Benchmark wrapper | Portion of workload |
|---|---|
| `select 1::numeric/3.333` | unmeasurable |
| `select random()::numeric/3.333` | 0.3% (bad) |
| `select sum(i/3.333) from generate_series(1::numeric, 1000) g(i);` | 17.9% (okay) |
| `select sum(i/3.333) from (SELECT generate_series(1::numeric, 1000)) g(i);` | 21.6% (okay) |
| `SELECT * FROM (SELECT generate_series(1::numeric, 1000)) g(i) WHERE I/3.333/i/i = 0;` | 49.5% (decent) |

Quoted from
<https://anarazel.de/talks/2026-05-21-pgconf-pgconf-profiling-postgres-perils/profiling-postgres-perils.pdf>
slide "Maximize to-be-benchmarked".

For C-level micro-benchmarks, write a dedicated bench function:
e.g. `src/test/modules/bench_*` patterns; see `deform_bench`
referenced in Andres's slides.

### Pitfall 9: Huge pages for code (iTLB misses)

PostgreSQL's binary is large enough that its instructions fall out
of the iTLB on hot paths. Workarounds:

- Compile with link-time alignment to 2 MB:
  `-Wl,-zcommon-page-size=0x200000 -Wl,-zmax-page-size=0x200000`
  Yields better hit rate on iTLB.
- Use kernel's `READ_ONLY_THP` for the binary: copy `postgres`
  into a `tmpfs` mounted with `huge=always` and run from there.
  ```sh
  sudo mount -t tmpfs -o huge=always,uid=postgres none /mnt/tmpfs_huge
  cp /path/to/postgres /mnt/tmpfs_huge/
  ```
- Verify with `perf stat -e iTLB-loads,iTLB-load-misses` or the
  AMD-specific `bp_l1_tlb_*` events from the slide deck:
  ```sh
  perf stat -a --delay 1 \
      -e iTLB-loads:u,iTLB-load-misses:u \
      -e bp_l1_tlb_fetch_hit.if2m:u \
      -e bp_l1_tlb_fetch_hit.if4k:u \
      -e bp_l1_tlb_miss_l2_tlb_miss.coalesced_4k:u \
      pgbench ...
  ```

None of the workarounds are great. Track pgsql-hackers for the
in-progress discussion of project-internal solutions (THP for code
is an open infra item).

## `perf top` for live production-style profiling

```sh
sudo perf top -F 99 -ag
```

Live updating "what's hot right now". Useful for shaping a
hypothesis quickly. Not a substitute for `perf record` + flame
graph for archival results.

## `perf report` flags worth knowing

Per Andres's "Other Tipps" slide:

- `perf report --children` (default) — propagates costs to callers.
  Allows seeing "dispersed" bottlenecks where many small functions
  share a parent.
- `perf report --no-children` — does not propagate. Big bottlenecks
  immediately visible.
- Use both. They show different things.
- `perf stat` with constant amount of work (`pgbench -t 10000`,
  not `-T 60`) makes absolute counter values comparable across
  runs.

## Custom workload scripts

For non-pgbench-builtin workloads, `pgbench -f my.sql`. The script
syntax:

```sql
\set aid random(1, 100000 * :scale)
SELECT abalance FROM pgbench_accounts WHERE aid = :aid;
```

`\set`, `\sleep`, `\if`, parameter substitution `:name`, all
documented at
<https://www.postgresql.org/docs/current/pgbench.html>.

For workloads that exercise specific access patterns (sequential
scan, index-only scan, particular planner regression), write the
script in plain SQL and use `\set` to randomise just the
parameters that matter.

## A/B per-run metric checklist (not just TPS)

TPS and latency alone under-report what an A/B comparison needs to show,
especially for a patch that targets something other than raw throughput.
Record these every run, both baseline and patched:

- **WAL volume generated.** Diff `pg_stat_wal` counters (or `pg_current_wal_lsn()`
  before/after) across the run. A patch that trades CPU for extra WAL (or vice
  versa) looks like a pure win on TPS alone and is not.
- **The per-feature `pg_stat_*` counter the change is supposed to move.** If
  the patch targets, say, checkpoint behaviour, read `pg_stat_checkpointer`;
  if it targets vacuum, read `pg_stat_progress_vacuum` / `pg_stat_database`'s
  dead-tuple counters. Confirm the mechanism moved, not just the headline
  number — a flat counter despite a throughput change means the win came
  from somewhere else and the explanation is wrong.
- **Index and table bloat, before and after.** A write-path change that
  looks faster can be winning by deferring work (e.g. skipping a cleanup
  step) that shows up later as bloat; measure it in the same run, not a
  separate pass days later.
- **Peak CPU and RSS**, not just the steady-state average — a change that
  raises peak memory can be invisible in a TPS number but still unsafe on a
  memory-constrained production host.
- **Latency percentiles (p50/p95/p99), not just mean/TPS.** A regression that
  only appears in the tail (p99) is routinely masked by an improved mean; use
  `pgbench -r` (per-script latency report) or your harness's percentile
  output, both baseline and patched, every run.

## Reporting results to -hackers

A -hackers performance post is judged on the methodology
*before* the numbers. Include:

1. Baseline commit SHA and patched commit SHA.
2. Hardware spec (CPU, RAM, storage, NUMA).
3. OS / kernel / filesystem / mount.
4. `postgresql.conf` diff from default.
5. The exact pgbench / custom invocation.
6. Boost / C-state / pinning state.
7. Number of runs, alternation pattern, run length, warm-up.
8. Median + variance (or full distribution).
9. `perf stat -ddd` for both baseline and patched.
10. Wait-event distribution if relevant.

A well-formatted report looks like Andres's or Vondra's mailing-
list posts; use them as templates.

## Sources

- **Andres Freund, "Profiling Postgres Perils"** (PGConf.dev
  2026-05-21):
  <https://anarazel.de/talks/2026-05-21-pgconf-pgconf-profiling-postgres-perils/profiling-postgres-perils.pdf>
  Local copy: `/scratch/andres-talks/profiling-postgres-perils.pdf`.
  Authoritative source for the 9-pitfall checklist and all the
  benchmark-portion / iTLB / C-state numbers cited above.
- **Tomas Vondra, "Benchmarking is hard, sometimes"**:
  <https://vondra.me/posts/benchmarking-is-hard-sometimes/>.
  Cited from Andres's slide deck.
- **Tomas Vondra, "The real cost of random I/O"** (2026-02-26):
  <https://vondra.me/posts/the-real-cost-of-random-io/>. For
  random_page_cost discussions.
- **Tomas Vondra, "Where do performance cliffs come from?"**
  POSETTE 2024 (YouTube `UzdAelm-QSY`),
  SFPUG 2025 (YouTube `j0ISi1KVulU`). Methodology for hunting
  performance cliffs.
- Andres's talks index: <https://anarazel.de/talks/>. Relevant:
  - 2024-10-23 PGConf.EU "NUMA vs. PostgreSQL".
  - 2024-05-29 PGConf.dev "C2C" (cross-core cache).
- Docs: <https://www.postgresql.org/docs/current/pgbench.html>.
- Brendan Gregg's flame graph tool:
  <https://github.com/brendangregg/FlameGraph>.
- BCC tools: <https://github.com/iovisor/bcc>.
- Intel Top-Down methodology:
  <https://www.intel.com/content/www/us/en/docs/vtune-profiler/cookbook/2023-0/top-down-microarchitecture-analysis-method.html>.
- `perf-stat(1)`, `perf-record(1)`, `perf-report(1)` man pages.
- Cross-reference: `community/voices/andres-freund.md` for Andres's
  recurring performance-review patterns.
- Cross-reference: `community/voices/tomas-vondra.md` for Vondra's
  performance-cliff methodology.
- Cross-reference: `generic/workflows/build-and-test.md` § "Recommended
  developer build" — note this is a *different* (no-cassert) build
  than the one used here.
- Cross-reference: `generic/workflows/debug-backend.md` for the
  `pg_stat_activity` wait-event introspection used in Pitfall 1.
