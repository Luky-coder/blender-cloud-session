"""Vérifie les FBX et les .blend du Monde 2 : ré-import, os, maillage, shape keys, actions et mouvement.

    blender -b --factory-startup --python-exit-code 1 -P models/monde2-desert/verify_fbx.py

Pour chaque ennemi :
- .blend : actions présentes (avec slot armature + slot shape keys), plage d'images, os keyés ;
- FBX ré-importé : armature, maillage skinné, shape keys Degonfle/Gonfle, une prise par action ;
- mouvement mesuré sur le maillage déformé : Idle qui boucle, Attack qui avance (+Y), Hit qui recule,
  Death qui se ratatine jusqu'à disparaître ; valeur de la shape key Degonfle en fin de Death.
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


def fcurves(act):
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                out += [(cb.slot, fc) for fc in cb.fcurves]
    return out


def bbox(mesh_ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh_ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = mesh_ob.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    lo = Vector(map(min, *pts)) if len(pts) > 1 else pts[0]
    hi = Vector(map(max, *pts)) if len(pts) > 1 else pts[0]
    return lo, hi


def check_blend(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh = next(o for o in bpy.data.objects if o.type == "MESH")
    acts = sorted(a.name for a in bpy.data.actions)
    errors = []
    loops = []
    for a in bpy.data.actions:
        kinds = {s.target_id_type for s in a.slots}
        if kinds != {"OBJECT"}:
            errors.append(f"{a.name}: slots {kinds}")
        fcs = [fc for _, fc in fcurves(a)]
        bones = {fc.data_path.split('"')[1] for fc in fcs if fc.data_path.startswith("pose.bones")}
        if len(bones) != len(rig.pose.bones):
            errors.append(f"{a.name}: {len(bones)}/{len(rig.pose.bones)} os keyés")
        if a.use_cyclic:  # boucle : image N+1 identique à l'image 1 sur toutes les courbes
            f0, f1 = a.frame_range
            def gap_of(fc):
                g = abs(fc.evaluate(f1 + 1) - fc.evaluate(f0))
                if fc.data_path.endswith("rotation_euler"):  # tours complets (orbites, hélices)
                    g = abs(g - 2 * math.pi * round(g / (2 * math.pi)))
                return g
            gap = max(gap_of(fc) for fc in fcs)
            loops.append(f"{a.name} : boucle {int(f0)}-{int(f1)}, écart N+1/1 = {gap:.4f}")
            if gap > 1e-3:
                errors.append(f"{a.name} : la boucle ne se referme pas ({gap:.4f})")
    drivers = mesh.data.shape_keys.animation_data.drivers if mesh.data.shape_keys and \
        mesh.data.shape_keys.animation_data else []
    if len(drivers) < 2:
        errors.append("drivers des shape keys absents")
    keys = [k.name for k in mesh.data.shape_keys.key_blocks] if mesh.data.shape_keys else []
    if "Degonfle" not in keys or "Gonfle" not in keys:
        errors.append("shape keys manquantes")
    mods = [m.type for m in mesh.modifiers]
    if mods != ["ARMATURE"]:
        errors.append(f"modificateurs {mods}")
    info = dict(actions=acts, bones=len(rig.pose.bones), verts=len(mesh.data.vertices),
                tris=sum(len(p.vertices) - 2 for p in mesh.data.polygons), mats=len(mesh.data.materials),
                pv=rig.get("PV"), shape_keys=keys[1:], loops=loops)
    return info, errors


def check_fbx(path, expected_actions):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    rig = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
    mesh = next((o for o in bpy.data.objects if o.type == "MESH"), None)
    errors, notes = [], []
    if rig is None or mesh is None:
        return ["armature ou maillage absent"], notes
    if not any(m.type == "ARMATURE" for m in mesh.modifiers):
        errors.append("maillage non skinné")
    sk = [k.name for k in mesh.data.shape_keys.key_blocks] if mesh.data.shape_keys else []
    if "Degonfle" not in sk:
        errors.append("shape key Degonfle absente du FBX")
    arm_acts = {a.name.split("|")[-1]: a for a in bpy.data.actions if a.name.startswith(rig.name + "|")
                or (a.name.count("|") == 2 and not a.name.startswith("Key"))}
    key_acts = {a.name.split("|")[-1]: a for a in bpy.data.actions if a.name.startswith("Key")}
    missing = [n for n in expected_actions if n not in arm_acts]
    if missing:
        errors.append(f"prises manquantes : {missing}")
    rig.animation_data_create()
    size0 = None
    for name, act in sorted(arm_acts.items()):
        rig.animation_data.action = act
        slot = next((s for s in act.slots), None)
        if slot:
            rig.animation_data.action_slot = slot
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        bpy.context.scene.frame_set(f0)
        lo0, hi0 = bbox(mesh)
        size0 = (hi0 - lo0).length
        c0 = (lo0 + hi0) / 2
        samples = []
        for f in range(f0, f1 + 1, max(1, (f1 - f0) // 12)):
            bpy.context.scene.frame_set(f)
            lo, hi = bbox(mesh)
            samples.append(((lo + hi) / 2, (hi - lo).length))
        bpy.context.scene.frame_set(f1)
        lo1, hi1 = bbox(mesh)
        size1, c1 = (hi1 - lo1).length, (lo1 + hi1) / 2
        moved = max((c - c0).length for c, _ in samples)
        fwd = max(c.y - c0.y for c, _ in samples)
        back = min(c.y - c0.y for c, _ in samples)
        kind = name.rsplit("_", 1)[-1]
        line = f"{name} [{f0}-{f1}] déplacement max {moved:.2f} m"
        if kind == "Idle" or kind == "Move":
            if moved < 0.005:
                errors.append(f"{name} immobile")
        if kind == "Attack" or name.endswith("Charge"):
            line += f", avancée max {fwd:.2f} m"
            if fwd < 0.05 * size0:
                errors.append(f"{name} : pas de coup vers l'avant (+Y)")
        if kind == "Hit":
            line += f", recul {back:.2f} m"
            if back > -0.01:
                errors.append(f"{name} : pas de recul")
        if kind == "Death":
            line += f", taille finale {size1 / size0 * 100:.1f} %"
            if size1 > 0.05 * size0:
                errors.append(f"{name} : ne disparaît pas")
            ka = key_acts.get(name)
            if ka:
                fcs = [fc for _, fc in fcurves(ka) if "Degonfle" in fc.data_path]
                if fcs:
                    v = fcs[0].evaluate(f1)
                    line += f", Degonfle fin = {v:.2f}"
                    if v < 0.9:
                        errors.append(f"{name} : shape key Degonfle non animée dans le FBX")
        notes.append(line)
    return errors, notes


def main():
    rows, all_errors, details = [], [], []
    blends = sorted(glob.glob(os.path.join(OUT, "Blender", "**", "*.blend"), recursive=True))
    blends = [b for b in blends if "_References" not in b]
    for bpath in blends:
        rel = os.path.relpath(bpath, os.path.join(OUT, "Blender"))
        fpath = os.path.join(OUT, "FBX", rel[:-6] + ".fbx")
        info, errs = check_blend(bpath)
        expected = info["actions"]
        if not os.path.isfile(fpath):
            errs.append("FBX absent")
            notes = []
        else:
            e2, notes = check_fbx(fpath, expected)
            errs += e2
        notes = info["loops"] + notes
        status = "OK" if not errs else "ÉCHEC"
        rows.append(f"| {rel[:-6]} | {info['pv']} | {info['bones']} | {info['verts']} | {info['tris']} | "
                    f"{info['mats']} | {len(info['actions'])} | {status} |")
        details.append(f"### {rel[:-6]}\n\n" + "\n".join(f"- {n}" for n in notes) +
                       ("\n" + "\n".join(f"- **ERREUR** {e}" for e in errs) if errs else "") + "\n")
        all_errors += [f"{rel}: {e}" for e in errs]
        print(f"[verify] {rel}: {status} {errs}")
    with open(os.path.join(OUT, "VERIFICATION.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Vérification des 23 ennemis (FBX ré-importés)\n\n")
        f.write(f"Généré par `verify_fbx.py` avec Blender {bpy.app.version_string}. "
                f"{len(blends)} modèles, {len(all_errors)} erreur(s).\n\n")
        f.write("| Modèle | PV | Os | Sommets | Triangles | Matériaux | Actions | Statut |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        f.write("\n".join(rows) + "\n\n## Détail des animations (mesurées sur le maillage déformé du FBX)\n\n")
        f.write("\n".join(details))
    if all_errors:
        print("[verify] ÉCHECS :\n" + "\n".join(all_errors))
        sys.exit(1)
    print(f"[verify] {len(blends)} modèles OK")


if __name__ == "__main__":
    main()
