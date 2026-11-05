# Installation

## Plateformes
- **Windows 10 / 11** : `install.ps1` (PowerShell). Windows 7 n'est pas pris en charge par Claude Code.
- **Linux** : `install.sh`. Debian, Ubuntu, Alpine, Fedora, Arch, openSUSE et dérivés (détection du gestionnaire de paquets).
- **Android** : `install.sh` dans l'application Termux. Le script détecte Termux, installe Alpine Linux et se relance à l'intérieur.
- **Apple (macOS, iOS)** : non conçu pour cet environnement, non testé.

## Deux façons d'installer

### Par votre agent Claude Code (recommandé si vous l'utilisez déjà)
Votre instance a déjà ses skills, agents, réglages, MCP, peut-être une mémoire : l'agent en fait l'inventaire, vous présente un plan, adapte l'import et n'agit qu'après votre accord. Le prompt à copier-coller est dans le [README](../README.md#méthode-recommandée--laissez-votre-agent-installer) ; le guide que suit l'agent est [SETUP.md](../SETUP.md).

### Par le script (configuration de référence)
Windows (PowerShell) :
```
irm matglitch-974.github.io/bc.ps1 | iex
```
Commande de secours (adresse complète, si `matglitch-974.github.io` est inaccessible) :
```
irm https://raw.githubusercontent.com/matglitch-974/Better-Context-of-Agents-Instance/main/install.ps1 | iex
```

Linux / Android (Termux) :
```
curl -fsSL matglitch-974.github.io/bc | sh
```
Commande de secours (adresse complète, si `matglitch-974.github.io` est inaccessible) :
```
curl -fsSL https://raw.githubusercontent.com/matglitch-974/Better-Context-of-Agents-Instance/main/install.sh | sh
```

Les commandes courtes passent par `matglitch-974.github.io` (GitHub Pages, dépôt `matglitch-974/matglitch-974.github.io`) : de simples relais vers `install.sh` et `install.ps1` de ce dépôt, qui reste la seule source de l'installateur. Les anciennes adresses (`…/BCI`, `…/BCI.ps1`) et `…/BCAI`, `…/BCAI.ps1` sont des relais identiques à `…/bc` et `…/bc.ps1`.

Deux étapes ne peuvent pas être automatisées :
1. Android : installer d'abord **Termux depuis F-Droid** (la version du Play Store est obsolète).
2. Au premier lancement de `claude`, **se connecter à son compte Anthropic**.

Variables reconnues : `BCAI_BRANCH` (branche du dépôt, `main` par défaut), `BCAI_ENCRYPT_KEYS=oui|non` (répond d'avance à la question du chiffrement), `BCAI_MODELS_DIR` (dossier des modèles, `~/ai/3-llm/models` par défaut ; les modèles Ollama vont dans son sous-dossier `ollama/`). Les anciens noms `BCI_*` sont encore lus si `BCAI_*` n'est pas défini.

## Ce que fait l'installateur
1. Installe les dépendances. Linux : curl, git, jq, python3, Node.js, npm (Alpine : + bash, ripgrep, libgcc, libstdc++), restic si disponible. Windows : Git, uv et Python par winget ; sans winget : uv par son script officiel, Python par uv, Git exigé (arrêt sinon). Sous Windows, Node.js et restic ne sont installés qu'à l'étape 10, avec les outils, après la migration (winget ; sans winget : restic depuis GitHub, Node.js signalé manquant).
2. Installe Claude Code avec l'installateur officiel d'Anthropic (`claude.ai/install.sh` ou `install.ps1`), s'il est absent.
3. Clone ce dépôt dans `~/ai/2-tools/3-software/bcai/` (ou le met à jour ; une installation d'avant le renommage est d'abord migrée, voir [plus bas](#mise-à-jour-dune-installation-bci)).
4. Sauvegarde complète avant la première installation (`install-avant`, toujours faite : `~/ai` existe déjà puisque le dépôt vient d'y être cloné) ; une seconde (`install-apres`) à la fin. Les deux sont conservées à vie ([memory.md](memory.md#sauvegardes-hooksbcai-backuppy)).
5. Crée `~/ai` et `~/project`, copie les fichiers de `skeleton/` sans jamais écraser un fichier existant.
6. Importe l'existant, par copie (les originaux restent) : skills et agents de `~/.claude`, secrets dans `2-tools/4-keys-code` ([keys.md](keys.md)), configs des autres LLM dans `3-llm/` ; les modèles Ollama sont déplacés une fois ([scripts.md](scripts.md#bcai-importpy)).
7. Fixe `CLAUDE_CONFIG_DIR` à `~/ai/2-tools/3-software/claude-code/`, y range le contenu de `~/.claude` et `~/.claude.json`, puis met les originaux dans `~/ai/4-trash/`. Votre ancien `CLAUDE.md` et votre ancien dossier `skills` y sont gardés en `*.bak-bcai`. Si des sessions `claude` tournent, `~/.claude/.credentials.json` leur est laissé ; le [hook mémoire](memory-hook.md#rangement-de-claude) le range plus tard.
8. Relie `CLAUDE.md` à `~/ai/AGENTS.md`, `skills`, `plugins` et `agents/0-persona` à leurs dossiers de `~/ai` (toutes les personas deviennent des sous-agents ; l'ancien lien `agents/system-agents` est retiré) ; `settings.json` est rangé dans `~/ai/memory/` (Linux) ou reste dans `claude-code/` (Windows).
9. Complète `settings.json` : agents intégrés désactivés, hooks `guard-sensible` et mémoire. Vos autres réglages et hooks sont conservés.
10. Installe les outils (sous Windows, d'abord restic et Node.js) et les outils web : SearXNG (métamoteur local, sans clé) et son MCP, `fetch`, `playwright`, `scrapling`, Crawl4AI. Retire les MCP `duckduckgo` et `brave` de portée utilisateur s'ils existent (remplacés par SearXNG). Un échec ici ne bloque pas l'installation.
11. Installe la commande `bcai`.
12. Propose de chiffrer `4-keys-code` avec une phrase secrète (restic). Chiffré, il n'existe en clair qu'entre `bcai keys open` et `bcai keys close`, et n'entre jamais en clair dans les sauvegardes.

Tout fichier remplacé est gardé en `*.bak-bcai`. Relancer la commande (ou `bcai install`) met l'instance à jour sans toucher à vos fichiers. Détail script par script : [scripts.md](scripts.md).

## Commande `bcai`
Installée avec BCAI (`~/.local/bin/bcai` ; Windows : `bcai.cmd` ; Termux : `$PREFIX/bin/bcai`, qui l'exécute dans Alpine). La toute première installation passe forcément par la commande ci-dessus : avant elle, `bcai` n'existe pas.

`bci`, l'ancien nom, est **obsolète** : il n'est gardé que sur les installations antérieures au renommage, où il affiche un avertissement puis appelle `bcai` avec les mêmes arguments (`bin/bci`, `bin/bci.cmd`, `bin/bci.ps1`). Il disparaîtra dans une version ultérieure.

| Commande | Effet |
|---|---|
| `bcai install` (ou `bcai update`) | met à jour depuis GitHub puis réinstalle ; aucun fichier personnel écrasé |
| `bcai uninstall` | désinstalle, après deux confirmations (oui, puis le mot `desinstaller`) et un avertissement en rouge ; de même avant de supprimer `~/ai` ou `~/project` |
| `bcai status` | versions, `CLAUDE_CONFIG_DIR`, SearXNG, nombre de sauvegardes, restic |
| `bcai backup` / `bcai backup list` | sauvegarde immédiate / liste |
| `bcai search "requête"` | recherche web (skill `search`) |
| `bcai keys open\|close\|status` | coffre chiffré de `2-tools/4-keys-code` (restic, phrase secrète) |
| `bcai import [skills\|agents\|secrets\|llm]` | réimporte l'existant (copies, sans doublon) |
| `bcai version` | version (fichier `VERSION`, semver) et commit installés |

## Mise à jour d'une installation BCI
Avant BCAI, le projet s'appelait Better Claude Instance (BCI). Une installation de cette époque se met à jour avec `bci install` ou la commande d'installation ci-dessus ; rien n'est effacé :

1. `~/ai/2-tools/3-software/better-claude-instance/` est renommé en `bcai/` et son dépôt Git pointe vers la nouvelle adresse. Un lien (jonction sous Windows) reste à l'ancien emplacement : les sessions Claude déjà ouvertes appellent encore leurs hooks par l'ancien chemin.
2. `~/ai/2-tools/logs/backup-bci/` devient `backup-bcai/` (fusionné élément par élément si `backup-bcai/` existe déjà) ; les sauvegardes d'installation existantes restent celles de la première installation.
3. Les chemins de `settings.json` (hooks) sont corrigés, après une copie datée dans `backup-bcai/reglages/`. Toute réécriture ultérieure de `settings.json` par l'installateur passe aussi par cette copie.
4. La commande `bcai` est installée ; `bci` devient l'alias obsolète décrit plus haut.
5. `~/ai/AGENTS.md` et le skill `memory`, copiés du skeleton, reçoivent les nouveaux chemins (copie datée dans `backup-bcai/reglages/` avant) ; les autres fichiers de `~/ai/memory`, `~/ai/0-persona` et des skills qui citent l'ancien chemin sont seulement signalés.
6. Au démarrage d'une session ultérieure, quand aucune autre session `claude` ne tourne, qu'aucun `settings.json` ne cite plus l'ancien chemin et que le lien a plus de 24 h, le [hook mémoire](memory-hook.md#migration-depuis-bci) supprime le lien (il ne contient rien) ou, si l'ancien dossier n'avait pas pu être renommé, range ce dossier dans `~/ai/4-trash/`. Le hook fait aussi lui-même la migration si l'installateur n'a pas pu aller au bout.

Script : `hooks/bcai-migrate.py` (`--check` : affiche ce qui reste à migrer, sans rien écrire). Les variables `BCI_*` restent lues en repli, les copies `*.bak-bci` sont restaurées par la désinstallation comme les `*.bak-bcai`.

## Pourquoi pas npm
L'installation par npm est dépréciée par Anthropic au profit de l'installateur natif, et npm n'est pas présent par défaut sous Windows.

## Pourquoi Alpine sous Android
Claude Code ne fournit pas de binaire pour Android. Il fournit en revanche un binaire `linux-arm64-musl`, qui fonctionne dans Alpine Linux lancé par `proot-distro`. Alpine est retenue pour sa légèreté (Ubuntu est trop lourde pour un téléphone). Sous Termux, la commande `claude` est un alias qui entre dans Alpine et lance Claude Code.

## Désinstallation et dépannage
- [Désinstallation](uninstall.md)
- [Dépannage](troubleshooting.md)
