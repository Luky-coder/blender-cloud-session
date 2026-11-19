#!/usr/bin/env bash
# Exporte les 23 ennemis pour Roblox (World_3_Glace/Roblox) puis vérifie chaque export.
cd "$(dirname "$0")/.."
R=World_3_Glace/Roblox
rm -rf "$R"; mkdir -p "$R" .logs
{
  for fam in Ballon_Igloo Ballon_Flocon Dirigeable_Polaire; do
    for e in Lumiere Tenebres Glace Feu Eau Plante Eclair; do
      echo "World_3_Glace/Blender/$fam/$e.blend $R/$fam/$e 0"
    done
  done
  echo "World_3_Glace/Blender/MiniBoss_Pin_Gonflable_Eau.blend $R/Boss/MiniBoss_Pin_Gonflable_Eau 0"
  echo "World_3_Glace/Blender/Boss_Gardien_Glaciers_Glace.blend $R/Boss/Boss_Gardien_Glaciers_Glace 0"
} | xargs -P 4 -L 1 bash -c '
  log=".logs/roblox_$(echo $1 | tr / _).log"
  blender -b "$0" --python-exit-code 1 -q -P src/roblox_export.py -- "$1" "$2" > "$log" 2>&1 \
    && blender -b --factory-startup -q -P src/roblox_check.py -- "$1" >> "$log" 2>&1 \
    && echo "$(grep "\[roblox\]" "$log") | vérif : $(grep "\[rbx\] OK\|\[rbx\] ERREURS" "$log")" || echo "ECHEC $1 (voir $log)"'
cp src/LISEZMOI_ROBLOX.md "$R/LISEZMOI_ROBLOX.md"
