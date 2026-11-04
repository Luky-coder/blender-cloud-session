"""Un seul matériau par ennemi : couleurs, lueurs, rugosité et métal lus dans des textures palette.

Pourquoi : plusieurs moteurs (Roblox notamment) découpent un maillage multi-matériaux en pièces séparées, et
beaucoup ignorent la couleur « Diffuse » des matériaux FBX. Chaque ancien matériau devient une case de 8 px dans :
    <Ennemi>_Palette.png            couleur de base (sRGB)            -> Base Color (incrustée dans le FBX)
    <Ennemi>_Palette_Emission.png   lueurs (halos, flammes, coutures) -> Emission Color
    <Ennemi>_Palette_RM.png         R = rugosité, G = métal (données)  -> Roughness / Metallic
Les UV de chaque face pointent sur le centre de la case de son ancien matériau. On garde aussi un attribut de
couleurs de sommets (« Couleur ») pour les shaders qui les lisent.
"""
import os

import bpy

from .materials import mat

CELL = 8
COLS = 16  # 16 x 16 cases -> 128 x 128 px, 256 anciens matériaux maximum
EMIT_MAX = 8.0


def _to_srgb(c):
    c = max(c, 0.0)
    return min(12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055, 1.0)


def _bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def _image(name, size, cells, path, data=False):
    px = [0.0] * (size * size * 4)
    for i in range(size * size):
        px[4 * i + 3] = 1.0
    for i, rgb in enumerate(cells):
        cx, cy = (i % COLS) * CELL, (i // COLS) * CELL
        for y in range(cy, cy + CELL):
            for x in range(cx, cx + CELL):
                o = (y * size + x) * 4
                px[o:o + 3] = rgb
    img = bpy.data.images.new(name, size, size, alpha=False, is_data=data)
    img.pixels.foreach_set(px)
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    if data:
        img.colorspace_settings.name = "Non-Color"
    return img


def bake(mesh, name, png_path):
    """Remplace tous les matériaux du maillage par un matériau unique à textures palette. Renvoie les images."""
    me = mesh.data
    mats = list(me.materials)
    size = CELL * COLS
    base, emit, rm = [], [], []
    for m in mats:
        b = _bsdf(m)
        c = b.inputs["Base Color"].default_value
        base.append([_to_srgb(c[k]) for k in range(3)])
        e = b.inputs["Emission Color"].default_value
        s = b.inputs["Emission Strength"].default_value / EMIT_MAX
        emit.append([_to_srgb(e[k] * s) for k in range(3)])
        rough = b.inputs["Roughness"].default_value
        if b.inputs["Transmission Weight"].default_value > 0.5:
            rough = min(rough, 0.08)  # verre / glace / bulles : très lisse
        rm.append([rough, b.inputs["Metallic"].default_value, 0.0])
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    stem = os.path.splitext(png_path)[0]
    img = _image(name, size, base, png_path)
    img_e = _image(name + "_Emission", size, emit, stem + "_Emission.png")
    img_rm = _image(name + "_RM", size, rm, stem + "_RM.png", data=True)

    # UV : chaque face au centre de la case de son ancien matériau ; couleurs de sommets
    uv = me.uv_layers.new(name="UVMap")
    co = [0.0] * (len(me.loops) * 2)
    col = me.color_attributes.new("Couleur", "BYTE_COLOR", "CORNER")
    cc = [1.0] * (len(me.loops) * 4)
    for p in me.polygons:
        i = p.material_index
        u = ((i % COLS) * CELL + CELL / 2) / size
        v = ((i // COLS) * CELL + CELL / 2) / size
        r, g, bl = base[i] if i < len(base) else (1, 1, 1)
        for li in p.loop_indices:
            co[2 * li], co[2 * li + 1] = u, v
            cc[4 * li:4 * li + 3] = (r, g, bl)
    uv.data.foreach_set("uv", co)
    col.data.foreach_set("color_srgb", cc)
    me.color_attributes.active_color = col

    # Matériau unique
    m = mat(name.replace("_Palette", "") + "_Materiau", "#FFFFFF", rough=0.3, coat=0.6)
    nt = m.node_tree
    b = _bsdf(m)

    def tex(image, y):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = image
        t.interpolation = "Closest"
        t.location = (b.location.x - 600, b.location.y + y)
        return t

    t_base, t_emit, t_rm = tex(img, 300), tex(img_e, -300), tex(img_rm, 0)
    t_base.label = "Palette couleur"
    t_emit.label = "Palette lueurs"
    t_rm.label = "Palette rugosité / métal"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    sep.location = (b.location.x - 300, b.location.y)
    nt.links.new(t_base.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t_rm.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Red"], b.inputs["Roughness"])
    nt.links.new(sep.outputs["Green"], b.inputs["Metallic"])
    nt.links.new(t_emit.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = EMIT_MAX
    me.materials.clear()
    me.materials.append(m)
    for p in me.polygons:
        p.material_index = 0
    for old in mats:
        if old.users == 0:
            bpy.data.materials.remove(old)
    return [img, img_e, img_rm]
