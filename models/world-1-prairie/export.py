"""Génère les ennemis du Monde 1 : .blend individuels, FBX animés et aperçus.

    blender -b --factory-startup -P models/world-1-prairie/export.py -- [cibles] [options]

Cibles : "all" (défaut), "classique:plante", "etoile:all", "montgolfiere", "zeppelin"...
Options : --no-fbx, --no-render, --no-sheet, --gif, --samples N

Sorties (dans models/world-1-prairie/World_1_Prairie/) :
    Blender/<Famille>/<Type>.blend   Blender/MiniBoss_...blend  Blender/Boss_...blend
    FBX/<Famille>/<Type>.fbx         (5 prises : Idle, Move, Attack, Hit, Death)
    Previews/<Famille>/<Type>.jpg    vue 3/4 avant
    Previews/<Famille>/<Type>_Animations.jpg  images clés des 5 animations
"""
import json
import os
import subprocess
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from prairie import anim, enemy, palette, render  # noqa: E402

OUT = os.path.join(HERE, "World_1_Prairie")
SCRATCH = os.environ.get("PRAIRIE_TMP", os.path.join(HERE, ".frames"))
ORDER = ["lumiere", "tenebres", "glace", "feu", "eau", "plante", "eclair"]


def targets(args):
    out = []
    for a in args or ["all"]:
        if a == "all":
            out += [(f, e) for f in enemy.FAMILIES for e in ORDER] + [("montgolfiere", "plante"), ("zeppelin", "plante")]
        elif a in enemy.BOSSES:
            out.append((a, "plante"))
        else:
            f, e = a.split(":")
            out += [(f, x) for x in (ORDER if e == "all" else [e])]
    return out


def paths(family, element):
    if family in enemy.BOSSES:
        base = enemy.BOSSES[family][1]
        return (os.path.join(OUT, "Blender", base + ".blend"), os.path.join(OUT, "FBX", base + ".fbx"),
                os.path.join(OUT, "Previews", base))
    folder = enemy.FAMILIES[family][1]
    t = enemy.ELEMENTS[element][1]
    return (os.path.join(OUT, "Blender", folder, t + ".blend"), os.path.join(OUT, "FBX", folder, t + ".fbx"),
            os.path.join(OUT, "Previews", folder, t))


def export_fbx(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=False, object_types={"ARMATURE", "MESH"}, use_custom_props=True,
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y",
        mesh_smooth_type="FACE", use_mesh_modifiers=False, add_leaf_bones=False, primary_bone_axis="Y",
        secondary_bone_axis="X", use_armature_deform_only=False, armature_nodetype="NULL",
        bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0,
        bake_anim_simplify_factor=0.0, path_mode="COPY", embed_textures=True, colors_type="SRGB")


def key_frames(F):
    A = anim.PARAMS[F.kind]
    n = {k: A[k] for k in ("idle", "move", "attack", "hit", "death")}
    a = n["attack"]
    a1, a2, a3, a4 = (round(a * x) for x in (0.30, 0.42, 0.50, 0.66))
    h = n["hit"]
    d = n["death"]
    return [
        ("Idle", [0, n["idle"] // 4, n["idle"] // 2, 3 * n["idle"] // 4]),
        ("Move", [0, n["move"] // 4, n["move"] // 2, 3 * n["move"] // 4]),
        ("Attack", [0, a1, (a1 + a2) // 2, a2, a3, a4, round(a * 0.82), a]),
        ("Hit", [0, max(2, round(h * 0.12)), round(h * 0.35), round(h * 0.6), h]),
        ("Death", [0, round(d * 0.1), round(d * 0.3), round(d * 0.5), round(d * 0.7), round(d * 0.88), d]),
    ]


def anim_bounds(arm, mesh):
    scene = bpy.context.scene
    lo = hi = None
    for act in bpy.data.actions:
        arm.animation_data.action = act
        for f in range(int(act.frame_start), int(act.frame_end) + 1, 3):
            scene.frame_set(f)
            l, h = render._bounds([mesh])
            lo = l if lo is None else type(l)(map(min, lo, l))
            hi = h if hi is None else type(h)(map(max, hi, h))
    return lo, hi


def render_sheet(arm, mesh, F, prefix, samples, gif=False):
    """Images clés des animations, vues de 3/4 côté (l'avant +Y part vers la droite de l'image)."""
    scene = bpy.context.scene
    lo, hi = anim_bounds(arm, mesh)
    render.setup(400, 300, samples, ground_z=0.0)
    render.camera("planche", lo, hi, -66, 6, lens=50, margin=1.0)
    tiles = {}
    tmp = os.path.join(SCRATCH, os.path.basename(prefix))
    for name, frames in key_frames(F):
        act = bpy.data.actions[name]
        arm.animation_data.action = act
        tiles[name] = []
        for f in frames:
            scene.frame_set(int(act.frame_start) + f)
            p = render.render_to(os.path.join(tmp, f"{name}_{f:03d}.jpg"))
            tiles[name].append((f, p))
    gif_frames = []
    if gif:
        act = bpy.data.actions["Attack"]
        arm.animation_data.action = act
        scene.render.resolution_x, scene.render.resolution_y = 360, 270
        for f in range(int(act.frame_start), int(act.frame_end) + 1):
            scene.frame_set(f)
            gif_frames.append(render.render_to(os.path.join(tmp, f"gif_{f:03d}.jpg")))
    arm.animation_data.action = bpy.data.actions["Idle"]
    scene.frame_set(1)
    return tiles, gif_frames


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = {a for a in argv if a.startswith("--")}
    samples = 48
    if "--samples" in argv:
        samples = int(argv[argv.index("--samples") + 1])
    args = [a for a in argv if not a.startswith("--") and not a.isdigit()]
    report = []
    for family, element in targets(args):
        t0 = time.time()
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.preferences.filepaths.save_version = 0
        arm, mesh, F = enemy.build_enemy(family, element)
        blend, fbx, prev = paths(family, element)
        os.makedirs(os.path.dirname(blend), exist_ok=True)
        # Couleurs exportables : texture palette (PNG à côté du FBX et incrustée dedans) + UV + couleurs de sommets
        img = palette.bake(mesh, enemy.enemy_id(family, element) + "_Palette",
                           os.path.splitext(fbx)[0] + "_Palette.png")
        if "--no-fbx" not in opts:
            export_fbx(fbx)
        img.pack()
        bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
        info = dict(id=enemy.enemy_id(family, element), name=arm["Nom"], element=arm["Element"], pv=arm["PV"],
                    verts=len(mesh.data.vertices), tris=sum(len(p.vertices) - 2 for p in mesh.data.polygons),
                    bones=len(arm.data.bones), materials=len(mesh.data.materials),
                    actions={a.name: [int(a.frame_start), int(a.frame_end)] for a in bpy.data.actions},
                    blend=os.path.relpath(blend, OUT), fbx=os.path.relpath(fbx, OUT))
        if "--no-render" not in opts:
            os.makedirs(os.path.dirname(prev), exist_ok=True)
            tiles = gif_frames = None
            if "--no-sheet" not in opts:
                tiles, gif_frames = render_sheet(arm, mesh, F, prev, max(8, samples // 4), "--gif" in opts)
            for ob in list(bpy.data.objects):
                if ob.name.startswith(render.PREFIX):
                    bpy.data.objects.remove(ob)
            render.hero(mesh, prev + ".jpg", 900, 900, samples)
            if tiles:
                job = dict(title=f"{arm['Nom']}  ·  {arm['Element']}  ·  {arm['PV']} PV", tiles=tiles,
                           out=prev + "_Animations.jpg", gif=gif_frames, gif_out=prev + "_Attack.gif")
                jp = os.path.join(SCRATCH, os.path.basename(prev) + ".json")
                with open(jp, "w") as fh:
                    json.dump(job, fh)
                subprocess.run(["python3", os.path.join(HERE, "compose.py"), jp], check=True)
        info["seconds"] = round(time.time() - t0, 1)
        report.append(info)
        print("[prairie]", json.dumps(info, ensure_ascii=False))
    os.makedirs(OUT, exist_ok=True)
    rp = os.path.join(OUT, "inventaire.json")
    old = []
    if os.path.isfile(rp):
        with open(rp) as fh:
            old = [r for r in json.load(fh) if r["id"] not in {x["id"] for x in report}]
    order = [enemy.enemy_id(f, e) for f, e in targets(["all"])]
    allr = sorted(old + report, key=lambda r: order.index(r["id"]) if r["id"] in order else 99)
    for r in allr:
        r.pop("seconds", None)
    with open(rp, "w", encoding="utf-8") as fh:
        json.dump(allr, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
