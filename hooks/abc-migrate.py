#!/usr/bin/env python3
"""Migration d'une installation d'avant le renommage en ABC (Agents with a Better Context).

Anciens noms : BCAI (dossier 3-software/bcai, commande bcai, sauvegardes backup-bcai) et, avant lui,
Better Claude Instance, BCI (dossier 3-software/better-claude-instance, commande bci, backup-bci).

  abc-migrate.py           migre ce qui peut l'être et affiche ce qui a été fait (appelé par les installateurs)
  abc-migrate.py --check   n'écrit rien : affiche ce qui reste à migrer

Idempotent ; rien n'est supprimé (l'ancien part dans ~/ai/4-trash). Étapes :
1. Ancien dossier du dépôt (bcai, ou better-claude-instance) renommé en abc, avec un lien à l'ancien
   emplacement : les sessions déjà ouvertes appellent leurs hooks par l'ancien chemin (un hook PreToolUse
   introuvable bloquerait tous leurs outils). Si abc existe déjà, l'ancien dossier attend l'étape 6.
   Le dépôt Git est repointé vers https://github.com/matglitch-974/abc.
2. Anciennes sauvegardes (backup-bcai, backup-bci) reprises dans backup-abc (abc-backup.py, adopt_legacy).
3. settings.json de Claude Code : anciens chemins remplacés, après copie dans backup-abc/reglages/.
4. Commandes : abc installée là où bcai ou bci l'était ; bcai devient le renvoi obsolète bin/bcai
   (une version) ; bci part dans 4-trash.
5. ~/ai/AGENTS.md et le skill memory (copiés du skeleton) : anciens chemins et noms remplacés, après copie
   dans backup-abc/reglages/. Les autres fichiers qui citent un ancien chemin sont seulement signalés.
6. Rangement, par le hook mémoire seulement (retire), au démarrage d'une session dont les réglages ne
   citaient déjà plus d'ancien chemin, quand aucune autre session ne tourne et que le lien a plus de 24 h
   (une session ouverte avant la migration, non vue par le comptage des processus, appellerait encore ses
   hooks par l'ancien chemin) : le lien est retiré (il ne contient rien ; rangé dans 4-trash, il pointerait
   encore vers abc, qu'un vidage de la corbeille pourrait suivre) ; un ancien dossier réel part dans 4-trash.

Variables : ABC_AI (ou l'ancien BCAI_AI) : autre racine, pour les tests (rediriger aussi HOME et USERPROFILE).
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
AI = Path(os.environ.get("ABC_AI") or os.environ.get("BCAI_AI") or HOME / "ai")
SOFT = AI / "2-tools" / "3-software"
OLD_NAMES = ("bcai", "better-claude-instance")   # BCAI, puis BCI
OLDS = [SOFT / n for n in OLD_NAMES]
NEW = SOFT / "abc"
REPO_NEW = "https://github.com/matglitch-974/abc"
REPO_OLDS = [f"https://github.com/matglitch-974/{n}" for n in OLD_NAMES]
CC = Path(os.environ.get("CLAUDE_CONFIG_DIR") or SOFT / "claude-code")
BIN = HOME / ".local" / "bin"
TRASH = AI / "4-trash"
NOWIN = {"creationflags": 0x08000000} if os.name == "nt" else {}   # CREATE_NO_WINDOW
LINK_GRACE = 24 * 3600   # âge minimal (date de l'entrée elle-même) avant de retirer l'ancien emplacement, en secondes
# Ancien chemin du dépôt dans un texte (barres obliques, contre-obliques, contre-obliques échappées en JSON)
OLD_PATH = re.compile(r"(3-software(?:/|\\\\|\\))(?:bcai|better-claude-instance)(?=[/\\\"'`\s)]|$)", re.M)
SKELETON = [AI / "AGENTS.md", AI / "2-tools" / "1-skills" / "memory" / "SKILL.md"]
SKELETON_RENAMES = [   # anciens noms dans les fichiers copiés du skeleton (motifs exacts)
    (re.compile(r"3-software \((?:bcai|better-claude-instance) ;"), "3-software (abc ;"),
    (re.compile(r"logs \(backup-bc(?:a)?i\)"), "logs (backup-abc)"),
    (re.compile(r"logs/backup-bc(?:a)?i/"), "logs/backup-abc/"),
    (re.compile(r"hooks/bc(?:a)?i-backup\.py"), "hooks/abc-backup.py"),
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


def to_trash(p, label):
    """Range p (fichier, lien ou dossier) dans 4-trash sous label_<date>."""
    TRASH.mkdir(parents=True, exist_ok=True)
    dst, i = TRASH / f"{label}_{stamp()}", 1
    while exists(dst):
        dst, i = TRASH / f"{label}_{stamp()}-{i}", i + 1
    os.rename(p, dst)
    return dst


def keep_copy(f):
    """Copie de f dans backup-abc/reglages/ avant de l'écrire."""
    d = AI / "2-tools" / "logs" / "backup-abc" / "reglages"
    d.mkdir(parents=True, exist_ok=True)
    dst = d / f"{f.name}_{stamp()}"
    shutil.copy2(f, dst)
    return dst


def write_atomic(path, text):
    tmp = path.with_name(path.name + ".tmp-abc")
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


def pending():
    """Reste-t-il une trace d'ancien nom (dossier ou lien du dépôt, anciennes sauvegardes) ?"""
    logs = AI / "2-tools" / "logs"
    return any(exists(o) for o in OLDS) or any((logs / n).exists() for n in ("backup-bcai", "backup-bci"))


def step_install(check):
    out = []
    for old in OLDS:
        if not exists(old) or is_link(old) or not old.is_dir():
            continue
        if exists(NEW):
            out.append(f"ancien dossier {old} : laissé en place ({NEW} existe), rangé plus tard par le hook mémoire")
            continue
        if check:
            out.append(f"à renommer : {old} -> {NEW}")
            continue
        old.rename(NEW)
        try:
            link(NEW, old)
            out.append(f"renommé  : {old} -> {NEW} (lien de compatibilité à l'ancien emplacement)")
        except (OSError, subprocess.CalledProcessError) as e:
            out.append(f"renommé  : {old} -> {NEW} (lien de compatibilité impossible : {e})")
    if (NEW / ".git").exists() and shutil.which("git"):
        r = subprocess.run(["git", "-C", str(NEW), "remote", "get-url", "origin"], capture_output=True,
                           text=True, stdin=subprocess.DEVNULL, **NOWIN)
        if r.stdout.strip().rstrip("/").removesuffix(".git") in REPO_OLDS:
            if check:
                out.append(f"à repointer : origin -> {REPO_NEW}")
            else:
                subprocess.run(["git", "-C", str(NEW), "remote", "set-url", "origin", REPO_NEW],
                               capture_output=True, stdin=subprocess.DEVNULL, **NOWIN)
                out.append(f"dépôt    : origin -> {REPO_NEW}")
    return out


def step_backups(check):
    logs = AI / "2-tools" / "logs"
    legacy = [logs / n for n in ("backup-bcai", "backup-bci") if (logs / n).is_dir() and not is_link(logs / n)]
    if not legacy:
        return []
    if check:
        return [f"à reprendre : {d}" for d in legacy]
    script = Path(__file__).resolve().parent / "abc-backup.py"
    sys.dont_write_bytecode = True   # pas de __pycache__ dans le dépôt
    spec = importlib.util.spec_from_file_location("abc_backup", script)
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
        write_atomic(f, OLD_PATH.sub(r"\1abc", text))
        out.append(f"réglages : {f} (anciens chemins remplacés ; copie : {kept})")
    return out


def step_commands(check):
    """abc installée là où bcai ou bci l'était ; bcai remplacée par le renvoi obsolète ; bci rangée."""
    if os.name == "nt":
        names = {"abc": "abc.cmd", "bcai": "bcai.cmd", "bci": "bci.cmd"}
    else:
        names = {"abc": "abc", "bcai": "bcai", "bci": "bci"}
    at = {k: BIN / v for k, v in names.items()}
    if not (exists(at["bcai"]) or exists(at["bci"])):
        return []
    src = {k: NEW / "bin" / names[k] for k in ("abc", "bcai")}
    if not all(s.is_file() for s in src.values()):
        return []

    def stale(k):
        """La commande installée diffère-t-elle de celle du dépôt ?"""
        if not exists(at[k]):
            return True
        if os.name == "nt":
            return at[k].read_bytes() != src[k].read_bytes()
        return not (at[k].is_symlink() and Path(os.readlink(at[k])) == src[k])

    todo = [k for k in ("abc", "bcai") if (k == "abc" or exists(at[k])) and stale(k)]
    if exists(at["bci"]):
        todo.append("bci")
    if not todo:
        return []
    if check:
        return [f"à mettre à jour : {at[k]}" for k in todo]
    out = []
    for k in todo:
        if k == "bci":
            out.append(f"commande : {at[k]} rangée dans {to_trash(at[k], 'commande-bci')}")
            continue
        if os.name == "nt":
            # Un .cmd en cours d'exécution (bcai install) est relu par cmd.exe à la même position :
            # le renvoi bin/bcai.cmd est plus court que l'ancien bcai.cmd, la suite lue est vide.
            shutil.copyfile(src[k], at[k])
            out.append(f"commande : {at[k]}")
        else:
            if exists(at[k]) and not is_link(at[k]):
                to_trash(at[k], f"commande-{k}")
            elif exists(at[k]):
                at[k].unlink()   # lien seul
            os.symlink(src[k], at[k])
            out.append(f"commande : {at[k]} -> {src[k]}")
    return out


def step_skeleton(check):
    out = []
    for f in SKELETON:
        if not f.is_file() or f.is_symlink():
            continue
        text = f.read_text(encoding="utf-8")
        new = OLD_PATH.sub(r"\1abc", text)
        for a, b in SKELETON_RENAMES:
            new = a.sub(b, new)
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
    """Autres fichiers de ~/ai (mémoire, personas, skills) qui citent encore un ancien chemin : signalés seulement."""
    out = []
    for root in (AI / "memory", AI / "0-persona", AI / "2-tools" / "1-skills"):
        if not root.is_dir():
            continue
        for f in root.rglob("*.md"):
            if "journal" in f.parts or not f.is_file() or (f in SKELETON and not f.is_symlink()):
                continue   # skeleton : déjà traité ou signalé par step_skeleton
            try:
                if cites_old(f.read_text(encoding="utf-8", errors="replace")):
                    out.append(f"à revoir : {f} cite encore un ancien chemin du dépôt")
            except OSError:
                continue
    return out


def retire(others):
    """Retire les anciens emplacements si plus rien ne s'en sert : lien supprimé, dossier réel rangé dans 4-trash."""
    if others or not (NEW / "hooks" / "memory-hook.py").is_file():
        return ""
    if any(cites_old(f.read_text(encoding="utf-8")) for f in settings_files()):
        return ""   # des sessions démarrées avec ces réglages appellent encore un ancien chemin
    done = []
    for old in OLDS:
        if not exists(old):
            continue
        try:
            if time.time() - os.lstat(old).st_mtime < LINK_GRACE:
                continue   # récent : une session ouverte avant la migration peut encore s'en servir
        except OSError:
            continue
        if is_link(old):
            try:
                os.rmdir(old) if os.name == "nt" else os.unlink(old)   # jonction / lien seul, la cible reste
            except OSError:
                continue
            done.append(f"lien {old} retiré")
            continue
        try:
            done.append(f"rangé dans 4-trash : {old} -> {to_trash(old, old.name)}")
        except OSError:
            continue   # encore tenu : nouvel essai au prochain démarrage
    return " ; ".join(done)


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
