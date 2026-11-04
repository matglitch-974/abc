#!/usr/bin/env python3
"""Hook mémoire de Better Claude Instance — automate sans LLM, branché sur les événements de Claude Code.

- Journal : chaque événement utile est ajouté aussitôt à ~/ai/memory/journal/AAAA-MM-JJ.md.
  Une fermeture brutale ne perd donc rien de ce qui a déjà eu lieu.
- Todos : au démarrage de session, la section « Projets » de ~/ai/memory/TODO.md est
  réécrite à partir des TODO.md de ~/project.
- Sauvegarde : au démarrage, bci-backup.py quotidienne (une par jour, en arrière-plan).
- Ancien ~/.claude : s'il était encore tenu par une session lors de l'installation, il est rangé
  dans ~/ai/4-trash au démarrage suivant (toute session le recréant est rangée de même).
- Persona : le premier message de la session choisit le persona par `@<nom>` (fichier de
  ~/ai/0-persona/, catégories comprises) ; sans `@`, c'est `slave`. Réinjecté après compaction.
- Isolement : un persona dont l'en-tête porte `isolated: true` ouvre une session cloisonnée dans
  les deux sens (mémoire propre dans ~/ai/isolated/<nom>/, accès croisés bloqués en PreToolUse).
- Réalignement : ~/ai/memory/realign.md est réinjecté dans le contexte tous les N messages
  de l'utilisateur (BCI_REALIGN_EVERY, 10 par défaut) et après chaque compaction.

Usage : appelé par Claude Code (JSON sur stdin), ou `memory-hook.py todo` pour le seul sommaire.
Ne bloque jamais Claude Code : toute erreur est ignorée, code de sortie toujours 0.
"""
import json
import os
import re
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


ISO = AI / "isolated"        # agents isolés : ~/ai/isolated/<nom>/ (mémoire, journal, sessions)
JOURNAL = MEM / "journal"    # session isolée : redirigé vers ISO/<nom>/journal par handle()


def isolated(sid):
    """Nom de l'agent isolé de cette session, ou ''."""
    p = MEM / ".state" / f"{sid}.isolated"
    return p.read_text(encoding="utf-8").strip() if p.is_file() else ""


def journal(line):
    d = JOURNAL
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"{time.strftime('%Y-%m-%d')}.md", "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%H:%M:%S')} {line}\n")


def realign():
    p = MEM / "realign.md"
    if not p.is_file():
        return ""
    text = p.read_text(encoding="utf-8").strip()
    return f"Rappel de réalignement (~/ai/memory/realign.md) :\n\n{text}\n" if text else ""


def persona(sid, prompt=None):
    """Premier message : `@<nom>` choisit le persona (défaut : slave). Sinon : celui déjà choisi."""
    state = MEM / ".state" / f"{sid}.persona"
    root = AI / "0-persona"
    note = ""
    if prompt is not None:
        m = re.match(r"\s*@([^\s/\\]+)", prompt or "")
        name = m.group(1) if m else "slave"
        found = [f for f in sorted(root.rglob("*")) if f.is_file() and name in (f.name, f.stem)]
        if not found and name != "slave":
            note = f"(Persona « {name} » introuvable dans ~/ai/0-persona : slave par défaut.)\n"
            found = [f for f in sorted(root.rglob("*")) if f.is_file() and f.stem == "slave"]
        if not found:
            return note
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(str(found[0]), encoding="utf-8")
        head = re.match(r"\A---\n(.*?)\n---\n", found[0].read_text(encoding="utf-8"), flags=re.S)
        if head and re.search(r"^isolated:\s*true\s*$", head.group(1), flags=re.M):
            d = ISO / found[0].stem
            (d / "journal").mkdir(parents=True, exist_ok=True)
            (MEM / ".state" / f"{sid}.isolated").write_text(found[0].stem, encoding="utf-8")
            with open(d / "sessions", "a", encoding="utf-8") as fh:   # transcripts à cacher aux autres
                fh.write(sid + "\n")
    if not state.is_file():
        return ""
    f = Path(state.read_text(encoding="utf-8").strip())
    if not f.is_file():
        return note
    text = re.sub(r"\A---\n.*?\n---\n", "", f.read_text(encoding="utf-8"), flags=re.S).strip()
    iso = isolated(sid)
    if iso:
        return (f"{note}Session ISOLÉE — agent {iso} ({f}). Isolement informationnel dans les deux sens : "
                f"n'utiliser ni ~/ai/AGENTS.md, ni ~/ai/memory (INDEX, TODO, journal, souvenirs), ni les autres "
                f"personas, même s'ils figurent déjà dans le contexte ; l'accès en est bloqué. Seule mémoire : "
                f"{ISO / iso}/ (notes dans memory.md, journal automatique). L'incarner jusqu'à la fin de la "
                f"session :\n\n{text}\n")
    return (f"{note}Persona de cette session : {f.stem} ({f}). L'utilisateur s'adresse à lui ; "
            f"l'incarner jusqu'à la fin de la session :\n\n{text}\n")


def guard(event, sid):
    """PreToolUse : cloison entre agents isolés et le reste. Retourne un motif de blocage ou ''."""
    ti = event.get("tool_input") or {}
    text = " ".join(str(v) for v in ti.values() if isinstance(v, str)).replace("\\", "/")
    iso = isolated(sid)
    if iso:
        mine = f"/ai/isolated/{iso}"
        others = re.sub(re.escape(mine), "", text)
        if re.search(r"/ai/(memory|AGENTS\.md|0-persona|isolated/)", others) or re.search(r"(^|[\s\"'])(memory|0-persona)/", others):
            return f"session isolée ({iso}) : seul ~/ai/isolated/{iso}/ est accessible, pas la mémoire commune ni les autres agents."
        return ""
    if "/ai/isolated" in text:
        return "~/ai/isolated/ appartient aux agents isolés : inaccessible depuis cette session."
    hidden = [s.strip() for p in ISO.glob("*/sessions") for s in p.read_text(encoding="utf-8").split() if s.strip()]
    if any(h in text for h in hidden):
        return "ce transcript appartient à une session isolée : inaccessible depuis cette session."
    return ""


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


def backup():
    """Sauvegarde quotidienne (bci-backup.py), détachée pour ne pas retarder le démarrage de la session."""
    import subprocess
    script = Path(__file__).resolve().parent / "bci-backup.py"
    kw = {"start_new_session": True} if os.name != "nt" else {"creationflags": 0x00000008}  # DETACHED_PROCESS
    subprocess.Popen([sys.executable, str(script), "quotidienne", "--if-needed"],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
    return "lancée (quotidienne, si pas encore faite aujourd'hui)"


def retire_old():
    """Range ~/.claude et ~/.claude.json laissés en cache par une session ouverte pendant l'installation."""
    cc = AI / "2-tools" / "3-software" / "claude-code"
    if Path(os.environ.get("CLAUDE_CONFIG_DIR") or "/").resolve() != cc.resolve():
        return ""
    stamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    done = []
    for name, label in ((".claude", "claude-ancien"), (".claude.json", "claude.json-ancien")):
        old = Path.home() / name
        if old.exists() and not old.is_symlink():
            try:
                old.rename(AI / "4-trash" / f"{label}_{stamp}")
                done.append(name)
            except OSError:
                pass   # encore tenu : nouvel essai au prochain démarrage
    return ", ".join(done)


def handle(event):
    name = event.get("hook_event_name", "")
    sid = str(event.get("session_id", "") or "sans-id")
    tag = f"[{sid[:8]}]"
    out = ""
    global JOURNAL
    if name == "PreToolUse":
        return guard(event, sid), True
    if isolated(sid):
        JOURNAL = ISO / isolated(sid) / "journal"
    if name == "SessionStart":
        src = event.get("source", "")
        journal(f"{tag} session démarrée ({src})")
        todo_sync()
        if src == "startup":
            journal(f"{tag} sauvegarde : {backup()}")
            retired = retire_old()
            if retired:
                journal(f"{tag} rangé dans 4-trash : {retired}")
            out = "Début de session : reconnaissance des outils (skill `mission`) avant la première tâche.\n"
        if src == "compact":
            out = (persona(sid) if isolated(sid) else realign() + persona(sid))
    elif name == "UserPromptSubmit":
        n = count_prompt(sid)
        if n == 1:   # persona choisi avant d'écrire : le message d'un agent isolé ne touche pas le journal commun
            out = persona(sid, event.get("prompt") or "")
            if isolated(sid):
                JOURNAL = ISO / isolated(sid) / "journal"
        journal(f"{tag} utilisateur : {short(event.get('prompt'))}")
        if EVERY > 0 and n % EVERY == 0 and not isolated(sid):
            out += realign()
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
        (MEM / ".state" / f"{sid}.persona").unlink(missing_ok=True)
        (MEM / ".state" / f"{sid}.isolated").unlink(missing_ok=True)
    return out, False


def main():
    if sys.argv[1:] == ["todo"]:
        todo_sync()
        return
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
        out, blocking = handle(event)
        if blocking:   # PreToolUse : code 2 = outil refusé, motif sur stderr
            if out:
                sys.stderr.buffer.write(f"Bloqué par l'isolement des agents : {out}\n".encode("utf-8"))
                sys.stderr.flush()
                os._exit(2)
            return
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
