# Workflow: Submit a patch to PostgreSQL

The canonical end-to-end patch-author flow: from "I have a change I
want to propose" through "the commitfest entry is ready for review".
This skill is the spine that ties the conventions and supporting
workflows together.

## TL;DR — the whole pipeline

```
1. Confirm the patch is wanted (search hackers, search commitfest).
2. (For non-trivial work) Post an RFC on -hackers FIRST, then iterate.
3. Develop on a feature branch off origin/master.
4. Self-review (Greg Smith methodology + pgindent + tests).
5. git format-patch --cover-letter -v1 -B -M origin/master..HEAD
6. Send to pgsql-hackers@lists.postgresql.org via git send-email.
7. Register the entry on commitfest.postgresql.org with the
   https://postgr.es/m/<id> link.
8. Watch cf-bot CI; address failures.
9. On review feedback, post v2/v3/... in the same -hackers thread.
10. When committed: thank reviewers, close the CF entry as committed.
```

## 0. Pre-submission research

Before writing any code, verify:

- **Is this already in commitfest?** Search at
  <https://commitfest.postgresql.org/> for keywords. If there's a
  live entry, your work should probably engage with that thread,
  not start a new one.
- **Has this been discussed and rejected?** Search the hackers
  archive for the topic:
  <https://www.postgresql.org/list/pgsql-hackers/>. If a similar
  proposal was rejected with a substantive objection, your patch
  must address that objection up front.
- **Is this on the wiki TODO list?**
  <https://wiki.postgresql.org/wiki/Todo>. The list is curated; an
  entry there is some signal that the project considers it
  desirable.
- **Is there a wiki design page?** For larger features, sometimes
  yes (see the `Hint Bits`, `Hot Standby`, `Logical Replication`
  pages as design-prose precedents).
- **Who has been most active in the area recently?**
  `git -P log --author=... --since=...` over `src/backend/<area>/`
  shows you who to expect on review.

Cross-reference: `generic/workflows/research-and-connect-dots.md`
for the deep-research workflow that produces this picture.

## 1. RFC for non-trivial work

If your change:

- Adds a new SQL clause, GUC, or view.
- Changes existing planner behaviour in a way users will notice.
- Changes WAL format or any installed catalog.
- Adds a new system shared-memory area.
- Touches more than ~500 lines of code, or
- Has a design choice with no clear precedent,

then post an **RFC** (request for comments) on -hackers *before*
writing the patch. Subject prefix: `[RFC]` or `Proposal:`. Body:

- Problem statement.
- Proposed design (1-3 paragraphs).
- Alternatives considered.
- Open questions you want input on.
- Estimated patch size.

Wait at least a few days for objections. Iterate the design via
follow-ups before writing code. This is cheaper than writing 2,000
lines and then learning the design is wrong.

For trivial work (typo fix, doc clarification, narrow bug fix),
skip RFC and post the patch directly.

## 2. Development

See `community/conventions/git-workflow.md` § "Branch-per-feature
workflow". Key rules:

- Branch off `origin/master`. Never off a back-branch.
- Rebase, never merge.
- Each commit independently builds and passes `make check`.
- Don't push to any shared remote.

## 3. Self-review

See `community/conventions/creating-clean-patches.md`. The minimum:

```sh
src/tools/pgindent/pgindent --commit origin/master..HEAD
git diff --check origin/master..
git diff --color origin/master..   # eyeball
make -s -j$(nproc) check-world     # full test suite
```

If anything fails, fix and re-test.

**catversion — mention it, don't bump it.** If the patch changes the
catalog or WAL format (new/changed system catalog, new built-in function
with a fixed OID, changed WAL record layout), do **not** bump
`CATALOG_VERSION_NO` in `src/include/catalog/catversion.h` in the patch you
post — a concrete bump guarantees a merge conflict with every other
in-flight catalog-touching patch. Instead, say so in the covering email, e.g.:

> This patch changes the catalog, so it will need a `catversion.h` bump when
> committed; I've left that out of the patch to avoid conflicts.

The committer sets the real value to the commit date at push time. See
`community/conventions/committing-checklist.md` § "catversion bump" for the
committer-side half of this.

## 4. Produce the patch series

```sh
git format-patch --cover-letter -v1 -B -M origin/master..HEAD
```

Output:

```
v1-0000-cover-letter.patch
v1-0001-Add-foo.patch
v1-0002-Test-foo.patch
v1-0003-Doc-foo.patch
```

Edit `v1-0000-cover-letter.patch`:

- Subject line of the *series*.
- Motivation paragraph.
- Layout summary (one bullet per numbered patch).
- Open questions.
- Testing summary.
- Performance numbers if perf is the rationale.

See `community/conventions/creating-clean-patches.md` § "The cover
letter".

## 5. Send to -hackers

```sh
git config sendemail.smtpserver smtp.example.com
git config sendemail.smtpuser   you@example.com
git config sendemail.smtpencryption tls
git config sendemail.smtpserverport 587

git send-email --to=pgsql-hackers@lists.postgresql.org \
               --annotate \
               v1-*.patch
```

`--annotate` opens each `.patch` in `$EDITOR` for one last review.
Always use it.

The *first* mail is the cover letter; subsequent are the numbered
patches as `In-Reply-To:` to the cover letter. `git send-email`
handles this if you pass `v1-*.patch` (alphabetical order).

If you don't have `git send-email` configured: post via your
mail client of choice, but ensure:

- Plain text only (no HTML).
- Patches as attachments, *not* inline. Some old MUAs (mutt) do
  inline correctly; most modern MUAs corrupt whitespace if asked
  to inline.
- Subject line uses the series subject (cover letter's subject).
- Body of the first message is the cover-letter body.

## 6. Register on commitfest

Go to <https://commitfest.postgresql.org/> and create an entry:

- **Open Commitfest**: pick the next open commitfest. Commitfests
  run quarterly (Mar, Jul, Sep, Nov on a typical year — exact
  schedule on the page).
- **Title**: short description, ≤80 chars.
- **Topic**: pick the most-specific category (Performance, Bug
  Fixes, Server Features, etc.).
- **Patch**: paste the link of the cover-letter message in the
  form `https://postgr.es/m/<message-id>`.

The cf-bot picks up the `https://postgr.es/m/` URL, fetches the
attached patches, and runs CI on them. Status appears within an
hour of registration.

## 7. Declare CF dependencies

If your patch depends on another in-flight patch:

- In the cover letter, state the dependency with the other patch's
  CF entry URL and -hackers thread URL.
- On the commitfest entry, link the dependency in the
  "Dependencies" field.
- Rebase on top of the dependency before posting; if your patch
  doesn't apply against `master` alone, the cf-bot CI will fail and
  reviewers will skip it.

If a dependency moves, you must rebase.

## 8. cf-bot CI failures

cf-bot runs on every patch posted to a registered CF entry, on
several platforms (Linux, FreeBSD, macOS, Windows). Status appears
on the CF entry page.

Common failure categories:

- **Apply failure** — patch no longer applies cleanly to master.
  Rebase, post v2.
- **Build failure** — your local build worked but a different
  toolchain doesn't. Investigate the cf-bot logs; common causes:
  - Missing Meson or autoconf parity (see
    `community/voices/michael-paquier.md` § "Build system").
  - Compiler-version-specific warnings on a stricter compiler.
  - Missing `pg_config_manual.h` defines on Windows.
- **Test failure** — `make check-world` fails on cf-bot but not
  locally. Common causes:
  - Test depends on locale; force `LANG=C` in TAP fixtures.
  - Test depends on timing; use injection points.
  - Test creates a role/object without `regress_` prefix and
    collides on shared cf-bot setups.
  - Race condition exposed by slower / faster CI hardware.
- **Linter failures** — pgindent disagrees with your formatting,
  whitespace check fails. See `community/conventions/pgindent.md`.

Address every cf-bot failure before posting v2. Reviewers ignore
red CF entries.

## 9. Responding to review feedback

When a reviewer responds:

- Read fully before replying. Quote-trim aggressively; reply
  inline at the points being addressed.
- For each substantive concern: either say "fixed in v2 by …" or
  "I disagree because …". Don't ignore points.
- For each suggested improvement: implement or explain why not.
- Update the cover letter for v2 with a "Changes since v1:"
  section.

Bump the version label and post v2 to the same thread:

```sh
git format-patch --cover-letter -v2 -B -M origin/master..HEAD
git send-email --to=pgsql-hackers@... --in-reply-to=<v1-cover-id> \
               v2-*.patch
```

`--in-reply-to=<message-id-of-v1-cover-letter>` keeps v2 in the same
threaded view.

The CF entry's "Latest attachment" field updates automatically when
cf-bot finds the new attachment via the `https://postgr.es/m/` URL.

## 10. Stalemates and pivots

If a patch sits in commitfest for 3+ cycles with no committer
attention:

- Re-pitch on -hackers: explain what changed, what the unresolved
  question is, ask if anyone is willing to commit.
- Find a committer to mentor the patch. Robert Haas's blog
  (`community/voices/robert-haas.md`) discusses this dynamic.
- Decompose the patch into a smaller "base" patch that lands now
  and follow-up patches that land later.
- Withdraw and re-target. Better to land 80% than to perpetually
  re-rebase 100%.

Do not re-bump the patch every cycle without engagement. Cf-bot
green + no reviewer attention is *not* a sign the patch is good;
it usually means the patch is contested or under-explained.

## 11. After commit

When a committer commits your patch:

- They reply to the thread with the commit hash.
- The CF entry moves to "Committed" status.
- Reply to thank reviewers and committers in the same thread.
- Watch the buildfarm at
  <https://buildfarm.postgresql.org/cgi-bin/show_status.pl>. If a
  red animal appears within hours of your commit, the committer
  may revert and ask for a fix. Be ready to respond quickly.

## Status transitions on commitfest

| State | Meaning |
|---|---|
| `Needs Review` | Open for review, no committed reviewer. |
| `Waiting on Author` | Reviewer has posted feedback; ball in author's court. |
| `Ready for Committer` | Reviewers are satisfied; awaiting committer attention. |
| `Committed` | Landed on master. |
| `Rejected` | Rejected with rationale. |
| `Withdrawn` | Author withdrew. |
| `Returned with Feedback` | Punted to the next CF for not progressing. |
| `Moved to next CF` | Punted to the next CF, still active. |

Authors should move their entries to `Waiting on Author` when they
are working on a v2, and back to `Needs Review` after posting it.

## Common author mistakes

1. **Posting before pgindent.** Patch goes back immediately.
2. **Posting from a branch with stray commits.** Patch series
   includes unrelated changes; reviewer asks for re-roll.
3. **Forgetting to register on commitfest.** Patch is invisible to
   the project's tracking; reviewers may never see it.
4. **No `Discussion:` link in the proposed commit message.** Author
   should not fill that in (committer does), but the author should
   have *a* hackers thread to point at.
5. **Bundling docs in a separate patch from code.** For a feature,
   doc and code go together. For pure infrastructure changes that
   land before the user-visible feature, docs follow with the
   feature.
6. **Replying off-list to reviewers.** All discussion stays
   on-list. Off-list discussion is ignored by other reviewers.

## Sources

- Wiki: <https://wiki.postgresql.org/wiki/Submitting_a_Patch> — the
  authoritative canonical guide. This skill operationalises it.
- Wiki: <https://wiki.postgresql.org/wiki/CommitFest> — commitfest
  process, schedule, status semantics.
- Wiki: <https://wiki.postgresql.org/wiki/Working_with_Git>.
- Wiki: <https://wiki.postgresql.org/wiki/Creating_Clean_Patches>.
- Wiki: <https://wiki.postgresql.org/wiki/Mailing_Lists> for list
  etiquette and the `https://postgr.es/m/` redirector.
- Wiki: <https://wiki.postgresql.org/wiki/Todo> — out-of-tree TODO.
- <https://commitfest.postgresql.org/> — the live commitfest.
- <https://cirrus.ci.postgresql.org/> — cf-bot CI status.
- <https://buildfarm.postgresql.org/cgi-bin/show_status.pl> —
  post-commit buildfarm.
- <https://www.postgresql.org/list/pgsql-hackers/> — searchable
  archive.
- Cross-reference: `community/conventions/git-workflow.md`.
- Cross-reference: `community/conventions/creating-clean-patches.md`.
- Cross-reference: `community/conventions/commit-message-format.md`.
- Cross-reference: `community/conventions/pgindent.md`.
- Cross-reference: `community/conventions/whitespace-and-encoding.md`.
- Cross-reference: `community/conventions/code-comments.md`.
- Cross-reference: `community/conventions/committing-checklist.md`
  for the checklist a committer applies after this skill ends.
- Cross-reference: `generic/workflows/build-and-test.md`.
- Cross-reference: `generic/workflows/research-and-connect-dots.md`
  for the pre-submission topic research.
- Cross-reference: `community/voices/michael-paquier.md` § "Build
  system" for cf-bot Meson/autoconf parity failures.
- Cross-reference: `community/voices/robert-haas.md` § "Concurrent
  development is hard" for stalemate dynamics.
