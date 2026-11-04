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


def envelope_faces(arm, mesh):
    """Faces de l'enveloppe : matériau unique, on les repère par leur case de palette (UV), listée dans la
    propriété « Enveloppe_Cases » de l'armature (exportée dans le FBX)."""
    me = mesh.data
    cells = {int(c) for c in str(arm.get("Enveloppe_Cases", "0")).split(",") if c.strip()}
    uv = me.uv_layers.active.data if me.uv_layers else None
    out = []
    for p in me.polygons:
        if uv is None:
            out.append(p.index)
            continue
        u, v = uv[p.loop_start].uv
        if int(u * 16) + 16 * int(v * 16) in cells:
            out.append(p.index)
    return out


def eye_depth(arm, mesh, acts):
    """Profondeur minimale (m) des yeux/sourcils par rapport à l'enveloppe déformée, sur toutes les images
    (négatif = sous la surface)."""
    from mathutils.bvhtree import BVHTree
    me = mesh.data
    gi = {g.index: g.name for g in mesh.vertex_groups}
    face_v = [v.index for v in me.vertices
              if any(g.weight > 0.5 and gi[g.group].split("_")[0] in ("Oeil", "Paupiere", "Pupille", "Sourcil")
                     for g in v.groups)]
    env_f = envelope_faces(arm, mesh)
    # autocollants épais : seule leur face visible compte (leur base est volontairement enfoncée)
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m2 = ev.to_mesh()
    V = [ev.matrix_world @ v.co for v in m2.vertices]
    bvh0 = BVHTree.FromPolygons(V, [tuple(m2.polygons[i].vertices) for i in env_f])
    outer = []
    for vi in face_v:
        loc, nor, _i, _d = bvh0.find_nearest(V[vi])
        if loc is not None and (V[vi] - loc).dot(nor) > 0.0005:
            outer.append(vi)
    ev.to_mesh_clear()
    arm.data.pose_position = "POSE"
    face_v = outer
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


ATTACHED = ("Helice", "Ficelle", "Nacelle")  # pièces animées qui doivent rester collées au corps


def all_fcurves(act):
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                yield from cb.fcurves


def compress(acts, step=4):
    """Simule la compression d'animation d'un moteur : une clé sur `step`, indépendamment pour chaque os."""
    for act in acts.values():
        f0 = act.frame_range[0]
        for fc in all_fcurves(act):
            kps = fc.keyframe_points
            last = len(kps) - 1
            for i in range(last - 1, 0, -1):
                if round(kps[i].co.x - f0) % step:
                    kps.remove(kps[i], fast=True)
            fc.update()


def attach_gap(arm, mesh, acts):
    """Pour chaque pièce attachée (hélices, ficelle, nacelle) : de combien sa distance au reste du modèle
    augmente au pire par rapport au repos (0 = toujours collée)."""
    from mathutils.kdtree import KDTree
    me = mesh.data
    gi = {g.index: g.name for g in mesh.vertex_groups}
    groups = {}
    for v in me.vertices:
        g = max(v.groups, key=lambda x: x.weight, default=None)
        if g is not None and g.weight > 0.5:
            key = next((a for a in ATTACHED if gi[g.group].startswith(a)), None)
            if key:
                groups.setdefault(gi[g.group] if key == "Helice" else key, []).append(v.index)
    if not groups:
        return {}
    scene = bpy.context.scene
    worst = {g: 0.0 for g in groups}

    def gaps():
        ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
        m2 = ev.to_mesh()
        V = [ev.matrix_world @ v.co for v in m2.vertices]
        ev.to_mesh_clear()
        out = {}
        for g, ids in groups.items():
            s = set(ids)
            others = [i for i in range(len(V)) if i not in s][::3]
            kd = KDTree(len(others))
            for k, i in enumerate(others):
                kd.insert(V[i], k)
            kd.balance()
            out[g] = min(kd.find(V[i])[2] for i in ids)
        return out

    for name in NAMES:
        act = acts.get(name)
        if act is None:
            continue
        arm.animation_data.action = act
        if act.slots:
            arm.animation_data.action_slot = act.slots[0]
        f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
        scene.frame_set(f0)
        rest = gaps()
        for f in range(f0, f1 + 1, 2):
            scene.frame_set(f)
            for g, d in gaps().items():
                worst[g] = max(worst[g], d - rest[g])
    return worst


def ignore_scales(acts):
    """Simule un moteur qui ignore l'échelle des os (Roblox) : toutes les clés d'échelle valent 1."""
    for act in acts.values():
        for fc in all_fcurves(act):
            if fc.data_path.endswith(".scale"):
                for kp in fc.keyframe_points:
                    kp.co.y = kp.handle_left.y = kp.handle_right.y = 1.0
                fc.update()


def animated_scales(acts):
    """Os dont l'échelle varie (hors disparition finale de Death sur Body)."""
    out = set()
    for name, act in acts.items():
        for fc in all_fcurves(act):
            if fc.data_path.endswith(".scale") and fc.keyframe_points:
                vals = [kp.co.y for kp in fc.keyframe_points]
                if max(abs(v - 1.0) for v in vals) > 1e-4:
                    bone = fc.data_path.split('"')[1]
                    if not (name == "Death" and bone == "Body"):
                        out.add(f"{name}:{bone}")
    return out


def robustness(arm, mesh, acts, size):
    """Pire cas moteur : échelles d'os ignorées (Roblox) ET compression (une clé sur 4, os par os)."""
    ignore_scales(acts)
    compress(acts)
    depth = eye_depth(arm, mesh, acts)
    gap = attach_gap(arm, mesh, acts)
    ok = all(v >= -0.001 for v in depth.values()) and all(v <= 0.0025 * size for v in gap.values())
    line = ("  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux "
            + (f"marge min {min(depth.values()) * 1000:+.1f} mm" if depth else "—")
            + ", pièces attachées : " + (", ".join(f"{g} {v * 1000:+.1f} mm" for g, v in sorted(gap.items())) or "—"))
    return ok, line


def loose_parts(mesh, size):
    """Au repos : morceaux du maillage qui ne touchent ni ne traversent aucun autre morceau."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bm.transform(mesh.matrix_world)
    bm.verts.ensure_lookup_table()
    owner, k = {}, 0
    for v in bm.verts:
        if v.index in owner:
            continue
        stack = [v]
        owner[v.index] = k
        while stack:
            x = stack.pop()
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in owner:
                    owner[o.index] = k
                    stack.append(o)
        k += 1
    co = [v.co.copy() for v in bm.verts]
    faces = {}
    for f in bm.faces:
        faces.setdefault(owner[f.verts[0].index], []).append(tuple(v.index for v in f.verts))
    verts_of = {}
    for i, o in owner.items():
        verts_of.setdefault(o, []).append(i)
    bm.free()
    tol = 0.002 * size
    loose = 0
    for isl, fl in faces.items():
        others = [f for o, l in faces.items() if o != isl for f in l]
        if not others:
            continue
        bvh = BVHTree.FromPolygons(co, others)
        if bvh.overlap(BVHTree.FromPolygons(co, fl)):
            continue
        if min(bvh.find_nearest(co[i])[3] for i in verts_of[isl]) > tol:
            loose += 1
    return loose, len(faces)


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
    size = dst["Idle"][1][0][2].length if "Idle" in dst else 1.0  # taille au repos (diagonale)
    scl = animated_scales(acts)
    if scl:
        ok = False
    lines.insert(0, "  Échelles d'os animées : " + ("aucune (hors disparition finale de Death)" if not scl
                                                     else "NON CONFORME " + ", ".join(sorted(scl))))
    nmat = len(mesh2.data.materials)
    if nmat != 1:
        ok = False
    gap = attach_gap(arm2, mesh2, acts)
    if gap:
        if any(v > 0.0025 * size for v in gap.values()):
            ok = False
        lines.insert(2, "  Pièces attachées (écart max au corps vs repos) : "
                     + ", ".join(f"{g} {v * 1000:+.1f} mm" for g, v in sorted(gap.items())))
    arm2.data.pose_position = "REST"
    bpy.context.view_layer.update()
    nloose, nparts = loose_parts(mesh2, size)
    arm2.data.pose_position = "POSE"
    if nloose:
        ok = False
    lines.insert(3, f"  Pièces détachées au repos : {nloose} sur {nparts} morceaux" + (" (tout est fixé)" if not nloose else ""))
    rok, rline = robustness(arm2, mesh2, acts, size)
    ok = ok and rok
    lines.append(rline)
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
                     "sont portées par la texture palette incrustée, les UV et les couleurs de sommets, que les yeux "
                     "restent au-dessus de l'enveloppe à chaque image de chaque prise et que les pièces animées (hélices, "
                     "ficelle, nacelle) restent collées au corps ; les mêmes contrôles sont refaits après une compression "
                     "d'animation simulée (une clé sur 4, os par os), comme dans un moteur de jeu.\n\n```\n")
            fh.write("\n".join(report) + "\n```\n")
    print("TOUT OK" if all_ok else "DES ERREURS", flush=True)
    sys.exit(0 if all_ok else 1)


main()
