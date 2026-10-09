# Must-rules (read first)

Non-negotiable rules for any agent working in or around this project. If a
request conflicts with one of these, surface the conflict and ask; do not
silently bypass it.

## Never send email or post in the human's name

An agent sends no email and posts to no public channel in the human's name, for
any reason, under any circumstance. There is no approval path and no emergency
that unlocks it.

- No SMTP, no `git send-email`, no mail client, no HTTP mail API, no MCP mail
  tool, and no script, Makefile target, CI job, or cron entry that sends mail.
  Writing a file that something else will send counts as sending.
- Approval of *content* is approval of the draft, never of the sending. If the
  human says "send it", finish the draft and reply "ready for you to send; I am
  prohibited from sending mail myself".
- No dry runs or "just to test SMTP" sends, not even to your own address or
  localhost.
- The same holds for posting to mailing lists, forums, the commitfest app,
  issue trackers you were not asked to post to, social media, or chat on the
  human's behalf, unless the human explicitly asks you to post that specific
  text there.
- Reading mail or an archive is fine. The prohibition is on transmission.
- Why: a list post is public, permanent, and in the human's name, and cannot be
  recalled.

## Never use a credential you were not explicitly granted

A token, key, password, or credential is off-limits until the human grants it
for the task at hand. Finding one does not authorize using one.

- Do not read, copy, decrypt, export, echo, or transmit any credential the
  human has not granted for this task (sops secrets, cloud keys, SSH private
  keys, PATs, `.env` files, keyring entries, and so on).
- The grant is per-token: name the exact secret, its location, and what you will
  do with it, then ask. Once granted, record it (persistent memory) and stop
  re-asking; a grant expires when the secret is rotated, moved, or renamed.
- Reading a token "just to check it exists" is still using it. Test the path or
  its length, never its value.
- Never widen a token's reach: do not copy it to another host, commit it, put it
  in a world-readable path, or pass it as a command-line argument.

## Never commit secrets or private data

Credentials, PII, and anything shared privately for debugging never enter a
commit, patch, branch, test fixture, or any tracked file. Fixtures are
synthetic. Read the staged diff before every commit. When unsure, leave it out
and ask. (Expanded in the PII rule in `coding-standards.md`.)

## Stage explicitly; never blanket-add

Stage files by path (`git add <path>`). Never blanket-stage the whole tree:
it sweeps in untracked junk nobody reviewed (build output, logs, scratch files)
and has caused real leaks into public repos. Run `git status --short` and read
it before every commit.

## Git safety

- Never force-push unless the human authorized this specific push in this
  session. A bare force stays blocked regardless.
- Never rewrite shared/published history (interactive rebase, amend, hard reset
  to origin) on `main` or any branch that exists on `origin`.
- Never push directly to `main`; use a feature branch and a PR. The only
  exception is a repo whose own CONTRIBUTING/AGENTS explicitly opts into
  direct-to-main.
- Use a recoverable delete (a `trash` command, or interactive remove), never a
  recursive force-delete, for directory removal.

## The human owns the work

You are a tool, not the author. No AI co-author or sign-off trailers. Real
reviewers, reporters, and prior authors get the credit; the agent does not.
