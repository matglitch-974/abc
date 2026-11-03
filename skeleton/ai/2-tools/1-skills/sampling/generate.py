#!/usr/bin/env python3
"""Génère un passage par un appel API dont les réglages sont fixés ici (effort, modèle, longueur).

  generate.py [--model M] [--effort E] [--max-tokens N] [--system S] [--compare E1,E2,…] [--dry-run] "consigne"
  (consigne lue sur stdin si absente)

temperature / top_p / top_k ne sont plus acceptés par les modèles Claude actuels : voir SKILL.md.
"""
import argparse
import json
import sys

EFFORTS = ("low", "medium", "high", "xhigh", "max")


def request(model, effort, max_tokens, system, prompt):
    req = {"model": model, "max_tokens": max_tokens, "output_config": {"effort": effort},
           "messages": [{"role": "user", "content": prompt}]}
    if system:
        req["system"] = system
    return req


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("prompt", nargs="?")
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--effort", default="medium", choices=EFFORTS)
    p.add_argument("--max-tokens", type=int, default=16000)
    p.add_argument("--system", default="")
    p.add_argument("--compare", help="efforts séparés par des virgules, ex. low,high")
    p.add_argument("--dry-run", action="store_true", help="affiche les requêtes sans appeler l'API")
    a = p.parse_args()
    prompt = a.prompt if a.prompt is not None else sys.stdin.read()
    if not prompt.strip():
        p.error("consigne vide")
    efforts = a.compare.split(",") if a.compare else [a.effort]
    bad = [e for e in efforts if e not in EFFORTS]
    if bad:
        p.error(f"effort inconnu : {', '.join(bad)}")
    reqs = [request(a.model, e, a.max_tokens, a.system, prompt) for e in efforts]
    if a.dry_run:
        print(json.dumps(reqs, ensure_ascii=False, indent=2))
        return 0
    try:
        import anthropic
    except ImportError:
        sys.exit("SDK absent : pip install anthropic (ou uv tool run --with anthropic python3 generate.py …)")
    client = anthropic.Anthropic()
    for r in reqs:
        try:
            with client.messages.stream(**r) as s:
                msg = s.get_final_message()
        except anthropic.APIStatusError as e:
            print(f"### effort={r['output_config']['effort']} : erreur {e.status_code} {e.message}")
            continue
        except anthropic.APIConnectionError as e:
            sys.exit(f"connexion impossible : {e}")
        if msg.stop_reason == "refusal":
            text = "(refus du modèle)"
        else:
            text = "".join(b.text for b in msg.content if b.type == "text")
        u = msg.usage
        print(f"### modèle={msg.model} effort={r['output_config']['effort']} "
              f"tokens entrée={u.input_tokens} sortie={u.output_tokens} arrêt={msg.stop_reason}\n{text}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
