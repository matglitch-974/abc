# Dépannage

Commencez toujours par `abc status` dans un **nouveau** terminal.

## Installation

| Symptôme | Cause | Solution |
|---|---|---|
| `Git est requis et winget est absent` (Windows) | Windows allégé sans winget | installer Git pour Windows (git-scm.com), puis relancer |
| `Python introuvable après installation` (Windows) | Python installé hors des emplacements connus | installer Python 3 (python.org), puis relancer |
| `bash de Git introuvable : hook guard-sensible inactif` | `bash.exe` non trouvé au-dessus de `git.exe` | réinstaller Git pour Windows, puis `abc install` |
| `ATTENTION : jq absent, … non modifié` (Linux) | `settings.json` existant non fusionné | installer `jq`, puis `abc install` |
| `SearXNG non installé`, `MCP … non installé`, `Node.js absent…`, `Scrapling non installé`, `Crawl4AI non installé`, précédés de `ATTENTION :` (Linux) ou `AVERTISSEMENT :` (Windows) | échec d'un outil web (réseau, navigateur absent sous Termux / musl) | non bloquant ; relancer `abc install` plus tard |
| `restic non installé (sauvegardes en tar.xz…)` | l'installation de restic a échoué (paquet introuvable, réseau, téléchargement) | sauvegardes en archives `tar.xz` ; pas de coffre chiffré tant que restic manque |
| aucun message, mais sauvegardes en `tar.xz` | restic présent mais antérieur à 0.17 : `abc-backup.py` se replie sur `tar.xz` sans le signaler | mettre restic à jour (version : `restic version`, ou `abc status` sous Linux) |
| `Gestionnaire de paquets inconnu` (Linux) | ni apk, apt-get, dnf, pacman ni zypper | installer curl, git, jq, python3 et nodejs, puis relancer |

## Claude Code

| Symptôme | Cause | Solution |
|---|---|---|
| Claude Code semble avoir tout oublié, `~/.claude` réapparaît | `CLAUDE_CONFIG_DIR` absent du terminal (ouvert avant l'installation, ou qui ne lit pas `~/.profile`) | ouvrir un nouveau terminal (ou `. ~/.profile`) ; vérifier avec `abc status` |
| `abc status` : `ATTENTION ~/.claude existe` | cache laissé par une session ouverte hors ABC | rien à faire : rangé dans `4-trash` au prochain lancement de `agent` quand aucune autre session ne tourne ([memory-hook.md](memory-hook.md#rangement-de-claude)) |
| `~/.claude` ne contient que `.credentials.json` | identifiants laissés aux sessions ouvertes pendant l'installation | normal ; rangé quand elles sont fermées |
| Erreur 401 avec `CLAUDE_CODE_OAUTH_TOKEN` défini | jeton mal copié (Claude Code, hors ABC) | voir ci-dessous |
| `Bloqué par guard-sensible : …` | la commande vise `sensible/` ou `4-keys-code` avec un moyen de sortie | voulu ; ne rien sortir de ces dossiers ([projects.md](projects.md#protections)) |
| `Bloqué par l'isolement des agents : …` | accès croisé entre une session isolée et le reste | voulu ([memory-hook.md](memory-hook.md#agents-isolés)) |

### Jeton `CLAUDE_CODE_OAUTH_TOKEN` et erreur 401
Ce point relève de Claude Code, pas du code d'ABC : ABC ne crée ni ne contrôle ce jeton, il copie seulement la variable dans `4-keys-code/env/secrets.env` lors de l'import des secrets.

Constaté le 04/11/2026 : un jeton `claude setup-token` valide fait **108 caractères**. Une capture automatisée du terminal peut y coller le mot suivant (« Store »), ce qui donne **113 caractères** : Claude Code répond alors 401.

Vérifier la longueur sans afficher le jeton (dans le terminal où la variable est définie) :
- Linux / Android : `printf %s "$CLAUDE_CODE_OAUTH_TOKEN" | wc -c`
- Windows (PowerShell) : `$env:CLAUDE_CODE_OAUTH_TOKEN.Length`

Corriger : redéfinir la variable avec le jeton exact, ouvrir un nouveau terminal, puis `abc import secrets` pour rafraîchir la copie de `4-keys-code/env/secrets.env`. Ne collez jamais la valeur du jeton dans une conversation ni dans un fichier hors de `4-keys-code`.

## Sauvegardes et coffre

| Symptôme | Cause | Solution |
|---|---|---|
| `sauvegarde échouée : …` | erreur de restic ou d'archive | lire `~/ai/2-tools/logs/backup-abc/errors.log` |
| `Vérification échouée (… fichiers chiffrés pour … en clair) : rien n'a été effacé.` | fichiers illisibles dans `4-keys-code` | fermer le programme qui les tient, relancer `abc keys close` |
| `4-keys-code est chiffré et fermé : secrets non réimportés` | coffre fermé | `abc keys open`, `abc import secrets`, `abc keys close` |
| Phrase secrète oubliée | — | le coffre est irrécupérable ; les originaux (`~/.ssh`, etc.) n'ont pas été touchés par l'import |

## Android (Termux)

| Symptôme | Cause | Solution |
|---|---|---|
| `claude native binary not installed` (npm, Termux) | pas de binaire Android | utiliser `ABC-install-<version>.sh`, qui passe par Alpine |
| `unexpected e_type: 2` | installateur lancé dans Termux et non dans Alpine | supprimer `~/.claude/downloads` côté Termux, relancer l'installateur |
| `apk: command not found` | commande tapée dans Termux au lieu d'Alpine | utiliser l'alias `agent`, ou `proot-distro login alpine` |
| `~/.local/bin is not in your PATH` | session ouverte avant l'installation | ouvrir un nouveau terminal (ou `. ~/.profile`) |
| recherche de fichiers en échec sous Alpine | ripgrep intégré compilé pour glibc | `USE_BUILTIN_RIPGREP=0`, ajouté automatiquement |

## Désinstallation

| Symptôme | Cause | Solution |
|---|---|---|
| La configuration n'est pas remise dans `~/.claude` | `~/.claude` existe déjà | voir [uninstall.md](uninstall.md#si-claude-existe-déjà) |
