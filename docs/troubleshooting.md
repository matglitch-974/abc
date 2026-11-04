# Dépannage

Commencez toujours par `bci status` dans un **nouveau** terminal.

## Installation

| Symptôme | Cause | Solution |
|---|---|---|
| `Git est requis et winget est absent` (Windows) | Windows allégé sans winget | installer Git pour Windows (git-scm.com), puis relancer |
| `Python introuvable après installation` (Windows) | Python installé hors des emplacements connus | installer Python 3 (python.org), puis relancer |
| `bash de Git introuvable : hook guard-sensible inactif` | `bash.exe` non trouvé au-dessus de `git.exe` | réinstaller Git pour Windows, puis `bci install` |
| `ATTENTION : jq absent, … non modifié` (Linux) | `settings.json` existant non fusionné | installer `jq`, puis `bci install` |
| `ATTENTION : SearXNG non installé`, `MCP … non installé`, `Scrapling non installé`, `Crawl4AI non installé` | échec d'un outil web (réseau, navigateur absent sous Termux / musl) | non bloquant ; relancer `bci install` plus tard |
| `restic non installé (sauvegardes en tar.xz)` | restic absent ou < 0.17 | sauvegardes en archives `tar.xz` ; pas de coffre chiffré tant que restic manque |
| `Gestionnaire de paquets inconnu` (Linux) | ni apk, apt-get, dnf, pacman ni zypper | installer curl, git, jq, python3 et nodejs, puis relancer |

## Claude Code

| Symptôme | Cause | Solution |
|---|---|---|
| Claude Code semble avoir tout oublié, `~/.claude` réapparaît | `CLAUDE_CONFIG_DIR` absent du terminal (ouvert avant l'installation, ou qui ne lit pas `~/.profile`) | ouvrir un nouveau terminal (ou `. ~/.profile`) ; vérifier avec `bci status` |
| `bci status` : `ATTENTION ~/.claude existe` | cache laissé par une session ouverte hors BCI | rien à faire : rangé dans `4-trash` au prochain lancement de `claude` quand aucune autre session ne tourne ([memory-hook.md](memory-hook.md#rangement-de-claude)) |
| `~/.claude` ne contient que `.credentials.json` | identifiants laissés aux sessions ouvertes pendant l'installation | normal ; rangé quand elles sont fermées |
| Erreur 401 avec `CLAUDE_CODE_OAUTH_TOKEN` défini | jeton mal copié | voir ci-dessous |
| `Bloqué par guard-sensible : …` | la commande vise `sensible/` ou `4-keys-code` avec un moyen de sortie | voulu ; ne rien sortir de ces dossiers ([projects.md](projects.md#protections)) |
| `Bloqué par l'isolement des agents : …` | accès croisé entre une session isolée et le reste | voulu ([memory-hook.md](memory-hook.md#agents-isolés)) |

### Jeton `CLAUDE_CODE_OAUTH_TOKEN` et erreur 401
Un jeton `CLAUDE_CODE_OAUTH_TOKEN` valide fait **108 caractères**. Un jeton de **113 caractères se terminant par « Store »** est une capture corrompue (5 caractères parasites collés à la fin) : Claude Code répond alors 401.

Vérifier la longueur sans afficher le jeton :
- Linux / Android : `printf %s "$CLAUDE_CODE_OAUTH_TOKEN" | wc -c`
- Windows (PowerShell) : `[Environment]::GetEnvironmentVariable('CLAUDE_CODE_OAUTH_TOKEN','User').Length`

Corriger : redéfinir la variable avec le jeton exact (108 caractères), ouvrir un nouveau terminal, puis `bci import secrets` pour rafraîchir la copie de `4-keys-code/env/secrets.env`. Ne collez jamais la valeur du jeton dans une conversation ni dans un fichier hors de `4-keys-code`.

## Sauvegardes et coffre

| Symptôme | Cause | Solution |
|---|---|---|
| `sauvegarde échouée : …` | erreur de restic ou d'archive | lire `~/ai/2-tools/logs/backup-bci/errors.log` |
| `Vérification échouée (… fichiers chiffrés pour … en clair) : rien n'a été effacé.` | fichiers illisibles dans `4-keys-code` | fermer le programme qui les tient, relancer `bci keys close` |
| `4-keys-code est chiffré et fermé : secrets non réimportés` | coffre fermé | `bci keys open`, `bci import secrets`, `bci keys close` |
| Phrase secrète oubliée | — | le coffre est irrécupérable ; les originaux (`~/.ssh`, etc.) n'ont pas été touchés par l'import |

## Android (Termux)

| Symptôme | Cause | Solution |
|---|---|---|
| `claude native binary not installed` (npm, Termux) | pas de binaire Android | utiliser `install.sh`, qui passe par Alpine |
| `unexpected e_type: 2` | installateur lancé dans Termux et non dans Alpine | supprimer `~/.claude/downloads` côté Termux, relancer `install.sh` |
| `apk: command not found` | commande tapée dans Termux au lieu d'Alpine | utiliser l'alias `claude`, ou `proot-distro login alpine` |
| `~/.local/bin is not in your PATH` | session ouverte avant l'installation | ouvrir un nouveau terminal (ou `. ~/.profile`) |
| recherche de fichiers en échec sous Alpine | ripgrep intégré compilé pour glibc | `USE_BUILTIN_RIPGREP=0`, ajouté automatiquement |

## Désinstallation

| Symptôme | Cause | Solution |
|---|---|---|
| La configuration n'est pas remise dans `~/.claude` | `~/.claude` existe déjà | voir [uninstall.md](uninstall.md#si-claude-existe-déjà) |
