# PostgreSQL Agent Skills

Pre-built skills and knowledge for AI coding agents working on PostgreSQL —
PostgreSQL first, the tools you use to build Postgres code second, and generic
agent habits third.

Written once for every agent (the [Agent Skills Open
Standard](https://agentskills.io/): `<collection>/<skill>/SKILL.md` with YAML
front matter). **No per-agent branches** — one repository, one `main`.

License: CC0-1.0 (public domain dedication). See [`LICENSE`](LICENSE). Use it,
modify it, ship it, no attribution required.

- **Source of truth:** Codeberg — <https://codeberg.org/ddx/skills>
- **Mirror + browsable catalogue:** GitHub —
  <https://github.com/gburd/postgres-agent-skills> (GitHub Pages catalogue
  generated from `main`)

Start at [`AGENTS.md`](AGENTS.md): the single root map, the universal rules, and
the security model. Tool stubs like [`CLAUDE.md`](CLAUDE.md) just contain
`@AGENTS.md`.

## Install

Clone the one repository into your agent's skills directory:

```bash
git clone https://github.com/gburd/postgres-agent-skills.git ~/.claude/skills/postgres   # Claude Code
git clone https://github.com/gburd/postgres-agent-skills.git ~/.kiro/skills/postgres     # Kiro / Pi (reads ~/.kiro/skills)
git clone https://github.com/gburd/postgres-agent-skills.git ~/agent-skills/postgres     # any MCP-aware agent
```

Then point the agent at the repo-root `AGENTS.md` (most read it automatically).

## The three collections

### 1. [`postgres/`](postgres/README.md) — Postgres skills, by role

Load the persona that matches how you interact with the database:

| Persona | You are… |
|---------|----------|
| [`postgres/user`](postgres/user/SKILL.md) | someone who runs queries |
| [`postgres/dba`](postgres/dba/SKILL.md) | the database owner (schema, migrations, backup, permissions, health) |
| [`postgres/overseer`](postgres/overseer/SKILL.md) | the reviewer/architect (design, PL/pgSQL, partitioning, indexes, extensions, server + OS config) |
| [`postgres/replication`](postgres/replication/SKILL.md) | the replication specialist (physical/logical, slots, failover, upgrades) |
| [`postgres/triage`](postgres/triage/SKILL.md) | first responder (down/stuck/slow, mysterious log errors, corruption, wraparound, OOM) |
| [`postgres/developer`](postgres/developer/SKILL.md) | a core/extension developer (C patches, patch-series discipline, internals, submission) |

[`postgres/best-practices`](postgres/best-practices/SKILL.md) is the shared
41-rule library (query, connection, security, schema, locking, data-access,
monitoring, operations, advanced) the personas cite — each rule names an
antipattern, shows the fix in runnable SQL, and cross-references the canonical
PostgreSQL docs.

### 2. [`tooling/`](tooling/README.md) — develop Postgres code

`agora` (pgsql-hackers + git research via the agora MCP), `coccinelle`,
`flex-bison-to-lime`, `hegel`, `pg-numa-benchmark`, `review-diff`.

### 3. [`ai-life-skills/`](ai-life-skills/README.md) — generic agent habits

`persistent-memory` (tool-agnostic cross-session memory), `stop-slop`,
`subagent-teams`, `btw`, `checkpoint`, `dream`, `maintain-docs`, `think-hard`,
`watchdog`.

### Steering — the always-on rules

[`steering/`](steering/README.md) holds the baseline rules an agent reads at
the start of every session (as opposed to skills, which load on demand): the
universal set (`must-rules`, `coding-standards`, `workflow`, `voice`,
`prose-mechanics`, `opinions`, `tools`) plus a domain file
([`steering/postgresql.md`](steering/postgresql.md)) you load only in Postgres
projects. [`steering/README.md`](steering/README.md) explains how to wire these
into Claude Code / Kiro / Pi / any AGENTS.md agent, and **how to set up your
environment for the best agentic results** (persistent memory, the agora MCP, a
version-matched docs source, executable checks, scoped context).

Shared PostgreSQL community knowledge: [`community/`](community/) (conventions,
committer "voices", review standards), [`examples/`](examples/),
[`generic/`](generic/).

## Suggested external skills & MCPs (not bundled)

Worth adding to your setup, but kept out of this repo (different owners and
licenses): [ponytail](https://github.com/DietrichGebert/ponytail) (lazy-senior-dev
ruleset), [superpowers](https://github.com/obra/superpowers) (spec → plan → TDD →
subagent methodology), [agent-skill-manager](https://www.npmjs.com/package/agent-skill-manager)
(cross-agent skill management), and [memelord](https://github.com/earendil-works/memelord)
(persistent-memory MCP). Install the ones you want.

## MCP server endpoint (agora)

```
https://pg.ddx.io/mcp/
```

Streamable HTTP / SSE, no auth. Indexes the pgsql-hackers archive, 28 git repos
with code intelligence, commitfest, build-farm, and the wiki. Drives the
`agora` tooling skill. See [`generic/mcp-servers.json`](generic/mcp-servers.json)
for a manifest including other useful MCPs (memelord, github, filesystem,
context7, sequential-thinking).

## Contributing

A shared community resource. Issues and PRs welcome from anyone, on either
forge — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

CC0-1.0 (public domain dedication). See [`LICENSE`](LICENSE).
