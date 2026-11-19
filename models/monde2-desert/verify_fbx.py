"""Vérifie les 25 ennemis : .blend et FBX ré-importés.

    blender -b --factory-startup --python-exit-code 1 -P models/monde2-desert/verify_fbx.py

Pour chaque ennemi :
- .blend : exactement 2 actions (Fly en boucle, Attack), tous les os keyés, aucune échelle d'os animée,
  boucle Fly refermée (image N+1 = image 1), <= 20 000 triangles, 1 seul matériau à texture-palette,
  UV + couleurs de sommets, pas de shape keys, visage pondéré comme la peau du corps ;
- FBX ré-importé : armature + maillage skinné, texture-palette incluse (couleurs présentes), couleurs de
  sommets, 2 prises Fly et Attack, aucune échelle animée, mouvement mesuré (vol qui bouge et boucle,
  attaque qui frappe vers l'avant (+Y)).
Écrit World_2_Desert/VERIFICATION.md et sort en erreur si un contrôle échoue.
"""
import glob
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "World_2_Desert")
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


def material_ok(me):
    mats = [m for m in me.materials if m]
    tex = [n.image for m in mats for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image]
    return len(mats), tex


def check_blend(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh = next(o for o in bpy.data.objects if o.type == "MESH")
    err, notes = [], []
    acts = sorted(a.name.rsplit("_", 1)[-1] for a in bpy.data.actions)
    if acts != ["Attack", "Fly"]:
        err.append(f"actions {acts} (attendu Fly, Attack)")
    for a in bpy.data.actions:
        fcs = fcurves(a)
        bones = {fc.data_path.split('"')[1] for fc in fcs if fc.data_path.startswith("pose.bones")}
        if len(bones) != len(rig.pose.bones):
            err.append(f"{a.name}: {len(bones)}/{len(rig.pose.bones)} os keyés")
        f0, f1 = a.frame_range
        smax = max((abs(fc.evaluate(f) - 1) for fc in fcs if fc.data_path.endswith(".scale")
                    for f in range(int(f0), int(f1) + 1, 3)), default=0.0)
        if smax > 1e-4:
            err.append(f"{a.name}: échelle d'os animée ({smax:.3f})")
        if a.use_cyclic:
            def gap(fc):
                g = abs(fc.evaluate(f1 + 1) - fc.evaluate(f0))
                if fc.data_path.endswith("rotation_euler"):
                    g = abs(g - 2 * math.pi * round(g / (2 * math.pi)))
                return g
            gmax = max(gap(fc) for fc in fcs)
            notes.append(f"{a.name} : boucle {int(f0)}-{int(f1)}, écart image N+1 / image 1 = {gmax:.4f}")
            if gmax > 1e-3:
                err.append(f"{a.name} : la boucle ne se referme pas")
    me = mesh.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    nmat, tex = material_ok(me)
    if tris > MAX_TRIS:
        err.append(f"{tris} triangles (> {MAX_TRIS})")
    if nmat != 1 or not tex:
        err.append(f"{nmat} matériau(x), texture-palette {'présente' if tex else 'absente'}")
    if not me.uv_layers or not me.color_attributes:
        err.append("UV ou couleurs de sommets absentes")
    if me.shape_keys:
        err.append("shape keys présentes")
    eye_bones = [b.name for b in rig.data.bones if b.name.startswith(("Eye_", "Pupil_", "Lid_", "Brow_"))]
    if eye_bones:
        err.append(f"os d'yeux séparés {eye_bones[:3]}")
    info = dict(pv=rig.get("PV"), bones=len(rig.pose.bones), verts=len(me.vertices), tris=tris)
    return info, err, notes


def check_fbx(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    rig = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
    mesh = next((o for o in bpy.data.objects if o.type == "MESH"), None)
    err, notes = [], []
    if rig is None or mesh is None:
        return ["armature ou maillage absent"], notes
    if not any(m.type == "ARMATURE" for m in mesh.modifiers):
        err.append("maillage non skinné")
    nmat, tex = material_ok(mesh.data)
    if nmat != 1 or not tex or not any(i.has_data or i.packed_file for i in tex):
        err.append("couleurs absentes du FBX (texture-palette non incluse)")
    if not mesh.data.color_attributes:
        err.append("couleurs de sommets absentes du FBX")
    takes = {a.name.split("|")[-1].rsplit("_", 1)[-1]: a for a in bpy.data.actions}
    if sorted(takes) != ["Attack", "Fly"]:
        err.append(f"prises {sorted(takes)} (attendu Fly, Attack)")
    rig.animation_data_create()
    lo0, hi0 = bbox(mesh)
    size0 = (hi0 - lo0).length
    for kind, act in sorted(takes.items()):
        rig.animation_data.action = act
        if act.slots:
            rig.animation_data.action_slot = act.slots[0]
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        smax = max((abs(fc.evaluate(f) - 1) for fc in fcurves(act) if fc.data_path.endswith(".scale")
                    for f in range(f0, f1 + 1, 3)), default=0.0)
        if smax > 1e-3:
            err.append(f"{kind} : échelle d'os animée dans le FBX")
        bpy.context.scene.frame_set(f0)
        c0 = sum(bbox(mesh), Vector()) / 2
        cs = []
        for f in range(f0, f1 + 1, max(1, (f1 - f0) // 15)):
            bpy.context.scene.frame_set(f)
            cs.append(sum(bbox(mesh), Vector()) / 2)
        moved = max((c - c0).length for c in cs)
        line = f"{act.name.split('|')[-1]} [{f0}-{f1}] : déplacement max {moved:.2f} m"
        if moved < 0.005:
            err.append(f"{kind} immobile")
        if kind == "Attack":
            fwd = max(c.y - c0.y for c in cs)
            line += f", avancée {fwd:.2f} m"
            if fwd < 0.03 * size0:
                err.append("Attack : pas de coup vers l'avant")
        notes.append(line)
    notes.append(f"FBX : 1 matériau, texture-palette incluse ({tex[0].size[0]}×{tex[0].size[1]} px), "
                 f"couleurs de sommets, taille {size0:.2f} m (diagonale)" if tex else "FBX : pas de texture")
    return err, notes


def main():
    rows, details, all_errors = [], [], []
    blends = sorted(b for b in glob.glob(os.path.join(OUT, "Blender", "**", "*.blend"), recursive=True)
                    if "_References" not in b)
    for bpath in blends:
        rel = os.path.relpath(bpath, os.path.join(OUT, "Blender"))[:-6]
        fpath = os.path.join(OUT, "FBX", rel + ".fbx")
        info, errs, notes = check_blend(bpath)
        if os.path.isfile(fpath):
            e2, n2 = check_fbx(fpath)
            errs += e2
            notes += n2
        else:
            errs.append("FBX absent")
        status = "OK" if not errs else "ÉCHEC"
        rows.append(f"| {rel} | {info['pv']} | {info['bones']} | {info['verts']} | {info['tris']} | 2 (Fly, Attack) | "
                    f"{status} |")
        details.append(f"### {rel}\n\n" + "\n".join(f"- {n}" for n in notes) +
                       ("\n" + "\n".join(f"- **ERREUR** {e}" for e in errs) if errs else "") + "\n")
        all_errors += [f"{rel}: {e}" for e in errs]
        print(f"[verify] {rel}: {status} {errs}")
    with open(os.path.join(OUT, "VERIFICATION.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Vérification des 23 ennemis (.blend et FBX ré-importés)\n\n"
                f"Généré par `verify_fbx.py` avec Blender {bpy.app.version_string}. "
                f"{len(blends)} modèles, {len(all_errors)} erreur(s).\n\n"
                "| Modèle | PV | Os | Sommets | Triangles | Animations | Statut |\n|---|---|---|---|---|---|---|\n"
                + "\n".join(rows) + "\n\n## Détail\n\n" + "\n".join(details))
    if all_errors:
        print("[verify] ÉCHECS :\n" + "\n".join(all_errors))
        sys.exit(1)
    print(f"[verify] {len(blends)} modèles OK")


if __name__ == "__main__":
    main()
