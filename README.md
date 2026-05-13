# PostgreSQL Community Agent Skills

Pre-built skills and knowledge for AI agents to interact with PostgreSQL community resources via the [Agora](https://postgr.esq) MCP server.

Agora provides access to 40+ years of PostgreSQL mailing list archives, the PostgreSQL source code with full call-graph intelligence, and community documentation — all through the Model Context Protocol (MCP).

## Quick Start

### Claude Code

1. Copy the MCP configuration into your project:

```bash
# Project-level configuration
cp claude/mcp-config.json .mcp.json

# Or add to your user-level config at ~/.claude/settings.json
```

2. Install skills (symlink or copy into your `.claude/skills/` directory):

```bash
mkdir -p .claude/skills
cp claude/*.md .claude/skills/
```

3. Skills are automatically available when Claude Code starts. Invoke them with slash commands or let Claude use them contextually.

### Kiro

1. Copy specs into your project's `.kiro/specs/` directory:

```bash
mkdir -p .kiro/specs
cp kiro/specs/*.md .kiro/specs/
```

2. Configure the MCP server in your Kiro settings using the endpoint `https://postgr.esq/l/mcp/`.

### Generic MCP Clients

1. Use the configuration in `generic/mcp-servers.json` to connect any MCP-compatible client to Agora.

2. Review the workflow documents in `generic/workflows/` for step-by-step guides on common tasks.

## Repository Structure

```
skills/
├── README.md                  # This file
├── claude/                    # Claude Code skills
│   ├── mcp-config.json        # MCP server configuration
│   ├── postgres-research.md   # Research methodology
│   ├── patch-review.md        # Patch review with historical context
│   ├── commit-archaeology.md  # Trace code to mailing list discussions
│   ├── community-norms.md     # Community methodology and etiquette
│   └── development-process.md # PostgreSQL development cycle
├── kiro/                      # Kiro agent specs
│   └── specs/
│       ├── research-hackers.md    # Research pgsql-hackers
│       ├── code-review.md         # Code review with context
│       └── community-context.md   # Community context
├── generic/                   # Any MCP client
│   ├── mcp-servers.json       # Standard MCP configuration
│   └── workflows/
│       ├── find-related-patches.md
│       ├── trace-feature-history.md
│       ├── review-thread-context.md
│       ├── semantic-code-search.md
│       └── bug-investigation.md
├── community/                 # PostgreSQL community knowledge base
│   ├── methodology.md         # Email-driven development practices
│   ├── review-standards.md    # What reviewers look for
│   ├── coding-conventions.md  # C coding standards
│   ├── patch-submission.md    # How to submit patches
│   ├── communication-norms.md # Mailing list etiquette
│   ├── decision-making.md     # How consensus is reached
│   └── common-pitfalls.md     # Mistakes newcomers make
└── examples/                  # Worked examples
    ├── how-was-wal-implemented.md
    ├── find-all-vacuum-discussions.md
    ├── trace-index-am-evolution.md
    └── review-a-patch-series.md
```

## MCP Server Endpoint

The Agora MCP server is available at:

```
https://postgr.esq/l/mcp/
```

Transport: Streamable HTTP (the modern MCP transport protocol).

## Available MCP Tools

The Agora server exposes tools for:

- **Email search**: Full-text, semantic, and hybrid search across all PostgreSQL mailing lists
- **Thread navigation**: Get complete threads, follow references, find related discussions
- **Code intelligence**: Symbol search, call graphs, type hierarchies, dead code detection
- **Git analysis**: Blame, diff, log, churn analysis, coupling detection
- **Patch tracking**: Find patch series, check upstream merge status
- **Community context**: Author history, contributor patterns, inbox statistics

## License

This repository is dedicated to the public domain under CC0-1.0.
