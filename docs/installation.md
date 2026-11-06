# Installation

## Plateformes
- **Windows 10 / 11** : `ABC-install-<version>.ps1` (PowerShell). Windows 7 n'est pas pris en charge par Claude Code.
- **Linux** : `ABC-install-<version>.sh`. Debian, Ubuntu, Alpine, Fedora, Arch, openSUSE et dérivés (détection du gestionnaire de paquets).
- **Android** : `ABC-install-<version>.sh` dans l'application Termux. Le script détecte Termux, installe Alpine Linux et se relance à l'intérieur.
- **Apple (macOS, iOS)** : non conçu pour cet environnement, non testé.

## Deux façons d'installer

### Par votre agent Claude Code (recommandé si vous l'utilisez déjà)
Votre instance a déjà ses skills, agents, réglages, MCP, peut-être une mémoire : l'agent en fait l'inventaire, vous présente un plan, adapte l'import et n'agit qu'après votre accord. Le prompt à copier-coller est dans le [README](../README.md#méthode-recommandée--laissez-votre-agent-installer) ; le guide que suit l'agent est [SETUP.md](../SETUP.md).

### Par le script (configuration de référence)
Windows (PowerShell) :
```
irm matglitch-974.github.io/abc.ps1 | iex
```
Commande de secours (adresse complète, si `matglitch-974.github.io` est inaccessible) :
```
irm https://raw.githubusercontent.com/matglitch-974/abc/main/ABC-install-0.4.0.ps1 | iex
```

Linux / Android (Termux) :
```
curl -fsSL matglitch-974.github.io/abc | sh
```
Commande de secours (adresse complète, si `matglitch-974.github.io` est inaccessible) :
```
curl -fsSL https://raw.githubusercontent.com/matglitch-974/abc/main/ABC-install-0.4.0.sh | sh
```

Les installateurs portent la version dans leur nom : `ABC-install-<version>.ps1` et `ABC-install-<version>.sh` (version lue dans `VERSION`). Les commandes courtes passent par `matglitch-974.github.io` (GitHub Pages, dépôt `matglitch-974/matglitch-974.github.io`) : `…/abc.ps1` et `…/abc` sont de simples relais vers l'installateur de la dernière version, et ce dépôt reste la seule source de l'installateur. Les anciennes adresses `…/bc`, `…/bc.ps1`, `…/BCAI`, `…/BCAI.ps1`, `…/BCI`, `…/BCI.ps1` sont des alias au contenu identique.

### Publier une version
1. Mettre la nouvelle version dans `VERSION`, committer le code.
2. `sh publish.sh [dossier du dépôt Pages]` (défaut : `../matglitch-974.github.io`, ou `ABC_PAGES_DIR`) : renomme les installateurs d'après `VERSION` (`git mv`), réécrit `abc`, `abc.ps1` et les alias du dépôt Pages pour qu'ils visent cette version, et indexe le tout ; rien n'est committé ni poussé.
3. Committer les deux dépôts, pousser d'abord celui-ci (sinon le lien court viserait un fichier encore absent), puis le dépôt Pages. Penser à la commande de secours du README, qui cite la version.

Deux étapes ne peuvent pas être automatisées :
1. Android : installer d'abord **Termux depuis F-Droid** (la version du Play Store est obsolète).
2. Au premier lancement de `agent` (Claude Code), **se connecter à son compte Anthropic**.

Variables reconnues : `ABC_BRANCH` (branche du dépôt, `main` par défaut), `ABC_CLI` (nom de la commande de Claude Code, `agent` par défaut ; `claude` garde le nom d'origine, voir [plus bas](#commande-agent)), `ABC_ENCRYPT_KEYS=oui|non` (répond d'avance à la question du chiffrement), `ABC_MODELS_DIR` (dossier des modèles, `~/ai/3-llm/models` par défaut ; les modèles Ollama vont dans son sous-dossier `ollama/`). Les anciens noms `BCAI_*` sont encore lus pendant cette version si `ABC_*` n'est pas défini ; les noms `BCI_*` ne le sont plus.

## Ce que fait l'installateur
1. Installe les dépendances. Linux : curl, git, jq, python3, Node.js, npm (Alpine : + bash, ripgrep, libgcc, libstdc++), restic si disponible. Windows : Git, uv et Python par winget ; sans winget : uv par son script officiel, Python par uv, Git exigé (arrêt sinon). Sous Windows, Node.js et restic ne sont installés qu'à l'étape 10, avec les outils, après la migration (winget ; sans winget : restic depuis GitHub, Node.js signalé manquant).
2. Installe Claude Code avec l'installateur officiel d'Anthropic (`claude.ai/install.sh` ou `install.ps1`), s'il est absent, puis renomme sa commande `claude` en `agent` ([détail](#commande-agent)).
3. Clone ce dépôt dans `~/ai/2-tools/3-software/abc/` (ou le met à jour ; une installation d'avant le renommage est d'abord migrée, voir [plus bas](#mise-à-jour-dune-installation-bcai-ou-bci)).
4. Sauvegarde complète avant la première installation (`install-avant`, toujours faite : `~/ai` existe déjà puisque le dépôt vient d'y être cloné) ; une seconde (`install-apres`) à la fin. Les deux sont conservées à vie ([memory.md](memory.md#sauvegardes-hooksabc-backuppy)).
5. Crée `~/ai` et `~/project`, copie les fichiers de `skeleton/` sans jamais écraser un fichier existant.
6. Importe l'existant, par copie (les originaux restent) : skills et agents de `~/.claude`, secrets dans `2-tools/4-keys-code` ([keys.md](keys.md)), configs des autres LLM dans `3-llm/` ; les modèles Ollama sont déplacés une fois ([scripts.md](scripts.md#abc-importpy)).
7. Fixe `CLAUDE_CONFIG_DIR` à `~/ai/2-tools/3-software/claude-code/`, y range le contenu de `~/.claude` et `~/.claude.json`, puis met les originaux dans `~/ai/4-trash/`. Votre ancien `CLAUDE.md` et votre ancien dossier `skills` y sont gardés en `*.bak-abc`. Si des sessions de Claude Code (`agent` ou `claude`) tournent, `~/.claude/.credentials.json` leur est laissé ; le [hook mémoire](memory-hook.md#rangement-de-claude) le range plus tard.
8. Relie `CLAUDE.md` à `~/ai/AGENTS.md`, `skills`, `plugins` et `agents/0-persona` à leurs dossiers de `~/ai` (toutes les personas deviennent des sous-agents ; l'ancien lien `agents/system-agents` est retiré) ; `settings.json` est rangé dans `~/ai/memory/` (Linux) ou reste dans `claude-code/` (Windows).
9. Complète `settings.json` : agents intégrés désactivés, hooks `guard-sensible` et mémoire. Vos autres réglages et hooks sont conservés.
10. Installe les outils (sous Windows, d'abord restic et Node.js) et les outils web : SearXNG (métamoteur local, sans clé) et son MCP, `fetch`, `playwright`, `scrapling`, Crawl4AI. Retire les MCP `duckduckgo` et `brave` de portée utilisateur s'ils existent (remplacés par SearXNG). Un échec ici ne bloque pas l'installation.
11. Installe la commande `abc`.
12. Propose de chiffrer `4-keys-code` avec une phrase secrète (restic). Chiffré, il n'existe en clair qu'entre `abc keys open` et `abc keys close`, et n'entre jamais en clair dans les sauvegardes.

Tout fichier remplacé est gardé en `*.bak-abc`. Relancer la commande (ou `abc install`) met l'instance à jour sans toucher à vos fichiers. Détail script par script : [scripts.md](scripts.md).

## Commande `abc`
Installée avec ABC (`~/.local/bin/abc` ; Windows : `abc.cmd` ; Termux : `$PREFIX/bin/abc`, qui l'exécute dans Alpine). La toute première installation passe forcément par la commande ci-dessus : avant elle, `abc` n'existe pas.

`bcai`, l'ancien nom, est **obsolète** : pendant la version 0.4, il n'est gardé que là où il était installé, où il affiche « bcai est devenu abc » puis appelle `abc` avec les mêmes arguments (`bin/bcai`, `bin/bcai.cmd`) ; il disparaîtra à la version suivante. `bci`, plus ancien encore, est retiré (rangé dans `~/ai/4-trash/`).

| Commande | Effet |
|---|---|
| `abc install` (ou `abc update`) | met à jour depuis GitHub puis réinstalle ; aucun fichier personnel écrasé |
| `abc uninstall` | désinstalle, après deux confirmations (oui, puis le mot `desinstaller`) et un avertissement en rouge ; de même avant de supprimer `~/ai` ou `~/project` |
| `abc status` | versions, `CLAUDE_CONFIG_DIR`, SearXNG, nombre de sauvegardes, restic |
| `abc backup` / `abc backup list` | sauvegarde immédiate / liste |
| `abc search "requête"` | recherche web (skill `search`) |
| `abc keys open\|close\|status` | coffre chiffré de `2-tools/4-keys-code` (restic, phrase secrète) |
| `abc import [skills\|agents\|secrets\|llm]` | réimporte l'existant (copies, sans doublon) |
| `abc version` | version (fichier `VERSION`, semver) et commit installés |

## Commande `agent`
ABC lance Claude Code sous le nom `agent` au lieu de `claude`. Ce n'est pas un alias ni un script enveloppe : l'installateur **renomme** la commande créée par l'installateur officiel (Windows : `~/.local/bin/claude.exe` devient `agent.exe` ; Linux : le lien `~/.local/bin/claude` devient `agent`). Windows permet de renommer un exécutable en cours d'exécution : une session ouverte continue de tourner.

- **Garder `claude`** : installer avec `ABC_CLI=claude` (PowerShell : `$env:ABC_CLI='claude'` avant la commande d'installation). Un autre nom est possible de la même façon.
- **Revenir à `claude`** après coup : renommer `~/.local/bin/agent.exe` (ou `agent`) en `claude.exe` (ou `claude`) ; `abc uninstall` le fait. Les scripts d'ABC prennent `agent` s'il existe, sinon `claude` ; `ABC_CLI` force le choix. Si un outil tweakcc est configuré (`~/.tweakcc/config.json`, `ccInstallationPath`), le remettre sur le nouveau chemin.
- **Mise à jour ou réinstallation de Claude Code** : l'installateur officiel recrée `claude`. Relancer `abc install` : le `claude` neuf remplace l'ancien `agent`, rangé dans `~/ai/4-trash/`. Un patch tweakcc appliqué à l'ancien binaire est à rejouer (`node patch/apply-prompt-patch.mjs`, qui vise `agent`).

**Conflit de nom connu** : le CLI de Cursor (`cursor-agent`) s'installe lui aussi sous le nom `agent` (Linux et macOS : `~/.local/bin/agent`). L'installateur vérifie que `agent --version` répond « Claude Code » avant de remplacer quoi que ce soit ; sinon il laisse `claude` et l'indique. Si les deux sont présents, le premier dans le `PATH` gagne : choisir un autre nom avec `ABC_CLI`.

**Ce que Claude Code suppose encore du nom `claude`** (non modifié dans le binaire, à savoir) :
- ses messages et son aide citent `claude` (« run claude --resume … », `claude doctor`, `claude mcp …`, `claude update`) : taper `agent` à la place ;
- la mise à jour automatique (désactivée par ABC, `DISABLE_AUTOUPDATER`) et `claude update` / `claude install` écrivent `~/.local/bin/claude` : après une mise à jour, relancer `abc install` ;
- `claude doctor` peut signaler une installation incohérente (commande attendue sous le nom `claude`) : sans conséquence ;
- tweakcc cherche `claude` dans le `PATH` : lui donner le chemin par `TWEAKCC_CC_INSTALLATION_PATH` ou `ccInstallationPath` (ce que fait `patch/apply-prompt-patch.mjs`) ;
- sous Windows, l'application Claude Desktop s'appelle aussi `claude.exe` : les outils qui comptent les processus `claude` ne confondent plus le CLI avec elle.

Sous Termux, l'alias créé dans `~/.bashrc` s'appelle `agent` (l'ancien alias `claude` posé par l'installateur est retiré, après une copie `~/.bashrc.bak-abc-<date>`).

## Mise à jour d'une installation BCAI ou BCI
Avant ABC, le projet s'appelait BCAI (dossier `3-software/bcai`, commande `bcai`, sauvegardes `backup-bcai`) et, avant encore, Better Claude Instance (BCI : `better-claude-instance`, `bci`, `backup-bci`). Une installation de ces époques se met à jour avec la commande d'installation ci-dessus (les anciennes adresses courtes y mènent) ; `bcai install` fonctionne aussi : il met le dépôt à jour, puis les anciens points d'entrée `install.sh` et `install.ps1`, gardés comme renvois, lancent l'installateur versionné. Le démarrage d'une session fait de toute façon les étapes 1 à 6 ci-dessous. Rien n'est effacé :

1. L'ancien dossier du dépôt (`bcai/` ou `better-claude-instance/`) est renommé en `abc/` et son dépôt Git pointe vers `github.com/matglitch-974/abc` (GitHub redirige les anciennes adresses). Un lien (jonction sous Windows) reste à l'ancien emplacement : les sessions déjà ouvertes appellent encore leurs hooks par l'ancien chemin.
2. `~/ai/2-tools/logs/backup-bcai/` (ou `backup-bci/`) devient `backup-abc/` (fusionné élément par élément si `backup-abc/` existe déjà) ; les sauvegardes d'installation existantes restent celles de la première installation.
3. Les chemins de `settings.json` (hooks) sont corrigés, après une copie datée dans `backup-abc/reglages/`. Seuls ces chemins changent. Toute réécriture ultérieure de `settings.json` par l'installateur passe aussi par cette copie.
4. La commande `abc` est installée là où `bcai` ou `bci` l'était ; `bcai` devient le renvoi obsolète décrit plus haut ; `bci` est rangé dans `~/ai/4-trash/`.
5. `~/ai/AGENTS.md` et le skill `memory`, copiés du skeleton, reçoivent les nouveaux chemins (copie datée dans `backup-abc/reglages/` avant) ; les autres fichiers de `~/ai/memory`, `~/ai/0-persona` et des skills qui citent un ancien chemin sont seulement signalés.
6. Au démarrage d'une session ultérieure, quand aucune autre session de Claude Code (`agent` ou `claude`) ne tourne, qu'aucun `settings.json` ne cite plus d'ancien chemin et que le lien a plus de 24 h, le [hook mémoire](memory-hook.md#migration-depuis-un-ancien-nom) supprime le lien (il ne contient rien) ou, si l'ancien dossier n'avait pas pu être renommé, range ce dossier dans `~/ai/4-trash/`. Le hook fait aussi lui-même la migration si l'installateur n'a pas pu aller au bout.

Script : `hooks/abc-migrate.py` (`--check` : affiche ce qui reste à migrer, sans rien écrire). Les variables `BCAI_*` restent lues en repli pendant cette version ; les copies `*.bak-bcai` et `*.bak-bci` sont restaurées par la désinstallation comme les `*.bak-abc`.

## Pourquoi pas npm
L'installation par npm est dépréciée par Anthropic au profit de l'installateur natif, et npm n'est pas présent par défaut sous Windows.

## Pourquoi Alpine sous Android
Claude Code ne fournit pas de binaire pour Android. Il fournit en revanche un binaire `linux-arm64-musl`, qui fonctionne dans Alpine Linux lancé par `proot-distro`. Alpine est retenue pour sa légèreté (Ubuntu est trop lourde pour un téléphone). Sous Termux, la commande `agent` est un alias qui entre dans Alpine et y lance Claude Code.

## Désinstallation et dépannage
- [Désinstallation](uninstall.md)
- [Dépannage](troubleshooting.md)
