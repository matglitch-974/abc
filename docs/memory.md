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
└── backup/           archives .tar.gz en rotation tour de Hanoï (voir Sauvegardes)
```
Format d'un souvenir et règles d'écriture : skill `memory` (`skeleton/ai/2-tools/1-skills/memory/SKILL.md`).

## Deux étages
**Automate (sans LLM)** — `hooks/memory-hook.py`, branché sur les événements de Claude Code :

| Événement | Action |
|---|---|
| `SessionStart` | journal ; sauvegarde (au lancement seulement) ; section Projets de `TODO.md` refaite depuis `~/project/**/TODO.md` (hors `sensible/`) ; après compaction, injection de `realign.md` |
| `UserPromptSubmit` | journal (200 premiers caractères) ; injection de `realign.md` tous les 10 messages (`BCI_REALIGN_EVERY`, 0 = jamais) |
| `PostToolUse` (Write, Edit, MultiEdit, NotebookEdit) | journal du fichier modifié |
| `PreCompact`, `Stop`, `SessionEnd` | journal |

Chaque ligne est ajoutée au journal au moment de l'événement : une fermeture brutale ne perd que ce qui n'a pas encore eu lieu. Le hook ne bloque jamais Claude Code (erreur consignée dans le journal, sortie 0).

**Modèle** — règles dans `AGENTS.md` : écrire un souvenir dès qu'une étape est terminée ; chaque correction de l'utilisateur devient un fichier `feedback/` ; fusionner les feedbacks redondants ; vérifier un souvenir avant d'agir dessus.

## Sauvegardes
Schéma documenté : rotation **tour de Hanoï** (*Tower of Hanoi backup rotation*), plus une règle : la première sauvegarde (`origine`) n'est jamais supprimée.

- Une archive `AAAAMMJJ-HHMMSS-n<k>-<jeu>.tar.gz` de `~/ai/memory` (sans `backup/` ni `.state/`) à chaque lancement de session, ou à la demande : `memory-hook.py backup`.
- La sauvegarde n° k va dans le jeu `h` = nombre de zéros terminaux de k en binaire, et remplace l'ancienne sauvegarde de ce jeu. Le jeu 0 est réécrit une fois sur deux, le jeu 1 une fois sur quatre, le jeu 2 une fois sur huit…
- Résultat : les sauvegardes récentes sont serrées, les anciennes espacées, et leur nombre reste borné : `BCI_BACKUP_SETS` jeux (8 par défaut) + l'origine. Avec 8 jeux, l'écart maximal couvre 128 sessions.
- Exemple avec 4 jeux, après 20 sauvegardes : il reste 1 (origine), 16, 18, 19, 20.
- Exception assumée à la règle « supprimer = déplacer dans `4-trash/` » : la rotation supprime elle-même les archives remplacées, sinon la corbeille grossirait sans fin.
- Restaurer : extraire l'archive voulue dans un dossier vide, comparer, puis copier ce qui manque.

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
Jeu de test : 20 sauvegardes avec `BCI_BACKUP_SETS=4` donnent la suite ci-dessus. `BCI_AI=<dossier>` redirige le hook vers une autre racine que `~/ai`, pour tester sans toucher à la vraie mémoire.
