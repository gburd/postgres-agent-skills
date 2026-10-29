---
name: review-as-author
description: >
  Predict how a named pgsql-hackers reviewer (a PostgreSQL committer such as
  Tom Lane or Andres Freund, or any contributor) would review a patch, commit
  or design, with every point grounded in that person's own quoted messages or
  commits, through the pg.ddx.io MCP tools. Use to anticipate a committer's
  objections before posting a patch, for an author's-perspective pre-review,
  or when asked to review something "as X would". Evidence first: a point with
  no quote or commit of theirs is not attributed to them.
license: MIT
metadata:
  author: ddx
  version: "2"
---

# Review as an author

Predict how a named pgsql-hackers reviewer would review a PostgreSQL patch,
commit or design, from what they have written on the list and committed. The
result is a **prediction attributed to the reviewer, not their words or
opinion**. Every point under their name rests on their own quoted messages or
their commits, and names the part of the change it applies to.

Server: `https://pg.ddx.io/mcp/` (see [`../pg-ddx-research/SKILL.md`](../pg-ddx-research/SKILL.md)
for setup). The eval for this skill is agora_ex `scripts/review-eval/`: 14 real
patches with what the reviewer actually said.

## Inputs

- **Reviewer:** a person's name. Ask for one if none was given.
- **Subject**, one of: a diff (pasted, a file, or `git diff`); a pgsql-hackers
  Message-ID or thread whose message carries the patch; a commit SHA or
  revision; a design in prose.
- **As-of date** (optional): predict what they would have said then, from what
  they had written by then. See [As-of reviews](#as-of-reviews).

## Ground rules

1. **Predict their review, not yours.** A point goes under the reviewer's name
   only with their evidence: a message they wrote (Message-ID, date, verbatim
   quote) or a commit they wrote or committed (SHA, subject).
2. **Tie every point to the change:** a file and function, a hunk, a line
   range, or the part of the design. Drop evidence that doesn't apply.
3. **Quote verbatim from their own text.** Copy character for character from a
   tool result, from what the reviewer wrote, not from text they quoted from
   someone else. Never invent a quote or paraphrase inside quotation marks.
   Verify every quote (step 5).
4. **Recent beats old.** People change their minds. When an older stance
   conflicts with a newer one, use the newer one and say so.
5. **Say what the record doesn't show.** A thin record (a few dozen messages,
   nothing on the topic) makes a weak prediction: say so instead of filling the
   gaps.
6. **Points without their evidence go under "General reviewer notes"**, not
   under their name. The checklist below and the voice files
   (`community/voices/*.md`) are context for choosing what to search for; they
   are never evidence.
7. **Third person.** "Tom Lane would likely object that ...". Never write as
   them.

## Their tools and ours

The skill is adapted from pghacker-mcp's `review-as-author` (sources below).
Where it calls a tool, use this server's:

| pghacker-mcp | pg.ddx.io |
| --- | --- |
| `search_authors`, `get_author` | `get_contributor(name:)` (profile, per-release roles, latest credited commits); `whats_new(who:, since:, until:)` for activity in a window |
| `author_perspective(author, topic, paths, until)` | `hybrid_search(query: <topic>, author: <name>, until: <as-of>)` and `retrieve_context(question:, author:, until:)`; positions on features: `cross_reference(ref: "feature:<words>")` |
| `search_threads(query, author)` | `hybrid_search(query:, author:, until:)`, `search(query: "f:<name> ...")` |
| `get_thread` | `get_thread(message_id:)` (own words by default; `include_bodies: false` for an outline) |
| `search_extracts` | `retrieve_context(question:)` |
| `search_commits(author, paths)` | `search_commits(author: <regex>, paths: [...], until:)` (author matches Author/Reviewed-by trailers too) |
| `get_commit` | `get_commit(commit:, diff: false)` (trailers, Discussion threads, back-patches) |
| `blame` | `blame(path:, start_line:, end_line:, version:)` |
| `search_patches` | `search_patches(query:)`; a thread's patch files: `get_message` / `get_attachment` |
| `search`, `grep`, `read_file` | `code_search(query:, version:)`, `read_file(path:, version:)` |
| `query` (SQL quote check) | `get_message(message_id:, quotes: [...], include_body: false)` (`own_words` per quote) |

## Procedure

Make independent calls in parallel. A review typically takes 15 to 25 calls.

### 1. The reviewer

- `get_contributor(name: <name>)`: their canonical name, roles per release
  (authored, reviewed, committed), latest credited commits. If several people
  match, ask which one.
- Note how much evidence there is and when they last posted
  (`whats_new(who: <name>, since: <as-of minus a year>, until: <as-of>T00:00)`).

### 2. The change

- **A diff:** list the files, the functions in the hunk headers, and what
  changes for users and for code: SQL syntax, catalogs, on-disk or WAL format,
  GUCs, structs and signatures in `src/include`, locking, hot paths.
- **A Message-ID:** `get_thread(message_id:, include_bodies: false)` for the
  subject, participants and attachments; read the patch with
  `get_attachment(message_id:, index:)`.
- **A commit:** `get_commit(commit: <sha>)`.
- **A design:** find the code it would touch with `code_search`, and prior
  discussion with `retrieve_context(question: <the design in a sentence>, until:)`.
- Write **one sentence** that says what the change does. It is the topic for
  the steps below.

### 3. Their history with this code

Skip what doesn't apply: a contributor may have no commits.

- `search_commits(author: <surname>, paths: [<changed files>], until: <as-of>, limit: 20)`:
  what they wrote, committed or reviewed in these files. Read the one to three
  most relevant with `get_commit(commit:, diff: false)` for their rationale.
- `blame(path:, start_line:, end_line:, version: "master@<the day before>")` on the lines
  the change rewrites. If the reviewer wrote them, their commit message is the
  design they would defend.

### 4. Their stated views

- `hybrid_search(query: <the one-sentence summary>, author: <name>, until: <as-of>)`:
  their messages on this topic.
- The kind of change, stated generically ("showing computed values in a
  monitoring view", "adding a field to a planner struct", "restricting what an
  admin tool may do"): the same search. How they judged similar proposals
  predicts their verdict better than anything else.
- For each checklist dimension the change touches, at most four, a search on
  that dimension's topic with `author:` and `until:`.
- Read the best one or two threads in context with `get_thread`, and only the
  reviewer's messages in them.

### 5. The review

- **Lead with their likely verdict on the premise and the approach**, before
  any detail: is the problem real and common enough to fix, and is what the
  change costs (complexity, struct size, work on hot paths, new user-visible
  semantics, a restriction on what experts can do, one more way to do
  something) worth it? A committer's first reply most often argues exactly
  this. When the record shows them rejecting similar changes, predict that,
  not a friendly list of details.
- Then the other points with the strongest evidence: stated objections first,
  then recurring themes, then the questions they habitually ask. Usually three
  to six points in all.
- For each point: what they would raise, where in the change, and the basis (a
  quote with its Message-ID and date, or a commit).
- **Quote short and exact:** one sentence or clause (under about 200
  characters) copied from one place in their message. No ellipses, no joining
  two passages, no tidying.
- **Cite at least two different messages of theirs.** One message is an
  anecdote; two show a position.
- **Check every citation** before answering, one call per message:

  ```
  get_message(message_id: "<id>", include_body: false,
              quotes: ["<quote 1>", "<quote 2>"])
  ```

  Keep a citation only when all three hold: the quote comes back
  `own_words: true` (not text they quoted from someone else), `from` is the
  reviewer, and `date` is before the as-of date. Drop or replace any other.

## Checklist: what PostgreSQL reviewers look for

Use it to choose what to search for. It is not the reviewer's opinion.

| Dimension | Signals in the change | Topic to search |
| --- | --- | --- |
| Catalogs | `src/include/catalog/*`, new catalog columns or objects | catalog changes and catversion bumps |
| pg_dump and pg_upgrade | new object kinds or DDL, catalog changes, `src/bin/pg_dump`, `src/bin/pg_upgrade` | pg_dump and pg_upgrade support |
| WAL and crash safety | `XLogInsert`, redo routines, page layout, fsync, `smgr` | WAL logging and crash safety |
| Replication | `src/backend/replication`, logical decoding, publications, standbys | replication and logical decoding |
| ABI and back-patching | structs or signatures in `src/include`, a fix meant for stable branches | ABI compatibility when back-patching |
| Locking and concurrency | lock levels, LWLocks, spinlocks, atomics, shared memory | lock levels and concurrency |
| Memory and errors | memory contexts, `palloc` in loops, `ereport` levels and wording | memory contexts and error reporting |
| Security | permission checks, `SECURITY DEFINER`, `search_path`, untrusted input | security and permission checks |
| Performance | executor, planner, buffer or per-tuple code; new work on hot paths | performance regressions and benchmarks |
| Portability | compiler or platform specifics, Windows, 32-bit, new dependencies, `meson.build` | portability and build dependencies |
| Compatibility | new syntax or keywords, changed behavior, deprecations | SQL standard conformance and backward compatibility |
| Configuration | new GUCs or reloptions, defaults | adding new GUCs |
| Tests and docs | missing regression or TAP tests, docs, comments | regression tests and documentation |

## As-of reviews

To predict what they would have said on a date (for example to compare with
what they did say). **The reviewer's actual reply to the patch is the answer
key, not evidence:** an as-of review that cites it, or anything else dated on
or after the as-of date, is void, however relevant it looks.

- pass `until: <as-of date>` to `hybrid_search`, `search` and
  `retrieve_context` (exclusive: only what came before it), and
  `until: <as-of date>T00:00` to `whats_new`;
- pass `until: <as-of date>` to `search_commits` (exclusive too: committed
  before);
- read code as it was with `version: "master@<the day before>"`, or the branch
  the patch targeted;
- don't open or cite anything dated on or after the as-of date. On the patch's
  own thread, read only the messages before the patch; the replies to it are
  what you are predicting. `get_thread` shows them all: skip them unread.

## Output

```markdown
> Simulated review: what <Name> would likely say about <subject>, predicted from
> <Name>'s public pgsql-hackers messages and commits. These aren't <Name>'s
> words or opinion.

**Likely verdict:** <one sentence: on the premise and the approach>

**What <Name> would likely raise**

1. **<The point>**: <where in the change>.
   Basis: on <YYYY-MM-DD>, <Name> wrote "<verbatim quote>" (<Message-ID>, thread "<subject>").
2. ...

**Questions <Name> would likely ask:** <each with its basis>

**What <Name> would likely accept:** <each with its basis>

**General reviewer notes** (not attributed to <Name>): <checklist points
without their evidence>

**Evidence:** <n> messages and <k> commits considered, from <year> to <year>.
<What the record doesn't cover.>
```

For a machine-checked run (the eval) end with a JSON block:
`{"answer": "<the review in two sentences>", "citations": [{"message_id": "...", "quote": "..."}]}`.

## Sources

- Adapted from pghacker-mcp's `skills/review-as-author/SKILL.md` (Copyright (c)
  Microsoft Corporation, MIT License; https://github.com/Azure-Samples/pghacker-mcp):
  the ground rules, procedure shape, 13-dimension checklist, as-of rules and
  output template. Rewritten for the pg.ddx.io tools. Because it carries their
  text, this skill is MIT (see [`LICENSE`](LICENSE) beside it), not CC0 like the
  rest of this repository.
- Its eval (`eval/reviews.json`, MIT) is ported to agora_ex `scripts/review-eval/`.
- `community/voices/*.md` and `community/review-standards.md`: background for
  choosing search topics, not evidence.
