# Missions, recherche web et réglages de génération

## Système « mission » (AGENTS.md, section Missions ; consigne de reconnaissance : skill `mission`)
La méthode est dans `AGENTS.md` parce qu'elle s'applique en permanence ; le skill ne garde que la consigne type du `slave` de reconnaissance et les règles d'installation. L'agent principal est un coordinateur : il ne lit aucun fichier, un `slave` exécute et un second `slave` contrôle.

Inspiré de Dr. Stone : partir de l'objectif, remonter jusqu'aux prérequis élémentaires, puis gravir l'arbre palier par palier.

1. **Reconnaissance** par un sous-agent `slave` : `tool-scan.py local` inventorie skills, MCP, plugins et agents installés ; `tool-scan.py online` interroge le registre officiel MCP (`registry.modelcontextprotocol.io`) et GitHub (étoiles, licence, dernière mise à jour, archivage). Le sous-agent complète par une recherche web (forums, comparatifs).
2. **Installation automatique** des outils retenus par `tool-install.py` (`agent mcp add -s user`, ou copie d'un dossier contenant `SKILL.md`). Chaque installation est journalisée dans `~/ai/2-tools/installed.md` et réversible (`tool-install.py remove <nom>`). Exclus d'office : outils exigeant une clé ou un compte, dépôts archivés.
3. **Décomposition** en tâches atomiques, de la plus simple à la plus complexe, prérequis d'abord.
4. **Carte `PLAN.md`** : une tâche par ligne (`T3 [ ] tâche | <- T1,T2 | @outil | ok: preuve`), sans prose.

### Pourquoi
- **Sous-agent** : la reconnaissance lit beaucoup (listes, pages) ; dans un sous-agent, ce volume ne pollue pas le contexte principal, seul le rapport y entre.
- **Scripts** : inventaire et requêtes sont mécaniques (règle 3), l'IA ne garde que le choix.
- **Déclencheur** : début de session (rappel injecté par `memory-hook.py`) et tâche lourde ; pas pour une question simple, où le coût dépasserait le gain.
- **Installation automatique** : choix explicite de l'utilisateur. Risque assumé : un MCP est du code exécuté avec les droits de l'utilisateur ; le journal et le retrait le limitent.
- **Format de `PLAN.md`** : choisi pour être relu par un LLM au moindre coût (identifiants courts, dépendances `<-`, états `[ ] [~] [x] [!]`), y compris après une compaction.

## Recherche web (skill `scraping`)
Installés par `bootstrap.sh` / `ABC-install-<version>.ps1` ; tous gratuits et sans clé :

| Outil | Licence | Rôle |
|---|---|---|
| `fetch` (`mcp-server-fetch`, MCP officiel) | MIT | page statique → Markdown |
| SearXNG (`searxng/searxng`, local) + MCP `searxng` (`mcp-searxng`) | AGPL-3.0 / MIT | **seul moteur de recherche** : métamoteur (Google, Bing, Brave, DuckDuckGo, Yahoo, Yandex, bases scientifiques… ; 353 moteurs déclarés), sortie JSON ; skill `search` |
| `playwright` (`@playwright/mcp`, Microsoft) | Apache-2.0 | navigateur réel, interaction |
| `scrapling` (`scrapling[ai,fetchers]`) | BSD-3-Clause | navigateur furtif, sites protégés |
| `crwl` (Crawl4AI, CLI) | Apache-2.0 | exploration de sites entiers |

Écartés : DuckDuckGo seul et l'API Brave Search (SearXNG les interroge déjà sans clé ; l'API Brave exige une clé), Firecrawl, Tavily, Exa, Bright Data (clé requise, quotas gratuits limités). Les échecs d'installation ne bloquent pas l'instance (navigateurs absents sous Termux/musl, par exemple).

### SearXNG
- Exigence : résultats de tous les moteurs, sans clé ni argent, exploitables par une IA, deep web en prime. SearXNG est le seul outil libre qui coche tout : il interroge les moteurs en parallèle, fusionne et dédoublonne, et répond en JSON.
- Installé dans `~/ai/2-tools/3-software/searxng/` (clone Git + environnement Python via uv, sans Docker) ; écoute sur `127.0.0.1:8888` seulement ; démarré à la demande par `search.py` (journal : `2-tools/logs/searxng.log`).
- Réglages `~/ai/2-tools/3-software/searxng-settings.yml`, créés au premier lancement (clé secrète aléatoire, JSON activé, moteurs désactivés par défaut réactivés : Bing, Google, Qwant, Yahoo, Yandex, Wiby, Crossref, OpenAlex).
- Mesuré (environnement de développement, adresse IP de centre de données) : 52 à 78 résultats par requête, issus de Yahoo, DuckDuckGo, Brave, Yandex, Bing, Google CSE, Semantic Scholar, Crossref, PubMed ; Google et Qwant y étaient bloqués (403, CAPTCHA). Depuis une connexion domestique, les blocages sont en général moins fréquents (non mesuré).
- Tor : seuls Ahmia et Torch passent par le proxy, le reste reste rapide. Modèle à ajouter sous `engines:` si Tor est installé après coup :
  ```yaml
  - name: ahmia
    using_tor_proxy: true
    proxies:
      all://: "socks5h://127.0.0.1:9050"
  ```
  (idem pour `torch`). Non testé : Tor absent de l'environnement de développement.
- Non activés délibérément : Anna's Archive et Library Genesis (bibliothèques pirates).

### Anonymat et bypass CAPTCHA

Trois niveaux configurables à la création de `searxng-settings.yml` (jamais réécrit ensuite) :

| Niveau | Prérequis | Effet |
|--------|-----------|-------|
| **FlareSolverr** | port 8191 ouvert | proxy global `http://localhost:8191` ; résout Cloudflare/JS via navigateur headless ; `SearxEngineCaptcha` → 60 s |
| **Tor** | `--tor` / `ABC_TOR=1` / port 9050 | proxy global `socks5h://127.0.0.1:9050` ; réduit les bans IP ; augmente les CAPTCHA Google |
| **FlareSolverr + Tor** | les deux | FlareSolverr sur le clearnet, Tor pour Ahmia/Torch uniquement |

`suspended_times` injectés par défaut dans les réglages générés :

```yaml
search:
  suspended_times:
    SearxEngineAccessDenied: 86400
    SearxEngineTooManyRequests: 3600
    SearxEngineCaptcha: 60      # 3600 sans résolveur actif
```

Mesures de référence (sans bypass, IP de centre de données) : 52–78 résultats/requête, Google et Qwant bloqués (403/CAPTCHA), Yahoo/DuckDuckGo/Brave/Bing/Yandex opérationnels. Depuis une IP domestique, les blocages sont moins fréquents (non mesuré ; référence `docs/missions.md` §SearXNG). Mesures avec FlareSolverr ou Tor : non disponibles (environnement de développement sans ces services).

### Sources dédiées
- **`specula`** : synthèses publiques quotidiennes de La Note Sentinelle (specula.fr). Passe par l'API WordPress publique du site plutôt que par l'analyse des pages : une requête par appel, données structurées, et une rupture de format détectée (nombre de points clés extraits comparé au nombre annoncé). L'édition complète, payante et envoyée par e-mail, n'est pas récupérée ; les contenus restent à usage personnel (CGV).

## Réglages de génération (skill `sampling`)
Claude ne peut pas régler sa température : l'échantillonnage a lieu côté serveur, avant toute réponse, et `temperature`/`top_p`/`top_k` sont refusés par les modèles actuels (et par la version d'API `2026-10-21` sur tous les modèles). Leviers réels : `effort` et modèle, exposés par `generate.py` (par défaut via `claude -p` et le compte connecté, Sonnet 5.5, sans clé API ; `--api` avec une clé). Le reste (registre, déterminisme apparent, style) relève d'une consigne de comportement, présentée comme telle. Un échantillonnage réel (glouton, logits visibles) exige un modèle à poids ouverts local (`~/ai/3-llm/`).
