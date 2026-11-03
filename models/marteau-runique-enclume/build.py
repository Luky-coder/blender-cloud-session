"""Marteau de Permafrost « Enclume runique », dérivé de la variante runique, en style Roblox low-poly : au centre
un grand médaillon octogonal de fer cerclé d'or où un orbe d'énergie est entouré d'un anneau de huit runes
lumineuses ; de chaque côté la glace turquoise s'évase jusqu'à des embouts massifs cloutés d'or, frappés d'un
flocon. Couronne de cristaux, manche de fer incrusté d'une spirale d'or et pommeau-cage tenant un petit orbe
(environ 2,5 m de haut)."""
import math

from kit import (Painter, aim, box, crack, crystal, frame, glyph, join, loft, mat, prism, ring_slab, seeded,
                 setup, shade_faces, slab, star, wrap)

rng = seeded(31)
setup("MarteauRuniqueEnclume")

# --------------------------------------------------------------------------- matériaux (aplats)
ice = mat("Glace turquoise", "#38C2E2")
ice_light = mat("Glace turquoise claire", "#93E9FA")
ice_deep = mat("Glace turquoise profonde", "#1A79AE")
frost = mat("Givre reflet", "#E9FDFF", rough=0.4)
crack_mat = mat("Fissure", "#15557F")
iron = mat("Fer sombre", "#3B4454", rough=0.5, metal=0.3)
iron_dark = mat("Fer noir", "#252B36", rough=0.5, metal=0.3)
gold = mat("Or", "#E2AE45", rough=0.38, metal=0.45)
gold_dark = mat("Or sombre", "#A9772A", rough=0.4, metal=0.45)
rune = mat("Rune lumineuse", "#4FEAFF", emit="#4FEAFF", strength=2.2)
core_glow = mat("Cœur énergie", "#22C8FF", emit="#22C8FF", strength=2.2)
orb_mat = mat("Orbe", "#2ECFFF", emit="#2ECFFF", strength=1.6)
core_hot = mat("Cœur blanc", "#E6FDFF", emit="#C9F8FF", strength=2.5)
crystal_mat = mat("Cristal", "#9FEAFF", rough=0.3)
leather = mat("Cuir bleu nuit", "#2C3F6E")
leather_dark = mat("Cuir bleu sombre", "#1B2645")

# --------------------------------------------------------------------------- proportions (m)
ZC = 1.9                     # centre de la tête
DR, DY = 0.29, 0.23          # médaillon central : apothème (dans le plan XZ) et demi-épaisseur (Y)
X0, X_ICE = 0.22, 0.56       # glace de |x| = X0 à X_ICE
A_IN, A_OUT = 0.17, 0.245    # apothème de la glace côté médaillon / côté embout


def shade(n):
    return 1 if n.z > 0.6 else 2 if n.z < -0.6 else 0


def side_prism(name, m, s, a_in, a_out, x_in, x_out, chamfer=0.0):
    """Prisme octogonal couché le long de X, du côté s (±1), de |x| = x_in (apothème a_in) à x_out."""
    return prism(name, m, a_in, a_out, x_in, x_out, chamfer=chamfer, loc=(0, 0, ZC), rot=(0, s * math.pi / 2, 0))


def ice_a(x):
    """Apothème de la glace évasée à la distance |x|."""
    return A_IN + (A_OUT - A_IN) * (x - X0) / (X_ICE - X0)


RUNES = {
    "isa": [[(0, -0.5), (0, 0.5)]],
    "hagalaz": [[(-0.28, -0.5), (-0.28, 0.5)], [(0.28, -0.5), (0.28, 0.5)], [(-0.28, 0.18), (0.28, -0.18)]],
    "naudiz": [[(0, -0.5), (0, 0.5)], [(-0.3, 0.2), (0.3, -0.12)]],
    "algiz": [[(0, -0.5), (0, 0.5)], [(0, 0.05), (-0.34, 0.45)], [(0, 0.05), (0.34, 0.45)]],
    "kaun": [[(0.25, 0.5), (-0.22, 0.0), (0.25, -0.5)]],
    "tiwaz": [[(0, -0.5), (0, 0.5)], [(-0.3, 0.2), (0, 0.5), (0.3, 0.2)]],
    "sowilo": [[(0.22, 0.5), (-0.2, 0.12), (0.2, -0.12), (-0.22, -0.5)]],
    "ingwaz": [[(0, 0.5), (0.3, 0), (0, -0.5), (-0.3, 0), (0, 0.5)]],
}


def snowflake(r):
    """Flocon à 6 branches, chacune avec deux chevrons."""
    out = []
    for k in range(6):
        a = math.pi / 2 + k * math.pi / 3
        c, sn = math.cos(a), math.sin(a)

        def rot(x, y):
            return (x * c - y * sn, x * sn + y * c)

        out.append([rot(0.03, 0), rot(r, 0)])
        for t, ln in ((0.45, 0.3), (0.72, 0.2)):
            d = ln * r
            out.append([rot(t * r + d, d), rot(t * r, 0), rot(t * r + d, -d)])
    return out


# --------------------------------------------------------------------------- médaillon central
drum = prism("Médaillon", iron, DR, DR, -DY, DY, chamfer=0.03, loc=(0, 0, ZC), rot=(math.pi / 2, 0, 0))
prism("Tranche dorée", gold, DR + 0.012, DR + 0.012, -0.035, 0.035, chamfer=0.01, loc=(0, 0, ZC),
      rot=(math.pi / 2, 0, 0))
drum_painter = Painter([drum])
for face, sy, fr in (("avant", -1, frame((0, -DY, ZC), (1, 0, 0), (0, 0, 1))),
                     ("arrière", 1, frame((0, DY, ZC), (-1, 0, 0), (0, 0, 1)))):
    view = "front" if sy < 0 else "back"
    ring_slab(f"Anneau or {face}", gold, fr, 0.272, 0.238, 0.014, base=-0.002)
    join([box(f"Rivet médaillon {face} {k}", gold_dark, (0.026, 0.026, 0.026),
              (0.255 / math.cos(math.pi / 8) * math.cos(math.pi / 8 + k * math.pi / 4) * (1 if sy < 0 else -1),
               sy * (DY + 0.014), ZC + 0.255 / math.cos(math.pi / 8) * math.sin(math.pi / 8 + k * math.pi / 4)),
              rot=(0, k * math.pi / 4 + math.pi / 8, 0), chamfer=0.007) for k in range(8)], f"Rivets médaillon {face}")
    # anneau de huit runes autour du cœur
    names = ["isa", "kaun", "hagalaz", "tiwaz", "naudiz", "sowilo", "algiz", "ingwaz"]
    obs = []
    for k, rn in enumerate(names):
        a = math.pi / 2 + k * math.pi / 4
        obs.append(glyph(drum_painter, f"Rune {face} {k}", rune, RUNES[rn],
                         (0.185 * math.cos(a), ZC + 0.185 * math.sin(a)), 0.062, view, 0.009, rot=a - math.pi / 2))
    join(obs, f"Anneau de runes {face}")
    # lunette, fond, disque d'énergie, orbe et griffes
    ring_slab(f"Lunette {face}", gold, fr, 0.135, 0.108, 0.03, base=-0.004)
    slab(f"Fond lunette {face}", iron_dark, [(0.11 * math.cos(math.pi / 8 + k * math.pi / 4) / math.cos(math.pi / 8),
                                              0.11 * math.sin(math.pi / 8 + k * math.pi / 4) / math.cos(math.pi / 8))
                                             for k in range(8)], fr, 0.012)
    slab(f"Disque énergie {face}", core_glow, star(0, 0, [0.095] * 8, 0.07, math.pi / 8), fr, 0.006, base=0.012)
    o, u, v, n = fr
    crystal(f"Orbe {face}", orb_mat, 0.065, 0.06, 0.03, loc=o + n * 0.03, rot=aim(n), sides=8)
    crystal(f"Orbe éclat {face}", core_hot, 0.03, 0.035, 0.0, loc=o + n * 0.075, rot=aim(n), sides=8)
    join([crystal(f"Griffe {face} {k}", gold, 0.016, 0.055, 0.0, sides=4,
                  loc=o + n * 0.025 + (u * math.cos(a) + v * math.sin(a)) * 0.115,
                  rot=aim(-(u * math.cos(a) + v * math.sin(a)) + n * 0.4))
          for k, a in enumerate([math.pi / 4 + i * math.pi / 2 for i in range(4)])], f"Griffes {face}")

# --------------------------------------------------------------------------- glace évasée et embouts cloutés
ice_parts, plates = [], []
for s, nm in ((-1, "gauche"), (1, "droite")):
    body = side_prism(f"Glace {nm}", ice, s, A_IN, A_OUT, X0, X_ICE)
    shade_faces(body, [ice, ice_light, ice_deep], shade)
    ice_parts.append(body)
    side_prism(f"Bride {nm}", gold, s, 0.2, 0.2, 0.235, 0.292, chamfer=0.01)

    # bague rivetée au milieu de la glace
    xm = 0.42
    side_prism(f"Bague {nm}", iron, s, ice_a(xm) + 0.016, ice_a(xm) + 0.016, xm - 0.025, xm + 0.025, chamfer=0.008)
    r = ice_a(xm) + 0.02
    join([box(f"Rivet {nm} {k}", gold, (0.024, 0.024, 0.024), (s * xm, dy * r, ZC + dz * r), chamfer=0.006)
          for k, (dy, dz) in enumerate(((-1, 0), (1, 0), (0, 1), (0, -1)))], f"Rivets {nm}")

    # embout massif : cerclage, bloc, clous dorés tout autour, plaque de frappe
    side_prism(f"Cerclage embout {nm}", gold, s, 0.262, 0.262, X_ICE - 0.02, X_ICE + 0.012, chamfer=0.006)
    side_prism(f"Embout {nm}", iron, s, 0.285, 0.29, X_ICE + 0.006, 0.645, chamfer=0.026)
    studs = []
    for k in range(8):
        a = k * math.pi / 4
        d = (0, math.cos(a), math.sin(a))
        studs.append(crystal(f"Clou {nm} {k}", gold, 0.024, 0.045, 0.0, sides=4, spin=math.pi / 4,
                             loc=(s * 0.603, 0.283 * d[1], ZC + 0.283 * d[2]), rot=aim(d)))
    join(studs, f"Clous {nm}")
    plates.append(side_prism(f"Plaque de frappe {nm}", iron_dark, s, 0.215, 0.2, 0.64, 0.67, chamfer=0.008))

    # stalactites sous la glace
    for k, x in enumerate((0.33, 0.5)):
        crystal(f"Stalactite {nm} {k}", crystal_mat, 0.03, 0.03, rng.uniform(0.07, 0.11),
                loc=(s * x, rng.uniform(-0.05, 0.05), ZC - ice_a(x) + 0.01), spin=0)

# reflets, éclats et fissures sur la glace
ice_painter = Painter(ice_parts)
for view in ("front", "back"):
    for s in (-1, 1):
        obs = []
        for x0, w, top in ((0.3, 0.024, 0.09), (0.335, 0.011, 0.09), (0.465, 0.022, 0.12), (0.5, 0.01, 0.12)):
            xa = s * x0
            poly = [(xa, ZC + top), (xa + s * w, ZC + top), (xa + s * (w + 0.05), ZC - 0.06), (xa + s * 0.05, ZC - 0.06)]
            obs.append(ice_painter.fill(f"Reflet {view} {s} {x0}", frost, poly if s > 0 else poly[::-1], view))
        obs.append(ice_painter.fill(f"Éclat {view} {s}", frost,
                                    star(s * 0.37, ZC + 0.12, [0.03, 0.017] * 2, 0.006), view, cuts=1))
        st = (s * rng.uniform(0.3, 0.37), ZC - 0.08)
        ln = crack(rng, st, rng.uniform(0, 2 * math.pi), 0.08, seg=0.022)
        obs.append(ice_painter.line(f"Fissure {view} {s}", crack_mat, ln, view, 0.008, taper=(1, 0.3)))
        join(obs, f"Dessins glace {view} {s}")

# flocon lumineux cerclé sur les plaques de frappe
cap_painter = Painter(plates)
for view, nm in (("right", "droite"), ("left", "gauche")):
    parts = [glyph(cap_painter, f"Flocon {nm}", rune, snowflake(0.125), (0, ZC), 1.0, view, 0.013)]
    hexa = [(0.03 * math.cos(a), ZC + 0.03 * math.sin(a)) for a in [k * math.pi / 3 for k in range(6)]]
    parts.append(cap_painter.line(f"Flocon centre {nm}", rune, hexa, view, 0.011, closed=True))
    octo = [(0.17 / math.cos(math.pi / 8) * math.cos(math.pi / 8 + k * math.pi / 4),
             ZC + 0.17 / math.cos(math.pi / 8) * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]
    parts.append(cap_painter.line(f"Cercle runique {nm}", rune, octo, view, 0.009, closed=True))
    join(parts, f"Sceau de givre {nm}")

# --------------------------------------------------------------------------- couronne
TOP = ZC + DR
prism("Socle couronne", gold, 0.105, 0.085, TOP - 0.02, TOP + 0.04, chamfer=0.012)
crystal("Cristal couronne", crystal_mat, 0.07, 0.24, 0.04, loc=(0, 0, TOP + 0.05), mid=0.05, spin=0)
for s in (-1, 1):
    crystal(f"Cristal couronne {'gauche' if s < 0 else 'droit'}", crystal_mat, 0.042, 0.13, 0.04,
            loc=(s * 0.08, 0, TOP + 0.03), rot=(0, s * 0.5, 0), mid=0.02, spin=0)
join([crystal(f"Pointe or {k}", gold, 0.018, 0.07, 0.0, sides=4,
              loc=(0.075 * math.cos(a), 0.075 * math.sin(a), TOP + 0.035),
              rot=aim((math.cos(a) * 0.45, math.sin(a) * 0.45, 1)))
      for k, a in enumerate([math.pi / 2, -math.pi / 2, math.pi / 4 + math.pi / 2, -math.pi / 4 - math.pi / 2,
                             math.pi / 4, -math.pi / 4])], "Pointes de couronne")

# --------------------------------------------------------------------------- manche
SOCK = ZC - DR
prism("Douille or", gold, 0.07, 0.088, SOCK - 0.05, SOCK + 0.01, chamfer=0.01)
prism("Douille", iron, 0.045, 0.06, SOCK - 0.12, SOCK - 0.045, chamfer=0.008)
prism("Bague douille", gold_dark, 0.05, 0.05, SOCK - 0.14, SOCK - 0.115, chamfer=0.006)
SHAFT_A = 0.036
prism("Hampe fer", iron_dark, SHAFT_A, SHAFT_A, 0.94, SOCK - 0.12)
for k, z in enumerate((1.0, 1.45)):
    prism(f"Anneau hampe {k}", gold, SHAFT_A + 0.009, SHAFT_A + 0.009, z - 0.013, z + 0.013, chamfer=0.004)
wrap("Spirale d'or", gold, SHAFT_A, 1.02, 1.43, 2.5, 0.013, thick=0.003, phase=0.0, direction=1)
wrap("Spirale de givre", rune, SHAFT_A, 1.02, 1.43, 2.5, 0.006, thick=0.002, phase=math.pi, direction=1)

# collier du milieu
prism("Anneau collier bas", gold, 0.05, 0.05, 0.84, 0.87, chamfer=0.007)
prism("Collier", iron, 0.06, 0.06, 0.865, 0.935, chamfer=0.014)
prism("Anneau collier haut", gold, 0.05, 0.05, 0.93, 0.96, chamfer=0.007)
join([crystal(f"Gemme collier {k}", rune, 0.014, 0.022, 0.022, sides=4, spin=0,
              loc=(0.062 * math.cos(a), 0.062 * math.sin(a), 0.9)) for k, a in
      enumerate([i * math.pi / 2 for i in range(4)])], "Gemmes collier")

# poignée : cuir bleu nuit, laçage d'or croisé
GRIP_A, G0, G1 = 0.04, 0.27, 0.845
prism("Poignée cuir", leather, GRIP_A, GRIP_A, G0, G1)
wrap("Laçage or A", gold, GRIP_A, G0 + 0.03, G1 - 0.03, 4, 0.011, thick=0.004, phase=0.0, direction=1)
wrap("Laçage or B", gold, GRIP_A + 0.002, G0 + 0.03, G1 - 0.03, 4, 0.011, thick=0.004, phase=math.pi, direction=-1)
for z, nm in ((G0 + 0.012, "bas"), (G1 - 0.012, "haut")):
    prism(f"Ligature {nm}", leather_dark, GRIP_A + 0.006, GRIP_A + 0.006, z - 0.014, z + 0.014, chamfer=0.004)

# pommeau-cage : quatre griffes d'or autour d'un petit orbe, puis pointe de cristal
prism("Bague pommeau", gold, 0.05, 0.05, 0.24, 0.272, chamfer=0.006)
prism("Chapeau pommeau", iron, 0.06, 0.06, 0.2, 0.245, chamfer=0.014)
join([loft(f"Griffe pommeau {k}", gold, [(0.052 * math.cos(a), 0.052 * math.sin(a), 0.205),
                                          (0.05 * math.cos(a), 0.05 * math.sin(a), 0.15),
                                          (0.03 * math.cos(a), 0.03 * math.sin(a), 0.105)],
            [0.014, 0.012, 0.01], sides=4, spin=math.pi / 4)
      for k, a in enumerate([math.pi / 4 + i * math.pi / 2 for i in range(4)])], "Griffes pommeau")
crystal("Orbe pommeau", orb_mat, 0.036, 0.04, 0.04, loc=(0, 0, 0.155), sides=8)
prism("Culot pommeau", gold, 0.028, 0.04, 0.09, 0.115, chamfer=0.005)
crystal("Pointe basse", crystal_mat, 0.032, 0.03, 0.095, loc=(0, 0, 0.095), sides=6, mid=0.0, spin=0)
