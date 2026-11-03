#!/usr/bin/env bash
# Génère une liste d'ennemis en parallèle (4 processus Blender).
#   bash src/run_batch.sh "igloo:glace igloo:feu ..." [options passées à generate.py]
cd "$(dirname "$0")/.."
JOBS="$1"; shift
mkdir -p .logs
printf '%s\n' $JOBS | xargs -P "${W3_JOBS:-4}" -I{} bash -c '
  f=${1%%:*}; e=${1##*:}
  blender -b --factory-startup -q --python-exit-code 1 -P src/generate.py -- "$f" "$e" '"$*"' > ".logs/$f-$e.log" 2>&1 \
    && grep "\[w3\]" ".logs/$f-$e.log" || echo "ECHEC $f $e (voir .logs/$f-$e.log)"' _ {}
