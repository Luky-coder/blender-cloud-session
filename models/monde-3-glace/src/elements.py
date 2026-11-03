"""Les 7 types élémentaires : palettes de matériaux et décorations géométriques.

Chaque famille fournit des « ancres » (points d'accroche sur sa silhouette) ; ce module y pose
les détails propres au type (flammes, cristaux, bulles, feuilles, éclairs, halo, fumée).
La silhouette de la famille n'est jamais modifiée : on ajoute, on ne remplace pas.
"""
import math
import random

from mathutils import Matrix, Vector

import w3lib as L

V = Vector

ELEMENTS = {
    # clé : (nom affiché, dossier/fichier)
    "lumiere": ("Lumière", "Lumiere"),
    "tenebres": ("Ténèbres", "Tenebres"),
    "glace": ("Glace", "Glace"),
    "feu": ("Feu", "Feu"),
    "eau": ("Eau", "Eau"),
    "plante": ("Plante", "Plante"),
    "eclair": ("Éclair", "Eclair"),
}
ORDER = ["lumiere", "tenebres", "glace", "feu", "eau", "plante", "eclair"]

# main : corps principal · second : blocs/couches alternés · accent : coutures, sourcils, liserés
# deco / deco2 : décorations élémentaires · glow : couleur émissive · pupil : pupilles
PALETTES = {
    "lumiere": dict(main="#FFF3D9", second="#FFD970", accent="#D9A21B", deco="#FFE27A", deco2="#FFFFFF",
                    glow="#FFE9A0", pupil="#3B2A0E", mouth="#7A4B12"),
    "tenebres": dict(main="#2B2140", second="#4A2C7C", accent="#120E1A", deco="#6E3FB0", deco2="#1C1428",
                     glow="#C27BFF", pupil="#1A0B2E", mouth="#0B0712"),
    "glace": dict(main="#BDE8FF", second="#F2FAFF", accent="#43B8EA", deco="#9DE4FF", deco2="#E9FBFF",
                  glow="#B9F5FF", pupil="#10324A", mouth="#123456"),
    "feu": dict(main="#E5402B", second="#FF8C2B", accent="#9E1C16", deco="#FF9E1F", deco2="#FFD84A",
                glow="#FFB733", pupil="#2A0A06", mouth="#4A0E08"),
    "eau": dict(main="#2E8BE0", second="#39D0C5", accent="#1A5AA5", deco="#8EE9FF", deco2="#FFFFFF",
                glow="#7FF1FF", pupil="#08223F", mouth="#0B2A4F"),
    "plante": dict(main="#3E9C46", second="#86CC5C", accent="#25632D", deco="#F57FB2", deco2="#FFE15C",
                   glow="#D2FF8E", pupil="#10260F", mouth="#173A12"),
    "eclair": dict(main="#FFD21C", second="#2F7BFF", accent="#1B3AAE", deco="#3D8BFF", deco2="#FFF04D",
                   glow="#A8EEFF", pupil="#0D1A45", mouth="#16245E"),
}


def materials(elem, prefix=""):
    """Jeu complet de matériaux pour un type (plus les matériaux communs au monde 3)."""
    p = PALETTES[elem]
    m = {}
    m["main"] = L.mat(f"{prefix}Corps", p["main"], 0.18)
    m["second"] = L.mat(f"{prefix}Corps_2", p["second"], 0.2)
    m["accent"] = L.mat(f"{prefix}Liseré", p["accent"], 0.25)
    m["deco"] = L.mat(f"{prefix}Déco", p["deco"], 0.18)
    m["deco2"] = L.mat(f"{prefix}Déco_2", p["deco2"], 0.18)
    m["glow"] = L.mat(f"{prefix}Lueur", p["glow"], 0.3, emit=p["glow"], strength=3.0)
    eye_emit = {"tenebres": (p["glow"], 1.2), "lumiere": ("#FFF6D0", 0.25)}.get(elem)
    m["eye"] = L.mat(f"{prefix}Oeil", "#FFFFFF" if elem != "tenebres" else "#E6CCFF", 0.15,
                     emit=eye_emit[0] if eye_emit else None, strength=eye_emit[1] if eye_emit else 0)
    m["pupil"] = L.mat(f"{prefix}Pupille", p["pupil"], 0.1)
    m["mouth"] = L.mat(f"{prefix}Bouche", p["mouth"], 0.4, coat=0.2)
    m["tongue"] = L.mat(f"{prefix}Langue", "#FF6F8E" if elem != "tenebres" else "#9B4DFF", 0.25)
    m["snow"] = L.mat("Neige", "#F4FAFF", 0.35, coat=0.3)
    m["ice"] = L.mat("Givre", "#BFEFFF", 0.05, coat=1.0, transmission=0.55)
    m["valve"] = L.mat("Valve_Argent", "#C7D2DC", 0.22, metal=0.85)
    m["gold"] = L.mat("Or", "#E8B43A", 0.22, metal=0.9)
    m["white"] = L.mat("Blanc", "#FFFFFF", 0.15)
    m["dark"] = L.mat("Sombre", "#1A2230", 0.4, coat=0.2)
    m["window"] = L.mat("Hublot", "#1E4E7A", 0.05, coat=1.0)
    if elem == "eau":
        m["bubble"] = L.mat("Bulle", "#B5F4FF", 0.03, coat=1.0, transmission=0.7)
    return m


# --------------------------------------------------------------------------------------------
# Visage commun
# --------------------------------------------------------------------------------------------
def eye(model, mats, pos, out, r, bone, look=V((0, 0, 0)), squint=0.0, name="oeil", pupil_k=0.55, side=None):
    """Œil gonflable : globe aplati + pupille + reflet.
    side ('G' ou 'D') : crée les os Oeil_<side> (ouverture/clignement, enfant de `bone`) et
    Pupille_<side> (regard : rotation autour du centre du globe)."""
    M = L.orient(V(pos), out)
    if side:
        model.bone(f"Oeil_{side}", V(pos), bone, length=r * 0.5)
        model.bone(f"Pupille_{side}", V(pos), f"Oeil_{side}", length=r * 0.4)
        model.meta["eye_r"] = r
        bone, pbone = f"Oeil_{side}", f"Pupille_{side}"
    else:
        pbone = bone
    g = L.ellipsoid(name, (0, 0, 0), (r, r * 0.55, r * 1.12 * (1 - squint)), 18, 12)
    L.xform(g, M)
    model.add(g, mats["eye"], bone)
    pr = r * pupil_k
    p = L.ellipsoid(name + "_p", (look.x * r * 0.35, r * 0.46, r * 0.05 + look.z * r * 0.3),
                    (pr, pr * 0.5, pr * 1.1 * (1 - squint)), 14, 10)
    L.xform(p, M)
    model.add(p, mats["pupil"], pbone)
    h = L.sphere(name + "_h", (look.x * r * 0.35 + pr * 0.35, r * 0.54 + pr * 0.35, r * 0.05 + pr * 0.45),
                 pr * 0.28, 8, 6)
    L.xform(h, M)
    model.add(h, mats["white"], pbone)


def brow(model, mats, pos, out, length, r, angle_deg, bone, name="sourcil", side=None):
    """Sourcil boudin (angle > 0 : extrémité intérieure plus basse = air fâché).
    side : crée l'os Sourcil_<side> (enfant de `bone`)."""
    M = L.orient(V(pos), out)
    if side:
        model.bone(f"Sourcil_{side}", V(pos), bone, length=length * 0.3)
        bone = f"Sourcil_{side}"
    a = math.radians(angle_deg)
    d = V((math.cos(a), 0, math.sin(a))) * length / 2
    pts = [-d, V((0, r * 0.3, 0)), d]
    t = L.tube(name, pts, [r * 0.8, r, r * 0.8], 10, cap_rings=3)
    L.xform(t, M)
    model.add(t, mats["accent"], bone)


def grin(model, mats, pos, out, w, h, bone, teeth=True, name="bouche"):
    """Bouche en sourire narquois : demi-ellipsoïde sombre + dents + langue."""
    M = L.orient(V(pos), out)
    pts = []
    n = 14
    for i in range(n + 1):
        a = math.pi * i / n
        pts.append((w * math.cos(a), -h * math.sin(a) * 1.0))
    for i in range(n - 1, 0, -1):
        a = math.pi * i / n
        pts.append((w * 0.92 * math.cos(a), -h * 0.25 * math.sin(a) + h * 0.05))
    pts = list(reversed(pts))
    b = L.puffy(name, pts, h * 0.35, h * 0.12, segs=2, M=Matrix.Rotation(0, 4, "X"))
    L.xform(b, M)
    model.add(b, mats["mouth"], bone)
    tg = L.ellipsoid(name + "_l", (0, h * 0.12, -h * 0.62), (w * 0.38, h * 0.12, h * 0.22), 12, 8)
    L.xform(tg, M)
    model.add(tg, mats["tongue"], bone)
    if teeth:
        for sx in (-1, 1):
            t = L.ellipsoid(name + "_d", (sx * w * 0.45, h * 0.16, -h * 0.12), (w * 0.12, h * 0.1, h * 0.16), 8, 6)
            L.xform(t, M)
            model.add(t, mats["white"], bone)


# --------------------------------------------------------------------------------------------
# Formes élémentaires
# --------------------------------------------------------------------------------------------
def flame(model, mats, base, up, size, bone, bend=0.0, name="flamme"):
    up = V(up).normalized()
    side = up.cross(V((0, 1, 0)))
    if side.length < 1e-3:
        side = V((1, 0, 0))
    side.normalize()
    base = V(base)
    pts = L.bezier_pts(base, base + up * size * 0.45, base + up * size * 0.8 + side * bend * size * 0.4,
                       base + up * size * 1.15 + side * bend * size * 0.75, 8)
    radii = [size * 0.32 * math.sin(math.pi * (0.25 + 0.75 * (i / 8) ** 0.75)) ** 0.9 + 0.006
             for i in range(9)]
    radii[0] = size * 0.24
    o = L.tube(name, pts, radii, 12, cap_rings=3)
    model.add(o, mats["deco"], bone)
    inner = [p + V((0, 0.12 * size, 0)) for p in pts[:6]]
    i = L.tube(name + "_c", inner, [r * 0.55 for r in radii[:6]], 10, cap_rings=2)
    model.add(i, mats["deco2"], bone)


def crystal_cluster(model, mats, base, up, size, bone, n=4, seed=1, name="cristal"):
    rnd = random.Random(seed)
    up = V(up).normalized()
    t1 = up.orthogonal().normalized()
    t2 = up.cross(t1)
    for k in range(n):
        if k == 0:
            d = up
            ln = size
        else:
            a = L.TAU * k / (n - 1) + rnd.uniform(-0.3, 0.3)
            d = (up + (t1 * math.cos(a) + t2 * math.sin(a)) * rnd.uniform(0.5, 0.8)).normalized()
            ln = size * rnd.uniform(0.5, 0.75)
        c = L.crystal(name, V(base) - up * size * 0.05, d, ln, ln * 0.2)
        model.add(c, mats["ice"] if k % 2 == 0 else mats["deco"], bone)


def leaf(model, mats, base, direction, face, size, bone, name="feuille", mat_key="deco_leaf"):
    pts = []
    n = 10
    for i in range(n + 1):
        t = i / n
        w = math.sin(math.pi * t) ** 0.8 * 0.38
        pts.append((w * size, t * size))
    for i in range(n - 1, 0, -1):
        t = i / n
        w = math.sin(math.pi * t) ** 0.8 * 0.38
        pts.append((-w * size, t * size))
    lf = L.puffy(name, pts, size * 0.1, size * 0.045, segs=2)
    M = L.orient(V(base), face, up=direction)
    L.xform(lf, M)
    model.add(lf, mats.get(mat_key, mats["second"]), bone)
    vein = L.tube(name + "_n", [V((0, size * 0.065, size * 0.08)), V((0, size * 0.07, size * 0.8))],
                  size * 0.025, 6, cap_rings=2)
    L.xform(vein, M)
    model.add(vein, mats["accent"], bone)


def flower(model, mats, pos, out, size, bone, name="fleur"):
    M = L.orient(V(pos), out)
    for k in range(5):
        a = L.TAU * k / 5
        p = L.ellipsoid(name + "_p", (math.cos(a) * size * 0.55, 0, math.sin(a) * size * 0.55),
                        (size * 0.42, size * 0.16, size * 0.42), 10, 6)
        L.xform(p, M)
        model.add(p, mats["deco"], bone)
    c = L.sphere(name + "_c", (0, size * 0.12, 0), size * 0.32, 10, 6)
    L.xform(c, M)
    model.add(c, mats["deco2"], bone)


def bolt(model, mats, base, up, size, bone, face=V((0, 1, 0)), name="eclair", flip=1):
    pts = [(0.0, 0.0), (0.22, 0.42), (0.06, 0.42), (0.3, 1.0), (-0.12, 0.5), (0.05, 0.5), (-0.14, 0.12)]
    pts = [(flip * x * size, z * size) for x, z in pts]
    b = L.puffy(name, pts, size * 0.16, size * 0.05, segs=3, sharp=80)
    M = L.orient(V(base), face, up=up)
    L.xform(b, M)
    model.add(b, mats["deco"], bone)


def spark(model, mats, pos, out, size, bone, name="etincelle"):
    s = L.puffy(name, L.star_pts(4, size, size * 0.35), size * 0.3, size * 0.1, segs=2)
    L.xform(s, L.orient(V(pos), out))
    model.add(s, mats["glow"], bone)


def snowflake_emblem(model, mats, pos, out, size, bone, mat=None, name="flocon_embleme"):
    """Petit emblème flocon gonflable (6 branches) : signature du monde 3."""
    M = L.orient(V(pos), out)
    for k in range(3):
        a = math.pi * k / 3
        d = V((math.cos(a), 0, math.sin(a))) * size
        t = L.tube(name, [-d, d], size * 0.13, 8, cap_rings=2)
        L.xform(t, M)
        model.add(t, mat or mats["snow"], bone)
    c = L.sphere(name + "_c", (0, size * 0.05, 0), size * 0.22, 10, 6)
    L.xform(c, M)
    model.add(c, mat or mats["snow"], bone)


def bubble(model, mats, pos, r, bone, name="bulle"):
    b = L.sphere(name, pos, r, 14, 9)
    model.add(b, mats.get("bubble", mats["deco"]), bone)
    h = L.sphere(name + "_h", V(pos) + V((r * 0.35, r * 0.55, r * 0.45)), r * 0.2, 6, 4)
    model.add(h, mats["white"], bone)


def horn(model, mats, base, up, size, bone, curl=1, name="corne"):
    up = V(up).normalized()
    side = V((curl, 0, 0))
    base = V(base)
    pts = L.bezier_pts(base, base + up * size * 0.5, base + up * size * 0.9 + side * size * 0.2,
                       base + up * size * 1.0 + side * size * 0.55, 7)
    radii = [size * 0.24 * (1 - i / 8) + 0.008 for i in range(8)]
    t = L.tube(name, pts, radii, 10, cap_rings=3)
    model.add(t, mats["accent"], bone)
    ring = L.torus(name + "_a", base + up * size * 0.12, size * 0.22, size * 0.05, 16, 6,
                   M=L.orient(V((0, 0, 0)), up).to_3x3().to_4x4() @ Matrix.Rotation(math.pi / 2, 4, "X"))
    model.add(ring, mats["deco"], bone)


def smoke(model, mats, center, size, bone, n=6, seed=3, name="fumee"):
    rnd = random.Random(seed)
    c = V(center)
    for k in range(n):
        a = L.TAU * k / n + rnd.uniform(-0.3, 0.3)
        p = c + V((math.cos(a) * size * 0.6, math.sin(a) * size * 0.6, rnd.uniform(-0.1, 0.35) * size))
        r = size * rnd.uniform(0.25, 0.42)
        s = L.lumpy(name, p, (r, r, r * 0.85), amp=0.12, seed=k + seed, nu=14, nv=8)
        model.add(s, mats["deco"] if k % 2 else mats["deco2"], bone)


def wave(model, mats, base, up, size, bone, face=V((0, 1, 0)), name="vague"):
    """Crête de vague gonflable enroulée."""
    M = L.orient(V(base), face, up=up)
    pts = []
    n = 14
    for i in range(n + 1):
        t = i / n
        a = math.pi * 1.6 * t
        r = size * (0.55 - 0.35 * t)
        pts.append(V((-size * 0.5 + size * 0.9 * t ** 0.7 - r * math.sin(a) * 0.3, 0,
                      size * 0.2 + r * (1 - math.cos(a)) * 0.9)))
    radii = [size * (0.2 - 0.13 * i / n) for i in range(n + 1)]
    w = L.tube(name, pts, radii, 10, cap_rings=3)
    L.xform(w, M)
    model.add(w, mats["second"], bone)
    f = L.sphere(name + "_e", pts[-1], radii[-1] * 1.3, 10, 6)
    L.xform(f, M)
    model.add(f, mats["deco2"], bone)


def droplet(model, mats, base, up, size, bone, name="goutte"):
    """Goutte d'eau gonflable, pointe vers le haut, avec reflet."""
    up = V(up).normalized()
    base = V(base)
    n = 12
    pts, radii = [], []
    for i in range(n + 1):
        s = 0.03 + 0.97 * i / n
        pts.append(base + up * size * 1.35 * s)
        radii.append(size * 0.62 * math.sin(math.pi * s) ** 0.7 * (1 - s) ** 0.55 + 0.004)
    model.add(L.tube(name, pts, radii, 14, cap_rings=3), mats["deco"], bone)
    side = up.orthogonal().normalized()
    h = L.ellipsoid(name + "_h", pts[3] + side * radii[3] * 0.55 + V((0, radii[3] * 0.6, 0)),
                    (size * 0.07, size * 0.07, size * 0.14), 8, 6)
    model.add(h, mats["white"], bone)


def vine(model, mats, pts, bone, r=0.018, leaf_size=0.08, every=4, name="liane"):
    """Liane : tube vert + petites feuilles alternées."""
    pts = [V(p) for p in pts]
    model.add(L.tube(name, pts, r, 8, cap_rings=2), mats["accent"], bone)
    for i in range(1, len(pts) - 1, every):
        d = (pts[i + 1] - pts[i - 1]).normalized()
        side = d.cross(V((0, 0, 1)))
        if side.length < 1e-3:
            side = V((1, 0, 0))
        side.normalize()
        sgn = 1 if (i // every) % 2 else -1
        leaf(model, mats, pts[i], (side * sgn + d * 0.4).normalized(), V((0, 0, 1)) if abs(d.z) < 0.7 else V((0, 1, 0)),
             leaf_size, bone, name=name + "_f")


def string_path(p0, ground, end, curl_turns=3.0, curl_r=0.032, n=14):
    """Ficelle de ballon : descend du nœud jusqu'au sol, traîne en S, puis frise en spirale (bolduc)."""
    p0, ground, end = V(p0), V(ground), V(end)
    pts = L.bezier_pts(p0, p0 + V((0, 0, -0.6 * (p0.z - ground.z))), ground + (ground - end).normalized() * 0.08 + V((0, 0, 0.02)),
                       ground, 8)
    d = (end - ground)
    side = d.cross(V((0, 0, 1))).normalized()
    for i in range(1, n + 1):
        t = i / n
        pts.append(ground + d * 0.55 * t + side * 0.04 * math.sin(math.pi * 2 * t))
    c0 = ground + d * 0.55
    dn = d.normalized()
    m = 40
    for i in range(1, m + 1):
        t = i / m
        a = L.TAU * curl_turns * t
        r = curl_r * (1 - 0.3 * t)
        pts.append(c0 + d * 0.45 * t + (side * math.sin(a) + V((0, 0, 1)) * (1 - math.cos(a))) * r)
    return pts


def hanging_path(top, bottom_z=0.02, curl_turns=3.0, curl_r=0.03, curl_h=0.13, n=18):
    """Ficelle de ballon qui pend à la verticale sous le nœud, légèrement ondulée, frisée au bout."""
    top = V(top)
    zc = bottom_z + curl_h
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(V((top.x + 0.022 * math.sin(math.pi * 2.2 * t) * t, top.y - 0.015 * math.sin(math.pi * t),
                      top.z + (zc - top.z) * t)))
    c = pts[-1]
    m = 36
    for i in range(1, m + 1):
        t = i / m
        a = L.TAU * curl_turns * t
        r = curl_r * (1 - 0.25 * t) * min(1.0, t * 6)
        pts.append(c + V((r * math.sin(a), r * (1 - math.cos(a)) - 0.0, -curl_h * t)))
    return pts


def add_hanging_string(model, mats, knot, bottom_z=0.02, parent="Body"):
    """Ficelle pendante skinnée sur la chaîne Ficelle_1..3 (os créés ici)."""
    knot = V(knot)
    pts = hanging_path(knot, bottom_z)
    h = knot.z - bottom_z
    heads = [knot, knot - V((0, 0, h * 0.4)), knot - V((0, 0, h * 0.75))]
    model.bone("Ficelle_1", heads[0], parent)
    model.bone("Ficelle_2", heads[1], "Ficelle_1")
    model.bone("Ficelle_3", heads[2], "Ficelle_2")
    balloon_string(model, mats, pts, [(f"Ficelle_{i + 1}", heads[i]) for i in range(3)])


def balloon_string(model, mats, pts, bones, r=0.007, mat_key="accent", knot=True, name="ficelle"):
    """Ajoute la ficelle `pts` ; `bones` = [(nom_os, position_tête)] pour une pondération en chaîne."""
    pts = [V(p) for p in pts]
    heads = [(b, V(h)) for b, h in bones]

    def w(co):
        out = {}
        for b, h in heads:
            out[b] = math.exp(-((co - h).length / 0.16) ** 2) + 1e-6
        return out

    model.add(L.tube(name, pts, r, 6, cap_rings=1), mats[mat_key], w if len(heads) > 1 else heads[0][0])
    if knot:
        k = pts[0]
        b0 = heads[0][0]
        model.add(L.ellipsoid(name + "_noeud", k + V((0, 0, 0.012)), (0.022, 0.022, 0.03), 10, 6), mats[mat_key], b0)
        for sx in (-1, 1):   # petit nœud papillon
            model.add(L.torus(name + "_boucle", k + V((sx * 0.03, 0, 0.015)), 0.022, 0.006, 14, 5,
                              M=Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Rotation(sx * 0.4, 4, "Y")), mats[mat_key], b0)


def star_deco(model, mats, pos, out, size, bone, n=4, mat_key="gold", name="etoile"):
    s = L.puffy(name, L.star_pts(n, size, size * 0.42), size * 0.35, size * 0.12, segs=3)
    L.xform(s, L.orient(V(pos), out))
    model.add(s, mats[mat_key], bone)


def halo(model, mats, center, radius, bone, name="halo"):
    h = L.torus(name, center, radius, radius * 0.11, 40, 10)
    model.add(h, mats["glow"], bone)
    for k in range(6):
        a = L.TAU * k / 6
        p = V(center) + V((math.cos(a) * radius, math.sin(a) * radius, 0))
        s = L.puffy(name + "_s", L.star_pts(4, radius * 0.16, radius * 0.06), radius * 0.06, radius * 0.02, segs=2)
        L.xform(s, L.orient(p, V((math.cos(a), math.sin(a), 0))))
        model.add(s, mats["gold"], bone)


# --------------------------------------------------------------------------------------------
# Application d'un type sur une famille
# --------------------------------------------------------------------------------------------
def decorate(model, elem, mats, A):
    """A : ancres fournies par la famille :
        crown   : [(pos, up, taille, os)] sommets de silhouette ;
        scatter : [(pos, normale, taille, os)] petites décorations de surface ;
        halo    : (centre, rayon, os) ;
        base    : [(pos, taille, os)] bas du modèle (fumée, bulles) ;
        face    : direction avant (pour orienter éclairs / vagues)."""
    face = A.get("face", V((0, 1, 0)))
    crown = A.get("crown", [])
    scatter = A.get("scatter", [])
    base = A.get("base", [])
    if elem == "lumiere":
        c, r, b = A["halo"]
        halo(model, mats, c, r, b)
        for i, (p, up, s, b) in enumerate(crown):
            star_deco(model, mats, V(p) + V(up) * s * 0.55, face, s * 0.55, b, n=4 if i % 2 else 5)
        for p, n, s, b in scatter:
            spark(model, mats, p, n, s * 0.8, b)
    elif elem == "tenebres":
        for i, (p, up, s, b) in enumerate(crown):
            horn(model, mats, p, up, s * 1.05, b, curl=1 if (i % 2 == 0) else -1)
        for p, s, b in base:
            smoke(model, mats, p, s, b, n=5, seed=int(abs(p[0]) * 100) + 3)
        for p, n, s, b in scatter:
            o = L.sphere("orbe", V(p) + V(n) * s * 0.3, s * 0.35, 10, 6)
            model.add(o, mats["glow"], b)
    elif elem == "glace":
        for i, (p, up, s, b) in enumerate(crown):
            crystal_cluster(model, mats, p, up, s * 1.1, b, n=4, seed=i + 7)
        for p, n, s, b in scatter:
            snowflake_emblem(model, mats, V(p) + V(n) * s * 0.1, n, s * 0.7, b, mat=mats["deco2"])
    elif elem == "feu":
        for i, (p, up, s, b) in enumerate(crown):
            flame(model, mats, p, up, s * 1.15, b, bend=0.5 if i % 2 else -0.5)
        for p, n, s, b in scatter:
            e = L.lumpy("braise", V(p) + V(n) * s * 0.15, (s * 0.32,) * 3, amp=0.2, seed=3, nu=10, nv=6)
            model.add(e, mats["glow"], b)
    elif elem == "eau":
        for i, (p, up, s, b) in enumerate(crown):
            droplet(model, mats, V(p) - V(up) * s * 0.1, up, s * (1.05 if i == len(crown) - 1 else 0.8), b)
        for p, n, s, b in scatter:
            bubble(model, mats, V(p) + V(n) * s * 0.3, s * 0.42, b)
        for p, s, b in base:
            for k in range(3):
                a = L.TAU * k / 3 + 0.4
                bubble(model, mats, V(p) + V((math.cos(a), math.sin(a), 0.4 * k)) * s * 0.45, s * (0.22 + 0.05 * k), b)
    elif elem == "plante":
        mats.setdefault("deco_leaf", mats["second"])
        for i, (p, up, s, b) in enumerate(crown):
            up = V(up).normalized()
            t = up.orthogonal().normalized()
            for k in range(3):
                a = L.TAU * k / 3 + i
                d = (up * 1.0 + (t * math.cos(a) + up.cross(t) * math.sin(a)) * 0.7).normalized()
                leaf(model, mats, p, d, (t * math.cos(a + 1.57) + up.cross(t) * math.sin(a + 1.57)), s * 1.25, b)
            flower(model, mats, V(p) + up * s * 0.25, face, s * 0.38, b)
        for pts, b in A.get("vine", []):
            vine(model, mats, pts, b)
        for j, (p, n, s, b) in enumerate(scatter):
            if j % 2 == 0:
                flower(model, mats, V(p) + V(n) * s * 0.05, n, s * 0.5, b)
            else:
                leaf(model, mats, p, V((0, 0, 1)) if abs(V(n).z) < 0.8 else V((0, 1, 0)), n, s * 0.9, b)
    elif elem == "eclair":
        for i, (p, up, s, b) in enumerate(crown):
            bolt(model, mats, V(p) - V(up) * s * 0.1, up, s * 1.45, b, face=face if abs(V(up).dot(face)) < 0.8 else V((1, 0, 0)),
                 flip=1 if i % 2 else -1)
        for p, n, s, b in scatter:
            spark(model, mats, V(p) + V(n) * s * 0.1, n, s * 0.7, b)
