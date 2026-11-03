# Feuille de route

## Dépôt privé `home`
Le dossier personnel devient un dépôt privé, synchronisé entre les machines (téléphone, PC fixe, portable) :
```
~/                     dépôt privé « home »
├── ai/                instance complète, persona principal compris
├── project/
└── os/                ISO, points de restauration, images prises à chaud
```
Limite : GitHub refuse les fichiers de plus de 100 Mo et un dépôt doit rester sous quelques gigaoctets. `os/` sera donc exclu de Git et synchronisé autrement (rsync via SSH, disque externe) ; seul l'inventaire de son contenu peut être suivi.

## Tous les modèles de langage
Faire tourner l'instance avec n'importe quel modèle, pas seulement Claude : ChatGPT (Codex), Grok, DeepSeek, modèles locaux ; par API, en local ou au quota d'un abonnement. Les règles (`AGENTS.md`), la mémoire, les skills et les projets restent communs ; seul le moteur change.

## Second cerveau
Relier l'instance à une base de connaissances persistante, au-delà des skills de leçons.

## Modes d'autorisation « yolo » et « sécurité »
Deux jeux de réglages (`~/ai/memory/settings.json`) entre lesquels basculer : « yolo » (le moins de demandes d'autorisation possible) et « sécurité » (tout ce qui modifie ou publie demande confirmation). Les réglages restent des autorisations personnelles, donc rangés avec la mémoire.

## Vocal Instant (`vocal-instant`)
Dictée vocale instantanée dans l'esprit de Wispr Flow : parler, et le texte propre s'insère là où se trouve le curseur.
- **Déclenchement** : raccourci clavier global (maintenir pour parler) ou commande terminal `vocal-instant`.
- **Interface** : ultra minimaliste, en terminal ; au plus un indicateur d'enregistrement.
- **Chaîne** : micro → transcription locale → nettoyage (ponctuation, hésitations, mise en forme) → presse-papiers ou saisie directe.
- **Transcription** : modèle local obligatoire, l'API Claude n'acceptant pas l'audio en entrée (vérifié, novembre 2026). Candidats à évaluer : whisper.cpp, faster-whisper, ou un modèle local de voix plus récent.
- **Nettoyage** : Haiku 5.5 via `claude -p` (abonnement, sans clé), ou modèle local pour un fonctionnement hors ligne.
- **Plateformes** : Linux (X11 et Wayland diffèrent pour le raccourci global et la saisie), Windows ; Android/Termux à évaluer (micro via Termux:API).
- **Mesures d'acceptation** : latence entre fin de parole et texte inséré, taux d'erreur sur le français, consommation de quota par dictée.

## Pistes évoquées, non retenues
- **Décompiler et recompiler le binaire de Claude Code** pour en retirer les prompts : écarté, contraire aux conditions d'utilisation d'Anthropic. Alternative légitime : construire sa propre instance avec le Claude Agent SDK ou un harnais open source, avec des outils open source branchés en MCP (`2-tools/0-mcp/`) et chaque prompt d'outil sous forme de skill.
- **Installation par npm** : dépréciée par Anthropic (voir [installation.md](installation.md)).
- **git-crypt** : voir [projects.md](projects.md).
