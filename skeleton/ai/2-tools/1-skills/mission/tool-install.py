#!/usr/bin/env python3
"""Installation automatique d'outils trouvés par la reconnaissance, avec journal et retrait.

  tool-install.py mcp <nom> <commande> [args…]   agent mcp add -s user <nom> -- <commande> [args…]
  tool-install.py skill <url-git> [sous-dossier]  copie le dossier contenant SKILL.md dans ~/ai/2-tools/1-skills/
  tool-install.py remove <nom>                    MCP : agent mcp remove ; skill : déplacé dans ~/ai/4-trash/
  tool-install.py log                             tout ce qui a été installé

Journal : ~/ai/2-tools/installed.md (date, type, nom, source).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AI = Path(os.environ.get("ABC_AI") or os.environ.get("BCAI_AI") or Path.home() / "ai")
SKILLS = AI / "2-tools" / "1-skills"
LOG = AI / "2-tools" / "installed.md"
TRASH = AI / "4-trash"


# Commande de Claude Code : agent (renommée par ABC), ou claude si gardée sous ce nom ; ABC_CLI force le choix.
CLI = os.environ.get("ABC_CLI") or ("agent" if shutil.which("agent") else "claude")


def log(kind, name, src):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    new = not LOG.exists()
    with open(LOG, "a", encoding="utf-8") as f:
        if new:
            f.write("# Outils installés automatiquement\n\n")
        f.write(f"- {time.strftime('%Y-%m-%d %H:%M')} | {kind} | {name} | {src}\n")


def logged(name):
    if not LOG.exists():
        return None
    for line in reversed(LOG.read_text(encoding="utf-8").splitlines()):
        p = [x.strip() for x in line.lstrip("- ").split("|")]
        if len(p) >= 3 and p[2] == name:
            return p[1]
    return None


def mcp(name, cmd):
    if subprocess.run([CLI, "mcp", "get", name], capture_output=True).returncode == 0:
        print(f"déjà présent : {name}")
        return 0
    r = subprocess.run([CLI, "mcp", "add", "-s", "user", name, "--", *cmd])
    if r.returncode == 0:
        log("mcp", name, " ".join(cmd))
        print(f"installé : MCP {name} (actif à la prochaine session)")
    return r.returncode


def skill(url, sub=""):
    with tempfile.TemporaryDirectory() as tmp:
        if subprocess.run(["git", "clone", "-q", "--depth", "1", url, tmp]).returncode:
            return 1
        base = Path(tmp) / sub
        found = [p.parent for p in base.rglob("SKILL.md") if ".git" not in p.parts]
        if not found:
            print("aucun SKILL.md trouvé", file=sys.stderr)
            return 1
        for src in found:
            dst = SKILLS / src.name.lower()
            if dst.exists():
                print(f"déjà présent : {dst.name}")
                continue
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git"))
            log("skill", dst.name, f"{url} {src.relative_to(tmp).as_posix()}")
            print(f"installé : skill {dst.name}")
    return 0


def remove(name):
    kind = logged(name)
    if kind == "mcp":
        r = subprocess.run([CLI, "mcp", "remove", "-s", "user", name]).returncode
    elif kind == "skill" and (SKILLS / name).exists():
        TRASH.mkdir(parents=True, exist_ok=True)
        shutil.move(str(SKILLS / name), str(TRASH / f"{name}-{time.strftime('%Y%m%d%H%M%S')}"))
        r = 0
    else:
        print(f"{name} : absent du journal ou déjà retiré", file=sys.stderr)
        return 1
    if r == 0:
        log("retiré", name, kind)
        print(f"retiré : {name}")
    return r


def main():
    a = sys.argv[1:]
    if a[:1] == ["mcp"] and len(a) >= 3:
        return mcp(a[1], a[2:])
    if a[:1] == ["skill"] and len(a) in (2, 3):
        return skill(a[1], a[2] if len(a) == 3 else "")
    if a[:1] == ["remove"] and len(a) == 2:
        return remove(a[1])
    if a == ["log"]:
        print(LOG.read_text(encoding="utf-8") if LOG.exists() else "(rien d'installé)")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
