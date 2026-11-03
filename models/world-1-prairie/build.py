"""Monde 1 « La Prairie » : les 23 ennemis gonflables réunis dans une scène de présentation (sans animations).

Rangées de devant à l'arrière : 7 Ballons Classiques, 7 Ballons Étoile, 7 Mini-dirigeables (Lumière, Ténèbres,
Glace, Feu, Eau, Plante, Éclair), puis la Montgolfière Solaire (mini-boss) et le Grand Zeppelin des Prairies (boss).
Les modèles individuels animés (.blend, FBX) et leurs aperçus sont dans World_1_Prairie/ (générés par export.py).
"""
import os
import sys

from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prairie import enemy  # noqa: E402

ORDER = ["lumiere", "tenebres", "glace", "feu", "eau", "plante", "eclair"]
ROWS = [("classique", 1.15, 3.2), ("etoile", 1.15, 1.6), ("dirigeable", 1.9, -0.6)]

for family, step, y in ROWS:
    for i, el in enumerate(ORDER):
        enemy.build_enemy(family, el, with_anims=False, offset=Vector(((3 - i) * step, y, 0)))
enemy.build_enemy("montgolfiere", with_anims=False, offset=Vector((6.2, -5.0, 0)))
enemy.build_enemy("zeppelin", with_anims=False, offset=Vector((-3.2, -7.5, 0)))
