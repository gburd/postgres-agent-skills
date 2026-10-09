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

# Skills that are documentation/shared, not loadable skill dirs, are skipped.
SKIP_DIRS = {".git", ".githooks", "tools", "community", "generic", "examples",
             "site", "claude", "codex", "kiro", "pi", "maki", "hermes", "other",
             "assets"}


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
    skills = []
    for entry in sorted(REPO.iterdir()):
        if not entry.is_dir() or entry.name in SKIP_DIRS or entry.name.startswith("."):
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.exists():
            continue
        name, desc = parse_frontmatter(skill_md)
        if not name:
            continue
        skills.append({"dir": entry.name, "name": name, "desc": desc or ""})
    return skills


def rule_index():
    """Parse postgres-best-practices/references/_sections.md into categories."""
    sec = REPO / "postgres-best-practices" / "references" / "_sections.md"
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
    gh = f"{GITHUB}/blob/main/{skill['dir']}/SKILL.md"
    return f"""
      <article class="card" id="skill-{esc(skill['dir'])}">
        <h3><code>{esc(skill['name'])}</code></h3>
        <p>{esc(skill['desc'])}</p>
        <p class="meta"><a href="{gh}">SKILL.md →</a></p>
      </article>"""


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


def build():
    skills = discover_skills()
    cats = rule_index()
    total_rules = sum(len(c["rules"]) for c in cats)
    cards = "\n".join(card(s) for s in skills)
    rules_html = rules_section(cats)

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
    <span class="pill">{len(skills)} skills</span>
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
<p>The repository uses one branch per supported agent. Clone the branch for yours:</p>
<pre><code>git clone -b claude {GITHUB}.git ~/.claude/skills/postgres
git clone -b kiro   {GITHUB}.git ~/.kiro/skills/postgres
git clone -b pi     {GITHUB}.git ~/.pi/skills
git clone -b other  {GITHUB}.git ~/agent-skills   # any MCP-aware agent</code></pre>
<p>Branches: <code>claude</code>, <code>kiro</code>, <code>pi</code>, <code>codex</code>,
<code>maki</code>, <code>hermes</code>, <code>other</code>. Shared content
(<code>community/</code>, <code>generic/</code>, <code>examples/</code>) ships on every branch.</p>

<h2 id="skills">Skills</h2>
<div class="grid">{cards}
</div>

<h2 id="best-practices">postgres-best-practices rules</h2>
<p>The <code>postgres-best-practices</code> skill is a ruleset for Postgres running anywhere.
Each rule names an antipattern, shows the fix in runnable SQL, and cites the canonical
PostgreSQL documentation that informed it. {total_rules} rules in {len(cats)} categories:</p>
{rules_html}

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
  <li><strong>Open a pull request</strong> (fix or add a rule/skill): fork, branch from the
  <em>agent branch</em> you target (<code>claude</code>, <code>pi</code>, …; shared content is
  cherry-picked across), and open a PR at
  <a href="{GITHUB}/pulls">{GITHUB}/pulls</a>. One rule per file, cite a canonical
  <code>postgresql.org</code> reference, keep it CC0.</li>
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
    print(f"wrote {OUT/'index.html'} — {len(skills)} skills, {total_rules} rules")


if __name__ == "__main__":
    build()
