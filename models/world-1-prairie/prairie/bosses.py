"""Mini-boss (Montgolfière Solaire) et boss (Grand Zeppelin des Prairies), tous deux de type Plante."""
import math

from mathutils import Matrix, Vector

from . import geo, rig
from .elements import _leaf_on, _tilted, face, poly_leaf, shine, vine
from .families import Frame, _blimp_radius
from .materials import inflatable, mat
from .surface import Surface, decal, seam_line

TAU = math.tau


def _alt_gores(ob, axis, count, center):
    """Fuseaux alternés : index de matériau 0/1 selon l'angle autour de l'axe."""
    def fn(c):
        if axis == "Z":
            a = math.atan2(c.y - center.y, c.x - center.x)
        else:
            a = math.atan2(c.z - center.z, c.x - center.x)
        return int(((a % TAU) / TAU) * count + 1e-3) % 2
    geo.set_face_materials(ob, fn)


def _leaf_decals(F, P, spots, size, name="Motif_Feuille"):
    for k, (p, n, rot_deg) in enumerate(spots):
        up = Vector((0, 0, 1))
        from mathutils import Quaternion
        up = Quaternion(Vector(n), math.radians(rot_deg)) @ up
        col = P["accent2"] if k % 2 == 0 else P["body2"]
        vein = P["body2"] if k % 2 == 0 else P["accent2"]
        rig.add(decal(F.surf, f"{name}_{k}", [poly_leaf(10, 0.45)], p, n, up, size, 0.012 * F.s, col, subdiv=1))
        rig.add(decal(F.surf, f"{name}_{k}_Nervure", [[(-0.035, -0.8), (0.035, -0.8), (0.02, 0.85), (-0.02, 0.85)]],
                      p, n, up, size, 0.022 * F.s, vein))


# ============================================================================ MINI-BOSS : Montgolfière Solaire

def build_montgolfiere(P):
    F = Frame("montgolfiere")
    C = Vector((0, 0, 3.55))
    F.C, F.half, F.s, F.bone_size = C, Vector((1.6, 1.6, 1.85)), 4.2, 0.6
    gold = mat("Plante_Or_Solaire", "#F2B93B", rough=0.22, metal=1.0, coat=0.4)
    gore2 = inflatable("Plante_Fuseau_Clair", "#78C94A")
    petal = mat("Plante_Petale_Soleil", "#FFC928", rough=0.3, coat=0.5, emit=0.4, emit_hex="#FFB800")

    ctrl = [(0.42, 1.55), (0.62, 1.92), (1.05, 2.5), (1.45, 3.1), (1.62, 3.65), (1.58, 4.15), (1.35, 4.62),
            (0.92, 4.98), (0.45, 5.18), (0.0, 5.25)]
    pts = geo.catmull([Vector((r, z, 0)) for r, z in ctrl], 4)
    prof = [(max(p.x, 0.0), p.y) for p in pts]
    prof[-1] = (0.0, prof[-1][1])
    env = geo.lathe("Enveloppe", prof, 24, "Z", [P["body"], gore2], (0, 0, 0), caps=True)
    _alt_gores(env, "Z", 12, C)
    rig.add(env)
    F.surf = Surface([env], C)

    # Sangles (coutures porteuses) dorées entre les fuseaux
    for k in range(12):
        a = TAU * k / 12
        thetas = [x for x in range(4, 150, 9) if not (k == 3 and 62 < x < 112)]  # visage dégagé
        runs, cur = [], []
        for x in thetas:
            if cur and x - cur[-1] > 9:
                runs.append(cur)
                cur = []
            cur.append(x)
        runs.append(cur)
        for r in runs:
            dirs = [(math.sin(t) * math.cos(a), math.sin(t) * math.sin(a), math.cos(t)) for t in map(math.radians, r)]
            rig.add(seam_line(F.surf, f"Sangle_{k}", dirs, 0.022, gold))
    rig.add(geo.torus("Bouche_Cerclage", 0.43, 0.045, 32, 8, P["wood_dark"], Matrix.Translation((0, 0, 1.56))))
    ring = [(math.cos(a) * math.sin(math.radians(118)), math.sin(a) * math.sin(math.radians(118)), math.cos(math.radians(118)))
            for a in (TAU * i / 64 for i in range(64))]
    rig.add(seam_line(F.surf, "Ceinture_Or", ring, 0.035, gold, closed=True))

    # Couronne solaire : tournesol doré au sommet
    top = Vector((0, 0, 5.25))
    rig.add(geo.sphere("Couronne_Coeur", top + Vector((0, 0, 0.06)), 0.42, 24, 10, (1, 1, 0.42), P["wood_dark"]))
    for i in range(10):
        a = math.radians(i * 36)
        rig.add(geo.sphere("Couronne_Graine", top + Vector((0.25 * math.cos(a), 0.25 * math.sin(a), 0.2)),
                           0.06, 8, 4, (1, 1, 0.6), P["wood"]))
    for k in range(16):
        a = TAU * k / 16
        d = Vector((math.cos(a), math.sin(a), 0.6)).normalized()
        base = top + Vector((math.cos(a), math.sin(a), 0)) * 0.3 + Vector((0, 0, -0.02))
        L = 1.0 if k % 2 == 0 else 0.8
        rig.add(_leaf_on("Couronne_Petale", base, d, Vector((0, 0, 1)), L, L * 0.42, petal, bend=-0.05, fold=0.1,
                         nu=4, nv=1))
    rig.add(geo.torus("Couronne_Anneau", 0.44, 0.05, 32, 8, gold, Matrix.Translation(top + Vector((0, 0, -0.02)))))

    # Motifs de feuilles (décalcomanies) sur les fuseaux, sauf devant (visage)
    spots = []
    for k, az in enumerate((-65, 65, 150, 210, 270, 330)):
        a = math.radians(az + 90)
        p, n = F.surf.ray((math.cos(a), math.sin(a), 0.05 if k % 2 else -0.25))
        spots.append((p, n, -25 if k % 2 else 25))
    for az in (60, 150, 210, 300):
        a = math.radians(az + 90 + 30)
        p, n = F.surf.ray((math.cos(a), math.sin(a), 0.95))
        spots.append((p, n, 0))
    _leaf_decals(F, P, spots, 0.55)
    # Lianes décoratives qui s'enroulent autour de l'enveloppe
    for v, a0 in enumerate((110, 230, 350)):
        dirs = []
        for i in range(70):
            t = i / 69
            th = math.radians(22 + 128 * t)
            ph = math.radians(a0 + 130 * t)
            dirs.append((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
        path = [F.surf.ray(d) for d in dirs]
        vine(F, P, path, radius=0.011, leaf_every=0.08, flowers=(0.3, 0.75), leaf_size=0.08, seed=10 + v)
    # Lianes pendantes sous l'enveloppe
    for k in range(5):
        a = TAU * k / 5 + 0.5
        p0 = Vector((math.cos(a) * 0.75, math.sin(a) * 0.75, 2.0))
        pts = [p0 + Vector((0.06 * math.sin(i * 0.9), 0.06 * math.cos(i * 0.7), -0.16 * i)) for i in range(6)]
        rig.add(geo.tapered_tube("Liane_Pendante", geo.catmull(pts, 3), 0.035, 0.012, 7, P["vine"]))
        rig.add(_leaf_on("Liane_Pendante_Feuille", pts[-1], Vector((math.cos(a), math.sin(a), -1.2)).normalized(),
                         Vector((math.cos(a), math.sin(a), 0)), 0.22, 0.12, P["accent"]))

    # Nacelle en osier (bois), brûleur et sacs de lest : rigides sur l'os Nacelle
    nac = ("bone", "Nacelle")
    W, Hb = 1.15, 0.75
    rig.add(geo.box("Nacelle_Panier", (0, 0, Hb / 2), (W, W, Hb), P["wood"], bevel=0.04), nac)
    for z in (0.16, 0.42):
        rig.add(geo.box("Nacelle_Tressage", (0, 0, z), (W + 0.025, W + 0.025, 0.07), P["wood_dark"], bevel=0.02), nac)
    rim = []
    for k in range(4):
        a = math.radians(45 + 90 * k)
        rim.append(Vector((math.copysign(W / 2, math.cos(a)), math.copysign(W / 2, math.sin(a)), Hb + 0.02)))
    rig.add(geo.tube("Nacelle_Rebord", geo.resample(rim + [rim[0]], 41, closed=False), 0.045, 8, P["wood_dark"], caps=False), nac)
    for c in rim:
        rig.add(geo.cylinder("Nacelle_Montant", c * Vector((0.96, 0.96, 0)) + Vector((0, 0, 0.02)), c * Vector((0.96, 0.96, 1)),
                             0.035, 8, P["wood_dark"]), nac)
        rig.add(geo.cylinder("Bruleur_Montant", c + Vector((0, 0, 0.02)), Vector((c.x * 0.3, c.y * 0.3, 1.18)), 0.02, 6,
                             P["metal"]), nac)
    rig.add(geo.cylinder("Bruleur", (0, 0, 1.08), (0, 0, 1.3), 0.13, 16, P["metal"]), nac)
    for k in range(4):  # bras qui fixent le brûleur à son cadre
        a = math.radians(45 + 90 * k)
        rig.add(geo.cylinder("Bruleur_Bras", (0.1 * math.cos(a), 0.1 * math.sin(a), 1.18),
                             (0.32 * math.cos(a), 0.32 * math.sin(a), 1.18), 0.018, 6, P["metal"]), nac)
    rig.add(geo.torus("Bruleur_Cadre", 0.3, 0.025, 4, 6, P["metal"], Matrix.Translation((0, 0, 1.18)) @ geo.rot((0, 0, 1), 45)), nac)
    fl = geo.flame("Bruleur_Flamme", 0.42, 0.11, P["glow"], bend=0.0)
    geo.transform(fl, Matrix.Translation((0, 0, 1.32)))
    rig.add(fl, nac)
    for k, (x, y) in enumerate(((W / 2 + 0.07, 0.15), (-W / 2 - 0.07, -0.15), (0.2, -W / 2 - 0.07), (-0.2, W / 2 + 0.07))):
        rig.add(geo.sphere("Sac_Lest", (x, y, 0.36), 0.1, 12, 6, (0.8, 0.8, 1.2), P["rope"]), nac)
        rig.add(geo.cylinder("Sac_Lest_Corde", (x * 0.97, y * 0.97, 0.47), (x * 0.95, y * 0.95, Hb + 0.02), 0.01, 5, P["rope"]), nac)
    rig.add(geo.box("Nacelle_Planche", (0, 0, 0.02), (W * 1.04, W * 1.04, 0.05), P["wood_dark"], bevel=0.015), nac)

    # Cordages : de la bouche de l'enveloppe aux coins de la nacelle (déformation progressive)
    for k in range(8):
        a = TAU * k / 8 + math.pi / 8
        top_p = Vector((0.42 * math.cos(a), 0.42 * math.sin(a), 1.58))
        bot = Vector((math.copysign(min(abs(math.cos(a)) * 1.3, 1) * W / 2, math.cos(a)),
                      math.copysign(min(abs(math.sin(a)) * 1.3, 1) * W / 2, math.sin(a)), Hb + 0.04))
        path = [top_p.lerp(bot, i / 10) for i in range(11)]
        rig.add(geo.tube("Cordage", path, 0.016, 6, P["rope"], caps=True), ("blend", "Nacelle", top_p, bot))
    F.extra_bones.append(dict(name="Nacelle", head=Vector((0, 0, 1.56)), length=0.6, parent="Lobe_Bas"))
    F.patch("Lobe_Bas", (0, 0, 1.56), 0.55, 1.0)  # bouche de l'enveloppe : même os que la nacelle
    F.nacelle = "Nacelle"

    p, n = F.surf.ray((0, 1, 0.12))
    F.eyes = dict(p=p, n=n, spacing=0.42, size=0.32, up=(0, 0, 1))
    F.shine = (F.surf.ray((-0.55, 0.6, 0.7)), 0.38, 30)
    face(F, P, angry=1.15)
    shine(F, P)
    F.orbit = (C, 2.2, Vector((0, 0, 1)))
    return F


# ============================================================================ BOSS : Grand Zeppelin des Prairies

def build_zeppelin(P):
    F = Frame("zeppelin")
    L, Rm, zc = 11.0, 1.55, 2.62
    C = Vector((0, 0, zc))
    F.C, F.half, F.s, F.bone_size = C, Vector((Rm, L / 2, Rm)), 5.0, 1.0
    gold = mat("Plante_Or_Zeppelin", "#EDB43A", rough=0.2, metal=1.0, coat=0.4)
    gore2 = inflatable("Plante_Fuseau_Fonce", "#3A9A3C")

    def rad(y):
        return _blimp_radius(y / L + 0.5, Rm, 0.56)

    N = 36
    prof = []
    for i in range(N + 1):
        u = (1 - math.cos(math.pi * i / N)) / 2
        prof.append((_blimp_radius(u, Rm, 0.56) if 0 < i < N else 0.0, (u - 0.5) * L))
    env = geo.lathe("Enveloppe", prof, 28, "Y", [P["body"], gore2], C, angle0=math.pi / 28)
    _alt_gores(env, "Y", 14, C)
    rig.add(env)
    F.surf = Surface([env], C)

    # Anneaux et liserés dorés
    for k, y in enumerate((-3.2, -0.6, 2.4)):
        dirs = [(math.cos(TAU * i / 32), 0, math.sin(TAU * i / 32)) for i in range(32)]
        rig.add(seam_line(F.surf, f"Anneau_Or_{k}", dirs, 0.07, gold, closed=True, origins=[C + Vector((0, y, 0))] * 32))
    for side in (-1, 1):
        ys = [-4.3 + 8.4 * i / 30 for i in range(31)]
        rig.add(seam_line(F.surf, "Lisere_Or", [(side, 0, 0.12)] * len(ys), 0.05, gold,
                          origins=[C + Vector((0, y, 0)) for y in ys]))
    for k, a in enumerate((45, 135)):
        a = math.radians(a)
        ys = [-4.6 + 8.6 * i / 30 for i in range(31)]
        rig.add(seam_line(F.surf, f"Couture_{k}", [(math.cos(a), 0, math.sin(a))] * len(ys), 0.025, P["seam"],
                          origins=[C + Vector((0, y, 0)) for y in ys]))
    nose = geo.lathe("Nez_Or", [(0.0, L / 2 + 0.02), (0.32, L / 2 - 0.06), (0.5, L / 2 - 0.2)], 24, "Y", gold, C)
    rig.add(nose)

    # Ailerons gonflables à liseré doré
    s7 = 7.4
    fin_pts = geo.catmull([(-0.73, 0.03), (-0.30, 0.17), (-0.50, 0.40), (-0.70, 0.40), (-0.77, 0.25)], 10, closed=True)
    fin_pts = [(p.x * s7, p.y * s7) for p in geo.resample(fin_pts, 32, closed=True)]
    for k, d in enumerate(((0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0))):
        d = Vector(d)
        fin = geo.pillow(f"Aileron_{k}", fin_pts, 0.2, rings=4, edge=0.35, material=P["body2"], power=0.6)
        ey = Vector((0, 1, 0))
        M = Matrix((ey, d.cross(ey), d)).transposed().to_4x4()
        M.translation = C
        geo.transform(fin, M)
        rig.add(fin)
        edge = [M @ Vector((x, 0, z)) for x, z in fin_pts]
        rig.add(geo.tube("Aileron_Lisere", edge + [edge[0]], 0.045, 4, gold, caps=False))

    # Grandes feuilles : crête dorsale et bouquets de queue
    for k, y in enumerate((-2.6, -1.4, -0.2, 1.0)):
        p, n = F.surf.ray((0, 0, 1), C + Vector((0, y, 0)))
        Lf = (2.0 if k % 2 == 0 else 1.6)
        rig.add(_leaf_on("Crete_Feuille", p - n * 0.05, Vector((0, -0.75, 1)).normalized(), Vector((1, 0, 0)), Lf, Lf * 0.5,
                         P["accent"] if k % 2 == 0 else P["accent2"], bend=-0.12, fold=0.35))
    for k, a in enumerate((45, 135, 225, 315)):
        a = math.radians(a)
        d = Vector((math.cos(a), 0, math.sin(a)))
        p, n = F.surf.ray(d, C + Vector((0, -3.6, 0)))
        rig.add(_leaf_on("Queue_Feuille", p - n * 0.05, (Vector((0, -1, 0)) + d * 0.55).normalized(), n, 2.2, 1.0,
                         P["accent"] if k % 2 else P["accent2"], bend=0.1, fold=0.3))
    spots = []
    for side in (-1, 1):
        for y, rotd in ((-2.0, 60), (0.9, 60)):
            p, n = F.surf.ray((side, 0, 0.35), C + Vector((0, y, 0)))
            spots.append((p, n, rotd * side))
    _leaf_decals(F, P, spots, 0.75)

    # Lianes et fleurs
    for v, a0 in enumerate((20, 200)):
        path = []
        for i in range(80):
            t = i / 79
            y = -3.0 + 6.6 * t
            a = math.radians(a0 + 720 * t)
            path.append(F.surf.ray((math.cos(a), 0, math.sin(a)), C + Vector((0, y, 0))))
        vine(F, P, path, radius=0.012, leaf_every=0.16, flowers=(0.35, 0.8), leaf_size=0.1, seed=30 + v)

    # Nacelle (cabine en bois et or)
    gy, gl = 0.9, 3.4
    gz = zc - rad(gy) - 0.62
    F.patch("Lobe_Bas", (0, gy, zc - rad(gy)), 1.4, 1.8)  # ventre : cabine et suspentes
    gprof = [(0.0, -gl / 2), (0.28, -gl / 2 + 0.08), (0.45, -gl / 2 + 0.35), (0.48, -0.6), (0.48, 0.8),
             (0.42, gl / 2 - 0.3), (0.25, gl / 2 - 0.06), (0.0, gl / 2)]
    cab = geo.lathe("Cabine", gprof, 20, "Y", P["wood"], (0, gy, gz))
    geo.transform(cab, Matrix.Translation((0, gy, gz)) @ Matrix.Diagonal((1, 1, 1.2, 1)) @ Matrix.Translation((0, -gy, -gz)))
    rig.add(cab)
    for yy in (-1.2, 0.0, 1.2):
        rig.add(geo.torus("Cabine_Cerclage", 0.49, 0.035, 20, 4, gold,
                          Matrix.Translation((0, gy + yy, gz)) @ geo.rot((1, 0, 0), 90) @ Matrix.Diagonal((1, 1.2, 1, 1))))
    for side in (-1, 1):
        for k in range(4):
            yy = gy - 1.05 + 0.7 * k
            rig.add(geo.sphere("Cabine_Hublot", (side * 0.455, yy, gz + 0.12), 0.13, 8, 4, (0.3, 1, 1.15), P["glass"]))
            rig.add(geo.torus("Cabine_Hublot_Cadre", 0.135, 0.022, 8, 3, gold,
                              Matrix.Translation((side * 0.475, yy, gz + 0.12)) @ geo.rot((0, 1, 0), 90) @ Matrix.Diagonal((1.15, 1, 1, 1))))
    for yy in (-1.0, 0.0, 1.0):
        for side in (-1, 1):
            rig.add(geo.cylinder("Cabine_Suspente", (side * 0.3, gy + yy, gz + 0.45), (side * 0.5, gy + yy, zc - rad(gy + yy) + 0.15),
                                 0.035, 6, P["metal"]))

    # Hélices : 4 moteurs latéraux + hélice de queue
    props = []
    parents = {}
    for name, side, y in (("Helice_AvG", -1, 1.6), ("Helice_AvD", 1, 1.6), ("Helice_ArG", -1, -1.9), ("Helice_ArD", 1, -1.9)):
        lobe = "Lobe_Gauche" if side < 0 else "Lobe_Droite"
        parents[name] = lobe
        px = side * (rad(y) + 0.75)
        pz = zc - 0.55
        pod = geo.lathe("Moteur", [(0.0, -0.55), (0.18, -0.5), (0.26, -0.2), (0.26, 0.25), (0.18, 0.5), (0.0, 0.6)],
                        16, "Y", gold, (px, y, pz))
        rig.add(pod, ("bone", lobe))
        sp, sn = F.surf.ray((side, 0, -0.35), C + Vector((0, y, 0)))
        rig.add(geo.cylinder("Moteur_Bras", sp - sn * 0.1, Vector((px - side * 0.15, y, pz + 0.05)), 0.07, 8, P["metal"]),
                ("bone", lobe))
        F.patch(lobe, sp, 0.45, 0.9)  # pied du bras moteur : même os que le moteur et son hélice
        hub = Vector((px, y - 0.62, pz))
        props.append((name, hub, 0.62))
    tail = Vector((0, -L / 2 - 0.25, zc))
    rig.add(geo.cylinder("Queue_Moteur", tail + Vector((0, 0.45, 0)), tail, 0.18, 14, gold, r1=0.12), ("bone", "Lobe_Arriere"))
    props.append(("Helice_Queue", tail - Vector((0, 0.1, 0)), 0.9))
    parents["Helice_Queue"] = "Lobe_Arriere"
    F.patch("Lobe_Arriere", (0, -L / 2, zc), 1.0, 1.9)
    for name, hub, R in props:
        parts = [geo.sphere(name + "_Moyeu", hub, R * 0.16, 14, 8, (1, 1.4, 1), P["metal_dark"]),
                 geo.cylinder(name + "_Axe", hub, hub + Vector((0, R * 0.35, 0)), R * 0.05, 8, P["metal"])]
        for k in range(3):
            a = TAU * k / 3
            radial = Vector((math.cos(a), 0, math.sin(a)))
            blade = geo.sphere("Pale", (0, 0, 0), 1.0, 12, 6, (R * 0.22, R * 0.05, R * 0.75), P["wood"])
            M = Matrix.Translation(hub + radial * R * 0.72) @ geo.basis_z((0, 0, 0), radial, (0, 1, 0)) @ geo.rot((0, 0, 1), 28)
            geo.transform(blade, M)
            parts.append(blade)
        rig.add(geo.join(parts, name), ("bone", name))
        F.extra_bones.append(dict(name=name, head=hub, length=R * 0.5, parent=parents[name]))
        F.props.append(name)

    # Valves sur le dos
    for y in (-3.4, 2.9):
        vp, vn = F.surf.ray((0, 0, 1), C + Vector((0, y, 0)))
        rig.add(geo.cylinder("Valve", vp - vn * 0.05, vp + vn * 0.14, 0.12, 14, gold))
        rig.add(geo.torus("Valve_Bouchon", 0.11, 0.04, 14, 6, gold, geo.basis_z(vp + vn * 0.15, vn)))

    p, n = F.surf.ray((0, 1, 0.3))
    F.eyes = dict(p=p, n=n, spacing=0.6, size=0.48, up=(0, 0, 1))
    F.shine = (F.surf.ray((-0.3, 0.1, 1), C + Vector((0, 1.8, 0))), 0.8, 82)
    face(F, P, angry=1.25)
    shine(F, P)
    F.orbit = (C, 2.5, Vector((0, 1, 0)))
    return F


BUILDERS = {"montgolfiere": build_montgolfiere, "zeppelin": build_zeppelin}
