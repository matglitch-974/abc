# Architecture

## Vue d'ensemble

```
~/
├── ai/                                   tout ce qui concerne l'IA (~/.claude n'existe plus)
│   ├── AGENTS.md                         sommaire + règles de travail
│   ├── 0-persona/                        personas et agents (contenu non numéroté)
│   │   ├── <persona>.md                  personas, nom libre ; choisi par `@<nom>` en début de session
│   │   └── system-agents/
│   │       └── slave.md                  le sous-agent par défaut
│   ├── 1-bench/                          espace de travail temporaire (secteurs)
│   ├── 2-tools/
│   │   ├── 0-mcp/                        serveurs MCP
│   │   ├── 1-skills/                     skills : persona, bench, project, memory, context, mission, search, scraping, sampling, specula, leçons…
│   │   ├── 2-plugins/                    plugins de Claude Code
│   │   ├── 3-software/                   logiciels de l'IA
│   │   │   ├── bcai/                     ce dépôt
│   │   │   ├── searxng/                  métamoteur local (skill search) ; réglages : searxng-settings.yml
│   │   │   └── claude-code/              configuration de Claude Code (CLAUDE_CONFIG_DIR) : historiques, caches, .claude.json
│   │   │       ├── CLAUDE.md  ───────▶ ~/ai/AGENTS.md
│   │   │       ├── skills     ───────▶ ~/ai/2-tools/1-skills/
│   │   │       ├── plugins    ───────▶ ~/ai/2-tools/2-plugins/
│   │   │       ├── agents/0-persona ─▶ ~/ai/0-persona/
│   │   │       └── settings.json ────▶ ~/ai/memory/settings.json
│   │   ├── 4-keys-code/                  clés SSH, jetons, clés d'API, cookies (copies de l'existant)
│   │   ├── 4-keys-code.restic/           coffre chiffré de 4-keys-code, si choisi (bcai keys)
│   │   └── logs/
│   │       └── backup-bcai/              sauvegardes (voir memory.md)
│   ├── 3-llm/                            autres LLM : configs copiées, llms.md, models/ (modèles Ollama)
│   ├── 4-trash/                          corbeille
│   ├── isolated/<nom>/                   mémoire et journal des agents isolés (cloisonnés)
│   └── memory/                           mémoire (voir memory.md)
│
└── project/
    └── <catégorie>/
        └── <project>/
            └── <sub-project>/            unité = dépôt Git (voir projects.md)
```

## Pourquoi chaque choix

### `~/.claude/` disparaît : tout vit dans `~/ai`
Claude Code lit sa configuration dans le dossier que désigne la variable `CLAUDE_CONFIG_DIR` (vérifié : `.claude.json` y est aussi rangé). L'installateur la fixe à `~/ai/2-tools/3-software/claude-code/` (`.profile`, `.bashrc`, `.zshrc` ; variable utilisateur sous Windows) et y déplace l'ancien `~/.claude` et `~/.claude.json`. Chaque élément utile y est un lien vers sa place dans `~/ai` : instructions, skills, plugins, agents, réglages (rangés avec la mémoire : ce sont des autorisations personnelles). Tout ce qui concerne l'IA tient ainsi dans un seul dossier, sauvegardé d'un bloc.
Risque : si `CLAUDE_CONFIG_DIR` manque (terminal qui ne lit pas `.profile`), Claude Code recrée un `~/.claude` vide et semble avoir tout oublié. Parade : ouvrir un nouveau terminal, ou `. ~/.profile`, puis déplacer ce `~/.claude` dans `~/ai/4-trash/` (le hook mémoire le fait au lancement suivant, voir [memory-hook.md](memory-hook.md#rangement-de-claude)). Windows : `settings.json` reste un vrai fichier dans `claude-code/` (un lien de fichier y exige des droits administrateur).

### `AGENTS.md` plutôt que `CLAUDE.md`
`AGENTS.md` est le nom ouvert, lu par plusieurs outils d'IA. `CLAUDE.md` n'existe que là où Claude Code l'exige, sous forme de lien vers `AGENTS.md` (sous Windows, un fichier d'une ligne `@~/ai/AGENTS.md`, car les liens de fichiers y exigent des droits administrateur).

### `AGENTS.md` = sommaire + règles de travail
Tout ce qui fait la qualité du travail y est : aucune invention, outils existants d'abord, script plutôt qu'IA, vérification des sources, amélioration continue, délégation. Le persona principal n'y ajoute qu'un caractère : le retirer ne dégrade rien.

### Numérotation `N-nom`
Les dossiers à contenu fixe sont numérotés de 0 à 9 pour imposer un ordre de lecture stable, identique sur toutes les machines. Un dossier dont le contenu peut dépasser 10 éléments (personas, skills, projets) ne numérote pas son contenu. Ordre retenu à la racine : `0-persona` (identité), `1-bench` (travail en cours), `2-tools`, `3-llm`, `4-trash` (fin de vie).

### `0-persona/` à la racine d'`ai/`
Les personas ne sont pas des outils : ils définissent qui agit. Ils ont donc leur propre dossier, en tête. Les agents y sont rangés par catégorie (`<catégorie>-agents/`), la catégorie `system-agents/` étant le minimum.

### `3-software/` dans `2-tools/`
Un logiciel utilisé par l'IA est un outil au même titre qu'un serveur MCP ou un plugin.

### `3-llm/` à la racine d'`ai/`
Les modèles locaux ne sont pas des outils de Claude Code mais une autre source d'IA, au même niveau que l'instance.

### `1-bench/` et `4-trash/`
Voir [workspace.md](workspace.md).

## Dépôt du projet

```
bcai/
├── README.md
├── LICENSE, NOTICE              AGPL-3.0-or-later + attribution
├── AGENTS.md, CLAUDE.md         règles pour travailler sur ce dépôt
├── SETUP.md                     guide d'installation destiné à un agent Claude Code
├── VERSION                      version de BCAI (semver), reprise par bcai version et les sauvegardes
├── install.sh, install.ps1      installation Linux / Android, Windows
├── uninstall.sh, uninstall.ps1  désinstallation
├── bootstrap.sh                 création de ~/ai et ~/project (Linux)
├── bin/bcai, bcai.ps1, bcai.cmd  commande bcai
├── bin/bci, bci.ps1, bci.cmd     ancien nom de la commande (obsolète), appelle bcai
├── hooks/guard-sensible.sh      hook de protection de sensible/ et de 4-keys-code
├── hooks/memory-hook.py         mémoire, persona de session (@<nom>), rangement de l'ancien ~/.claude
├── hooks/bcai-backup.py         sauvegardes (restic ou tar.xz)
├── hooks/bcai-import.py         import de l'existant : skills, agents, secrets, autres LLM
├── hooks/bcai-keys.py           coffre chiffré de 4-keys-code (restic)
├── hooks/bcai-migrate.py        migration d'une installation d'avant BCAI (better-claude-instance)
├── skeleton/                    fichiers copiés tels quels dans ~/ (jamais écrasés)
└── docs/                        cette documentation
```
Rôle de chaque script : [scripts.md](scripts.md).

L'installateur clone le dépôt dans `~/ai/2-tools/3-software/bcai/` : c'est un logiciel de l'IA, mis à jour avec `git pull`.
