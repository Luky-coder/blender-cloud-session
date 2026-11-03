"""Génère le Monde 2 : références, 23 .blend, 23 FBX, aperçus et planches d'animation.

    blender -b --factory-startup --python-exit-code 1 -P models/monde2-desert/export_all.py -- [options]

Options :
  --only cactus,pyramide,dirigeable,scaraballon,oasis   familles à traiter (défaut : toutes)
  --elements Plante,Feu                                  types à traiter (familles A à C)
  --no-render                                            pas d'aperçus
  --samples N  --width W --height H                      qualité des aperçus
Sortie : models/monde2-desert/World_2_Desert/{Blender,FBX,Textures,Previews}
"""
import argparse
import os
import shutil
import sys
import tempfile
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "tools"))

import preview  # noqa: E402

from desert import core, family  # noqa: E402
from desert.elements import ELEMENTS, ORDER  # noqa: E402

OUT = os.path.join(HERE, "World_2_Desert")


FAMILIES = {  # clé : (module, types)
    "cactus": ("cactus", ORDER),
    "pyramide": ("pyramid", ORDER),
    "dirigeable": ("airship", ORDER),
    "scaraballon": ("scarab", ["Plante"]),
    "oasis": ("oasis", ["Plante"]),
}


def load_family(key):
    import importlib
    mod, elems = FAMILIES[key]
    return importlib.import_module("desert." + mod).FAMILY, list(elems)


def paths(fam, elem):
    if getattr(fam, "boss_file", None):
        stem = fam.boss_file
        return (os.path.join(OUT, "Blender", stem + ".blend"), os.path.join(OUT, "FBX", stem + ".fbx"),
                os.path.join(OUT, "Previews", stem))
    return (os.path.join(OUT, "Blender", fam.key, elem + ".blend"),
            os.path.join(OUT, "FBX", fam.key, elem + ".fbx"),
            os.path.join(OUT, "Previews", fam.key, elem))


def preview_world():
    w = bpy.data.worlds.new("_preview_desert")
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (*core.lin("#E9D8BE"), 1.0)
    bg.inputs["Strength"].default_value = 0.75
    bpy.context.scene.world = w


def render_variant(rig, key, acts, fam, stem, args):
    """Grille 4 vues (Idle image 1) + planche d'animation (images clés de chaque action)."""
    scene = bpy.context.scene
    preview_world()
    tmp = tempfile.mkdtemp()
    views = ["iso_back", "back", "right", "iso"]
    core.assign_action(rig, key, acts[0])
    scene.frame_set(1)
    preview.render_previews(tmp, views, args.width, args.height, args.samples)
    os.makedirs(os.path.dirname(stem), exist_ok=True)
    shutil.copy(os.path.join(tmp, "preview.jpg"), stem + ".jpg")

    # planche d'animation : caméra fixe 3/4 avant, cadrage élargi pour les déplacements
    lo, hi = preview.scene_bounds(bpy.context.evaluated_depsgraph_get())
    pad = (hi - lo) * 0.0
    lo2, hi2 = lo - pad, hi + pad
    hi2.y += (hi - lo).y * fam.anim_pad_forward
    for ob in [o for o in scene.objects if o.name.startswith(preview.PREFIX) and o.type == "CAMERA"]:
        bpy.data.objects.remove(ob)
    cam = preview._setup_camera(scene, "anim", 215, 18, False, lo2, hi2)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = args.anim_width, args.anim_height
    shots = []
    for act in acts:
        suffix = act.name[len(rig.name) + 1:]
        for f in fam.anim_frames.get(suffix, fam.anim_frames.get("_default", (1,))):
            shots.append((act, suffix, f))
    paths_ = []
    for i, (act, suffix, f) in enumerate(shots):
        core.assign_action(rig, key, act)
        scene.frame_set(f)
        pth = os.path.join(tmp, f"anim_{i:02d}.jpg")
        scene.render.filepath = pth
        bpy.ops.render.render(write_still=True)
        paths_.append(pth)
    preview.make_grid(paths_, stem + "_anim.jpg", cols=fam.anim_cols)
    shutil.rmtree(tmp, ignore_errors=True)
    core.assign_action(rig, key, acts[0])
    scene.frame_set(1)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--only", default="")
    p.add_argument("--elements", default="")
    p.add_argument("--no-render", action="store_true")
    p.add_argument("--samples", type=int, default=24)
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--anim-width", type=int, default=360)
    p.add_argument("--anim-height", type=int, default=300)
    args = p.parse_args(argv)
    keys = [k for k in args.only.split(",") if k] or list(FAMILIES)
    for k in keys:
        fam, elems = load_family(k)
        if args.elements:
            elems = [e for e in args.elements.split(",") if e in elems]
        t0 = time.time()
        ref = os.path.join(OUT, "Blender", "_References", fam.key + "_Reference.blend")
        family.build_reference(fam, ref)
        print(f"[monde2] référence {fam.key} ({time.time() - t0:.1f}s)")
        for e in elems:
            t1 = time.time()
            blend, fbx, stem = paths(fam, e)
            rig, mesh, key, acts = family.build_variant(fam, e, ref, blend, fbx)
            nv, nf = len(mesh.data.vertices), sum(len(pp.vertices) - 2 for pp in mesh.data.polygons)
            print(f"[monde2] {fam.key}/{e} : {nv} sommets, {nf} triangles, {len(acts)} actions, "
                  f"{len(rig.pose.bones)} os ({time.time() - t1:.1f}s)")
            if not args.no_render:
                t2 = time.time()
                render_variant(rig, key, acts, fam, stem, args)
                print(f"[monde2] aperçus {fam.key}/{e} ({time.time() - t2:.1f}s)")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
