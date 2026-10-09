# Workflow

The order of operations for making a change.

## Before committing

1. Re-read your own diff for unnecessary complexity, redundant code, and
   unclear naming.
2. Run the relevant tests (the subset that covers your change, not always the
   whole suite).
3. Run the linter and type checker; fix everything before committing.

## Commits

- Imperative subject, one logical change per commit, short subject line. The
  message shape and register are in `prose-mechanics.md`; project-specific
  formats (PostgreSQL has its own) take precedence.
- The message stands alone and carries what the diff cannot: why the change is
  needed, caveats and how they are handled, alternatives considered and why
  they lost, and work deliberately deferred.
- Never amend or rebase commits already pushed to a shared branch.
- Never push directly to `main`; use feature branches and PRs.
- Never commit secrets or credentials. Stage explicitly by path (see
  `must-rules.md`).

## Git safety

- Never delete a `.git` directory or rewrite published history.
- Never force-push unless explicitly authorized for this push.
- Prefer non-interactive, non-paginated git invocations in scripts so a command
  does not block on a pager or an editor.
- Use a recoverable delete, never a recursive force-delete.

## Pull requests

Describe what the code does now, not the discarded approaches or prior
iterations. Keep the register plain and factual (see `opinions.md`).

## Progress heartbeat

Before a stretch of silent tool work (deep reads, subagent dispatch, builds,
long CI watches), emit one short line saying what you are about to do and a
rough ETA, so a remote or mobile session shows a heartbeat rather than going
dark.

## Planning artifacts

Plans, specs, and design notes are working files, not user-facing docs. Keep
them out of a `docs/` tree (that is for shipped documentation). Put them in a
gitignored working location (for example `.plans/` or `.agent/`), and never
commit them unless the human asks.
