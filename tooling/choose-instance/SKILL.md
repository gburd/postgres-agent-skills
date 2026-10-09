---
name: choose-instance
description: >
  Choose a cloud instance type (or a short list of candidates) to run a
  benchmark on, across providers (AWS, GCP, Azure, Hetzner, Equinix Metal,
  OVH, and others). Covers matching the instance to what the benchmark stresses
  (CPU, memory bandwidth, IO, NUMA topology), when a bare-metal instance is
  required vs. a shared VM, sizing storage and network, spot/preemptible
  trade-offs, and cost control. Use before launching anything to benchmark on
  cloud infrastructure; pair with `benchmark` (methodology) and
  `tune-os-for-benchmark` (making it measurement-grade).
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
---

# Choose a cloud instance for benchmarking

Pick the smallest instance that faithfully represents what you are measuring,
and know when "faithfully" forces you up to bare metal. The wrong instance
produces a precise answer to the wrong question.

## First: what does the benchmark actually stress?

Match the dominant resource, because that decides the instance family:

| Bottleneck | Pick for | Example families |
|------------|----------|------------------|
| CPU / clock | high per-core perf, few fast cores | AWS `c7i`/`c7a`/`c8g`, GCP `c3`/`h3`, Azure `Fsv2`, Hetzner `CCX` |
| Memory capacity | large RAM, buffer pools, caches | AWS `r7i`/`r8g`, GCP `m3`, Azure `Esv5` |
| Memory bandwidth / NUMA | multi-socket topology, bandwidth | **bare metal** `.metal`, Equinix Metal, large `m`/`r` metal |
| Storage IO | local NVMe, high IOPS | AWS `i4i`/`im4gn` (local NVMe), GCP `z3`, Azure `Lsv3` |
| Network | high bandwidth, low jitter | the `n`/`...n` network-optimised variants |
| Balanced / app | general mix | AWS `m7i`/`m8g`, GCP `n2`/`c3`, Azure `Dsv5`, Hetzner `CX`/`CPX` |

Architecture matters: ARM (Graviton `*g`, Ampere, Axion) vs x86 is itself a
variable — benchmark on the arch you deploy on, and never A/B across arches by
accident.

## When you need bare metal (and when you do not)

Use a `.metal` / dedicated bare-metal instance only when the benchmark is
sensitive to things a hypervisor hides or perturbs:

- **real NUMA topology** (multi-socket, sub-NUMA clustering) — a VM often
  presents a flattened or fictional topology;
- **no hypervisor jitter** — tail-latency and scheduler-sensitive tests;
- **hardware counters / `perf`** at full fidelity;
- **huge, stable allocations** (hugepages) without balloon interference.

Otherwise a regular large VM is cheaper, launches in seconds, and is perfectly
valid for relative A/B of two builds. Do not pay for metal to measure something
a VM measures identically.

## Size the rest to the workload

- **vCPU/core count** — enough to run the workload's concurrency plus headroom;
  more is not better if the test is single-threaded (you pay for idle cores).
  Know whether "vCPU" means a full core or an SMT thread on that family.
- **RAM** — deliberately *smaller* than the dataset when you want to exercise
  eviction/IO; comfortably *larger* when you want to measure the in-memory path.
  Decide which, per the `benchmark` skill.
- **Storage** — for IO tests prefer **local NVMe** instances (predictable,
  no network-storage throttling) over network block storage. If you must use
  network storage (AWS EBS gp3/io2, GCP PD/Hyperdisk, Azure managed disks),
  **provision IOPS and throughput explicitly** — defaults throttle and will cap
  your result below the hardware.
- **Network** — only size up if the benchmark is network-bound; note the
  advertised bandwidth is a ceiling, often burst.

## Spot / preemptible

Spot (AWS) / preemptible (GCP) / low-priority (Azure) instances are 60-90%
cheaper and fine for *interruptible* benchmark runs if your harness
checkpoints results as it goes. Do **not** use them for a single long
unattended run that loses everything on reclaim, or for latency-sensitive runs
where a mid-run migration perturbs the measurement.

## Cost control (the expensive mistakes)

- **Bare metal is $4-15+/hr.** A forgotten instance is the single biggest cost
  error. Note the launch, set an alarm, and terminate the moment you have the
  CSVs (see `benchmark`).
- **Prefer the cheapest instance that still answers the question** — step up to
  metal/bigger only when a cheaper tier demonstrably distorts the result.
- **Pick a region close to you** for lower SSH latency and (often) lower price;
  check the per-region price, they vary.
- **Short-list, then test one.** Name 2-3 candidates and their hourly cost;
  launch the cheapest adequate one first and only escalate if it is unfaithful.

## Output of this skill

A concrete recommendation: a primary instance type + region + hourly cost, a
one-line justification tying it to the benchmark's bottleneck, whether bare
metal is required and why, storage/network sizing, and a cheaper fallback.
Then hand off to `tune-os-for-benchmark` and `benchmark`.
