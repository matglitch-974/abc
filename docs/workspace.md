# Espace de travail (1-bench) et corbeille (4-trash)

## 1-bench
Nom : *bench*, abréviation de *workbench* (établi). « Établi » a été écarté à cause de son accent, incompatible avec la syntaxe des noms ; `tmp` et `temp` l'ont été pour leur manque de caractère.

`1-bench/` est entièrement temporaire. Il est découpé en **secteurs**, un par sous-agent :

- Création : `sh ~/ai/2-tools/1-skills/bench/sector new` crée le prochain secteur libre et affiche son chemin.
- Ordre : `A-sector` … `Z-sector`, puis `AB-sector`, `BB-sector` … `ZB-sector`, puis `AC-sector`, etc. En pratique, 26 secteurs suffisent ; la suite n'existe que par sécurité.
- Les lettres sont en majuscules : elles sont l'identifiant du secteur (exception à la règle des minuscules).
- Lecture : tout sous-agent peut lire le secteur d'un autre ; interdire la lecture limiterait trop la collaboration.
- Suppression : seul le créateur supprime son secteur (`sector release <nom>`), à la fin de son travail. Si le créateur n'est plus disponible et que son travail est certainement terminé, un autre sous-agent le supprime à sa place.
- À la fin du travail de l'agent principal, `1-bench/` est vide.

`mkdir` étant atomique, deux sous-agents lancés en même temps ne peuvent pas obtenir le même secteur.

## 4-trash
- Supprimer un fichier hors de `1-bench/` = le déplacer dans `4-trash/`.
- La corbeille n'est jamais vidée sans la supervision de l'utilisateur ; idéalement, c'est lui qui la vide.
