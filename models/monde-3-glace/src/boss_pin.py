"""Mini-boss — Le Pin Gonflable (type Eau, PV 900).

Immense sapin entièrement gonflable, version aquatique : quatre étages de branches-boudins festonnés
(bleu abysse / turquoise lagon en alternance), bulles et gouttes d'eau sur les branches, algues-lianes, tronc côtelé, six racines gonflables au sol, grand visage sur le
deuxième étage, étoile dorée au sommet, boules et guirlandes dorées, pommes de pin décoratives,
neige sur les branches, valve à l'arrière. Deux grandes branches-bras repliées et quatre lianes
qui se déploient en phase 2. Projectiles intégrés (pomme de pin, racine surgissante, bloc de
neige), cachés (échelle 0) hors de leurs attaques.
"""
import math

from mathutils import Matrix, Vector

import elements as E
import w3lib as L
from w3lib import Pose, TAU, decay, ease, osc, track, track3

V = Vector
FAMILY = ("Boss", "Mini-boss Pin Gonflable", 900)

# (z bas, hauteur, rayon, nombre de festons)
TIERS = [(0.75, 1.25, 1.55, 9), (1.55, 1.15, 1.25, 8), (2.3, 1.05, 0.95, 7), (2.95, 1.0, 0.62, 6)]
CTRL = [(0.0, 0.18), (0.45, 0.1), (0.85, 0.02), (1.0, 0.08), (1.03, 0.17), (0.93, 0.27), (0.7, 0.42),
        (0.45, 0.66), (0.2, 0.88), (0.0, 1.0)]


def _catmull(pts, n):
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(pts[-1])
    return out


PROFILE = _catmull(CTRL, 4)   # 37 points (r/R, z/h) du dessous vers la pointe


def tier_point(k, s, ph, off=0.0):
    """Point de la surface de l'étage k : s ∈ [0,1] le long du profil, ph angle (π/2 = avant)."""
    zb, h, R, n = TIERS[k]
    f = s * (len(PROFILE) - 1)
    i = min(int(f), len(PROFILE) - 2)
    a = f - i
    rr = PROFILE[i][0] * (1 - a) + PROFILE[i + 1][0] * a
    zz = PROFILE[i][1] * (1 - a) + PROFILE[i + 1][1] * a
    lobe = abs(math.cos(n * (ph - math.pi / 2) / 2)) ** 0.5
    r = rr * R * (1 + 0.24 * (lobe - 0.55) * rr ** 2)
    z = zb + zz * h - 0.1 * (1 - lobe) * rr ** 3     # les creux entre festons retombent un peu
    p = V((r * math.cos(ph), r * math.sin(ph), z))
    n_ = V((math.cos(ph), math.sin(ph), 0.0)) * 0.7 + V((0, 0, 1)) * 0.7
    return p + n_.normalized() * off


def tier_z_of_s(k, s):
    return tier_point(k, s, math.pi / 2).z


def find_s(k, target_r_frac, upper=True):
    """Paramètre s où le profil (côté supérieur) atteint une fraction de rayon donnée."""
    rng = range(15, len(PROFILE)) if upper else range(0, 16)
    best = min(rng, key=lambda i: abs(PROFILE[i][0] - target_r_frac))
    return best / (len(PROFILE) - 1)


def pine_cone(name, center, size, axis=V((0, 0, -1))):
    def disp(u, v, p):
        return 1 + 0.16 * abs(math.sin(TAU * u * 6 + v * 10)) ** 0.7 * math.sin(math.pi * v) ** 0.5

    ob = L.ellipsoid(name, (0, 0, 0), (size * 0.5, size * 0.5, size), 20, 14, disp)
    q = V((0, 0, 1)).rotation_difference(V(axis).normalized())
    ob.data.transform(Matrix.Translation(center) @ q.to_matrix().to_4x4())
    return ob


def materials(elem="eau"):
    """Palette Eau : bleu abysse, turquoise lagon, écume blanche, perles, algues, or."""
    mats = E.materials("eau")
    mats["main"] = L.mat("Sapin_Abysse", "#1B5EA8", 0.18)
    mats["second"] = L.mat("Sapin_Lagon", "#38C3D3", 0.18)
    mats["accent"] = L.mat("Sapin_Liseré", "#0F3A6B", 0.25)
    mats["bark"] = L.mat("Tronc_Gonflable", "#2E5E82", 0.3)
    mats["cone"] = L.mat("Pomme_de_Pin", "#8B5A2B", 0.35)
    mats["bauble2"] = L.mat("Perle", "#EAF8FF", 0.1, metal=0.3)
    mats["deco_leaf"] = L.mat("Algue", "#27B597", 0.22)
    mats["leaf"] = mats["deco_leaf"]
    return mats


def water_decor(m, mats):
    """Bulles et gouttes d'eau gonflables posées sur les étages (signature du type Eau)."""
    for k, (zb, h, R, n) in enumerate(TIERS):
        b = f"Etage_{k + 1}"
        s_top = find_s(k, 0.9)
        for j in range(n):
            ph = math.pi / 2 + TAU * j / n
            if j % 2 == 1 and k < 3:          # gouttes sur les festons sans neige
                p = tier_point(k, s_top, ph, 0.0)
                up = (V((math.cos(ph), math.sin(ph), 0)) * 0.4 + V((0, 0, 1))).normalized()
                E.droplet(m, mats, p, up, 0.16 + 0.02 * (3 - k), b)
        for j in range(3):                    # grappes de bulles sur les pentes
            ph = 0.9 + TAU * j / 3 + 0.4 * k
            p = tier_point(k, find_s(k, 0.55), ph, 0.08)
            E.bubble(m, mats, p, 0.09, b)
            E.bubble(m, mats, p + V((0.08, 0.05, 0.1)), 0.055, b)


def build_geometry(m, mats):
    m.bone("Root", (0, 0, 0))
    m.bone("Tronc", (0, 0, 0.5), "Root")
    zs = []
    parent = "Tronc"
    for k, (zb, h, R, n) in enumerate(TIERS):
        zc = zb + 0.35 * h
        zs.append(zc)
        m.bone(f"Etage_{k + 1}", (0, 0, zc), parent)
        parent = f"Etage_{k + 1}"
    m.bone("Visage", (0, 0.95, 2.05), "Etage_2")
    m.bone("Bouche", (0, 1.25, 1.7), "Etage_2")
    m.bone("Etoile", (0, 0, 3.95), "Etage_4")
    m.bone("Bras_G", (-1.05, 0, 1.95), "Etage_2")
    m.bone("Bras_D", (1.05, 0, 1.95), "Etage_2")
    for i in range(4):
        m.bone(f"Liane_{i + 1}", (0, 0, 0), "Etage_1" if i < 2 else "Etage_2")   # têtes fixées plus bas
    for i in range(6):
        a = TAU * i / 6 + math.pi / 6
        m.bone(f"Racine_{i + 1}", (math.cos(a) * 0.4, math.sin(a) * 0.4, 0.25), "Root")
    m.bone("Proj_Pomme", (0.85, 0.9, 1.6), "Root")
    m.bone("Proj_Racine", (0, 3.4, 0.0), "Root")
    m.bone("Proj_Neige", (0, 0.95, 2.4), "Root")
    m.bone("CTRL_Formes", (0, 0, -0.3), deform=False)

    names = ["Tronc"] + [f"Etage_{k + 1}" for k in range(4)]
    heights = [0.5] + zs

    def zweight(co):
        return {nm: math.exp(-((co.z - zh) / 0.42) ** 2) + (1e-4 if nm == "Tronc" else 0)
                for nm, zh in zip(names, heights)}

    # Tronc côtelé + couture
    def trunk(u, v):
        ph = TAU * u
        z = 0.08 + 0.95 * v
        r = 0.45 * (1 + 0.07 * abs(math.sin(5 * ph)) ** 0.4) * (1 + 0.12 * (1 - v) ** 3)
        return V((r * math.cos(ph), r * math.sin(ph), z))

    m.add(L.surface("tronc", trunk, 40, 10, pole0=False), mats["bark"], "Tronc")
    m.add(L.torus("tronc_couture", (0, 0, 0.62), 0.47, 0.025, 40, 6), mats["accent"], "Tronc")

    # Racines gonflables
    for i in range(6):
        a = TAU * i / 6 + math.pi / 6
        d = V((math.cos(a), math.sin(a), 0))
        ln = 1.25 + 0.15 * (i % 2)
        pts = L.bezier_pts(d * 0.35 + V((0, 0, 0.32)), d * 0.75 + V((0, 0, 0.3)), d * ln * 0.85 + V((0, 0, 0.06)),
                           d * ln + V((0, 0, 0.14)), 10)
        radii = [0.2 - 0.12 * (j / 10) ** 0.8 for j in range(11)]
        m.add(L.tube("racine", pts, radii, 14, cap_rings=3), mats["bark"], f"Racine_{i + 1}")
        m.add(L.lumpy("neige_racine", d * ln * 0.7 + V((0, 0, 0.2)), (0.13, 0.11, 0.05), amp=0.25, seed=i,
                      nu=10, nv=6), mats["snow"], f"Racine_{i + 1}")

    # Étages de branches gonflables
    for k, (zb, h, R, n) in enumerate(TIERS):
        mat = mats["main"] if k % 2 == 0 else mats["second"]
        ob = L.surface(f"etage_{k + 1}", lambda u, v, k=k: tier_point(k, v, TAU * u), 120, 36, pole0=True, pole1=True)
        m.add(ob, mat, zweight)
        # couture du bord (passepoil)
        s_rim = find_s(k, 1.03, upper=False) + 0.02
        ring = [tier_point(k, s_rim + 0.04, TAU * i / 120, 0.015) for i in range(121)]
        m.add(L.tube("passepoil", ring, 0.018, 6, caps=(False, False)), mats["accent"], zweight)
        # neige sur un feston sur deux, boules dorées / turquoise entre les festons
        s_top = find_s(k, 0.9)
        for j in range(n):
            ph = math.pi / 2 + TAU * j / n
            if j % 2 == 0 or k == 3:
                p = tier_point(k, s_top, ph, 0.02)
                m.add(L.lumpy("neige", p, (0.2 * R / 1.2, 0.2 * R / 1.2, 0.06), amp=0.25, seed=j + 10 * k,
                              nu=14, nv=8), mats["snow"], zweight)
            if k < 3 and j % 2 == 1:
                ph2 = ph + math.pi / n
                p = tier_point(k, find_s(k, 1.0, upper=False), ph2, 0.0) + V((0, 0, -0.1))
                b = mats["gold"] if (j // 2) % 2 == 0 else mats["bauble2"]
                m.add(L.sphere("boule", p, 0.085, 14, 10), b, zweight)
                m.add(L.tube("boule_attache", [p + V((0, 0, 0.07)), p + V((0, 0, 0.12))], 0.025, 8, cap_rings=1),
                      mats["gold"], zweight)
        # guirlande dorée festonnée
        if k < 3:
            s_g = find_s(k, 0.62)
            pts = []
            for i in range(97):
                ph = TAU * i / 96
                sag = abs(math.sin(n * (ph - math.pi / 2) / 2 * 1.0))
                pts.append(tier_point(k, s_g, ph, 0.07) + V((0, 0, -0.1 * sag)))
            m.add(L.tube("guirlande", pts, 0.036, 8, caps=(False, False)), mats["gold"], zweight)

    # Étoile dorée au sommet
    st = L.puffy("etoile", L.star_pts(5, 0.36, 0.16), 0.14, 0.05, segs=3)
    L.xform(st, Matrix.Translation((0, 0, 4.2)))
    m.add(st, mats["gold"], "Etoile")
    m.add(L.sphere("etoile_coeur", (0, 0.08, 4.2), 0.08, 12, 8), mats["glow"], "Etoile")

    # Visage (étage 2) : yeux, sourcils, grande bouche sur le feston avant
    for sx in (-1, 1):
        ph = math.pi / 2 - sx * 0.36
        s_e = find_s(1, 0.74)
        p = tier_point(1, s_e, ph, 0.0) + V((0, 0, 0.12))
        nrm = V((math.cos(ph), math.sin(ph), 0.45)).normalized()
        E.eye(m, mats, p, nrm, 0.27, "Visage", side=("G" if sx < 0 else "D"), look=V((0, 0, -0.25)), pupil_k=0.5)
        E.brow(m, mats, p + V((sx * 0.02, 0.08, 0.31)), nrm, 0.38, 0.06, 22 * sx, "Visage", side=("G" if sx < 0 else "D"))
    pm = tier_point(1, find_s(1, 1.0, upper=False) + 0.03, math.pi / 2, 0.0)
    E.grin(m, mats, pm + V((0, 0.05, 0.14)), V((0, 1, 0.1)), 0.55, 0.3, "Bouche")

    # Pommes de pin décoratives
    for k, ph in ((0, 0.6), (0, 2.5), (1, 0.15), (1, 3.0), (0, 4.2)):
        p = tier_point(k, find_s(k, 1.0, upper=False), ph, 0.0) + V((0, 0, -0.18))
        m.add(pine_cone("pomme_deco", p, 0.17), mats["cone"], zweight)
        m.add(L.lumpy("pomme_neige", p + V((0, 0, 0.13)), (0.07, 0.07, 0.035), amp=0.2, seed=int(ph * 10), nu=8, nv=6),
              mats["snow"], zweight)

    # Valve (dos de l'étage 1)
    pv = tier_point(0, find_s(0, 0.6), -math.pi / 2, 0.0)
    Mv = L.orient(pv, V((0, -1, 0.5)))
    for ob in (L.tube("valve", [V((0, -0.02, 0)), V((0, 0.1, 0))], 0.08, 12, cap_rings=2),
               L.torus("valve_bague", (0, 0.06, 0), 0.09, 0.025, 16, 6, M=Matrix.Rotation(math.pi / 2, 4, "X")),
               L.ellipsoid("valve_bouchon", (0, 0.14, 0), (0.055, 0.035, 0.055), 10, 6)):
        m.add(L.xform(ob, Mv), mats["valve"], zweight)

    # Bras-branches (repliés au repos, déployés en phase 2)
    for sx, b in ((-1, "Bras_G"), (1, "Bras_D")):
        sh = V((sx * 1.05, 0, 1.95))
        d = V((sx * 0.62, 0.15, -0.78)).normalized()
        pts = [sh + d * t for t in (0.0, 0.4, 0.8, 1.15)]
        m.add(L.tube("bras", pts, [0.17, 0.15, 0.12, 0.1], 14, cap_rings=3), mats["second"], b)
        m.add(L.sphere("bras_bout", pts[-1] + d * 0.1, 0.13, 14, 10), mats["snow"], b)
        side = d.cross(V((0, 1, 0))).normalized()
        for t, sgn in ((0.45, 1), (0.75, -1), (0.95, 1)):
            base = sh + d * t
            tip = base + (d * 0.6 + side * sgn * 0.8).normalized() * 0.35
            m.add(L.tube("brindille", [base, tip], [0.08, 0.06], 10, cap_rings=3), mats["main"], b)
            m.add(L.sphere("brindille_neige", tip + (tip - base).normalized() * 0.03, 0.065, 10, 6), mats["snow"], b)
        m.add(L.torus("bras_collier", sh + d * 0.12, 0.17, 0.03, 20, 6,
                      M=L.orient(V((0, 0, 0)), d) @ Matrix.Rotation(math.pi / 2, 4, "X")), mats["gold"], b)

    # Lianes pendantes (rétractées hors phase 2 par l'échelle de leur os)
    vine_specs = [(0, 0.35, 1.1), (0, 2.75, 1.2), (1, 1.05 + math.pi, 0.95), (1, -0.25 + math.pi, 0.9)]
    for i, (k, ph, ln) in enumerate(vine_specs):
        top = tier_point(k, find_s(k, 1.0, upper=False) + 0.02, ph, -0.05)
        b = f"Liane_{i + 1}"
        m.bones[b]["head"] = top.copy()
        pts = [top + V((0.05 * math.sin(j * 1.3), 0.05 * math.cos(j * 1.1), -ln * j / 12)) for j in range(13)]
        E.vine(m, mats, pts, b, r=0.03, leaf_size=0.13, every=3)
        E.flower(m, mats, pts[-1] + V((0, 0.06, 0)), V((0, 1, 0)), 0.09, b)

    # Projectiles intégrés
    m.add(pine_cone("proj_pomme", V((0.85, 0.9, 1.6)), 0.32, axis=V((0, 1, -0.3))), mats["cone"], "Proj_Pomme")
    m.add(L.lumpy("proj_pomme_neige", V((0.85, 0.82, 1.82)), (0.12, 0.12, 0.05), amp=0.2, seed=2, nu=10, nv=6),
          mats["snow"], "Proj_Pomme")
    rp = L.bezier_pts(V((0, 3.4, -0.1)), V((0, 3.4, 0.5)), V((0.12, 3.25, 0.9)), V((0.05, 3.15, 1.4)), 10)
    m.add(L.tube("proj_racine", rp, [0.3 - 0.25 * (j / 10) for j in range(11)], 14, cap_rings=3), mats["bark"], "Proj_Racine")
    for j in range(6):
        a = TAU * j / 6
        m.add(L.lumpy("proj_racine_neige", V((math.cos(a) * 0.42, 3.4 + math.sin(a) * 0.42, 0.05)),
                      (0.16, 0.16, 0.08), amp=0.3, seed=j + 30, nu=10, nv=6), mats["snow"], "Proj_Racine")
    E.leaf(m, mats, rp[-2], V((0.5, -0.3, 1)), V((1, 0, 0)), 0.22, "Proj_Racine")
    m.add(L.lumpy("proj_neige", V((0, 0.95, 2.4)), (0.36, 0.3, 0.26), amp=0.16, seed=7, nu=18, nv=10), mats["snow"],
          "Proj_Neige")
    return names


# --------------------------------------------------------------------------------------------
# Animations
# --------------------------------------------------------------------------------------------
HIDDEN = ("Proj_Pomme", "Proj_Racine", "Proj_Neige")
TIER_B = ["Etage_1", "Etage_2", "Etage_3", "Etage_4"]


def base_pose(t, phase2=False, vines=None):
    p = Pose()
    for b in HIDDEN:
        p.set(b, scl=0.0001)
    v = 1.0 if phase2 else 0.42
    if vines is not None:
        v = vines
    for i in range(4):
        p.set(f"Liane_{i + 1}", scl=(1, 1, v), rot=(3 * osc(t, 60, i), 3 * osc(t, 60, i + 1), 0))
    if phase2:
        p.set("Bras_G", rot=(0, 95, 0))
        p.set("Bras_D", rot=(0, -95, 0))
    return p


def blink(p, t, at):
    p.set("Visage", scl=(1, 1, 1 - 0.85 * math.exp(-((t - at) / 1.6) ** 2)))


def a_idle(t, phase2=False):
    p = base_pose(t, phase2)
    P = 60.0
    p.set("Tronc", scl=(1 + 0.015 * osc(t, P, 0, 2), 1 + 0.015 * osc(t, P, 0, 2), 1 - 0.02 * osc(t, P, 0, 2)))
    for k, b in enumerate(TIER_B):
        a = 1.2 + 0.7 * k
        p.set(b, loc=(0, 0, 0.025 * (k + 1) * (0.5 - 0.5 * math.cos(TAU * t / P - 0.4 * k))),
              rot=(a * osc(t, P, 0.5 * k), a * 0.8 * osc(t, P, 1.3 + 0.5 * k), 0),
              scl=(1 + 0.02 * osc(t, P, k, 2), 1 + 0.02 * osc(t, P, k, 2), 1 - 0.02 * osc(t, P, k, 2)))
    p.set("Etoile", rot=(0, 8 * osc(t, P, 0.2), 4 * osc(t, P, 0.0)))
    for i in range(6):
        p.set(f"Racine_{i + 1}", scl=(1, 1, 1 + 0.06 * osc(t, P, i, 2)))
    if phase2:
        p.set("Bras_G", rot=(6 * osc(t, P, 0.2, 2), 95 + 10 * osc(t, P, 0.0), 0))
        p.set("Bras_D", rot=(6 * osc(t, P, 1.2, 2), -95 - 10 * osc(t, P, 0.7), 0))
        for i in range(4):
            p.set(f"Liane_{i + 1}", scl=1, rot=(9 * osc(t, P, i), 9 * osc(t, P, i + 1), 0))
    blink(p, t, 40)
    p.shapes(resp=0.4 * osc(t, P, 0, 2))
    return p


def a_move(t):
    p = base_pose(t)
    P = 40.0
    hop = abs(math.sin(TAU * t / P))
    p.set("Root", loc=(0, 0, 0.12 * hop))
    p.set("Tronc", rot=(-5, 0, 3 * osc(t, P, 0)), scl=(1 + 0.05 * (1 - hop), 1 + 0.05 * (1 - hop), 1 - 0.07 * (1 - hop)))
    for k, b in enumerate(TIER_B):
        p.set(b, rot=(-1.5 - 2.5 * osc(t, P, 1.2 + 0.5 * k, 2), 3 * osc(t, P, 0.4 * k), 0),
              loc=(0, -0.02 * (k + 1), 0))
    for i in range(6):
        a = TAU * i / 6 + math.pi / 6
        p.set(f"Racine_{i + 1}", rot=(12 * osc(t, P, i * 1.0) * math.sin(a), -12 * osc(t, P, i * 1.0) * math.cos(a), 0),
              loc=(0, 0, -0.1 * hop))
    p.set("Etoile", rot=(0, 10 * osc(t, P, 0.6), 0))
    p.shapes(resp=0.2, impact=0.1 + 0.08 * (1 - hop))
    return p


def a_fly(t):
    """VOL : le sapin gonflable décolle, racines et lianes pendantes, plane en se balançant."""
    p = base_pose(t, vines=0.75)
    P = 60.0
    p.set("Root", loc=(0.1 * osc(t, P, 0), 0, 1.1 + 0.15 * osc(t, P, 0.5, 2)))
    p.set("Tronc", rot=(-7 + 2 * osc(t, P, 1.0, 2), 8 * osc(t, P, 0), 4 * osc(t, P, math.pi / 2)))
    for k, b in enumerate(TIER_B):
        p.set(b, rot=(3 + 2.5 * osc(t, P, 1.2 + 0.5 * k, 2), -3 * osc(t, P, 0.4 * k + 0.5), 0))
    for i in range(6):
        a = TAU * i / 6 + math.pi / 6
        droop = 38 + 8 * osc(t, P, i * 0.9, 2)
        p.set(f"Racine_{i + 1}", rot=(-droop * math.sin(a), droop * math.cos(a), 0))
    for i in range(4):
        p.add(f"Liane_{i + 1}", rot=(18 + 6 * osc(t, P, i, 2), 8 * osc(t, P, i + 1), 0))
    p.set("Bras_G", rot=(0, 25 + 8 * osc(t, P, 0.3, 2), 0))
    p.set("Bras_D", rot=(0, -25 - 8 * osc(t, P, 0.3, 2), 0))
    p.set("Etoile", rot=(12, 10 * osc(t, P, 0.6), 0))
    p.shapes(resp=0.3 + 0.2 * osc(t, P, 0, 2))
    return p


def a_attack(t):
    """Coup de tronc : le sapin se cambre en arrière, fouette vers l'avant et percute."""
    p = base_pose(t)
    p.set("Root", loc=(0, track(t, [(0, 0), (12, -0.3), (18, 0.9, "in"), (23, 0.8), (31, 0.35), (44, 0, "ease")]),
                       track(t, [(0, 0), (12, 0), (18, 0.1), (22, 0), (27, 0.2), (33, 0), (44, 0)])))
    lean = track(t, [(0, 0), (12, 10), (17, -16), (21, -12), (27, 5), (35, -2), (44, 0)])
    p.set("Tronc", rot=(lean, 0, 0),
          scl=track3(t, [(0, (1, 1, 1)), (12, (1.08, 1.08, 0.88)), (17, (0.95, 0.95, 1.08)), (21, (1.1, 0.85, 0.93)),
                         (28, (1, 1, 1))]))
    for k, b in enumerate(TIER_B):
        lag = 2 * k
        p.set(b, rot=(track(t, [(0, 0), (12 + lag * 0.3, 4 + 2 * k), (18 + lag * 0.3, -6 - 4 * k), (22, 3 + k),
                                (30, -1), (44, 0)]), decay(t, 20, 18, 2.5, 3 + k), 0),
              scl=track3(t, [(0, (1, 1, 1)), (19, (1, 1, 1)), (21, (1.08, 0.82, 1.04)), (26, (0.98, 1.05, 1)),
                             (32, (1, 1, 1))]))
    p.set("Bouche", scl=track3(t, [(0, (1, 1, 1)), (12, (0.9, 1, 0.8)), (18, (1.2, 1, 1.5)), (24, (1.15, 1, 1.3)),
                                   (32, (1, 1, 1))]))
    p.set("Visage", scl=(1, 1, track(t, [(0, 1), (12, 0.6), (18, 1.15), (21, 0.6), (28, 1), (44, 1)])))
    p.set("Etoile", rot=(track(t, [(0, 0), (12, 15), (18, -25), (23, 15), (30, -5), (44, 0)]), 0, 0))
    for i in range(4):
        p.add(f"Liane_{i + 1}", rot=(track(t, [(0, 0), (12, -20), (18, 30), (24, -15), (34, 0)]), 0, 0))
    p.shapes(resp=track(t, [(0, 0), (12, 0.5), (18, -0.2), (24, 0), (44, 0)]),
             impact=track(t, [(0, 0), (18, 0), (21, 1.0), (27, 0.1), (34, 0), (44, 0)]))
    return p


def a_hit(t):
    p = base_pose(t)
    p.set("Root", loc=(0, track(t, [(0, 0), (3, -0.25, "out"), (11, -0.15), (20, 0, "ease")]), 0))
    p.set("Tronc", rot=(track(t, [(0, 0), (3, 7), (8, -3), (13, 1.5), (20, 0)]), decay(t, 2, 16, 3, 3), 0),
          scl=track3(t, [(0, (1, 1, 1)), (2, (1.1, 0.85, 0.9)), (6, (0.96, 1.05, 1.06)), (11, (1, 1, 1))]))
    for k, b in enumerate(TIER_B):
        p.set(b, rot=(decay(t, 2 + k * 0.7, 16, 3, 5 + 2 * k), decay(t, 3 + k * 0.7, 16, 2.5, 4 + k), 0),
              scl=(1 + decay(t, 2, 14, 4, 0.05), 1 - decay(t, 2, 14, 4, 0.05), 1))
    p.set("Visage", scl=(1.05, 1, track(t, [(0, 1), (2, 0.3), (10, 0.4), (15, 1), (20, 1)])))
    p.set("Etoile", rot=(decay(t, 3, 17, 3, 20), decay(t, 4, 17, 2.5, 15), 0))
    p.shapes(resp=track(t, [(0, 0), (2, -0.5), (8, 0.2), (14, 0)]), impact=track(t, [(0, 0), (2, 0.8), (9, 0), (20, 0)]))
    return p


def a_death(t):
    """Dégonflage du haut vers le bas : la pointe s'affaisse, les étages s'écrasent, tout se ratatine."""
    p = base_pose(t)
    on = 1.0 if t > 8 else 0.0
    fade = 1 - ease((t - 50) / 20)
    p.set("Root", loc=(0, track(t, [(0, 0), (3, -0.25, "out"), (10, -0.15), (80, -0.1)]), 0))
    p.set("Tronc", rot=(track(t, [(0, 0), (3, 8), (10, 0), (60, -6), (80, -8)]) + 4 * math.sin(TAU * t / 9) * on * fade,
                        3 * math.sin(TAU * t / 7) * on * fade, 0),
          scl=track3(t, [(0, (1, 1, 1)), (10, (1, 1, 1)), (60, (1.12, 1.12, 0.55), "ease"), (72, (1.1, 1.1, 0.4)),
                         (80, (0.001, 0.001, 0.001), "in")]))
    for k, b in enumerate(TIER_B):
        start = 10 + (3 - k) * 7
        sag = ease((t - start) / 30)
        p.set(b, loc=(0, 0, -0.18 * (k + 1) * sag),
              rot=(-12 * sag * (k + 1) / 4 + 6 * math.sin(TAU * t / 8 + k) * on * fade,
                   5 * math.sin(TAU * t / 6 + k) * on * fade, 20 * sag * (1 if k % 2 else -1)),
              scl=(1 + 0.1 * sag, 1 + 0.1 * sag, 1 - 0.45 * sag))
    for i in range(6):
        p.set(f"Racine_{i + 1}", scl=track3(t, [(0, (1, 1, 1)), (40, (1, 1, 1)), (70, (0.75, 0.75, 0.5)),
                                                (80, (0.001, 0.001, 0.001), "in")]))
    p.set("Visage", scl=(1, 1, track(t, [(0, 1), (3, 0.3), (12, 0.9), (40, 0.5), (60, 0.15), (80, 0.15)])))
    p.set("Etoile", rot=(track(t, [(0, 0), (20, 0), (50, 70, "ease"), (80, 80)]), 0, track(t, [(0, 0), (60, 140)])),
          scl=track(t, [(0, 1), (30, 1), (60, 0.5), (80, 0.001, "in")]))
    p.shapes(resp=track(t, [(0, 0), (3, -0.4), (10, 0), (40, -0.6), (65, -1)]),
             impact=track(t, [(0, 0), (3, 0.7), (10, 0)]),
             deflate=track(t, [(0, 0), (10, 0), (40, 0.35, "ease"), (66, 1.0, "ease"), (80, 1.0)]))
    return p


def a_pommes(t):
    """Lance une pomme de pin gonflable : elle gonfle sur une branche, le sapin la catapulte."""
    p = base_pose(t)
    lean = track(t, [(0, 0), (14, 9), (19, -12), (24, 4), (32, -1), (45, 0)])
    p.set("Tronc", rot=(lean, 0, track(t, [(0, 0), (14, -6), (19, 8), (26, 0)])))
    for k, b in enumerate(TIER_B):
        p.set(b, rot=(track(t, [(0, 0), (14, 3 + k), (19, -5 - 2 * k), (25, 2), (34, 0)]), decay(t, 19, 18, 2.5, 4), 0))
    grow = track(t, [(0, 0.0001), (5, 0.0001), (14, 1.25, "out"), (19, 1.0)])
    fly = ease_lin = max(0.0, min(1.0, (t - 19) / 17))
    y = 0.9 + fly * 6.0
    z = 1.6 + fly * 1.8 - (fly ** 2) * 3.4 + track(t, [(0, 0), (14, 0.15), (19, 0)])
    land = track(t, [(0, 1), (36, 1), (39, 0.0001, "in")])
    sq = track3(t, [(0, (1, 1, 1)), (35, (1, 1, 1)), (37, (1.4, 1.4, 0.5)), (39, (1, 1, 1))])
    p.set("Proj_Pomme", loc=(-0.85 * fly * 0.6, y - 0.9, z - 1.6),
          rot=(fly * 720, 0, fly * 180),
          scl=(max(grow * land * sq[0], 1e-4), max(grow * land * sq[1], 1e-4), max(grow * land * sq[2], 1e-4)))
    p.set("Bouche", scl=track3(t, [(0, (1, 1, 1)), (14, (0.9, 1, 0.8)), (19, (1.2, 1, 1.4)), (28, (1, 1, 1))]))
    p.set("Visage", scl=(1, 1, track(t, [(0, 1), (14, 0.6), (19, 1.15), (28, 1)])))
    p.shapes(resp=track(t, [(0, 0), (14, 0.6), (19, -0.3), (28, 0)]))
    return p


def a_racines(t):
    """Les racines plongent sous la neige et une racine géante surgit sous le joueur (≈3,4 m devant)."""
    p = base_pose(t)
    crouch = track(t, [(0, 0), (10, 1), (16, 1.1), (22, 0.6), (44, 0.3), (55, 0)])
    p.set("Tronc", scl=(1 + 0.08 * crouch, 1 + 0.08 * crouch, 1 - 0.1 * crouch),
          rot=(3 * math.sin(TAU * t / 5) * (8 < t < 22), 0, 0))
    for k, b in enumerate(TIER_B):
        p.set(b, rot=(2 * math.sin(TAU * t / 4 + k) * (8 < t < 22), 2 * math.sin(TAU * t / 5 + k) * (8 < t < 22), 0))
    dive = track(t, [(0, 0), (6, 0), (16, 1, "ease"), (40, 1), (52, 0, "ease")])
    for i in range(6):
        a = TAU * i / 6 + math.pi / 6
        p.set(f"Racine_{i + 1}", loc=(0, 0, -0.25 * dive),
              rot=(-25 * dive * math.sin(a), 25 * dive * math.cos(a), 0), scl=(1, 1, 1 - 0.3 * dive))
    up = track(t, [(0, -1.6), (18, -1.6), (23, 0.15, "out"), (26, -0.05), (29, 0.0), (38, 0.0), (45, -1.6, "in")])
    s = track(t, [(0, 0.0001), (18, 0.0001), (20, 0.8), (24, 1.1), (27, 1.0), (40, 1.0), (45, 0.0001)])
    p.set("Proj_Racine", loc=(0, 0, up), scl=max(s, 1e-4),
          rot=(decay(t, 23, 15, 3, 10), decay(t, 24, 15, 2.5, 8), 0))
    p.set("Visage", scl=(1, 1, track(t, [(0, 1), (10, 0.5), (22, 0.4), (30, 1), (55, 1)])))
    p.set("Bouche", scl=track3(t, [(0, (1, 1, 1)), (10, (1.1, 1, 0.6)), (22, (1.15, 1, 1.3)), (34, (1, 1, 1))]))
    p.shapes(resp=track(t, [(0, 0), (10, -0.3), (22, 0.5), (34, 0)]))
    return p


def a_neige(t):
    """Le sapin secoue ses branches : un bloc de neige tombe devant lui."""
    p = base_pose(t)
    shake = (6 < t < 22) * 1.0
    for k, b in enumerate(TIER_B):
        p.set(b, rot=(3 * math.sin(TAU * t / 4 + k) * shake, 0, 9 * math.sin(TAU * t / 5 + 0.8 * k) * shake),
              scl=(1 + 0.04 * math.sin(TAU * t / 3) * shake,) * 3)
    p.set("Tronc", rot=(track(t, [(0, 0), (20, 0), (24, -8), (30, 3), (40, 0)]), 0, 0))
    grow = track(t, [(0, 0.0001), (4, 0.0001), (10, 1.0, "out")])
    fall = ease_in_x = max(0.0, min(1.0, (t - 20) / 9)) ** 2
    land = track3(t, [(0, (1, 1, 1)), (29, (1, 1, 1)), (31, (1.5, 1.5, 0.45)), (34, (1.3, 1.3, 0.6)), (40, (0.0001,) * 3, "in")])
    p.set("Proj_Neige", loc=(0, 1.6 * min(1.0, max(0.0, (t - 20) / 9)), -2.1 * fall + 0.03 * math.sin(TAU * t / 3) * shake),
          rot=(fall * 160, fall * 40, 0),
          scl=(max(grow * land[0], 1e-4), max(grow * land[1], 1e-4), max(grow * land[2], 1e-4)))
    p.set("Visage", scl=(1, 1, track(t, [(0, 1), (8, 0.4), (22, 0.5), (26, 1.1), (34, 1)])))
    p.shapes(resp=0.3 * math.sin(TAU * t / 4) * shake)
    return p


def a_phase2(t):
    """Phase 2 : il se ramasse, puis déploie d'un coup ses bras-branches et ses lianes."""
    k = track(t, [(0, 0), (16, 0), (26, 1.12, "out"), (32, 0.96), (38, 1.0)])
    p = base_pose(t, vines=max(0.42 + 0.58 * min(1.0, max(0.0, (t - 18) / 16)), 0.42))
    p.set("Bras_G", rot=(track(t, [(0, 0), (26, -15), (34, 5), (40, 0)]), 95 * k, 0))
    p.set("Bras_D", rot=(track(t, [(0, 0), (26, -15), (34, 5), (40, 0)]), -95 * k, 0))
    crouch = track(t, [(0, 0), (14, 1), (20, -0.6), (28, 0.2), (36, 0)])
    p.set("Tronc", scl=(1 + 0.08 * crouch, 1 + 0.08 * crouch, 1 - 0.12 * crouch))
    for i, b in enumerate(TIER_B):
        p.set(b, scl=track(t, [(0, 1), (14, 0.96), (22, 1.1), (30, 1.04), (40, 1.05), (60, 1.05)]),
              rot=(decay(t, 20, 20, 3, 4 + i), decay(t, 21, 20, 2.5, 3 + i), 0))
    p.set("Etoile", rot=(0, track(t, [(0, 0), (18, 0), (40, 720, "ease"), (60, 720)]), 0),
          scl=track(t, [(0, 1), (22, 1.4), (34, 1.15), (60, 1.15)]))
    p.set("Bouche", scl=track3(t, [(0, (1, 1, 1)), (14, (0.9, 1, 0.7)), (22, (1.3, 1, 1.6)), (34, (1.2, 1, 1.4)),
                                   (46, (1, 1, 1))]))
    p.set("Visage", scl=(1.05, 1, track(t, [(0, 1), (14, 0.4), (22, 1.2), (40, 1.05), (60, 1.0)])))
    p.shapes(resp=track(t, [(0, 0), (14, -0.4), (22, 1.0), (34, 0.5), (60, 0.5)]))
    return p


ACTIONS = {
    "IDLE": (61, True, lambda t: a_idle(t)),
    "MOVE": (41, True, a_move),
    "FLY": (61, True, a_fly),
    "ATTACK": (45, False, a_attack),
    "HIT": (21, False, a_hit),
    "DEATH": (81, False, a_death),
    "ATTACK_PommesDePin": (46, False, a_pommes),
    "ATTACK_Racines": (56, False, a_racines),
    "ATTACK_ChuteNeige": (46, False, a_neige),
    "PHASE2_Deploiement": (61, False, a_phase2),
    "IDLE_Phase2": (61, True, lambda t: a_idle(t, True)),
}


def build(elem="eau"):
    m = L.Model("MiniBoss_Pin_Gonflable_Eau", "Le Pin Gonflable")
    mats = materials(elem)
    build_geometry(m, mats)
    water_decor(m, mats)
    m.build(shape_amp=0.5, wrinkle=0.025)
    import anims
    return m, anims.with_eyes(ACTIONS, m.meta.get("eye_r", 0.25))
