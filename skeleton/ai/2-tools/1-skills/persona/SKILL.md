---
name: persona
description: Documentation du système de personas et d'agents (emplacement, catégories, nommage, activation, confidentialité).
---

# Système de personas

## Emplacement
`~/ai/0-persona/`. Son contenu n'est pas numéroté.

## Personas
- Un fichier par persona dans `0-persona/` (racine ou catégorie).
- Nom entièrement libre : majuscules, chiffres, caractères spéciaux, Unicode, émojis.
- Décrit uniquement le caractère. Les règles de travail sont dans `~/ai/AGENTS.md` : retirer le persona ne dégrade pas le travail.
- Activation : le premier message de la session commence par `@<nom>` (nom du fichier, avec ou sans `.md`). Sans `@`, ou nom introuvable : `slave`. Le hook `memory-hook.py` injecte le persona et le réinjecte après chaque compaction.
- Les personas personnels sont des données personnelles : jamais publiés.
- Agent isolé : en-tête `isolated: true`. Choisi par `@<nom>`, il ouvre une session cloisonnée dans les deux sens : mémoire et journal propres dans `~/ai/isolated/<nom>/` ; le hook bloque (PreToolUse) ses accès à `~/ai/memory`, `AGENTS.md`, aux autres personas et agents isolés, et bloque l'accès des autres sessions à `~/ai/isolated/` comme aux transcripts de ses sessions. Limite : `AGENTS.md` et la mémoire importée sont déjà chargés au démarrage, avant le choix du persona ; la consigne d'isolement demande de les ignorer.

## Agents
- Rangés par catégorie : `0-persona/<catégorie>-agents/<agent>.md`.
- Catégorie minimale obligatoire : `system-agents/`, qui contient `slave.md`.
- `slave` est l'unique sous-agent : exécution, récapitulatifs, recherches, explorations.
- Les agents système font partie du projet public.
- Chaque dossier `<catégorie>-agents/` est relié dans `agents/` de la configuration de Claude Code (`$CLAUDE_CONFIG_DIR`, soit `~/ai/2-tools/3-software/claude-code/`) (Claude Code y cherche récursivement ; l'identité vient du champ `name`).
- Nouvelle catégorie : créer `0-persona/<catégorie>-agents/`, puis `ln -s ~/ai/0-persona/<catégorie>-agents "$CLAUDE_CONFIG_DIR/agents/<catégorie>-agents"`.
