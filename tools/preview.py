"""Rendu d'aperçus (screenshots) d'une scène Blender en headless, avec Cycles sur CPU.

Deux usages :
  1. importé par tools/build.py ;
  2. sur un .blend existant :
       blender -b --factory-startup chemin/fichier.blend -P tools/preview.py -- --out chemin/screenshots

Les caméras, lumières et le monde d'aperçu sont ajoutés en mémoire seulement :
ce script ne réenregistre jamais le .blend.
"""
import argparse
import math
import os
import sys
import time

import bpy
from mathutils import Vector

# nom -> (azimut en degrés, élévation en degrés, orthographique ?)
# Azimut 0 = face avant (caméra côté -Y, regarde vers +Y) ; 90 = côté droit (+X).
VIEWS = {
    "iso": (40, 25, False),
    "iso_back": (220, 25, False),
    "front": (0, 0, True),
    "back": (180, 0, True),
    "right": (90, 0, True),
    "left": (-90, 0, True),
    "top": (0, 90, True),
}
DEFAULT_VIEWS = ["iso", "front", "right", "top"]

RENDERABLE = {"MESH", "CURVE", "SURFACE", "META", "FONT", "CURVES", "POINTCLOUD", "VOLUME", "GREASEPENCIL"}
MARGIN = 1.12
PREFIX = "_preview_"


def scene_bounds(depsgraph):
    """Boîte englobante (min, max) en coordonnées monde de tout ce qui est rendu, instances comprises."""
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    found = False
    for inst in depsgraph.object_instances:
        ob = inst.object
        if ob.type not in RENDERABLE or ob.original.hide_render:
            continue
        mw = inst.matrix_world.copy()
        for corner in ob.bound_box:
            p = mw @ Vector(corner)
            lo = Vector(map(min, lo, p))
            hi = Vector(map(max, hi, p))
            found = True
    return (lo, hi) if found else None


def _direction(azimuth, elevation):
    """Vecteur unitaire allant du centre de l'objet vers la caméra."""
    az, el = math.radians(azimuth), math.radians(elevation)
    return Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))


def _setup_render(scene, width, height, samples):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.use_persistent_data = True  # garde le BVH entre les vues
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"


def _ensure_lighting(scene):
    """Ajoute un monde gris et deux soleils si la scène n'a pas son propre éclairage."""
    if scene.world is None:
        world = bpy.data.worlds.new(PREFIX + "world")
        bg = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)
        if bg is not None:
            bg.inputs["Color"].default_value = (0.62, 0.64, 0.68, 1.0)
            bg.inputs["Strength"].default_value = 0.7
        scene.world = world

    has_light = any(o.type == "LIGHT" and not o.hide_render for o in scene.objects)
    if has_light:
        return
    # (azimut, élévation de la position du soleil, puissance, angle)
    for name, az, el, strength, angle in (("key", -35, 50, 3.5, 8), ("rim", 150, 30, 1.2, 15)):
        data = bpy.data.lights.new(PREFIX + name, "SUN")
        data.energy = strength
        data.angle = math.radians(angle)
        ob = bpy.data.objects.new(PREFIX + name, data)
        ob.rotation_euler = (-_direction(az, el)).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(ob)


def _setup_camera(scene, name, azimuth, elevation, ortho, lo, hi):
    center = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 1e-3)
    d = _direction(azimuth, elevation)

    data = bpy.data.cameras.new(PREFIX + name)
    data.type = "ORTHO" if ortho else "PERSP"
    data.lens = 50
    data.clip_start = radius * 0.01
    data.clip_end = radius * 100
    cam = bpy.data.objects.new(PREFIX + name, data)
    scene.collection.objects.link(cam)

    if elevation >= 89.9:
        cam.rotation_euler = (0.0, 0.0, 0.0)  # regarde vers -Z, l'arrière (+Y) en haut de l'image
    else:
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]

    if ortho:
        # Projette la boîte sur les axes droite/haut de la caméra et cadre exactement.
        rot = cam.rotation_euler.to_matrix()
        right, up, back = rot.col[0], rot.col[1], rot.col[2]
        xs = [c.dot(right) for c in corners]
        ys = [c.dot(up) for c in corners]
        ew, eh = max(xs) - min(xs), max(ys) - min(ys)
        w, h = scene.render.resolution_x, scene.render.resolution_y
        # ortho_scale couvre la plus grande dimension de l'image (sensor_fit AUTO)
        data.ortho_scale = max(ew, eh * w / h) * MARGIN if w >= h else max(eh, ew * h / w) * MARGIN
        cam.location = (right * (max(xs) + min(xs)) / 2 + up * (max(ys) + min(ys)) / 2
                        + back * (center.dot(back) + radius * 3))
    else:
        cam.location = center + d * radius * 3
        bpy.context.view_layer.update()
        flat = [c for v in corners for c in v]
        loc, _ = cam.camera_fit_coords(bpy.context.evaluated_depsgraph_get(), flat)
        cam.location = center + (Vector(loc) - center) * MARGIN
    return cam


def make_grid(paths, out_path, cols=2):
    """Assemble plusieurs PNG de même taille en une grille (ordre de lecture : gauche->droite, haut->bas)."""
    import numpy as np

    images = [bpy.data.images.load(p, check_existing=False) for p in paths]
    w, h = images[0].size
    rows = math.ceil(len(images) / cols)
    canvas = np.ones((rows * h, cols * w, 4), dtype=np.float32)
    for i, img in enumerate(images):
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        r, c = divmod(i, cols)
        y0 = (rows - 1 - r) * h  # les pixels Blender partent du bas de l'image
        canvas[y0:y0 + h, c * w:(c + 1) * w] = px.reshape(h, w, 4)
    grid = bpy.data.images.new(PREFIX + "grid", cols * w, rows * h, alpha=False)
    grid.pixels.foreach_set(canvas.ravel())
    grid.filepath_raw = out_path
    grid.file_format = "PNG"
    grid.save()
    for img in images + [grid]:
        bpy.data.images.remove(img)


def render_previews(out_dir, views=None, width=800, height=600, samples=32):
    """Rend chaque vue dans out_dir/<vue>.png, plus out_dir/preview.png (grille de toutes les vues)."""
    views = views or DEFAULT_VIEWS
    unknown = [v for v in views if v not in VIEWS]
    if unknown:
        raise ValueError(f"Vue(s) inconnue(s) : {unknown}. Disponibles : {list(VIEWS)}")

    scene = bpy.context.scene
    bounds = scene_bounds(bpy.context.evaluated_depsgraph_get())
    if bounds is None:
        raise RuntimeError("Rien à rendre : la scène ne contient aucun objet visible au rendu.")
    lo, hi = bounds

    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):  # supprime les anciennes captures
        if f.endswith(".png"):
            os.remove(os.path.join(out_dir, f))

    _setup_render(scene, width, height, samples)
    _ensure_lighting(scene)

    paths = []
    for name in views:
        t0 = time.time()
        az, el, ortho = VIEWS[name]
        scene.camera = _setup_camera(scene, name, az, el, ortho, lo, hi)
        path = os.path.join(out_dir, f"{name}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        paths.append(path)
        print(f"[preview] {name}: {path} ({time.time() - t0:.1f}s)")

    grid_path = os.path.join(out_dir, "preview.png")
    make_grid(paths, grid_path, cols=2 if len(paths) > 1 else 1)
    print(f"[preview] grille : {grid_path}")
    return paths, grid_path


def _main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser(prog="tools/preview.py", description="Rend des aperçus du .blend ouvert.")
    p.add_argument("--out", required=True, help="dossier de sortie des PNG")
    p.add_argument("--views", default=",".join(DEFAULT_VIEWS), help=f"vues parmi {','.join(VIEWS)}")
    p.add_argument("--width", type=int, default=800)
    p.add_argument("--height", type=int, default=600)
    p.add_argument("--samples", type=int, default=32)
    a = p.parse_args(argv)
    render_previews(os.path.abspath(a.out), a.views.split(","), a.width, a.height, a.samples)


if __name__ == "__main__":
    try:
        _main()
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
