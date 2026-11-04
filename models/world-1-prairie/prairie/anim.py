"""Animations : 5 Actions indépendantes (Idle, Move, Attack, Hit, Death) par ennemi.

Chaque animation est une fonction pose(frame) écrite en axes monde (avant = +Y), échantillonnée à chaque
image puis convertie en clés linéaires (les clés redondantes sont supprimées). Toutes les actions animent
tous les os : passer d'une action à l'autre ne laisse jamais de pose résiduelle.
Rotations : X négatif = penche vers l'avant ; os de ficelle : X positif = la ficelle part vers l'avant.
"""
import math
import random

import bpy
from mathutils import Euler, Quaternion, Vector

from .rig import LOBES, lobe_weights

TAU = math.tau
FPS = 30

PARAMS = {
    #             S : échelle des distances ; durées en images à 30 i/s
    "classique": dict(S=1.0, idle=72, move=36, attack=42, hit=18, death=60, float=0.045, sway=4.0, yaw=6.0,
                      breath=0.022, deform=1.0, lean=14.0, att_lean=18.0, back=0.17, lunge=0.62, hop=0.07,
                      recoil=0.12, drop=0.35, spin=260, string=5.0, trail=22.0, nac=0.0, prop=(0, 0, 0)),
    "etoile": dict(S=1.0, idle=72, move=36, attack=42, hit=18, death=60, float=0.045, sway=5.0, yaw=14.0,
                   breath=0.016, deform=0.85, lean=12.0, att_lean=16.0, back=0.18, lunge=0.66, hop=0.07,
                   recoil=0.13, drop=0.35, spin=300, string=5.0, trail=22.0, nac=0.0, prop=(0, 0, 0)),
    "dirigeable": dict(S=1.2, idle=72, move=36, attack=44, hit=18, death=66, float=0.035, sway=3.0, yaw=3.0,
                       breath=0.014, deform=0.8, lean=6.0, att_lean=5.0, back=0.26, lunge=0.95, hop=0.0,
                       recoil=0.14, drop=0.3, spin=200, string=0.0, trail=0.0, nac=0.0, prop=(6, 6, 18)),
    "montgolfiere": dict(S=3.5, idle=96, move=48, attack=60, hit=24, death=90, float=0.12, sway=1.6, yaw=3.0,
                         breath=0.016, deform=0.7, lean=6.0, att_lean=6.0, back=0.45, lunge=1.5, hop=0.12,
                         recoil=0.3, drop=1.2, spin=90, string=0.0, trail=0.0, nac=3.0, prop=(0, 0, 0)),
    "zeppelin": dict(S=8.0, idle=120, move=60, attack=72, hit=30, death=110, float=0.18, sway=1.2, yaw=1.0,
                     breath=0.012, deform=0.6, lean=3.0, att_lean=3.0, back=0.9, lunge=3.2, hop=0.0,
                     recoil=0.5, drop=2.2, spin=40, string=0.0, trail=0.0, nac=2.0, prop=(8, 8, 26)),
}


# ------------------------------------------------------------------------------------------- outils

def ease(u, kind):
    u = min(max(u, 0.0), 1.0)
    if kind == "lin":
        return u
    if kind == "in":
        return u * u * u
    if kind == "in2":
        return u * u
    if kind == "out":
        return 1 - (1 - u) ** 3
    if kind == "out2":
        return 1 - (1 - u) ** 2
    return u * u * (3 - 2 * u)  # inout


def track(f, keys):
    """keys = [(image, valeur), (image, valeur, 'ease'), ...] ; l'easing s'applique au segment qui arrive."""
    if f <= keys[0][0]:
        return keys[0][1]
    for a, b in zip(keys, keys[1:]):
        if f <= b[0]:
            u = (f - a[0]) / max(b[0] - a[0], 1e-9)
            return a[1] + (b[1] - a[1]) * ease(u, b[2] if len(b) > 2 else "inout")
    return keys[-1][1]


def fade(f, n, start=0.7):
    """1 puis 0 en fin d'animation (les vibrations s'éteignent pour finir exactement au repos)."""
    u = (f / n - start) / (1 - start)
    return 1.0 if u <= 0 else max(0.0, 1 - ease(u, "inout"))


def vib(f, f0, amp, period, n, decay=0.3, phase=0.0):
    if f < f0:
        return 0.0
    x = f - f0
    return amp * math.exp(-x / max(decay * n, 1e-6)) * math.sin(TAU * x / period + phase) * fade(f, n)


class Pose:
    def __init__(self):
        self.d = {}
        self.spins = {}
        self.vanish = None

    def _g(self, b):
        return self.d.setdefault(b, [Vector(), Quaternion(), Vector((1, 1, 1))])

    def loc(self, b, v):
        g = self._g(b)
        g[0] = g[0] + Vector(v)

    def rot(self, b, deg):
        g = self._g(b)
        g[1] = Euler([math.radians(x) for x in deg], "XYZ").to_quaternion() @ g[1]

    def rot_axis(self, b, axis, deg):
        g = self._g(b)
        g[1] = Quaternion(Vector(axis), math.radians(deg)) @ g[1]

    def scl(self, b, s):
        g = self._g(b)
        s = Vector((s, s, s)) if isinstance(s, (int, float)) else Vector(s)
        g[2] = Vector((g[2].x * s.x, g[2].y * s.y, g[2].z * s.z))

    def spin(self, b, angle):
        """Rotation locale autour de l'axe de l'os (hélices), en radians, sans limite de tours."""
        self.spins[b] = self.spins.get(b, 0.0) + angle


def _simplify(vals, tol):
    n = len(vals)
    keep = [0]
    i = 0
    while i < n - 1:
        j = i + 1
        while j + 1 < n:
            a, b = vals[i], vals[j + 1]
            ok = True
            for k in range(i + 1, j + 1):
                if abs(a + (b - a) * (k - i) / (j + 1 - i) - vals[k]) > tol:
                    ok = False
                    break
            if not ok:
                break
            j += 1
        keep.append(j)
        i = j
    return keep


CHANNELS = [("location", 0), ("location", 1), ("location", 2), ("rotation_euler", 0), ("rotation_euler", 1),
            ("rotation_euler", 2), ("scale", 0), ("scale", 1), ("scale", 2)]


def write_action(arm, F, name, n, fn, loop):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    bones = [b.name for b in arm.data.bones]
    rest = {b.name: b.matrix_local.to_quaternion() for b in arm.data.bones}
    vals = {b: [[] for _ in CHANNELS] for b in bones}
    prev = {}
    for f in range(n + 1):
        P = fn(f)
        to_translations(P, F)
        for b in bones:
            l, q, s = P.d.get(b, (Vector(), Quaternion(), Vector((1, 1, 1))))
            R = rest[b]
            Ri = R.inverted()
            ll = Ri @ l
            ql = Ri @ q @ R
            e = ql.to_euler("XYZ", prev[b]) if b in prev else ql.to_euler("XYZ")
            prev[b] = e.copy()
            ex, ey, ez = e
            if b in P.spins:
                ey += P.spins[b]
            for k, v in enumerate((ll.x, ll.y, ll.z, ex, ey, ez, s.x, s.y, s.z)):
                vals[b][k].append(v)
    for b in bones:
        for k, (path, idx) in enumerate(CHANNELS):
            v = vals[b][k]
            keep = _simplify(v, 2e-5 if k < 3 else 1e-4)
            fc = act.fcurve_ensure_for_datablock(arm, f'pose.bones["{b}"].{path}', index=idx, group_name=b)
            fc.keyframe_points.add(len(keep))
            co = []
            for j in keep:
                co += [1.0 + j, v[j]]
            fc.keyframe_points.foreach_set("co", co)
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
            fc.update()
    act.use_frame_range = True
    act.frame_start = 1
    act.frame_end = 1 + n
    act.use_cyclic = loop
    return act


# ------------------------------------------------------------------------------------------- briques

def _lobes_dir(P, k_fn):
    for name, e in LOBES:
        k = k_fn(e)
        if k is not None:
            P.scl(name, k)


def _front_squash(P, k, D=1.0):
    """Écrase l'avant (k < 1) : les lobes avant rétrécissent vers le centre (échelle uniforme). Les yeux, enfants
    de Lobe_Avant, suivent exactement la même transformation que la peau du visage."""
    for name, e in LOBES:
        w = max(0.0, e.y)
        if w > 0:
            P.scl(name, 1 + (k - 1) * 0.6 * w)


def _chain(P, F, angles_x, angles_y=None):
    for i, b in enumerate(F.chain):
        ax = angles_x[i] if isinstance(angles_x, (list, tuple)) else angles_x
        ay = (angles_y[i] if isinstance(angles_y, (list, tuple)) else angles_y) if angles_y is not None else 0.0
        P.rot(b, (ax, ay, 0))


def bump(f, center, half):
    """0 -> 1 -> 0 autour de `center` (clignement)."""
    u = 1 - abs(f - center) / half
    return 0.0 if u <= 0 else u * u * (3 - 2 * u)


def _eyes(P, F, blink=0.0, look=(0.0, 0.0), anger=0.0, raise_=0.0, wide=1.0):
    """Yeux, uniquement par déplacements d'os : blink 0 = ouverts, 1 = fermés (les paupières haut/bas se
    rejoignent et ressortent du creux de la surface) ; look en fraction de la taille de l'oeil (x vers la droite
    de l'observateur, y vers le haut) ; anger en degrés (froncés si > 0, inquiets si < 0) ; raise_ lève les
    sourcils ; wide > 1 écarquille."""
    for e in F.eye_rig:
        hh, be, ne = e["size"], e["b"], e["n"]
        bl = min(max(blink, 0.0), 0.97)
        extra = (wide - 1.0) * (1.0 - bl)
        top = be * (hh * (extra - bl)) + ne * (e["sag"] * bl)
        bot = be * (hh * (bl - extra)) + ne * (e["sag"] * bl)
        P.loc(e["lid_h"], top)
        P.loc(e["lid_b"], bot)
        P.loc(e["pupil"], e["t"] * (look[0] * 0.32 * hh) + be * (look[1] * 0.3 * hh))
        P.loc(e["pup_h"], top)
        P.loc(e["pup_l"], bot)
        P.rot_axis(e["brow"], ne, e["side"] * anger)
        P.loc(e["brow"], be * (raise_ * hh))


def to_translations(P, F):
    """Convertit l'écrasement / gonflement (échelles virtuelles de Body et des lobes) en DÉPLACEMENTS des os de
    l'enveloppe, posés sur la surface : aucune échelle d'os n'est exportée (Roblox et certains moteurs les
    ignorent). Les pièces attachées sont des enfants de ces os : elles suivent exactement."""
    one = Vector((1, 1, 1))
    body = P.d["Body"][2].copy() if "Body" in P.d else one.copy()
    for name, _e in LOBES:
        k = P.d[name][2].copy() if name in P.d else one.copy()
        tot = Vector((body.x * k.x, body.y * k.y, body.z * k.z))
        rel = F.lobe_heads[name] - F.C
        if name in P.d:
            P.d[name][2] = one.copy()
        P.loc(name, Vector(((tot.x - 1) * rel.x, (tot.y - 1) * rel.y, (tot.z - 1) * rel.z)))
    if "Body" in P.d:
        P.d["Body"][2] = one.copy()
    if getattr(P, "vanish", None) is not None:
        P.scl("Body", P.vanish)  # seule échelle réelle : disparition finale de Death (ignorée par Roblox)


def _body_vol(P, sy, extra=(1, 1, 1)):
    sxz = 1 / math.sqrt(max(sy, 1e-3))
    P.scl("Body", (sxz * extra[0], sy * extra[1], sxz * extra[2]))


# ------------------------------------------------------------------------------------------- animations

def idle(F, A, f, n):
    P = Pose()
    t = f / n
    w = TAU * t
    fl, b = A["float"], A["breath"]
    P.loc("Motion", (0.25 * fl * math.sin(w + 1.1), 0.2 * fl * math.sin(w + 2.3), fl * math.sin(w)))
    P.rot("Motion", (0.6 * A["sway"] * math.sin(w + 0.7), A["sway"] * math.sin(w + 2.0), A["yaw"] * math.sin(w + 0.4)))
    sz = 1 + b * math.sin(2 * w) + 0.6 * b * math.cos(w)
    k = 1 / math.sqrt(sz)
    P.scl("Body", (k * (1 + 0.25 * b * math.sin(2 * w + 1.3)), k * (1 - 0.25 * b * math.sin(2 * w + 1.3)), sz))
    for i, (name, _e) in enumerate(LOBES):
        P.scl(name, 1 + 0.45 * b * math.sin(2 * w + 1.9 * i))
    _chain(P, F, [A["string"] * math.sin(w - 0.9 * (i + 1)) for i in range(len(F.chain))],
           [0.6 * A["string"] * math.sin(w + 1.3 - 0.7 * i) for i in range(len(F.chain))])
    P.rot_axis("Orbite", F.orbit[2], 16 * math.sin(w))
    for pb in F.props:
        P.spin(pb, TAU * A["prop"][0] * t)
    if F.nacelle:
        P.rot(F.nacelle, (A["nac"] * math.sin(w - 1.2), 0.6 * A["nac"] * math.sin(w + 0.5), 0))
    glance = max(-1.0, min(1.0, 1.8 * math.sin(w + 0.3))) * 0.55
    _eyes(P, F, blink=bump(f, 0.62 * n, 3.5), look=(glance, 0.12 * math.sin(2 * w)),
          anger=2.0 * math.sin(w), raise_=0.03 * math.sin(2 * w))
    return P


def move(F, A, f, n):
    P = Pose()
    t = f / n
    w = TAU * t
    fl, D, L = A["float"], A["deform"], A["lean"]
    P.loc("Motion", (0.15 * fl * math.sin(w), 0.3 * fl * math.sin(2 * w + 0.8), 0.6 * fl * math.sin(2 * w)))
    P.rot("Motion", (-L + 0.22 * L * math.sin(2 * w + 0.6), 0.6 * A["sway"] * math.sin(w), 0.4 * A["yaw"] * math.sin(w + 1)))
    sy = 1 + 0.07 * D + 0.025 * D * math.sin(2 * w + 0.5)
    _body_vol(P, sy, (1.0, 1.0, 1 - 0.02 * D))
    _front_squash(P, 1 - 0.07 * D - 0.015 * D * math.sin(2 * w))
    _lobes_dir(P, lambda e: 1 + 0.035 * D * (-e.y) if e.y < 0 else None)
    _chain(P, F, [-A["trail"] / max(len(F.chain), 1) + 4 * math.sin(2 * w - 0.9 * (i + 1)) for i in range(len(F.chain))],
           [2.5 * math.sin(w - 0.7 * i) for i in range(len(F.chain))])
    P.rot_axis("Orbite", F.orbit[2], 10 * math.sin(w) - 8)
    for pb in F.props:
        P.spin(pb, TAU * A["prop"][1] * t)
    if F.nacelle:
        P.rot(F.nacelle, (-0.8 * L + A["nac"] * 0.5 * math.sin(2 * w - 1.0), 0.5 * A["nac"] * math.sin(w), 0))
    _eyes(P, F, blink=0.15, look=(0.15 * math.sin(w), -0.35), anger=7 + 2 * math.sin(2 * w), raise_=-0.05)
    return P


def attack(F, A, f, n):
    """Recul + compression, projection brutale vers l'avant (+Y), écrasement à l'impact, rebond, retour."""
    P = Pose()
    a1, a2, a3, a4 = (round(n * x) for x in (0.30, 0.42, 0.50, 0.66))
    back, lunge, L, D, S = A["back"], A["lunge"], A["att_lean"], A["deform"], A["S"]
    y = track(f, [(0, 0), (a1, -back, "inout"), (a2, lunge, "in2"), (a3, lunge * 1.04, "out"),
                  (a4, lunge * 0.8, "out2"), (n, 0, "inout")])
    z = track(f, [(0, 0), (a1, -0.25 * back, "inout"), (a2, 0.02 * S, "lin"), (a3, 0, "out"),
                  ((a3 + a4) // 2, A["hop"], "out"), (a4, 0, "in2"), (n, 0)])
    P.loc("Motion", (vib(f, a2, 0.012 * S, 3.0, n), y, z))
    pitch = track(f, [(0, 0), (a1, 0.6 * L, "inout"), (a2, -L, "in2"), (a3, -1.25 * L, "out"),
                      (a4, 0.35 * L, "inout"), (n, 0, "inout")]) + vib(f, a4, 0.15 * L, n * 0.14, n)
    P.rot("Motion", (pitch, vib(f, a2, 3.0, 5.0, n), 0))
    sy = track(f, [(0, 1), (a1, 1 - 0.2 * D, "inout"), (a2 - 1, 1 + 0.24 * D, "in2"), (a2, 1 + 0.18 * D, "lin"),
                   (a3, 1 - 0.24 * D, "out"), (a4, 1 + 0.07 * D, "inout"), (n, 1, "inout")])
    sy += vib(f, a4, 0.035 * D, n * 0.11, n)
    _body_vol(P, sy)
    kf = track(f, [(0, 1), (a2 - 1, 1.03, "inout"), (a3, 1 - 0.28 * D, "out"), (a4, 1.0, "inout"), (n, 1)])
    _front_squash(P, kf)
    _chain(P, F, [track(f, [(0, 0), (a1, 16), (a2, -36, "in2"), (a3, 26, "out"), (a4, -10), (n, 0)]) / max(len(F.chain), 1) * (1 + 0.3 * i)
                  + vib(f, a4, 6, 9, n, phase=-0.8 * i) for i in range(len(F.chain))])
    P.rot_axis("Orbite", F.orbit[2], track(f, [(0, 0), (a1, 12), (a2, -25, "in2"), (a3, 15, "out"), (n, 0)]))
    for pb in F.props:
        P.spin(pb, TAU * A["prop"][2] * ease(f / n, "inout"))
    if F.nacelle:
        nac = track(f, [(0, 0), (a1, 10), (a2, -20, "in2"), (a3, 28, "out"), (a4, -8, "inout"), (n, 0, "inout")])
        P.rot(F.nacelle, (nac + vib(f, a4, 4, n * 0.2, n), 0, 0))
    _eyes(P, F,
          blink=track(f, [(0, 0), (a1, 0.45), (a2 - 1, 0, "out"), (a3, 0.9, "out"), (a4, 0.0), (n, 0)]),
          look=(0.0, track(f, [(0, 0), (a1, -0.4), (a4, -0.3), (n, 0)])),
          anger=track(f, [(0, 0), (a1, 15), (a3, 18), (a4, 8), (n, 0)]),
          raise_=track(f, [(0, 0), (a1, -0.12), (a3, -0.1), (n, 0)]),
          wide=track(f, [(0, 1), (a1, 1), (a2 - 1, 1.15, "out"), (a3, 1.0), (n, 1)]))
    return P


def hit(F, A, f, n):
    """Compression rapide, petit recul, vibration, retour à la forme normale."""
    P = Pose()
    i1 = max(2, round(n * 0.12))
    rec, D, S = A["recoil"], A["deform"], A["S"]
    y = track(f, [(0, 0), (i1, -rec, "out"), (round(n * 0.6), -0.45 * rec, "inout"), (n, 0, "inout")])
    P.loc("Motion", (vib(f, i1, 0.16 * rec, 2.6, n, 0.35), y, vib(f, i1, 0.08 * rec, 3.4, n, 0.35, 1.0)))
    P.rot("Motion", (track(f, [(0, 0), (i1, 0.6 * max(A["att_lean"], 6), "out"), (n, 0, "inout")]) + vib(f, i1, 3, 3.0, n),
                     vib(f, i1, 5.0, 2.8, n, 0.3, 0.5), vib(f, i1, 3.0, 3.6, n)))
    sy = track(f, [(0, 1), (i1, 1 - 0.22 * D, "out"), (round(n * 0.35), 1 + 0.08 * D, "inout"),
                   (round(n * 0.6), 1 - 0.03 * D, "inout"), (n, 1, "inout")])
    _body_vol(P, sy, (1 + vib(f, i1, 0.03 * D, 2.2, n), 1, 1 - vib(f, i1, 0.03 * D, 2.2, n)))
    _front_squash(P, track(f, [(0, 1), (i1, 1 - 0.16 * D, "out"), (round(n * 0.45), 1.02, "inout"), (n, 1)]))
    for i, (name, _e) in enumerate(LOBES):
        P.scl(name, 1 + vib(f, i1, 0.03 * D, 2.4 + 0.2 * (i % 3), n, 0.3, 1.7 * i))
    _chain(P, F, [track(f, [(0, 0), (i1, 18), (round(n * 0.5), -8), (n, 0)]) + vib(f, i1, 6, 5, n, phase=-0.8 * i)
                  for i in range(len(F.chain))])
    P.rot_axis("Orbite", F.orbit[2], vib(f, 0, 12, n * 0.4, n, 0.5))
    for pb in F.props:
        P.spin(pb, TAU * max(1, A["prop"][0] // 4) * f / n)
    if F.nacelle:
        P.rot(F.nacelle, (track(f, [(0, 0), (i1, -8), (round(n * 0.5), 5), (n, 0)]) + vib(f, i1, 3, n * 0.3, n), 0, 0))
    _eyes(P, F,
          blink=track(f, [(0, 0), (i1, 1, "out"), (round(n * 0.45), 1), (round(n * 0.6), 0, "out"), (n, 0)]),
          look=(vib(f, round(n * 0.6), 0.5, 3.0, n, 0.4), 0.0),
          anger=track(f, [(0, 0), (i1, -14), (round(n * 0.6), -8), (n, 0)]),
          raise_=track(f, [(0, 0), (i1, 0.25), (n, 0)]),
          wide=track(f, [(0, 1), (round(n * 0.6), 1), (round(n * 0.72), 1.15), (n, 1)]))
    return P


def death(F, A, f, n):
    """Le ballon se dégonfle : il perd son volume par endroits, se ratatine en tournoyant, puis disparaît."""
    P = Pose()
    rnd = random.Random(1234)
    j = max(3, round(n * 0.1))
    e_end = round(n * 0.75)
    rec, D, S = A["recoil"], A["deform"], A["S"]
    env = math.sin(math.pi * min(max((f - j) / (e_end - j), 0), 1))
    # recul initial, puis vol erratique en perdant de l'altitude
    y = track(f, [(0, 0), (j, -0.8 * rec, "out"), (n, -1.1 * rec, "lin")])
    z = track(f, [(0, 0), (j, 0.02 * S, "out"), (e_end, -0.65 * A["drop"], "in2"), (n, -A["drop"], "lin")])
    zx = 0.07 * S * env * math.sin(TAU * f / (n * 0.24))
    zy = 0.05 * S * env * math.sin(TAU * f / (n * 0.19) + 1.0)
    P.loc("Motion", (zx, y + zy, z))
    spin = track(f, [(0, 0), (j, 0), (n, A["spin"], "inout")])
    P.rot("Motion", (track(f, [(0, 0), (j, 0.6 * max(A["att_lean"], 6), "out"), (n, 0)]) + 16 * env * math.sin(TAU * f / (n * 0.17)),
                     11 * env * math.sin(TAU * f / (n * 0.13) + 1), spin))
    # volume global : choc, puis le ballon se vide et s'aplatit, puis disparaît
    shrink = track(f, [(0, 1), (j, 1, "lin"), (e_end, 0.82, "inout"), (n, 0.65, "in")])
    # disparition finale : seule échelle réelle exportée (dans un moteur sans échelle d'os, il reste un petit tas
    # dégonflé : retirer l'ennemi à la fin de l'animation)
    P.vanish = track(f, [(0, 1.0), (round(n * 0.85), 1.0), (n, 0.001, "in")])
    flat = track(f, [(0, 1), (j, 1, "lin"), (e_end, 0.68, "inout"), (n, 0.68)])
    sy = track(f, [(0, 1), (j, 1 - 0.2 * D, "out"), (2 * j, 1, "inout"), (n, 1)])
    sxz = 1 / math.sqrt(sy)
    P.scl("Body", (shrink * sxz, shrink * sy, shrink * sxz * flat))
    # ratatinement : chaque lobe se vide à son rythme, avec des frémissements
    for i, (name, _e) in enumerate(LOBES):
        tgt = rnd.uniform(0.5, 0.88)
        delay = rnd.uniform(0.0, 0.3) * (e_end - j)
        k = track(f, [(0, 1), (j + delay, 1, "lin"), (e_end, tgt, "inout"), (n, tgt)])
        k += 0.07 * env * math.sin(TAU * f / (n * rnd.uniform(0.07, 0.11)) + i * 1.7)
        tw = rnd.uniform(-1, 1)
        P.scl(name, k * (1 + 0.12 * env * tw))
    _chain(P, F, [track(f, [(0, 0), (j, 15), (n, -25)]) + 12 * env * math.sin(TAU * f / (n * 0.2) - 0.8 * i)
                  for i in range(len(F.chain))])
    P.rot_axis("Orbite", F.orbit[2], track(f, [(0, 0), (n, 90)]))
    for pb in F.props:
        P.spin(pb, TAU * A["prop"][0] * 0.5 * ease(f / n, "out2"))
    if F.nacelle:
        P.rot(F.nacelle, (track(f, [(0, 0), (j, -10), (n, 18)]) + 8 * env * math.sin(TAU * f / (n * 0.3)), 6 * env, 0))
    # yeux : choc, puis regard étourdi (les pupilles tournent), puis les yeux se ferment
    r = track(f, [(0, 0), (j, 0.0), (round(n * 0.3), 0.8), (round(n * 0.7), 0.8), (round(n * 0.8), 0.2)])
    a = TAU * 3.0 * f / n
    _eyes(P, F,
          blink=track(f, [(0, 0), (round(n * 0.68), 0), (round(n * 0.85), 1, "inout"), (n, 1)]),
          look=(r * math.cos(a), r * math.sin(a)),
          anger=track(f, [(0, 0), (j, -16, "out"), (n, -16)]),
          raise_=track(f, [(0, 0), (j, 0.3, "out"), (n, 0.25)]),
          wide=track(f, [(0, 1), (j, 1.2, "out"), (round(n * 0.6), 1.1), (n, 1.0)]))
    return P


ACTIONS = [("Idle", idle, "idle", True), ("Move", move, "move", True), ("Attack", attack, "attack", False),
           ("Hit", hit, "hit", False), ("Death", death, "death", False)]


def make_all(arm, F, prefix=""):
    A = PARAMS[F.kind]
    acts = {}
    for name, fn, key, loop in ACTIONS:
        n = A[key]
        acts[name] = write_action(arm, F, prefix + name, n, lambda f, fn=fn, n=n: fn(F, A, f, n), loop)
    arm.animation_data.action = acts["Idle"]
    return acts
