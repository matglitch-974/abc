# Hook mémoire (`hooks/memory-hook.py`)

Un automate sans LLM, branché sur les événements de Claude Code par l'installateur (`settings.json`, section `hooks`). Il tient le journal, le sommaire des tâches, la sauvegarde quotidienne, le persona de la session, la cloison des agents isolés, et range l'ancien `~/.claude`.

Il ne bloque jamais Claude Code : toute erreur est consignée dans le journal (`[hook] erreur : …`) et le code de sortie reste 0. Seule exception voulue : un accès refusé par la cloison des agents isolés (code 2, voir plus bas).

## Événements

| Événement | Ce que fait le hook |
|---|---|
| `SessionStart` | journal (`session démarrée (<source>)`) ; section Projets de `TODO.md` refaite. Au lancement (`startup`) : sauvegarde quotidienne lancée en arrière-plan, rangement de l'ancien `~/.claude`, rappel injecté (« reconnaissance des outils, skill `mission` »). Après compaction (`compact`) : `realign.md` et le persona réinjectés |
| `UserPromptSubmit` | premier message : choix du persona (`@nom`) ; journal (200 premiers caractères du message) ; tous les `BCI_REALIGN_EVERY` messages (10 par défaut, 0 = jamais) : `realign.md` réinjecté |
| `PreToolUse` (Read, Write, Edit, MultiEdit, NotebookEdit, Glob, Grep, Bash) | cloison des agents isolés |
| `PostToolUse` (Write, Edit, MultiEdit, NotebookEdit) | journal du fichier modifié |
| `PreCompact` | journal (`compaction (<déclencheur>)`) |
| `Stop` | journal (`fin de tour`, avec les 200 premiers caractères de la dernière réponse) |
| `SessionEnd` | journal ; fichiers d'état de la session effacés |

Chaque ligne du journal porte l'heure et les 8 premiers caractères de l'identifiant de session.

## Journal
`~/ai/memory/journal/AAAA-MM-JJ.md`, un fichier par jour. Chaque ligne est ajoutée au moment de l'événement : une fermeture brutale ne perd que ce qui n'a pas encore eu lieu. Le journal est écrit par le hook, jamais par l'agent.

## TODO
`~/ai/memory/TODO.md` contient deux sections : *Transverse* (à la main) et *Projets* (automatique). Au démarrage de chaque session, le hook parcourt `~/project/**/TODO.md` (hors `.git`, `sensible` et `node_modules`), garde les lignes `- [ ]` et réécrit tout ce qui se trouve entre les marqueurs `<!-- projets:début …` et `<!-- projets:fin -->`. Sans ces marqueurs, il ne touche à rien. Écriture atomique (fichier temporaire puis remplacement).

À la main : `python3 hooks/memory-hook.py todo`.

## Sauvegarde quotidienne
Au lancement d'une session, le hook démarre `hooks/bci-backup.py quotidienne --if-needed` dans un processus détaché : la session n'attend pas, et rien ne se passe si la sauvegarde du jour existe déjà. Détail des sauvegardes : [memory.md](memory.md#sauvegardes-hooksbci-backuppy).

## Persona de la session
Au premier message, `@<nom>` en tête choisit le persona : le hook cherche dans `~/ai/0-persona/` (sous-dossiers compris) un fichier dont le nom, avec ou sans extension, vaut `<nom>`. Sans `@`, ou si le nom est introuvable, c'est `slave` (avec une note dans le second cas). Le texte du persona, sans son en-tête, est injecté dans le contexte, puis réinjecté après chaque compaction. Le choix est gardé dans `~/ai/memory/.state/<session>.persona`.

## Agents isolés
Un persona dont l'en-tête porte `isolated: true` ouvre une session cloisonnée :
- journal et mémoire propres dans le dossier `isolated/<nom>/` de `~/ai` ; `realign.md` n'est pas injecté ;
- en `PreToolUse`, le hook refuse (code 2, motif sur stderr) tout accès de cette session à `~/ai/memory`, `~/ai/AGENTS.md`, `~/ai/0-persona` et aux autres agents isolés ;
- dans les autres sessions, il refuse tout accès au dossier `isolated/` de `~/ai` et aux transcripts des sessions isolées (listées dans `isolated/<nom>/sessions`).

Limites : `AGENTS.md` et la mémoire importée sont chargés au démarrage, avant le choix du persona ; la consigne d'isolement demande de les ignorer. Le filtre examine le texte des paramètres de l'outil : il n'est pas une barrière absolue, et il refuse aussi l'écriture d'un fichier qui ne fait que citer le chemin complet de ce dossier.

## Rangement de `~/.claude`
Une session Claude Code ouverte pendant l'installation garde l'ancienne configuration et peut recréer `~/.claude` ou `~/.claude.json`. Au lancement de chaque session BCI (seulement si `CLAUDE_CONFIG_DIR` vaut `~/ai/2-tools/3-software/claude-code`), le hook :
1. compte les autres processus `claude` (`tasklist` sous Windows, `pgrep` ailleurs ; en cas d'échec, il suppose qu'il y en a) ;
2. si `~/.claude` ne contient plus que `.credentials.json` et que d'autres sessions tournent, le laisse : ce sont leurs identifiants ;
3. sinon, déplace `~/.claude` et `~/.claude.json` dans `~/ai/4-trash/` sous les noms `claude-ancien_<date>` et `claude.json-ancien_<date>` (suffixe `-1`, `-2`… si le nom existe déjà) ;
4. si d'autres sessions tournent, recopie `.credentials.json` dans un `~/.claude` neuf pour ne pas les déconnecter.

Un dossier encore verrouillé est laissé en place : nouvel essai au lancement suivant. Ce qui a été rangé est noté dans le journal.

## Fichiers d'état
`~/ai/memory/.state/<session>.count` (nombre de messages), `.persona`, `.isolated` ; effacés à `SessionEnd`.

## Variables
- `BCI_REALIGN_EVERY` : fréquence de réinjection de `realign.md` (10 par défaut, 0 = jamais).
- `BCI_AI` : autre racine que `~/ai`, pour les tests.
