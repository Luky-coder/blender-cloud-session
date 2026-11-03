"""Projection sur l'enveloppe d'un ennemi : points d'ancrage, décalcomanies en relief, patchs, chemins."""
import math

import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from . import geo

TAU = math.tau


class Surface:
    def __init__(self, objs, center):
        bm = bmesh.new()
        for ob in objs:  # objets à transformation identité : coordonnées monde
            bm.from_mesh(ob.data)
        bm.normal_update()
        self.tree = BVHTree.FromBMesh(bm)
        self.center = Vector(center)
        bm.free()

    def ray(self, direction, origin=None):
        """Point de l'enveloppe dans la direction donnée depuis le centre (lancer depuis l'extérieur)."""
        d = Vector(direction).normalized()
        o = Vector(origin) if origin is not None else self.center
        far = o + d * 50.0
        loc, nor, _i, _d = self.tree.ray_cast(far, -d)
        if loc is None:
            loc, nor, _i, _d = self.tree.find_nearest(o + d)
        return loc, nor.normalized()

    def project(self, p, n):
        """Projette p sur la surface en lançant le long de -n depuis l'extérieur."""
        n = Vector(n).normalized()
        loc, nor, _i, _d = self.tree.ray_cast(Vector(p) + n * 5.0, -n)
        if loc is None:
            loc, nor, _i, _d = self.tree.find_nearest(Vector(p))
        return loc, nor.normalized()

    def nearest(self, p):
        loc, nor, _i, _d = self.tree.find_nearest(Vector(p))
        return loc, nor.normalized()


def frame_at(p, n, up=(0, 0, 1)):
    """Repère tangent (t, b, n) : b au plus près de `up`."""
    n = Vector(n).normalized()
    up = Vector(up)
    t = up.cross(n)
    if t.length < 1e-5:
        t = n.orthogonal()
    t.normalize()
    b = n.cross(t)
    return t, b, n


def decal(surf, name, polys, anchor, normal, up, scale, offset, material, subdiv=2):
    """Décalcomanie en relief : polygones 2D (u, v) posés sur la surface autour d'un ancrage.

    u va vers la droite (vu de face), v vers le haut. Les sommets sont densifiés puis projetés.
    """
    t, b, n = frame_at(anchor, normal, up)  # t = droite de l'observateur placé face à la surface
    bm = bmesh.new()
    for poly in polys:
        vs = [bm.verts.new((u * scale, v * scale, 0.0)) for u, v in poly]
        bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    if subdiv:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=subdiv, use_grid_fill=True)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
    verts = []
    for v in bm.verts:
        q = Vector(anchor) + t * v.co.x + b * v.co.y
        loc, nor = surf.project(q, n)
        verts.append(loc + nor * offset)
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    ob = geo.mesh_obj(name, verts, faces, material, smooth=True, recalc=False)
    # normales vers l'extérieur
    me = ob.data
    flip = sum(1 for p in me.polygons if p.normal.dot(n) < 0) > len(me.polygons) / 2
    if flip:
        me.flip_normals()
    return ob


def ellipse(cx, cy, rx, ry, n=20, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        a = TAU * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def patch(surf, name, axis, theta_fn, offset, material, n_theta=8, n_phi=36, up=(0, 1, 0)):
    """Calotte qui épouse l'enveloppe autour d'un axe, de bord theta_fn(phi) (radians)."""
    axis = Vector(axis).normalized()
    t, b, _n = frame_at(Vector(), axis, up)
    verts, faces = [], []
    loc, nor = surf.ray(axis)
    verts.append(loc + nor * offset)
    for i in range(1, n_theta + 1):
        for j in range(n_phi):
            phi = TAU * j / n_phi
            th = theta_fn(phi) * i / n_theta
            d = axis * math.cos(th) + (t * math.cos(phi) + b * math.sin(phi)) * math.sin(th)
            loc, nor = surf.ray(d)
            verts.append(loc + nor * offset * (1.0 if i < n_theta else 0.4))
    for j in range(n_phi):
        faces.append((0, 1 + j, 1 + (j + 1) % n_phi))
    for i in range(n_theta - 1):
        a0, a1 = 1 + i * n_phi, 1 + (i + 1) * n_phi
        for j in range(n_phi):
            faces.append((a0 + j, a1 + j, a1 + (j + 1) % n_phi, a0 + (j + 1) % n_phi))
    ob = geo.mesh_obj(name, verts, faces, material, smooth=True)
    return ob


def surface_path(surf, dirs, offset, origins=None):
    """Points de surface (décalés le long de la normale) pour une liste de directions depuis le centre."""
    out = []
    for k, d in enumerate(dirs):
        loc, nor = surf.ray(d, origins[k] if origins else None)
        out.append((loc + nor * offset, nor))
    return out


def seam_line(surf, name, dirs, radius, material, offset=0.0, closed=False, origins=None, seg=4):
    pts = [p for p, _n in surface_path(surf, dirs, offset + radius * 0.4, origins)]
    if closed:
        pts = pts + [pts[0]]
    return geo.tube(name, pts, radius, seg, material, caps=not closed)
