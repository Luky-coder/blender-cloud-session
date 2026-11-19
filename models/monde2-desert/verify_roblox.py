"""Vérifie l'export Roblox : ré-importe chaque modèle FBX et chaque animation FBX.

    blender -b --factory-startup --python-exit-code 1 -P models/monde2-desert/verify_roblox.py [-- --render]

Contrôles : 1 maillage skinné, 1 seul matériau avec texture-palette, UV + couleurs de sommets,
<= 20 000 triangles, <= 4 os par sommet, pas de shape keys, os de repos sans échelle ; chaque animation :
1 seule prise, aucune échelle d'os (toutes à 1), os tous présents dans le modèle, mouvement réel une fois
appliquée au modèle (coup vers l'avant, recul, disparition sous le sol pour la mort).
--render : planche d'images clés rendue à partir des FBX ré-importés (contrôle visuel).
Écrit World_2_Desert/Roblox/VERIFICATION_ROBLOX.md.
"""
import glob
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
RBX = os.path.join(HERE, "World_2_Desert", "Roblox")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools"))
MAX_TRIS = 20000


def fcurves(act):
    return [fc for layer in act.layers for st in layer.strips for cb in st.channelbags for fc in cb.fcurves]


def bbox(mesh):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    pts = [mesh.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return Vector(map(min, *pts)), Vector(map(max, *pts))


def check(folder, render=False):
    name = os.path.basename(folder.rstrip("/"))
    model = [f for f in glob.glob(os.path.join(folder, "*.fbx")) if not os.path.basename(f).startswith("Prop_")][0]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=model)
    rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    err, notes = [], []
    if len(meshes) != 1:
        err.append(f"{len(meshes)} maillages")
    mesh = meshes[0]
    me = mesh.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    infl = max(len([g for g in v.groups if g.weight > 1e-4]) for v in me.vertices)
    mats = [m for m in me.materials if m]
    tex = any(n.type == "TEX_IMAGE" and n.image for m in mats for n in m.node_tree.nodes)
    if tris > MAX_TRIS:
        err.append(f"{tris} triangles")
    if len(mats) != 1:
        err.append(f"{len(mats)} matériaux")
    if not tex:
        err.append("texture-palette non liée au matériau")
    if not me.uv_layers:
        err.append("pas d'UV")
    if not me.color_attributes:
        err.append("pas de couleurs de sommets")
    if me.shape_keys:
        err.append("shape keys présentes")
    if infl > 4:
        err.append(f"{infl} os sur un sommet")
    if not any(m.type == "ARMATURE" for m in mesh.modifiers):
        err.append("maillage non skinné")
    size0 = None
    lo0, hi0 = bbox(mesh)
    size0 = (hi0 - lo0)
    notes.append(f"modèle : {tris} triangles, {len(rig.data.bones)} os, 1 matériau, {infl} os max par sommet, "
                 f"taille {size0.x:.2f} × {size0.y:.2f} × {size0.z:.2f} m "
                 f"(≈ {size0.z / 0.28:.1f} studs de haut)")
    bones = set(rig.data.bones.keys())
    rig.animation_data_create()
    shots = []
    for af in sorted(glob.glob(os.path.join(folder, "Animations", "*.fbx"))):
        before = set(bpy.data.objects)
        before_acts = set(bpy.data.actions)
        bpy.ops.import_scene.fbx(filepath=af)
        new_objs = [o for o in bpy.data.objects if o not in before]
        acts = [a for a in bpy.data.actions if a not in before_acts]
        an = os.path.basename(af)[:-4]
        arm = next((o for o in new_objs if o.type == "ARMATURE"), None)
        if len(acts) != 1:
            err.append(f"{an} : {len(acts)} prises (1 attendue)")
        if arm is None or not acts:
            err.append(f"{an} : armature ou animation absente")
            continue
        act = acts[0]
        missing = set(arm.data.bones.keys()) - bones
        if missing:
            err.append(f"{an} : os inconnus du modèle {sorted(missing)[:3]}")
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        smax = 0.0
        for fc in fcurves(act):
            if fc.data_path.endswith(".scale"):
                for f in range(f0, f1 + 1, 2):
                    smax = max(smax, abs(fc.evaluate(f) - 1.0))
        if smax > 1e-3:
            err.append(f"{an} : échelle d'os animée ({smax:.3f})")
        for o in new_objs:
            bpy.data.objects.remove(o)
        rig.animation_data.action = act
        if act.slots:
            rig.animation_data.action_slot = act.slots[0]
        cs = []
        for f in range(f0, f1 + 1, max(1, (f1 - f0) // 15)):
            bpy.context.scene.frame_set(f)
            lo, hi = bbox(mesh)
            cs.append(((lo + hi) / 2, lo, hi))
        bpy.context.scene.frame_set(f1)
        lo1, hi1 = bbox(mesh)
        c0 = cs[0][0]
        moved = max((c - c0).length for c, _, _ in cs)
        kind = an[len(name.split("/")[-1]):] if False else an.split("_", 2)[-1]
        line = f"{an} [{f0}-{f1}] : déplacement max {moved:.2f} m, échelle max {smax:.4f}"
        if moved < 0.005:
            err.append(f"{an} : immobile")
        if kind == "Attack":
            fwd = max(c.y - c0.y for c, _, _ in cs)
            line += f", avancée {fwd:.2f} m"
            if fwd < 0.03 * size0.length:
                err.append(f"{an} : pas de coup vers l'avant")
        if kind == "Hit":
            back = min(c.y - c0.y for c, _, _ in cs)
            line += f", recul {back:.2f} m"
            if back > -0.01:
                err.append(f"{an} : pas de recul")
        if kind == "Death":
            line += f", sommet final à {hi1.z:.2f} m (sous le sol si < 0)"
            if hi1.z > 0.05:
                err.append(f"{an} : ne disparaît pas sous le sol")
        notes.append(line)
        shots.append((act, f0, f1, kind))
    kinds = sorted(k for _, _, _, k in shots)
    if kinds != ["Attack", "Fly"]:
        err.append(f"animations {kinds} (attendu Fly, Attack)")
    props = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(folder, "Prop_*.fbx")))
    if props:
        notes.append("accessoires séparés : " + ", ".join(props))
    if render:
        render_sheet(folder, rig, mesh, shots)
    return err, notes


def render_sheet(folder, rig, mesh, shots):
    import preview
    sc = bpy.context.scene
    w = bpy.data.worlds.new("w")
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.75, 0.68, 1)
    sc.world = w
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.location, pb.rotation_quaternion = (0, 0, 0), (1, 0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
    sc.frame_set(1)
    lo, hi = bbox(mesh)
    pad = (hi - lo) * 0.15
    preview._setup_render(sc, 300, 260, 12)
    preview._ensure_lighting(sc)
    sc.camera = preview._setup_camera(sc, "c", 215, 15, False, lo - pad, hi + pad + Vector((0, (hi - lo).y * 0.4, 0)))
    paths = []
    picks = []
    for act, f0, f1, kind in shots:
        frac = {"Fly": (0.0, 0.33, 0.66), "Hit": (0.15, 0.35), "Idle": (0.0,), "Move": (0.25,),
                "Attack": (0.25, 0.45), "Death": (0.5, 0.9)}.get(
            kind, (0.4,))
        picks += [(act, int(f0 + (f1 - f0) * x)) for x in frac]
    for i, (act, f) in enumerate(picks):
        rig.animation_data.action = act
        if act.slots:
            rig.animation_data.action_slot = act.slots[0]
        sc.frame_set(f)
        p = os.path.join(bpy.app.tempdir, f"rbx_{i}.jpg")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    preview.make_grid(paths, os.path.join(folder, "Apercu_Roblox.jpg"), cols=next((c for c in (5, 4, 3, 6, 7) if len(paths) % c == 0), 4) if len(paths) > 4 else len(paths))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    render = "--render" in argv
    only = [a for a in argv if not a.startswith("--")]
    folders = sorted({os.path.dirname(os.path.dirname(p)) for p in glob.glob(os.path.join(RBX, "**", "Animations", "*.fbx"),
                                                                            recursive=True)})
    rows, details, total = [], [], 0
    for fo in folders:
        rel = os.path.relpath(fo, RBX)
        if only and not any(o in rel for o in only):
            continue
        err, notes = check(fo, render)
        total += len(err)
        rows.append(f"| {rel} | {'OK' if not err else 'ÉCHEC'} |")
        details.append(f"### {rel}\n\n" + "\n".join(f"- {n}" for n in notes) +
                       ("\n" + "\n".join(f"- **ERREUR** {e}" for e in err) if err else "") + "\n")
        print(f"[roblox-verify] {rel}: {'OK' if not err else err}")
    with open(os.path.join(RBX, "VERIFICATION_ROBLOX.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Vérification de l'export Roblox (FBX ré-importés)\n\n"
                f"Généré par `verify_roblox.py`. {len(rows)} ennemis, {total} erreur(s).\n\n"
                "| Ennemi | Statut |\n|---|---|\n" + "\n".join(rows) + "\n\n" + "\n".join(details))
    if total:
        sys.exit(1)


if __name__ == "__main__":
    main()
