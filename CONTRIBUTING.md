# Contributing

This is a **shared community resource**, dedicated to the public domain under
[CC0-1.0](LICENSE). Corrections, additions, removals, and arguments are all
welcome — from anyone.

## Open an issue

Found a wrong rule, a missing topic, or just have a question?
<https://github.com/gburd/postgres-agent-skills/issues/new>

## Open a pull request

1. Fork the repo.
2. Branch from the **agent branch** you target (`claude`, `kiro`, `pi`,
   `codex`, `maki`, `hermes`, `other`). Shared content (`community/`,
   `generic/`, `examples/`, and the shared skills) is edited on one branch and
   the maintainer cherry-picks it across the others.
3. Make the change. For a `postgres-best-practices` rule:
   - one rule per file, `references/{prefix}-{name}.md`;
   - follow `references/_template.md`;
   - name the antipattern, show the fix in **runnable SQL**;
   - cite a canonical reference — prefer `postgresql.org/docs/current/…`;
     the project wiki is fine when the manual doesn't cover it (ideas only, no
     copied text);
   - keep it CC0: write original words, do not paste copyrighted or copyleft
     text from blogs, books, or the wiki.
   - add the rule to `references/_sections.md`.
4. Run the catalog generator to confirm it still parses:
   `python3 tools/build-catalog.py /tmp/out && echo ok`.
5. Open the PR: <https://github.com/gburd/postgres-agent-skills/pulls>.

## Source of truth

The canonical home is Codeberg: <https://codeberg.org/ddx/skills>. GitHub is a
mirror, but issues and PRs on either are read.

## License

By contributing, you agree your contribution is dedicated to the public domain
under CC0-1.0. No attribution is required (though it is appreciated).
