#!/bin/sh
# bootstrap.sh — crée ~/ai et ~/project, relie Claude Code. Appelé par install.sh.
# N'écrase jamais un fichier existant ; sauvegarde ce qu'il remplace en *.bak-bci.
set -eu
SRC="$(cd "$(dirname "$0")" && pwd)"
AI="$HOME/ai"
CL="$HOME/.claude"
HOOK="$SRC/hooks/guard-sensible.sh"

# --- Arborescence et fichiers de base -----------------------------------------
mkdir -p "$AI/0-persona/system-agents" "$AI/1-bench" "$AI/2-tools/0-mcp" \
         "$AI/2-tools/1-skills" "$AI/2-tools/2-plugins" "$AI/2-tools/3-software" \
         "$AI/3-llm" "$AI/4-trash" "$HOME/project"
for t in user feedback project reference journal; do mkdir -p "$AI/memory/$t"; done

( cd "$SRC/skeleton" && find . -type f ) | while read -r f; do
  dst="$HOME/${f#./}"
  if [ -e "$dst" ]; then echo "conservé : $dst"; else
    mkdir -p "$(dirname "$dst")"; cp "$SRC/skeleton/$f" "$dst"; echo "créé     : $dst"
  fi
done
chmod +x "$SRC/hooks/memory-hook.py" "$AI/2-tools/1-skills/bench/sector" "$AI/2-tools/1-skills/bench/agent-id.py" "$AI/2-tools/1-skills/project/new-unit" "$HOOK" \
  "$AI/2-tools/1-skills/mission/tool-scan.py" "$AI/2-tools/1-skills/mission/tool-install.py"

# --- Environnement -------------------------------------------------------------
MUSL=false
{ [ -f /etc/alpine-release ] || ldd --version 2>&1 | grep -qi musl; } && MUSL=true
grep -q '.local/bin' "$HOME/.profile" 2>/dev/null || \
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.profile"
if $MUSL; then
  # Le ripgrep intégré à Claude Code est compilé pour glibc : utiliser celui du système.
  grep -q USE_BUILTIN_RIPGREP "$HOME/.profile" 2>/dev/null || \
    echo 'export USE_BUILTIN_RIPGREP=0' >> "$HOME/.profile"
fi

# --- Liens Claude Code -----------------------------------------------------------
[ -L "$CL/agents" ] && rm "$CL/agents"   # ancienne installation : agents était un lien vers un dossier
mkdir -p "$CL/agents"
link() { # link <cible> <lien>
  if [ -e "$2" ] && [ ! -L "$2" ]; then mv "$2" "$2.bak-bci"; echo "sauvegardé : $2.bak-bci"; fi
  ln -sfn "$1" "$2"; echo "lien     : $2 -> $1"
}
link "$AI/AGENTS.md"                 "$CL/CLAUDE.md"
link "$AI/2-tools/1-skills"          "$CL/skills"
link "$AI/0-persona/system-agents"   "$CL/agents/system-agents"

# --- settings.json : agents intégrés désactivés + hooks sensible/ et mémoire ----
M='{"type":"command","command":"python3 \"'"$SRC"'/hooks/memory-hook.py\""}'
ADD=$(cat <<EOF
{"permissions":{"deny":["Agent(Explore)","Agent(Plan)","Agent(general-purpose)","Agent(statusline-setup)","Agent(claude-code-guide)"]},
 "hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"sh \"$HOOK\""}]}],
  "SessionStart":[{"hooks":[$M]}], "UserPromptSubmit":[{"hooks":[$M]}],
  "PostToolUse":[{"matcher":"Write|Edit|MultiEdit|NotebookEdit","hooks":[$M]}],
  "PreCompact":[{"hooks":[$M]}], "Stop":[{"hooks":[$M]}], "SessionEnd":[{"hooks":[$M]}]}}
EOF
)
S="$CL/settings.json"
if [ ! -s "$S" ]; then
  printf '%s\n' "$ADD" > "$S"
  $MUSL && command -v jq >/dev/null && { jq '.env.USE_BUILTIN_RIPGREP="0"' "$S" > "$S.tmp" && mv "$S.tmp" "$S"; }
elif command -v jq >/dev/null 2>&1; then
  [ -e "$S.bak-bci" ] || cp "$S" "$S.bak-bci"
  jq --argjson add "$ADD" --argjson musl "$MUSL" '
    .permissions.deny = (((.permissions.deny // []) + $add.permissions.deny) | unique)
    | .hooks = (reduce ($add.hooks | keys[]) as $k (.hooks // {};
        .[$k] = (((.[$k] // []) | map(select((.hooks[0].command // "")
                   | (contains("guard-sensible") or contains("memory-hook")) | not)))
                 + $add.hooks[$k])))
    | if $musl then .env.USE_BUILTIN_RIPGREP = "0" else . end' "$S" > "$S.tmp" && mv "$S.tmp" "$S"
else
  echo "ATTENTION : jq absent, $S existant non modifié. Ajoutez-y à la main : $ADD" >&2
fi
echo "réglages : $S"

# --- Outils de recherche web (gratuits, sans clé) ---------------------------------
# Échecs non bloquants : un outil manquant n'empêche pas l'instance de fonctionner.
command -v uv >/dev/null 2>&1 || [ -x "$HOME/.local/bin/uv" ] || curl -LsSf https://astral.sh/uv/install.sh | sh || true
export PATH="$HOME/.local/bin:$PATH"
if command -v claude >/dev/null 2>&1; then
  addmcp() { claude mcp get "$1" >/dev/null 2>&1 || claude mcp add -s user "$@" || echo "ATTENTION : MCP $1 non installé" >&2; }
  addmcp fetch -- uvx mcp-server-fetch
  addmcp duckduckgo -- uvx duckduckgo-mcp-server
  if command -v npx >/dev/null 2>&1; then addmcp playwright -- npx -y @playwright/mcp@latest
  else echo "ATTENTION : Node.js absent, MCP playwright non installé" >&2; fi
fi
if command -v uv >/dev/null 2>&1 && ! command -v scrapling >/dev/null 2>&1; then
  { uv tool install -q "scrapling[ai,fetchers]" && scrapling install; } || echo "ATTENTION : Scrapling non installé" >&2
fi
command -v claude >/dev/null 2>&1 && command -v scrapling >/dev/null 2>&1 && addmcp scrapling -- scrapling mcp
if command -v uv >/dev/null 2>&1 && ! command -v crwl >/dev/null 2>&1; then
  { uv tool install -q crawl4ai && crawl4ai-setup; } || echo "ATTENTION : Crawl4AI non installé (navigateur requis)" >&2
fi
