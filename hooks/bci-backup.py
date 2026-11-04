#!/usr/bin/env python3
"""Sauvegardes de Better Claude Instance — restic >= 0.17 (dédupliqué, compressé), sinon repli tar.xz.

  bci-backup.py quotidienne [--if-needed]   sauvegarde du jour, rotation « tour de Hanoï »
  bci-backup.py install-avant | install-apres   première installation seulement, conservées à vie
  bci-backup.py list

Contenu : tout ~/ai (sauf les sauvegardes elles-mêmes) ; install-avant ajoute ~/.claude et ~/.claude.json
s'ils existent encore. Destination : ~/ai/2-tools/logs/backup-bci/
  .restic/                          dépôt restic commun (sans mot de passe : données locales)
  .backup_AAAA-MM-JJ[_type]/meta.json   un dossier par sauvegarde : date à la seconde, versions, instantané
  .backup_…/metadata.json           copie lisible de la métadonnée embarquée (ci-dessous)
Métadonnée : metadata.json à la racine de l'instantané restic (/metadata.json) ou de l'archive tar.xz :
version de BCI (fichier VERSION + commit git), date, système, type, versions des dépendances (« absent »
si non installée), noms des MCP et des skills. Aucun secret ; le dossier personnel est écrit ~.
Rotation (quotidienne) : la sauvegarde n° k va dans le jeu h = zéros terminaux de k en binaire (plafonné à
SETS-1) et remplace l'ancienne de ce jeu ; elles s'espacent avec l'âge (au plus SETS sauvegardes).
Ne bloque jamais : code de sortie 0, erreurs consignées dans backup-bci/errors.log.
"""
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HOME = Path.home()
AI = Path(os.environ.get("BCI_AI") or HOME / "ai")
DEST = AI / "2-tools" / "logs" / "backup-bci"
REPO = DEST / ".restic"
SETS = max(1, int(os.environ.get("BCI_BACKUP_SETS", "8") or 8))
SRC_DIR = Path(__file__).resolve().parent.parent  # dépôt better-claude-instance
TYPES = ("quotidienne", "install-avant", "install-apres")
CC = Path(os.environ.get("CLAUDE_CONFIG_DIR") or AI / "2-tools" / "3-software" / "claude-code")
NOWIN = {"creationflags": 0x08000000} if os.name == "nt" else {}  # CREATE_NO_WINDOW : pas de console qui clignote


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=kw.pop("timeout", 30),
                          stdin=subprocess.DEVNULL, **NOWIN, **kw)


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


def versions(md):
    """Résumé des versions pour meta.json, tiré de la métadonnée complète (aucune commande relancée)."""
    b, dep = md.get("bci") or {}, md.get("dependances") or {}
    bci = " ".join(x for x in (b.get("version"), (b.get("commit") or "")[:7], b.get("date_commit")) if x)
    sysi = md.get("systeme") or {}
    out = {"bci": bci or None, "python": dep.get("python")}
    for k in ("claude_code", "node", "git", "jq", "uv", "restic"):
        out[k] = None if dep.get(k) in (None, "absent") else dep.get(k)
    out["systeme"] = f"{sysi.get('nom')} {sysi.get('publication')} {sysi.get('arch')}"
    return out


def tilde(s):
    """Remplace le dossier personnel par ~ (pas de nom d'utilisateur dans la métadonnée)."""
    if not isinstance(s, str):
        return s
    for h in {str(HOME), HOME.as_posix()}:
        s = s.replace(h, "~")
    return s


def quick(cmd, timeout=10):
    """(code, sortie) de `cmd`, tué après `timeout` s. Sortie dans un fichier temporaire, pas un tube : un
    sous-processus resté ouvert après le délai ne peut pas bloquer la sauvegarde."""
    with tempfile.TemporaryFile() as out:
        p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT, **NOWIN)
        try:
            rc = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            raise
        out.seek(0)
        return rc, out.read().decode("utf-8", "replace")


def tool(cmd, lines=1, timeout=10):
    """Premières lignes non vides de `cmd` ; « absent » si introuvable, « erreur (…) » si elle échoue."""
    exe = shutil.which(cmd[0])
    if not exe:
        return "absent"
    try:
        rc, out = quick([exe] + cmd[1:], timeout)
    except Exception as e:
        return f"erreur ({type(e).__name__})"
    text = [l.strip() for l in out.splitlines() if l.strip()]
    if rc or not text:
        return f"erreur (code {rc})"
    return tilde(" ; ".join(text[:lines])[:160])


def uv_tools():
    """Versions des outils Python installés par `uv tool` (scrapling, crawl4ai : leur --version est lent)."""
    found = {}
    exe = shutil.which("uv")
    if exe:
        try:
            for l in quick([exe, "tool", "list"], 15)[1].splitlines():
                parts = l.split()
                if len(parts) >= 2 and not l.startswith("-"):
                    found[parts[0].lower()] = parts[1]
        except Exception:
            pass
    return found


def bci_version():
    v = {"version": None, "commit": None, "date_commit": None, "modifie": None}
    try:
        v["version"] = (SRC_DIR / "VERSION").read_text(encoding="utf-8").strip() or None
    except OSError:
        pass
    if (SRC_DIR / ".git").exists() and shutil.which("git"):
        try:
            out = run(["git", "-C", str(SRC_DIR), "log", "-1", "--format=%H %cI"], timeout=10).stdout.split()
            if len(out) == 2:
                v["commit"], v["date_commit"] = out
            st = run(["git", "-C", str(SRC_DIR), "status", "--porcelain", "--untracked-files=no"], timeout=10)
            v["modifie"] = bool(st.stdout.strip()) if st.returncode == 0 else None
        except Exception:
            pass
    return v


def system_info():
    s = {"nom": platform.system(), "publication": platform.release(), "version": platform.version(),
         "arch": platform.machine()}
    try:
        if s["nom"] == "Linux":
            s["distribution"] = platform.freedesktop_os_release().get("PRETTY_NAME")
        elif s["nom"] == "Windows":
            s["edition"] = platform.win32_edition()
    except Exception:
        pass
    if os.environ.get("TERMUX_VERSION") or Path("/data/data/com.termux").exists():
        s["termux"] = True
    return s


def mcp_names():
    """Noms des serveurs MCP déclarés (utilisateur et projets) : ni commandes, ni en-têtes, ni env."""
    names = set()
    for f in (CC / ".claude.json", HOME / ".claude.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        names.update((d.get("mcpServers") or {}).keys())
        for proj in (d.get("projects") or {}).values():
            if isinstance(proj, dict):
                names.update((proj.get("mcpServers") or {}).keys())
    return sorted(names)


def skill_names():
    return sorted(p.parent.name for p in (AI / "2-tools" / "1-skills").glob("*/SKILL.md"))


def metadata(kind, name, date):
    """Métadonnée embarquée dans chaque sauvegarde ; aucune erreur ne remonte (commandes en parallèle, 10 s max)."""
    cmds = {"claude_code": ["claude", "--version"], "node": ["node", "--version"], "npm": ["npm", "--version"],
            "git": ["git", "--version"], "restic": ["restic", "version"], "uv": ["uv", "--version"],
            "jq": ["jq", "--version"], "ripgrep": ["rg", "--version"], "curl": ["curl", "--version"],
            "bash": ["bash", "--version"]}
    if os.name == "nt":
        ps = "$PSVersionTable.PSVersion.ToString()"
        cmds.update({"powershell": ["powershell", "-NoProfile", "-Command", ps],
                     "pwsh": ["pwsh", "-NoProfile", "-Command", ps], "winget": ["winget", "--version"]})
    m = {"format": 1, "nom": name, "type": kind, "date": date}
    dep = {"python": platform.python_version()}
    with ThreadPoolExecutor(max_workers=8) as ex:
        # claude --version : deuxième ligne = tweakcc s'il a modifié Claude Code
        jobs = {k: ex.submit(tool, c, 2 if k == "claude_code" else 1) for k, c in cmds.items()}
        uvt, bci = ex.submit(uv_tools), ex.submit(bci_version)
        for k, f in jobs.items():
            try:
                dep[k] = f.result()
            except Exception:
                dep[k] = "erreur"
        try:
            u = uvt.result()
        except Exception:
            u = {}
        for k in ("scrapling", "crawl4ai"):
            dep[k] = u.get(k, "absent")
        try:
            m["bci"] = bci.result()
        except Exception:
            m["bci"] = None
    for k, f in (("systeme", system_info), ("mcp", mcp_names), ("skills", skill_names)):
        try:
            m[k] = f()
        except Exception:
            m[k] = None
    m["dependances"] = dep
    return m


def restic_ok():
    """restic utilisable : présent et >= 0.17 (option --insecure-no-password)."""
    v = version(["restic", "version"]) or ""
    try:
        major, minor = (int(x) for x in v.split()[1].split(".")[:2])
    except (IndexError, ValueError):
        return False
    return (major, minor) >= (0, 17)


def restic(*args, timeout=3600, **kw):
    return run(["restic", "-r", str(REPO), "--insecure-no-password", *args], timeout=timeout, **kw)


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
    date = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    use_restic = restic_ok()
    try:
        md = metadata(kind, d.name, date)
    except Exception as e:  # la métadonnée ne fait jamais échouer la sauvegarde
        md = {"format": 1, "nom": d.name, "type": kind, "date": date, "erreur": type(e).__name__}
    md["mode"] = "restic" if use_restic else "tar.xz"
    md["sources"] = [tilde(str(p)) for p in sources]
    md_bytes = (json.dumps(md, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    meta = {"nom": d.name, "type": kind, "date": date,
            "sources": [str(p) for p in sources], "versions": versions(md)}
    d.mkdir()
    (d / "metadata.json").write_bytes(md_bytes)
    # 4-keys-code chiffré : sa version en clair (ouverte) ne va jamais dans les sauvegardes, le coffre si
    keys = AI / "2-tools" / "4-keys-code"
    vaulted = (AI / "2-tools" / "4-keys-code.restic" / "config").is_file()
    excl = ["--exclude", str(keys)] if vaulted else []
    if use_restic:
        if not (REPO / "config").exists():
            r = restic("init")
            if r.returncode:
                raise RuntimeError(f"restic init : {r.stderr.strip()[:300]}")
        # metadata.json donné en chemin relatif depuis un dossier temporaire : restic le range à la racine
        # de l'instantané (/metadata.json), à côté des sources
        with tempfile.TemporaryDirectory(prefix="bci-meta-") as tmp:
            (Path(tmp) / "metadata.json").write_bytes(md_bytes)
            r = restic("backup", "--json", "--compression", "max", "--tag", d.name,
                       "--exclude", str(DEST), *excl, "metadata.json", *map(str, sources), cwd=tmp)
        summary = [json.loads(l) for l in r.stdout.splitlines() if '"message_type":"summary"' in l]
        if r.returncode not in (0, 3) or not summary:  # 3 = fichiers illisibles ignorés, instantané créé
            shutil.rmtree(d)
            raise RuntimeError(f"restic backup : {r.stderr.strip()[:300]}")
        meta["restic"] = {"instantane": summary[0].get("snapshot_id"),
                          "ajoute_octets": summary[0].get("data_added"),
                          "fichiers": summary[0].get("total_files_processed")}
    else:
        arch = d / "data.tar.xz"
        skip = [DEST] + ([AI / "2-tools" / "4-keys-code"] if vaulted else [])
        missed = 0
        with tarfile.open(arch, "w:xz", preset=9) as tar:
            info = tarfile.TarInfo("metadata.json")
            info.size, info.mtime, info.mode = len(md_bytes), int(time.time()), 0o644
            tar.addfile(info, io.BytesIO(md_bytes))
            # parcours fichier par fichier : un lien cassé ou un fichier verrouillé est sauté, pas fatal
            for p in sources:
                if p.is_file():
                    tar.add(p, arcname=p.name)
                    continue
                for root, dirs, files in os.walk(p):
                    r = Path(root)
                    dirs[:] = [x for x in dirs if r / x not in skip]
                    for name in files:
                        f = r / name
                        try:
                            tar.add(f, arcname=str(Path(p.name) / f.relative_to(p)), recursive=False)
                        except OSError:
                            missed += 1
        meta["archive"] = {"fichier": arch.name, "octets": arch.stat().st_size, "fichiers_sautes": missed}
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
