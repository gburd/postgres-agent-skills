# Workflow: Package and ship a PostgreSQL extension

A working `.so` on your machine is not a release. Shipping means a buildable
source tree, tests that prove install *and* upgrade work, CI across the
PostgreSQL majors you claim to support, and a path for users to install without
reading your Makefile.

## Inputs

- `extension_path`: the working extension tree (control file, SQL scripts,
  and C sources if any) to package.
- `pg_majors`: the PostgreSQL major versions you intend to support (drives
  the CI matrix in step 4).

## Steps

### 1. Lay out the tree conventionally

A conventional PGXS/PGXN-friendly tree:

```
my_extension/
  Makefile                      # PGXS (see extension-conventions)
  my_extension.control
  my_extension--1.0.sql
  my_extension--1.0--1.1.sql
  my_extension--1.1.sql
  src/                          # C sources, if any
  sql/                          # pg_regress input scripts
  expected/                     # pg_regress expected output
  test/                         # TAP tests, if any
  doc/
  META.json                     # PGXN metadata
  LICENSE
  README.md
```

### 2. Write regression tests, including the upgrade path

Drive tests with `pg_regress` through PGXS. `REGRESS = basic upgrade` in the
Makefile runs `sql/basic.sql` and `sql/upgrade.sql`, diffing stdout against
`expected/<name>.out`. A test *is* a `.sql` input plus its expected output; a
diff is a failure.

```bash
make
make install
make installcheck PGUSER=postgres        # runs against a running server
```

Test the upgrade path explicitly — it is the most common thing a release
breaks. One regression script should install the old version and update:

```sql
CREATE EXTENSION my_extension VERSION '1.0';
-- exercise 1.0 behaviour, create objects
ALTER EXTENSION my_extension UPDATE TO '1.1';
-- confirm the upgrade script migrated everything correctly
```

### 3. Guard version-specific C with `PG_VERSION_NUM`

Server internals change between majors. Guard C that touches moved APIs with the
version macro from `pg_config.h`:

```c
#if PG_VERSION_NUM >= 160000
    /* 16+ signature */
#else
    /* pre-16 */
#endif
```

Keep the SQL scripts version-agnostic where possible. Decide and document the
oldest major you support; CI (next step) is what proves the claim rather than
hope.

### 4. Build a CI matrix across supported majors

Build, install, and `installcheck` on every major you support, on each push. A
GitHub Actions matrix is the common shape:

```yaml
strategy:
  matrix:
    pg: [13, 14, 15, 16, 17]
steps:
  - uses: actions/checkout@v4
  - run: |
      sudo apt-get update
      sudo apt-get install -y postgresql-${{ matrix.pg }} \
                              postgresql-server-dev-${{ matrix.pg }}
  - run: make PG_CONFIG=/usr/lib/postgresql/${{ matrix.pg }}/bin/pg_config
  - run: sudo make install PG_CONFIG=/usr/lib/postgresql/${{ matrix.pg }}/bin/pg_config
  - run: make installcheck PG_CONFIG=/usr/lib/postgresql/${{ matrix.pg }}/bin/pg_config
```

If `installcheck` fails, read `regression.diffs` in the build dir — it holds the
expected-vs-actual diff for the failing script.

### 5. Mark trusted extensions deliberately (PG13+)

By default `CREATE EXTENSION` requires superuser. If your extension is safe for
a non-superuser database owner to install — no filesystem access, no arbitrary
C that escapes the SQL sandbox's guarantees — mark it trusted in the control
file:

```
trusted = true
```

A role with `CREATE` privilege on the database can then install it. Only mark
trusted what genuinely cannot escalate privilege; a trusted extension that
exposes `SECURITY DEFINER` footguns or raw filesystem access is a vulnerability.
When unsure, leave it superuser-only.

### 6. Write PGXN metadata

`META.json` describes the distribution for the PGXN index and client:

```json
{
  "name": "my_extension",
  "abstract": "Does one useful thing",
  "version": "1.1.0",
  "maintainer": "Jane Doe <jane.doe@example.com>",
  "license": "postgresql",
  "provides": {
    "my_extension": {
      "file": "my_extension--1.1.sql",
      "version": "1.1.0"
    }
  },
  "meta-spec": { "version": "1.0.0" }
}
```

### 7. Cut a release tarball

Ship a versioned source tarball whose top directory matches the name and
version, so PGXN and package maintainers can unpack predictably:

```bash
git archive --format=tar.gz --prefix=my_extension-1.1.0/ \
    -o my_extension-1.1.0.tar.gz v1.1.0
```

Include `LICENSE`, a `README`/`doc/` that documents every public function and
GUC, and a changelog noting the upgrade steps for each version.

## Outputs

A release a user can install by one of three equivalent paths — all end in the
same server-side `CREATE EXTENSION`:

- **PGXN client**: `pgxn install my_extension` then, in a database,
  `CREATE EXTENSION my_extension;`.
- **OS packages**: distribution or PGDG packages drop the control file, SQL
  scripts, and `.so` into the server's directories; the user then runs
  `CREATE EXTENSION`.
- **From source**: `make && sudo make install && psql -c 'CREATE EXTENSION
  my_extension'`.

## See also

`generic/workflows/write-an-extension.md`,
`community/conventions/extension-conventions.md`,
`generic/workflows/build-and-test.md`,
`postgres/overseer/SKILL.md` § "Judging extensions (gatekeep hard)",
`postgres/best-practices/references/ops-extension-upgrades.md`,
<https://www.postgresql.org/docs/current/extend-pgxs.html>,
<https://www.postgresql.org/docs/current/sql-createextension.html>,
<https://www.postgresql.org/docs/current/regress.html>,
<https://pgxn.org/spec/>,
<https://manager.pgxn.org/howto>.
