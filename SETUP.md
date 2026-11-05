# SETUP.md — guide d'installation pour un agent Claude Code

Ce fichier s'adresse à **l'agent** (Claude Code) à qui l'utilisateur demande, en n'importe quels termes, d'installer, d'adapter, de mettre à jour ou de désinstaller BCAI. Un humain peut le lire, mais il est écrit pour être exécuté.

Pourquoi passer par un agent : chaque instance de Claude Code est différente (`CLAUDE.md`, skills, agents, réglages, hooks, serveurs MCP, mémoire). L'installateur applique une recette fixe ; toi, tu peux voir ce qui existe déjà et adapter l'import.

## Règle d'or
**Aucune modification avant la validation explicite de l'utilisateur.** Les étapes 1 à 3 ne font que lire. Rien n'est créé, déplacé ni installé avant l'étape 4.

## Ce que tu ne fais jamais
- **Supprimer.** Tout ce qui doit disparaître est déplacé dans `~/ai/4-trash/` (nom horodaté, unique). Seule exception : ton propre secteur de travail dans `~/ai/1-bench/`, s'il existe.
- **Copier un secret hors de `~/ai/2-tools/4-keys-code/`** : clé SSH, jeton, clé d'API, cookie, `.credentials.json`, `secrets.env`. Ni dans un rapport, ni dans la mémoire, ni dans un projet, ni dans le chat. Tu peux citer le **nom** d'une variable ou d'un fichier, jamais sa **valeur**.
- **Lire, copier ou publier le contenu d'un dossier `sensible/`.**
- **Saisir ou demander une phrase secrète.** Le chiffrement de `4-keys-code` se fait par l'utilisateur lui-même, dans son terminal (`bcai keys close`).
- **Écraser un fichier existant sans sauvegarde** (`<fichier>.bak-bcai`, comme le fait l'installateur).
- **Pousser, publier ou envoyer** quoi que ce soit (`git push`, gist, upload).
- **Vider `~/ai/4-trash/`**, ni lancer la suppression de `~/ai` ou de `~/project` : c'est à l'utilisateur de le faire.

## 1. Lire
Lis, dans cet ordre, depuis GitHub (`https://raw.githubusercontent.com/matglitch-974/Better-Context-of-Agents-Instance/main/<fichier>`) ou depuis un clone placé dans un dossier temporaire du système (pas encore dans `~/ai`) :
1. `docs/architecture.md` : la structure cible de `~/ai` et `~/project` ;
2. `skeleton/ai/AGENTS.md` : les règles que l'instance installée lira à chaque session ;
3. `install.ps1` (Windows) ou `install.sh` puis `bootstrap.sh` (Linux, Android) : ce que l'installateur fait réellement ;
4. `hooks/bcai-import.py` : ce qu'il copie (skills, agents, secrets, autres LLM) ;
5. `docs/scripts.md`, `docs/memory-hook.md`, `docs/keys.md` : le détail des scripts, du hook et du coffre.

Fie-toi aux scripts plutôt qu'à la documentation en cas d'écart, et signale l'écart.

## 2. Faire l'inventaire
Relève, sans rien modifier :

| À relever | Où regarder | Ce que l'installateur en fait |
|---|---|---|
| Système, shell, gestionnaire de paquets, `winget` présent ou non | — | choisit `install.ps1` ou `install.sh` ; sans winget, replis (uv, restic depuis GitHub) mais Git doit déjà être là |
| Claude Code installé, version | `claude --version` | l'installe s'il manque (installateur officiel) |
| `CLAUDE_CONFIG_DIR` déjà défini | variable d'environnement | la fixe à `~/ai/2-tools/3-software/claude-code` |
| `~/.claude/CLAUDE.md` | contenu | **mis de côté** en `claude-code/CLAUDE.md.bak-bcai` : il n'est plus chargé, `CLAUDE.md` pointe vers `~/ai/AGENTS.md` |
| `~/.claude/skills/` | liste des skills | copiés dans `~/ai/2-tools/1-skills/` ; nom déjà pris : renommé `<nom>1`, conflit noté dans `memory/TODO.md` |
| `~/.claude/agents/` | liste des agents | copiés dans `~/ai/0-persona/` (choisis par `@<nom>`) ; le dossier d'origine reste dans `claude-code/agents/` |
| `~/.claude/settings.json` | `permissions`, `hooks`, `env` | conservé et complété : 6 agents intégrés refusés (`Agent(Explore)`, `Agent(Plan)`, `Agent(general-purpose)`, `Agent(statusline-setup)`, `Agent(claude-code-guide)`, `Agent(claude)`), hooks `guard-sensible` et `memory-hook` ajoutés ; vos autres hooks restent |
| Serveurs MCP | `claude mcp list`, `~/.claude.json` | `.claude.json` est déplacé dans `claude-code/` : vos MCP suivent. Ajouts : `fetch`, `searxng`, `playwright`, `scrapling` ; **retraits** : `duckduckgo` et `brave` s'ils existent en portée utilisateur |
| `~/.claude/plugins/` | liste | déplacé dans `~/ai/2-tools/2-plugins/` (s'il est vide), sinon en `plugins.bak-bcai` |
| Mémoire existante | `~/.claude/projects/*/memory/`, fichiers de mémoire maison | rien n'est importé dans `~/ai/memory/` : à proposer |
| Dossiers `~/ai` et `~/project` existants | contenu | les fichiers de `skeleton/` ne sont copiés que s'ils manquent |
| Secrets que l'import copierait | `~/.ssh`, variables dont le nom contient KEY, TOKEN, SECRET, PASSWORD ou API, `.git-credentials`, `.netrc`, `.npmrc`, `.pypirc`, `~/.aws`, `~/.kube/config`, `~/.docker/config.json`, rclone, `gh`, identifiants de Claude Code, cookies Firefox / Chrome / Edge / Brave | **copiés** dans `~/ai/2-tools/4-keys-code/` (les originaux restent) ; ne relève que les noms |
| Autres LLM | `~/.ollama`, `~/.codex`, `~/.gemini`, `~/.grok`, `~/.lmstudio`, opencode, aider… | configs copiées dans `~/ai/3-llm/` ; **modèles Ollama déplacés** vers `~/ai/3-llm/models/ollama` et `OLLAMA_MODELS` modifié |
| Sessions Claude Code ouvertes | processus `claude` | ta propre session en fait partie : voir l'étape 5 |

## 3. Présenter le plan et attendre
Présente à l'utilisateur, élément par élément :
- ce qui sera **créé** (`~/ai`, `~/project`, commande `bcai`, variable `CLAUDE_CONFIG_DIR`, outils de recherche web) ;
- ce qui sera **déplacé ou mis de côté** (`~/.claude`, `~/.claude.json`, ton `CLAUDE.md`, modèles Ollama) ;
- ce qui sera **copié** (skills, agents, secrets, configs d'autres LLM) ;
- ce qui sera **ajouté ou retiré** dans les réglages et les MCP ;
- tes **propositions d'adaptation**, par exemple : reprendre les règles utiles de l'ancien `CLAUDE.md` dans `~/ai/AGENTS.md` ou dans `~/ai/memory/` ; garder un agent intégré que l'utilisateur utilise ; ne pas importer les cookies ; laisser les modèles Ollama où ils sont ; ne pas retirer un MCP `brave` configuré avec une clé.

Laisse l'utilisateur garder, déplacer, renommer ou retirer n'importe quel élément. Note chaque écart à la référence. Récapitule le plan final et **attends une confirmation explicite** (« oui, vas-y » ou équivalent). Sans réponse claire, ne fais rien.

## 4. Appliquer
**Sans écart** : lance l'installateur officiel, sans interaction (le chiffrement est fait plus tard par l'utilisateur) :
- Windows (depuis PowerShell) :
  ```
  $env:BCAI_ENCRYPT_KEYS='non'; irm https://raw.githubusercontent.com/matglitch-974/Better-Context-of-Agents-Instance/main/install.ps1 | iex
  ```
- Linux, Android (Termux) :
  ```
  curl -fsSL https://raw.githubusercontent.com/matglitch-974/Better-Context-of-Agents-Instance/main/install.sh | BCAI_ENCRYPT_KEYS=non sh
  ```
  Sous Linux, l'installation des paquets passe par `sudo` : si un mot de passe est demandé, l'utilisateur lance la commande lui-même. Sous Termux, `install.sh` se relance dans Alpine sans transmettre `BCAI_ENCRYPT_KEYS` : la question du chiffrement peut y être posée au terminal.

**Avec écarts** : reproduis les étapes de l'installateur à la main, dans l'ordre du script de la plateforme, en sautant ou modifiant ce que l'utilisateur a refusé :
- Windows (`install.ps1`) : sauvegarde `install-avant`, arborescence et skeleton, import, `CLAUDE_CONFIG_DIR` et migration de `~/.claude`, liens, réglages, outils, commande `bcai`, chiffrement proposé, sauvegarde `install-apres` ;
- Linux (`bootstrap.sh`) : sauvegarde `install-avant`, arborescence et skeleton, commande `bcai`, environnement (`PATH`, `CLAUDE_CONFIG_DIR`), import, migration de `~/.claude`, réglages, liens, outils, chiffrement proposé, sauvegarde `install-apres`.

Les étapes d'import sont séparables : `python3 hooks/bcai-import.py skills|agents|secrets|llm`. Un élément de `~/.claude` qu'on ne veut pas migrer est déplacé ailleurs **avant** la migration, jamais supprimé.

Puis applique les adaptations validées (fusion de l'ancien `CLAUDE.md`, souvenirs à écrire dans `~/ai/memory/<type>/` avec leur ligne dans `INDEX.md`, etc.) et mets à jour `~/ai/AGENTS.md` (sommaire et chemins) pour qu'il décrive la structure réellement installée.

## 5. Vérifier
- `bcai status` (nouveau terminal) : `CLAUDE_CONFIG_DIR` pointe vers `~/ai/2-tools/3-software/claude-code`.
- `claude-code/CLAUDE.md` mène à `~/ai/AGENTS.md` (lien sous Linux ; ligne `@~/ai/AGENTS.md` sous Windows).
- `claude-code/skills`, `plugins`, `agents/0-persona` sont des liens (jonctions sous Windows) vers `~/ai` ; l'ancien `agents/system-agents` n'existe plus.
- `settings.json` contient les hooks `guard-sensible` et `memory-hook`, et les anciens hooks de l'utilisateur.
- `claude mcp list` : anciens MCP présents, nouveaux ajoutés (un échec d'outil web n'est pas bloquant : signale-le).
- `~/ai/2-tools/logs/backup-bcai/` contient `install-avant` et `install-apres` (les deux sont faites à la première installation : l'installateur crée `~/ai` pour y cloner le dépôt avant la sauvegarde `install-avant`).
- Les avertissements de la sortie de l'installateur, `ATTENTION` sous Linux, `AVERTISSEMENT` sous Windows (préfixe de `Write-Warning`, `WARNING` sur un Windows en anglais) : relève-les tous.

Ta session a démarré avant l'installation : elle lit encore l'ancienne configuration et peut recréer `~/.claude`. C'est prévu : l'installateur laisse `~/.claude/.credentials.json` aux sessions ouvertes, et le hook mémoire range ce reliquat dans `4-trash` au premier démarrage d'une session BCAI où aucune autre session ne tourne.

## 6. Rapport final
- ce qui a été fait, les écarts retenus, les avertissements ;
- ce qui reste à l'utilisateur : fermer cette session, ouvrir un **nouveau terminal**, lancer `claude` (se connecter si demandé) ; s'il le souhaite, chiffrer `4-keys-code` avec `bcai keys close` ;
- aucun secret, aucune valeur de variable, aucun contenu de `sensible/` dans le rapport.

## Toujours appliqué, même en cas d'adaptation
- `sensible/` reste exclu par `.gitignore` dans chaque unité de projet.
- Le hook `hooks/guard-sensible.sh` reste actif. Sécurités supplémentaires à proposer, jamais imposer : analyse de secrets avant publication (ex. gitleaks), vérification de la visibilité du dépôt distant avant un push. Le hook Git `pre-push` est déjà posé par `new-unit` dans chaque unité.
- Aucun fichier existant n'est écrasé sans sauvegarde `*.bak-bcai`.

## Mise à jour
`bcai install` (ou `bcai update`) : `git pull` du dépôt puis réinstallation ; rien de personnel n'est écrasé. Après une mise à jour, relis le diff du dépôt et signale ce qui change pour l'utilisateur.

Installation d'avant le renommage en BCAI (dossier `~/ai/2-tools/3-software/better-claude-instance`, commande `bci`) : `bci install`, ou la commande d'installation, la migre ([docs/installation.md](docs/installation.md#mise-à-jour-dune-installation-bci)). Ensuite, `python3 ~/ai/2-tools/3-software/bcai/hooks/bcai-migrate.py --check` (Windows : `python`) liste ce qui reste à migrer, dont les fichiers de mémoire, de personas ou de skills qui citent encore l'ancien chemin : propose leur correction à l'utilisateur, ne la fais pas sans son accord.

## Désinstallation
La désinstallation demande deux confirmations tapées au clavier, puis deux autres avant chaque suppression : **l'utilisateur la lance lui-même** (`bcai uninstall`). Tu peux lui expliquer ce qu'elle fait ([docs/uninstall.md](docs/uninstall.md)) et, s'il le demande, préparer les étapes réversibles à la main (remettre la configuration dans `~/.claude`, retirer `CLAUDE_CONFIG_DIR`, restaurer les `*.bak-bcai`, retirer les réglages ajoutés). La suppression de `~/ai` et `~/project` n'est jamais de ton ressort.
