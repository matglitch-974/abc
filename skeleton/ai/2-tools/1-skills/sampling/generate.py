#!/usr/bin/env python3
"""Génère un passage avec des réglages fixés ici (modèle, effort, prompt système), dans une instance isolée.

  generate.py [--model M] [--effort E] [--system S] [--compare E1,E2,…] [--api] [--dry-run] "consigne"
  (consigne lue sur stdin si absente)

Par défaut : `claude -p` avec le compte connecté (abonnement, sans clé API), sans outils,
sans CLAUDE.md, réglages ni MCP. --api : SDK `anthropic` et clé API à la place.
temperature / top_p / top_k ne sont plus acceptés par les modèles Claude actuels : voir SKILL.md.
"""
import argparse
import json
import shutil
import subprocess
import sys
import time

EFFORTS = ("low", "medium", "high", "xhigh", "max")


def cli_cmd(model, effort, system, prompt):
    cmd = ["claude", "-p", "--model", model, "--effort", effort, "--tools", "", "--strict-mcp-config",
           "--setting-sources", "", "--no-session-persistence", "--output-format", "json"]
    if system:
        cmd += ["--system-prompt", system]
    return cmd + ["--", prompt]


def via_cli(model, effort, system, prompt):
    t = time.time()
    r = subprocess.run(cli_cmd(model, effort, system, prompt), capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return None, f"échec de claude -p : {(r.stderr or r.stdout).strip()[:300]}"
    u = d.get("usage") or {}
    head = (f"modèles={','.join(d.get('modelUsage') or {}) or model} effort={effort} "
            f"tokens sortie={u.get('output_tokens')} durée={time.time() - t:.0f}s")
    if d.get("is_error"):
        return None, f"{head} erreur : {d.get('result')}"
    return head, d.get("result", "")


def via_api(model, effort, system, prompt):
    try:
        import anthropic
    except ImportError:
        sys.exit("SDK absent : pip install anthropic")
    req = {"model": model, "max_tokens": 16000, "output_config": {"effort": effort},
           "messages": [{"role": "user", "content": prompt}]}
    if system:
        req["system"] = system
    try:
        with anthropic.Anthropic().messages.stream(**req) as s:
            msg = s.get_final_message()
    except anthropic.APIStatusError as e:
        return None, f"effort={effort} erreur {e.status_code} {e.message}"
    except anthropic.APIConnectionError as e:
        return None, f"connexion impossible : {e}"
    text = "(refus du modèle)" if msg.stop_reason == "refusal" else \
        "".join(b.text for b in msg.content if b.type == "text")
    return f"modèle={msg.model} effort={effort} tokens sortie={msg.usage.output_tokens}", text


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("prompt", nargs="?")
    p.add_argument("--model", default="claude-sonnet-5-5")
    p.add_argument("--effort", default="medium", choices=EFFORTS)
    p.add_argument("--system", default="")
    p.add_argument("--compare", help="efforts séparés par des virgules, ex. low,max")
    p.add_argument("--api", action="store_true", help="SDK anthropic + clé API au lieu de claude -p")
    p.add_argument("--dry-run", action="store_true", help="affiche les commandes sans rien lancer")
    a = p.parse_args()
    prompt = a.prompt if a.prompt is not None else sys.stdin.read()
    if not prompt.strip():
        p.error("consigne vide")
    efforts = a.compare.split(",") if a.compare else [a.effort]
    bad = [e for e in efforts if e not in EFFORTS]
    if bad:
        p.error(f"effort inconnu : {', '.join(bad)}")
    if a.dry_run:
        for e in efforts:
            print(json.dumps(cli_cmd(a.model, e, a.system, prompt), ensure_ascii=False))
        return 0
    if not a.api and not shutil.which("claude"):
        sys.exit("claude introuvable dans le PATH")
    run = via_api if a.api else via_cli
    code = 0
    for e in efforts:
        head, text = run(a.model, e, a.system, prompt)
        if head is None:
            print(f"### {text}")
            code = 1
        else:
            print(f"### {head}\n{text}\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
