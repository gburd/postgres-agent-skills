---
name: tune-os-for-benchmark
description: >
  Configure an operating system so a benchmark run is accurate and
  reproducible, on any OS: Linux, the BSDs (FreeBSD/OpenBSD/NetBSD), illumos
  (OmniOS/SmartOS), and Windows. Covers CPU frequency scaling and governors,
  transparent hugepages and explicit hugepages, NUMA placement, interrupt and
  thread affinity, filesystem and mount choice, disabling background jitter
  (auto-update, indexing, telemetry), and verifying the machine is actually
  quiesced. Use after choosing a host/instance and before the first measured
  run; pair with `benchmark` and `choose-instance`.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
---

# Tune the OS for an accurate benchmark

An untuned machine lies: frequency scaling ramps mid-run, transparent
hugepages pause you for compaction, a background updater fires at run 3, NUMA
balancing migrates your pages. Quiesce and pin the machine first, record what
you changed, and **revert it after** so the box is not left in a benchmark-only
state. The principles are universal; the commands differ per OS.

## The universal checklist

1. **Pin CPU frequency** — disable scaling/boost variability so clock is
   constant across runs.
2. **Control hugepages** — explicit hugepages for the workload's large
   allocations; disable *transparent* hugepages (their background compaction
   adds latency spikes).
3. **Make NUMA placement deterministic** — disable automatic NUMA balancing and
   pin memory+CPU, or deliberately interleave, so placement does not vary
   run-to-run.
4. **Affinity** — pin the workload threads (and, where it matters, device
   interrupts) to specific cores so the scheduler does not reshuffle under you.
5. **Pick and mount the filesystem deliberately** — the FS and its mount
   options materially change IO results; choose one and record it.
6. **Kill background jitter** — stop auto-update, package indexing, search
   indexing, telemetry, cron/scheduled maintenance for the duration.
7. **Verify quiescence** — confirm load is near zero and topology is what you
   expect before the first measured run.

## Linux

```bash
# 1. Governor: performance, no scaling. (cpupower, or sysfs directly.)
sudo cpupower frequency-set -g performance 2>/dev/null || \
  for c in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance | sudo tee "$c"; done
# disable turbo for a flat clock (intel_pstate):
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || true

# 2. Transparent hugepages OFF; pre-allocate explicit hugepages as needed.
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
sudo sysctl -w vm.nr_hugepages=<N>              # size to the workload

# 3. NUMA: stop automatic balancing; inspect topology.
sudo sysctl -w kernel.numa_balancing=0
numactl -H ; lscpu
# run pinned, e.g.:  numactl --cpunodebind=0 --membind=0 ./workload

# 4. (optional) IRQ affinity, isolcpus/nohz_full on the kernel cmdline for
#    tail-latency work; disable the watchdog (kernel.nmi_watchdog=0).

# 6. Quiesce background work for the duration (revert after!):
sudo systemctl stop apt-daily.timer apt-daily-upgrade.timer unattended-upgrades 2>/dev/null || true
sudo systemctl stop plocate-updatedb.timer man-db.timer 2>/dev/null || true
# any project auto-update/maintenance timers too.
```

Filesystem (Linux): `xfs` and `ext4` are the predictable defaults for database
/ IO benchmarks; `btrfs`/`zfs` add CoW/compression that you must account for
(disable compression + atime, know that CoW changes write patterns). Mount with
`noatime`; for a pure throughput test on disposable data people sometimes add
`nobarrier`/`nodelalloc` — only with eyes open, it trades durability for
numbers. Record FS + mount options.

## FreeBSD / OpenBSD / NetBSD

```sh
# CPU: disable frequency scaling (powerd) so clock is pinned.
sudo service powerd stop            # FreeBSD; leave cx_lowest at C1
sudo sysctl dev.cpu.0.freq=<max>    # or set hw.acpi/est to the top P-state
# NUMA (FreeBSD): inspect + pin.
cpuset -g                           # topology
cpuset -l 0-7 -n domain:0 ./workload   # pin cpus + NUMA domain
# Quiesce: stop periodic(8) jobs for the duration (daily/weekly/security).
```

Filesystem (BSD): **ZFS** is the common choice — for benchmarking set a matched
`recordsize` to the workload's IO size, `atime=off`, and decide on
`compression` deliberately (off for a raw-IO measurement; record it either
way). UFS is the lower-overhead alternative when you want to measure the
device, not the FS. Note ZFS's ARC will cache aggressively — size the dataset
past ARC or cap `vfs.zfs.arc_max` to measure the IO path.

## illumos (OmniOS / SmartOS / OpenIndiana)

```sh
# CPU: disable power management so frequency is stable.
# /etc/power.conf -> cpupm disable ; then: pmconfig
# Affinity / NUMA: bind with processor sets + lgroup awareness.
psrset -c 0 1 2 3            # create a processor set of specific CPUs
psrset -e <setid> <cmd>      # run bound to it
lgrpinfo                     # inspect NUMA (locality groups)
# Observe with the DTrace/kstat toolbox rather than perf.
```

Filesystem (illumos): **ZFS** is native and the default; same discipline as BSD
ZFS — matched `recordsize`, `atime=off`, deliberate `compression`, and account
for the ARC (cap it or exceed it). This is the platform ZFS was built for;
tune `zfs_arc_max` via `/etc/system` and reboot for a clean cap.

## Windows

```powershell
# 1. Power plan: High performance (or Ultimate), no throttling.
powercfg /setactive SCHEME_MIN      # High performance
powercfg /change monitor-timeout-ac 0

# 3-4. Affinity: pin the process to specific cores.
Start-Process .\workload.exe -ProcessorAffinity 0xFF   # cores 0-7 bitmask
# or: an existing process -> (Get-Process workload).ProcessorAffinity = 0xFF

# 6. Quiesce: pause Windows Update, Search indexing, Defender real-time for
#    the duration (and RE-ENABLE after).
Stop-Service wuauserv, WSearch -Force
Set-MpPreference -DisableRealtimeMonitoring $true     # revert afterwards
```

Filesystem (Windows): **NTFS** is standard; **ReFS** for very large volumes
(integrity-stream/CoW changes write behaviour — account for it). Disable
8.3-name creation and last-access updates for IO tests
(`fsutil behavior set disable8dot3 1`, `... disablelastaccess 1`), and know
whether BitLocker is in the path (it adds crypto overhead to every IO).

## Verify before you measure

```text
load is ~0 before each run (uptime / top / Task Manager)
topology matches expectation (numactl -H / cpuset -g / lgrpinfo / Get-ComputerInfo)
governor/power plan is the performance one
THP/transparent hugepages are off; explicit hugepages are allocated
the filesystem and mount options are what you intend, and recorded
no auto-update / indexing / telemetry / cron will fire during the window
```

## Afterwards

Revert everything you changed (re-enable updates, Defender, indexing, restore
the default governor/power plan). Record the exact tuning applied in the
results so the run is reproducible — an unrecorded tweak is an unreproducible
result. Hand the tuned, quiesced host to the `benchmark` skill.
