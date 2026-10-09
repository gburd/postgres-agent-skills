# Tooling skills

Integration with the tools you use **while developing code for PostgreSQL**.
These are secondary to the `postgres/` persona skills: reach for them in
service of a Postgres task, not for their own sake.

| Skill | Use for |
|-------|---------|
| [`postgresq/`](postgresq/SKILL.md) | research the PostgreSQL community via the agora MCP server — pgsql-hackers archive, git history, code intelligence, commit↔thread correlation |
| [`coccinelle/`](coccinelle/SKILL.md) | AST-level C semantic patches: refactoring, finding API-usage/null-deref/leak patterns across the backend or an extension |
| [`flex-bison-to-lime/`](flex-bison-to-lime/SKILL.md) | porting flex+bison parser/scanner pairs to the Lime parser generator |
| [`hegel/`](hegel/SKILL.md) | property-based tests (round-trips, invariants, contracts) across Rust/C/C++/Go/TypeScript |
| [`pg-numa-benchmark/`](pg-numa-benchmark/SKILL.md) | A/B PostgreSQL benchmarks on bare-metal NUMA hardware (pgbench, HammerDB), stock vs patched |
| [`review-diff/`](review-diff/SKILL.md) | review a git diff for regressions, style, complexity, and security — one agent reviewing another's change |

The `postgresq` research skill is the rule of first resort for the
`postgres/developer` persona: ask the archive before grepping or guessing.

CC0-1.0 (public domain). See the repo root `LICENSE`.
