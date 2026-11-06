#!/bin/sh
# ABC (Agents with a Better Context) — installation Linux / Android (Termux).
#   curl -fsSL matglitch-974.github.io/abc | sh
#   (secours : curl -fsSL https://raw.githubusercontent.com/matglitch-974/abc/main/ABC-install-<version>.sh | sh)
# Termux : installe Alpine Linux (proot) puis relance ce script à l'intérieur.
# Linux : Debian, Ubuntu, Alpine, Fedora, Arch, openSUSE et dérivés.
set -eu
REPO="https://github.com/matglitch-974/abc"
BRANCH="${ABC_BRANCH:-${BCAI_BRANCH:-main}}"   # BCAI_BRANCH : ancien nom, encore lu
CLI="${ABC_CLI:-agent}"   # nom de la commande de Claude Code ; ABC_CLI=claude garde le nom d'origine
RAW="https://raw.githubusercontent.com/matglitch-974/abc/$BRANCH"
DEST="$HOME/ai/2-tools/3-software/abc"
OLD_DESTS="$HOME/ai/2-tools/3-software/bcai $HOME/ai/2-tools/3-software/better-claude-instance"   # avant ABC (BCAI, BCI)

say() { printf '\n==> %s\n' "$1"; }

# --- Android (Termux) -------------------------------------------------------
# (garde /etc/alpine-release : sous proot, les chemins et le PATH de Termux peuvent rester visibles)
if [ ! -f /etc/alpine-release ] && { [ -n "${TERMUX_VERSION:-}" ] || [ -d /data/data/com.termux/files/usr ]; } && command -v pkg >/dev/null 2>&1; then
  say "Termux détecté : installation d'Alpine Linux"
  pkg install -y proot-distro
  rm -rf "$HOME/.claude/downloads"   # restes d'un essai natif (binaire incompatible avec Android)
  # Test par entrée réelle : l'emplacement des conteneurs change selon la version de proot-distro.
  proot-distro login alpine -- true >/dev/null 2>&1 || proot-distro install alpine
  # Le nom de l'installateur porte la version : lue dans VERSION, sur la même branche.
  V=$(curl -fsSL "$RAW/VERSION")
  proot-distro login alpine -- sh -c "apk add --no-cache curl && curl -fsSL '$RAW/ABC-install-$V.sh' | ABC_BRANCH='$BRANCH' ABC_CLI='$CLI' sh"
  # Alias côté Termux ; celui d'avant ABC (alias claude) appellerait une commande renommée.
  if [ "$CLI" != claude ] && grep -qx "alias claude='proot-distro login alpine -- sh -lc claude'" "$HOME/.bashrc" 2>/dev/null; then
    cp "$HOME/.bashrc" "$HOME/.bashrc.bak-abc-$(date +%Y-%m-%d_%H-%M-%S)"
    sed -i "/^alias claude='proot-distro login alpine -- sh -lc claude'\$/d" "$HOME/.bashrc"
  fi
  grep -q "alias $CLI=" "$HOME/.bashrc" 2>/dev/null || \
    echo "alias $CLI='proot-distro login alpine -- sh -lc $CLI'" >> "$HOME/.bashrc"
  # abc côté Termux : exécutée dans Alpine, arguments transmis tels quels
  printf '#!/bin/sh\nexec proot-distro login alpine -- sh -lc '"'"'abc "$@"'"'"' abc "$@"\n' > "$PREFIX/bin/abc"
  chmod +x "$PREFIX/bin/abc"
  # bcai, bci : anciens noms, renvois vers abc pendant une version, là où ils étaient installés
  for old in bcai bci; do
    [ -e "$PREFIX/bin/$old" ] || continue
    printf '#!/bin/sh\necho "%s est devenu abc : utilisez abc" >&2\nexec abc "$@"\n' "$old" > "$PREFIX/bin/$old"
    chmod +x "$PREFIX/bin/$old"
  done
  say "Terminé. Fermez puis rouvrez Termux, puis tapez : $CLI   (Claude Code ; mises à jour : abc install)"
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

# restic : sauvegardes dédupliquées (>= 0.17 ; sinon abc-backup.py se replie sur tar.xz). Non bloquant.
{ if   command -v apk     >/dev/null 2>&1; then $SUDO apk add --no-cache restic
  elif command -v apt-get >/dev/null 2>&1; then $SUDO apt-get install -y -qq restic
  elif command -v dnf     >/dev/null 2>&1; then $SUDO dnf install -y restic
  elif command -v pacman  >/dev/null 2>&1; then $SUDO pacman -S --noconfirm --needed restic
  elif command -v zypper  >/dev/null 2>&1; then $SUDO zypper --non-interactive install restic
  fi; } || echo "ATTENTION : restic non installé (sauvegardes en tar.xz)" >&2

N="$HOME/.local/bin"   # emplacement de l'installateur natif
is_cc() { "$1" --version 2>/dev/null | head -n 1 | grep -q 'Claude Code'; }
if ! command -v claude >/dev/null 2>&1 && [ ! -x "$N/claude" ] && ! { [ -x "$N/$CLI" ] && is_cc "$N/$CLI"; }; then
  say "Installation de Claude Code (installateur officiel)"
  curl -fsSL https://claude.ai/install.sh | bash
fi

# --- Commande agent : le lien ~/.local/bin/claude est renommé -------------------------------
# Un claude neuf (mise à jour, réinstallation) remplace l'agent précédent, rangé dans 4-trash.
# Un agent qui n'est pas Claude Code (CLI de Cursor, installé lui aussi en ~/.local/bin/agent) n'est jamais touché.
if [ "$CLI" != claude ] && { [ -e "$N/claude" ] || [ -L "$N/claude" ]; }; then
  if [ -e "$N/$CLI" ] && ! is_cc "$N/$CLI"; then
    echo "ATTENTION : $N/$CLI existe et n'est pas Claude Code (CLI de Cursor ?) : la commande reste claude (autre nom : ABC_CLI=<nom>)" >&2
  else
    if [ -e "$N/$CLI" ] || [ -L "$N/$CLI" ]; then
      mkdir -p "$HOME/ai/4-trash"
      mv "$N/$CLI" "$HOME/ai/4-trash/${CLI}_$(date +%Y-%m-%d_%H-%M-%S)" && echo "rangé    : ancien $N/$CLI -> 4-trash"
    fi
    mv "$N/claude" "$N/$CLI" && echo "commande : claude -> $CLI ($N/$CLI)"
  fi
fi
export ABC_CLI="$CLI"   # bootstrap.sh

say "Téléchargement d'ABC"
# Installation d'avant ABC (bcai, ou better-claude-instance) : le dossier est renommé ; un lien reste à l'ancien
# emplacement pour les sessions ouvertes, qui appellent encore les hooks par là (retiré ensuite par memory-hook.py).
for OLD_DEST in $OLD_DESTS; do
  if [ -d "$OLD_DEST" ] && [ ! -L "$OLD_DEST" ] && [ ! -e "$DEST" ]; then
    mv "$OLD_DEST" "$DEST" && ln -s "$DEST" "$OLD_DEST" && echo "renommé  : $OLD_DEST -> $DEST"
  fi
done
if [ -d "$DEST/.git" ]; then
  git -C "$DEST" remote set-url origin "$REPO"   # clone d'un ancien dépôt (bcai, better-claude-instance) : nouvelle adresse
  git -C "$DEST" pull -q --ff-only
else
  mkdir -p "$(dirname "$DEST")"
  git clone -q --depth 1 -b "$BRANCH" "$REPO" "$DEST"
fi

sh "$DEST/bootstrap.sh"
say "Terminé. Ouvrez un nouveau terminal, puis tapez : $CLI   (Claude Code ; mises à jour : abc install)"
