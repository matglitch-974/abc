#!/bin/sh
# Hook PreToolUse (Bash) : bloque toute commande susceptible de faire sortir un dossier sensible/.
# Entrée : JSON de Claude Code sur stdin. Sortie 2 = commande bloquée (message sur stderr).
input=$(cat)

block() { echo "Bloqué par guard-sensible : $1" >&2; exit 2; }

# 1. Commande qui mentionne sensible/ et un moyen de sortie ou de suivi forcé.
if printf '%s' "$input" | grep -q 'sensible'; then
  printf '%s' "$input" | grep -Eq 'git (add|stage)[^"]*(-f|--force)|git push|scp |rsync |curl |wget |(^|[ ;&|])nc |s?ftp |gh (gist|release|repo)|tar |zip ' \
    && block "la commande vise un dossier sensible/."
fi

# 2. git push depuis un dépôt qui suit déjà un fichier de sensible/.
if printf '%s' "$input" | grep -q 'git push'; then
  cwd=$(printf '%s' "$input" | sed -n 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
  [ -n "$cwd" ] && git -C "$cwd" ls-files 2>/dev/null | grep -Eq '(^|/)sensible/' \
    && block "ce dépôt suit des fichiers de sensible/ : retirez-les (git rm -r --cached sensible) avant de pousser."
fi
exit 0
