# Workflow: Understand the Full Context of a Review Thread

Given a review thread (or any discussion thread), build complete understanding of its context: what preceded it, what it references, who the key participants are, and what the outcome was.

## Inputs

- `message_id`: A Message-ID from the thread (any message in the thread works)
- OR `subject`: Subject line keywords to find the thread

## Steps

### 1. Find the Thread

If you have a Message-ID:
```
get_thread(message_id: "<message-id>")
```

If searching by subject:
```
search(query: "s:subject-keywords", inbox: "pgsql-hackers")
# Then get the thread from the most relevant result
get_thread(message_id: "<found-message-id>")
```

### 2. Identify Key Participants

From the thread messages, note:
- The original author (proposer/patch author)
- Reviewers (people providing feedback)
- Committers (people with commit authority who comment)
- What role each person plays in the discussion

For deeper context on a participant:
```
get_contributor_history(contributor: "person@email")
get_author_messages(author: "person@email", after: "relevant-period")
```

### 3. Find Preceding Context

Threads rarely exist in isolation. Find what came before:

```
# Check explicit references
get_message_references(message_id: "<first-message-id>")

# Find cross-thread references
get_thread_references(message_id: "<any-message-id>")

# Search for earlier discussions on the same topic
search(query: "s:topic-keywords d:earlier-range", inbox: "pgsql-hackers")
```

### 4. Find Related Threads

```
# Semantic similarity
find_similar_messages(message_id: "<key-message-id>")

# Same topic, different time
search(query: "s:topic d:different-range", inbox: "pgsql-hackers")
```

### 5. Understand the Code Context (if reviewing a patch)

```
# Find what's being changed
search_symbols(query: "function-mentioned-in-patch")
get_symbol(qualified_name: "affected_function")
get_callers(qualified_name: "affected_function")

# Understand the impact
get_impact(qualified_name: "affected_function")
```

### 6. Determine the Outcome

```
# Was it committed?
search(query: "s:topic", inbox: "pgsql-committers")
git_search(query: "topic keywords")

# Was it returned or withdrawn?
# (usually visible in the thread itself or commitfest)
search_patches(query: "topic")
```

## Outputs

- Thread summary: who said what, key technical points
- Preceding context: what discussions led to this thread
- Related threads: parallel or follow-up discussions
- Participant context: who has authority/expertise here
- Outcome: what was decided and why
- Code context: what code is affected and its dependencies

## Tips

- The first message in the thread sets the context; always read it fully
- Messages from committers carry decision-making weight
- If the thread dies without resolution, check if a new thread was started
- Long gaps between messages often mean "waiting on author" or "lost momentum"
- Top-posted "looks good to me" from a committer often means it will be committed soon
