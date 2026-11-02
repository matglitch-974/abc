# Installation

## Plateformes
- **Windows 10 / 11** : `install.ps1` (PowerShell). Windows 7 n'est pas pris en charge par Claude Code.
- **Linux** : `install.sh`. Debian, Ubuntu, Alpine, Fedora, Arch, openSUSE et dérivés (détection du gestionnaire de paquets).
- **Android** : `install.sh` dans l'application Termux. Le script détecte Termux, installe Alpine Linux et se relance à l'intérieur.
- **Apple (macOS, iOS)** : non conçu pour cet environnement, non testé.

## Commandes

Windows (PowerShell) :
```
irm https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/install.ps1 | iex
```

Linux / Android (Termux) :
```
curl -fsSL https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/install.sh | sh
```

Deux étapes ne peuvent pas être automatisées :
1. Android : installer d'abord **Termux depuis F-Droid** (la version du Play Store est obsolète).
2. Au premier lancement de `claude`, **se connecter à son compte Anthropic**.

## Ce que fait l'installateur
1. Installe les dépendances (Linux : curl, git, jq ; Alpine : + bash, ripgrep, libgcc, libstdc++ ; Windows : Git via winget).
2. Installe Claude Code avec l'installateur officiel d'Anthropic (`claude.ai/install.sh` ou `install.ps1`), s'il est absent.
3. Clone ce dépôt dans `~/ai/2-tools/3-software/better-claude-instance/`.
4. Crée `~/ai` et `~/project`, copie les fichiers de `skeleton/` sans jamais écraser un fichier existant.
5. Relie `~/.claude/` (CLAUDE.md, skills, agents) et complète `settings.json` : agents intégrés désactivés, hook `guard-sensible`.
6. Sauvegarde tout fichier remplacé en `*.bak-bci`.

Relancer la commande met à jour l'instance (`git pull`) sans toucher à vos fichiers.

## Pourquoi pas npm
L'installation par npm est dépréciée par Anthropic au profit de l'installateur natif, et npm n'est pas présent par défaut sous Windows.

## Pourquoi Alpine sous Android
Claude Code ne fournit pas de binaire pour Android. Il fournit en revanche un binaire `linux-arm64-musl`, qui fonctionne dans Alpine Linux lancé par `proot-distro`. Alpine est retenue pour sa légèreté (Ubuntu est trop lourde pour un téléphone). Sous Termux, la commande `claude` est un alias qui entre dans Alpine et lance Claude Code.

## Installation négociée
Pour adapter l'installation à ses besoins : installer Claude Code, cloner ce dépôt, lancer `claude` dans le dossier et demander, en n'importe quels termes, de l'installer ou de l'adapter. Le fichier `AGENTS.md` du dépôt renvoie vers `SETUP.md`, qui fait présenter chaque étape, accepter les modifications (« modifie ça, laisse ça, déplace ceci là »), confirmer le plan, puis l'appliquer.

## Désinstallation
Windows :
```
irm https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/uninstall.ps1 | iex
```
Linux / Android (dans Alpine) :
```
curl -fsSL https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/uninstall.sh | sh
```
Retire les liens et réglages, restaure les sauvegardes, puis demande avant de supprimer `~/ai` et `~/project`. Claude Code lui-même reste installé. Claude Code peut aussi désinstaller l'organisation sur simple demande (voir `SETUP.md`).

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `claude native binary not installed` (npm, Termux) | pas de binaire Android | utiliser `install.sh`, qui passe par Alpine |
| `unexpected e_type: 2` | installateur lancé dans Termux et non dans Alpine | supprimer `~/.claude/downloads` côté Termux, relancer `install.sh` |
| `apk: command not found` | commande tapée dans Termux au lieu d'Alpine | utiliser l'alias `claude`, ou `proot-distro login alpine` |
| `~/.local/bin is not in your PATH` | session ouverte avant l'installation | ouvrir un nouveau terminal (ou `. ~/.profile`) |
| recherche de fichiers en échec sous Alpine | ripgrep intégré compilé pour glibc | `USE_BUILTIN_RIPGREP=0`, ajouté automatiquement |
| `jq absent` à l'installation | settings.json existant non fusionné | installer jq et relancer |
