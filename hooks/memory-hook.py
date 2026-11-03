#!/usr/bin/env python3
"""Hook mémoire de Better Claude Instance — automate sans LLM, branché sur les événements de Claude Code.

- Journal : chaque événement utile est ajouté aussitôt à ~/ai/memory/journal/AAAA-MM-JJ.md.
  Une fermeture brutale ne perd donc rien de ce qui a déjà eu lieu.
- Todos : au démarrage de session, la section « Projets » de ~/ai/memory/TODO.md est
  réécrite à partir des TODO.md de ~/project.
- Réalignement : ~/ai/memory/realign.md est réinjecté dans le contexte tous les N messages
  de l'utilisateur (BCI_REALIGN_EVERY, 10 par défaut) et après chaque compaction.

Usage : appelé par Claude Code (JSON sur stdin), ou `memory-hook.py todo` pour le seul sommaire.
Ne bloque jamais Claude Code : toute erreur est ignorée, code de sortie toujours 0.
"""
import json
import os
import sys
import time
from pathlib import Path

AI = Path(os.environ.get("BCI_AI") or Path.home() / "ai")   # BCI_AI : autre racine (tests)
MEM = AI / "memory"
PROJECTS = Path.home() / "project"
EVERY = int(os.environ.get("BCI_REALIGN_EVERY", "10") or 10)
BEGIN = "<!-- projets:début"
END = "<!-- projets:fin -->"


def short(text, n=200):
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def journal(line):
    d = MEM / "journal"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"{time.strftime('%Y-%m-%d')}.md", "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%H:%M:%S')} {line}\n")


def realign():
    p = MEM / "realign.md"
    if not p.is_file():
        return ""
    text = p.read_text(encoding="utf-8").strip()
    return f"Rappel de réalignement (~/ai/memory/realign.md) :\n\n{text}\n" if text else ""


def count_prompt(sid):
    d = MEM / ".state"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{sid}.count"
    n = int(p.read_text() or 0) + 1 if p.is_file() else 1
    p.write_text(str(n))
    return n


def write_atomic(path, text):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def todo_sync():
    """Réécrit la section Projets de TODO.md : une entrée par TODO.md de ~/project avec ses tâches ouvertes."""
    target = MEM / "TODO.md"
    if not target.is_file():
        return
    blocks = []
    if PROJECTS.is_dir():
        for todo in sorted(PROJECTS.rglob("TODO.md")):
            rel = todo.parent.relative_to(PROJECTS).as_posix()
            if any(part in (".git", "sensible", "node_modules") for part in todo.parts):
                continue
            items = [l.strip() for l in todo.read_text(encoding="utf-8", errors="replace").splitlines()
                     if l.strip().startswith("- [ ]")]
            if items:
                blocks.append(f"### {rel} — {len(items)} ouverte(s)\n" + "\n".join(items))
    body = "\n\n".join(blocks) if blocks else "(aucune tâche ouverte dans ~/project)"
    old = target.read_text(encoding="utf-8")
    i, j = old.find(BEGIN), old.find(END)
    if i < 0 or j < i:
        return
    head = old[: old.index("\n", i) + 1]
    new = f"{head}{body}\n{old[j:]}"
    if new != old:
        write_atomic(target, new)


def handle(event):
    name = event.get("hook_event_name", "")
    sid = str(event.get("session_id", "") or "sans-id")
    tag = f"[{sid[:8]}]"
    out = ""
    if name == "SessionStart":
        src = event.get("source", "")
        journal(f"{tag} session démarrée ({src})")
        todo_sync()
        if src == "compact":
            out = realign()
    elif name == "UserPromptSubmit":
        journal(f"{tag} utilisateur : {short(event.get('prompt'))}")
        if EVERY > 0 and count_prompt(sid) % EVERY == 0:
            out = realign()
    elif name == "PostToolUse":
        ti = event.get("tool_input") or {}
        path = ti.get("file_path") or ti.get("notebook_path")
        if path:
            journal(f"{tag} {event.get('tool_name', 'outil')} : {path}")
    elif name == "PreCompact":
        journal(f"{tag} compaction ({event.get('trigger', '')})")
    elif name == "Stop":
        last = event.get("last_assistant_message")
        journal(f"{tag} fin de tour" + (f" : {short(last)}" if last else ""))
    elif name == "SessionEnd":
        journal(f"{tag} session terminée ({event.get('reason', '')})")
        (MEM / ".state" / f"{sid}.count").unlink(missing_ok=True)
    return out


def main():
    if sys.argv[1:] == ["todo"]:
        todo_sync()
        return
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
        out = handle(event)
        if out:
            sys.stdout.buffer.write(out.encode("utf-8"))
    except Exception as e:  # le journal ne doit jamais bloquer la session
        try:
            journal(f"[hook] erreur : {short(e)}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
    sys.exit(0)
