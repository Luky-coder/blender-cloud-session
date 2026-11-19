"""Bibliothèque commune du Monde 3 « Le Royaume Givré ».

Contient tout ce qui est partagé par les 23 ennemis :
  - matériaux plastique gonflable (Principled BSDF brillant) ;
  - générateurs de géométrie (surfaces paramétriques, tubes, formes 2D gonflées) ;
  - classe `Model` : pièces -> maillage unique skinné sur une armature ;
  - shape keys « Respiration », « Impact », « Degonfle » pilotées par l'os CTRL_Formes ;
  - cuisson des Actions (keyframes) à partir de fonctions de pose ;
  - export .blend / .fbx.

Conventions : mètres, Z vers le haut, AVANT DU MODÈLE VERS +Y, pivot (origine) au sol sous le modèle.
Tous les os ont une orientation de repos identité (os pointant vers +Y, roll 0) : les
translations / rotations / échelles des poses s'expriment donc directement dans les axes du monde.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

TAU = 2 * math.pi
V = Vector


# --------------------------------------------------------------------------------------------
# Couleurs et matériaux
# --------------------------------------------------------------------------------------------
def srgb(hexstr):
    """'#RRGGBB' -> couleur linéaire (r, g, b)."""
    h = hexstr.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


MATERIAL_INFO = {}  # nom -> description (exportée en JSON pour les moteurs de jeu)


RES = 0.7   # densité des maillages (1 = pleine résolution) : modèles allégés pour le jeu


def mat(name, hexcolor, rough=0.2, metal=0.0, coat=0.7, emit=None, strength=0.0, alpha=1.0,
        transmission=0.0, fabric=False):
    """Principled BSDF. fabric=True ou '#RRGGBB' (couleur des fuseaux alternés) : toile de montgolfière (nylon satiné, fuseaux et coutures peints
    dans les couleurs de sommets) ; sinon plastique brillant (yeux, valves, cristaux…).
    La couleur affichée vient de l'attribut de sommets « Couleur » (motifs compris)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    col = srgb(hexcolor)
    if fabric:
        rough, coat = 0.42, 0.15
        b.inputs["Sheen Weight"].default_value = 0.5
        b.inputs["Sheen Roughness"].default_value = 0.35
        m["tissu"] = 1
        if isinstance(fabric, str):                       # couleur des fuseaux alternés
            m["tissu_alt"] = srgb(fabric)
    b.inputs["Base Color"].default_value = (*col, 1.0)
    if not any(n.type == "VERTEX_COLOR" for n in m.node_tree.nodes):
        vc = m.node_tree.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Couleur"
        m.node_tree.links.new(vc.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.06
    b.inputs["Specular IOR Level"].default_value = 0.6
    if transmission:
        b.inputs["Transmission Weight"].default_value = transmission
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
    if emit:
        b.inputs["Emission Color"].default_value = (*srgb(emit), 1.0)
        b.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*col, 1.0)
    m.roughness = rough
    m.metallic = metal
    MATERIAL_INFO[name] = dict(base_color=hexcolor, roughness=rough, metallic=metal, coat=coat,
                               emission=emit, emission_strength=strength, alpha=alpha,
                               transmission=transmission)
    return m


# --------------------------------------------------------------------------------------------
# Géométrie
# --------------------------------------------------------------------------------------------
def _link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def mesh_from_rows(name, rows, pole0=None, pole1=None, closed=True, recalc=True):
    """Maillage à partir d'anneaux de sommets (même nombre par anneau) et de pôles optionnels."""
    verts, faces = [], []
    n = len(rows[0])
    idx0 = None
    if pole0 is not None:
        idx0 = 0
        verts.append(tuple(pole0))
    starts = []
    for row in rows:
        starts.append(len(verts))
        verts.extend(tuple(p) for p in row)
    if pole1 is not None:
        verts.append(tuple(pole1))
    m = n if closed else n - 1
    for r in range(len(rows) - 1):
        a, b = starts[r], starts[r + 1]
        for i in range(m):
            j = (i + 1) % n
            faces.append((a + i, a + j, b + j, b + i))
    if idx0 is not None:
        a = starts[0]
        for i in range(m):
            faces.append((idx0, a + (i + 1) % n, a + i))
    if pole1 is not None:
        a = starts[-1]
        p = len(verts) - 1
        for i in range(m):
            faces.append((a + i, a + (i + 1) % n, p))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    R = len(rows) - 1
    pu, pv = [], []
    for r in range(R):
        for i in range(m):
            pu.append((i + 0.5) / n)
            pv.append((r + 0.5) / max(R, 1))
    for v_cap in ([0.0] if idx0 is not None else []) + ([1.0] if pole1 is not None else []):
        for i in range(m):
            pu.append((i + 0.5) / n)
            pv.append(v_cap)
    for key, vals in (("pat_u", pu), ("pat_v", pv), ("pat_n", [float(n)] * len(pu)), ("pat_r", [float(R)] * len(pu))):
        at = me.attributes.new(key, "FLOAT", "FACE")
        at.data.foreach_set("value", vals)
    me.validate()
    if recalc:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
    me.shade_smooth()
    return _link(bpy.data.objects.new(name, me))


def surface(name, fn, nu, nv, pole0=False, pole1=False, closed=True):
    """Surface paramétrique fn(u, v) -> Vector, u ∈ [0,1) autour, v ∈ [0,1] le long."""
    step = 8 if nu * RES >= 24 else 4                     # fuseaux alignés sur la grille
    nu = max(8, step * round(nu * RES / step))
    nv = max(4, round(nv * RES))
    rows = []
    j0 = 1 if pole0 else 0
    j1 = nv - 1 if pole1 else nv
    count = nu if closed else nu + 1
    for j in range(j0, j1 + 1):
        v = j / nv
        rows.append([fn(i / nu, v) for i in range(count)])
    return mesh_from_rows(name, rows, fn(0, 0) if pole0 else None, fn(0, 1) if pole1 else None,
                          closed=closed)


def ellipsoid(name, center, radii, nu=24, nv=14, disp=None, M=None):
    """Ellipsoïde ; disp(u, v, p_local) -> facteur radial optionnel ; M rotation optionnelle."""
    c = V(center)
    rx, ry, rz = radii
    R = M.to_3x3() if M is not None else Matrix.Identity(3)

    def fn(u, v):
        th = math.pi * (v - 0.5)
        ph = TAU * u
        p = V((math.cos(th) * math.cos(ph), math.cos(th) * math.sin(ph), math.sin(th)))
        k = disp(u, v, p) if disp else 1.0
        return c + R @ V((p.x * rx * k, p.y * ry * k, p.z * rz * k))

    return surface(name, fn, nu, nv, pole0=True, pole1=True)


def sphere(name, center, r, nu=16, nv=10):
    return ellipsoid(name, center, (r, r, r), nu, nv)


def _frames(pts):
    """Repères (tangente, normale, binormale) par transport parallèle le long d'une polyligne."""
    n = len(pts)
    tans = []
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        t = (b - a)
        tans.append(t.normalized() if t.length > 1e-9 else V((0, 0, 1)))
    ref = V((0, 0, 1)) if abs(tans[0].z) < 0.9 else V((1, 0, 0))
    nrm = tans[0].cross(ref).normalized()
    out = []
    for i, t in enumerate(tans):
        if i > 0:
            q = tans[i - 1].rotation_difference(t)
            nrm = (q @ nrm)
            nrm = (nrm - t * nrm.dot(t)).normalized()
        out.append((t, nrm, t.cross(nrm).normalized()))
    return out


def tube(name, pts, radii, nseg=12, caps=(True, True), cap_rings=4, squash=None):
    """Tube gonflable le long d'une polyligne, rayons par point, extrémités hémisphériques.
    squash(i, a) -> facteur sur le rayon (pour les profils non circulaires)."""
    pts = [V(p) for p in pts]
    nseg = max(6, 2 * round(nseg * RES / 2))
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * len(pts)
    fr = _frames(pts)

    def ring(c, r, t, n, b, i=None):
        row = []
        for k in range(nseg):
            a = TAU * k / nseg
            s = squash(i, a) if (squash and i is not None) else 1.0
            row.append(c + (n * math.cos(a) + b * math.sin(a)) * r * s)
        return row

    rows = []
    pole0 = pole1 = None
    if caps[0]:
        t, n, b = fr[0]
        for c in range(cap_rings, 0, -1):
            ph = (math.pi / 2) * c / (cap_rings + 1)
            rows.append(ring(pts[0] - t * radii[0] * math.sin(ph), radii[0] * math.cos(ph), t, n, b))
        pole0 = pts[0] - t * radii[0]
    for i, p in enumerate(pts):
        t, n, b = fr[i]
        rows.append(ring(p, radii[i], t, n, b, i))
    if caps[1]:
        t, n, b = fr[-1]
        for c in range(1, cap_rings + 1):
            ph = (math.pi / 2) * c / (cap_rings + 1)
            rows.append(ring(pts[-1] + t * radii[-1] * math.sin(ph), radii[-1] * math.cos(ph), t, n, b))
        pole1 = pts[-1] + t * radii[-1]
    return mesh_from_rows(name, rows, pole0, pole1)


def bezier_pts(p0, p1, p2, p3, n=12):
    p0, p1, p2, p3 = map(V, (p0, p1, p2, p3))
    out = []
    for i in range(n + 1):
        t = i / n
        a = 1 - t
        out.append(p0 * a ** 3 + p1 * 3 * a * a * t + p2 * 3 * a * t * t + p3 * t ** 3)
    return out


def torus(name, center, R, r, nu=32, nv=10, M=None, lobes=0, lobe_amp=0.0):
    c = V(center)
    Rm = M.to_3x3() if M is not None else Matrix.Identity(3)

    def fn(u, v):
        ph, th = TAU * u, TAU * v
        rr = r * (1 + lobe_amp * abs(math.cos(lobes * ph / 2))) if lobes else r
        p = V(((R + rr * math.cos(th)) * math.cos(ph), (R + rr * math.cos(th)) * math.sin(ph), rr * math.sin(th)))
        return c + Rm @ p

    nu = max(8, 4 * round(nu * RES / 4))
    nv = max(4, round(nv * RES))
    rows = [[fn(i / nu, j / nv) for i in range(nu)] for j in range(nv)]
    # fermeture en v : on ajoute la première rangée à la fin
    rows.append(rows[0])
    ob = mesh_from_rows(name, rows)
    _merge(ob)
    return ob


def _merge(ob, dist=1e-5):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.shade_smooth()


def apply_modifiers(ob):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    bpy.data.meshes.remove(old)
    return ob


def puffy(name, pts2d, depth, bevel_w, M=None, segs=4, sharp=70):
    """Forme 2D (x, z) extrudée en Y puis biseautée en coussin : lettre / étoile gonflable.
    M place la forme (son plan XZ, épaisseur en Y)."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, -depth / 2, z)) for x, z in pts2d]
    f = bm.faces.new(vs)
    bm.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    res = bmesh.ops.extrude_face_region(bm, geom=[f])
    moved = [e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=moved, vec=(0, depth, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = _link(bpy.data.objects.new(name, me))
    mod = ob.modifiers.new("Bevel", "BEVEL")
    mod.width = bevel_w
    mod.segments = segs
    mod.limit_method = "NONE"
    mod.use_clamp_overlap = True
    apply_modifiers(ob)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.to_mesh(ob.data)
    bm.free()
    if M is not None:
        ob.data.transform(M)
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=math.radians(sharp))
    return ob


def rounded_box(name, center, size, bevel_w, segs=3, M=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = _link(bpy.data.objects.new(name, me))
    mod = ob.modifiers.new("Bevel", "BEVEL")
    mod.width = bevel_w
    mod.segments = segs
    mod.limit_method = "NONE"
    mod.use_clamp_overlap = True
    apply_modifiers(ob)
    T = Matrix.Translation(center) @ (M if M is not None else Matrix.Identity(4))
    ob.data.transform(T)
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=math.radians(60))
    return ob


def star_pts(n, r_out, r_in, rot=0.0):
    pts = []
    for i in range(2 * n):
        a = rot + math.pi / 2 + math.pi * i / n
        r = r_out if i % 2 == 0 else r_in
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def look_matrix(pos, normal, up=V((0, 0, 1)), scale=1.0):
    """Matrice qui place un objet local (axe -Y local = « dehors ») … voir orient_y."""
    return orient(pos, normal, up, scale)


def orient(pos, out, up=V((0, 0, 1)), scale=1.0):
    """Repère local : +Y local -> `out`, +Z local -> au plus près de `up`."""
    y = V(out).normalized()
    up = V(up)
    if abs(y.dot(up.normalized())) > 0.98:
        up = V((0, 1, 0)) if abs(y.y) < 0.9 else V((1, 0, 0))
    x = y.cross(up).normalized()
    z = x.cross(y).normalized()
    R = Matrix((x, y, z)).transposed().to_4x4()
    S = Matrix.Diagonal((scale, scale, scale, 1)) if not isinstance(scale, (tuple, list)) else \
        Matrix.Diagonal((*scale, 1))
    return Matrix.Translation(pos) @ R @ S


def xform(ob, M):
    ob.data.transform(M)
    return ob


def lumpy(name, center, radii, amp=0.12, freq=2.2, seed=0, nu=20, nv=12, flat_bottom=None):
    """Blob de neige bosselé (bruit) ; flat_bottom aplatit le dessous."""
    off = V((seed * 3.7, seed * 1.3, seed * 2.1))

    def disp(u, v, p):
        k = 1 + amp * noise.noise((p * freq) + off)
        return k

    ob = ellipsoid(name, center, radii, nu, nv, disp)
    if flat_bottom is not None:
        for vtx in ob.data.vertices:
            if vtx.co.z < flat_bottom:
                vtx.co.z = flat_bottom + (vtx.co.z - flat_bottom) * 0.15
    return ob


def icicle(name, top, length, r, nseg=8, curve=0.0):
    """Petite stalactite (pointe vers le bas) un peu bombée."""
    top = V(top)
    rows = []
    n = 6
    for j in range(n):
        t = j / n
        rr = r * (1 - t) ** 0.8 * (1 + 0.15 * math.sin(math.pi * t))
        c = top + V((curve * t * t, 0, -length * t))
        rows.append([c + V((rr * math.cos(TAU * k / nseg), rr * math.sin(TAU * k / nseg), 0)) for k in range(nseg)])
    return mesh_from_rows(name, rows, pole0=top + V((0, 0, r * 0.4)), pole1=top + V((curve, 0, -length)))


def crystal(name, base, direction, length, r, sides=6, M_up=None):
    """Cristal de glace hexagonal (prisme + pointe), base sur la surface."""
    d = V(direction).normalized()
    M = orient(V(base), d)
    rows = []
    for h in (-0.15, 0.62):
        rows.append([V((r * math.cos(TAU * k / sides), h * length, r * math.sin(TAU * k / sides)))
                     for k in range(sides)])
    ob = mesh_from_rows(name, rows, pole0=V((0, -0.2 * length, 0)), pole1=V((0, length, 0)))
    ob.data.transform(M)
    ob.data.set_sharp_from_angle(angle=math.radians(30))
    return ob


# --------------------------------------------------------------------------------------------
# Modèle : pièces -> maillage unique skinné
# --------------------------------------------------------------------------------------------
class Model:
    """Accumule les pièces (objets maillage + matériau + os), puis construit l'ennemi final :
    un maillage unique, une armature, des shape keys et des Actions."""

    def __init__(self, name, title):
        self.name = name
        self.title = title
        self.parts = []
        self.bones = {}
        self.counter = 0
        self.meta = {}

    # -- os
    def bone(self, name, head, parent=None, soft=None, deform=True, length=0.15):
        """soft = (sigma, poids_de_base) si l'os participe à la pondération douce (RBF)."""
        self.bones[name] = dict(head=V(head), parent=parent, soft=soft, deform=deform, length=length)

    def lift(self, dz):
        """Soulève tout le modèle de dz (pièces déjà ajoutées et têtes d'os, sauf Root et CTRL_Formes)."""
        T = Matrix.Translation((0, 0, dz))
        for ob, _ in self.parts:
            ob.data.transform(T)
        for n, b in self.bones.items():
            if n not in ("Root", "CTRL_Formes"):
                b["head"] = b["head"] + V((0, 0, dz))
        self.meta["eye_centers"] = [c + V((0, 0, dz)) for c in self.meta.get("eye_centers", [])]
        self.meta["locks"] = [(c + V((0, 0, dz)), r, b) for c, r, b in self.meta.get("locks", [])]

    # -- pièces
    def add(self, ob, material, bone=None):
        """bone : nom d'os (rigide), None (pondération douce sur tous les os soft) ou
        liste d'os soft."""
        self.counter += 1
        ob.name = f"{self.name}_p{self.counter:03d}"
        if material is not None:
            ob.data.materials.clear()
            ob.data.materials.append(material)
        self.parts.append((ob, bone))
        return ob

    def lock(self, point, radius, bone):
        """Verrou d'attache : autour de `point`, la peau suit exactement `bone` (pleinement jusqu'à la
        moitié du rayon, puis en fondu). Une pièce animée par `bone` (ou un de ses enfants pivotant sur
        ce point) reste ainsi collée au corps pendant les animations."""
        self.meta.setdefault("locks", []).append((V(point), radius, bone))

    def _face_lock(self, co, ws):
        """Applique les verrous d'attache (yeux + verrous déclarés) au poids d'un sommet de peau."""
        locks = list(self.meta.get("locks", []))
        eyes = self.meta.get("eye_centers")
        if eyes and "Visage" in self.bones:
            r = self.meta.get("eye_r", 0.1)
            for c in eyes:
                locks.append((c, 3.5 * r, self.bones["Visage"]["parent"]))
        best_f, best_b = 0.0, None
        for c, rad, bone in locks:
            x = ((co - c).length - 0.5 * rad) / (0.5 * rad)
            f = 1.0 if x <= 0 else (0.0 if x >= 1 else 1 - x * x * (3 - 2 * x))
            if f > best_f:
                best_f, best_b = f, bone
        if best_f <= 0:
            return ws
        s = sum(ws.values()) or 1.0
        out = {n: (1 - best_f) * w / s for n, w in ws.items()}
        out[best_b] = out.get(best_b, 0.0) + best_f
        return out

    def _weights(self, ob, bone):
        if callable(bone):          # fonction position -> {os: poids}
            groups = {}
            for v in ob.data.vertices:
                ws = self._face_lock(v.co, bone(v.co))
                s = sum(ws.values()) or 1.0
                for n, w in ws.items():
                    if w / s > 0.002:
                        if n not in groups:
                            groups[n] = ob.vertex_groups.new(name=n)
                        groups[n].add([v.index], w / s, "REPLACE")
            return
        if isinstance(bone, str):
            vg = ob.vertex_groups.new(name=bone)
            vg.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")
            return
        names = bone if bone else [n for n, b in self.bones.items() if b["soft"]]
        groups = {}
        for v in ob.data.vertices:
            ws = {}
            for n in names:
                sig, base = self.bones[n]["soft"]
                if sig is None:
                    w = base
                else:
                    d = (v.co - self.bones[n]["head"]).length
                    w = base * math.exp(-(d / sig) ** 2)
                ws[n] = w
            ws = self._face_lock(v.co, ws)
            s = sum(ws.values()) or 1.0
            for n, w in ws.items():
                if w / s > 0.002:
                    if n not in groups:
                        groups[n] = ob.vertex_groups.new(name=n)
                    groups[n].add([v.index], w / s, "REPLACE")

    def drop(self, pred):
        """Retire du modèle les os pred(nom) == True et toutes les pièces qui leur sont attachées."""
        gone = {n for n in self.bones if pred(n)}
        keep = []
        for ob, bone in self.parts:
            if isinstance(bone, str) and bone in gone:
                bpy.data.objects.remove(ob)
            else:
                keep.append((ob, bone))
        self.parts = keep
        for n in gone:
            del self.bones[n]

    def build(self, shape_amp=1.0, wrinkle=0.07):
        for ob, bone in self.parts:
            self._weights(ob, bone)
        objs = [ob for ob, _ in self.parts]
        main = objs[0]
        with bpy.context.temp_override(active_object=main, selected_editable_objects=objs,
                                       selected_objects=objs):
            bpy.ops.object.join()
        main.name = self.name
        main.data.name = self.name
        self.mesh = main
        _merge(main, 1e-6)
        self._paint()
        self._rig()
        self._shape_keys(shape_amp, wrinkle)
        return main

    def _paint(self):
        """Attribut « Couleur » : couleur de chaque matériau ; sur les grandes enveloppes en toile
        (matériaux tissu), motif de montgolfière : fuseaux verticaux alternant les deux couleurs du
        type, séparés par des coutures foncées, qui convergent vers les pôles."""
        me = self.mesh.data
        base, fab = [], []
        for m in me.materials:
            b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            src = "Emission Color" if b.inputs["Emission Strength"].default_value > 1.0 else "Base Color"
            base.append(tuple(b.inputs[src].default_value)[:3])
            fab.append(bool(m.get("tissu")))
        at = me.attributes
        get = {k: [0.0] * len(me.polygons) for k in ("pat_u", "pat_v", "pat_n", "pat_r")}
        for k in get:
            if k in at:
                at[k].data.foreach_get("value", get[k])
        col_attr = me.color_attributes.new("Couleur", "BYTE_COLOR", "CORNER")
        alt = []
        for m in me.materials:
            a = m.get("tissu_alt")
            alt.append(tuple(a) if a else None)
        for p in me.polygons:
            c = base[p.material_index]
            n = int(round(get["pat_n"][p.index]))
            if fab[p.material_index] and n >= 20:
                G = 8 if n >= 32 else 4
                col = min(int(get["pat_u"][p.index] * n), n - 1)
                gore = col * G // n
                seam = n // G >= 5 and (col * G) % n < G
                if seam:                                   # couture entre deux fuseaux
                    c = tuple(x * 0.5 for x in c)
                elif gore % 2:                             # fuseau alterné : 2e couleur du type
                    a = alt[p.material_index]
                    if a:
                        c = a
                    else:
                        lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
                        c = tuple(x * 0.8 for x in c) if lum > 0.6 else tuple(x + (1 - x) * 0.3 for x in c)
            for li in p.loop_indices:
                col_attr.data[li].color = (*c, 1.0)
        me.color_attributes.active_color = col_attr
        for k in ("pat_u", "pat_v", "pat_n", "pat_r"):
            if k in me.attributes:
                me.attributes.remove(me.attributes[k])

    def _rig(self):
        arm = bpy.data.armatures.new(self.name + "_Rig")
        rig = _link(bpy.data.objects.new(self.name + "_Rig", arm))
        arm.display_type = "STICK"
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode="EDIT")
        for n, b in self.bones.items():
            eb = arm.edit_bones.new(n)
            eb.head = b["head"]
            eb.tail = b["head"] + V((0, b["length"], 0))
            eb.roll = 0
            eb.use_deform = b["deform"]
        for n, b in self.bones.items():
            if b["parent"]:
                arm.edit_bones[n].parent = arm.edit_bones[b["parent"]]
        bpy.ops.object.mode_set(mode="OBJECT")
        for pb in rig.pose.bones:
            pb.rotation_mode = "XYZ"
        self.mesh.parent = rig
        mod = self.mesh.modifiers.new("Armature", "ARMATURE")
        mod.object = rig
        self.rig = rig

    def _shape_keys(self, amp, wrinkle=0.07):
        ob = self.mesh
        me = ob.data
        co = [v.co.copy() for v in me.vertices]
        nr = [v.normal.copy() for v in me.vertices]
        lo = V((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
        hi = V((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
        size = (hi - lo)
        ctr = (lo + hi) / 2
        ref = max(size)
        ob.shape_key_add(name="Basis", from_mix=False)

        k = ob.shape_key_add(name="Respiration", from_mix=False)
        k.slider_min = -1.0
        for i, p in enumerate(co):
            k.data[i].co = p + nr[i] * 0.025 * ref * amp

        k = ob.shape_key_add(name="Impact", from_mix=False)
        for i, p in enumerate(co):
            f = max(0.0, min(1.0, (p.y - ctr.y) / (size.y / 2 + 1e-6)))
            f = f * f * (3 - 2 * f)
            q = p.copy()
            q.y = ctr.y + (p.y - ctr.y) * (1 - 0.28 * f)
            q.x = ctr.x + (p.x - ctr.x) * (1 + 0.14 * f)
            q.z = ctr.z + (p.z - ctr.z) * (1 + 0.12 * f)
            k.data[i].co = q

        k = ob.shape_key_add(name="Degonfle", from_mix=False)
        for i, p in enumerate(co):
            w = noise.noise_vector(p * (5.0 / ref))
            q = V((ctr.x + (p.x - ctr.x) * 0.92, ctr.y + (p.y - ctr.y) * 0.92,
                   lo.z + (p.z - lo.z) * 0.32))
            k.data[i].co = q + w * wrinkle * ref + nr[i] * (-0.4 * wrinkle * ref)

        for name, axis in (("Respiration", "LOC_X"), ("Impact", "LOC_Y"), ("Degonfle", "LOC_Z")):
            kb = me.shape_keys.key_blocks[name]
            fc = kb.driver_add("value")
            dr = fc.driver
            dr.type = "AVERAGE"
            var = dr.variables.new()
            var.name = "v"
            var.type = "TRANSFORMS"
            t = var.targets[0]
            t.id = self.rig
            t.bone_target = "CTRL_Formes"
            t.transform_type = axis
            t.transform_space = "LOCAL_SPACE"
        self.bounds = (lo, hi)


# --------------------------------------------------------------------------------------------
# Animations
# --------------------------------------------------------------------------------------------
def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = max(0.0, min(1.0, x))
    return x ** 3


def track(t, keys):
    """Interpolation par morceaux. keys = [(frame, valeur[, 'ease'|'lin'|'in'|'out'|'cr'])].
    Par défaut : Catmull-Rom (souple, léger dépassement)."""
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for i in range(len(keys) - 1):
        f0, v0 = keys[i][0], keys[i][1]
        f1, v1 = keys[i + 1][0], keys[i + 1][1]
        if f0 <= t <= f1:
            mode = keys[i + 1][2] if len(keys[i + 1]) > 2 else "cr"
            x = (t - f0) / (f1 - f0) if f1 > f0 else 1.0
            if mode == "lin":
                return v0 + (v1 - v0) * x
            if mode == "ease":
                return v0 + (v1 - v0) * ease(x)
            if mode == "in":
                return v0 + (v1 - v0) * ease_in(x)
            if mode == "out":
                return v0 + (v1 - v0) * ease_out(x)
            vm = keys[i - 1][1] if i > 0 else v0
            vp = keys[i + 2][1] if i + 2 < len(keys) else v1
            m0 = (v1 - vm) / 2
            m1 = (vp - v0) / 2
            x2, x3 = x * x, x * x * x
            return ((2 * x3 - 3 * x2 + 1) * v0 + (x3 - 2 * x2 + x) * m0 +
                    (-2 * x3 + 3 * x2) * v1 + (x3 - x2) * m1)
    return keys[-1][1]


def track3(t, keys):
    """keys = [(frame, (x, y, z)[, mode])]."""
    return tuple(track(t, [(k[0], k[1][i], *k[2:]) for k in keys]) for i in range(3))


class Pose(dict):
    """Pose : os -> {'loc': (x,y,z), 'rot': (degrés), 'scl': (x,y,z)}."""

    def set(self, bone, loc=None, rot=None, scl=None):
        d = self.setdefault(bone, {})
        if loc is not None:
            d["loc"] = tuple(loc)
        if rot is not None:
            d["rot"] = tuple(rot)
        if scl is not None:
            d["scl"] = (scl, scl, scl) if isinstance(scl, (int, float)) else tuple(scl)
        return self

    def add(self, bone, loc=None, rot=None, scl=None):
        """Cumule (loc et rot additionnés, échelles multipliées)."""
        d = self.setdefault(bone, {})
        if loc is not None:
            o = d.get("loc", (0, 0, 0))
            d["loc"] = tuple(a + b for a, b in zip(o, loc))
        if rot is not None:
            o = d.get("rot", (0, 0, 0))
            d["rot"] = tuple(a + b for a, b in zip(o, rot))
        if scl is not None:
            s = (scl, scl, scl) if isinstance(scl, (int, float)) else scl
            o = d.get("scl", (1, 1, 1))
            d["scl"] = tuple(a * b for a, b in zip(o, s))
        return self

    def shapes(self, resp=0.0, impact=0.0, deflate=0.0):
        self["CTRL_Formes"] = {"loc": (resp, impact, deflate)}
        return self


def bake_action(rig, name, nframes, fn, loop=False):
    """Crée l'Action `name` (frames 1..nframes) en échantillonnant fn(t) (t = frame - 1)."""
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    slot = act.slots.new(id_type="OBJECT", name=rig.name)
    layer = act.layers.new("Layer")
    strip = layer.strips.new(type="KEYFRAME")
    cb = strip.channelbag(slot, ensure=True)
    poses = [fn(t) for t in range(nframes)]
    for pb in rig.pose.bones:
        b = pb.name
        for prop, key, default in (("location", "loc", (0, 0, 0)), ("rotation_euler", "rot", (0, 0, 0)),
                                   ("scale", "scl", (1, 1, 1))):
            for i in range(3):
                vals = [p.get(b, {}).get(key, default)[i] for p in poses]
                if key == "rot":
                    vals = [math.radians(x) for x in vals]
                const = max(vals) - min(vals) < 1e-6
                fc = cb.fcurves.new(f'pose.bones["{b}"].{prop}', index=i, group_name=b)
                frames = [1, nframes] if const else list(range(1, nframes + 1))
                vv = [vals[0], vals[0]] if const else vals
                fc.keyframe_points.add(len(frames))
                flat = []
                for f, v in zip(frames, vv):
                    flat += [f, v]
                fc.keyframe_points.foreach_set("co", flat)
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
                if loop:
                    fc.modifiers.new("CYCLES")
                fc.update()
    act.use_frame_range = True
    act.frame_start = 1
    act.frame_end = nframes
    act.use_cyclic = loop
    act["w3_loop"] = loop
    return act, slot


def set_action(rig, act):
    ad = rig.animation_data or rig.animation_data_create()
    ad.action = act
    ad.action_slot = act.slots[0]
    sc = bpy.context.scene
    sc.frame_start = int(act.frame_start)
    sc.frame_end = int(act.frame_end)


# Fonctions temporelles utiles ------------------------------------------------------------------
def osc(t, period, phase=0.0, harm=1):
    return math.sin(TAU * harm * t / period + phase)


def decay(t, t0, dur, freq, amp):
    """Vibration amortie à partir de t0."""
    if t < t0:
        return 0.0
    x = (t - t0) / dur
    if x > 1:
        return 0.0
    return amp * math.sin(TAU * freq * x) * (1 - x) ** 2
