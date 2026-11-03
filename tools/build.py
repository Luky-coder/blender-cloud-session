"""Construit un modèle à partir de son script models/<nom>/build.py.

    blender -b --factory-startup -P tools/build.py -- models/<nom> [options]
    (ou plus simplement : bash tools/build.sh models/<nom> [options])

Étapes : scène vide -> exécution de build.py -> <nom>.blend
         -> screenshots/*.jpg + screenshots/preview.jpg -> README.md du modèle.
"""
import argparse
import ast
import os
import runpy
import sys
import time

import bpy

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)
import preview  # noqa: E402


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser(prog="tools/build.py")
    p.add_argument("model_dir", help="dossier du modèle, ex. models/table")
    p.add_argument("--samples", type=int, default=32, help="échantillons Cycles par vue (défaut 32)")
    p.add_argument("--width", type=int, default=800, help="largeur de chaque vue (défaut 800)")
    p.add_argument("--height", type=int, default=600, help="hauteur de chaque vue (défaut 600)")
    p.add_argument("--views", default=",".join(preview.DEFAULT_VIEWS),
                   help=f"vues séparées par des virgules, parmi {','.join(preview.VIEWS)}")
    p.add_argument("--no-render", action="store_true", help="ne pas faire les screenshots")
    return p.parse_args(argv)


def mesh_stats(scene):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    objects = verts = faces = 0
    for ob in scene.objects:
        if ob.type != "MESH" or ob.hide_render:
            continue
        ev = ob.evaluated_get(depsgraph)
        me = ev.to_mesh()
        objects += 1
        verts += len(me.vertices)
        faces += len(me.polygons)
        ev.to_mesh_clear()
    bounds = preview.scene_bounds(depsgraph)
    dims = (bounds[1] - bounds[0]) if bounds else None
    return objects, verts, faces, dims


def write_readme(model_dir, name, script, stats, views):
    with open(script, encoding="utf-8") as f:
        doc = ast.get_docstring(ast.parse(f.read())) or ""
    objects, verts, faces, dims = stats
    lines = [f"# {name}", ""]
    if doc:
        lines += [doc.strip(), ""]
    if os.path.isfile(os.path.join(model_dir, "screenshots", "preview.jpg")):
        lines += ["![Aperçu](screenshots/preview.jpg)", ""]
        if views:
            lines += ["Vues : " + " · ".join(f"[{v}](screenshots/{v}.jpg)" for v in views), ""]
    lines += ["| Fichier | Contenu |", "|---|---|",
              f"| [`{name}.blend`]({name}.blend) | Fichier Blender {bpy.app.version_string} |",
              "| [`build.py`](build.py) | Script qui génère le modèle |", ""]
    if dims is not None:
        lines.append(f"**Dimensions** : {dims.x:.3f} × {dims.y:.3f} × {dims.z:.3f} m (X × Y × Z) · "
                     f"**Objets** : {objects} · **Sommets** : {verts:,} · **Faces** : {faces:,}".replace(",", " "))
    with open(os.path.join(model_dir, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main():
    args = parse_args()
    model_dir = os.path.abspath(args.model_dir)
    name = os.path.basename(model_dir.rstrip("/\\"))
    script = os.path.join(model_dir, "build.py")
    if not os.path.isfile(script):
        raise FileNotFoundError(f"{script} introuvable")
    t_start = time.time()

    # 1. Scène vide, puis exécution du script du modèle
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0  # pas de fichiers .blend1
    sys.path.insert(0, model_dir)
    print(f"[build] exécution de {script}")
    runpy.run_path(script, run_name="__main__")
    scene = bpy.context.scene
    for ob in scene.objects:  # maillages nommés comme leur objet (sinon "Cylinder.003"…)
        if ob.data is not None and ob.type == "MESH" and ob.data.users == 1:
            ob.data.name = ob.name
    stats = mesh_stats(scene)

    # 2. Fichier Blender (avant d'ajouter caméras/lumières d'aperçu)
    blend_path = os.path.join(model_dir, f"{name}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)
    print(f"[build] {blend_path}")

    # 3. Screenshots
    views = [] if args.no_render else args.views.split(",")
    if views:
        preview.render_previews(os.path.join(model_dir, "screenshots"), views,
                                args.width, args.height, args.samples)

    # 4. README du modèle
    write_readme(model_dir, name, script, stats, views)
    objects, verts, faces, dims = stats
    size = f"{dims.x:.3f} x {dims.y:.3f} x {dims.z:.3f} m" if dims is not None else "scène vide"
    print(f"[build] OK en {time.time() - t_start:.1f}s : {objects} objets, {verts} sommets, {faces} faces, {size}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        traceback.print_exc()
        print("[build] ÉCHEC", file=sys.stderr)
        sys.exit(1)
