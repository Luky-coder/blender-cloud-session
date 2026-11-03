"""Noyau commun : couleurs, matériaux, géométrie gonflable paramétrique, visage, rig, animations, export.

Conventions (spécifiques à cette mission, demandées par l'utilisateur) :
- mètres, Z vers le haut, AVANT DES ENNEMIS VERS +Y, pivot (os Root) au sol en (0, 0, 0) ;
- chaque ennemi = 1 armature + 1 maillage skinné (multi-matériaux) + shape keys « Degonfle » et « Gonfle » ;
- les shape keys sont pilotées par des drivers lisant la position X des os de contrôle CTRL_Degonfle /
  CTRL_Gonfle (non déformants) : chaque action ne contient donc que des courbes d'armature, et l'export
  FBX « toutes les actions » cuit correctement les blendshapes de chaque prise ;
- tous les os ont une orientation de repos identique aux axes du monde (os pointant vers +Y, roll 0) :
  loc/rot/scale de pose s'expriment donc directement en axes X/Y/Z (rotation X = tangage, Z = lacet).
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

FPS = 30
TAU = 2 * math.pi


# ---------------------------------------------------------------------------------------------
# Couleurs et matériaux
# ---------------------------------------------------------------------------------------------
def lin(hexcode):
    """'#RRGGBB' (sRGB) -> couleur linéaire (r, g, b)."""
    h = hexcode.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def set_material(mat, color, rough=0.3, metal=0.0, coat=0.6, emit=None, emit_s=0.0, transm=0.0):
    """Principled BSDF « plastique gonflable » : brillant, vernis (coat) léger."""
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    c = lin(color)
    bsdf.inputs["Base Color"].default_value = (*c, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Coat Roughness"].default_value = 0.08
    bsdf.inputs["Transmission Weight"].default_value = transm
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*lin(emit), 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_s
    else:
        bsdf.inputs["Emission Strength"].default_value = 0.0
    mat.diffuse_color = (*c, 1.0)
    mat.roughness = rough
    mat.metallic = metal
    return mat


# Rôles de matériaux. Les rôles « désert » sont communs à tout le monde 2 (identité du monde),
# les rôles élémentaires sont fournis par la palette de chaque type (elements.py).
DESERT_ROLES = {
    "or": dict(color="#E8B53A", rough=0.22, metal=0.85, coat=0.3),
    "sable": dict(color="#E9CB92", rough=0.4, coat=0.5),
    "ocre": dict(color="#CC7A2E", rough=0.35, coat=0.6),
    "cuir": dict(color="#6E4526", rough=0.5, coat=0.3),
    "turquoise": dict(color="#1FB5A5", rough=0.2, coat=0.8),
    "terre": dict(color="#B95A33", rough=0.4, coat=0.5),
    "oeil": dict(color="#FFFFFF", rough=0.15, coat=1.0),
    "reflet": dict(color="#FFFFFF", rough=0.1, coat=1.0, emit="#FFFFFF", emit_s=1.5),
    "bouche": dict(color="#4A1420", rough=0.45, coat=0.3),
    "langue": dict(color="#E8697A", rough=0.3, coat=0.6),
    "dent": dict(color="#FFF7E8", rough=0.2, coat=0.8),
}
ELEMENT_ROLES = ("corps", "corps2", "couture", "glyphe", "epine", "fx", "fx2", "pupille", "joue")
ALL_ROLES = ELEMENT_ROLES + tuple(DESERT_ROLES)

# Palette neutre « sable » des géométries de référence (avant application d'un type élémentaire).
NEUTRAL_PALETTE = {
    "corps": dict(color="#D9B377"), "corps2": dict(color="#F1DDB1"), "couture": dict(color="#9C7444"),
    "glyphe": dict(color="#8A5A2B"), "epine": dict(color="#FFF4DA"), "fx": dict(color="#F2E2BF"),
    "fx2": dict(color="#C99C5C"), "pupille": dict(color="#20140E"), "joue": dict(color="#F09A7A"),
}


def make_materials(prefix, palette):
    """Crée tous les rôles de matériaux : {rôle: Material} nommés '<prefix>_<rôle>'."""
    mats = {}
    for role in ALL_ROLES:
        spec = palette.get(role) if role in ELEMENT_ROLES else DESERT_ROLES[role]
        mat = bpy.data.materials.new(f"{prefix}_{role}")
        set_material(mat, **spec)
        mats[role] = mat
    return mats


def recolor_materials(mats, prefix, palette):
    """Applique une palette élémentaire à des matériaux de rôle existants (et les renomme)."""
    for role, mat in mats.items():
        spec = palette.get(role) if role in ELEMENT_ROLES else DESERT_ROLES[role]
        set_material(mat, **spec)
        mat.name = f"{prefix}_{role}"


def role_of(mat):
    return mat.name.rsplit("_", 1)[-1]


# ---------------------------------------------------------------------------------------------
# Géométrie
# ---------------------------------------------------------------------------------------------
def collection(name):
    coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    return coll


class Builder:
    """Crée les pièces dans une collection, avec les matériaux de rôle."""

    def __init__(self, coll, mats):
        self.coll = coll
        self.mats = mats
        self.parts = []

    def obj(self, name, verts, faces, roles, face_roles=None, smooth=True, recalc=True):
        """roles : liste des rôles des slots ; face_roles : index de slot par face (ou None)."""
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in verts], [], faces)
        me.validate()
        if face_roles is not None:
            me.polygons.foreach_set("material_index", face_roles)
        ob = bpy.data.objects.new(name, me)
        self.coll.objects.link(ob)
        for r in roles:
            me.materials.append(self.mats[r])
        if recalc:
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me)
            bm.free()
        if smooth:
            me.shade_smooth()
        self.parts.append(ob)
        return ob

    def from_bmesh(self, name, bm, role, smooth=True):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        self.coll.objects.link(ob)
        me.materials.append(self.mats[role])
        if smooth:
            me.shade_smooth()
        else:
            me.shade_flat()
        self.parts.append(ob)
        return ob

    # -- primitives ----------------------------------------------------------------------------
    def sweep(self, name, path, radii, roles, nseg=16, section=None, up=None, closed=False,
              mat_fn=None, twist=0.0, smooth=True):
        """Tube balayé le long d'un chemin (parallel transport). Extrémités fermées par des pôles :
        donner des rayons ~0 aux extrémités pour des bouts arrondis.
        section(theta, t) -> multiplicateur du rayon (côtes, ellipses, superellipses).
        theta = 0 : direction « up » (normale initiale) ; theta = 90° : T x N.
        mat_fn(i, j, theta, t) -> index de slot pour la face entre l'anneau i et i+1."""
        P = [Vector(p) for p in path]
        n = len(P)
        T = []
        for i in range(n):
            if closed:
                a, b = P[i - 1], P[(i + 1) % n]
            else:
                a, b = P[max(i - 1, 0)], P[min(i + 1, n - 1)]
            T.append((b - a).normalized())
        u = Vector(up) if up is not None else (Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((0, 1, 0)))
        N = u - T[0] * u.dot(T[0])
        if N.length < 1e-6:
            N = T[0].orthogonal()
        N.normalize()
        frames = []
        for i in range(n):
            if i:
                N = T[i - 1].rotation_difference(T[i]) @ N
                N = (N - T[i] * N.dot(T[i])).normalized()
            frames.append((N.copy(), T[i].cross(N)))
        verts, rings = [], []
        for i in range(n):
            t = i / (n - 1) if n > 1 else 0
            if not closed and i in (0, n - 1):
                rings.append([len(verts)])
                verts.append(P[i])
                continue
            Ni, Bi = frames[i]
            ids = []
            for j in range(nseg):
                th = TAU * j / nseg + twist * t
                m = section(th, t) if section else 1.0
                ids.append(len(verts))
                verts.append(P[i] + (Ni * math.cos(th) + Bi * math.sin(th)) * radii[i] * m)
            rings.append(ids)
        faces, fmat = [], []
        pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if closed else [])
        for i, k in pairs:
            a, b = rings[i], rings[k]
            t = (i + 0.5) / (n - 1)
            for j in range(nseg):
                j2 = (j + 1) % nseg
                th = TAU * (j + 0.5) / nseg
                if len(a) == 1:
                    faces.append((a[0], b[j], b[j2]))
                elif len(b) == 1:
                    faces.append((a[j], b[0], a[j2]))
                else:
                    faces.append((a[j], b[j], b[j2], a[j2]))
                fmat.append(mat_fn(i, j, th, t) if mat_fn else 0)
        return self.obj(name, verts, faces, roles, fmat if mat_fn else None, smooth=smooth)

    def sphere(self, name, center, radii, role, seg=16, rings=10, M=None):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
        S = Matrix.Diagonal((*radii, 1.0))
        X = (M if M is not None else Matrix.Translation(center)) @ S
        bmesh.ops.transform(bm, matrix=X, verts=bm.verts)
        return self.from_bmesh(name, bm, role)

    def cone(self, name, M, r1, r2, depth, role, seg=12, smooth=True):
        """Cône/cylindre dont la base est à z=0 local et le sommet à z=depth, puis transformé par M."""
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=depth)
        bmesh.ops.translate(bm, vec=(0, 0, depth / 2), verts=bm.verts)
        bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
        return self.from_bmesh(name, bm, role, smooth=smooth)

    def prism(self, name, pts2d, depth, role, M=None, smooth=False):
        """Polygone 2D (plan XY local) extrudé de `depth` vers +Z local. Sert aux glyphes et décors."""
        bm = bmesh.new()
        vs = [bm.verts.new((x, y, 0.0)) for x, y in pts2d]
        f = bm.faces.new(vs)
        res = bmesh.ops.extrude_face_region(bm, geom=[f])
        top = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0, 0, depth), verts=top)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
        if M is not None:
            bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
        return self.from_bmesh(name, bm, role, smooth=smooth)

    def tube(self, name, ctrl, r, role, n=12, nseg=8, cap=True, rfn=None, section=None, up=None,
             roles=None, mat_fn=None, ncap=4):
        path, radii = capsule_path(ctrl, r, n=n, cap0=cap, cap1=cap, rfn=rfn, ncap=ncap)
        return self.sweep(name, path, radii, roles or [role], nseg=nseg, section=section, up=up,
                          mat_fn=mat_fn)

    def ring(self, name, center, radius, minor, role, axis=(0, 0, 1), nseg=8, n=32, section=None,
             roles=None, mat_fn=None, rfn=None):
        """Anneau (tore) fermé autour de `axis`. rfn(phi) -> multiplicateur du grand rayon."""
        ax = Vector(axis).normalized()
        a = ax.orthogonal().normalized()
        b = ax.cross(a)
        c = Vector(center)
        path = []
        for k in range(n):
            ph = TAU * k / n
            R = radius * (rfn(ph) if rfn else 1.0)
            path.append(c + (a * math.cos(ph) + b * math.sin(ph)) * R)
        return self.sweep(name, path, [minor] * n, roles or [role], nseg=nseg, section=section, up=ax,
                          closed=True, mat_fn=mat_fn)


def spline(ctrl, n):
    """Catmull-Rom passant par les points de contrôle, rééchantillonnée en n points équidistants."""
    C = [Vector(c) for c in ctrl]
    if len(C) == 2:
        return [C[0].lerp(C[1], i / (n - 1)) for i in range(n)]
    pts = [C[0]] + C + [C[-1]]
    dense = []
    for s in range(len(C) - 1):
        p0, p1, p2, p3 = pts[s:s + 4]
        for k in range(16):
            t = k / 16
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(C[-1])
    L = [0.0]
    for a, b in zip(dense, dense[1:]):
        L.append(L[-1] + (b - a).length)
    out, k = [], 0
    for i in range(n):
        d = L[-1] * i / (n - 1)
        while k < len(L) - 2 and L[k + 1] < d:
            k += 1
        seg = L[k + 1] - L[k]
        out.append(dense[k].lerp(dense[k + 1], (d - L[k]) / seg if seg > 0 else 0))
    return out


def capsule_path(ctrl, r, n=12, cap0=True, cap1=True, rfn=None, ncap=4):
    """Chemin + rayons d'un boudin gonflable : bouts hémisphériques (ou fermés à plat)."""
    pts = spline(ctrl, n)
    radii = [r * (rfn(i / (n - 1)) if rfn else 1.0) for i in range(n)]
    path, rad = list(pts), list(radii)
    T1 = (pts[-1] - pts[-2]).normalized()
    T0 = (pts[0] - pts[1]).normalized()
    if cap1:
        for k in range(1, ncap + 1):
            ph = (math.pi / 2) * k / ncap
            path.append(pts[-1] + T1 * radii[-1] * math.sin(ph))
            rad.append(radii[-1] * math.cos(ph) if k < ncap else 0.0)
    else:
        path.append(pts[-1] + T1 * 1e-4)
        rad.append(0.0)
    if cap0:
        pre_p, pre_r = [], []
        for k in range(ncap, 0, -1):
            ph = (math.pi / 2) * k / ncap
            pre_p.append(pts[0] + T0 * radii[0] * math.sin(ph))
            pre_r.append(radii[0] * math.cos(ph) if k < ncap else 0.0)
        path, rad = pre_p + path, pre_r + rad
    else:
        path, rad = [pts[0] + T0 * 1e-4] + path, [0.0] + rad
    return path, rad


def axis_path(a, b, n, spacing="cos"):
    """n points de a à b, resserrés aux extrémités (pour des bouts bien arrondis)."""
    a, b = Vector(a), Vector(b)
    ts = [(1 - math.cos(math.pi * i / (n - 1))) / 2 if spacing == "cos" else i / (n - 1) for i in range(n)]
    return [a.lerp(b, t) for t in ts], ts


def dome(t, t0=0.15, t1=0.15, e0=0.5, e1=0.5):
    """Profil de bouts arrondis : 0 aux extrémités, 1 au milieu (e = 0.5 -> quart d'ellipse)."""
    if t < t0:
        x = 1 - t / t0
        return max(0.0, 1 - x * x) ** e0
    if t > 1 - t1:
        x = (t - (1 - t1)) / t1
        return max(0.0, 1 - x * x) ** e1
    return 1.0


def ellipse(a, b):
    """Section elliptique : demi-axe a selon la normale (theta=0), b selon la binormale."""
    return lambda th, t: 1.0 / math.sqrt((math.cos(th) / a) ** 2 + (math.sin(th) / b) ** 2)


def superellipse(p, rot=0.0):
    """Section carrée arrondie (p=2 : cercle, p grand : carré)."""
    def f(th, t):
        c, s = abs(math.cos(th - rot)), abs(math.sin(th - rot))
        return 1.0 / ((c ** p + s ** p) ** (1.0 / p))
    return f


def gores(n, amp, phase=0.0, sharp=0.6):
    """Fuseaux gonflés : bombés au centre, pincés aux coutures (theta = phase + k*2pi/n)."""
    def f(th, t):
        x = ((th - phase) * n / TAU) % 1.0
        return 1.0 - amp + amp * math.sin(math.pi * x) ** sharp
    return f


def gore_angles(n, phase=0.0):
    return [phase + TAU * k / n for k in range(n)]


def frame_matrix(loc, normal, up=(0, 0, 1), spin=0.0, scale=1.0):
    """Repère : Z local = normale, Y local ~ up, X local = up x normale."""
    n = Vector(normal).normalized()
    u = Vector(up)
    if abs(n.dot(u.normalized())) > 0.98:
        u = Vector((0, 1, 0)) if abs(n.y) < 0.9 else Vector((1, 0, 0))
    x = u.cross(n).normalized()
    y = n.cross(x)
    R = Matrix((x, y, n)).transposed()
    if spin:
        R = R @ Matrix.Rotation(spin, 3, "Z")
    return Matrix.Translation(Vector(loc)) @ R.to_4x4() @ Matrix.Scale(scale, 4)


def bake(ob, M):
    ob.data.transform(M)
    ob.data.update()
    return ob


def bvh_of(objs):
    bm = bmesh.new()
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    return tree


def surface(bvh, origin, direction, dist=50.0):
    """Premier point de surface touché : (position, normale) ou (None, None)."""
    d = Vector(direction).normalized()
    hit = bvh.ray_cast(Vector(origin), d, dist)
    if hit[0] is None:
        return None, None
    n = hit[1]
    if n.dot(d) > 0:
        n = -n
    return hit[0], n


def conform(ob, M, bvh, lift=0.0, reach=0.6):
    """Plaque un décor (construit dans le plan XY local, relief en +Z) sur la surface, via M."""
    n = M.to_3x3().col[2].normalized()
    sz = M.to_3x3().col[2].length
    for v in ob.data.vertices:
        base = M @ Vector((v.co.x, v.co.y, 0.0))
        hit = bvh.ray_cast(base + n * reach, -n, reach * 3)
        if hit[0] is None:
            v.co = M @ v.co
        else:
            v.co = hit[0] + n * (v.co.z * sz + lift)
    ob.data.update()
    return ob


# ---------------------------------------------------------------------------------------------
# Visage expressif
# ---------------------------------------------------------------------------------------------
class FaceFrame:
    """Projection de coordonnées 2D (u vers la droite du spectateur, v vers le haut) sur la surface."""

    def __init__(self, bvh, center, forward=(0, 1, 0), up=(0, 0, 1), dist=3.0):
        self.bvh = bvh
        self.f = Vector(forward).normalized()  # direction vers laquelle regarde le visage
        self.U = Vector(up).normalized()
        self.R = self.U.cross(self.f).normalized()  # droite du spectateur
        self.U = self.f.cross(self.R).normalized()
        self.c = Vector(center)
        self.dist = dist

    def at(self, u, v):
        o = self.c + self.R * u + self.U * v + self.f * self.dist
        return surface(self.bvh, o, -self.f, self.dist * 3)


def eye_surface_z(x, y, rx, ry, rz):
    q = 1 - (x / rx) ** 2 - (y / ry) ** 2
    return rz * math.sqrt(max(q, 0.0))


def build_face(B, ff, p, prefix="Visage"):
    """Construit yeux, pupilles, reflets, sourcils, bouche, langue, crocs et joues.
    p : dict de paramètres (voir valeurs par défaut ci-dessous). Renvoie la liste des objets."""
    d = dict(eye_r=0.08, eye_dx=0.11, eye_v=0.1, eye_tall=1.25, look=(0.0, -0.1), brow=0.35, brow_arch=0.12,
             brow_w=0.17, mouth_v=-0.1, mouth_w=0.2, mouth_h=0.08, smile=0.6, fangs=True, tongue=True,
             cheeks=True, lift=0.004, grumpy=0.0, pupil_scale=1.0)
    d.update(p)
    objs = []
    er = d["eye_r"]
    for side in (-1, 1):
        u0 = side * d["eye_dx"]
        loc, nrm = ff.at(u0, d["eye_v"])
        if loc is None:
            continue
        n_eye = (nrm + ff.f * 1.5).normalized()
        rx, ry, rz = er, er * d["eye_tall"], er * 0.6
        M = frame_matrix(loc - n_eye * rz * 0.25, n_eye, up=ff.U)
        objs.append(B.sphere(f"{prefix}_Oeil_{'G' if side < 0 else 'D'}", None, (rx, ry, rz), "oeil", 16, 10, M=M))
        # pupille : posée sur la surface de l'œil, regard légèrement vers l'intérieur (air espiègle)
        px = d["look"][0] * er - side * 0.12 * er
        py = d["look"][1] * er
        ps = d["pupil_scale"]
        pz = eye_surface_z(px, py, rx, ry, rz)
        Mp = M @ Matrix.Translation((px, py, pz - er * 0.12))
        objs.append(B.sphere(f"{prefix}_Pupille_{side}", None, (er * 0.5 * ps, er * 0.62 * ps, er * 0.22), "pupille",
                             12, 8, M=Mp))
        hx, hy = px + er * 0.18, py + er * 0.24
        hz = eye_surface_z(hx, hy, rx, ry, rz) + er * 0.08
        Mh = M @ Matrix.Translation((hx, hy, hz))
        objs.append(B.sphere(f"{prefix}_Reflet_{side}", None, (er * 0.13, er * 0.13, er * 0.06), "reflet", 8, 6,
                             M=Mh))
        # sourcil : arc, extrémité intérieure plus basse = air déterminé / taquin
        bw = d["brow_w"]
        ctrl = []
        for k in range(5):
            s = -1 + 2 * k / 4  # -1 extérieur -> +1 intérieur
            uu = u0 - side * s * bw / 2
            vv = d["eye_v"] + ry + er * 0.45 + d["brow_arch"] * er * (1 - s * s) - d["brow"] * er * s
            pl, pn = ff.at(uu, vv)
            if pl is not None:
                ctrl.append(pl + pn * er * 0.12)
        if len(ctrl) >= 3:
            objs.append(B.tube(f"{prefix}_Sourcil_{side}", ctrl, er * 0.17, "couture", n=10, nseg=8,
                               rfn=lambda t: 0.75 + 0.35 * math.sin(math.pi * t)))
        if d["cheeks"]:
            cl, cn = ff.at(side * (d["eye_dx"] + er * 0.9), d["eye_v"] - ry * 1.15)
            if cl is not None:
                Mc = frame_matrix(cl, cn, up=ff.U)
                objs.append(B.sphere(f"{prefix}_Joue_{side}", None, (er * 0.55, er * 0.35, er * 0.12), "joue", 10, 6,
                                     M=Mc))
    # bouche en « D » souriant (ou grognon si smile < 0)
    w, h, k = d["mouth_w"], d["mouth_h"], d["smile"]
    mloc, mn = ff.at(0.0, d["mouth_v"])
    if mloc is not None:
        mn = (mn + ff.f).normalized()
        M = frame_matrix(mloc, mn, up=ff.U)
        top, bot = [], []
        N = 12
        for i in range(N + 1):
            x = -w / 2 + w * i / N
            curve = k * h * (2 * x / w) ** 2 - d["grumpy"] * h * (1 - (2 * x / w) ** 2)
            top.append((x, curve))
            bot.append((x, curve - h * math.sqrt(max(0.0, 1 - (2 * x / w) ** 2)) * (1 - 0.3 * k)))
        outline = top + bot[::-1][1:-1]
        outline = outline[::-1]  # sens antihoraire
        mo = B.prism(f"{prefix}_Bouche", outline, 0.012, "bouche")
        conform(mo, M, ff.bvh, lift=d["lift"] - 0.006)
        objs.append(mo)
        if d["tongue"]:
            tw, th = w * 0.42, h * 0.45
            yb = -h * (1 - 0.3 * k) + th * 0.55
            pts = [(tw / 2 * math.cos(a), yb + th / 2 * math.sin(a)) for a in
                   [TAU * i / 14 for i in range(14)]]
            to = B.prism(f"{prefix}_Langue", pts, 0.014, "langue")
            conform(to, M, ff.bvh, lift=d["lift"] - 0.003)
            objs.append(to)
        if d["fangs"]:
            for s in (-1, 1):
                x0 = s * w * 0.26
                y0 = k * h * (2 * x0 / w) ** 2 + 0.002
                fw = w * 0.11
                pts = [(x0 - fw / 2, y0), (x0, y0 - h * 0.42), (x0 + fw / 2, y0)][::-1]
                fo = B.prism(f"{prefix}_Croc_{s}", pts, 0.016, "dent")
                conform(fo, M, ff.bvh, lift=d["lift"] - 0.002)
                objs.append(fo)
    return objs


# ---------------------------------------------------------------------------------------------
# Hiéroglyphes et motifs (traits 2D, normalisés dans [-0.5, 0.5])
# ---------------------------------------------------------------------------------------------
def _circle(cx, cy, r, n=10, a0=0.0, a1=TAU):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / (n - 1)), cy + r * math.sin(a0 + (a1 - a0) * i / (n - 1)))
            for i in range(n)]


HIEROGLYPHS = {
    # Œil (oudjat stylisé)
    "oeil": [[(-0.45, 0.05), (-0.2, 0.2), (0.15, 0.2), (0.45, 0.02)], [(-0.45, 0.05), (-0.1, -0.12), (0.3, -0.05),
             (0.45, 0.02)], _circle(0.0, 0.04, 0.09, 8), [(-0.05, -0.1), (-0.1, -0.4)],
             [(0.1, -0.08), (0.25, -0.35), (0.38, -0.3)], [(-0.4, 0.3), (0.0, 0.38), (0.4, 0.3)]],
    # Ânkh
    "ankh": [_circle(0.0, 0.25, 0.16, 12), [(0.0, 0.09), (0.0, -0.48)], [(-0.3, 0.02), (0.3, 0.02)]],
    # Eau (zigzag, signe « n »)
    "eau": [[(-0.45, y), (-0.3, y + 0.08), (-0.15, y), (0.0, y + 0.08), (0.15, y), (0.3, y + 0.08), (0.45, y)]
            for y in (0.2, -0.05, -0.3)],
    # Disque solaire avec ailes
    "soleil": [_circle(0.0, 0.05, 0.16, 12), [(-0.18, 0.05), (-0.48, 0.15), (-0.45, -0.02)],
               [(0.18, 0.05), (0.48, 0.15), (0.45, -0.02)], [(-0.2, -0.25), (0.2, -0.25)]],
    # Oiseau (ibis stylisé)
    "oiseau": [[(-0.3, 0.3), (-0.1, 0.35), (0.0, 0.25), (0.05, -0.1), (-0.2, -0.25), (0.3, -0.25),
                (0.15, -0.05), (0.05, -0.1)], [(-0.3, 0.3), (-0.45, 0.1)], [(-0.05, -0.25), (-0.1, -0.45)],
               [(0.05, -0.25), (0.08, -0.45)]],
    # Plume de Maât
    "plume": [[(0.0, -0.45), (0.0, 0.4), (0.15, 0.45)], [(0.0, 0.3), (0.2, 0.2), (0.2, -0.35), (0.0, -0.4)]],
    # Scarabée stylisé
    "scarabee": [_circle(0.0, -0.05, 0.2, 12), [(0.0, 0.15), (0.0, -0.25)], _circle(0.0, 0.25, 0.08, 8),
                 [(-0.2, 0.0), (-0.4, 0.15)], [(0.2, 0.0), (0.4, 0.15)], [(-0.18, -0.15), (-0.38, -0.32)],
                 [(0.18, -0.15), (0.38, -0.32)]],
    # Lotus
    "lotus": [[(0.0, -0.45), (0.0, -0.05)], [(0.0, -0.05), (-0.12, 0.2), (0.0, 0.45), (0.12, 0.2), (0.0, -0.05)],
              [(0.0, -0.05), (-0.35, 0.05), (-0.3, 0.3)], [(0.0, -0.05), (0.35, 0.05), (0.3, 0.3)]],
    # Dunes (motif de vagues de sable)
    "dunes": [[(-0.5, -0.1), (-0.3, 0.12), (-0.1, -0.1), (0.1, 0.12), (0.3, -0.1), (0.5, 0.12)],
              [(-0.5, -0.35), (-0.3, -0.13), (-0.1, -0.35), (0.1, -0.13), (0.3, -0.35), (0.5, -0.13)]],
    # Cactus (motif)
    "cactus": [[(0.0, -0.45), (0.0, 0.4)], [(0.0, -0.05), (-0.25, -0.05), (-0.25, 0.25)],
               [(0.0, 0.1), (0.25, 0.1), (0.25, 0.35)]],
}


def glyph(B, name, strokes, size, M, bvh, role="glyphe", width=0.045, lift=0.0):
    """Hiéroglyphe en relief : un boudin fin par trait, plaqué sur la surface."""
    objs = []
    for i, st in enumerate(strokes):
        ctrl = [Vector((x * size, y * size, 0.0)) for x, y in st]
        if len(ctrl) < 2:
            continue
        n = max(4, min(18, len(ctrl) * 3))
        ob = B.tube(f"{name}_{i}", ctrl, width * size, role, n=n, nseg=6, ncap=2)
        # rayon ~ demi-épaisseur : relief = moitié haute du boudin
        conform(ob, M, bvh, lift=lift)
        objs.append(ob)
    return objs


# ---------------------------------------------------------------------------------------------
# Pondérations (vertex groups)
# ---------------------------------------------------------------------------------------------
def weight_all(ob, bone):
    vg = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
    vg.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")
    return ob


def weight_fn(ob, fn):
    """fn(co) -> {os: poids} (normalisé ici)."""
    groups = {}
    for v in ob.data.vertices:
        w = fn(v.co)
        tot = sum(w.values()) or 1.0
        for b, x in w.items():
            if x <= 1e-4:
                continue
            if b not in groups:
                groups[b] = ob.vertex_groups.get(b) or ob.vertex_groups.new(name=b)
            groups[b].add([v.index], x / tot, "REPLACE")
    return ob


def gradient(axis, stops):
    """Mélange linéaire entre os placés le long d'un axe : stops = [(coord, os), ...] triés."""
    i_ax = "xyz".index(axis)

    def fn(co):
        x = co[i_ax]
        if x <= stops[0][0]:
            return {stops[0][1]: 1.0}
        if x >= stops[-1][0]:
            return {stops[-1][1]: 1.0}
        for (a, ba), (b, bb) in zip(stops, stops[1:]):
            if a <= x <= b:
                t = (x - a) / (b - a)
                t = t * t * (3 - 2 * t)
                return {ba: 1 - t, bb: t} if ba != bb else {ba: 1.0}
        return {stops[-1][1]: 1.0}
    return fn


# ---------------------------------------------------------------------------------------------
# Rig, assemblage, shape keys
# ---------------------------------------------------------------------------------------------
SHAPES = ("Degonfle", "Gonfle")


def make_rig(name, bones, coll, length=0.08):
    """bones : [(nom, tête (x, y, z), parent ou None)]. Os orientés comme le monde (vers +Y, roll 0).
    Ajoute les os de contrôle (non déformants) des shape keys sous Root."""
    arm = bpy.data.armatures.new(name + "_Armature")
    rig = bpy.data.objects.new(name, arm)
    coll.objects.link(rig)
    arm.display_type = "STICK"
    rig.show_in_front = True
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for bname, head, parent in bones:
        eb = arm.edit_bones.new(bname)
        eb.head = head
        eb.tail = Vector(head) + Vector((0, length, 0))
        eb.roll = 0.0
        eb.use_deform = True
        if parent:
            eb.parent = arm.edit_bones[parent]
            eb.use_connect = False
    for s in SHAPES:
        eb = arm.edit_bones.new("CTRL_" + s)
        eb.head = (0, 0, 0)
        eb.tail = (0, length * 0.5, 0)
        eb.use_deform = False
        eb.parent = arm.edit_bones[bones[0][0]]
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
    return rig


def join(objs, name):
    objs = [o for o in objs if o is not None]
    target = objs[0]
    with bpy.context.temp_override(active_object=target, selected_editable_objects=objs,
                                   selected_objects=objs):
        bpy.ops.object.join()
    target.name = name
    target.data.name = name
    return target


def bind(mesh, rig):
    mesh.parent = rig
    mod = mesh.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    return mod


def add_shape_keys(mesh, shapes):
    """shapes : {nom: fn(co) -> nouvelle position}."""
    mesh.shape_key_add(name="Basis", from_mix=False)
    for name, fn in shapes.items():
        sk = mesh.shape_key_add(name=name, from_mix=False)
        for i, v in enumerate(mesh.data.vertices):
            sk.data[i].co = fn(v.co.copy())
    mesh.data.shape_keys.name = mesh.name + "_Keys"
    return mesh.data.shape_keys


def drive_shape_keys(key, rig):
    """valeur de la shape key = position X locale de l'os CTRL_<nom> (bornée 0..1)."""
    for kb in key.key_blocks[1:]:
        fc = kb.driver_add("value")
        drv = fc.driver
        drv.type = "SCRIPTED"
        drv.expression = "min(max(v, 0.0), 1.0)"
        var = drv.variables.new()
        var.name = "v"
        var.type = "SINGLE_PROP"
        var.targets[0].id_type = "OBJECT"
        var.targets[0].id = rig
        var.targets[0].data_path = f'pose.bones["CTRL_{kb.name}"].location[0]'


def wrinkle(co, k=1.0, seed=0.0):
    """Bruit de plis déterministe (pour le dégonflage)."""
    return (math.sin(co.x * 23.0 * k + seed) * math.sin(co.y * 19.0 * k + 1.3) * 0.6
            + math.sin(co.z * 29.0 * k + co.x * 7.0 + seed) * 0.4)


# ---------------------------------------------------------------------------------------------
# Animation procédurale -> actions à keyframes
# ---------------------------------------------------------------------------------------------
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def K(*keys):
    """Courbe pose-à-pose : K((f0, v0), (f1, v1), ...) -> fonction t -> valeur (ease in/out par segment)."""
    keys = sorted(keys)

    def f(t):
        if t <= keys[0][0]:
            return keys[0][1]
        for (a, va), (b, vb) in zip(keys, keys[1:]):
            if t <= b:
                e = ease((t - a) / (b - a))
                if isinstance(va, (tuple, list)):
                    return tuple(x + (y - x) * e for x, y in zip(va, vb))
                return va + (vb - va) * e
        return keys[-1][1]
    return f


def vol(s, axis="z"):
    """Squash & stretch à volume constant le long d'un axe."""
    o = 1.0 / math.sqrt(max(s, 1e-3))
    return {"x": (s, o, o), "y": (o, s, o), "z": (o, o, s)}[axis]


def damp(t, t0, amp, freq, decay):
    """Oscillation amortie démarrant à t0."""
    if t < t0:
        return 0.0
    x = t - t0
    return amp * math.sin(x * freq) * math.exp(-x / decay)


def jitter(t, amp, seed=0.0):
    return amp * (math.sin(t * 2.7 + seed) * 0.6 + math.sin(t * 5.3 + seed * 2.1) * 0.4)


class Pose(dict):
    def __init__(self):
        super().__init__()
        self.shapes = {}

    def add(self, bone, loc=None, rot=None, scl=None):
        d = self.setdefault(bone, {"loc": [0.0, 0.0, 0.0], "rot": [0.0, 0.0, 0.0], "scl": [1.0, 1.0, 1.0]})
        if loc:
            for i in range(3):
                d["loc"][i] += loc[i]
        if rot:
            for i in range(3):
                d["rot"][i] += rot[i]
        if scl is not None:
            s = (scl, scl, scl) if isinstance(scl, (int, float)) else scl
            for i in range(3):
                d["scl"][i] *= s[i]
        return self

    def shape(self, name, value):
        self.shapes[name] = max(self.shapes.get(name, 0.0), value)
        return self


def _slot_for(act, id_type):
    return next((s for s in act.slots if s.target_id_type == id_type), None)


def assign_action(rig, key, act):
    """key : conservé pour compatibilité (les shape keys suivent l'armature par drivers)."""
    rig.animation_data.action = act
    s = _slot_for(act, "OBJECT")
    if s:
        rig.animation_data.action_slot = s


def bake_action(rig, key, name, nframes, fn, loop=False, step=2):
    """Échantillonne fn(t) (t = 0 .. nframes) et pose des keyframes sur TOUS les os (y compris CTRL_*
    qui portent les valeurs des shape keys). Image 1 = t 0. Boucles : la clé t = nframes (image N+1)
    égale la première, plage d'action 1..N : le moteur enchaîne N -> 1 sans à-coup."""
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = act
    end = nframes if loop else nframes - 1
    ts = list(range(0, end + 1, step))
    if ts[-1] != end:
        ts.append(end)
    for t in ts:
        pose = fn(t)
        f = t + 1
        for s in SHAPES:
            pose.add("CTRL_" + s, loc=(min(max(pose.shapes.get(s, 0.0), 0.0), 1.0), 0, 0))
        for pb in rig.pose.bones:
            d = pose.get(pb.name)
            pb.location = d["loc"] if d else (0, 0, 0)
            pb.rotation_euler = d["rot"] if d else (0, 0, 0)
            pb.scale = d["scl"] if d else (1, 1, 1)
            pb.keyframe_insert("location", frame=f, group=pb.name)
            pb.keyframe_insert("rotation_euler", frame=f, group=pb.name)
            pb.keyframe_insert("scale", frame=f, group=pb.name)
    act.use_frame_range = True
    act.frame_start = 1
    act.frame_end = nframes if loop else nframes
    act.use_cyclic = loop
    return act


# ---------------------------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------------------------
def export_fbx(path, rig, mesh):
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"ARMATURE", "MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
        use_mesh_modifiers=False, mesh_smooth_type="FACE", use_triangles=False,  # True casse les blendshapes animés
        add_leaf_bones=False, primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=True,
        bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True,
        bake_anim_step=1.0, bake_anim_simplify_factor=0.5, use_custom_props=True,
        path_mode="AUTO", embed_textures=False)
