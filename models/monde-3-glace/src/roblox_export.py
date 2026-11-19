"""Export Roblox d'un ennemi du monde 3, à partir de son .blend.

    blender -b <ennemi>.blend --python-exit-code 1 -P src/roblox_export.py -- <dossier_sortie> <triangles_max>

Contraintes Roblox prises en compte :
  - un seul matériau par MeshPart -> couleurs des matériaux en couleurs de sommets (attribut Couleur) ;
  - au plus 20 000 triangles par maillage -> découpe en morceaux de 19 000 triangles (allègement
    Decimate seulement si un plafond est donné) ;
  - au plus 4 os par sommet -> poids limités à 4 et normalisés ;
  - pas d'échelle d'os dans les animations -> canaux position + rotation de chaque os conservés,
    échelle abandonnée partout (maillage et os restent cohérents : les yeux restent collés au corps) ;
  - pas de shape keys génériques -> supprimées ;
  - projectiles intégrés (os Proj_*) et aura -> retirés du modèle, exportés à part (objets statiques) ;
  - une prise par fichier d'animation (import via l'éditeur d'animation de Roblox).
Avant du modèle vers -Z côté FBX (= LookVector de Roblox), Y vers le haut, unités en mètres.
"""
import math
import os
import re
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
TARGET = int(argv[1])
CHUNK = 19000
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
rig = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH")
NAME = mesh.name
HIDE = {b.name for b in rig.data.bones if b.name.startswith("Proj_") or b.name == "Coeur_Aura"}


def ctx(ob, objs=None):
    objs = objs or [ob]
    return bpy.context.temp_override(object=ob, active_object=ob, selected_objects=objs,
                                     selected_editable_objects=objs)


# ------------------------------------------------------------------------------------------
# 1. Animations : poses recalculées sans échelle (avant toute modification du rig)
# ------------------------------------------------------------------------------------------
actions = [a for a in bpy.data.actions if a.slots]
order = ["FLY", "ATTACK", "IDLE", "MOVE", "HIT", "DEATH"]
actions.sort(key=lambda a: (order.index(a.name) if a.name in order else 99, a.name))
keep = [b.name for b in rig.data.bones if b.use_deform and b.name not in HIDE]
parent_of = {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones}
rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
lo = Vector((min(v.co.x for v in mesh.data.vertices), 0, min(v.co.z for v in mesh.data.vertices)))
hi_z = max(v.co.z for v in mesh.data.vertices)
height = hi_z - lo.z
baked = {}
for act in actions:
    rig.animation_data.action = act
    rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_start), int(act.frame_end)
    frames = []
    prev_q = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        pose = {}
        for b in keep:
            loc, q, _ = rig.pose.bones[b].matrix_basis.decompose()   # échelle abandonnée
            if b in prev_q and prev_q[b].dot(q) < 0:
                q.negate()
            prev_q[b] = q.copy()
            pose[b] = (loc, q)
        frames.append(pose)
    if act.name == "DEATH":       # sans échelle, le ballon ne peut pas rétrécir : il s'enfonce dans la neige
        n = len(frames)
        for i, pose in enumerate(frames):
            x = max(0.0, (i / (n - 1) - 0.7) / 0.3)
            loc, q = pose["Root"]
            pose["Root"] = (loc + Vector((0, 0, -1.25 * height * x ** 2)), q)
    baked[act.name] = (f0, f1, bool(act.use_cyclic), frames)

# ------------------------------------------------------------------------------------------
# 2. Maillage : shape keys, couleurs de sommets, matériau unique
# ------------------------------------------------------------------------------------------
if mesh.data.shape_keys:
    mesh.data.shape_keys.animation_data_clear()
    mesh.shape_key_clear()
me = mesh.data


def mat_color(m):
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b is not None and b.inputs["Emission Strength"].default_value > 1.0:
        c = b.inputs["Emission Color"].default_value
    elif b is not None:
        c = b.inputs["Base Color"].default_value
    else:
        c = m.diffuse_color
    return (c[0], c[1], c[2], 1.0)


if "Couleur" not in me.color_attributes:
    cols = [mat_color(sl.material) for sl in mesh.material_slots]
    attr = me.color_attributes.new("Couleur", "BYTE_COLOR", "CORNER")
    for poly in me.polygons:
        for li in poly.loop_indices:
            attr.data[li].color = cols[poly.material_index]
me.color_attributes.active_color = me.color_attributes["Couleur"]
for ca in list(me.color_attributes):
    if ca.name != "Couleur":
        me.color_attributes.remove(ca)

single = bpy.data.materials.new("Roblox_Couleurs_Sommets")
single.diffuse_color = (1, 1, 1, 1)
nt = single.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Roughness"].default_value = 0.3
vc = nt.nodes.new("ShaderNodeVertexColor")
vc.layer_name = "Couleur"
nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])

# ------------------------------------------------------------------------------------------
# 3. Projectiles et aura : extraits en objets statiques, retirés du modèle
# ------------------------------------------------------------------------------------------
gidx = {g.index: g.name for g in mesh.vertex_groups}


def dominant(v):
    best, w = None, 0.0
    for g in v.groups:
        if g.weight > w:
            best, w = gidx.get(g.group), g.weight
    return best


vdom = [dominant(v) for v in me.vertices]
proj_faces = {}
for poly in me.polygons:
    d = vdom[poly.vertices[0]]
    if d in HIDE:
        proj_faces.setdefault(d, []).append(poly.index)

proj_dir = os.path.join(os.path.dirname(os.path.dirname(OUT)), "Projectiles")
done_stems = set()
for bone_name, faces in proj_faces.items():
    stem = re.sub(r"_\d+$", "", bone_name)
    if stem in done_stems or bone_name == "Coeur_Aura":
        continue
    done_stems.add(stem)
    keep_f = set(faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep_f], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    cen = sum((v.co for v in bm.verts), Vector()) / max(len(bm.verts), 1)
    bmesh.ops.translate(bm, verts=bm.verts, vec=-cen)
    pm = bpy.data.meshes.new(f"{NAME}_{stem}")
    bm.to_mesh(pm)
    bm.free()
    pm.materials.clear()
    pm.materials.append(single)
    for p in pm.polygons:
        p.material_index = 0
    po = bpy.data.objects.new(pm.name.replace("Proj_", "Projectile_"), pm)
    sc.collection.objects.link(po)
    os.makedirs(proj_dir, exist_ok=True)
    with ctx(po):
        bpy.ops.export_scene.fbx(filepath=os.path.join(proj_dir, po.name + ".fbx"), use_selection=True,
                                 object_types={"MESH"}, apply_scale_options="FBX_SCALE_UNITS",
                                 mesh_smooth_type="FACE", use_triangles=True, colors_type="SRGB",
                                 bake_anim=False)
    bpy.data.objects.remove(po)

all_proj = {i for fs in proj_faces.values() for i in fs}
if all_proj:
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in all_proj], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(me)
    bm.free()

# os supprimés : projectiles, aura, contrôle des shape keys
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
for b in list(rig.data.edit_bones):
    if b.name in HIDE or not b.use_deform:
        rig.data.edit_bones.remove(b)
bpy.ops.object.mode_set(mode="OBJECT")
valid = {b.name for b in rig.data.bones}
for g in list(mesh.vertex_groups):
    if g.name not in valid:
        mesh.vertex_groups.remove(g)

# ------------------------------------------------------------------------------------------
# 4. Allègement, triangulation, 4 os max par sommet
# ------------------------------------------------------------------------------------------
bm = bmesh.new()
bm.from_mesh(me)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.to_mesh(me)
bm.free()
tris = len(me.polygons)
if TARGET and tris > TARGET:      # 0 = pas d'allègement (motifs nets, découpe en morceaux)
    dec = mesh.modifiers.new("Allegement", "DECIMATE")
    dec.ratio = TARGET / tris
    dec.use_collapse_triangulate = True
    with ctx(mesh):
        bpy.ops.object.modifier_move_to_index(modifier=dec.name, index=0)
        bpy.ops.object.modifier_apply(modifier=dec.name)
me.materials.clear()
me.materials.append(single)
for p in me.polygons:
    p.material_index = 0
with ctx(mesh):
    bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.01)
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
me.shade_smooth()
me.set_sharp_from_angle(angle=math.radians(45))

# ------------------------------------------------------------------------------------------
# 5. Découpe en morceaux de 19 000 triangles maximum
# ------------------------------------------------------------------------------------------
parts = [mesh]
if len(me.polygons) > CHUNK:
    bpy.context.view_layer.objects.active = mesh
    with ctx(mesh):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.separate(type="LOOSE")
        bpy.ops.object.mode_set(mode="OBJECT")
    pieces = [o for o in sc.objects if o.type == "MESH"]
    pieces.sort(key=lambda o: (round(sum((v.co for v in o.data.vertices), Vector()).y / len(o.data.vertices), 1),
                               sum(v.co.z for v in o.data.vertices) / len(o.data.vertices)))
    bins, cur, n = [], [], 0
    for o in pieces:
        t = len(o.data.polygons)
        if cur and n + t > CHUNK:
            bins.append(cur)
            cur, n = [], 0
        cur.append(o)
        n += t
    bins.append(cur)
    parts = []
    for objs in bins:
        with ctx(objs[0], objs):
            bpy.ops.object.join()
        parts.append(objs[0])
for i, o in enumerate(parts):
    o.name = f"{NAME}_Maillage" if len(parts) == 1 else f"{NAME}_Maillage{i + 1}"
    o.data.name = o.name

# ------------------------------------------------------------------------------------------
# 6. Actions Roblox (position + rotation) et exports
# ------------------------------------------------------------------------------------------
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.scale = (1, 1, 1)
rig.animation_data_clear()
rig.animation_data_create()
rig.name = f"{NAME}_Rig"
rig.data.name = rig.name

new_actions = []
for name, (f0, f1, loop, frames) in baked.items():
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    slot = act.slots.new(id_type="OBJECT", name=rig.name)
    strip = act.layers.new("Layer").strips.new(type="KEYFRAME")
    cb = strip.channelbag(slot, ensure=True)
    for b in keep:
        for prop, n_idx, getter in (("location", 3, lambda p, i: p[0][i]), ("rotation_quaternion", 4, lambda p, i: p[1][i])):
            for i in range(n_idx):
                fc = cb.fcurves.new(f'pose.bones["{b}"].{prop}', index=i, group_name=b)
                fc.keyframe_points.add(len(frames))
                flat = []
                for k, pose in enumerate(frames):
                    flat += [f0 + k, getter(pose[b], i)]
                fc.keyframe_points.foreach_set("co", flat)
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
                fc.update()
    act.use_frame_range = True
    act.frame_start, act.frame_end = f0, f1
    act.use_cyclic = loop
    new_actions.append(act)

common = dict(apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Z", axis_up="Y", add_leaf_bones=False,
              use_armature_deform_only=True, primary_bone_axis="Y", secondary_bone_axis="X")
idle = bpy.data.actions.get("ATTACK") or new_actions[0]   # image 1 = pose de repos
rig.animation_data.action = idle
rig.animation_data.action_slot = idle.slots[0]
sc.frame_set(int(idle.frame_start))
with ctx(rig, parts + [rig]):
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, NAME + ".fbx"), use_selection=True,
                             object_types={"ARMATURE", "MESH"}, mesh_smooth_type="FACE", use_triangles=True,
                             colors_type="SRGB", bake_anim=False, **common)
anim_dir = os.path.join(OUT, "Animations")
os.makedirs(anim_dir, exist_ok=True)
for act in new_actions:
    rig.animation_data.action = act
    rig.animation_data.action_slot = act.slots[0]
    sc.frame_start, sc.frame_end = int(act.frame_start), int(act.frame_end)
    sc.name = act.name              # nom de la prise dans le FBX
    with ctx(rig):
        bpy.ops.export_scene.fbx(filepath=os.path.join(anim_dir, f"{NAME}_{act.name}.fbx"), use_selection=True,
                                 object_types={"ARMATURE"}, bake_anim=True, bake_anim_use_all_bones=True,
                                 bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False,
                                 bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0, **common)

rig.animation_data.action = idle
rig.animation_data.action_slot = idle.slots[0]
sc.frame_start, sc.frame_end = int(idle.frame_start), int(idle.frame_end)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "_roblox_" + NAME + ".blend"), compress=True)
print(f"[roblox] {NAME} : {len(parts)} maillage(s) {[len(o.data.polygons) for o in parts]} triangles, "
      f"{len(keep)} os, {len(new_actions)} animations, projectiles : {sorted(done_stems)}")
