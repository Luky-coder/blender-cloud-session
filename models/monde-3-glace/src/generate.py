"""Génère UN ennemi du monde 3 : .blend + .fbx + aperçus.

    blender -b --factory-startup -q --python-exit-code 1 -P src/generate.py -- <famille> <element> [options]

    famille : igloo | flocon | dirigeable | pin | gardien
    element : lumiere | tenebres | glace | feu | eau | plante | eclair   (pin : eau, gardien : glace)
    options : --no-render   --no-sheet   --samples N   --out DOSSIER (défaut : World_3_Glace)
"""
import argparse
import importlib
import json
import math
import os
import shutil
import sys
import time

import bpy
from mathutils import Vector

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
REPO = os.path.dirname(os.path.dirname(ROOT))
sys.path.insert(0, SRC)
sys.path.insert(0, os.path.join(REPO, "tools"))

import elements as E  # noqa: E402
import preview  # noqa: E402
import w3lib as L  # noqa: E402

FAMILIES = {"igloo": "fam_igloo", "flocon": "fam_flocon", "dirigeable": "fam_dirigeable",
            "pin": "boss_pin", "gardien": "boss_gardien"}
BOSS_FILES = {"pin": "MiniBoss_Pin_Gonflable_Eau", "gardien": "Boss_Gardien_Glaciers_Glace"}
# Animations exportées (demande : seulement le vol et l'attaque). Les autres (IDLE, MOVE, HIT, DEATH,
# attaques spéciales des boss…) restent définies dans le code : les ajouter ici pour les réactiver.
EXPORT_ACTIONS = ["FLY", "ATTACK"]


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("family", choices=list(FAMILIES))
    p.add_argument("element", choices=E.ORDER)
    p.add_argument("--no-render", action="store_true")
    p.add_argument("--no-sheet", action="store_true")
    p.add_argument("--samples", type=int, default=24)
    p.add_argument("--size", default="640x480")
    p.add_argument("--out", default=os.path.join(ROOT, "World_3_Glace"))
    p.add_argument("--tmp", default=os.path.join(ROOT, ".tmp_render"))
    return p.parse_args(argv)


def paths(args, mod):
    fam_dir, _, _ = mod.FAMILY
    key = E.ELEMENTS[args.element][1]
    if args.family in BOSS_FILES:
        base = BOSS_FILES[args.family]
        blend = os.path.join(args.out, "Blender", base + ".blend")
        fbx = os.path.join(args.out, "FBX", base + ".fbx")
        prev = os.path.join(args.out, "Previews", base)
    else:
        blend = os.path.join(args.out, "Blender", fam_dir, key + ".blend")
        fbx = os.path.join(args.out, "FBX", fam_dir, f"{fam_dir}_{key}.fbx")
        prev = os.path.join(args.out, "Previews", fam_dir, key)
    return blend, fbx, prev


def eval_bounds(mesh_ob):
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh_ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    if len(co) == 0:
        return None
    return Vector(co.min(axis=0)), Vector(co.max(axis=0))


def render_sheet(rig, mesh_ob, actions, out_path, tmp, cols=6, w=300, h=225, samples=8):
    """Planche : une ligne par Action (ordre de `actions`), `cols` images réparties sur sa durée.
    Le cadrage est commun à toute une ligne (on voit le déplacement), il change d'une ligne à l'autre."""
    scene = bpy.context.scene
    preview._setup_render(scene, w, h, samples)
    preview._ensure_lighting(scene)
    os.makedirs(tmp, exist_ok=True)
    paths = []
    for act in actions:
        L.set_action(rig, act)
        n = int(act.frame_end)
        fr = [1 + round(i * (n - 1) / (cols - 1)) for i in range(cols)]
        if act.name == "ATTACK" and n == 37:
            fr = [1, 9, 14, 17, 23, 32]   # repos, recul, projection, impact, rebond, retour
        lo = Vector((1e9,) * 3)
        hi = Vector((-1e9,) * 3)
        for f in fr:
            scene.frame_set(f)
            b = eval_bounds(mesh_ob)
            if b and (b[1] - b[0]).length > 0.05:
                lo = Vector(map(min, lo, b[0]))
                hi = Vector(map(max, hi, b[1]))
        scene.camera = preview._setup_camera(scene, "sheet_" + act.name, 215, 14, True, lo, hi)
        for f in fr:
            scene.frame_set(f)
            pth = os.path.join(tmp, f"sheet_{act.name}_{f:03d}.jpg")
            scene.render.filepath = pth
            bpy.ops.render.render(write_still=True)
            paths.append(pth)
    preview.make_grid(paths, out_path, cols=cols)


def main():
    args = parse()
    t0 = time.time()
    mod = importlib.import_module(FAMILIES[args.family])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.unit_settings.system = "METRIC"

    m, actions = mod.build(args.element)
    rig, mesh = m.rig, m.mesh
    _, fam_title, hp = mod.FAMILY
    rig["ennemi"] = m.title
    rig["famille"] = fam_title
    rig["type"] = E.ELEMENTS[args.element][0]
    rig["pv"] = hp
    rig["avant"] = "+Y"
    rig["fps"] = 30

    # collection propre au modèle
    coll = bpy.data.collections.new(m.name)
    scene.collection.children.link(coll)
    for ob in (rig, mesh):
        scene.collection.objects.unlink(ob)
        coll.objects.link(ob)

    baked = []
    for name in EXPORT_ACTIONS:
        n, loop, fn = actions[name]
        act, _ = L.bake_action(rig, name, n, fn, loop)
        baked.append(act)
    idle = bpy.data.actions["FLY"]
    rest = bpy.data.actions["ATTACK"]      # image 1 de l'attaque = pose de repos (projectiles cachés)
    L.set_action(rig, idle)
    scene.frame_set(1)
    bpy.context.view_layer.update()

    # Couleurs des matériaux recopiées en couleurs de sommets (lues par Roblox et la plupart des moteurs)
    me0 = mesh.data
    cols = []
    for slot in mesh.material_slots:
        bsdf = next(nd for nd in slot.material.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
        src = "Emission Color" if bsdf.inputs["Emission Strength"].default_value > 1.0 else "Base Color"
        cols.append(tuple(bsdf.inputs[src].default_value))
    attr = me0.color_attributes.new("Couleur", "BYTE_COLOR", "CORNER")
    for poly in me0.polygons:
        for li in poly.loop_indices:
            attr.data[li].color = cols[poly.material_index]

    blend, fbx, prev = paths(args, mod)
    for d in (os.path.dirname(blend), os.path.dirname(fbx), prev):
        os.makedirs(d, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)

    # Export FBX : maillage + armature, toutes les Actions (une prise par Action)
    bpy.ops.export_scene.fbx(
        filepath=fbx, use_selection=False, object_types={"ARMATURE", "MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Z", axis_up="Y",
        use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=False,
        add_leaf_bones=False, use_armature_deform_only=True, primary_bone_axis="Y", secondary_bone_axis="X",
        bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0,
        bake_anim_simplify_factor=0.0, path_mode="AUTO", embed_textures=False, colors_type="SRGB")
    L.set_action(rig, rest)
    scene.frame_set(1)

    # Statistiques
    dg = bpy.context.evaluated_depsgraph_get()
    me = mesh.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    stats = dict(verts=len(me.vertices), tris=len(me.loop_triangles))
    mesh.evaluated_get(dg).to_mesh_clear()
    lo, hi = m.bounds
    info = dict(name=m.name, title=m.title, family=fam_title, element=E.ELEMENTS[args.element][0], hp=hp,
                blend=os.path.relpath(blend, args.out), fbx=os.path.relpath(fbx, args.out),
                dims=[round(x, 3) for x in (hi - lo)], bones=len(rig.data.bones),
                deform_bones=sum(1 for b in rig.data.bones if b.use_deform),
                shape_keys=[k.name for k in mesh.data.shape_keys.key_blocks[1:]],
                actions=[dict(name=a.name, frames=int(a.frame_end), loop=bool(a.use_cyclic),
                              seconds=round((a.frame_end - 1) / 30, 2)) for a in baked],
                materials={s.material.name: L.MATERIAL_INFO.get(s.material.name) for s in mesh.material_slots},
                **stats)

    if not args.no_render:
        w, h = map(int, args.size.split("x"))
        tmp = os.path.join(args.tmp, m.name)
        os.makedirs(tmp, exist_ok=True)
        _, grid = preview.render_previews(tmp, ["iso_back", "back", "right", "iso"], w, h, args.samples)
        shutil.copy(grid, prev + ".jpg")
        if not args.no_sheet:
            render_sheet(rig, mesh, baked, prev + "_animations.jpg", tmp)
        shutil.rmtree(tmp, ignore_errors=True)
    info["seconds"] = round(time.time() - t0, 1)
    with open(prev + ".json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    print(f"[w3] OK {m.name} : {stats['verts']} sommets, {stats['tris']} triangles, "
          f"{len(baked)} actions, {info['seconds']} s")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
