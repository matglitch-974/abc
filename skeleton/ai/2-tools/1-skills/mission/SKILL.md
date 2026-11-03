---
name: mission
description: Reconnaissance des outils (skills, MCP) locaux et en ligne par un sous-agent, installation automatique, puis décomposition en arbre de tâches du plus simple au plus complexe et carte PLAN.md. Début de session et toute tâche lourde.
---

# Mission (méthode Senku : remonter de l'objectif aux matériaux de base, puis gravir l'arbre)

Déclencheurs : début de session (obligatoire dans une unité de code) ; toute tâche lourde (plusieurs étapes, plusieurs fichiers ou outil manquant). Question simple, retouche d'une ligne → exécution directe.

## 1. Reconnaissance (sous-agent `slave`, skill `bench`)
Consigne type, à compléter :
```
Ton identifiant : slave-<code>. Objectif : <objectif>. Mots-clés : <mots>.
1. python3 ~/ai/2-tools/1-skills/mission/tool-scan.py local <mots>
2. python3 ~/ai/2-tools/1-skills/mission/tool-scan.py online <mots> (2-3 jeux de mots-clés) ; WebSearch : forums, comparatifs récents.
3. Retenir, pour chaque besoin, le meilleur outil : existant local d'abord ; sinon qualité et maintenance (màj < 1 an, non archivé, étoiles) > open source > licence permissive > sans clé.
4. Installer chaque candidat retenu absent en local :
   python3 ~/ai/2-tools/1-skills/mission/tool-install.py mcp <nom> <commande…>   (npx/uvx de préférence)
   python3 ~/ai/2-tools/1-skills/mission/tool-install.py skill <url-git> [sous-dossier]
   Ne pas installer : outil exigeant une clé ou un compte (le signaler), dépôt archivé, source introuvable.
5. Rapport, une ligne par besoin : besoin | outil | local/installé/à-clé | source | pourquoi.
```
Un MCP installé n'est actif qu'à la session suivante : en attendant, passer par son équivalent CLI ou un outil déjà chargé. Signaler à l'utilisateur chaque installation (`tool-install.py log` ; retrait : `remove <nom>`).

## 2. Décomposition
Remonter de l'objectif à ses prérequis jusqu'aux tâches atomiques (une action vérifiable chacune), puis les ordonner : les prérequis avant, les plus simples d'abord. Tâches sans dépendance commune → sous-agents en parallèle.

## 3. Carte `PLAN.md`
À la racine de l'unité (sinon dans le secteur de `1-bench/`). Format dense, une tâche par ligne, mis à jour à chaque palier :
```
# PLAN : <objectif>
fini quand : <critère vérifiable>
outils : <outil>=<usage>, …
T1 [x] <tâche> | <- - | @<outil> | ok: <preuve attendue>
T2 [~] <tâche> | <- T1 | @<outil> | ok: <…>
T3 [ ] <tâche> | <- T1,T2 | @slave | ok: <…>
risques : <risque> -> <parade>
```
États : `[ ]` à faire, `[~]` en cours, `[x]` fait, `[!]` bloqué (raison en fin de ligne). `<-` = dépend de. Pas de prose : le plan se relit en quelques tokens après une compaction.
