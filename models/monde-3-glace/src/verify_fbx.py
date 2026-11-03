"""Vérifie des FBX en les ré-important dans une scène vide.

    blender -b --factory-startup -q -P src/verify_fbx.py -- World_3_Glace/FBX [rapport.json]

Pour chaque fichier : maillages, os, shape keys, prises d'animation (Actions) avec leur durée,
présence de courbes d'os et de courbes de shape keys, et contrôle que les poses bougent bien.
"""
import json
import os
import sys

import bpy

REQUIRED = ["IDLE", "MOVE", "ATTACK", "HIT", "DEATH"]


def channelbag_curves(act):
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                out.extend(cb.fcurves)
    return out


def check(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path, use_anim=True)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    res = dict(file=os.path.basename(path), meshes=len(meshes), armatures=len(arms), errors=[])
    if len(meshes) != 1 or len(arms) != 1:
        res["errors"].append(f"{len(meshes)} maillage(s), {len(arms)} armature(s)")
    if meshes:
        me = meshes[0].data
        res["verts"] = len(me.vertices)
        res["materials"] = len(me.materials)
        res["shape_keys"] = [k.name for k in me.shape_keys.key_blocks[1:]] if me.shape_keys else []
        res["vertex_groups"] = len(meshes[0].vertex_groups)
        if meshes[0].parent not in arms:
            res["errors"].append("maillage non parenté à l'armature")
    if arms:
        res["bones"] = len(arms[0].data.bones)
    takes = {}
    for act in bpy.data.actions:
        curves = channelbag_curves(act)
        bone_c = [c for c in curves if c.data_path.startswith("pose.bones")]
        key_c = [c for c in curves if c.data_path.startswith("key_blocks")]
        moving = sum(1 for c in bone_c if len({round(k.co[1], 4) for k in c.keyframe_points}) > 1)
        short = act.name.split("|")[-1]
        entry = takes.setdefault(short, dict(frames=0, bone_curves=0, moving_bone_curves=0, shape_curves=0))
        entry["frames"] = max(entry["frames"], int(act.frame_range[1] - act.frame_range[0] + 1))
        entry["bone_curves"] += len(bone_c)
        entry["moving_bone_curves"] += moving
        entry["shape_curves"] += len(key_c)
    res["takes"] = takes
    for name in REQUIRED:
        if name not in takes:
            res["errors"].append(f"prise {name} absente")
        elif takes[name]["moving_bone_curves"] == 0:
            res["errors"].append(f"prise {name} immobile")
    if takes.get("DEATH", {}).get("shape_curves", 0) == 0:
        res["errors"].append("pas de courbes de shape keys dans DEATH")
    return res


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    root = argv[0]
    out = argv[1] if len(argv) > 1 else None
    files = []
    for d, _, fs in os.walk(root):
        files += [os.path.join(d, f) for f in fs if f.lower().endswith(".fbx")]
    results = [check(f) for f in sorted(files)]
    for r in results:
        tk = ", ".join(f"{k}({v['frames']}f, os:{v['moving_bone_curves']}, sk:{v['shape_curves']})"
                       for k, v in r["takes"].items())
        status = "OK " if not r["errors"] else "ERR"
        print(f"[verif] {status} {r['file']}: {r.get('verts')} sommets, {r.get('bones')} os, "
              f"shape keys {r.get('shape_keys')}, prises : {tk} {r['errors'] or ''}")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=1)
    print(f"[verif] {sum(1 for r in results if not r['errors'])}/{len(results)} FBX valides")


if __name__ == "__main__":
    main()
