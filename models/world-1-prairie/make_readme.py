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
      "- **Animations sans échelle d'os** : tout est fait en position et rotation d'os. Le corps s'écrase, s'étire et "
      "se dégonfle en déplaçant 14 os posés sur l'enveloppe. Seule exception : l'os `Body` passe à l'échelle 0 dans les "
      "dernières images de `Death` (disparition) ; un moteur qui ignore l'échelle (Roblox) garde un petit tas dégonflé : "
      "retirer l'ennemi à la fin de `Death`.",
      "- **Os** : `Root` (sol, immobile) → `Motion` (déplacements, rotations) → `Body` → 14 `Lobe_*` (6 axes + 8 coins, "
      "posés sur l'enveloppe). Tout ce qui est fixé au corps est **enfant de l'os qui porte la peau à son point "
      "d'attache**, et cette zone de peau est pondérée à 100 % sur ce même os : visage → `Lobe_Avant` "
      "(`Paupiere_H/B_G/D`, `Pupille_G/D` + `Pupille_H/B_G/D`, `Sourcil_G/D`) ; noeud et ficelle → `Lobe_Bas` "
      "(`Ficelle_1..3`) ; hélice du mini-dirigeable → `Lobe_Arriere` ; nacelle de la montgolfière → `Lobe_Bas` ; "
      "moteurs latéraux du zeppelin → `Lobe_Gauche/Droite`. Les autres décors prennent exactement les poids de "
      "l'enveloppe sous eux. Rien ne peut se décoller, quel que soit le moteur ou sa compression d'animation.",
      "- **Yeux animés** dans les 5 actions : clignement (les paupières haut/bas se rejoignent) et coups d'oeil en "
      "`Idle`, regard concentré en `Move`, plissement à l'anticipation puis yeux écarquillés et crispés à l'impact en "
      "`Attack`, yeux fermés de douleur en `Hit`, regard étourdi (pupilles qui tournent) puis fermeture en `Death`. "
      "Ligne « YEUX » des planches d'animation.",
      "- **Tout est fixé** : aucune pièce ne flotte (contrôlé au repos) ; les motifs imprimés sont des autocollants "
      "épais dont la base s'enfonce dans l'enveloppe, le halo est tenu par une tige, les petits décors (étoiles, bulles, "
      "éclats, braises, étincelles, volutes) sont posés sur le ballon.",
      "- **Budget** : 20 000 triangles maximum par ennemi (vérifié à chaque génération, colonne « Triangles »). "
      "4 influences maximum par sommet.",
      "- **Un seul matériau par ennemi** (`<Ennemi>_Materiau`) : toutes les couleurs sont dans une petite **texture "
      "palette** (`*_Palette.png`, 128 × 128, une case par couleur, **incrustée dans le FBX** et fournie à côté), avec "
      "des **UV** qui placent chaque face sur sa case. Lueurs (`*_Palette_Emission.png`) et rugosité/métal "
      "(`*_Palette_RM.png`) sont fournies pour les moteurs qui les utilisent. Attribut de **couleurs de sommets** "
      "(`Couleur`) en plus.",
      "- **Propriétés personnalisées** sur l'armature (exportées dans le FBX) : `Nom`, `Famille`, `Element`, `PV`, `Avant`, `Animations`.",
      "", "## FBX", "",
      "Export Blender standard : `-Z` avant / `Y` haut (convention FBX), unités appliquées, pas d'os de bout (leaf bones), "
      "tous les os, une prise par Action (`<Rig>|Idle`, `<Rig>|Attack`…), toutes les images échantillonnées.",
      "Le résultat de la vérification automatique (réimport et comparaison au `.blend`) est dans "
      "[`FBX/verification.md`](FBX/verification.md).", "",
      "- **Roblox Studio** : importer le FBX avec le *3D Importer* (un seul MeshPart skinné de moins de 20 000 "
      "triangles). Appliquer `*_Palette.png` comme texture (`TextureID` ou `SurfaceAppearance.ColorMap`) si elle "
      "n'est pas reprise automatiquement. Les 5 prises sont dans le FBX ; à la fin de `Death`, retirer l'ennemi.",
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
