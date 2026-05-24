# Commit message format

PostgreSQL commit messages have a strong, consistent shape that is
audited by every committer at review time. Getting the form right is
the single cheapest way to look like you have done this before.

## TL;DR — what the agent must do

Write the commit message in this shape:

```
<subject ≤ ~70 chars, present-tense imperative, period at end>
<blank line>
<body, paragraphs of prose, wrapped to 72-78 cols>
<blank line>
Author: First Last <email@example.com>
Co-authored-by: First Last <email@example.com>
Reported-by: First Last <email@example.com>
Reviewed-by: First Last <email@example.com>
Tested-by: First Last <email@example.com>
Suggested-by: First Last <email@example.com>
Discussion: https://postgr.es/m/<message-id>
Backpatch-through: <branch>
```

Trailers appear in roughly that order (Author first, Discussion last
before Backpatch-through). Trailers are *load-bearing*: the project
will not commit a patch without `Discussion:`.

## Subject line

- **Length**: empirically up to ~79 chars, with the bulk of commits
  in the 50–70 range (samples from `git log --pretty=%s` on
  `origin/master`). The wiki guideline says "ideally under 80". Aim
  for ≤72; treat the 80-char ceiling as a soft cap, not a target.
  The "50-char subject" rule from generic git advice is *not* what
  the project does — many real subjects exceed 50.
- **Imperative mood**: "Add X.", "Fix Y.", "Reject Z.", not "Added"
  / "Adding" / "Fixes".
- **Period at the end** of the subject. This is unusual versus
  generic git practice and is the project's convention. Inspect
  `git log --pretty=%s` for confirmation.
- **Subsystem prefix optional**, but common when the change is
  scoped tightly: `psql:`, `pg_dump:`, `Doc:`, `Meson:`, `pgindent:`.
  No square brackets. No conventional-commits `feat:` / `fix:`
  prefixes.
- **Initial cap, normal English capitalisation** otherwise.
- **Do not encode the bug number or CF entry** in the subject. Those
  go in the body or the Discussion link.

Examples from `origin/master`:

- `Make ExecForPortionOfLeftovers() obey SRF protocol.`
- `Doc: split functions-posix-regexp section into multiple subsections.`
- `Fix injection point detach timing problem in TAP test for lock stats`
  (note: 68 chars, no period — a small minority do this; most include
  the period)
- `Run pgindent.`

## Body

- Wrap at 72-78 columns. Every prose line under that limit.
- Paragraphs separated by blank lines.
- Robert Haas's essay-shape (problem / design / alternatives
  considered) is the gold standard; see
  `community/voices/robert-haas.md` § "Comprehensible commit messages".
- Tom Lane's bug-fix-shape (buggy behaviour described, then the
  underlying invariant restored) is the gold standard for fixes; see
  `community/voices/tom-lane.md` § "Don't paper over the symptom".
- No markdown. The body is plain text rendered as plain text by `git
  log` and the mailing-list.
- Reference other commits as bare 7-12-char SHAs, optionally with
  the subject in quotes: `commit c6e0fe1f2` or `c6e0fe1f2 "Rewrite ..."`.
- File paths are bare: `src/backend/parser/gram.y`, no backticks.
- "In passing, ..." is the project idiom for an unrelated tiny
  cleanup that is easier to bundle than to split. Use sparingly;
  Tom rejects it for non-trivial cleanups.

## Trailers — every name and form

The project's accepted trailers and what they mean. Use the exact
spelling — committers' tooling parses these.

| Trailer | Who it credits |
|---|---|
| `Author:` | Primary author of the patch. |
| `Co-authored-by:` | Substantial co-author. |
| `Reported-by:` | Person who reported the bug or proposed the change request. |
| `Reviewed-by:` | Person who reviewed the patch in depth. **Not** for "+1" replies. |
| `Tested-by:` | Person who confirmed the patch works in their environment. |
| `Suggested-by:` | Person who suggested the design but did not write the patch. |
| `Diagnosed-by:` | (Less common) Person who found the root cause. |
| `Backpatch-through:` | Branch name (e.g. `15`) to which back-patches apply. |
| `Discussion:` | Mailing-list URL. **Mandatory.** |

Form rules:

- One trailer per line. Multiple `Reviewed-by:` lines if multiple
  reviewers; do not combine them onto one line.
- Email address in `<...>` brackets. Real address; no obfuscation.
- Optional parenthetical scope qualifier after the address:
  `Reviewed-by: Tom Lane <tgl@sss.pgh.pa.us> (coverity fix only)`.
  See commit `5ba34f6dc83` (Lukas Fittl, 2026-05-16) for the
  canonical example of scope-qualified review.
- `Discussion:` URL form: prefer
  `https://postgr.es/m/<MESSAGE_ID>` (the short redirector). The
  long form `https://www.postgresql.org/message-id/<MESSAGE_ID>` is
  also accepted; old commits use both. Bare message-ids are
  forbidden.
- `Discussion:` may also use the *flat* view of a thread:
  `https://postgr.es/m/flat/<MESSAGE_ID>`. See commit `e157fe6f76e`
  (Tomas Vondra) Discussion:
  `https://postgr.es/m/flat/a177a6dd-240b-455a-8f25-aca0b1c08c6e%40vondra.me`.
- Multiple `Discussion:` lines are accepted when the patch came out
  of more than one thread. Keep them in chronological order.

## The `https://postgr.es/m/<id>` short form

`postgr.es/m/` redirects to
`www.postgresql.org/message-id/<id>`. The short form is preferred
because:

- It is shorter (matters for 79-col commit-message wrap).
- It survives subdomain reorganisations on www.postgresql.org.
- The project's tooling — commitfest.postgresql.org, the
  cross-reference scanner that links commit messages to threads —
  recognises it canonically.

URL-encode `@` as `%40` in message-ids that contain it. Example:
`a177a6dd-240b-455a-8f25-aca0b1c08c6e%40vondra.me`.

## Back-branch commits

When a fix is back-patched, the **commit message stays identical
across back-branches** with these exceptions:

1. The subject may add `(branch)` if there is branch-specific
   divergence; this is rare.
2. The body may add a "differs from master in ..." paragraph if the
   patch had to be adapted.
3. The trailers stay identical, including `Discussion:`.
4. The committer adds `Backpatch-through: <oldest-supported-branch>`
   on the master commit (and on all back-branch commits) so the
   archaeology is unambiguous.

`git log --grep="Backpatch-through"` on master shows the canonical
shape. The trailer is *not* added retroactively to old commits.

## What a non-committer puts in their proposed message

Authors submitting patches for review write a *proposed* commit
message in the cover letter, including everything except the
`Discussion:` trailer (which the committer fills in with the
canonical hackers thread URL). Authors should:

- Write the subject and body fully.
- List `Author:` (themselves) and any `Co-authored-by:`.
- List `Reported-by:` if they know the original reporter.
- *Not* fill in `Reviewed-by:` themselves — committers add that
  based on the actual review activity in the thread.
- *Not* fill in `Discussion:` — the committer uses the URL of the
  thread that landed the patch (often a different thread from the
  initial proposal).

## Bruce-style release-note language

For user-visible behaviour changes that are headed for the release
notes (`doc/src/sgml/release-*.sgml`), Bruce Momjian rewrites
contributor wording into a project house-style. The patch author can
save Bruce a step by writing the user-facing description in the
release-note shape directly:

- Begin with a verb in the present tense: "Add", "Improve", "Fix",
  "Reject", "Reduce".
- Avoid implementation jargon ("hash table reorg", "atomic CAS")
  that the user does not see.
- One sentence. If you need two, the change is probably two
  release-note items.

See `community/voices/index.md` § "Bruce Momjian" for the broader
release-note conventions.

## Commit message vs. cover letter

- The **cover letter** (the `0000-cover-letter.patch` from
  `git format-patch --cover-letter`) is conversational; it explains
  context, motivation, and how the series is split.
- The **commit message** is what lands in `git log` and outlives
  the thread. It should be self-contained: a future archaeologist
  reading `git show <sha>` should not need to chase the
  `Discussion:` link to understand the change.

If your commit message is identical to your cover letter, one of
them is wrong (probably the commit message — too verbose or too
tutorial).

## Pre-commit-check the message

Before sending `git format-patch`:

```sh
git log -1 --format=%B            # the message your patch will carry
git log -1 --format=%s | wc -c    # subject length sanity check
git log -1 --format=%B | awk 'length>80 {print NR": "length" chars"}'
                                  # any over-long body line
```

If any body line exceeds ~80 chars (URLs excepted), reflow.

## Sources

- Wiki: <https://wiki.postgresql.org/wiki/Working_with_Git> §§
  "Commit messages", "Commit message format". Authoritative on the
  subject line, body, and trailer shape.
- Wiki: <https://wiki.postgresql.org/wiki/Submitting_a_Patch>
  § "Save us the trouble of reformatting" and § "What gets posted to
  hackers".
- Wiki: <https://wiki.postgresql.org/wiki/Committing_checklist> for
  the committer-side checks on the message.
- Empirical: `git log --pretty=%s -n 500 origin/master` from a fresh
  clone shows the actual subject-length distribution; the 80-char
  cap is hit but rare, the median is around 60.
- Commit `5ba34f6dc83` "pg_test_timing: Show additional TSC clock
  source debug info" (Lukas Fittl, 2026-05-16) — scope-qualified
  `Reviewed-by:` example.
- Commit `e157fe6f76e` "Add EXPLAIN (IO) instrumentation for
  TidRangeScan" (Tomas Vondra) — `flat/` Discussion-URL example.
- Commit `207cb2abcba` "Make ExecForPortionOfLeftovers() obey SRF
  protocol." (Tom Lane) — typical Tom shape.
- Commit `e8ec19aa321` "Add pg_stash_advice contrib module." (Robert
  Haas) — typical Robert essay-shape.
- Cross-reference: `community/conventions/git-workflow.md` for the
  `git format-patch --cover-letter` mechanic.
- Cross-reference: `community/voices/tom-lane.md` § "Don't paper
  over the symptom" — bug-fix message shape.
- Cross-reference: `community/voices/robert-haas.md` §
  "Comprehensible commit messages".
- Cross-reference: `community/conventions/committing-checklist.md` for
  trailer-presence audits.
- `https://postgr.es/m/` redirector documented at
  <https://wiki.postgresql.org/wiki/Mailing_Lists>.
