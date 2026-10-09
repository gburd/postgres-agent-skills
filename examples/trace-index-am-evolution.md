# Example: Trace Index AM API Evolution

This example demonstrates using Agora to trace how the Index Access Method (AM) API evolved across PostgreSQL releases — from the original fixed set of index types to the modern extensible interface.

## Background

PostgreSQL originally had a fixed set of index types (B-tree, hash, GiST). Over time, the Index AM API was redesigned to allow extensible index types (GIN, BRIN, Bloom, and third-party types). This is a case study in API evolution driven by community need.

## Step 1: Find the Original AM Interface

### Search for Early Design
```
search(query: "s:index access method d:1996-01..2005-12", inbox: "pgsql-hackers")
search(query: "s:GiST access method", inbox: "pgsql-hackers")
```

### Find the Code Structure
```
search_symbols(query: "IndexAmRoutine")
search_symbols(query: "amgettuple")
get_symbol(qualified_name: "IndexAmRoutine")
```

## Step 2: Trace GIN Introduction (8.2, ~2006)

GIN (Generalized Inverted Index) was one of the first major new index types:

```
search(query: "s:GIN index d:2005-01..2007-01", inbox: "pgsql-hackers")
search_patches(query: "GIN index")
git_search(query: "GIN index access method")
```

## Step 3: Trace the AM API Redesign (9.6, ~2016)

The major API redesign replaced function OID arrays with a proper handler interface:

```
# Find the RFC/proposal
search(query: "s:index AM API OR s:index access method refactor d:2014-01..2016-12", inbox: "pgsql-hackers")
hybrid_search(query: "redesign index access method API extensible handler")

# Find the patches
search_patches(query: "index AM handler")

# Find the commit
search(query: "s:index AM", inbox: "pgsql-committers")
git_search(query: "IndexAmRoutine")
```

### Key Changes in the Redesign
```
# Old interface (function OIDs in pg_am)
search(query: "s:pg_am amgettuple aminsert", inbox: "pgsql-hackers")

# New interface (IndexAmRoutine struct)
get_symbol(qualified_name: "IndexAmRoutine")
get_type_hierarchy(qualified_name: "IndexAmRoutine")
```

## Step 4: Trace BRIN Introduction (9.5, ~2015)

BRIN (Block Range Index) was designed specifically for large sequential datasets:

```
search(query: "s:BRIN OR s:block range index d:2013-01..2015-12", inbox: "pgsql-hackers")
search_patches(query: "BRIN")

# Find Alvaro Herrera's original patches
get_author_messages(author: "alvherre", after: "2013-01-01", before: "2015-12-31")
```

## Step 5: Trace Table AM API (12, ~2019)

The success of the Index AM API led to a similar refactoring for table storage:

```
search(query: "s:table AM OR s:table access method d:2017-01..2019-12", inbox: "pgsql-hackers")
search_patches(query: "table access method")

# Find Andres Freund's work
get_author_messages(author: "andres@anarazel.de", after: "2017-01-01", before: "2019-12-31")

# Find the table AM handler
search_symbols(query: "TableAmRoutine")
get_symbol(qualified_name: "TableAmRoutine")
```

## Step 6: Examine Current AM API Structure

```
# All AM-related symbols
search_symbols(query: "AmRoutine")
search_symbols(query: "amhandler")

# See how a specific AM implements the interface
find_pattern(pattern: "IndexAmRoutine.*btree")
search_symbols(query: "bthandler")
get_symbol(qualified_name: "bthandler")
get_callees(qualified_name: "bthandler")

# Compare with another AM
search_symbols(query: "ginhandler")
get_symbol(qualified_name: "ginhandler")
```

## Step 7: Find Extension Points

```
# How third-party extensions register new AMs
find_pattern(pattern: "PG_FUNCTION_INFO_V1.*handler")
search_symbols(query: "handler", kind: "function")

# Find examples of extension index AMs
search(query: "s:bloom index OR s:rum index OR s:zombodb", inbox: "pgsql-hackers")
```

## Step 8: Analyze the Call Graph

```
# What does the executor call when using an index?
search_symbols(query: "index_getnext")
get_callers(qualified_name: "index_getnext")
get_callees(qualified_name: "index_getnext")

# How does the planner interact with AMs?
search_symbols(query: "amcostestimate")
get_callers(qualified_name: "btcostestimate")
```

## Step 9: Find Design Discussions About Trade-offs

```
# Why was the interface designed this way?
hybrid_search(query: "index AM design trade-offs callback versus virtual table")

# What were the rejected alternatives?
search(query: "s:index AM alternative approach", inbox: "pgsql-hackers")

# Performance concerns
search(query: "s:index AM overhead OR performance", inbox: "pgsql-hackers")
```

## What You Learn

### API Evolution Pattern

1. **Monolithic phase** (pre-8.0): Fixed set of index types, hard-coded in the executor
2. **Function-pointer phase** (8.0-9.5): pg_am catalog with function OID columns
3. **Handler phase** (9.6+): IndexAmRoutine struct returned by AM handler function
4. **Extension to tables** (12): Same pattern applied to table storage

### Design Principles Revealed

- **Extensibility without core changes**: New AMs don't require modifying core code
- **Performance preservation**: The indirection adds minimal overhead
- **Backwards compatibility**: Old AMs continue to work through compatibility shims
- **Incremental adoption**: Not all AM callbacks are required; many are optional

### Key People in AM API Evolution

Identified through the search:
- Alvaro Herrera (BRIN, AM infrastructure)
- Andres Freund (Table AM)
- Alexander Korotkov (GiST, GIN improvements)
- Peter Geoghegan (B-tree improvements, nbtree)
- Heikki Linnakangas (GiST, index infrastructure)

### Key Files
```
src/include/access/amapi.h           — IndexAmRoutine definition
src/include/access/tableam.h         — TableAmRoutine definition
src/backend/access/index/indexam.c   — Generic index AM dispatch
src/backend/access/nbtree/           — B-tree AM implementation
src/backend/access/gin/              — GIN implementation
src/backend/access/brin/             — BRIN implementation
src/backend/access/gist/             — GiST implementation
```
