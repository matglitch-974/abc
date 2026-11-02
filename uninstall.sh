#!/bin/sh
# Better Claude Instance — désinstallation Linux / Android (dans Alpine sous Termux).
#   curl -fsSL https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/uninstall.sh | sh
# Retire les liens et réglages ; demande avant de toucher à ~/ai et ~/project. Claude Code reste installé.
set -eu
CL="$HOME/.claude"
ask() { printf '%s [o/N] ' "$1" > /dev/tty; read -r r < /dev/tty; [ "$r" = o ] || [ "$r" = O ]; }

for l in "$CL/CLAUDE.md" "$CL/skills" "$CL/agents/system-agents"; do
  [ -L "$l" ] && rm "$l" && echo "lien retiré : $l"
  [ -e "$l.bak-bci" ] && mv "$l.bak-bci" "$l" && echo "restauré : $l"
done

S="$CL/settings.json"
if [ -e "$S.bak-bci" ]; then
  mv "$S.bak-bci" "$S"; echo "réglages restaurés : $S"
elif [ -e "$S" ] && command -v jq >/dev/null 2>&1; then
  jq '.permissions.deny |= map(select(startswith("Agent(") | not))
      | .hooks.PreToolUse |= map(select((.hooks[0].command // "") | contains("guard-sensible") | not))' \
     "$S" > "$S.tmp" && mv "$S.tmp" "$S" && echo "réglages nettoyés : $S"
fi

ask "Supprimer définitivement ~/ai (personas, skills, corbeille compris) ?" && rm -rf "$HOME/ai" && echo "~/ai supprimé"
ask "Supprimer définitivement ~/project (tous vos projets) ?" && rm -rf "$HOME/project" && echo "~/project supprimé"
echo "Désinstallation terminée. Claude Code lui-même reste installé."
