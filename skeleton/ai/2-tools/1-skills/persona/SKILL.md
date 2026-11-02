---
name: persona
description: Documentation du système de personas et d'agents (emplacement, catégories, nommage, activation, confidentialité).
---

# Système de personas

## Emplacement
`~/ai/0-persona/`. Son contenu n'est pas numéroté.

## Persona principal
- Facultatif. Un fichier à la racine de `0-persona/`, sans catégorie tant qu'il est seul.
- Nom entièrement libre : majuscules, chiffres, caractères spéciaux, Unicode, émojis.
- Décrit uniquement le caractère. Les règles de travail sont dans `~/ai/AGENTS.md` : retirer le persona ne dégrade pas le travail.
- Activation : ligne `@~/ai/0-persona/<nom>` dans `~/ai/AGENTS.md`.
- Le persona principal est une donnée personnelle : il n'est jamais publié.

## Agents
- Rangés par catégorie : `0-persona/<catégorie>-agents/<agent>.md`.
- Catégorie minimale obligatoire : `system-agents/`, qui contient `slave.md`.
- `slave` est l'unique sous-agent : exécution, récapitulatifs, recherches, explorations.
- Les agents système font partie du projet public.
- Chaque dossier `<catégorie>-agents/` est relié dans `~/.claude/agents/` (Claude Code y cherche récursivement ; l'identité vient du champ `name`).
- Nouvelle catégorie : créer `0-persona/<catégorie>-agents/`, puis `ln -s ~/ai/0-persona/<catégorie>-agents ~/.claude/agents/<catégorie>-agents`.
