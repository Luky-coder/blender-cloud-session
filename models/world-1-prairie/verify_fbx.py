"""Vérifie les FBX : réimporte chaque fichier dans une scène vide et compare ses 5 animations au .blend source.

    blender -b --factory-startup -P models/world-1-prairie/verify_fbx.py -- [chemin/vers/FBX ...]

Pour chaque prise (Idle, Move, Attack, Hit, Death), on compare aux mêmes images le centre et la taille de la
boîte englobante du maillage déformé (FBX réimporté vs .blend). Écrit World_1_Prairie/FBX/verification.md.
"""
import glob
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "World_1_Prairie")
NAMES = ["Idle", "Move", "Attack", "Hit", "Death"]


def bbox(mesh):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    lo = Vector(map(min, *pts)) if len(pts) > 1 else pts[0]
    hi = Vector(map(max, *pts)) if len(pts) > 1 else pts[0]
    return (lo + hi) / 2, hi - lo


def sample(arm, mesh, act_by_name):
    scene = bpy.context.scene
    res = {}
    for name in NAMES:
        act = act_by_name.get(name)
        if act is None:
            continue
        arm.animation_data.action = act
        if hasattr(arm.animation_data, "action_slot") and act.slots:
            arm.animation_data.action_slot = act.slots[0]
        f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
        frames = sorted({f0, f0 + (f1 - f0) // 4, f0 + (f1 - f0) // 2, f0 + round((f1 - f0) * 0.46), f1})
        res[name] = (f1 - f0, [(f - f0, *bbox_at(scene, f, mesh)) for f in frames])
    return res


def bbox_at(scene, f, mesh):
    scene.frame_set(f)
    return bbox(mesh)


def eye_depth(arm, mesh, acts):
    """Profondeur minimale (m) des yeux/sourcils par rapport à l'enveloppe déformée, sur toutes les images
    (négatif = sous la surface)."""
    from mathutils.bvhtree import BVHTree
    me = mesh.data
    env = {i for i, m in enumerate(me.materials) if any(k in m.name for k in ("Enveloppe", "Mylar", "Fuseau"))}
    gi = {g.index: g.name for g in mesh.vertex_groups}
    face_v = [v.index for v in me.vertices
              if any(g.weight > 0.5 and gi[g.group].split("_")[0] in ("Oeil", "Pupille", "Sourcil") for g in v.groups)]
    env_f = [p.index for p in me.polygons if p.material_index in env]
    scene = bpy.context.scene
    worst = {}
    for name in NAMES:
        act = acts.get(name)
        if act is None or not face_v:
            continue
        arm.animation_data.action = act
        if act.slots:
            arm.animation_data.action_slot = act.slots[0]
        f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
        w = 1e9
        for f in range(f0, f1 + 1):
            scene.frame_set(f)
            ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
            m2 = ev.to_mesh()
            V = [ev.matrix_world @ v.co for v in m2.vertices]
            bvh = BVHTree.FromPolygons(V, [tuple(m2.polygons[i].vertices) for i in env_f])
            for vi in face_v:
                loc, nor, _i, _d = bvh.find_nearest(V[vi])
                if loc is not None:
                    w = min(w, (V[vi] - loc).dot(nor))
            ev.to_mesh_clear()
        worst[name] = w
    return worst


def check(fbx):
    rel = os.path.relpath(fbx, os.path.join(OUT, "FBX"))
    blend = os.path.join(OUT, "Blender", os.path.splitext(rel)[0] + ".blend")
    # Source
    bpy.ops.wm.open_mainfile(filepath=blend)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh = next(o for o in bpy.data.objects if o.type == "MESH")
    src = sample(arm, mesh, {a.name: a for a in bpy.data.actions})
    nb_bones = len(arm.data.bones)
    # FBX réimporté
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    bpy.ops.import_scene.fbx(filepath=fbx, use_anim=True, ignore_leaf_bones=False, automatic_bone_orientation=False)
    arm2 = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh2 = next(o for o in bpy.data.objects if o.type == "MESH")
    acts = {a.name.split("|")[-1]: a for a in bpy.data.actions}
    dst = sample(arm2, mesh2, acts)
    lines, ok = [], True
    for name in NAMES:
        if name not in dst:
            lines.append(f"  {name}: ABSENTE du FBX")
            ok = False
            continue
        n_src, s = src[name]
        n_dst, d = dst[name]
        err = max(max((a[1] - b[1]).length, (a[2] - b[2]).length) for a, b in zip(s, d))
        size0 = s[0][2].length
        moves = max((x[1] - s[0][1]).length for x in s)
        lines.append(f"  {name}: {n_dst} images (source {n_src}), écart max {err * 1000:.1f} mm, "
                     f"déplacement max {moves:.2f} m, taille fin/début {d[-1][2].length / size0:.2f}")
        if n_src != n_dst or err > 0.01 * size0 + 0.002:
            ok = False
    depth = eye_depth(arm2, mesh2, acts)
    if depth:
        bad = {k: v for k, v in depth.items() if v < -0.001}
        if bad:
            ok = False
        lines.insert(0, "  Yeux : toujours au-dessus de l'enveloppe" if not bad else "  Yeux : SOUS l'enveloppe")
        lines.insert(1, "  Yeux (marge minimale, mm) : " + ", ".join(f"{k} {v * 1000:+.1f}" for k, v in depth.items()))
    tex = [i for i in bpy.data.images if i.name.endswith("_Palette") and i.size[0] > 0]
    uv, vcol = len(mesh2.data.uv_layers), len(mesh2.data.color_attributes)
    linked = all(any(n.type == "TEX_IMAGE" and n.image in tex for n in m.node_tree.nodes) for m in mesh2.data.materials)
    if not (tex and uv and vcol and linked):
        ok = False
    lines.insert(0, f"  Couleurs : texture palette incrustée {'oui' if tex else 'NON'}, UV {'oui' if uv else 'NON'}, "
                    f"couleurs de sommets {'oui' if vcol else 'NON'}, texture sur tous les matériaux {'oui' if linked else 'NON'}")
    head = (f"{'OK ' if ok else 'ERREUR'} {rel} : {len(mesh2.data.vertices)} sommets, {nb_bones} os "
            f"({len(arm2.data.bones)} réimportés), {len(mesh2.data.materials)} matériaux, prises : "
            f"{', '.join(sorted(a.name for a in bpy.data.actions))}")
    return ok, [head] + lines


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    files = argv or sorted(glob.glob(os.path.join(OUT, "FBX", "**", "*.fbx"), recursive=True))
    report, all_ok = [], True
    for f in files:
        ok, lines = check(os.path.abspath(f))
        all_ok &= ok
        report += lines
        print("\n".join(lines), flush=True)
    if not argv:
        with open(os.path.join(OUT, "FBX", "verification.md"), "w", encoding="utf-8") as fh:
            fh.write("# Vérification des FBX\n\nChaque FBX est réimporté dans Blender et comparé au .blend source "
                     "(boîte englobante du maillage déformé à 5 instants de chaque prise) ; on contrôle aussi que les couleurs "
                     "sont portées par la texture palette incrustée, les UV et les couleurs de sommets, et que les yeux "
                     "restent au-dessus de l'enveloppe à chaque image de chaque prise.\n\n```\n")
            fh.write("\n".join(report) + "\n```\n")
    print("TOUT OK" if all_ok else "DES ERREURS", flush=True)
    sys.exit(0 if all_ok else 1)


main()
