# From "ready for committer" to committed: closing the gap

A patch marked **Ready for Committer** (RfC) is not a patch that will be
committed soon, or at all. There is a real, well-understood gap between
"the author/reviewer thinks it's done" and "a committer pushed it." This
skill explains *why* the gap exists and *what actually changes* in that
window, so an author (or an agent acting for one) can shorten it instead
of waiting in confusion.

Cross-refs: `community/decision-making.md` (champion model),
`community/communication-norms.md` (silence semantics),
`community/review-standards.md` (the final review bar),
`community/conventions/committing-checklist.md` (what the committer runs).

## Why a "ready" patch still waits

1. **No committer has adopted it.** RfC means a *reviewer* is satisfied.
   Commit requires a *committer* who will (a) personally re-review, (b)
   push it, and (c) be accountable for any fallout. With ~30 active
   committers, a patch with no committer champion simply waits. This is
   the single most common cause. *Action:* make the patch trivially
   adoptable (see below), and — politely, on-thread — make the ask
   ("this is RfC; is any committer interested in taking it?").
2. **Committer bandwidth / timing.** Silence after RfC usually means
   "they'll get to it," not rejection. Reviews and commits speed up
   during a commitfest and slow down in holiday months and near
   release-team milestones.
3. **The committer's own re-review finds something.** Committers do not
   rubber-stamp an RfC; they re-review and routinely construct
   adversarial cases (grammar edge cases, NULLs, polymorphic types,
   concurrency races, back-compat, pg_upgrade). Anything they find sends
   it back to Waiting on Author.
4. **Feature-freeze / branch timing.** Catalog changes (catversion) can
   only land before feature freeze; large features parked near a freeze
   wait for the next cycle. Bug fixes get back-patched; new features
   never go to stable branches.
5. **A dormant objection resurfaces.** Consensus means *no sustained
   committer objection*. An objection raised earlier and never truly
   resolved can reappear at commit time and block it. The
   "extension-first" question ("does this even belong in core?") is a
   common late resurfacer.
6. **CI isn't actually green.** If cfbot is red on any platform, or the
   patch no longer applies to `master`, no committer will touch it until
   it's green and rebased.

## What actually changes between RfC and the push

Expect the committer to do these at commit time — which tells you what
*not* to over-invest in beforehand, and what to make easy:

- **Rebase to current `master`** and confirm cfbot is green on every
  platform. *Your job:* keep it applying and green; rebase promptly when
  it drifts.
- **Set `CATALOG_VERSION_NO`.** The committer bumps catversion at push.
  *Your job:* do **not** ship a concrete bump in your posted patch (it
  guarantees rebase conflicts); note that one is needed. See
  `community/conventions/committing-checklist.md` and the `postgres/developer`
  skill § "patch-series discipline" (catversion/typedefs).
- **Run `pgindent` and finalize whitespace/format.** *Your job:* run it
  yourself so there's nothing to fix, and make sure any new type is in
  `typedefs.list` in the same commit.
- **Rewrite the commit message and trailers.** Committers routinely
  reword the message and set `Author:`, `Reviewed-by:`, `Discussion:`,
  and `Backpatch-through:` trailers. *Your job:* provide a clean,
  imperative, why-focused message and the discussion link; don't be
  precious about exact wording — it will change.
- **Minor cosmetic polish.** Comment wording, error-message style, a
  variable rename. *Your job:* get it close, but don't burn cycles
  gold-plating cosmetics the committer will redo anyway.
- **Occasionally split or reorder** the series for cleaner history.

## How to shorten the gap (author checklist)

- Keep the patch **focused**; out-of-scope changes go to their own
  thread (see `community/conventions/creating-clean-patches.md`).
- Keep it **applying to master and cfbot-green**; rebase on drift.
- Make it **trivially committable**: run the full committing checklist
  yourself *except* the catversion bump; leave that to the committer.
- **Address the last review comment concretely**, or say why you didn't.
- **Answer the necessity question up front** ("why core, not an
  extension?") so it can't resurface late.
- **Ping gently** after a couple of weeks; name the ask ("RfC since
  <date>; happy to address anything before a committer picks it up").
- Accept that **committed is not released** — even after the push, it
  can be reverted before GA. Watch the buildfarm after commit.

The through-line: a committer's scarcest resource is attention and
accountability. The patches that cross the gap fastest are the ones that
ask the least of the committer at the moment they look at it.
