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

## Commandes d'installation plus courtes
Les commandes actuelles passent par `raw.githubusercontent.com`. Pistes :
- renommer le dépôt en `better-claude-instance` (dans GitHub : Settings → General → Repository name ; les anciens liens sont redirigés) ;
- publier des alias courts depuis un site GitHub Pages personnel ou un dépôt dédié au nom très court, par exemple `irm <utilisateur>.github.io/w | iex` et `curl -sL <utilisateur>.github.io/l | sh`.

## Second cerveau
Relier l'instance à une base de connaissances persistante, au-delà des skills de leçons.

## Pistes évoquées, non retenues
- **Décompiler et recompiler le binaire de Claude Code** pour en retirer les prompts : écarté, contraire aux conditions d'utilisation d'Anthropic. Alternative légitime : construire sa propre instance avec le Claude Agent SDK ou un harnais open source, avec des outils open source branchés en MCP (`2-tools/0-mcp/`) et chaque prompt d'outil sous forme de skill.
- **Installation par npm** : dépréciée par Anthropic (voir [installation.md](installation.md)).
- **git-crypt** : voir [projects.md](projects.md).
