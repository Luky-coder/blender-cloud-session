"""Export Roblox des 25 ennemis du Monde 2, à partir des .blend de World_2_Desert/Blender.

    blender -b --factory-startup --python-exit-code 1 -P models/monde2-desert/export_roblox.py

Contraintes Roblox prises en compte :
- un seul matériau par MeshPart -> une texture-palette par ennemi (une case de couleur par matériau
  d'origine, UV de chaque face au centre de sa case) + les mêmes couleurs en couleurs de sommets ;
  cartes Rugosité / Métal assorties pour une SurfaceAppearance (aspect plastique brillant) ;
- pas d'échelle d'os dans les animations -> chaque action est recalculée sans échelle : la pose de chaque
  os (position + rotation) reproduit la pose d'origine, le squash vertical passe par le déplacement des os ;
  la disparition finale de la mort devient un enfoncement dans le sol ;
- pas de blendshapes hors tête -> shape keys retirées (le dégonflage passe par les os) ;
- une seule animation par FBX -> un FBX par animation (armature seule), plus un FBX modèle (rig + maillage) ;
- 20 000 triangles max par maillage, 4 os max par sommet, pas d'os feuilles, os de repos sans rotation
  ni échelle ;
- accessoires d'attaque des boss (racines, noix de coco, vague, tornade, cactus) : maillages séparés,
  à faire apparaître et à animer par script (usage normal sur Roblox).
Sortie : World_2_Desert/Roblox/<Famille>/<Type>/ ou World_2_Desert/Roblox/<Boss>/
"""
import glob
import math
import os
import re
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "World_2_Desert")
RBX = os.path.join(OUT, "Roblox")
PROP_RE = re.compile(r"^(Roots_\d+|Coco_\d+|SandWave|Tornado_\d+|Cactus_\d+)$")
PROP_EXPORT = {"Roots_2": "Prop_Racine", "Coco_1": "Prop_NoixDeCoco", "SandWave": "Prop_VagueDeSable",
               "Tornado_1": "Prop_Tornade", "Cactus_2": "Prop_CactusSurgissant"}
COLS, ROWS, CELL = 8, 4, 32   # palette 256 x 128 px


def srgb(c):
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def bsdf_of(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def mat_values(mat):
    b = bsdf_of(mat)
    col = list(b.inputs["Base Color"].default_value)[:3]
    em = b.inputs["Emission Strength"].default_value
    if em > 0.5:  # matériau lumineux : Roblox n'a pas d'émission sur MeshPart, on éclaircit la couleur
        ec = list(b.inputs["Emission Color"].default_value)[:3]
        col = [min(1.0, c * 0.6 + e * 0.5) for c, e in zip(col, ec)]
    return col, b.inputs["Roughness"].default_value, b.inputs["Metallic"].default_value


def cell_uv(i):
    cx, cy = i % COLS, i // COLS
    return ((cx + 0.5) / COLS, 1.0 - (cy + 0.5) / ROWS)


def palette_images(name, mats, folder):
    """3 images (couleur, rugosité, métal) : une case par matériau d'origine."""
    w, h = COLS * CELL, ROWS * CELL
    out = {}
    for kind in ("Couleur", "Rugosite", "Metal"):
        px = [0.0] * (w * h * 4)
        for i, m in enumerate(mats):
            col, rough, metal = mat_values(m)
            if kind == "Couleur":
                val = col
            elif kind == "Rugosite":
                val = [rough] * 3
            else:
                val = [metal] * 3
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
        path = os.path.join(folder, f"{name}_{kind}.png")
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        out[kind] = img
    return out


def palette_material(name, imgs):
    mat = bpy.data.materials.new(name + "_Palette")
    nt = mat.node_tree
    bsdf = bsdf_of(mat)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = imgs["Couleur"]
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.3
    bsdf.inputs["Coat Weight"].default_value = 0.0
    return mat


def apply_palette(ob, src_mats, mat):
    """UV de chaque face -> centre de la case de son matériau ; couleurs de sommets ; matériau unique."""
    me = ob.data
    for uv in list(me.uv_layers):
        me.uv_layers.remove(uv)
    uvl = me.uv_layers.new(name="UVPalette")
    ca = me.color_attributes.new("Couleur", "BYTE_COLOR", "CORNER")
    slot_to_cell = {}
    for si, m in enumerate(me.materials):
        slot_to_cell[si] = src_mats.index(m) if m in src_mats else 0
    cols = [mat_values(m)[0] for m in src_mats]
    for p in me.polygons:
        cell = slot_to_cell.get(p.material_index, 0)
        u, v = cell_uv(cell)
        c = cols[cell]
        for li in p.loop_indices:
            uvl.data[li].uv = (u, v)
            ca.data[li].color = (c[0], c[1], c[2], 1.0)
    me.materials.clear()
    me.materials.append(mat)
    for p in me.polygons:
        p.material_index = 0


def separate_props(rig, mesh):
    """Détache la géométrie des accessoires (os d'accessoire) ; renvoie {os: objet} en pose de repos."""
    props = {}
    names = [g.name for g in mesh.vertex_groups if PROP_RE.match(g.name)]
    for gname in names:
        gi = mesh.vertex_groups[gname].index
        ids = {v.index for v in mesh.data.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups)}
        if not ids:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = mesh
        mesh.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        for v in mesh.data.vertices:
            v.select = v.index in ids
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.separate(type="SELECTED")
        bpy.ops.object.mode_set(mode="OBJECT")
        new = next(o for o in bpy.context.selected_objects if o != mesh)
        new.name = gname
        new.parent = None
        new.matrix_world = Matrix()
        for mod in list(new.modifiers):
            new.modifiers.remove(mod)
        new.vertex_groups.clear()
        head = rig.data.bones[gname].head_local
        new.data.transform(Matrix.Translation(-head))
        props[gname] = new
    return props


def delete_bones(rig, names):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for n in names:
        eb = rig.data.edit_bones.get(n)
        if eb:
            rig.data.edit_bones.remove(eb)
    bpy.ops.object.mode_set(mode="OBJECT")


def bake_scale_free(rig, act, height, out_name):
    """Recalcule une action sans échelle d'os : position + rotation de chaque os en espace armature."""
    scene = bpy.context.scene
    rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    bones = sorted(rig.pose.bones, key=lambda pb: len(pb.parent_recursive))
    for pb in bones:  # les actions d'origine sont en Euler
        pb.rotation_mode = "XYZ"
    frames = {}
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        root = bones[0]
        s = min(root.scale)
        sink = 0.0
        if s < 0.999:  # disparition par échelle -> enfoncement dans le sol
            sink = height * (1.0 - s) * 1.6
            root.scale = (1.0, 1.0, 1.0)
            bpy.context.view_layer.update()
        targets = {}
        for pb in bones:
            loc, rot, _ = pb.matrix.decompose()
            loc.z -= sink
            targets[pb.name] = Matrix.LocRotScale(loc, rot, None)
        frames[f] = targets
    new = bpy.data.actions.new(out_name)
    rig.animation_data.action = new
    for pb in bones:
        pb.rotation_mode = "QUATERNION"
    prev = {}
    for f in range(f0, f1 + 1):
        T = frames[f]
        for pb in bones:
            b = pb.bone
            if b.parent:
                rel = b.parent.matrix_local.inverted() @ b.matrix_local
                basis = rel.inverted() @ T[b.parent.name].inverted() @ T[b.name]
            else:
                basis = b.matrix_local.inverted() @ T[b.name]
            loc, q, _ = basis.decompose()
            if pb.name in prev and prev[pb.name].dot(q) < 0:
                q = -q
            prev[pb.name] = q
            pb.location = loc
            pb.rotation_quaternion = q
            pb.scale = (1.0, 1.0, 1.0)
            pb.keyframe_insert("location", frame=f, group=pb.name)
            pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
            pb.keyframe_insert("scale", frame=f, group=pb.name)
    new.use_frame_range = True
    new.frame_start, new.frame_end = f0, f1
    new.use_cyclic = act.use_cyclic
    return new


def anim_proxy(rig):
    """Maillage-témoin minuscule (un triangle de 1 mm par os, pondéré à 100 % sur cet os) : sans maillage
    skinné, l'exporteur FBX écrit la pose courante comme pose de repos ; avec lui, la vraie pose de liaison
    (bind pose) est écrite et l'animation se recale sur le rig importé par le 3D Importer."""
    verts, faces, groups = [], [], []
    for b in rig.data.bones:
        h = b.head_local
        i = len(verts)
        verts += [h, h + Vector((0.001, 0, 0)), h + Vector((0, 0, 0.001))]
        faces.append((i, i + 1, i + 2))
        groups.append(b.name)
    me = bpy.data.meshes.new("AnimProxy")
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(rig.name + "_AnimProxy", me)
    bpy.context.scene.collection.objects.link(ob)
    for k, g in enumerate(groups):
        ob.vertex_groups.new(name=g).add([3 * k, 3 * k + 1, 3 * k + 2], 1.0, "REPLACE")
    ob.parent = rig
    ob.modifiers.new("Armature", "ARMATURE").object = rig
    return ob


FBX_COMMON = dict(apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS", add_leaf_bones=False,
                  primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=True,
                  mesh_smooth_type="FACE", use_mesh_modifiers=False, use_custom_props=False)


def export(path, objs, anim=None, types=("ARMATURE", "MESH"), embed=False):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    sc = bpy.context.scene
    if anim:
        sc.frame_start, sc.frame_end = int(anim.frame_range[0]), int(anim.frame_range[1])
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types=set(types),
                             bake_anim=bool(anim), bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                             bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0,
                             use_triangles=True, path_mode="COPY" if embed else "AUTO", embed_textures=embed,
                             **FBX_COMMON)


def process(blend):
    bpy.ops.wm.open_mainfile(filepath=blend)
    rel = os.path.relpath(blend, os.path.join(OUT, "Blender"))[:-6]
    folder = os.path.join(RBX, rel)
    os.makedirs(os.path.join(folder, "Animations"), exist_ok=True)
    rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh = next(o for o in bpy.data.objects if o.type == "MESH")
    name = rig.name
    order = [s for s in rig.get("Actions", "").split(",") if s]
    acts = [bpy.data.actions[f"{name}_{s}"] for s in order]
    for o in [o for o in bpy.data.objects if o not in (rig, mesh)]:
        bpy.data.objects.remove(o)

    # maillage : shape keys retirées (pas de blendshapes hors tête sur Roblox), accessoires détachés
    mesh.data.animation_data_clear() if mesh.data.animation_data else None
    if mesh.data.shape_keys:
        if mesh.data.shape_keys.animation_data:
            mesh.data.shape_keys.animation_data_clear()
        mesh.shape_key_clear()
    src_mats = list(mesh.data.materials)
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.location, pb.rotation_euler, pb.scale = (0, 0, 0), (0, 0, 0), (1, 1, 1)
    props = separate_props(rig, mesh)
    texs = [n.image for m in src_mats for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image]
    if len(src_mats) == 1 and texs:  # matériau-palette déjà en place (pipeline principal) : PNG recopiés
        import shutil
        for img in texs:
            shutil.copy(bpy.path.abspath(img.filepath), os.path.join(folder, img.name + ".png"))
    else:
        imgs = palette_images(name, src_mats, folder)
        pmat = palette_material(name, imgs)
        apply_palette(mesh, src_mats, pmat)
        for o in props.values():
            apply_palette(o, src_mats, pmat)
    mesh.name = name + "_Mesh"
    height = max((rig.matrix_world @ mesh.matrix_world @ v.co).z for v in mesh.data.vertices) + 0.1

    # rig : sans os d'accessoires ni os de contrôle des shape keys
    drop = [b.name for b in rig.data.bones if PROP_RE.match(b.name) or b.name.startswith("CTRL_")]
    delete_bones(rig, drop)
    for vg in [g for g in mesh.vertex_groups if g.name in drop]:
        mesh.vertex_groups.remove(vg)

    # actions recalculées sans échelle (une par FBX)
    clean = []
    for a, s in zip(acts, order):
        clean.append((s, bake_scale_free(rig, a, height, f"{name}_{s}_Roblox")))
    for a in acts:
        bpy.data.actions.remove(a)

    # modèle (rig + maillage, pose de repos), animations (armature seule), accessoires
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.location, pb.rotation_quaternion, pb.scale = (0, 0, 0), (1, 0, 0, 0), (1, 1, 1)
    export(os.path.join(folder, f"{name}.fbx"), [rig, mesh], embed=True)
    proxy = anim_proxy(rig)
    for s, a in clean:
        a.name = f"{name}_{s}"
        rig.animation_data.action = a
        export(os.path.join(folder, "Animations", f"{name}_{s}.fbx"), [rig, proxy], anim=a)
    for bone, label in PROP_EXPORT.items():
        if bone in props:
            ob = props[bone]
            ob.name = label
            export(os.path.join(folder, f"{label}.fbx"), [ob], types=("MESH",), embed=True)
    tris = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
    print(f"[roblox] {rel}: {tris} triangles, {len(rig.data.bones)} os, {len(clean)} animations, "
          f"{len([b for b in PROP_EXPORT if b in props])} accessoires")


README = """# Monde 2 — export Roblox

Une version de chaque ennemi préparée pour Roblox Studio (3D Importer + Animation Editor).
Le contrôle automatique (ré-import de tous les FBX) est dans [VERIFICATION_ROBLOX.md](VERIFICATION_ROBLOX.md),
avec une planche `Apercu_Roblox.jpg` par ennemi rendue à partir des FBX ré-importés.

## Contenu d'un dossier d'ennemi

```
<Nom>.fbx                     modèle : rig + maillage skinné, 1 matériau à texture-palette incluse, <= 20 000 triangles
<Nom>_Couleur.png             texture-palette (couleurs) — aussi présente en couleurs de sommets
<Nom>_Rugosite.png            carte de rugosité (SurfaceAppearance.RoughnessMap)
<Nom>_Metal.png               carte de métal (SurfaceAppearance.MetalnessMap)
Animations/<Nom>_Fly.fbx      vol (en boucle)
Animations/<Nom>_Attack.fbx   attaque (coup physique vers l'avant)
Apercu_Roblox.jpg             images clés rendues depuis les FBX ré-importés
```

## Import dans Roblox Studio

1. **Modèle** : menu *Import 3D*, choisis `<Nom>.fbx` (un fichier à la fois : l'import groupé gère mal les
   maillages skinnés). Le fichier est en **mètres** : si Studio demande les dimensions du fichier, choisis
   *Meters* (un cactus fait alors environ 6 studs, le boss environ 50 studs de long). Garde les os : c'est un
   modèle riggé (os `Root` au sol sous l'ennemi, avant vers +Y de Blender).
2. **Couleurs** : la texture-palette est incluse dans le FBX et les couleurs sont aussi en couleurs de
   sommets. Si Studio affiche le modèle gris, ajoute au MeshPart une `SurfaceAppearance` avec
   `ColorMap = <Nom>_Couleur.png` (et `RoughnessMap`, `MetalnessMap`), ou mets `<Nom>_Couleur.png` dans
   `TextureID`. Laisse la couleur du MeshPart en blanc.
3. **Animations** : sélectionne le modèle, ouvre l'*Animation Editor*, menu « ⋯ » > *Import* >
   *From FBX Animation*, puis choisis `Animations/<Nom>_Fly.fbx` (coche *Loop*) et `Animations/<Nom>_Attack.fbx`.
   Publie-les et joue-les avec l'`Animator` du modèle (Humanoid ou AnimationController).

Les animations n'utilisent que des positions et rotations d'os (aucune échelle, que Roblox ne lit pas).
Le visage est pondéré comme la peau du ballon : les yeux restent collés au corps dans toutes les poses.
"""


def main():
    os.makedirs(RBX, exist_ok=True)
    with open(os.path.join(RBX, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(README)
    blends = sorted(b for b in glob.glob(os.path.join(OUT, "Blender", "**", "*.blend"), recursive=True)
                    if "_References" not in b)
    only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for b in blends:
        if only and not any(o in b for o in only):
            continue
        process(b)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
