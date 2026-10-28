# Sources and the cloud-vs-owned-hardware matrix

Every rule in [`../SKILL.md`](../SKILL.md) traces to one of these. Each figure
was checked against the source text on 2026-10-20. Where a line is our
inference rather than a quote, it says **[inferred]**; where we looked and found
nothing, it says **[not found]**.

## PostgreSQL committers and contributors

- **Andres Freund, "Profiling Postgres Perils"**, PGConf.dev, 2026-05-21.
  Slides: <https://anarazel.de/talks/2026-05-21-pgconf-profiling-postgres-perils/profiling-postgres-perils.pdf>;
  session: <https://2026.pgconf.dev/session/594>.
  - Boost off (`intel_pstate/no_turbo`, `cpufreq/boost`), marked "DO NOT DO
    THIS IN PRODUCTION"; "slower but predictable"; swap the order of
    benchmarks; wait between runs ("10s of seconds").
  - Write-heavy SSD runs degrade: over-provision, `fstrim -v`, use a small
    part of the drive, better SSDs, wait "minutes to hours".
  - Cores are not equal: "different boost speeds (I've seen up to 15%)",
    efficiency vs performance cores, memory distance, interrupts;
    `numactl --physcpubind 1,17 <task>`.
  - Idle states: latency 0.047 ms before a `\sleep 10ms`, 0.235 ms after;
    same-core client/server 42,552 TPS vs different cores 40,057 TPS on
    single-client `pgbench -S`; `cpupower idle-set -D0` (re-enable `-E`);
    disabling idle states reduces turbo potential.
  - Amdahl: `select 1::numeric/3.333` "unusable" vs a `generate_series` form at
    49.5% of runtime; a 10x speedup on 1.5% moves 60 to 59.19; dedicated C
    benchmark functions (`deform_bench`).
  - Contention: `LOCK pgbench_accounts` gives 5.793 tps at 1 client and 5.919
    at 8; use wait events / off-CPU profiling.
  - `perf stat -ddd`; Intel "Top Down" methodology; under virtualisation perf
    emulates cycles with a timer, "very inaccurate, particularly with lots of
    context switches".
  - Code on huge pages: `-Wl,-zcommon-page-size=0x200000
    -Wl,-zmax-page-size=0x200000` or a `tmpfs` with `huge=always`; constant
    work for `perf stat`; `perf report --children` and `--no-children`.
- **Andres Freund, review of "More speedups for tuple deformation"**,
  pgsql-hackers, 2026-01-23:
  <https://postgr.es/m/pmik622adey6fnddivkt4uvkulvnc6rasmq3tcbrzeglx4hsn7@f3x6e2eph3w5>.
  "I disabled turbo boost, cpu idling and pinned the backend to a single CPU
  core"; one machine had light noise with everything pinned to the other
  socket, the other was entirely idle; he removed the script's `sleep 10` "to
  reduce runtimes, the results seem stable enough anyway".
- **Andres Freund on Oxide and Friends, "Discovering the XZ Backdoor"**:
  <https://oxide-and-friends.transistor.fm/episodes/discovering-the-xz-backdoor-with-andres-freund/transcript>.
  Repeated benchmark runs "varied a bit too much for my liking", so he checked
  whether the system was idle; a server CPU "and I didn't have turbo boost
  enabled".
- **Andres Freund on Talking Postgres (AIO episode)**:
  <https://talkingpostgres.com/episodes/what-went-wrong-what-went-right-with-aio-with-andres-freund/transcript>.
  Learning low-level benchmarking "has unexpected benefits". No BIOS content.
- **Tomas Vondra, "Stabilizing Benchmarks"**:
  <https://vondra.me/posts/stabilizing-benchmarks/>.
  - Read-write pgbench: "5 runs, each long enough to cover 2-3 checkpoints";
    warm-up visible in `pgbench -P 1` (his example ~200 s); 1000 vs 1100 tps
    means little if runs vary by ~200 tps; he usually doesn't bother with
    statistical models for run counts.
  - `pg_buffercache_evict_relation`, `drop_caches`, the SSD's own cache;
    `MAP_POPULATE` in the `mmap()` calls of `src/backend/port/sysv_shmem.c`
    for shared-memory page faults ("maybe we should add this as a developer
    GUC"); THP `never` for `enabled` and `defrag`. A read-only pgbench "has
    nothing to do with checkpoints, so runs can be much shorter (a minute,
    maybe?)". Re-checked 2026-10-28.
  - Code layout: 10 builds with different `mold --shuffle-sections` seeds,
    10 runs each, ~1% within a build, close to 5% between builds; average or
    median across builds.
  - pgbench `--pin-cpus` patch (`none` / `colocated` / `random`); pinning the
    postmaster pins its children; `idle=poll` ("don't do this except when
    benchmarking"); CPU model, compiler and separate builds change results.
- **Tomas Vondra, "Benchmarking is hard, sometimes..."**:
  <https://vondra.me/posts/benchmarking-is-hard-sometimes/>.
  176-core EPYC, read-only pgbench scale 50, ~500k to ~350k tps at ~22 clients;
  colocated pinning removed it, random pinning moved it to ~45; `stress` under
  `SCHED_IDLEPRIO` raised throughput to ~1.3M; pipelining removed it; NUMA
  balancing, autogroup, THP and kernel 6.15 did not; reproduced on FreeBSD 14.1;
  `cpupower idle-set -D 1` made no difference on his Xeon; cause unresolved.
- **Alexander Lakhin, "Re: Streaming read-ready sequential scan code"**,
  pgsql-hackers, 2024-08-29:
  <https://postgr.es/m/679d9fe8-360d-7324-2809-d0ee46493f55@gmail.com>.
  Runs alternating ~160 ms and ~280 ms became stable "with the 'performance'
  governor set and the boost mode disabled (I do this tuning before running
  performance tests...)".
- **Melanie Plageman on Postgres FM, "Getting started with benchmarking"**:
  <https://postgres.fm/episodes/getting-started-with-benchmarking/transcript>.
  "As a benchmarker, you're kind of accountable for the analysis and trying to
  find out if your results are valid."
- **pgbench documentation, "Good Practices"**:
  <https://www.postgresql.org/docs/current/pgbench.html>. Never trust a run of
  a few seconds; scale factor at least as large as the client count, or you
  measure `pgbench_branches` contention; results depend on time since init,
  dead rows and autovacuum; pgbench can be the bottleneck.
- **[not found]** Benchmarking-methodology writing by Ants Aasma, Heikki
  Linnakangas, Thomas Munro or Tom Lane. Munro appears only as a patch author
  (the Lakhin thread; Vondra's `_bt_getroot` mention).
- **[not found]** Any committer source on DWARF vs LBR unwinding, sampling
  skid or PEBS.

## Measurement science

- **Mytkowicz, Diwan, Hauswirth, Sweeney, "Producing Wrong Data Without Doing
  Anything Obviously Wrong!"**, ASPLOS 2009:
  <https://gwern.net/doc/cs/algorithm/2009-mytkowicz.pdf>. Link order and UNIX
  environment size changed O2-vs-O3 conclusions; remedies are setup
  randomisation (484 setups, 3 runs each, t-test) and causal analysis.
- **Kalibera & Jones, "Rigorous benchmarking in reasonable time"**, ISMM 2013:
  <https://dl.acm.org/doi/abs/10.1145/2464157.2464160>. Repeat at the levels
  that vary (builds, executions, iterations); report an effect-size confidence
  interval. Abstract only; the full text was not reachable.
- **Chen & Revels, "Robust benchmarking in noisy environments"**, 2016:
  <https://arxiv.org/abs/1608.04295>. Timing measurements are not i.i.d.; mean
  and median can be multimodal; the minimum is unimodal and is their
  estimator. Repetition alone does not remove environmental bias.
- **Daly et al., "Change Point Detection in Software Performance Testing"**
  (MongoDB), ICPE 2020: <https://arxiv.org/abs/2003.00584>. E-Divisive means;
  up to 99% false positives with the old thresholds; canary tests; noise that
  is correlated with time is not handled well.
- **Brendan Gregg, "Evaluating the Evaluation: A Benchmarking Checklist"**:
  <https://www.brendangregg.com/blog/2018-06-30/benchmarking-checklist.html>.
  The seven questions; let load averages reach 0.00; run ten times.
- **Brendan Gregg, "The MSRs of EC2"**:
  <https://www.brendangregg.com/blog/2014-09-15/the-msrs-of-ec2.html>. Turbo
  puts many measurements' error margin over 10%; measure real clock with
  APERF/MPERF; two identical servers at the top and bottom of a rack differed
  5%; as an EC2 Xen guest you can't change the BIOS.
- **Brendan Gregg, "The Return of the Frame Pointers"**:
  <https://www.brendangregg.com/blog/2024-03-17/the-return-of-the-frame-pointers.html>.
- **LLVM, "Benchmarking tips"**: <https://llvm.org/docs/Benchmarking.html>.
  ASLR off, boost off, performance governor, `cset shield`, SMT siblings
  offline, `perf stat -r 10`; "less than 0.1%" variation; tmpfs for inputs;
  low noise is not enough because of measurement bias.
- **Mozilla, "Benchmarking"**:
  <https://firefox-source-docs.mozilla.org/performance/Benchmarking.html>, and
  the SpiderMonkey agent skill:
  <https://firefox-source-docs.mozilla.org/ai-agent-tools/skills/js-perf-investigation/SKILL.html>.
- **Coz** (causal profiling): <https://github.com/plasma-umass/coz>.
  **Stabilizer** (layout re-randomisation): <https://people.cs.umass.edu/~emery/pubs/stabilizer-asplos13.pdf>.

## Where to run: cloud metal vs owned hardware

What the platform lets you set. Gigabyte MS73-HB1 (dual 4th/5th-gen Xeon
Scalable, Sapphire/Emerald Rapids) is the owned-hardware example; options are from its manual,
<https://download.gigabyte.com/FileList/Manual/server_mb_manual_MS73-HB0_1_e_v1.0.pdf>.

| Control | EC2 bare metal | Owned board (MS73-HB1) |
|---|---|---|
| Firmware/BIOS | none (community answer, not AWS docs: <https://repost.aws/questions/QUko15IyYKQ164x3UF0Ka72w/>) | full setup menu |
| C-states, P-states from the OS | yes, "all bare metal instances with Intel and AMD processors" (<https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/processor_state_control.html>) | yes |
| Turbo | OS `no_turbo` / `boost` **[inferred]**, verify with APERF/MPERF | BIOS Turbo Mode, or OS |
| SMT | OS offlining only; `CpuOptions` rejected for `c5n.metal` (<https://github.com/aws/aws-parallelcluster/issues/1855>) | BIOS "Enable LP" (all / single) |
| Firmware core disable | no | per-socket Core Disable Bitmap |
| Package C-state limit, MWAIT | no **[inferred]** | BIOS |
| C1E | possibly from the OS (`intel_idle` state, `cpupower idle-set -d <n>`) **[inferred]** | BIOS or OS |
| Hardware P-state mode, Energy Perf Bias | fixed by AWS **[inferred]** | BIOS (Native / Out-of-Band / ...; EPB OS/BIOS/PECI) |
| Sub-NUMA clustering | fixed per instance type **[inferred]** | BIOS (SNC2 / SNC4 / off) |
| Prefetchers (HW, adjacent-line, DCU streamer, DCU IP) | possibly via MSR 0x1A4, untested on EC2 **[not found]** | BIOS, or MSR |
| UPI link speed, memory frequency, patrol scrub, ADR | fixed **[inferred]** | BIOS |
| Uncore frequency | Linux `intel_uncore_frequency` if exposed **[not found]** | Linux sysfs (`min_freq_khz` / `max_freq_khz`) |
| Hardware counters, RAPL | available on metal (RAPL seen on `i3.metal`: <https://github.com/sustainable-computing-io/kepler/discussions/1116>) | available |
| Same host, firmware, microcode next month | no documented guarantee **[inferred]** | yes |
| Cost of hours of rest between runs | billed hourly | electricity |

Notes:

- Hypervisor overhead is not the argument: AWS measured metal vs full-size
  virtual instances "within 1%" on its tests
  (<https://aws.amazon.com/blogs/hpc/bare-metal-performance-with-the-aws-nitro-system/>).
  The argument for owned hardware is control and a fixed baseline.
- A cloud can expose firmware knobs: Oracle bare metal sets cores, NPS, SMT,
  access control service, IOMMU and more at launch, not afterwards
  (<https://docs.oracle.com/en-us/iaas/Content/Compute/References/bios-settings.htm>).
- **[not found]** A source on engineering-sample CPUs (that their absolute
  numbers may not transfer to retail parts). Neither Freund's slides nor
  Vondra's posts mention them; the SKILL.md line is our judgement.
- **[not found]** A source for the claim that some BIOS settings exist only on
  a machine you own. The slides, the two podcasts and the hackers threads above
  do not contain it. The matrix shows which controls are firmware-only; that
  is the defensible form of the claim.

## Where sources disagree

- **Idle states:** Freund uses `cpupower idle-set -D0`; Vondra suggests
  `idle=poll`; both cost turbo headroom, and `idle-set -D 1` did nothing on one
  of Vondra's Xeons. Pick one, record it, and check it took effect.
- **Pinning:** reduces noise (Freund), but is not a fix and can hide real
  behaviour (Vondra). Report pinned results as pinned.
- **THP vs code on huge pages:** Vondra turns THP off; Freund wants code on
  huge pages. Only the `tmpfs huge=always` route works with THP `never`; the
  link-flag route relies on `READ_ONLY_THP_FOR_FS` and THP enabled.
- **Minimum vs median:** Chen & Revels use the minimum for microbenchmarks;
  Vondra uses mean/median across builds for throughput. The skill uses the
  minimum inside one binary and the median across shuffled builds; that split
  is our reconciliation.
- **Waiting vs warm-up:** waiting between runs controls clock and SSD drift;
  warm-up reaches steady state. They are separate controls.
