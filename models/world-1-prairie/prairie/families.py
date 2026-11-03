"""Géométrie de base des 3 familles de mobs normaux.

Chaque constructeur crée l'enveloppe et les pièces fixes de la famille, puis renvoie un `Frame` :
centre de déformation, points d'ancrage des détails élémentaires, os supplémentaires.
Avant du modèle : +Y. Point le plus bas : Z = 0. Origine de l'objet : (0, 0, 0).
"""
import math

from mathutils import Matrix, Vector

from . import geo, rig
from .surface import Surface, frame_at, seam_line

TAU = math.tau


class Frame:
    def __init__(self, kind):
        self.kind = kind
        self.C = Vector()
        self.half = Vector((1, 1, 1))
        self.s = 1.0               # échelle des détails
        self.bone_size = 0.2
        self.surf = None
        self.eyes = None           # dict(p, n, spacing, size, up)
        self.shine = None          # (p, n, taille, angle)
        self.crest = []            # [(p, n)] : sommet (le premier est le principal)
        self.under = []            # [(p, n)] : dessous (objets suspendus)
        self.emblems = []          # [(p, n, taille)] : décalcomanies latérales
        self.horns = []            # [(p, n)]
        self.orbit = None          # (centre, rayon, axe)
        self.band = []             # [(p, n)] boucle fermée sur l'enveloppe
        self.vine = []             # [(p, n)] chemin ouvert sur l'enveloppe
        self.cap_theta = 0.6
        self.chain = []            # os de la ficelle
        self.chain_pts = []
        self.string_path = []
        self.props = []            # os d'hélices
        self.nacelle = None
        self.extra_bones = []
        self.followers = {}        # os enfants de Motion qui suivent la déformation de l'enveloppe


def _ray_pairs(surf, dirs, origins=None):
    out = []
    for k, d in enumerate(dirs):
        out.append(surf.ray(d, origins[k] if origins else None))
    return out


def _string(F, P, top, length, wiggle=0.02, nb=3, radius=0.0055):
    """Ficelle souple de `top` jusqu'au sol, avec une chaîne de `nb` os."""
    top = Vector(top)
    ctrl = [top, top + Vector((wiggle * 0.8, -wiggle * 0.5, -length * 0.3)),
            top + Vector((-wiggle, wiggle * 0.3, -length * 0.62)), Vector((wiggle * 0.5, 0, top.z - length))]
    path = geo.resample(geo.catmull(ctrl, 8), 24)
    s = geo.tube("Ficelle", path, radius, 6, P["string"])
    joints = geo.resample(path, nb + 1)
    F.chain = [f"Ficelle_{i + 1}" for i in range(nb)]
    F.chain_pts = joints
    F.string_path = path
    for i in range(nb):
        F.extra_bones.append(dict(name=F.chain[i], head=joints[i], length=(joints[i + 1] - joints[i]).length,
                                  parent="Motion" if i == 0 else F.chain[i - 1]))
    rig.add(s, ("chain", F.chain, joints))
    return s


# ============================================================================ FAMILLE A : Ballon Classique

def build_classique(P):
    F = Frame("classique")
    R, H, zc = 0.33, 0.40, 0.80
    C = Vector((0, 0, zc))
    F.C, F.half, F.s, F.bone_size = C, Vector((R, R, H)), 1.0, 0.18

    prof = [(0.020, -H - 0.042), (0.028, -H - 0.016)]
    N = 24
    for i in range(N + 1):
        th = math.pi * (0.09 + 0.91 * i / N)
        z = -math.cos(th)
        r = math.sin(th)
        if z < 0:
            r *= 1 - 0.55 * (-z) ** 2.5
        prof.append((max(r, 0) * R if i < N else 0.0, z * H))
    body = geo.lathe("Enveloppe", prof, 32, "Z", P["body"], C)
    rig.add(body)
    F.surf = Surface([body], C)

    # Valve / noeud : bourrelet roulé + noeud
    kz = zc - H - 0.048
    rig.add(geo.torus("Noeud_Bourrelet", 0.024, 0.012, 20, 8, P["body"], Matrix.Translation((0, 0, kz))))
    rig.add(geo.sphere("Noeud", (0, 0, kz - 0.016), 0.017, 12, 6, (1.15, 1, 0.8), P["body"]))
    _string(F, P, (0, 0, kz - 0.026), kz - 0.026)

    # Coutures : 4 méridiens en diagonale (le visage reste dégagé)
    for k, phi in enumerate((45, 135, 225, 315)):
        p = math.radians(phi)
        dirs = [(math.sin(t) * math.cos(p), math.sin(t) * math.sin(p), math.cos(t))
                for t in (math.radians(a) for a in range(6, 165, 6))]
        rig.add(seam_line(F.surf, f"Couture_{k}", dirs, 0.0042, P["seam"]))

    p, n = F.surf.ray((0, 1, 0.14))
    F.eyes = dict(p=p, n=n, spacing=0.092, size=0.07, up=(0, 0, 1))
    F.shine = (F.surf.ray((-0.5, 0.55, 0.75)), 0.085, 35)
    F.crest = [F.surf.ray((0, 0, 1))]
    F.under = _ray_pairs(F.surf, [(math.cos(a) * 0.82, math.sin(a) * 0.82, -0.55)
                                  for a in (math.radians(x) for x in (20, 92, 164, 236, 308))])
    F.emblems = [(*F.surf.ray(d), 0.11) for d in ((-1, -0.1, 0.12), (1, -0.1, 0.12), (0, -1, 0.15))]
    F.horns = _ray_pairs(F.surf, [(-0.5, 0.12, 0.86), (0.5, 0.12, 0.86)])
    F.orbit = (C + Vector((0, 0, 0.02)), R * 1.5, Vector((0, 0, 1)))
    F.band = _ray_pairs(F.surf, [(math.cos(a), math.sin(a), -0.42) for a in (TAU * i / 64 for i in range(64))])
    vine_dirs = []
    for i in range(60):
        t = i / 59
        th = math.radians(24 + 124 * t)
        ph = math.radians(130 + 275 * t)
        vine_dirs.append((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
    F.vine = _ray_pairs(F.surf, vine_dirs)
    F.cap_theta = 0.62
    return F


# ============================================================================ FAMILLE B : Ballon Étoile

def build_etoile(P):
    F = Frame("etoile")
    Ro, Ri, T, zc = 0.46, 0.235, 0.125, 0.76
    C = Vector((0, 0, zc))
    F.C, F.half, F.s, F.bone_size = C, Vector((0.44, 0.14, 0.42)), 0.95, 0.18

    outline = geo.star_outline(Ro, Ri, 5, 120, sharp=1.45)
    foil = P["body"].copy()
    foil.name = P["body"].name.replace("Enveloppe", "Mylar")
    b = next(n for n in foil.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Metallic"].default_value = 0.55
    b.inputs["Roughness"].default_value = 0.14
    P["foil"] = foil
    body = geo.pillow("Enveloppe", outline, T, rings=10, edge=0.16, material=foil, power=0.55)
    geo.transform(body, Matrix.Translation(C))
    rig.add(body)
    F.surf = Surface([body], C)

    # Couture sertie tout autour (bord du mylar)
    rim = [C + Vector((x, 0, z)) for x, z in geo.resample([Vector(p) for p in outline], 120, closed=True)]
    rig.add(geo.tube("Couture_Sertie", rim + [rim[0]], 0.0115, 6, P["seam"], caps=False))

    # Valve plate en bas (creux entre les deux pointes basses) + noeud
    vz = zc - Ri + 0.012
    valve = geo.sphere("Valve", (0, 0, vz - 0.04), 0.045, 12, 8, (0.42, 0.16, 1.0), P["seam"])
    rig.add(valve)
    rig.add(geo.torus("Valve_Bague", 0.016, 0.007, 16, 6, P["seam"], Matrix.Translation((0, 0, vz - 0.085))))
    _string(F, P, (0, 0, vz - 0.092), vz - 0.092)

    p, n = F.surf.project(C + Vector((0, 0, 0.02)), (0, 1, 0))
    F.eyes = dict(p=p, n=Vector((0, 1, 0.05)).normalized(), spacing=0.082, size=0.064, up=(0, 0, 1))
    F.shine = (F.surf.project(C + Vector((-0.14, 0, 0.17)), (0, 1, 0)), 0.07, 40)
    F.crest = [F.surf.ray((0, 0, 1))]
    tips = [(math.sin(a), 0, math.cos(a)) for a in (math.radians(x) for x in (144, 216))]
    F.under = _ray_pairs(F.surf, tips)
    F.emblems = [(*F.surf.project(C, (0, -1, 0)), 0.14),
                 (*F.surf.project(C + Vector((-0.27, 0, 0.075)), (0, 1, 0)), 0.065),
                 (*F.surf.project(C + Vector((0.27, 0, 0.075)), (0, 1, 0)), 0.065)]
    F.horns = _ray_pairs(F.surf, [(-0.6, 0, 0.8), (0.6, 0, 0.8)])
    F.orbit = (C, Ro * 1.3, Vector((0, 1, 0)))
    band = []
    for x, z in geo.resample([Vector(p) for p in outline], 96, closed=True):
        q = C + Vector((x, 0, z)) * 0.86
        band.append(F.surf.project(q, (0, 1, 0)))
    F.band = band
    vine = []
    for i in range(70):
        t = i / 69
        a = math.radians(170 + 200 * t)
        g = ((1 + math.cos(5 * a)) / 2) ** 1.45
        r = (Ri + (Ro - Ri) * g) * 0.985
        q = C + Vector((r * math.sin(a), 0, r * math.cos(a)))
        y = 0.065 * math.sin(TAU * 4.5 * t)
        vine.append((q + Vector((0, y, 0)), Vector((math.sin(a), 0.6 * math.copysign(1, y), math.cos(a))).normalized()))
    F.vine = vine
    F.cap_theta = 0.32
    return F


# ============================================================================ FAMILLE C : Mini-dirigeable

def _blimp_radius(u, Rm, m=0.6):
    if u >= m:
        x = (u - m) / (1 - m)
        return Rm * max(1 - x ** 2.2, 0) ** 0.5
    x = (m - u) / m
    return Rm * max(1 - x ** 1.7, 0) ** 0.62


def build_dirigeable(P):
    F = Frame("dirigeable")
    L, Rm, zc = 1.6, 0.29, 0.43
    C = Vector((0, 0, zc))
    F.C, F.half, F.s, F.bone_size = C, Vector((Rm, L / 2, Rm)), 1.0, 0.22

    N = 30
    prof = []
    for i in range(N + 1):
        u = (1 - math.cos(math.pi * i / N)) / 2
        prof.append((_blimp_radius(u, Rm) if 0 < i < N else 0.0, (u - 0.5) * L))
    body = geo.lathe("Enveloppe", prof, 28, "Y", P["body"], C, angle0=math.pi / 28)
    rig.add(body)
    F.surf = Surface([body], C)

    def rad(y):
        return _blimp_radius(y / L + 0.5, Rm)

    # Ailerons gonflables (4, en croix)
    fin_pts = geo.catmull([(-0.73, 0.03), (-0.30, 0.17), (-0.50, 0.40), (-0.70, 0.40), (-0.77, 0.25)], 10, closed=True)
    fin_pts = [(p.x, p.y) for p in geo.resample(fin_pts, 72, closed=True)]
    for k, d in enumerate(((0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0))):
        d = Vector(d)
        fin = geo.pillow(f"Aileron_{k}", fin_pts, 0.032, rings=7, edge=0.05, material=P["body2"], power=0.6)
        ey = Vector((0, 1, 0))
        t = d.cross(ey)
        M = Matrix((ey, t, d)).transposed().to_4x4()
        M.translation = C
        geo.transform(fin, M)
        rig.add(fin)
        # couture du bord de l'aileron
    # Hélice arrière + moteur
    ty = -L / 2
    rig.add(geo.cylinder("Moteur", C + Vector((0, ty + 0.05, 0)), C + Vector((0, ty - 0.07, 0)), 0.04, 14,
                         P["metal"], r1=0.03))
    hub_c = C + Vector((0, ty - 0.09, 0))
    props = [geo.sphere("Helice_Moyeu", hub_c, 0.032, 14, 8, (1, 1.3, 1), P["metal_dark"])]
    for k in range(3):
        a = TAU * k / 3
        radial = Vector((math.cos(a), 0, math.sin(a)))
        blade = geo.sphere(f"Pale_{k}", (0, 0, 0), 1.0, 12, 6, (0.04, 0.009, 0.13), P["metal_dark"])
        M = Matrix.Translation(hub_c + radial * 0.12) @ geo.basis_z((0, 0, 0), radial, (0, 1, 0)) @ geo.rot((0, 0, 1), 28)
        geo.transform(blade, M)
        props.append(blade)
    prop = geo.join(props, "Helice")
    rig.add(prop, ("bone", "Helice"))
    F.extra_bones.append(dict(name="Helice", head=hub_c, length=0.1))
    F.props = ["Helice"]

    # Nacelle mécanique
    gy, gr = 0.06, 0.068
    gz = zc - rad(gy) - 0.075
    gprof = [(0.0, -0.2), (0.035, -0.19), (0.058, -0.155), (0.068, -0.09), (0.068, 0.07), (0.06, 0.14),
             (0.04, 0.18), (0.0, 0.195)]
    gond = geo.lathe("Nacelle", gprof, 18, "Y", P["body2"], (0, gy, gz))
    geo.transform(gond, Matrix.Translation((0, gy, gz)) @ Matrix.Diagonal((1, 1, 1.12, 1)) @ Matrix.Translation((0, -gy, -gz)))
    rig.add(gond)
    for yy in (-0.08, 0.11):
        rig.add(geo.torus("Nacelle_Cerclage", gr * 1.01, 0.008, 20, 6, P["metal"],
                          Matrix.Translation((0, gy + yy, gz)) @ geo.rot((1, 0, 0), 90) @ Matrix.Diagonal((1, 1.12, 1, 1))))
    for side in (-1, 1):
        for k, yy in enumerate((-0.04, 0.03, 0.10)):
            w = geo.sphere("Hublot", (side * 0.062, gy + yy, gz + 0.012), 0.022, 12, 6, (0.35, 1, 1), P["glass"])
            rig.add(w)
            rig.add(geo.torus("Hublot_Cadre", 0.022, 0.005, 14, 5, P["metal"],
                              Matrix.Translation((side * 0.066, gy + yy, gz + 0.012)) @ geo.rot((0, 1, 0), 90)))
    for yy in (-0.06, 0.16):
        top = zc - rad(gy + yy) + 0.02
        rig.add(geo.cylinder("Suspente", (0, gy + yy, gz + 0.05), (0, gy + yy, top), 0.008, 8, P["metal"]))
    # Valve sur le dos
    vp, vn = F.surf.ray((0, 0, 1), C + Vector((0, -0.32, 0)))
    rig.add(geo.cylinder("Valve", vp - vn * 0.01, vp + vn * 0.025, 0.022, 14, P["seam"]))
    rig.add(geo.torus("Valve_Bouchon", 0.02, 0.008, 14, 6, P["seam"], geo.basis_z(vp + vn * 0.028, vn)))

    # Coutures longitudinales (diagonales) + cerclages
    for k, a in enumerate((45, 135, 225, 315)):
        a = math.radians(a)
        d = Vector((math.cos(a), 0, math.sin(a)))
        ys = [-0.62 + 1.16 * i / 40 for i in range(41)]
        rig.add(seam_line(F.surf, f"Couture_L{k}", [d] * len(ys), 0.0045, P["seam"],
                          origins=[C + Vector((0, y, 0)) for y in ys]))
    for k, y in enumerate((-0.26, 0.40)):
        dirs = [(math.cos(TAU * i / 40), 0, math.sin(TAU * i / 40)) for i in range(40)]
        rig.add(seam_line(F.surf, f"Couture_C{k}", dirs, 0.0055, P["seam"], closed=True,
                          origins=[C + Vector((0, y, 0))] * 40))

    p, n = F.surf.ray((0, 1, 0.2))
    F.eyes = dict(p=p, n=n, spacing=0.092, size=0.076, up=(0, 0, 1))
    F.shine = (F.surf.ray((-0.35, 0.1, 1), C + Vector((0, 0.2, 0))), 0.12, 80)
    F.crest = [F.surf.ray((0, 0, 1), C + Vector((0, 0.08, 0))), F.surf.ray((0, 0, 1), C + Vector((0, -0.42, 0)))]
    F.under = [F.surf.ray((0, 0, -1), C + Vector((0, y, 0))) for y in (-0.4, 0.42)] + \
              [F.surf.ray((s * 0.7, 0, -0.7), C + Vector((0, y, 0))) for s in (-1, 1) for y in (-0.2, 0.25)]
    F.emblems = [(*F.surf.ray((-1, 0, 0.1), C + Vector((0, -0.05, 0))), 0.13),
                 (*F.surf.ray((1, 0, 0.1), C + Vector((0, -0.05, 0))), 0.13)]
    F.horns = [F.surf.ray((-0.55, 0, 0.83), C + Vector((0, 0.38, 0))),
               F.surf.ray((0.55, 0, 0.83), C + Vector((0, 0.38, 0)))]
    F.orbit = (C + Vector((0, 0.05, 0.02)), 0.47, Vector((0, 1, 0)))
    F.band = [F.surf.ray((math.cos(a), 0, math.sin(a)), C + Vector((0, 0.16, 0)))
              for a in (TAU * i / 56 for i in range(56))]
    vine = []
    for i in range(80):
        t = i / 79
        y = -0.24 + 0.66 * t
        a = math.radians(-60 + 560 * t)
        vine.append(F.surf.ray((math.cos(a), 0, math.sin(a)), C + Vector((0, y, 0))))
    F.vine = vine
    F.cap_theta = 0.45
    return F


BUILDERS = {"classique": build_classique, "etoile": build_etoile, "dirigeable": build_dirigeable}
