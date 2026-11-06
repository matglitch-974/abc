#!/bin/sh
# Ancien nom de l'installateur (BCAI). Renvoi pendant la version 0.4, retiré ensuite : ABC-install-<version>.sh.
set -eu
B="${ABC_BRANCH:-${BCAI_BRANCH:-main}}"
V=$(curl -fsSL "https://raw.githubusercontent.com/matglitch-974/abc/$B/VERSION")
curl -fsSL "https://raw.githubusercontent.com/matglitch-974/abc/$B/ABC-install-$V.sh" | sh -s -- "$@"
