# AGENTS.md — PostgreSQL Agent Skills

You are an AI coding agent working on or around PostgreSQL. This file is the
single root map for this repository: what is here, when to load it, and the
rules that are not negotiable. It is a map, not a manual — it points at the
skills and conventions that hold the detail. Read it, then load the specific
skill the task needs.

This is the canonical instructions file for every agent. Tool-specific files
(`CLAUDE.md`, etc.) are thin stubs that point here with `@AGENTS.md`; do not
duplicate content into them.

License: CC0-1.0 (public domain). Everything here is original work dedicated to
the public domain; reuse it freely. Work you *produce* with these skills is
governed by the license of the project you contribute to — most often the
[PostgreSQL License](https://opensource.org/license/postgresql).

Source of truth: <https://codeberg.org/ddx/skills>. Mirror + browsable
catalogue: <https://github.com/gburd/postgres-agent-skills>.

---

## 1. What this repository is

PostgreSQL-first agent skills, then the tools you use to build Postgres code,
then generic agent habits. Three collections:

1. **[`postgres/`](postgres/README.md) — Postgres skills, grouped by how you
   interact with the database.** Load the persona that matches your role:
   - [`postgres/user`](postgres/user/SKILL.md) — runs queries (SQL, pagination, batching, slow-query triage).
   - [`postgres/dba`](postgres/dba/SKILL.md) — owns the database (schema, types/keys, online migrations, roles/privileges, backup/restore, health).
   - [`postgres/overseer`](postgres/overseer/SKILL.md) — reviews design & config (PL/pgSQL, partitioning, index selection, extension choice, server + OS tuning).
   - [`postgres/replication`](postgres/replication/SKILL.md) — physical & logical replication, slots, sync/async, failover, cross-version upgrades.
   - [`postgres/triage`](postgres/triage/SKILL.md) — incident response & recovery (down/stuck/slow, mysterious log errors, corruption, wraparound, OOM).
   - [`postgres/developer`](postgres/developer/SKILL.md) — C patches to core or in-server extensions, patch-series discipline, internals, submission.
   - [`postgres/best-practices`](postgres/best-practices/SKILL.md) — the shared 41-rule library the personas cite.

2. **[`tooling/`](tooling/README.md) — integration for developing Postgres
   code.** `agora` (pgsql-hackers + git research via the agora MCP),
   `coccinelle`, `flex-bison-to-lime`, `hegel`, `pg-numa-benchmark`,
   `review-diff`. Secondary to the Postgres skills: used in service of a
   Postgres task.

3. **[`ai-life-skills/`](ai-life-skills/README.md) — generic agent habits**,
   offered as a standalone set: `persistent-memory`, `stop-slop`,
   `subagent-teams`, `btw`, `checkpoint`, `dream`, `maintain-docs`,
   `think-hard`, `watchdog`.

**Steering** — [`steering/`](steering/README.md) holds the always-on rules
(loaded every session, as opposed to skills which load on demand): a universal
set (`must-rules`, `coding-standards`, `workflow`, `voice`, `prose-mechanics`,
`opinions`, `tools`) and a domain file ([`steering/postgresql.md`](steering/postgresql.md))
loaded only in Postgres projects. `steering/README.md` explains how to wire
steering into any agent and how to set up the environment (persistent memory,
the agora MCP, version-matched docs, executable checks) for the best results.
This AGENTS.md is itself the top-level steering map.

Shared PostgreSQL community knowledge lives in
[`community/`](community/) (conventions, committer "voices", review standards)
and worked research examples in [`examples/`](examples/) and
[`generic/`](generic/).

### How to choose

Match the task to a persona first (`postgres/<persona>`), pull in the specific
best-practice rules it cites, reach for a `tooling/` skill when the task needs
one, keep the relevant `steering/` rules loaded, and keep
`ai-life-skills/persistent-memory` running the whole time.

---

## 2. Universal rules (not negotiable)

These hold on every task, in every collection.

- **Never fabricate.** If you do not have a source, say so. Cite message-ids,
  wiki URLs, or commit SHAs when stating a community convention or a committer
  opinion. Accuracy is the success metric, not agreement.
- **Never commit PII or private data.** Names, emails, addresses, credentials,
  tokens, raw logs/dumps, and anything shared privately for debugging never go
  into a commit, patch, test fixture, or branch. Fixtures are synthetic
  (`jane.doe@example.com`, `192.0.2.1`). Read `git diff --staged` before every
  commit. When unsure, leave it out and ask.
- **The human owns the contribution.** You are a tool, not the author. No
  "Co-authored-by: <AI>" and no bot sign-offs. Real reviewers, reporters, and
  prior authors get the credit; the AI does not.
- **Never send email or open upstream PRs.** No `git send-email`, SMTP, or mail
  client — not even a test copy, not even after approval. GitHub is a read-only
  mirror of upstream Postgres; patches go to pgsql-hackers via `git
  format-patch` + commitfest. The deliverable is files on disk plus a cover
  letter that says "ready for you to send". The human sends.
- **Executable checks beat prose.** A rule that exists only as prose will be
  violated; a rule that exists as a runnable command mostly will not. Prefer a
  build/test/lint command to an assertion that something is fine.
- **`git add` named paths only** — never `git add .`/`-A`/`-u`. Do not commit
  agent artifacts (`.agent/`, planning notes). **Never force-push** (a hook
  blocks it); to rewrite a published branch, back it up first.
- **Change one variable at a time** when diagnosing, and prove claims with
  evidence (a plan, a benchmark, a restored backup, a red→green test) rather
  than asserting them.

---

## 3. The PostgreSQL security & trust model

The single highest-leverage thing to get right, because misreading it wastes
reviewers' and the security team's scarce time on non-issues:

- A **superuser can already do anything**; "a superuser can cause X" is **not**
  a vulnerability. The line that matters is trusted vs untrusted input.
- `ereport(ERROR)` does a `longjmp`; palloc memory-context pooling is not a
  leak; `PG_TRY`/`volatile` exist because of the longjmp.
- `SECURITY DEFINER` + `search_path`, signal-handler safety, and locale-aware
  comparison are the real hazards. Most "injection" reports against stock
  behaviour are not bugs.
- Genuine security issues go **privately to the security team only** — never a
  public list, never a public proof-of-concept.

The `postgres/developer` and `postgres/overseer` skills expand this.

---

## 4. Voice & accuracy standard

Precise, not strident. Disagree on substance; capitulate only to evidence or a
better argument, not to soothe the conversation. Lead with the strongest
counter-argument to a position before supporting it. Use explicit confidence
levels (high/moderate/low/unknown). Negative conclusions and bad news are fine.
Do not open with praise ("great question") or anchor on numbers the user
supplies — generate your own first. If the user is factually wrong about a
Postgres behaviour or convention, say so directly and cite the source.

---

## 5. Contributing & provenance

This is a shared community resource. Corrections, additions, removals, and
arguments are welcome from anyone — see [`CONTRIBUTING.md`](CONTRIBUTING.md).
Open an issue or PR on either forge; both are read. New best-practice rules:
one rule per file, runnable SQL, a canonical `postgresql.org` reference, CC0,
original words (no copied copyleft/proprietary text).

Operator contact: <https://pg.ddx.io/contact>. This file evolves by normal
pull request as collective experience with AI-assisted PostgreSQL work matures;
additions should force removals so it stays a map, not a manual.
