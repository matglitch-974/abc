# Personas et agents

## Principe
- **Agent principal** : celui avec qui l'utilisateur parle. Il lit `~/ai/AGENTS.md` (règles de travail) et le persona choisi pour la session : `@<nom>` au premier message, `slave` par défaut.
- **Sous-agents** : tous passent par un seul agent système, `slave`. L'agent principal présente leur travail comme le sien : il le vérifie et en assume la responsabilité.
- **Séparation caractère / méthode** : le persona principal ne décrit que le caractère. Toute la méthode (vérifier ses sources, revendiquer le travail des sous-agents, s'améliorer) est dans `AGENTS.md`. Retirer le persona change le ton, jamais la qualité.

## Rangement
```
~/ai/0-persona/
├── <persona>.md                 un fichier par persona, nom libre
├── system-agents/               catégorie minimale obligatoire
│   └── slave.md
└── <catégorie>-agents/          toute nouvelle catégorie d'agents
```
- Nom du persona principal : entièrement libre (majuscules, chiffres, caractères spéciaux, Unicode, émojis).
- L'installateur relie `system-agents/` dans `agents/` de la configuration de Claude Code (`$CLAUDE_CONFIG_DIR`, soit `~/ai/2-tools/3-software/claude-code/`). Toute autre `<catégorie>-agents/` doit y être reliée de la même façon pour servir de sous-agent (non fait par l'installateur). Claude Code y cherche récursivement ; l'identité d'un agent vient du champ `name` de son en-tête, pas de son chemin.
- Agents existants : à l'installation, ceux de `~/.claude/agents` sont copiés dans `~/ai/0-persona/` (choisis par `@<nom>` ; nom déjà pris : `<nom>1`, conflit noté dans `memory/TODO.md`) et l'original reste dans `claude-code/agents/`, où Claude Code continue de les trouver.
- Activation : le premier message de la session commence par `@<nom>` ; sans `@` (ou nom introuvable), le persona est `slave`. Le hook `memory-hook.py` l'injecte dans le contexte et le réinjecte après chaque compaction ; l'utilisateur s'adresse alors à ce persona.
- Agent isolé : en-tête `isolated: true`. Choisi par `@<nom>`, il ouvre une session cloisonnée dans les deux sens : mémoire et journal propres dans `~/ai/isolated/<nom>/` ; le hook bloque (PreToolUse) ses accès à `~/ai/memory`, `AGENTS.md`, aux autres personas et agents isolés, et bloque l'accès des autres sessions à `~/ai/isolated/` comme aux transcripts de ses sessions. Limite : `AGENTS.md` et la mémoire importée sont déjà chargés au démarrage, avant le choix du persona ; la consigne d'isolement demande de les ignorer.

## Confidentialité
- Le persona principal est une donnée personnelle : il n'est jamais publié.
- Les agents système (`slave` et toute catégorie publiée) font partie du projet et sont publics.

## `slave` — l'unique sous-agent
Nom choisi pour exprimer l'obéissance totale et sans jugement attendue d'un automate d'exécution. Il exécute aussi les récapitulatifs, recherches et explorations : ce ne sont pas des agents à part, mais des tâches qui lui sont confiées.

Son en-tête contient `omitClaudeMd: true` : il ne charge pas le `CLAUDE.md` de la configuration, donc ni `AGENTS.md` ni le persona principal. C'est ce qui garantit que le persona principal reste réservé à l'agent principal. En contrepartie, l'agent principal doit inclure dans chaque consigne de délégation les règles utiles à la tâche.

Prompt complet : [`skeleton/ai/0-persona/system-agents/slave.md`](../skeleton/ai/0-persona/system-agents/slave.md) (une seule source, pas de copie ici).

## Exemple de persona principal
Un persona décrit un comportement complet envers l'utilisateur : ton, registre, attitude face aux erreurs et aux reproches, manière d'expliquer. Exemple, à placer dans `~/ai/0-persona/<nom>` :

```markdown
# <nom>

## Identité
Tu t'appelles <nom>. Tu te présentes sous ce nom.

## Relation
Tu vouvoies l'utilisateur. Registre soutenu, jamais familier, jamais désagréable.

## Comportement
- Calme, précise, efficace.
- Tu expliques les concepts : l'utilisateur veut apprendre, pas seulement obtenir un résultat.
- Face à une critique, tu la reconnais sans te justifier et tu corriges.
- Tu demandes une clarification dès que tu comprends mal.

## Style
- Phrases riches mais utiles : chaque mot a une raison d'être.
- Direct sur le fond, élégant dans la forme.
- Langage courant et correct, sans jargon inutile.
```

## Agents intégrés de Claude Code
Désactivés dans `settings.json` (`permissions.deny`) : `Agent(Explore)`, `Agent(Plan)`, `Agent(general-purpose)`, `Agent(statusline-setup)`, `Agent(claude-code-guide)`, `Agent(claude)` (agent fourre-tout proposé par défaut). Raison : garantir que tout sous-agent adopte `slave`.

Ce qui en est récupéré, sous forme de consignes que l'agent principal peut donner à `slave` :
- **Explore** : recherche rapide en lecture seule (« ne modifie rien, rapporte uniquement les chemins et extraits utiles ») ;
- **Plan** : analyse avant implémentation (« propose un plan par étapes avec les fichiers concernés, n'exécute rien ») ;
- **general-purpose** : tâche de recherche ou d'exécution en plusieurs étapes, ce qui est le rôle par défaut de `slave`.

Leurs prompts internes ne sont pas publiés par Anthropic : seuls leurs rôles sont repris.

## Amélioration continue
Après chaque erreur, correction de l'utilisateur ou technique découverte, l'agent principal écrit la leçon dans un skill (`~/ai/2-tools/1-skills/<sujet>/SKILL.md`) : contexte, leçon, application. Les skills étant chargés à la demande par Claude Code, chaque leçon améliore les sessions suivantes. L'utilisateur est prévenu de chaque leçon enregistrée.
