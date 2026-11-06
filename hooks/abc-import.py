#!/usr/bin/env python3
"""Import de l'existant dans ABC — appelé par install.ps1 / bootstrap.sh avant la migration.

Tout est COPIÉ (les originaux restent, les outils continuent de marcher), sauf les modèles Ollama,
déplacés une seule fois pour ne pas doubler des gigaoctets.

  abc-import.py skills    skills de ~/.claude/skills -> ~/ai/2-tools/1-skills
                           nom déjà pris : le skill importé devient <nom>1 (puis 2, 3…), ligne ajoutée à TODO.md
  abc-import.py agents    agents de ~/.claude/agents -> ~/ai/0-persona (sélection par @<nom>) ; même règle de conflit
  abc-import.py secrets   clés SSH, variables secrètes, identifiants d'outils, cookies -> ~/ai/2-tools/4-keys-code
  abc-import.py llm       configs des autres LLM -> ~/ai/3-llm/<outil> ; modèles Ollama -> ABC_MODELS_DIR
  abc-import.py all       les trois (plus l'ancien 2-tools/0-mcp/sensible versé dans 4-keys-code)

Variables : ABC_AI (autre racine, tests), ABC_MODELS_DIR (modèles ; défaut ~/ai/3-llm/models).
Idempotent : relancer ne duplique rien. Fichiers secrets ignorés si 4-keys-code est chiffré et fermé.
"""
import hashlib
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):   # console Windows en cp1252 : jamais d'échec sur « -> » ou les accents
    try:
        _s.reconfigure(errors="replace")
    except AttributeError:
        pass

HOME = Path.home()
AI = Path(os.environ.get("ABC_AI") or os.environ.get("BCAI_AI") or HOME / "ai")
SKILLS = AI / "2-tools" / "1-skills"
KEYS = AI / "2-tools" / "4-keys-code"
VAULT = AI / "2-tools" / "4-keys-code.restic"
LLM = AI / "3-llm"
WIN = os.name == "nt"
SECRET_NAME = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|PASSWD|API", re.I)
SECRET_FILE = re.compile(r"^(id_[^.]+|.*\.(pem|key|p12|pfx)|.*credential.*|auth\.json|oauth.*\.json|\.env.*|token.*)$", re.I)
SKIP_ENV = re.compile(r"^CLAUDE_CODE_(MESSAGING|SESSION|BRIDGE|CHILD)", re.I)
BIG = 100 * 1024 * 1024   # au-delà : fichier signalé dans llms.md, pas copié (poids de modèles)


def is_link(p):
    """Lien symbolique ou jonction Windows. La jonction est lue dans st_reparse_tag : os.path.isjunction
    n'existe qu'à partir de Python 3.12 et Path.is_symlink() ne voit pas les jonctions."""
    try:
        st = os.lstat(p)
    except OSError:
        return False
    return stat.S_ISLNK(st.st_mode) or (os.name == "nt" and getattr(st, "st_reparse_tag", 0)
                                         == getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003))


def say(msg):
    print(f"import   : {msg}")


def tree_hash(p):
    h = hashlib.sha256()
    for f in sorted(x for x in p.rglob("*") if x.is_file()):
        h.update(str(f.relative_to(p)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def private(path):
    """Droits restreints au propriétaire (sans effet notable sous Windows : profil déjà privé)."""
    try:
        os.chmod(path, 0o700 if Path(path).is_dir() else 0o600)
    except OSError:
        pass


def copy_any(src, dst, skip=None):
    """Copie fichier ou dossier ; fichiers verrouillés sautés. skip(path) -> True pour ignorer."""
    src, dst = Path(src), Path(dst)
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
        except OSError:
            say(f"sauté (verrouillé) : {src}")
        return
    for f in src.rglob("*"):
        if not f.is_file() or (skip and skip(f)):
            continue
        t = dst / f.relative_to(src)
        t.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(f, t)
        except OSError:
            say(f"sauté (verrouillé) : {f}")


# --- Skills ---------------------------------------------------------------------------
def todo_line(text):
    todo = AI / "memory" / "TODO.md"
    if not todo.is_file():
        return
    s = todo.read_text(encoding="utf-8")
    line = f"- [ ] {text}"
    if line in s:
        return
    s = s.replace("## Transverse\n", f"## Transverse\n{line}\n", 1) if "## Transverse\n" in s else s + f"\n{line}\n"
    todo.write_text(s, encoding="utf-8")


def import_skills(src=None):
    src = Path(src) if src else HOME / ".claude" / "skills"
    if not src.is_dir() or is_link(src):
        return
    SKILLS.mkdir(parents=True, exist_ok=True)
    for sk in sorted(p for p in src.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()):
        h = tree_hash(sk)
        name, n = sk.name, 0
        target = SKILLS / name
        # déjà importé (marque .abc-import, ou .bcai-import et .bci-import des anciens noms), ou identique au skill de même nom : rien à faire
        if (target.is_dir() and tree_hash(target) == h) or any(
                (c / m).is_file() and (c / m).read_text().strip() == h
                for c in SKILLS.iterdir() if c.is_dir() for m in (".abc-import", ".bcai-import", ".bci-import")):
            continue
        while target.exists():
            n += 1
            target = SKILLS / f"{sk.name}{n}"
        shutil.copytree(sk, target)
        (target / ".abc-import").write_text(h + "\n")   # empreinte de l'original : pas de réimport
        if n:
            md = target / "SKILL.md"
            md.write_text(re.sub(r"^(name:\s*).*$", rf"\g<1>{target.name}", md.read_text(encoding="utf-8"),
                                 count=1, flags=re.M), encoding="utf-8")
            todo_line(f"Conflit de skills : « {sk.name} » existait déjà dans ABC ; le vôtre est renommé "
                      f"« {target.name} » ({target}). Fusionner, garder les deux ou en retirer un.")
            say(f"skill {sk.name} -> {target.name} (conflit noté dans TODO.md)")
        else:
            say(f"skill {name}")


def import_agents(src=None):
    """Agents de ~/.claude/agents -> ~/ai/0-persona (choisis par @<nom>) ; nom pris : <nom>1, 2… + TODO.md."""
    src = Path(src) if src else HOME / ".claude" / "agents"
    if not src.is_dir() or is_link(src):
        return
    root = AI / "0-persona"
    root.mkdir(parents=True, exist_ok=True)
    taken = {f.stem: f for f in root.rglob("*.md")}
    for ag in sorted(src.rglob("*.md")):
        if any(is_link(p) for p in [ag, *ag.parents] if src in p.parents or p == src):
            continue   # liens ABC (0-persona, ancien system-agents)
        data = ag.read_bytes()
        if any(f.read_bytes() == data for f in taken.values()):
            continue
        name, n = ag.stem, 0
        while name in taken:
            n += 1
            name = f"{ag.stem}{n}"
        dst = root / f"{name}.md"
        dst.write_bytes(data)
        taken[name] = dst
        if n:
            todo_line(f"Conflit d'agents : « {ag.stem} » existait déjà dans 0-persona ; le vôtre est renommé "
                      f"« {name} » ({dst}).")
        say(f"agent {ag.stem} -> 0-persona/{name}.md")


# --- Secrets --------------------------------------------------------------------------
def vault_closed():
    return VAULT.is_dir() and not KEYS.is_dir()


def env_secrets():
    found = {}
    if WIN:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            i = 0
            while True:
                try:
                    n, v, _ = winreg.EnumValue(k, i)
                except OSError:
                    break
                found[n] = str(v)
                i += 1
    else:
        found = dict(os.environ)
    return {k: v for k, v in found.items() if SECRET_NAME.search(k) and not SKIP_ENV.match(k) and v}


def firefox_profiles():
    base = (Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles") if WIN \
        else HOME / ".mozilla" / "firefox"
    return [p for p in base.glob("*") if (p / "cookies.sqlite").is_file()] if base.is_dir() else []


def export_firefox(profile, out):
    """cookies.sqlite (+ WAL) copié à part puis exporté au format Netscape (cookies.txt : yt-dlp, curl…)."""
    with tempfile.TemporaryDirectory() as td:
        for ext in ("", "-wal", "-shm"):
            f = profile / f"cookies.sqlite{ext}"
            if f.is_file():
                shutil.copy2(f, Path(td) / f.name)
        con = sqlite3.connect(Path(td) / "cookies.sqlite")
        rows = con.execute("SELECT host, path, isSecure, expiry, name, value FROM moz_cookies").fetchall()
        con.close()
    lines = ["# Netscape HTTP Cookie File"]
    for host, path, secure, expiry, name, value in rows:
        exp = int(expiry) // 1000 if expiry and expiry > 10**11 else int(expiry or 0)  # ms -> s selon version
        lines.append("\t".join([host, "TRUE" if host.startswith(".") else "FALSE", path,
                                "TRUE" if secure else "FALSE", str(exp), name, value]))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    private(out)
    return len(rows)


def chromium_dirs():
    if WIN:
        la = Path(os.environ.get("LOCALAPPDATA", ""))
        cands = {"chrome": la / "Google/Chrome/User Data", "edge": la / "Microsoft/Edge/User Data",
                 "brave": la / "BraveSoftware/Brave-Browser/User Data"}
    else:
        c = HOME / ".config"
        cands = {"chrome": c / "google-chrome", "chromium": c / "chromium", "edge": c / "microsoft-edge",
                 "brave": c / "BraveSoftware/Brave-Browser"}
    return {k: v for k, v in cands.items() if v.is_dir()}


def import_secrets():
    if vault_closed():
        say("4-keys-code est chiffré et fermé : secrets non réimportés (abc keys open, puis relancer)")
        return
    KEYS.mkdir(parents=True, exist_ok=True)
    private(KEYS)
    # ancien emplacement des clés MCP (sensible/ est désormais réservé aux projets)
    old = AI / "2-tools" / "0-mcp" / "sensible"
    if old.is_dir() and any(old.iterdir()):
        copy_any(old, KEYS / "mcp")
        trash = AI / "4-trash" / f"0-mcp-sensible_{time.strftime('%Y-%m-%d_%H-%M-%S')}"
        shutil.move(str(old), str(trash))
        say("2-tools/0-mcp/sensible -> 4-keys-code/mcp (original dans 4-trash)")
    elif old.is_dir():
        old.rmdir()
    # clés SSH
    if (HOME / ".ssh").is_dir():
        copy_any(HOME / ".ssh", KEYS / "ssh")
        say("~/.ssh -> 4-keys-code/ssh")
    # variables d'environnement secrètes (noms contenant KEY, TOKEN, SECRET, PASSWORD, API)
    env = env_secrets()
    if env:
        f = KEYS / "env" / "secrets.env"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("".join(f"{k}={v}\n" for k, v in sorted(env.items())), encoding="utf-8")
        private(f)
        say(f"{len(env)} variable(s) secrète(s) -> 4-keys-code/env/secrets.env : {', '.join(sorted(env))}")
    # identifiants d'outils
    appdata = Path(os.environ.get("APPDATA", HOME / "AppData/Roaming"))
    tools = {".git-credentials": HOME / ".git-credentials", ".netrc": HOME / ".netrc", "_netrc": HOME / "_netrc",
             "docker/config.json": HOME / ".docker/config.json", ".npmrc": HOME / ".npmrc",
             ".pypirc": HOME / ".pypirc", "pip/pip.conf": HOME / ".config/pip/pip.conf",
             "pip/pip.ini": appdata / "pip/pip.ini", "aws": HOME / ".aws", "kube/config": HOME / ".kube/config",
             "rclone/rclone.conf": HOME / ".config/rclone/rclone.conf",
             "gh/hosts.yml": (appdata / "GitHub CLI/hosts.yml") if WIN else HOME / ".config/gh/hosts.yml",
             "claude/.credentials.json": HOME / ".claude/.credentials.json",
             "claude/.claude.json": HOME / ".claude.json"}
    got = []
    for rel, src in tools.items():
        if src.exists():
            copy_any(src, KEYS / "tools" / rel)
            got.append(rel)
    gh = shutil.which("gh") or (r"C:\Program Files\GitHub CLI\gh.exe" if WIN else None)
    if gh and Path(gh).exists():
        r = subprocess.run([gh, "auth", "token"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            t = KEYS / "tools" / "gh" / "token"
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text(r.stdout.strip() + "\n", encoding="utf-8")
            got.append("gh/token")
    if got:
        say("identifiants d'outils -> 4-keys-code/tools : " + ", ".join(got))
    # cookies
    for p in firefox_profiles():
        try:
            n = export_firefox(p, KEYS / "cookies" / f"firefox-{p.name}.txt")
            say(f"cookies Firefox ({p.name}) : {n} -> 4-keys-code/cookies")
        except (OSError, sqlite3.Error) as e:
            say(f"cookies Firefox ({p.name}) illisibles : {e}")
    for b, d in chromium_dirs().items():
        # valeurs chiffrées par le navigateur (DPAPI / trousseau) : utilisables seulement sur ce compte
        for f in [d / "Local State", *d.glob("*/Network/Cookies"), *d.glob("*/Cookies")]:
            if f.is_file():
                copy_any(f, KEYS / "cookies" / b / f.relative_to(d))
        say(f"cookies {b} (base chiffrée par le navigateur) -> 4-keys-code/cookies/{b}")
    for f in KEYS.rglob("*"):
        private(f)


# --- Autres LLM -----------------------------------------------------------------------
LLM_DIRS = {"ollama": ".ollama", "grok": ".grok", "codex": ".codex", "gemini": ".gemini", "qwen": ".qwen",
            "lmstudio": ".lmstudio", "lm-studio-cache": ".cache/lm-studio", "opencode": ".config/opencode",
            "opencode-data": ".local/share/opencode", "continue": ".continue", "aider": ".aider.conf.yml",
            "kimi": ".kimi", "deepseek": ".deepseek", "crush": ".config/crush", "goose": ".config/goose"}


def set_user_env(name, value):
    if os.environ.get("ABC_AI") or os.environ.get("BCAI_AI"):   # racine de test : ne jamais toucher l'environnement réel
        say(f"(test) {name}={value} non posé")
        os.environ[name] = value
        return
    if WIN:   # via .NET : diffuse le changement aux nouveaux terminaux (WM_SETTINGCHANGE)
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"[Environment]::SetEnvironmentVariable('{name}', $env:ABC_VAL, 'User')"],
                       env={**os.environ, "ABC_VAL": value}, check=True)
    else:
        prof = HOME / ".profile"
        s = prof.read_text(encoding="utf-8") if prof.is_file() else ""
        s = re.sub(rf"^export {name}=.*\n?", "", s, flags=re.M) + f'export {name}="{value}"\n'
        prof.write_text(s, encoding="utf-8")
    os.environ[name] = value


def user_env(name):
    if WIN:
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                return winreg.QueryValueEx(k, name)[0]
        except OSError:
            return os.environ.get(name, "")
    return os.environ.get(name, "")


def import_llm():
    LLM.mkdir(parents=True, exist_ok=True)
    report = ["# LLM présents sur cette machine", "",
              "Généré par abc-import.py. Configs copiées ici (originaux en place) ; secrets dans 2-tools/4-keys-code/llm.", ""]
    big = []
    for tool, rel in LLM_DIRS.items():
        src = HOME / rel
        if not src.exists():
            continue

        def skip(f, src=src, tool=tool):
            parts = f.relative_to(src).parts
            if tool == "ollama" and parts[:1] == ("models",):
                return True
            if f.stat().st_size > BIG:
                big.append(f)
                return True
            if SECRET_FILE.match(f.name) and not f.name.endswith(".pub"):
                if not vault_closed():
                    copy_any(f, KEYS / "llm" / tool / f.relative_to(src))
                return True
            return False
        copy_any(src, LLM / tool / (src.name if src.is_file() else ""), skip=skip)
        report.append(f"- **{tool}** : `{src}` -> `3-llm/{tool}/`")
        say(f"LLM {tool} -> 3-llm/{tool}")
    # modèles Ollama : un seul exemplaire, déplacé vers ABC_MODELS_DIR
    if (HOME / ".ollama").exists() or shutil.which("ollama"):
        cur = Path(user_env("OLLAMA_MODELS") or HOME / ".ollama" / "models")
        dst = Path(os.environ.get("ABC_MODELS_DIR") or os.environ.get("BCAI_MODELS_DIR") or LLM / "models") / "ollama"
        dst.mkdir(parents=True, exist_ok=True)
        if cur.is_dir() and cur.resolve() != dst.resolve():
            for item in cur.iterdir():
                if not (dst / item.name).exists():
                    shutil.move(str(item), str(dst / item.name))
                elif item.is_dir():
                    copy_any(item, dst / item.name)
                    shutil.rmtree(item)
        set_user_env("OLLAMA_MODELS", str(dst))
        report.append(f"- **modèles Ollama** : `{dst}` (OLLAMA_MODELS ; redémarrer Ollama pour la prise en compte)")
        say(f"modèles Ollama -> {dst} (OLLAMA_MODELS posé)")
    # autres poids de modèles rangés dans ABC_MODELS_DIR (gguf, safetensors…) : inventoriés, jamais copiés
    mdir = Path(os.environ.get("ABC_MODELS_DIR") or os.environ.get("BCAI_MODELS_DIR") or LLM / "models")
    weights = sorted(f for f in mdir.rglob("*") if f.is_file() and f.suffix.lower() in
                     (".gguf", ".safetensors", ".bin", ".onnx")) if mdir.is_dir() else []
    if weights:
        report += ["", f"## Poids de modèles dans `{mdir}`", ""]
        report += [f"- `{f.relative_to(mdir)}` ({f.stat().st_size / 2**30:.1f} Go)" for f in weights]
    if big:
        report += ["", "## Gros fichiers laissés en place (poids de modèles, > 100 Mo)", ""]
        report += [f"- `{f}`" for f in big]
    (LLM / "llms.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"skills": [import_skills], "agents": [import_agents], "secrets": [import_secrets], "llm": [import_llm],
             "all": [import_skills, import_agents, import_secrets, import_llm]}
    if cmd not in steps:
        print(__doc__)
        return 1
    for step in steps[cmd]:
        try:
            if step is import_skills and len(sys.argv) > 2:
                step(sys.argv[2])
            else:
                step()
        except Exception as e:   # un import raté ne bloque jamais l'installation
            print(f"ATTENTION : import {step.__name__} : {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
