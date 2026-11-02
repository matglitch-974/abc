---
name: project
description: Création et organisation des projets dans ~/project (catégorie, project, sub-project, dossier sensible).
---

# Projets

- Hiérarchie : `~/project/<catégorie>/<project>/<sub-project>/`.
- Unité (dépôt Git) : le sub-project ; ou le project s'il n'a pas de sub-project. Une catégorie n'est jamais un project.
- Créer une unité : `sh ~/ai/2-tools/1-skills/project/new-unit <catégorie>/<project>[/<sub-project>]`.
- Dossier `sensible/` à la racine de chaque unité : données sensibles uniquement (IP, clés…), jamais de prompts.
- `sensible/` est toujours dans `.gitignore`. Version privée = l'unité complète en local ; version publique = sans `sensible/`.
- Un hook Claude Code bloque toute commande qui tenterait de faire sortir `sensible/`.
