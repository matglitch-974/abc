#!/bin/sh
# Better Claude Instance — installation Linux / Android (Termux).
#   curl -fsSL https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/install.sh | sh
# Termux : installe Alpine Linux (proot) puis relance ce script à l'intérieur.
# Linux : Debian, Ubuntu, Alpine, Fedora, Arch, openSUSE et dérivés.
set -eu
REPO="https://github.com/matglitch-974/better-claude-instance"
BRANCH="${BCI_BRANCH:-main}"
RAW="https://raw.githubusercontent.com/matglitch-974/better-claude-instance/$BRANCH"
DEST="$HOME/ai/2-tools/3-software/better-claude-instance"

say() { printf '\n==> %s\n' "$1"; }

# --- Android (Termux) -------------------------------------------------------
# (garde /etc/alpine-release : sous proot, les chemins et le PATH de Termux peuvent rester visibles)
if [ ! -f /etc/alpine-release ] && { [ -n "${TERMUX_VERSION:-}" ] || [ -d /data/data/com.termux/files/usr ]; } && command -v pkg >/dev/null 2>&1; then
  say "Termux détecté : installation d'Alpine Linux"
  pkg install -y proot-distro
  rm -rf "$HOME/.claude/downloads"   # restes d'un essai natif (binaire incompatible avec Android)
  # Test par entrée réelle : l'emplacement des conteneurs change selon la version de proot-distro.
  proot-distro login alpine -- true >/dev/null 2>&1 || proot-distro install alpine
  proot-distro login alpine -- sh -c "apk add --no-cache curl && curl -fsSL '$RAW/install.sh' | BCI_BRANCH='$BRANCH' sh"
  grep -q "alias claude=" "$HOME/.bashrc" 2>/dev/null || \
    echo "alias claude='proot-distro login alpine -- sh -lc claude'" >> "$HOME/.bashrc"
  say "Terminé. Fermez puis rouvrez Termux, puis tapez : claude"
  exit 0
fi

# --- Linux -------------------------------------------------------------------
SUDO=""
[ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1 && SUDO="sudo"

say "Installation des paquets nécessaires"
if   command -v apk     >/dev/null 2>&1; then $SUDO apk add --no-cache bash curl git jq ripgrep libgcc libstdc++ python3 nodejs npm
elif command -v apt-get >/dev/null 2>&1; then $SUDO apt-get update -qq && $SUDO apt-get install -y -qq curl git jq python3 nodejs npm
elif command -v dnf     >/dev/null 2>&1; then $SUDO dnf install -y curl git jq python3 nodejs npm
elif command -v pacman  >/dev/null 2>&1; then $SUDO pacman -Sy --noconfirm --needed curl git jq python nodejs npm
elif command -v zypper  >/dev/null 2>&1; then $SUDO zypper --non-interactive install curl git jq python3 nodejs npm
else echo "Gestionnaire de paquets inconnu : installez curl, git, jq, python3 et nodejs, puis relancez." >&2; exit 1
fi

if ! command -v claude >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/claude" ]; then
  say "Installation de Claude Code (installateur officiel)"
  curl -fsSL https://claude.ai/install.sh | bash
fi

say "Téléchargement de Better Claude Instance"
if [ -d "$DEST/.git" ]; then
  git -C "$DEST" pull -q --ff-only
else
  mkdir -p "$(dirname "$DEST")"
  git clone -q --depth 1 -b "$BRANCH" "$REPO" "$DEST"
fi

sh "$DEST/bootstrap.sh"
say "Terminé. Ouvrez un nouveau terminal, puis tapez : claude"
