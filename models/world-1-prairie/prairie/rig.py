"""Armature, pondérations (skinning) et assemblage de toutes les pièces en un seul maillage."""
import bpy
from mathutils import Vector

from . import geo

PARTS = []  # (objet, règle de pondération)


def _lobes():
    out = [("Lobe_Haut", (0, 0, 1)), ("Lobe_Bas", (0, 0, -1)), ("Lobe_Avant", (0, 1, 0)),
           ("Lobe_Arriere", (0, -1, 0)), ("Lobe_Gauche", (-1, 0, 0)), ("Lobe_Droite", (1, 0, 0))]
    for z, zn in ((1, "H"), (-1, "B")):
        for y, yn in ((1, "Av"), (-1, "Ar")):
            for x, xn in ((-1, "G"), (1, "D")):
                out.append((f"Lobe_{zn}{yn}{xn}", (x, y, z)))
    return [(n, Vector(d).normalized()) for n, d in out]


# 14 os de déformation de l'enveloppe : 6 axes + 8 coins. L'avant est +Y, la gauche du modèle est -X.
LOBES = _lobes()
MAX_INFLUENCES = 4


def reset():
    PARTS.clear()


def add(ob, rule="lobes"):
    """Enregistre une pièce. Règles :
    "lobes"                       déformation par l'enveloppe (selon la position)
    ("bone", nom)                 rigide sur un os
    ("chain", [os...], [points])  le long d'une chaîne (ficelle)
    ("blend", os, p_haut, p_bas)  de l'enveloppe (en haut) vers un os (en bas) : cordages
    """
    PARTS.append((ob, rule))
    return ob


def lobe_weights(F, co):
    d = co - F.C
    d = Vector((d.x / F.half.x, d.y / F.half.y, d.z / F.half.z))
    if d.length < 1e-6:
        return {"Lobe_Haut": 1.0}
    d.normalize()
    w = {}
    for name, e in LOBES:
        v = max(0.0, d.dot(e)) ** 3
        if v > 1e-5:
            w[name] = v
    return w


def surface_weights(F, s):
    """Poids de l'enveloppe au point de surface s, avec les zones d'attache (patches) : autour d'un point
    d'attache (visage, queue, noeud, bouche de la montgolfière...), l'enveloppe est pondérée à 100 % sur l'os
    porteur, celui dont les pièces attachées (yeux, hélice, ficelle, nacelle) sont les enfants."""
    w = dict(_limit(lobe_weights(F, s)))
    for p in F.patches:
        d = (s - p["center"]).length
        if d >= p["r1"]:
            continue
        a = 1.0 if d <= p["r0"] else 1.0 - (d - p["r0"]) / (p["r1"] - p["r0"])
        a = a * a * (3 - 2 * a)
        w = {k: v * (1 - a) for k, v in w.items()}
        w[p["bone"]] = w.get(p["bone"], 0.0) + a
    return w


def _chain_weights(bones, pts, co):
    # paramètre le long de la polyligne
    best, best_s = 1e9, 0.0
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        ab = b - a
        t = max(0.0, min(1.0, (co - a).dot(ab) / max(ab.dot(ab), 1e-12)))
        dist = (co - (a + ab * t)).length
        if dist < best:
            best, best_s = dist, k + t
    w = {}
    for k, b in enumerate(bones):
        v = max(0.0, 1.0 - abs(best_s - (k + 0.5)))
        if v > 0:
            w[b] = v
    if not w:
        w[bones[0] if best_s < 0.5 else bones[-1]] = 1.0
    return w


def weights_for(F, rule, co):
    if rule == "lobes":
        # collé à l'enveloppe : mêmes poids que le point de surface le plus proche
        s, _n = F.surf.nearest(co)
        return surface_weights(F, s)
    kind = rule[0]
    if kind == "bone":
        return {rule[1]: 1.0}
    if kind == "lid":
        # paupières : le haut de l'oeil suit l'os du haut, le bas suit l'os du bas, fondu linéaire entre les deux
        _k, top, bot, center, up, half = rule
        a = max(0.0, min(1.0, 0.5 + 0.5 * (co - center).dot(up) / half))
        return {top: a, bot: 1.0 - a} if 0.0 < a < 1.0 else ({top: 1.0} if a >= 1.0 else {bot: 1.0})
    if kind == "chain":
        return _chain_weights(rule[1], rule[2], co)
    if kind == "blend":
        _k, bone, top, bot = rule
        ab = bot - top
        t = max(0.0, min(1.0, (co - top).dot(ab) / max(ab.dot(ab), 1e-12)))
        t = t * t * (3 - 2 * t)
        w = {k: v * (1 - t) for k, v in surface_weights(F, F.surf.nearest(top)[0]).items()}
        w[bone] = w.get(bone, 0.0) + t
        return w
    raise ValueError(rule)


def _limit(w):
    items = sorted(w.items(), key=lambda kv: -kv[1])[:MAX_INFLUENCES]
    tot = sum(v for _k, v in items) or 1.0
    return [(k, v / tot) for k, v in items if v / tot > 1e-3]


def build_armature(F, name):
    data = bpy.data.armatures.new(name)
    data.display_type = "OCTAHEDRAL"
    arm = bpy.data.objects.new(name, data)
    (geo.COLLECTION or bpy.context.scene.collection).objects.link(arm)
    arm.show_in_front = True
    vl = bpy.context.view_layer
    vl.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = data.edit_bones
    s = F.bone_size

    def B(n, head, tail, parent=None, deform=False, z_axis=None):
        b = eb.new(n)
        b.head = Vector(head)
        b.tail = Vector(tail)
        b.roll = 0.0
        if z_axis is not None:
            b.align_roll(Vector(z_axis))
        b.use_deform = deform
        if parent:
            b.parent = eb[parent]
            b.use_connect = False

    C = F.C
    B("Root", (0, 0, 0), (0, s, 0))
    B("Motion", C, C + Vector((0, s, 0)), "Root")
    B("Body", C, C + Vector((0, 0.8 * s, 0)), "Motion")
    # Les pièces attachées sont des ENFANTS de l'os qui porte l'enveloppe à leur point d'attache : elles suivent
    # le corps par la hiérarchie du squelette, sans aucune clé de compensation (robuste dans tous les moteurs).
    # Os de l'enveloppe posés SUR la surface : le corps se déforme en les déplaçant (aucune échelle d'os).
    F.lobe_heads = {}
    for n, e in LOBES:
        d = Vector((e.x * F.half.x, e.y * F.half.y, e.z * F.half.z))
        h, _nor = F.surf.ray(d)
        F.lobe_heads[n] = h.copy()
        B(n, h, h + Vector((0, 0.3 * s, 0)), "Body", True)
    for x in F.extra_bones:
        head = Vector(x["head"])
        y_dir = Vector(x.get("y_axis", (0, 1, 0))).normalized()
        B(x["name"], head, head + y_dir * x.get("length", 0.3 * s), x["parent"], x.get("deform", True), x.get("z_axis"))
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
    return arm


def skin_and_join(F, arm, name):
    objs = []
    for ob, rule in PARTS:
        groups = {}
        for v in ob.data.vertices:
            for g, val in _limit(weights_for(F, rule, v.co.copy())):
                groups.setdefault(g, {}).setdefault(round(val, 4), []).append(v.index)
        for g, by_w in groups.items():
            vg = ob.vertex_groups.get(g) or ob.vertex_groups.new(name=g)
            for val, idx in by_w.items():
                vg.add(idx, val, "REPLACE")
        objs.append(ob)
    mesh = geo.join(objs, name)
    mesh.parent = arm
    mod = mesh.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    # tous les groupes de déformation existent, même vides (exports homogènes)
    for b in arm.data.bones:
        if b.use_deform and b.name not in mesh.vertex_groups:
            mesh.vertex_groups.new(name=b.name)
    return mesh
