# Architecture

## Vue d'ensemble

```
~/
├── .claude/                              ce que Claude Code lit : uniquement des liens
│   ├── CLAUDE.md  ─────────▶ ~/ai/AGENTS.md
│   ├── skills     ─────────▶ ~/ai/2-tools/1-skills/
│   ├── agents/
│   │   └── system-agents ──▶ ~/ai/0-persona/system-agents/
│   └── settings.json                     agents intégrés désactivés + hook sensible/
│
├── ai/                                   tout ce qui concerne l'IA
│   ├── AGENTS.md                         sommaire + règles de travail
│   ├── 0-persona/                        personas et agents (contenu non numéroté)
│   │   ├── <persona principal>           facultatif, nom libre
│   │   └── system-agents/
│   │       └── slave.md                  l'unique sous-agent
│   ├── 1-bench/                          espace de travail temporaire (secteurs)
│   ├── 2-tools/
│   │   ├── 0-mcp/                        serveurs MCP
│   │   ├── 1-skills/                     skills : persona, bench, project, memory, leçons…
│   │   ├── 2-plugins/
│   │   └── 3-software/                   logiciels de l'IA, dont better-claude-instance
│   ├── 3-llm/                            modèles et runtimes locaux
│   ├── 4-trash/                          corbeille
│   └── memory/                           mémoire (voir memory.md)
│
└── project/
    └── <catégorie>/
        └── <project>/
            └── <sub-project>/            unité = dépôt Git (voir projects.md)
```

## Pourquoi chaque choix

### `~/.claude/` ne contient que des liens
Claude Code cherche ses fichiers dans `~/.claude/`. En n'y mettant que des liens, la vraie source reste dans `~/ai/`, rangée selon nos règles et facile à sauvegarder ou synchroniser. Remplacer l'instance revient à refaire les liens.

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
better-claude-instance/
├── README.md
├── LICENSE, NOTICE              AGPL-3.0-or-later + attribution
├── AGENTS.md, CLAUDE.md         règles pour travailler sur ce dépôt
├── SETUP.md                     prompt d'installation négociée
├── install.sh, install.ps1      installation Linux / Android, Windows
├── uninstall.sh, uninstall.ps1  désinstallation
├── bootstrap.sh                 création de ~/ai et ~/project (Linux)
├── hooks/guard-sensible.sh      hook de protection de sensible/
├── skeleton/                    fichiers copiés tels quels dans ~/ (jamais écrasés)
└── docs/                        cette documentation
```

L'installateur clone le dépôt dans `~/ai/2-tools/3-software/better-claude-instance/` : c'est un logiciel de l'IA, mis à jour avec `git pull`.
