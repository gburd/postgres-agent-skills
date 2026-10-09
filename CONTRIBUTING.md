# Contributing

This is a **shared community resource**, dedicated to the public domain under
[CC0-1.0](LICENSE). Corrections, additions, removals, and arguments are all
welcome — from anyone.

## Open an issue

Found a wrong rule, a missing topic, or just have a question?
<https://github.com/gburd/postgres-agent-skills/issues/new>

## Open a pull request

1. Fork the repo.
2. Make the change on `main`. Skills are written **once for every agent** (the
   Agent Skills Open Standard, `<collection>/<skill>/SKILL.md` with YAML front
   matter) — there are no per-agent branches.
3. Place it in the right collection:
   - a Postgres role skill → `postgres/<persona>/SKILL.md`;
   - a shared best-practice rule → `postgres/best-practices/references/{prefix}-{name}.md`;
   - a tool-integration skill → `tooling/<name>/SKILL.md`;
   - a generic agent habit → `ai-life-skills/<name>/SKILL.md`.
4. For a `postgres/best-practices` rule:
   - one rule per file; follow `postgres/best-practices/references/_template.md`;
   - name the antipattern, show the fix in **runnable SQL**;
   - cite a canonical reference — prefer `postgresql.org/docs/current/…`; the
     project wiki is fine when the manual doesn't cover it (ideas only, no
     copied text);
   - keep it CC0: write original words, do not paste copyrighted or copyleft
     text from blogs, books, or the wiki;
   - add the rule to `postgres/best-practices/references/_sections.md`.
5. Keep `SKILL.md` uppercase — it is the Agent Skills Open Standard filename
   that every agent globs for; do not rename it.
6. Run the catalog generator to confirm it still parses:
   `python3 tools/build-catalog.py /tmp/out && echo ok`.
7. Open the PR: <https://github.com/gburd/postgres-agent-skills/pulls>.

## Source of truth

The canonical home is Codeberg: <https://codeberg.org/ddx/skills>. GitHub is a
mirror, but issues and PRs on either are read.

## License

By contributing, you agree your contribution is dedicated to the public domain
under CC0-1.0. No attribution is required (though it is appreciated).
