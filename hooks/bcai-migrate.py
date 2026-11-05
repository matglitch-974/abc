#!/usr/bin/env python3
"""Migration d'une installation d'avant le renommage en BCAI (anciennement Better Claude Instance, BCI).

  bcai-migrate.py           migre ce qui peut l'être et affiche ce qui a été fait (appelé par les installateurs)
  bcai-migrate.py --check   n'écrit rien : affiche ce qui reste à migrer

Idempotent ; rien n'est supprimé (l'ancien part dans ~/ai/4-trash). Étapes :
1. ~/ai/2-tools/3-software/better-claude-instance renommé en bcai, avec un lien à l'ancien emplacement :
   les sessions Claude déjà ouvertes appellent leurs hooks par l'ancien chemin (un hook PreToolUse
   introuvable bloquerait tous leurs outils). Si bcai existe déjà, l'ancien dossier attend l'étape 6.
2. ~/ai/2-tools/logs/backup-bci repris en backup-bcai (bcai-backup.py, adopt_legacy).
3. settings.json de Claude Code : anciens chemins remplacés, après copie dans backup-bcai/reglages/.
4. Commandes : bcai installée là où bci l'était ; bci repointée sur l'alias obsolète bin/bci.
5. ~/ai/AGENTS.md et le skill memory (copiés du skeleton) : anciens chemins remplacés, après copie
   dans backup-bcai/reglages/. Les autres fichiers qui citent l'ancien chemin sont seulement signalés.
6. Rangement, par le hook mémoire seulement (retire), au démarrage d'une session dont les réglages ne
   citaient déjà plus l'ancien chemin, quand aucune autre session claude ne tourne et que le lien a plus
   de 24 h (une session ouverte avant la migration, non vue par le comptage des processus, appellerait
   encore ses hooks par l'ancien chemin ; un hook PreToolUse introuvable bloque ses outils) : le lien est retiré (il ne contient rien ; rangé
   dans 4-trash, il pointerait encore vers bcai, qu'un vidage de la corbeille pourrait suivre) ; un ancien
   dossier réel part dans 4-trash.

Variables : BCAI_AI (ou l'ancien BCI_AI) : autre racine, pour les tests (rediriger aussi HOME et USERPROFILE).
"""
import importlib.util
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):   # console Windows en cp1252 : jamais d'échec sur les accents
    try:
        _s.reconfigure(errors="replace")
    except AttributeError:
        pass

HOME = Path.home()
AI = Path(os.environ.get("BCAI_AI") or os.environ.get("BCI_AI") or HOME / "ai")
SOFT = AI / "2-tools" / "3-software"
OLD = SOFT / "better-claude-instance"   # emplacement d'avant BCAI
NEW = SOFT / "bcai"
REPO_OLD = "https://github.com/matglitch-974/better-claude-instance"
REPO_NEW = "https://github.com/matglitch-974/Better-Context-of-Agents-Instance"
CC = Path(os.environ.get("CLAUDE_CONFIG_DIR") or SOFT / "claude-code")
TRASH = AI / "4-trash"
NOWIN = {"creationflags": 0x08000000} if os.name == "nt" else {}   # CREATE_NO_WINDOW
LINK_GRACE = 24 * 3600   # âge minimal (date de l'entrée elle-même) avant de retirer l'ancien emplacement, en secondes
# Ancien chemin du dépôt dans un texte (barres obliques, contre-obliques, contre-obliques échappées en JSON)
OLD_PATH = re.compile(r"(3-software(?:/|\\\\|\\))better-claude-instance(?=[/\\\"'`\s)]|$)", re.M)
SKELETON = [AI / "AGENTS.md", AI / "2-tools" / "1-skills" / "memory" / "SKILL.md"]
SKELETON_RENAMES = [   # anciens noms dans les fichiers copiés du skeleton (chaînes exactes)
    ("3-software (better-claude-instance ;", "3-software (bcai ;"),
    ("logs (backup-bci)", "logs (backup-bcai)"),
    ("logs/backup-bci/", "logs/backup-bcai/"),
    ("hooks/bci-backup.py", "hooks/bcai-backup.py"),
]


def stamp():
    return time.strftime("%Y-%m-%d_%H-%M-%S")


def is_link(p):
    """Lien symbolique ou jonction Windows (un renommage ne déplace que le lien, pas sa cible).
    La jonction est lue dans st_reparse_tag : os.path.isjunction n'existe qu'à partir de Python 3.12."""
    try:
        st = os.lstat(p)
    except OSError:
        return False
    return stat.S_ISLNK(st.st_mode) or (os.name == "nt" and getattr(st, "st_reparse_tag", 0)
                                         == getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003))


def exists(p):
    return os.path.lexists(p)


def link(target, at):
    """Lien de compatibilité at -> target : jonction sous Windows (sans droits admin), sinon lien symbolique."""
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(at), str(target)], check=True,
                       capture_output=True, stdin=subprocess.DEVNULL, **NOWIN)
    else:
        os.symlink(target, at, target_is_directory=True)


def keep_copy(f):
    """Copie de f dans backup-bcai/reglages/ avant de l'écrire."""
    d = AI / "2-tools" / "logs" / "backup-bcai" / "reglages"
    d.mkdir(parents=True, exist_ok=True)
    dst = d / f"{f.name}_{stamp()}"
    shutil.copy2(f, dst)
    return dst


def write_atomic(path, text):
    tmp = path.with_name(path.name + ".tmp-bcai")
    tmp.write_bytes(text.encode("utf-8"))
    os.replace(tmp, path)


def settings_files():
    """settings.json de Claude Code (sous Linux, lien vers ~/ai/memory/settings.json : la cible est lue)."""
    out = []
    for f in (CC / "settings.json", AI / "memory" / "settings.json"):
        try:
            r = f.resolve()
        except OSError:
            continue
        if r.is_file() and r not in out:
            out.append(r)
    return out


def cites_old(text):
    return bool(OLD_PATH.search(text))


def step_install(check):
    if not exists(OLD) or is_link(OLD) or not OLD.is_dir():
        return []
    if exists(NEW):
        return [f"ancien dossier {OLD} : laissé en place ({NEW} existe), rangé plus tard par le hook mémoire"]
    if check:
        return [f"à renommer : {OLD} -> {NEW}"]
    OLD.rename(NEW)
    try:
        link(NEW, OLD)
        msg = f"renommé  : {OLD} -> {NEW} (lien de compatibilité à l'ancien emplacement)"
    except (OSError, subprocess.CalledProcessError) as e:
        msg = f"renommé  : {OLD} -> {NEW} (lien de compatibilité impossible : {e})"
    out = [msg]
    if (NEW / ".git").exists() and shutil.which("git"):
        r = subprocess.run(["git", "-C", str(NEW), "remote", "get-url", "origin"], capture_output=True,
                           text=True, stdin=subprocess.DEVNULL, **NOWIN)
        if r.stdout.strip().rstrip("/").removesuffix(".git") == REPO_OLD:
            subprocess.run(["git", "-C", str(NEW), "remote", "set-url", "origin", REPO_NEW],
                           capture_output=True, stdin=subprocess.DEVNULL, **NOWIN)
            out.append(f"dépôt    : origin -> {REPO_NEW}")
    return out


def step_backups(check):
    legacy = AI / "2-tools" / "logs" / "backup-bci"
    if not legacy.is_dir():
        return []
    if check:
        return [f"à reprendre : {legacy}"]
    script = Path(__file__).resolve().parent / "bcai-backup.py"
    sys.dont_write_bytecode = True   # pas de __pycache__ dans le dépôt
    spec = importlib.util.spec_from_file_location("bcai_backup", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    msg = mod.adopt_legacy()
    return [msg] if msg else []


def step_settings(check):
    if not (NEW / "hooks" / "memory-hook.py").is_file():
        return []   # pas encore de nouveau dépôt : rien vers quoi pointer
    out = []
    for f in settings_files():
        text = f.read_text(encoding="utf-8")
        if not cites_old(text):
            continue
        if check:
            out.append(f"à corriger : {f}")
            continue
        kept = keep_copy(f)
        write_atomic(f, OLD_PATH.sub(r"\1bcai", text))
        out.append(f"réglages : {f} (anciens chemins remplacés ; copie : {kept})")
    return out


def step_commands(check):
    b = HOME / ".local" / "bin"
    out = []
    if os.name == "nt":
        old, new = b / "bci.cmd", b / "bcai.cmd"
        if old.is_file() and "better-claude-instance" in old.read_text(errors="replace"):
            if check:
                return [f"à mettre à jour : {old}"]
            for name in ("bcai.cmd", "bci.cmd"):
                src = NEW / "bin" / name
                if src.is_file():
                    shutil.copyfile(src, b / name)
                    out.append(f"commande : {b / name}")
        elif old.is_file() and not new.exists() and (NEW / "bin" / "bcai.cmd").is_file() and not check:
            shutil.copyfile(NEW / "bin" / "bcai.cmd", new)
            out.append(f"commande : {new}")
        return out
    old, new = b / "bci", b / "bcai"
    if not old.is_symlink():
        return out
    if "better-claude-instance" in os.readlink(old) or not new.exists():
        if check:
            return [f"à mettre à jour : {old}"]
        for name in ("bcai", "bci"):
            src, at = NEW / "bin" / name, b / name
            if src.is_file() and (is_link(at) or not exists(at)):
                if exists(at):
                    at.unlink()
                os.symlink(src, at)
                out.append(f"commande : {at} -> {src}")
    return out


def step_skeleton(check):
    out = []
    for f in SKELETON:
        if not f.is_file() or f.is_symlink():
            continue
        text = f.read_text(encoding="utf-8")
        new = OLD_PATH.sub(r"\1bcai", text)
        for a, b in SKELETON_RENAMES:
            new = new.replace(a, b)
        if new == text:
            continue
        if check:
            out.append(f"à corriger : {f}")
            continue
        kept = keep_copy(f)
        write_atomic(f, new)
        out.append(f"chemins  : {f} (copie : {kept})")
    return out


def leftovers():
    """Autres fichiers de ~/ai (mémoire, personas, skills) qui citent encore l'ancien chemin : signalés seulement."""
    out = []
    for root in (AI / "memory", AI / "0-persona", AI / "2-tools" / "1-skills"):
        if not root.is_dir():
            continue
        for f in root.rglob("*.md"):
            if "journal" in f.parts or not f.is_file() or (f in SKELETON and not f.is_symlink()):
                continue   # skeleton : déjà traité ou signalé par step_skeleton
            try:
                if cites_old(f.read_text(encoding="utf-8", errors="replace")):
                    out.append(f"à revoir : {f} cite encore {OLD}")
            except OSError:
                continue
    return out


def retire(others):
    """Retire l'ancien emplacement si plus rien ne s'en sert : lien supprimé, dossier réel rangé dans 4-trash."""
    if not exists(OLD) or others or not (NEW / "hooks" / "memory-hook.py").is_file():
        return ""
    if any(cites_old(f.read_text(encoding="utf-8")) for f in settings_files()):
        return ""   # des sessions démarrées avec ces réglages appellent encore l'ancien chemin
    try:
        if time.time() - os.lstat(OLD).st_mtime < LINK_GRACE:
            return ""   # récent : une session ouverte avant la migration peut encore s'en servir
    except OSError:
        return ""
    if is_link(OLD):
        try:
            os.rmdir(OLD) if os.name == "nt" else os.unlink(OLD)   # jonction / lien seul, la cible reste
        except OSError:
            return ""
        return f"lien {OLD} retiré"
    TRASH.mkdir(parents=True, exist_ok=True)
    dst, i = TRASH / f"better-claude-instance_{stamp()}", 1
    while exists(dst):
        dst, i = TRASH / f"better-claude-instance_{stamp()}-{i}", i + 1
    try:
        os.rename(OLD, dst)
    except OSError:
        return ""   # encore tenu : nouvel essai au prochain démarrage
    return f"rangé dans 4-trash : {OLD} -> {dst}"


def migrate(check=False):
    """Étapes 1 à 5 ; renvoie la liste des actions (ou de ce qui reste à faire si check)."""
    out = []
    for step in (step_install, step_backups, step_settings, step_commands, step_skeleton):
        try:
            out += step(check)
        except Exception as e:   # une étape ratée n'empêche pas les suivantes
            out.append(f"échec    : {step.__name__} : {e}")
    return out


def main():
    check = "--check" in sys.argv[1:]
    lines = migrate(check) + leftovers()
    for line in lines:
        print(line)
    if check and not lines:
        print("rien à migrer")


if __name__ == "__main__":
    main()
