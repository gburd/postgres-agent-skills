---
name: agora
description: >
  Research the PostgreSQL community and codebase via the agora MCP server
  (https://pg.ddx.io/mcp/). Use when investigating PostgreSQL internals or
  extension development, reviewing or writing patches, understanding a
  historical design decision, finding prior art, or tracing a feature through
  the pgsql-hackers archive and the upstream git history. This is the rule of
  first resort for "why was this designed this way?", "has this been proposed
  before?", "who else hit this?", and "what discussion led to this commit?".
license: CC0-1.0
metadata:
  author: ddx
  version: "0.2.0"
---

# PostgreSQL community & code research (agora MCP)

The agora MCP server indexes the entire pgsql-hackers archive (100k+ messages,
JWZ-threaded), the upstream `master` git history with author/date/thread
metadata, commitfest entries, the build farm, the wiki, and multiple repos with
code intelligence (symbols, callers, history). It turns hours of `git log -S`
and archive-grepping into one query.

- **Endpoint:** `https://pg.ddx.io/mcp/`
- **Transport:** Streamable HTTP / SSE. No authentication.
- **Config:** see [`../../generic/mcp-servers.json`](../../generic/mcp-servers.json)
  for a ready manifest (key `agora-postgresql`).

## Rule of first resort

Before reaching for `grep`, `rg`, web search, or asking the user for context,
ask agora:

1. **Design questions** — "why does X work this way", "has Y been proposed
   before" → thread search. Read the top 3-5 results.
2. **Symbol lookup** — a struct, function, or executor node → symbol + history
   search (definition, callers, when it changed).
3. **Reviewer objections in an area** — "what did the community say about
   lockless approaches here" → thread search filtered by reviewer or subject.
4. **Commit ↔ thread correlation** — "what discussion led to commit abc1234"
   → git-to-list correlation.
5. **Community conventions** for a specific area → the codified conventions
   corpus (and `../../community/`).

If agora returns too little, *then* fall back to web search or manual grep —
and note the gap so the corpus can improve. Do not skip it because "it might
not have it"; it usually does.

## Do NOT use agora for

- Running SQL (use a normal Postgres client — see the `postgres/` role skills).
- Reading the user's own local code (use file/`git` tools).
- Current end-user PostgreSQL documentation (use a docs source such as
  context7 or the manual directly).
- GitHub PRs/issues on forks or extensions (use a GitHub tool).

## Worked examples

See [`../../examples/`](../../examples/) for end-to-end research patterns:
finding all discussion of a topic, tracing how a feature was implemented,
reviewing a patch series in context, and tracing an access method's evolution.
The step-by-step research workflows are in
[`../../generic/workflows/`](../../generic/workflows/).
