#!/bin/sh
# publish.sh — prépare la publication de la version inscrite dans VERSION (fichiers indexés, ni commit ni push).
#   sh publish.sh [dossier du dépôt Pages]   (défaut : $ABC_PAGES_DIR, sinon ../matglitch-974.github.io)
# 1. Installateurs du dépôt nommés d'après VERSION : ABC-install-<version>.ps1 et .sh (renommés par git mv
#    s'ils portent encore une autre version).
#    Les commandes de secours de README, SETUP et docs/ (adresse complète) suivent la version.
# 2. Dépôt Pages : abc.ps1 et abc visent ces installateurs ; bc, bc.ps1, BCAI, BCAI.ps1, BCI, BCI.ps1
#    (anciens liens courts) sont des alias au contenu identique. Lien court = toujours la dernière version.
# Ordre de publication : pousser d'abord ce dépôt (sinon le lien court vise un fichier encore absent), puis Pages.
set -eu
SRC="$(cd "$(dirname "$0")" && pwd)"
PAGES="${1:-${ABC_PAGES_DIR:-$SRC/../matglitch-974.github.io}}"
RAW="https://raw.githubusercontent.com/matglitch-974/abc/main"
V=$(tr -d ' \r\n' < "$SRC/VERSION")
case "$V" in ''|*[!0-9.]*) echo "VERSION invalide : « $V »" >&2; exit 1 ;; esac
[ -d "$PAGES/.git" ] || { echo "Dépôt Pages introuvable : $PAGES (git clone https://github.com/matglitch-974/matglitch-974.github.io)" >&2; exit 1; }

# --- 1. Installateurs versionnés ------------------------------------------------------------
for ext in ps1 sh; do
  want="ABC-install-$V.$ext"
  [ -f "$SRC/$want" ] && continue
  set -- "$SRC"/ABC-install-*."$ext"
  [ $# -eq 1 ] && [ -f "$1" ] || { echo "Un seul ABC-install-*.$ext attendu dans $SRC" >&2; exit 1; }
  git -C "$SRC" mv "$(basename "$1")" "$want"
  echo "renommé  : $(basename "$1") -> $want"
done
# Commandes de secours de la documentation : adresse complète de l'installateur de cette version.
for f in "$SRC/README.md" "$SRC/SETUP.md" "$SRC"/docs/*.md; do
  sed -i -E "s/ABC-install-[0-9]+(\.[0-9]+)*\.(ps1|sh)/ABC-install-$V.\2/g" "$f"
done
git -C "$SRC" add README.md SETUP.md docs

# --- 2. Liens courts (GitHub Pages) -----------------------------------------------------------
# .ps1 : une seule ligne, sans BOM (exécutée par irm | iex).
ps1="irm $RAW/ABC-install-$V.ps1 | iex"
sh_relay() {
  printf '#!/bin/sh\n# %s\ncurl -fsSL %s/ABC-install-%s.sh | sh\n' "$1" "$RAW" "$V"
}
printf '%s\n' "$ps1" > "$PAGES/abc.ps1"
sh_relay "Relais vers l'installateur d'ABC (Agents with a Better Context), version $V." > "$PAGES/abc"
for old in bc BCAI BCI; do
  printf '%s\n' "$ps1" > "$PAGES/$old.ps1"
  sh_relay "Ancien lien court, alias de abc : installateur d'ABC, version $V." > "$PAGES/$old"
done
chmod +x "$PAGES/abc" "$PAGES/bc" "$PAGES/BCAI" "$PAGES/BCI"
git -C "$PAGES" add -A
git -C "$PAGES" diff --cached --quiet && echo "Pages    : déjà à jour (version $V)" || git -C "$PAGES" diff --cached --stat
echo "Ensuite : committer les deux dépôts, pousser celui-ci, puis le dépôt Pages ($PAGES)."
