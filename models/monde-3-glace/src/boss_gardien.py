"""Boss final — Le Grand Gardien des Glaciers (type Glace, PV 3000).

Gigantesque dirigeable végétal gonflable inspiré d'un ancien arbre gelé : enveloppe-tronc de près
de 10 m à écorce côtelée bleu glacier, houppiers givrés hérissés de cristaux cerclée de sangles dorées, visage ancien sur la proue,
cœur végétal lumineux dans une cage dorée sous le menton, trois grandes branches gonflables
portant des houppiers enneigés, racines pendantes, lianes, cristaux de glace turquoise, givre et
stalactites, quatre hélices latérales à pales-feuilles et une grande hélice de queue, ailerons-feuilles.
Projectiles intégrés : graine explosive, deux petits ballons végétaux invoqués, vague de trois
racines surgissantes, anneau de tempête de neige. Cachés (échelle 0) hors de leurs attaques.
"""
import math

from mathutils import Matrix, Vector

import elements as E
import w3lib as L
from w3lib import Pose, TAU, decay, ease, osc, track, track3

V = Vector
FAMILY = ("Boss", "Boss Grand Gardien des Glaciers", 3000)

ZC, RM = 3.7, 1.55
Y0, Y1 = -4.3, 4.3


def prof(t):
    if t >= 0.6:
        x = (t - 0.6) / 0.4
        return RM * math.sqrt(max(0.0, 1 - x * x))
    x = (0.6 - t) / 0.6
    r = RM * (1 - 0.72 * x * x)
    if x > 0.86:
        r *= math.sqrt(max(0.0, 1 - ((x - 0.86) / 0.14) ** 2))
    return r


def t_of(y):
    return (y - Y0) / (Y1 - Y0)


def env(t, ph, off=0.0, bark=True):
    r = prof(t)
    y = Y0 + (Y1 - Y0) * t
    if bark:
        r *= (1 + 0.045 * abs(math.sin(7 * ph)) ** 0.5 * math.sin(math.pi * t) ** 0.3
              + 0.035 * math.sin(2.3 * y + 1) * math.cos(3 * ph) * math.sin(math.pi * t))
    dt = 0.002
    dr = (prof(min(t + dt, 1)) - prof(max(t - dt, 0))) / (2 * dt * (Y1 - Y0))
    n = V((math.cos(ph), -dr, math.sin(ph))).normalized()
    return V((r * math.cos(ph), y, ZC + r * math.sin(ph))) + n * off, n


def materials(elem="glace"):
    """Palette Glace : écorce bleu glacier, feuillage givré blanc-bleu, cristaux cyan, cœur de glace lumineux."""
    mats = E.materials("glace")
    mats["main"] = L.mat("Ecorce_Gelee", "#6FB6D9", 0.2, fabric="#DDF3FF")
    mats["second"] = L.mat("Feuillage_Givre", "#DDF3FF", 0.22, fabric="#8CCBE6")
    mats["leaf_dark"] = L.mat("Feuillage_Glacier", "#8CCBE6", 0.2, fabric="#DDF3FF")
    mats["accent"] = L.mat("Ecorce_Liseré", "#2D6E96", 0.25)
    mats["root"] = L.mat("Racine_Gelee", "#7D93AE", 0.3, fabric="#A9BCD3")
    mats["turq"] = L.mat("Cristal_Turquoise", "#3FD8E8", 0.06, coat=1.0, transmission=0.4)
    mats["heart"] = L.mat("Coeur_de_Glace", "#BFF8FF", 0.2, emit="#7FEFFF", strength=6.0)
    mats["aura"] = L.mat("Aura_Coeur", "#9FEFFF", 0.3, emit="#9FEFFF", strength=3.0, alpha=0.35)
    mats["deco"] = mats["second"]
    mats["deco_leaf"] = mats["second"]
    mats["eye"] = L.mat("Oeil_Ancien", "#FFFFFF", 0.15)
    mats["pupil"] = L.mat("Pupille_Turquoise", "#06302E", 0.1, emit="#1FC8BC", strength=0.25)
    return mats


def canopy(m, mats, tip, size, bone, seed):
    for k in range(5):
        a = TAU * k / 5 + seed
        p = tip + V((math.cos(a) * size * 0.55, math.sin(a) * size * 0.55, (0.15 if k % 2 else -0.1) * size))
        r = size * (0.48 + 0.08 * (k % 3))
        m.add(L.lumpy("houppier", p, (r, r, r * 0.85), amp=0.12, seed=seed * 10 + k, nu=18, nv=10),
              mats["second"] if k % 2 else mats["leaf_dark"], bone)
        m.add(L.lumpy("houppier_neige", p + V((0, 0, r * 0.72)), (r * 0.6, r * 0.6, r * 0.22), amp=0.2,
                      seed=seed * 7 + k, nu=12, nv=6), mats["snow"], bone)
    m.add(L.lumpy("houppier_coeur", tip + V((0, 0, size * 0.35)), (size * 0.6,) * 3, amp=0.12, seed=seed + 3, nu=18, nv=10),
          mats["second"], bone)
    m.add(L.lumpy("houppier_neige", tip + V((0, 0, size * 0.85)), (size * 0.45, size * 0.45, size * 0.18), amp=0.2,
                  seed=seed + 5, nu=12, nv=6), mats["snow"], bone)


def propeller(m, mats, hub, radius, bone, blades=4, axis_y=-1):
    m.add(L.tube("moyeu", [hub + V((0, -axis_y * 0.1, 0)), hub + V((0, axis_y * radius * 0.25, 0))],
                 [radius * 0.16, radius * 0.04], 12, cap_rings=2), mats["gold"], bone)
    for k in range(blades):
        a = TAU * k / blades + 0.3
        bl = L.ellipsoid("pale_feuille", (radius * 0.55, 0, 0), (radius * 0.5, radius * 0.045, radius * 0.17), 16, 8)
        L.xform(bl, Matrix.Translation(hub) @ Matrix.Rotation(a, 4, "Y") @ Matrix.Rotation(math.radians(25), 4, "X"))
        m.add(bl, mats["second"], bone)
        vein = L.tube("pale_nervure", [V((radius * 0.12, radius * 0.04, 0)), V((radius * 0.95, radius * 0.03, 0))],
                      radius * 0.02, 6, cap_rings=1)
        L.xform(vein, Matrix.Translation(hub) @ Matrix.Rotation(a, 4, "Y") @ Matrix.Rotation(math.radians(25), 4, "X"))
        m.add(vein, mats["accent"], bone)


def root_spike(m, mats, base, bone, h=1.7):
    rp = L.bezier_pts(base + V((0, 0, -0.15)), base + V((0, 0, h * 0.4)), base + V((0.2, -0.15, h * 0.7)),
                      base + V((0.05, -0.3, h)), 10)
    m.add(L.tube("racine_surgie", rp, [0.38 - 0.32 * (j / 10) for j in range(11)], 14, cap_rings=3), mats["root"], bone)
    for j in range(6):
        a = TAU * j / 6
        m.add(L.lumpy("eclat_neige", base + V((math.cos(a) * 0.55, math.sin(a) * 0.55, 0.05)), (0.2, 0.2, 0.1), amp=0.3,
                      seed=j + int(base.y * 10), nu=10, nv=6), mats["snow"], bone)
    E.leaf(m, mats, rp[-3], V((0.6, -0.2, 1)), V((1, 0, 0)), 0.35, bone)


def build_geometry(m, mats):
    m.bone("Root", (0, 0, 0))
    m.bone("Body", (0, 0, ZC), "Root", soft=(None, 0.5))
    m.bone("Avant", (0, 3.0, ZC), "Body", soft=(1.7, 1.0))
    m.bone("Arriere", (0, -3.0, ZC), "Body", soft=(1.7, 1.0))
    m.bone("Visage", (0, 3.9, ZC + 0.6), "Avant")
    m.bone("Bouche", (0, 4.2, ZC - 0.3), "Avant")
    pc, nc = env(0.8, -math.pi / 2 + 0.12, 0.0, bark=False)
    heart_c = pc + nc * 0.3
    m.bone("Coeur", heart_c, "Avant")
    m.bone("Coeur_Aura", heart_c, "Coeur")
    branches = [(0.68, V((0.35, 0.3, 1)), 2.3), (0.47, V((-0.55, -0.05, 1)), 2.6), (0.3, V((0.5, -0.4, 1)), 2.1)]
    for i, (t, d, ln) in enumerate(branches):
        m.bone(f"Branche_{i + 1}", env(t, math.pi / 2, -0.1)[0], "Body")
    roots = [(0.33, -0.35), (0.45, 0.4), (0.57, -0.3), (0.39, 0.05), (0.52, 0.0)]
    for i, (t, dph) in enumerate(roots):
        m.bone(f"Racine_{i + 1}", env(t, -math.pi / 2 + dph, -0.1)[0], "Body")
    vines = [(0.62, 0.15), (0.36, 0.2), (0.62, math.pi - 0.15), (0.36, math.pi - 0.2)]
    for i, (t, ph) in enumerate(vines):
        m.bone(f"Liane_{i + 1}", env(t, ph - 0.25 if ph < 1 else ph + 0.25, -0.05)[0], "Body")
    pods = [(1, 1.4), (1, -1.6), (-1, 1.4), (-1, -1.6)]
    for i, (sx, y) in enumerate(pods):
        m.bone(f"Helice_{i + 1}", (sx * 2.75, y - 0.62, ZC - 0.1), "Body")
    m.bone("Helice_Queue", (0, Y0 - 0.25, ZC), "Arriere")
    m.bone("Ailerons", (0, -3.6, ZC), "Arriere")
    m.bone("Proj_Graine", heart_c + V((0, 0.5, -0.1)), "Root")
    m.bone("Proj_Invoc_1", (-0.9, 1.6, ZC - 1.9), "Root")
    m.bone("Proj_Invoc_2", (0.9, 1.6, ZC - 1.9), "Root")
    for i in range(3):
        m.bone(f"Proj_Vague_{i + 1}", (0, 6.0 + 2.3 * i, 0), "Root")
    m.bone("Proj_Tempete", (0, 0, ZC), "Root")
    m.bone("CTRL_Formes", (0, 0, -0.3), deform=False)

    # Enveloppe-tronc
    m.add(L.surface("tronc", lambda u, v: env(v, TAU * u)[0], 72, 64, pole0=True, pole1=True), mats["main"], None)
    for t in (0.22, 0.52, 0.72):
        c, _ = env(t, 0, 0, bark=False)
        rr = prof(t) * 1.06 + 0.02
        m.add(L.torus("sangle", (0, c.y, ZC), rr, 0.07, 72, 8, M=Matrix.Rotation(math.pi / 2, 4, "X")), mats["gold"], None)
        for k in range(12):
            a = TAU * k / 12
            m.add(L.sphere("rivet", V((math.cos(a) * (rr + 0.06), c.y + 0.03, ZC + math.sin(a) * (rr + 0.06))), 0.04, 8, 6),
                  mats["valve"], None)

    # Visage ancien : yeux, sourcils givrés, bouche sur la proue, barbe de mousse
    brow_mats = dict(mats, accent=mats["snow"])
    for sx in (-1, 1):
        p, n = env(0.9, math.pi / 2 - sx * 0.5, -0.06)
        E.eye(m, mats, p, n + V((0, 0.5, 0)), 0.42, "Visage", side=("G" if sx < 0 else "D"), look=V((0, 0, -0.35)), pupil_k=0.52)
        pb, nb = env(0.87, math.pi / 2 - sx * 0.3, 0.08)
        E.brow(m, brow_mats, pb + V((0, 0.12, 0.05)), nb + V((0, 0.6, 0)), 0.8, 0.12, 20 * sx, "Visage", side=("G" if sx < 0 else "D"))
        for j in range(3):
            m.add(L.icicle("givre_sourcil", pb + V((sx * (0.16 * j - 0.16), 0.22, -0.06)), 0.14, 0.04), mats["ice"], "Visage")
    zmo = 0.5
    tm = 0.6 + 0.4 * math.sqrt(1 - (zmo / RM) ** 2)
    ym = Y0 + (Y1 - Y0) * tm
    E.grin(m, mats, V((0, ym + 0.04, ZC - zmo)), V((0, 1, -0.5)), 0.6, 0.34, "Bouche")
    for k in range(6):
        a = -math.pi / 2 + (k - 2.5) * 0.28
        p, _ = env(0.935, a, -0.06)
        m.add(L.lumpy("mousse", p + V((0, 0.05, -0.05)), (0.22, 0.2, 0.24), amp=0.25, seed=k + 40, nu=12, nv=8),
              mats["leaf_dark"], "Bouche")

    # Cœur végétal lumineux dans sa cage dorée
    m.add(L.lumpy("coeur", heart_c, (0.38, 0.38, 0.42), amp=0.06, seed=3, nu=20, nv=12), mats["heart"], "Coeur")
    for a in (0.0, math.pi / 2):
        m.add(L.torus("cage", heart_c, 0.5, 0.045, 32, 6, M=Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Rotation(a, 4, "Y")
                      if False else Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X")), mats["gold"], "Coeur")
    for k in range(5):
        a = TAU * k / 5
        d = V((math.cos(a), 0.2, math.sin(a))).normalized()
        E.leaf(m, mats, heart_c + d * 0.45 - V((0, 0.15, 0)), d, V((0, 1, 0)), 0.35, "Coeur")
    m.add(L.sphere("aura", heart_c, 0.85, 24, 14), mats["aura"], "Coeur_Aura")

    # Branches + houppiers enneigés + cristaux
    for i, (t, d, ln) in enumerate(branches):
        b = f"Branche_{i + 1}"
        base = env(t, math.pi / 2, -0.1)[0]
        d = d.normalized()
        tip = base + d * ln + V((0, 0, 0.3))
        pts = L.bezier_pts(base, base + V((0, 0, ln * 0.45)), tip - d * ln * 0.3, tip, 10)
        m.add(L.tube("branche", pts, [0.48 - 0.3 * (j / 10) for j in range(11)], 16, cap_rings=3), mats["main"], b)
        fork_b = pts[5]
        side = d.cross(V((0, 0, 1))).normalized()
        ftip = fork_b + (side * (1 if i % 2 else -1) + V((0, 0, 0.9))).normalized() * ln * 0.45
        m.add(L.tube("fourche", [fork_b, (fork_b + ftip) / 2 + V((0, 0, 0.1)), ftip], [0.25, 0.2, 0.15], 12, cap_rings=3),
              mats["main"], b)
        canopy(m, mats, tip, 0.85, b, i * 1.7)
        canopy(m, mats, ftip, 0.5, b, i * 2.3 + 1)
        E.crystal_cluster(m, {"ice": mats["turq"], "deco": mats["ice"]}, tip + V((0, 0, 0.95)), V((0, 0, 1)),
                          0.6, b, n=5, seed=i + 20)
        m.add(L.torus("bague_branche", base + V((0, 0, 0.35)), 0.5, 0.06, 32, 6), mats["gold"], b)
        E.crystal_cluster(m, mats, base + V((side.x * 0.55, 0.0, 0.25)), V((side.x, 0, 1)), 0.55, b, n=4, seed=i + 2)
        m.add(L.lumpy("neige_branche", pts[3] + V((0, 0, 0.3)), (0.32, 0.3, 0.12), amp=0.2, seed=i + 60, nu=12, nv=6),
              mats["snow"], b)

    # Cristaux turquoise et neige sur l'échine, stalactites sous le ventre
    for k, (t, ph) in enumerate(((0.58, 1.95), (0.38, 1.2), (0.2, 1.9), (0.8, 1.3))):
        p, n = env(t, ph, -0.05)
        E.crystal_cluster(m, {"ice": mats["turq"], "deco": mats["ice"]}, p, n + V((0, 0, 0.6)), 0.65, None, n=5, seed=k + 9)
    for k, t in enumerate((0.15, 0.25, 0.4, 0.57, 0.78, 0.85)):
        p, n = env(t, math.pi / 2 + (0.15 if k % 2 else -0.15), -0.03)
        m.add(L.lumpy("neige_echine", p, (0.45, 0.4, 0.14), amp=0.22, seed=k + 70, nu=16, nv=8), mats["snow"], None)
    for k in range(14):
        t = 0.18 + 0.6 * k / 13
        ph = -math.pi / 2 + (0.95 if k % 2 else -0.95)
        p, _ = env(t, ph, -0.02)
        m.add(L.icicle("stalactite", p, 0.25 + 0.12 * (k % 3), 0.07), mats["ice"], None)

    # Racines pendantes
    for i, (t, dph) in enumerate(roots):
        b = f"Racine_{i + 1}"
        p0 = env(t, -math.pi / 2 + dph, -0.1)[0]
        sx = 1 if dph >= 0 else -1
        ln = 1.9 + 0.3 * (i % 2)
        pts = L.bezier_pts(p0, p0 + V((0, 0, -ln * 0.45)), p0 + V((sx * 0.45, -0.35, -ln * 0.85)),
                           p0 + V((sx * 0.75, 0.05, -ln * 0.95)), 12)
        m.add(L.tube("racine", pts, [0.26 - 0.2 * (j / 12) ** 0.9 for j in range(13)], 12, cap_rings=3), mats["root"], b)
        m.add(L.lumpy("racine_givre", pts[6], (0.17, 0.17, 0.08), amp=0.2, seed=i + 80, nu=10, nv=6), mats["snow"], b)

    # Lianes
    for i, (t, ph) in enumerate(vines):
        b = f"Liane_{i + 1}"
        top = m.bones[b]["head"]
        pts = [top + V((0.08 * math.sin(j * 1.1), 0.08 * math.cos(j * 0.9), -2.0 * j / 14)) for j in range(15)]
        E.vine(m, mats, pts, b, r=0.05, leaf_size=0.25, every=3)
        E.flower(m, mats, pts[-1] + V((0, 0.1, 0)), V((0, 1, 0)), 0.16, b)

    # Hélices latérales (nacelles) + hélice de queue
    for i, (sx, y) in enumerate(pods):
        b = f"Helice_{i + 1}"
        a = V((sx * 1.3, y, ZC - 0.25))
        m.add(L.tube("pylone", [a, V((sx * 2.0, y, ZC - 0.2)), V((sx * 2.55, y, ZC - 0.1))], 0.12, 10, cap_rings=2),
              mats["gold"], "Body")
        m.add(L.tube("nacelle", [V((sx * 2.75, y + 0.55, ZC - 0.1)), V((sx * 2.75, y, ZC - 0.1)),
                                 V((sx * 2.75, y - 0.5, ZC - 0.1))], [0.24, 0.3, 0.26], 16, cap_rings=4), mats["accent"], "Body")
        m.add(L.torus("nacelle_bague", (sx * 2.75, y + 0.15, ZC - 0.1), 0.3, 0.04, 24, 6,
                      M=Matrix.Rotation(math.pi / 2, 4, "X")), mats["gold"], "Body")
        m.add(L.lumpy("nacelle_neige", V((sx * 2.75, y, ZC + 0.18)), (0.2, 0.32, 0.07), amp=0.2, seed=i + 90, nu=12, nv=6),
              mats["snow"], "Body")
        propeller(m, mats, V((sx * 2.75, y - 0.62, ZC - 0.1)), 0.75, b)
    m.add(L.tube("arbre_queue", [V((0, Y0 + 0.15, ZC)), V((0, Y0 - 0.25, ZC))], 0.12, 10, cap_rings=2), mats["gold"], "Arriere")
    propeller(m, mats, V((0, Y0 - 0.25, ZC)), 1.1, "Helice_Queue")

    # Ailerons-feuilles
    for d, face in ((V((1, -0.5, 0)), V((0, 0, 1))), (V((-1, -0.5, 0)), V((0, 0, 1))), (V((0, -0.6, 1)), V((1, 0, 0)))):
        base = V((0, -3.35, ZC)) + V((d.x, 0, d.z)).normalized() * (prof(t_of(-3.35)) - 0.1)
        E.leaf(m, mats, base, d.normalized(), face, 1.5, "Ailerons", mat_key="leaf_dark")

    # Valve
    pv, nv = env(0.12, math.pi / 2 + 0.5, 0.0)
    Mv = L.orient(pv, nv)
    for ob in (L.tube("valve", [V((0, -0.03, 0)), V((0, 0.18, 0))], 0.13, 14, cap_rings=2),
               L.torus("valve_bague", (0, 0.1, 0), 0.15, 0.04, 18, 6, M=Matrix.Rotation(math.pi / 2, 4, "X")),
               L.ellipsoid("valve_bouchon", (0, 0.24, 0), (0.09, 0.05, 0.09), 12, 8)):
        m.add(L.xform(ob, Mv), mats["valve"], None)

    # Projectiles
    g = m.bones["Proj_Graine"]["head"]
    m.add(L.ellipsoid("graine", g, (0.3, 0.42, 0.3), 18, 12), mats["gold"], "Proj_Graine")
    m.add(L.torus("graine_bande", g, 0.3, 0.04, 24, 6, M=Matrix.Rotation(math.pi / 2, 4, "X")), mats["heart"], "Proj_Graine")
    E.leaf(m, mats, g + V((0, -0.1, 0.25)), V((0.3, -0.5, 1)), V((1, 0, 0)), 0.35, "Proj_Graine")
    for i in (1, 2):
        b = f"Proj_Invoc_{i}"
        c = m.bones[b]["head"]
        m.add(L.ellipsoid("mini_ballon", c, (0.38, 0.36, 0.42), 20, 12), mats["second"], b)
        m.add(L.tube("mini_noeud", [c + V((0, 0, -0.42)), c + V((0, 0, -0.55))], [0.06, 0.03], 8, cap_rings=2), mats["accent"], b)
        top = c + V((0, 0, -0.55))
        hang = [top + V((0.04 * math.sin(j * 0.8), 0.03 * math.sin(j * 0.5), -0.9 * j / 18)) for j in range(19)]
        for j in range(1, 25):
            a = L.TAU * 3 * j / 24
            hang.append(hang[18] + V((0.05 * math.sin(a), 0.05 * (1 - math.cos(a)), -0.35 * j / 24)))
        E.balloon_string(m, mats, hang, [(b, top)], r=0.014, knot=False)
        E.leaf(m, mats, c + V((0, 0, 0.38)), V((0.4 * (1 if i == 1 else -1), 0, 1)), V((0, 1, 0)), 0.3, b)
        for sx in (-1, 1):
            E.eye(m, mats, c + V((sx * 0.13, 0.31, 0.08)), V((sx * 0.3, 1, 0.1)), 0.1, b, look=V((0, 0, -0.2)))
    for i in range(3):
        root_spike(m, mats, m.bones[f"Proj_Vague_{i + 1}"]["head"].copy(), f"Proj_Vague_{i + 1}", h=1.6 + 0.2 * i)
    for k in range(12):
        a = TAU * k / 12
        p = V((math.cos(a) * 3.6, math.sin(a) * 3.6, ZC + 0.4 * math.sin(3 * a)))
        m.add(L.lumpy("tempete_neige", p, (0.45, 0.45, 0.3), amp=0.25, seed=k + 100, nu=12, nv=8), mats["snow"], "Proj_Tempete")
        if k % 3 == 0:
            E.snowflake_emblem(m, mats, p + V((0, 0, 0.55)), V((math.cos(a), math.sin(a), 0)), 0.3, "Proj_Tempete",
                               mat=mats["turq"])
    # verrous d'attache : branches, racines, lianes, pylônes, cœur, bouche, queue collés au tronc
    for i in range(3):
        m.lock(m.bones[f"Branche_{i + 1}"]["head"], 0.8, "Body")
    for i in range(5):
        m.lock(m.bones[f"Racine_{i + 1}"]["head"], 0.45, "Body")
    for i in range(4):
        m.lock(m.bones[f"Liane_{i + 1}"]["head"], 0.3, "Body")
    for sx, y in pods:
        m.lock(V((sx * 1.3, y, ZC - 0.25)), 0.55, "Body")
    m.lock(m.bones["Coeur"]["head"], 0.8, "Avant")
    m.lock(m.bones["Bouche"]["head"], 0.85, "Bouche")
    m.lock(V((0, -3.35, ZC)), 1.3, "Arriere")
    return branches


# --------------------------------------------------------------------------------------------
# Animations
# --------------------------------------------------------------------------------------------
HIDDEN = ["Proj_Graine", "Proj_Invoc_1", "Proj_Invoc_2", "Proj_Vague_1", "Proj_Vague_2", "Proj_Vague_3",
          "Proj_Tempete", "Coeur_Aura"]
PROPS = ["Helice_1", "Helice_2", "Helice_3", "Helice_4"]


def base_pose(t, spin, phase2=False, vines=None, P=60.0):
    p = Pose()
    for b in HIDDEN:
        p.set(b, scl=0.0001)
    for i, b in enumerate(PROPS):
        p.set(b, rot=(0, spin * (1 if i < 2 else -1), 0))
    p.set("Helice_Queue", rot=(0, spin * 0.7, 0))
    v = vines if vines is not None else (1.0 if phase2 else 0.5)
    for i in range(4):
        p.set(f"Liane_{i + 1}", scl=(1, 1, v), rot=(5 * osc(t, P, i), 5 * osc(t, P, i + 1.5), 0))
    for i in range(5):
        p.set(f"Racine_{i + 1}", rot=(6 * osc(t, P, 0.7 * i), 4 * osc(t, P, 0.7 * i + 1), 0))
    for i in range(3):
        p.set(f"Branche_{i + 1}", rot=(2.5 * osc(t, P, 1.1 * i), 2.5 * osc(t, P, 1.1 * i + 0.8), 0))
    if phase2:
        p.set("Coeur_Aura", scl=1.0 + 0.12 * osc(t, P, 0, 4))
        p.set("Coeur", scl=1.15 + 0.1 * osc(t, P, 0, 4))
    else:
        p.set("Coeur", scl=1.0 + 0.05 * osc(t, P, 0, 2))
    return p


def a_idle(t, phase2=False):
    P = 60.0
    p = base_pose(t, 360 * (6 if phase2 else 4) * t / P, phase2)
    p.set("Root", loc=(0, 0, 0.18 * (0.5 - 0.5 * math.cos(TAU * t / P))))
    p.set("Body", rot=(1.5 * osc(t, P, 0.4), 1.8 * osc(t, P, 1.4), 1.0 * osc(t, P, 0.2)),
          scl=(1 + 0.012 * osc(t, P, 0, 2), 1 - 0.008 * osc(t, P, 0, 2), 1 + 0.012 * osc(t, P, 0, 2)))
    p.set("Avant", scl=(1 + 0.015 * osc(t, P, 1, 2),) * 3)
    p.set("Arriere", rot=(0, 0, 1.2 * osc(t, P, 1.0)))
    p.set("Ailerons", rot=(4 * osc(t, P, 0.3, 2), 0, 3 * osc(t, P, 1.3)))
    a = 4.5 if phase2 else 2.5
    for i in range(3):
        p.set(f"Branche_{i + 1}", rot=(a * osc(t, P, 1.1 * i), a * osc(t, P, 1.1 * i + 0.8), 0))
    p.set("Visage", scl=(1, 1, 1 - 0.85 * math.exp(-((t - 42) / 1.8) ** 2)))
    p.shapes(resp=0.4 * osc(t, P, 0, 2))
    return p


def a_move(t):
    P = 40.0
    p = base_pose(t, 360 * 9 * t / P, P=P)
    p.set("Root", loc=(0, 0, 0.12 * (0.5 - 0.5 * math.cos(TAU * 2 * t / P))))
    p.set("Body", rot=(-6 + 1.5 * osc(t, P, 0.5, 2), 2.5 * osc(t, P, 0), 0), scl=(0.98, 1.04, 0.98))
    p.set("Arriere", loc=(0, -0.1, 0), rot=(0, 0, 2.5 * osc(t, P, 0.4)))
    p.set("Avant", scl=(1.02, 0.97, 1.02))
    for i in range(3):
        p.set(f"Branche_{i + 1}", rot=(12 + 3 * osc(t, P, i, 2), 3 * osc(t, P, i + 1), 0))
    for i in range(5):
        p.set(f"Racine_{i + 1}", rot=(22 + 5 * osc(t, P, i, 2), 3 * osc(t, P, i), 0))
    for i in range(4):
        p.add(f"Liane_{i + 1}", rot=(25, 0, 0))
    p.set("Ailerons", rot=(5 * osc(t, P, 0.3, 2), 0, 4 * osc(t, P, 1.3)))
    p.shapes(resp=0.2, impact=0.12)
    return p


def a_fly(t):
    """VOL : monte en altitude, hélices à plein régime, grands virages inclinés, branches et racines
    rabattues par le vent."""
    P = 60.0
    p = base_pose(t, 360 * 14 * t / P, P=P)
    p.set("Root", loc=(0.3 * osc(t, P, 0), 0, 1.4 + 0.2 * osc(t, P, 0.5, 2)))
    p.set("Body", rot=(-7 + 2 * osc(t, P, 0.5, 2), 9 * osc(t, P, 0), 5 * osc(t, P, math.pi / 2)),
          scl=(0.98, 1.05, 0.98))
    p.set("Arriere", loc=(0, -0.12, 0), rot=(0, 0, -3 * osc(t, P, 0.4)))
    p.set("Avant", scl=(1.02, 0.96, 1.02))
    for i in range(3):
        p.set(f"Branche_{i + 1}", rot=(16 + 4 * osc(t, P, i, 2), 5 * osc(t, P, i + 1), 0))
    for i in range(5):
        p.set(f"Racine_{i + 1}", rot=(30 + 6 * osc(t, P, i, 2), 5 * osc(t, P, i), 0))
    for i in range(4):
        p.add(f"Liane_{i + 1}", rot=(32, 0, 0))
    p.set("Ailerons", rot=(6 * osc(t, P, 0.3, 2), 0, -7 * osc(t, P, 1.3)))
    p.shapes(resp=0.25, impact=0.15)
    return p


def a_attack(t):
    """Éperonnage : recul, toutes hélices à fond, ruée de la proue, impact écrasé, rebond."""
    spin = track(t, [(0, 0, "lin"), (14, 900, "in"), (24, 2800, "lin"), (50, 4200, "out")])
    p = base_pose(t, spin)
    p.set("Root", loc=(0, track(t, [(0, 0), (14, -1.0, "ease"), (21, 3.6, "in"), (25, 3.4), (34, 1.6), (50, 0, "ease")]),
                       track(t, [(0, 0), (14, 0.2), (21, -0.1), (25, 0), (31, 0.4), (40, 0.05), (50, 0)])))
    p.set("Body", rot=(track(t, [(0, 0), (14, 6), (20, -6), (25, 2), (32, -1.5), (50, 0)]), decay(t, 23, 18, 2.5, 4), 0),
          scl=track3(t, [(0, (1, 1, 1)), (14, (1.05, 0.9, 1.05)), (20, (0.95, 1.12, 0.95)), (24, (1.08, 0.86, 1.06)),
                         (30, (0.98, 1.04, 0.99)), (50, (1, 1, 1))]))
    p.set("Avant", loc=(0, track(t, [(0, 0), (21, 0), (24, -0.4), (30, 0.05), (40, 0)]), 0),
          scl=track3(t, [(0, (1, 1, 1)), (21, (1, 1, 1)), (24, (1.15, 0.78, 1.12)), (31, (1, 1, 1))]))
    p.set("Arriere", loc=(0, track(t, [(0, 0), (14, 0.15), (20, -0.3), (25, 0.3), (33, 0), (50, 0)]), 0))
    for i in range(3):
        p.set(f"Branche_{i + 1}", rot=(track(t, [(0, 0), (14, -10), (20, 22), (25, -20), (32, 8), (42, 0)]),
                                       decay(t, 23, 20, 2.5, 8), 0))
    for i in range(5):
        p.set(f"Racine_{i + 1}", rot=(track(t, [(0, 0), (14, -15), (20, 35), (25, -25), (33, 10), (44, 0)]), 0, 0))
    p.set("Bouche", scl=track3(t, [(0, (1, 1, 1)), (14, (0.9, 1, 0.8)), (21, (1.2, 1, 1.5)), (28, (1.1, 1, 1.2)),
                                   (36, (1, 1, 1))]))
    p.set("Visage", scl=(1, 1, track(t, [(0, 1), (14, 0.6), (20, 1.15), (24, 0.5), (32, 1), (50, 1)])))
    p.shapes(resp=track(t, [(0, 0), (14, 0.5), (21, -0.2), (28, 0), (50, 0)]),
             impact=track(t, [(0, 0), (21, 0), (24, 1.0), (30, 0.1), (38, 0), (50, 0)]))
    return p


def a_hit(t):
    p = base_pose(t, track(t, [(0, 0), (3, -90), (20, 300)]))
    p.set("Root", loc=(decay(t, 2, 16, 3, 0.1), track(t, [(0, 0), (3, -0.5, "out"), (11, -0.3), (20, 0, "ease")]),
                       track(t, [(0, 0), (3, 0.1), (20, 0)])))
    p.set("Body", rot=(track(t, [(0, 0), (3, 6), (8, -3), (13, 1), (20, 0)]), decay(t, 2, 16, 3, 5), decay(t, 3, 16, 2.5, 3)),
          scl=track3(t, [(0, (1, 1, 1)), (2, (1.08, 0.88, 0.92)), (6, (0.96, 1.05, 1.05)), (11, (1, 1, 1))]))
    for i in range(3):
        p.set(f"Branche_{i + 1}", rot=(decay(t, 2 + i, 17, 3, 15), decay(t, 3 + i, 17, 2.5, 10), 0))
    for i in range(5):
        p.set(f"Racine_{i + 1}", rot=(decay(t, 2, 17, 2.5, 25), decay(t, 3, 17, 2, 12), 0))
    p.set("Visage", scl=(1.05, 1, track(t, [(0, 1), (2, 0.3), (10, 0.4), (15, 1), (20, 1)])))
    p.set("Coeur", scl=track(t, [(0, 1), (2, 1.3), (8, 0.9), (14, 1)]))
    p.shapes(resp=track(t, [(0, 0), (2, -0.5), (8, 0.2), (14, 0)]), impact=track(t, [(0, 0), (2, 0.8), (9, 0), (20, 0)]))
    return p


def a_death(t):
    """L'air fuit : il pique du nez en spirale, ses branches retombent, il s'écrase dans la neige,
    se ratatine et disparaît."""
    spin = track(t, [(0, 0, "lin"), (10, 400, "lin"), (50, 1300, "out"), (90, 1320)])
    p = base_pose(t, spin)
    on = 1.0 if t > 8 else 0.0
    fade = 1 - ease((t - 50) / 20)
    p.set("Root", loc=(0.4 * math.sin(TAU * max(t - 8, 0) / 30) * on * fade,
                       track(t, [(0, 0), (3, -0.5, "out"), (10, -0.3), (55, 1.0), (90, 1.2)]),
                       track(t, [(0, 0), (3, 0.1), (12, 0.4), (58, -ZC + 1.6, "ease"), (90, -ZC + 1.6)])))
    s = track3(t, [(0, (1, 1, 1)), (3, (1.08, 0.9, 0.9)), (10, (1, 1, 1)), (45, (0.92, 0.9, 0.85), "ease"),
                   (62, (1.05, 0.82, 0.45), "ease"), (76, (0.95, 0.75, 0.3)), (90, (0.001, 0.001, 0.001), "in")])
    p.set("Body", rot=(track(t, [(0, 0), (3, 6), (12, 0), (58, -14, "ease"), (66, -4), (90, -4)]) + 3 * math.sin(TAU * t / 9) * on * fade,
                       track(t, [(0, 0), (10, 0), (58, 35, "ease"), (66, 10), (90, 10)]),
                       track(t, [(0, 0), (10, 0), (58, 70, "ease"), (90, 75)])), scl=s)
    for i in range(3):
        droop = ease((t - 20 - 5 * i) / 35)
        p.set(f"Branche_{i + 1}", rot=(50 * droop + 6 * math.sin(TAU * t / 7 + i) * on * fade, (-1) ** i * 35 * droop, 0),
              scl=1 - 0.3 * droop)
    for i in range(5):
        p.set(f"Racine_{i + 1}", rot=(track(t, [(0, 0), (40, 15), (60, 70)]), 0, 0), scl=1 - 0.4 * ease((t - 50) / 20))
    p.set("Coeur", scl=track(t, [(0, 1), (3, 1.4), (10, 1), (50, 0.6), (70, 0.2), (90, 0.2)]))
    p.set("Visage", scl=(1, 1, track(t, [(0, 1), (3, 0.3), (12, 0.9), (40, 0.6), (62, 0.15), (90, 0.15)])))
    p.shapes(resp=track(t, [(0, 0), (3, -0.4), (10, 0), (45, -0.6), (68, -1)]),
             impact=track(t, [(0, 0), (3, 0.7), (10, 0), (56, 0), (60, 0.8), (68, 0.3)]),
             deflate=track(t, [(0, 0), (10, 0), (45, 0.35, "ease"), (70, 1.0, "ease"), (90, 1.0)]))
    return p


def a_vague(t):
    """Les racines plongent sous la neige ; trois racines surgissent l'une après l'autre devant lui."""
    p = base_pose(t, 360 * 5 * t / 60)
    dive = track(t, [(0, 0), (12, 1, "ease"), (44, 1), (58, 0, "ease")])
    for i in range(5):
        p.set(f"Racine_{i + 1}", rot=(-35 * dive, 0, 0), scl=(1, 1, 1 + 0.6 * dive))
    p.set("Body", rot=(track(t, [(0, 0), (12, -8), (44, -8), (58, 0)]), 0, 0),
          scl=(1 + 0.05 * dive, 1, 1 - 0.05 * dive))
    p.set("Root", loc=(0, 0, track(t, [(0, 0), (12, -0.4), (44, -0.4), (58, 0)])))
    for i in range(3):
        t0 = 16 + 6 * i
        up = track(t, [(0, -2.0), (t0, -2.0), (t0 + 5, 0.25, "out"), (t0 + 8, -0.05), (t0 + 11, 0), (t0 + 20, 0),
                       (t0 + 27, -2.0, "in")])
        s = track(t, [(0, 0.0001), (t0, 0.0001), (t0 + 2, 0.8), (t0 + 6, 1.15), (t0 + 9, 1.0), (t0 + 22, 1.0), (t0 + 27, 0.0001)])
        p.set(f"Proj_Vague_{i + 1}", loc=(0, 0, up), scl=max(s, 1e-4), rot=(decay(t, t0 + 5, 14, 3, 10), decay(t, t0 + 6, 14, 2.5, 8), 0))
    p.set("Visage", scl=(1, 1, track(t, [(0, 1), (12, 0.5), (40, 0.5), (50, 1), (60, 1)])))
    p.set("Bouche", scl=track3(t, [(0, (1, 1, 1)), (12, (1.15, 1, 1.4)), (40, (1.1, 1, 1.2)), (52, (1, 1, 1))]))
    p.shapes(resp=track(t, [(0, 0), (12, -0.3), (30, 0.3), (50, 0)]))
    return p


def a_graines(t):
    """Le cœur pulse, une graine explosive est expulsée, décrit une parabole et explose ~10 m devant."""
    p = base_pose(t, 360 * 5 * t / 45)
    p.set("Coeur", scl=track(t, [(0, 1), (6, 1.3), (9, 1.0), (12, 1.45), (16, 0.85), (22, 1.0)]))
    p.set("Body", rot=(track(t, [(0, 0), (12, 5), (16, -7), (22, 2), (30, 0)]), 0, 0))
    p.set("Root", loc=(0, track(t, [(0, 0), (12, 0.2), (16, -0.5, "out"), (30, 0, "ease")]), 0))
    grow = track(t, [(0, 0.0001), (8, 0.0001), (14, 1.0, "out")])
    fly = max(0.0, min(1.0, (t - 16) / 16))
    boom = track(t, [(0, 1), (32, 1), (34, 2.8, "out"), (40, 0.0001, "in")])
    g0 = 1.0
    p.set("Proj_Graine", loc=(0, fly * 8.5, fly * 3.0 - fly * fly * (3.0 + 2.2) + 0.0 * g0),
          rot=(fly * 540, 0, fly * 120), scl=max(grow * boom, 1e-4))
    p.set("Bouche", scl=track3(t, [(0, (1, 1, 1)), (12, (0.9, 1, 0.8)), (16, (1.2, 1, 1.4)), (26, (1, 1, 1))]))
    p.shapes(resp=track(t, [(0, 0), (12, 0.6), (16, -0.4), (26, 0)]))
    return p


def a_tempete(t):
    """Il agite ses grandes branches : un anneau de tempête de neige tourbillonne et s'étend."""
    p = base_pose(t, track(t, [(0, 0, "lin"), (60, 3600, "lin")]))
    shake = (8 < t < 44) * 1.0
    for i in range(3):
        p.set(f"Branche_{i + 1}", rot=(14 * math.sin(TAU * t / 6 + i) * shake, 18 * math.sin(TAU * t / 5 + 1.3 * i) * shake, 0))
    p.set("Body", rot=(0, 4 * math.sin(TAU * t / 10) * shake, 0))
    s = track(t, [(0, 0.0001), (10, 0.0001), (18, 1.0, "out"), (40, 1.7), (52, 2.4), (58, 0.0001, "in")])
    p.set("Proj_Tempete", rot=(0, 0, track(t, [(0, 0, "lin"), (60, 540, "lin")])), scl=(max(s, 1e-4), max(s, 1e-4), max(min(s, 1.3), 1e-4)))
    p.set("Visage", scl=(1, 1, track(t, [(0, 1), (8, 0.5), (44, 0.5), (52, 1)])))
    p.shapes(resp=0.3 * math.sin(TAU * t / 5) * shake)
    return p


def a_invoc(t):
    """Le ventre se gonfle et libère deux petits ballons végétaux qui s'envolent sur les côtés."""
    p = base_pose(t, 360 * 4 * t / 50)
    p.set("Body", scl=track3(t, [(0, (1, 1, 1)), (12, (1.06, 1, 1.08)), (16, (0.96, 1, 0.94)), (24, (1, 1, 1))]))
    for i, sx in ((1, -1), (2, 1)):
        d = 2 * (i - 1)
        s = track(t, [(0, 0.0001), (10 + d, 0.0001), (16 + d, 1.2, "out"), (20 + d, 1.0)])
        x = track(t, [(0, 0), (16 + d, 0), (34 + d, sx * 2.0, "ease"), (50, sx * 2.0)])
        z = track(t, [(0, 0), (14 + d, -0.3), (20 + d, -1.0), (34 + d, -0.6), (50, -0.6)]) + 0.1 * math.sin(TAU * t / 12) * (t > 34)
        y = track(t, [(0, 0), (16 + d, 0), (34 + d, 1.6, "ease"), (50, 1.6)])
        p.set(f"Proj_Invoc_{i}", loc=(x, y, z), scl=max(s, 1e-4), rot=(0, decay(t, 16 + d, 20, 2, 15), 0))
    p.set("Visage", scl=(1, 1, track(t, [(0, 1), (10, 0.5), (18, 1.1), (28, 1)])))
    p.set("Coeur", scl=track(t, [(0, 1), (12, 1.3), (18, 1.0)]))
    p.shapes(resp=track(t, [(0, 0), (12, 0.9), (16, -0.3), (26, 0)]))
    return p


def a_phase2(t):
    """Phase 2 : le cœur s'illumine (aura), les lianes s'étendent, les branches s'ouvrent."""
    k = ease((t - 14) / 20)
    p = base_pose(t, track(t, [(0, 0, "lin"), (20, 600, "in"), (60, 3200, "lin")]), vines=0.5 + 0.5 * k)
    p.set("Coeur", scl=track(t, [(0, 1), (10, 0.85), (18, 1.6, "out"), (26, 1.1), (60, 1.15)]))
    p.set("Coeur_Aura", scl=max(track(t, [(0, 0.0001), (14, 0.0001), (22, 1.4, "out"), (30, 0.95), (60, 1.0)]), 1e-4))
    for i in range(3):
        p.set(f"Branche_{i + 1}", rot=(track(t, [(0, 0), (12, 10), (24, -12), (34, -6), (60, -6)]),
                                       (-1) ** i * track(t, [(0, 0), (12, -4), (24, 14), (34, 9), (60, 9)]), 0))
    p.set("Body", rot=(track(t, [(0, 0), (12, 6), (22, -8), (32, 0)]), 0, 0),
          scl=track(t, [(0, 1), (12, 0.97), (22, 1.06), (32, 1.02), (60, 1.02)]))
    p.set("Bouche", scl=track3(t, [(0, (1, 1, 1)), (12, (0.9, 1, 0.7)), (22, (1.3, 1, 1.6)), (36, (1.15, 1, 1.3)), (50, (1, 1, 1))]))
    p.set("Visage", scl=(1.05, 1, track(t, [(0, 1), (12, 0.4), (22, 1.2), (40, 1.05), (60, 1)])))
    p.shapes(resp=track(t, [(0, 0), (12, -0.4), (22, 1.0), (34, 0.5), (60, 0.5)]))
    return p


ACTIONS = {
    "IDLE": (61, True, lambda t: a_idle(t)),
    "MOVE": (41, True, a_move),
    "FLY": (61, True, a_fly),
    "ATTACK": (51, False, a_attack),
    "HIT": (21, False, a_hit),
    "DEATH": (91, False, a_death),
    "ATTACK_VagueRacines": (61, False, a_vague),
    "ATTACK_GrainesExplosives": (46, False, a_graines),
    "ATTACK_TempeteNeige": (61, False, a_tempete),
    "ATTACK_Invocation": (51, False, a_invoc),
    "PHASE2_Eveil": (61, False, a_phase2),
    "IDLE_Phase2": (61, True, lambda t: a_idle(t, True)),
}


def build(elem="glace"):
    m = L.Model("Boss_Gardien_Glaciers_Glace", "Le Grand Gardien des Glaciers")
    mats = materials(elem)
    build_geometry(m, mats)
    # seuls les éléments du boss restent : projectiles et aura (attaques spéciales non exportées) retirés
    m.drop(lambda n: n.startswith("Proj_") or n == "Coeur_Aura")
    m.build(shape_amp=0.4, wrinkle=0.012)
    import anims
    return m, anims.with_eyes(ACTIONS, m.meta.get("eye_r", 0.25))
