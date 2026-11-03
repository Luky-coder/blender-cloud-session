"""Javelot de Valkyrie, proposition 2 « Ailes d'argent » : variante ailée de la lance courte (1,70 m).
Fer en feuille d'argent bordé d'or avec rune ᛉ, ailes de valkyrie en plumes sur la douille, poignée gainée
de cuir blanc, pommeau doré à gemmes et éclairs violets ; targe ronde (54 cm) argent et or avec gemme
violette, ailes en relief et éclair. Style Roblox : facettes plates, pièces en blocs, motifs plats en relief.
"""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

from helpers import material


# ---------------------------------------------------------------- couleurs et matériaux
def lin(r, g, b):
    """Couleur sRGB 0-255 -> linéaire (ce qu'attend Blender)."""
    def c(x):
        x /= 255
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return (c(r), c(g), c(b))



ARGENT = material("Argent", lin(226, 231, 240), roughness=0.35, metallic=0.25)
OR = material("Or", lin(240, 186, 58), roughness=0.38, metallic=0.35)
VIOLET = material("Violet", lin(104, 58, 180), roughness=0.45, metallic=0.1)
NUIT = material("Violet_nuit", lin(44, 34, 84), roughness=0.45, metallic=0.15)
CUIR_BLANC = material("Cuir_blanc", lin(236, 226, 208), roughness=0.7)
GEMME = material("Gemme", lin(170, 100, 255), roughness=0.2, emission=lin(150, 70, 255), emission_strength=1.2)
ECLAIR = material("Eclair", lin(205, 130, 255), roughness=0.3, emission=lin(175, 90, 255), emission_strength=1.6)
ETINCELLE = material("Etincelle", lin(255, 236, 255), roughness=0.3, emission=lin(255, 200, 255), emission_strength=1.0)


# ---------------------------------------------------------------- géométrie 2D (u = X, v = Z)
def area(pts):
    return 0.5 * sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts)))


def offset(pts, d, limit=2.5):
    """Décale un polygone fermé de d vers l'extérieur (d < 0 : vers l'intérieur), joints en onglet."""
    s = 1 if area(pts) > 0 else -1
    out = []
    for i in range(len(pts)):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
        e1, e2 = (p1 - p0).normalized(), (p2 - p1).normalized()
        n1, n2 = Vector((e1.y, -e1.x)) * s, Vector((e2.y, -e2.x)) * s
        m = n1 + n2
        m = m.normalized() if m.length > 1e-6 else n1
        q = p1 + m * (d / max(m.dot(n1), 1 / limit))
        out.append((q.x, q.y))
    return out


def mirror(half):
    """Demi-profil (u >= 0, du bas vers le haut) -> polygone symétrique complet."""
    return half + [(-u, v) for u, v in reversed(half) if u > 1e-9]


def circle(r, n, phase=-math.pi / 2, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(phase + 2 * math.pi * k / n), cy + r * math.sin(phase + 2 * math.pi * k / n))
            for k in range(n)]


def stroke(pts, w, w_end=None):
    """Polyligne ouverte -> polygone de largeur w (qui peut s'affiner jusqu'à w_end)."""
    left, right = [], []
    for i, p in enumerate(pts):
        p = Vector(p)
        segs = []
        if i > 0:
            segs.append((p - Vector(pts[i - 1])).normalized())
        if i < len(pts) - 1:
            segs.append((Vector(pts[i + 1]) - p).normalized())
        normals = [Vector((-d.y, d.x)) for d in segs]
        m = sum(normals, Vector((0, 0))).normalized()
        wi = w if w_end is None else w + (w_end - w) * i / (len(pts) - 1)
        k = (wi / 2) / max(m.dot(normals[0]), 0.35)
        left.append(tuple(p + m * k))
        right.append(tuple(p - m * k))
    return left + right[::-1]


_SEG = [0]


def segments(bm, pts, w, y0, y1, M=None):
    """Tracé anguleux : un bloc par segment, chacun à une profondeur légèrement différente
    (des faces coplanaires qui se chevauchent font des taches noires au rendu)."""
    for p, q in zip(pts, pts[1:]):
        p, q = Vector(p), Vector(q)
        d = (q - p).normalized() * w * 0.45
        _SEG[0] += 1
        e = 0.00035 * (_SEG[0] % 4)
        slab(bm, stroke([tuple(p - d), tuple(q + d)], w), y0 - e, y1 + (e if y1 > 0.005 else 0), M)


def place(pts, scale=1.0, rot=0.0, at=(0.0, 0.0)):
    c, s = math.cos(rot), math.sin(rot)
    return [(at[0] + scale * (c * u - s * v), at[1] + scale * (s * u + c * v)) for u, v in pts]


# ---------------------------------------------------------------- briques 3D (ajoutées à un bmesh)
def _xf(bm, verts, M):
    if M is not None:
        bmesh.ops.transform(bm, matrix=M, verts=verts)


def slab(bm, pts, y0, y1, M=None):
    """Polygone du plan XZ extrudé entre y0 et y1."""
    if area(pts) < 0:
        pts = pts[::-1]
    a = [bm.verts.new((u, y0, v)) for u, v in pts]
    b = [bm.verts.new((u, y1, v)) for u, v in pts]
    bm.faces.new(a)
    bm.faces.new(b[::-1])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((a[i], a[j], b[j], b[i]))
    _xf(bm, a + b, M)


def ring(bm, outer, inner, y0, y1, M=None):
    """Bande entre deux polygones de même nombre de points (contour, liseré, jante)."""
    if area(outer) < 0:
        outer, inner = outer[::-1], inner[::-1]
    ao = [bm.verts.new((u, y0, v)) for u, v in outer]
    bo = [bm.verts.new((u, y1, v)) for u, v in outer]
    ai = [bm.verts.new((u, y0, v)) for u, v in inner]
    bi = [bm.verts.new((u, y1, v)) for u, v in inner]
    for i in range(len(outer)):
        j = (i + 1) % len(outer)
        bm.faces.new((ao[i], ao[j], ai[j], ai[i]))
        bm.faces.new((bo[i], bi[i], bi[j], bo[j]))
        bm.faces.new((ao[i], bo[i], bo[j], ao[j]))
        bm.faces.new((ai[i], ai[j], bi[j], bi[i]))
    _xf(bm, ao + bo + ai + bi, M)


def outline(bm, pts, w, y0, y1, M=None):
    ring(bm, offset(pts, w / 2), offset(pts, -w / 2), y0, y1, M)


def loft(bm, prof, n=8, phase=None, sx=1.0, sy=1.0, M=None):
    """Solide de révolution à facettes le long de Z. prof = [(z, rayon)], rayon 0 = pointe."""
    phase = math.pi / n if phase is None else phase
    rings = []
    for z, r in prof:
        if r <= 0:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((sx * r * math.cos(phase + 2 * math.pi * k / n),
                                        sy * r * math.sin(phase + 2 * math.pi * k / n), z)) for k in range(n)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(n):
            q = [r0[k % len(r0)], r0[(k + 1) % len(r0)], r1[(k + 1) % len(r1)], r1[k % len(r1)]]
            q = [v for i, v in enumerate(q) if v not in q[:i]]
            bm.faces.new(q)
    for rg in (rings[0], rings[-1]):
        if len(rg) > 2:
            bm.faces.new(rg)
    _xf(bm, [v for rg in rings for v in rg], M)


def prism(bm, r, z0, z1, n=8, r1=None, M=None, **kw):
    loft(bm, [(z0, r), (z1, r if r1 is None else r1)], n, M=M, **kw)


def box(bm, size, loc, rot=(0, 0, 0)):
    M = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*size, 1))
    bmesh.ops.create_cube(bm, size=1.0, matrix=M)


def beam(bm, p0, p1, t):
    """Poutre de section carrée t entre deux points 3D."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    M = (Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
         @ Matrix.Diagonal((t, t, d.length + t * 0.9, 1)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=M)


def diamond(bm, loc, r, stretch=1.0):
    """Petit octaèdre (étincelle, clou en losange)."""
    x, y, z = loc
    vs = [bm.verts.new(p) for p in ((x + r, y, z), (x, y + r, z), (x - r, y, z), (x, y - r, z),
                                     (x, y, z + r * stretch), (x, y, z - r * stretch))]
    for k in range(4):
        bm.faces.new((vs[k], vs[(k + 1) % 4], vs[4]))
        bm.faces.new((vs[(k + 1) % 4], vs[k], vs[5]))


def arc(bm, rng, a, c, b, n=8, jitter=0.012, t=0.0075, forks=1):
    """Arc électrique stylisé : courbe a -> b tirée vers c, cassée en zigzag de poutres carrées,
    avec de petites fourches. Renvoie les points du zigzag."""
    a, c, b = Vector(a), Vector(c), Vector(b)
    normal = (c - a).cross(b - a)
    if normal.length < 1e-9:
        normal = (b - a).orthogonal()
    normal.normalize()
    pts = []
    for i in range(n + 1):
        s = i / n
        p = (1 - s) ** 2 * a + 2 * (1 - s) * s * c + s * s * b
        if 0 < i < n:
            tan = (2 * (1 - s) * (c - a) + 2 * s * (b - c)).normalized()
            side = normal.cross(tan).normalized()
            p = p + side * (1 if i % 2 else -1) * jitter * rng.uniform(0.55, 1.0) \
                + normal * jitter * rng.uniform(-0.4, 0.4)
        pts.append(p)
    for i in range(n):
        taper = 1 - 0.4 * abs(2 * i / max(n - 1, 1) - 1)    # plus épais au milieu de l'arc
        beam(bm, pts[i], pts[i + 1], t * taper)
    for _ in range(forks):
        k = rng.randint(2, n - 2)
        out = pts[k] - Vector((0, 0, pts[k].z))              # s'éloigne de l'axe de la lance
        d = (out.normalized() + Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5),
                                        rng.uniform(-0.3, 0.6)))).normalized()
        e = pts[k] + d * rng.uniform(0.035, 0.055)
        arc(bm, rng, pts[k], (pts[k] + e) / 2, e, n=3, jitter=jitter * 0.6, t=t * 0.65, forks=0)
    return pts


# ---------------------------------------------------------------- objets
PARTS = {}


def collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def empty(name, col, loc=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_type = "PLAIN_AXES"
    ob.empty_display_size = 0.15
    ob.location = loc
    ob.parent = parent
    col.objects.link(ob)
    return ob


def part(name, mat, parent):
    """bmesh d'un objet (un objet = un matériau, comme une MeshPart Roblox)."""
    if name not in PARTS:
        PARTS[name] = (bmesh.new(), mat, parent)
    return PARTS[name][0]


def finish():
    for name, (bm, mat, parent) in PARTS.items():
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        ob = bpy.data.objects.new(name, me)
        parent.users_collection[0].objects.link(ob)
        ob.parent = parent


# ---------------------------------------------------------------- ailes de valkyrie
PLUME = [(0.0, -0.42), (0.70, -1.0), (1.0, -0.22), (0.86, 0.55), (0.0, 0.42)]   # (le long, travers)
# (position le long du bras, angle par rapport au bras en degrés, longueur relative au bras)
PLUMES = ((0.08, -122, 0.30), (0.26, -102, 0.38), (0.44, -82, 0.46), (0.62, -60, 0.53), (0.79, -38, 0.60),
          (0.94, -14, 0.70))


def wing(root, tip, side=1, bulge=0.14, wscale=1.0):
    """Aile droite (side=1) ou gauche (side=-1) dans le plan XZ : bras courbe de root à tip, plumes qui
    pendent dessous en éventail. Renvoie (bras, [(plume, nervure, pointe), ...])."""
    R, W = Vector(root), Vector(tip)
    D = W - R
    A = D.length
    alpha = math.atan2(D.y, D.x)
    C = (R + W) / 2 + Vector((-D.y, D.x)).normalized() * A * bulge

    def curve(t):
        return (1 - t) ** 2 * R + 2 * (1 - t) * t * C + t * t * W

    def flip(pts):
        return [(side * u, v) for u, v in pts]

    arm = flip(stroke([tuple(curve(i / 8)) for i in range(9)], 0.20 * A * wscale, 0.07 * A * wscale))
    feathers = []
    for t, rel, lr in PLUMES:
        p, ang, L, w = tuple(curve(t)), alpha + math.radians(rel), lr * A, 0.15 * A * wscale
        feathers.append((flip(place([(L * a, w * b) for a, b in PLUME], 1.0, ang, p)),
                         flip(place([(0.10 * L, 0.0), (0.78 * L, 0.0)], 1.0, ang, p)),
                         flip(place([(L, 0.0)], 1.0, ang, p))[0]))
    return arm, feathers


# ================================================================ LE JAVELOT
# Debout le long de Z, pointe en haut, pommeau sur Z = 0, fer à plat face à -Y.
col_j = collection("Javelot")
JAV = empty("Javelot", col_j)
ECL = empty("Javelot_Eclairs", col_j, parent=JAV)

R_HAMPE = 0.023
Z_LAME = 1.232            # base du fer
L_LAME = 0.465            # longueur du fer

# --- Pommeau doré à facettes, serti de gemmes
bm = part("Javelot_Pommeau", OR, JAV)
loft(bm, [(0.0, 0.0), (0.016, 0.022), (0.040, 0.032), (0.060, 0.024), (0.068, 0.019), (0.072, 0.028),
          (0.092, 0.028), (0.096, 0.024)])
bm = part("Javelot_Gemmes", GEMME, JAV)
for k in range(4):
    th = math.pi / 4 + k * math.pi / 2
    diamond(bm, (0.031 * math.cos(th), 0.031 * math.sin(th), 0.040), 0.0085, 1.3)

# --- Hampe violet nuit, bagues dorées, poignée en cuir blanc enroulé
prism(part("Javelot_Hampe", NUIT, JAV), R_HAMPE, 0.090, 1.078)
bm = part("Javelot_Bagues", OR, JAV)
for z0, z1 in ((0.300, 0.310), (0.318, 0.328), (0.488, 0.504), (0.806, 0.822), (0.960, 0.970), (0.978, 0.988)):
    prism(bm, 0.0265, z0, z1)
bm = part("Javelot_Poignee", CUIR_BLANC, JAV)
for i in range(9):
    prism(bm, 0.0262, -0.012, 0.012,
          M=Matrix.Translation((0, 0, 0.522 + i * 0.0335)) @ Matrix.Rotation(math.radians(14), 4, "X"))

# --- Douille : bagues, bande violette sertie, cône d'argent, ailes de valkyrie
bm = part("Javelot_Douille_Or", OR, JAV)
prism(bm, 0.029, 1.072, 1.090)
prism(bm, 0.029, 1.130, 1.146)
prism(bm, 0.021, 1.220, 1.236)
prism(part("Javelot_Douille_Bande", VIOLET, JAV), 0.027, 1.090, 1.130)
bm = part("Javelot_Gemmes", GEMME, JAV)
for k in range(4):
    th = -math.pi / 2 + k * math.pi / 2
    diamond(bm, (0.026 * math.cos(th), 0.026 * math.sin(th), 1.110), 0.0075, 1.4)
loft(part("Javelot_Douille_Cone", ARGENT, JAV), [(1.146, 0.026), (1.185, 0.0225), (1.222, 0.0175)])

bm_pl = part("Javelot_Ailes_Plumes", ARGENT, JAV)
bm_or = part("Javelot_Ailes_Or", OR, JAV)
wing_tips = []
for side in (1, -1):
    arm, feathers = wing((0.016, 1.160), (0.136, 1.284), side)
    for k, (pts, quill, tip) in enumerate(feathers):
        h = 0.0085 - 0.0007 * k            # les plumes intérieures recouvrent les suivantes
        slab(bm_pl, pts, -h, h)
        slab(bm_or, stroke(quill, 0.0040), -h - 0.0012, h + 0.0012)
        wing_tips.append(tip)
    slab(bm_or, arm, -0.0115, 0.0115)
    outline(bm_pl, arm, 0.0035, -0.0125, 0.0125)
    for y in (-0.0125, 0.0125):
        diamond(part("Javelot_Gemmes", GEMME, JAV), (side * 0.040, y, 1.186), 0.0075, 1.3)

# --- Fer en feuille : liseré d'or, corps d'argent, panneau violet gravé d'une rune ᛉ
LAME = mirror([(0.016, 0.000), (0.022, 0.018), (0.046, 0.055), (0.064, 0.105), (0.069, 0.150),
               (0.064, 0.215), (0.050, 0.290), (0.032, 0.360), (0.014, 0.422), (0.0, L_LAME)])
PANNEAU = mirror([(0.0, 0.048), (0.016, 0.074), (0.033, 0.128), (0.035, 0.176), (0.026, 0.250),
                  (0.012, 0.322), (0.0, 0.362)])
M_LAME = Matrix.Translation((0, 0, Z_LAME))
slab(part("Javelot_Fer_Fil", OR, JAV), LAME, -0.0055, 0.0055, M_LAME)
slab(part("Javelot_Fer_Corps", ARGENT, JAV), offset(LAME, -0.0115), -0.0105, 0.0105, M_LAME)
slab(part("Javelot_Fer_Panneau", VIOLET, JAV), PANNEAU, -0.0125, 0.0125, M_LAME)
bm = part("Javelot_Fer_Gravures", OR, JAV)
outline(bm, offset(PANNEAU, 0.0035), 0.0045, -0.0132, 0.0132, M_LAME)
for line in ([(0, 0.084), (0, 0.160)], [(-0.017, 0.152), (0, 0.128), (0.017, 0.152)], [(0, 0.182), (0, 0.330)]):
    segments(bm, line, 0.0055, -0.0136, 0.0136, M_LAME)

# --- Électricité violette : arcs autour du fer et entre les pointes des ailes
rng = random.Random(5)
bm = part("Javelot_Eclairs_Arcs", ECLAIR, ECL)
tr, tl = wing_tips[len(PLUMES) - 1], wing_tips[-1]
ARCS = (
    ((0.066, 0.004, 1.400), (0.175, -0.055, 1.450), (0.052, -0.004, 1.525)),
    ((-0.066, 0.004, 1.370), (-0.170, 0.055, 1.420), (-0.058, -0.004, 1.495)),
    ((0.030, 0.000, 1.610), (0.120, 0.045, 1.660), (0.010, 0.000, 1.685)),
    ((-0.030, 0.000, 1.600), (-0.110, -0.050, 1.640), (-0.012, 0.000, 1.678)),
    ((tr[0], 0.004, tr[1]), (0.150, -0.050, 1.390), (0.068, 0.000, 1.400)),
    ((tl[0], -0.004, tl[1]), (-0.150, 0.050, 1.380), (-0.068, 0.000, 1.390)),
    ((0.024, -0.020, 1.100), (0.100, -0.070, 1.040), (0.024, -0.012, 0.985)),
    ((0.068, 0.000, 1.460), (0.190, 0.020, 1.500), (0.215, -0.030, 1.575)),
    ((-0.068, 0.000, 1.430), (-0.190, -0.020, 1.480), (-0.210, 0.030, 1.555)))
tips = []
for a, c, b in ARCS:
    tips += arc(bm, rng, a, c, b, n=8, forks=1)[2::3]
bm = part("Javelot_Eclairs_Etincelles", ETINCELLE, ECL)
for p in rng.sample(tips, 12):
    off = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.5, 1))).normalized() * 0.035
    diamond(bm, p + off, 0.0085, 1.7)

# ================================================================ LA TARGE
# Debout sur sa jante, face avant tournée vers -Y, à droite du javelot.
col_t = collection("Targe")
R_T = 0.270
TAR = empty("Targe", col_t, loc=(0.62, 0, R_T))
N_T = 24
Y_FACE = -0.012
TO_FRONT = Matrix.Rotation(math.radians(90), 4, "X")   # +Z local -> -Y (vers l'avant)


def polar(r, deg):
    return (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)))


slab(part("Targe_Plateau", ARGENT, TAR), circle(0.244, N_T), Y_FACE, -Y_FACE)
ring(part("Targe_Jante", OR, TAR), circle(R_T, N_T), circle(0.238, N_T), -0.024, 0.014)
bm = part("Targe_Gemmes", GEMME, TAR)
for k in range(8):
    u, v = polar(0.254, 90 + 45 * k)
    diamond(bm, (u, -0.024, v), 0.0095, 1.0)
outline(part("Targe_Cercle", VIOLET, TAR), circle(0.222, N_T), 0.010, Y_FACE - 0.0015, Y_FACE + 0.001)

# --- Umbo : collerette dorée, coupe à facettes, grosse gemme violette
bm = part("Targe_Umbo_Or", OR, TAR)
loft(bm, [(0.010, 0.088), (0.022, 0.088), (0.026, 0.080)], n=12, M=TO_FRONT)
loft(bm, [(0.026, 0.064), (0.046, 0.057), (0.054, 0.042)], n=8, M=TO_FRONT)
loft(part("Targe_Umbo_Gemme", GEMME, TAR), [(0.050, 0.042), (0.062, 0.031), (0.074, 0.0)], n=8, M=TO_FRONT)
bm = part("Targe_Rivets", ARGENT, TAR)
for k in range(8):
    u, v = polar(0.076, 22.5 + 45 * k)
    loft(bm, [(0.023, 0.0065), (0.027, 0.0065), (0.030, 0.0035)], M=TO_FRONT @ Matrix.Translation((u, v, 0)))

# --- Ailes en relief de part et d'autre de l'umbo
bm_ai = part("Targe_Ailes", OR, TAR)
bm_q = part("Targe_Ailes_Nervures", VIOLET, TAR)
for side in (1, -1):
    arm, feathers = wing((0.072, 0.026), (0.152, 0.112), side, wscale=1.45)
    for k, (pts, quill, tip) in enumerate(feathers):
        y0 = Y_FACE - 0.0034 + 0.0003 * k
        slab(bm_ai, pts, y0, Y_FACE + 0.001)
        slab(bm_q, stroke(quill, 0.0038), y0 - 0.0008, Y_FACE + 0.001)
    slab(bm_ai, arm, Y_FACE - 0.0048, Y_FACE + 0.001)
    outline(bm_q, arm, 0.0035, Y_FACE - 0.0056, Y_FACE + 0.001)

# --- Éclair sous l'umbo, rune ᛉ au-dessus
FOUDRE = [(-0.15, 0.50), (0.26, 0.50), (0.04, 0.12), (0.30, 0.12), (-0.22, -0.50), (-0.04, -0.06),
          (-0.30, -0.06)]
pts = place(FOUDRE, 0.112, 0.0, (0.0, -0.158))
slab(part("Targe_Foudre", VIOLET, TAR), pts, Y_FACE - 0.0018, Y_FACE + 0.001)
bm = part("Targe_Motifs_Or", OR, TAR)
outline(bm, pts, 0.008, Y_FACE - 0.0028, Y_FACE + 0.001)
for line in ([(0, 0.112), (0, 0.200)], [(-0.032, 0.196), (0, 0.160), (0.032, 0.196)]):
    segments(bm, line, 0.010, Y_FACE - 0.003, Y_FACE + 0.001)

# --- Dos : poignée et sangle de bras en cuir blanc, ferrures dorées
bm = part("Targe_Dos_Cuir", CUIR_BLANC, TAR)
box(bm, (0.150, 0.024, 0.026), (0, 0.054, 0.0))
box(bm, (0.220, 0.008, 0.050), (0, 0.050, -0.140))
bm = part("Targe_Dos_Ferrures", OR, TAR)
for x in (-0.085, 0.085):
    box(bm, (0.022, 0.050, 0.036), (x, 0.036, 0.0))
for x in (-0.122, 0.122):
    box(bm, (0.026, 0.044, 0.060), (x, 0.032, -0.140))
ring(bm, circle(0.230, N_T), circle(0.216, N_T), 0.011, 0.016)

finish()
