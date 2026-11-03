"""Maillages de base, construits directement en coordonnées monde (objets à transformation identité)."""
import math

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

TAU = math.tau
COLLECTION = None  # collection où sont créés les objets (définie par enemy.build_enemy)


def _link(ob):
    coll = COLLECTION or bpy.context.scene.collection
    coll.objects.link(ob)
    return ob


def mesh_obj(name, verts, faces, material=None, smooth=True, recalc=True):
    """Objet maillage à partir de sommets/faces. `material` : un matériau ou une liste (index par face)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(clean_customdata=False)
    if recalc:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
    if material is not None:
        for m in (material if isinstance(material, (list, tuple)) else [material]):
            me.materials.append(m)
    if smooth:
        me.shade_smooth()
    else:
        me.shade_flat()
    me.update()
    return _link(bpy.data.objects.new(name, me))


def set_face_materials(ob, fn):
    """fn(centre_de_face) -> index de matériau."""
    me = ob.data
    for p in me.polygons:
        p.material_index = fn(p.center)


def transform(ob, M):
    ob.data.transform(M)
    ob.data.update()
    return ob


def basis(origin, ydir, zhint=(0, 0, 1)):
    """Matrice qui envoie l'axe local +Y sur `ydir` et +Z au plus près de `zhint`."""
    y = Vector(ydir).normalized()
    x = y.cross(Vector(zhint))
    if x.length < 1e-6:
        x = y.orthogonal()
    x.normalize()
    z = x.cross(y)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = Vector(origin)
    return M


def basis_z(origin, zdir, yhint=(0, 1, 0)):
    """Matrice qui envoie l'axe local +Z sur `zdir` et +Y au plus près de `yhint`."""
    z = Vector(zdir).normalized()
    x = Vector(yhint).cross(z)
    if x.length < 1e-6:
        x = z.orthogonal()
    x.normalize()
    y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = Vector(origin)
    return M


def rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, Vector(axis))


def join(objs, name):
    """Fusionne des objets (matériaux et groupes de sommets fusionnés par nom)."""
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    if len(objs) > 1:
        with bpy.context.temp_override(active_object=objs[0], object=objs[0],
                                       selected_objects=objs, selected_editable_objects=objs):
            bpy.ops.object.join()
    ob = objs[0]
    ob.name = name
    ob.data.name = name
    return ob


def apply_modifiers(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    me.name = old.name
    bpy.data.meshes.remove(old)
    return ob


def bevel_apply(ob, width, segments=2, angle=35):
    mod = ob.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angle)
    apply_modifiers(ob)
    ob.data.set_sharp_from_angle(angle=math.radians(40))
    return ob


def subsurf_apply(ob, levels=1):
    mod = ob.modifiers.new("Subsurf", "SUBSURF")
    mod.levels = levels
    mod.render_levels = levels
    apply_modifiers(ob)
    ob.data.shade_smooth()
    return ob


# --------------------------------------------------------------------------------------------- courbes

def catmull(points, per_seg=6, closed=False):
    """Lisse une polyligne (Catmull-Rom)."""
    P = [Vector(p) for p in points]
    n = len(P)
    out = []
    segs = n if closed else n - 1
    for i in range(segs):
        p0 = P[(i - 1) % n] if closed or i > 0 else P[0] * 2 - P[1]
        p1 = P[i]
        p2 = P[(i + 1) % n]
        p3 = P[(i + 2) % n] if closed or i + 2 < n else P[-1] * 2 - P[-2]
        for k in range(per_seg):
            t = k / per_seg
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(P[-1].copy())
    return out


def resample(points, n, closed=False):
    """Ré-échantillonne une polyligne en n points régulièrement espacés."""
    P = [Vector(p) for p in points]
    if closed:
        P = P + [P[0]]
    L = [0.0]
    for a, b in zip(P, P[1:]):
        L.append(L[-1] + (b - a).length)
    total = L[-1]
    out = []
    count = n if closed else n - 1
    j = 0
    for i in range(n):
        d = total * i / count
        while j < len(L) - 2 and L[j + 1] < d:
            j += 1
        seg = max(L[j + 1] - L[j], 1e-9)
        out.append(P[j].lerp(P[j + 1], min(max((d - L[j]) / seg, 0), 1)))
    return out


# --------------------------------------------------------------------------------------------- primitives

def lathe(name, profile, seg=24, axis="Z", material=None, center=(0, 0, 0), smooth=True, angle0=0.0, caps=True):
    """Révolution d'un profil [(rayon, hauteur)] du bas vers le haut. Rayon 0 = pôle."""
    c = Vector(center)
    verts, faces, rings = [], [], []

    def P(x, y, h):
        if axis == "Z":
            return c + Vector((x, y, h))
        if axis == "Y":  # hauteur le long de +Y, cercle dans XZ
            return c + Vector((x, h, y))
        return c + Vector((h, x, y))

    for r, h in profile:
        if r < 1e-7:
            rings.append([len(verts)])
            verts.append(P(0, 0, h))
        else:
            idx = []
            for i in range(seg):
                a = angle0 + TAU * i / seg
                idx.append(len(verts))
                verts.append(P(r * math.cos(a), r * math.sin(a), h))
            rings.append(idx)
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1:
            continue
        if len(A) == 1:
            faces += [(A[0], B[i], B[(i + 1) % seg]) for i in range(seg)]
        elif len(B) == 1:
            faces += [(A[i], A[(i + 1) % seg], B[0]) for i in range(seg)]
        else:
            faces += [(A[i], A[(i + 1) % seg], B[(i + 1) % seg], B[i]) for i in range(seg)]
    if caps:
        if len(rings[0]) > 1:
            faces.append(tuple(reversed(rings[0])))
        if len(rings[-1]) > 1:
            faces.append(tuple(rings[-1]))
    return mesh_obj(name, verts, faces, material, smooth)


def sphere(name, center, radius, seg=20, rings=10, scale=(1, 1, 1), material=None, smooth=True):
    prof = [(radius * math.sin(math.pi * i / rings), -radius * math.cos(math.pi * i / rings)) for i in range(rings + 1)]
    ob = lathe(name, prof, seg, "Z", material, (0, 0, 0), smooth)
    M = Matrix.Translation(Vector(center)) @ Matrix.Diagonal((*scale, 1))
    return transform(ob, M)


def cylinder(name, p0, p1, radius, seg=12, material=None, smooth=True, r1=None):
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    ob = lathe(name, [(radius, 0), (radius if r1 is None else r1, L)], seg, "Z", material, (0, 0, 0), smooth)
    if smooth:
        ob.data.set_sharp_from_angle(angle=math.radians(40))
    return transform(ob, basis_z(p0, p1 - p0))


def torus(name, R, r, seg=32, seg2=8, material=None, M=None, smooth=True):
    verts, faces = [], []
    for i in range(seg):
        a = TAU * i / seg
        ca, sa = math.cos(a), math.sin(a)
        for j in range(seg2):
            b = TAU * j / seg2
            rr = R + r * math.cos(b)
            verts.append((rr * ca, rr * sa, r * math.sin(b)))
    for i in range(seg):
        for j in range(seg2):
            a, b = i * seg2 + j, i * seg2 + (j + 1) % seg2
            c, d = ((i + 1) % seg) * seg2 + (j + 1) % seg2, ((i + 1) % seg) * seg2 + j
            faces.append((a, b, c, d))
    ob = mesh_obj(name, verts, faces, material, smooth)
    return transform(ob, M) if M is not None else ob


def box(name, center, size, material=None, bevel=0.0):
    sx, sy, sz = (s / 2 for s in size)
    verts = [(x * sx, y * sy, z * sz) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    ob = mesh_obj(name, verts, faces, material, smooth=False)
    transform(ob, Matrix.Translation(Vector(center)))
    if bevel > 0:
        bevel_apply(ob, bevel, segments=2)
    return ob


def tube(name, pts, radius, seg=8, material=None, caps=True, radii=None, smooth=True):
    """Tube le long d'une polyligne (repères à transport parallèle). `radii` : rayon par point."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    T = []
    for i in range(n):
        a = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        T.append(a.normalized() if a.length > 1e-9 else Vector((0, 0, 1)))
    up = Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0))
    N = T[0].cross(up).normalized()
    verts, faces = [], []
    for i in range(n):
        if i > 0:
            N = T[i - 1].rotation_difference(T[i]) @ N
            N = (N - T[i] * N.dot(T[i])).normalized()
        B = T[i].cross(N)
        rr = radii[i] if radii is not None else radius
        rr = max(rr, 1e-4)
        for j in range(seg):
            a = TAU * j / seg
            verts.append(pts[i] + (N * math.cos(a) + B * math.sin(a)) * rr)
    for i in range(n - 1):
        for j in range(seg):
            faces.append((i * seg + j, i * seg + (j + 1) % seg, (i + 1) * seg + (j + 1) % seg, (i + 1) * seg + j))
    if caps:
        faces.append(tuple(range(seg))[::-1])
        faces.append(tuple(range((n - 1) * seg, n * seg)))
    return mesh_obj(name, verts, faces, material, smooth)


def tapered_tube(name, pts, r0, r1, seg=8, material=None, power=1.0):
    n = len(pts)
    radii = [r0 + (r1 - r0) * (i / (n - 1)) ** power for i in range(n)]
    return tube(name, pts, r0, seg, material, True, radii)


# --------------------------------------------------------------------------------------------- formes gonflables

def pillow(name, outline, thickness, rings=8, edge=None, material=None, center=None, power=0.5):
    """Coussin gonflé à partir d'un contour 2D fermé (étoilé par rapport à `center`).

    Le contour est dans le plan local XZ ; l'épaisseur est le long de Y (+Y = face avant).
    La hauteur de chaque point dépend de sa distance au bord : les pointes fines sont plus minces.
    """
    O = [Vector((p[0], p[1])) for p in outline]
    n = len(O)
    c = Vector(center) if center is not None else sum(O, Vector((0, 0))) / n
    edge = edge or thickness * 2.2

    def dist_edge(p):
        best = 1e9
        for i in range(n):
            a, b = O[i], O[(i + 1) % n]
            ab = b - a
            t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.dot(ab), 1e-12)))
            best = min(best, (p - (a + ab * t)).length)
        return best

    def height(p):
        u = min(dist_edge(p) / edge, 1.0)
        return thickness * (1 - (1 - u) ** 2) ** power

    verts, faces = [], []
    grid_f, grid_b = [], []
    for k in range(1, rings + 1):
        s = (k / rings) ** 0.85
        rowf, rowb = [], []
        for i in range(n):
            p = c + (O[i] - c) * s
            h = height(p) if k < rings else 0.0
            if k < rings:
                rowf.append(len(verts))
                verts.append((p.x, h, p.y))
                rowb.append(len(verts))
                verts.append((p.x, -h, p.y))
            else:
                rowf.append(len(verts))
                verts.append((p.x, 0.0, p.y))
                rowb.append(rowf[-1])
        grid_f.append(rowf)
        grid_b.append(rowb)
    hc = height(c)
    cf = len(verts)
    verts.append((c.x, hc, c.y))
    cb = len(verts)
    verts.append((c.x, -hc, c.y))
    for grid, cen in ((grid_f, cf), (grid_b, cb)):
        faces += [(cen, grid[0][i], grid[0][(i + 1) % n]) for i in range(n)]
        for A, B in zip(grid, grid[1:]):
            faces += [(A[i], B[i], B[(i + 1) % n], A[(i + 1) % n]) for i in range(n)]
    return mesh_obj(name, verts, faces, material, True)


def star_outline(ro, ri, n=5, samples=120, sharp=1.6, rot0=0.0):
    """Contour d'étoile à pointes arrondies (plan XZ, pointe vers +Z)."""
    pts = []
    for i in range(samples):
        a = TAU * i / samples
        g = ((1 + math.cos(n * a)) / 2) ** sharp
        r = ri + (ro - ri) * g
        pts.append((r * math.sin(a + rot0), r * math.cos(a + rot0)))
    return pts


def leaf(name, length, width, material, fold=0.25, bend=0.25, nu=8, nv=3, thick=0.004, tip=1.0):
    """Feuille double face. Locale : base à l'origine, pointe vers +Y, face vers +Z."""
    verts, faces = [], []
    cols = 2 * nv + 1
    for side, off in ((0, thick / 2), (1, -thick / 2)):
        for i in range(nu + 1):
            u = i / nu
            w = width * 0.5 * math.sin(math.pi * u) ** 0.8 * (1 + 0.35 * (1 - u)) ** tip / 1.2
            for j in range(-nv, nv + 1):
                v = j / nv
                x = v * w
                z = bend * length * u * u + fold * abs(v) * w + off
                verts.append((x, u * length, z))
    base = (nu + 1) * cols
    for i in range(nu):
        for j in range(cols - 1):
            a, b, c, d = i * cols + j, i * cols + j + 1, (i + 1) * cols + j + 1, (i + 1) * cols + j
            faces.append((a, b, c, d))
            faces.append((base + d, base + c, base + b, base + a))
    return mesh_obj(name, verts, faces, material, True, recalc=False)


def star3d(name, ro, ri, depth, material, n=5, smooth=True):
    """Étoile pleine bombée. Locale : plan XY, pointe vers +Y, épaisseur selon Z."""
    verts = [(0, 0, depth), (0, 0, -depth)]
    for k in range(2 * n):
        r = ro if k % 2 == 0 else ri
        a = math.pi / 2 + k * math.pi / n
        verts.append((r * math.cos(a), r * math.sin(a), 0))
    m = 2 * n
    faces = []
    for k in range(m):
        faces.append((0, 2 + k, 2 + (k + 1) % m))
        faces.append((1, 2 + (k + 1) % m, 2 + k))
    ob = mesh_obj(name, verts, faces, material, smooth)
    if smooth:
        ob.data.set_sharp_from_angle(angle=math.radians(50))
    return ob


def flame(name, h, r, material, seg=10, bend=0.25, rings=10):
    """Flamme stylisée (goutte effilée et courbée). Locale : base à l'origine, pointe vers +Z."""
    prof = []
    for i in range(rings + 1):
        t = i / rings
        rr = r * math.sqrt(t) * (1 - t) ** 1.15 / 0.36 if 0 < t < 1 else 0.0
        prof.append((rr, t * h - 0.1 * r))
    ob = lathe(name, prof, seg, "Z", material)
    for v in ob.data.vertices:
        t = max(v.co.z / h, 0)
        v.co.x += bend * h * t * t
    ob.data.update()
    return ob


def teardrop(name, R, material, seg=14, rings=10, m=1.3, stretch=1.6):
    """Goutte d'eau, pointe vers +Z, centre de la partie ronde à l'origine."""
    prof = []
    for i in range(rings + 1):
        th = math.pi * (1 - i / rings)  # pi (bas) -> 0 (pointe)
        x = R * math.sin(th) * math.sin(th / 2) ** m
        z = R * math.cos(th)
        if z > 0:
            z *= stretch
        prof.append((abs(x), z))
    return lathe(name, prof, seg, "Z", material)


def crystal(name, h, r, material, sides=6):
    """Cristal hexagonal à pointe. Locale : base à l'origine, pointe vers +Z."""
    prof = [(0.0, -0.05 * h), (r * 0.85, 0.0), (r, 0.12 * h), (r, 0.68 * h), (0.0, h)]
    ob = lathe(name, prof, sides, "Z", material, smooth=False)
    return ob


def bolt(name, height, thick, material, width=None):
    """Éclair en zigzag extrudé. Locale : plan XZ, pointe vers -Z, épaisseur selon Y."""
    P = [(0.10, 1.00), (0.62, 1.00), (0.24, 0.22), (0.58, 0.22), (-0.30, -1.00), (0.02, -0.06), (-0.34, -0.06)]
    w = (width or height) / 2
    hh = height / 2
    pts = [(x * w, z * hh) for x, z in P]
    n = len(pts)
    verts = [(x, -thick / 2, z) for x, z in pts] + [(x, thick / 2, z) for x, z in pts]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    ob = mesh_obj(name, verts, faces, material, smooth=False)
    return bevel_apply(ob, thick * 0.35, segments=2, angle=30)


def puff_cluster(name, center, size, material, count=4, seed=0, flatten=0.8):
    """Petit nuage de fumée (boules qui se chevauchent)."""
    import random
    rnd = random.Random(seed)
    parts = []
    for k in range(count):
        a = TAU * k / count + rnd.uniform(-0.4, 0.4)
        off = Vector((math.cos(a), math.sin(a), rnd.uniform(-0.3, 0.4))) * size * 0.55
        rr = size * rnd.uniform(0.45, 0.7)
        parts.append(sphere(f"{name}_{k}", Vector(center) + off, rr, 8, 5, (1, 1, flatten), material))
    parts.append(sphere(f"{name}_c", center, size * 0.7, 9, 5, (1, 1, flatten), material))
    return join(parts, name)


def flower(name, radius, petal_mat, center_mat, n=5, cup=22):
    """Fleur. Locale : face vers +Z, centre à l'origine."""
    parts = []
    for k in range(n):
        p = leaf(f"{name}_p{k}", radius, radius * 0.75, petal_mat, fold=0.08, bend=-0.1, nu=3, nv=1,
                 thick=radius * 0.04)
        transform(p, rot((0, 0, 1), 360 * k / n) @ rot((1, 0, 0), cup))
        parts.append(p)
    parts.append(sphere(f"{name}_coeur", (0, 0, radius * 0.12), radius * 0.32, 8, 4, (1, 1, 0.6), center_mat))
    return join(parts, name)


def quat_from_to(a, b):
    return Vector(a).rotation_difference(Vector(b))


__all__ = [n for n in dir() if not n.startswith("_")] + ["Quaternion"]
