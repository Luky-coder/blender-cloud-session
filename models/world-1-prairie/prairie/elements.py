"""Visage commun + détails propres à chacun des 7 éléments, posés sur les ancrages d'une famille."""
import math
import random

from mathutils import Matrix, Quaternion, Vector

from . import geo, rig
from .surface import decal, ellipse, frame_at, patch

TAU = math.tau


# ------------------------------------------------------------------------------------------- formes 2D

def poly_star(n=5, ro=1.0, ri=0.45, rot=0.0):
    return [((ro if k % 2 == 0 else ri) * math.cos(math.pi / 2 + rot + k * math.pi / n),
             (ro if k % 2 == 0 else ri) * math.sin(math.pi / 2 + rot + k * math.pi / n)) for k in range(2 * n)]


def poly_leaf(n=10, w=0.42):
    right = [(w * math.sin(math.pi * t) ** 0.8, -1 + 2 * t) for t in (i / n for i in range(1, n))]
    left = [(-x, y) for x, y in reversed(right)]
    return [(0, -1)] + right + [(0, 1)] + left


def poly_drop(n=16):
    pts = []
    for i in range(n):
        th = TAU * i / n
        x = math.sin(th) * abs(math.sin(th / 2)) ** 1.2
        y = math.cos(th)
        pts.append((x * 0.8, (y * 1.25 if y > 0 else y) * 0.85))
    return pts


def poly_flame():
    P = [(0.0, -1.0), (0.55, -0.8), (0.75, -0.3), (0.6, 0.2), (0.62, 0.62), (0.32, 0.38), (0.22, 1.0),
         (-0.12, 0.45), (-0.4, 0.75), (-0.62, 0.2), (-0.72, -0.35), (-0.5, -0.82)]
    return [(x * 0.8, y) for x, y in P]


def poly_bolt():
    P = [(0.10, 1.00), (0.62, 1.00), (0.24, 0.22), (0.58, 0.22), (-0.30, -1.00), (0.02, -0.06), (-0.34, -0.06)]
    return [(x * 0.9 - 0.1, y) for x, y in P]


def poly_crescent(n=14):
    outer = [(math.cos(a), math.sin(a)) for a in (math.radians(-150 + 300 * i / n) for i in range(n + 1))]
    inner = [(0.35 + 0.78 * math.cos(a), 0.78 * math.sin(a)) for a in (math.radians(140 - 280 * i / n) for i in range(n + 1))]
    return outer + inner


def poly_snowflake():
    polys = []
    for k in range(6):
        a = math.pi / 2 + k * math.pi / 3
        c, s = math.cos(a), math.sin(a)

        def R(x, y):
            return (x * c - y * s, x * s + y * c)
        polys.append([R(0.12, -0.07), R(1.0, -0.07), R(1.0, 0.07), R(0.12, 0.07)])
        for d, L in ((0.55, 0.32), (0.8, 0.2)):
            for sg in (-1, 1):
                b = sg * math.radians(50)
                ex, ey = d + L * math.cos(b), L * math.sin(b)
                nx, ny = -math.sin(b) * 0.05, math.cos(b) * 0.05
                polys.append([R(d - nx, -ny), R(ex - nx, ey - ny), R(ex + nx, ey + ny), R(d + nx, ny)]
                             if sg > 0 else [R(d + nx, ny), R(ex + nx, ey + ny), R(ex - nx, ey - ny), R(d - nx, -ny)])
    polys.append([(0.16 * math.cos(math.pi / 2 + k * math.pi / 3), 0.16 * math.sin(math.pi / 2 + k * math.pi / 3))
                  for k in range(6)])
    return polys


# ------------------------------------------------------------------------------------------- visage

def face(F, P, angry=1.0):
    """Yeux imprimés sur l'enveloppe (comme un ballon de fête) : regard en colère, ils marquent l'avant (+Y)."""
    e = F.eyes
    p, n, sp, sz, up = e["p"], e["n"], e["spacing"], e["size"], e.get("up", (0, 0, 1))
    k = F.s
    white = P["iris"] if P.get("iris") else P["eye_white"]
    sclera, pupils, shines, brows = [], [], [], []
    for side in (-1, 1):
        cx = side * sp
        sclera.append(ellipse(cx, 0, sz * 0.78, sz, 22))
        if P.get("iris"):
            pupils.append(ellipse(cx - side * 0.1 * sz, -0.08 * sz, sz * 0.16, sz * 0.62, 14))
        else:
            pupils.append(ellipse(cx - side * 0.13 * sz, -0.12 * sz, sz * 0.4, sz * 0.5, 16))
            shines.append(ellipse(cx - side * 0.02 * sz, 0.12 * sz, sz * 0.13, sz * 0.13, 8))
        th = 0.3 * sz
        x_in, x_out = cx - side * 0.95 * sz, cx + side * 0.95 * sz
        y_in, y_out = 0.78 * sz, (0.78 + 0.5 * angry) * sz
        quad = [(x_in, y_in - th / 2), (x_out, y_out - th / 2), (x_out, y_out + th / 2), (x_in, y_in + th / 2)]
        brows.append(quad if side > 0 else list(reversed(quad)))
    rig.add(decal(F.surf, "Yeux", sclera, p, n, up, 1.0, 0.0035 * k, white))
    rig.add(decal(F.surf, "Pupilles", pupils, p, n, up, 1.0, 0.0065 * k, P["pupil"]))
    if shines:
        rig.add(decal(F.surf, "Yeux_Reflets", shines, p, n, up, 1.0, 0.009 * k, P["shine"], subdiv=0))
    rig.add(decal(F.surf, "Sourcils", brows, p, n, up, 1.0, 0.0085 * k, P["brow"]))


def shine(F, P):
    """Reflet stylisé « cartoon » sur l'enveloppe."""
    (p, n), size, ang = F.shine
    a = math.radians(ang)
    poly = ellipse(0, 0, 1.0, 0.32, 18, a)
    small = ellipse(0.85 * math.cos(a) - 0.55 * math.sin(a), 0.85 * math.sin(a) + 0.55 * math.cos(a), 0.17, 0.17, 10)
    rig.add(decal(F.surf, "Reflet", [poly, small], p, n, (0, 0, 1), size, 0.003 * F.s, P["shine"]))


# ------------------------------------------------------------------------------------------- utilitaires

def _tilted(n, tilt_deg, az_deg, up=(0, 0, 1)):
    t, b, n = frame_at(Vector(), n, up)
    a = math.radians(az_deg)
    axis = t * math.cos(a) + b * math.sin(a)
    return (Quaternion(axis, math.radians(tilt_deg)) @ n).normalized()


def _orbit_points(F, count, phase=0.3, wobble=0.06):
    oc, orad, oax = F.orbit
    t, b, _ = frame_at(Vector(), oax, (0, 0, 1) if abs(oax.z) < 0.9 else (0, 1, 0))
    pts = []
    for k in range(count):
        a = TAU * k / count + phase
        r = orad * (1 + 0.08 * math.sin(3 * a))
        pts.append(oc + (t * math.cos(a) + b * math.sin(a)) * r + oax * wobble * F.s * math.sin(2 * a + 1))
    return pts


def _emblems(F, P, name, polys, mat, scale=1.0, offset=0.004, rot_deg=0.0, inner=None):
    for i, (p, n, size) in enumerate(F.emblems):
        up = Vector((0, 0, 1)) if abs(Vector(n).z) < 0.9 else Vector((0, 1, 0))
        if rot_deg:
            up = Quaternion(Vector(n), math.radians(rot_deg)) @ up
        rig.add(decal(F.surf, f"{name}_{i}", polys, p, n, up, size * scale, offset * F.s, mat))
        if inner:
            ipolys, imat, iscale = inner
            rig.add(decal(F.surf, f"{name}_{i}_Coeur", ipolys, p, n, up, size * scale * iscale, offset * 1.8 * F.s, imat))


def _path_offset(path, amp_fn, offset):
    """Décale un chemin de surface sur le côté (dans le plan tangent) : vagues, zigzags."""
    out = []
    N = len(path)
    for i, (p, n) in enumerate(path):
        tan = (path[(i + 1) % N][0] - path[i - 1][0])
        side = Vector(n).cross(tan)
        side = side.normalized() if side.length > 1e-9 else Vector((0, 0, 1))
        out.append(p + Vector(n) * offset + side * amp_fn(i / N))
    return out


def _leaf_on(name, p, direction, normal, length, width, mat, bend=0.25, fold=0.22):
    lf = geo.leaf(name, length, width, mat, fold=fold, bend=bend, nu=7, nv=2, thick=0.003 * max(length / 0.1, 1))
    geo.transform(lf, geo.basis(p, direction, normal))
    return lf


def vine(F, P, path, radius=0.013, leaf_every=0.075, flowers=(0.42, 0.86), leaf_size=0.092, seed=3, rule="lobes",
         petal=None):
    """Liane posée sur l'enveloppe avec feuilles et fleurs."""
    rnd = random.Random(seed)
    s = F.s
    pts = [p + Vector(n) * radius * 0.6 for p, n in path]
    rig.add(geo.tube("Liane", pts, radius * s, 7, P.get("vine", P["string"])), rule)
    acc = 0.0
    side = 1
    for i in range(1, len(path) - 1):
        acc += (path[i][0] - path[i - 1][0]).length
        if acc < leaf_every * s:
            continue
        acc = 0.0
        p, n = path[i]
        tan = (path[i + 1][0] - path[i - 1][0]).normalized()
        n = Vector(n)
        d = (n.cross(tan) * side * 0.8 + n * 0.35 + tan * 0.3).normalized()
        L = leaf_size * s * rnd.uniform(0.75, 1.1)
        rig.add(_leaf_on("Liane_Feuille", pts[i], d, n, L, L * 0.55, P["accent"] if side > 0 else P["accent2"],
                         bend=0.15, fold=0.18), rule)
        side = -side
    for f in flowers:
        i = int(f * (len(path) - 1))
        p, n = path[i]
        fl = geo.flower("Fleur", 0.045 * s, petal or P.get("petal", P["accent2"]), P["glow"])
        geo.transform(fl, geo.basis_z(pts[i] + Vector(n) * 0.01 * s, n))
        rig.add(fl, rule)


# =========================================================================================== 7 ÉLÉMENTS

def deco_lumiere(F, P):
    s = F.s
    p, n = F.crest[0]
    hc = p + n * 0.13 * s
    hn = _tilted(n, 34, 0, (0, 1, 0))
    rig.add(geo.torus("Halo", 0.15 * s, 0.02 * s, 36, 8, P["glow"], geo.basis_z(hc, hn)))
    # rayons dorés autour du halo
    for k in range(8):
        a = TAU * k / 8
        t, b, _ = frame_at(Vector(), hn)
        d = t * math.cos(a) + b * math.sin(a)
        rig.add(geo.cylinder("Halo_Rayon", hc + d * 0.19 * s, hc + d * 0.245 * s, 0.009 * s, 6, P["accent2"], r1=0.002 * s))
    for k, q in enumerate(_orbit_points(F, 5)):
        big = k % 2 == 0
        st = geo.star3d(f"Etoile_Orbite_{k}", (0.06 if big else 0.045) * s, 0.024 * s, 0.02 * s,
                        P["glow"] if big else P["accent"])
        face_dir = ((q - F.orbit[0]).normalized() + Vector((0, 0.8, 0))).normalized()
        geo.transform(st, geo.basis_z(q, face_dir, (0, 0, 1)) @ geo.rot((0, 0, 1), 15 * k))
        rig.add(st, ("bone", "Orbite"))
    _emblems(F, P, "Soleil", [poly_star(8, 1.0, 0.55)], P["accent"], 0.85, inner=([ellipse(0, 0, 0.5, 0.5, 18)], P["accent2"], 1.0))
    # petites étoiles scintillantes sur l'enveloppe
    for k, (p2, n2) in enumerate(F.under[:3]):
        rig.add(decal(F.surf, "Scintillement", [poly_star(4, 1.0, 0.25)], p2, n2, (0, 0, 1) if abs(n2.z) < 0.9 else (0, 1, 0),
                      0.045 * s, 0.004 * s, P["accent2"]))


def deco_tenebres(F, P):
    s = F.s
    for i, (p, n) in enumerate(F.horns):
        side = -1 if i == 0 else 1
        out = Vector((side, 0, 0))
        pts = [p - n * 0.04 * s, p + n * 0.05 * s, p + n * 0.11 * s + out * 0.035 * s,
               p + n * 0.15 * s + out * 0.085 * s + Vector((0, 0, 0.02)) * s]
        path = geo.catmull(pts, 6)
        rig.add(geo.tapered_tube("Corne", path, 0.042 * s, 0.003 * s, 10, P["accent"], power=1.3))
        rig.add(geo.torus("Corne_Anneau", 0.04 * s, 0.009 * s, 16, 6, P["glow"], geo.basis_z(p + n * 0.012 * s, n)))
    # fumée sombre : volutes sous le ballon et autour
    rnd = random.Random(7)
    for k, (p, n) in enumerate(F.under):
        c = p + Vector(n) * 0.04 * s + Vector((0, 0, -0.03 * s))
        rig.add(geo.puff_cluster("Fumee", c, 0.075 * s * rnd.uniform(0.85, 1.15),
                                 P["smoke"] if k % 2 else P["smoke2"], count=4, seed=k))
    for k, q in enumerate(_orbit_points(F, 5, phase=1.0, wobble=0.1)):
        rig.add(geo.puff_cluster("Fumee_Volute", q, 0.055 * s, P["smoke2"], count=3, seed=20 + k), ("bone", "Orbite"))
        rig.add(geo.sphere("Etincelle_Sombre", q + Vector((0, 0, 0.06 * s)), 0.012 * s, 8, 4, (1, 1, 1), P["glow"]),
                ("bone", "Orbite"))
    _emblems(F, P, "Croissant", [poly_crescent()], P["accent2"], 0.8, rot_deg=-25)


def deco_glace(F, P):
    s = F.s
    p, n = F.crest[0]
    axis = (p - F.surf.center).normalized()
    th = F.cap_theta
    rig.add(patch(F.surf, "Givre", axis, lambda ph: th * (1 + 0.2 * math.sin(5 * ph) + 0.1 * math.sin(11 * ph + 1)),
                  0.006 * s, P["frost"], n_theta=9, n_phi=48))
    spec = [(0, 0, 0.21, 0.036), (30, 20, 0.15, 0.03), (32, 140, 0.13, 0.028), (34, 250, 0.14, 0.03), (24, 320, 0.1, 0.022)]
    for k, (tilt, az, h, r) in enumerate(spec):
        d = _tilted(n, tilt, az)
        t, b, _ = frame_at(Vector(), n)
        off = (t * math.cos(math.radians(az)) + b * math.sin(math.radians(az))) * (0.035 * s if tilt else 0)
        cr = geo.crystal("Cristal", h * s, r * s, P["accent"] if k % 2 == 0 else P["accent2"])
        geo.transform(cr, geo.basis_z(p + off - n * 0.02 * s, d) @ geo.rot((0, 0, 1), 17 * k))
        rig.add(cr)
    for k, (p2, n2) in enumerate(F.under):
        down = (Vector(n2) * 0.35 + Vector((0, 0, -1))).normalized()
        L = (0.12 if k % 2 == 0 else 0.085) * s
        ic = geo.lathe("Stalactite", [(0, -L), (0.012 * s, -L * 0.55), (0.022 * s, -0.01 * s), (0.016 * s, 0.01 * s)],
                       8, "Z", P["accent"])
        geo.transform(ic, geo.basis_z(p2 + Vector(n2) * 0.005 * s, -down))
        rig.add(ic)
    for k, q in enumerate(_orbit_points(F, 5, phase=0.7)):
        sh = geo.crystal("Eclat_Glace", 0.06 * s, 0.018 * s, P["accent"], sides=4)
        geo.transform(sh, geo.basis_z(q, _tilted(Vector((0, 0, 1)), 35, 70 * k)))
        rig.add(sh, ("bone", "Orbite"))
    _emblems(F, P, "Flocon", poly_snowflake(), P["body2"], 0.9, offset=0.004, inner=None)


def deco_feu(F, P):
    s = F.s
    p, n = F.crest[0]
    spec = [(0, 0, 0.27, 0.075, 0.1), (38, 0, 0.17, 0.055, 0.35), (38, 180, 0.17, 0.055, 0.35),
            (30, 90, 0.13, 0.045, 0.3), (30, 270, 0.12, 0.045, 0.3)]
    t, b, _ = frame_at(Vector(), n)
    for k, (tilt, az, h, r, bend) in enumerate(spec):
        d = _tilted(n, tilt, az + 90)
        side_dir = (t * math.cos(math.radians(az)) + b * math.sin(math.radians(az)))
        base = p - n * 0.03 * s + side_dir * (0.04 * s if tilt else 0)
        M = geo.basis_z(base, d, side_dir if tilt else (0, 1, 0)) @ geo.rot((0, 0, 1), -90 if tilt else 0)
        outer = geo.flame("Flamme", h * s, r * s, P["accent"], bend=bend)
        geo.transform(outer, M)
        rig.add(outer)
        inner = geo.flame("Flamme_Coeur", h * 0.62 * s, r * 0.62 * s, P["accent2"], bend=bend * 0.8)
        geo.transform(inner, M @ Matrix.Translation((0, 0, 0.005 * s)) @ Matrix.Translation((0, r * 0.45 * s, 0)))
        rig.add(inner)
    for extra in F.crest[1:]:
        p2, n2 = extra
        for k, (h, off) in enumerate(((0.16, 0), (0.1, 0.05), (0.1, -0.05))):
            fl = geo.flame("Flamme_Dos", h * s, 0.045 * s, P["accent"] if k == 0 else P["accent2"], bend=-0.2)
            geo.transform(fl, geo.basis_z(p2 - Vector(n2) * 0.02 * s + Vector((0, off * s, 0)), _tilted(n2, 20 * (k != 0), 0)))
            rig.add(fl)
    for k, q in enumerate(_orbit_points(F, 6, phase=0.2, wobble=0.09)):
        rig.add(geo.sphere("Braise", q, (0.022 if k % 2 else 0.015) * s, 10, 5, (1, 1, 1.2), P["glow"]), ("bone", "Orbite"))
        if k % 2 == 0:
            fl = geo.flame("Flammeche", 0.07 * s, 0.022 * s, P["accent"], seg=8, bend=0.3)
            geo.transform(fl, geo.basis_z(q + Vector((0, 0, 0.02 * s)), (0, 0, 1)))
            rig.add(fl, ("bone", "Orbite"))
    _emblems(F, P, "Flamme_Motif", [poly_flame()], P["accent"], 0.95, inner=([poly_flame()], P["accent2"], 0.55))
    # chaleur : bandeau orange sous l'équateur
    pts = _path_offset(F.band, lambda u: 0.0, 0.004 * s)
    rig.add(geo.tube("Bandeau_Chaleur", pts + [pts[0]], 0.012 * s, 6, P["body2"], caps=False))


def deco_eau(F, P):
    s = F.s
    p, n = F.crest[0]
    drop = geo.teardrop("Goutte_Crete", 0.07 * s, P["accent"], stretch=1.9)
    geo.transform(drop, geo.basis_z(p + n * 0.06 * s, n))
    rig.add(drop)
    for extra in F.crest[1:]:
        p2, n2 = extra
        d2 = geo.teardrop("Goutte_Dos", 0.045 * s, P["accent"], stretch=1.9)
        geo.transform(d2, geo.basis_z(p2 + Vector(n2) * 0.04 * s, n2))
        rig.add(d2)
    for amp_k, (off, rad, mat) in enumerate(((0.0, 0.014, P["accent2"]), (0.05, 0.008, P["body2"]))):
        pts = _path_offset(F.band, lambda u, o=off: (0.028 * math.sin(TAU * 9 * u) - o) * s, 0.006 * s)
        rig.add(geo.tube("Vague", pts + [pts[0]], rad * s, 6, mat, caps=False))
    rnd = random.Random(5)
    for k, q in enumerate(_orbit_points(F, 7, phase=0.5, wobble=0.12)):
        r = rnd.uniform(0.03, 0.06) * s
        rig.add(geo.sphere("Bulle", q, r, 14, 8, (1, 1, 1), P["glow"]), ("bone", "Orbite"))
        rig.add(geo.sphere("Bulle_Reflet", q + Vector((-0.4, 0.5, 0.55)).normalized() * r * 0.72, r * 0.22, 8, 4,
                           (1, 1, 1), P["shine"]), ("bone", "Orbite"))
    for k, (p2, n2) in enumerate(F.under):
        q = p2 + Vector(n2) * 0.02 * s + Vector((0, 0, -0.07 if k % 2 == 0 else -0.04)) * s
        d = geo.teardrop("Gouttelette", 0.022 * s, P["accent"])
        geo.transform(d, Matrix.Translation(q))
        rig.add(d)
    _emblems(F, P, "Goutte_Motif", [poly_drop()], P["body2"], 0.85, inner=([ellipse(-0.18, -0.2, 0.18, 0.28, 10, 0.4)], P["shine"], 1.0))


def deco_plante(F, P):
    s = F.s
    p, n = F.crest[0]
    for k in range(5):
        az = 72 * k + 18
        d = _tilted(n, 68, az)
        L = (0.2 if k % 2 == 0 else 0.17) * s
        rig.add(_leaf_on("Feuille_Couronne", p - n * 0.015 * s, d, n, L, L * 0.52,
                         P["accent"] if k % 2 else P["accent2"], bend=-0.18, fold=0.3))
    for k, side in enumerate((-1, 1)):
        d = _tilted(n, 32, 90 + side * 90)
        L = 0.21 * s
        rig.add(_leaf_on("Feuille_Pousse", p + n * 0.03 * s, d, Vector((0, 1, 0.2)), L, L * 0.5,
                         P["accent2"] if k else P["accent"], bend=0.12, fold=0.28))
    # pousse enroulée au centre
    curl = []
    for i in range(24):
        t = i / 23
        a = TAU * 1.2 * t
        r = 0.035 * s * (1 - 0.6 * t)
        curl.append(p + n * (0.11 * s * min(t * 1.6, 1)) + Vector((r * math.cos(a) * t, r * math.sin(a) * t, 0)))
    rig.add(geo.tapered_tube("Pousse", curl, 0.012 * s, 0.004 * s, 7, P["vine"]))
    for extra in F.crest[1:]:
        p2, n2 = extra
        for k, az in enumerate((0, 180)):
            rig.add(_leaf_on("Feuille_Dos", p2, _tilted(n2, 50, az), n2, 0.11 * s, 0.06 * s, P["accent"]))
    vine(F, P, F.vine)
    _emblems(F, P, "Feuille_Motif", [poly_leaf()], P["body2"], 0.95, rot_deg=-30,
             inner=([[(-0.04, -0.85), (0.04, -0.85), (0.03, 0.8), (-0.03, 0.8)]], P["accent2"], 1.0))
    # feuilles sur la ficelle (qui devient une liane)
    if F.string_path:
        sp = F.string_path
        for k, f in enumerate((0.3, 0.62)):
            i = int(f * (len(sp) - 1))
            tan = (sp[i + 1] - sp[i - 1]).normalized()
            out = Vector((1 if k % 2 == 0 else -1, 0.3, 0)).normalized()
            rig.add(_leaf_on("Ficelle_Feuille", sp[i], (out + tan * -0.3).normalized(), Vector((0, 1, 0.3)), 0.06 * s,
                             0.035 * s, P["accent"]), ("chain", F.chain, F.chain_pts))


def deco_eclair(F, P):
    s = F.s
    p, n = F.crest[0]
    t, b, _ = frame_at(Vector(), n)
    for k, (az, mat, h) in enumerate(((0, P["accent"], 0.3), (180, P["accent2"], 0.24))):
        d = _tilted(n, 24, az + 90)
        bl = geo.bolt("Eclair_Crete", h * s, 0.035 * s, mat, width=h * 0.6 * s)
        side = t * math.cos(math.radians(az)) + b * math.sin(math.radians(az))
        M = geo.basis_z(p + n * (h * 0.42 * s) + side * 0.03 * s, d, (0, 1, 0)) @ geo.rot((1, 0, 0), 180)
        geo.transform(bl, M)
        rig.add(bl)
    for extra in F.crest[1:]:
        p2, n2 = extra
        bl = geo.bolt("Eclair_Dos", 0.15 * s, 0.025 * s, P["accent2"], width=0.08 * s)
        geo.transform(bl, geo.basis_z(Vector(p2) + Vector(n2) * 0.06 * s, n2, (1, 0, 0)) @ geo.rot((1, 0, 0), 180))
        rig.add(bl)
    pts = _path_offset(F.band, lambda u: (0.03 * (1 if int(u * 24) % 2 == 0 else -1)) * s, 0.006 * s)
    zig = []
    for i in range(0, len(pts), max(1, len(pts) // 24)):
        zig.append(pts[i])
    rig.add(geo.tube("Zigzag", zig + [zig[0]], 0.012 * s, 6, P["body2"], caps=False, smooth=False))
    for k, q in enumerate(_orbit_points(F, 6, phase=0.1, wobble=0.1)):
        sp = geo.star3d("Etincelle", (0.05 if k % 2 == 0 else 0.035) * s, 0.012 * s, 0.012 * s, P["glow"], n=4)
        face_dir = ((q - F.orbit[0]).normalized() + Vector((0, 0.8, 0))).normalized()
        geo.transform(sp, geo.basis_z(q, face_dir) @ geo.rot((0, 0, 1), 30 * k))
        rig.add(sp, ("bone", "Orbite"))
    _emblems(F, P, "Eclair_Motif", [poly_bolt()], P["body2"], 0.9)


DECOR = {
    "lumiere": deco_lumiere, "tenebres": deco_tenebres, "glace": deco_glace, "feu": deco_feu,
    "eau": deco_eau, "plante": deco_plante, "eclair": deco_eclair,
}
