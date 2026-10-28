---
name: pg-benchmark-rigor
description: >
  The measurement discipline PostgreSQL committers apply before they believe a
  benchmark or a profile: preflight of CPU boost, idle states, pinning, THP,
  SSD state and counters; A/A noise floor; interleaved run order with waits;
  multiple builds against code-layout noise; the right summary statistic; and a
  STABLE / NOISY / UNSTABLE verdict instead of a bare number. Use whenever you
  benchmark, compare, or profile PostgreSQL (pgbench, a microbenchmark, perf),
  when results look unstable, or when deciding whether a cloud host or owned
  hardware can answer the question. Layers on the generic `benchmark` and
  `tune-os-for-benchmark` skills.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
---

# PostgreSQL benchmark rigor

Most casual performance numbers are artefacts of the method. This skill is the
checklist an agent follows so that a PostgreSQL result survives review on
pgsql-hackers, and the rule for what to say when it cannot. Sources for each
rule, the places they disagree, and the cloud-vs-owned-hardware capability
matrix are in [`references/sources.md`](references/sources.md); the A/A rule
and the verdict scheme are this skill's own synthesis.

Pair with: [`benchmark`](../benchmark/SKILL.md) (generic A/B workflow, remote
runs), [`tune-os-for-benchmark`](../tune-os-for-benchmark/SKILL.md) (per-OS
commands), [`choose-instance`](../choose-instance/SKILL.md), and the
[`perf-testing`](../../generic/workflows/perf-testing.md) workflow (pgbench
recipes, the profiling pitfalls from Andres Freund's talk in detail).

## Hard rules

1. **Never report a single run.** Run for minutes, not seconds, and repeat.
   A read-write pgbench run should cover 2-3 checkpoints; five such runs is
   normal, so a comparison can take hours. A read-only run does no
   checkpoints and can be much shorter (Vondra: "a minute, maybe?"), but
   still needs several runs.
2. **Never run all of A, then all of B.** Frequency and thermal drift bias
   whichever ran second. Interleave (ABBA or randomised order) and wait between
   runs.
3. **Run A/A first.** The same binary against itself gives the noise floor. A
   difference no larger than the A/A spread is not a result.
4. **Measure only what you changed.** If the code under test is 1.5% of the
   runtime, a 10x speedup moves the total from 60 to 59.19. Shape the query (or
   write a C benchmark function) so the code under test dominates.
5. **Cycles are the wrong profile for contention.** If adding clients does not
   add throughput, look at wait events or off-CPU time, not `perf record`.
6. **Code layout is a confounder.** An unrelated code change or a relink with
   another layout can move results 1-5%. A claimed effect under ~5% needs several builds with shuffled layout.
7. **Label pinned results as pinned.** Pinning cuts noise but can hide real
   scheduler behaviour.
8. **Ask before changing a host.** Every sysfs, sysctl and procfs write and
   every kernel-cmdline change in section 1 is for benchmark machines only.
   Print the commands; run them only with the owner's approval, and revert
   afterwards (re-enable ASLR, boost, idle states, SMT).
9. **Low noise is necessary, not sufficient.** Link order and even the size of
   the environment can flip a conclusion (O2 vs O3 in Mytkowicz et al.:
   measurement bias).
10. **If you cannot control it, say so.** Report a verdict (below), never a
    bare number from an uncontrolled run.

## 1. Preflight

Record every item; a change in any of them invalidates comparison with earlier
results (CPU model, compiler version and separate builds all move numbers).

| Control | How | Why |
|---|---|---|
| Quiesce | stop other work; load average near 0; stop auto-update and cron for the run | background noise; checking why a supposedly idle benchmark box was noisy led Freund to the xz backdoor |
| Boost off (Intel) | `echo 1 \| sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo` (only with the `intel_pstate` driver) | slower but predictable |
| Boost off (AMD) | `echo 0 \| sudo tee /sys/devices/system/cpu/cpufreq/boost`; if absent, check `scaling_driver` | same |
| Governor | `cpupower frequency-set -g performance` | ~160 ms vs ~280 ms swings in one hackers thread became much more stable with this plus boost off |
| Idle states | `cpupower idle-set -D0` (undo `-E`), or boot `idle=poll` | latency after idle is ~5x higher; both options cost turbo headroom and power |
| Pinning | `numactl --physcpubind=<cpus>`; pinning the postmaster pins its children | cores differ (boost up to 15%, P/E cores, memory distance, interrupts) |
| Client placement | record it | same-core vs different-core client/server moved single-client `pgbench -S` by 6% |
| THP | `never` for `enabled` and `defrag` | background compaction stalls |
| SMT / ASLR / shielding | offline siblings, `randomize_va_space=0`, `cset shield` (cgroup v1; on v2 use `isolcpus=`/`nohz_full=` or a cpuset partition) | LLVM reports under 0.1% variation with these |
| SSD state | `fstrim -v`, over-provision, use a small part of the drive, rest between write-heavy runs | write throughput degrades run over run |
| Caches (cold runs) | `pg_buffercache_evict_relation()` (PG 18+, `pg_buffercache` extension, superuser), `sync; echo 3 > /proc/sys/vm/drop_caches` | neither clears the SSD's own DRAM cache |
| Counters | `perf stat -e cycles true` must show hardware events | when a hypervisor hides the PMU, perf falls back to timer sampling, which is very inaccurate |
| Real clock | read APERF/MPERF (`turbostat`) during the run | verifies boost really is off; turbo alone can skew 10%+ |
| Build | optimised, no `--enable-cassert`; frame pointers for profiling | assert builds measure the asserts (Mozilla: debug builds distort profiles) |

Output of preflight: the environment record (CPU model and microcode, kernel,
governor, boost, idle states, THP, SMT, NUMA layout, VM or metal, storage
model, compiler, configure flags, PostgreSQL commit) plus the list of controls
you could not set.

## 2. Run protocol

1. **Scale >= clients** for pgbench, or you measure `pgbench_branches`
   contention. Check pgbench itself is not the bottleneck.
2. **Same starting state** every run (re-init or reset): results depend on time
   since init, dead tuples and autovacuum.
3. **Warm up to steady state.** Watch `pgbench -P 1`; one documented case took
   ~200 s. The first runs after startup also pay shared-memory page faults
   (the kernel reserves the segment but touches few pages); adding
   `MAP_POPULATE` to the `mmap()` calls in `src/backend/port/sysv_shmem.c`
   removes that noise on a benchmark build (Vondra; not an upstream option).
   Discard warm-up.
4. **Interleave and wait.** ABBA or random order; wait 10s of seconds between
   runs for clock drift, minutes to hours for SSD recovery.
5. **Constant work for `perf stat`**, so absolute counts compare.
6. **Several builds for small effects.** Build each side with different
   layout seeds (`LDFLAGS="-fuse-ld=mold -Wl,--shuffle-sections=$SEED"`); summarise per build, then across builds.
7. **Distrust very short queries.** On a 176-core EPYC, read-only pgbench fell
   from ~500k to ~350k tps around 22 clients; pinning moved the dip, pipelining
   removed it, an idle-priority CPU burner raised throughput, and the cause is
   unresolved. Vary client count and try pipelining before trusting a curve.

## 3. Statistics

- **Repeat at every level that varies:** builds, executions, iterations.
- **Summary statistic by context:** the *minimum* for a microbenchmark inside
  one binary (timing noise only adds delay, so its distribution is skewed and
  multimodal); the *median across shuffled builds* for system throughput. The
  split is our reconciliation of two sources; see `references/sources.md`.
- **Effect with an interval**, never a lone ratio: "B/A = 1.03, 95% CI
  [1.01, 1.05], 3 builds x 5 runs".
- **Repetition does not remove bias.** A biased setup repeated 100 times is
  still biased; randomise the setup instead.
- **Continuous benchmarking:** change-point detection (E-Divisive means), not a
  static threshold (MongoDB counted up to 99% false positives with thresholds,
  "depending on how you count"); run canary workloads that should never change; correlated noise
  still gets through.
- **Before accepting any result** (Gregg): why not double? was it tuned? did it
  break limits (need more bandwidth or IOPS than the hardware has)? did it error? does it reproduce? does it matter? did it really
  happen?

## 4. Profiling

- Confirm hardware counters, then fix the amount of work.
- `perf stat -ddd` first: memory latency, dTLB/iTLB and branch misses; Intel's
  Top-Down method for the breakdown.
- Read `perf report` with both `--children` and `--no-children`.
- Build with `-fno-omit-frame-pointer` for usable stacks.
- iTLB-bound: put code on huge pages. Either link with
  `-Wl,-zcommon-page-size=0x200000 -Wl,-zmax-page-size=0x200000` on a kernel
  with `READ_ONLY_THP_FOR_FS` (this needs THP enabled, so it conflicts with
  `never`), or run the binary from a `tmpfs` mounted `huge=always`, which works
  with THP `never`. Freund: none of the workarounds are great.
- Causal profiling (Coz) estimates what speeding up a region would buy.
  Stabilizer re-randomises layout and often makes times near-normal, but is
  unmaintained; shuffled-section builds are the practical substitute.
- No committer source covers DWARF vs LBR unwinding, skid or PEBS; if you rely
  on them, say it is your judgement.

## 5. Why is it unstable?

| Symptom | Likely cause | Test |
|---|---|---|
| later runs faster/slower in fixed order | clock or thermal drift | reverse order; check APERF/MPERF |
| write runs degrade over a session | SSD state | `fstrim`, rest, rerun |
| unrelated change or relink, 1-5% shift | code layout | shuffled multi-build |
| fast on one core, slow on another | core variation, interrupts | pin to other cores |
| low-client latency worse after idle | C-states | `idle-set -D0`, compare |
| dip at one client count | scheduler + idle interaction | pin, pipeline, idle-priority filler |
| first runs after restart slow | shmem page faults, cold caches | longer warm-up |
| random multi-ms stalls | THP compaction | THP `never` |
| coarse, odd perf profile | no hardware counters | check for virtualisation |
| moved with no config change | host, firmware or microcode changed | diff the environment record |

## 6. Verdict and report

Every result ends with one verdict:

- `STABLE`: A/A spread is well below the claimed effect.
- `NOISY - CONCLUSION LIMITED`: list the uncontrolled items and what they
  could do to the number.
- `UNSTABLE - NO CLAIM`: A/A spread is at or above the effect. Report the
  spread, not a winner.

Report: hypothesis; environment record; A/A floor; run order and count; builds;
summary statistic and why; effect with interval; verdict; uncontrolled items.
Raw per-run data goes with it (CSV), as reviewers on pgsql-hackers ask for it.

**Engineering-sample CPUs:** fine for an A/B on the same box, but do not
compare their absolute numbers with retail parts, cloud hosts or production.
This is our judgement, not a sourced committer rule (see
`references/sources.md`).

## Where to run

Cloud bare metal gives you the OS-level controls above (AWS lets the OS set
C-states and P-states on Intel and AMD metal) but no firmware access, and AWS
documents no guarantee that the next host, firmware or microcode is the same.
Owned hardware adds firmware-only knobs (package C-state limit, sub-NUMA
clustering, UPI and memory settings, firmware core disable) and a platform you
can hold fixed for years. C1E and the prefetchers also have OS paths
(`cpupower idle-set -d`, MSR 0x1A4), untested on EC2. Use cloud metal for relative A/B inside one
reservation; use owned hardware when the question needs a firmware setting or a
long-lived fixed baseline. Details and sources:
[`references/sources.md`](references/sources.md#where-to-run-cloud-metal-vs-owned-hardware).
