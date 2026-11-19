"""Couleurs « transportables » : un seul matériau par ennemi, piloté par une texture-palette.

Chaque matériau de rôle (corps, couture, or, ...) devient une case de 32 px dans une image 256 x 128 ;
les UV de chaque face sont posées au centre de la case de son matériau. Mêmes couleurs en couleurs de
sommets (attribut « Couleur »). Cartes de rugosité et de métal assorties (aspect plastique brillant, or).
Les couleurs arrivent ainsi dans n'importe quel moteur (Roblox, Unity, Unreal, Godot) via le FBX.
"""
import os

import bpy

COLS, ROWS, CELL = 8, 4, 32


def _bsdf(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def values(mat):
    b = _bsdf(mat)
    col = list(b.inputs["Base Color"].default_value)[:3]
    if b.inputs["Emission Strength"].default_value > 0.5:  # lumineux : couleur éclaircie (pas d'émission en jeu)
        ec = list(b.inputs["Emission Color"].default_value)[:3]
        col = [min(1.0, c * 0.6 + e * 0.5) for c, e in zip(col, ec)]
    return col, b.inputs["Roughness"].default_value, b.inputs["Metallic"].default_value


def cell_uv(i):
    cx, cy = i % COLS, i // COLS
    return ((cx + 0.5) / COLS, 1.0 - (cy + 0.5) / ROWS)


def images(name, mats, folder):
    w, h = COLS * CELL, ROWS * CELL
    out = {}
    os.makedirs(folder, exist_ok=True)
    for kind in ("Couleur", "Rugosite", "Metal"):
        px = [0.0] * (w * h * 4)
        for i, m in enumerate(mats):
            col, rough, metal = values(m)
            val = col if kind == "Couleur" else ([rough] * 3 if kind == "Rugosite" else [metal] * 3)
            cx, cy = i % COLS, i // COLS
            for y in range(CELL):
                row = (h - 1 - (cy * CELL + y)) * w
                for x in range(CELL):
                    k = (row + cx * CELL + x) * 4
                    px[k:k + 4] = [val[0], val[1], val[2], 1.0]
        img = bpy.data.images.new(f"{name}_{kind}", w, h, alpha=False)
        if kind != "Couleur":
            img.colorspace_settings.name = "Non-Color"
        img.pixels.foreach_set(px)
        img.filepath_raw = os.path.join(folder, f"{name}_{kind}.png")
        img.file_format = "PNG"
        img.save()
        out[kind] = img
    return out


def material(name, imgs):
    mat = bpy.data.materials.new(name + "_Palette")
    nt = mat.node_tree
    bsdf = _bsdf(mat)
    for kind, socket in (("Couleur", "Base Color"), ("Rugosite", "Roughness"), ("Metal", "Metallic")):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = imgs[kind]
        tex.interpolation = "Closest"
        tex.location = (-400, {"Couleur": 300, "Rugosite": 0, "Metal": -300}[kind])
        nt.links.new(tex.outputs["Color"], bsdf.inputs[socket])
    bsdf.inputs["Coat Weight"].default_value = 0.4
    bsdf.inputs["Coat Roughness"].default_value = 0.08
    return mat


def apply(ob, name, folder):
    """Remplace les matériaux de rôle de `ob` par le matériau-palette. Renvoie les images."""
    me = ob.data
    src = [m for m in me.materials if m]
    imgs = images(name, src, folder)
    mat = material(name, imgs)
    for uv in list(me.uv_layers):
        me.uv_layers.remove(uv)
    uvl = me.uv_layers.new(name="UVPalette")
    ca = me.color_attributes.new("Couleur", "BYTE_COLOR", "CORNER")
    cols = [values(m)[0] for m in src]
    for p in me.polygons:
        cell = min(p.material_index, len(src) - 1)
        u, v = cell_uv(cell)
        c = cols[cell]
        for li in p.loop_indices:
            uvl.data[li].uv = (u, v)
            ca.data[li].color = (c[0], c[1], c[2], 1.0)
    me.materials.clear()
    me.materials.append(mat)
    for p in me.polygons:
        p.material_index = 0
    me.color_attributes.active_color = ca
    for img in imgs.values():
        img.pack()
    for m in src:
        if m.users == 0:
            bpy.data.materials.remove(m)
    return imgs
