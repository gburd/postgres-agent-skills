# PostgreSQL Community Agent Skills

Pre-built skills and knowledge for AI agents to interact with PostgreSQL community resources via the [Agora](https://postgr.esq) MCP server.

## Branch Strategy

This repository uses per-agent branches. Clone the branch for your agent:

```bash
git clone -b <agent> https://codeberg.org/postgresq/skills.git
```

### Available Branches

| Branch | Contents |
|--------|----------|
| `claude` | Claude Code skills + shared content (generic/, community/, examples/) |
| `kiro` | Kiro specs + shared content |
| `pi` | Pi (pi.dev) AGENTS.md + shared content |
| `maki` | Maki Lua plugins + shared content |
| `other` | Shared content only (generic/, community/, examples/) |

### Quick Install

**Claude Code:**
```bash
git clone -b claude https://codeberg.org/postgresq/skills.git .claude/skills/postgresq
```

**Kiro:**
```bash
git clone -b kiro https://codeberg.org/postgresq/skills.git .kiro/skills/postgresq
```

**Pi (pi.dev):**
```bash
git clone -b pi https://codeberg.org/postgresq/skills.git /tmp/skills
cp /tmp/skills/pi/AGENTS.md ./AGENTS.md
```

**Maki (tontinton/maki):**
```bash
git clone -b maki https://codeberg.org/postgresq/skills.git /tmp/skills
cp /tmp/skills/maki/plugins/agora.lua ~/.config/maki/plugins/
```

**Any MCP client:**
```bash
git clone -b other https://codeberg.org/postgresq/skills.git /tmp/skills
# Use generic/mcp-servers.json for your client's MCP configuration
```

## What's Included

Each agent branch includes these shared directories:

- **generic/** — MCP client configs and step-by-step workflows for common tasks
- **community/** — PostgreSQL community knowledge base (40 years of encoded practice)
- **examples/** — Worked examples showing research patterns

Plus the agent-specific directory with skills in the agent's native format.

## MCP Server Endpoint

```
https://postgr.esq/l/mcp/
```

Transport: Streamable HTTP. No authentication required.

## License

CC0-1.0 (public domain dedication)
