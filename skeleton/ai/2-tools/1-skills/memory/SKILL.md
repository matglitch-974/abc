---
name: memory
description: Écrire, mettre à jour ou consolider la mémoire ~/ai/memory (un fait par fichier, index, todos, réalignement). À utiliser dès qu'une étape est terminée, qu'une correction est reçue ou qu'un fait mérite de survivre à la session.
---

# Mémoire de ~/ai/memory

## Format d'un souvenir
Un fichier par fait : `~/ai/memory/<type>/<nom-en-kebab>.md`.

```markdown
---
name: <nom-en-kebab>
description: <une ligne, sert à juger la pertinence au rappel>
type: user | feedback | project | reference
---

<le fait ; pour feedback et project, ajouter :>
**Pourquoi :** <la raison, souvent un incident ou une contrainte>
**Comment l'appliquer :** <quand et où la règle s'applique>
```

Puis une ligne dans `INDEX.md` : `- [Titre](<type>/<nom>.md) — accroche`.

## Types
- `user` : qui est l'utilisateur, ses compétences, ses préférences.
- `feedback` : corrections et consignes, confirmées ou reçues. C'est l'alignement de l'instance.
- `project` : travaux en cours, décisions, contraintes absentes du code. Dates absolues (AAAA-MM-JJ), jamais « demain ».
- `reference` : pointeurs vers l'extérieur (URL, tableau de bord, ticket).

## Règles
- Avant d'écrire : chercher un fichier qui couvre déjà le sujet et le mettre à jour plutôt que d'en créer un second.
- Supprimer un souvenir faux = le déplacer dans `~/ai/4-trash/` et retirer sa ligne de l'index.
- Lier les souvenirs voisins par `[[nom]]`.

## Ne pas enregistrer
- Ce que le dépôt ou l'historique Git disent déjà (structure du code, correctifs passés).
- Ce qui ne sert qu'à la conversation en cours (étapes de travail : todo du projet).
- Tout contenu d'un dossier `sensible/` : clés, mots de passe, IP.

## Consolidation
Quand plusieurs feedbacks se recoupent : les fusionner en une règle plus courte et plus forte, déplacer les anciens dans `4-trash/`. Une règle qui doit tenir sur les longues sessions va dans `realign.md` (court : il est réinjecté tous les 10 messages et après chaque compaction).

## Todos
- Chaque unité de `~/project` a son `TODO.md` (`- [ ] tâche`).
- `~/ai/memory/TODO.md` : section Transverse écrite à la main ; section Projets refaite automatiquement. Forcer la mise à jour : `python3 ~/ai/2-tools/3-software/bcai/hooks/memory-hook.py todo` (Windows : `python`).

## Sauvegardes
Tout `~/ai` est sauvegardé une fois par jour dans `~/ai/2-tools/logs/backup-bcai/` (restic, rotation tour de Hanoï ; détail : `docs/memory.md` du dépôt). Sauvegarde immédiate (avant une consolidation risquée) : `python3 ~/ai/2-tools/3-software/bcai/hooks/bcai-backup.py quotidienne` ; liste : `… list`. Restaurer dans `~/ai/1-bench/<secteur>/`, comparer, recopier ce qui manque.

## Journal
`journal/AAAA-MM-JJ.md` est écrit par le hook, jamais par l'agent. Il sert à reprendre après une fermeture brutale : relire le journal du jour pour savoir où la session s'est arrêtée.
