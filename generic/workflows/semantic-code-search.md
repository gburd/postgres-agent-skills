# Workflow: Find Code by Meaning, Not Just Text

Use semantic search to find PostgreSQL code that implements a concept, even when you don't know the exact function names or terminology used in the source.

## Inputs

- `concept`: A natural language description of what the code does (e.g., "calculate the cost of a sequential scan", "handle deadlock detection")

## Steps

### 1. Semantic Code Search

Start with meaning-based search:

```
semantic_search_code(query: "description of what the code does")
```

This returns symbols whose implementation is semantically similar to your description, even if they use different terminology.

### 2. Hybrid Code Search

Combine keyword and semantic for better precision:

```
hybrid_search_code(query: "concept description with some technical terms")
```

### 3. Explore Found Symbols

For each relevant result:

```
get_symbol(qualified_name: "found_function_name")
get_signature(qualified_name: "found_function_name")
```

### 4. Navigate the Call Graph

Once you find a relevant function, explore its neighborhood:

```
# What does it call? (understand its implementation)
get_callees(qualified_name: "found_function")

# Who calls it? (understand where it fits)
get_callers(qualified_name: "found_function")

# What community/module does it belong to?
get_communities()
get_community(community_id: N)
```

### 5. Find Related Symbols by Pattern

If you found one relevant function, search for similar patterns:

```
find_pattern(pattern: "regex-matching-similar-code")
```

### 6. Understand the File Context

```
symbols_in_file(path: "path/to/relevant/file.c")
find_imports(path: "path/to/relevant/file.c")
```

### 7. Trace to Discussions

Once you've found the code:

```
git_blame(path: "path/to/file.c")
find_related_discussions(query: "commit-that-added-it")
```

## Outputs

- List of symbols implementing the concept
- Call graph context showing how they fit together
- File locations and module membership
- Original discussions that motivated the code

## Example

Concept: "How does PostgreSQL decide whether to use an index or a sequential scan?"

```
# 1. Semantic search
semantic_search_code(query: "decide between index scan and sequential scan cost comparison")

# 2. Likely finds cost_seqscan, cost_index, etc.
get_symbol(qualified_name: "cost_seqscan")
get_symbol(qualified_name: "cost_index")

# 3. Who calls these cost functions?
get_callers(qualified_name: "cost_seqscan")
# → Likely points to create_seqscan_path and similar

# 4. Explore the path creation layer
get_callees(qualified_name: "create_seqscan_path")

# 5. Find the comparison/selection logic
semantic_search_code(query: "select cheapest path from alternatives")
```

## Tips

- Semantic search is best when you know WHAT code does but not HOW it's named
- Hybrid search works well when you know some terms but not all
- After finding one relevant symbol, use call graph navigation to discover related ones
- PostgreSQL uses descriptive function names — once you find one, you can often guess related names
- The community detection (`get_communities`) groups functionally related code, useful for understanding modules
