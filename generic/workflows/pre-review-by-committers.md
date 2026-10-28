# Workflow: Pre-Review a Patch as Several Committers Would

Before posting a patch to pgsql-hackers, predict what three or more PostgreSQL
committers would raise, so the author can address the obvious objections
first. Each reviewer's prediction is a run of the evidence-grounded skill
[`tooling/review-as-author/SKILL.md`](../../tooling/review-as-author/SKILL.md):
every point attributed to a person rests on their own quoted message
(Message-ID, date, verbatim, checked with `get_message(quotes:)`) or their
commit. This page only says who to pick and how to combine the results.

This replaced a role-play from the voice files. The voice files
(`community/voices/*.md`) are still useful, but as **secondary context**: they
suggest what to search for. They are not evidence, and nothing goes under a
reviewer's name because a voice file says so.

## Inputs

One of: a patch file, a commit SHA, a branch (`git diff $(git merge-base
origin/master <branch>)..<branch>`), or a pgsql-hackers Message-ID whose
attachment is the patch (`get_attachment`).

## Steps

### 1. Is it worth it?

Skip, with a one-line note, if the patch is under 20 lines and touches no
header, `.sgml` or `pg_proc.dat` file; a translation (`*.po`); or build or
editor configuration only.

### 2. Pick the reviewers

Map the touched paths to a subsystem, then pick three or more people with a
record there. Find them from the evidence, not from memory:

- `search_commits(paths: [<changed files>], limit: 30)`: who committed and who
  is in the `Reviewed-by:` trailers of recent changes to these files.
- `blame(path:, start_line:, end_line:)` on the rewritten lines: who wrote them.
- `get_contributor(name:)` on each candidate: how active they are now.

A voice file for a candidate (`community/voices/<name>.md`) can suggest search
topics for step 3.

### 3. One review per reviewer

Run [`review-as-author`](../../tooling/review-as-author/SKILL.md) for each,
with the same as-of date (today, or the patch's posting date). Keep its output
format: verdict on the premise first, points with their basis, then "General
reviewer notes" for checklist items with no evidence from that person.

### 4. Synthesize

- **Agreement:** points two or more reviewers would raise, each with its own
  evidence. Fix these before posting.
- **Divergence:** where their records point different ways. Say so; the author
  decides.
- **Prior art:** `retrieve_context(question: <the patch in one sentence>)` and
  `cross_reference(ref: "feature:<words>")` for earlier proposals. "We
  discussed this in 2019 and rejected it" is the objection most worth
  pre-empting.
- **Agent observations:** anything you noticed that no reviewer's evidence
  covers, labelled as yours.

### 5. The report

Top of the report:

```
> Simulated pre-review: predictions of what <names> would likely raise,
> from their public pgsql-hackers messages and commits. These aren't their
> words or opinions. Don't cite this report on the list as if they said it.
```

Then the per-reviewer sections, then the synthesis. Never quote a voice file
as if the person said it.

## Failure modes

- **Thin record:** a reviewer with few messages on the topic gives a weak
  prediction; say so in their section rather than padding it from the voice
  file.
- **A quote fails the check:** `own_words: false` means they quoted someone
  else. Drop it or find their own words.
- **A huge patch:** split it per subsystem and run this per part.

## Sources

- [`tooling/review-as-author/SKILL.md`](../../tooling/review-as-author/SKILL.md),
  adapted from pghacker-mcp (MIT).
- `community/voices/*.md`, `community/review-standards.md`,
  `community/common-pitfalls.md`: background, not evidence.
- [`review-thread-context.md`](review-thread-context.md): when the patch already
  has replies on the list, read them first.
