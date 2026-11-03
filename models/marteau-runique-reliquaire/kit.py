"""Kit de style « Roblox low-poly » pour les armes : formes plates, prismes chanfreinés et décalques.

Tout est construit directement en coordonnées monde (objets à l'origine, géométrie appliquée) :
- `prism`, `box`, `hull`, `crystal`, `slab` : volumes à facettes plates ;
- `Painter` : « dessins » plats (traits et aplats) projetés sur les surfaces, comme des décalques ;
- `wrap` : sangle enroulée en hélice sur un manche octogonal.
"""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

from helpers import material

_root = None


# --------------------------------------------------------------------------- matériaux

def hexcol(h):
    """'#RRGGBB' (sRGB) -> couleur linéaire (r, g, b)."""
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def mat(name, hexa, rough=0.55, metal=0.1, emit=None, strength=1.0):
    """Matériau à couleur unie, façon Roblox (aplat), éventuellement émissif."""
    return material(name, hexcol(hexa), rough, metal, hexcol(emit) if emit else None, strength)


# --------------------------------------------------------------------------- objets

def setup(name):
    """Crée l'Empty racine auquel toutes les pièces sont rattachées."""
    global _root
    _root = bpy.data.objects.new(name, None)
    _root.empty_display_type = "PLAIN_AXES"
    _root.empty_display_size = 0.3
    bpy.context.scene.collection.objects.link(_root)
    return _root


def to_object(name, bm, mats):
    """bmesh -> objet (ombrage plat). `mats` : un matériau ou une liste (indices de faces du bmesh)."""
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats if isinstance(mats, (list, tuple)) else [mats]:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if _root is not None:
        ob.parent = _root
    return ob


def _xform(bm, loc=(0, 0, 0), rot=(0, 0, 0), scale=None):
    m = Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4()
    if scale is not None:
        m = m @ Matrix.Diagonal((*scale, 1.0))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts[:])


def _chamfer(bm, edges, width):
    if width > 0 and edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, segments=1, affect="EDGES", profile=0.5,
                        clamp_overlap=True)


def prism(name, m, a0, a1, z0, z1, sides=8, chamfer=0.0, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Prisme (ou tronc) à `sides` pans le long de Z, de z0 à z1. a0/a1 = apothèmes bas/haut
    (demi-largeur entre deux pans opposés). Chanfrein des arêtes des deux bouts."""
    bm = bmesh.new()
    k = 1 / math.cos(math.pi / sides)
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=sides,
                          radius1=a0 * k, radius2=a1 * k, depth=z1 - z0)
    bmesh.ops.rotate(bm, verts=bm.verts[:], matrix=Matrix.Rotation(math.pi / sides, 3, "Z"))
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=(0, 0, (z0 + z1) / 2))
    bm.normal_update()
    caps = {f for f in bm.faces if len(f.verts) == sides}
    _chamfer(bm, [e for e in bm.edges if sum(f in caps for f in e.link_faces) == 1], chamfer)
    _xform(bm, loc, rot)
    return to_object(name, bm, m)


def box(name, m, size, loc=(0, 0, 0), rot=(0, 0, 0), chamfer=0.0, taper=None):
    """Pavé chanfreiné. `taper` = (fx, fy) : réduction de la face du haut (+Z)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    if taper:
        for v in bm.verts:
            if v.co.z > 0:
                v.co.x *= taper[0]
                v.co.y *= taper[1]
    bmesh.ops.scale(bm, vec=size, verts=bm.verts[:])
    _chamfer(bm, bm.edges[:], chamfer)
    _xform(bm, loc, rot)
    return to_object(name, bm, m)


def hull(name, mats, points, dissolve=3.0, shade=None):
    """Bloc taillé : enveloppe convexe des points, facettes coplanaires fusionnées.
    `shade(normal) -> index de matériau` pour peindre les facettes selon leur orientation."""
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p)
    res = bmesh.ops.convex_hull(bm, input=bm.verts[:], use_existing_faces=False)
    junk = list({g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)})
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(dissolve), verts=bm.verts[:], edges=bm.edges[:])
    bm.normal_update()
    if shade:
        for f in bm.faces:
            f.material_index = shade(f.normal)
    return to_object(name, bm, mats)


def chunk_points(rng, center, half, cut=0.06, jitter=0.02, bumps=0, bump_h=0.02):
    """Points d'un pavé aux arêtes abattues, déformé au hasard -> à passer à `hull`.
    `half` = demi-dimensions, `cut` = taille des pans coupés (scalaire ou (x, y, z))."""
    cx, cy, cz = center
    hx, hy, hz = half
    cuts = cut if isinstance(cut, (tuple, list)) else (cut, cut, cut)
    pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                kx, ky, kz = (c * rng.uniform(0.6, 1.4) for c in cuts)
                for p in ((hx, hy - ky, hz - kz), (hx - kx, hy, hz - kz), (hx - kx, hy - ky, hz)):
                    pts.append(Vector((cx + sx * p[0], cy + sy * p[1], cz + sz * p[2])))
    for p in pts:
        p += Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * jitter
    for _ in range(bumps):  # petites bosses : nouvelles facettes sur les grandes faces
        axis = rng.randrange(3)
        s = rng.choice((-1, 1))
        p = [rng.uniform(-0.75, 0.75) * h for h in half]
        p[axis] = s * (half[axis] + rng.uniform(0.3, 1.0) * bump_h)
        pts.append(Vector((cx + p[0], cy + p[1], cz + p[2])))
    return pts


def crystal(name, m, r, up, down, loc=(0, 0, 0), rot=(0, 0, 0), sides=4, mid=0.0, spin=None):
    """Cristal bipyramidal : pointe de longueur `up` vers +Z, `down` vers -Z, section prismatique `mid`."""
    bm = bmesh.new()
    spin = math.pi / sides if spin is None else spin
    ring0 = [bm.verts.new((r * math.cos(spin + i * 2 * math.pi / sides),
                           r * math.sin(spin + i * 2 * math.pi / sides), 0)) for i in range(sides)]
    ring1 = ring0
    if mid > 0:
        ring1 = [bm.verts.new((v.co.x, v.co.y, mid)) for v in ring0]
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((ring0[i], ring0[j], ring1[j], ring1[i]))
    top = bm.verts.new((0, 0, mid + up))
    bot = bm.verts.new((0, 0, -down))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((ring1[i], ring1[j], top))
        bm.faces.new((ring0[j], ring0[i], bot))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _xform(bm, loc, rot)
    return to_object(name, bm, m)


def frame(origin, u, v):
    """Repère plan (origine, axe U, axe V) ; la normale sortante est U x V."""
    o, u, v = Vector(origin), Vector(u).normalized(), Vector(v).normalized()
    return o, u, v, u.cross(v)


def slab(name, m, poly, fr, depth, base=0.0, scale=1.0):
    """Forme 2D (liste de (u, v)) extrudée sur `depth` le long de la normale du repère `fr`,
    à partir d'un décalage `base`. Pour les reliefs plats (étoile, runes, plaques…)."""
    o, u, v, n = fr
    bm = bmesh.new()
    verts = [bm.verts.new(o + u * (a * scale) + v * (b * scale) + n * base) for a, b in poly]
    face = bm.faces.new(verts)
    bm.normal_update()
    if face.normal.dot(n) < 0:
        face.normal_flip()
    ext = bmesh.ops.extrude_face_region(bm, geom=[face])
    top = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=top, vec=n * depth)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return to_object(name, bm, m)


# --------------------------------------------------------------------------- formes 2D

def star(cx, cy, radii, inner, rot=0.0):
    """Étoile : une branche par rayon de `radii`, creux de rayon `inner` (scalaire ou liste)."""
    n = len(radii)
    inner = inner if isinstance(inner, (list, tuple)) else [inner] * n
    pts = []
    for i in range(n):
        a = rot + i * 2 * math.pi / n
        b = a + math.pi / n
        pts.append((cx + radii[i] * math.cos(a), cy + radii[i] * math.sin(a)))
        pts.append((cx + inner[i] * math.cos(b), cy + inner[i] * math.sin(b)))
    return pts


def ngon(cx, cy, r, n, rot=0.0):
    return [(cx + r * math.cos(rot + i * 2 * math.pi / n), cy + r * math.sin(rot + i * 2 * math.pi / n))
            for i in range(n)]


def crack(rng, start, angle, length, seg=0.035, wobble=0.55):
    """Ligne brisée de fissure partant de `start` dans la direction `angle` (radians)."""
    pts = [start]
    x, y = start
    done = 0.0
    while done < length:
        s = min(seg * rng.uniform(0.7, 1.3), length - done)
        a = angle + rng.uniform(-wobble, wobble)
        x, y = x + s * math.cos(a), y + s * math.sin(a)
        pts.append((x, y))
        done += s
    return pts


def resample(pts, step, closed=False):
    pts = [Vector((p[0], p[1])) for p in pts]
    if closed:
        pts = pts + [pts[0]]
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.ceil((b - a).length / step)))
        out += [a.lerp(b, (i + 1) / n) for i in range(n)]
    if closed:
        out.pop()
    return out


# --------------------------------------------------------------------------- décalques projetés

VIEWS = {  # vue -> (origine du plan de projection, axe U, axe V, direction de projection)
    "front": ((0, -5, 0), (1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "back": ((0, 5, 0), (-1, 0, 0), (0, 0, 1), (0, -1, 0)),
    "right": ((5, 0, 0), (0, 1, 0), (0, 0, 1), (-1, 0, 0)),
    "left": ((-5, 0, 0), (0, -1, 0), (0, 0, 1), (1, 0, 0)),
    "top": ((0, 0, 9), (1, 0, 0), (0, 1, 0), (0, 0, -1)),
    "bottom": ((0, 0, -5), (1, 0, 0), (0, -1, 0), (0, 0, 1)),
}


class Painter:
    """Peint des décalques plats sur la surface d'objets, par projection depuis une vue.
    Coordonnées 2D (u, v) : en vue de face, u = X et v = Z (mêmes valeurs que dans la scène)."""

    def __init__(self, objects, offset=0.004):
        verts, polys = [], []
        for ob in objects:
            mw = ob.matrix_world
            base = len(verts)
            verts += [mw @ v.co for v in ob.data.vertices]
            polys += [[base + i for i in p.vertices] for p in ob.data.polygons]
        self.bvh = BVHTree.FromPolygons(verts, polys)
        self.offset = offset

    def cast(self, u, v, view):
        o, du, dv, d = (Vector(x) for x in VIEWS[view])
        loc, nor, _, _ = self.bvh.ray_cast(o + du * u + dv * v, d)
        if loc is None:
            return None
        if nor.dot(d) > 0:
            nor = -nor
        return loc, nor

    def line(self, name, m, pts, view, width, taper=(1.0, 1.0), step=0.008, closed=False):
        """Trait (ruban plat) le long d'une ligne brisée. `taper` = facteurs de largeur début/fin."""
        samples = resample(pts, step, closed)
        if closed:
            samples.append(samples[0])
        hits = [self.cast(p.x, p.y, view) for p in samples]
        bm = bmesh.new()
        n = len(samples)
        run = []

        def flush(run):
            if len(run) < 2:
                return
            rows = []
            for k, (i, (loc, nor)) in enumerate(run):
                a = run[max(k - 1, 0)][1][0]
                b = run[min(k + 1, len(run) - 1)][1][0]
                t = (b - a).normalized()
                side = nor.cross(t).normalized()
                f = i / max(n - 1, 1)
                w = width * (taper[0] + (taper[1] - taper[0]) * f) / 2
                c = loc + nor * self.offset
                rows.append((bm.verts.new(c + side * w), bm.verts.new(c - side * w), nor))
            for (l0, r0, nor), (l1, r1, _) in zip(rows, rows[1:]):
                face = bm.faces.new((l0, r0, r1, l1))
                face.normal_update()
                if face.normal.dot(nor) < 0:
                    face.normal_flip()

        for i, h in enumerate(hits):
            if h is None:
                flush(run)
                run = []
            else:
                run.append((i, h))
        flush(run)
        return to_object(name, bm, m) if bm.faces else (bm.free() or None)

    def fill(self, name, m, poly, view, cuts=2, step=0.03):
        """Aplat : polygone 2D rempli, plaqué sur la surface."""
        bm = bmesh.new()
        verts = [bm.verts.new((p.x, p.y, 0)) for p in resample(poly, step, closed=True)]
        face = bm.faces.new(verts)
        bmesh.ops.triangulate(bm, faces=[face])
        if cuts:
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
        d = Vector(VIEWS[view][3])
        dead = []
        for vert in bm.verts:
            h = self.cast(vert.co.x, vert.co.y, view)
            if h is None:
                dead.append(vert)
            else:
                vert.co = h[0] + h[1] * self.offset
        if dead:
            bmesh.ops.delete(bm, geom=dead, context="VERTS")
        bm.normal_update()
        for f in bm.faces:
            if f.normal.dot(d) > 0:
                f.normal_flip()
        return to_object(name, bm, m)


# --------------------------------------------------------------------------- sangles

def wrap(name, m, apothem, z0, z1, turns, width, thick=0.004, sides=8, phase=0.0, direction=1,
         steps_per_side=3):
    """Sangle plate enroulée en hélice sur un prisme `sides` pans (apothème donné) de z0 à z1."""
    bm = bmesh.new()
    seg = 2 * math.pi / sides
    total = turns * 2 * math.pi
    # angles d'échantillonnage : réguliers + coins exacts du prisme
    angles = {i * total / (turns * sides * steps_per_side) for i in range(int(turns * sides * steps_per_side) + 1)}
    k = 0
    while k * seg - seg / 2 <= total + seg:
        c = k * seg + seg / 2 - phase * direction
        if 0 < c < total:
            angles.add(c)
        k += 1
    rows = []
    for t in sorted(angles):
        th = phase + direction * t
        delta = (th + seg / 2) % seg - seg / 2
        r_in = (apothem - 0.001) / math.cos(delta)
        r_out = (apothem + thick) / math.cos(delta)
        z = z0 + (z1 - z0) * t / total
        cs, sn = math.cos(th), math.sin(th)
        rows.append([bm.verts.new((r * cs, r * sn, z + dz)) for r, dz in
                     ((r_in, -width / 2), (r_out, -width / 2), (r_out, width / 2), (r_in, width / 2))])
    for a, b in zip(rows, rows[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(rows[0][::-1])
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return to_object(name, bm, m)


def seeded(seed):
    return random.Random(seed)


def shade_faces(ob, mats, fn):
    """Peint les faces d'un objet selon leur normale : `fn(normal) -> index` dans `mats`."""
    me = ob.data
    me.materials.clear()
    for m in mats:
        me.materials.append(m)
    for p in me.polygons:
        p.material_index = fn(p.normal)
    return ob


def glyph(painter, name, m, strokes, center, size, view, width, rot=0.0):
    """Dessine un symbole (liste de traits, coordonnées dans [-0.5, 0.5]) projeté depuis `view`."""
    cx, cy = center
    c, s = math.cos(rot), math.sin(rot)
    obs = []
    for k, stroke in enumerate(strokes):
        pts = [(cx + size * (x * c - y * s), cy + size * (x * s + y * c)) for x, y in stroke]
        ob = painter.line(f"{name} {k}", m, pts, view, width, step=0.006)
        if ob is not None:
            obs.append(ob)
    return join(obs, name)


def join(obs, name):
    """Fusionne plusieurs objets maillage en un seul (moins de pièces à importer)."""
    obs = [o for o in obs if o is not None]
    if not obs:
        return None
    if len(obs) == 1:
        obs[0].name = name
        return obs[0]
    with bpy.context.temp_override(active_object=obs[0], selected_editable_objects=obs, object=obs[0]):
        bpy.ops.object.join()
    obs[0].name = name
    return obs[0]


def aim(direction):
    """Rotation (Euler) qui oriente l'axe +Z d'une pièce vers `direction`."""
    return Vector(direction).to_track_quat("Z", "Y").to_euler()


def ring_slab(name, m, fr, r_out, r_in, depth, base=0.0, n=8, rot=None):
    """Anneau plat à n pans (apothèmes r_out / r_in) dans le repère `fr`, extrudé sur `depth`."""
    o, u, v, nrm = fr
    rot = math.pi / n if rot is None else rot
    k = 1 / math.cos(math.pi / n)
    bm = bmesh.new()

    def ring(r, z):
        return [bm.verts.new(o + u * (r * k * math.cos(rot + i * 2 * math.pi / n))
                             + v * (r * k * math.sin(rot + i * 2 * math.pi / n)) + nrm * z) for i in range(n)]

    ob, ib, ot, it = ring(r_out, base), ring(r_in, base), ring(r_out, base + depth), ring(r_in, base + depth)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ib[i], ib[j], ob[j], ob[i]))
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((it[i], it[j], ib[j], ib[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return to_object(name, bm, m)


def loft(name, m, spine, radii, sides=4, spin=0.0, tip=None, up=(0, 0, 1)):
    """Tube à `sides` pans le long d'une ligne `spine` (points 3D), rayon (circonscrit) par section.
    `tip` : point final pour fermer en pointe ; sinon le bout est bouché."""
    spine = [Vector(p) for p in spine]
    up = Vector(up)
    bm = bmesh.new()
    rings = []
    for i, (c, r) in enumerate(zip(spine, radii)):
        a = spine[max(i - 1, 0)]
        b = spine[min(i + 1, len(spine) - 1)]
        t = (b - a).normalized()
        x = up.cross(t)
        if x.length < 1e-6:
            x = Vector((1, 0, 0)).cross(t)
        x.normalize()
        y = t.cross(x)
        rings.append([bm.verts.new(c + (x * math.cos(spin + k * 2 * math.pi / sides)
                                        + y * math.sin(spin + k * 2 * math.pi / sides)) * r)
                      for k in range(sides)])
    for ra, rb in zip(rings, rings[1:]):
        for k in range(sides):
            j = (k + 1) % sides
            bm.faces.new((ra[k], ra[j], rb[j], rb[k]))
    bm.faces.new(rings[0][::-1])
    if tip is not None:
        tv = bm.verts.new(Vector(tip))
        for k in range(sides):
            bm.faces.new((rings[-1][k], rings[-1][(k + 1) % sides], tv))
    else:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return to_object(name, bm, m)


def curl(cx, cy, r, turns=1.25, a0=0.0, direction=1, n=28, shrink=0.75):
    """Volute (spirale qui se resserre) : départ à l'angle a0, rayon r."""
    pts = []
    for i in range(n + 1):
        t = i / n
        a = a0 + direction * t * turns * 2 * math.pi
        rr = r * (1 - shrink * t)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts
