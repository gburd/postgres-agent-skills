# Tooling skills

Integration with the tools you use **while developing and testing PostgreSQL
code**. These are secondary to the `postgres/` role skills: reach for them in
service of a Postgres task, not for their own sake.

| Skill | Use for |
|-------|---------|
| [`pg-ddx-research/`](pg-ddx-research/SKILL.md) | research the PostgreSQL community & codebase via the pg.ddx.io MCP server — pgsql-hackers archive, git history, code intelligence, commit↔thread correlation |
| [`benchmark/`](benchmark/SKILL.md) | run a reproducible benchmark correctly (A/B, warm-up, repetition, variance), locally or on a remote host over SSH |
| [`choose-instance/`](choose-instance/SKILL.md) | pick a cloud instance type (any provider) that faithfully represents what the benchmark stresses; when bare metal is required |
| [`tune-os-for-benchmark/`](tune-os-for-benchmark/SKILL.md) | make an OS measurement-grade before benchmarking (Linux/BSD/illumos/Windows): governor, hugepages, NUMA, filesystem, quiescing jitter |
| [`pg-numa-benchmark/`](pg-numa-benchmark/SKILL.md) | the PostgreSQL layer on the three skills above: buffer-manager clock-sweep A/B (pgbench, HammerDB), stock vs patched on NUMA hardware |
| [`coccinelle/`](coccinelle/SKILL.md) | AST-level C semantic patches: refactoring, finding API-usage/null-deref/leak patterns across the backend or an extension |
| [`flex-bison-to-lime/`](flex-bison-to-lime/SKILL.md) | porting flex+bison parser/scanner pairs to the Lime parser generator |
| [`hegel/`](hegel/SKILL.md) | property-based tests (round-trips, invariants, contracts) across Rust/C/C++/Go/TypeScript |
| [`review-diff/`](review-diff/SKILL.md) | review a git diff for regressions, style, complexity, and security — one agent reviewing another's change |

The `pg-ddx-research` skill is the rule of first resort for the
`postgres/developer` persona: ask the archive before grepping or guessing.

The three benchmarking skills compose: **choose-instance** → **tune-os-for-benchmark**
→ **benchmark**, with **pg-numa-benchmark** layering the PostgreSQL specifics on
top. Each is provider- and OS-agnostic on its own.

CC0-1.0 (public domain). See the repo root `LICENSE`.
