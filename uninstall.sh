#!/bin/sh
# Better Claude Instance — désinstallation Linux / Android (dans Alpine sous Termux).
#   curl -fsSL https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/uninstall.sh | sh
# Remet la configuration de Claude Code dans ~/.claude, retire les liens et réglages ajoutés,
# puis demande avant de toucher à ~/ai et ~/project. Claude Code reste installé.
set -eu
AI="$HOME/ai"
CC="$AI/2-tools/3-software/claude-code"
CL="$HOME/.claude"
ask() { printf '%s [o/N] ' "$1" > /dev/tty; read -r r < /dev/tty; [ "$r" = o ] || [ "$r" = O ]; }

# 1. Configuration : ~/ai/2-tools/3-software/claude-code -> ~/.claude (liens remplacés par des copies réelles)
if [ -d "$CC" ] && [ ! -e "$CL" ]; then
  mv "$CC" "$CL"; echo "configuration remise : $CL"
  [ -f "$CL/.claude.json" ] && [ ! -e "$HOME/.claude.json" ] && mv "$CL/.claude.json" "$HOME/.claude.json"
  for l in "$CL/CLAUDE.md" "$CL/skills" "$CL/agents/system-agents"; do [ -L "$l" ] && rm "$l"; done
  for l in "$CL/plugins" "$CL/settings.json"; do
    [ -L "$l" ] || continue
    t=$(readlink "$l"); rm "$l"; [ -e "$t" ] && cp -R "$t" "$l" && echo "copié : $l"
  done
  for b in "$CL"/*.bak-bci; do [ -e "$b" ] && mv "$b" "${b%.bak-bci}" && echo "restauré : ${b%.bak-bci}"; done
fi
for f in "$HOME/.profile" "$HOME/.bashrc" "$HOME/.zshrc"; do
  [ -f "$f" ] && grep -q CLAUDE_CONFIG_DIR "$f" && sed -i '/CLAUDE_CONFIG_DIR/d' "$f" && echo "variable retirée : $f"
done

# 2. Réglages : retirer uniquement ce que l'installation a ajouté
S="$CL/settings.json"
if [ -f "$S" ] && command -v jq >/dev/null 2>&1; then
  jq '.permissions.deny |= map(select(startswith("Agent(") | not))
      | .hooks |= with_entries(.value |= map(select((.hooks[0].command // "")
          | (contains("guard-sensible") or contains("memory-hook")) | not)))' \
     "$S" > "$S.tmp" && mv "$S.tmp" "$S" && echo "réglages nettoyés : $S"
fi

ask "Supprimer définitivement ~/ai (personas, skills, sauvegardes, corbeille compris) ?" && rm -rf "$AI" && echo "~/ai supprimé"
ask "Supprimer définitivement ~/project (tous vos projets) ?" && rm -rf "$HOME/project" && echo "~/project supprimé"
echo "Désinstallation terminée. Claude Code lui-même reste installé. Ouvrez un nouveau terminal."
