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

# Identifiants de sous-agents

`agent-id.py` donne à chaque sous-agent un code à 4 chiffres, de son lancement à son arrêt. Il coexiste avec les secteurs : le code identifie l'agent, le secteur est son espace de travail. Utilisé par l'agent principal (`python3`, ou `python` sous Windows) :
- `agent-id.py new [nom]` : réserve un code libre et affiche `<nom>-<code>` (nom par défaut : `slave`), par exemple `slave-4821` ;
- `agent-id.py release <code>` : libère le code à l'arrêt du sous-agent (accepte aussi `slave-4821`) ;
- `agent-id.py list` : sous-agents encore vivants.

Le nom `slave-<code>` se place en tête de la `description` de l'appel (`slave-4821 : audit des liens`), dans la consigne (« Ton identifiant : slave-4821 ») et en tête du rapport. L'agent principal désigne chaque sous-agent par ce nom, jamais par un numéro d'ordre ; il libère le code à l'arrêt (rapport, échec ou interruption).

Registre : un fichier `1-bench/<code>.id` par sous-agent vivant ; sa création exclusive interdit les doublons, même entre lancements simultanés.
