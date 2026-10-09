---
name: pg-numa-benchmark
description: Run PostgreSQL clock sweep benchmarks on bare-metal EC2 instances. Covers AWS setup, instance launch (r8i.metal-96xl / m6i.metal), OS tuning, PG build (stock + patched), pgbench A/B testing, HammerDB TPC-C, and result collection. Use when benchmarking PostgreSQL buffer manager changes on NUMA hardware.
---

## Overview

A/B benchmark comparing stock vs patched PostgreSQL on bare-metal NUMA instances. Tests clock sweep contention under memory pressure (shared_buffers < dataset).

## Quick Reference

| Instance | vCPUs | NUMA Nodes | RAM | Cost/hr | Use |
|----------|-------|------------|-----|---------|-----|
| r8i.metal-96xl | 384 | 6 (SNC3) | 3TB | $14.45 | Primary benchmark |
| m6i.metal | 128 | 2 | 512GB | $4.61 | Quick/cheap testing |

## Workflow

1. **Launch:** `aws ec2 run-instances --instance-type r8i.metal-96xl` in us-east-2 with 2TB gp3 EBS
2. **Bootstrap:** Install build deps, tune kernel (hugepages, disable NUMA balancing, performance governor)
3. **Build:** Stock PG to `/postgres/pg_stock`, apply patches, build to `/postgres/pg_patch`
4. **Load:** `pgbench -i -s 3000` (~45GB dataset, exceeds 32GB shared_buffers)
5. **Benchmark:** A/B alternating stock/patched at each client count, 3 iterations, report medians
6. **Collect:** `scp` results CSV + system info
7. **Terminate:** Don't forget — $14.45/hr!

## Critical Details

- **Always start PG with** `numactl --cpunodebind=0` — pins postmaster to node 0 for deterministic NUMA placement. Without this, stock TPS varies 31K-40K (29% variance).
- **Build with** `--with-libnuma` — without it, patch batch_size=1 (no improvement).
- **shared_buffers = 32GB** — must be smaller than dataset to force clock sweep eviction.
- **huge_pages = on** with `vm.nr_hugepages = 17408` — eliminates TLB misses.
- **Use separate data dirs** for stock/patched to avoid cross-contamination.

## Expected Results (r8i.metal-96xl)

pgbench RO: **+16-20%** improvement (clock sweep is the bottleneck)
pgbench RW: **~0%** (WAL/checkpoint bottlenecked, not sweep)
HammerDB TPC-C: **no regression** (write-heavy, sweep not dominant)

## Full Guide

See `references/GREG_BENCHMARK_GUIDE.md` for the complete step-by-step procedure including all scripts, postgresql.conf settings, HammerDB setup, and troubleshooting.
