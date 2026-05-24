# Voices index

The named voices in `community/voices/` are stylistic distillations of
specific PostgreSQL committers' recurring review patterns. Each is a
checklist for `generic/workflows/pre-review-by-committers.md`, not a
biography. Cite a voice file by its sub-section, not as a whole.

## Voices with their own files

- `tom-lane.md` — planner correctness, type system, grammar.y, "don't
  reformat unrelated code", "preserve git history", documentation
  parity, root-cause-not-symptom commit messages.
- `andres-freund.md` — performance methodology (the 9 pitfalls from
  PGConf.dev 2026 "Profiling Postgres Perils"), lock-free / atomics
  discipline, hot-path inlining, async I/O (`io_uring`), NUMA
  awareness, `pg_test_timing`.
- `tomas-vondra.md` — extended statistics, partition pruning,
  parallel-query costing, performance cliffs, "benchmarking is hard
  sometimes" methodology, EXPLAIN visibility for new behaviour.
- `michael-paquier.md` — TAP test discipline, regression test
  isolation, Meson + autoconf parity, back-patching mechanics, "why
  `assert(false)` is not a fix", pgstats and injection_points
  infrastructure.
- `robert-haas.md` — parallel query and DSM, project-process / "what
  the project values" / commitfest cycle commentary, EXPLAIN
  extension, backwards compatibility, comprehensive commit messages.

## Voices integrated as cross-references (no separate file)

The committers below are referenced from inside the five files above
and from the conventions/* and workflows/* skills. Their recurring
patterns are documented in-line at the point of use rather than
duplicated into separate files. This keeps the simulation budget
focused on the five highest-coverage voices.

### Heikki Linnakangas (`heikki@iki.fi`)

Areas: WAL, MVCC, snapshot management, recovery, logical/streaming
replication, slot lifecycle, GiST.

Recurring patterns the agent should look up at point of use:

- WAL record format changes require XLOG version bump and a
  back-compat story.
- `RmgrDescData` and `XLOG_*` redo functions must be kept in sync —
  every new WAL record gets a `*_desc.c` entry.
- Replication slots are persistent state: dropping one is a
  protocol-level operation, not a catalog DELETE.
- GiST: leaf vs. internal page handling and `gistGetFakeLSN` patterns
  (cross-reference commit `b1f14c96720`).

Where cross-referenced:

- `community/voices/andres-freund.md` § "Async I/O and io_uring" — Heikki
  contributes recovery-side AIO review.
- `community/voices/tomas-vondra.md` § "Performance cliffs > average
  performance" — recovery-side cliffs.
- `community/conventions/committing-checklist.md` § "WAL/catversion".

For real-time review patterns, search the pgsql-hackers archive for
"Heikki Linnakangas" as author:
<https://www.postgresql.org/list/pgsql-hackers/>.

### Bruce Momjian (`bruce@momjian.us`)

Areas: release management, design overview, doc / commit-message
authorship, the historical "TODO list" on the wiki, project history.

Recurring patterns the agent should look up at point of use:

- Release notes (`doc/src/sgml/release-*.sgml`) are written by Bruce;
  patch authors writing user-visible changes should expect Bruce to
  rewrite their proposed release-note text.
- The wiki TODO list (<https://wiki.postgresql.org/wiki/Todo>) is the
  closest thing to a project roadmap — but it is curated, not
  authoritative; new entries land via -hackers consensus.
- Design overviews and educational tutorials in `doc/src/sgml/` are
  often Bruce's; consistency with the existing overview language
  matters.

Where cross-referenced:

- `community/conventions/commit-message-format.md` § "Bruce-style
  release-note language".
- `generic/workflows/submit-patch.md` § "What goes in release notes".

For real-time review patterns, search the pgsql-hackers archive for
"Bruce Momjian":
<https://www.postgresql.org/list/pgsql-hackers/>.

### Peter Eisentraut (`peter@eisentraut.org`)

Areas: build system (Meson migration with Michael Paquier), locale
and ICU, libpq internals, SQL standard conformance, NLS / `gettext`,
documentation toolchain.

Recurring patterns the agent should look up at point of use:

- Meson migration parity: see `community/voices/michael-paquier.md`
  § "Build system: Meson and autoconf parity".
- Locale: do not assume the C locale is available with full collation
  semantics on all platforms; ICU is the project-preferred path for
  collation correctness on PG 16+.
- libpq protocol changes require a protocol version bump *and* a
  graceful-degradation path for older clients.
- SQL standard: when a feature exists in the standard, the project
  prefers the standard's spelling. Departures must be justified.
- `make world` / `make docs` toolchain changes (DocBook XSL, dblatex)
  go through Peter.

Where cross-referenced:

- `community/voices/michael-paquier.md` § "Build system".
- `community/conventions/whitespace-and-encoding.md` § "ASCII-only in
  source/commits".
- `generic/workflows/build-and-test.md` § "Meson vs. autoconf",
  § "DocBook conventions".

For real-time review patterns, search the pgsql-hackers archive for
"Peter Eisentraut":
<https://www.postgresql.org/list/pgsql-hackers/>.

## Other committers (not given dedicated cross-reference sections)

Active committers whose review patterns are not separately
distilled in this index but who appear regularly on -hackers:
Álvaro Herrera, Amit Kapila, Amit Langote, Daniel Gustafsson, David
Rowley, Dean Rasheed, Etsuro Fujita, Fujii Masao, Heikki (above),
Jeff Davis, John Naylor, Magnus Hagander, Masahiko Sawada, Melanie
Plageman, Nathan Bossart, Noah Misch, Peter Geoghegan, Stephen Frost,
Thomas Munro.

When pre-reviewing a patch in their primary area, search the
pgsql-hackers archive for their name + the specific subsystem:
e.g. for a vacuum patch, search "Peter Geoghegan vacuum"; for a
parallel-aggregate patch, "David Rowley parallel".

## Sources

- This index was constructed from the action-skill
  `generic/workflows/pre-review-by-committers.md` § "Select 3+ voices
  to simulate", which lists the 8 voice files this skillset covers
  with file or anchor pointers.
- Committer email addresses verifiable from `git log --format='%aN
  <%aE>'` on a fresh clone of `git.postgresql.org/postgresql.git`.
- Cross-reference: `community/voices/{tom-lane,andres-freund,tomas-
  vondra,michael-paquier,robert-haas}.md`.
- Live archive: <https://www.postgresql.org/list/pgsql-hackers/>.
