"""Les 7 types élémentaires : palettes de matériaux + décors élémentaires.

Chaque type fournit :
- palette : couleurs des rôles élémentaires (corps, corps2, couture, glyphe, epine, fx, fx2, pupille, joue) ;
- face : réglages d'expression du visage ;
- crown(B, M, s) : décor de sommet (halo, flamme, cristaux...) construit en repère local (Z = haut) puis M ;
- particle(B, M, s, i) : (non utilisée : plus rien ne flotte autour des ballons) ;
- emblem(B, name, M, bvh, s) : emblème en relief plaqué sur la surface.
Les décors restent petits et au-dessus / autour du corps : la silhouette de la famille est conservée.
"""
import math

from mathutils import Matrix, Vector

from .core import TAU, bake, conform, glyph, spline


def _star(n, r_out, r_in, a0=math.pi / 2):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = a0 + math.pi * i / n
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def _circle(r, n=14, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(TAU * i / n), cy + r * math.sin(TAU * i / n)) for i in range(n)]


BOLT = [(0.05, 0.5), (-0.22, 0.02), (-0.02, 0.02), (-0.12, -0.5), (0.24, 0.08), (0.03, 0.08), (0.18, 0.5)]


def _flame_outline(w=0.5, h=1.0, n=10):
    """Silhouette de flamme (goutte à pointe ondulée), centrée en bas sur (0, -h/2)."""
    right, left = [], []
    for i in range(n + 1):
        t = i / n
        r = w * math.sin(math.pi * t) ** 0.7 * (1 - 0.55 * t)
        y = -h / 2 + h * t
        sway = 0.06 * h * math.sin(t * 5.5)
        right.append((sway + r, y))
        left.append((sway - r, y))
    return right + left[::-1][1:-1]


def _upright(depth):
    """Prisme dessiné dans XY puis redressé : plan XZ, épaisseur centrée sur Y."""
    return Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Translation((0, 0, -depth / 2))


def _flame(B, name, M, w, h, bend, role, n=10, nseg=10):
    ctrl = [Vector((0, 0, 0)), Vector((bend * 0.3, 0, h * 0.35)), Vector((-bend * 0.2, 0, h * 0.7)),
            Vector((bend, 0, h))]
    path = spline(ctrl, n)
    radii = [w * math.sin(math.pi * (i / (n - 1))) ** 0.6 * (1 - 0.6 * i / (n - 1)) for i in range(n)]
    radii[0] = radii[-1] = 0.0
    ob = B.sweep(name, path, radii, [role], nseg=nseg)
    return bake(ob, M)


def _leaf(B, name, M, length, width, role, curl=0.25, n=8):
    ctrl = [Vector((0, 0, 0)), Vector((0, length * 0.5, length * curl * 0.6)), Vector((0, length, length * curl * 0.2))]
    path = spline(ctrl, n)
    radii = [width * math.sin(math.pi * (i / (n - 1))) ** 0.8 for i in range(n)]
    radii[0] = radii[-1] = 0.0

    def sec(th, t):
        return 1.0 / math.sqrt(math.cos(th) ** 2 / 0.12 ** 2 + math.sin(th) ** 2)
    ob = B.sweep(name, path, radii, [role], nseg=8, section=sec, up=(0, 0, 1))
    return bake(ob, M)


def _drop(B, name, M, w, h, role, n=10):
    path = [Vector((0, 0, h * i / (n - 1))) for i in range(n)]
    radii = [w * math.sin(math.pi * (i / (n - 1)) ** 0.6) ** 0.8 for i in range(n)]
    radii[0] = radii[-1] = 0.0
    return bake(B.sweep(name, path, radii, [role], nseg=10), M)


# ---------------------------------------------------------------------------------------------
# LUMIÈRE
# ---------------------------------------------------------------------------------------------
def crown_lumiere(B, M, s):
    """Étoile dorée plantée au sommet, cerclée d'un anneau-halo posé sur la tête (rien ne flotte)."""
    d = s * 0.1
    out = [B.prism("FX_Etoile", _star(4, s * 0.36, s * 0.12), d, "fx2",
                   M=M @ Matrix.Translation((0, 0, s * 0.3)) @ _upright(d), smooth=False),
           bake(B.ring("FX_Halo", (0, 0, s * 0.03), s * 0.26, s * 0.06, "fx", nseg=6, n=20), M)]
    return out


def particle_lumiere(B, M, s, i):
    d = s * 0.25
    return [B.prism(f"Aura_Etincelle_{i}", _star(4, s * 0.55, s * 0.16), d, "fx",
                    M=M @ Matrix.Translation((0, 0, -d / 2)))]


def emblem_lumiere(B, name, M, bvh, s):
    out = [conform(B.prism(name + "_Disque", _circle(0.2 * s, 16)[::-1], 0.012, "glyphe"), M, bvh, lift=-0.004)]
    for k in range(8):
        a = TAU * k / 8
        c, sn = math.cos(a), math.sin(a)
        tri = [(c * 0.27 * s - sn * 0.05 * s, sn * 0.27 * s + c * 0.05 * s), (c * 0.45 * s, sn * 0.45 * s),
               (c * 0.27 * s + sn * 0.05 * s, sn * 0.27 * s - c * 0.05 * s)]
        out.append(conform(B.prism(f"{name}_Rayon_{k}", tri, 0.012, "glyphe"), M, bvh, lift=-0.004))
    return out


# ---------------------------------------------------------------------------------------------
# TÉNÈBRES
# ---------------------------------------------------------------------------------------------
def _crescent(r, n=12):
    outer = [(r * math.cos(a), r * math.sin(a)) for a in
             [math.pi / 2 + math.pi * 1.25 * i / (n - 1) for i in range(n)]]
    inner = [(r * 0.35 + r * 0.8 * math.cos(a), r * 0.15 + r * 0.8 * math.sin(a)) for a in
             [math.pi / 2 + math.pi * 1.25 * i / (n - 1) for i in range(n)]]
    return outer + inner[::-1]


def crown_tenebres(B, M, s):
    out = []
    for k in range(6):
        a = k * 1.9
        r = s * (0.34 - 0.04 * k)
        loc = Vector((math.cos(a) * s * 0.18 * (1 - k / 7), math.sin(a) * s * 0.18 * (1 - k / 7), s * (0.12 + 0.2 * k)))
        out.append(B.sphere(f"FX_Fumee_{k}", None, (r, r, r * 0.85), "fx", 10, 6, M=M @ Matrix.Translation(loc)))
    d = s * 0.08
    pts = _crescent(s * 0.3)
    pts = pts[::-1]
    out.append(B.prism("FX_Lune", pts, d, "fx2", M=M @ Matrix.Translation((0, 0, s * 1.3)) @ _upright(d)))
    return out


def particle_tenebres(B, M, s, i):
    out = []
    for k, (dx, dy, r) in enumerate(((0, 0, 0.42), (0.35, 0.1, 0.3), (-0.3, -0.05, 0.28))):
        out.append(B.sphere(f"Aura_Fumee_{i}_{k}", None, (r * s,) * 3, "fx", 10, 6,
                            M=M @ Matrix.Translation((dx * s, dy * s, 0))))
    return out


def emblem_tenebres(B, name, M, bvh, s):
    out = [conform(B.prism(name + "_Lune", [(x * 1.3, y * 1.3) for x, y in _crescent(0.3 * s)][::-1], 0.012,
                           "glyphe"), M, bvh, lift=-0.004)]
    out += glyph(B, name + "_Oeil", [[(0.15, 0.25), (0.3, 0.32), (0.45, 0.25)], [(0.15, 0.25), (0.3, 0.18),
                                                                                  (0.45, 0.25)]], s, M, bvh)
    return out


# ---------------------------------------------------------------------------------------------
# GLACE
# ---------------------------------------------------------------------------------------------
def _crystal(B, name, M, r, h, role):
    body = B.cone(name, M, r, r, h * 0.7, role, seg=6, smooth=False)
    tip = B.cone(name + "_Pointe", M @ Matrix.Translation((0, 0, h * 0.7)), r, 0.0, h * 0.3, role, seg=6,
                 smooth=False)
    return [body, tip]


def crown_glace(B, M, s):
    out = _crystal(B, "FX_Cristal_0", M @ Matrix.Translation((0, 0, -s * 0.05)), s * 0.14, s * 1.0, "fx")
    for k in range(5):
        a = TAU * k / 5 + 0.3
        R = Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((s * 0.16, 0, -s * 0.05)) @ Matrix.Rotation(0.5, 4, "Y")
        out += _crystal(B, f"FX_Cristal_{k + 1}", M @ R, s * 0.09, s * (0.55 + 0.12 * (k % 2)),
                        "fx2" if k % 2 else "fx")
    return out


def _snowflake_strokes():
    st = []
    for k in range(6):
        a = TAU * k / 6
        c, sn = math.cos(a), math.sin(a)
        st.append([(0, 0), (c * 0.45, sn * 0.45)])
        for f in (0.28,):
            px, py = c * f, sn * f
            for da in ((0.6,) if k % 2 else (-0.6,)):
                st.append([(px, py), (px + math.cos(a + da) * 0.14, py + math.sin(a + da) * 0.14)])
    return st


def particle_glace(B, M, s, i):
    out = []
    d = s * 0.18
    for k in range(3):
        R = Matrix.Rotation(math.pi * k / 3, 4, "Z")
        bar = [(-s * 0.55, -s * 0.07), (s * 0.55, -s * 0.07), (s * 0.55, s * 0.07), (-s * 0.55, s * 0.07)]
        out.append(B.prism(f"Aura_Flocon_{i}_{k}", bar, d, "fx2" if k else "fx",
                           M=M @ R @ Matrix.Translation((0, 0, -d / 2))))
    return out


def emblem_glace(B, name, M, bvh, s):
    return glyph(B, name + "_Flocon", _snowflake_strokes(), s, M, bvh, width=0.05)


# ---------------------------------------------------------------------------------------------
# FEU
# ---------------------------------------------------------------------------------------------
def crown_feu(B, M, s):
    out = [_flame(B, "FX_Flamme", M @ Matrix.Translation((0, 0, -s * 0.15)), s * 0.42, s * 1.35, s * 0.18, "fx"),
           _flame(B, "FX_Flamme_Coeur", M @ Matrix.Translation((0, s * 0.2, -s * 0.1)), s * 0.24, s * 0.85,
                  -s * 0.1, "fx2")]
    for k, side in enumerate((-1, 1)):
        R = Matrix.Translation((side * s * 0.3, -s * 0.05, -s * 0.12)) @ Matrix.Rotation(side * 0.45, 4, "Y")
        out.append(_flame(B, f"FX_Flammeche_{k}", M @ R, s * 0.22, s * 0.75, side * s * 0.1, "fx"))
    return out


def particle_feu(B, M, s, i):
    R = Matrix.Rotation(-math.pi / 2, 4, "X")  # flamme (Z) dirigée vers le haut du repère de particule (Y)
    return [_flame(B, f"Aura_Braise_{i}", M @ Matrix.Translation((0, -s * 0.5, 0)) @ R, s * 0.35,
                   s * 1.1, s * 0.12, "fx2", n=9, nseg=8)]


def emblem_feu(B, name, M, bvh, s):
    pts = [(x * s * 0.85, y * s * 0.85) for x, y in _flame_outline(0.3, 1.0)]
    return [conform(B.prism(name + "_Flamme", pts[::-1], 0.012, "glyphe"), M, bvh, lift=-0.004)]


# ---------------------------------------------------------------------------------------------
# EAU
# ---------------------------------------------------------------------------------------------
def crown_eau(B, M, s):
    """Goutte d'eau plantée au sommet (avec son reflet)."""
    out = [_drop(B, "FX_Goutte", M @ Matrix.Translation((0, 0, -s * 0.1)), s * 0.34, s * 1.15, "fx")]
    out.append(B.sphere("FX_Goutte_Reflet", None, (s * 0.07, s * 0.05, s * 0.1), "reflet", 8, 6,
                        M=M @ Matrix.Translation((-s * 0.12, s * 0.26, s * 0.32))))
    return out


def particle_eau(B, M, s, i):
    return [B.sphere(f"Aura_Bulle_{i}", None, (s * 0.5,) * 3, "fx2", 10, 6, M=M),
            B.sphere(f"Aura_Bulle_Reflet_{i}", None, (s * 0.12, s * 0.12, s * 0.06), "reflet", 6, 4,
                     M=M @ Matrix.Translation((-s * 0.2, s * 0.22, s * 0.42)))]


def emblem_eau(B, name, M, bvh, s):
    strokes = [[(-0.45, y), (-0.3, y + 0.1), (-0.15, y), (0.0, y + 0.1), (0.15, y), (0.3, y + 0.1), (0.45, y)]
               for y in (0.18, -0.05, -0.28)]
    return glyph(B, name + "_Vagues", strokes, s, M, bvh, width=0.05)


# ---------------------------------------------------------------------------------------------
# PLANTE
# ---------------------------------------------------------------------------------------------
def crown_plante(B, M, s):
    out = [B.sphere("FX_Fleur_Coeur", None, (s * 0.25, s * 0.25, s * 0.17), "or", 12, 8,
                    M=M @ Matrix.Translation((0, 0, s * 0.18)))]
    for k in range(6):
        a = TAU * k / 6
        R = Matrix.Translation((0, 0, s * 0.12)) @ Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(-0.35, 4, "X")
        out.append(_leaf(B, f"FX_Petale_{k}", M @ R, s * 0.85, s * 0.3, "fx", curl=0.35))
    for k, a in enumerate((0.6, 0.6 + math.pi)):
        R = Matrix.Translation((0, 0, s * 0.02)) @ Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(-0.1, 4, "X")
        out.append(_leaf(B, f"FX_Feuille_{k}", M @ R, s * 1.0, s * 0.28, "fx2", curl=0.1))
    return out


def particle_plante(B, M, s, i):
    return [_leaf(B, f"Aura_Feuille_{i}", M @ Matrix.Translation((0, -s * 0.6, 0)), s * 1.2, s * 0.38, "fx2",
                  curl=0.3)]


def emblem_plante(B, name, M, bvh, s):
    pts = []
    for i in range(16):
        t = i / 15
        y = -0.45 + 0.9 * t
        pts.append((0.22 * math.sin(math.pi * t) ** 0.9, y))
    pts = pts + [(-x, y) for x, y in pts[::-1][1:-1]]
    leaf = conform(B.prism(name + "_Feuille", [(x * s, y * s) for x, y in pts], 0.012, "glyphe"), M, bvh, lift=-0.004)
    vein = glyph(B, name + "_Nervure", [[(0, -0.55), (0, 0.38)], [(0, -0.1), (0.13, 0.08)],
                                        [(0, 0.08), (-0.12, 0.24)]], s, M, bvh, role="fx2", width=0.03, lift=0.008)
    return [leaf] + vein


# ---------------------------------------------------------------------------------------------
# ÉCLAIR
# ---------------------------------------------------------------------------------------------
def crown_eclair(B, M, s):
    """Éclair planté au sommet."""
    d = s * 0.14
    pts = [(x * s * 1.5, y * s * 1.5) for x, y in BOLT][::-1]
    return [B.prism("FX_Eclair", pts, d, "fx2", M=M @ Matrix.Translation((0, 0, s * 0.62)) @ _upright(d))]


def particle_eclair(B, M, s, i):
    d = s * 0.25
    pts = [(x * s * 1.3, y * s * 1.3) for x, y in BOLT][::-1]
    return [B.prism(f"Aura_Eclair_{i}", pts, d, "fx", M=M @ Matrix.Translation((0, 0, -d / 2)))]


def emblem_eclair(B, name, M, bvh, s):
    pts = [(x * s * 0.95, y * s * 0.95) for x, y in BOLT][::-1]
    return [conform(B.prism(name + "_Eclair", pts, 0.012, "glyphe"), M, bvh, lift=-0.004)]


# ---------------------------------------------------------------------------------------------
# Table des types
# ---------------------------------------------------------------------------------------------
def P(color, rough=0.28, metal=0.0, coat=0.7, emit=None, emit_s=0.0, transm=0.0):
    return dict(color=color, rough=rough, metal=metal, coat=coat, emit=emit, emit_s=emit_s, transm=transm)


ELEMENTS = {
    "Lumiere": dict(
        label="Lumière",
        palette=dict(corps=P("#FFF0BE"), corps2=P("#FFC93C"), couture=P("#C08A1E", 0.3),
                     glyphe=P("#B97C10", 0.25, 0.8, 0.3), epine=P("#FFFFFF"),
                     fx=P("#FFE27A", 0.2, emit="#FFCC33", emit_s=2.5), fx2=P("#FFFFFF", 0.2, emit="#FFF0B0", emit_s=2.5),
                     pupille=P("#5A3500"), joue=P("#FFB46B")),
        face=dict(brow=0.15, smile=0.8, look=(0.0, 0.0)),
        crown=crown_lumiere, particle=particle_lumiere, emblem=emblem_lumiere),
    "Tenebres": dict(
        label="Ténèbres",
        palette=dict(corps=P("#3D2559"), corps2=P("#16101E", 0.35), couture=P("#0E0A14", 0.4),
                     glyphe=P("#B36BFF", 0.3, emit="#9F4DFF", emit_s=3.0), epine=P("#C7B2E6"),
                     fx=P("#2B2138", 0.75, coat=0.0), fx2=P("#C890FF", 0.2, emit="#A050FF", emit_s=3.0),
                     pupille=P("#E0B0FF", 0.2, emit="#C070FF", emit_s=4.0), joue=P("#7B4FA8")),
        face=dict(brow=0.55, smile=0.9, grumpy=0.0, look=(0.15, -0.15), pupil_scale=0.85),
        crown=crown_tenebres, particle=particle_tenebres, emblem=emblem_tenebres),
    "Glace": dict(
        label="Glace",
        palette=dict(corps=P("#A8DCF7"), corps2=P("#F5FBFF"), couture=P("#4F8FBF"), glyphe=P("#2C78BC", 0.2),
                     epine=P("#FFFFFF"), fx=P("#DDF5FF", 0.05, transm=0.35), fx2=P("#86CDF5", 0.08),
                     pupille=P("#0F2C45"), joue=P("#B9C6FF")),
        face=dict(brow=0.3, smile=0.4, look=(0.0, -0.05), pupil_scale=0.85),
        crown=crown_glace, particle=particle_glace, emblem=emblem_glace),
    "Feu": dict(
        label="Feu",
        palette=dict(corps=P("#E8432A"), corps2=P("#FF9A2E"), couture=P("#8E2010"),
                     glyphe=P("#FFD23A", 0.25, emit="#FFB020", emit_s=1.5), epine=P("#FFE3A8"),
                     fx=P("#FF6A1A", 0.3, emit="#FF4A0A", emit_s=2.2), fx2=P("#FFD84A", 0.3, emit="#FFB820", emit_s=2.5),
                     pupille=P("#2A0804"), joue=P("#FFB04A")),
        face=dict(brow=0.75, smile=0.5, look=(0.0, -0.1)),
        crown=crown_feu, particle=particle_feu, emblem=emblem_feu),
    "Eau": dict(
        label="Eau",
        palette=dict(corps=P("#2D7FD8"), corps2=P("#35CACA"), couture=P("#174A8A"), glyphe=P("#E8FBFF", 0.2),
                     epine=P("#E8FBFF"), fx=P("#3BB8F0", 0.05, transm=0.25), fx2=P("#C2F3FF", 0.05, transm=0.35),
                     pupille=P("#0A1A30"), joue=P("#86D9FF")),
        face=dict(brow=0.1, smile=1.0, look=(0.0, 0.05)),
        crown=crown_eau, particle=particle_eau, emblem=emblem_eau),
    "Plante": dict(
        label="Plante",
        palette=dict(corps=P("#56A63A"), corps2=P("#A6D65E"), couture=P("#2B6620"),
                     glyphe=P("#E8B53A", 0.25, 0.75, 0.3), epine=P("#FFF2CC"), fx=P("#FF7FB2"),
                     fx2=P("#3E9C33"), pupille=P("#1A240F"), joue=P("#FF9E9E")),
        face=dict(brow=0.35, smile=0.75, look=(0.1, -0.1)),
        crown=crown_plante, particle=particle_plante, emblem=emblem_plante),
    "Eclair": dict(
        label="Éclair",
        palette=dict(corps=P("#FFD52E"), corps2=P("#2E66FF"), couture=P("#1B3A99"),
                     glyphe=P("#2E66FF", 0.2, emit="#3A7BFF", emit_s=1.5), epine=P("#FFFFFF"),
                     fx=P("#62D2FF", 0.2, emit="#38B4FF", emit_s=2.5), fx2=P("#FFF6A0", 0.2, emit="#FFE040", emit_s=2.5),
                     pupille=P("#0A1440"), joue=P("#FFAE45")),
        face=dict(brow=0.5, smile=1.0, look=(-0.1, 0.0), pupil_scale=0.75),
        crown=crown_eclair, particle=particle_eclair, emblem=emblem_eclair),
}
ORDER = ["Lumiere", "Tenebres", "Glace", "Feu", "Eau", "Plante", "Eclair"]
