"""BOSS FINAL - LE GRAND BALLON OASIS (type Plante, PV 1800).

Immense dirigeable gonflable portant une oasis volante : enveloppe verte à 12 fuseaux, bandes dorées et
turquoise à losanges berbères, frise de hiéroglyphes dorés, visage de boss sur le nez ; sur le dos, une
île de sable aux rides de dunes avec un bassin gonflable turquoise, trois palmiers gonflables (troncs
annelés, palmes, noix de coco), buissons et grande fleur ; dessous, une réserve d'eau gonflable suspendue
à des cordages ; lianes feuillues pendantes ; deux nacelles-moteurs latérales et une grande hélice
arrière (3 hélices) ; 4 grands ailerons.
Longueur ~15 m, centre de l'enveloppe à 7 m, avant vers +Y, pivot au sol.
"""
import math

from mathutils import Vector

from . import core
from .core import TAU, HIEROGLYPHS, K, Pose, damp, frame_matrix, gores, jitter, surface, vol
from .family import Family, fx_layer, valve

ZC = 7.0
Y0, Y1 = -6.8, 6.0
RMAX = 2.6
GORE = gores(12, 0.04, phase=0.0, sharp=0.7)
HIDDEN = 0.001

ISLAND_C = Vector((0, -0.4, ZC + 2.25))
PALMS = [(-1.05, -2.2), (1.15, -1.0), (-0.9, 1.15)]
POND = (0.55, 1.3)
PODS = [(1, "Prop_L"), (-1, "Prop_R")]
VINES = [(1, 2.2), (1, -0.6), (1, -3.2), (-1, 1.6), (-1, -1.2), (-1, -3.6)]
TORNADOES = [(-3.6, 8.0), (3.6, 8.0)]
CACTI = [(-2.4, 11.0), (0.0, 12.6), (2.4, 11.0)]
COCO_TARGETS = [(-1.8, 10.0), (0.4, 12.5), (2.2, 9.5)]


def env_r(t):
    tp = 1 - (1 - t) ** 0.8
    return RMAX * max(0.0, math.sin(math.pi * tp)) ** 0.55


def env_point(t, th, lift=0.0):
    r = env_r(t) * GORE(th, t) + lift
    return Vector((math.sin(th) * r, Y0 + (Y1 - Y0) * t, ZC + math.cos(th) * r))


BANDS = [(0.1, 0.13, "or"), (0.13, 0.155, "turquoise"),
         (0.36, 0.38, "sable"), (0.38, 0.45, "turquoise"), (0.45, 0.47, "sable"),
         (0.76, 0.78, "or"), (0.78, 0.81, "turquoise"), (0.81, 0.83, "or")]
SLOTS = ["corps", "corps2", "sable", "ocre", "or", "turquoise"]


def palm_top(k):
    x, y = PALMS[k]
    return Vector((x + (0.35 if x < 0 else -0.35) * 0 + 0.25 * (1 if k == 1 else -1), y + 0.2, ISLAND_C.z + 0.35 + 3.0))


class Oasis(Family):
    key = "Grand_Ballon_Oasis"
    short = "Oasis"
    label = "Le Grand Ballon Oasis (boss final)"
    boss_file = "Boss_Grand_Ballon_Oasis_Plante"
    pv = 1800
    surface_parts = ("Enveloppe",)
    crown = dict(loc=(1.05, 2.55, ZC + 2.4), size=0.95)
    aura = dict(center=(0, 0, ZC), radius=1.0, axis=(0, 0, 1), count=0, size=0.1)
    emblems = (((-9, -2.2, ZC + 0.4), (1, 0, 0), 1.2), ((9, -2.2, ZC + 0.4), (-1, 0, 0), 1.2))
    face_frame = dict(center=(0, 0, ZC), dist=12.0)
    face_params = dict(eye_r=0.5, eye_dx=0.85, eye_v=0.5, mouth_v=-0.75, mouth_w=1.35, mouth_h=0.48, brow_w=1.0,
                       brow=0.65, brow_arch=0.2)
    face_bone = "Env_Front"
    fly_from = "Move"
    fly_lift = 0.0
    prop_prefixes = ('Coco', 'Vague', 'Tornade', 'Mini_Cactus')
    strings = tuple(dict(parent="Envelope", hang=True, dir=(0, 0, -1), r=0.045, scale=3.5,
                         path=[(x, y, z), (x + 0.1, y - 0.1, z - 1.1), (x - 0.12, y - 0.2, z - 2.2),
                               (x + 0.08, y - 0.3, z - 3.2)])
                    for x, y, z in ((0.0, -3.0, 4.98), (-0.9, -2.3, 4.92), (0.9, -2.3, 4.92)))
    anim_pad_forward = 0.8

    def __init__(self):
        b = [("Root", (0, 0, 0), None), ("Hover", (0, 0, ZC), "Root"), ("Envelope", (0, 0, ZC), "Hover"),
             ("Env_Front", (0, 3.8, ZC), "Envelope"), ("Env_Back", (0, -3.8, ZC), "Envelope"),
             ("Island", tuple(ISLAND_C), "Envelope"), ("FX", self.crown["loc"], "Island"),
             ("Tank", (0, 0.4, ZC - 2.45), "Hover"), ("Prop_T", (0, Y0 - 0.45, ZC), "Env_Back")]
        for k, (x, y) in enumerate(PALMS):
            b.append((f"Palm_{k + 1}", (x, y, ISLAND_C.z + 0.3), "Island"))
            b.append((f"Palm_{k + 1}_Top", tuple(palm_top(k)), f"Palm_{k + 1}"))
            b.append((f"Coco_{k + 1}", tuple(palm_top(k) - Vector((0, 0, 0.35))), "Hover"))
        for s, bone in PODS:
            b.append((bone, (s * 3.05, -2.05, ZC - 0.7), "Envelope"))
        for k, (s, y) in enumerate(VINES):
            b.append((f"Vine_{k + 1}", (s * 2.25, y, ZC - 1.0), "Envelope"))
        b.append(("SandWave", (0, 4.0, 0), "Root"))
        for k, (x, y) in enumerate(TORNADOES):
            b.append((f"Tornado_{k + 1}", (x, y, 0), "Root"))
        for k, (x, y) in enumerate(CACTI):
            b.append((f"Cactus_{k + 1}", (x, y, 0), "Root"))
        self.BONES = b
        self.HEAD = {n: Vector(h) for n, h, _ in b}

    def body_weight(self, co):
        return core.gradient("y", [(-4.5, "Env_Back"), (-1.0, "Envelope"), (1.5, "Envelope"), (4.6, "Env_Front")])(co)

    # ------------------------------------------------------------------ géométrie de référence
    def build(self, B):
        rig = core.make_rig("REF_" + self.key, self.rig_bones(), B.coll, length=0.4)
        bw = self.body_weight
        # anneaux de base + anneaux posés exactement sur les bords des bandes (bandes nettes, peu de triangles)
        base = [0.5 * (i / 21) + 0.5 * (1 - math.cos(math.pi * i / 21)) / 2 for i in range(22)]
        ts = sorted(set([round(t, 4) for t in base] + [v for a, b, _ in BANDS for v in (a, b)]))
        ts = [t for k, t in enumerate(ts) if k == 0 or t - ts[k - 1] > 0.004]
        n = len(ts)
        path = [Vector((0, Y0 + (Y1 - Y0) * t, ZC)) for t in ts]

        def mat(i, j, th, t):
            tm = (ts[i] + ts[min(i + 1, n - 1)]) / 2
            for a, b, role in BANDS:
                if a <= tm < b:
                    if role == "turquoise" and (b - a) > 0.05:
                        x = abs(((th * 12 / TAU) % 1.0) - 0.5) * 2
                        if x * 0.04 + abs(tm - (a + b) / 2) < 0.032:
                            return SLOTS.index("ocre")
                    return SLOTS.index(role)
            return 1 if math.cos(th) < -0.55 and tm < 0.74 else 0
        env = B.sweep("Enveloppe", path, [env_r(t) for t in ts], SLOTS, nseg=36, section=GORE, up=(0, 0, 1),
                      mat_fn=mat)
        core.weight_fn(env, bw)
        bvh = core.bvh_of([env])
        for k in range(0, 12, 2):  # une couture sur deux suffit à cette échelle
            th = TAU * k / 12
            pts = [env_point(0.03 + 0.76 * i / 13, th, 0.01) for i in range(14)]
            core.weight_fn(B.tube(f"Couture_{k}", pts, 0.03, "couture", n=14, nseg=3, ncap=1), bw)

        # frise de hiéroglyphes dorés (flancs)
        names = ["soleil", "ankh", "oeil", "eau", "lotus", "oiseau", "plume", "scarabee"]
        gi = 0
        for s in (-1, 1):
            for y in (-2.0, 1.2):
                o = Vector((s * 9, y, ZC - 0.6))
                loc, nrm = surface(bvh, o, (-s, 0, 0))
                if loc is None:
                    continue
                M = frame_matrix(loc, nrm, up=(0, 0, 1))
                g = names[gi % len(names)]
                gi += 1
                for gob in core.glyph(B, f"Hieroglyphe_{gi}", HIEROGLYPHS[g], 0.95, M, bvh, role="or", width=0.045):
                    core.weight_fn(gob, bw)

        # ailerons
        for k, th in enumerate((0.0, math.pi / 2, math.pi, 3 * math.pi / 2)):
            d = Vector((math.sin(th), 0, math.cos(th)))
            base = Vector((0, -4.7, ZC)) + d * 0.6
            tip = Vector((0, -6.0, ZC)) + d * (3.9 if k != 2 else 3.2)
            pathf = core.spline([base, base.lerp(tip, 0.5) + Vector((0, -0.2, 0)), tip], 12)
            radii = [0.0] + [1.4 * (1 - 0.6 * i / 11) * math.sin(math.pi * min(1.0, (11 - i) / 3.0) / 2) ** 0.5
                             for i in range(1, 11)] + [0.0]
            fin = B.sweep(f"Aileron_{k}", pathf, radii, ["corps2", "or"], nseg=8, section=core.ellipse(1.0, 0.15),
                          up=(0, 1, 0), mat_fn=lambda i, j, th_, t: 1 if i >= 8 else 0)
            core.weight_all(fin, "Env_Back")

        # hélices : grande hélice arrière + 2 nacelles-moteurs latérales
        def propeller(name, center, radius, nblades, bone, role="sable"):
            c = Vector(center)
            core.weight_all(B.sphere(name + "_Moyeu", c, (radius * 0.22, radius * 0.18, radius * 0.22), "or", 10, 6), bone)
            for k in range(nblades):
                a = TAU * k / nblades
                d = Vector((math.sin(a), 0, math.cos(a)))
                pth = core.spline([c + d * radius * 0.12, c + d * radius], 7)
                rr = [0.0] + [radius * 0.24 * math.sin(math.pi * (i / 6) ** 0.8) for i in range(1, 6)] + [0.0]
                core.weight_all(B.sweep(f"{name}_Pale_{k}", pth, rr, [role], nseg=4, section=core.ellipse(1.0, 0.18),
                                        up=(math.cos(a) * 0.6, 0.8, -math.sin(a) * 0.6), twist=0.5), bone)
        core.weight_all(B.cone("Helice_Axe", frame_matrix((0, Y0 + 0.1, ZC), (0, -1, 0)), 0.25, 0.16, 0.6, "cuir",
                               seg=12), "Env_Back")
        propeller("Helice_Arriere", (0, Y0 - 0.45, ZC), 1.55, 4, "Prop_T")
        for s, bone in PODS:
            px, py, pz = s * 3.05, -1.0, ZC - 0.7
            pod = B.tube(f"Nacelle_Moteur_{s}", [(px, py + 0.9, pz), (px, py - 0.85, pz)], 0.45, "corps2", n=6,
                         nseg=8, ncap=3, rfn=lambda t: 1.0 - 0.25 * t,
                         roles=["corps2", "or"], mat_fn=lambda i, j, th, t: 1 if 2 <= i <= 3 else 0)
            core.weight_all(pod, "Envelope")
            strut = B.tube(f"Mat_Moteur_{s}", [(px - s * 0.3, py, pz + 0.1), (s * 1.9, py, ZC - 0.2)], 0.12, "or", n=4,
                           nseg=6)
            core.weight_all(strut, "Envelope")
            propeller(f"Helice_{s}", (px, -2.05, pz), 0.95, 3, bone)

        # île de sable sur le dos
        isl = B.sphere("Ile", ISLAND_C, (2.05, 3.7, 0.62), "sable", 24, 8)
        core.weight_all(isl, "Island")
        ibvh = core.bvh_of([isl])

        def on_island(x, y):
            loc, nrm = surface(ibvh, (x, y, ZC + 8), (0, 0, -1))
            return loc, nrm
        for k, y in enumerate((-2.6, -1.0, 2.2)):
            pts = []
            for i in range(9):
                x = -1.6 + 3.2 * i / 8
                loc, _ = on_island(x, y + 0.18 * math.sin(i * 1.3 + k))
                if loc is not None:
                    pts.append(loc + Vector((0, 0, 0.01)))
            if len(pts) > 3:
                core.weight_all(B.tube(f"Dune_{k}", pts, 0.045, "ocre", n=10, nseg=4), "Island")
        # bassin gonflable
        loc, _ = on_island(*POND)
        pc = loc + Vector((0, 0, 0.12))
        core.weight_all(B.ring("Bassin_Boudin", pc, 0.85, 0.16, "or", nseg=5, n=20), "Island")
        core.weight_all(B.sphere("Bassin_Eau", pc + Vector((0, 0, -0.02)), (0.82, 0.82, 0.1), "turquoise", 16, 4),
                        "Island")
        core.weight_all(B.ring("Bassin_Liseré", pc + Vector((0, 0, 0.1)), 0.85, 0.05, "turquoise", nseg=4, n=24),
                        "Island")
        # palmiers gonflables
        for k, (x, y) in enumerate(PALMS):
            base, _ = on_island(x, y)
            top = palm_top(k)
            ctrl = [base - Vector((0, 0, 0.2)), base.lerp(top, 0.45) + Vector((0.25 if k != 1 else -0.25, 0, 0)), top]
            pb, pt = f"Palm_{k + 1}", f"Palm_{k + 1}_Top"
            trunk = B.tube(f"Palmier_Tronc_{k}", ctrl, 0.24, "ocre", n=15, nseg=7,
                           rfn=lambda t: (1 - 0.35 * t) * (1 + 0.12 * abs(math.sin(t * math.pi * 7))),
                           roles=["ocre", "cuir"], mat_fn=lambda i, j, th, t: 1 if i % 4 == 0 else 0)
            core.weight_fn(trunk, core.gradient("z", [(base.z + 0.3, pb), (top.z - 0.4, pt)]))
            for f in range(5):
                a = TAU * f / 5 + k
                d = Vector((math.cos(a), math.sin(a), 0))
                fctrl = [top, top + d * 0.8 + Vector((0, 0, 0.45)), top + d * 1.6 + Vector((0, 0, 0.2)),
                         top + d * 2.15 + Vector((0, 0, -0.45))]
                pth = core.spline(fctrl, 9)
                rr = [0.0] + [0.38 * math.sin(math.pi * (i / 8) ** 0.7) for i in range(1, 8)] + [0.0]
                frond = B.sweep(f"Palme_{k}_{f}", pth, rr, ["fx2"], nseg=5, section=core.ellipse(0.12, 1.0),
                                up=(0, 0, 1))
                core.weight_all(frond, pt)
            for c in range(3):
                a = TAU * c / 3 + 0.5
                core.weight_all(B.sphere(f"Noix_Deco_{k}_{c}", top + Vector((math.cos(a) * 0.28, math.sin(a) * 0.28, -0.3)),
                                         (0.2, 0.2, 0.22), "cuir", 8, 5), pt)
        # buissons
        for k, (x, y) in enumerate(((1.3, -2.6), (-1.4, -0.5), (-1.2, 2.3))):
            loc, _ = on_island(x, y)
            if loc is None:
                continue
            for j in range(2):
                a = TAU * j / 2 + k
                core.weight_all(B.sphere(f"Buisson_{k}_{j}", loc + Vector((math.cos(a) * 0.25, math.sin(a) * 0.25, 0.15)),
                                         (0.32, 0.32, 0.26), "fx2", 8, 5), "Island")

        # lianes feuillues pendantes
        for k, (s, y) in enumerate(VINES):
            top, _ = surface(bvh, (s * 9, y, ZC - 1.1), (-s, 0, 0))
            if top is None:
                continue
            L = 2.4 + 0.5 * (k % 3)
            ctrl = [top + Vector((0, 0, 0.1)), top + Vector((s * 0.25, 0.2, -L * 0.35)),
                    top + Vector((s * 0.1, -0.15, -L * 0.7)), top + Vector((s * 0.2, 0.1, -L))]
            vb = f"Vine_{k + 1}"
            vw = core.gradient("z", [(top.z - 0.6, vb), (top.z - 0.1, "Envelope")])
            vine = B.tube(f"Liane_{k}", ctrl, 0.07, "fx2", n=8, nseg=4, ncap=1)
            core.weight_fn(vine, vw)
            pts = core.spline(ctrl, 3)
            for j, p in enumerate(pts[1:]):
                a = j * 2.1 + k
                d = Vector((math.cos(a), math.sin(a), -0.3)).normalized()
                pth = core.spline([p, p + d * 0.25 + Vector((0, 0, 0.08)), p + d * 0.48], 6)
                rr = [0.0] + [0.13 * math.sin(math.pi * i / 5) ** 0.8 for i in range(1, 5)] + [0.0]
                leaf = B.sweep(f"Liane_Feuille_{k}_{j}", pth, rr, ["corps2"], nseg=5, section=core.ellipse(0.15, 1.0),
                               up=(0, 0, 1))
                core.weight_fn(leaf, vw)

        # réserve d'eau suspendue
        tc = Vector((0, 0.4, ZC - 4.1))
        tank = B.sphere("Reserve_Eau", tc, (1.55, 1.15, 0.95), "turquoise", 18, 10)
        core.weight_all(tank, "Tank")
        for x in (-0.6, 0.6):
            rx = 1.15 * math.sqrt(1 - (x / 1.55) ** 2) + 0.03
            rz = 0.95 * math.sqrt(1 - (x / 1.55) ** 2) + 0.03
            pts = [Vector((x, tc.y + math.cos(a) * rx, tc.z + math.sin(a) * rz)) for a in [TAU * i / 24 for i in range(24)]]
            core.weight_all(B.sweep(f"Reserve_Cerclage_{x}", pts, [0.07] * 24, ["or"], nseg=4, up=(1, 0, 0), closed=True),
                            "Tank")
        spout = B.cone("Reserve_Robinet", frame_matrix(tc + Vector((0, 0.9, -0.55)), (0, 0.7, -0.7)), 0.16, 0.12, 0.35,
                       "or", seg=12)
        core.weight_all(spout, "Tank")
        core.weight_all(B.sphere("Reserve_Goutte", tc + Vector((0, 1.25, -1.0)), (0.1, 0.1, 0.15), "turquoise", 10, 8),
                        "Tank")
        rope_w = core.gradient("z", [(ZC - 3.4, "Tank"), (ZC - 2.6, "Envelope")])
        for sx in (-1, 1):
            for sy in (-1, 1):
                a = tc + Vector((sx * 0.9, sy * 0.6, 0.65))
                top, _ = surface(bvh, (sx * 1.3, tc.y + sy * 1.2, ZC), (0, 0, -1))
                rope = B.tube(f"Reserve_Cordage_{sx}_{sy}", [a, top + Vector((0, 0, 0.05))], 0.05, "cuir", n=4, nseg=4)
                core.weight_fn(rope, rope_w)
        loc, nrm = surface(bvh, (-9, 0.8, ZC - 1.6), (1, 0, 0))
        valve(B, loc, nrm, "Envelope", 5.0)

        self._props(B)
        return rig

    def _props(self, B):
        # noix de coco gonflables (projectiles)
        for k in range(3):
            c = self.HEAD[f"Coco_{k + 1}"]
            bone = f"Coco_{k + 1}"
            core.weight_all(B.sphere(f"Coco_{k}", c, (0.42, 0.42, 0.46), "cuir", 10, 7), bone)
            for j in range(3):
                a = TAU * j / 3
                core.weight_all(B.sphere(f"Coco_Oeil_{k}_{j}", c + Vector((math.cos(a) * 0.12, 0.38, 0.12 + math.sin(a) * 0.1)),
                                         (0.06, 0.04, 0.06), "bouche", 6, 4), bone)
            core.weight_all(B.cone(f"Coco_Valve_{k}", frame_matrix(c + Vector((0, 0, 0.44)), (0, 0, 1)), 0.08, 0.06, 0.1,
                                   "turquoise", seg=10), bone)
        # vague de sable : rouleau élancé, lèvre de crête enroulée vers l'avant, écume de sable
        xs = [-4.8 + 9.6 * i / 15 for i in range(16)]
        pts = [Vector((x, 4.0 + 0.09 * x * x, 0.0)) for x in xs]
        rr = [1.5 * math.sin(math.pi * i / 15) ** 0.5 for i in range(16)]
        rr[0] = rr[-1] = 0.0
        wave = B.sweep("Vague_Sable", pts, rr, ["sable", "ocre"], nseg=12,
                       section=lambda th, t: 1.0 / math.sqrt((math.cos(th) / 1.0) ** 2 + (math.sin(th) / 0.28) ** 2),
                       up=(0, -0.35, 1), mat_fn=lambda i, j, th, t: 1 if math.cos(th) > 0.6 else 0)
        core.weight_all(wave, "SandWave")
        lip = [Vector((x, 4.35 + 0.09 * x * x, 1.3 * math.sin(math.pi * i / 15) ** 0.5))
               for i, x in enumerate(xs)][2:-2]
        core.weight_all(B.tube("Vague_Levre", lip, 0.32, "ocre", n=12, nseg=6,
                               rfn=lambda t: math.sin(math.pi * t) ** 0.4 + 0.1), "SandWave")
        for i in range(2, 12, 2):
            c = lip[i - 2] + Vector((0, 0.3, 0.12))
            core.weight_all(B.sphere(f"Vague_Ecume_{i}", c, (0.26, 0.26, 0.22), "sable", 8, 5), "SandWave")
        # tornades
        for k, (x, y) in enumerate(TORNADOES):
            pth = [Vector((x + 0.3 * math.sin(i * 0.9), y, 5.8 * i / 13)) for i in range(14)]
            pth[-1] = Vector((pth[-2].x, y, 5.0))           # sommet en entonnoir (creux)
            rr = [0.0] + [0.15 + 1.35 * (i / 12) ** 1.4 for i in range(1, 13)] + [0.0]
            tor = B.sweep(f"Tornade_{k}", pth, rr, ["sable", "ocre"], nseg=10, section=gores(5, 0.3), up=(0, 1, 0),
                          twist=9.0, mat_fn=lambda i, j, th, t: 1 if (j + i) % 6 < 2 else 0)
            core.weight_all(tor, f"Tornado_{k + 1}")
        # cactus gonflables qui surgissent du sol
        for k, (x, y) in enumerate(CACTI):
            bone = f"Cactus_{k + 1}"
            path = [Vector((x, y, 1.6 * i / 9)) for i in range(10)]
            rr = [0.33 * core.dome(i / 9, 0.08, 0.35) for i in range(10)]
            core.weight_all(B.sweep(f"Mini_Cactus_{k}", path, rr, ["corps"], nseg=12, section=gores(6, 0.12),
                                    up=(0, 1, 0)), bone)
            for s in (-1, 1):
                core.weight_all(B.tube(f"Mini_Cactus_Bras_{k}_{s}", [(x, y, 0.75 + 0.1 * s), (x + s * 0.5, y, 0.75 + 0.1 * s),
                                                                    (x + s * 0.55, y, 1.15 + 0.1 * s)], 0.1, "corps",
                                       n=5, nseg=6, ncap=2), bone)
                core.weight_all(B.sphere(f"Mini_Cactus_Oeil_{k}_{s}", (x + s * 0.13, y + 0.3, 1.15), (0.08, 0.05, 0.1),
                                         "oeil", 8, 5), bone)
                core.weight_all(B.sphere(f"Mini_Cactus_Pupille_{k}_{s}", (x + s * 0.12, y + 0.345, 1.13),
                                         (0.04, 0.03, 0.05), "pupille", 6, 4), bone)
            core.weight_all(B.ring(f"Mini_Cactus_Sable_{k}", (x, y, 0.04), 0.42, 0.1, "sable", nseg=4, n=12), bone)

    # ------------------------------------------------------------------ shape keys
    def deflate(self, co):
        if abs(co.x) < 1.3 and -3.5 < co.y < -1.9 and co.z < 4.85:   # ficelles
            return co
        if co.z < ZC - 3.0 or (co.z < 6.0 and abs(co.x) < 6 and co.y > 3.0):  # réserve, accessoires
            return co
        w = core.wrinkle(co, 0.25)
        dz = co.z - ZC
        ny = co.y / 6.5
        return Vector((co.x * (0.6 + 0.1 * w), co.y * 0.85, ZC + dz * (0.45 + 0.06 * w) - 1.4 * ny * ny - 0.6))

    def inflate(self, co):
        if co.z < ZC - 3.0 or co.z < 6.0:
            return co
        return Vector((co.x * 1.05, co.y * 1.02, ZC + (co.z - ZC) * 1.05))

    # ------------------------------------------------------------------ animations
    def legacy_actions(self):
        return [("Idle", 90, self.idle, True), ("Move", 60, self.move, True), ("Attack", 60, self.attack, False),
                ("Hit", 24, self.hit, False), ("Death", 120, self.death, False),
                ("Attack_SandWave", 90, self.sandwave, False), ("Attack_Coconuts", 90, self.coconuts, False),
                ("Attack_Tornado", 110, self.tornado, False), ("Attack_CactusSpawn", 90, self.cactus, False)]

    def props(self, p, show=()):
        """Accessoires cachés (échelle ~0, repliés dans le ballon) sauf ceux listés dans show."""
        for name in ["SandWave"] + [f"Tornado_{k + 1}" for k in range(2)] + [f"Cactus_{k + 1}" for k in range(3)]:
            if name not in show:
                h = self.HEAD[name]
                p.add(name, loc=(-h.x, -h.y, ZC - h.z), scl=HIDDEN)
        for k in range(3):
            if f"Coco_{k + 1}" not in show:
                p.add(f"Coco_{k + 1}", scl=HIDDEN)
        return p

    def ambient(self, p, t, n, speed=1.0, sway=1.0, loop=False):
        """Mouvements secondaires : hélices, palmiers, lianes, réserve d'eau.
        speed : facteur constant ou fonction du temps (intégrée : l'hélice ne recule jamais).
        Boucles : nombre de tours entier par cycle."""
        w = TAU * t / n
        for bone, base in [("Prop_T", 3.0)] + [(b, 4.0) for _, b in PODS]:
            if callable(speed):
                steps = max(1, int(t * 2))
                turns = sum(speed(t * (i + 0.5) / steps) for i in range(steps)) * (t / steps) * base / 90.0
                ang = -TAU * turns
            elif loop:
                ang = -TAU * max(1, round(base * speed * n / 90.0)) * t / n
            else:
                ang = -TAU * base * speed * t / 90.0
            p.add(bone, rot=(0, ang, 0))
        for k in range(3):
            p.add(f"Palm_{k + 1}", rot=(0.05 * sway * math.sin(w + k), 0.05 * sway * math.sin(w + 1.3 * k), 0))
            p.add(f"Palm_{k + 1}_Top", rot=(0.08 * sway * math.sin(w + k - 1.0), 0.08 * sway * math.sin(w + k - 0.4),
                                             0.06 * sway * math.sin(w + k)))
        for k in range(len(VINES)):
            p.add(f"Vine_{k + 1}", rot=(0.07 * sway * math.sin(w + k * 0.9), 0.05 * sway * math.sin(w + k * 1.7), 0))
        p.add("Tank", rot=(0.04 * sway * math.sin(w - 1.2), 0.04 * sway * math.sin(w - 0.5), 0))
        return p

    def idle(self, t):
        p = self.props(Pose())
        w = TAU * t / 90
        p.add("Hover", loc=(0.1 * math.sin(w + 1), 0, 0.3 * math.sin(w)),
              rot=(0.025 * math.sin(w + 1.0), 0.035 * math.sin(w), 0.015 * math.sin(w + 2)))
        p.add("Envelope", scl=vol(1 + 0.015 * math.sin(2 * w), "y"))
        p.add("Env_Front", rot=(0.02 * math.sin(w - 0.8), 0, 0.015 * math.sin(w)))
        p.add("Env_Back", rot=(0.02 * math.sin(w - 1.6), 0, 0.02 * math.sin(w - 1)))
        p.add("Island", rot=(0.01 * math.sin(w - 1.5), 0.015 * math.sin(w - 0.7), 0))
        self.ambient(p, t, 90, loop=True)
        p.shape("Gonfle", 0.15 + 0.15 * math.sin(2 * w))
        return fx_layer(p, t, 90, "idle")

    def move(self, t):
        p = self.props(Pose())
        w = TAU * t / 60
        p.add("Hover", loc=(0, 0, 0.2 * math.sin(2 * w)), rot=(-0.08 + 0.02 * math.sin(2 * w), 0.04 * math.sin(w), 0))
        p.add("Envelope", scl=vol(1.03 + 0.015 * math.sin(2 * w), "y"))
        p.add("Env_Front", scl=vol(0.96, "y"))
        p.add("Env_Back", rot=(0.03 * math.sin(2 * w - 1), 0, 0.03 * math.sin(w)))
        self.ambient(p, t, 60, speed=2.0, sway=1.4, loop=True)
        for k in range(3):
            p.add(f"Palm_{k + 1}", rot=(0.1, 0, 0))
        for k in range(len(VINES)):
            p.add(f"Vine_{k + 1}", rot=(-0.18, 0, 0))
        p.add("Tank", rot=(-0.1, 0, 0))
        p.shape("Gonfle", 0.1)
        return fx_layer(p, t, 60, "move")

    def attack(self, t):
        """Charge éperon : recul et gonflement, ruée nez en avant, impact écrasé, rebond."""
        p = self.props(Pose())
        y = K((0, 0.0), (16, -1.2), (24, 3.0), (28, 3.3), (36, 1.8), (46, 0.4), (60, 0.0))(t)
        z = K((0, 0.0), (16, 0.4), (24, -0.6), (28, -0.7), (36, 0.3), (46, 0.0), (60, 0.0))(t)
        rx = K((0, 0.0), (16, 0.14), (24, -0.16), (28, -0.12), (36, 0.08), (46, -0.02), (60, 0.0))(t)
        p.add("Hover", loc=(0, y, z), rot=(rx, 0, 0))
        p.add("Envelope", scl=vol(K((0, 1.0), (16, 0.86), (23, 1.15), (26, 1.12), (29, 0.84), (36, 1.06), (46, 0.98),
                                    (60, 1.0))(t), "y"))
        p.add("Env_Front", scl=vol(K((0, 1.0), (26, 1.0), (29, 0.7), (36, 1.05), (44, 1.0))(t), "y"),
              rot=(damp(t, 28, 0.06, 1.0, 7), 0, 0))
        self.ambient(p, t, 60, speed=K((0, 1.0), (16, 0.5), (26, 4.0), (60, 2.5)), sway=1.0)
        whip = K((0, 0.0), (16, 0.2), (24, 0.25), (29, -0.45), (36, 0.2), (46, -0.05), (60, 0.0))(t)
        for k in range(3):
            p.add(f"Palm_{k + 1}", rot=(whip, 0, 0))
            p.add(f"Palm_{k + 1}_Top", rot=(whip * 1.3, 0, 0))
        for k in range(len(VINES)):
            p.add(f"Vine_{k + 1}", rot=(whip * 1.2, 0, 0))
        p.add("Tank", rot=(whip * 0.8, 0, 0))
        p.shape("Gonfle", K((0, 0.0), (16, 0.9), (24, 0.3), (29, 0.0), (60, 0.0))(t))
        return fx_layer(p, t, 60, "attack")

    def hit(self, t):
        p = self.props(Pose())
        decay = math.exp(-t / 6)
        p.add("Hover", loc=(jitter(t * 3, 0.15) * decay, K((0, 0.0), (4, -0.8), (11, -0.45), (24, 0.0))(t),
                            K((0, 0.0), (4, 0.2), (24, 0.0))(t)),
              rot=(K((0, 0.0), (4, 0.14), (10, -0.04), (16, 0.02), (24, 0.0))(t), damp(t, 1, 0.06, 1.6, 5),
                   damp(t, 1, 0.04, 2.0, 5)))
        p.add("Envelope", scl=vol(K((0, 1.0), (4, 0.86), (9, 1.06), (14, 0.97), (24, 1.0))(t), "y"))
        p.add("Env_Front", scl=vol(K((0, 1.0), (4, 0.8), (10, 1.04), (24, 1.0))(t), "y"))
        self.ambient(p, t, 24, speed=0.4, sway=0.5)
        for k in range(3):
            p.add(f"Palm_{k + 1}_Top", rot=(damp(t, 2, 0.35, 1.2, 6), damp(t, 2, 0.2, 1.5, 6), 0))
        p.add("Tank", rot=(damp(t, 2, -0.25, 0.8, 8), 0, 0))
        p.shape("Gonfle", K((0, 0.0), (4, 0.0), (9, 0.5), (24, 0.0))(t))
        return fx_layer(p, t, 24, "hit")

    def death(self, t):
        """Crevaison géante : l'oasis se vide, tournoie, s'écrase au sol en se ratatinant, puis disparaît."""
        p = self.props(Pose())
        d = K((0, 0.0), (12, 0.0), (90, 1.0))(t)
        p.shape("Degonfle", d)
        p.add("Hover", loc=(0.6 * math.sin(t * 0.12) * d, -0.5 * d, K((0, 0.0), (12, 0.3), (30, 0.5), (92, -5.6),
                                                                       (98, -5.2), (104, -5.6))(t)),
              rot=(K((0, 0.0), (6, 0.12), (14, 0.0), (92, -0.2))(t) + jitter(t * 0.5, 0.04 * d),
                   jitter(t * 0.5 + 2, 0.05 * d) + 0.2 * d, K((12, 0.0), (92, 1.6))(t)))
        p.add("Envelope", scl=(1.0, K((0, 1.0), (6, 0.9), (12, 1.04), (90, 0.88))(t), 1.0))
        p.add("Env_Front", rot=(-0.3 * d + jitter(t * 0.5, 0.04 * d), 0, 0.15 * d))
        p.add("Env_Back", rot=(0.25 * d, 0, -0.2 * d))
        self.ambient(p, t, 120, speed=K((0, 1.0), (40, 0.5), (90, 0.1)), sway=1.0 + d)
        for k in range(3):
            p.add(f"Palm_{k + 1}", rot=(0.5 * d * (1 if k % 2 else -1), 0.6 * d, 0))
            p.add(f"Palm_{k + 1}_Top", rot=(0.4 * d, 0, 0), scl=1 - 0.3 * d)
        for k in range(len(VINES)):
            p.add(f"Vine_{k + 1}", rot=(0.5 * d * math.sin(k), 0.4 * d, 0))
        p.add("Tank", scl=(1 + 0.2 * d, 1 + 0.2 * d, 1 - 0.4 * d))
        p.add("Root", scl=K((0, 1.0), (104, 1.0), (120, 0.001))(t))
        return fx_layer(p, t, 120, "death")

    def _slam(self, p, t, t0):
        """Le boss se cabre puis frappe l'air vers le sol (appel d'attaque)."""
        p.add("Hover", loc=(0, K((0, 0.0), (t0 - 10, -0.6), (t0, 0.8), (t0 + 20, 0.0))(t),
                            K((0, 0.0), (t0 - 10, 0.8), (t0, -0.8), (t0 + 20, 0.0))(t)),
              rot=(K((0, 0.0), (t0 - 10, 0.15), (t0, -0.12), (t0 + 20, 0.0))(t), 0, 0))
        p.add("Envelope", scl=vol(K((0, 1.0), (t0 - 10, 0.9), (t0 - 2, 1.08), (t0 + 2, 0.92), (t0 + 12, 1.0))(t), "z"))
        p.shape("Gonfle", K((0, 0.0), (t0 - 10, 0.9), (t0, 0.0))(t))

    def _visible(self, t, a, b):
        return a - 4 <= t <= b + 4

    def sandwave(self, t):
        """Projection d'une vague de sable qui déferle vers l'avant."""
        show = ["SandWave"] if self._visible(t, 24, 84) else []
        p = self.props(Pose(), show)
        w = TAU * t / 90
        p.add("Hover", loc=(0, 0, 0.2 * math.sin(w)))
        self._slam(p, t, 26)
        if show:
            p.add("SandWave", loc=(0, K((0, 0.0), (26, 0.0), (78, 9.0))(t), K((0, -0.6), (24, -0.6), (32, 0.0))(t)),
                  rot=(0.12 * math.sin(t * 0.4), 0, 0.03 * math.sin(t * 0.3)),
                  scl=K((0, HIDDEN), (24, HIDDEN), (32, 1.0), (60, 1.25), (78, 1.4), (84, HIDDEN))(t))
        self.ambient(p, t, 90, speed=2.0, sway=1.5)
        return fx_layer(p, t, 90, "attack")

    def coconuts(self, t):
        """Les palmiers se tendent puis lancent 3 noix de coco gonflables en cloche vers l'avant."""
        show = [f"Coco_{k + 1}" for k in range(3) if self._visible(t, 14, 84)]
        p = self.props(Pose(), show)
        w = TAU * t / 90
        p.add("Hover", loc=(0, 0, 0.2 * math.sin(w)), rot=(K((0, 0.0), (18, 0.08), (26, -0.08), (40, 0.0))(t), 0, 0))
        self.ambient(p, t, 90)
        bend = K((0, 0.0), (20, 0.45), (26, -0.6), (34, 0.2), (44, -0.05), (54, 0.0))(t)
        for k in range(3):
            p.add(f"Palm_{k + 1}", rot=(bend * 0.6, 0, 0))
            p.add(f"Palm_{k + 1}_Top", rot=(bend, 0, 0))
        for k in range(3):
            if f"Coco_{k + 1}" not in show:
                continue
            h = self.HEAD[f"Coco_{k + 1}"]
            tx, ty = COCO_TARGETS[k]
            t0 = 26 + 3 * k
            s = min(max((t - t0) / 20.0, 0.0), 1.0)
            bounce = 0.0
            if t > t0 + 20:
                x = (t - t0 - 20) / 12.0
                bounce = 1.6 * max(0.0, math.sin(math.pi * min(x, 1.0))) * (1 if x < 1 else 0)
            delta = Vector((tx - h.x, ty - h.y, 0.45 - h.z))
            loc = delta * s + Vector((0, 0, 6.0 * 4 * s * (1 - s) + bounce))
            p.add(f"Coco_{k + 1}", loc=tuple(loc), rot=(-0.5 * s * 6, 0, 0),
                  scl=K((0, HIDDEN), (14, HIDDEN), (20, 1.0), (76, 1.0), (84, HIDDEN))(t))
        return fx_layer(p, t, 90, "attack")

    def tornado(self, t):
        """Les hélices s'emballent et soulèvent deux tornades de sable qui avancent en serpentant."""
        show = [f"Tornado_{k + 1}" for k in range(2)] if self._visible(t, 18, 104) else []
        p = self.props(Pose(), show)
        w = TAU * t / 110
        p.add("Hover", loc=(0, 0, 0.6 * math.sin(w)), rot=(K((0, 0.0), (15, 0.12), (95, 0.12), (110, 0.0))(t),
                                                         0.05 * math.sin(2 * w), 0))
        self.ambient(p, t, 110, speed=K((0, 1.0), (15, 6.0), (95, 6.0), (110, 2.0)), sway=2.0)
        for k in range(len(show)):
            sgn = -1 if k == 0 else 1
            p.add(f"Tornado_{k + 1}",
                  loc=(sgn * -0.8 * math.sin(t * 0.08) + 0.0, K((0, 0.0), (20, 0.0), (100, 5.0))(t), 0),
                  rot=(0.06 * math.sin(t * 0.3), 0.06 * math.cos(t * 0.27), -TAU * 5 * t / 110),
                  scl=K((0, HIDDEN), (18, HIDDEN), (36, 1.0), (92, 1.1), (104, HIDDEN))(t))
        p.shape("Gonfle", 0.4 * K((0, 0.0), (15, 1.0), (95, 1.0), (110, 0.0))(t))
        return fx_layer(p, t, 110, "attack")

    def cactus(self, t):
        """Frappe d'appel : trois cactus gonflables jaillissent du sol sous le joueur puis s'enfoncent."""
        show = [f"Cactus_{k + 1}" for k in range(3) if self._visible(t, 22 + 5 * k, 82)]
        p = self.props(Pose(), show)
        self._slam(p, t, 22)
        self.ambient(p, t, 90, speed=1.5, sway=1.2)
        for k in range(3):
            name = f"Cactus_{k + 1}"
            if name not in show:
                continue
            t0 = 24 + 5 * k
            z = K((0, -1.7), (t0, -1.7), (t0 + 5, 0.25), (t0 + 9, -0.08), (t0 + 13, 0.0), (68, 0.0), (80, -1.7))(t)
            sq = K((0, 1.0), (t0 + 5, 1.25), (t0 + 9, 0.85), (t0 + 13, 1.0))(t)
            p.add(name, loc=(0, 0, z), rot=(0.12 * math.sin(t * 0.5 + k), 0.12 * math.sin(t * 0.45 + 2 * k), 0),
                  scl=tuple(a * K((0, HIDDEN), (t0 - 1, HIDDEN), (t0 + 3, 1.0), (72, 1.0), (82, HIDDEN))(t)
                            for a in vol(sq)))
        return fx_layer(p, t, 90, "attack")


FAMILY = Oasis()
