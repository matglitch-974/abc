#!/bin/sh
# BCAI — désinstallation Linux / Android (dans Alpine sous Termux).
#   bcai uninstall   (ou : curl -fsSL https://raw.githubusercontent.com/matglitch-974/Better-Context-of-Agents-Instance/main/uninstall.sh | sh)
# Deux confirmations (oui, puis un mot à taper) avant toute modification, et de nouveau avant chaque suppression.
# Remet la configuration de Claude Code dans ~/.claude, retire les liens et réglages ajoutés,
# puis demande avant de toucher à ~/ai et ~/project. Claude Code reste installé.
set -eu
AI="$HOME/ai"
CC="$AI/2-tools/3-software/claude-code"
CL="$HOME/.claude"
ROUGE=$(printf '\033[1;31m'); NORMAL=$(printf '\033[0m')
warn() { printf '%s%s%s\n' "$ROUGE" "$1" "$NORMAL" > /dev/tty; }
ask() { printf '%s [o/N] ' "$1" > /dev/tty; read -r r < /dev/tty; [ "$r" = o ] || [ "$r" = O ]; }
# Deux confirmations : [o/N], puis le mot demandé tapé en entier.
confirm2() { # confirm2 <avertissement> <question> <mot>
  warn "$1"
  ask "$2" || return 1
  printf 'Seconde confirmation : tapez « %s » : ' "$3" > /dev/tty; read -r r < /dev/tty
  [ "$r" = "$3" ] || { echo "Annulé." > /dev/tty; return 1; }
}

confirm2 "ATTENTION : la désinstallation retire BCAI de Claude Code (réglages, hooks, liens, variable CLAUDE_CONFIG_DIR) et remet la configuration dans ~/.claude. Vos dossiers ~/ai et ~/project restent en place, sauf si vous demandez ensuite leur suppression." \
  "Désinstaller BCAI ?" "desinstaller" || { echo "Rien n'a été modifié."; exit 0; }

# 1. Configuration : ~/ai/2-tools/3-software/claude-code -> ~/.claude (liens remplacés par des copies réelles)
if [ -d "$CC" ] && [ ! -e "$CL" ]; then
  mv "$CC" "$CL"; echo "configuration remise : $CL"
  [ -f "$CL/.claude.json" ] && [ ! -e "$HOME/.claude.json" ] && mv "$CL/.claude.json" "$HOME/.claude.json"
  for l in "$CL/CLAUDE.md" "$CL/skills" "$CL/agents/0-persona" "$CL/agents/system-agents"; do [ -L "$l" ] && rm "$l"; done
  for l in "$CL/plugins" "$CL/settings.json"; do
    [ -L "$l" ] || continue
    t=$(readlink "$l"); rm "$l"; [ -e "$t" ] && cp -R "$t" "$l" && echo "copié : $l"
  done
  for b in "$CL"/*.bak-bcai; do [ -e "$b" ] && [ ! -e "${b%.bak-bcai}" ] && mv "$b" "${b%.bak-bcai}" && echo "restauré : ${b%.bak-bcai}"; done
  # *.bak-bci : copies faites avant le renommage en BCAI
  for b in "$CL"/*.bak-bci; do [ -e "$b" ] && [ ! -e "${b%.bak-bci}" ] && mv "$b" "${b%.bak-bci}" && echo "restauré : ${b%.bak-bci}"; done
fi
for f in "$HOME/.profile" "$HOME/.bashrc" "$HOME/.zshrc"; do
  [ -f "$f" ] && grep -q CLAUDE_CONFIG_DIR "$f" && sed -i '/CLAUDE_CONFIG_DIR/d' "$f" && echo "variable retirée : $f"
done

for c in bcai bci; do   # bci : ancien nom (obsolète)
  [ -L "$HOME/.local/bin/$c" ] && rm "$HOME/.local/bin/$c" && echo "commande $c retirée"
done

# 2. Réglages : retirer uniquement ce que l'installation a ajouté
S="$CL/settings.json"
if [ -f "$S" ] && command -v jq >/dev/null 2>&1; then
  jq '.permissions.deny |= map(select(startswith("Agent(") | not))
      | .hooks |= with_entries(.value |= map(select((.hooks[0].command // "")
          | (contains("guard-sensible") or contains("memory-hook")) | not)))' \
     "$S" > "$S.tmp" && mv "$S.tmp" "$S" && echo "réglages nettoyés : $S"
fi

# Modèles Ollama rangés dans ~/ai par BCAI : remis dans ~/.ollama/models avant toute suppression de ~/ai
OM=$(sed -n 's/^export OLLAMA_MODELS="\(.*\)"$/\1/p' "$HOME/.profile" 2>/dev/null | tail -1)
case "$OM" in "$AI"/*)
  mkdir -p "$HOME/.ollama/models" && mv "$OM"/* "$HOME/.ollama/models/" 2>/dev/null
  sed -i '/^export OLLAMA_MODELS=/d' "$HOME/.profile"; echo "modèles Ollama remis dans ~/.ollama/models" ;;
esac

confirm2 "DANGER : supprimer ~/ai efface DÉFINITIVEMENT mémoire, personas, skills, corbeille ET toutes les sauvegardes (backup-bcai). Aucune récupération possible." \
  "Supprimer définitivement ~/ai ?" "supprimer ai" && rm -rf "$AI" && echo "~/ai supprimé"
confirm2 "DANGER : supprimer ~/project efface DÉFINITIVEMENT tous vos projets, y compris leurs dossiers sensible/ et ce qui n'a jamais été poussé sur GitHub." \
  "Supprimer définitivement ~/project ?" "supprimer project" && rm -rf "$HOME/project" && echo "~/project supprimé"
echo "Désinstallation terminée. Claude Code lui-même reste installé. Ouvrez un nouveau terminal."
