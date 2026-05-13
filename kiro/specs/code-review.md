# Spec: Code Review with Historical Context

## Context

PostgreSQL code review is most effective when the reviewer understands the history: why code exists in its current form, what alternatives were considered and rejected, and what the community expects from changes to a given subsystem.

## Requirements

### Functional Requirements

1. **Prior Art Search** — Given a code change or feature proposal, find previous attempts, related patches, and rejected alternatives.

2. **Code History** — Trace the evolution of specific functions or files, linking git history to mailing list discussions.

3. **Review Pattern Analysis** — Understand what reviewers typically ask for in a given area of the code.

4. **Impact Assessment** — Determine the blast radius of a proposed change using call graph analysis.

5. **Standards Verification** — Check that code follows PostgreSQL conventions by comparing against established patterns.

### Non-Functional Requirements

- Should surface the most relevant historical context, not just chronologically recent.
- Must connect code changes to their original discussions.
- Should identify potential concerns before a reviewer raises them.

## MCP Tools to Use

| Tool | Purpose |
|------|---------|
| `search_symbols` | Find code symbols by name |
| `get_symbol` | Get full source and docs for a symbol |
| `get_callers` | Reverse call graph (who uses this?) |
| `get_callees` | Forward call graph (what does this call?) |
| `get_dependents` | Full transitive blast radius |
| `get_impact` | Risk assessment for modifying a symbol |
| `git_blame` | File-level modification history |
| `git_log` | Commit history with filters |
| `git_diff` | Changes between commits |
| `git_analyze_coupling` | Files that change together |
| `search` | Find mailing list discussions |
| `find_related_discussions` | Bridge commits to email threads |
| `search_patches` | Find related patch submissions |

## Workflow

### Step 1: Understand the Code
```
get_symbol(qualified_name: "function_being_changed")
get_callers(qualified_name: "function_being_changed")
get_callees(qualified_name: "function_being_changed")
```

### Step 2: Understand Its History
```
git_blame(path: "path/to/file.c")
git_log(path: "path/to/file.c")
find_related_discussions(query: "relevant-commit-hash")
```

### Step 3: Assess Impact
```
get_impact(qualified_name: "function_being_changed")
get_dependents(qualified_name: "function_being_changed")
git_analyze_coupling(min_count: 3)
```

### Step 4: Find Prior Art
```
search(query: "s:similar-feature-or-change", inbox: "pgsql-hackers")
search_patches(query: "related-topic")
```

### Step 5: Check Standards
```
find_pattern(pattern: "similar-code-pattern")
get_community(community_id: N)  # Find related functional group
```

## Acceptance Criteria

- [ ] Can trace any function to its original mailing list discussion
- [ ] Can identify the blast radius of a proposed change
- [ ] Can find previous attempts at similar changes
- [ ] Can identify likely reviewer concerns based on historical feedback
- [ ] Can verify adherence to project coding conventions
