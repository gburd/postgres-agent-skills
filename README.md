# PostgreSQL Community Agent Skills

Pre-built skills and knowledge for AI coding agents working on PostgreSQL — community research, patch review, internals investigation, performance work, and the surrounding workflow.

The repository is structured as one branch per supported agent. Each branch ships shared community knowledge, agent-specific configuration, and the operator's tested per-task skills translated into that agent's native skill format.

License: CC0-1.0 (public domain dedication). See `LICENSE`.

## Branch Strategy

This repository uses per-agent branches. Clone the branch for your agent:

```bash
git clone -b <agent> https://codeberg.org/ddx/skills.git
```

### Available Branches

| Branch | Contents |
|--------|----------|
| `claude` | Claude Code skills + 13 operator skills (`<skill>/SKILL.md` w/ frontmatter) + shared content |
| `kiro` | Kiro specs + 13 operator skills (same frontmatter format) + shared content |
| `pi` | Pi (pi.dev) AGENTS.md + 13 operator skills (Pi reads `~/.kiro/skills/`) + shared content |
| `codex` | OpenAI Codex prompts + 13 operator skills (no frontmatter) + `codex/install.sh` + `codex/mcp_servers.toml` + shared content |
| `maki` | Maki Lua plugin + 13 operator skills as agent context + shared content |
| `other` | Shared content + 13 operator skills, generic markdown for any MCP-aware agent |

### Quick Install

**Claude Code:**
```bash
git clone -b claude https://codeberg.org/ddx/skills.git ~/.claude/skills/postgresq
```

**Kiro:**
```bash
git clone -b kiro https://codeberg.org/ddx/skills.git ~/.kiro/skills/postgresq
```

**Pi (pi.dev):**
```bash
git clone -b pi https://codeberg.org/ddx/skills.git /tmp/skills
cp /tmp/skills/pi/AGENTS.md ./AGENTS.md
# Pi also reads ~/.kiro/skills/ for /skill:<name>; symlink the per-skill dirs there if desired.
```

**OpenAI Codex:**
```bash
git clone -b codex https://codeberg.org/ddx/skills.git ~/codex-skills
cd ~/codex-skills && bash codex/install.sh
# Then paste codex/mcp_servers.toml into ~/.codex/config.toml.
```

**Maki (tontinton/maki):**
```bash
git clone -b maki https://codeberg.org/ddx/skills.git /tmp/skills
cp /tmp/skills/maki/plugins/agora.lua ~/.config/maki/plugins/
```

**Any MCP client:**
```bash
git clone -b other https://codeberg.org/ddx/skills.git /tmp/skills
# generic/mcp-servers.json is the starting point.
```

## What's Included

Each agent branch includes:

- **generic/** — MCP client config and step-by-step workflows for common research tasks.
- **community/** — PostgreSQL community knowledge base (40 years of encoded conventions, review standards, communication norms).
- **examples/** — Worked examples showing research patterns end-to-end.
- **13 operator skills** at branch root — workflow meta (`btw`, `checkpoint`, `dream`, `maintain-docs`, `review-diff`, `think-hard`, `watchdog`), porting and code-transformation (`coccinelle`, `flex-bison-to-lime`), property-based testing (`hegel`), agent-memory bootstrap (`memelord-init`), PG-specific benchmarking (`pg-numa-benchmark`), and PG community-research (`postgresq`).
- **Agent-specific subdirectory** — Claude/Kiro/Pi/Codex/Maki native artefacts.

## MCP Server Endpoint (postgresq / agora)

```
https://pg.ddx.io/mcp/
```

Transport: Streamable HTTP / SSE. No authentication required. Provides 108 tools across the pgsql-hackers archive (188k+ messages, JWZ-threaded), 28 git repos with code intelligence (165k+ symbols including UCB POSTGRES historical and modern trees), commitfest, build-farm, and the wiki.

## Other MCP Services of Interest

The skills assume a small constellation of MCP servers running alongside the agent. They are independent — install whichever you actually need. Listed in the order the operator finds most useful; install snippets are minimal, see each project's docs for full configuration.

### memelord — persistent memory across sessions
- **Source:** https://github.com/earendil-works/memelord
- **Transport:** stdio
- **Purpose:** Per-project notebook the agent reads at session start and writes to throughout. Cross-session lessons survive between conversations — "pg_search BM25 fails on replica", "this benchmark host's NUMA topology", which patch landed and which did not — preserved across sessions, agents, and machines.
- **When to use for PG dev:** every long-running PostgreSQL task. Lessons learned reviewing one patch get reused when reviewing the next; gotchas about a benchmark host survive instance restarts.
- **Install (Pi):** `memelord-mcp` extension in `~/.pi/agent/extensions/`.
- **Install (Claude Code):** stdio entry in `~/.claude.json` `mcpServers`, plus `SessionStart` / `PostToolUse` / `Stop` / `SessionEnd` hooks. See the `memelord-init` skill.
- **Install (Codex):**

  ```toml
  [mcp_servers.memelord]
  command = "node"
  args = ["/home/<you>/.npm-global/bin/memelord", "serve"]
  env = { MEMELORD_DIR = "/home/<you>/.memelord" }
  enabled = true
  ```

### postgresq — PostgreSQL community + git + code intel (the agora server)
- **Source:** https://codeberg.org/ddx/agora (publicly hosted at https://pg.ddx.io/)
- **Transport:** SSE (HTTP)
- **Endpoint:** `https://pg.ddx.io/mcp/`
- **Purpose:** 108-tool MCP exposing the entire pgsql-hackers archive, 28 git repos with code intelligence, commitfest entries, build-farm runs, the wiki, and 1837 wiki pages. Primary tool for PG community research.
- **When to use for PG dev:** any time the question "why was this designed this way?", "who else has hit this?", "what does the buildfarm say?", or "who calls this function?" comes up. Replaces hours of `git log -S` and archive-grepping.
- **Install (Pi):** `agora-mcp` extension in `~/.pi/agent/extensions/`.
- **Install (Claude Code):**

  ```json
  "postgresq": { "type": "http", "url": "https://pg.ddx.io/mcp/" }
  ```

- **Install (Codex):**

  ```toml
  [mcp_servers.postgresq]
  url = "https://pg.ddx.io/mcp/"
  transport = "sse"
  enabled = true
  ```

### github — read-only GitHub repos and issues
- **Source:** `github-mcp-server` (binary; authenticated via `gh auth token`)
- **Transport:** stdio
- **Purpose:** Browse GitHub repos and issues without leaving the agent. The Postgres org has many adjacent repos (`psycopg/psycopg`, `postgrespro/postgres`, `supabase/postgres`, extension vendors); this server gives the agent a uniform read interface. Dynamic toolsets register only for repos you actually fetch.
- **When to use for PG dev:** triaging an issue against a downstream fork, comparing extension implementations across vendors, fetching a referenced PR's diff without leaving the conversation.
- **Install (Pi):** stdio entry pointing at the `github-mcp-server` binary; export `GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token)` first.
- **Install (Claude Code):** same stdio entry in `~/.claude.json`.
- **Install (Codex):**

  ```toml
  [mcp_servers.github]
  command = "/path/to/github-mcp-server"
  args = ["stdio", "--dynamic-toolsets", "--read-only"]
  enabled = false  # requires `gh auth login` first
  ```

### filesystem — sandboxed local file access
- **Source:** `@modelcontextprotocol/server-filesystem`
- **Transport:** stdio
- **Purpose:** Constrain agent file I/O to a configured root. Useful when an agent needs to inspect a checkout, a patch series, or a benchmark-results directory without granting it free reign over `$HOME`.
- **When to use for PG dev:** inspecting a patched PostgreSQL tree, applying or reading `.patch` files, walking a benchmark-results dump.
- **Install (Pi):** stdio entry, `args = ["-y", "@modelcontextprotocol/server-filesystem", "<root>"]`.
- **Install (Claude Code):** same stdio entry in `~/.claude.json`.
- **Install (Codex):**

  ```toml
  [mcp_servers.filesystem]
  command = "npx"
  args = ["-y", "@modelcontextprotocol/server-filesystem", "/home/<you>"]
  enabled = true
  ```

### server-memory — knowledge-graph persistent memory
- **Source:** `@modelcontextprotocol/server-memory`
- **Transport:** stdio
- **Purpose:** A *different* persistence mechanism from memelord — structured knowledge-graph (entities, relations, observations) rather than freeform notes. Useful when the agent needs structured fact-recall across a single long session.
- **When to use for PG dev:** complex multi-hop deduction over a single review pass — "this function calls that, which is held in tension with this MR, which contradicts that thread on -hackers". Within one session it builds and traverses the graph; memelord is the cross-session counterpart.
- **Install (Pi):** stdio entry, `args = ["-y", "@modelcontextprotocol/server-memory"]`.
- **Install (Claude Code):** same stdio entry in `~/.claude.json` (key: `memory`).
- **Install (Codex):**

  ```toml
  [mcp_servers.memory]
  command = "npx"
  args = ["-y", "@modelcontextprotocol/server-memory"]
  enabled = true
  ```

### server-git — local Git operations
- **Source:** `mcp-server-git` (official MCP, Python; via `uvx`)
- **Transport:** stdio
- **Purpose:** `log`, `diff`, `blame`, `show`, branch/tree inspection on a *local* checkout. Distinct from the `github` server (remote) and from `postgresq` (curated PG repos with code intel).
- **When to use for PG dev:** archaeology on a local PostgreSQL tree — bisecting, blaming a hunk, walking a patch series across rebases.
- **Install (Pi):** stdio entry, `args = ["--from", "mcp-server-git", "mcp-server-git"]` via `uvx`.
- **Install (Claude Code):** same stdio entry in `~/.claude.json` (key: `git`).
- **Install (Codex):**

  ```toml
  [mcp_servers.git]
  command = "uvx"
  args = ["--from", "mcp-server-git", "mcp-server-git"]
  enabled = true
  ```

### context7 — version-aware library docs (Upstash)
- **Source:** `@upstash/context7-mcp`
- **Transport:** stdio
- **Purpose:** Live library documentation lookup *for the version pinned in your project*. Resolves the long-standing failure mode where an agent cites a library API that no longer exists or never existed in your version.
- **When to use for PG dev:** any time you touch a third-party library — psycopg3, asyncpg, sqlalchemy, libpq bindings, a Rust crate wrapping libpq. Pull the docs the project actually uses, not whatever version the LLM trained on.
- **Install (Pi):** stdio entry, `args = ["-y", "@upstash/context7-mcp@latest"]`.
- **Install (Claude Code):** same stdio entry in `~/.claude.json`.
- **Install (Codex):**

  ```toml
  [mcp_servers.context7]
  command = "npx"
  args = ["-y", "@upstash/context7-mcp@latest"]
  enabled = true
  ```

### sequential-thinking — structured multi-step reasoning
- **Source:** `@modelcontextprotocol/server-sequential-thinking`
- **Transport:** stdio
- **Purpose:** A reasoning scaffold the agent calls out to when a problem benefits from explicit step-by-step deduction with revision. Externalises the chain of thought so it can be revised mid-stream rather than written-and-forgotten.
- **When to use for PG dev:** complex internals deduction — "trace WAL replay through a pending-merge phase", "reason about lock interactions between CONCURRENTLY index build and a parallel VACUUM", anything where a single forward pass produces hand-wavy nonsense.
- **Install (Pi):** stdio entry, `args = ["-y", "@modelcontextprotocol/server-sequential-thinking"]`.
- **Install (Claude Code):** same stdio entry in `~/.claude.json`.
- **Install (Codex):**

  ```toml
  [mcp_servers.sequential-thinking]
  command = "npx"
  args = ["-y", "@modelcontextprotocol/server-sequential-thinking"]
  enabled = true
  ```

### llms-docs — `mcpdoc` wrappers for `llms.txt` sources
- **Source:** `mcpdoc` (via `uvx`)
- **Transport:** stdio
- **Purpose:** Each entry in this group wraps an `llms.txt` URL — PostgreSQL official docs, pgsql-hackers archive renders, vendor docs — and exposes them as a fetchable resource. The agent gets authoritative text on demand, *per project*, configured by the operator.
- **When to use for PG dev:** quoting the canonical PostgreSQL docs verbatim, fetching the latest `pg_hba.conf` reference, citing a -hackers thread by URL. Anything where you want the source-of-truth text rather than the model's recollection.
- **Install (Pi):** one stdio entry per source, each invoking `uvx --from mcpdoc mcpdoc --urls "<title>:<url>" --transport stdio`.
- **Install (Claude Code):** same per-source stdio entries in `~/.claude.json`.
- **Install (Codex):**

  ```toml
  [mcp_servers.pg-docs]
  command = "uvx"
  args = ["--from", "mcpdoc", "mcpdoc", "--urls", "PostgreSQL:https://www.postgresql.org/llms.txt", "--transport", "stdio"]
  enabled = false  # configure your own llms.txt sources
  ```

These are the operator's curated servers; the broader MCP ecosystem has many more. Forks and additions welcome.

## Contributing

The repo is a starting point, not a finished product. PRs welcome. Branches are per-agent; submit changes against the branch matching the agent you target. Shared content (community/, examples/, generic/) lives on every branch — edit it on one and the maintainer cherry-picks across.

## License

CC0-1.0 (public domain dedication). See `LICENSE`. Use it, modify it, ship it, sell it — no attribution required (though appreciated).
