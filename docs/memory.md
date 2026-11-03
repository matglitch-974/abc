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
└── journal/          AAAA-MM-JJ.md, écrit par le hook, jamais par l'agent
```
Format d'un souvenir et règles d'écriture : skill `memory` (`skeleton/ai/2-tools/1-skills/memory/SKILL.md`).

## Deux étages
**Automate (sans LLM)** — `hooks/memory-hook.py`, branché sur les événements de Claude Code :

| Événement | Action |
|---|---|
| `SessionStart` | journal ; section Projets de `TODO.md` refaite depuis `~/project/**/TODO.md` (hors `sensible/`) ; après compaction, injection de `realign.md` |
| `UserPromptSubmit` | journal (200 premiers caractères) ; injection de `realign.md` tous les 10 messages (`BCI_REALIGN_EVERY`, 0 = jamais) |
| `PostToolUse` (Write, Edit, MultiEdit, NotebookEdit) | journal du fichier modifié |
| `PreCompact`, `Stop`, `SessionEnd` | journal |

Chaque ligne est ajoutée au journal au moment de l'événement : une fermeture brutale ne perd que ce qui n'a pas encore eu lieu. Le hook ne bloque jamais Claude Code (erreur consignée dans le journal, sortie 0).

**Modèle** — règles dans `AGENTS.md` : écrire un souvenir dès qu'une étape est terminée ; chaque correction de l'utilisateur devient un fichier `feedback/` ; fusionner les feedbacks redondants ; vérifier un souvenir avant d'agir dessus.

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
`BCI_AI=<dossier>` redirige le hook vers une autre racine que `~/ai`, pour tester sans toucher à la vraie mémoire.
