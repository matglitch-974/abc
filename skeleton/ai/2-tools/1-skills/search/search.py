#!/usr/bin/env python3
"""Recherche web sans clé : SearXNG local (métamoteur), démarré à la demande. Sortie compacte pour une IA.

  search.py "requête" [-n 10] [-c general|science|news|it|files|onions…] [-e brave,bing,…] [-l fr] [-p 2] [--json] [--tor]
  search.py start [--tor] | stop | status

Moteurs : ceux de SearXNG (Google, Bing, Brave, DuckDuckGo, Qwant, Yahoo, Yandex…, Startpage ; science : arXiv,
PubMed, Semantic Scholar, OpenAlex, Crossref, Google Scholar) ; Tor (Ahmia, Torch, catégorie onions) si
--tor / ABC_TOR=1 ou si 127.0.0.1:9050 écoute au premier démarrage.
FlareSolverr (127.0.0.1:8191) : bypass automatique des challenges JS/Cloudflare si détecté au premier démarrage.
Réglages : ~/ai/2-tools/3-software/searxng-settings.yml (créé au premier lancement, jamais réécrit).
"""
import argparse
import html
import re
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

AI = Path(os.environ.get("ABC_AI") or os.environ.get("BCAI_AI") or Path.home() / "ai")
SX = AI / "2-tools" / "3-software" / "searxng"
SETTINGS = AI / "2-tools" / "3-software" / "searxng-settings.yml"
LOG = AI / "2-tools" / "logs" / "searxng.log"
PORT = int(os.environ.get("ABC_SEARX_PORT") or os.environ.get("BCAI_SEARX_PORT") or "8888")
URL = f"http://127.0.0.1:{PORT}"
PY = SX / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
ENABLE = ["bing", "google", "qwant", "yahoo", "yandex", "wiby", "crossref", "openalex", "startpage"]


def port_open(port):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def write_settings():
    if SETTINGS.exists():
        return
    tor = port_open(9050) or (os.environ.get("ABC_TOR") or os.environ.get("BCAI_TOR") or "").lower() in ("1", "true", "yes")
    flaresolverr = port_open(8191)
    captcha_suspend = 60 if flaresolverr else 3600

    lines = [
        "# Réglages SearXNG d'ABC (search.py). Modifiable ; jamais réécrit.",
        "use_default_settings: true",
        "server:",
        f'  secret_key: "{secrets.token_hex(32)}"',
        '  bind_address: "127.0.0.1"',
        f"  port: {PORT}",
        "  limiter: false",
        "  public_instance: false",
        "search:",
        "  formats: [html, json]",
        "  suspended_times:",
        "    SearxEngineAccessDenied: 86400",
        "    SearxEngineTooManyRequests: 3600",
        f"    SearxEngineCaptcha: {captcha_suspend}",
    ]

    if flaresolverr or tor:
        lines += ["outgoing:", "  proxies:"]
        if flaresolverr:
            lines += ['    all://: "http://localhost:8191"']
        else:
            lines += ['    all://: "socks5h://127.0.0.1:9050"']

    lines += ["engines:"]
    lines += [f"  - name: {e}\n    disabled: false" for e in ENABLE]

    if tor:
        for e in ("ahmia", "torch"):
            lines += [
                f"  - name: {e}",
                "    disabled: false",
                "    using_tor_proxy: true",
                "    proxies:",
                '      all://: "socks5h://127.0.0.1:9050"',
            ]

    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if flaresolverr:
        print(f"# FlareSolverr détecté (8191) → proxy bypass CAPTCHA actif ; SearxEngineCaptcha={captcha_suspend}s.", file=sys.stderr)
    if tor and not flaresolverr:
        print("# Tor détecté (9050) → proxy global socks5h ; Ahmia + Torch activés.", file=sys.stderr)
    elif tor and flaresolverr:
        print("# Tor détecté (9050) → Ahmia + Torch activés (FlareSolverr pour le clearnet).", file=sys.stderr)


def running():
    try:
        with urllib.request.urlopen(f"{URL}/healthz", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def start():
    if running():
        return True
    if not PY.exists():
        sys.exit(f"SearXNG absent ({SX}) : relancer l'installation d'ABC.")
    write_settings()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, SEARXNG_SETTINGS_PATH=str(SETTINGS))
    kw = {"start_new_session": True} if os.name != "nt" else {"creationflags": 0x00000008}
    with open(LOG, "a", encoding="utf-8") as log:
        subprocess.Popen([str(PY), "-m", "searx.webapp"], cwd=SX, env=env, stdin=subprocess.DEVNULL,
                         stdout=log, stderr=log, **kw)
    for _ in range(60):
        if running():
            return True
        time.sleep(0.5)
    sys.exit(f"SearXNG ne démarre pas : voir {LOG}")


def stop():
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/FI", "WINDOWTITLE eq searx*"], capture_output=True)
    else:
        subprocess.run(["pkill", "-f", "searx.webapp"], capture_output=True)


def search(a):
    start()
    q = {"q": a.query, "format": "json", "pageno": a.p}
    if a.c:
        q["categories"] = a.c
    if a.e:
        q["engines"] = a.e
    if a.l:
        q["language"] = a.l
    with urllib.request.urlopen(f"{URL}/search?{urllib.parse.urlencode(q)}", timeout=60) as r:
        d = json.loads(r.read().decode("utf-8"))
    res = d.get("results", [])[: a.n]
    if a.json:
        print(json.dumps({"resultats": res, "reponses": d.get("answers"), "suggestions": d.get("suggestions"),
                          "moteurs_en_echec": d.get("unresponsive_engines")}, ensure_ascii=False, indent=1))
        return
    for ans in d.get("answers") or []:
        print(f"réponse : {ans.get('answer') if isinstance(ans, dict) else ans}")
    for i, x in enumerate(res, 1):
        snippet = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", x.get("content") or "")).split())[:220]
        date = f" | {x['publishedDate'][:10]}" if x.get("publishedDate") else ""
        print(f"{i}. {html.unescape(x.get('title', '')).strip()} | {x.get('url')} | {','.join(x.get('engines', []))}{date}\n   {snippet}")
    bad = d.get("unresponsive_engines") or []
    print(f"# {len(res)}/{len(d.get('results', []))} résultat(s)"
          + (f" ; en échec : {', '.join(f'{e[0]} ({e[1]})' for e in bad)}" if bad else ""))


def main():
    # --tor doit être traité avant write_settings() (appelé par start())
    if "--tor" in sys.argv:
        if SETTINGS.exists():
            print(f"# Réglages déjà créés : --tor ignoré. Pour l'activer, supprimer {SETTINGS} et relancer.", file=sys.stderr)
        else:
            os.environ["ABC_TOR"] = "1"

    if sys.argv[1:2] and sys.argv[1] in ("start", "stop", "status"):
        cmd = sys.argv[1]
        if cmd == "start":
            start()
        elif cmd == "stop":
            stop()
        print(f"SearXNG {'actif' if running() else 'arrêté'} : {URL}")
        return

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("query")
    p.add_argument("-n", type=int, default=10, help="nombre de résultats affichés (défaut 10)")
    p.add_argument("-c", help="catégories, ex. general,science,news,it,files,onions")
    p.add_argument("-e", help="moteurs précis, ex. brave,bing,arxiv")
    p.add_argument("-l", help="langue, ex. fr, en, all")
    p.add_argument("-p", type=int, default=1, help="page")
    p.add_argument("--json", action="store_true")
    p.add_argument("--tor", action="store_true",
                   help="proxy global Tor (socks5h://127.0.0.1:9050) + Ahmia/Torch ; "
                        "effectif uniquement si les réglages n'existent pas encore (ou ABC_TOR=1)")
    search(p.parse_args())


if __name__ == "__main__":
    main()
