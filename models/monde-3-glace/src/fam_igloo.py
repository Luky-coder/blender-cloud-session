"""Famille A — Ballon Igloo (PV 60).

Petit igloo gonflable : dôme fait de rangées de blocs-coussins séparés par des coutures creuses,
boudin gonflable à la base, tunnel d'entrée sombre qui sert de bouche (stalactites en guise de
dents), deux yeux au-dessus, valve de gonflage à l'arrière, calotte de neige et petit fanion
d'expédition polaire. Charge frontale en attaque.
"""
import math

from mathutils import Vector

import anims as A
import elements as E
import w3lib as L

V = Vector
FAMILY = ("Ballon_Igloo", "Ballon Igloo", 60)

RH, HD, ZB = 0.58, 0.56, 0.13            # rayon du dôme, hauteur du dôme, base du dôme
ROWS = [0.0, 0.36, 0.72, 1.07, math.pi / 2]
BLOCKS = [11, 9, 7]
PUFF = 0.045
LIFT = 0.55                         # hauteur de vol (longueur de la ficelle)


def dome_point(th, ph, puff=0.0):
    p = V((RH * math.cos(th) * math.cos(ph), RH * math.cos(th) * math.sin(ph), ZB + HD * math.sin(th)))
    n = V((math.cos(th) * math.cos(ph) / RH, math.cos(th) * math.sin(ph) / RH, math.sin(th) / HD)).normalized()
    return p + n * puff, n


def _pillow(th, ph):
    for k in range(4):
        if ROWS[k] <= th <= ROWS[k + 1] + 1e-9:
            v = (th - ROWS[k]) / (ROWS[k + 1] - ROWS[k])
            if k == 3:
                return math.sin(math.pi / 2 * min(1.0, v * 1.6)) ** 0.35
            u = (ph / L.TAU * BLOCKS[k] + 0.5 * (k % 2)) % 1.0
            return (math.sin(math.pi * u) * math.sin(math.pi * v)) ** 0.35
    return 0.0


def build_geometry(m, mats):
    """Géométrie de référence de la famille (identique pour les 7 types)."""
    m.bone("Root", (0, 0, 0))
    m.bone("Body", (0, 0, 0.38), "Root", soft=(None, 0.45))
    m.bone("Haut", (0, 0, 0.74), "Body", soft=(0.3, 1.0))
    m.bone("Avant", (0, 0.62, 0.24), "Body", soft=(0.3, 1.0))
    m.bone("Arriere", (0, -0.56, 0.3), "Body", soft=(0.3, 0.8))
    m.bone("Visage", (0, 0.5, 0.56), "Avant")
    m.bone("Bouche", (0, 0.8, 0.2), "Avant")
    m.bone("Deco", (0, 0, 0.72), "Haut")
    m.bone("Drapeau", (0, -0.3, 0.68), "Haut")
    m.bone("CTRL_Formes", (0, 0, -0.2), deform=False)

    # Dôme : rangées de blocs-coussins (coutures = creux entre blocs)
    def fn(u, v):
        k = min(int(v * 4), 3)
        th = ROWS[k] + (v * 4 - k) * (ROWS[k + 1] - ROWS[k])
        ph = L.TAU * u
        p, _ = dome_point(th, ph, PUFF * _pillow(th, ph))
        return p

    dome = L.surface("dome", fn, 120, 32, pole1=True)
    m.add(dome, mats["main"], None)

    # Boudin gonflable de base, segmenté, et sa couture
    m.add(L.torus("boudin", (0, 0, 0.115), RH + 0.01, 0.105, 88, 14, lobes=22, lobe_amp=0.1), mats["second"], None)
    m.add(L.torus("couture", (0, 0, 0.2), RH - 0.02, 0.012, 64, 6), mats["accent"], None)

    # Tunnel d'entrée (arche de blocs) = bouche
    ra, ha, y0, y1 = 0.31, 0.43, 0.3, 0.71

    def tun(u, v):
        a = math.pi * u
        y = y0 + (y1 - y0) * v
        pu = (math.sin(math.pi * ((u * 5) % 1)) * math.sin(math.pi * ((v * 2) % 1))) ** 0.35
        r = 1 + 0.12 * pu
        return V((ra * r * math.cos(a), y, 0.0 + ha * r * math.sin(a)))

    tunnel = L.surface("tunnel", tun, 40, 12, closed=False)
    m.add(tunnel, mats["main"], None)
    arch = [V((ra * 1.04 * math.cos(math.pi * i / 16), y1 + 0.01, ha * 1.04 * math.sin(math.pi * i / 16)))
            for i in range(17)]
    m.add(L.tube("arche", arch, 0.07, 12, cap_rings=3), mats["second"], "Bouche")
    hole = [(ra * 0.86 * math.cos(math.pi * i / 20), ha * 0.86 * math.sin(math.pi * i / 20)) for i in range(21)]
    plate = L.puffy("entree", hole, 0.06, 0.02, segs=2)
    L.xform(plate, L.Matrix.Translation((0, y1 - 0.01, 0.01)))
    m.add(plate, mats["mouth"], "Bouche")
    for x, ln in ((-0.13, 0.12), (0.0, 0.16), (0.13, 0.11)):     # dents-stalactites
        m.add(L.icicle("dent", (x, y1 + 0.035, ha * 0.86 * math.sqrt(max(0, 1 - (x / (ra * 0.86)) ** 2)) + 0.01),
                       ln, 0.038), mats["ice"], "Bouche")
    m.add(L.ellipsoid("langue", (0, y1 + 0.02, 0.06), (0.12, 0.05, 0.05), 12, 8), mats["tongue"], "Bouche")

    # Visage : yeux et sourcils sur le dôme au-dessus de l'entrée
    for sx in (-1, 1):
        ph = math.pi / 2 - sx * 0.36
        p, n = dome_point(0.9, ph, PUFF * 0.6)
        E.eye(m, mats, p, n, 0.125, "Visage", side=("G" if sx < 0 else "D"), look=V((0, 0, -0.2)))
        pb, nb = dome_point(1.16, math.pi / 2 - sx * 0.36, PUFF * 1.2)
        E.brow(m, mats, pb, nb, 0.19, 0.03, 20 * sx, "Visage", side=("G" if sx < 0 else "D"))

    # Valve de gonflage (arrière droit)
    pv, nv = dome_point(0.62, -math.pi / 2 + 0.55, PUFF)
    M = L.orient(pv, nv)
    for ob in (L.tube("valve", [V((0, -0.01, 0)), V((0, 0.05, 0))], 0.045, 14, cap_rings=2),
               L.torus("valve_bague", (0, 0.03, 0), 0.05, 0.014, 18, 6, M=L.Matrix.Rotation(math.pi / 2, 4, "X")),
               L.ellipsoid("valve_bouchon", (0, 0.075, 0), (0.03, 0.02, 0.03), 10, 6)):
        L.xform(ob, M)
        m.add(ob, mats["valve"], None)

    # Neige : calotte + coulures
    m.add(L.lumpy("neige_calotte", (0, -0.06, ZB + HD + 0.0), (0.22, 0.24, 0.075), amp=0.18, seed=2, nu=26, nv=12,
                  flat_bottom=ZB + HD - 0.03), mats["snow"], None)
    for k, ph in enumerate((0.9, 2.6, 4.3)):
        p, n = dome_point(1.15, ph, PUFF)
        m.add(L.lumpy("neige_coulure", p, (0.09, 0.09, 0.06), amp=0.2, seed=k + 5, nu=12, nv=8), mats["snow"], None)
    for k, ph in enumerate((0.3, 1.25, 1.9, 2.8, 3.6, 5.1, 5.9)):     # neige sur le boudin
        p = V((math.cos(ph) * (RH + 0.02), math.sin(ph) * (RH + 0.02), 0.2))
        if abs(ph - math.pi / 2) < 0.5:
            continue
        m.add(L.lumpy("neige_boudin", p, (0.08, 0.08, 0.04), amp=0.25, seed=k + 11, nu=10, nv=6), mats["snow"], None)

    # Fanion d'expédition polaire (os Drapeau)
    pole_base, _ = dome_point(1.25, -math.pi / 2, 0.02)
    m.bones["Drapeau"]["head"] = pole_base.copy()       # le fanion pivote sur son pied
    m.lock(pole_base, 0.18, "Haut")
    m.lock(V((0, 0.72, 0.2)), 0.45, "Bouche")           # le tunnel-bouche suit l'arche
    top = pole_base + V((0, 0, 0.36))
    m.add(L.tube("mat", [pole_base, top], 0.012, 8, cap_rings=2), mats["valve"], "Drapeau")
    m.add(L.sphere("mat_boule", top + V((0, 0, 0.015)), 0.025, 10, 6), mats["gold"], "Drapeau")
    flag = L.puffy("fanion", [(0, 0), (0.2, -0.06), (0, -0.12)], 0.025, 0.009, segs=2)
    L.xform(flag, L.Matrix.Translation(top + V((0.0, 0, -0.01))))
    m.add(flag, mats["accent"], "Drapeau")
    E.snowflake_emblem(m, mats, top + V((0.075, 0.016, -0.06)), V((0, 1, 0)), 0.03, "Drapeau")

    # Ancres pour les décorations élémentaires
    # Fond gonflable (le ballon flotte : on voit le dessous)
    m.add(L.ellipsoid("fond", (0, 0, 0.07), (RH + 0.02, RH + 0.02, 0.07), 40, 10), mats["second"], None)
    m.add(L.torus("fond_couture", (0, 0, 0.035), RH * 0.55, 0.012, 48, 6), mats["accent"], None)

    anchors = dict(face=V((0, 1, 0)), crown=[], scatter=[], base=[])
    for ph in (math.pi / 2 - 1.15, math.pi / 2 + 1.15):
        p, n = dome_point(1.18, ph, PUFF)
        anchors["crown"].append((p - n * 0.02, (n + V((0, 0, 1.2))).normalized(), 0.2, "Deco"))
    anchors["crown"].append((V((0, -0.05, ZB + HD + 0.05)), V((0, -0.15, 1)).normalized(), 0.24, "Deco"))
    for th, ph in ((0.5, 0.25), (0.5, math.pi - 0.25), (0.55, -0.9), (0.55, math.pi + 0.9), (0.18, -2.1)):
        p, n = dome_point(th, ph, PUFF * 0.9)
        anchors["scatter"].append((p, n, 0.11, None))
    anchors["halo"] = (V((0, 0, ZB + HD + 0.2)), 0.27, "Deco")
    vine_pts = []
    for i in range(40):
        ph = 2.15 + (L.TAU - 0.95) * i / 39
        vine_pts.append(dome_point(0.42 + 0.13 * math.sin(4 * ph), ph, PUFF + 0.012)[0])
    anchors["vine"] = [(vine_pts, None)]
    anchors["base"] = [(V((0.48, -0.3, 0.06)), 0.3, "Body"), (V((-0.45, -0.38, 0.06)), 0.28, "Body")]
    return anchors


def build(elem):
    disp, key = E.ELEMENTS[elem]
    m = L.Model(f"Ballon_Igloo_{key}", f"Ballon Igloo {disp}")
    mats = E.materials(elem)
    anchors = build_geometry(m, mats)
    E.decorate(m, elem, mats, anchors)
    m.lift(LIFT)                                  # le ballon flotte au-dessus de sa ficelle
    E.add_hanging_string(m, mats, (0, 0.0, LIFT + 0.005), parent="Body")
    m.build()
    spec = dict(L=1.2, hover=0.06, body_h=0.38 + LIFT, bones=set(m.bones), eye_r=m.meta.get("eye_r", 0.1))

    def attack(spec, t):
        # charge frontale : gros recul, projection, impact du tunnel-bouche
        return A.attack_charge(spec, t, reach=0.85, back=0.25, tilt=1.0, hop=0.14)

    def extra(name, t, p):
        if name == "IDLE":
            p.set("Drapeau", rot=(0, 0, 8 * A.osc(t, 60, 0.0, 2)))
        elif name == "MOVE":
            p.set("Drapeau", rot=(-6, 0, 14 * A.osc(t, 40, 0.0, 2)))
        elif name == "FLY":
            p.set("Drapeau", rot=(-12, 0, 20 * A.osc(t, 60, 0.0, 2)))
        elif name == "ATTACK":
            p.set("Drapeau", rot=(A.track(t, [(0, 0), (9, -15), (14, 25), (19, -20), (26, 8), (36, 0)]), 0, 0))
        elif name in ("HIT", "DEATH"):
            p.set("Drapeau", rot=(A.decay(t, 2, 16, 2.5, 20), 0, A.decay(t, 2, 16, 3, 15)))

    return m, A.make_mob_actions(spec, attack, extra)
