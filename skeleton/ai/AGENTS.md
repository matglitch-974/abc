# AGENTS.md — instance principale

Fichier lu par l'agent principal à chaque session (via `~/.claude/CLAUDE.md`).

## Sommaire

```
~/ai/
├── AGENTS.md                ce fichier : sommaire + règles de travail
├── 0-persona/               personas (contenu non numéroté)
│   ├── <persona principal>  facultatif, nom libre
│   └── system-agents/       agents système (slave.md)
├── 1-bench/                 espace de travail temporaire, découpé en secteurs
├── 2-tools/
│   ├── 0-mcp/               serveurs MCP
│   ├── 1-skills/            skills (= ~/.claude/skills)
│   ├── 2-plugins/
│   └── 3-software/          logiciels utilisés par l'IA (dont better-claude-instance)
├── 3-llm/                   modèles et runtimes locaux
├── 4-trash/                 corbeille
└── memory/                  mémoire : INDEX.md, TODO.md, realign.md, user/ feedback/ project/ reference/, journal/
~/project/<catégorie>/<project>/<sub-project>/
```

## Persona principal (facultatif)

Décrit uniquement le caractère. Le retirer ne change rien au travail.
Pour l'activer : retirer les marques de commentaire et remplacer `<nom>` par le nom exact du fichier.

<!-- @~/ai/0-persona/<nom> -->

## Règles de travail

1. Aucune invention, sauf demande explicite.
2. Se baser sur des outils existants (utilisation, puis fork). Priorités : qualité et capacité de modification, puis open source, puis licence la plus permissive.
3. Si un script peut faire la tâche, utiliser le script. L'IA est réservée aux nuances. Toute tâche récurrente devient un script.
4. Vérifier chiffres, sources et méthodes avant de répondre ; relire et corriger avant d'envoyer.
5. Informer l'utilisateur avant toute modification importante de fichiers.
6. Demander une clarification dès qu'une demande est ambiguë.

## Délégation

- Tout sous-agent passe par l'agent `slave` (`0-persona/system-agents/slave.md`). Les agents intégrés de Claude Code sont désactivés.
- Un récapitulatif, une recherche ou une exploration sont des tâches confiées à `slave`, pas des agents à part.
- L'agent principal présente le travail des sous-agents comme le sien : il le vérifie et en assume la responsabilité.
- `slave` ne lit pas ce fichier : toute règle utile à la tâche doit figurer dans la consigne de délégation.

### Identifiant à 4 chiffres
- Avant chaque lancement : `python3 ~/ai/2-tools/1-skills/bench/agent-id.py new` (Windows : `python`) réserve un code libre et affiche le nom complet, par exemple `slave-4821`.
- Ce nom accompagne le sous-agent du lancement à l'arrêt : en tête de la `description` de l'appel (`slave-4821 : audit des liens`), dans la consigne (« Ton identifiant : slave-4821 ») et en tête de son rapport. L'agent principal désigne chaque sous-agent par ce nom, jamais par un numéro d'ordre.
- À l'arrêt du sous-agent (rapport reçu, échec ou interruption) : `agent-id.py release slave-4821`. `agent-id.py list` affiche les sous-agents encore vivants.

## Mémoire

La session peut être fermée à tout moment : rien ne doit attendre la fin pour être écrit.

@~/ai/memory/INDEX.md
@~/ai/memory/TODO.md

- **Automatique** (hook `memory-hook.py`, sans LLM) : `journal/AAAA-MM-JJ.md` reçoit chaque message, chaque fichier modifié, chaque fin de tour et chaque compaction ; la section Projets de `TODO.md` est refaite au démarrage ; `realign.md` est réinjecté tous les 10 messages et après compaction. Ne jamais éditer `journal/`.
- **À la charge de l'agent**, dès qu'une étape est terminée : un fait par fichier dans `memory/<type>/`, une ligne dans `INDEX.md`. Format et exclusions : skill `memory`.
- Chaque correction de l'utilisateur devient un fichier `feedback/` : c'est l'alignement. Fusionner les feedbacks qui se recoupent en une règle plus courte ; une règle essentielle remonte dans `realign.md`.
- Un souvenir décrit le passé : vérifier ce qu'il nomme (fichier, commande, état) avant d'agir dessus.
- Tâches : celles d'un projet dans le `TODO.md` de son unité ; les transverses dans `memory/TODO.md`.

## Amélioration continue

Après chaque erreur, correction de l'utilisateur ou technique découverte :
1. rédiger la leçon dans un skill (`~/ai/2-tools/1-skills/<sujet>/SKILL.md`, créé ou complété) : contexte, leçon, application ;
2. signaler à l'utilisateur qu'une leçon a été enregistrée.

## 1-bench (secteurs)

- Chaque sous-agent crée son secteur avec `~/ai/2-tools/1-skills/bench/sector new` : `A-sector`, `B-sector`… `Z-sector`, puis `AB-sector`, `BB-sector`… `ZB-sector`, puis `AC-sector`, etc.
- Tout sous-agent peut lire le secteur d'un autre.
- Seul le créateur supprime son secteur, à la fin de son travail. Si le créateur n'est plus disponible et que son travail est certainement terminé, un autre sous-agent le supprime à sa place.
- À la fin du travail de l'agent principal, `1-bench/` est vide.

## 4-trash (corbeille)

- Supprimer = déplacer dans `4-trash/`.
- La corbeille n'est jamais vidée sans la supervision de l'utilisateur.

## Projets

- Hiérarchie : `~/project/<catégorie>/<project>/<sub-project>/`.
- L'unité (dépôt Git) est le sub-project ; ou le project s'il n'a pas de sub-project. Une catégorie n'est jamais elle-même un project.
- Chaque unité contient `AGENTS.md`, `CLAUDE.md -> AGENTS.md`, `README.md`, `TODO.md`, `.gitignore` et `sensible/`.
- Créer une unité : `~/ai/2-tools/1-skills/project/new-unit <catégorie>/<project>[/<sub-project>]`.
- `sensible/` (toujours à la racine de l'unité) contient uniquement des données sensibles (IP, clés…), jamais de prompts. Il est exclu par `.gitignore` et ne sort jamais vers un dépôt public ; un hook bloque les tentatives.

## Nommage

- Syntaxe GitHub : minuscules, chiffres, `-`, `_` ; ni accent ni espace.
- Exceptions : noms propres choisis par l'utilisateur, fichiers de persona (nom libre), lettres des secteurs (majuscules).
- Numérotation `N-nom` (0 à 9) pour les dossiers à contenu fixe ; le contenu d'un dossier pouvant dépasser 10 éléments n'est pas numéroté.
- Les fichiers lus par l'IA (`AGENTS.md`, `CLAUDE.md`, `SKILL.md`) gardent leur nom exact.
- Noms de fichiers et de dossiers en anglais ; `sensible/`, contenu des prompts et documentation en français.
