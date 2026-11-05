# Mémoire (`~/ai/memory/`)

## Exigence
L'instance peut être fermée à n'importe quel moment sans rien perdre. Rien n'attend la fin de session pour être écrit.

## Structure
```
~/ai/memory/
├── INDEX.md          une ligne par souvenir ; chargé au démarrage (import dans AGENTS.md)
├── TODO.md           sommaire de toutes les todos : Transverse (à la main) + Projets (automatique)
├── realign.md        règles réinjectées en cours de session
├── user/             qui est l'utilisateur
├── feedback/         corrections et consignes : l'alignement de l'instance
├── project/          travaux en cours, décisions
├── reference/        pointeurs externes
├── journal/          AAAA-MM-JJ.md, écrit par le hook, jamais par l'agent
├── settings.json     réglages de Claude Code (autorisations personnelles), relié depuis la configuration
└── (sauvegardes : ~/ai/2-tools/logs/backup-bcai/, voir Sauvegardes)
```
Format d'un souvenir et règles d'écriture : skill `memory` (`skeleton/ai/2-tools/1-skills/memory/SKILL.md`).

## Deux étages
**Automate (sans LLM)** — `hooks/memory-hook.py`, branché sur les événements de Claude Code :

| Événement | Action |
|---|---|
| `SessionStart` | journal ; sauvegarde quotidienne en arrière-plan (au lancement, si pas encore faite ce jour) ; section Projets de `TODO.md` refaite depuis `~/project/**/TODO.md` (hors `sensible/`) ; après compaction, injection de `realign.md` |
| `UserPromptSubmit` | journal (200 premiers caractères) ; injection de `realign.md` tous les 10 messages (`BCAI_REALIGN_EVERY`, 0 = jamais) |
| `PostToolUse` (Write, Edit, MultiEdit, NotebookEdit) | journal du fichier modifié |
| `PreCompact`, `Stop`, `SessionEnd` | journal |

Le hook choisit aussi le persona de la session, tient la cloison des agents isolés et range l'ancien `~/.claude` : détail complet dans [memory-hook.md](memory-hook.md).

Chaque ligne est ajoutée au journal au moment de l'événement : une fermeture brutale ne perd que ce qui n'a pas encore eu lieu. Le hook ne bloque jamais Claude Code (erreur consignée dans le journal, sortie 0).

**Modèle** — règles dans `AGENTS.md` : écrire un souvenir dès qu'une étape est terminée ; chaque correction de l'utilisateur devient un fichier `feedback/` ; fusionner les feedbacks redondants ; vérifier un souvenir avant d'agir dessus.

## Sauvegardes (`hooks/bcai-backup.py`)
Tout `~/ai` est sauvegardé (mémoire, personas, skills, configuration de Claude Code, modèles locaux), dans `~/ai/2-tools/logs/backup-bcai/` (avant BCAI : `backup-bci/`, repris au premier appel du script) :
```
backup-bcai/
├── .restic/                           dépôt restic commun : données dédupliquées et compressées
├── .backup_2026-11-03/meta.json       une sauvegarde = un dossier, nom court
├── .backup_2026-11-03/metadata.json   copie lisible de la métadonnée embarquée
├── .backup_2026-11-03_install-avant/  première installation : avant…
└── .backup_2026-11-03_install-apres/  … et après ; les deux conservées à vie
```
- **Métadonnées** (`meta.json`) plutôt que nom long : date à la seconde, versions résumées, identifiant de l'instantané restic, rotation. Le nom reste court et s'ouvre partout.
- **`metadata.json` embarqué** : à la racine de chaque sauvegarde, donc restauré avec elle (`/metadata.json` dans l'instantané restic, `metadata.json` en tête de `data.tar.xz`), avec une copie dans le dossier de la sauvegarde. Contenu : version de BCAI (fichier `VERSION` du dépôt, commit, dépôt modifié ou non), date ISO, type, mode (restic ou tar.xz), système (nom, version, architecture), versions de Python, Claude Code (et tweakcc s'il l'a modifié), Node.js, npm, git, restic, uv, jq, ripgrep, curl, bash, Scrapling, Crawl4AI, et sous Windows PowerShell, pwsh, winget ; noms des MCP déclarés et des skills de `2-tools/1-skills`. `absent` si l'outil manque, `erreur (…)` s'il échoue ou dépasse 10 s : rien de cela n'arrête la sauvegarde. Ni secret, ni commande ou variable des MCP ; le dossier personnel est écrit `~`. Lire sans restaurer : `restic -r … --insecure-no-password dump <instantané> /metadata.json`.
- **restic** (≥ 0.17) : chaque sauvegarde est complète et restaurable seule, mais seuls les blocs nouveaux sont stockés (déduplication) puis compressés (zstd, niveau max). Mesure sur 21 Mo de texte, 10 jours d'ajouts simulés : 32,9 Mo en archives xz complètes contre ≈ 3,3 Mo dédupliqués. Recompresser restic en xz ne gagne rien (une archive xz repassée en xz grossit de 224 octets). Sans mot de passe : les données restent sur la machine, comme `~/ai` lui-même.
- **Sans restic** (absent ou < 0.17, ex. Debian 12) : repli sur une archive `data.tar.xz` (xz -9) dans le dossier de la sauvegarde.
- **Rythme** : une sauvegarde par jour, lancée en arrière-plan au premier démarrage de session du jour ; `install-avant` / `install-apres` lors de la première installation seulement.
- **Rotation tour de Hanoï** (Édouard Lucas) sur les quotidiennes : la sauvegarde n° k va dans le jeu `h` = nombre de zéros terminaux de k en binaire (plafonné à `BCAI_BACKUP_SETS - 1`, 8 jeux par défaut) et remplace l'ancienne de ce jeu. Récentes serrées, anciennes espacées : 8 quotidiennes + 2 d'installation = 10 sauvegardes au plus ; avec 8 jeux, l'écart maximal couvre 128 jours.
- Exception assumée à « supprimer = déplacer dans `4-trash/` » : la rotation supprime elle-même ce qu'elle remplace (`restic forget` + `prune`).
- Commandes : `python3 ~/ai/2-tools/3-software/bcai/hooks/bcai-backup.py list`, `… quotidienne`. Restaurer : `restic -r ~/ai/2-tools/logs/backup-bcai/.restic --insecure-no-password restore <instantané> --target <dossier vide>`, ou extraire `data.tar.xz` ; comparer, puis recopier ce qui manque. Échecs : `backup-bcai/errors.log`.

## Réalignement
Le modèle ne peut pas recevoir de consigne plus dense que du texte : pas de « bloc binaire ». L'alignement se construit donc par fichiers :
1. chaque correction → un fichier `feedback/` (règle, Pourquoi, Comment l'appliquer) ;
2. consolidation régulière : les règles qui se recoupent fusionnent en une seule, plus courte ;
3. les règles qui doivent tenir sur les longues sessions vont dans `realign.md`, réinjecté automatiquement. C'est le seul réalignement qui agit pendant la session ; le reste agit au démarrage suivant.

`realign.md` reste court : il est relu tous les 10 messages.

## Inspirations
- **Claude Code** : un fait par fichier, en-tête typé (user, feedback, project, reference), lignes Pourquoi / Comment l'appliquer, index, liste d'exclusions.
- **Hermes Agent** (Nous Research) : mémoire injectée une fois au démarrage puis figée (le cache de prompt reste valide), automate d'écriture indépendant de la conversation, recherche brute dans les sessions passées sans LLM.

## Tests
`BCAI_AI=<dossier>` (et `HOME=<dossier>` ; sous Windows aussi `USERPROFILE`, d'où Python tire le dossier personnel) redirige hooks et sauvegardes vers une autre racine, pour tester sans toucher à la vraie instance (`install-avant` lit `~/.claude` : rediriger aussi `HOME`). L'ancien nom `BCI_AI` est encore lu. `metadata.json` testé sous Windows avec restic 0.19 et en repli tar.xz, outils factices en échec, en attente (coupé à 10 s) ou absents. Testé : rotation avec `BCAI_BACKUP_SETS=4` (4 quotidiennes conservées), une seule quotidienne par jour, une seule paire d'installation, repli tar.xz. Le chemin restic n'a pas pu être exécuté dans l'environnement de développement (installation refusée) : à vérifier au premier lancement réel.
