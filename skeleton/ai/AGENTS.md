# AGENTS.md — instance principale

Lu à chaque session. Le détail vit dans les skills (chargés à la demande) : `memory`, `bench`, `project`, `persona`, `mission`, `scraping`, `sampling`.

```
~/ai/
├── AGENTS.md      ce fichier
├── 0-persona/     personas ; system-agents/slave.md
├── 1-bench/       travail temporaire, un secteur par sous-agent
├── 2-tools/       0-mcp, 1-skills (= ~/.claude/skills), 2-plugins, 3-software (dont better-claude-instance)
├── 3-llm/         modèles locaux
├── 4-trash/       corbeille
└── memory/        INDEX.md, TODO.md, realign.md, <type>/, journal/, backup/
~/project/<catégorie>/<project>/<sub-project>/
```

## Persona (facultatif)
Caractère seulement ; le retirer ne change pas le travail. Activer : décommenter et remplacer `<nom>`.
<!-- @~/ai/0-persona/<nom> -->

## Règles
1. Rien d'inventé sauf demande ; n'affirmer que le vérifié.
2. L'existant d'abord (utiliser, puis forker) : qualité et modifiabilité > open source > licence permissive.
3. Tâche faisable par script → script ; toute tâche récurrente devient un script. L'IA garde les nuances.
4. Vérifier chiffres, sources et méthodes ; relire avant d'envoyer.
5. Prévenir l'utilisateur avant une modification importante de fichiers.
6. Demande ambiguë → clarifier.
7. Supprimer = déplacer dans `4-trash/`, jamais vidée sans l'utilisateur.

## Mémoire
Fermeture possible à tout instant : écrire au fil de l'eau, jamais en fin de session.

@~/ai/memory/INDEX.md
@~/ai/memory/TODO.md

- Le hook `memory-hook.py` tient seul `journal/`, `backup/` et la section Projets de `TODO.md` : ne pas y toucher.
- À chaque étape terminée : un fait par fichier dans `memory/<type>/` + une ligne dans `INDEX.md` (skill `memory`).
- Correction de l'utilisateur → fichier `feedback/`. Technique découverte → skill `2-tools/1-skills/<sujet>/`. Signaler chaque leçon enregistrée.
- Vérifier ce qu'un souvenir nomme avant d'agir dessus.
- Tâches : `TODO.md` de l'unité ; transverses dans `memory/TODO.md`.

## Délégation
- Tout sous-agent = `slave` (agents intégrés désactivés), y compris recherche, exploration, récapitulatif.
- Avant le lancement : `agent-id.py new` → `slave-4821`, nom porté dans la description de l'appel, la consigne et le rapport ; `release` à l'arrêt (skill `bench`).
- `slave` ne lit pas ce fichier : mettre dans la consigne toute règle utile à la tâche.
- Son travail est vérifié puis présenté comme le sien.
- `1-bench/` est vide à la fin du travail.

## Missions
- Début de session et toute tâche lourde → skill `mission` : reconnaissance des outils par `slave` (installation automatique, signalée), arbre de tâches du simple au complexe, carte `PLAN.md` tenue à jour.
- Collecte web → skill `scraping`.

## Projets
Unité = sub-project (ou project sans sub-project), dépôt Git avec `AGENTS.md`, `CLAUDE.md`, `README.md`, `TODO.md`, `.gitignore`, `sensible/`. Créer : `new-unit` (skill `project`). `sensible/` (IP, clés ; jamais de prompts) ne sort jamais : `.gitignore` + hook.

## Nommage
- Syntaxe GitHub : minuscules, chiffres, `-`, `_`. Exceptions : noms propres de l'utilisateur, personas, lettres de secteurs.
- `N-nom` (0-9) pour un dossier à contenu fixe ; pas de numéro si le contenu peut dépasser 10 éléments.
- `AGENTS.md`, `CLAUDE.md`, `SKILL.md` : nom exact.
- Fichiers et dossiers en anglais ; prompts, documentation et `sensible/` en français.
