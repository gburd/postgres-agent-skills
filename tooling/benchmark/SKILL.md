---
name: benchmark
description: >
  Run a reproducible performance benchmark with a measure-correctly workflow,
  on the local machine or on a remote host over SSH (a LAN box, a lab server,
  or a cloud instance). Covers A/B methodology, warm-up, repetition and
  variance, controlling for drift, sizing the working set against cache, and
  collecting machine-readable results. Use for ANY benchmark — CPU, memory, IO,
  database, application. For picking a cloud instance to run on, pair with the
  `choose-instance` skill; for making the OS measurement-grade first, pair with
  `tune-os-for-benchmark`.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
---

# Benchmark — measure correctly, locally or over SSH

A benchmark is only useful if it is reproducible and its result is not an
artefact of drift, caching, or a noisy machine. This skill is the methodology;
it is workload-agnostic (load your specific build/data/runner at the workload
step) and host-agnostic (run it here or drive a remote host over SSH).

## Where to run

- **Local** — fine for relative A/B of two builds when the machine is otherwise
  idle. Close other work; results on a laptop under thermal throttling are
  suspect.
- **Remote over SSH** — a dedicated LAN box or lab server removes your desktop's
  noise and lets long runs proceed unattended. Drive it with a single script:

  ```bash
  HOST=bench01.lan            # or user@host, or an SSH config alias
  scp ./run-bench.sh "$HOST":/tmp/
  ssh "$HOST" 'bash /tmp/run-bench.sh' | tee results-$(date +%Y%m%d-%H%M%S).log
  # pull machine-readable output back
  scp "$HOST":/tmp/bench-out/*.csv ./results/
  ```

  Prefer a persistent session (`tmux`/`screen` on the remote, or
  `ssh -o ServerAliveInterval=30`) so a dropped connection does not kill a
  multi-hour run. Record the remote host's exact spec (CPU, RAM, kernel, OS,
  filesystem) alongside the results — a number without its machine is noise.

- **Cloud instance** — same as remote-over-SSH, plus pick the right instance
  (`choose-instance`) and **remember to terminate it** when done.

Make the OS measurement-grade before the first run — see
`tune-os-for-benchmark`. An untuned host (frequency scaling, THP, a busy
background cron) will produce results you cannot trust or reproduce.

## The workflow

1. **Define the question precisely.** "Is build B faster than build A on
   workload W at parameter P?" A benchmark without a specific comparison is a
   number with nothing to compare it to.
2. **Fix the environment.** Same host, same OS, same kernel, same filesystem,
   same background load for both variants. Record all of it. Refuse to run with
   a dirty source tree.
3. **Build both variants from the same checkout**, each into its own prefix, so
   the only difference is the change under test. For a feature branch, compare
   against its **merge-base with the mainline**, not an arbitrary tip, to
   isolate the feature from unrelated churn.
4. **Size the working set against the relevant cache.** To exercise the eviction
   / IO path you must exceed RAM (or the buffer pool, or the CPU cache,
   whichever the test targets); otherwise you only measure the cache.
5. **Warm up, then measure.** Discard the first run(s) (cold cache, JIT,
   autovacuum/compaction settling); measure steady state.
6. **A/B alternate, do not batch.** Run A, B, A, B, ... at each parameter point,
   not all-A then all-B. Hardware, thermal, and noisy-neighbour drift over a
   long run otherwise biases whichever variant ran second. At least 3 (better 5)
   measured repetitions per point.
7. **Record raw, machine-readable output** (CSV/JSON) per run, not just a
   summary: the metric, every repetition, and the conditions. Compute median
   and spread (IQR or stddev) afterwards.
8. **Report with variance.** "B is 1.00x +/- 0.04 vs A over 5 runs" is a result;
   "B was faster" is not. If the spread overlaps zero, say the result is
   inconclusive rather than picking a winner.

## What to record every time

- Hardware: CPU model, core/thread count, NUMA topology, RAM, storage device.
- Software: OS + version, kernel, filesystem + mount options, compiler/runtime
  versions, the exact revisions of both variants.
- Tuning applied (governor, THP, hugepages, etc. — see `tune-os-for-benchmark`).
- The workload definition and every parameter point.
- Per-run raw numbers and the derived median/spread.

A timestamped results directory with a CSV plus a short Markdown summary makes
runs comparable over time; re-run the same harness after any rebase so
regressions are caught against the current mainline.

## Common ways a benchmark lies (control for each)

- **Drift** — thermals/neighbours over a long batched run → A/B alternate.
- **Cache** — working set fits in RAM/cache → size it bigger, or state that you
  are measuring the cached path deliberately.
- **Cold start** — first run includes warm-up cost → discard it.
- **Frequency scaling** — governor ramps mid-run → pin `performance`
  (`tune-os-for-benchmark`).
- **Background load** — a cron job, an auto-update timer, another tenant fired
  mid-run → quiesce the host; stop auto-update/maintenance timers for the
  duration; check `uptime`/load before each point.
- **Stale build** — the thing you measured was not the thing you changed →
  verify the binary/revision actually rebuilt before trusting a delta.
- **One run** — a single number has no error bar → repeat.
