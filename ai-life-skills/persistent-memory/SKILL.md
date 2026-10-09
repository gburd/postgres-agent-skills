---
name: persistent-memory
description: >
  Choose and use a local persistent memory store so lessons, corrections, and
  project knowledge survive across sessions. Tool-agnostic: works with memelord,
  an MCP knowledge-graph memory server, a plain notes file, or any similar
  store. Use at the START of any non-trivial or long-running task to recall
  prior context, when you self-correct or the user corrects you, when you learn
  something durable about a codebase, and before finishing a task to record what
  was learned. Also use to initialise memory in a project that has none.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.2.0"
---

# Persistent memory

Carry knowledge across sessions instead of relearning it every time. This skill
is about the *discipline*; the specific store is pluggable.

## Pick a store (first available wins)

1. **A memory MCP server already configured** (e.g. memelord, or an MCP
   knowledge-graph `memory` server) — prefer it; it has structured
   recall/retrieval. Detect by listing MCP tools for names like
   `memory_start_task`, `memory_report`, `create_entities`, `add_observations`.
2. **A project-local store on disk** — a `.memelord/` directory, a
   knowledge-graph JSON, or a committed/ignored `NOTES.md`/`DECISIONS.md`.
   Detect by checking the project root.
3. **Nothing yet** — initialise one (below) rather than going without.

Treat the store as an interface with four operations; map them onto whatever
tool you found:

| Operation | memelord | MCP knowledge-graph | plain file |
|-----------|----------|---------------------|-----------|
| recall at task start | `memory_start_task` | `search_nodes` / `read_graph` | read the notes file |
| record a correction | `memory_report type=correction` | `add_observations` | append dated entry |
| record an insight | `memory_report type=insight` | `create_entities`/`add_observations` | append dated entry |
| close out | `memory_end_task` | (none; just write) | append summary |

## Initialise a store if the project has none

- **memelord present on PATH:** check for `.memelord/`; if absent run
  `memelord init`, then `memelord status`. Done.
- **An MCP memory server is configured but empty:** nothing to init; just start
  recording.
- **Neither:** create a plain `MEMORY.md` (or `.agent/memory.md`) at the project
  root with sections `## Decisions`, `## Gotchas`, `## Corrections`, and add it
  to `.gitignore` unless the user wants it committed. State which you chose.

## The discipline (do this every task)

1. **At task start**, recall: pull memories relevant to the request before doing
   any work. Past lessons prevent repeating past mistakes.
2. **On self-correction** (tried X, it failed, Y worked): record a *correction*
   with what failed and what worked.
3. **When the user corrects you or shares project knowledge**: record it. The
   user should never have to tell you the same thing twice.
4. **When you learn something durable about the codebase** (file locations,
   build/test conventions, architecture, a non-obvious gotcha): record an
   *insight* so the next session skips the re-exploration.
5. **Before finishing**, review what you recalled against what you found. If a
   stored memory is now wrong (stale path, wrong version, bad explanation),
   **correct or delete it** — a bad memory poisons every future session. Then
   write the net-new lessons.

## What belongs in memory vs not

- **In:** reusable lessons, failure modes and their fixes, project conventions,
  stable facts (ground-truth versions, host topology), decisions and their
  rationale.
- **Out:** secrets, PII, anything private shared for debugging, and transient
  state that will be false next week. If a "fact" has a short shelf life, note
  its date and source so a later session can tell it is stale.

## Keep it true

Memory is only an asset if it is trustworthy. Prefer deleting a doubtful entry
to carrying it. When you record a version or a count, note where it came from
and when, because the thing most likely to rot is a number.
