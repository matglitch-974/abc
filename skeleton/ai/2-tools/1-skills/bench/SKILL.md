---
name: bench
description: Secteurs de l'espace de travail temporaire ~/ai/1-bench. À utiliser au début et à la fin de chaque travail de sous-agent.
---

# Secteurs de 1-bench

- `sh ~/ai/2-tools/1-skills/bench/sector new` : crée le prochain secteur libre (`A-sector`… `Z-sector`, `AB-sector`… `ZB-sector`, `AC-sector`…) et affiche son chemin.
- `sh ~/ai/2-tools/1-skills/bench/sector release <nom>` : supprime le secteur.

Règles :
- un secteur appartient à son créateur ; les autres peuvent le lire ;
- seul le créateur le supprime, à la fin de son travail ;
- si le créateur n'est plus disponible et que son travail est certainement terminé, un autre sous-agent le supprime ;
- à la fin du travail de l'agent principal, `1-bench/` est vide.
