---
name: mission
description: Consigne type du slave de reconnaissance (outils locaux et en ligne, installation automatique) et règles d'installation. La méthode elle-même est dans AGENTS.md (section Missions).
---

# Reconnaissance des outils

Consigne type pour `slave` (skill `bench`), à compléter :
```
Ton identifiant : slave-<code>. Objectif : <objectif>. Mots-clés : <mots>.
1. python3 ~/ai/2-tools/1-skills/mission/tool-scan.py local <mots>
2. python3 ~/ai/2-tools/1-skills/mission/tool-scan.py online <mots> (2-3 jeux de mots-clés) ; Brave Search (MCP brave) : forums, comparatifs récents.
3. Retenir, pour chaque besoin, le meilleur outil : existant local d'abord ; sinon qualité et maintenance (màj < 1 an, non archivé, étoiles) > open source > licence permissive > sans clé.
4. Installer chaque candidat retenu absent en local :
   python3 ~/ai/2-tools/1-skills/mission/tool-install.py mcp <nom> <commande…>   (npx/uvx de préférence)
   python3 ~/ai/2-tools/1-skills/mission/tool-install.py skill <url-git> [sous-dossier]
   Ne pas installer : outil exigeant une clé ou un compte (le signaler), dépôt archivé, source introuvable.
5. Rapport, une ligne par besoin : besoin | outil | local/installé/à-clé | source | pourquoi.
```

- Un MCP installé n'est actif qu'à la session suivante : en attendant, passer par son équivalent CLI ou un outil déjà chargé.
- Signaler à l'utilisateur chaque installation (`tool-install.py log` ; retrait : `tool-install.py remove <nom>`).
- `PLAN.md` hors d'une unité : dans le secteur `1-bench/` du `slave`.
