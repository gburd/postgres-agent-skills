# PostgreSQL Review Standards

What PostgreSQL reviewers look for when evaluating patches. These standards have evolved over decades and are largely unwritten — learned by observing reviews rather than reading a document.

## The Review Hierarchy

Reviewers evaluate patches on multiple levels, roughly in this priority order:

### 1. Necessity (Does This Belong in Core?)

Before any code is reviewed, the fundamental question:
- Does this solve a real problem that enough people have?
- Can it be done as an extension instead?
- Does the benefit justify the eternal maintenance burden?
- Is the approach the right one, or should we solve the underlying problem differently?

A perfect implementation of an unnecessary feature will be rejected.

### 2. Correctness

- **Concurrency safety**: Does it handle concurrent access correctly? Are locks held at the right level and for the right duration?
- **Error handling**: Are all error paths correct? No leaked resources (memory, locks, file descriptors) on error?
- **NULL handling**: Does it handle NULL inputs correctly everywhere?
- **Edge cases**: Empty tables, zero rows, maximum values, boundary conditions?
- **Memory management**: Proper use of memory contexts? No leaks? No use-after-free?
- **Signal safety**: Can it be interrupted safely? Does it handle cancel/die correctly?

### 3. Backwards Compatibility

This is the strongest constraint in PostgreSQL:
- **Behavioral compatibility**: Existing queries must continue to produce the same results
- **Dump/restore**: Old dumps must load into new servers
- **pg_upgrade**: In-place upgrade must work
- **Replication**: Logical replication protocol must remain compatible
- **Client libraries**: libpq wire protocol backwards compatibility
- **Extensions**: Extension APIs should not change without deprecation

If a change breaks backwards compatibility, it needs extraordinary justification.

### 4. Catalog Changes (catversion)

Any change to system catalogs requires:
- Incrementing `CATALOG_VERSION_NO` in `src/include/catalog/catversion.h`
- Proper pg_upgrade support
- Documentation of the change
- This can only happen before feature freeze

### 5. Performance

- **No regression on common paths**: Even if the new feature is fast, it must not slow down existing workloads
- **Appropriate algorithms**: O(n^2) where O(n log n) is possible will be rejected
- **Memory efficiency**: No excessive allocation, proper use of palloc contexts
- **Lock contention**: Minimize time holding contended locks
- **Benchmarks expected**: For performance-sensitive code, provide pgbench results or similar

### 6. Code Quality

- **pgindent compliance**: Code must be formatted with pgindent/pg_bsd_indent
- **Naming conventions**: Follow existing naming patterns in the subsystem
- **Comments**: Explain WHY, not WHAT. Non-obvious algorithms need comments.
- **No dead code**: Don't leave commented-out code or unused functions
- **Minimal diff**: Don't refactor unrelated code in the same patch

### 7. Documentation

Required for any user-visible change:
- SGML/XML documentation in `doc/src/sgml/`
- Clear explanation for end users (not developers)
- Examples where appropriate
- Release notes entry

### 8. Testing

- **Regression tests**: Required for all behavioral changes
- **Isolation tests**: Required for concurrency-sensitive code
- **TAP tests**: For client-facing tools (pg_dump, pg_basebackup, etc.)
- **Tests must be deterministic**: No timing-dependent expected output
- **Error path testing**: Exercise error conditions, not just happy paths
- **Platform portability**: Tests must pass on all buildfarm members

## Common Reviewer Feedback

### Frequently Requested Changes

| Feedback | What It Means |
|----------|---------------|
| "This needs a catversion bump" | You changed catalogs without incrementing the version |
| "Run pgindent" | Formatting doesn't match project standards |
| "This breaks ABI" | You changed a public struct/function signature |
| "Missing regression test" | Can't commit without test coverage |
| "What about NULL?" | Didn't handle NULL case in your logic |
| "Please split this patch" | Too many changes in one commit |
| "Needs docs" | User-visible change without documentation |
| "This isn't back-patchable" | Fix is too invasive for stable branches |
| "What about pg_upgrade?" | Catalog change needs upgrade path |
| "Error message style" | Doesn't follow error message conventions |

### Error Message Conventions

PostgreSQL has specific rules for error messages:
- Primary message: Brief, starts with lowercase, no period at end
- Detail: Additional information, can be multi-sentence
- Hint: Suggested action for the user
- No "ERROR:" prefix (the system adds it)
- Use errmsg_internal() for messages not intended for translation
- Error codes must be appropriate (see `src/backend/utils/errcodes.txt`)

Example:
```c
ereport(ERROR,
    (errcode(ERRCODE_UNDEFINED_TABLE),
     errmsg("relation \"%s\" does not exist", relname),
     errhint("Check the schema search path.")));
```

## Review Etiquette (for Reviewers)

- Be specific: "this has a bug where X" not "this seems wrong"
- Suggest fixes, not just problems
- Distinguish between "must fix" and "nice to have"
- Acknowledge good work alongside criticism
- If you don't understand something, say so rather than approving blindly
- Review the design (is it the right approach?) before reviewing the code (is it implemented correctly?)
- One thorough review is better than five superficial ones
