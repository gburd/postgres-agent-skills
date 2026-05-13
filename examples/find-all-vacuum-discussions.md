# Example: Find and Summarize All Autovacuum Discussions

This example shows how to use Agora to comprehensively research a topic — in this case, autovacuum and its evolution.

## Background

Autovacuum is PostgreSQL's automatic maintenance system that reclaims dead tuples, prevents transaction ID wraparound, and updates statistics. It's one of the most discussed subsystems because it directly impacts production database performance.

## Step 1: Find All Major Autovacuum Threads

### Broad Search
```
search(query: "s:autovacuum", inbox: "pgsql-hackers", limit: 100)
```

### Focused on Design and Implementation
```
search(query: "s:autovacuum design OR implementation OR RFC", inbox: "pgsql-hackers")
```

### Focused on Problems
```
search(query: "s:autovacuum OR s:auto_vacuum", inbox: "pgsql-bugs")
search(query: "s:autovacuum performance OR bloat OR wraparound", inbox: "pgsql-hackers")
```

## Step 2: Trace the Timeline

### Original Autovacuum Introduction (8.1, circa 2005)
```
search(query: "s:autovacuum d:2004-01..2005-12", inbox: "pgsql-hackers")
```

### Multi-Worker Autovacuum (8.3, circa 2007)
```
search(query: "s:autovacuum worker d:2006-01..2008-01", inbox: "pgsql-hackers")
```

### Cost-Based Vacuum Delay
```
search(query: "s:vacuum cost delay OR s:vacuum_cost_delay", inbox: "pgsql-hackers")
```

### Aggressive Vacuum for Wraparound Prevention
```
search(query: "s:aggressive vacuum OR s:anti-wraparound", inbox: "pgsql-hackers")
```

### Recent Improvements (PG 16-17)
```
search(query: "s:autovacuum d:2022-01..2025-01", inbox: "pgsql-hackers")
search(query: "s:vacuum failsafe OR s:vacuum eager", inbox: "pgsql-hackers")
```

## Step 3: Find the Key Contributors

```
# Who writes about autovacuum the most?
get_author_messages(author: "peter.geoghegan", inbox: "pgsql-hackers")
get_author_messages(author: "masahiko.sawada", inbox: "pgsql-hackers")

# Who commits vacuum-related changes?
search(query: "s:vacuum OR s:autovacuum", inbox: "pgsql-committers")
```

## Step 4: Understand the Code

```
# Find autovacuum-related functions
search_symbols(query: "autovacuum", kind: "function")
search_symbols(query: "lazy_vacuum")

# Main autovacuum launcher
get_symbol(qualified_name: "AutoVacLauncherMain")
get_callees(qualified_name: "AutoVacLauncherMain")

# Main vacuum execution
get_symbol(qualified_name: "lazy_vacuum_heap_rel")
get_callees(qualified_name: "lazy_vacuum_heap_rel")

# Find the community (module) for vacuum
get_communities()
# Look for the vacuum-related community
```

## Step 5: Find Bug Reports and Issues

```
# Production problems with autovacuum
search(query: "s:autovacuum bloat OR wraparound OR stuck", inbox: "pgsql-bugs")
search(query: "b:autovacuum not running", inbox: "pgsql-bugs")

# Semantic search for performance issues
hybrid_search(query: "autovacuum causing performance problems production")
```

## Step 6: Find Configuration Discussions

```
# GUC tuning discussions
search(query: "s:autovacuum_naptime OR s:autovacuum_vacuum_threshold", inbox: "pgsql-hackers")
search(query: "s:autovacuum tuning OR s:autovacuum configuration", inbox: "pgsql-general")
hybrid_search(query: "how to tune autovacuum for large tables")
```

## Step 7: Trace File History

```
# Autovacuum launcher/worker
git_log(path: "src/backend/postmaster/autovacuum.c")
git_analyze_churn()  # See if autovacuum files are high-churn

# Vacuum execution
git_log(path: "src/backend/access/heap/vacuumlazy.c")
git_blame(path: "src/backend/access/heap/vacuumlazy.c")
```

## Synthesis

After completing these searches, you can construct a narrative:

### Evolution Summary

1. **Pre-8.1**: Manual VACUUM required. DBAs had to schedule it via cron. Failure to vacuum caused table bloat and eventually transaction ID wraparound (database shutdown).

2. **8.1 (2005)**: Autovacuum introduced as a single background process. Basic threshold-based triggering.

3. **8.3 (2008)**: Multi-worker autovacuum. Multiple tables can be vacuumed concurrently. Cost-based delay to limit I/O impact.

4. **9.x era**: Continuous improvements to wraparound prevention, better statistics tracking, improved cost model.

5. **PG 13-14**: Parallel vacuum capabilities. Index vacuum improvements.

6. **PG 15-16**: Vacuum failsafe mechanism (emergency mode to prevent wraparound at any cost), eager scanning, improved progress reporting.

7. **PG 17+**: Ongoing work on vacuum efficiency, better handling of large tables, reduced lock contention.

### Key Insights

- Autovacuum is the source of more production incidents than almost any other subsystem
- The community continually balances "run vacuum aggressively enough" vs "don't impact workload"
- Transaction ID wraparound prevention is a hard constraint — vacuum MUST complete before XIDs wrap
- Most "PostgreSQL is slow" complaints trace back to autovacuum misconfiguration

### Unresolved Debates

Search for current threads to find ongoing debates:
```
search(query: "s:autovacuum d:2024-01..", inbox: "pgsql-hackers")
```

Common ongoing topics: better defaults, reducing I/O impact, handling very large tables, improving wraparound prevention guarantees.
