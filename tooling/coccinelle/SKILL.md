---
name: coccinelle
description: Run semantic patches on C/C++ via spatch. Use for AST-level refactoring, finding API usage patterns, enforcing coding standards structurally, migrating deprecated APIs, and finding null-deref / resource-leak patterns across large codebases. Pairs with the Pi `coccinelle` extension's pre-defined patterns (null-checks, error-handling, memory-leaks, resource-leaks, dead-code, simplify-conditionals, const-correctness).
---

# Coccinelle — C Semantic Patching

Use Coccinelle (spatch) for structured, semantic code transformations and searches across C codebases. Coccinelle understands C syntax at the AST level, unlike regex-based tools.

## When to Use

- Refactoring C code (dbsql, libdb, openldap, PostgreSQL extensions)
- Finding API usage patterns across a large codebase
- Enforcing coding standards structurally
- Migrating deprecated API calls to new ones
- Finding bugs (null dereference patterns, resource leaks)

## Core Commands

```bash
# Apply a semantic patch
spatch --sp-file rule.cocci --dir src/

# Dry-run (show what would change)
spatch --sp-file rule.cocci --dir src/ --dry-run

# Search only (no modifications)
spatch --sp-file find.cocci --dir src/ -o /dev/null

# Multiple files with specific extensions
spatch --sp-file rule.cocci --include-headers --dir .
```

## SmPL (Semantic Patch Language) Patterns

### Find a function call pattern
```
@@
expression E;
@@
- malloc(E)
+ xmalloc(E)
```

### Find null-check-after-use bugs
```
@@
expression p, E;
@@
*p = ...;
... when != p = E
*if (p == NULL) { ... }
```

### Rename a function across codebase
```
@@
@@
- old_function_name(
+ new_function_name(
  ...)
```

### Add error check after allocation
```
@@
expression p;
@@
p = malloc(...);
+ if (p == NULL) return -ENOMEM;
```

## Best Practices

1. Always use `--dry-run` first to preview changes
2. Use `... when != X` to express "without intervening X"
3. Use `*` prefix on lines to mark them for reporting (search mode)
4. Use `@@` metavariable blocks to bind expressions, types, identifiers
5. Combine with `--dir` to scope to specific subdirectories
6. Use `--include-headers` when patterns span .h and .c files
