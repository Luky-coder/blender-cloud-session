"""Famille C — Dirigeable Polaire (PV 75).

Petit dirigeable gonflable inspiré d'un brise-glace : enveloppe allongée à fuseaux cousus, nez
arrondi cerclé d'un anneau pare-glace et souligné d'une étrave (quille) rivetée, visage sur le nez,
nacelle-cabine à hublots suspendue par des câbles, deux hélices latérales sur nacelles, quatre
ailerons gonflables, chaîne de montagnes enneigées et bande de glacier sur les flancs, skis
d'atterrissage polaires. Attaque : charge horizontale, nez en avant.
"""
import math

from mathutils import Matrix, Vector

import anims as A
import elements as E
import w3lib as L

V = Vector
FAMILY = ("Dirigeable_Polaire", "Dirigeable Polaire", 75)

ZC, RM = 0.92, 0.44
Y0, Y1 = -1.05, 1.05


def prof(t):
    if t >= 0.55:
        x = (t - 0.55) / 0.45
        return RM * math.sqrt(max(0.0, 1 - x * x))
    x = (0.55 - t) / 0.55
    return RM * max(0.0, 1 - x * x) ** 0.72


def t_of(y):
    return (y - Y0) / (Y1 - Y0)


def env(t, ph, off=0.0, gore=True):
    r = prof(t)
    if gore:
        r *= 1 + 0.032 * abs(math.sin(4 * ph)) ** 0.4 * math.sin(math.pi * t) ** 0.5
    y = Y0 + (Y1 - Y0) * t
    dt = 0.002
    dr = (prof(min(t + dt, 1)) - prof(max(t - dt, 0))) / (2 * dt * (Y1 - Y0))
    n = V((math.cos(ph), -dr, math.sin(ph))).normalized()
    return V((r * math.cos(ph), y, ZC + r * math.sin(ph))) + n * off, n


def side_x(y, z, off=0.006):
    r = prof(t_of(y)) * 1.034 + off
    return math.sqrt(max(r * r - (z - ZC) ** 2, 0.0))


def build_geometry(m, mats):
    m.bone("Root", (0, 0, 0))
    m.bone("Body", (0, 0, ZC), "Root", soft=(None, 0.5))
    m.bone("Nez", (0, 0.8, ZC), "Body", soft=(0.42, 1.0))
    m.bone("Queue", (0, -0.75, ZC), "Body", soft=(0.42, 1.0))
    m.bone("Cabine", (0, 0.05, 0.48), "Body")
    m.bone("Helice_G", (-0.6, -0.27, 0.36), "Cabine")
    m.bone("Helice_D", (0.6, -0.27, 0.36), "Cabine")
    m.bone("Ailerons", (0, -0.78, ZC), "Queue")
    m.bone("Visage", (0, 0.88, ZC + 0.12), "Nez")
    m.bone("Deco", (0, 0.05, ZC + RM), "Body")
    m.bone("CTRL_Formes", (0, 0, -0.2), deform=False)

    # Enveloppe à 8 fuseaux
    m.add(L.surface("enveloppe", lambda u, v: env(v, L.TAU * u)[0], 48, 46, pole0=True, pole1=True),
          mats["main"], None)

    # Anneau pare-glace + rivets
    tr = 0.8
    c, _ = env(tr, 0, 0, gore=False)
    yr = c.y
    rr = prof(tr) * 1.035 + 0.012
    m.add(L.torus("pare_glace", (0, yr, ZC), rr, 0.048, 48, 10, M=Matrix.Rotation(math.pi / 2, 4, "X")),
          mats["accent"], None)
    for k in range(10):
        a = L.TAU * k / 10 + 0.3
        p = V((math.cos(a) * (rr + 0.04), yr + 0.012, ZC + math.sin(a) * (rr + 0.04)))
        m.add(L.sphere("rivet", p, 0.017, 8, 6), mats["valve"], None)
    m.add(L.torus("couture_nez", (0, yr - 0.09, ZC), prof(t_of(yr - 0.09)) * 1.03 + 0.004, 0.011, 48, 6,
                  M=Matrix.Rotation(math.pi / 2, 4, "X")), mats["accent"], None)

    # Étrave (quille de brise-glace) sous le nez, rivetée
    pts = [env(t, -math.pi / 2, 0.012, gore=False)[0] for t in (0.42, 0.55, 0.68, 0.8, 0.87, 0.91)]
    m.add(L.tube("etrave", pts, [0.025, 0.05, 0.06, 0.065, 0.055, 0.04], 12, cap_rings=3),
          mats["accent"], None)
    for t in (0.6, 0.7, 0.84):
        p, n = env(t, -math.pi / 2, 0.06, gore=False)
        m.add(L.sphere("rivet_etrave", p + V((0, 0, 0)), 0.02, 8, 6), mats["valve"], None)

    # Visage sur le nez
    for sx in (-1, 1):
        ph = math.pi / 2 - sx * 0.62
        p, n = env(0.905, ph, 0.0)
        E.eye(m, mats, p, n, 0.1, "Visage", look=V((-sx * 0.1, 0, -0.1)))
        pb, nb = env(0.86, math.pi / 2 - sx * 0.5, 0.02)
        E.brow(m, mats, pb + V((0, 0.04, 0.02)), nb + V((0, 0.6, 0)), 0.15, 0.025, 20 * sx, "Visage")
    pm, nm = env(0.962, -math.pi / 2 + 0.25, -0.01)
    E.grin(m, mats, V((0, pm.y, pm.z)), V((0, 1, -0.35)), 0.15, 0.1, "Visage")

    # Montagnes enneigées + glacier sur les deux flancs
    peaks = [(-0.58, 0.0), (-0.45, 0.17), (-0.33, 0.06), (-0.17, 0.27), (-0.02, 0.09), (0.12, 0.23),
             (0.26, 0.05), (0.4, 0.17), (0.54, 0.0)]
    zb = ZC - 0.17

    def ztop(y):
        for (y0, h0), (y1, h1) in zip(peaks, peaks[1:]):
            if y0 <= y <= y1:
                return zb + h0 + (h1 - h0) * (y - y0) / (y1 - y0)
        return zb

    for sx in (-1, 1):
        cols = 72
        ys = [peaks[0][0] + (peaks[-1][0] - peaks[0][0]) * i / cols for i in range(cols + 1)]
        rows = []
        for j in range(5):
            row = []
            for y in ys:
                z = zb + (ztop(y) - zb) * j / 4
                row.append(V((sx * side_x(y, z), y, z)))
            rows.append(row)
        ob = L.mesh_from_rows("montagnes", rows, closed=False, recalc=False)
        sol = ob.modifiers.new("ep", "SOLIDIFY")
        sol.thickness = 0.01
        L.apply_modifiers(ob)
        m.add(ob, mats["accent"], None)
        rows = []
        for j in range(3):
            row = []
            for y in ys:
                top = ztop(y)
                lo = max(zb, top - 0.055 - 0.02 * math.sin(55 * y) ** 2)
                if top - zb < 0.1:
                    lo = top
                z = lo + (top - lo) * j / 2
                row.append(V((sx * side_x(y, z, 0.013), y, z)))
            rows.append(row)
        ob = L.mesh_from_rows("neiges_eternelles", rows, closed=False, recalc=False)
        sol = ob.modifiers.new("ep", "SOLIDIFY")
        sol.thickness = 0.008
        L.apply_modifiers(ob)
        m.add(ob, mats["snow"], None)
        gl = [V((sx * side_x(y, zb - 0.035 + 0.014 * math.sin(16 * y), 0.012), y,
                 zb - 0.035 + 0.014 * math.sin(16 * y))) for y in [-0.62 + 1.25 * i / 30 for i in range(31)]]
        m.add(L.tube("glacier", gl, 0.016, 8, cap_rings=2), mats["ice"], None)

    # Nacelle-cabine (os Cabine) : pylônes, câbles, hublots
    cab_c, cab_s = V((0, 0.05, 0.27)), V((0.36, 0.62, 0.24))
    m.add(L.rounded_box("cabine", cab_c, cab_s, 0.08, 3), mats["second"], "Cabine")
    m.add(L.rounded_box("toit", cab_c + V((0, 0, 0.115)), V((0.3, 0.5, 0.04)), 0.018, 2), mats["accent"], "Cabine")
    for y in (-0.15, 0.22):
        m.add(L.tube("pylone", [V((0, y, 0.38)), V((0, y, ZC - RM + 0.05))], 0.03, 10, cap_rings=2),
              mats["valve"], "Cabine")
    for sx in (-1, 1):
        for sy in (-1, 1):
            a = V((sx * 0.16, 0.05 + sy * 0.27, 0.37))
            p, _ = env(t_of(0.05 + sy * 0.42), -math.pi / 2 + sx * 0.7, 0.0)
            m.add(L.tube("cable", [a, p], 0.008, 6, cap_rings=1), mats["dark"], "Cabine")
        for y in (-0.14, 0.05, 0.24):
            p = V((sx * 0.183, y, 0.285))
            Mx = L.orient(p, V((sx, 0, 0)))
            m.add(L.xform(L.ellipsoid("hublot", (0, 0, 0), (0.05, 0.018, 0.052), 14, 8), Mx), mats["window"], "Cabine")
            m.add(L.xform(L.torus("hublot_bague", (0, 0.004, 0), 0.056, 0.011, 16, 6,
                                  M=Matrix.Rotation(math.pi / 2, 4, "X")), Mx), mats["valve"], "Cabine")
    Mf = L.orient(V((0, 0.364, 0.29)), V((0, 1, 0.1)))
    m.add(L.xform(L.ellipsoid("pare_brise", (0, 0, 0), (0.13, 0.02, 0.06), 16, 8), Mf), mats["window"], "Cabine")

    # Skis d'atterrissage polaires
    for sx in (-1, 1):
        x = sx * 0.15
        m.add(L.rounded_box("ski", V((x, 0.0, 0.035)), V((0.075, 0.78, 0.028)), 0.012, 2), mats["accent"], "Cabine")
        tip = L.rounded_box("ski_spatule", V((0, 0, 0)), V((0.075, 0.16, 0.028)), 0.012, 2)
        L.xform(tip, Matrix.Translation((x, 0.44, 0.075)) @ Matrix.Rotation(math.radians(35), 4, "X"))
        m.add(tip, mats["accent"], "Cabine")
        for y in (-0.2, 0.2):
            m.add(L.tube("jambe_ski", [V((x, y, 0.045)), V((x * 0.8, y, 0.17))], 0.014, 6, cap_rings=1),
                  mats["valve"], "Cabine")

    # Hélices latérales sur nacelles
    for sx, hb in ((-1, "Helice_G"), (1, "Helice_D")):
        m.add(L.tube("bras", [V((sx * 0.17, -0.05, 0.3)), V((sx * 0.4, -0.05, 0.34)), V((sx * 0.55, -0.05, 0.36))],
                     0.028, 8, cap_rings=2), mats["valve"], "Cabine")
        m.add(L.tube("nacelle", [V((sx * 0.6, 0.14, 0.36)), V((sx * 0.6, -0.04, 0.36)), V((sx * 0.6, -0.2, 0.36))],
                     [0.06, 0.078, 0.068], 14, cap_rings=4), mats["main"], "Cabine")
        m.add(L.torus("nacelle_bague", (sx * 0.6, 0.06, 0.36), 0.072, 0.012, 20, 6,
                      M=Matrix.Rotation(math.pi / 2, 4, "X")), mats["accent"], "Cabine")
        hub = V((sx * 0.6, -0.27, 0.36))
        m.add(L.tube("moyeu", [hub + V((0, 0.03, 0)), hub + V((0, -0.05, 0))], [0.04, 0.012], 12, cap_rings=2),
              mats["gold"], hb)
        for k in range(3):
            a = L.TAU * k / 3 + 0.4
            bl = L.ellipsoid("pale", (0.12, 0, 0), (0.11, 0.013, 0.038), 14, 8)
            L.xform(bl, Matrix.Translation(hub) @ Matrix.Rotation(a, 4, "Y") @ Matrix.Rotation(math.radians(28 * sx), 4, "X"))
            m.add(bl, mats["second"], hb)

    # Ailerons gonflables (croix)
    fin = [(0.03, 0.0), (-0.44, -0.2), (-0.52, 0.17), (-0.38, 0.25), (-0.1, 0.075)]
    for ph in (math.pi / 2, -math.pi / 2, 0.0, math.pi):
        r_hat = V((math.cos(ph), 0, math.sin(ph)))
        yh = V((0, 1, 0))
        Mr = Matrix((yh, r_hat.cross(yh), r_hat)).transposed().to_4x4()
        anchor = V((0, -0.55, ZC)) + r_hat * (prof(t_of(-0.55)) - 0.035)
        f = L.puffy("aileron", fin, 0.065, 0.028, segs=3)
        L.xform(f, Matrix.Translation(anchor) @ Mr)
        m.add(f, mats["second"], "Ailerons")
        edge = [anchor + Mr.to_3x3() @ V((x, 0, z)) for x, z in ((-0.5, 0.2), (-0.42, 0.26), (-0.2, 0.15))]
        m.add(L.tube("liseré_aileron", edge, 0.018, 8, cap_rings=2), mats["accent"], "Ailerons")

    # Valve (dessus arrière) et neige
    pv, nv = env(0.32, math.pi / 2 + 0.5, 0.0)
    Mv = L.orient(pv, nv)
    for ob in (L.tube("valve", [V((0, -0.01, 0)), V((0, 0.06, 0))], 0.042, 12, cap_rings=2),
               L.torus("valve_bague", (0, 0.035, 0), 0.047, 0.013, 16, 6, M=Matrix.Rotation(math.pi / 2, 4, "X")),
               L.ellipsoid("valve_bouchon", (0, 0.08, 0), (0.03, 0.02, 0.03), 10, 6)):
        m.add(L.xform(ob, Mv), mats["valve"], None)
    for k, (t, ph) in enumerate(((0.45, math.pi / 2 - 0.25), (0.6, math.pi / 2 + 0.3), (0.72, math.pi / 2 - 0.1))):
        p, n = env(t, ph, -0.01)
        m.add(L.lumpy("neige", p, (0.12, 0.09, 0.045), amp=0.25, seed=k + 3, nu=14, nv=8), mats["snow"], None)

    anchors = dict(face=V((0, 1, 0)), crown=[], scatter=[], base=[])
    for t in (0.38, 0.53, 0.66):
        p, n = env(t, math.pi / 2, -0.02)
        anchors["crown"].append((p, V((0, 0.15, 1)).normalized(), 0.19, "Deco"))
    for t, ph in ((0.3, 0.75), (0.3, math.pi - 0.75), (0.62, -0.75), (0.62, math.pi + 0.75), (0.15, 0.6),
                  (0.15, math.pi - 0.6)):
        p, n = env(t, ph, 0.0)
        anchors["scatter"].append((p, n, 0.1, None))
    anchors["halo"] = (V((0, 0.05, ZC + RM + 0.3)), 0.3, "Deco")
    anchors["vine"] = [([env(0.12 + 0.62 * i / 40, 2.0 + L.TAU * 0.9 * i / 40, 0.015)[0] for i in range(41)], None)]
    anchors["base"] = [(V((0, -1.12, ZC + 0.02)), 0.24, "Ailerons")]
    return anchors


def build(elem):
    disp, key = E.ELEMENTS[elem]
    m = L.Model(f"Dirigeable_Polaire_{key}", f"Dirigeable Polaire {disp}")
    mats = E.materials(elem)
    anchors = build_geometry(m, mats)
    E.decorate(m, elem, mats, anchors)
    m.build(shape_amp=0.7)
    spec = dict(L=2.2, hover=0.08, body_h=ZC, bones=set(m.bones), lean=7)

    def attack(spec, t):
        """Charge horizontale : recul, hélices à fond, ruée nez en avant, impact, rebond."""
        Lm = spec["L"]
        p = A.Pose()
        p.set("Root", loc=(0, A.track(t, [(0, 0), (10, -0.2 * Lm, "ease"), (15, 0.75 * Lm, "in"), (19, 0.71 * Lm),
                                           (26, 0.4 * Lm), (36, 0, "ease")]),
                           A.track(t, [(0, 0), (10, 0.03 * Lm), (15, 0), (19, 0.01 * Lm), (24, 0.06 * Lm), (36, 0)])))
        p.set("Body", rot=(A.track(t, [(0, 0), (10, 7), (14, -7), (18, 3), (24, -2), (36, 0)]),
                           A.decay(t, 17, 14, 2.5, 6), A.decay(t, 17, 14, 2, 4)),
              scl=A.track3(t, [(0, (1, 1, 1)), (10, (1.06, 0.88, 1.06)), (14, (0.93, 1.17, 0.93)),
                               (18, (1.1, 0.84, 1.08)), (23, (0.97, 1.05, 0.98)), (36, (1, 1, 1))]))
        p.set("Nez", loc=(0, A.track(t, [(0, 0), (15, 0), (18, -0.07 * Lm), (23, 0.01 * Lm), (36, 0)]), 0),
              scl=A.track3(t, [(0, (1, 1, 1)), (15, (0.97, 1.05, 0.97)), (18, (1.16, 0.75, 1.14)), (24, (1, 1, 1))]))
        p.set("Queue", loc=(0, A.track(t, [(0, 0), (10, 0.03 * Lm), (14, -0.05 * Lm), (19, 0.06 * Lm), (26, -0.01 * Lm),
                                            (36, 0)]), 0),
              rot=(0, 0, A.decay(t, 18, 14, 2, 6)))
        p.set("Cabine", rot=(A.track(t, [(0, 0), (10, 12), (15, -16), (19, 18), (25, -8), (31, 3), (36, 0)]),
                             A.decay(t, 18, 15, 2, 6), 0))
        spin = A.track(t, [(0, 0, "lin"), (10, 400, "in"), (19, 1500, "lin"), (36, 2300, "out")])
        p.set("Helice_G", rot=(0, -spin, 0))
        p.set("Helice_D", rot=(0, spin, 0))
        p.set("Ailerons", rot=(A.decay(t, 17, 16, 3, 10), 0, 0))
        p.set("Visage", scl=(1, 1, A.track(t, [(0, 1), (9, 0.7), (14, 1.15), (18, 0.5), (25, 1), (36, 1)])))
        p.set("Deco", rot=(A.track(t, [(0, 0), (10, -8), (14, 12), (18, -14), (25, 4), (36, 0)]), 0, 0))
        p.shapes(resp=A.track(t, [(0, 0), (10, 0.5), (15, -0.2), (22, 0), (36, 0)]),
                 impact=A.track(t, [(0, 0), (15, 0), (18, 1.0), (23, 0.1), (29, 0)]))
        return p

    def extra(name, t, p):
        if name == "IDLE":
            spin = 360 * 4 * t / 60
            p.set("Cabine", rot=(2.5 * A.osc(t, 60, 1.6), 3 * A.osc(t, 60, 2.6), 0))
            p.set("Ailerons", rot=(3 * A.osc(t, 60, 0.4, 2), 0, 2 * A.osc(t, 60, 1.4)))
            p.set("Queue", rot=(0, 0, 1.5 * A.osc(t, 60, 0.8)))
        elif name == "MOVE":
            spin = 360 * 6 * t / 40
            p.set("Cabine", rot=(8 + 2 * A.osc(t, 40, 0.6, 2), 2 * A.osc(t, 40, 1.0), 0))
            p.set("Ailerons", rot=(4 * A.osc(t, 40, 0.4, 2), 0, 3 * A.osc(t, 40, 0.2)))
            p.set("Queue", rot=(0, 0, 2.5 * A.osc(t, 40, 0.0)))
        elif name == "HIT":
            spin = A.track(t, [(0, 0), (3, -60), (18, 200)])
            p.set("Cabine", rot=(A.track(t, [(0, 0), (3, -18), (8, 12), (13, -5), (18, 0)]), A.decay(t, 2, 16, 2.5, 10), 0))
            p.set("Ailerons", rot=(A.decay(t, 2, 16, 3, 12), 0, A.decay(t, 3, 16, 3, 8)))
        elif name == "DEATH":
            spin = A.track(t, [(0, 0, "lin"), (10, 300, "lin"), (40, 900, "out"), (60, 920)])
            p.set("Cabine", rot=(A.track(t, [(0, 0), (3, -15), (30, 10), (48, 30), (60, 30)]),
                                 12 * math.sin(L.TAU * t / 8) * (6 < t < 40), 0))
            p.set("Ailerons", rot=(A.track(t, [(0, 0), (48, -25)]), 0, 8 * math.sin(L.TAU * t / 6) * (6 < t < 44)))
        else:
            return
        p.set("Helice_G", rot=(0, -spin, 0))
        p.set("Helice_D", rot=(0, spin, 0))

    return m, A.make_mob_actions(spec, attack, extra)
