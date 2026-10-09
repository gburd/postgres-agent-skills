#!/usr/bin/env python3
"""Generate agents.txt + agents.json for pg.ddx.io from this skills repo.

pg.ddx.io serves this repository's content at https://pg.ddx.io/skills/<path>.
This emits the two agents-txt-standard discovery files that index it, kept in
exact sync from one walk of the tree so they cannot drift.

The curated index lists the loadable skills: the persona SKILL.md files
(postgres/, tooling/, ai-life-skills/), the always-on steering files, and the
shared community conventions + generic workflows. The best-practice reference
rules (postgres/best-practices/references/*.md) are cited BY the personas and
documented in the Pages catalogue, so they are not listed individually here.

Usage: tools/gen-agents.py [output_dir]   (default: repo root)
Stdlib only.
"""
import glob
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else REPO
BASE = "https://pg.ddx.io/skills/"

SITE = {
    "name": "pg.ddx.io",
    "url": "https://pg.ddx.io",
    "description": (
        "Free, read-only, public mirror of the PostgreSQL community archives "
        "since 1991: every mailing list, the git history of postgres and its "
        "ecosystem, commitfest, buildfarm, docs and wiki, cross-linked from "
        "discussion to commit. No login, no API key."
    ),
}
MCP = [{
    "url": "https://pg.ddx.io/mcp",
    "type": "streamable-http",
    "description": (
        "Anonymous, read-only tools over the whole archive: retrieve_context "
        "(cited passages within a token budget), hybrid_search, get_thread, "
        "get_message, git_search, commit_history, plus commitfest, buildfarm, "
        "docs, wiki and code-intelligence tools. See https://pg.ddx.io/mcp-tools."
    ),
}]

# Presentation sections, in load order. Each is (heading, list-of-paths).
# Persona collections load first (pick the one matching your role), then the
# always-on steering, then the shared conventions and step-by-step workflows.
PERSONA_COLLECTIONS = ["postgres", "tooling", "ai-life-skills"]


def rel(path):
    return os.path.relpath(path, REPO)


def frontmatter_desc(text):
    """A YAML `description:` scalar (inline or folded `>`/`|`), else None."""
    bm = re.search(r"^description:\s*[>|]\s*\n((?:[ \t]+.*\n?)+)", text, re.M)
    if bm:
        lines = [ln.strip() for ln in bm.group(1).splitlines()]
        return " ".join(l for l in lines if l)
    im = re.search(r'^description:\s*"?(.*?)"?\s*$', text, re.M)
    return im.group(1).strip() if im else None


def desc(path):
    """Skill description: frontmatter `description:`, else H1 + first sentence."""
    text = open(path, encoding="utf-8").read()
    fm = frontmatter_desc(text)
    if fm:
        return fm
    h1 = re.search(r"^#\s+(.+?)\s*$", text, re.M)
    body = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.S)
    body = re.sub(r"^#.*$", "", body, flags=re.M).strip()
    sentence = re.split(r"(?<=[.!?])\s", body, maxsplit=1)[0].strip() if body else ""
    return ((h1.group(1) + ". ") if h1 else "") + sentence


def personas():
    """<collection>/<skill>/SKILL.md, one level deep, collection order."""
    out = []
    for coll in PERSONA_COLLECTIONS:
        base = os.path.join(REPO, coll)
        if not os.path.isdir(base):
            continue
        for d in sorted(os.listdir(base)):
            p = os.path.join(base, d, "SKILL.md")
            if os.path.isfile(p):
                out.append(p)
    return out


def section(sub):
    return sorted(glob.glob(os.path.join(REPO, sub, "*.md")),
                  key=lambda p: os.path.basename(p))


def steering():
    return [p for p in section("steering")
            if os.path.basename(p) != "README.md"]


def main():
    groups = [
        ("Role skills -- load the one matching the task.", personas()),
        ("Steering: always-on rules an agent reads at session start.", steering()),
        ("Conventions: the PostgreSQL project's rules.",
         section("community/conventions")),
        ("Workflows: step-by-step procedures.", section("generic/workflows")),
    ]
    all_paths = [p for _h, ps in groups for p in ps]

    doc = {
        "$schema": "https://agents-txt.com/schema/agents-json/v1.0.json",
        "version": "1.0",
        "standard": "https://agents-txt.com",
        "site": SITE,
        "mcp": MCP,
        "skills": [{"url": BASE + rel(p), "description": desc(p)}
                   for p in all_paths],
    }
    with open(os.path.join(OUT, "agents.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")

    lines = [
        "# agents.txt",
        "# Standard: https://agents-txt.com",
        "# JSON: https://pg.ddx.io/agents.json",
        "",
        "MCP: https://pg.ddx.io/mcp",
    ]
    for heading, ps in groups:
        lines += ["", f"# --- {heading} ---"]
        lines += [f"Skills: {BASE}{rel(p)}" for p in ps]
    with open(os.path.join(OUT, "agents.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    counts = " ".join(f"{len(ps)} {h.split(':')[0].split()[0].lower()}"
                      for h, ps in groups)
    print(f"wrote {len(all_paths)} skills to agents.txt + agents.json ({counts})")


if __name__ == "__main__":
    main()
