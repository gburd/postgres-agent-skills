#!/usr/bin/env python3
"""Generate the GitHub Pages skills catalog (site/index.html) from the repo.

Reads every <skill>/SKILL.md front matter (name + description) and the
postgres-best-practices rule index, and emits a single static HTML page
documenting the whole skill set: what each skill is, when to use it, how to
install it, the sources that informed it, and how to contribute.

No third-party dependencies — stdlib only, so CI needs nothing but Python 3.

Usage: tools/build-catalog.py [output_dir]   (default: ./site)
"""
import html
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "site"

GITHUB = "https://github.com/gburd/postgres-agent-skills"
CODEBERG = "https://codeberg.org/ddx/skills"

# The three skill collections, in presentation order, with a blurb each.
COLLECTIONS = [
    ("postgres", "PostgreSQL skills",
     "Grouped by how you interact with the database. Load the persona that "
     "matches your role."),
    ("tooling", "Tooling",
     "Integration with the tools you use while developing code for PostgreSQL. "
     "Secondary to the Postgres skills."),
    ("ai-life-skills", "AI life skills",
     "Generic, domain-agnostic agent habits, offered as a standalone set."),
]

# Old path/anchor -> new, for redirect stubs on the Pages site (the repo was
# restructured from flat skills + per-agent branches to nested collections on a
# single branch). Each old anchor gets a tiny HTML page that meta-refreshes to
# the new catalog location.
REDIRECTS = {
    "postgres-best-practices": "#collection-postgres",
    "memelord-init": "#skill-ai-life-skills-persistent-memory",
    "btw": "#skill-ai-life-skills-btw",
    "checkpoint": "#skill-ai-life-skills-checkpoint",
    "dream": "#skill-ai-life-skills-dream",
    "maintain-docs": "#skill-ai-life-skills-maintain-docs",
    "think-hard": "#skill-ai-life-skills-think-hard",
    "watchdog": "#skill-ai-life-skills-watchdog",
    "stop-slop": "#skill-ai-life-skills-stop-slop",
    "subagent-teams": "#skill-ai-life-skills-subagent-teams",
    "coccinelle": "#skill-tooling-coccinelle",
    "flex-bison-to-lime": "#skill-tooling-flex-bison-to-lime",
    "hegel": "#skill-tooling-hegel",
    "pg-numa-benchmark": "#skill-tooling-pg-numa-benchmark",
    "postgresq": "#skill-tooling-agora",
    "aws-benchmark": "#skill-tooling-benchmark",
    "review-diff": "#skill-tooling-review-diff",
}

# Third-party skills/MCPs worth adding but NOT bundled (different owners and
# licenses). Listed on the catalogue as suggestions.
SUGGESTED = [
    ("ponytail", "https://github.com/DietrichGebert/ponytail",
     "cross-agent 'lazy senior dev' ruleset that forces the simplest working "
     "solution (YAGNI, stdlib-first)."),
    ("superpowers", "https://github.com/obra/superpowers",
     "a spec -> plan -> TDD -> subagent-execution methodology; the "
     "brainstorming, writing-plans, test-driven-development, and "
     "dispatching-parallel-agents skills fill real gaps."),
    ("agent-skill-manager (asm)", "https://www.npmjs.com/package/agent-skill-manager",
     "interactive cross-agent skill install/search/audit/dedup across "
     "Claude/Kiro/Pi/others."),
    ("memelord", "https://github.com/earendil-works/memelord",
     "persistent cross-session memory MCP; pairs with the persistent-memory "
     "skill."),
]


def parse_frontmatter(md_path):
    """Return (name, description) from a SKILL.md YAML front matter block."""
    text = md_path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, None
    fm = m.group(1)
    name = _scalar(fm, "name")
    desc = _scalar(fm, "description")
    return name, desc


def _scalar(fm, key):
    """Extract a YAML scalar that may be inline or a '>'/'|' folded block."""
    # folded/literal block: `key: >` then indented lines
    bm = re.search(rf"^{key}:\s*[>|]\s*\n((?:[ \t]+.*\n?)+)", fm, re.M)
    if bm:
        lines = [ln.strip() for ln in bm.group(1).splitlines()]
        return " ".join(l for l in lines if l)
    # inline, possibly quoted
    im = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', fm, re.M)
    return im.group(1).strip() if im else None


def discover_skills():
    """Walk each collection one level deep for <collection>/<skill>/SKILL.md."""
    groups = []
    for coll, title, blurb in COLLECTIONS:
        base = REPO / coll
        if not base.is_dir():
            continue
        skills = []
        for entry in sorted(base.iterdir()):
            if not entry.is_dir():
                continue
            skill_md = entry / "SKILL.md"
            if not skill_md.exists():
                continue
            name, desc = parse_frontmatter(skill_md)
            if not name:
                continue
            skills.append({"coll": coll, "dir": entry.name,
                           "name": name, "desc": desc or ""})
        if skills:
            groups.append({"coll": coll, "title": title,
                           "blurb": blurb, "skills": skills})
    return groups


def rule_index():
    """Parse postgres/best-practices/references/_sections.md into categories."""
    sec = REPO / "postgres" / "best-practices" / "references" / "_sections.md"
    if not sec.exists():
        return []
    cats = []
    cur = None
    for line in sec.read_text(encoding="utf-8").splitlines():
        h = re.match(r"^##\s+\d+\.\s+(.*)", line)
        if h:
            cur = {"title": h.group(1).strip(), "impact": "", "rules": []}
            cats.append(cur)
            continue
        if cur is None:
            continue
        im = re.match(r"^\*\*Impact:\*\*\s*(.*)", line)
        if im:
            cur["impact"] = im.group(1).strip()
            continue
        rm = re.match(r"^-\s+`([a-z0-9-]+)`\s+—\s+(.*)", line)
        if rm:
            cur["rules"].append((rm.group(1), rm.group(2).strip()))
    return cats


def esc(s):
    return html.escape(s or "")


def card(skill):
    gh = f"{GITHUB}/blob/main/{skill['coll']}/{skill['dir']}/SKILL.md"
    anchor = f"skill-{skill['coll']}-{skill['dir']}"
    return f"""
      <article class="card" id="{esc(anchor)}">
        <h3><code>{esc(skill['name'])}</code></h3>
        <p>{esc(skill['desc'])}</p>
        <p class="meta"><a href="{gh}">SKILL.md →</a></p>
      </article>"""


def groups_section(groups):
    blocks = []
    for g in groups:
        cards = "\n".join(card(s) for s in g["skills"])
        blocks.append(f"""
<h3 id="collection-{esc(g['coll'])}">{esc(g['title'])} <span class="muted">({len(g['skills'])})</span></h3>
<p class="muted">{esc(g['blurb'])}</p>
<div class="grid">{cards}
</div>""")
    return "\n".join(blocks)


def rules_section(cats):
    if not cats:
        return ""
    blocks = []
    for c in cats:
        rows = "\n".join(
            f"          <tr><td><code>{esc(r)}</code></td><td>{esc(d)}</td></tr>"
            for r, d in c["rules"])
        blocks.append(f"""
      <details class="rulecat">
        <summary><strong>{esc(c['title'])}</strong> <span class="impact">{esc(c['impact'])}</span> · {len(c['rules'])} rules</summary>
        <table>
          <thead><tr><th>Rule</th><th>What it says</th></tr></thead>
          <tbody>
{rows}
          </tbody>
        </table>
      </details>""")
    return "\n".join(blocks)


def steering_index():
    """Flat steering/*.md (not SKILL.md dirs): H1 title + first paragraph."""
    base = REPO / "steering"
    if not base.is_dir():
        return []
    out = []
    for p in sorted(base.glob("*.md")):
        if p.name == "README.md":
            continue
        text = p.read_text(encoding="utf-8")
        title = next((l[2:].strip() for l in text.splitlines()
                      if l.startswith("# ")), p.stem)
        # first non-blank, non-heading line as the blurb
        blurb = ""
        body = text.split("---", 2)[-1] if text.startswith("---") else text
        for l in body.splitlines():
            s = l.strip()
            if s and not s.startswith("#"):
                blurb = s
                break
        out.append((p.stem, title, blurb))
    return out


def steering_section(items):
    if not items:
        return ""
    rows = "\n".join(
        f'          <tr><td><a href="{GITHUB}/blob/main/steering/{esc(stem)}.md">'
        f'<code>{esc(stem)}</code></a></td><td>{esc(blurb)}</td></tr>'
        for stem, _title, blurb in items)
    return f"""
<p>Always-on rules an agent reads at the start of every session (as opposed to
skills, which load on demand). The universal files load everywhere; the domain
files (e.g. <code>postgresql</code>) are opt-in per project. See
<a href="{GITHUB}/blob/main/steering/README.md">steering/README.md</a> for how to
wire these into Claude Code, Kiro, Pi, or any AGENTS.md-based agent, and how to
set up your environment for the best agentic results.</p>
<table>
  <thead><tr><th>File</th><th>Governs</th></tr></thead>
  <tbody>
{rows}
  </tbody>
</table>"""


def suggested_section():
    rows = "\n".join(
        f'  <li><a href="{esc(url)}">{esc(name)}</a> \u2014 {esc(desc)}</li>'
        for name, url, desc in SUGGESTED)
    return f"""
<p>These third-party skill sets and MCP servers are worth adding but are
<strong>not bundled</strong> here (different owners and licenses). Install the
ones you want:</p>
<ul>
{rows}
</ul>"""


def build():
    groups = discover_skills()
    cats = rule_index()
    steer = steering_index()
    total_rules = sum(len(c["rules"]) for c in cats)
    total_skills = sum(len(g["skills"]) for g in groups)
    skills_html = groups_section(groups)
    rules_html = rules_section(cats)
    steering_html = steering_section(steer)
    suggested_html = suggested_section()

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PostgreSQL Agent Skills</title>
<style>
  :root {{ --fg:#1a1a1a; --muted:#555; --bg:#fff; --accent:#336791; --line:#e3e3e3; --code:#f4f4f6; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --fg:#e6e6e6; --muted:#9aa; --bg:#15181c; --accent:#6ea8d8; --line:#2a2f36; --code:#1e232a; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
         color:var(--fg); background:var(--bg); }}
  .wrap {{ max-width:960px; margin:0 auto; padding:2rem 1.2rem 4rem; }}
  header h1 {{ font-size:2rem; margin:0 0 .3rem; }}
  header p.lead {{ color:var(--muted); font-size:1.1rem; margin:.2rem 0 1rem; }}
  a {{ color:var(--accent); }}
  code {{ background:var(--code); padding:.12em .4em; border-radius:4px; font-size:.9em; }}
  pre {{ background:var(--code); padding:.9rem 1rem; border-radius:8px; overflow:auto; }}
  pre code {{ background:none; padding:0; }}
  h2 {{ margin-top:2.5rem; border-bottom:1px solid var(--line); padding-bottom:.3rem; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:1rem; }}
  .card {{ border:1px solid var(--line); border-radius:10px; padding:1rem 1.1rem; background:var(--bg); }}
  .card h3 {{ margin:.1rem 0 .5rem; }}
  .card p {{ margin:.3rem 0; font-size:.93rem; color:var(--fg); }}
  .card .meta {{ font-size:.85rem; }}
  .pill {{ display:inline-block; background:var(--code); border:1px solid var(--line);
           border-radius:999px; padding:.15rem .7rem; font-size:.8rem; color:var(--muted); margin:.15rem .3rem .15rem 0; }}
  details.rulecat {{ border:1px solid var(--line); border-radius:8px; margin:.6rem 0; padding:.4rem .9rem; }}
  details.rulecat summary {{ cursor:pointer; }}
  details.rulecat .impact {{ color:var(--muted); font-size:.8rem; }}
  table {{ border-collapse:collapse; width:100%; margin:.6rem 0; font-size:.9rem; }}
  th,td {{ text-align:left; padding:.35rem .5rem; border-bottom:1px solid var(--line); vertical-align:top; }}
  footer {{ margin-top:3rem; color:var(--muted); font-size:.9rem; border-top:1px solid var(--line); padding-top:1rem; }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>PostgreSQL Agent Skills</h1>
  <p class="lead">Pre-built skills and knowledge for AI coding agents working on PostgreSQL —
  from database application best practices to community patch work.</p>
  <p>
    <span class="pill">{total_skills} skills</span>
    <span class="pill">{len(steer)} steering files</span>
    <span class="pill">{total_rules} best-practice rules</span>
    <span class="pill">CC0-1.0 · public domain</span>
    <span class="pill"><a href="{GITHUB}">GitHub</a></span>
    <span class="pill"><a href="{CODEBERG}">Codeberg (source of truth)</a></span>
  </p>
</header>

<section>
  <p>This is a <strong>shared community resource</strong>. The content is dedicated to the
  public domain (CC0-1.0): use it, change it, ship it, no attribution required. Everyone is
  welcome to comment, contribute, correct, and extend it — see
  <a href="#contribute">Contributing</a>.</p>
</section>

<h2 id="install">Install</h2>
<p>It is <strong>one repository</strong>, one copy for every agent (Agent Skills
Open Standard: <code>&lt;collection&gt;/&lt;skill&gt;/SKILL.md</code> with YAML front
matter; no per-agent branches, no per-agent copies). Clone it once:</p>
<pre><code>git clone {GITHUB}.git postgres-agent-skills</code></pre>
<p>Then make it visible to your agent by putting it where that agent looks for
skills (move the clone there, or symlink it). The content is identical; only the
location differs:</p>
<table>
  <thead><tr><th>Agent</th><th>Put it here</th></tr></thead>
  <tbody>
    <tr><td>Claude Code</td><td><code>~/.claude/skills/postgres</code></td></tr>
    <tr><td>Kiro (and Pi, which reads Kiro's dir)</td><td><code>~/.kiro/skills/postgres</code></td></tr>
    <tr><td>Any other MCP-aware agent</td><td>whatever skills directory it is configured to read</td></tr>
  </tbody>
</table>
<p>For example, straight into Claude Code's skills directory:</p>
<pre><code>git clone {GITHUB}.git ~/.claude/skills/postgres</code></pre>
<p>Finally, point your agent at <code>AGENTS.md</code> at the repo root (most read
it automatically; <code>CLAUDE.md</code> is a stub that imports it). Topic
collections: <code>postgres/</code>, <code>tooling/</code>,
<code>ai-life-skills/</code>, <code>steering/</code>; shared knowledge in
<code>community/</code>, <code>generic/</code>, <code>examples/</code>.</p>

<h2 id="skills">Skills</h2>
{skills_html}

<h2 id="steering">Steering</h2>
{steering_html}

<h2 id="best-practices">postgres-best-practices rules</h2>
<p>The <code>postgres/best-practices</code> library is the shared ruleset the role
personas cite. Each rule names an antipattern, shows the fix in runnable SQL, and
cites the canonical PostgreSQL documentation that informed it. {total_rules} rules
in {len(cats)} categories:</p>
{rules_html}

<h2 id="suggested">Suggested external skills &amp; MCPs</h2>
{suggested_html}

<h2 id="sources">Sources &amp; cross-references</h2>
<p>Every rule and skill is written from scratch in original words and dedicated to the public
domain. The <em>ideas</em> are drawn from, and cross-referenced to, these authoritative
sources so you can connect each skill back to its origin:</p>
<ul>
  <li><a href="https://www.postgresql.org/docs/current/">PostgreSQL manual</a> — the canonical
  reference cited per rule (PostgreSQL License).</li>
  <li><a href="https://wiki.postgresql.org/wiki/Don%27t_Do_This">PostgreSQL wiki — Don't Do This</a>
  and <a href="https://wiki.postgresql.org/wiki/Performance_Optimization">Performance Optimization</a>
  (CC-BY-SA-3.0; ideas re-expressed, no text reused).</li>
  <li>Community practice distilled from the pgsql-hackers archive, exposed via the
  <a href="https://pg.ddx.io/mcp/">agora MCP server</a> that several skills drive.</li>
  <li>The structure of this ruleset was informed by
  <a href="https://github.com/supabase/agent-skills">supabase/agent-skills</a>; our rules are
  independent CC0 rewrites, not copies.</li>
</ul>

<h2 id="contribute">Contributing — everyone is welcome</h2>
<p>This is a shared resource for the whole PostgreSQL community. Corrections, additions,
removals, and arguments are all welcome.</p>
<ul>
  <li><strong>Open an issue</strong> (a question, a bug in a rule, a missing topic):
  <a href="{GITHUB}/issues/new">{GITHUB}/issues/new</a></li>
  <li><strong>Open a pull request</strong> (fix or add a rule/skill): fork, make the
  change on <code>main</code>, and open a PR at
  <a href="{GITHUB}/pulls">{GITHUB}/pulls</a>. One rule per file, cite a canonical
  <code>postgresql.org</code> reference, keep it CC0. (Skills are written once for all
  agents — no per-agent branches.)</li>
  <li>The canonical source of truth is Codeberg
  (<a href="{CODEBERG}">{CODEBERG}</a>); GitHub is a mirror, but issues and PRs on either are read.</li>
</ul>

<footer>
  <p>PostgreSQL Agent Skills · CC0-1.0 (public domain) · generated by
  <code>tools/build-catalog.py</code>. Not affiliated with the PostgreSQL Global Development
  Group; "PostgreSQL" is a trademark of the PostgreSQL Community Association.</p>
</footer>
</div>
</body>
</html>
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    # Old-name redirect stubs: the repo was restructured; keep old deep links
    # working with a tiny meta-refresh page under skills/<old-name>/.
    n_redir = 0
    for old, target in REDIRECTS.items():
        d = OUT / "skills" / old
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            f'<!doctype html><meta charset="utf-8">'
            f'<title>moved</title>'
            f'<meta http-equiv="refresh" content="0; url=/postgres-agent-skills/{target}">'
            f'<link rel="canonical" href="/postgres-agent-skills/{target}">'
            f'<p>This skill moved. <a href="/postgres-agent-skills/{target}">Go to the catalogue</a>.</p>\n',
            encoding="utf-8")
        n_redir += 1
    print(f"wrote {OUT/'index.html'} — {total_skills} skills, {total_rules} rules, {n_redir} redirects")


if __name__ == "__main__":
    build()
