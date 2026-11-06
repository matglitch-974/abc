#!/usr/bin/env python3
"""Audit du contexte chargé à chaque session : tokens par fichier, doublons, sections à sortir en skill.

ctx-audit.py            estimation (2,3 octets par token : calibré sur Claude, texte français, 2026-11-03)
ctx-audit.py --exact    mesure réelle : une session `agent -p` (ou `claude -p`) par fichier, comparée à une session vide
                        (consomme un peu de quota ; modèle : ABC_AUDIT_MODEL, haiku par défaut)

Chargé à chaque session : ~/ai/AGENTS.md et ses imports @ (récursifs), memory/realign.md (réinjecté),
la ligne description de chaque skill.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AI = Path(os.environ.get("ABC_AI") or os.environ.get("BCAI_AI") or Path.home() / "ai")   # ABC_AI : autre racine (tests)
BYTES_PER_TOKEN = 2.3
SECTION_LIMIT = 300  # tokens : au-delà, une section est candidate à devenir un skill
MODEL = os.environ.get("ABC_AUDIT_MODEL") or os.environ.get("BCAI_AUDIT_MODEL") or "haiku"


# Commande de Claude Code : agent (renommée par ABC), ou claude si gardée sous ce nom ; ABC_CLI force le choix.
CLI = os.environ.get("ABC_CLI") or ("agent" if shutil.which("agent") else "claude")


def imports(path, seen):
    """AGENTS.md et ses @imports, hors blocs de code et commentaires HTML."""
    path = path.resolve()
    if path in seen or not path.is_file():
        return
    seen.append(path)
    text = re.sub(r"```.*?```|<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
    for m in re.finditer(r"^@(\S+)", text, re.M):
        ref = m.group(1)
        if ref.startswith("~/ai/"):
            target = AI / ref[5:]
        elif ref.startswith("~"):
            target = Path(ref.replace("~", str(Path.home()), 1))
        else:
            target = path.parent / ref
        imports(target, seen)


def exact_tokens(text, base=None):
    def run(body):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(body)
        out = subprocess.run([CLI, "-p", "ok", "--system-prompt-file", f.name, "--tools", "",
                              "--setting-sources", "", "--strict-mcp-config", "--model", MODEL,
                              "--output-format", "json"], capture_output=True, text=True, encoding="utf-8")
        Path(f.name).unlink(missing_ok=True)
        res = json.loads(out.stdout or "{}")
        if res.get("is_error") or not res.get("usage", {}).get("input_tokens"):
            sys.exit(f"Mesure impossible : {res.get('result') or out.stderr.strip() or f'{CLI} -p sans réponse'}")
        u = res["usage"]
        return u["input_tokens"] + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
    return run(text) - (base if base is not None else run("."))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    exact = "--exact" in sys.argv
    files = []
    imports(AI / "AGENTS.md", files)
    realign = AI / "memory" / "realign.md"
    def label(p):
        try:
            return "~/ai/" + p.relative_to(AI.resolve()).as_posix()
        except ValueError:
            return str(p)
    entries = [(label(p), p.read_text(encoding="utf-8")) for p in files]
    if realign.is_file():
        entries.append(("~/ai/memory/realign.md (tous les 10 messages)", realign.read_text(encoding="utf-8")))
    desc = "\n".join(l for s in sorted((AI / "2-tools" / "1-skills").glob("*/SKILL.md"))
                     for l in s.read_text(encoding="utf-8").splitlines() if l.startswith("description:"))
    entries.append(("descriptions des skills", desc))

    base = exact_tokens(".", 0) if exact else None
    count = (lambda t: exact_tokens(t, base)) if exact else (lambda t: round(len(t.encode("utf-8")) / BYTES_PER_TOKEN))
    total = 0
    print(f"{'fichier':60s} tokens ({'mesurés' if exact else 'estimés'})")
    for name, text in entries:
        n = count(text)
        total += n
        print(f"{name:60s} {n:6d}")
    print(f"{'TOTAL':60s} {total:6d}")

    print("\nSections longues (candidates à un skill) :")
    for name, text in entries:
        for sec in re.split(r"\n(?=## )", text):
            n = round(len(sec.encode("utf-8")) / BYTES_PER_TOKEN)
            if n > SECTION_LIMIT and sec.startswith("## "):
                print(f"  {name} :: {sec.splitlines()[0]}  ~{n}")

    print("\nLignes répétées d'un fichier à l'autre :")
    where = {}
    for name, text in entries:
        for line in {l.strip() for l in text.splitlines() if len(l.strip()) > 40}:
            where.setdefault(line, []).append(name)
    dups = [(l, n) for l, n in where.items() if len(n) > 1]
    for line, names in dups:
        print(f"  « {line[:70]} » : {', '.join(names)}")
    if not dups:
        print("  aucune")


if __name__ == "__main__":
    main()
