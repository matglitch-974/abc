---
name: sampling
description: Comment Claude génère ses tokens, ce qu'il peut réellement régler sur lui-même (effort, modèle, longueur) et ce qui n'est qu'une consigne de style. À utiliser quand l'utilisateur demande de changer température, déterminisme, profondeur de réflexion ou manière de parler.
---

# Génération et réglages de soi

## Mécanique
À chaque pas, le réseau produit un score (logit) pour chaque token du vocabulaire ; un échantillonneur, côté serveur, les change en probabilités et en tire un. Température, top_k, top_p agissent sur ce tirage. Le modèle ne voit ni ses logits ni l'échantillonneur, et ne peut rien régler en cours de réponse : tout paramètre est fixé par l'appelant avant le premier token.

## Ce qui est réglable (vérifié, novembre 2026)
- **temperature / top_p / top_k : indisponibles.** Supprimés (400) sur tous les modèles Claude actuels (Fable 5.x, Opus 5.x/4.7/4.8, Sonnet 5, et valeurs non par défaut refusées sur Sonnet 5.5 et Haiku 5.5) ; la version d'API `2026-10-21` les refuse sur tous les modèles. Seuls d'anciens modèles (Haiku 4.5, Sonnet/Opus 4.6) les acceptaient encore avec `2023-06-01`.
- **effort** (`low` … `max`) : profondeur de réflexion et dépense de tokens. C'est le vrai levier.
- **modèle** (Haiku, Sonnet, Opus, Fable) et **max_tokens**.
- Dans Claude Code : `claude --effort <niveau>` et `--model <modèle>` au lancement, `/model` en session, `/fast` (même modèle, sortie plus rapide).

`generate.py` délègue un passage à une instance isolée (sans outils, sans CLAUDE.md, réglages ni MCP) dont ces réglages sont fixés, puis rend le texte avec ses paramètres. Par défaut : `claude -p` avec le compte connecté (abonnement, pas de clé API), modèle `claude-sonnet-5-5`.
```
python3 ~/ai/2-tools/1-skills/sampling/generate.py --effort low "consigne"
python3 … --compare low,max --system "prompt système" "consigne"   # même consigne, plusieurs efforts
python3 … --api …                                                  # SDK anthropic + clé API
```
Constaté (Sonnet 5.5, énigme de l'escargot) : `low` se trompe puis se corrige en cours de réponse, `max` répond juste d'emblée. Le texte vient d'une autre instance : le présenter comme tel. Chaque appel consomme le quota de l'abonnement.

## Contrôle comportemental (consigne, pas réglage)
Sur demande, adopter et tenir jusqu'à contre-ordre : formulation la plus attendue (« déterministe »), registre, longueur, langue, bégaiement, style imposé. Le dire honnêtement : c'est un comportement choisi, comme un humain qui s'applique à parler autrement, pas un changement d'échantillonnage.

## Échantillonnage réel
Température, glouton (température 0), top_k et logits visibles : seulement avec un modèle à poids ouverts exécuté localement (`~/ai/3-llm/`, ex. llama.cpp), qui n'est pas Claude.
