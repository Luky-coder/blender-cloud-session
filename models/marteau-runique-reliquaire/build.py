"""Marteau de Permafrost « Reliquaire runique », dérivé de la variante runique, en style Roblox low-poly : au
centre, une cage de bronze ouverte laisse voir le cœur d'énergie, un grand cristal aigue-marine suspendu entre
deux coupelles et ceint d'un anneau lumineux en orbite. De chaque côté, la glace est taillée en prismes
hexagonaux givrés de fougères de glace. Les embouts cornus portent une vitre de glace où brille un flocon, et
un médaillon runique pend à une chaîne (environ 2,6 m de haut)."""
import math

from mathutils import Vector

from kit import (Painter, aim, box, crack, crystal, frame, glyph, join, mat, prism, ring_slab, seeded, setup,
                 shade_faces, slab, wrap)

rng = seeded(58)
setup("MarteauRuniqueReliquaire")

# --------------------------------------------------------------------------- matériaux (aplats)
ice = mat("Glace aigue-marine", "#36C9CF")
ice_light = mat("Glace aigue-marine claire", "#9BF0EE")
ice_deep = mat("Glace aigue-marine profonde", "#14879B")
frost = mat("Givre", "#E8FFFD", rough=0.4)
crack_mat = mat("Fissure", "#0D5765")
bronze = mat("Bronze", "#C98A3E", rough=0.4, metal=0.45)
bronze_dark = mat("Bronze sombre", "#8A5526", rough=0.42, metal=0.45)
iron = mat("Fer sombre", "#353B45", rough=0.5, metal=0.3)
iron_dark = mat("Fer noir", "#22262E", rough=0.5, metal=0.3)
rune = mat("Rune lumineuse", "#5CFFE6", emit="#5CFFE6", strength=2.0)
core = mat("Cristal d'énergie", "#14D8CC", emit="#14D8CC", strength=0.9)
core_hot = mat("Cœur blanc", "#E6FFFD", emit="#C9FFF8", strength=2.5)
crystal_mat = mat("Cristal", "#A4F2F0", rough=0.3)
leather = mat("Cuir", "#5B3A26")
leather_dark = mat("Cuir sombre", "#3A2418")

# --------------------------------------------------------------------------- proportions (m)
ZC = 1.95                    # centre de la tête
CAGE_X = 0.2                 # demi-largeur de la cage centrale
HEX_A = 0.3                  # apothème des plaques hexagonales de la cage
HEX_R = HEX_A / math.cos(math.pi / 6)
X0, X_ICE = 0.23, 0.57       # glace de |x| = X0 à X_ICE
A_ICE = 0.24                 # apothème de la glace (demi-profondeur, faces avant/arrière plates)


def side_prism(name, m, s, a_in, a_out, x_in, x_out, chamfer=0.0, sides=6):
    """Prisme hexagonal couché le long de X (faces avant/arrière plates, arêtes en haut et en bas)."""
    rot = (0, s * math.pi / 2, 0)
    return prism(name, m, a_in, a_out, x_in, x_out, sides=sides, chamfer=chamfer, loc=(0, 0, ZC), rot=rot)


def shade(n):
    return 1 if n.z > 0.6 else 2 if n.z < -0.6 else 0


def hex_vertex(k, r):
    """Sommet k de l'hexagone (dans le plan YZ), k = 0 en haut."""
    a = math.pi / 2 + k * math.pi / 3
    return Vector((0, r * math.cos(a), ZC + r * math.sin(a)))


RUNES = {
    "isa": [[(0, -0.5), (0, 0.5)]],
    "hagalaz": [[(-0.28, -0.5), (-0.28, 0.5)], [(0.28, -0.5), (0.28, 0.5)], [(-0.28, 0.18), (0.28, -0.18)]],
    "naudiz": [[(0, -0.5), (0, 0.5)], [(-0.3, 0.2), (0.3, -0.12)]],
    "algiz": [[(0, -0.5), (0, 0.5)], [(0, 0.05), (-0.34, 0.45)], [(0, 0.05), (0.34, 0.45)]],
    "ingwaz": [[(0, 0.5), (0.3, 0), (0, -0.5), (-0.3, 0), (0, 0.5)]],
}


def snowflake(r):
    out = []
    for k in range(6):
        a = math.pi / 2 + k * math.pi / 3
        c, sn = math.cos(a), math.sin(a)

        def rot(x, y):
            return (x * c - y * sn, x * sn + y * c)

        out.append([rot(0.025, 0), rot(r, 0)])
        for t, ln in ((0.45, 0.3), (0.72, 0.2)):
            d = ln * r
            out.append([rot(t * r + d, d), rot(t * r, 0), rot(t * r + d, -d)])
    return out


def fern(x, z, angle, length, side_len, n=4):
    """Fougère de givre : une tige et des paires de ramures qui raccourcissent."""
    c, s = math.cos(angle), math.sin(angle)
    strokes = [[(x, z), (x + c * length, z + s * length)]]
    for i in range(1, n + 1):
        t = i / (n + 1)
        px, pz = x + c * length * t, z + s * length * t
        ln = side_len * (1 - 0.6 * t)
        for sgn in (-1, 1):
            a = angle + sgn * 0.85
            strokes.append([(px, pz), (px + math.cos(a) * ln, pz + math.sin(a) * ln)])
    return strokes


# --------------------------------------------------------------------------- cage centrale et cœur suspendu
for s, nm in ((-1, "gauche"), (1, "droite")):
    side_prism(f"Plaque de cage {nm}", bronze, s, HEX_A, HEX_A, CAGE_X - 0.02, CAGE_X + 0.035, chamfer=0.014)
    side_prism(f"Fond de cage {nm}", iron_dark, s, HEX_A - 0.05, HEX_A - 0.05, CAGE_X - 0.026, CAGE_X - 0.015)
bars = []
for k in range(6):
    p = hex_vertex(k, HEX_R - 0.03)
    bars.append(box(f"Barreau {k}", bronze_dark, (2 * CAGE_X, 0.04, 0.04), (0, p.y, p.z),
                    rot=(k * math.pi / 3 + math.pi / 4, 0, 0), chamfer=0.008))
join(bars, "Barreaux de cage")
# coupelles qui tiennent le cristal
prism("Coupelle basse", bronze, 0.05, 0.085, ZC - HEX_R + 0.02, ZC - 0.2, sides=6, chamfer=0.01)
prism("Coupelle haute", bronze, 0.085, 0.05, ZC + 0.2, ZC + HEX_R - 0.02, sides=6, chamfer=0.01)
join([crystal(f"Griffe coupelle {k}", bronze, 0.014, 0.06, 0.0, sides=4,
              loc=(0.075 * math.cos(a), 0.075 * math.sin(a), ZC + sz * 0.2),
              rot=aim((-0.4 * math.cos(a), -0.4 * math.sin(a), -sz)))
      for k, (a, sz) in enumerate([(i * math.pi / 3 + math.pi / 6, z) for i in range(6) for z in (-1, 1)])],
     "Griffes coupelles")
crystal("Cristal d'énergie", core, 0.11, 0.19, 0.19, loc=(0, 0, ZC), sides=6, mid=0.0, spin=0)
# anneau lumineux en orbite et éclats flottants
tilt = math.radians(22)
ring_fr = frame((0, 0, ZC), (math.cos(0.3), math.sin(0.3), 0), (-math.sin(0.3) * math.cos(tilt),
                                                                  math.cos(0.3) * math.cos(tilt), math.sin(tilt)))
ring_slab("Anneau d'orbite", rune, ring_fr, 0.165, 0.152, 0.01, base=-0.005, n=16)
for k in range(3):
    a = 0.6 + k * 2 * math.pi / 3
    o, u, v, n = ring_fr
    p = o + (u * math.cos(a) + v * math.sin(a)) * 0.159
    crystal(f"Éclat en orbite {k}", crystal_mat, 0.018, 0.035, 0.035, loc=p, rot=(0.3 * k, 0.5, 0.2 * k), sides=4)

# --------------------------------------------------------------------------- glace hexagonale et embouts
ice_parts, windows = [], []
for s, nm in ((-1, "gauche"), (1, "droite")):
    body = side_prism(f"Glace {nm}", ice, s, A_ICE, A_ICE, X0, X_ICE)
    shade_faces(body, [ice, ice_light, ice_deep], shade)
    ice_parts.append(body)
    # bague rivetée et barreaux de crête (dessus / dessous)
    side_prism(f"Bague {nm}", bronze, s, A_ICE + 0.018, A_ICE + 0.018, 0.395, 0.435, chamfer=0.008)
    join([box(f"Rivet {nm} {k}", bronze_dark, (0.024, 0.024, 0.024), (s * 0.415, sy * (A_ICE + 0.02), ZC),
              chamfer=0.006) for k, sy in enumerate((-1, 1))], f"Rivets {nm}")
    crest = []
    for k, sz in enumerate((1, -1)):
        r = A_ICE / math.cos(math.pi / 6)
        crest.append(box(f"Crête {nm} {k}", bronze_dark, (X_ICE - X0, 0.035, 0.035),
                         (s * (X0 + X_ICE) / 2, 0, ZC + sz * (r - 0.004)), rot=(math.pi / 4, 0, 0), chamfer=0.006))
    join(crest, f"Crêtes {nm}")

    # embout : bague, bloc de fer, cornes de bronze, vitre de glace au flocon
    side_prism(f"Bague embout {nm}", bronze, s, A_ICE + 0.03, A_ICE + 0.03, X_ICE - 0.015, X_ICE + 0.02,
               chamfer=0.007)
    side_prism(f"Embout {nm}", iron, s, A_ICE + 0.04, A_ICE + 0.032, X_ICE + 0.012, 0.665, chamfer=0.022)
    rr = (A_ICE + 0.04) / math.cos(math.pi / 6)
    join([crystal(f"Corne {nm} {k}", bronze, 0.03, 0.11, 0.02, sides=4, spin=math.pi / 4,
                  loc=(s * 0.62, 0, ZC + sz * (rr - 0.03)), rot=aim((s * 0.55, 0, sz)))
          for k, sz in enumerate((1, -1))], f"Cornes {nm}")
    side_prism(f"Cadre vitre {nm}", bronze, s, 0.2, 0.19, 0.655, 0.68, chamfer=0.006)
    windows.append(side_prism(f"Vitre de glace {nm}", ice_light, s, 0.165, 0.165, 0.66, 0.684))

    # stalactites
    for k, x in enumerate((0.3, 0.51)):
        crystal(f"Stalactite {nm} {k}", crystal_mat, 0.026, 0.025, rng.uniform(0.07, 0.1),
                loc=(s * x, rng.uniform(-0.04, 0.04), ZC - A_ICE / math.cos(math.pi / 6) + 0.02), spin=0)

# fougères de givre, reflets et fissures sur les faces avant / arrière
ice_painter = Painter(ice_parts)
for view in ("front", "back"):
    for s in (-1, 1):
        obs = []
        strokes = fern(s * 0.245, ZC - 0.17, math.pi / 2 - s * 0.5, 0.2, 0.06) + \
            fern(s * 0.545, ZC + 0.16, -math.pi / 2 - s * 0.6, 0.13, 0.04, n=3)
        obs.append(glyph(ice_painter, f"Fougère {view} {s}", frost, strokes, (0, 0), 1.0, view, 0.008))
        for x0, w in ((0.315, 0.022), (0.347, 0.01)):
            xa = s * x0
            poly = [(xa, ZC + 0.13), (xa + s * w, ZC + 0.13), (xa + s * (w + 0.05), ZC - 0.03), (xa + s * 0.05, ZC - 0.03)]
            obs.append(ice_painter.fill(f"Reflet {view} {s} {x0}", frost, poly if s > 0 else poly[::-1], view))
        ln = crack(rng, (s * 0.5, ZC - 0.1), rng.uniform(0, 6.28), 0.07, seg=0.02)
        obs.append(ice_painter.line(f"Fissure {view} {s}", crack_mat, ln, view, 0.008, taper=(1, 0.3)))
        join(obs, f"Dessins glace {view} {s}")

# flocons lumineux derrière les vitres
win_painter = Painter(windows, offset=0.003)
for view, nm in (("right", "droite"), ("left", "gauche")):
    flake = glyph(win_painter, f"Flocon {nm}", rune, snowflake(0.12), (0, ZC), 1.0, view, 0.012)
    hexa = [(0.028 * math.cos(a), ZC + 0.028 * math.sin(a)) for a in [k * math.pi / 3 for k in range(6)]]
    join([flake, win_painter.line(f"Flocon centre {nm}", rune, hexa, view, 0.01, closed=True)], f"Flocon {nm}")

# --------------------------------------------------------------------------- lanterne au sommet
TOP = ZC + HEX_R - 0.02
prism("Socle lanterne", bronze, 0.075, 0.06, TOP, TOP + 0.05, sides=6, chamfer=0.01)
crystal("Cristal lanterne", crystal_mat, 0.06, 0.2, 0.03, loc=(0, 0, TOP + 0.07), sides=6, mid=0.06, spin=0)
prism("Bague lanterne", bronze_dark, 0.07, 0.07, TOP + 0.09, TOP + 0.11, sides=6, chamfer=0.006)

# --------------------------------------------------------------------------- chaîne et médaillon runique
links = []
x_ch, z = 0.12, ZC - HEX_R + 0.01
for k in range(5):
    if k % 2 == 0:
        fr = frame((x_ch, -0.0, z - 0.02), (1, 0, 0), (0, 0, 1))
    else:
        fr = frame((x_ch, 0.0, z - 0.02), (0, 1, 0), (0, 0, 1))
    links.append(ring_slab(f"Maillon {k}", bronze_dark, fr, 0.016, 0.009, 0.007, base=-0.0035, n=6, rot=math.pi / 2))
    z -= 0.03
join(links, "Chaîne")
med_fr = frame((x_ch, -0.008, z - 0.03), (1, 0, 0), (0, 0, 1))
medal = slab("Médaillon", bronze, [(0.042 * math.cos(a), 0.042 * math.sin(a)) for a in
                                   [math.pi / 2 + k * math.pi / 3 for k in range(6)]], med_fr, -0.016)
med_p = Painter([medal], offset=0.002)
join([glyph(med_p, f"Rune médaillon {v}", rune, RUNES["ingwaz"], (x_ch * (1 if v == "front" else -1), z - 0.03),
            0.05, v, 0.007) for v in ("front", "back")], "Rune médaillon")

# --------------------------------------------------------------------------- manche hexagonal
SOCK = ZC - HEX_R + 0.01
prism("Douille", bronze, 0.06, 0.085, SOCK - 0.08, SOCK + 0.01, sides=6, chamfer=0.01)
prism("Bague douille", iron, 0.05, 0.05, SOCK - 0.13, SOCK - 0.075, sides=6, chamfer=0.008)
SHAFT_A = 0.036
shaft = prism("Hampe fer", iron_dark, SHAFT_A, SHAFT_A, 0.94, SOCK - 0.12, sides=6)
for k, z in enumerate((1.12, 1.36)):
    prism(f"Anneau hampe {k}", bronze, SHAFT_A + 0.009, SHAFT_A + 0.009, z - 0.013, z + 0.013, sides=6, chamfer=0.004)
shaft_painter = Painter([shaft])
for view in ("front", "back"):
    join([glyph(shaft_painter, f"Rune {rn} {view}", rune, RUNES[rn], (0, z), 0.075, view, 0.008)
          for rn, z in (("algiz", 1.04), ("hagalaz", 1.24), ("isa", 1.42))],
         f"Runes hampe {view}")

# collier du milieu
prism("Anneau collier bas", bronze, 0.05, 0.05, 0.84, 0.87, sides=6, chamfer=0.007)
prism("Collier", iron, 0.062, 0.062, 0.865, 0.935, sides=6, chamfer=0.015)
prism("Anneau collier haut", bronze, 0.05, 0.05, 0.93, 0.96, sides=6, chamfer=0.007)
join([crystal(f"Gemme collier {k}", rune, 0.014, 0.022, 0.022, sides=4, spin=0,
              loc=(0.064 * math.cos(a), 0.064 * math.sin(a), 0.9)) for k, a in
      enumerate([i * math.pi / 3 for i in range(6)])], "Gemmes collier")

# poignée : cuir brun, laçage de bronze croisé
GRIP_A, G0, G1 = 0.04, 0.27, 0.845
prism("Poignée cuir", leather, GRIP_A, GRIP_A, G0, G1, sides=6)
wrap("Laçage A", bronze, GRIP_A, G0 + 0.03, G1 - 0.03, 4, 0.01, thick=0.004, sides=6, phase=0.0, direction=1)
wrap("Laçage B", bronze, GRIP_A + 0.002, G0 + 0.03, G1 - 0.03, 4, 0.01, thick=0.004, sides=6, phase=math.pi,
     direction=-1)
for z, nm in ((G0 + 0.012, "bas"), (G1 - 0.012, "haut")):
    prism(f"Ligature {nm}", leather_dark, GRIP_A + 0.006, GRIP_A + 0.006, z - 0.014, z + 0.014, sides=6, chamfer=0.004)

# pommeau : couronne inversée de bronze autour d'une pointe de glace
prism("Bague pommeau", bronze, 0.05, 0.05, 0.235, 0.268, sides=6, chamfer=0.006)
prism("Pommeau", iron, 0.062, 0.05, 0.17, 0.24, sides=6, chamfer=0.014)
join([crystal(f"Dent pommeau {k}", bronze, 0.014, 0.05, 0.0, sides=4, spin=math.pi / 4,
              loc=(0.05 * math.cos(a), 0.05 * math.sin(a), 0.175), rot=aim((0.35 * math.cos(a), 0.35 * math.sin(a), -1)))
      for k, a in enumerate([i * math.pi / 3 for i in range(6)])], "Couronne pommeau")
crystal("Pointe basse", crystal_mat, 0.034, 0.04, 0.155, loc=(0, 0, 0.155), sides=6, spin=0)
