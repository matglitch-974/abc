#!/usr/bin/env python3
"""Inventaire des outils disponibles (local) et recherche de candidats (en ligne). Sans dépendance.

  tool-scan.py local [mots…]    skills, MCP, plugins et agents installés ; avec des mots, filtrés et classés
  tool-scan.py online <mots…>   registre officiel MCP + GitHub (dépôts MCP et skills), classés par étoiles

Sortie compacte, une ligne par outil, faite pour être lue par un LLM.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HOME = Path.home()
CL = Path(os.environ.get("CLAUDE_CONFIG_DIR") or HOME / ".claude")  # configuration de Claude Code


def words(args):
    return [w.lower() for w in args if w.strip()]


def score(text, ws):
    t = text.lower()
    return sum(t.count(w) for w in ws)


def front(path):
    """name et description du front matter d'un SKILL.md ou d'un agent."""
    try:
        txt = path.read_text(encoding="utf-8", errors="replace")[:3000]
    except OSError:
        return None, ""
    m = re.match(r"---\s*\n(.*?)\n---", txt, re.S)
    meta = m.group(1) if m else ""
    name = re.search(r"^name:\s*(.+)$", meta, re.M)
    desc = re.search(r"^description:\s*(.+)$", meta, re.M)
    return (name.group(1).strip() if name else path.parent.name), (desc.group(1).strip() if desc else "")


def mcp_servers():
    out = {}
    for f in (CL / ".claude.json", HOME / ".claude.json", Path.cwd() / ".mcp.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        out.update(d.get("mcpServers") or {})
        proj = (d.get("projects") or {}).get(str(Path.cwd())) or {}
        out.update(proj.get("mcpServers") or {})
    return out


def local(ws):
    rows = []
    seen = set()
    for root, kind in ((CL / "skills", "skill"), (CL / "plugins", "plugin-skill"), (CL / "agents", "agent")):
        if not root.exists():
            continue
        pat = "*.md" if kind == "agent" else "SKILL.md"
        for p in root.rglob(pat):
            if kind == "agent" and p.name in ("README.md",):
                continue
            name, desc = front(p)
            key = (kind, name)
            if name and key not in seen:
                seen.add(key)
                rows.append((kind, name, desc, str(p.parent)))
    for name, cfg in mcp_servers().items():
        cmd = " ".join([cfg.get("command", "")] + list(cfg.get("args") or [])) or cfg.get("url", "")
        rows.append(("mcp", name, cmd, ""))
    if ws:
        rows = [r for r in rows if score(" ".join(r[1:3]), ws)]
        rows.sort(key=lambda r: -score(" ".join(r[1:3]), ws))
    for kind, name, desc, where in rows:
        print(f"{kind} | {name} | {desc[:160]}")
    print(f"# {len(rows)} outil(s) local(aux)")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "bcai-tool-scan", "Accept": "application/json"})
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def online(ws):
    q = " ".join(ws)
    try:
        servers = []
        # le registre cherche une sous-chaîne : requête entière, puis chaque mot si elle ne donne rien
        for term in [q] + (ws if len(ws) > 1 else []):
            servers += get("https://registry.modelcontextprotocol.io/v0/servers?limit=20&search="
                           + urllib.parse.quote(term)).get("servers", [])
            if servers and term == q:
                break
        seen = set()
        for s in servers:
            sv = s.get("server", {})
            if sv.get("name") in seen:
                continue
            seen.add(sv.get("name"))
            how = [p.get("registryType", "") + ":" + p.get("identifier", "") for p in sv.get("packages") or []]
            how += ["remote:" + r.get("url", "") for r in sv.get("remotes") or []]
            secret = any(e.get("isSecret") for p in sv.get("packages") or [] for e in p.get("environmentVariables") or []) \
                or any(h.get("isSecret") for r in sv.get("remotes") or [] for h in r.get("headers") or [])
            print(f"registre-mcp | {sv.get('name')} | {sv.get('version', '')} | {'CLÉ' if secret else 'sans-clé'} | "
                  f"{' '.join(how)[:120]} | {(sv.get('description') or '')[:120]}")
    except Exception as e:
        print(f"# registre MCP indisponible : {e}")
    for suffix, label in ((" mcp", "github-mcp"), (" claude skill", "github-skill")):
        try:
            d = get("https://api.github.com/search/repositories?sort=stars&per_page=8&q="
                    + urllib.parse.quote(q + suffix))
            for r in d.get("items", []):
                lic = (r.get("license") or {}).get("spdx_id") or "?"
                arch = " ARCHIVÉ" if r.get("archived") else ""
                print(f"{label} | {r['full_name']} | ★{r['stargazers_count']} | {lic} | màj {r['pushed_at'][:10]}{arch} | "
                      f"{(r.get('description') or '')[:120]}")
        except Exception as e:
            print(f"# GitHub indisponible ({label}) : {e}")


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("local", "online") or (a[0] == "online" and len(a) < 2):
        print(__doc__)
        sys.exit(1)
    (local if a[0] == "local" else online)(words(a[1:]))


if __name__ == "__main__":
    main()
