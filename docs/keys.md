# Coffre des clés (`~/ai/2-tools/4-keys-code`)

Un seul endroit pour les secrets : clés SSH, jetons, clés d'API, identifiants d'outils, cookies. Règle de l'instance : un secret n'est **jamais copié hors de ce dossier** (ni dans un projet, ni dans la mémoire, ni dans un rapport).

## Remplissage : `hooks/abc-import.py secrets`
Lancé par l'installateur (`abc-import.py all`) et à la demande (`abc import secrets`). Tout est **copié** : les originaux restent en place et les outils continuent de fonctionner. Relancer ne crée pas de doublon.

| Dossier | Contenu |
|---|---|
| `ssh/` | copie de `~/.ssh` |
| `env/secrets.env` | variables d'environnement dont le nom contient KEY, TOKEN, SECRET, PASSWORD, PASSWD ou API (sous Windows : variables utilisateur du registre) ; les variables de session de Claude Code (`CLAUDE_CODE_MESSAGING…`, `SESSION`, `BRIDGE`, `CHILD`) sont écartées |
| `tools/` | `.git-credentials`, `.netrc` / `_netrc`, `docker/config.json`, `.npmrc`, `.pypirc`, `pip.conf` / `pip.ini`, `aws/`, `kube/config`, `rclone/rclone.conf`, `gh/hosts.yml`, `gh/token` (sortie de `gh auth token`), `claude/.credentials.json`, `claude/.claude.json` |
| `cookies/` | Firefox : exportés au format Netscape (`firefox-<profil>.txt`, utilisable par curl, yt-dlp…) ; Chrome, Edge, Brave : bases copiées telles quelles, chiffrées par le navigateur (lisibles seulement sur le même compte) |
| `llm/<outil>/` | fichiers secrets trouvés dans les configs des autres LLM (`id_*`, `*.pem`, `*.key`, `*credential*`, `auth.json`, `oauth*.json`, `.env*`, `token*`) |
| `mcp/` | ancien emplacement `2-tools/0-mcp/sensible`, versé ici (l'original part dans `4-trash`) |

Droits restreints au propriétaire (700 / 600) hors Windows. L'import n'affiche que les **noms** des variables, jamais leurs valeurs.

## Chiffrement : `hooks/abc-keys.py` (commande `abc keys`)
Le chiffrement est facultatif ; il exige restic. `abc-keys.py` vérifie seulement que restic est présent, pas sa version ; le seuil 0.17 est contrôlé par `abc-backup.py` pour les sauvegardes. L'installateur le propose une fois (`ABC_ENCRYPT_KEYS=oui|non` évite la question).

| Commande | Effet |
|---|---|
| `abc keys close` | chiffre `4-keys-code` dans `4-keys-code.restic` ; vérifie que le nombre de fichiers chiffrés égale celui des fichiers en clair ; garde les 3 derniers instantanés ; puis efface la version en clair. Premier appel : crée le coffre, phrase secrète demandée deux fois |
| `abc keys open` | déchiffre le dernier instantané dans `4-keys-code` |
| `abc keys status` | `ouvert`, `fermé (chiffré)`, `non chiffré` ou `absent` |

- Phrase secrète demandée au terminal, ou lue dans `ABC_KEYS_PASSWORD`. **Phrase oubliée = secrets perdus.**
- Si la sauvegarde ou la vérification échoue, rien n'est effacé.
- Coffre fermé : `abc import secrets` ne réimporte rien (ouvrez-le d'abord).
- Coffre créé : la version en clair n'entre jamais dans les sauvegardes quotidiennes, seul le coffre chiffré y va.

## Protections
- Le hook `guard-sensible.sh` bloque toute commande Bash qui mentionne `4-keys-code` (ou `sensible`) avec un moyen de sortie : `git add -f`, `git push`, `scp`, `rsync`, `curl`, `wget`, `nc`, `ftp`, `gh gist|release|repo`, `tar`, `zip`. Une exclusion (`--exclude=…keys-code…`) ne compte pas comme une mention.
- Ce filtre est contournable (script, motif détourné) : il complète la règle, il ne la remplace pas.
