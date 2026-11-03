#!/usr/bin/env python3
"""Code à 4 chiffres d'un sous-agent, de son lancement à son arrêt.

agent-id.py new [nom]       tire un code libre, le réserve, affiche « <nom>-<code> » (nom par défaut : slave)
agent-id.py release <code>  libère le code (accepte aussi « <nom>-<code> »)
agent-id.py list            affiche les codes réservés

Registre : un fichier ~/ai/1-bench/<code>.id par sous-agent vivant.
La création exclusive du fichier empêche deux sous-agents d'obtenir le même code.
"""
import os
import random
import sys
from pathlib import Path

BENCH = Path.home() / "ai" / "1-bench"


def new(name):
    BENCH.mkdir(parents=True, exist_ok=True)
    codes = [f"{n:04d}" for n in range(10000)]
    random.shuffle(codes)
    for code in codes:
        try:
            fd = os.open(BENCH / f"{code}.id", os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(name + "\n")
        print(f"{name}-{code}")
        return 0
    print("Aucun code libre.", file=sys.stderr)
    return 1


def release(arg):
    code = arg.rsplit("-", 1)[-1]
    if not (len(code) == 4 and code.isdigit()):
        print(f"Code invalide : {arg}", file=sys.stderr)
        return 1
    (BENCH / f"{code}.id").unlink(missing_ok=True)
    return 0


def list_ids():
    for p in sorted(BENCH.glob("[0-9][0-9][0-9][0-9].id")):
        print(f"{p.read_text(encoding='utf-8').strip()}-{p.stem}")
    return 0


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "new":
        return new(argv[2] if len(argv) > 2 else "slave")
    if cmd == "release" and len(argv) > 2:
        return release(argv[2])
    if cmd == "list":
        return list_ids()
    print("usage : agent-id.py new [nom] | release <code> | list", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
