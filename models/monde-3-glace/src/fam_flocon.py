"""Famille B — Ballon Flocon (PV 50).

Ballon en forme de flocon à six branches, debout face au joueur (+Y). Trois couches gonflables :
étoile arrière à 6 pointes, branches-boudins avec sous-branches et bulbes de neige, disque central
bombé portant le visage. Colliers de couture à la base des branches, valve au dos, petites
stalactites sous les branches basses. Attaque : toupie rapide puis projection vers l'avant.
"""
import math

from mathutils import Quaternion, Vector

import anims as A
import elements as E
import w3lib as L

V = Vector
FAMILY = ("Ballon_Flocon", "Ballon Flocon", 50)

RT, BULB, RC = 0.64, 0.095, 0.3     # rayon des pointes, bulbe terminal, disque central
HC = RT + BULB + 0.005              # hauteur du centre (pointe basse posée au sol)
C = V((0, 0, HC))
LIFT = 0.5                          # hauteur de vol (longueur de la ficelle)
ANG = [math.radians(90 + 60 * k) for k in range(6)]   # haut, haut-gauche, bas-gauche, bas, bas-droite, haut-droite


def d2(a):
    return V((math.cos(a), 0, math.sin(a)))


def build_geometry(m, mats):
    m.bone("Root", (0, 0, 0))
    m.bone("Body", C, "Root", soft=(None, 1.0))
    for k, a in enumerate(ANG):
        m.bone(f"Branche_{k}", C + d2(a) * 0.2, "Body")
    m.bone("Visage", C + V((0, 0.16, 0.02)), "Body")
    m.bone("Deco", C + V((0, 0, RT * 0.7)), "Body")
    m.bone("CTRL_Formes", (0, 0, -0.2), deform=False)

    # Couche 1 : étoile arrière à 6 pointes
    star = L.puffy("etoile_dos", L.star_pts(6, 0.5, 0.28, rot=math.radians(30) - math.pi / 2 + math.pi / 2),
                   0.13, 0.055, segs=4)
    L.xform(star, L.Matrix.Translation(C + V((0, -0.085, 0))) @ L.Matrix.Rotation(math.radians(0), 4, "Y"))
    m.add(star, mats["second"], "Body")

    # Couche 2 : branches
    for k, a in enumerate(ANG):
        b = f"Branche_{k}"
        d = d2(a)
        side = V((-d.z, 0, d.x))
        pts = [C + d * t for t in (0.12, 0.3, 0.45, RT)]
        m.add(L.tube("branche", pts, [0.115, 0.1, 0.09, 0.072], 14, caps=(False, True), cap_rings=3),
              mats["main"], b)
        m.add(L.sphere("bulbe", C + d * (RT + 0.02), BULB, 16, 10), mats["snow"], b)
        for s in (-1, 1):
            base = C + d * 0.4
            tip = base + (d * math.cos(math.radians(52)) + side * s * math.sin(math.radians(52))) * 0.2
            m.add(L.tube("sous_branche", [base, (base + tip) / 2, tip], [0.06, 0.054, 0.048], 10, cap_rings=3),
                  mats["main"], b)
            m.add(L.sphere("sous_bulbe", tip + (tip - base).normalized() * 0.02, 0.058, 12, 8), mats["snow"], b)
        M = L.orient(V((0, 0, 0)), d)
        col = L.torus("collier", C + d * 0.31, 0.104, 0.022, 20, 6, M=M @ L.Matrix.Rotation(math.pi / 2, 4, "X"))
        m.add(col, mats["accent"], b)
        # couture longitudinale (piqûre) sur le dessus de la branche
        seam = [C + d * t + V((0, 0.1 - 0.015 * (t - 0.32) / 0.3, 0)) for t in (0.34, 0.45, 0.55, 0.62)]
        m.add(L.tube("piqure", seam, 0.01, 6, cap_rings=1), mats["accent"], b)
        if math.sin(a) < 0.3 and abs(math.cos(a)) > 0.3:      # stalactites sous les branches basses/latérales
            for t, ln in ((0.38, 0.09), (0.52, 0.06)):
                p = C + d * t + V((0, 0, -0.085))
                m.add(L.icicle("stalactite", p, ln, 0.022), mats["ice"], b)

    # Couche 3 : disque central bombé (hexagonal)
    def disp(u, v, p):
        ph = math.atan2(p.z, p.x)
        return 1 + 0.05 * math.cos(6 * (ph - math.pi / 2))

    disc = L.ellipsoid("centre", C, (RC, 0.17, RC), 36, 18, disp)
    m.add(disc, mats["main"], "Body")
    ring = L.torus("couture_centre", C + V((0, 0.035, 0)), RC * 0.98, 0.016, 48, 6,
                   M=L.Matrix.Rotation(math.pi / 2, 4, "X"))
    m.add(ring, mats["accent"], "Body")

    # Visage
    for sx in (-1, 1):
        E.eye(m, mats, C + V((sx * 0.105, 0.135, 0.06)), V((sx * 0.25, 1, 0.12)), 0.097, "Visage", side=("G" if sx < 0 else "D"),
              look=V((-sx * 0.15, 0, -0.1)))
        E.brow(m, mats, C + V((sx * 0.11, 0.135, 0.175)), V((sx * 0.2, 1, 0.4)), 0.13, 0.022, 22 * sx, "Visage", side=("G" if sx < 0 else "D"))
    E.grin(m, mats, C + V((0, 0.15, -0.1)), V((0, 1, -0.25)), 0.1, 0.07, "Visage")
    for sx in (-1, 1):   # joues
        m.add(L.ellipsoid("joue", C + V((sx * 0.2, 0.1, -0.06)), (0.045, 0.02, 0.03), 10, 6,
                          M=L.orient(V((0, 0, 0)), V((sx * 0.6, 1, 0)))), mats["tongue"], "Visage")

    # Valve au dos
    M = L.orient(C + V((0, -0.16, -0.05)), V((0, -1, 0)))
    for ob in (L.tube("valve", [V((0, 0, 0)), V((0, 0.06, 0))], 0.04, 12, cap_rings=2),
               L.torus("valve_bague", (0, 0.035, 0), 0.045, 0.012, 16, 6, M=L.Matrix.Rotation(math.pi / 2, 4, "X")),
               L.ellipsoid("valve_bouchon", (0, 0.08, 0), (0.028, 0.018, 0.028), 10, 6)):
        L.xform(ob, M)
        m.add(ob, mats["valve"], "Body")
    # neige sur le haut du disque
    m.add(L.lumpy("neige", C + V((0.0, 0.02, RC * 0.82)), (0.13, 0.12, 0.05), amp=0.2, seed=4, nu=14, nv=8),
          mats["snow"], "Body")

    anchors = dict(face=V((0, 1, 0)), crown=[], scatter=[], base=[])
    for k in (0, 1, 5):
        d = d2(ANG[k])
        anchors["crown"].append((C + d * (RT + BULB * 0.7), d, 0.17, f"Branche_{k}"))
    for k in range(6):
        a = ANG[k] + math.radians(30)
        anchors["scatter"].append((C + d2(a) * 0.4 + V((0, -0.01, 0)), V((0, 1, 0.0)), 0.09, "Body"))
    anchors["halo"] = (C + V((0, 0, RT + 0.3)), 0.22, "Deco")
    anchors["vine"] = []
    for k in (1, 5):
        d = d2(ANG[k])
        side = V((-d.z, 0, d.x))
        pts = [C + d * (0.2 + 0.42 * i / 24) + (side * math.cos(i * 0.75) + V((0, 1, 0)) * math.sin(i * 0.75)) * 0.11
               for i in range(25)]
        anchors["vine"].append((pts, f"Branche_{k}"))
    anchors["base"] = [(C + d2(ANG[2]) * 0.45 + V((0, -0.1, -0.05)), 0.22, f"Branche_2"),
                       (C + d2(ANG[4]) * 0.45 + V((0, -0.1, -0.05)), 0.22, f"Branche_4")]
    return anchors


def _bend(k, inplane, out):
    """Rotation d'une branche : `inplane` degrés dans le plan du flocon (autour de Y), `out` degrés
    hors plan (pointe vers +Y si positif)."""
    d = d2(ANG[k])
    axis = d.cross(V((0, 1, 0))).normalized()
    q = Quaternion(V((0, 1, 0)), math.radians(inplane)) @ Quaternion(axis, math.radians(-out))
    e = q.to_euler("XYZ")
    return tuple(math.degrees(x) for x in e)


def build(elem):
    disp, key = E.ELEMENTS[elem]
    m = L.Model(f"Ballon_Flocon_{key}", f"Ballon Flocon {disp}")
    mats = E.materials(elem)
    anchors = build_geometry(m, mats)
    E.decorate(m, elem, mats, anchors)
    m.lift(LIFT)                                  # le ballon flotte au-dessus de sa ficelle
    E.add_hanging_string(m, mats, (0, 0.0, LIFT - 0.005), parent="Branche_3")
    m.build(shape_amp=0.8)
    spec = dict(L=1.4, hover=0.1, body_h=HC + LIFT, bones=set(m.bones), eye_r=m.meta.get("eye_r", 0.1), lean=14)

    def attack(spec, t):
        """Toupie rapide (2 tours dans le plan) puis projection vers l'avant."""
        Lm = spec["L"]
        p = A.Pose()
        y = A.track(t, [(0, 0), (11, -0.18 * Lm, "ease"), (16, 0.85 * Lm, "in"), (19, 0.8 * Lm),
                        (26, 0.45 * Lm), (36, 0, "ease")])
        z = A.track(t, [(0, 0), (11, 0.08 * Lm), (16, 0.04 * Lm), (19, 0.02 * Lm), (24, 0.16 * Lm),
                        (30, 0.03 * Lm), (36, 0)])
        p.set("Root", loc=(0, y, z))
        spin = A.track(t, [(0, 0, "lin"), (2, -30, "in"), (11, -690, "lin"), (14, -720, "out"), (36, -720)])
        p.set("Body", rot=(A.track(t, [(0, 0), (11, 8), (15, -28), (19, -6), (25, 8), (36, 0)]),
                           spin + A.decay(t, 19, 12, 2, 8), 0),
              scl=A.track3(t, [(0, (1, 1, 1)), (11, (0.9, 0.9, 0.9)), (15, (0.95, 1.35, 0.95)),
                               (19, (1.16, 0.7, 1.12)), (24, (0.96, 1.1, 0.97)), (30, (1.02, 0.98, 1.01)),
                               (36, (1, 1, 1))]))
        flare = A.track(t, [(0, 0), (6, -12), (11, -18), (15, 20), (19, -25), (25, 8), (36, 0)])
        for k in range(6):
            p.set(f"Branche_{k}", rot=_bend(k, A.decay(t, 2, 12, 3, 6) * (1 if k % 2 else -1), flare),
                  scl=A.track(t, [(0, 1), (11, 1.08), (15, 1.0), (19, 0.92), (26, 1.0)]))
        p.set("Visage", scl=(1, 1, A.track(t, [(0, 1), (10, 0.65), (15, 1.15), (19, 0.55), (26, 1), (36, 1)])))
        p.set("Deco", rot=(A.track(t, [(0, 0), (15, 20), (19, -18), (26, 5), (36, 0)]), 0, 0))
        p.shapes(resp=A.track(t, [(0, 0), (11, 0.6), (16, -0.2), (22, 0), (36, 0)]),
                 impact=A.track(t, [(0, 0), (16, 0), (19, 1.0), (24, 0.1), (30, 0)]))
        return p

    def extra(name, t, p):
        for k in range(6):
            b = f"Branche_{k}"
            ph = k * 1.05
            if name == "IDLE":
                p.set(b, rot=_bend(k, 3 * A.osc(t, 60, ph), 6 * A.osc(t, 60, ph + 1.0, 2)),
                      scl=1 + 0.025 * A.osc(t, 60, ph, 2))
            elif name == "MOVE":
                p.set(b, rot=_bend(k, 4 * A.osc(t, 40, ph, 2), -14 + 6 * A.osc(t, 40, ph, 2)))
            elif name == "FLY":     # branches rabattues vers l'arrière, battement ample
                p.set(b, rot=_bend(k, 6 * A.osc(t, 60, ph, 2), -20 + 9 * A.osc(t, 60, ph, 2)))
            elif name == "HIT":
                p.set(b, rot=_bend(k, A.decay(t, 2, 15, 3.5, 12) * (1 if k % 2 else -1),
                                   A.track(t, [(0, 0), (2, -22), (6, 10), (11, -4), (18, 0)])))
            elif name == "DEATH":
                droop = A.track(t, [(0, 0), (8, 0), (30, -10), (48, -35, "ease"), (60, -40)])
                p.set(b, rot=_bend(k, 10 * math.sin(L.TAU * t / 6 + ph) * (6 < t < 44), droop),
                      scl=A.track(t, [(0, 1), (30, 0.95), (48, 0.8), (60, 0.8)]))
        if name == "IDLE":
            # léger balancement dans le plan (sans tourner le visage en entier)
            p.add("Body", rot=(0, 7 * A.osc(t, 60, 0.4), 0))

    return m, A.make_mob_actions(spec, attack, extra)
