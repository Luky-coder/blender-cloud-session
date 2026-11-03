"""FAMILLE C - DIRIGEABLE DU DÉSERT (PV 55).

Petit dirigeable-jouet gonflable : enveloppe allongée à 8 fuseaux cousus, bandes de tissu désertique
(rayures et losanges berbères), visage sur le nez, 4 ailerons gonflables, hélice arrière dorée, nacelle
gonflable tressée suspendue par 4 cordages, sacs de sable, longue-vue d'explorateur et fanion.
Longueur ~2,9 m, vol stationnaire à 1,5 m (centre de l'enveloppe), avant vers +Y, pivot au sol.
"""
import math

from mathutils import Vector

from . import core
from .core import TAU, K, Pose, damp, frame_matrix, gores, jitter, surface, vol
from .family import Family, fx_layer, valve

ZC = 1.5               # hauteur du centre de l'enveloppe
Y0, Y1 = -1.3, 1.25    # queue / nez
RMAX = 0.55
GORE = gores(8, 0.05, phase=0.0, sharp=0.7)


def env_r(t):
    tp = 1 - (1 - t) ** 0.8
    return RMAX * max(0.0, math.sin(math.pi * tp)) ** 0.6


def env_point(t, th, lift=0.0):
    r = env_r(t) * GORE(th, t) + lift
    return Vector((math.sin(th) * r, Y0 + (Y1 - Y0) * t, ZC + math.cos(th) * r))


BANDS = [  # (t0, t1, rôle) : tissus rayés du désert
    (0.10, 0.125, "sable"), (0.125, 0.17, "corps2"), (0.17, 0.195, "sable"),
    (0.30, 0.325, "sable"), (0.325, 0.405, "corps2"), (0.405, 0.43, "sable"),
    (0.70, 0.725, "sable"), (0.725, 0.775, "corps2"), (0.775, 0.80, "sable")]
SLOTS = ["corps", "corps2", "sable", "ocre"]


class Airship(Family):
    key = "Dirigeable_Desert"
    short = "Dirigeable"
    label = "Dirigeable du Désert"
    pv = 55
    surface_parts = ("Enveloppe",)
    crown = dict(loc=(0, 0.15, ZC + RMAX - 0.03), size=0.32)
    aura = dict(center=(0, -0.45, ZC), radius=0.88, axis=(0, 1, 0), count=6, size=0.14, phase=0.3)
    emblems = (((-2, 0.45, ZC + 0.12), (1, 0, 0), 0.3), ((2, 0.45, ZC + 0.12), (-1, 0, 0), 0.3))
    face_frame = dict(center=(0, 0, ZC))
    face_params = dict(eye_r=0.1, eye_dx=0.17, eye_v=0.11, mouth_v=-0.17, mouth_w=0.24, mouth_h=0.085, brow_w=0.17)
    face_bone = "Env_Front"
    strings = (dict(parent="Envelope", hang=True, dir=(0, 0, -1), r=0.013,
                    path=[(0, -0.62, 1.11), (0.02, -0.66, 0.8), (-0.03, -0.7, 0.5), (0.02, -0.74, 0.2)]),)
    anim_frames = {"Idle": (1,), "Move": (8,), "Attack": (10, 15, 18), "Hit": (4,), "Death": (30, 50, 64)}
    anim_pad_forward = 0.2

    BONES = [("Root", (0, 0, 0), None), ("Hover", (0, 0, ZC), "Root"), ("Envelope", (0, 0, ZC), "Hover"),
             ("Env_Front", (0, 0.7, ZC), "Envelope"), ("Env_Back", (0, -0.7, ZC), "Envelope"),
             ("Prop", (0, -1.45, ZC), "Env_Back"), ("Gondola", (0, 0, ZC - 0.5), "Hover"),
             ("FX", (0, 0.15, ZC + RMAX), "Envelope"), ("Aura", (0, -0.45, ZC), "Hover")]

    def body_weight(self, co):
        return core.gradient("y", [(-0.9, "Env_Back"), (-0.2, "Envelope"), (0.25, "Envelope"),
                                   (0.85, "Env_Front")])(co)

    # ------------------------------------------------------------------ géométrie de référence
    def build(self, B):
        rig = core.make_rig("REF_" + self.key, self.rig_bones(), B.coll)
        bw = self.body_weight
        n = 52
        ts = [0.5 * (i / (n - 1)) + 0.5 * (1 - math.cos(math.pi * i / (n - 1))) / 2 for i in range(n)]
        path = [Vector((0, Y0 + (Y1 - Y0) * t, ZC)) for t in ts]

        def mat(i, j, th, t):
            tm = (ts[i] + ts[min(i + 1, n - 1)]) / 2
            for a, b, role in BANDS:
                if a <= tm < b:
                    if role == "corps2" and (b - a) > 0.06:  # losanges berbères
                        x = abs(((th * 8 / TAU) % 1.0) - 0.5) * 2
                        if x * 0.035 + abs(tm - (a + b) / 2) < 0.03:
                            return 3
                    return SLOTS.index(role)
            return 0
        env = B.sweep("Enveloppe", path, [env_r(t) for t in ts], SLOTS, nseg=48, section=GORE, up=(0, 0, 1),
                      mat_fn=mat)
        core.weight_fn(env, bw)
        bvh = core.bvh_of([env])

        # coutures des fuseaux (arrêtées avant le nez/visage)
        for k in range(8):
            th = TAU * k / 8
            pts = [env_point(0.03 + 0.77 * i / 17, th, 0.002) for i in range(18)]
            o = B.tube(f"Couture_{k}", pts, 0.007, "couture", n=18, nseg=4, ncap=1)
            core.weight_fn(o, bw)

        # ailerons gonflables (en +)
        for k, th in enumerate((0.0, math.pi / 2, math.pi, 3 * math.pi / 2)):
            d = Vector((math.sin(th), 0, math.cos(th)))
            base = Vector((0, -0.92, ZC)) + d * 0.12
            tip = Vector((0, -1.12, ZC)) + d * (0.86 if k != 2 else 0.72)
            ctrl = [base, base.lerp(tip, 0.5) + Vector((0, -0.04, 0)), tip]
            pathf = core.spline(ctrl, 12)
            radii = [0.0] + [0.3 * (1 - 0.6 * i / 11) * math.sin(math.pi * min(1.0, (11 - i) / 3.0) / 2) ** 0.5
                             for i in range(1, 11)] + [0.0]
            fin = B.sweep(f"Aileron_{k}", pathf, radii, ["corps2", "ocre"], nseg=12, section=core.ellipse(1.0, 0.17),
                          up=(0, 1, 0), mat_fn=lambda i, j, th_, t: 1 if i >= 8 else 0)
            core.weight_all(fin, "Env_Back")

        # hélice arrière
        shaft = B.cone("Helice_Axe", frame_matrix((0, -1.26, ZC), (0, -1, 0)), 0.05, 0.035, 0.18, "cuir", seg=12)
        core.weight_all(shaft, "Env_Back")
        hub = B.sphere("Helice_Moyeu", (0, -1.46, ZC), (0.075, 0.06, 0.075), "or", 10, 6)
        core.weight_all(hub, "Prop")
        for k in range(3):
            a = TAU * k / 3
            d = Vector((math.sin(a), 0, math.cos(a)))
            ctrl = [Vector((0, -1.46, ZC)) + d * 0.04, Vector((0, -1.46, ZC)) + d * 0.36]
            pth = core.spline(ctrl, 9)
            rr = [0.0] + [0.075 * math.sin(math.pi * (i / 8) ** 0.8) for i in range(1, 8)] + [0.0]
            blade = B.sweep(f"Helice_Pale_{k}", pth, rr, ["sable"], nseg=8, section=core.ellipse(1.0, 0.18),
                            up=(math.cos(a) * 0.6, 0.8, -math.sin(a) * 0.6), twist=0.5)
            core.weight_all(blade, "Prop")

        # nacelle gonflable tressée
        gz = 0.8

        def gsec(th, t):
            c, s = abs(math.cos(th)), abs(math.sin(th))
            return 1.0 / ((c ** 4 / 0.62 ** 4 + s ** 4) ** 0.25)
        gp = [Vector((0, -0.38 + 0.76 * i / 13, gz)) for i in range(14)]
        gr = [0.21 * core.dome(i / 13, 0.18, 0.18, 0.5, 0.5) for i in range(14)]
        gond = B.sweep("Nacelle", gp, gr, ["cuir", "ocre"], nseg=16, section=gsec, up=(0, 0, 1),
                       mat_fn=lambda i, j, th, t: 1 if (i + j) % 4 == 0 else 0)
        core.weight_all(gond, "Gondola")
        rim_pts = [Vector((math.sin(a) * 0.19 * (1.1 if abs(math.sin(a)) > 0.9 else 1.0), math.cos(a) * 0.36,
                           gz + 0.12)) for a in [TAU * k / 24 for k in range(24)]]
        rim = B.sweep("Nacelle_Boudin", rim_pts, [0.035] * 24, ["sable"], nseg=6, up=(0, 0, 1), closed=True)
        core.weight_all(rim, "Gondola")
        rope_w = core.gradient("z", [(0.95, "Gondola"), (1.03, "Envelope")])
        for sx in (-1, 1):
            for sy in (-1, 1):
                a = Vector((sx * 0.15, sy * 0.28, gz + 0.13))
                top, _ = surface(bvh, Vector((sx * 0.22, sy * 0.42, ZC)), (0, 0, -1))
                if top is None:
                    top = Vector((sx * 0.22, sy * 0.42, ZC - 0.45))
                rope = B.tube(f"Cordage_{sx}_{sy}", [a, top + Vector((0, 0, 0.02))], 0.012, "cuir", n=4, nseg=4)
                core.weight_fn(rope, rope_w)
        for sx in (-1, 1):
            bag = B.sphere(f"Sac_Sable_{sx}", (sx * 0.24, -0.12, gz - 0.06), (0.075, 0.07, 0.095), "sable", 10, 6)
            tie = B.ring(f"Sac_Lien_{sx}", (sx * 0.24, -0.12, gz + 0.02), 0.035, 0.01, "cuir", nseg=6, n=12)
            core.weight_all(bag, "Gondola")
            core.weight_all(tie, "Gondola")
        # longue-vue d'explorateur et fanion
        scope = B.tube("Longue_Vue", [(0.07, 0.3, gz + 0.12), (0.1, 0.62, gz + 0.22)], 0.035, "or", n=5, nseg=8,
                       rfn=lambda t: 0.8 + 0.4 * t)
        lens = B.ring("Longue_Vue_Bague", (0.1, 0.6, gz + 0.215), 0.045, 0.012, "turquoise", axis=(0.09, 0.95, 0.3),
                      nseg=6, n=14)
        pole = B.tube("Fanion_Mat", [(0, -0.33, gz + 0.1), (0, -0.36, gz + 0.48)], 0.012, "cuir", n=4, nseg=6)
        flag = B.prism("Fanion", [(0, 0), (0.0, 0.14), (-0.22, 0.07)], 0.012, "turquoise",
                       M=frame_matrix((0.006, -0.36, gz + 0.32), (1, 0, 0), up=(0, 0, 1)))
        for o in (scope, lens, pole, flag):
            core.weight_all(o, "Gondola")

        # valve (flanc gauche, -X)
        loc, nrm = surface(bvh, (-2, -0.45, ZC - 0.12), (1, 0, 0))
        valve(B, loc, nrm, "Envelope", 1.6)
        return rig

    # ------------------------------------------------------------------ shape keys
    def deflate(self, co):
        f = core.ease((co.z - 0.92) / 0.15)       # l'enveloppe se vide, la nacelle reste
        if f <= 0:
            return co
        w = core.wrinkle(co, 0.9)
        dz = co.z - ZC
        ny = co.y / 1.3
        new = Vector((co.x * (0.55 + 0.1 * w), co.y * 0.82,
                      ZC + dz * (0.45 + 0.06 * w) - 0.28 * ny * ny - 0.12))
        return co.lerp(new, f)

    def inflate(self, co):
        f = core.ease((co.z - 0.92) / 0.15)
        return Vector((co.x * (1 + 0.06 * f), co.y * (1 + 0.025 * f), ZC + (co.z - ZC) * (1 + 0.06 * f))) \
            if f > 0 else co

    # ------------------------------------------------------------------ animations
    def actions(self):
        return [("Idle", 60, self.idle, True), ("Move", 30, self.move, True), ("Attack", 40, self.attack, False),
                ("Hit", 20, self.hit, False), ("Death", 70, self.death, False)]

    def idle(self, t):
        p = Pose()
        w = TAU * t / 60
        p.add("Hover", loc=(0.02 * math.sin(w + 1), 0, 0.08 * math.sin(w)),
              rot=(0.04 * math.sin(w + 1.0), 0.05 * math.sin(w), 0.03 * math.sin(w + 2)))
        p.add("Envelope", scl=vol(1 + 0.02 * math.sin(2 * w), "y"))
        p.add("Env_Front", rot=(0.03 * math.sin(w - 0.8), 0, 0.02 * math.sin(w)))
        p.add("Env_Back", rot=(0.03 * math.sin(w - 1.6), 0, 0.03 * math.sin(w - 1)))
        p.add("Prop", rot=(0, -TAU * 4 * t / 60, 0))
        p.add("Gondola", rot=(0.06 * math.sin(w - 1.2), 0.05 * math.sin(w - 0.9), 0))
        p.shape("Gonfle", 0.15 + 0.15 * math.sin(2 * w))
        return fx_layer(p, t, 60, "idle", aura_axis=1)

    def move(self, t):
        p = Pose()
        w = TAU * t / 30
        p.add("Hover", loc=(0, 0, 0.06 * math.sin(2 * w)),
              rot=(-0.16 + 0.04 * math.sin(2 * w + 0.6), 0.06 * math.sin(w), 0.04 * math.sin(w + 1)))
        p.add("Envelope", scl=vol(1.05 + 0.02 * math.sin(2 * w), "y"))
        p.add("Env_Front", scl=vol(0.94, "y"), rot=(0.03 * math.sin(2 * w), 0, 0))
        p.add("Env_Back", rot=(0.05 * math.sin(2 * w - 1.0), 0, 0.06 * math.sin(w - 0.6)))
        p.add("Prop", rot=(0, -TAU * 4 * t / 30, 0))
        p.add("Gondola", rot=(0.05 + 0.06 * math.sin(2 * w - 1.4), 0.05 * math.sin(w - 1.0), 0))
        p.shape("Gonfle", 0.1)
        return fx_layer(p, t, 30, "move", aura_axis=1)

    def attack(self, t):
        """Charge éperon : recul et gonflement, plongée rapide nez en avant, impact écrasé, rebond."""
        p = Pose()
        y = K((0, 0.0), (10, -0.3), (15, 0.85), (18, 0.95), (24, 0.5), (31, 0.1), (40, 0.0))(t)
        z = K((0, 0.0), (10, 0.12), (15, -0.12), (18, -0.15), (24, 0.06), (32, 0.0), (40, 0.0))(t)
        rx = K((0, 0.0), (10, 0.22), (15, -0.28), (18, -0.22), (24, 0.12), (31, -0.03), (40, 0.0))(t)
        p.add("Hover", loc=(0, y, z), rot=(rx, 0, 0))
        p.add("Envelope", scl=vol(K((0, 1.0), (10, 0.86), (14, 1.2), (17, 1.15), (19, 0.8), (24, 1.08), (31, 0.97),
                                    (40, 1.0))(t), "y"))
        p.add("Env_Front", scl=vol(K((0, 1.0), (17, 1.0), (19, 0.68), (24, 1.06), (30, 1.0))(t), "y"),
              rot=(damp(t, 18, 0.1, 1.3, 5), 0, 0))
        p.add("Env_Back", rot=(K((0, 0.0), (10, -0.06), (15, 0.08), (19, -0.1), (26, 0.03), (40, 0.0))(t), 0, 0))
        p.add("Prop", rot=(0, -K((0, 0.0), (10, 2.0), (18, 16.0), (40, 26.0))(t), 0))
        p.add("Gondola", rot=(K((0, 0.0), (10, 0.25), (15, -0.35), (19, 0.3), (26, -0.12), (34, 0.04), (40, 0.0))(t),
                              0, 0))
        p.shape("Gonfle", K((0, 0.0), (10, 0.9), (15, 0.3), (19, 0.0), (40, 0.0))(t))
        return fx_layer(p, t, 40, "attack", aura_axis=1)

    def hit(self, t):
        p = Pose()
        decay = math.exp(-t / 5)
        p.add("Hover", loc=(jitter(t * 3, 0.04) * decay, K((0, 0.0), (3, -0.28), (9, -0.15), (20, 0.0))(t),
                            K((0, 0.0), (3, 0.06), (20, 0.0))(t)),
              rot=(K((0, 0.0), (3, 0.3), (8, -0.08), (13, 0.04), (20, 0.0))(t), damp(t, 1, 0.12, 1.8, 4),
                   damp(t, 1, 0.08, 2.2, 4)))
        p.add("Envelope", scl=vol(K((0, 1.0), (3, 0.84), (7, 1.08), (11, 0.96), (20, 1.0))(t), "y"))
        p.add("Env_Front", scl=vol(K((0, 1.0), (3, 0.8), (8, 1.04), (20, 1.0))(t), "y"))
        p.add("Gondola", rot=(damp(t, 1, -0.35, 1.0, 6), damp(t, 2, 0.15, 1.4, 5), 0))
        p.add("Prop", rot=(0, -K((0, 0.0), (20, 3.0))(t), 0))
        p.shape("Gonfle", K((0, 0.0), (3, 0.0), (7, 0.5), (20, 0.0))(t))
        return fx_layer(p, t, 20, "hit", aura_axis=1)

    def death(self, t):
        """Crevaison : l'air s'échappe, le dirigeable tournoie, se dégonfle, tombe au sol et disparaît."""
        p = Pose()
        d = K((0, 0.0), (8, 0.0), (50, 1.0))(t)
        p.shape("Degonfle", d)
        p.add("Hover", loc=(0.15 * math.sin(t * 0.3) * d, -0.2 * d, K((0, 0.0), (8, 0.05), (20, 0.1), (52, -1.05),
                                                                       (58, -0.95), (62, -1.05))(t)),
              rot=(K((0, 0.0), (4, 0.25), (10, 0.0), (52, -0.35))(t) + jitter(t, 0.07 * d),
                   jitter(t + 2, 0.1 * d) + 0.3 * d, K((8, 0.0), (52, 3.2))(t)))
        p.add("Envelope", scl=(1.0, K((0, 1.0), (4, 0.88), (8, 1.05), (50, 0.85))(t), 1.0))
        p.add("Env_Front", rot=(-0.35 * d + jitter(t, 0.06 * d), 0, 0.2 * d))
        p.add("Env_Back", rot=(0.3 * d, 0, -0.25 * d))
        p.add("Prop", rot=(0, -K((0, 0.0), (10, 3.0), (40, 6.0), (70, 6.5))(t), 0))
        p.add("Gondola", rot=(damp(t, 2, 0.4, 0.7, 12), 0.3 * d, 0), scl=K((0, 1.0), (50, 1.0), (60, 0.85))(t))
        p.add("Root", scl=K((0, 1.0), (56, 1.0), (70, 0.001))(t))
        return fx_layer(p, t, 70, "death", aura_axis=1)


FAMILY = Airship()
