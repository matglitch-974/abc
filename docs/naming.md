# Nommage et langue

## Syntaxe GitHub
Tout nom de dossier ou de fichier qui n'est pas un prompt : minuscules, chiffres, `-`, `_` ; ni accent ni espace. Raison : compatibilité totale avec GitHub, les terminaux et tous les systèmes, sans échappement.

## Exceptions
- Noms propres choisis par l'utilisateur (casse conservée).
- Fichiers de persona : nom entièrement libre (majuscules, caractères spéciaux, Unicode, alphabets non latins, émojis).
- Lettres des secteurs de `1-bench` : majuscules (`A-sector`, `AB-sector`), car elles sont l'identifiant du secteur.

## Numérotation
- `N-nom`, N de 0 à 9 : pour les dossiers à contenu fixe (racine d'`ai/`, `2-tools/`), afin d'imposer un ordre stable.
- Le contenu d'un dossier qui peut dépasser 10 éléments (personas, skills, projets) n'est pas numéroté.
- Les fichiers lus par l'IA gardent leur nom exact : `AGENTS.md`, `CLAUDE.md`, `SKILL.md`.

## Langue
- **Anglais** : noms de fichiers et de dossiers (`project`, `sub-project`, `bench`, `trash`…).
- **Français** : le dossier `sensible/`, le contenu des prompts et toute la documentation.
