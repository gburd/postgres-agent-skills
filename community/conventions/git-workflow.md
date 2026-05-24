# Git workflow

How to clone, branch, develop, and post patches to PostgreSQL using the
project's git conventions. The mechanical commands matter; so does the
social rule that you never rewrite shared history.

## TL;DR — what the agent must do

```sh
git clone https://git.postgresql.org/git/postgresql.git
cd postgresql
git remote set-url --push origin DISABLED          # never push to origin
git config branch.autoSetupRebase always
git config blame.ignoreRevsFile .git-blame-ignore-revs
git checkout -b my-feature                          # branch per feature
# ... hack ...
git rebase -i origin/master                         # squash style fixes
src/tools/pgindent/pgindent <changed-files>
git diff --check
git format-patch --cover-letter -v1 -B -M origin/master..HEAD
```

Send the resulting `.patch` files to `pgsql-hackers@lists.postgresql.org`.
Then register the entry on commitfest.postgresql.org.

## Canonical clones

The project hosts at `git.postgresql.org`; GitHub
`github.com/postgres/postgres` is a read-only mirror.

```sh
# anonymous read-only (preferred for agents)
git clone https://git.postgresql.org/git/postgresql.git

# committer push (you don't have this; included for symmetry)
git clone ssh://git@git.postgresql.org/postgresql.git
```

The mirror is:

- `https://github.com/postgres/postgres` — read-only, lags master by
  a small number of seconds.

PRs against the GitHub mirror are *ignored*. The project does not
take pull requests; everything goes via -hackers.

To prevent accidentally pushing to the read-only origin (or to a
fork that is not where patches go):

```sh
git remote set-url --push origin DISABLED
```

## Branch names

There is no naming convention enforced by the project for *your*
local branches; use whatever you like. The only rule: do not push
your local branches to a remote that other contributors read, except
your personal fork.

The project's *upstream* branches are:

- `master` — current development.
- `REL_NN_STABLE` — back-branches for supported releases. As of
  mid-2026, `REL_18_STABLE`, `REL_17_STABLE`, etc.
- Tags `REL_NN_M` — releases (e.g. `REL_18_0`, `REL_18_1`).

Do not branch from `REL_NN_STABLE` for new features. New features go
on `master`; back-patches happen *after* commit, by the committer.

## Local config the project expects

```sh
git config branch.autoSetupRebase always
git config pull.rebase true
git config rebase.autoSquash true
git config blame.ignoreRevsFile .git-blame-ignore-revs
git config core.autocrlf false
git config apply.whitespace error
git config core.whitespace 'tab-in-indent,trailing-space,cr-at-eol'
```

`blame.ignoreRevsFile .git-blame-ignore-revs` is load-bearing: the
project commits bulk pgindent / pgperltidy / reformat-dat-files
sweeps as their own commits, and the in-tree `.git-blame-ignore-revs`
lists those SHAs so `git blame` skips them. See
`community/conventions/pgindent.md` § "Release-cycle reformat".

## Branch-per-feature workflow

```sh
git fetch origin
git checkout -b my-feature origin/master

# ... hack hack hack ...
git add path/to/foo.c
git commit -m "..."

# Pull master changes by rebasing, never merging
git fetch origin
git rebase origin/master

# Stale conflicts? Resolve, then continue
git rebase --continue

# Polish before posting
git rebase -i origin/master           # squash style-fix commits
src/tools/pgindent/pgindent path/to/foo.c
git diff --check
```

The local feature branch is private. You will not push it anywhere
shared.

## Rebase-and-squash, not merge

The PostgreSQL git history is *linear* on `master`. There are no
merge commits introduced by feature work. Committers commit (push)
each accepted patch as one or more linear commits.

What this means for the agent:

- Never `git merge` master into your feature branch. Use `git rebase
  origin/master`.
- Never publish merge commits in your patch. `git format-patch` from
  a properly-rebased branch produces patch files; if the receiving
  committer cannot apply them with `git am`, you will be asked to
  resend.
- Squash WIP / "fix typo" / "address review" commits into the
  logical commit they belong to *before* posting. Use `git rebase -i
  origin/master` and `fixup` / `squash` as needed.

## Never force-push to shared refs

`git.postgresql.org`'s `master` and `REL_NN_STABLE` branches reject
force pushes; this is enforced server-side. But the social rule
extends to any branch other contributors are reading.

Forbidden:

```sh
git push --force origin master                    # rejected by server
git push --force origin REL_18_STABLE             # rejected by server
git push --force origin codereview-thread-12345   # social violation
```

Allowed (purely-local rebase):

```sh
git rebase -i origin/master            # rewrites your local feature
                                       # branch — fine, no one else
                                       # has it
```

If you have already shared a branch and need to revise, post a v2
patch series instead of force-pushing. See
`community/conventions/creating-clean-patches.md`.

## `git format-patch` for posting

The canonical command for the patch-author:

```sh
git format-patch --cover-letter -v1 -B -M origin/master..HEAD
```

Flags:

- `--cover-letter` — generate `0000-cover-letter.patch` for the
  series. Edit it; don't post the auto-generated `*** SUBJECT HERE ***`.
- `-v1` (or `-v2`, `-v3`...) — version label. Use `v1` first, bump
  on resubmits.
- `-B` — detect "complete rewrite" file changes (treat as
  delete+add).
- `-M` — detect renames as renames.

Output: `v1-0000-cover-letter.patch`, `v1-0001-...`, etc. Send all of
them to `pgsql-hackers@lists.postgresql.org` in a single thread,
reply-to the cover letter for each numbered patch (most modern MUAs
do this for you with `git send-email`).

## `git send-email` setup

```sh
git config sendemail.smtpserver smtp.example.com
git config sendemail.smtpuser   you@example.com
git config sendemail.smtpencryption tls
git config sendemail.smtpserverport 587

git send-email --to=pgsql-hackers@lists.postgresql.org \
               --annotate \
               v1-*.patch
```

`--annotate` opens each patch in `$EDITOR` so you can review the
final body before sending. Always use it.

## `.git/hooks/pre-commit` template

A minimal hook that catches the most common mistakes. Save as
`.git/hooks/pre-commit`, `chmod +x`:

```sh
#!/bin/sh
# pre-commit: project-style guards
set -e

# 1. Whitespace errors.
git diff --cached --check || {
    echo "Whitespace errors. See 'git diff --check'."
    exit 1
}

# 2. C-comment style.
if git diff --cached --name-only --diff-filter=ACM | grep -qE '\.[ch]$'; then
    files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.[ch]$')
    if echo "$files" | xargs grep -nE '^\+.*//[^/]' /dev/null 2>&1 | grep -v '://'; then
        echo "C++-style // comments not allowed in *.c/*.h."
        exit 1
    fi

# 3. pgindent on changed files.
    if [ -x src/tools/pgindent/pgindent ]; then
        src/tools/pgindent/pgindent --check $files || {
            echo "pgindent reports diffs. Run pgindent to fix."
            exit 1
        }
    fi
fi

# 4. Forbid known-bad markers.
git diff --cached -U0 | grep -E '^\+.*/\*\s*(HACK|BUG)\s*[: ]' && {
    echo "Project does not use HACK: or BUG: markers; use XXX or FIXME."
    exit 1
}

exit 0
```

Cross-reference: this hook implements the rules from
`community/conventions/pgindent.md`,
`community/conventions/whitespace-and-encoding.md`, and
`community/conventions/code-comments.md`.

## Updating an existing patch series (v2, v3, ...)

When you respond to review feedback:

1. Apply review comments to your branch (`git rebase -i` to fix the
   right commit, not pile a "review fixes" commit on top).
2. Re-run `pgindent`, `git diff --check`, `make check-world`.
3. Bump the version: `git format-patch --cover-letter -v2 -B -M
   origin/master..HEAD`.
4. Reply to the existing -hackers thread (do not start a new one).
   Attach the v2 patches.
5. Update the commitfest entry's "Latest attachment" if necessary.

The version bump is real: cf-bot uses the `v<N>` filename to deduplicate.

## Tracking what's on master

```sh
git fetch origin && git -P log --oneline origin/master.. HEAD
                                               # what you have on top
git -P log --oneline ..origin/master           # what master has on top
git -P log --oneline --since="1 week" origin/master
                                               # who committed what
git -P log --oneline --author="Tom Lane" origin/master
                                               # filter by committer
```

## Where to find canonical project state

- Source of truth: `git.postgresql.org` repository.
- Cross-reference for in-flight features: commitfest.postgresql.org.
- Buildfarm CI: `buildfarm.postgresql.org`.
- cf-bot CI: `cirrus.ci.postgresql.org` (the per-CF-entry status).

## Sources

- Wiki: <https://wiki.postgresql.org/wiki/Working_with_Git>. The
  authoritative document on cloning, branching, and the project's
  git social conventions.
- Wiki: <https://wiki.postgresql.org/wiki/Submitting_a_Patch>
  § "Producing the patch" — `git format-patch` flags and the
  cover-letter convention.
- Wiki: <https://wiki.postgresql.org/wiki/Creating_Clean_Patches>
  (Greg Smith) — the rebase-and-squash workflow and the "review
  your own diff" discipline.
- `src/tools/pgindent/pgindent` — invocation in pre-commit hook.
- `.git-blame-ignore-revs` (postgres tree) — header comment
  documents the file's purpose.
- `git-format-patch(1)`, `git-send-email(1)`, `git-am(1)` man pages.
- Cross-reference: `community/conventions/pgindent.md` for the
  formatter the hook calls.
- Cross-reference: `community/conventions/whitespace-and-encoding.md`
  for `git diff --check` rules.
- Cross-reference: `community/conventions/code-comments.md` for the
  marker-set the hook scans.
- Cross-reference: `community/conventions/creating-clean-patches.md`
  for the post-rebase polish step.
- Cross-reference: `community/conventions/commit-message-format.md`
  for the message-shape that `git format-patch` packages.
- Cross-reference: `generic/workflows/submit-patch.md` for the
  end-to-end author submission flow.
