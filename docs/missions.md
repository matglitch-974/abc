# Missions, recherche web et réglages de génération

## Système « mission » (AGENTS.md, section Missions ; consigne de reconnaissance : skill `mission`)
La méthode est dans `AGENTS.md` parce qu'elle s'applique en permanence ; le skill ne garde que la consigne type du `slave` de reconnaissance et les règles d'installation. L'agent principal est un coordinateur : il ne lit aucun fichier, un `slave` exécute et un second `slave` contrôle.

Inspiré de Dr. Stone : partir de l'objectif, remonter jusqu'aux prérequis élémentaires, puis gravir l'arbre palier par palier.

1. **Reconnaissance** par un sous-agent `slave` : `tool-scan.py local` inventorie skills, MCP, plugins et agents installés ; `tool-scan.py online` interroge le registre officiel MCP (`registry.modelcontextprotocol.io`) et GitHub (étoiles, licence, dernière mise à jour, archivage). Le sous-agent complète par une recherche web (forums, comparatifs).
2. **Installation automatique** des outils retenus par `tool-install.py` (`claude mcp add -s user`, ou copie d'un dossier contenant `SKILL.md`). Chaque installation est journalisée dans `~/ai/2-tools/installed.md` et réversible (`tool-install.py remove <nom>`). Exclus d'office : outils exigeant une clé ou un compte, dépôts archivés.
3. **Décomposition** en tâches atomiques, de la plus simple à la plus complexe, prérequis d'abord.
4. **Carte `PLAN.md`** : une tâche par ligne (`T3 [ ] tâche | <- T1,T2 | @outil | ok: preuve`), sans prose.

### Pourquoi
- **Sous-agent** : la reconnaissance lit beaucoup (listes, pages) ; dans un sous-agent, ce volume ne pollue pas le contexte principal, seul le rapport y entre.
- **Scripts** : inventaire et requêtes sont mécaniques (règle 3), l'IA ne garde que le choix.
- **Déclencheur** : début de session (rappel injecté par `memory-hook.py`) et tâche lourde ; pas pour une question simple, où le coût dépasserait le gain.
- **Installation automatique** : choix explicite de l'utilisateur. Risque assumé : un MCP est du code exécuté avec les droits de l'utilisateur ; le journal et le retrait le limitent.
- **Format de `PLAN.md`** : choisi pour être relu par un LLM au moindre coût (identifiants courts, dépendances `<-`, états `[ ] [~] [x] [!]`), y compris après une compaction.

## Recherche web (skill `scraping`)
Installés par `bootstrap.sh` / `install.ps1` ; tous gratuits et sans clé, sauf Brave Search (choix de l'utilisateur, à la place de DuckDuckGo) :

| Outil | Licence | Rôle |
|---|---|---|
| `fetch` (`mcp-server-fetch`, MCP officiel) | MIT | page statique → Markdown |
| `brave` (`@brave/brave-search-mcp-server`, officiel) | MIT | **seul moteur de recherche** : web, actualités, contexte LLM, réponse IA (`brave_summarizer`) ; clé API requise (`BRAVE_API_KEY_FILE` → `~/ai/2-tools/0-mcp/sensible/brave-api-key`) |
| `playwright` (`@playwright/mcp`, Microsoft) | Apache-2.0 | navigateur réel, interaction |
| `scrapling` (`scrapling[ai,fetchers]`) | BSD-3-Clause | navigateur furtif, sites protégés |
| `crwl` (Crawl4AI, CLI) | Apache-2.0 | exploration de sites entiers |

Écartés : DuckDuckGo (remplacé par Brave Search), Firecrawl, Tavily, Exa, Bright Data (clé requise, quotas gratuits limités). Les échecs d'installation ne bloquent pas l'instance (navigateurs absents sous Termux/musl, par exemple).

### Sources dédiées
- **`specula`** : synthèses publiques quotidiennes de La Note Sentinelle (specula.fr). Passe par l'API WordPress publique du site plutôt que par l'analyse des pages : une requête par appel, données structurées, et une rupture de format détectée (nombre de points clés extraits comparé au nombre annoncé). L'édition complète, payante et envoyée par e-mail, n'est pas récupérée ; les contenus restent à usage personnel (CGV).

## Réglages de génération (skill `sampling`)
Claude ne peut pas régler sa température : l'échantillonnage a lieu côté serveur, avant toute réponse, et `temperature`/`top_p`/`top_k` sont refusés par les modèles actuels (et par la version d'API `2026-10-21` sur tous les modèles). Leviers réels : `effort` et modèle, exposés par `generate.py` (par défaut via `claude -p` et le compte connecté, Sonnet 5.5, sans clé API ; `--api` avec une clé). Le reste (registre, déterminisme apparent, style) relève d'une consigne de comportement, présentée comme telle. Un échantillonnage réel (glouton, logits visibles) exige un modèle à poids ouverts local (`~/ai/3-llm/`).
