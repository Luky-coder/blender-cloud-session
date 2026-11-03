"""FAMILLE B - BALLON PYRAMIDE (PV 45).

Pyramide gonflable à base carrée arrondie : quatre panneaux bombés, assises de « pierres » marquées par des
coutures (horizontales, joints décalés, arêtes), frise de dunes sur l'assise basse, hiéroglyphes en relief
sur les trois autres faces, pyramidion doré, quatre pieds-coussins et une petite valve.
Base ~1,6 m, hauteur ~1,65 m (pyramidion compris), avant (visage) vers +Y, pivot au sol.
"""
import math

from mathutils import Vector

from . import core
from .core import TAU, HIEROGLYPHS, K, Pose, damp, dome, frame_matrix, jitter, surface, vol
from .family import Family, fx_layer, valve

Z0, H = 0.06, 1.42       # bas / haut du corps
S0, HA = 0.78, 1.5       # demi-côté à la base, hauteur de l'apex virtuel
P_EXP = 5.0              # superellipse : carré aux angles arrondis
COURSES = (0.32, 0.62, 0.9, 1.15)   # coutures horizontales des assises


def half(z):
    u = min(max(z / HA, 0.0), 1.0)
    return S0 * (1 - u) ** 0.85


def section(th, t=0.0):
    c, s = abs(math.cos(th)), abs(math.sin(th))
    sq = 1.0 / ((c ** P_EXP + s ** P_EXP) ** (1.0 / P_EXP))
    return sq * (1 + 0.035 * math.cos(2 * th) ** 2)   # panneaux bombés


def body_r(t):
    z = Z0 + (H - Z0) * t
    return half(z) * dome(t, t0=0.07, t1=0.0, e0=0.5)


def point(z, th, lift=0.0):
    t = (z - Z0) / (H - Z0)
    r = body_r(t) * section(th) + lift
    return Vector((-math.sin(th) * r, math.cos(th) * r, z))


def front(th):
    """Vrai si l'angle tombe sur la face avant (visage)."""
    a = (th + math.pi) % TAU - math.pi
    return abs(a) < math.radians(40)


class Pyramid(Family):
    key = "Ballon_Pyramide"
    short = "Pyramide"
    label = "Ballon Pyramide"
    pv = 45
    surface_parts = ("Corps",)
    crown = dict(loc=(0, 0, 1.62), size=0.34)
    aura = dict(center=(0, 0, 1.05), radius=0.72, axis=(0, 0, 1), count=6, size=0.14, phase=0.0)
    emblems = (((-2, 0, 0.88), (1, 0, 0), 0.26), ((2, 0, 0.88), (-1, 0, 0), 0.26), ((0, -2, 0.98), (0, 1, 0), 0.22))
    face_frame = dict(center=(0, 0, 0.62))
    face_params = dict(eye_r=0.11, eye_dx=0.2, eye_v=0.13, mouth_v=-0.13, mouth_w=0.3, mouth_h=0.11, brow_w=0.21)
    face_bone = "Body_Mid"
    strings = (dict(parent="Body", hang=False, dir=(0, -1, -0.3), r=0.014,
                    path=[(0, -0.74, 0.14), (0.05, -1.0, 0.03), (-0.06, -1.35, 0.015), (0.04, -1.7, 0.015)]),)
    anim_frames = {"Idle": (1,), "Move": (8,), "Attack": (10, 15, 18), "Hit": (4,), "Death": (24, 42, 54)}

    BONES = [("Root", (0, 0, 0), None), ("Body", (0, 0, 0.05), "Root"), ("Body_Mid", (0, 0, 0.6), "Body"),
             ("Body_Top", (0, 0, 1.0), "Body_Mid"), ("Cap", (0, 0, 1.38), "Body_Top"), ("FX", (0, 0, 1.62), "Cap"),
             ("Aura", (0, 0, 1.05), "Body_Mid"),
             ("Foot_FL", (0.56, 0.56, 0.07), "Body"), ("Foot_FR", (-0.56, 0.56, 0.07), "Body"),
             ("Foot_BL", (0.56, -0.56, 0.07), "Body"), ("Foot_BR", (-0.56, -0.56, 0.07), "Body")]
    FEET = ("Foot_FL", "Foot_FR", "Foot_BL", "Foot_BR")

    def body_weight(self, co):
        return core.gradient("z", [(0.2, "Body"), (0.6, "Body_Mid"), (1.05, "Body_Top")])(co)

    # ------------------------------------------------------------------ géométrie de référence
    def build(self, B):
        rig = core.make_rig("REF_" + self.key, self.rig_bones(), B.coll)
        bw = self.body_weight
        n = 30
        path, ts = core.axis_path((0, 0, Z0), (0, 0, H), n)

        def mat(i, j, th, t):
            z = Z0 + (H - Z0) * (ts[i] + ts[min(i + 1, n - 1)]) / 2
            if z < COURSES[0]:  # assise basse : frise de dunes
                tri = 2 * abs(((th * 8 / TAU) % 1.0) - 0.5) * 2 - 1
                return 2 if abs(z - (0.19 + 0.035 * tri)) < 0.03 else 1
            return 0
        body = B.sweep("Corps", path, [body_r(t) for t in ts], ["corps", "corps2", "ocre"], nseg=48,
                       section=section, up=(0, 1, 0), mat_fn=mat)
        core.weight_fn(body, bw)
        bvh = core.bvh_of([body])

        def seam(name, pts):
            if len(pts) >= 2:
                o = B.tube(name, pts, 0.0075, "couture", n=max(4, len(pts)), nseg=4, ncap=1)
                core.weight_fn(o, bw)

        # coutures horizontales (interrompues devant le visage)
        for ci, z in enumerate(COURSES):
            pts = []
            for k in range(37):
                th = math.radians(40) + (TAU - math.radians(80)) * k / 36 if 0.5 < z < 1.0 else TAU * k / 36
                pts.append(point(z, th, 0.002))
            seam(f"Couture_Assise_{ci}", pts)
        # arêtes
        for k in range(4):
            th = math.pi / 4 + k * math.pi / 2
            seam(f"Couture_Arete_{k}", [point(Z0 + 0.05 + (H - 0.1 - Z0) * i / 15, th, 0.002) for i in range(16)])
        # joints verticaux décalés (pierres)
        bounds = (Z0 + 0.03,) + COURSES + (H - 0.05,)
        for c in range(len(bounds) - 1):
            za, zb = bounds[c] + 0.01, bounds[c + 1] - 0.01
            fr = (-0.45, 0.05, 0.55) if c % 2 else (-0.2, 0.3)
            if c >= 3:
                fr = (0.0,)
            for face_i in range(4):
                th0 = face_i * math.pi / 2
                for f in fr:
                    th = th0 + math.atan(f * 0.9)
                    if face_i == 0 and 0 < c < 3:
                        continue
                    seam(f"Couture_Joint_{c}_{face_i}_{f}", [point(za + (zb - za) * i / 5, th, 0.002) for i in range(6)])

        # hiéroglyphes en relief : faces gauche, droite et arrière
        names = list(core.HIEROGLYPHS)
        gi = 0
        for d, rows in (((1, 0, 0), ((0.47, (-0.32, 0.0, 0.32)),)), ((-1, 0, 0), ((0.47, (-0.32, 0.0, 0.32)),)),
                        ((0, 1, 0), ((0.47, (-0.32, 0.0, 0.32)), (0.76, (-0.22, 0.22))))):
            dv = Vector(d)
            lat = Vector((0, 0, 1)).cross(dv)
            for z, us in rows:
                for u in us:
                    o = -dv * 2 + lat * u + Vector((0, 0, z))
                    loc, nrm = surface(bvh, o, dv)
                    if loc is None:
                        continue
                    M = frame_matrix(loc, nrm, up=(0, 0, 1))
                    gname = names[gi % len(names)]
                    gi += 1
                    for g in core.glyph(B, f"Hieroglyphe_{gi}_{gname}", HIEROGLYPHS[gname], 0.22, M, bvh):
                        core.weight_fn(g, bw)

        # pyramidion doré
        cp = [Vector((0, 0, 1.33 + 0.3 * i / 9)) for i in range(10)]
        cr = [0.19 * (1 - i / 9) ** 0.9 * dome(i / 9, t0=0.12, t1=0.0) for i in range(10)]
        cr[0] = cr[-1] = 0.0
        cap = B.sweep("Pyramidion", cp, cr, ["or"], nseg=24, section=section, up=(0, 1, 0))
        core.weight_all(cap, "Cap")
        rp = [Vector((-math.sin(a) * 0.18 * section(a), math.cos(a) * 0.18 * section(a), 1.365))
              for a in [TAU * k / 28 for k in range(28)]]
        ring = B.sweep("Pyramidion_Bague", rp, [0.024] * 28, ["turquoise"], nseg=4, up=(0, 0, 1), closed=True)
        core.weight_all(ring, "Cap")

        # pieds-coussins
        for bone in self.FEET:
            hx, hy, _ = dict((b[0], b[1]) for b in self.BONES)[bone]
            foot = B.sphere(f"Pied_{bone}", (hx, hy, 0.075), (0.15, 0.15, 0.08), "sable", 12, 6)
            core.weight_all(foot, bone)

        # valve (face -X, en bas)
        loc, nrm = surface(bvh, (-2, -0.3, 0.2), (1, 0, 0))
        valve(B, loc, nrm, "Body", 1.6)
        return rig

    # ------------------------------------------------------------------ shape keys
    def deflate(self, co):
        h = max(co.z, 0.0)
        w = core.wrinkle(co, 0.8)
        rad = (0.82 + 0.3 * (1 - min(h / 1.6, 1.0))) * (1 + 0.08 * w)
        return Vector((co.x * rad, co.y * rad, max(0.0, h * 0.45 + 0.04 * w * h)))

    def inflate(self, co):
        f = core.ease((co.z - 0.1) / 0.2)
        return Vector((co.x * (1 + 0.06 * f), co.y * (1 + 0.06 * f), co.z * (1 + 0.03 * f)))

    # ------------------------------------------------------------------ animations
    def actions(self):
        return [("Idle", 60, self.idle, True), ("Move", 30, self.move, True), ("Attack", 40, self.attack, False),
                ("Hit", 20, self.hit, False), ("Death", 60, self.death, False)]

    def feet(self, p, fn):
        for i, b in enumerate(self.FEET):
            loc, rot, scl = fn(i, b)
            p.add(b, loc=loc, rot=rot, scl=scl)

    def idle(self, t):
        p = Pose()
        w = TAU * t / 60
        p.add("Root", loc=(0, 0, 0.04 * (1 - math.cos(w))), rot=(0.02 * math.sin(w + 0.5), 0.03 * math.sin(w + 1.2), 0))
        p.add("Body", scl=vol(1 + 0.022 * math.sin(2 * w)))
        p.add("Body_Mid", rot=(0.02 * math.sin(w - 0.5), 0.025 * math.sin(w + 0.4), 0))
        p.add("Body_Top", rot=(0.04 * math.sin(w - 1.0), 0.05 * math.sin(w - 0.6), 0), scl=vol(1 - 0.02 * math.sin(2 * w)))
        p.add("Cap", loc=(0, 0, 0.02 * math.sin(w - 1.4)), rot=(0, 0, 0.12 * math.sin(w)))
        self.feet(p, lambda i, b: ((0, 0, 0), (0, 0, 0), vol(1 + 0.08 * math.sin(w + i * 1.6))))
        p.shape("Gonfle", 0.15 + 0.15 * math.sin(2 * w))
        return fx_layer(p, t, 60, "idle")

    def move(self, t):
        p = Pose()
        w = TAU * t / 30
        hop = abs(math.sin(w))
        land = (1 - hop) ** 6
        p.add("Root", loc=(0, 0, 0.17 * hop), rot=(-0.13 + 0.04 * math.sin(2 * w + 1.0), 0, 0.03 * math.sin(w)))
        p.add("Body", scl=vol(1 - 0.18 * land + 0.06 * hop))
        p.add("Body_Top", rot=(0.07 * math.cos(2 * w + 0.6), 0.03 * math.sin(w), 0))
        p.add("Cap", rot=(0.12 * math.cos(2 * w + 1.0), 0, 0), loc=(0, 0, 0.03 * math.cos(2 * w + 1.2)))
        self.feet(p, lambda i, b: ((0, 0, 0.02 * hop), (0, 0, 0), vol(1 - 0.35 * hop + 0.25 * land)))
        p.shape("Gonfle", 0.2 * land)
        return fx_layer(p, t, 30, "move")

    def attack(self, t):
        """Saut en avant et coup de « tête » de la pyramide (la face avant percute)."""
        p = Pose()
        y = K((0, 0.0), (10, -0.12), (15, 0.6), (18, 0.7), (24, 0.42), (31, 0.08), (40, 0.0))(t)
        z = K((0, 0.0), (10, 0.0), (14, 0.32), (18, 0.04), (23, 0.14), (28, 0.0), (40, 0.0))(t)
        rx = K((0, 0.0), (10, 0.22), (15, -0.5), (18, -0.38), (24, 0.1), (31, -0.04), (40, 0.0))(t)
        p.add("Root", loc=(0, y, z), rot=(rx, 0, 0))
        sz = K((0, 1.0), (10, 0.74), (14, 1.12), (17, 1.0), (40, 1.0))(t)
        sy = K((0, 1.0), (16, 1.0), (19, 0.78), (24, 1.08), (31, 0.97), (40, 1.0))(t)
        p.add("Body", scl=vol(sz, "z")).add("Body", scl=vol(sy, "y"))
        p.add("Body_Top", rot=(K((0, 0.0), (10, 0.1), (15, 0.12), (18, -0.3), (24, 0.12), (40, 0.0))(t)
                               + damp(t, 18, 0.07, 1.2, 5), 0, 0))
        p.add("Cap", rot=(K((0, 0.0), (10, 0.15), (15, 0.25), (18, -0.45), (24, 0.2), (32, 0.0), (40, 0.0))(t), 0, 0),
              loc=(0, 0, K((0, 0.0), (17, 0.0), (20, 0.08), (26, 0.0))(t)))
        self.feet(p, lambda i, b: ((0, 0, 0), (0, 0, 0), vol(K((0, 1.0), (10, 0.6), (14, 1.3), (18, 0.8), (26, 1.0))(t))))
        p.shape("Gonfle", K((0, 0.0), (10, 0.8), (15, 0.3), (18, 0.0), (40, 0.0))(t))
        return fx_layer(p, t, 40, "attack")

    def hit(self, t):
        p = Pose()
        decay = math.exp(-t / 5)
        p.add("Root", loc=(jitter(t * 3, 0.03) * decay, K((0, 0.0), (3, -0.18), (9, -0.1), (20, 0.0))(t), 0),
              rot=(K((0, 0.0), (3, 0.22), (8, -0.05), (13, 0.03), (20, 0.0))(t), 0, damp(t, 1, 0.07, 2.0, 4)))
        p.add("Body", scl=vol(K((0, 1.0), (3, 0.8), (7, 1.08), (11, 0.96), (20, 1.0))(t), "y"))
        p.add("Body_Top", rot=(damp(t, 2, 0.18, 1.6, 4), damp(t, 2, 0.14, 2.1, 4), 0))
        p.add("Cap", rot=(damp(t, 2, 0.35, 1.4, 5), damp(t, 3, 0.25, 1.9, 5), 0))
        p.shape("Gonfle", K((0, 0.0), (3, 0.0), (7, 0.5), (20, 0.0))(t))
        return fx_layer(p, t, 20, "hit")

    def death(self, t):
        p = Pose()
        d = K((0, 0.0), (8, 0.0), (44, 1.0))(t)
        p.shape("Degonfle", d)
        p.add("Root", loc=(0.07 * math.sin(t * 0.45) * d, -0.05 * d, K((0, 0.0), (8, 0.0), (14, 0.14), (30, 0.06),
                                                                        (44, 0.0))(t)),
              rot=(K((0, 0.0), (4, 0.22), (8, 0.0), (44, -0.1))(t) + jitter(t, 0.05 * d), jitter(t + 3, 0.06 * d),
                   K((8, 0.0), (46, -1.3))(t)),
              scl=K((0, 1.0), (46, 1.0), (60, 0.001))(t))
        p.add("Body", scl=(1 + 0.1 * d, 1 + 0.1 * d, K((0, 1.0), (4, 0.85), (8, 1.05), (44, 0.6), (60, 0.5))(t)))
        p.add("Body_Top", rot=(0.35 * d + jitter(t, 0.08 * d), jitter(t + 5, 0.12 * d), 0.25 * d))
        p.add("Cap", loc=(0.12 * d, 0, -0.1 * d), rot=(0.6 * d, 0.5 * d, 0))
        self.feet(p, lambda i, b: ((0, 0, 0), (0, 0, 0), (1 + 0.3 * d, 1 + 0.3 * d, 1 - 0.5 * d)))
        return fx_layer(p, t, 60, "death")


FAMILY = Pyramid()
