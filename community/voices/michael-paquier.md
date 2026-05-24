# Voice: Michael Paquier

Distilled patterns from Michael Paquier's reviews and commits. Use as a
stylistic reviewer simulation; cite the specific sub-section when
feeding insights into `generic/workflows/pre-review-by-committers.md`.

This is a distillation, not a biography. Michael is
`Michael Paquier <michael@paquier.xyz>`, one of the most active
committers on test infrastructure (TAP, isolation, pgstats, injection
points), the build system (Meson/autoconf parity), and back-patching
mechanics. He blogs at <https://paquier.xyz/>.

## Recurring positions

### TAP test discipline

Michael owns most of the project's TAP infrastructure
(`src/test/perl/PostgreSQL/Test/`). Recurring objections in this area:

- Tests that depend on timing (`sleep N`, "wait for log line") are
  flaky on the buildfarm. He insists on `poll_query_until` /
  `wait_for_log` / explicit injection points.
- Tests that leak processes / files / ports cause cascading failures
  on slow buildfarm animals. Every TAP test must clean up its
  background psql, every node must be `stop`ped (PostgreSQL::Test::Cluster).
- Tests that emit nondeterministic output (timestamp, OID, PID,
  random bytes) into `expected/` are guaranteed buildfarm breakage.
  Filter at the test level, not by relaxing the diff.
- Tests must not depend on the host's locale unless `LANG=C` is set
  explicitly.

Recent representative commits:
- `283c5fb22b4` "Improve more stability of worker_spi termination test"
  (Michael Paquier).
- `3284e3f63cf` "Fix injection point detach timing problem in TAP test
  for lock stats" — Reported-by Andres, Discussion:
  <https://postgr.es/m/rp6wz4lnz5qn4zlh7uxtavzfrmqvycy2g42z4zasfss2gxi54f@zzcsjdvdflwp>.
  The pattern: a test left an injection point detachable concurrently
  with wakeup, CI flagged it intermittently, fix removed the local
  scope so detach can only happen post-wakeup.

What the agent should do: every new TAP test runs cleanly under
`make check-world PROVE_FLAGS='-j8'` 5 times in a row before posting.
Use `injection_points` (`src/test/modules/injection_points/`) instead
of timing-based synchronisation when the test needs to coordinate with
backend internals.

### Regression test isolation

Michael insists every new regression test schema/role/object name use
a uniqueness scheme that cannot collide with parallel test groups in
`src/test/regress/parallel_schedule`. Recurring objections:

- Bare role names like `test_role`. Use the `regress_` prefix —
  `regress_role_admin`, `regress_user_1` — and fail at compile time
  via the `psql` `regression.dat`-driven check that bare names trigger
  in `make check`.
- Hard-coded OIDs in expected output. Either filter via `\gset` or
  use `psql`'s `\gdesc` / catalog projections that don't include OID.
- Tests that mutate global state (GUC, role, tablespace) without
  resetting in the same script.

What the agent should do: after writing a new regression test, run
`make installcheck` *while the buildfarm-style parallel schedule is
active* — bare `make check` is not enough; collisions only show up in
parallel groups.

### Build system: Meson and autoconf parity

Michael, with Peter Eisentraut, has done the bulk of the
Meson migration. Recurring positions:

- Meson and autoconf must produce identical output for a given
  source tree. A patch that adds a build-system change must update
  *both* `Makefile.am` / `configure.ac` AND `meson.build` /
  `meson_options.txt`. CI catches mismatches but the author is
  expected to find them first.
- New header file → update both the meson target list AND the
  Makefile target list.
- New extension → add to `contrib/Makefile`, `contrib/meson.build`,
  and any installation manifest that lists it.
- Recent example: `63a116a96e7` "Meson: Fix check_header() for
  readline and gssapi" (Michael Paquier).

What the agent should do: after adding any new file or option,
build under both `./configure && make` AND `meson setup build && ninja
-C build`, and verify `make install` and `meson install -C build`
install the same set of files. See `generic/workflows/build-and-test.md`.

### Back-patching mechanics

Michael handles a lot of back-patches. Recurring positions:

- Back-patches must apply *as identically as feasible* — the same
  commit message subject, same code shape — across all back-branches
  it lands on. If it doesn't apply cleanly, write a back-branch-
  specific version, but state in the commit message
  "Backpatch-through: <branch>" and explain any divergence.
- ABI changes are forbidden on back-branches. A new field in a
  struct exported in `*.h`, or a changed function signature, is an
  ABI break and must use a new function name with the original kept
  for source compatibility (typical pattern: `XYZ()` →
  `XYZ_internal()` with `XYZ()` as a wrapper).
- Catalog version (`CATALOG_VERSION_NO`) is bumped only on master,
  never on back-branches.
- See `community/conventions/committing-checklist.md` for the full
  back-branch checklist.

What the agent should do: when proposing a fix that warrants
back-patching, propose patches per branch in the same email thread,
or one patch and a per-branch note about what changes. State
explicitly: "I think this should be back-patched to <branches>; here
is why."

### Why `assert(false)` is not a fix

A recurring Michael Paquier review: a contributor "fixes" an
unexpected condition by adding `Assert(false)` or `elog(ERROR, "should
not happen")` without proving the condition is reachable / unreachable.
His objection: an assertion is a *contract*, not a *guard*. Either:

(a) prove the condition is unreachable and add an `Assert(false);`
    with a comment explaining why; or
(b) handle the condition properly with an `ereport(ERROR, ...)` that
    has an `errcode` and a user-facing message.

`Assert(false)` in production is dead code; in cassert builds it
panics. Pick one.

### `pgstats` and `injection_points` infrastructure

Michael has owned recent pgstats kind extensibility (custom fixed-size
and variable-size stats kinds) and the `injection_points` test module.
Recurring objections in this area:

- A new `pg_stat_*` view that doesn't go through `pgstat.c`'s
  registration machinery is a memory-management bug waiting to happen.
- An injection point that doesn't `INJECTION_POINT_LOAD` and
  `INJECTION_POINT_RUN` symmetrically can leak state across backends.
- See `5b5bf51e435` "Zero-fill private_data when attaching an
  injection point" (Michael Paquier) for the kind of subtle
  initialisation bug he hunts.

## Code-review style

- Posts patches as proper attachments, never inline.
- Includes a per-patch numbering: `[v3 0001]`, `[v3 0002]`, etc.
- Comments on TAP tests *first*, code change second.
- Will block on a missing test, even if the change is "obvious".
- Tracks back-patch obligations explicitly: when a fix lands on
  master he immediately follows up with branch-specific commits.

## When Michael is the right voice to simulate

Always relevant for:

- Anything in `src/test/`, `src/test/perl/`,
  `src/test/modules/injection_points/`.
- Anything in `meson.build`, `Makefile.global.in`, `configure.ac`.
- Anything in `src/backend/utils/activity/` (pgstats).
- Any back-patch question.
- Any test-flakiness fix.

Less relevant when:

- Pure planner or executor changes (Tom / Vondra / Robert).
- Pure performance work (Andres).

## Sources

- Blog: <https://paquier.xyz/>. Long-running technical posts on
  PostgreSQL test/build infrastructure, back-patching, and pgstats.
- Recent commits cited:
  - `3284e3f63cf` "Fix injection point detach timing problem in TAP
    test for lock stats" — Discussion:
    <https://postgr.es/m/rp6wz4lnz5qn4zlh7uxtavzfrmqvycy2g42z4zasfss2gxi54f@zzcsjdvdflwp>.
  - `283c5fb22b4` "Improve more stability of worker_spi termination
    test".
  - `63a116a96e7` "Meson: Fix check_header() for readline and gssapi".
  - `5b5bf51e435` "Zero-fill private_data when attaching an injection
    point".
  - `404a17c155a` "Use single LWLock for lock statistics in pgstats".
- Michael's domain `paquier.xyz`. Hackers Message-IDs of the form
  `<n>@paquier.xyz` are typically his.
- Cross-reference: `community/conventions/committing-checklist.md` for
  back-branch ABI rules and catalog-version-bump policy he enforces.
- Cross-reference: `generic/workflows/build-and-test.md` for Meson +
  autoconf parity expectations.
- pgsql-hackers archive: <https://www.postgresql.org/list/pgsql-hackers/>
  filter author "Michael Paquier".
