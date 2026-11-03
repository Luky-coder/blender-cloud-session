"""Écrit World_1_Prairie/README.md à partir de World_1_Prairie/inventaire.json (python3, hors Blender)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "World_1_Prairie")

with open(os.path.join(OUT, "inventaire.json"), encoding="utf-8") as fh:
    inv = json.load(fh)


def prev(r):
    base = os.path.splitext(r["blend"].replace("Blender/", "Previews/", 1))[0]
    return base


L = ["# Monde 1 — La Prairie : 23 ennemis gonflables", "",
     "![Présentation](Previews/Presentation_Monde1.jpg)", "",
     "21 mobs normaux (3 familles × 7 éléments), 1 mini-boss et 1 boss. Chaque ennemi est un modèle indépendant : "
     "**un maillage unique + une armature + 5 Actions** (`Idle`, `Move`, `Attack`, `Hit`, `Death`), "
     "dans son propre `.blend` et son propre `.fbx`.", "",
     "| Ennemi | Élément | PV | Sommets | Triangles | Os | Fichiers | Aperçus |", "|---|---|---|---|---|---|---|---|"]
for r in inv:
    p = prev(r)
    L.append(f"| {r['name']} | {r['element']} | {r['pv']} | {r['verts']:,} | {r['tris']:,} | {r['bones']} | "
             f"[blend]({r['blend']}) · [fbx]({r['fbx']}) | [vue]({p}.jpg) · [animations]({p}_Animations.jpg) · "
             f"[attaque (gif)]({p}_Attack.gif) |".replace(",", " "))
a = inv[0]["actions"]
L += ["", "## Animations", "",
      "Durées à 30 images/s. Toutes les animations sont « sur place » : l'os `Root` ne bouge jamais, et chaque "
      "animation se termine dans la pose de repos (ou disparaît pour `Death`).", "",
      "| Action | Boucle | Ballons (Classique, Étoile) | Mini-dirigeable | Montgolfière | Zeppelin | Contenu |",
      "|---|---|---|---|---|---|---|"]
by = {}
for r in inv:
    fam = r["id"].split("_")[0] + "_" + r["id"].split("_")[1]
    by.setdefault(fam, r["actions"])


def d(fam, act):
    v = by.get(fam, {}).get(act)
    return f"{v[1] - v[0]} i" if v else "—"


desc = {
    "Idle": "flottement vertical, oscillation, « respiration » de l'enveloppe, ficelle/nacelle qui suivent avec retard",
    "Move": "inclinaison vers l'avant (+Y), flottement plus rapide, étirement sous l'accélération, avant aplati par l'air",
    "Attack": "recul + compression → projection brutale vers l'avant → écrasement à l'impact → petit rebond → retour",
    "Hit": "compression rapide, petit recul, vibration amortie, retour à la forme normale",
    "Death": "choc, puis dégonflement inégal (14 lobes), ratatinement en tournoyant et en chutant, disparition",
}
for act in ["Idle", "Move", "Attack", "Hit", "Death"]:
    L.append(f"| `{act}` | {'oui' if act in ('Idle', 'Move') else 'non'} | {d('Ballon_Classique', act)} | "
             f"{d('Mini_Dirigeable', act)} | {d('MiniBoss_Montgolfiere', act)} | {d('Boss_Zeppelin', act)} | {desc[act]} |")
L += ["",
      "Spécificités de l'attaque : les mini-dirigeables chargent à l'horizontale (hélice qui s'emballe), la nacelle de "
      "la montgolfière bascule vers l'avant et frappe à l'impact, le zeppelin avance de tout son corps (≈ 3 m).", "",
      "Chaque planche `*_Animations.jpg` montre les images clés des 5 animations vues de côté (l'avant, +Y, part vers "
      "la droite). Les GIF `*_Attack.gif` montrent l'attaque complète image par image.", "",
      "## Rig et conventions", "",
      "- **Axes** : avant = **+Y**, haut = +Z, unités en mètres. Le point le plus bas (bout de ficelle, nacelle) est à Z = 0, "
      "l'origine de l'objet est au sol sous le modèle.",
      "- **Pivots** : `Motion` et `Body` sont au centre de l'enveloppe (rotations et écrasements autour du centre "
      "du ballon) ; la nacelle de la montgolfière pivote sous la bouche de l'enveloppe ; chaque hélice sur son moyeu.",
      "- **Os** : `Root` (sol, immobile) → `Motion` (déplacements, rotations) → `Body` (écrasement / étirement) → "
      "14 `Lobe_*` (6 axes + 8 coins : déforment l'enveloppe, servent au dégonflement). Suiveurs enfants de `Motion` : "
      "`Orbite` (éléments flottants : étoiles, bulles, braises…), `Ficelle_1..3`, `Helice*`, `Nacelle`.",
      "- **Export propre pour les moteurs** : tous les os sont orientés comme le monde. Les échelles non uniformes "
      "ne sont portées que par des os sans enfants tournés, donc sans cisaillement : le FBX se lit à l'identique "
      "dans Unity, Unreal ou Godot. 4 influences maximum par sommet.",
      "- **Couleurs** : chaque ennemi a une petite **texture palette** (`*_Palette.png`, 128 × 128, une case de couleur "
      "par matériau) branchée sur la Base Color de tous ses matériaux, des **UV** qui placent chaque face sur sa case, et "
      "un attribut de **couleurs de sommets** (`Couleur`). La texture est **incrustée dans le FBX** (et fournie à côté) : "
      "les couleurs s'affichent même dans les moteurs qui ignorent la couleur « Diffuse » des matériaux FBX.",
      "- **Matériaux** : Principled BSDF (rugosité, vernis, émission pour les lueurs : halos, flammes, coutures violettes…).",
      "- **Propriétés personnalisées** sur l'armature (exportées dans le FBX) : `Nom`, `Famille`, `Element`, `PV`, `Avant`, `Animations`.",
      "", "## FBX", "",
      "Export Blender standard : `-Z` avant / `Y` haut (convention FBX), unités appliquées, pas d'os de bout (leaf bones), "
      "tous les os, une prise par Action (`<Rig>|Idle`, `<Rig>|Attack`…), toutes les images échantillonnées.",
      "Le résultat de la vérification automatique (réimport et comparaison au `.blend`) est dans "
      "[`FBX/verification.md`](FBX/verification.md).", "",
      "- **Unity** : importer le FBX en *Rig > Generic*. Les clips `Idle` et `Move` se mettent en *Loop Time*. "
      "Si les matériaux restent blancs : onglet *Materials* > *Extract Textures…* (la palette est alors extraite et reliée).",
      "- **Unreal** : importer avec *Import Animations* ; le squelette est propre à chaque ennemi.",
      "- **Godot 4** : importer le FBX directement ; mettre `Idle`/`Move` en boucle dans l'AnimationPlayer.", "",
      "## Régénérer", "",
      "```bash", "blender -b --factory-startup -P models/world-1-prairie/export.py -- all --gif",
      "blender -b --factory-startup -P models/world-1-prairie/verify_fbx.py", "python3 models/world-1-prairie/make_readme.py",
      "```", "",
      "Le code source est dans `models/world-1-prairie/prairie/` : `families.py` (formes de base), `elements.py` "
      "(détails des 7 éléments), `bosses.py`, `rig.py`, `anim.py`.", ""]
with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(L))
print("README écrit")
