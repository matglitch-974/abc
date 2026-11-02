# Projets, données sensibles et publication

## Hiérarchie
```
~/project/
└── <catégorie>/              regroupe des projets (jamais un projet elle-même)
    └── <project>/
        └── <sub-project>/
```
Les noms de catégories, projects et sub-projects sont libres dans la syntaxe des noms (voir [naming.md](naming.md)). Le mot « catégorie » n'apparaît dans aucun nom de dossier.

## Unité
L'**unité** est le dossier qui porte le contenu réel et forme un dépôt Git :
- le **sub-project** ;
- ou le **project** s'il n'a pas de sub-project.

Une catégorie qui ne contient qu'un seul project reste une catégorie : elle ne devient pas le project.

Contenu d'une unité, créé par `sh ~/ai/2-tools/1-skills/project/new-unit <catégorie>/<project>[/<sub-project>]` :
```
<unité>/
├── AGENTS.md                  règles du projet (jamais de données sensibles)
├── CLAUDE.md -> AGENTS.md
├── README.md
├── .gitignore                 contient toujours sensible/
└── sensible/                  données sensibles
```

## `sensible/`
- Toujours à la racine de l'unité, toujours ce nom : il est reconnaissable d'un coup d'œil et facile à exclure partout.
- Contient uniquement des données sensibles : adresses IP, clés, identifiants… Jamais de prompts (ils ont leur propre place).
- **Version privée** = l'unité complète. **Version publique** = l'unité sans `sensible/`. Publier `sensible/` reviendrait à exposer ses propres faiblesses.

Il n'y a donc plus de dossiers `private/` et `public/` : `sensible/` suffit à séparer les deux versions.

## Protections
1. **`.gitignore`** : `sensible/` y est inscrit automatiquement à la création de chaque unité. Git ne le suit donc jamais.
2. **Hook Claude Code** (`hooks/guard-sensible.sh`, événement `PreToolUse`) : avant chaque commande, il bloque
   - toute commande qui mentionne `sensible` avec un moyen de sortie (`git add -f`, `git push`, `scp`, `rsync`, `curl`, `wget`, `nc`, `ftp`, `gh`, `tar`, `zip`) ;
   - tout `git push` depuis un dépôt qui suit déjà un fichier de `sensible/`.

## Pourquoi pas une partie privée dans un dépôt public
GitHub ne le permet pas : un dépôt est entièrement public ou entièrement privé. Les dépôts privés sont en revanche gratuits et illimités depuis 2019. Solutions étudiées :
- **git-crypt** (chiffrement de certains fichiers dans un dépôt public) : écarté. Les noms et tailles restent visibles, et une fuite de la clé rendrait tout l'historique lisible, définitivement.
- **Dépôt privé séparé** : retenu. Les données sensibles et le persona principal vivent dans le dépôt privé `home` (voir [roadmap.md](roadmap.md)).

## Sécurités supplémentaires possibles
À proposer lors d'une installation négociée (`SETUP.md`), non installées par défaut :
- hook Git `pre-push` refusant tout fichier de `sensible/` ;
- analyse de secrets avant publication (ex. gitleaks) ;
- vérification de la visibilité du dépôt distant avant un push.
