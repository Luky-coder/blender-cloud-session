"""Javelot de Valkyrie « Ailes d'argent » : lance courte à une main (1,70 m). Fer en feuille d'argent bien
en volume (arête centrale, 7 cm d'épaisseur), biseau d'or, panneau violet orné d'une rune ᛉ, d'une plume
gravée, d'un double filet et de perles d'or ; ailes de valkyrie en plumes barbées d'or sur la douille,
poignée gainée de cuir blanc, bandeau de tissu violet noué au bas de la hampe, pommeau doré serti de
gemmes violettes. Targe ronde (54 cm) argent et or :
gemme violette, ailes en relief, cimier de plumes, éclair, volutes en filigrane et cercle perlé.
Style Roblox : facettes plates, pièces en blocs, motifs en relief.
"""
import math

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
TISSU = material("Tissu_violet", lin(126, 72, 206), roughness=0.85)
CUIR_BLANC = material("Cuir_blanc", lin(236, 226, 208), roughness=0.7)
GEMME = material("Gemme", lin(170, 100, 255), roughness=0.2, emission=lin(150, 70, 255), emission_strength=1.2)


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


def spiral(c, r0, r1, turns, a0=0.0, sense=1, n=None):
    """Volute : spirale de rayon r0 -> r1 autour de c."""
    n = n or max(8, int(18 * turns))
    return [(c[0] + (r0 + (r1 - r0) * i / n) * math.cos(a0 + sense * 2 * math.pi * turns * i / n),
             c[1] + (r0 + (r1 - r0) * i / n) * math.sin(a0 + sense * 2 * math.pi * turns * i / n)) for i in range(n + 1)]


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


def beam(bm, p0, p1, t, ext=0.9):
    """Poutre de section carrée t entre deux points 3D (prolongée de ext * t pour bien raccorder)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    M = (Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
         @ Matrix.Diagonal((t, t, d.length + t * ext, 1)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=M)


def diamond(bm, loc, r, stretch=1.0):
    """Petit octaèdre (gemme, clou en losange)."""
    x, y, z = loc
    vs = [bm.verts.new(p) for p in ((x + r, y, z), (x, y + r, z), (x - r, y, z), (x, y - r, z),
                                     (x, y, z + r * stretch), (x, y, z - r * stretch))]
    for k in range(4):
        bm.faces.new((vs[k], vs[(k + 1) % 4], vs[4]))
        bm.faces.new((vs[(k + 1) % 4], vs[k], vs[5]))


# ---------------------------------------------------------------- lames en volume (section en losange)
def _const(h):
    return h if callable(h) else (lambda u, v: h)


def roof(bm, outline, ridge, he, hr, M=None):
    """Solide « en toit » dans le plan XZ : chaque face (avant et arrière) monte du contour (demi-épaisseur
    he) jusqu'à la ligne de faîte `ridge` (demi-épaisseur hr). Donne une lame à arête centrale, à facettes.
    he et hr : nombres ou fonctions (u, v) -> demi-épaisseur."""
    he, hr = _const(he), _const(hr)
    cum = [0.0]
    for a, b in zip(ridge, ridge[1:]):
        cum.append(cum[-1] + (Vector(b) - Vector(a)).length)

    def project(p):
        best = (1e9, 0.0)
        for k, (a, b) in enumerate(zip(ridge, ridge[1:])):
            a, b, p_ = Vector(a), Vector(b), Vector(p)
            d = b - a
            t = max(0.0, min(1.0, (p_ - a).dot(d) / d.length_squared))
            best = min(best, ((a + d * t - p_).length, cum[k] + t * d.length))
        return round(best[1], 7)

    def at(s):
        for k in range(len(ridge) - 1):
            if s <= cum[k + 1] + 1e-9 or k == len(ridge) - 2:
                a, b = Vector(ridge[k]), Vector(ridge[k + 1])
                return a + (b - a) * ((s - cum[k]) / (cum[k + 1] - cum[k]))

    s_out = [project(p) for p in outline]
    s_all = sorted(set(s_out) | {round(c, 7) for c in cum if min(s_out) <= round(c, 7) <= max(s_out)})
    idx = {s: i for i, s in enumerate(s_all)}
    rp = [at(s) for s in s_all]
    n, sides, new = len(outline), [], []
    for sign in (-1, 1):
        O = [bm.verts.new((u, sign * he(u, v), v)) for u, v in outline]
        R = [bm.verts.new((p.x, sign * hr(p.x, p.y), p.y)) for p in rp]
        for i in range(n):
            a, b = idx[s_out[i]], idx[s_out[(i + 1) % n]]
            seq = range(a, b + 1) if a <= b else range(a, b - 1, -1)
            bm.faces.new([O[i], O[(i + 1) % n]] + [R[k] for k in reversed(list(seq))])
        sides.append(O)
        new += O + R
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((sides[0][i], sides[0][j], sides[1][j], sides[1][i]))
    _xf(bm, new, M)


def half_width(half, v):
    """Demi-largeur à la hauteur v d'un demi-profil (u >= 0) monotone en v."""
    for (u0, v0), (u1, v1) in zip(half, half[1:]):
        if v0 <= v <= v1 and v1 > v0:
            return u0 + (u1 - u0) * (v - v0) / (v1 - v0)
    return half[0][0] if v < half[0][1] else 0.0


def leaf_height(half, he, hr):
    """Demi-épaisseur d'une feuille à arête centrale (u = 0) : he au bord, hr sur l'arête."""
    def h(u, v):
        hw = half_width(half, v)
        return he if hw < 1e-6 else he + (hr - he) * max(0.0, 1 - abs(u) / hw)
    return h


def lifted(bm, lines, h, t, M=None, ext=0.9, sub=1):
    """Traits en relief posés sur une surface de demi-épaisseur h(u, v), sur les deux faces.
    sub : découpe de chaque segment pour suivre la surface (ext=0 alors, sinon les morceaux se chevauchent)."""
    M = M or Matrix()
    for sign in (-1, 1):
        for line in lines:
            pts = [tuple(Vector(p).lerp(Vector(q), k / sub)) for p, q in zip(line, line[1:]) for k in range(sub)]
            pts.append(line[-1])
            for p, q in zip(pts, pts[1:]):
                beam(bm, M @ Vector((p[0], sign * h(*p), p[1])), M @ Vector((q[0], sign * h(*q), q[1])), t, ext)


def cloth(bm, t0, t1, rows, length, width, thick, sway, twist, notch=0.0, crease=0.004, M=None):
    """Pan de tissu qui pend le long de -Z (largeur selon X), de la fraction t0 à t1 de sa longueur :
    ondule vers l'avant (sway), vrille (twist, radians), plis à facettes (crease), bout fendu (notch)."""
    rows_v = []
    for i in range(rows + 1):
        t = t0 + (t1 - t0) * i / rows
        tw = twist * t
        xd, nd = Vector((math.cos(tw), math.sin(tw), 0)), Vector((-math.sin(tw), math.cos(tw), 0))
        c = Vector((0, 0, -length * t)) - nd * sway * math.sin(math.pi * 1.1 * t)
        w = width * (1 - 0.12 * t)
        mid = c - nd * crease * (1 if i % 2 else -1) + Vector((0, 0, notch if (i == rows and t1 >= 1) else 0))
        row = [c - xd * w / 2, mid, c + xd * w / 2]
        rows_v.append(([bm.verts.new(p - nd * thick / 2) for p in row], [bm.verts.new(p + nd * thick / 2) for p in row]))
    for (f0, b0), (f1, b1) in zip(rows_v, rows_v[1:]):
        for j in range(2):
            bm.faces.new((f0[j], f0[j + 1], f1[j + 1], f1[j]))
            bm.faces.new((b0[j], b1[j], b1[j + 1], b0[j + 1]))
        bm.faces.new((f0[0], f1[0], b1[0], b0[0]))
        bm.faces.new((f0[2], b0[2], b1[2], f1[2]))
    (ft, bt), (fb, bb) = rows_v[0], rows_v[-1]
    bm.faces.new(ft + bt[::-1])
    for j in range(2):
        bm.faces.new((fb[j], bb[j], bb[j + 1], fb[j + 1]))
    _xf(bm, [v for f, b in rows_v for v in f + b], M)


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
    pendent dessous en éventail. Renvoie (bras, [(plume, nervure, pointe, barbes), ...], arête du bras)."""
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
                         flip(place([(L, 0.0)], 1.0, ang, p))[0],
                         [flip(place([(c + 0.13 * L, 0.36 * w), (c, 0.0), (c + 0.13 * L, -0.60 * w)], 1.0, ang, p))
                          for c in (0.30 * L, 0.52 * L)]))
    ridge = flip([tuple(curve(0.05 + 0.9 * i / 8)) for i in range(9)])
    return arm, feathers, ridge


# ================================================================ LE JAVELOT
# Debout le long de Z, pointe en haut, pommeau sur Z = 0, fer à plat face à -Y.
col_j = collection("Javelot")
JAV = empty("Javelot", col_j)

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

# --- Bandeau : ruban violet noué sous les bagues dorées, deux pans fendus à bande dorée
Z_NOEUD = 0.250
bm_t = part("Javelot_Bandeau", TISSU, JAV)
bm_tor = part("Javelot_Bandeau_Or", OR, JAV)
prism(bm_t, 0.0262, Z_NOEUD - 0.014, Z_NOEUD + 0.012)
box(bm_t, (0.024, 0.012, 0.022), (0, -0.0285, Z_NOEUD), rot=(0, math.pi / 4, 0))
for x0, y0, rz, length, sway, twist in ((0.019, -0.024, -0.65, 0.140, 0.012, 0.30),
                                       (-0.019, -0.024, 0.65, 0.118, 0.010, -0.30)):
    M = Matrix.Translation((x0, y0, Z_NOEUD - 0.004)) @ Matrix.Rotation(rz, 4, "Z")
    cloth(bm_t, 0.0, 1.0, 5, length, 0.025, 0.0040, sway, twist, notch=0.013, crease=0.0, M=M)
    cloth(bm_tor, 0.68, 0.78, 1, length, 0.0262, 0.0064, sway, twist, crease=0.0, M=M)

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
for side in (1, -1):
    arm, feathers, ridge = wing((0.016, 1.160), (0.136, 1.284), side)
    for k, (pts, quill, tip, barbs) in enumerate(feathers):
        h = 0.0095 - 0.0008 * k            # les plumes intérieures recouvrent les suivantes
        slab(bm_pl, pts, -h, h)
        slab(bm_or, stroke(quill, 0.0042), -h - 0.0025, h + 0.0025)
        for chev in barbs:                 # barbes dorées en chevrons
            segments(bm_or, chev, 0.0030, -h - 0.0008, h + 0.0008)
    roof(bm_or, arm, ridge, 0.0080, 0.0185)                            # bras doré à arête
    roof(bm_pl, offset(arm, 0.0035), ridge, 0.0050, 0.0145)            # liseré d'argent dessous
    for y in (-0.0185, 0.0185):
        diamond(part("Javelot_Gemmes", GEMME, JAV), (side * 0.040, y, 1.186), 0.0075, 1.3)

# --- Fer en feuille, très en volume : biseau d'or du tranchant, corps d'argent à arête centrale (7 cm
#     d'épaisseur au panneau), panneau violet en relief ; dorures : rune ᛉ, plume gravée, double filet, perles
FEUILLE = [(0.016, 0.000), (0.022, 0.018), (0.046, 0.055), (0.064, 0.105), (0.069, 0.150), (0.064, 0.215),
           (0.050, 0.290), (0.032, 0.360), (0.014, 0.422), (0.0, L_LAME)]
PANNEAU_D = [(0.0, 0.048), (0.016, 0.074), (0.033, 0.128), (0.035, 0.176), (0.026, 0.250), (0.012, 0.322),
             (0.0, 0.362)]
M_LAME = Matrix.Translation((0, 0, Z_LAME))


def taper(v):
    """L'arête s'abaisse vers la base du fer pour rester dans la douille."""
    return min(1.0, 0.45 + 0.55 * v / 0.11)


HE_FIL, HE_CORPS = 0.0030, 0.0100                     # demi-épaisseurs au bord (m)


def hr_fil(u, v):
    return 0.019 * taper(v)


def hr_corps(u, v):
    return 0.030 * taper(v)


def hr_pan(u, v):
    return hr_corps(u, v) + 0.005


LAME, PANNEAU = mirror(FEUILLE), mirror(PANNEAU_D)
CORPS = offset(LAME, -0.0115)
CORPS_D = CORPS[:len(FEUILLE)]
roof(part("Javelot_Fer_Fil", OR, JAV), LAME, [(0, 0.004), (0, L_LAME - 0.070)], HE_FIL, hr_fil, M_LAME)
roof(part("Javelot_Fer_Corps", ARGENT, JAV), CORPS, [(0, 0.014), (0, L_LAME - 0.085)], HE_CORPS, hr_corps, M_LAME)


def h_corps(u, v):
    hw = half_width(CORPS_D, v)
    return HE_CORPS if hw < 1e-6 else HE_CORPS + (hr_corps(u, v) - HE_CORPS) * max(0.0, 1 - abs(u) / hw)


def h_panneau(u, v):
    hw = half_width(PANNEAU_D, v)
    if hw < 1e-6:
        return hr_pan(u, v)
    he = h_corps(hw, v) + 0.0025
    return he + (hr_pan(u, v) - he) * max(0.0, 1 - abs(u) / hw)


arete_p = [(0, 0.058), (0, 0.345)]
bm = part("Javelot_Fer_Gravures", OR, JAV)
roof(bm, offset(PANNEAU, 0.0045), arete_p, lambda u, v: h_corps(u, v) + 0.0010,
     lambda u, v: hr_pan(u, v) - 0.0020, M_LAME)
roof(part("Javelot_Fer_Panneau", VIOLET, JAV), PANNEAU, arete_p, lambda u, v: h_corps(u, v) + 0.0025, hr_pan,
     M_LAME)
# rune ᛉ, puis plume gravée : nervure centrale et barbes en chevrons
lifted(bm, [[(0, 0.084), (0, 0.160)], [(-0.017, 0.152), (0, 0.128), (0.017, 0.152)], [(0, 0.176), (0, 0.338)]],
       lambda u, v: h_panneau(u, v) + 0.0004, 0.0050, M_LAME)
for v0 in (0.204, 0.236, 0.268, 0.300, 0.328):
    w = 0.66 * half_width(PANNEAU_D, v0 - 0.022)
    lifted(bm, [[(-w, v0 - 0.024), (0, v0), (w, v0 - 0.024)]], lambda u, v: h_panneau(u, v) + 0.0004, 0.0038,
           M_LAME)
# double filet doré sur l'argent, autour du panneau
filet = offset(PANNEAU, 0.0115)
lifted(bm, [filet + filet[:1]], lambda u, v: h_corps(u, v) + 0.0003, 0.0034, M_LAME, ext=0.0, sub=3)
# perles dorées aux deux bouts du panneau
for v in (0.064, 0.350):
    for sgn in (-1, 1):
        diamond(bm, (0, sgn * h_panneau(0, v), Z_LAME + v), 0.0062, 1.5)

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
    arm, feathers, _ = wing((0.072, 0.026), (0.152, 0.112), side, wscale=1.45)
    for k, (pts, quill, tip, barbs) in enumerate(feathers):
        y0 = Y_FACE - 0.0034 + 0.0003 * k
        slab(bm_ai, pts, y0, Y_FACE + 0.001)
        slab(bm_q, stroke(quill, 0.0038), y0 - 0.0022, Y_FACE + 0.001)
        segments(bm_q, barbs[1], 0.0026, y0 - 0.0006, Y_FACE + 0.001)
    slab(bm_ai, arm, Y_FACE - 0.0048, Y_FACE + 0.001)
    outline(bm_q, arm, 0.0035, Y_FACE - 0.0056, Y_FACE + 0.001)

# --- Éclair sous l'umbo, rune ᛉ au-dessus
FOUDRE = [(-0.15, 0.50), (0.26, 0.50), (0.04, 0.12), (0.30, 0.12), (-0.22, -0.50), (-0.04, -0.06),
          (-0.30, -0.06)]
pts = place(FOUDRE, 0.112, 0.0, (0.0, -0.158))
slab(part("Targe_Foudre", VIOLET, TAR), pts, Y_FACE - 0.0018, Y_FACE + 0.001)
bm = part("Targe_Motifs_Or", OR, TAR)
outline(bm, pts, 0.008, Y_FACE - 0.0028, Y_FACE + 0.001)
# volutes en filigrane de part et d'autre de l'éclair
for side in (1, -1):
    for c, r0, a0 in (((0.064, -0.150), 0.019, math.pi),):
        pts = spiral((side * c[0], c[1]), r0, 0.0035, 1.35, a0=a0 if side > 0 else 0.0, sense=-side)
        tail = [(side * (c[0] - r0 - 0.016), c[1] - 0.010), pts[0]]
        segments(bm, tail + pts[1:], 0.0045, Y_FACE - 0.0028, Y_FACE + 0.001)
# cimier : éventail de cinq plumes d'or nervurées de violet qui sortent de derrière l'umbo
CIMIER = (0.0, 0.050)
PLUME_S = [(0.0, -0.30), (0.62, -0.95), (1.0, 0.0), (0.62, 0.95), (0.0, 0.30)]
bm_cv = part("Targe_Ailes_Nervures", VIOLET, TAR)
for k, (deg, L) in enumerate(((141, 0.112), (39, 0.112), (115, 0.138), (65, 0.138), (90, 0.152))):
    ang, w = math.radians(deg), 0.150 * L
    shape = PLUME if deg < 89 else ([(a, -b) for a, b in PLUME] if deg > 91 else PLUME_S)
    y0 = Y_FACE - 0.0030 - 0.0005 * k
    slab(part("Targe_Ailes", OR, TAR), place([(L * a, w * b) for a, b in shape], 1.0, ang, CIMIER),
         y0, Y_FACE + 0.001)
    slab(bm_cv, stroke(place([(0.20 * L, 0.0), (0.84 * L, 0.0)], 1.0, ang, CIMIER), 0.0034, 0.0022),
         y0 - 0.0024, Y_FACE + 0.001)
    for c in (0.48 * L, 0.64 * L):                # barbes en V vers la pointe
        segments(bm_cv, place([(c + 0.10 * L, 0.45 * w), (c, 0.0), (c + 0.10 * L, -0.55 * w)], 1.0, ang, CIMIER),
                 0.0026, y0 - 0.0006, Y_FACE + 0.001)
# filet doré intérieur et perles sur le cercle violet
outline(bm, circle(0.207, 48), 0.0035, Y_FACE - 0.0016, Y_FACE + 0.001)
for k in range(8):
    u, v = polar(0.222, 22.5 + 45 * k)
    diamond(bm, (u, Y_FACE - 0.0022, v), 0.0058, 1.0)

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
