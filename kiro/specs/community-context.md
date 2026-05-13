# Spec: Understanding Community Context

## Context

The PostgreSQL community has implicit norms, power structures, and decision-making processes that are not formally documented anywhere. Understanding these is essential for effective participation in PostgreSQL development.

## Requirements

### Functional Requirements

1. **Contributor Profiling** — Given a contributor name or email, determine their role, expertise areas, and communication style.

2. **Decision History** — For any technical decision, find how it was made: who proposed, who objected, how consensus was reached.

3. **Norm Inference** — Determine community expectations for a given type of contribution (patch format, review style, discussion approach).

4. **Status Assessment** — Determine the current state of a proposal or feature: active, stalled, rejected, committed.

5. **Relationship Mapping** — Understand who works with whom, who reviews whose patches, mentor relationships.

## MCP Tools to Use

| Tool | Purpose |
|------|---------|
| `get_author_messages` | All messages from a contributor |
| `get_contributor_history` | Patch submission history |
| `get_inbox_stats` | Activity patterns and top contributors |
| `search` | Find specific discussions and decisions |
| `get_thread` | Read complete decision threads |
| `hybrid_search` | Find discussions about norms/process |
| `git_analyze_authors` | Commit statistics per author |
| `browse_by_date` | Understand activity in a period |
| `find_similar_messages` | Find discussions with similar tone/topic |

## Workflow

### Understanding a Contributor
```
get_author_messages(author: "person@email", inbox: "pgsql-hackers")
get_contributor_history(contributor: "person@email")
git_analyze_authors()  # See where they rank
```

### Understanding a Decision
```
search(query: "s:topic-of-decision", inbox: "pgsql-hackers")
get_thread(message_id: "<decision-thread-id>")
get_thread_references(message_id: "<id>")  # Find related threads
```

### Understanding Community Norms
```
# Find meta-discussions about process
search(query: "s:commitfest process OR s:review process OR s:patch submission")
hybrid_search(query: "how should patches be submitted to PostgreSQL")

# See how successful patches were submitted
search_patches(query: "committed")
```

### Assessing Proposal Status
```
search(query: "s:proposal-topic d:recent-range", inbox: "pgsql-hackers")
search_patches(query: "proposal-topic")
get_thread(message_id: "<latest-thread>")
```

## Key Context

### Power Structure
- ~30 committers can push to the repo
- No formal BDFL; consensus-driven
- Major committers (Tom Lane, Andres Freund, Robert Haas) have outsized influence
- "Commit bits" are granted by existing committers to proven contributors

### Decision Making
- No voting mechanism
- Consensus means "no strong objections from committers"
- One committed committer can champion a feature
- One strongly objecting committer can block
- Silence ≠ approval; it means nobody cares enough

### Cultural Values (ranked)
1. Backwards compatibility
2. Correctness
3. Simplicity (avoid unnecessary complexity)
4. Performance
5. Standards compliance
6. Developer convenience

## Acceptance Criteria

- [ ] Can profile any contributor's role and expertise
- [ ] Can trace how a specific decision was made
- [ ] Can identify community expectations for a given type of contribution
- [ ] Can assess whether a proposal has community support
- [ ] Can identify key stakeholders for a given topic
