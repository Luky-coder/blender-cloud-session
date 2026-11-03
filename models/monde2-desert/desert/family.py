"""Pipeline commun : géométrie de référence -> variante élémentaire -> fichier .blend + FBX.

1. build_reference(fam) construit la géométrie de référence d'une famille (palette neutre « sable »,
   pièces séparées déjà pondérées sur le rig) et l'enregistre dans Blender/_References/.
2. build_variant(fam, élément) repart d'une scène vide, AJOUTE (append, pas link) la référence,
   recolore les matériaux de rôle, refait le visage avec l'expression du type, ajoute les décors
   élémentaires, fusionne tout en un maillage skinné, crée les shape keys et les 5 actions (ou plus).
   Chaque variante est donc un modèle indépendant, sans reconstruire la géométrie de la famille.
"""
import math
import os

import bpy
from mathutils import Vector

from . import core
from .core import TAU, Builder, K, Pose, damp, frame_matrix, jitter, surface
from .elements import ELEMENTS


class Family:
    key = "Famille"        # dossier / préfixe de fichier
    short = "Famille"      # préfixe des noms d'objets et d'actions
    label = "Famille"      # nom affiché
    pv = 0
    surface_parts = ("Corps",)
    crown = dict(loc=(0, 0, 1), size=0.2)                     # os FX
    aura = dict(center=(0, 0, 1), radius=0.6, axis=(0, 0, 1), count=6, size=0.07)  # os Aura
    emblems = ()           # [(origine, direction, taille)]
    face_frame = dict(center=(0, 0, 1))
    face_params = {}
    face_bone = "Body_Top"
    boss_file = None       # boss : nom de fichier unique (sinon <famille>/<type>)
    # images montrées dans la planche d'animation des aperçus
    anim_frames = {"Idle": (1,), "Move": (8,), "Attack": (10, 15, 18), "Hit": (4,), "Death": (24, 42, 54)}
    anim_cols = 3
    anim_pad_forward = 0.15
    # ficelles de ballon : nœud de gonflage + ficelle animée par une chaîne de 3 os (String<i>_1..3)
    # dict(parent=os, path=[nœud, ...points], dir=sortie du nœud, hang=pend (sinon traîne au sol),
    #      r=rayon de la ficelle, scale=taille du nœud)
    strings = ()
    STRING_SPLIT = (0.0, 0.4, 0.75)

    # -- à fournir par chaque famille --------------------------------------------------------------
    def build(self, B):
        raise NotImplementedError

    def body_weight(self, co):
        return {"Body": 1.0}

    def deflate(self, co):
        return co

    def inflate(self, co):
        return co

    def actions(self):
        """[(suffixe, nb_images, fn(t) -> Pose, boucle ?)]"""
        raise NotImplementedError

    # -- commun -----------------------------------------------------------------------------------
    def rig_bones(self):
        """Os de la famille + chaînes des ficelles."""
        out = list(self.BONES)
        for i, st in enumerate(self.strings):
            pts = core.spline(st["path"], 41)
            for k, f in enumerate(self.STRING_SPLIT):
                parent = st["parent"] if k == 0 else f"String{i + 1}_{k}"
                out.append((f"String{i + 1}_{k + 1}", tuple(pts[int(round(f * 40))]), parent))
        return out

    def build_strings(self, B):
        """Nœud de ballon (col, bourrelet roulé, nœud) + ficelle torsadée + perle d'extrémité."""
        for i, st in enumerate(self.strings):
            s = st.get("scale", 1.0)
            P = Vector(st["path"][0])
            d = Vector(st["dir"]).normalized()
            Mk = frame_matrix(P - d * 0.012 * s, d, up=(0, 0, 1) if abs(d.z) < 0.9 else (0, 1, 0))
            knot = [B.cone(f"Noeud_Col_{i}", Mk, 0.028 * s, 0.013 * s, 0.04 * s, "corps", seg=8),
                    B.ring(f"Noeud_Bourrelet_{i}", Mk @ Vector((0, 0, 0.045 * s)), 0.017 * s, 0.009 * s, "corps",
                           axis=d, nseg=4, n=10),
                    B.sphere(f"Noeud_{i}", None, (0.019 * s, 0.016 * s, 0.014 * s), "corps", 8, 5,
                             M=Mk @ core.Matrix.Translation((0, 0, 0.056 * s)))]
            for o in knot:
                core.weight_all(o, f"String{i + 1}_1")
            ctrl = [P + d * 0.06 * s] + [Vector(p) for p in st["path"][1:]]
            dense = core.spline(ctrl, 60)
            L = [0.0]
            for a, b in zip(dense, dense[1:]):
                L.append(L[-1] + (b - a).length)
            line = B.tube(f"Ficelle_{i}", ctrl, st.get("r", 0.009), "dent", n=22, nseg=4, ncap=1)
            bead = B.sphere(f"Ficelle_Perle_{i}", dense[-1], (st.get("r", 0.009) * 2.2,) * 3, "dent", 6, 4)
            split = self.STRING_SPLIT
            names = [f"String{i + 1}_{k + 1}" for k in range(3)]

            def w(co, dense=dense, L=L, names=names):
                j = min(range(len(dense)), key=lambda q: (dense[q] - co).length_squared)
                u = L[j] / L[-1]
                return core.gradient("x", [(split[0], names[0]), (split[1], names[1]), (split[2], names[2])])(
                    Vector((u, 0, 0)))
            core.weight_fn(line, w)
            core.weight_all(bead, names[2])

    def string_motion(self, p, t, n, suffix):
        """Mouvement secondaire des ficelles, en retard sur le corps, selon l'action."""
        w = TAU * t / n
        for i, st in enumerate(self.strings):
            hang = st.get("hang", True)
            for k in range(3):
                lag = 0.8 * k + 1.3 * i
                if suffix == "Idle":
                    a, b = 0.12 * math.sin(w - lag), 0.1 * math.sin(w + 1 - lag)
                elif suffix == "Move":
                    if hang:
                        a, b = -0.3 + 0.12 * math.sin(2 * w - lag), 0.1 * math.sin(w - lag)
                    else:
                        a, b = -0.08 * (1 - math.cos(2 * w - lag)), 0.3 * math.sin(2 * w - lag)
                elif suffix == "Hit":
                    a = damp(t, 1 + k, 0.5 if hang else -0.3, 1.4, 4)
                    b = damp(t, 2 + k, 0.3, 1.8, 4)
                elif suffix == "Death":
                    d = core.ease(t / n)
                    a = (0.35 if hang else -0.1) * d * math.sin(t * 0.3 - lag)
                    b = 0.4 * d * math.sin(t * 0.25 + lag)
                else:  # attaques : recul, fouet à la projection, oscillation amortie
                    a0, a1 = 0.25 * n, 0.45 * n
                    curve = K((0, 0.0), (a0, 0.35), (a1, -0.6), (a1 + 0.15 * n, 0.3), (n, 0.0))(t - 2 * k)
                    a = curve * (1.0 if hang else -0.4) + damp(t, a1 + 2 * k, 0.25, 1.3, 6)
                    b = 0.2 * math.sin(t * 0.4 - lag) * math.exp(-t / n)
                # pendante : X = avant/arrière, Y = latéral ; au sol : X = soulève, Z = serpente
                p.add(f"String{i + 1}_{k + 1}", rot=(a, b, 0) if hang else (a, 0, b))
        return p
    def face(self, B, bvh, overrides):
        """Visage (expression du type) + os animables des yeux : Eye_L/R (clignement, plissement),
        Pupil_L/R (regard, dilatation, enfants des yeux), Brow_L/R (sourcils). _L = côté +X."""
        params = dict(self.face_params)
        params.update(overrides)
        ff = core.FaceFrame(bvh, self.face_frame["center"], forward=self.face_frame.get("forward", (0, 1, 0)),
                            dist=self.face_frame.get("dist", 3.0))
        B.face_info = {}
        objs = core.build_face(B, ff, params)
        rig = next(o for o in B.coll.objects if o.type == "ARMATURE")
        bones = []
        for side, tag in ((-1, "L"), (1, "R")):
            info = B.face_info.get(side)
            if info:
                bones += [(f"Eye_{tag}", tuple(info["eye"]), self.face_bone),
                          (f"Pupil_{tag}", tuple(info["pupil"]), f"Eye_{tag}"),
                          (f"Brow_{tag}", tuple(info["brow"]), self.face_bone)]
        core.add_bones(rig, bones, length=params.get("eye_r", 0.08) * 0.5)
        for o in objs:
            n = o.name
            side = "L" if (n.endswith("_G") or n.endswith("_-1")) else ("R" if (n.endswith("_D") or n.endswith("_1"))
                                                                         else None)
            if "_Oeil_" in n and side:
                bone = f"Eye_{side}"
            elif ("_Pupille_" in n or "_Reflet_" in n) and side:
                bone = f"Pupil_{side}"
            elif "_Sourcil_" in n and side:
                bone = f"Brow_{side}"
            else:
                bone = self.face_bone
            core.weight_all(o, bone)
        return objs

    def eye_motion(self, p, t, n, suffix):
        """Regard expressif : clignements, saccades, plissement d'attaque, douleur, étourdissement."""
        er = self.face_params.get("eye_r", 0.08)
        w = TAU * t / n

        def blink(t0, dur=6):
            if t0 <= t <= t0 + dur:
                x = (t - t0) / dur
                return 1 - 0.92 * min(1.0, math.sin(math.pi * x) * 1.6)
            return 1.0
        lid, look, dil, brow_z, brow_g = 1.0, (0.0, 0.0), 1.0, 0.0, 0.0
        if suffix == "Idle":
            lid = blink(0.35 * n) * (blink(0.8 * n) if n >= 80 else 1.0)
            look = K((0, (0.0, 0.0)), (0.2 * n, (0.0, 0.0)), (0.26 * n, (0.28, 0.06)), (0.5 * n, (0.28, 0.06)),
                     (0.56 * n, (-0.24, -0.02)), (0.74 * n, (-0.24, -0.02)), (0.8 * n, (0.0, 0.0)), (n, (0.0, 0.0)))(t)
            brow_z = 0.1 * er * math.sin(w)
        elif suffix == "Move":
            lid = blink(0.55 * n, 5)
            look, brow_z, brow_g = (0.0, -0.12), -0.12 * er, 0.12
        elif suffix == "Hit":
            lid = K((0, 1.0), (2, 0.08), (6, 0.08), (9, 1.28), (14, 1.1), (n, 1.0))(t)
            dil = K((0, 1.0), (6, 1.0), (9, 0.6), (n, 1.0))(t)
            look = (jitter(t * 4, 0.15) * math.exp(-t / 6), jitter(t * 4 + 2, 0.1) * math.exp(-t / 6))
            brow_z = K((0, 0.0), (3, -0.15 * er), (9, 0.35 * er), (n, 0.0))(t)
            brow_g = K((0, 0.0), (3, 0.3), (9, -0.35), (n, 0.0))(t)
        elif suffix == "Death":
            lid = K((0, 1.0), (0.08 * n, 1.32), (0.2 * n, 1.15), (0.6 * n, 0.85), (0.72 * n, 0.08), (n, 0.08))(t)
            dil = K((0, 1.0), (0.08 * n, 0.55), (0.25 * n, 0.8), (n, 0.8))(t)
            spin = K((0, 0.0), (0.15 * n, 0.0), (0.25 * n, 0.3), (0.65 * n, 0.3), (0.72 * n, 0.0))(t)
            look = (spin * math.cos(t * 0.6), spin * math.sin(t * 0.6))
            brow_z = K((0, 0.0), (0.08 * n, 0.4 * er), (0.7 * n, 0.15 * er), (n, -0.1 * er))(t)
            brow_g = K((0, 0.0), (0.08 * n, -0.4), (n, -0.2))(t)
        else:  # Attack et attaques spéciales : plisse en préparation, effort à l'impact, yeux grands ouverts
            lid = K((0, 1.0), (0.25 * n, 0.5), (0.42 * n, 0.55), (0.47 * n, 0.25), (0.58 * n, 1.18), (0.8 * n, 1.0))(t)
            dil = K((0, 1.0), (0.25 * n, 0.8), (0.58 * n, 0.7), (n, 1.0))(t)
            look = K((0, (0.0, 0.0)), (0.25 * n, (0.0, -0.12)), (0.7 * n, (0.0, -0.12)), (n, (0.0, 0.0)))(t)
            brow_z = K((0, 0.0), (0.25 * n, -0.28 * er), (0.5 * n, -0.3 * er), (0.6 * n, 0.15 * er), (n, 0.0))(t)
            brow_g = K((0, 0.0), (0.25 * n, 0.4), (0.5 * n, 0.45), (0.65 * n, 0.1), (n, 0.0))(t)
        for tag, sgn in (("L", 1), ("R", -1)):
            p.add(f"Eye_{tag}", scl=(1.0 + 0.3 * (lid - 1) if lid > 1 else 1.0, 1.0, lid))
            p.add(f"Pupil_{tag}", loc=(look[0] * er, 0, look[1] * er), scl=dil)
            p.add(f"Brow_{tag}", loc=(0, 0, brow_z), rot=(0, -brow_g * sgn, 0))
        return p

    def add_element(self, B, elem, bvh):
        E = ELEMENTS[elem]
        # couronne (os FX)
        c = self.crown
        M = frame_matrix(c["loc"], c.get("up", (0, 0, 1)), up=(0, 1, 0))
        for o in E["crown"](B, M, c["size"]):
            core.weight_all(o, "FX")
        # particules en orbite (os Aura)
        a = self.aura
        ax = Vector(a["axis"]).normalized()
        u = Vector(a.get("ref", (1, 0, 0)))
        u = (u - ax * u.dot(ax)).normalized()
        v = ax.cross(u)
        for k in range(a["count"]):
            ph = TAU * k / a["count"] + a.get("phase", 0.0)
            radial = u * math.cos(ph) + v * math.sin(ph)
            pos = Vector(a["center"]) + radial * a["radius"] + ax * (0.12 * a["radius"] * math.sin(2 * ph))
            Mk = frame_matrix(pos, radial, up=ax)
            for o in E["particle"](B, Mk, a["size"], k):
                core.weight_all(o, "Aura")
        # emblèmes en relief sur le corps
        for i, (origin, direction, size) in enumerate(self.emblems):
            loc, n = surface(bvh, origin, direction)
            if loc is None:
                print(f"[warn] emblème {i} : pas de surface")
                continue
            Me = frame_matrix(loc, n, up=(0, 0, 1))
            for o in E["emblem"](B, f"Emblème_{i}", Me, bvh, size):
                core.weight_fn(o, self.body_weight)


def valve(B, loc, n, bone, s=1.0):
    """Valve de gonflage : embase dorée, col, bouchon turquoise (orientée selon la normale)."""
    M = frame_matrix(loc - n * 0.01 * s, n, up=(0, 0, 1))
    objs = [B.cone("Valve_Base", M, 0.052 * s, 0.05 * s, 0.025 * s, "or", seg=12),
            B.cone("Valve_Col", M, 0.024 * s, 0.022 * s, 0.07 * s, "or", seg=8),
            B.sphere("Valve_Bouchon", None, (0.034 * s, 0.034 * s, 0.024 * s), "turquoise", 10, 6,
                     M=M @ core.Matrix.Translation((0, 0, 0.08 * s)))]
    for o in objs:
        core.weight_all(o, bone)
    return objs


# ---------------------------------------------------------------------------------------------
# Couches d'animation communes aux décors élémentaires
# ---------------------------------------------------------------------------------------------
def fx_layer(p, t, n, mode, aura_axis=2, spin=1.0):
    """FX (couronne) : respiration / balancement. Aura : orbite. Death : tout se résorbe."""
    w = TAU * t / n
    rot = [0.0, 0.0, 0.0]
    if mode == "idle":
        rot[aura_axis] = TAU * t / n * spin
        p.add("FX", loc=(0, 0, 0.015 * math.sin(w)), rot=(0.06 * math.sin(w + 1), 0.06 * math.sin(w), 0),
              scl=1 + 0.06 * math.sin(2 * w))
        p.add("Aura", rot=rot, scl=1 + 0.04 * math.sin(2 * w))
    elif mode == "move":
        rot[aura_axis] = TAU * t / n * spin
        p.add("FX", rot=(-0.15 + 0.05 * math.sin(2 * w), 0, 0), scl=1 + 0.05 * math.sin(2 * w))
        p.add("Aura", rot=rot)
    elif mode == "attack":
        rot[aura_axis] = core.K((0, 0.0), (12, -0.6), (18, 2.4), (40, TAU))(t) * spin
        p.add("FX", scl=core.K((0, 1.0), (10, 0.85), (17, 1.3), (24, 0.95), (40, 1.0))(t))
        p.add("Aura", rot=rot, scl=core.K((0, 1.0), (12, 0.8), (18, 1.25), (40, 1.0))(t))
    elif mode == "hit":
        p.add("FX", rot=(core.damp(t, 1, 0.35, 1.3, 4), 0, core.damp(t, 1, 0.25, 1.7, 4)),
              scl=core.K((0, 1.0), (3, 0.7), (9, 1.1), (20, 1.0))(t))
        rot[aura_axis] = core.K((0, 0.0), (3, 0.8), (20, 0.0))(t)
        p.add("Aura", rot=rot, scl=core.K((0, 1.0), (3, 1.3), (12, 0.95), (20, 1.0))(t))
    elif mode == "death":
        p.add("FX", rot=(core.K((0, 0.0), (20, 0.6))(t), 0, 0), scl=core.K((0, 1.0), (6, 1.15), (28, 0.001))(t))
        rot[aura_axis] = core.K((0, 0.0), (30, 3.0))(t)
        p.add("Aura", rot=rot, scl=core.K((0, 1.0), (8, 1.3), (30, 0.001))(t))
    return p


# ---------------------------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    sc = bpy.context.scene
    sc.render.fps = core.FPS
    sc.frame_start = 1
    sc.unit_settings.system = "METRIC"
    return sc


def build_reference(fam, path):
    """Construit et enregistre la géométrie de référence (neutre) d'une famille."""
    reset_scene()
    mats = core.make_materials("REF", core.NEUTRAL_PALETTE)
    coll = core.collection("REF_" + fam.key)
    B = Builder(coll, mats)
    fam.build(B)
    fam.build_strings(B)
    bvh = core.bvh_of([o for o in coll.objects if o.name in fam.surface_parts])
    fam.face(B, bvh, {})
    for m in mats.values():
        m.use_fake_user = True  # garde tous les rôles, même ceux non utilisés par la référence
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    return path


def assemble(fam, elem, ref_path, extra_parts=None, animate=True):
    """Crée la variante dans la scène courante. Renvoie (rig, mesh, key, actions).
    animate=False : sans actions (planche de présentation)."""
    E = ELEMENTS[elem]
    with bpy.data.libraries.load(ref_path, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c.startswith("REF_")]
        dst.materials = [m for m in src.materials if m.startswith("REF_")]
    coll = dst.collections[0]
    bpy.context.scene.collection.children.link(coll)
    name = f"{fam.short}_{elem}"
    coll.name = name
    mats = {core.role_of(m): m for m in dst.materials}
    for m in mats.values():
        m.use_fake_user = False
    core.recolor_materials(mats, name, E["palette"])

    rig = next(o for o in coll.objects if o.type == "ARMATURE")
    for o in [o for o in coll.objects if o.name.startswith("Visage")]:
        bpy.data.meshes.remove(o.data)
    parts = [o for o in coll.objects if o.type == "MESH"]
    B = Builder(coll, mats)
    bvh = core.bvh_of([o for o in parts if o.name in fam.surface_parts])
    fam.face(B, bvh, E["face"])
    fam.add_element(B, elem, bvh)
    if extra_parts:
        extra_parts(B, bvh)
    mesh = core.join(parts + B.parts, name + "_Mesh")
    # matériaux inutilisés (rôles non utilisés) : on les retire du maillage
    used = {p.material_index for p in mesh.data.polygons}
    for i in reversed(range(len(mesh.data.materials))):
        if i not in used:
            mesh.data.materials.pop(index=i)
    core.bind(mesh, rig)
    rig.name = name
    rig.data.name = name + "_Armature"
    key = core.add_shape_keys(mesh, {"Degonfle": fam.deflate, "Gonfle": fam.inflate})
    core.drive_shape_keys(key, rig)
    acts = []
    for suffix, n, fn, loop in (fam.actions() if animate else []):
        def full(t, fn=fn, n=n, suffix=suffix):
            return fam.eye_motion(fam.string_motion(fn(t), t, n, suffix), t, n, suffix)
        acts.append(core.bake_action(rig, key, f"{name}_{suffix}", n, full, loop=loop))
    if acts:
        core.assign_action(rig, key, acts[0])
    rig["Famille"] = fam.label
    rig["Element"] = E["label"]
    rig["PV"] = fam.pv
    rig["Actions"] = ",".join(a.name[len(name) + 1:] for a in acts)
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = int(acts[0].frame_end) if acts else 1
    sc.frame_set(1)
    for m in list(bpy.data.materials):
        if m.users == 0:
            bpy.data.materials.remove(m)
    return rig, mesh, key, acts


def build_variant(fam, elem, ref_path, blend_out, fbx_out):
    reset_scene()
    rig, mesh, key, acts = assemble(fam, elem, ref_path)
    os.makedirs(os.path.dirname(blend_out), exist_ok=True)
    os.makedirs(os.path.dirname(fbx_out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_out, compress=True)
    core.export_fbx(fbx_out, rig, mesh)
    core.assign_action(rig, key, acts[0])
    bpy.context.scene.frame_set(1)
    return rig, mesh, key, acts
