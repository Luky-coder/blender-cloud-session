"""Monde 3 « Le Royaume Givré » : modèle de référence, le Ballon Igloo Glace (rig et 5 animations).
Les 23 ennemis (3 familles × 7 types, mini-boss Pin Gonflable, boss Gardien des Glaciers) sont dans
`World_3_Glace/` (.blend, .fbx, aperçus) ; voir `World_3_Glace/RAPPORT.md`. Avant du modèle vers +Y."""
import os
import sys

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import fam_igloo  # noqa: E402
import w3lib as L  # noqa: E402

m, actions = fam_igloo.build("glace")
for name, (n, loop, fn) in actions.items():
    L.bake_action(m.rig, name, n, fn, loop)
L.set_action(m.rig, bpy.data.actions["IDLE"])
bpy.context.scene.render.fps = 30
bpy.context.scene.frame_set(1)
