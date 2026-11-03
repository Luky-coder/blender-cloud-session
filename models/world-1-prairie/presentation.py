"""Rendu de présentation générale des 23 ennemis (à partir de la scène world-1-prairie.blend).

    blender -b --factory-startup models/world-1-prairie/world-1-prairie.blend -P models/world-1-prairie/presentation.py
Écrit World_1_Prairie/Previews/Presentation_Monde1.jpg (le .blend n'est pas réenregistré).
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from prairie import render  # noqa: E402

meshes = [o for o in bpy.data.objects if o.type == "MESH"]
lo, hi = render._bounds(meshes)
render.setup(1800, 1000, 64, ground_z=0.0)
render.camera("presentation", lo, hi, 18, 16, lens=40, margin=1.02)
render.render_to(os.path.join(HERE, "World_1_Prairie", "Previews", "Presentation_Monde1.jpg"))
