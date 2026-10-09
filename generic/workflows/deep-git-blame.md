# Workflow: Deep git-blame — the history behind a line, commit, email, or idea

Given a starting point — a line (or lines) of PostgreSQL source, a commit, a
mailing-list message, or just a concept — assemble everything the pg.ddx.io
MCP server knows about where it came from and why, and write it up as one
concise, cited paragraph of the kind you see in a `pgsql-hackers` reply ("That
goes back to commit abc1234 (committed 2019), which came out of the thread at
postgr.es/m/..., where the concern was ...").

This is deeper than `git blame`: plain blame tells you *which commit last
touched a line*; this follows that commit to its discussion thread, the thread
to its participants and its sibling messages, and the concept across the whole
archive — mail, git, and commitfest together.

## Inputs

One of:

- `line_range`: a file path plus line numbers, or a verbatim snippet of code.
- `commit_sha`: a SHA (full or 7-12 char prefix).
- `message_id`: a Message-ID or an archive URL.
- `concept`: a feature, GUC, error message, behaviour, or design term
  ("fast-path locks", "HOT updates", "why is `work_mem` per-node").

## Outputs

One concise cited paragraph (occasionally two, for a concept with a long arc)
in the hackers-reply style described below — origin, trace, current state —
with every claim attributable to a commit or thread actually read.

## Steps

### 1. Resolve the starting point to a commit (when possible)

- **Line / snippet** → find the commit that introduced or last changed it.
  Use `git_search` with a distinctive phrase from the line, or the function
  name, to locate the commit(s) that touched it. For a precise "who last
  changed this line", pair the file with `git_blame`. Prefer the commit that
  *introduced* the behaviour over the most recent cosmetic touch.
- **SHA** → you already have the commit; go to step 2.
- **Message-ID / URL** → `get_message(message_id: "<id>")` and
  `get_thread(message_id: "<id>")` to see the discussion; note any commit
  SHAs cited in the thread.
- **Concept** → start at `retrieve_context(question: "<concept>", token_budget:
  4000)` for cited passages, then `hybrid_search` and `git_search` to pin the
  defining commit(s) and thread(s).

### 2. Commit → discussion

For each commit of interest:

```
git_show_file(repo: "postgres", sha: "<sha>", path: "<file>")
git_log(repo: "postgres", path: "<file>", limit: 1)
```

Read the commit message. Its `Discussion:` trailer links the thread that
argued for it; its `Author:` / `Reviewed-by:` / `Reported-by:` trailers name
who did the work — see `community/conventions/commit-message-format.md` §
"Trailers" for the exact schema. The commit search result also carries
`mail_refs` (the mail that refers to the commit) and `people`
(author/committer + trailer-credited reviewers) — use them, do not re-derive
attribution by hand.

### 3. Discussion → context

```
get_thread(message_id: "<id>")
```

Who raised the problem, what alternatives were weighed, what was rejected and
why. The *rejected* approaches are often the most useful part of the history.
Follow references backward: a thread usually cites the earlier thread or
commit it builds on. Walk one or two hops until the origin stops moving.

### 4. Concept → breadth

For a concept (not a single line), widen: `hybrid_search` for the several
threads where it was designed, revised, and revisited across releases, and
`git_search` for the commits that implemented each step. The history of a
concept is a chain of commits-plus-threads, not one commit.

## Output: one cited paragraph, hackers-style

Write **one concise paragraph** (occasionally two for a concept with a long
arc). Lead with the origin, trace the change, end with the current state.
Cite inline the way hackers mail does:

- commits as a short SHA with the commit year: `commit a1b2c3d
  (committed 2022)` (name the author only if it is material and you are
  quoting the real commit's own trailer);
- threads as the archive URL: `https://postgr.es/m/<message-id>` (a bare
  Message-ID also resolves at `https://pg.ddx.io/id/<message-id>`);
- people by name as the archive records them (from the trailers / From lines),
  never invented.

Keep it factual and attributable: every claim about *why* something was done
should trace to a thread or commit message you actually read, not to a guess.
If the archive does not explain the "why", say so rather than inventing a
rationale.

### Example shape

> This check dates to commit `9f2c4e1` (committed 2017), added in response to
> the report at https://postgr.es/m/12345.1500000000@example.com, where
> `pg_dump` could emit an invalid dependency order for a materialized view that
> referenced a sequence. The original fix only covered sequences; it was
> extended to foreign tables in `3b1d2f0` (committed 2019) after the
> thread at https://postgr.es/m/abc...@example.com noted the same hazard there.
> The code has not changed since; a 2021 discussion
> (https://postgr.es/m/def...) considered generalising it to all relation
> kinds but concluded the explicit allow-list was safer.

## Pitfalls

- `git blame`'s "last touched" is not "introduced". A pgindent run or an
  unrelated refactor can be the last toucher of a line (see
  `community/conventions/pgindent.md` § "Release-cycle reformat" — those
  bulk-reformat commits are exactly this trap); follow the thread to find the
  commit that actually created the behaviour.
- A SHA prefix can collide; confirm the full SHA and subject before citing.
- Do not attribute a design opinion to a person unless the message you are
  citing actually says it. Quote the archive; do not paraphrase someone into a
  position.

## Sources

- `generic/workflows/research-and-connect-dots.md` — the broader
  concept-research flow this skill specialises for provenance.
- `community/conventions/commit-message-format.md` § "Trailers" — the
  attribution schema (`Author:`, `Reviewed-by:`, `Discussion:`, etc.) this
  skill reads off every commit.
- `community/decision-making.md`, `community/methodology.md` — how the
  archive records consensus and rationale, the model this skill assumes when
  tracing a design decision back to its thread.
