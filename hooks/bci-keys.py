#!/usr/bin/env python3
"""Coffre chiffré de ~/ai/2-tools/4-keys-code (clés SSH, jetons, clés d'API, cookies) — restic >= 0.17.

  bci-keys.py close    chiffre 4-keys-code dans 4-keys-code.restic, vérifie, puis efface la version en clair
                       (premier appel : crée le coffre, phrase secrète demandée deux fois)
  bci-keys.py open     déchiffre le coffre dans 4-keys-code
  bci-keys.py status   ouvert / fermé / non chiffré

Phrase secrète : demandée au terminal, ou BCI_KEYS_PASSWORD. Phrase oubliée = secrets perdus.
"""
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):   # console Windows en cp1252 : jamais d'échec sur « → » ou les accents
    try:
        _s.reconfigure(errors="replace")
    except AttributeError:
        pass

AI = Path(os.environ.get("BCI_AI") or Path.home() / "ai")
KEYS = AI / "2-tools" / "4-keys-code"
VAULT = AI / "2-tools" / "4-keys-code.restic"


def password(confirm=False):
    pw = os.environ.get("BCI_KEYS_PASSWORD")
    if pw:
        return pw
    pw = getpass.getpass("Phrase secrète de 4-keys-code : ")
    if confirm and getpass.getpass("Confirmez : ") != pw:
        sys.exit("Les deux saisies diffèrent : rien n'a été chiffré.")
    if not pw:
        sys.exit("Phrase vide refusée.")
    return pw


def restic(pw, *args, cwd=None):
    exe = shutil.which("restic")
    if not exe:
        sys.exit("restic introuvable : installez-le (bci install), puis relancez.")
    return subprocess.run([exe, "-r", str(VAULT), *args], cwd=cwd, capture_output=True, text=True,
                          env={**os.environ, "RESTIC_PASSWORD": pw})


def close():
    if not KEYS.is_dir():
        sys.exit("4-keys-code est déjà fermé (ou absent).")
    new = not (VAULT / "config").is_file()
    pw = password(confirm=new)
    if new:
        r = restic(pw, "init")
        if r.returncode:
            sys.exit(f"restic init : {r.stderr.strip()[:300]}")
    r = restic(pw, "backup", ".", "--tag", "4-keys-code", cwd=KEYS)
    if r.returncode:   # 3 = fichiers illisibles : on n'efface rien
        sys.exit(f"restic backup : {r.stderr.strip()[:300]}\nRien n'a été effacé.")
    local = sum(1 for f in KEYS.rglob("*") if f.is_file())
    ls = restic(pw, "ls", "latest", "--json")
    saved = ls.stdout.count('"type":"file"')
    if ls.returncode or saved != local:
        sys.exit(f"Vérification échouée ({saved} fichiers chiffrés pour {local} en clair) : rien n'a été effacé.")
    restic(pw, "forget", "--keep-last", "3", "--prune")
    shutil.rmtree(KEYS)
    print(f"4-keys-code chiffré ({local} fichiers) et fermé : {VAULT}")


def open_():
    if KEYS.is_dir():
        sys.exit("4-keys-code est déjà ouvert.")
    if not (VAULT / "config").is_file():
        sys.exit("Aucun coffre : 4-keys-code n'a jamais été chiffré.")
    pw = password()
    KEYS.mkdir(parents=True)
    r = restic(pw, "restore", "latest", "--target", str(KEYS))
    if r.returncode:
        shutil.rmtree(KEYS, ignore_errors=True)
        sys.exit(f"restic restore : {r.stderr.strip()[:300]}")
    print(f"4-keys-code ouvert : {KEYS}  (refermer : bci keys close)")


def status():
    vault = (VAULT / "config").is_file()
    print("ouvert (chiffré à la fermeture)" if vault and KEYS.is_dir() else
          "fermé (chiffré)" if vault else "non chiffré" if KEYS.is_dir() else "absent")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"close": close, "open": open_, "status": status}.get(cmd, lambda: print(__doc__))()
