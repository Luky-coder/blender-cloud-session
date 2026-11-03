"""Rendus d'aperçu (Cycles CPU) : vue héros 3/4 avant et images clés des animations.

Tout ce qui est ajouté ici (caméra, lumières, sol, monde) est temporaire : appeler après l'enregistrement du .blend.
"""
import math
import os

import bpy
from mathutils import Vector

PREFIX = "_apercu_"


def _bounds(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for ob in objs:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        for v in me.vertices:
            p = ev.matrix_world @ v.co
            lo = Vector(map(min, lo, p))
            hi = Vector(map(max, hi, p))
        ev.to_mesh_clear()
    return lo, hi


def setup(width, height, samples, ground=True, ground_z=None):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.transmission_bounces = 6
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.use_persistent_data = True
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"

    world = bpy.data.worlds.new(PREFIX + "ciel")
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.66, 0.80, 0.95, 1)
    bg.inputs["Strength"].default_value = 0.9
    scene.world = world

    for name, rot, energy, angle in (("cle", (math.radians(50), 0, math.radians(150)), 3.6, 6),
                                     ("contre", (math.radians(60), 0, math.radians(-30)), 1.6, 12),
                                     ("bouche", (math.radians(75), 0, math.radians(250)), 0.6, 30)):
        data = bpy.data.lights.new(PREFIX + name, "SUN")
        data.energy = energy
        data.angle = math.radians(angle)
        ob = bpy.data.objects.new(PREFIX + name, data)
        ob.rotation_euler = rot
        scene.collection.objects.link(ob)

    if ground:
        me = bpy.data.meshes.new(PREFIX + "sol")
        s = 200
        me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
        ob = bpy.data.objects.new(PREFIX + "sol", me)
        ob.location.z = ground_z or 0.0
        m = bpy.data.materials.new(PREFIX + "herbe")
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = (0.22, 0.36, 0.14, 1)
        b.inputs["Roughness"].default_value = 0.9
        me.materials.append(m)
        scene.collection.objects.link(ob)


def camera(name, target_lo, target_hi, azimuth, elevation, lens=50, margin=1.15):
    """Caméra cadrant la boîte. Azimut 0 = face avant (caméra côté +Y), 90 = côté droit du modèle (-X)."""
    scene = bpy.context.scene
    center = (target_lo + target_hi) / 2
    az, el = math.radians(azimuth), math.radians(elevation)
    d = Vector((-math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    data = bpy.data.cameras.new(PREFIX + name)
    data.lens = lens
    radius = (target_hi - target_lo).length / 2
    data.clip_start = radius * 0.01
    data.clip_end = radius * 400
    cam = bpy.data.objects.new(PREFIX + name, data)
    scene.collection.objects.link(cam)
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cam.location = center + d * radius * 4
    bpy.context.view_layer.update()
    corners = [Vector((x, y, z)) for x in (target_lo.x, target_hi.x) for y in (target_lo.y, target_hi.y)
               for z in (target_lo.z, target_hi.z)]
    loc, _ = cam.camera_fit_coords(bpy.context.evaluated_depsgraph_get(), [c for v in corners for c in v])
    cam.location = center + (Vector(loc) - center) * margin
    scene.camera = cam
    return cam


def render_to(path):
    scene = bpy.context.scene
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def hero(mesh, path, width=900, height=900, samples=48, azimuth=32, elevation=8):
    lo, hi = _bounds([mesh])
    setup(width, height, samples, ground_z=0.0)
    camera("hero", lo, hi, azimuth, elevation, lens=60, margin=1.1)
    return render_to(path)
