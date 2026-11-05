# BCAI

[![Licence AGPL-3.0](https://img.shields.io/badge/Licence-AGPL--3.0-blue?style=for-the-badge)](LICENSE)
[![Documentation](https://img.shields.io/badge/Documentation-_?style=for-the-badge&logo=bookstack&color=grey)](docs/)

BCAI, anciennement Better Claude Instance (BCI), transforme votre Claude Code en une instance rangée, prudente et qui n'oublie rien, en une seule commande. Tout ce qui touche à l'IA tient dans un seul dossier, `~/ai`, vos projets dans `~/project`, et vos données sensibles ne sortent jamais de leur place.

Vous y gagnez une mémoire écrite au fil de l'eau, des personas à choisir d'un simple `@nom`, un sous-agent d'exécution unique, une recherche web locale sans clé, des sauvegardes quotidiennes et un coffre pour vos clés. Plus besoin de tout configurer à la main : BCAI s'en charge, et ce qu'il retire de votre configuration part dans une corbeille au lieu d'être effacé.

> [!NOTE]
> BCAI fonctionne sous Windows 10 / 11, Linux et Android (Termux). Il n'est pas conçu pour l'environnement Apple : ni macOS, ni iPhone, ni iPad.

## Utilisation

> [!WARNING]
> BCAI déplace votre configuration de Claude Code (`~/.claude`) dans `~/ai`. Aucun de vos fichiers n'est effacé : les anciens vont dans `~/ai/4-trash/`, tout fichier remplacé est gardé en `*.bak-bcai`, et une sauvegarde complète est faite avant et après la première installation. Exceptions : sous Termux, `~/.claude/downloads` (reste d'un essai d'installation incompatible) est supprimé ; quelques dossiers vides sont retirés (`2-plugins` avant d'y placer vos plugins, l'ancien `2-tools/0-mcp/sensible`) ; `bcai keys close` efface la version en clair de `4-keys-code` une fois le coffre chiffré et vérifié. Lisez tout de même ce que l'installation va faire avant de la lancer.

### Méthode recommandée : laissez votre agent installer

Vous utilisez déjà Claude Code ? Alors votre instance a sa propre histoire : un `CLAUDE.md`, des skills, des agents, des réglages, des serveurs MCP, peut-être une mémoire. Votre agent peut la regarder et adapter l'import au lieu d'appliquer une recette toute faite.

1. Ouvrez Claude Code comme d'habitude.
2. Copiez-collez ce message :

```
Installe BCAI sur cette machine en suivant son guide pour agents :
https://raw.githubusercontent.com/matglitch-974/bcai/main/SETUP.md
Lis-le en entier, puis les fichiers qu'il désigne. Fais l'inventaire de mon installation actuelle de Claude Code (CLAUDE.md, skills, agents, réglages et hooks, serveurs MCP, mémoire, plugins) et de ce que l'installateur toucherait. Présente-moi ton plan, élément par élément, avec ce que tu proposes de garder, d'adapter ou de laisser de côté. Ne modifie rien avant ma validation explicite.
```

3. Lisez le plan, demandez les changements que vous voulez (« garde ça, ne copie pas mes cookies, laisse mes modèles où ils sont »), puis validez.
4. À la fin, fermez la session, ouvrez un nouveau terminal et tapez `claude`.

Le guide suivi par l'agent est [SETUP.md](SETUP.md) : il lui interdit de supprimer quoi que ce soit, de sortir un secret de son coffre ou de toucher à vos dossiers `sensible/`.

### Méthode rapide : une commande

Vous débutez avec Claude Code, ou vous voulez simplement la configuration de référence ? Lancez le script.

**Windows**

1. Ouvrez PowerShell.
2. Copiez-collez la commande ci-dessous :

```PowerShell
irm matglitch-974.github.io/bc.ps1 | iex
```

3. Attendez la fin de l'installation (Git, Python, uv, Claude Code et les outils sont installés s'ils manquent).
4. Ouvrez un nouveau terminal et tapez `claude`. Au premier lancement, connectez-vous à votre compte Anthropic.

**Linux / Android (Termux)**

1. Ouvrez un terminal. Sur Android, installez d'abord [Termux depuis F-Droid](https://f-droid.org/packages/com.termux/) (la version du Play Store est obsolète).
2. Copiez-collez la commande ci-dessous :

```sh
curl -sL matglitch-974.github.io/bc | sh
```

3. Attendez la fin de l'installation. Sous Android, le script installe Alpine Linux et s'y relance tout seul.
4. Ouvrez un nouveau terminal (sous Android : fermez puis rouvrez Termux) et tapez `claude`. Au premier lancement, connectez-vous à votre compte Anthropic.

<details>
  <summary>Commandes de secours, si <code>matglitch-974.github.io</code> est inaccessible.</summary><br/>

  Windows :
  ```PowerShell
  irm https://raw.githubusercontent.com/matglitch-974/bcai/main/install.ps1 | iex
  ```
  Linux / Android :
  ```sh
  curl -fsSL https://raw.githubusercontent.com/matglitch-974/bcai/main/install.sh | sh
  ```
</details>

À la fin, l'installateur vous propose de chiffrer votre coffre de clés avec une phrase secrète. Vous pouvez répondre non et le faire plus tard avec `bcai keys close`.

### Après l'installation

Tout se pilote avec la commande `bcai` :

| Commande | Ce qu'elle fait |
|---|---|
| `bcai install` | met à jour BCAI depuis GitHub (alias : `bcai update`) ; vos fichiers ne sont pas écrasés |
| `bcai status` | fait le point : versions, configuration, recherche web, sauvegardes |
| `bcai backup` | sauvegarde tout de suite (`bcai backup list` pour les voir) |
| `bcai search "requête"` | recherche web locale, sans clé |
| `bcai keys open` / `close` | ouvre ou referme le coffre chiffré de vos clés |
| `bcai import` | réimporte vos skills, agents, secrets ou autres LLM (sans doublon) |
| `bcai uninstall` | désinstalle, après deux confirmations |

Installé avant le renommage en BCAI ? `bci install` (l'ancien nom, désormais obsolète, qui appelle `bcai`) ou la commande d'installation ci-dessus migre tout seul : dossier, sauvegardes, réglages ([détail](docs/installation.md#mise-à-jour-dune-installation-bci)).

## Fonctionnalités

Voici ce que BCAI apporte à votre Claude Code. Chaque point renvoie à la documentation pour le détail.

> [!TIP]
> `bcai uninstall` remet l'essentiel en place : votre configuration revient dans `~/.claude`, et `~/ai` et `~/project` ne sont touchés que si vous le demandez, avec un mot de confirmation à taper en entier. Ce n'est pas un retour complet en arrière : les MCP `duckduckgo` et `brave` retirés à l'installation ne sont pas restaurés, les MCP ajoutés (`fetch`, `searxng`, `playwright`, `scrapling`) restent déclarés, et toutes les entrées `Agent(…)` de `permissions.deny` sont retirées, y compris les vôtres. Voir [la désinstallation](docs/uninstall.md).

#### Un seul dossier pour l'IA

- `~/.claude` disparaît : Claude Code lit sa configuration dans `~/ai` (variable `CLAUDE_CONFIG_DIR`).
- Personas, espace de travail, outils, autres LLM, corbeille et mémoire ont chacun leur dossier numéroté.
- Vos projets vivent dans `~/project/<catégorie>/<project>/<sub-project>/`, un dépôt Git par unité.

Voir [l'architecture](docs/architecture.md) et [les projets](docs/projects.md).

#### Une mémoire qui ne perd rien

- Un journal du jour écrit à chaque événement : vous pouvez fermer à tout moment.
- Un sommaire des tâches ouvertes de tous vos projets, mis à jour à chaque démarrage.
- Des règles de réalignement réinjectées tous les 10 messages et après chaque compaction.

Voir [la mémoire](docs/memory.md) et [le hook mémoire](docs/memory-hook.md).

#### Personas et sous-agent

- Choisissez le persona de la session en commençant votre premier message par `@nom`.
- Un seul sous-agent, `slave`, pour toutes les tâches déléguées : les agents intégrés de Claude Code sont désactivés.
- Des agents isolés, avec leur propre mémoire, cloisonnés du reste de l'instance.

Voir [les personas et agents](docs/agents.md).

#### Vos secrets restent à leur place

- Clés SSH, jetons, identifiants d'outils et cookies sont rassemblés dans `~/ai/2-tools/4-keys-code`, chiffrable avec restic.
- Un dossier `sensible/` dans chaque projet, exclu de Git et bloqué par deux gardes (commandes de Claude Code et hook `pre-push`).

Voir [le coffre des clés](docs/keys.md) et [les protections](docs/projects.md#protections).

#### Recherche web sans clé

- SearXNG en local : un métamoteur qui interroge Google, Bing, Brave, DuckDuckGo et bien d'autres, sans compte ni clé.
- Serveurs MCP `fetch`, `searxng`, `playwright` et `scrapling`, plus Crawl4AI pour explorer des sites entiers.

Voir [la recherche web](docs/missions.md#recherche-web-skill-scraping).

#### Sauvegardes automatiques

- Une sauvegarde de tout `~/ai` par jour, dédupliquée et compressée (restic, ou archive `tar.xz` à défaut).
- Rotation « tour de Hanoï » : au plus 10 sauvegardes, des plus récentes aux plus anciennes.

Voir [les sauvegardes](docs/memory.md#sauvegardes-hooksbcai-backuppy).

#### Votre existant est repris

- Vos skills, agents, réglages, hooks et serveurs MCP sont conservés (sauf les MCP `duckduckgo` et `brave`, remplacés par SearXNG) ; un skill au nom déjà pris est renommé, pas écrasé.
- Les configurations de vos autres LLM (Ollama, Codex, Gemini, Grok, LM Studio…) sont copiées dans `~/ai/3-llm`.

Voir [l'import](docs/scripts.md#bcai-importpy) et [l'installation](docs/installation.md).

## L'architecture

```
~/ai/
├── AGENTS.md          sommaire + règles de travail (lu à chaque session)
├── 0-persona/         personas (choisis par @nom) ; system-agents/slave.md
├── 1-bench/           espace de travail temporaire, un secteur par sous-agent
├── 2-tools/           0-mcp, 1-skills, 2-plugins, 3-software, 4-keys-code, logs
├── 3-llm/             autres LLM (configs, modèles)
├── 4-trash/           corbeille : rien n'est supprimé, tout y est déplacé
└── memory/            INDEX.md, TODO.md, realign.md, journal/
~/project/<catégorie>/<project>/<sub-project>/   avec sensible/, jamais publié
```

Le détail de chaque dossier est dans [l'architecture](docs/architecture.md).

## Documentation

- [Architecture](docs/architecture.md) : la structure de `~/ai` et `~/project`, et la raison de chaque choix
- [Installation](docs/installation.md) : plateformes, ce que fait l'installateur, commande `bcai`
- [Scripts](docs/scripts.md) : ce que fait chaque script du dépôt et de l'instance
- [Hook mémoire](docs/memory-hook.md) : journal, TODO, sauvegarde quotidienne, persona, rangement de `~/.claude`
- [Mémoire et sauvegardes](docs/memory.md) : index, todos, réalignement, restic
- [Personas et agents](docs/agents.md) : `@nom`, `slave`, agents isolés
- [Coffre des clés](docs/keys.md) : `4-keys-code`, import et chiffrement
- [Projets](docs/projects.md) : hiérarchie, `sensible/`, protections
- [Espace de travail](docs/workspace.md) : secteurs de `1-bench`, corbeille
- [Missions et recherche web](docs/missions.md) : reconnaissance d'outils, SearXNG, scraping
- [Désinstallation](docs/uninstall.md)
- [Dépannage](docs/troubleshooting.md)
- [Nommage et langue](docs/naming.md)
- [Feuille de route](docs/roadmap.md)

## Licence

BCAI est distribué sous [AGPL-3.0-or-later](LICENSE), avec un terme additionnel d'attribution ([NOTICE](NOTICE)) :
- vous pouvez tout faire avec ce projet : l'utiliser, le modifier, le redistribuer ;
- toute œuvre qui en dérive doit rester open source, sous la même licence (y compris lorsqu'elle est proposée comme service en ligne) ;
- elle doit mentionner « BCAI, par matglitch-974 » dans son README et sa documentation officielle.

La licence couvre les œuvres dérivées de ce projet, pas les projets que vous créez simplement en utilisant l'instance.
