# SETUP.md — installation négociée

Prompt de mise en place destiné à Claude Code. À suivre dès que l'utilisateur demande, en n'importe quels termes, d'installer, configurer, adapter ou désinstaller Better Claude Instance.

## Déroulé
1. Lire `docs/architecture.md` et `skeleton/ai/AGENTS.md` : c'est la structure de référence.
2. Inspecter la machine : système, Claude Code déjà installé ou non, `~/.claude/` et `~/.claude.json` existants (déplacés dans `~/ai/2-tools/3-software/claude-code/` à l'installation), dossiers `~/ai` et `~/project` existants.
3. Présenter à l'utilisateur, étape par étape, ce qui va être créé, relié ou modifié, et ce qui existe déjà.
4. Négocier : l'utilisateur peut garder, déplacer, renommer ou retirer n'importe quel élément (« modifie ça, laisse ça tel quel, déplace tout ceci là »). Noter chaque écart par rapport à la référence.
5. Récapituler le plan final et attendre une confirmation explicite.
6. Appliquer : sans écart, exécuter `install.sh` (Linux / Android) ou `install.ps1` (Windows) ; avec écarts, appliquer les mêmes étapes à la main en respectant les choix de l'utilisateur.
7. Mettre à jour `~/ai/AGENTS.md` (sommaire et chemins) pour qu'il décrive la structure réellement installée.
8. Rapport final : ce qui a été fait, les écarts retenus, ce qui reste à faire (connexion au compte Anthropic au premier lancement).

## Toujours appliqué, même en cas de négociation
- `sensible/` reste exclu par `.gitignore` dans chaque unité de projet.
- Le hook `hooks/guard-sensible.sh` reste actif. Sécurités supplémentaires possibles plus tard (à proposer, pas à imposer) : hook `pre-push` Git refusant tout fichier de `sensible/`, analyse de secrets avant publication (ex. gitleaks), vérification de la visibilité du dépôt distant avant un push.
- Aucun fichier existant n'est écrasé sans sauvegarde (`*.bak-bci`).

## Désinstallation
Exécuter `uninstall.sh` ou `uninstall.ps1`, ou en reproduire les étapes à la main : remettre la configuration dans `~/.claude/`, retirer `CLAUDE_CONFIG_DIR`, restaurer les sauvegardes `*.bak-bci`, retirer les réglages ajoutés, puis demander avant de supprimer `~/ai` et `~/project`.
