---
name: context
description: Mesurer et compresser le contexte chargé à chaque session (AGENTS.md, imports, realign.md, descriptions de skills) sans perte de sens. À utiliser avant et après toute modification de ces fichiers.
---

# Compression du contexte

Mesurer : `python3 ~/ai/2-tools/1-skills/context/ctx-audit.py` (estimation) ou `--exact` (sessions `agent -p` réelles ; Claude Code, commande renommée par ABC). Windows : `python`.

## Méthodes, par ordre de gain
1. **Charger à la demande** : ce qui ne sert pas à chaque tour quitte AGENTS.md pour un skill (coût au repos : sa ligne `description`).
2. **Une règle, un seul endroit** : ailleurs, un renvoi (« skill `bench` »).
3. **Écrire dense** : listes à un verbe par ligne, tableaux, flèches (`→`) pour les conditions ; ni politesse, ni rappel du contexte, ni exemple évident.
4. **Préfixe stable** : rien de variable (date, compteur) dans les fichiers chargés au démarrage, pour que le cache de prompt serve à chaque tour.
5. **`realign.md` à la première personne** et très court : il est réinjecté tous les 10 messages.

## Interdits
- Compression automatique par suppression de mots (type LLMLingua) : une négation ou un « jamais » perdu inverse une règle.
- Abréviations maison que le modèle doit deviner.
- Changer la langue des prompts : décision de l'utilisateur.

## Vérifier après chaque compression
1. Remesurer (`--exact`).
2. Poser au modèle, avec le seul fichier compressé comme prompt système, 3 à 5 questions dont les réponses dépendent des règles retirées ou condensées. Toute réponse fausse → rétablir la règle.

## Référence (2026-11-03)
AGENTS.md 2 783 → 1 448 tokens ; chargement total 3 047 → 1 546 ; realign.md 278 → 191. Test de compréhension sur Haiku : 4/4.
