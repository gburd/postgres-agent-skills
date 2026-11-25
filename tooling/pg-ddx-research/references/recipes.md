# Composition recipes: asking bigger questions of pg.ddx.io

One MCP call answers one small question. The questions people actually ask
("what's the history of X?", "who should review this?") take several calls,
with the output of one feeding the next. These recipes are those call
sequences, one per question shape, written as short pseudo-code over the real
tool and argument names of the pg.ddx.io MCP server
(<https://pg.ddx.io/mcp-tools> lists every tool and argument). Each recipe was
run once against the production server on the example named in it.

How to read them:

- `x = tool(arg=...)` is one MCP `tools/call`; `x.field` is a field of its JSON
  answer. `for`, `if` and `stop` are your agent's own logic.
- **Cite** is what the answer must link. A claim without one of those links is
  your inference: say so.
- **Limits** are what the index does not hold, or where a result looks more
  certain than it is.
- **REST/GraphQL** gives the same sequence over plain HTTP where those
  surfaces have the endpoints. REST paths are under `https://pg.ddx.io`; the
  OpenAPI document is `/openapi.yaml`. Where a step exists only as an MCP tool,
  the recipe says so.

General rules for every recipe: search before you read (`retrieve_context` or
`hybrid_search` return excerpts, so you can judge a hit without opening it);
read threads as outlines first (`get_thread` with `include_body=false`); a
result with `complete: false` is partial; and the server is shared, so keep to
about one request per second.

## 1. "What's the history of ___?"

Inputs: a feature name (MERGE, BRIN, logical decoding).

```text
x = cross_reference(ref="feature:<name>", limit=5)    # timeline + design-history graph
h = history-of(query="<name>", limit=5)               # threads and people
c = search_commits(message="^<Commit subject words>", limit=20)
for each landmark commit k in x.timeline.events (commit, revert) and c.commits:
    k = commit_history(commit=k.sha)                  # Discussion thread, first_releases, reverted_by
    if k.reverted_by: note the revert and fetch it the same way
t = retrieve_context(query="why was <name> reverted", until="<year after the revert>",
                     token_budget=4000)
```

Stop when the timeline is continuous from the first proposal to the newest
release that ships it. Cite: commit SHAs with their `first_releases`, the
Discussion threads' urls, the passages' urls.

Limits: `search_commits.message` is a case-insensitive regex, so `MERGE` also
matches "mergejoin"; anchor it (`^Add support for MERGE`). The `cross_reference`
graph for a common word can attach to one commitfest entry rather than the
feature (for "MERGE command" it led with a 2026 bug-fix entry); trust its
`timeline` events, check its `graph` facts. `history-of`'s commits are the
newest that match the words, one row per branch copy: for MERGE all five were
copies of one unrelated 2026 fix, so take landmark commits from the timeline.
Without `until`, `retrieve_context` answers with the newest matching revert
(for MERGE, 2026's MERGE/SPLIT PARTITION revert). Mail before the list
archive's start is not indexed.

Validated on MERGE: the timeline runs from Simon Riggs's 2017 thread through
two 2018 commits and their reverts (`e6597dc353` by `aa5877bb26`, `d204ef6377`
by `08ea7a2291`) to `7103ebb7aa` (2022-03-28, first release 15.0), and
`commit_history` agrees on each. `retrieve_context` with `until="2019-01-01"`
led with Simon Riggs's revert on pgsql-committers.

REST/GraphQL: `GET /api/v2/related?ref=feature:<name>`,
`GET /api/v2/code/history/commits?message=...`,
`GET /api/v2/code/history/commit/<sha>`. `history-of` is MCP only.

## 2. "Which committers will be most interested in ___?"

Inputs: a subsystem path (`src/backend/access/brin/`) or a topic.

```text
c = search_commits(paths=["<dir>/"], since="<3y ago>", range="master", limit=200)
count c.commits by author                            # who changed it lately
m = hybrid_search(query="<topic>", since="1y", limit=50)
count m.results by from                              # who discusses it lately
for top 5 names n:
    p = get_contributor(name=n)                      # p.releases[*].committed says committer
    w = whats_new(who=n, since="6m", kinds=["mail_from", "git_author"], limit=5)
rank by recent commits + recent mail; drop names with nothing in 6 months
```

Cite: the commit SHAs and message urls behind each name. Present it as "who
has worked here", not "who will review".

Limits: without `range`, every branch is searched and each back-patch counts
again (on BRIN, Tomas Vondra 77 and the 200-row limit reached); `range="master"`
counts a back-patched fix once, and misses work that landed only on a back
branch. `search_commits` rows carry `author` only (the committer); patch
authors credited in trailers need `get_commit` on each. Commit counts reward
committers who split work into many small commits. A name with no
`get_contributor` match may be a new address of a known person.

Validated on BRIN since 2023-01-01, master: 111 commits, Tomas Vondra 30,
Peter Eisentraut 25, Michael Paquier 10, Alvaro Herrera and David Rowley 6
each; Tomas Vondra also leads the last year's BRIN mail (5 of 50 hits).

REST/GraphQL: `GET /api/v2/code/history/commits?range=master&paths=<dir>/&since=...`,
`GET /api/v2/mail/search?q=<topic>&since=1y`, `GET /api/v2/activity?who=<name>`.
GraphQL `repositoryCommits(repo: "postgres", branch: "master", path: "<dir>",
since: ...)`. Both gave the same 111 commits.

## 3. "What are the design influences for ___?"

Inputs: a feature or algorithm (serializable isolation, Lehman and Yao btrees).

```text
c = search_commits(message="<feature words>", limit=10)  # the commit that landed it
k = get_commit(commit=<first commit>.sha, diff=false)
read k.message for "based on", "paper", "see README-*"
if it names a README: r = read_file(path="<README path>")   # references sections
t = retrieve_context(query="<feature> design paper <author name>", token_budget=4000)
for each prior system or paper named: hybrid_search(query="<name> <feature>")
```

Cite: the README lines (path and line numbers), the commit message, and the
mail passages where the design was argued.

Limits: influences that nobody wrote down are not in the index. Papers are not
indexed: only what the code, commits and mail say about them. A passage that
mentions a paper is not evidence that the design followed it; look for the
commit or README that says so.

Validated on SSI: `dafaa3efb7` (2011-02-07) "based on research papers by
Michael J. Cahill (see README-SSI)"; `read_file` of
`src/backend/storage/lmgr/README-SSI` lines 16-31 names the SIGMOD 2008 paper
and the thesis; `retrieve_context` returned Kevin Grittner's 2009 message
introducing the paper.

REST/GraphQL: `GET /api/v2/code/history/commits?message=...`,
`GET /api/v2/code/history/commit/<sha>?diff=false`,
`GET /api/v2/code/history/file?path=...`. `retrieve_context` is MCP only
(`/api/v2/mail/search` gives the ranked hits without the passages).

## 4. "Who contributed to ___ and is still active on the list?"

Inputs: a feature with a known commit (or find it as in recipe 1).

```text
k = get_commit(commit="<sha>", diff=false)
people = k.trailers["Author"] + k.trailers["Reviewed-by"] + ...
h = commit_history(commit="<sha>")                   # + Discussion participants
people += h.participants[*].name
for each name n in people:
    a = get_author_messages(author=n, since="6m", limit=1)
    active = a.total > 0
```

Cite: the trailer lines of the commit, and for each active person their newest
message url.

Limits: `get_author_messages` searches one list (default pgsql-hackers); pass
`inbox` for others. A person who changed address or display name can look
inactive (Simon Riggs and Pavan Deolasee both return 0, for different
reasons: check `get_contributor` before concluding). Trailer names carry
qualifiers such as "(earlier versions)"; strip them before the lookup.

Validated on MERGE `7103ebb7aa`: authors Pavan Deolasee, Alvaro Herrera, Amit
Langote, Simon Riggs; Amit Langote has mail in the last 6 months, Pavan
Deolasee and Simon Riggs none.

REST/GraphQL: `GET /api/v2/code/history/commit/<sha>?diff=false`, then
`GET /api/v2/mail/search?q=from:"<name>"&since=6m&list=pgsql-hackers&sort=latest`.
`commit_history` participants are MCP only.

## 5. "Has the idea ___ been tried before?"

Inputs: the idea in a few words (64-bit transaction ids).

```text
e = search_commitfest(query="\"<phrase>\"", commitfests="all", limit=20)
for each entry x in e.results:
    hx = entry_history(cf_id=x.cf_id)                # earlier and later incarnations
    gx = get_entry(cf_id=x.cf_id)                    # threads, authors, status
r = retrieve_context(query="<idea>", token_budget=4000)  # older mail, before the commitfest app
s = said(message_id=gx.threads[0])                   # who objected, in their own words
```

Stop when every entry's final status is known. Cite: entry ids with status,
the thread urls, and objections as `said` sentences with their urls.

Limits: quote the phrase: an unquoted query matches any transaction-id entry
(132 for "64-bit transaction ids"). `entry_history` linkage `title-prefix` is
weak (it joined "64-bit XIDs in deleted nbtree pages", a different patch).
`said` stance labels come from cue words; read the sentence. Discussions before
the commitfest app (2014) are only in the mail search.

Validated on 64-bit XIDs: entries 4703 and 3594 (Returned with feedback),
first proposals on the list in 2006; `said` on 4703's thread found Robert
Haas's and Heikki Linnakangas's concerns.

REST/GraphQL: `GET /api/v2/commitfest/search?q=...&cf=all`,
`GET /mcp/api/commitfest/entry/<cf_id>/history`. GraphQL
`entries(author: ...)`, `search(inbox:, query:)`. `said` is MCP only.

## 6. "Is ___ a known security issue?"

Inputs: a CVE id, or a symptom in a security-relevant area.

```text
if a CVE id:
    x = cross_reference(ref="CVE-YYYY-NNNNN", kinds=["git"], limit=10)
    fix = x.related.git where relations has "fixes-cve" and title matches x.ref.title
    for fix: get_commit(commit=fix.sha, diff=false)   # message, first_releases per branch
else:
    c = search_commits(message="Security: CVE-", paths=["<dir>/"], limit=20)
    a = hybrid_search(query="<area> security", inbox="pgsql-announce")
```

Cite: the advisory url (`x.ref.url`), the fixing commit per branch with the
release that first shipped it.

Limits: `fixes-cve` also tags later commits that name the CVE (test and build
follow-ups); for CVE-2024-10979 the real fix "Block environment variable
mutations from trusted PL/Perl" came fourth. Match the advisory title.
Undisclosed issues are not in a public archive, so "nothing found" means
"nothing public", never "not vulnerable". The `Security: CVE-...` trailer
convention is recent; older fixes say so only in the release notes.

Validated on CVE-2024-10979: advisory url, fix on 12-17 and master, shipped in
12.21, 13.17, 14.14, 15.9, 16.5, 17.1. The path route found the November 2026
PL/Perl fixes (`c148f9509e` carries `Security: CVE-2026-...`).

REST/GraphQL: `GET /api/v2/related?ref=CVE-YYYY-NNNNN&kinds=git`,
`GET /api/v2/code/history/commits?message=Security:%20CVE-&paths=...`.

## 7. "Is ___ a known bug?"

Inputs: a symptom (an error message, a crash in a command).

```text
b = hybrid_search(query="<symptom>", inbox="pgsql-bugs", limit=10)
for each likely report r in b.results:
    t = get_thread(message_id=r.message_id, inbox="pgsql-bugs", include_body=false)
    x = cross_reference(ref=r.message_id, kinds=["git"])  # commits tied to the thread
    read the replies (get_message) for "fixed by", a SHA, or "cannot reproduce"
c = search_commits(message="<symptom words>", since="<version branch date>")
for a fix f: commit_history(commit=f.sha).first_releases   # which minor release has it
```

Cite: the report url, the reply that diagnoses it, and the fixing commit with
its first release.

Limits: a commit is tied to a report only when its `Discussion:` names the
thread or the thread cites the SHA; many fixes do neither. Bug numbers
(`BUG #17960`) are not a lookup key for `find_related_discussions` (it does a
substring match over Message-IDs); use the report's Message-ID. Reports
answered off-list leave no trace.

Validated on "pg_dump generated column": BUG #17960 (2023-06-04); Tom Lane's
reply points at `0b126c6a4b`, and `cross_reference` on the report found the
same commit (first shipped in 12.10, 13.6, 14.2, 15.0).

REST/GraphQL: `GET /api/v2/mail/search?q=...&list=pgsql-bugs`,
`GET /api/v2/related?ref=<message-id>&kinds=git`.

## 8. "Why was ___ designed this way?"

Inputs: a design choice, ideally with the code it lives in.

```text
r = retrieve_context(query="why does <thing> <behaviour>", token_budget=4000)
if r.commit_context: k = r.commit_context            # check it is the right commit
else:
    b = blame(path="<file>", start_line=a, end_line=z)   # who wrote the lines
    k = get_commit(commit=<the line's sha>, diff=false)
d = cross_reference(ref=k.sha)                       # the Discussion thread and timeline
s = said(message_id=<that thread>, topic="<choice>")
```

Cite: the commit message, the Discussion thread, and the objection or
agreement sentences.

Limits: `commit_context.states_reason` is a rule's guess; read the message.
`blame` ignores pgindent commits by default (`ignore_revs`); a line moved by a
refactor blames the refactor, so walk back with `commit=<sha>^`. Reasons given
in person, at conferences or on IRC, are not in the index.

Validated on "why was MERGE reverted in 2018": `commit_context` was the revert
`aa5877bb26`, and the passages included Simon Riggs's revert message on
pgsql-committers.

REST/GraphQL: `GET /api/v2/code/history/blame?path=...`,
`GET /api/v2/related?ref=<sha>`. `retrieve_context` and `said` are MCP only.

## 9. "What happened to patch ___?"

Inputs: a patch subject, a commitfest entry, or a thread.

```text
e = search_commitfest(query="<title words>", commitfests="all")
g = get_entry(cf_id=e.results[0].cf_id)              # status, threads, branches
h = entry_history(cf_id=g.cf_id)                     # moved, returned, committed when
if status is committed: c = cross_reference(ref=g.threads[0], kinds=["git"])
else: t = get_thread(message_id=g.threads[0], include_body=false)   # last activity
      s = said(message_id=g.threads[0])              # what stopped it
```

Cite: the entry with each commitfest's status, the last messages, and the
commit if it landed.

Limits: the `outlook` in `search_commitfest` is a model's estimate of P(commit),
not a review. Entries filed before the commitfest app only exist as threads.
A patch can land under a different subject: search the commits by author and
date too.

Validated on "Native planner and executor for SQL/PGQ": entry 7258, Needs
review in commitfest 62, outlook p_release 0.24; and on MERGE thread
`CANP8+jKitBSrB7o...`: entry 1446, Returned with feedback in 2018.

REST/GraphQL: `GET /api/v2/commitfest/search?q=...&cf=all`,
`GET /mcp/api/commitfest/entry/<cf_id>/history`. `get_entry` and `said` are
MCP only.

## 10. "What broke after commit ___?"

Inputs: a postgres commit, or a window on a branch.

```text
s = commit_buildfarm_status(commit="<sha>")           # per animal: status, failing stage
w = search_commits(range="master", since="<day>")     # neighbours, to bound a window
pick <before> and <after> from w whose commit_buildfarm_status count > 0
b = find_breaks(branch="master", from_commit=<before>, to_commit=<after>)
for each failing animal a: animal_history(name=a, branch="master", limit=10)
f = search_commits(message="revert|fix", since="<day>", paths=[<touched paths>])
```

Cite: the buildfarm log urls, the commit, and any follow-up fix or revert.

Limits: the buildfarm has no commit order: `find_breaks` windows are by run
time, not git topology. Buildfarm history does not reach back years: for a
2022 commit `commit_buildfarm_status` returned `count: 0`, which means "no
runs on record", not "nothing broke". Animals build the branch tip, so many
commits have no runs of their own; `find_breaks` with such a commit as an end
fails with "resolve window: ... cannot scan NULL": pick ends that have runs.
User-visible breakage reaches the lists later; search pgsql-bugs for the
commit's subject too.

Validated on `5ff67951c4` (2026-11-25): 39 runs, all passed. `find_breaks`
from it to `048c8725bf` (07:59 to 15:14 UTC that day): 0 failures. With
`650925dad0` (8 runs) to `14644e1238` (0 runs) as the ends it gave the
window error.

REST/GraphQL: `GET /mcp/api/buildfarm/commit/<sha>`,
`GET /mcp/api/buildfarm/breaks?branch=master&from=<sha>&to=<sha>`.

## 11. "Who should review ___?"

Inputs: a patch (its thread, or the files it touches).

```text
files = the paths the patch touches (get_attachment, or the diff you hold)
for each file p:
    b = git_blame(path=p, limit=100)                 # recent commits to the file
    count b.history by author_name
prior = hybrid_search(query="<subject words>", limit=20)
count prior.results by from                          # who argued about this area
for top names n: whats_new(who=n, since="2m", kinds=["mail_from"])   # still around
exclude the patch's own authors; prefer people with both commits and mail here
```

Cite: the commits and messages behind each suggestion.

Limits: this finds people who know the code, not people with time; say so.
`git_blame` gives a file's commit list (it does not take a directory: use
`search_commits(paths=[...])` for one); `blame` gives lines. Authors who never
commit (reviewers) show only in mail and in `Reviewed-by:` trailers.

Validated on `src/backend/access/brin/brin.c`: of the file's last 100 commits
Tomas Vondra has 22, Peter Eisentraut 17 and Tom Lane 10, and Tomas Vondra also
leads the last year's BRIN mail; `get_attachment` read the patch of a posted
series (MERGE v21) to get its file list.

REST/GraphQL: `GET /api/v2/code/history/commits?paths=<file>`,
`GET /api/v2/mail/search?q=...`, `GET /api/v2/activity?who=<name>`.
