"""FAMILLE A - BALLON CACTUS (PV 35).

Cactus-saguaro gonflable posé dans un pot gonflable en terre cuite : 8 fuseaux pincés par des coutures,
deux bras coudés, touffes d'épines arrondies sur les crêtes, bandana d'explorateur rayé, valve dorée.
Hauteur ~1,7 m (couronne élémentaire comprise), avant vers +Y, pivot au sol.
"""
import math

from mathutils import Vector

from . import core
from .core import TAU, K, Pose, damp, dome, frame_matrix, gores, jitter, surface, vol
from .family import Family, fx_layer, valve

Z0, Z1 = 0.22, 1.62   # bas / sommet du corps
NG = 8                # fuseaux : couture centrale à l'avant (theta = 0 -> +Y)
GORE = gores(NG, 0.10, phase=0.0, sharp=0.6)
POT_H = 0.36


def body_R(t):
    return (0.355 + 0.025 * math.sin(math.pi * t * 0.9)) * dome(t, t0=0.05, t1=0.24, e0=0.5, e1=0.55)


def body_point(t, th, lift=0.0):
    """Point de la surface du corps (t de 0 à 1 de bas en haut, theta = 0 vers +Y, 90° vers -X)."""
    r = body_R(t) * GORE(th, t) + lift
    return Vector((-math.sin(th) * r, math.cos(th) * r, Z0 + (Z1 - Z0) * t))


class Cactus(Family):
    key = "Ballon_Cactus"
    short = "Cactus"
    label = "Ballon Cactus"
    pv = 35
    surface_parts = ("Corps",)
    crown = dict(loc=(0, 0, 1.585), size=0.36)
    aura = dict(center=(0, 0, 1.42), radius=0.56, axis=(0, 0, 1), count=6, size=0.14, phase=0.0)
    emblems = (((-2, 0, 1.12), (1, 0, 0), 0.26), ((2, 0, 1.3), (-1, 0, 0), 0.2), ((0, -2, 1.05), (0, 1, 0), 0.3))
    face_frame = dict(center=(0, 0, 1.13))
    face_params = dict(eye_r=0.085, eye_dx=0.14, eye_v=0.1, mouth_v=-0.1, mouth_w=0.2, mouth_h=0.075,
                       brow_w=0.16)
    face_bone = "Body_Top"
    fly_from = "Idle"
    fly_lift = 0.6
    strings = (dict(parent="Body", hang=False, dir=(0, -1, -0.25), r=0.013,
                    path=[(0, -0.335, 0.07), (0.04, -0.55, 0.02), (-0.06, -0.85, 0.014), (0.05, -1.15, 0.014)]),)

    BONES = [("Root", (0, 0, 0), None), ("Body", (0, 0, 0.02), "Root"), ("Body_Mid", (0, 0, 0.72), "Body"),
             ("Body_Top", (0, 0, 1.18), "Body_Mid"), ("Arm_L", (0.36, 0, 0.64), "Body_Mid"),
             ("Arm_R", (-0.36, 0, 0.56), "Body_Mid"), ("FX", (0, 0, 1.6), "Body_Top"),
             ("Aura", (0, 0, 1.5), "Body_Top")]

    def body_weight(self, co):
        return core.gradient("z", [(0.3, "Body"), (0.75, "Body_Mid"), (1.22, "Body_Top")])(co)

    # ------------------------------------------------------------------ géométrie de référence
    def build(self, B):
        rig = core.make_rig("REF_" + self.key, self.rig_bones(), B.coll)
        bw = self.body_weight

        # Corps : 8 fuseaux gonflés
        path, ts = core.axis_path((0, 0, Z0), (0, 0, Z1), 28)
        body = B.sweep("Corps", path, [body_R(t) for t in ts], ["corps"], nseg=NG * 5, section=GORE,
                       up=(0, 1, 0))
        core.weight_fn(body, bw)
        bvh = core.bvh_of([body])

        # Coutures dans les creux (interrompues devant le visage)
        for k in range(NG):
            th = TAU * k / NG
            spans = [(0.1, 0.985)] if k else [(0.1, 0.45), (0.8, 0.985)]
            for a, b in spans:
                pts = [body_point(a + (b - a) * i / 13, th, 0.002) for i in range(14)]
                o = B.tube(f"Couture_{k}_{a}", pts, 0.0065, "couture", n=14, nseg=4, ncap=1)
                core.weight_fn(o, bw)

        # Touffes d'épines arrondies sur les crêtes
        for k in range(NG):
            thc = TAU * (k + 0.5) / NG
            front = k in (0, NG - 1)
            for zi, z in enumerate((0.55, 0.95, 1.35) if k % 2 == 0 else (0.75, 1.15)):
                if front and 0.8 < z < 1.45:
                    continue
                t = (z - Z0) / (Z1 - Z0)
                p0 = body_point(t, thc, 0.3)
                loc, n = surface(bvh, p0, body_point(t, thc) - p0)
                if loc is None:
                    continue
                self._spine_tuft(B, f"Epine_{k}_{zi}", loc, n, bw)

        # Bras coudés (côtes, bouts arrondis)
        for side, bone, ctrl, r in (
                (1, "Arm_L", [(0.2, 0, 0.64), (0.4, 0, 0.64), (0.53, 0, 0.69), (0.6, 0, 0.82), (0.61, 0, 1.0)],
                 0.115),
                (-1, "Arm_R", [(-0.2, 0, 0.56), (-0.4, 0, 0.56), (-0.52, 0, 0.61), (-0.58, 0, 0.73),
                               (-0.59, 0, 0.88)], 0.105)):
            arm = B.tube(f"Bras_{bone}", ctrl, r, "corps", n=12, nseg=18, section=gores(6, 0.1, phase=0.0),
                         up=(0, 1, 0), ncap=4)
            core.weight_all(arm, bone)
            abvh = core.bvh_of([arm])
            top = Vector(ctrl[-1])
            for i, (dz, dx, dy) in enumerate(((0.05, side * 0.3, 0.2), (-0.2, side * 0.4, -0.1))):
                target = top + Vector((0, 0, dz))
                o0 = target + Vector((dx, dy, 0)).normalized() * 0.5
                loc, n = surface(abvh, o0, target - o0)
                if loc is not None:
                    for o in self._spine_tuft(B, f"Epine_{bone}_{i}", loc, n, None, small=True):
                        core.weight_all(o, bone)

        # Pot gonflable en terre cuite, frise de dunes
        path = [Vector((0, 0, POT_H * i / 19)) for i in range(20)]
        prof = [(0.31 + 0.09 * i / 19) * dome(i / 19, t0=0.16, t1=0.03, e0=0.5, e1=0.3) for i in range(20)]
        prof[0] = prof[-1] = 0.0

        def pot_mat(i, j, th, t):
            z = POT_H * (i + 0.5) / 19
            tri = 2 * abs(((th * 5 / TAU) % 1.0) - 0.5) * 2 - 1
            zc = 0.17 + 0.035 * tri
            if abs(z - zc) < 0.022:
                return 1
            if abs(z - 0.075) < 0.012 or abs(z - 0.28) < 0.012:
                return 2
            return 0
        pot = B.sweep("Pot", path, prof, ["terre", "sable", "turquoise"], nseg=30, section=gores(10, 0.04),
                      up=(0, 1, 0), mat_fn=pot_mat)
        core.weight_all(pot, "Body")
        rim = B.ring("Pot_Bord", (0, 0, POT_H), 0.405, 0.062, "ocre", nseg=8, n=30)
        core.weight_all(rim, "Body")

        # Bandana d'explorateur (rayé désert) qui serre le ballon
        zb = 0.84
        tb = (zb - Z0) / (Z1 - Z0)
        ring = []
        for k in range(40):
            th = TAU * k / 40
            r = body_R(tb) * (0.5 + 0.5 * GORE(th, tb)) + 0.012
            ring.append(Vector((-math.sin(th) * r, math.cos(th) * r, zb)))

        def band_mat(i, j, th, t):
            return 1 if (i // 2) % 3 == 0 else (2 if j in (0,) else 0)
        band = B.sweep("Bandana", ring, [0.045] * 40, ["ocre", "sable", "turquoise"], nseg=6,
                       section=core.ellipse(1.0, 0.35), up=(0, 0, 1), closed=True, mat_fn=band_mat)
        core.weight_all(band, "Body_Mid")
        flap_path = core.spline([(0, 0.395, 0.835), (0, 0.39, 0.76), (0, 0.375, 0.66)], 8)
        flap_r = [0.0] + [0.125 * (1 - i / 7) ** 0.9 for i in range(1, 7)] + [0.0]
        flap = B.sweep("Bandana_Pointe", flap_path, flap_r, ["ocre", "sable"], nseg=8,
                       section=core.ellipse(1.0, 0.13), up=(1, 0, 0),
                       mat_fn=lambda i, j, th, t: 1 if i in (2, 3) else 0)
        core.weight_all(flap, "Body_Mid")
        knot = B.sphere("Bandana_Noeud", (0, -0.405, 0.84), (0.05, 0.035, 0.045), "ocre", 8, 6)
        core.weight_all(knot, "Body_Mid")
        for s in (-1, 1):
            tail = B.tube(f"Bandana_Pan_{s}", [(s * 0.02, -0.41, 0.83), (s * 0.07, -0.43, 0.76),
                                               (s * 0.09, -0.42, 0.7)], 0.03, "sable", n=6, nseg=6,
                          section=core.ellipse(0.3, 1.0), up=(0, 1, 0))
            core.weight_all(tail, "Body_Mid")

        # Valve de gonflage (dos, côté -X)
        loc, n = surface(bvh, (-2, -2, 1.3), (1, 1, 0))
        valve(B, loc, n, "Body_Top", 1.5)
        return rig

    def _spine_tuft(self, B, name, loc, n, bw, small=False):
        objs = []
        side = n.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        side.normalize()
        L = 0.045 if small else 0.055
        for i, a in enumerate((0.45, -0.45)):
            d = (n * math.cos(a) + Vector((0, 0, 1)) * math.sin(a) * 0.9 + side * 0.15 * (1 if i else -1)).normalized()
            M = frame_matrix(loc + d * L * 0.55, d, up=(0, 0, 1))
            o = B.sphere(f"{name}_{i}", None, (0.014, 0.014, L), "epine", 6, 4, M=M)
            if bw:
                core.weight_fn(o, bw)
            objs.append(o)
        return objs

    # ------------------------------------------------------------------ shape keys
    def deflate(self, co):
        h = max(co.z, 0.0)
        w = core.wrinkle(co)
        rad = (0.8 + 0.28 * (1 - min(h / 1.7, 1.0))) * (1 + 0.08 * w)
        return Vector((co.x * rad, co.y * rad, max(0.0, h * 0.55 + 0.035 * w * h)))

    def inflate(self, co):
        f = core.ease((co.z - 0.3) / 0.25)
        return Vector((co.x * (1 + 0.07 * f), co.y * (1 + 0.07 * f), co.z * (1 + 0.025 * f)))

    # ------------------------------------------------------------------ animations
    def legacy_actions(self):
        return [("Idle", 60, self.idle, True), ("Move", 30, self.move, True), ("Attack", 40, self.attack, False),
                ("Hit", 20, self.hit, False), ("Death", 60, self.death, False)]

    def idle(self, t):
        p = Pose()
        w = TAU * t / 60
        p.add("Root", loc=(0, 0, 0.035 * (1 - math.cos(w))), rot=(0.025 * math.sin(w + 0.5), 0.035 * math.sin(w + 1.2), 0))
        p.add("Body", scl=vol(1 + 0.025 * math.sin(2 * w)))
        p.add("Body_Mid", rot=(0.03 * math.sin(w - 0.4), 0.04 * math.sin(w + 0.6), 0))
        p.add("Body_Top", rot=(0.04 * math.sin(w - 1.0), 0.05 * math.sin(w), 0.03 * math.sin(w + 2)),
              scl=vol(1 - 0.02 * math.sin(2 * w)))
        p.add("Arm_L", rot=(0.05 * math.sin(w), -0.1 * math.sin(w - 0.8), 0.06 * math.sin(w)))
        p.add("Arm_R", rot=(-0.05 * math.sin(w), 0.1 * math.sin(w - 1.6), -0.06 * math.sin(w + 1)))
        p.shape("Gonfle", 0.15 + 0.15 * math.sin(2 * w))
        return fx_layer(p, t, 60, "idle")

    def move(self, t):
        p = Pose()
        w = TAU * t / 30
        hop = abs(math.sin(w))          # deux bonds par cycle
        land = (1 - hop) ** 6
        p.add("Root", loc=(0, 0, 0.14 * hop), rot=(-0.17 + 0.04 * math.sin(2 * w + 1.0), 0, 0.04 * math.sin(w)))
        p.add("Body", scl=vol(1 - 0.16 * land + 0.06 * hop))
        p.add("Body_Mid", rot=(0.05 * math.cos(2 * w), 0.03 * math.sin(w), 0))
        p.add("Body_Top", rot=(0.08 * math.cos(2 * w + 0.6), 0, 0), scl=vol(1 + 0.04 * math.cos(2 * w + 0.6)))
        p.add("Arm_L", rot=(0.45 * math.sin(w), -0.2 - 0.15 * hop, 0.3 * math.sin(w)))
        p.add("Arm_R", rot=(-0.45 * math.sin(w), 0.2 + 0.15 * hop, 0.3 * math.sin(w)))
        p.shape("Gonfle", 0.2 * land)
        return fx_layer(p, t, 30, "move")

    def attack(self, t):
        p = Pose()
        y = K((0, 0.0), (10, -0.14), (15, 0.5), (18, 0.56), (24, 0.3), (30, 0.06), (40, 0.0))(t)
        z = K((0, 0.0), (10, 0.0), (15, 0.1), (18, 0.06), (23, 0.14), (28, 0.0), (40, 0.0))(t)
        rx = K((0, 0.0), (10, 0.24), (15, -0.38), (18, -0.42), (24, 0.12), (31, -0.05), (40, 0.0))(t)
        p.add("Root", loc=(0, y, z), rot=(rx, 0, 0))
        sz = K((0, 1.0), (10, 0.8), (14, 1.0), (40, 1.0))(t)
        sy = K((0, 1.0), (10, 1.0), (14, 1.15), (17, 1.18), (19, 0.76), (24, 1.08), (30, 0.97), (40, 1.0))(t)
        p.add("Body", scl=vol(sz, "z")).add("Body", scl=vol(sy, "y"))
        p.add("Body_Top", rot=(K((0, 0.0), (10, 0.12), (15, -0.1), (18, -0.25), (23, 0.1), (30, -0.04), (40, 0.0))(t)
                               + damp(t, 18, 0.06, 1.2, 5), 0, 0),
              scl=vol(K((0, 1.0), (17, 1.0), (19, 0.85), (25, 1.05), (40, 1.0))(t), "y"))
        p.add("Arm_L", rot=(0, K((0, 0.0), (10, 0.3), (15, -0.2), (40, 0.0))(t),
                            K((0, 0.0), (10, -0.5), (15, 1.25), (19, 1.1), (28, 0.2), (40, 0.0))(t)))
        p.add("Arm_R", rot=(0, K((0, 0.0), (10, -0.3), (15, 0.15), (40, 0.0))(t),
                            K((0, 0.0), (10, 0.4), (15, -0.9), (19, -0.8), (28, -0.1), (40, 0.0))(t)))
        p.shape("Gonfle", K((0, 0.0), (10, 0.8), (15, 0.25), (19, 0.0), (40, 0.0))(t))
        return fx_layer(p, t, 40, "attack")

    def hit(self, t):
        p = Pose()
        decay = math.exp(-t / 5)
        y = K((0, 0.0), (3, -0.16), (9, -0.1), (20, 0.0))(t)
        rx = K((0, 0.0), (3, 0.28), (8, -0.06), (13, 0.04), (20, 0.0))(t)
        p.add("Root", loc=(jitter(t * 3, 0.03) * decay, y, 0), rot=(rx, 0, damp(t, 1, 0.08, 2.0, 4)))
        p.add("Body", scl=vol(K((0, 1.0), (3, 0.78), (7, 1.1), (11, 0.95), (20, 1.0))(t), "y"))
        p.add("Body_Mid", rot=(0, 0, damp(t, 2, 0.12, 2.6, 4)))
        p.add("Body_Top", rot=(damp(t, 2, 0.2, 1.6, 4), damp(t, 2, 0.15, 2.1, 4), 0))
        p.add("Arm_L", rot=(0, K((0, 0.0), (3, -0.6), (10, 0.1), (20, 0.0))(t), 0))
        p.add("Arm_R", rot=(0, K((0, 0.0), (3, 0.6), (10, -0.1), (20, 0.0))(t), 0))
        p.shape("Gonfle", K((0, 0.0), (3, 0.0), (7, 0.5), (20, 0.0))(t))
        return fx_layer(p, t, 20, "hit")

    def death(self, t):
        p = Pose()
        d = K((0, 0.0), (8, 0.0), (44, 1.0))(t)
        p.shape("Degonfle", d)
        p.add("Root", loc=(0.08 * math.sin(t * 0.45) * d, -0.06 * d, K((0, 0.0), (8, 0.0), (14, 0.16), (30, 0.08),
                                                                        (44, 0.0))(t)),
              rot=(K((0, 0.0), (4, 0.25), (8, 0.0), (40, -0.15), (60, -0.2))(t) + jitter(t, 0.05 * d),
                   jitter(t + 3, 0.06 * d), K((8, 0.0), (46, 1.6))(t) if t >= 8 else 0.0),
              scl=K((0, 1.0), (46, 1.0), (60, 0.001))(t))
        p.add("Body", scl=(1 + 0.08 * d, 1 + 0.08 * d, K((0, 1.0), (4, 0.85), (8, 1.05), (44, 0.62), (60, 0.5))(t)))
        p.add("Body_Mid", rot=(0, 0.2 * d * math.sin(t * 0.6), 0))
        p.add("Body_Top", rot=(0.3 * d + jitter(t, 0.08 * d), jitter(t + 5, 0.1 * d), 0.2 * d))
        p.add("Arm_L", rot=(0, 0.9 * d, 0))
        p.add("Arm_R", rot=(0, -0.9 * d, 0))
        return fx_layer(p, t, 60, "death")


FAMILY = Cactus()
