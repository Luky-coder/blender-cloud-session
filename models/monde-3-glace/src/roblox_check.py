"""Vérifie un export Roblox : ré-importe le modèle et ses animations, contrôle les contraintes.

    blender -b --factory-startup -q -P src/roblox_check.py -- <dossier_modele_roblox> [apercu.jpg]

Contrôles : triangles <= 20 000 par maillage, <= 4 os par sommet, couleurs de sommets présentes,
un seul matériau, une prise par fichier d'animation, aucune courbe d'échelle d'os.
Avec apercu.jpg : rend une planche (une ligne par animation) de la version Roblox.
"""
import glob
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
d = os.path.abspath(argv[0])
sheet = argv[1] if len(argv) > 1 else None
errors = []
model = [f for f in glob.glob(os.path.join(d, "*.fbx"))][0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=model)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
for o in meshes:
    me = o.data
    me.calc_loop_triangles()
    t = len(me.loop_triangles)
    infl = max((sum(1 for g in v.groups if g.weight > 0) for v in me.vertices), default=0)
    if t > 20000:
        errors.append(f"{o.name}: {t} triangles")
    if infl > 4:
        errors.append(f"{o.name}: {infl} influences")
    if not me.color_attributes:
        errors.append(f"{o.name}: pas de couleurs de sommets")
    if len(me.materials) > 1:
        errors.append(f"{o.name}: {len(me.materials)} matériaux")
    ncol = len({tuple(round(x, 2) for x in d.color[:3]) for d in me.color_attributes[0].data}) if me.color_attributes else 0
    print(f"[rbx] maillage {o.name}: {t} triangles, max {infl} os/sommet, couleurs de sommets : {ncol} teintes")
    if ncol < 3:
        errors.append(f"{o.name}: couleurs de sommets uniformes")
arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
print(f"[rbx] armature : {arms[0].name}, {len(arms[0].data.bones)} os")
for f in sorted(glob.glob(os.path.join(d, "Animations", "*.fbx"))):
    before = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=f)
    new = [a for a in bpy.data.actions if a not in before]
    curves = [c for a in new for l in a.layers for s in l.strips for cb in s.channelbags for c in cb.fcurves]
    scl = [c for c in curves if c.data_path.endswith(".scale") and len({round(k.co[1], 4) for k in c.keyframe_points}) > 1]
    moving = [c for c in curves if len({round(k.co[1], 4) for k in c.keyframe_points}) > 1]
    rng = new[0].frame_range[:] if new else None
    print(f"[rbx] {os.path.basename(f)}: {len(new)} prise(s) {[a.name for a in new]}, {rng}, "
          f"{len(moving)} courbes animées, {len(scl)} courbes d'échelle animées")
    if len(new) != 1:
        errors.append(f"{os.path.basename(f)}: {len(new)} prises")
    if scl:
        errors.append(f"{os.path.basename(f)}: échelle animée")
    if not moving:
        errors.append(f"{os.path.basename(f)}: immobile")
    for o in [o for o in bpy.data.objects if o not in arms and o not in meshes]:
        bpy.data.objects.remove(o)
print("[rbx] " + ("OK" if not errors else "ERREURS : " + " ; ".join(errors)))

if sheet:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
    import preview
    blend = glob.glob(os.path.join(d, "_roblox_*.blend"))[0]
    bpy.ops.wm.open_mainfile(filepath=blend)
    sc = bpy.context.scene
    rig = next(o for o in sc.objects if o.type == "ARMATURE")
    mat = bpy.data.materials["Roblox_Couleurs_Sommets"]
    preview._setup_render(sc, 256, 200, 8)
    preview._ensure_lighting(sc)
    paths = []
    tmp = os.path.dirname(sheet)
    meshes = [o for o in sc.objects if o.type == "MESH"]
    acts = sorted(bpy.data.actions, key=lambda a: (["IDLE", "MOVE", "ATTACK", "HIT", "DEATH"].index(a.name)
                                                     if a.name in ["IDLE", "MOVE", "ATTACK", "HIT", "DEATH"] else 9, a.name))
    from mathutils import Vector
    for act in acts:
        rig.animation_data.action = act
        rig.animation_data.action_slot = act.slots[0]
        n = int(act.frame_end)
        fr = [int(act.frame_start) + round(i * (n - act.frame_start) / 5) for i in range(6)]
        lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
        for f in fr:
            sc.frame_set(f)
            b = preview.scene_bounds(bpy.context.evaluated_depsgraph_get())
            if b:
                lo, hi = Vector(map(min, lo, b[0])), Vector(map(max, hi, b[1]))
        sc.camera = preview._setup_camera(sc, "s_" + act.name, 215, 14, True, lo, hi)
        for f in fr:
            sc.frame_set(f)
            p = os.path.join(tmp, f"rbx_{act.name}_{f}.jpg")
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
            paths.append(p)
    preview.make_grid(paths, sheet, cols=6)
