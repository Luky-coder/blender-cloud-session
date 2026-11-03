"""Monde 2 « Le Désert des Ballons Perdus » : planche de présentation des 23 ennemis gonflables (21 mobs en
7 types élémentaires, le mini-boss Scaraballon et le boss Grand Ballon Oasis), posés en rangs, avant vers +Y.
Les fichiers de jeu (23 .blend animés + 23 FBX) sont produits par export_all.py dans World_2_Desert/ :
ce .blend-ci n'est qu'une vitrine sans animations.
"""
import math
import os
import sys
import tempfile

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from desert import family  # noqa: E402
from desert import airship, cactus, oasis, pyramid, scarab  # noqa: E402
from desert.elements import ORDER  # noqa: E402

def idle_pose(fam, rig):
    """Pose fixe = image 1 de l'Idle (cache aussi les accessoires d'attaque des boss)."""
    pose = fam.actions()[0][2](0)
    for s in ("Degonfle", "Gonfle"):
        pose.add("CTRL_" + s, loc=(pose.shapes.get(s, 0.0), 0, 0))
    for pb in rig.pose.bones:
        d = pose.get(pb.name)
        if d:
            pb.location, pb.rotation_euler, pb.scale = d["loc"], d["rot"], d["scl"]


tmp = tempfile.mkdtemp()
refs = {}
for fam in (cactus.FAMILY, pyramid.FAMILY, airship.FAMILY, scarab.FAMILY, oasis.FAMILY):
    refs[fam.key] = family.build_reference(fam, os.path.join(tmp, fam.key + ".blend"))

family.reset_scene()
layout = [(cactus.FAMILY, ORDER, 0.0, 2.0), (pyramid.FAMILY, ORDER, -2.8, 2.2), (airship.FAMILY, ORDER, -6.2, 3.1)]
for fam, elems, y, dx in layout:
    for i, e in enumerate(elems):
        rig, mesh, key, acts = family.assemble(fam, e, refs[fam.key], animate=False)
        idle_pose(fam, rig)
        rig.location = ((i - 3) * dx, y, 0.0)
rig, *_ = family.assemble(scarab.FAMILY, "Plante", refs[scarab.FAMILY.key], animate=False)
idle_pose(scarab.FAMILY, rig)
rig.location = (-7.5, -11.0, 0.0)
rig, *_ = family.assemble(oasis.FAMILY, "Plante", refs[oasis.FAMILY.key], animate=False)
idle_pose(oasis.FAMILY, rig)
rig.location = (4.5, -15.0, -0.5)
rig.rotation_euler = (0.0, 0.0, -math.pi / 2)  # le boss de profil, nez vers +X, derrière les rangs
bpy.context.view_layer.update()
