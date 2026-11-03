"""Table basse en bois avec une tasse : modèle d'exemple, qui sert aussi de test du pipeline."""
import math

import bmesh
import bpy

from helpers import assign, bevel, material, smooth

wood = material("Bois", (0.32, 0.17, 0.08), roughness=0.55)
metal = material("Métal noir", (0.02, 0.02, 0.02), roughness=0.35, metallic=1.0)
ceramic = material("Céramique", (0.75, 0.22, 0.12), roughness=0.2)

L, W, H, T = 1.10, 0.60, 0.42, 0.04  # longueur, profondeur, hauteur totale, épaisseur du plateau (m)

# Plateau
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, H - T / 2))
top = bpy.context.object
top.name = "Plateau"
top.scale = (L, W, T)
bpy.ops.object.transform_apply(scale=True)
bevel(top, width=0.008)
assign(top, wood)

# Pieds
for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=H - T, vertices=24,
                                        location=(sx * (L / 2 - 0.07), sy * (W / 2 - 0.07), (H - T) / 2))
    leg = bpy.context.object
    leg.name = f"Pied.{i + 1}"
    smooth(leg)
    assign(leg, metal)

# Tasse : cylindre ouvert en haut + épaisseur + anse
mx, my, mh = 0.25, -0.05, 0.09
bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=mh, vertices=48, location=(mx, my, H + mh / 2))
mug = bpy.context.object
mug.name = "Tasse"
bm = bmesh.new()
bm.from_mesh(mug.data)
bm.normal_update()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context="FACES_ONLY")
bm.to_mesh(mug.data)
bm.free()
mug.modifiers.new("Épaisseur", "SOLIDIFY").thickness = 0.004
smooth(mug)
assign(mug, ceramic)

bpy.ops.mesh.primitive_torus_add(major_radius=0.025, minor_radius=0.006,
                                 location=(mx + 0.042, my, H + mh / 2), rotation=(math.pi / 2, 0, 0))
handle = bpy.context.object
handle.name = "Anse"
smooth(handle)
assign(handle, ceramic)
