# Better Claude Instance

Une instance de Claude Code rangée, portable et prête à l'emploi : règles de travail exigeantes, un sous-agent d'exécution unique, un espace de travail temporaire découpé en secteurs, une organisation des projets qui sépare d'office les données sensibles, et une installation en une seule commande.

> Non conçu pour l'environnement Apple : ni macOS, ni iPhone, ni iPad.

## Installation

### Windows
Dans PowerShell :
```
irm matglitch-974.github.io/BCI.ps1 | iex
```
Commande de secours (adresse complète, si `matglitch-974.github.io` est inaccessible) :
```
irm https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/install.ps1 | iex
```

### Linux / Android (Termux)
Dans un terminal, ou dans l'application Termux installée depuis F-Droid :
```
curl -sL matglitch-974.github.io/BCI | sh
```
Commande de secours (adresse complète, si `matglitch-974.github.io` est inaccessible) :
```
curl -fsSL https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/install.sh | sh
```

Au premier lancement de `claude`, connectez-vous à votre compte Anthropic. Ensuite : `bci install` met à jour, `bci uninstall` désinstalle, `bci status` fait le point (voir [la commande bci](docs/installation.md#commande-bci)). Pour adapter l'installation à vos besoins plutôt que de l'appliquer telle quelle, voir l'[installation négociée](docs/installation.md#installation-négociée).

## Ce que vous obtenez

```
~/ai/
├── AGENTS.md          sommaire + règles de travail
├── 0-persona/         personas ; system-agents/slave.md (l'unique sous-agent)
├── 1-bench/           espace de travail temporaire, un secteur par sous-agent
├── 2-tools/           0-mcp, 1-skills, 2-plugins, 3-software
├── 3-llm/             modèles locaux
├── 4-trash/           corbeille
└── memory/           mémoire écrite en continu : INDEX.md, TODO.md, realign.md, journal/
~/project/<catégorie>/<project>/<sub-project>/   avec sensible/ jamais publié
```

## Documentation
- [Architecture](docs/architecture.md) : la structure et la raison de chaque choix
- [Installation](docs/installation.md) : plateformes, fonctionnement, désinstallation, dépannage
- [Personas et agents](docs/agents.md) : persona principal, `slave`, amélioration continue
- [Mémoire](docs/memory.md) : index, todos, journal automatique, réalignement
- [Missions et recherche web](docs/missions.md) : reconnaissance d'outils, arbre de tâches, scraping, réglages de génération
- [Espace de travail](docs/workspace.md) : secteurs de `1-bench`, corbeille
- [Projets](docs/projects.md) : hiérarchie, unité, `sensible/`, protections
- [Nommage et langue](docs/naming.md)
- [Feuille de route](docs/roadmap.md)

## Licence
[AGPL-3.0-or-later](LICENSE), avec un terme additionnel d'attribution ([NOTICE](NOTICE)) :
- vous pouvez tout faire avec ce projet : l'utiliser, le modifier, le redistribuer ;
- toute œuvre qui en dérive doit rester open source, sous la même licence (y compris lorsqu'elle est proposée comme service en ligne) ;
- elle doit mentionner « Better Claude Instance, par matglitch-974 » dans son README et sa documentation officielle.

La licence couvre les œuvres dérivées de ce projet, pas les projets que vous créez simplement en utilisant l'instance.
