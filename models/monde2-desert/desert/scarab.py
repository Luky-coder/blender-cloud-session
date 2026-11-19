"""MINI-BOSS - LE SCARABALLON (type Plante, PV 450).

Énorme scarabée entièrement gonflable : grande carapace verte à élytres côtelés et bordure dorée,
pronotum doré, tête expressive, deux antennes à bourgeons, deux ailes-feuilles décoratives, six pattes
gonflables à genouillères dorées, motifs végétaux dorés et gemmes turquoise sur la carapace,
pousses et fleur au sommet.
Longueur ~3,3 m, hauteur ~2 m, avant vers +Y, pivot au sol.
"""
import math

from mathutils import Vector

from . import core
from .core import TAU, HIEROGLYPHS, K, Pose, damp, frame_matrix, jitter, surface, vol
from .family import Family, fx_layer, valve

SY0, SY1, SZ = -1.45, 0.55, 0.88    # carapace : arrière, avant, hauteur du centre
LEGS = [("L1", 1, 0.45, 0.5), ("L2", 1, -0.1, 0.0), ("L3", 1, -0.6, -0.55),
        ("R1", -1, 0.45, 0.5), ("R2", -1, -0.1, 0.0), ("R3", -1, -0.6, -0.55)]
TRIPOD = {"L1": 0, "R2": 0, "L3": 0, "R1": 1, "L2": 1, "R3": 1}
ROOTS = [(-0.95, 2.9), (0.0, 3.5), (0.95, 2.9)]
HIDDEN = 0.001


def shell_r(t):
    return 1.0 * core.dome(t, 0.28, 0.32, 0.5, 0.55)


def shell_sec(th, t):
    c, s = math.cos(th), math.sin(th)
    a = 0.85 if c > 0 else 0.5
    m = 1.0 / math.sqrt((c / a) ** 2 + s ** 2)
    if c > 0.15:  # stries des élytres
        x = ((th * 14 / TAU) % 1.0)
        m *= 1 - 0.035 * (1 - math.sin(math.pi * x) ** 0.6) * min(1.0, (c - 0.15) * 4)
    return m


def shell_point(t, th, lift=0.0):
    r = shell_r(t) * shell_sec(th, t) + lift
    return Vector((math.sin(th) * r, SY0 + (SY1 - SY0) * t, SZ + math.cos(th) * r))


class Scarab(Family):
    key = "Scaraballon"
    short = "Scaraballon"
    label = "Le Scaraballon (mini-boss)"
    boss_file = "MiniBoss_Scaraballon_Plante"
    pv = 450
    surface_parts = ("Carapace", "Pronotum", "Tete")
    crown = dict(loc=(0, -0.3, SZ + 0.83), size=0.5)
    aura = dict(center=(0, -0.2, 1.15), radius=1.75, axis=(0, 0, 1), count=8, size=0.24, phase=0.2)
    emblems = (((-3, -0.75, 1.0), (1, 0, 0), 0.4), ((3, -0.75, 1.0), (-1, 0, 0), 0.4))
    face_frame = dict(center=(0, 1.2, 0.72))
    face_params = dict(eye_r=0.125, eye_dx=0.2, eye_v=0.08, mouth_v=-0.17, mouth_w=0.28, mouth_h=0.1, brow_w=0.22,
                       brow=0.6)
    face_bone = "Head"
    fly_from = "Idle"
    fly_lift = 0.9
    prop_prefixes = ('Racine',)
    strings = (dict(parent="Shell", hang=False, dir=(0, -0.6, -0.8), r=0.022, scale=1.6,
                    path=[(0, -1.38, 0.66), (0.05, -1.6, 0.35), (-0.08, -1.95, 0.03), (0.06, -2.5, 0.02)]),)
    anim_pad_forward = 0.5

    BONES = [("Root", (0, 0, 0), None), ("Roll", (0, 0, 0.85), "Root"), ("Body", (0, 0, 0.3), "Roll"),
             ("Shell", (0, -0.3, 0.9), "Body"), ("Wing_L", (0.55, -0.55, 1.15), "Shell"),
             ("Wing_R", (-0.55, -0.55, 1.15), "Shell"), ("FX", (0, -0.3, SZ + 0.83), "Shell"),
             ("Aura", (0, -0.2, 1.15), "Body"), ("Thorax", (0, 0.75, 0.85), "Body"),
             ("Head", (0, 1.1, 0.75), "Thorax"), ("Ant_L", (0.15, 1.38, 1.02), "Head"),
             ("Ant_R", (-0.15, 1.38, 1.02), "Head")] + \
            [(f"Leg_{n}", (s * 0.62, y, 0.5), "Body") for n, s, y, _ in LEGS] + \
            [(f"Roots_{k + 1}", (x, y, 0.0), "Root") for k, (x, y) in enumerate(ROOTS)]

    def body_weight(self, co):
        return core.gradient("y", [(0.45, "Shell"), (0.6, "Thorax")])(co)

    # ------------------------------------------------------------------ géométrie de référence
    def build(self, B):
        rig = core.make_rig("REF_" + self.key, self.rig_bones(), B.coll, length=0.15)
        n = 34
        path, ts = core.axis_path((0, SY0, SZ), (0, SY1, SZ), n)

        def mat(i, j, th, t):
            return 0 if math.cos(th) > -0.2 else 1
        shell = B.sweep("Carapace", path, [shell_r(t) for t in ts], ["corps", "corps2"], nseg=42, section=shell_sec,
                        up=(0, 0, 1), mat_fn=mat)
        core.weight_all(shell, "Shell")
        pron = B.sphere("Pronotum", (0, 0.72, 0.92), (0.74, 0.44, 0.52), "or", 22, 12)
        core.weight_all(pron, "Thorax")
        head = B.sphere("Tete", (0, 1.2, 0.74), (0.56, 0.46, 0.5), "corps", 24, 12)
        core.weight_all(head, "Head")
        bvh = core.bvh_of([shell, pron, head])

        # bordures dorées et suture des élytres
        for s in (-1, 1):
            th = s * math.radians(101)
            pts = [shell_point(0.05 + 0.9 * i / 17, th, 0.004) for i in range(18)]
            core.weight_all(B.tube(f"Bordure_{s}", pts, 0.035, "or", n=18, nseg=5), "Shell")
        pts = [shell_point(0.04 + 0.94 * i / 17, 0.0, 0.004) for i in range(18)]
        core.weight_all(B.tube("Suture", pts, 0.022, "or", n=18, nseg=5), "Shell")
        # coutures discrètes
        for s in (-1, 1):
            pts = [shell_point(0.04 + 0.92 * i / 15, s * 0.85, 0.002) for i in range(16)]
            core.weight_all(B.tube(f"Couture_{s}", pts, 0.008, "couture", n=16, nseg=4, ncap=1), "Shell")

        # motifs végétaux dorés (rinceaux + lotus) et gemmes turquoise sur les élytres
        vine = [[(-0.5, -0.3), (-0.3, -0.05), (-0.05, -0.12), (0.15, 0.1), (0.4, 0.05), (0.5, 0.25)],
                [(-0.3, -0.05), (-0.35, 0.18), (-0.2, 0.25)], [(0.15, 0.1), (0.1, 0.32), (0.25, 0.38)],
                [(-0.05, -0.12), (0.05, -0.35), (0.2, -0.32)]]
        for s in (-1, 1):
            for k, (t, th, g, sz) in enumerate(((0.35, 0.55, vine, 0.75), (0.68, 0.5, HIEROGLYPHS["lotus"], 0.45))):
                p0 = shell_point(t, s * th, 0.6)
                loc, nrm = surface(bvh, p0, shell_point(t, s * th) - p0)
                if loc is None:
                    continue
                M = frame_matrix(loc, nrm, up=(0, 1, 0))
                strokes = [[(x * s, y) for x, y in st] for st in g]
                for o in core.glyph(B, f"Motif_{s}_{k}", strokes, sz, M, bvh, role="or", width=0.035):
                    core.weight_all(o, "Shell")
        for k, t in enumerate((0.25, 0.5, 0.75)):
            loc = shell_point(t, 0.0, 0.02)
            core.weight_all(B.sphere(f"Gemme_{k}", loc, (0.07, 0.07, 0.05), "turquoise", 8, 5), "Shell")
        loc, nrm = surface(bvh, (0, 1.6, 1.5), (0, -1, -0.6))
        core.weight_all(B.sphere("Gemme_Front", None, (0.07, 0.07, 0.04), "turquoise", 12, 8,
                                 M=frame_matrix(loc, nrm, up=(0, 0, 1))), "Head")

        # pousses végétales sur la carapace
        for k, (t, th) in enumerate(((0.3, 0.6), (0.3, -0.6), (0.62, 0.35), (0.55, -0.45))):
            base = shell_point(t, th, -0.01)
            nrm = (base - Vector((0, base.y, SZ))).normalized()
            for j, a in enumerate((-0.5, 0.5)):
                d = (nrm + Vector((0, a, 0.3))).normalized()
                ctrl = [base, base + d * 0.12 + Vector((0, 0, 0.05)), base + d * 0.24 + Vector((0, a * 0.1, 0.02))]
                pth = core.spline(ctrl, 8)
                rr = [0.0] + [0.07 * math.sin(math.pi * i / 7) ** 0.8 for i in range(1, 7)] + [0.0]
                leaf = B.sweep(f"Pousse_{k}_{j}", pth, rr, ["fx2"], nseg=6, section=core.ellipse(0.15, 1.0),
                               up=(0, 0, 1))
                core.weight_all(leaf, "Shell")

        # antennes à bourgeons
        for s, bone in ((1, "Ant_L"), (-1, "Ant_R")):
            ctrl = [(s * 0.15, 1.36, 1.0), (s * 0.22, 1.55, 1.3), (s * 0.4, 1.72, 1.52), (s * 0.55, 1.8, 1.6)]
            core.weight_all(B.tube(f"Antenne_{s}", ctrl, 0.03, "couture", n=10, nseg=6), bone)
            core.weight_all(B.sphere(f"Antenne_Bourgeon_{s}", (s * 0.58, 1.82, 1.62), (0.09, 0.09, 0.12), "fx2", 10, 6),
                            bone)
            core.weight_all(B.sphere(f"Antenne_Fleur_{s}", (s * 0.6, 1.84, 1.72), (0.05, 0.05, 0.04), "fx", 8, 5), bone)

        # ailes-feuilles décoratives (dépassant de sous la carapace)
        for s, bone in ((1, "Wing_L"), (-1, "Wing_R")):
            ctrl = [Vector((s * 0.55, -0.35, 1.12)), Vector((s * 1.05, -0.95, 1.3)), Vector((s * 1.3, -1.6, 1.38))]
            pth = core.spline(ctrl, 14)
            rr = [0.0] + [0.34 * math.sin(math.pi * (i / 13) ** 0.8) for i in range(1, 13)] + [0.0]
            wing = B.sweep(f"Aile_{s}", pth, rr, ["fx2"], nseg=8, section=core.ellipse(0.08, 1.0), up=(0, 0, 1))
            core.weight_all(wing, bone)
            core.weight_all(B.tube(f"Aile_Nervure_{s}", [ctrl[0] + Vector((0, 0, 0.03)), ctrl[1] + Vector((0, 0, 0.035)),
                                                          ctrl[2] + Vector((0, 0, 0.0))], 0.016, "or", n=10, nseg=4),
                            bone)

        # six pattes gonflables
        for name, s, y, sw in LEGS:
            hip = Vector((s * 0.55, y, 0.55))
            knee = Vector((s * 1.12, y + sw * 0.35, 0.78))
            foot = Vector((s * 1.3, y + sw * 0.55, 0.1))
            leg = B.tube(f"Patte_{name}", [hip, hip.lerp(knee, 0.5) + Vector((0, 0, 0.06)), knee,
                                           knee.lerp(foot, 0.5) + Vector((s * 0.06, 0, 0)), foot], 0.1, "corps",
                         n=12, nseg=10, rfn=lambda t: 1.0 - 0.3 * t + 0.15 * math.sin(math.pi * t * 2) ** 2)
            core.weight_all(leg, f"Leg_{name}")
            core.weight_all(B.sphere(f"Genou_{name}", knee, (0.105,) * 3, "or", 10, 6), f"Leg_{name}")
            core.weight_all(B.sphere(f"Pied_{name}", foot + Vector((0, 0.03, -0.02)), (0.11, 0.14, 0.08), "corps2", 10, 6),
                            f"Leg_{name}")

        # valve (flanc gauche arrière)
        loc, nrm = surface(bvh, (-3, -0.9, 0.62), (1, 0, 0))
        valve(B, loc, nrm, "Shell", 2.2)

        # racines-accessoires de l'attaque « Racines » (cachées hors de cette action)
        for k, (x, y) in enumerate(ROOTS):
            bone = f"Roots_{k + 1}"
            ctrl = [(x, y, -0.1), (x + 0.15, y - 0.05, 0.45), (x - 0.12, y + 0.1, 0.95), (x + 0.1, y + 0.05, 1.45)]
            root = B.tube(f"Racine_{k}", ctrl, 0.16, "cuir", n=12, nseg=8,
                          rfn=lambda t: (1 - t) ** 0.7 * (1 + 0.12 * math.sin(t * 25)) + 0.05)
            core.weight_all(root, bone)
            mound = B.ring(f"Racine_Butte_{k}", (x, y, 0.03), 0.24, 0.07, "sable", nseg=6, n=16)
            core.weight_all(mound, bone)
            for j, (h, a) in enumerate(((0.55, 0.0), (1.0, 2.2))):
                c = Vector((x, y, h))
                d = Vector((math.cos(a), math.sin(a), 0.4)).normalized()
                pth = core.spline([c, c + d * 0.18, c + d * 0.34 + Vector((0, 0, 0.05))], 8)
                rr = [0.0] + [0.09 * math.sin(math.pi * i / 7) ** 0.8 for i in range(1, 7)] + [0.0]
                core.weight_all(B.sweep(f"Racine_Feuille_{k}_{j}", pth, rr, ["fx2"], nseg=6,
                                        section=core.ellipse(0.15, 1.0), up=(0, 0, 1)), bone)
        return rig

    # ------------------------------------------------------------------ shape keys
    def deflate(self, co):
        if co.y > 2.0:            # racines : inchangées
            return co
        h = max(co.z, 0.0)
        w = core.wrinkle(co, 0.6)
        rad = (0.85 + 0.2 * (1 - min(h / 1.8, 1.0))) * (1 + 0.07 * w)
        return Vector((co.x * rad, co.y * (0.92 + 0.04 * w), max(0.0, h * 0.42 + 0.04 * w * h)))

    def inflate(self, co):
        if co.y > 2.0:
            return co
        f = core.ease((co.z - 0.3) / 0.3)
        return Vector((co.x * (1 + 0.05 * f), co.y * (1 + 0.03 * f), co.z * (1 + 0.04 * f)))

    # ------------------------------------------------------------------ animations
    def fly_extra(self, p, t, n):
        """Le scarabée vole : ailes-feuilles qui battent, pattes pendantes qui pédalent, corps penché."""
        w = TAU * t / n
        p.add("Root", rot=(-0.08, 0, 0))
        for s, b in ((1, "Wing_L"), (-1, "Wing_R")):
            p.add(b, rot=(0.15, -s * (0.25 + 0.35 * math.sin(4 * w)), s * 0.2))
        for name, s, _, _ in LEGS:
            p.add(f"Leg_{name}", rot=(0.15 * math.sin(2 * w + len(name)), s * 0.35, 0))
        return p

    def legacy_actions(self):
        return [("Idle", 60, self.idle, True), ("Move", 30, self.move, True), ("Attack", 50, self.attack, False),
                ("Hit", 20, self.hit, False), ("Death", 80, self.death, False),
                ("Attack_Roll", 80, self.roll, False), ("Attack_Roots", 72, self.roots, False)]

    def base(self, p, roots=HIDDEN, show=None):
        """Racines cachées : échelle quasi nulle ET repliées sous le ventre (hors cadrage, hors bbox)."""
        for k, (x, y) in enumerate(ROOTS):
            vis = show[k] if show else False
            p.add(f"Roots_{k + 1}", scl=roots if isinstance(roots, (int, float)) else roots[k],
                  loc=(0, 0, 0) if vis else (-x, -y, 0.3))
        return p

    def legs(self, p, fn):
        for name, s, _, _ in LEGS:
            rot, scl = fn(name, s)
            p.add(f"Leg_{name}", rot=rot, scl=scl)

    def idle(self, t):
        p = self.base(Pose())
        w = TAU * t / 60
        p.add("Root", loc=(0, 0, 0.04 * (1 - math.cos(w))), rot=(0.015 * math.sin(w + 0.5), 0.02 * math.sin(w + 1), 0))
        p.add("Body", scl=vol(1 + 0.02 * math.sin(2 * w)))
        p.add("Shell", scl=vol(1 + 0.025 * math.sin(2 * w - 0.5)), rot=(0.015 * math.sin(w), 0, 0))
        p.add("Thorax", rot=(0.02 * math.sin(w - 0.6), 0, 0.02 * math.sin(w)))
        p.add("Head", rot=(0.05 * math.sin(w - 1.0), 0.04 * math.sin(w), 0.06 * math.sin(w + 0.5)))
        for s, b in ((1, "Ant_L"), (-1, "Ant_R")):
            p.add(b, rot=(0.15 * math.sin(2 * w + s), 0.1 * math.sin(w + s), 0.08 * s * math.sin(w)))
        for s, b in ((1, "Wing_L"), (-1, "Wing_R")):
            p.add(b, rot=(0.05 * math.sin(2 * w), -s * 0.06 * math.sin(2 * w + 0.4), 0))
        self.legs(p, lambda n, s: ((0, -s * 0.04 * math.sin(w + len(n)), 0.03 * math.sin(w)), 1.0))
        p.shape("Gonfle", 0.15 + 0.15 * math.sin(2 * w))
        return fx_layer(p, t, 60, "idle", spin=1.0)

    def move(self, t):
        """Trottinement en trépied (L1, R2, L3 / R1, L2, R3)."""
        p = self.base(Pose())
        w = TAU * t / 30
        p.add("Root", loc=(0, 0, 0.05 * abs(math.sin(2 * w))), rot=(-0.06, 0.03 * math.sin(2 * w), 0.04 * math.sin(w)))
        p.add("Body", scl=vol(1 - 0.04 * math.cos(4 * w)))
        p.add("Shell", rot=(0.03 * math.cos(2 * w), 0.02 * math.sin(2 * w), 0))
        p.add("Head", rot=(0.05 * math.cos(2 * w), 0, 0.06 * math.sin(w)))
        for s, b in ((1, "Ant_L"), (-1, "Ant_R")):
            p.add(b, rot=(-0.3 + 0.1 * math.sin(2 * w + s), 0, 0))

        def leg(n, s):
            ph = w + math.pi * TRIPOD[n]
            swing = 0.38 * math.sin(ph)
            lift = 0.32 * max(0.0, math.cos(ph))
            return (0, -s * lift, s * swing), 1.0
        self.legs(p, leg)
        p.shape("Gonfle", 0.1)
        return fx_layer(p, t, 30, "move", spin=1.0)

    def attack(self, t):
        """Charge frontale avec la carapace."""
        p = self.base(Pose())
        y = K((0, 0.0), (14, -0.35), (21, 1.7), (24, 1.85), (31, 1.25), (38, 0.4), (50, 0.0))(t)
        z = K((0, 0.0), (14, 0.0), (21, 0.12), (24, 0.04), (29, 0.22), (34, 0.0), (50, 0.0))(t)
        rx = K((0, 0.0), (14, 0.12), (21, -0.18), (24, -0.12), (30, 0.12), (38, -0.03), (50, 0.0))(t)
        p.add("Root", loc=(0, y, z), rot=(rx, 0, jitter(t, 0.03) if t < 14 else 0))
        p.add("Body", scl=vol(K((0, 1.0), (14, 0.82), (20, 1.08), (23, 1.05), (25, 0.85), (31, 1.05), (40, 1.0))(t))
              ).add("Body", scl=vol(K((0, 1.0), (20, 1.0), (22, 1.12), (24, 0.8), (30, 1.06), (40, 1.0))(t), "y"))
        p.add("Shell", rot=(K((0, 0.0), (14, -0.12), (21, -0.2), (24, 0.12), (32, -0.04), (50, 0.0))(t), 0, 0),
              loc=(0, K((0, 0.0), (21, 0.0), (24, 0.12), (30, 0.0))(t), 0))
        p.add("Head", rot=(K((0, 0.0), (14, 0.25), (21, 0.3), (24, -0.2), (32, 0.05), (50, 0.0))(t), 0, 0),
              scl=vol(K((0, 1.0), (22, 1.0), (24, 0.75), (30, 1.05), (40, 1.0))(t), "y"))
        for s, b in ((1, "Ant_L"), (-1, "Ant_R")):
            p.add(b, rot=(K((0, 0.0), (14, -0.5), (21, -0.8), (24, 0.5), (32, -0.1), (50, 0.0))(t), 0, 0))

        def leg(n, s):
            ph = TAU * t / 8 + math.pi * TRIPOD[n]
            run = K((0, 0.0), (8, 0.0), (14, 0.6), (21, 1.0), (24, 0.0), (32, 0.5), (44, 0.0))(t)
            return (0, -s * 0.3 * max(0.0, math.cos(ph)) * run, s * 0.4 * math.sin(ph) * run), 1.0
        self.legs(p, leg)
        p.shape("Gonfle", K((0, 0.0), (14, 0.9), (21, 0.4), (24, 0.0), (50, 0.0))(t))
        return fx_layer(p, t, 50, "attack")

    def hit(self, t):
        p = self.base(Pose())
        decay = math.exp(-t / 5)
        p.add("Root", loc=(jitter(t * 3, 0.05) * decay, K((0, 0.0), (3, -0.3), (9, -0.18), (20, 0.0))(t), 0),
              rot=(K((0, 0.0), (3, 0.15), (8, -0.04), (20, 0.0))(t), damp(t, 1, 0.06, 2.0, 4), damp(t, 1, 0.06, 2.4, 4)))
        p.add("Body", scl=vol(K((0, 1.0), (3, 0.82), (7, 1.08), (11, 0.96), (20, 1.0))(t), "y"))
        p.add("Shell", rot=(damp(t, 2, 0.12, 1.6, 4), damp(t, 2, 0.1, 2.1, 4), 0))
        p.add("Head", rot=(K((0, 0.0), (3, 0.35), (10, -0.05), (20, 0.0))(t), 0, damp(t, 2, 0.2, 1.8, 4)),
              scl=vol(K((0, 1.0), (3, 0.8), (8, 1.05), (20, 1.0))(t), "y"))
        for s, b in ((1, "Ant_L"), (-1, "Ant_R")):
            p.add(b, rot=(damp(t, 1, 0.6, 1.5, 5), 0, s * damp(t, 2, 0.3, 2.0, 5)))
        self.legs(p, lambda n, s: ((0, -s * K((0, 0.0), (3, 0.35), (12, 0.0))(t), 0), 1.0))
        p.shape("Gonfle", K((0, 0.0), (3, 0.0), (7, 0.5), (20, 0.0))(t))
        return fx_layer(p, t, 20, "hit")

    def death(self, t):
        """Dégonflage : pattes qui s'affaissent, bascule sur le dos, ratatinement, disparition."""
        p = self.base(Pose())
        d = K((0, 0.0), (10, 0.0), (60, 1.0))(t)
        p.shape("Degonfle", d)
        p.add("Root", loc=(0.1 * math.sin(t * 0.3) * d, 0, K((0, 0.0), (10, 0.0), (18, 0.25), (32, 0.1), (60, 0.0))(t)),
              rot=(K((0, 0.0), (5, 0.18), (10, 0.0))(t) + jitter(t, 0.04 * d), jitter(t + 2, 0.05 * d),
                   K((10, 0.0), (62, 1.2))(t)),
              scl=K((0, 1.0), (66, 1.0), (80, 0.001))(t))
        p.add("Roll", rot=(0, K((0, 0.0), (28, 0.0), (48, 2.6), (54, 2.4), (60, 2.5))(t), 0))
        p.add("Body", scl=(1 + 0.08 * d, 1.0, K((0, 1.0), (5, 0.85), (10, 1.05), (60, 0.65))(t)))
        p.add("Head", rot=(0.4 * d + jitter(t, 0.06 * d), 0, 0.3 * d))
        for s, b in ((1, "Ant_L"), (-1, "Ant_R")):
            p.add(b, rot=(0.9 * d, 0, s * 0.5 * d))
        for s, b in ((1, "Wing_L"), (-1, "Wing_R")):
            p.add(b, rot=(0.3 * d, s * 0.4 * d, 0))
        self.legs(p, lambda n, s: ((0, -s * (K((0, 0.0), (10, 0.0), (30, -0.3), (50, 0.5))(t)
                                              + 0.25 * math.sin(t * 0.9 + len(n)) * d), 0), 1.0))
        return fx_layer(p, t, 80, "death")

    def roll(self, t):
        """Se met en boule, roule vers l'avant (2 tours), percute, se déroule et revient."""
        p = self.base(Pose())
        tuck = K((0, 0.0), (12, 1.0), (56, 1.0), (64, 0.0))(t)
        y = K((0, 0.0), (12, -0.2), (50, 3.6), (54, 3.8), (60, 3.5), (80, 0.0))(t)
        p.add("Root", loc=(0, y, 0.12 * abs(math.sin(t * 0.5)) * tuck - 0.25 * tuck))
        p.add("Roll", rot=(K((0, 0.0), (12, 0.25), (50, -2 * TAU), (54, -2 * TAU - 0.3), (60, -2 * TAU))(t), 0, 0))
        p.add("Body", scl=(1 - 0.08 * tuck, 1 - 0.25 * tuck, 1 + 0.1 * tuck))
        p.add("Body", scl=vol(K((0, 1.0), (49, 1.0), (52, 0.82), (56, 1.06), (62, 1.0))(t), "y"))
        p.add("Shell", scl=(1.0, 1 - 0.1 * tuck, 1 + 0.12 * tuck))
        p.add("Head", rot=(0.8 * tuck, 0, 0), scl=1 - 0.3 * tuck, loc=(0, -0.3 * tuck, 0.1 * tuck))
        for s, b in ((1, "Ant_L"), (-1, "Ant_R")):
            p.add(b, rot=(1.2 * tuck, 0, 0), scl=1 - 0.6 * tuck)
        for s, b in ((1, "Wing_L"), (-1, "Wing_R")):
            p.add(b, scl=1 - 0.7 * tuck)

        def leg(n, s):
            walk = K((60, 0.0), (64, 1.0), (76, 1.0), (80, 0.0))(t)
            ph = TAU * t / 8 + math.pi * TRIPOD[n]
            return ((0, s * 0.9 * tuck - s * 0.3 * max(0.0, math.cos(ph)) * walk, s * 0.4 * math.sin(ph) * walk),
                    1 - 0.65 * tuck)
        self.legs(p, leg)
        p.shape("Gonfle", K((0, 0.0), (12, 0.6), (50, 0.6), (53, 0.0), (80, 0.0))(t))
        return fx_layer(p, t, 80, "attack")

    def roots(self, t):
        """Se cabre, frappe le sol : trois racines gonflables surgissent devant lui puis se rétractent."""
        g = [K((0, HIDDEN), (17 + 4 * k, HIDDEN), (23 + 4 * k, 1.15), (27 + 4 * k, 0.95), (31 + 4 * k, 1.0),
               (52, 1.0), (62, HIDDEN), (72, HIDDEN))(t) for k in range(3)]
        p = self.base(Pose(), roots=g, show=[13 + 4 * k <= t <= 66 for k in range(3)])
        for k in range(3):
            p.add(f"Roots_{k + 1}", rot=(0.15 * math.sin(t * 0.35 + k), 0.12 * math.sin(t * 0.3 + 2 * k),
                                         0.4 * math.sin(t * 0.2 + k)))
        rx = K((0, 0.0), (14, 0.32), (18, -0.14), (22, -0.08), (54, -0.05), (66, 0.0))(t)
        p.add("Root", loc=(0, K((0, 0.0), (14, -0.15), (18, 0.15), (66, 0.0))(t), K((0, 0.0), (14, 0.25), (18, 0.0))(t)),
              rot=(rx, 0, 0))
        p.add("Body", scl=vol(K((0, 1.0), (14, 1.1), (18, 0.78), (23, 1.05), (30, 1.0))(t)))
        p.add("Head", rot=(K((0, 0.0), (14, -0.3), (18, 0.3), (26, 0.0))(t), 0, 0.05 * math.sin(t * 0.3)))
        for s, b in ((1, "Wing_L"), (-1, "Wing_R")):
            p.add(b, rot=(K((0, 0.0), (14, 0.4), (20, -0.1), (54, -0.1), (66, 0.0))(t),
                          -s * K((0, 0.0), (14, 0.5), (20, 0.2), (60, 0.0))(t), 0))
        for s, b in ((1, "Ant_L"), (-1, "Ant_R")):
            p.add(b, rot=(K((0, 0.0), (14, -0.6), (20, 0.3), (40, 0.0))(t), 0, 0))
        self.legs(p, lambda n, s: ((0, -s * (0.45 if n.endswith("1") else 0.0) * K((0, 0.0), (14, 1.0), (18, 0.0))(t),
                                    0), 1.0))
        p.shape("Gonfle", K((0, 0.0), (14, 0.8), (18, 0.0), (72, 0.0))(t))
        return fx_layer(p, t, 72, "attack")


FAMILY = Scarab()
