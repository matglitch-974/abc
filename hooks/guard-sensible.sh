#!/bin/sh
# Hook PreToolUse (Bash) : bloque toute commande susceptible de faire sortir un dossier sensible/
# ou le coffre des clés (~/ai/2-tools/4-keys-code).
# Entrée : JSON de Claude Code sur stdin. Sortie 2 = commande bloquée (message sur stderr).
input=$(cat)
# Seule la commande compte (pas sa description) ; sans Python, repli sur tout le JSON.
cmd=$(printf '%s' "$input" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' 2>/dev/null) \
  || cmd=$input
# Une exclusion (--exclude=sensible…) protège sensible/ : elle ne compte pas comme une mention.
cmd=$(printf '%s' "$cmd" | sed -E 's/--exclude[= ][^ ]*(sensible|keys-code)[^ ]*//g')

block() { echo "Bloqué par guard-sensible : $1" >&2; exit 2; }

# 1. Commande qui mentionne sensible/ et un moyen de sortie ou de suivi forcé.
if printf '%s' "$cmd" | grep -Eq 'sensible|4-keys-code'; then
  printf '%s' "$cmd" | grep -Eq 'git (add|stage)[^"]*(-f|--force)|git push|scp |rsync |curl |wget |(^|[ ;&|])nc |s?ftp |gh (gist|release|repo)|tar |zip ' \
    && block "la commande vise un dossier sensible/ ou 4-keys-code."
fi

# 2. git push depuis un dépôt qui suit déjà un fichier de sensible/.
if printf '%s' "$cmd" | grep -q 'git push'; then
  cwd=$(printf '%s' "$input" | sed -n 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
  [ -n "$cwd" ] && git -C "$cwd" ls-files 2>/dev/null | grep -Eq '(^|/)sensible/' \
    && block "ce dépôt suit des fichiers de sensible/ : retirez-les (git rm -r --cached sensible) avant de pousser."
fi
exit 0
