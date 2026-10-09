# PostgreSQL C Coding Conventions

PostgreSQL's C coding standards, evolved over 30+ years. These are enforced in review and many are checked by automated tools (pgindent, pg_bsd_indent).

## Formatting

### Indentation
- Tabs for indentation, spaces for alignment (after the initial tabs)
- Tab width = 4 spaces (for display purposes)
- All code must pass through `pgindent` cleanly
- Run `src/tools/pgindent/pgindent` on your changes before submitting

### Braces
- Opening brace on same line for control structures:
```c
if (condition)
{
    body;
}
```
- Exception: function definitions have opening brace on its own line:
```c
FunctionName(args)
{
    body;
}
```

### Line Length
- No hard limit, but keep lines reasonable (~80 chars preferred)
- Function signatures that are too long get broken after the return type:
```c
static int
very_long_function_name(int arg1, int arg2,
                        int arg3)
{
```

## Naming Conventions

### Functions
- Lower case with underscores: `heap_insert`, `ExecInitNode`
- Subsystem prefix: `heap_*`, `index_*`, `ExecInit*`, `cost_*`
- Accessor functions: `Get*`, `Set*`
- Boolean functions: `Is*`, `Has*`, `Can*`
- Capitalized words for important subsystems: `ExecProcNode`, `RelationGetDescr`

### Variables
- Short, descriptive names: `rel`, `tuple`, `slot`, `plan`
- Common abbreviations: `rel` (relation), `tup` (tuple), `desc` (descriptor)
- Loop variables: `i`, `j`, `k` are fine
- Pointer variables: no Hungarian notation, no `p_` prefix

### Macros
- ALL_CAPS with underscores: `HEAP_XMAX_COMMITTED`, `PG_TRY`
- Macro arguments in parentheses: `#define FOO(x) ((x) + 1)`

### Types
- Capitalized with no underscores: `HeapTuple`, `Relation`, `PlanState`
- `Node` types end in node kind: `SeqScan`, `HashJoin`, `NestLoop`
- Struct tags match typedef: `typedef struct HeapTupleData { ... } HeapTupleData;`
- Pointer typedefs: `typedef HeapTupleData *HeapTuple;`

### Enums
- Values are ALL_CAPS: `CMD_SELECT`, `CMD_INSERT`

## Memory Management

### Memory Contexts
- Always allocate in the appropriate memory context
- Use `palloc` / `pfree`, never raw `malloc` / `free`
- Switch context before allocating long-lived data:
```c
oldcontext = MemoryContextSwitchTo(long_lived_context);
result = palloc(size);
MemoryContextSwitchTo(oldcontext);
```
- Clean up by destroying contexts, not individual pfrees (for bulk data)

### Common Patterns
```c
/* Allocate in current context */
ptr = palloc(sizeof(MyStruct));
ptr = palloc0(sizeof(MyStruct));  /* zero-filled */

/* String duplication */
str = pstrdup(original);

/* Array allocation */
arr = palloc(nelems * sizeof(Datum));
```

## Error Handling

### ereport Pattern
```c
ereport(ERROR,
    (errcode(ERRCODE_SOMETHING),
     errmsg("primary message: %s", detail),
     errdetail("Additional context."),
     errhint("Try doing this instead.")));
```

### Error Levels
- `DEBUG1-5`: Debug messages (higher = more verbose)
- `LOG`: Server log messages
- `INFO`: Informational messages to client
- `NOTICE`: Notices to client (non-fatal)
- `WARNING`: Warnings to client
- `ERROR`: Aborts current transaction (longjmp!)
- `FATAL`: Disconnects client
- `PANIC`: Crashes the server (only for unrecoverable corruption)

### PG_TRY / PG_CATCH
```c
PG_TRY();
{
    /* code that might throw ERROR */
}
PG_CATCH();
{
    /* cleanup on error */
    PG_RE_THROW();
}
PG_END_TRY();
```

Important: `ERROR` does a longjmp. Code after ereport(ERROR,...) never executes. Cleanup must be in PG_CATCH or registered via resource owners.

### Resource cleanup and critical sections

- **`ResourceOwner`** tracks buffer pins, relcache references, catcache
  references, and tuple descriptors, releasing them automatically when an
  `ERROR` longjmps past the code that acquired them. Prefer the
  resource-owner-aware acquisition functions so cleanup is automatic; `PG_TRY`/
  `PG_CATCH` is for cleanup the resource owner does not cover (undoing a
  transient subsystem state), not a universal substitute for it.
- **`PG_ENSURE_ERROR_CLEANUP`** registers a callback that runs exactly once
  regardless of whether the enclosed code completes normally or errors out —
  use it when cleanup must happen on both paths and a plain `PG_CATCH` (which
  only fires on the error path) would require duplicating the cleanup call on
  the success path too.
- **`palloc`/`palloc0` never return NULL.** On allocation failure they
  `ereport(ERROR)`. Do not null-check their result — that check is dead code,
  not a safety net.
- **Code between `START_CRIT_SECTION()` and `END_CRIT_SECTION()` must not
  `ereport(ERROR)` or `palloc`.** A failure in a critical section is promoted
  to `PANIC` by design — the server crashes rather than risk leaving shared
  state (e.g. a page being WAL-logged) half-updated. Do all fallible work
  (allocation, validation, lookups that might fail) *before* entering the
  section; the section itself should only perform operations that cannot fail.
- **A WAL-logging change needs matching redo.** Any change that writes a new
  or modified WAL record requires the corresponding redo (replay) function,
  and consideration of `pg_upgrade` compatibility, physical/logical
  replication, and crash recovery. A write path without its redo counterpart
  is an incomplete patch, not a follow-up.

## Common Patterns

### Node Type Checking
```c
if (IsA(node, SeqScan))
{
    SeqScan *scan = (SeqScan *) node;
    ...
}
```

### List Iteration
```c
ListCell *lc;

foreach(lc, mylist)
{
    MyType *item = (MyType *) lfirst(lc);
    ...
}
```

### Catalog Access
```c
Relation rel;
HeapTuple tup;
ScanKeyData key;

rel = table_open(MyRelationId, AccessShareLock);
ScanKeyInit(&key, ...);
scan = systable_beginscan(rel, ...);
while ((tup = systable_getnext(scan)) != NULL)
{
    ...
}
systable_endscan(scan);
table_close(rel, AccessShareLock);
```

### Lock Ordering
- Always acquire locks in a consistent order to prevent deadlocks
- Relations before indexes
- Lower OID before higher OID (for same lock level)
- Document lock ordering when it matters

## Things to Avoid

- **C++ style comments** (`//`) — use `/* */` only
- **Variable declarations after statements** — all declarations at top of block (C89 style, though this is relaxing in newer code)
- **GNU extensions** — code must compile on all supported platforms
- **Platform-specific code without #ifdef** — use `src/include/port.h` abstractions
- **sizeof(type)** — prefer `sizeof(*variable)` for safety
- **Magic numbers** — define named constants
- **Global variables** — use GUC system for configurable values

## Commit Message Format

```
Brief summary (< 72 chars, imperative mood)

Longer description if needed. Explain WHY the change is made, not
just WHAT was changed (the diff shows the what).

Multiple paragraphs are fine for complex changes.

Author: Patch Author <email>
Reviewed-by: Reviewer <email>
Discussion: https://postgr.es/m/Message-ID@example.com
```
