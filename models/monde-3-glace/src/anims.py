"""Animations physiques des mobs gonflables (IDLE, MOVE, ATTACK, HIT, DEATH).

Chaque animation est une fonction pose(t) -> Pose, échantillonnée image par image par
w3lib.bake_action. La structure commune (flottement, inclinaison, compression, dégonflage) est
ici ; chaque famille ajoute ses propres mouvements via `extra(nom_action, t, pose)` et choisit
son style d'attaque (charge frontale, toupie + projection, charge horizontale).

Os attendus : Root, Body, CTRL_Formes ; optionnels : Haut, Avant, Arriere, Visage, Bouche, Deco.
Vitesse : 30 images/s.
"""
import math

from w3lib import Pose, TAU, decay, ease, osc, track, track3

FPS = 30
LENGTHS = {"IDLE": 61, "MOVE": 41, "FLY": 61, "ATTACK": 37, "HIT": 19, "DEATH": 61}
LOOPS = {"IDLE": True, "MOVE": True, "FLY": True, "ATTACK": False, "HIT": False, "DEATH": False}


def _has(spec, b):
    return b in spec["bones"]


def idle(spec, t):
    L, hov = spec["L"], spec["hover"]
    P = 60.0
    p = Pose()
    p.set("Root", loc=(0, 0, hov * 0.5 * (1 - math.cos(TAU * t / P))))
    p.set("Body", rot=(2.2 * osc(t, P, 0.9), 1.6 * osc(t, P, 2.1), 1.2 * osc(t, P, 0.3)))
    s = 0.02 * osc(t, P, 0.0, 2)
    p.set("Body", scl=(1 + s, 1 + s, 1 - 1.3 * s))
    if _has(spec, "Haut"):
        p.set("Haut", loc=(0.012 * L * osc(t, P, 1.4), 0.008 * L * osc(t, P, 2.4), 0),
              scl=(1 - 0.025 * osc(t, P, 0.9, 2), 1 - 0.025 * osc(t, P, 0.9, 2), 1 + 0.04 * osc(t, P, 0.9, 2)))
    if _has(spec, "Avant"):
        p.set("Avant", scl=(1 + 0.02 * osc(t, P, 2.0, 2), 1 - 0.015 * osc(t, P, 2.0, 2), 1 + 0.02 * osc(t, P, 2.0, 2)))
    if _has(spec, "Arriere"):
        p.set("Arriere", scl=(1 + 0.02 * osc(t, P, 3.0, 2),) * 3)
    if _has(spec, "Deco"):
        p.set("Deco", loc=(0, 0, 0.012 * L * osc(t, P, 1.8, 2)), rot=(4 * osc(t, P, 0.5), 4 * osc(t, P, 1.5), 0))
    if _has(spec, "Visage"):
        # clignement au milieu de la boucle
        blink = 1 - 0.85 * math.exp(-((t - 38) / 1.6) ** 2)
        p.set("Visage", scl=(1, 1, blink))
    p.shapes(resp=0.45 * osc(t, P, 0.3, 2))
    return p


def move(spec, t):
    L, hov = spec["L"], spec["hover"]
    P = 40.0
    p = Pose()
    p.set("Root", loc=(0, 0, hov * 0.6 * (1 - math.cos(TAU * 2 * t / P))))
    lean = spec.get("lean", 11)
    p.set("Body", rot=(-lean + 2.5 * osc(t, P, 0.6, 2), 3.5 * osc(t, P, 0.0), 2.0 * osc(t, P, 1.0)))
    st = 0.035 * osc(t, P, 1.2, 2)
    p.set("Body", scl=(0.96 - 0.5 * st, 1.08 + st, 0.95 - 0.5 * st))
    if _has(spec, "Haut"):
        p.set("Haut", loc=(0.01 * L * osc(t, P, 0.4), -0.035 * L + 0.012 * L * osc(t, P, 1.9, 2), 0),
              scl=(1, 1, 1 + 0.03 * osc(t, P, 0.5, 2)))
    if _has(spec, "Avant"):
        p.set("Avant", loc=(0, -0.02 * L, 0), scl=(1.04, 0.94, 1.03))
    if _has(spec, "Arriere"):
        p.set("Arriere", loc=(0, -0.03 * L + 0.01 * L * osc(t, P, 2.6, 2), 0), scl=(0.96, 1.06, 0.97))
    if _has(spec, "Deco"):
        p.set("Deco", loc=(0, -0.02 * L, 0), rot=(9 + 4 * osc(t, P, 0.5, 2), 4 * osc(t, P, 1.5), 0))
    p.shapes(resp=0.2, impact=0.15 + 0.05 * osc(t, P, 0.0, 2))
    return p


def fly(spec, t):
    """VOL (boucle de 2 s) : prend de l'altitude, plane en virages en S (roulis + lacet), nez incliné,
    corps étiré par la vitesse. L'altitude ajoutée vaut spec['fly_alt'] × taille."""
    L = spec["L"]
    P = 60.0
    p = Pose()
    alt = spec.get("fly_alt", 0.35) * L
    p.set("Root", loc=(0.06 * L * osc(t, P, 0.0), 0, alt + 0.07 * L * osc(t, P, 0.4, 2)))
    p.set("Body", rot=(-9 + 3 * osc(t, P, 1.0, 2), 13 * osc(t, P, 0.0), 7 * osc(t, P, math.pi / 2)))
    st = 0.03 * osc(t, P, 0.5, 2)
    p.set("Body", scl=(0.95 - 0.5 * st, 1.1 + st, 0.95 - 0.5 * st))
    if _has(spec, "Haut"):
        p.set("Haut", loc=(-0.02 * L * osc(t, P, 0.4), -0.04 * L, 0), scl=(1, 1, 1 + 0.03 * osc(t, P, 0.5, 2)))
    if _has(spec, "Avant"):
        p.set("Avant", loc=(0, -0.025 * L, 0), scl=(1.05, 0.92, 1.04))
    if _has(spec, "Arriere"):
        p.set("Arriere", loc=(0.015 * L * osc(t, P, 1.2), -0.04 * L, 0), scl=(0.95, 1.08, 0.96))
    if _has(spec, "Deco"):
        p.set("Deco", loc=(0, -0.03 * L, 0), rot=(14 + 5 * osc(t, P, 0.5, 2), 6 * osc(t, P, 1.5), 0))
    p.shapes(resp=0.25, impact=0.2 + 0.05 * osc(t, P, 0.0, 2))
    return p


def attack_charge(spec, t, reach=0.8, back=0.22, tilt=1.0, hop=0.12):
    """Charge frontale : recul + compression, projection, impact, rebond, retour."""
    L = spec["L"]
    p = Pose()
    y = track(t, [(0, 0), (9, -back * L, "ease"), (14, reach * L, "in"), (18, (reach - 0.06) * L),
                  (24, (reach - 0.32) * L), (36, 0, "ease")])
    z = track(t, [(0, 0), (9, 0), (14, 0.04 * L), (18, 0.02 * L), (22, hop * L), (28, 0.02 * L), (36, 0)])
    p.set("Root", loc=(0, y, z))
    p.set("Body", rot=(track(t, [(0, 0), (9, 15 * tilt), (13, -20 * tilt), (17, -3 * tilt), (23, 7 * tilt),
                                 (30, -2 * tilt), (36, 0)]),
                       decay(t, 16, 14, 2.5, 5), 0))
    p.set("Body", scl=track3(t, [(0, (1, 1, 1)), (9, (1.09, 0.82, 0.93)), (13, (0.9, 1.24, 0.92)),
                                 (17, (1.17, 0.7, 1.13)), (22, (0.95, 1.1, 0.98)), (28, (1.02, 0.97, 1.01)),
                                 (36, (1, 1, 1))]))
    if _has(spec, "Haut"):
        p.set("Haut", loc=(0, track(t, [(0, 0), (9, 0.03 * L), (13, -0.06 * L), (18, 0.07 * L), (24, -0.02 * L),
                                        (36, 0)]), 0))
    if _has(spec, "Arriere"):
        p.set("Arriere", loc=(0, track(t, [(0, 0), (9, 0.02 * L), (13, -0.07 * L), (18, 0.05 * L), (36, 0)]), 0))
    if _has(spec, "Avant"):
        p.set("Avant", loc=(0, track(t, [(0, 0), (14, 0), (17, -0.06 * L), (22, 0.01 * L), (36, 0)]), 0),
              scl=track3(t, [(0, (1, 1, 1)), (14, (1, 1, 1)), (17, (1.12, 0.8, 1.1)), (22, (1, 1, 1))]))
    if _has(spec, "Visage"):
        sq = track(t, [(0, 1), (8, 0.7), (13, 1.15), (17, 0.6), (24, 1), (36, 1)])
        p.set("Visage", scl=(1, 1, sq))
    if _has(spec, "Bouche"):
        p.set("Bouche", scl=track3(t, [(0, (1, 1, 1)), (9, (0.95, 1, 0.9)), (13, (1.12, 1, 1.2)),
                                       (18, (1.08, 1, 1.1)), (26, (1, 1, 1))]))
    if _has(spec, "Deco"):
        p.set("Deco", loc=(0, track(t, [(0, 0), (9, 0.03 * L), (13, -0.05 * L), (18, 0.05 * L), (26, 0)]), 0),
              rot=(track(t, [(0, 0), (9, -10), (13, 18), (18, -12), (25, 4), (36, 0)]), 0, 0))
    p.shapes(resp=track(t, [(0, 0), (9, 0.6), (14, -0.2), (20, 0), (36, 0)]),
             impact=track(t, [(0, 0), (14, 0), (17, 1.0), (22, 0.15), (28, 0), (36, 0)]))
    return p


def hit(spec, t):
    L = spec["L"]
    p = Pose()
    p.set("Root", loc=(decay(t, 2, 14, 3.5, 0.03 * L),
                       track(t, [(0, 0), (3, -0.14 * L, "out"), (10, -0.09 * L), (18, 0, "ease")]),
                       track(t, [(0, 0), (3, 0.03 * L), (9, 0.01 * L), (18, 0)])))
    p.set("Body", rot=(track(t, [(0, 0), (3, 13), (7, -5), (11, 3), (18, 0)]),
                       decay(t, 2, 14, 3, 8), decay(t, 2, 14, 2.5, 5)))
    s = track3(t, [(0, (1, 1, 1)), (2, (1.13, 0.8, 0.85)), (5, (0.93, 1.07, 1.1)), (8, (1.05, 0.97, 0.96)),
                   (12, (0.99, 1.01, 1.01)), (18, (1, 1, 1))])
    v = decay(t, 2, 14, 4, 0.035)
    p.set("Body", scl=(s[0] + v, s[1] - v, s[2] + v))
    if _has(spec, "Haut"):
        p.set("Haut", loc=(decay(t, 2, 14, 3, 0.03 * L), decay(t, 3, 14, 2.5, 0.04 * L), 0))
    if _has(spec, "Avant"):
        p.set("Avant", scl=track3(t, [(0, (1, 1, 1)), (2, (1.1, 0.8, 1.08)), (7, (1, 1, 1))]))
    if _has(spec, "Visage"):
        p.set("Visage", scl=(1.05, 1, track(t, [(0, 1), (2, 0.35), (9, 0.4), (14, 1), (18, 1)])))
    if _has(spec, "Deco"):
        p.set("Deco", rot=(decay(t, 2, 16, 3, 14), decay(t, 3, 16, 2.5, 10), 0))
    p.shapes(resp=track(t, [(0, 0), (2, -0.6), (8, 0.2), (14, 0)]),
             impact=track(t, [(0, 0), (2, 0.85), (8, 0), (18, 0)]))
    return p


def death(spec, t):
    """0-6 sursaut · 6-30 l'air s'échappe (toupie, envol) · 30-48 affaissement au sol ·
    48-60 ratatinement puis disparition."""
    L, hb = spec["L"], spec["body_h"]
    p = Pose()
    fade = 1 - ease((t - 30) / 14)
    on = 1.0 if t > 6 else 0.0
    ax = 0.16 * L * math.sin(TAU * max(t - 6, 0) / 17) * on * fade
    ay = 0.1 * L * math.sin(TAU * max(t - 6, 0) / 11) * on * fade
    z = track(t, [(0, 0), (3, 0.04 * L), (8, 0.02 * L), (18, 0.32 * L), (30, 0.22 * L), (46, 0, "ease"),
                  (60, 0)])
    p.set("Root", loc=(ax, ay + track(t, [(0, 0), (3, -0.12 * L, "out"), (8, -0.08 * L), (60, -0.05 * L)]), z))
    wob = 11 * math.sin(TAU * t / 7) * on * fade
    p.set("Body", rot=(track(t, [(0, 0), (3, 12), (8, 0), (44, 0), (52, 7), (60, 7)]) + wob,
                       0.8 * wob, track(t, [(0, 0), (6, 0), (44, 300, "ease"), (60, 320)])))
    sxy = track(t, [(0, 1), (3, 1.12), (6, 1.0), (30, 0.86, "ease"), (48, 0.66, "ease"), (53, 0.6),
                    (60, 0.0, "in")])
    sz = track(t, [(0, 1), (3, 0.82), (6, 1.0), (30, 0.85, "ease"), (48, 0.58, "ease"), (53, 0.45),
                   (60, 0.0, "in")])
    j = 0.05 * math.sin(TAU * t / 5) * (6 < t < 46)
    sx, sy, sz = sxy * (1 + j), sxy * (1 - j), sz * (1 + 0.5 * j)
    p.set("Body", scl=(max(sx, 0.001), max(sy, 0.001), max(sz, 0.001)))
    # garde le bas du modèle au contact du sol pendant l'affaissement
    p.add("Body", loc=(0, 0, -hb * (1 - max(sz, 0.001)) * ease((t - 30) / 16)))
    if _has(spec, "Haut"):
        k = ease((t - 28) / 22)
        p.set("Haut", loc=(0.03 * L * math.sin(TAU * t / 6) * on * fade, 0, -0.08 * L * k),
              scl=(1 + 0.15 * k, 1 + 0.15 * k, 1 - 0.3 * k))
    if _has(spec, "Visage"):
        p.set("Visage", scl=(1, 1, track(t, [(0, 1), (3, 0.3), (10, 0.9), (30, 0.6), (46, 0.15), (60, 0.15)])))
    if _has(spec, "Deco"):
        p.set("Deco", rot=(track(t, [(0, 0), (30, 15), (48, 45), (60, 50)]), wob, 0),
              loc=(0, 0, -0.05 * L * ease((t - 30) / 18)))
    p.shapes(resp=track(t, [(0, 0), (3, -0.4), (8, 0), (30, -0.5), (48, -1.0)]),
             impact=track(t, [(0, 0), (3, 0.7), (9, 0)]),
             deflate=track(t, [(0, 0), (8, 0), (30, 0.3, "ease"), (48, 1.0, "ease"), (60, 1.0)]))
    return p


def string_motion(name, t, p):
    """Ficelle pendante (chaîne verticale) : rot X = balancier avant/arrière (négatif = traîne
    vers l'arrière), rot Y = balancier latéral."""
    for i in range(3):
        b = f"Ficelle_{i + 1}"
        lag = 0.9 * i
        if name == "IDLE":
            p.set(b, rot=(4 * osc(t, 60, lag + 0.5), 6 * osc(t, 60, lag), 0))
        elif name == "MOVE":
            p.set(b, rot=((-12 if i == 0 else -5) + 4 * osc(t, 40, lag, 2), 7 * osc(t, 40, lag), 0))
        elif name == "FLY":
            p.set(b, rot=((-22 if i == 0 else -8) + 5 * osc(t, 60, lag, 2), 12 * osc(t, 60, lag + 0.6), 0))
        elif name == "ATTACK":
            p.set(b, rot=(track(t - 1.5 * i, [(0, 0), (9, 12), (14, -30), (19, 22), (26, -10), (32, 4), (36, 0)]),
                          decay(t, 16 + 2 * i, 18, 2.5, 10), 0))
        elif name == "HIT":
            p.set(b, rot=(decay(t, 2 + i, 16, 3, 18), decay(t, 2 + i, 16, 2.5, 12), 0))
        elif name == "DEATH":
            on = 1.0 if 6 < t < 46 else 0.0
            p.set(b, rot=(25 * on * math.sin(TAU * t / 9 + lag), 30 * on * math.sin(TAU * t / 7 + lag), 0))


# --------------------------------------------------------------------------------------------
# Yeux : ouverture (Oeil_G/D), regard (Pupille_G/D), sourcils (Sourcil_G/D)
# --------------------------------------------------------------------------------------------
def _blink(t, at, w=1.4):
    return 1 - 0.92 * math.exp(-((t - at) / w) ** 2)


def eye_motion(name, t, p, n, r):
    """Superpose le jeu des yeux à une pose. `n` = nombre d'images de l'action, `r` = rayon des yeux.
    Regard : rot Z > 0 = vers la gauche du modèle (-X), rot X > 0 = vers le haut.
    Sourcils : loc Z = hausse, rot Y = inclinaison (fâché = côté intérieur abaissé)."""
    T = n - 1
    u = t / T if T else 0.0

    def k(keys):   # clés en fraction de durée -> images
        return track(t, [(a * T, *rest) for a, *rest in keys])

    p.set("Visage", scl=(1, 1, 1))
    lr = ud = 0.0
    opn = wide = pup = 1.0
    angry = raise_ = 0.0
    if name.startswith("IDLE"):
        P = T
        lr = k([(0, 0), (0.13, 0), (0.2, 20, "ease"), (0.37, 20), (0.43, -20, "ease"), (0.6, -20), (0.67, 0, "ease"),
                (1, 0)])
        ud = k([(0, 0), (0.43, 0), (0.5, 9, "ease"), (0.6, 9), (0.67, -4, "ease"), (0.85, -4), (0.93, 0, "ease"), (1, 0)])
        opn = _blink(t, 0.3 * P) * _blink(t, 0.78 * P) * _blink(t, 0.84 * P)
        raise_ = 0.25 * max(0.0, ud / 9)
        angry = 12 if "Phase2" in name else 4
        wide = 1.0 + 0.04 * math.sin(TAU * u)
    elif name.startswith("MOVE") or name.startswith("FLY"):
        lr = 8 * math.sin(TAU * u)
        ud = -6
        opn = 0.85 * _blink(t, 0.7 * T)
        angry, raise_ = 12, -0.2
    elif name.startswith("ATTACK") or name == "CHARGE":
        opn = k([(0, 1), (0.22, 0.55), (0.36, 1.0), (0.46, 0.12), (0.56, 1.0), (0.85, 0.85), (0.9, 0.15), (0.95, 1), (1, 1)])
        wide = k([(0, 1), (0.22, 0.95), (0.36, 1.25), (0.46, 1.1), (0.56, 1.05), (0.8, 1), (1, 1)])
        pup = k([(0, 1), (0.22, 1.1), (0.36, 0.72), (0.5, 0.9), (0.7, 1), (1, 1)])
        angry = k([(0, 4), (0.22, 22), (0.36, 14), (0.46, 20), (0.6, 8), (1, 4)])
        raise_ = k([(0, 0), (0.22, -0.35), (0.36, 0.3), (0.46, -0.2), (0.6, 0.1), (1, 0)])
        ud = k([(0, 0), (0.22, -6), (0.36, 0), (1, 0)])
        dz = max(0.0, min(1.0, (u - 0.52) / 0.06)) * (1 - max(0.0, min(1.0, (u - 0.62) / 0.2)))
        lr += 13 * math.cos(TAU * 2.5 * u) * dz
        ud += 14 * math.sin(TAU * 2.5 * u) * dz
    elif name == "HIT":
        opn = k([(0, 1), (0.08, 0.08), (0.3, 0.1), (0.42, 1.15), (0.7, 1.05), (0.8, 0.15), (0.88, 1), (1, 1)])
        wide = k([(0, 1), (0.42, 1.18), (0.75, 1.0), (1, 1)])
        pup = k([(0, 1), (0.42, 0.7), (0.8, 1), (1, 1)])
        angry = k([(0, 4), (0.1, -16), (0.45, -12), (0.8, 0), (1, 4)])
        raise_ = k([(0, 0), (0.1, 0.45), (0.5, 0.35), (1, 0)])
        dz = max(0.0, min(1.0, (u - 0.35) / 0.08)) * (1 - max(0.0, min(1.0, (u - 0.6) / 0.15)))
        lr = 14 * math.cos(TAU * 3 * u) * dz
        ud = 14 * math.sin(TAU * 3 * u) * dz
    elif name == "DEATH":
        opn = k([(0, 1), (0.05, 0.08), (0.12, 1.2), (0.5, 1.2), (0.62, 0.65), (0.78, 0.5), (0.86, 0.1), (1, 0.08)])
        wide = k([(0, 1), (0.12, 1.3), (0.5, 1.25), (0.7, 1.0), (1, 1)])
        pup = k([(0, 1), (0.12, 0.55), (0.5, 0.6), (0.7, 0.9), (1, 0.9)])
        angry = k([(0, 4), (0.08, -20), (0.6, -22), (1, -10)])
        raise_ = k([(0, 0), (0.1, 0.5), (0.6, 0.45), (1, -0.1)])
        dart = max(0.0, min(1.0, (u - 0.12) / 0.05)) * (1 - max(0.0, min(1.0, (u - 0.48) / 0.05)))
        lr = 17 * math.sin(TAU * 4.3 * u) * dart
        ud = 12 * math.sin(TAU * 3.1 * u + 1) * dart
        dz = max(0.0, min(1.0, (u - 0.5) / 0.05)) * (1 - max(0.0, min(1.0, (u - 0.8) / 0.06)))
        lr += 15 * math.cos(TAU * 3.5 * u) * dz
        ud += 12 * math.sin(TAU * 3.5 * u) * dz
    elif name.startswith("PHASE2"):
        opn = k([(0, 1), (0.2, 0.35), (0.32, 1.25), (0.6, 1.0), (1, 0.9)])
        wide = k([(0, 1), (0.32, 1.35), (0.6, 1.1), (1, 1.05)])
        pup = k([(0, 1), (0.32, 0.65), (0.7, 0.85), (1, 0.85)])
        angry = k([(0, 4), (0.2, 25), (0.32, 10), (0.6, 18), (1, 14)])
        raise_ = k([(0, 0), (0.2, -0.4), (0.32, 0.45), (0.6, 0), (1, -0.1)])
    for side, sx in (("G", -1), ("D", 1)):
        p.set(f"Oeil_{side}", scl=(wide, wide, max(wide * opn, 0.02)))
        p.set(f"Pupille_{side}", rot=(ud, 0, lr))   # regard seul : pas de rétrécissement (yeux de biais)
        p.set(f"Sourcil_{side}", loc=(0, 0, raise_ * r), rot=(0, -sx * angry, 0))


def with_eyes(actions, r):
    """Enveloppe un dictionnaire d'actions {nom: (n, boucle, fn)} avec le jeu des yeux."""
    out = {}
    for name, (n, loop, fn) in actions.items():
        def f(t, fn=fn, name=name, n=n):
            pose = fn(t)
            eye_motion(name, t, pose, n, r)
            return pose
        out[name] = (n, loop, f)
    return out


def make_mob_actions(spec, attack_fn, extra=None):
    """Retourne {nom: (n_images, boucle, fonction)}."""
    base = {"IDLE": idle, "MOVE": move, "FLY": fly, "ATTACK": attack_fn, "HIT": hit, "DEATH": death}
    out = {}
    for name, fn in base.items():
        def f(t, fn=fn, name=name):
            pose = fn(spec, t)
            if extra:
                extra(name, t, pose)
            if "Ficelle_1" in spec["bones"]:
                string_motion(name, t, pose)
            if "Oeil_G" in spec["bones"]:
                eye_motion(name, t, pose, LENGTHS[name], spec.get("eye_r", 0.1))
            return pose
        out[name] = (LENGTHS[name], LOOPS[name], f)
    return out
