# Désinstallation

## Lancer
```
abc uninstall
```
Ou, sans la commande `abc` :
- Windows (PowerShell) :
  ```
  irm https://raw.githubusercontent.com/matglitch-974/abc/main/uninstall.ps1 | iex
  ```
- Linux / Android (dans Alpine) :
  ```
  curl -fsSL https://raw.githubusercontent.com/matglitch-974/abc/main/uninstall.sh | sh
  ```

La désinstallation est interactive : un avertissement en rouge, une question `[o/N]`, puis le mot `desinstaller` à taper en entier. Sans ces deux confirmations, rien n'est modifié. Elle se lance donc dans un terminal, par l'utilisateur, pas par un agent.

## Ce qu'elle fait
1. **Configuration remise dans `~/.claude`** — seulement si `~/.claude` n'existe pas déjà :
   - Linux : `claude-code/` est renommé en `~/.claude` ; `CLAUDE.md`, `skills`, `agents/0-persona` (et l'ancien `agents/system-agents`) sont retirés s'ils sont des liens symboliques (un `CLAUDE.md` devenu fichier ordinaire est gardé) ; `plugins` et `settings.json` (liens) sont remplacés par des copies réelles ;
   - Windows : les jonctions `skills`, `agents/0-persona` (et l'ancienne `agents/system-agents`) sont retirées, `plugins` remplacé par une copie ; `CLAUDE.md` est retiré dès qu'il contient l'import `@~/ai/AGENTS.md`, même s'il contient aussi d'autres lignes ; puis `claude-code/` est déplacé en `~/.claude` ;
   - `.claude.json` revient dans `~/` (s'il n'y est pas déjà) ; les `*.bak-abc` (et les `*.bak-bcai`, `*.bak-bci` faits sous les anciens noms) sont restaurés à leur nom d'origine.
2. **Variable `CLAUDE_CONFIG_DIR` retirée** (lignes de `~/.profile`, `~/.bashrc`, `~/.zshrc` ; variable utilisateur sous Windows) et commandes `abc`, `bcai` et `bci` (anciens noms) retirées de `~/.local/bin`. La commande `agent` redevient `claude` (si c'est bien Claude Code et que `claude` est libre).
3. **Réglages nettoyés** dans `~/.claude/settings.json` : entrées `Agent(…)` de `permissions.deny` et hooks `guard-sensible` / `memory-hook` retirés (sous Linux, il faut `jq`).
4. **Modèles Ollama** : si `OLLAMA_MODELS` pointe dans `~/ai`, ils reviennent dans `~/.ollama/models` et la variable est retirée.
5. **Suppressions, à la demande seulement** : deux nouvelles confirmations (`supprimer ai`, puis `supprimer project`) avant d'effacer `~/ai` ou `~/project`.

> [!WARNING]
> Supprimer `~/ai` efface définitivement la mémoire, les personas, les skills, le coffre `4-keys-code`, la corbeille **et toutes les sauvegardes** (`backup-abc`). Supprimer `~/project` efface vos projets, `sensible/` compris, et tout ce qui n'a jamais été poussé.

## Ce qu'elle ne fait pas
- Claude Code reste installé, ainsi que Git, Python, uv, Node.js, restic, SearXNG, Scrapling, Crawl4AI.
- Les serveurs MCP ajoutés (`fetch`, `searxng`, `playwright`, `scrapling`) restent déclarés.
- Les serveurs MCP `duckduckgo` et `brave` retirés à l'installation ne sont pas restaurés.
- Toutes les entrées `Agent(…)` de `permissions.deny` sont retirées, y compris celles que vous auriez ajoutées vous-même.
- Les copies faites par l'import (skills, secrets, configs d'autres LLM) restent dans `~/ai` tant que vous ne le supprimez pas ; les originaux n'ont jamais été touchés.
- Sous Termux, l'alias `agent` de `~/.bashrc`, `$PREFIX/bin/abc` et les éventuels `$PREFIX/bin/bcai` et `bci` restent côté Termux.

## Si `~/.claude` existe déjà
L'étape 1 est alors sautée (le script ne remplace jamais un `~/.claude` existant) : c'est le cas si une session ouverte a laissé `~/.claude/.credentials.json`. Fermez toutes les sessions Claude Code, déplacez ce `~/.claude` dans `~/ai/4-trash/`, puis relancez la désinstallation.
