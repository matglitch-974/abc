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
irm matglitch-974.github.io/BCI.ps1 | iex
```
Commande de secours (adresse complète, si `matglitch-974.github.io` est inaccessible) :
```
irm https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/install.ps1 | iex
```

Linux / Android (Termux) :
```
curl -sL matglitch-974.github.io/BCI | sh
```
Commande de secours (adresse complète, si `matglitch-974.github.io` est inaccessible) :
```
curl -fsSL https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/install.sh | sh
```

Les commandes courtes passent par `matglitch-974.github.io` (GitHub Pages, dépôt `matglitch-974/matglitch-974.github.io`) : de simples relais vers `install.sh` et `install.ps1` de ce dépôt, qui reste la seule source de l'installateur.

Deux étapes ne peuvent pas être automatisées :
1. Android : installer d'abord **Termux depuis F-Droid** (la version du Play Store est obsolète).
2. Au premier lancement de `claude`, **se connecter à son compte Anthropic**.

Variables reconnues : `BCI_BRANCH` (branche du dépôt, `main` par défaut), `BCI_ENCRYPT_KEYS=oui|non` (répond d'avance à la question du chiffrement), `BCI_MODELS_DIR` (emplacement des modèles Ollama, `~/ai/3-llm/models` par défaut).

## Ce que fait l'installateur
1. Installe les dépendances. Linux : curl, git, jq, python3, Node.js, npm (Alpine : + bash, ripgrep, libgcc, libstdc++), restic si disponible. Windows : Git, uv, Python, Node.js, restic par winget ; sans winget : uv et restic par leurs sources officielles, Python par uv, Git exigé (arrêt sinon), Node.js signalé manquant.
2. Installe Claude Code avec l'installateur officiel d'Anthropic (`claude.ai/install.sh` ou `install.ps1`), s'il est absent.
3. Clone ce dépôt dans `~/ai/2-tools/3-software/better-claude-instance/` (ou le met à jour).
4. Sauvegarde complète avant la première installation (`install-avant`, si `~/ai` ou `~/.claude` existe) ; une seconde (`install-apres`) à la fin. Les deux sont conservées à vie ([memory.md](memory.md#sauvegardes-hooksbci-backuppy)).
5. Crée `~/ai` et `~/project`, copie les fichiers de `skeleton/` sans jamais écraser un fichier existant.
6. Importe l'existant, par copie (les originaux restent) : skills et agents de `~/.claude`, secrets dans `2-tools/4-keys-code` ([keys.md](keys.md)), configs des autres LLM dans `3-llm/` ; les modèles Ollama sont déplacés une fois ([scripts.md](scripts.md#bci-importpy)).
7. Fixe `CLAUDE_CONFIG_DIR` à `~/ai/2-tools/3-software/claude-code/`, y range le contenu de `~/.claude` et `~/.claude.json`, puis met les originaux dans `~/ai/4-trash/`. Votre ancien `CLAUDE.md` et votre ancien dossier `skills` y sont gardés en `*.bak-bci`. Si des sessions `claude` tournent, `~/.claude/.credentials.json` leur est laissé ; le [hook mémoire](memory-hook.md#rangement-de-claude) le range plus tard.
8. Relie `CLAUDE.md` à `~/ai/AGENTS.md`, `skills`, `plugins` et `agents/system-agents` à leurs dossiers de `~/ai` ; `settings.json` est rangé dans `~/ai/memory/` (Linux) ou reste dans `claude-code/` (Windows).
9. Complète `settings.json` : agents intégrés désactivés, hooks `guard-sensible` et mémoire. Vos autres réglages et hooks sont conservés.
10. Installe les outils web : SearXNG (métamoteur local, sans clé) et son MCP, `fetch`, `playwright`, `scrapling`, Crawl4AI. Retire les MCP `duckduckgo` et `brave` de portée utilisateur s'ils existent (remplacés par SearXNG). Un échec ici ne bloque pas l'installation.
11. Installe la commande `bci`.
12. Propose de chiffrer `4-keys-code` avec une phrase secrète (restic). Chiffré, il n'existe en clair qu'entre `bci keys open` et `bci keys close`, et n'entre jamais en clair dans les sauvegardes.

Tout fichier remplacé est gardé en `*.bak-bci`. Relancer la commande (ou `bci install`) met l'instance à jour sans toucher à vos fichiers. Détail script par script : [scripts.md](scripts.md).

## Commande `bci`
Installée avec BCI (`~/.local/bin/bci` ; Windows : `bci.cmd` ; Termux : `$PREFIX/bin/bci`, qui l'exécute dans Alpine). La toute première installation passe forcément par la commande ci-dessus : avant elle, `bci` n'existe pas.

| Commande | Effet |
|---|---|
| `bci install` (ou `bci update`) | met à jour depuis GitHub puis réinstalle ; aucun fichier personnel écrasé |
| `bci uninstall` | désinstalle, après deux confirmations (oui, puis le mot `desinstaller`) et un avertissement en rouge ; de même avant de supprimer `~/ai` ou `~/project` |
| `bci status` | versions, `CLAUDE_CONFIG_DIR`, SearXNG, nombre de sauvegardes, restic |
| `bci backup` / `bci backup list` | sauvegarde immédiate / liste |
| `bci search "requête"` | recherche web (skill `search`) |
| `bci keys open\|close\|status` | coffre chiffré de `2-tools/4-keys-code` (restic, phrase secrète) |
| `bci import [skills\|agents\|secrets\|llm]` | réimporte l'existant (copies, sans doublon) |
| `bci version` | commit installé |

## Pourquoi pas npm
L'installation par npm est dépréciée par Anthropic au profit de l'installateur natif, et npm n'est pas présent par défaut sous Windows.

## Pourquoi Alpine sous Android
Claude Code ne fournit pas de binaire pour Android. Il fournit en revanche un binaire `linux-arm64-musl`, qui fonctionne dans Alpine Linux lancé par `proot-distro`. Alpine est retenue pour sa légèreté (Ubuntu est trop lourde pour un téléphone). Sous Termux, la commande `claude` est un alias qui entre dans Alpine et lance Claude Code.

## Désinstallation et dépannage
- [Désinstallation](uninstall.md)
- [Dépannage](troubleshooting.md)
