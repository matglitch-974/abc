# Scripts

Ce que fait chaque script, tel qu'il est écrit. Le dépôt est cloné dans `~/ai/2-tools/3-software/bcai/` ; les scripts de `skeleton/` sont copiés dans `~/ai` (jamais par-dessus un fichier existant).

## Installation et désinstallation (racine du dépôt)

### `install.ps1` (Windows 10 / 11)
1. Installe ce qui manque : Git (winget ; sans winget, arrêt avec un message), uv (winget, sinon script officiel d'Astral), Python 3.13 (winget, sinon `uv python install`), Claude Code (installateur officiel `claude.ai/install.ps1`).
2. Clone ou met à jour (`git pull --ff-only`) le dépôt ; `BCAI_BRANCH` choisit la branche. Une installation d'avant BCAI est d'abord renommée (`better-claude-instance` → `bcai`, jonction laissée à l'ancien emplacement), puis `bcai-migrate.py` reprend sauvegardes, réglages, commandes et chemins du skeleton ([installation.md](installation.md#mise-à-jour-dune-installation-bci)).
3. Sauvegarde `install-avant` (première installation seulement ; toujours faite alors, car le clone vient de créer `~/ai`).
4. Crée l'arborescence de `~/ai` et `~/project`, copie `skeleton/` sans rien écraser.
5. Importe l'existant (`bcai-import.py all`).
6. Fixe `CLAUDE_CONFIG_DIR` (variable utilisateur), copie `~/.claude` élément par élément dans `claude-code/` (fichiers verrouillés sautés ; `CLAUDE.md` et `skills` en `*.bak-bcai`), puis range l'original et `~/.claude.json` dans `4-trash` par renommage atomique ; encore tenus par une session, ils restent en place jusqu'au rangement par le hook mémoire. Si des sessions `claude` tournent, `~/.claude/.credentials.json` leur est laissé.
7. `CLAUDE.md` = une ligne `@~/ai/AGENTS.md` ; `skills`, `plugins`, `agents/system-agents` = jonctions vers `~/ai` ; `settings.json` reste un vrai fichier dans `claude-code/` (les liens de fichiers exigent des droits administrateur).
8. Complète `settings.json` (copie `.bak-bcai` à la première installation ; avant chaque réécriture qui le change, copie datée dans `backup-bcai/reglages/`) : 6 agents intégrés refusés, hook `guard-sensible` (lancé par le bash de Git) et hook mémoire sur 7 événements ; les anciennes entrées BCAI sont remplacées, les autres hooks gardés.
9. Outils, sans bloquer : restic (winget, sinon binaire officiel de GitHub dans `~/.local/bin`), Node.js (winget), SearXNG (clone avec `core.protectNTFS=false`, environnement uv), MCP `searxng`, `fetch`, `playwright`, `scrapling` (retrait de `duckduckgo` et `brave`), Scrapling, Crawl4AI.
10. Copie `bcai.cmd` dans `~/.local/bin` (ajouté au PATH utilisateur ; `bci.cmd`, l'ancien nom obsolète, n'est remplacé par l'alias que s'il existait déjà), propose le chiffrement de `4-keys-code`, sauvegarde `install-apres`.

### `install.sh` (Linux, Android)
- **Termux** : installe `proot-distro` et Alpine, relance `install.sh` dans Alpine, ajoute l'alias `claude` dans `~/.bashrc` et une commande `bcai` dans `$PREFIX/bin` qui s'exécute dans Alpine (un ancien `$PREFIX/bin/bci` devient un alias obsolète de `bcai`).
- **Linux** : installe les paquets (apk, apt-get, dnf, pacman ou zypper ; `sudo` si besoin) : curl, git, jq, python3, Node.js, npm (+ bash, ripgrep, libgcc, libstdc++ sous Alpine) ; restic sans bloquer ; Claude Code par l'installateur officiel s'il manque ; renomme une installation d'avant BCAI (lien symbolique laissé à l'ancien emplacement) ; clone ou met à jour le dépôt ; lance `bootstrap.sh`, qui commence par `bcai-migrate.py`.

### `bootstrap.sh` (Linux, appelé par `install.sh`)
Même déroulé que les étapes 3 à 10 de `install.ps1`, avec ces différences :
- `~/.claude` est **déplacé** élément par élément (pas copié) ; `settings.json` va dans `~/ai/memory/settings.json` ; `plugins` dans `~/ai/2-tools/2-plugins` s'il est vide ;
- les liens sont symboliques : `CLAUDE.md` → `~/ai/AGENTS.md`, `settings.json` → `~/ai/memory/settings.json` ;
- `~/.local/bin` est ajouté au PATH dans `~/.profile` seulement ; `CLAUDE_CONFIG_DIR` est ajouté à `~/.profile`, et à `~/.bashrc` et `~/.zshrc` s'ils existent ; sous musl (Alpine), `USE_BUILTIN_RIPGREP=0` ;
- la fusion de `settings.json` exige `jq` ; sans lui, le fichier existant n'est pas modifié (avertissement) ; fusion qui change le fichier : copie datée dans `backup-bcai/reglages/` d'abord ;
- `bcai` est un lien `~/.local/bin/bcai` → `bin/bcai` ; un ancien lien `~/.local/bin/bci` est repointé vers l'alias obsolète `bin/bci` ; uv est installé par le script officiel s'il manque.

### `uninstall.sh`, `uninstall.ps1`
Voir [uninstall.md](uninstall.md).

## Commande `bcai` (`bin/`)
`bin/bcai` (sh), `bin/bcai.ps1` appelé par `bin/bcai.cmd` (Windows). `bin/bci`, `bin/bci.cmd`, `bin/bci.ps1` : ancien nom, obsolète, gardé pour les installations antérieures au renommage (avertissement, puis `bcai` avec les mêmes arguments). Sous-commandes : `install` / `update`, `uninstall`, `status`, `backup [list]`, `search`, `keys open|close|status`, `import [skills|agents|secrets|llm]`, `version`. Voir [installation.md](installation.md#commande-bcai).

## Hooks et outils (`hooks/`)

| Script | Rôle |
|---|---|
| `memory-hook.py` | journal, TODO, sauvegarde quotidienne, persona, agents isolés, rangement de `~/.claude` : [memory-hook.md](memory-hook.md) |
| `guard-sensible.sh` | hook `PreToolUse` (Bash) : bloque une commande qui mentionne `sensible` ou `4-keys-code` avec un moyen de sortie, et tout `git push` depuis un dépôt qui suit un fichier de `sensible/` : [projects.md](projects.md#protections) |
| `bcai-backup.py` | sauvegardes `quotidienne`, `install-avant`, `install-apres`, `list` : [memory.md](memory.md#sauvegardes-hooksbcai-backuppy) |
| `bcai-import.py` | import par copie : `skills`, `agents`, `secrets`, `llm`, `all` (voir ci-dessous) |
| `bcai-keys.py` | coffre chiffré de `4-keys-code` : [keys.md](keys.md) |
| `bcai-migrate.py` | migration d'une installation d'avant BCAI (`--check` : sans rien écrire) : [installation.md](installation.md#mise-à-jour-dune-installation-bci) |

### `bcai-import.py`
- `skills` : chaque dossier de `~/.claude/skills` contenant `SKILL.md` est copié dans `~/ai/2-tools/1-skills/` ; nom déjà pris par un skill différent : `<nom>1`, `<nom>2`…, champ `name` corrigé, ligne ajoutée à `memory/TODO.md`. Une empreinte (`.bcai-import` ; `.bci-import` avant BCAI, encore reconnue) évite tout réimport.
- `agents` : chaque `.md` de `~/.claude/agents` est copié dans `~/ai/0-persona/` (sélection par `@nom`), même règle de conflit ; les liens BCAI sont ignorés.
- `secrets` : voir [keys.md](keys.md). Verse aussi l'ancien `2-tools/0-mcp/sensible` dans `4-keys-code/mcp` (l'original part dans `4-trash` ; vide, il est supprimé), donc aussi avec `bcai import secrets`.
- `llm` : configs de Ollama, Grok, Codex, Gemini, Qwen, LM Studio, opencode, Continue, aider, Kimi, DeepSeek, Crush, Goose copiées dans `~/ai/3-llm/<outil>/` (fichiers de plus de 100 Mo laissés en place, secrets envoyés dans `4-keys-code/llm/`) ; modèles Ollama **déplacés** une fois vers `$BCAI_MODELS_DIR/ollama` (défaut `~/ai/3-llm/models/ollama`), `OLLAMA_MODELS` y pointe ; inventaire dans `~/ai/3-llm/llms.md`.
- `all` : les quatre, dans cet ordre.

## Scripts de l'instance (`skeleton/ai/2-tools/1-skills/`)

| Script | Rôle |
|---|---|
| `bench/sector` | `new` : crée le prochain secteur libre de `~/ai/1-bench` (`A-sector`…) ; `release <nom>` : le supprime |
| `bench/agent-id.py` | `new [nom]` réserve un code à 4 chiffres (`slave-4821`) dans `1-bench/<code>.id` ; `release`, `list` |
| `context/ctx-audit.py` | estime (ou mesure avec `--exact`) les tokens chargés à chaque session : `AGENTS.md` et ses imports, `realign.md`, descriptions de skills |
| `memory/` | skill sans script : règles d'écriture de la mémoire |
| `mission/tool-scan.py` | `local` : inventaire des skills, MCP, plugins et agents ; `online` : registre MCP officiel et GitHub |
| `mission/tool-install.py` | `mcp`, `skill`, `remove`, `log` ; journal dans `~/ai/2-tools/installed.md` ; un skill retiré part dans `4-trash` |
| `project/new-unit` | crée une unité de projet (Git, `AGENTS.md`, `CLAUDE.md`, `README.md`, `TODO.md`, `.gitignore` avec `sensible/`, hook `pre-push`) ; `--hook <dossier>` pose seulement le hook |
| `project/pre-push` | hook Git : refuse un push dont l'arbre ou l'historique envoyé contient un fichier de `sensible/` |
| `search/search.py` | recherche via SearXNG local (démarré à la demande sur `127.0.0.1:8888`) ; `start`, `stop`, `status` |
| `sampling/generate.py` | génère un passage avec modèle et effort fixés, par `claude -p` (ou `--api`) |
| `specula/specula.py` | synthèses publiques de La Note Sentinelle (API WordPress de specula.fr) |
