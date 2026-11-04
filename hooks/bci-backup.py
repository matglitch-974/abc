#!/usr/bin/env python3
"""Sauvegardes de Better Claude Instance — restic >= 0.17 (dédupliqué, compressé), sinon repli tar.xz.

  bci-backup.py quotidienne [--if-needed]   sauvegarde du jour, rotation « tour de Hanoï »
  bci-backup.py install-avant | install-apres   première installation seulement, conservées à vie
  bci-backup.py list

Contenu : tout ~/ai (sauf les sauvegardes elles-mêmes) ; install-avant ajoute ~/.claude et ~/.claude.json
s'ils existent encore. Destination : ~/ai/2-tools/logs/backup-bci/
  .restic/                          dépôt restic commun (sans mot de passe : données locales)
  .backup_AAAA-MM-JJ[_type]/meta.json   un dossier par sauvegarde : date à la seconde, versions, instantané
Rotation (quotidienne) : la sauvegarde n° k va dans le jeu h = zéros terminaux de k en binaire (plafonné à
SETS-1) et remplace l'ancienne de ce jeu ; elles s'espacent avec l'âge (au plus SETS sauvegardes).
Ne bloque jamais : code de sortie 0, erreurs consignées dans backup-bci/errors.log.
"""
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

HOME = Path.home()
AI = Path(os.environ.get("BCI_AI") or HOME / "ai")
DEST = AI / "2-tools" / "logs" / "backup-bci"
REPO = DEST / ".restic"
SETS = max(1, int(os.environ.get("BCI_BACKUP_SETS", "8") or 8))
SRC_DIR = Path(__file__).resolve().parent.parent  # dépôt better-claude-instance
TYPES = ("quotidienne", "install-avant", "install-apres")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=kw.pop("timeout", 30), **kw)


def version(cmd):
    exe = shutil.which(cmd[0])
    if not exe:
        return None
    try:
        out = run([exe] + cmd[1:])
        text = (out.stdout or out.stderr).strip().splitlines()
        return text[0][:120] if text else None
    except Exception:
        return None


def versions():
    bci = None
    if (SRC_DIR / ".git").exists():
        try:
            out = run(["git", "-C", str(SRC_DIR), "log", "-1", "--format=%h %cI"])
            bci = out.stdout.strip() or None
        except Exception:
            pass
    return {
        "bci": bci,
        "claude_code": version(["claude", "--version"]),
        "tweakcc": version(["tweakcc", "--version"]),
        "node": version(["node", "--version"]),
        "python": platform.python_version(),
        "git": version(["git", "--version"]),
        "jq": version(["jq", "--version"]),
        "uv": version(["uv", "--version"]),
        "restic": version(["restic", "version"]),
        "systeme": f"{platform.system()} {platform.release()} {platform.machine()}",
    }


def restic_ok():
    """restic utilisable : présent et >= 0.17 (option --insecure-no-password)."""
    v = version(["restic", "version"]) or ""
    try:
        major, minor = (int(x) for x in v.split()[1].split(".")[:2])
    except (IndexError, ValueError):
        return False
    return (major, minor) >= (0, 17)


def restic(*args, timeout=3600):
    return run(["restic", "-r", str(REPO), "--insecure-no-password", *args], timeout=timeout)


def folders():
    out = []
    for d in sorted(DEST.glob(".backup_*")):
        try:
            out.append((d, json.loads((d / "meta.json").read_text(encoding="utf-8"))))
        except (OSError, ValueError):
            continue
    return out


def backup(kind, if_needed=False):
    DEST.mkdir(parents=True, exist_ok=True)
    day = time.strftime("%Y-%m-%d")
    done = [m for _, m in folders() if m.get("type") == kind]
    if kind != "quotidienne" and done:   # installation : une seule paire, celle de la première installation
        return None
    if if_needed and any(m.get("date", "").startswith(day) for m in done):
        return None
    name = f".backup_{day}" + ("" if kind == "quotidienne" else f"_{kind}")
    d, n = DEST / name, 2
    while d.exists():
        d, n = DEST / f"{name}_{n}", n + 1
    sources = [p for p in (AI, HOME / ".claude", HOME / ".claude.json")
               if p.exists() and (p == AI or kind == "install-avant") and not p.is_symlink()]
    if not sources:
        return None
    meta = {"nom": d.name, "type": kind, "date": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "sources": [str(p) for p in sources], "versions": versions()}
    d.mkdir()
    # 4-keys-code chiffré : sa version en clair (ouverte) ne va jamais dans les sauvegardes, le coffre si
    keys = AI / "2-tools" / "4-keys-code"
    vaulted = (AI / "2-tools" / "4-keys-code.restic" / "config").is_file()
    excl = ["--exclude", str(keys)] if vaulted else []
    if restic_ok():
        if not (REPO / "config").exists():
            r = restic("init")
            if r.returncode:
                raise RuntimeError(f"restic init : {r.stderr.strip()[:300]}")
        r = restic("backup", "--json", "--compression", "max", "--tag", d.name,
                   "--exclude", str(DEST), *excl, *map(str, sources))
        summary = [json.loads(l) for l in r.stdout.splitlines() if '"message_type":"summary"' in l]
        if r.returncode not in (0, 3) or not summary:  # 3 = fichiers illisibles ignorés, instantané créé
            shutil.rmtree(d)
            raise RuntimeError(f"restic backup : {r.stderr.strip()[:300]}")
        meta["restic"] = {"instantane": summary[0].get("snapshot_id"),
                          "ajoute_octets": summary[0].get("data_added"),
                          "fichiers": summary[0].get("total_files_processed")}
    else:
        arch = d / "data.tar.xz"
        with tarfile.open(arch, "w:xz", preset=9) as tar:
            for p in sources:
                tar.add(p, arcname=p.name, filter=lambda ti: None if ti.name.startswith(
                    f"{AI.name}/2-tools/logs/backup-bci") or (vaulted and ti.name.startswith(
                    f"{AI.name}/2-tools/4-keys-code/")) or (vaulted and ti.name == f"{AI.name}/2-tools/4-keys-code")
                    else ti)
        meta["archive"] = {"fichier": arch.name, "octets": arch.stat().st_size}
    if kind == "quotidienne":
        counter = DEST / "counter"
        k = int(counter.read_text() or 0) + 1 if counter.is_file() else 1
        meta["rotation"] = {"numero": k, "jeu": min((k & -k).bit_length() - 1, SETS - 1)}
        counter.write_text(str(k))
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    if kind == "quotidienne":
        rotate(d, meta["rotation"]["jeu"])
    return d


def rotate(new, jeu):
    """Remplace l'ancienne sauvegarde quotidienne du même jeu (les sauvegardes d'installation ne tournent pas)."""
    old = [(d, m) for d, m in folders() if d != new and m.get("type") == "quotidienne"
           and (m.get("rotation") or {}).get("jeu") == jeu]
    for d, m in old:
        snap = (m.get("restic") or {}).get("instantane")
        if snap and restic_ok():
            restic("forget", snap)
        shutil.rmtree(d)
    if old and restic_ok():
        restic("prune", timeout=7200)


def main():
    a = sys.argv[1:]
    try:
        if a[:1] == ["list"]:
            for d, m in folders():
                print(f"{d.name}  {m.get('type')}  {m.get('date')}  "
                      f"{(m.get('restic') or {}).get('instantane') or (m.get('archive') or {}).get('fichier')}")
            return
        if not a or a[0] not in TYPES:
            print(__doc__)
            return
        d = backup(a[0], if_needed="--if-needed" in a)
        print(d if d else "rien à sauvegarder")
    except Exception as e:
        try:
            DEST.mkdir(parents=True, exist_ok=True)
            with open(DEST / "errors.log", "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {' '.join(a)} : {e}\n")
        except OSError:
            pass
        print(f"sauvegarde échouée : {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
    sys.exit(0)
