"""Couleurs exportables : texture palette + UV + couleurs de sommets.

Les moteurs de jeu ignorent souvent la couleur « Diffuse » des matériaux FBX. On écrit donc la couleur de chaque
matériau dans une petite texture palette (une case de 8 px par matériau), on place les UV de chaque face au centre
de la case de son matériau, et on branche la texture sur la Base Color de tous les matériaux. On ajoute aussi un
attribut de couleur par coin (« Couleur ») pour les shaders qui lisent les couleurs de sommets.
"""
import os

import bpy

CELL = 8
COLS = 16  # 16 x 16 cases -> 128 x 128 px, 256 matériaux maximum


def _to_srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def bake(mesh, name, png_path):
    """Crée la palette `name`, l'enregistre en PNG et l'applique au maillage. Renvoie l'image."""
    me = mesh.data
    mats = list(me.materials)
    size = CELL * COLS
    px = [1.0] * (size * size * 4)
    cols = []
    for i, m in enumerate(mats):
        c = _bsdf(m).inputs["Base Color"].default_value
        srgb = [min(max(_to_srgb(c[k]), 0.0), 1.0) for k in range(3)]
        cols.append(srgb)
        cx, cy = (i % COLS) * CELL, (i // COLS) * CELL
        for y in range(cy, cy + CELL):
            for x in range(cx, cx + CELL):
                o = (y * size + x) * 4
                px[o:o + 3] = srgb
    img = bpy.data.images.new(name, size, size, alpha=False)
    img.pixels.foreach_set(px)
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    img.filepath_raw = png_path
    img.file_format = "PNG"
    img.save()

    # UV : chaque face au centre de la case de son matériau
    uv = me.uv_layers.new(name="UVMap")
    co = [0.0] * (len(me.loops) * 2)
    col = me.color_attributes.new("Couleur", "BYTE_COLOR", "CORNER")
    cc = [1.0] * (len(me.loops) * 4)
    for p in me.polygons:
        i = p.material_index
        u = ((i % COLS) * CELL + CELL / 2) / size
        v = ((i // COLS) * CELL + CELL / 2) / size
        r, g, b = cols[i] if i < len(cols) else (1, 1, 1)
        for li in p.loop_indices:
            co[2 * li], co[2 * li + 1] = u, v
            cc[4 * li:4 * li + 3] = (r, g, b)
    uv.data.foreach_set("uv", co)
    # BYTE_COLOR attend des valeurs sRGB via .color_srgb
    col.data.foreach_set("color_srgb", cc)
    me.color_attributes.active_color = col

    # Texture branchée sur la Base Color (filtrage « Closest » : couleurs exactes)
    for m in mats:
        nt = m.node_tree
        b = _bsdf(m)
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.name = tex.label = "Palette"
        tex.image = img
        tex.interpolation = "Closest"
        tex.location = (b.location.x - 320, b.location.y)
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    return img
