#!/usr/bin/env python3
"""Dernières synthèses publiques de La Note Sentinelle (specula.fr, rubrique « Ce matin »).

  specula.py [-n N] [--since AAAA-MM-JJ] [--json] [--save DOSSIER]

Source : API WordPress publique du site (une seule requête par appel). Sortie Markdown par défaut :
date, type d'édition, titre, lien, fait dominant, points clés. --save écrit une édition par fichier
(AAAA-MM-JJ.md), sans réécrire un fichier existant. Sans dépendance.
"""
import argparse
import datetime
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

API = "https://specula.fr/wp-json/wp/v2/posts"
CATEGORY = 87  # « Ce matin » : synthèse publique quotidienne de La Note Sentinelle
UA = "abc-specula/1.0 (lecture personnelle; +https://github.com/matglitch-974/abc)"
STOP = "ce que contient l"  # section promotionnelle en fin d'article : ignorée


class Blocks(HTMLParser):
    """Découpe le contenu en blocs (tag, texte) : p, h2, li."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks, self.tag, self.buf = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "h2", "h3", "li"):
            self.tag, self.buf = tag, []

    def handle_endtag(self, tag):
        if tag == self.tag:
            text = " ".join("".join(self.buf).split())
            if text:
                self.blocks.append((tag, text))
            self.tag = None

    def handle_data(self, data):
        if self.tag:
            self.buf.append(data)


def parse(post):
    b = Blocks()
    b.feed(post["content"]["rendered"])
    lead, points, section = [], [], "lead"
    for tag, text in b.blocks:
        if tag in ("h2", "h3"):
            if text.lower().startswith(STOP):
                break
            section = "points" if "points cl" in text.lower() else "other"
        elif section == "lead" and tag == "p":
            lead.append(text)
        elif section == "points" and tag == "li":
            points.append(text)
    excerpt = html.unescape(re.sub("<[^>]+>", "", post["excerpt"]["rendered"]))
    kind = re.search(r"—\s*([^:]+?)\s*:", excerpt)
    announced = re.search(r"et (\d+) points? cl", excerpt)
    if not lead or not points or (announced and int(announced.group(1)) != len(points)):
        print(f"attention : {post['link']} — {len(points)} point(s) extrait(s)"
              f"{', ' + announced.group(1) + ' annoncé(s)' if announced else ''} : format du site peut-être changé",
              file=sys.stderr)
    return {"date": post["date"][:10], "edition": kind.group(1) if kind else "",
            "titre": html.unescape(post["title"]["rendered"]), "lien": post["link"],
            "fait_dominant": lead, "points_cles": points}


def fetch(n, since):
    q = {"categories": CATEGORY, "per_page": min(max(n, 1), 100), "orderby": "date", "order": "desc",
         "_fields": "date,link,title,excerpt,content"}
    if since:
        q["after"] = f"{since}T00:00:00"
    req = urllib.request.Request(f"{API}?{urllib.parse.urlencode(q)}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def markdown(e):
    out = [f"## {e['date']} — {e['titre']}", f"_{e['edition']}_ · {e['lien']}", "", "**Fait dominant**", ""]
    out += [p + "\n" for p in e["fait_dominant"]]
    out += ["**Points clés**", ""] + [f"{i}. {p}" for i, p in enumerate(e["points_cles"], 1)]
    return "\n".join(out) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-n", type=int, default=1, help="nombre d'éditions (1 à 100, défaut 1)")
    p.add_argument("--since", help="seulement les éditions publiées depuis cette date (AAAA-MM-JJ)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--save", metavar="DOSSIER")
    a = p.parse_args()
    if a.since:
        try:
            datetime.date.fromisoformat(a.since)
        except ValueError:
            p.error("--since : date AAAA-MM-JJ valide attendue")
    try:
        editions = [parse(x) for x in fetch(100 if a.since else a.n, a.since)]
    except Exception as e:
        sys.exit(f"specula.fr injoignable ou format changé : {e}")
    if not a.since:
        editions = editions[: a.n]
    if a.save:
        d = Path(a.save).expanduser()
        d.mkdir(parents=True, exist_ok=True)
        for e in editions:
            f = d / f"{e['date']}.md"
            if not f.exists():
                f.write_text(markdown(e), encoding="utf-8")
                print(f"écrit : {f}", file=sys.stderr)
    print(json.dumps(editions, ensure_ascii=False, indent=1) if a.json else "\n".join(markdown(e) for e in editions))


if __name__ == "__main__":
    main()
