# Steering

Steering files are the always-on rules an agent reads at the start of every
session, as opposed to skills, which load on demand for a specific task. This
collection is the baseline the author uses; it is CC0, so fork it and make it
yours.

## What is here

Universal (load for any project):

| File | What it governs |
|------|-----------------|
| [`must-rules.md`](must-rules.md) | the non-negotiables: never send mail or post as the human, never use an ungranted credential, never commit secrets/PII, stage explicitly, git safety |
| [`coding-standards.md`](coding-standards.md) | how to write code: no speculative features, no premature abstraction, the PII rule, hard limits, zero-warnings, comments |
| [`workflow.md`](workflow.md) | the order of operations: pre-commit checks, commit/PR rules, git safety, progress heartbeat, where planning artifacts go |
| [`voice.md`](voice.md) | how the agent reasons and talks: calibrated, evidence-bound, lead with the finding, disagree on evidence |
| [`prose-mechanics.md`](prose-mechanics.md) | mechanical prose rules for anything under the human's name: punctuation, naming, commit-message shape |
| [`opinions.md`](opinions.md) | taste (fork this first): no em dashes, plain register, no filler validation |
| [`tools.md`](tools.md) | preferred CLI tools and per-language defaults; MCP routing |

Domain (load only in a project of that kind):

| File | Load when |
|------|-----------|
| [`postgresql.md`](postgresql.md) | the project works on PostgreSQL (patches, internals, performance, extensions). The richest file here; it extends the universal set and wins where it differs. |

## Why steering and skills are separate

Steering is small and always loaded, so it must stay a tight set of rules that
apply everywhere; every line costs context on every task. Skills are larger and
load only when their trigger matches, so detail lives there. Keep domain
knowledge (how PostgreSQL review works) in a domain steering file that is
opt-in per project, not in the global set, so an unrelated repo does not pay for
Postgres context it never uses.

## How to integrate this when you work on PostgreSQL

The goal: your agent reads the universal rules in every project, and the
PostgreSQL rules only in your Postgres projects.

### 1. Clone the repo

```bash
git clone https://github.com/gburd/postgres-agent-skills.git ~/agent/postgres-skills
```

### 2. Wire the universal steering globally

Point your agent's global instructions at the universal files so they load
everywhere. The exact location is agent-specific:

- **Claude Code** reads `~/.claude/CLAUDE.md`. Make it a small index that
  imports the universal files:

  ```markdown
  # Steering
  @~/agent/postgres-skills/steering/must-rules.md
  @~/agent/postgres-skills/steering/coding-standards.md
  @~/agent/postgres-skills/steering/workflow.md
  @~/agent/postgres-skills/steering/voice.md
  @~/agent/postgres-skills/steering/prose-mechanics.md
  @~/agent/postgres-skills/steering/opinions.md
  @~/agent/postgres-skills/steering/tools.md
  ```

  Keep the top-level file tiny (an index of imports); some agents warn on a
  large top-level instructions file, and imports are resolved recursively.

- **Kiro** reads `~/.kiro/steering/*.md`: symlink or copy the universal files
  in there.
- **Agents that read a project `AGENTS.md`** (and many do): reference the files
  from your project `AGENTS.md`, or inline them if your agent does not resolve
  imports.

### 3. Add the PostgreSQL steering per Postgres project

Do not load `postgresql.md` globally; it is long and irrelevant to non-Postgres
work. Instead, in each Postgres project, add one line to the project's
`AGENTS.md` (or the agent's project-local instructions):

```markdown
See ~/agent/postgres-skills/steering/postgresql.md for PostgreSQL steering.
```

or, for an agent that resolves imports, `@~/agent/postgres-skills/steering/postgresql.md`.
A tiny `.envrc`/direnv helper that appends that line when you enter a Postgres
checkout automates this; keep the generated file gitignored so it never leaks
into a patch.

### 4. Add the skills

Point your agent's skills directory at the repo so the `postgres/`, `tooling/`,
and `ai-life-skills/` collections are discoverable:

```bash
ln -s ~/agent/postgres-skills ~/.claude/skills/postgres    # Claude Code
ln -s ~/agent/postgres-skills ~/.kiro/skills/postgres      # Kiro / Pi
```

## Setting up your environment for the best agentic results

Steering and skills are necessary but not sufficient. The setup that most
improves agent quality on PostgreSQL work:

- **Persistent memory.** Configure a cross-session memory store so lessons,
  corrections, and project facts survive between sessions; the agent should
  recall at task start and record at task end. See the
  `ai-life-skills/persistent-memory` skill. This is the single highest-leverage
  addition: it is how the agent stops making the same mistake twice.
- **The pg.ddx.io research MCP server.** Configure `https://pg.ddx.io/mcp/` (see
  `tooling/pg-ddx-research` and `generic/mcp-servers.json`). It replaces hours of
  archive-grepping with one query and is the rule of first resort for "why",
  "who else hit this", and "what thread led to this commit".
- **A docs source for the version you run.** Point a docs tool at the manual
  for *your* major version so the agent quotes real, current API, not whatever
  it half-remembers.
- **Executable checks over prose rules.** A rule that exists only as prose gets
  violated; a rule that exists as a command (a pre-commit hook, a `make check`
  target, a lint gate) mostly does not. Put the definition of done in runnable
  form (warning-free build, cassert test pass, pgindent, docs build) and run it
  before you believe a result.
- **A clean, reproducible build.** For core work, build with cassert and
  dependency tracking on; a build system that silently serves stale objects or
  a stale initdb template will make the agent confidently report a wrong
  answer. See `steering/postgresql.md`.
- **Scope context deliberately.** Global steering stays small; domain steering
  is opt-in; skills load on trigger. Do not dump everything into one giant
  always-on file: more irrelevant context measurably lowers agent success.
- **Suggested external skills (optional).** Beyond this repo, several
  third-party agent skill sets are worth adding; the repo root `README.md`
  lists them under "Suggested external skills & MCPs". They are not bundled
  here (different owners and licenses); add the ones you want.

CC0-1.0 (public domain). See the repo root `LICENSE`.
