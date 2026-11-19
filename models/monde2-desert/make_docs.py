"""Écrit la documentation du Monde 2 : World_2_Desert/README.md et Textures/ (palettes de référence).

    blender -b --factory-startup --python-exit-code 1 -P models/monde2-desert/make_docs.py
"""
import importlib
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "World_2_Desert")

from desert import core  # noqa: E402
from desert.elements import ELEMENTS, ORDER  # noqa: E402

FAMS = [("cactus", ORDER), ("pyramid", ORDER), ("airship", ORDER), ("scarab", ["Plante"]), ("oasis", ["Plante"])]
ROLES = list(core.ELEMENT_ROLES) + ["or", "sable", "ocre", "cuir", "turquoise", "terre"]


def palette_png(elem, path, cell=64):
    """Nuancier : une case par rôle de matériau (rôles élémentaires puis rôles désert)."""
    pal = ELEMENTS[elem]["palette"]
    cols = len(ROLES)
    img = bpy.data.images.new("pal_" + elem, cols * cell, cell, alpha=False)
    px = []
    for _y in range(cell):
        for c in range(cols * cell):
            role = ROLES[c // cell]
            spec = pal.get(role) if role in core.ELEMENT_ROLES else core.DESERT_ROLES[role]
            r, g, b = core.lin(spec["color"])
            px += [r, g, b, 1.0]
    img.pixels.foreach_set(px)
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()


def main():
    os.makedirs(os.path.join(OUT, "Textures"), exist_ok=True)
    for e in ORDER:
        palette_png(e, os.path.join(OUT, "Textures", f"Palette_{e}.png"))
    with open(os.path.join(OUT, "Textures", "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Textures\n\nChaque ennemi a sa texture-palette dans `<Famille>/<Nom>_Couleur.png` (avec "
                "`_Rugosite.png` et `_Metal.png`) : une case de 32 px par couleur, les UV de chaque face pointent "
                "au centre de sa case. Elle est aussi incluse dans les FBX et dans les .blend.\n\n"
                "Les fichiers `Palette_<Type>.png` sont des nuanciers de référence (une case de 64 px par rôle, "
                "dans l'ordre) pour recréer les matériaux dans un moteur :\n\n"
                + " · ".join(f"`{r}`" for r in ROLES) + "\n\n"
                "Les rôles `corps` à `joue` changent selon le type élémentaire ; `or`, `sable`, `ocre`, `cuir`, "
                "`turquoise`, `terre` sont communs à tout le monde 2 (identité désert).\n")

    rows, sections = [], []
    for mod, elems in FAMS:
        fam = importlib.import_module("desert." + mod).FAMILY
        acts = fam.actions()
        act_txt = ", ".join(f"`{s}` ({n} im.{', boucle' if loop else ''})" for s, n, _, loop in acts)
        doc = (importlib.import_module("desert." + mod).__doc__ or "").strip().split("\n\n")
        sections.append(f"### {fam.label} — PV {fam.pv}\n\n" + "\n\n".join(doc[1:2]).replace("\n", " ") +
                        f"\n\nActions : {act_txt}.\n")
        for e in elems:
            if fam.boss_file:
                stem = fam.boss_file
                blend, fbx, prev = f"Blender/{stem}.blend", f"FBX/{stem}.fbx", f"Previews/{stem}"
            else:
                blend, fbx = f"Blender/{fam.key}/{e}.blend", f"FBX/{fam.key}/{e}.fbx"
                prev = f"Previews/{fam.key}/{e}"
            rows.append(f"| {fam.label} {ELEMENTS[e]['label'] if not fam.boss_file else '(Plante)'} | "
                        f"{ELEMENTS[e]['label']} | {fam.pv} | [`.blend`]({blend}) · [`.fbx`]({fbx}) | "
                        f"[vues]({prev}.jpg) · [anim]({prev}_anim.jpg) |")
            sections.append(f"![{fam.short} {e}]({prev}.jpg)\n")
        sections.append("")

    gal = []
    for key in ("Ballon_Cactus", "Ballon_Pyramide", "Dirigeable_Desert"):
        gal.append(" ".join(f"<img src=\"Previews/{key}/{e}.jpg\" width=\"24%\">" for e in ORDER[:4]))
        gal.append(" ".join(f"<img src=\"Previews/{key}/{e}.jpg\" width=\"24%\">" for e in ORDER[4:]))

    text = f"""# Monde 2 — Le Désert des Ballons Perdus

23 ennemis gonflables (cartoon 3D, plastique brillant, coutures, valves) : 3 familles × 7 types élémentaires,
le mini-boss **Scaraballon** et le boss final **Grand Ballon Oasis**. Chaque ennemi est un modèle indépendant
(1 armature + 1 maillage skinné à matériau unique), avec 2 animations : **Fly** (vol, en boucle) et **Hit**
(coup reçu). Le contrôle automatique des 23 FBX est dans [VERIFICATION.md](VERIFICATION.md).

## Fichiers

```
World_2_Desert/
  Blender/<Famille>/<Type>.blend        21 mobs (+ MiniBoss_..., Boss_... à la racine)
  Blender/_References/                  géométrie de référence de chaque famille (palette neutre)
  FBX/<Famille>/<Type>.fbx              mêmes chemins, un FBX par ennemi
  Textures/<Famille>/<Nom>_*.png        texture-palette de chaque ennemi (couleur, rugosité, métal)
  Previews/<Famille>/<Type>.jpg         4 vues (3/4 avant, face, profil, 3/4 arrière)
  Previews/<Famille>/<Type>_anim.jpg    images clés des actions
  Roblox/                               version prête pour Roblox Studio (voir Roblox/README.md)
```

**Roblox** : utilise le dossier [Roblox/](Roblox/README.md) : un FBX modèle + un FBX par animation (sans
échelle d'os), une texture-palette par ennemi, notice d'import.

| Ennemi | Type | PV | Fichiers | Aperçus |
|---|---|---|---|---|
""" + "\n".join(rows) + f"""

## Conventions techniques

- **Unités** : mètres. **Haut** : +Z. **Avant : +Y** (le visage regarde +Y). **Pivot** : os `Root` au sol,
  sous l'ennemi (les volants planent au-dessus : dirigeables à 1,5 m, boss à 7 m).
- **Rig** : os orientés comme le monde (pointant vers +Y, roll 0) ; `Root` porte le déplacement global.
  Hiérarchie typique : `Root > Body > Body_Mid > Body_Top` (+ membres, `FX` = décor élémentaire posé au
  sommet). Dirigeables : `Root > Hover > Envelope > Env_Front / Env_Back`, `Prop` (hélice), `Gondola`.
- **Animations** : 2 actions indépendantes par ennemi, `<Famille>_<Type>_Fly` (vol en boucle : le ballon
  flotte, se balance, ses membres et sa ficelle suivent ; les cactus, pyramides et le scarabée s'élèvent
  au-dessus du sol, le scarabée bat des ailes ; les dirigeables avancent hélices en route) et
  `<Famille>_<Type>_Hit` (recul, secousse, retour). 30 im/s, tous les os keyés à chaque image, **positions
  et rotations seulement, aucune échelle d'os** (compatible Roblox). Boucle Fly : image N+1 = image 1.
- **Pas de shape keys** (non prises en charge hors tête sur Roblox), pas de caméra ni de contrainte.
- **Couleurs** : un seul matériau par ennemi, piloté par une texture-palette (une case par couleur
  d'origine : corps, coutures, or, sable, turquoise...) incluse dans le FBX et fournie en PNG dans
  `Textures/` ; les mêmes couleurs sont aussi en couleurs de sommets. Cartes de rugosité et de métal
  assorties. Motifs (hiéroglyphes, dunes, rayures) en vraie géométrie.
- **Budget polygones : 20 000 triangles maximum par ennemi** (boss compris), contrôlé par `verify_fbx.py` :
  mobs ~10,5 à 14 k triangles, mini-boss ~17 k, boss ~19,5 k (détail du nombre exact dans VERIFICATION.md).
- **Yeux collés au corps** : chaque sommet du visage (yeux, pupilles, sourcils, bouche) reprend les poids
  du sommet de peau le plus proche : le visage suit exactement la surface du ballon dans toutes les poses.
- **Rien autour des ballons** : pas de particules en orbite ni d'accessoires flottants ; seuls les éléments
  fixés au ballon (décor élémentaire planté au sommet, emblèmes, valve, ficelle, nacelle, palmiers...).
- **Ficelles de ballon** : nœud de gonflage + ficelle portée par une chaîne `String<i>_1..3`, animée en
  mouvement secondaire (pend sous le ballon en vol, ondule, sursaute au coup reçu).
- **Export FBX** : sélection armature + maillage, « All Actions » (une prise par action), os déformants
  seulement, sans os feuilles, échelle `FBX_SCALE_UNITS` (1 unité = 1 m dans Unity), axes par défaut de
  Blender (-Z avant / Y haut côté FBX), propriétés personnalisées incluses (`PV`, `Element`, `Famille`).
  Maillage triangulé, texture-palette incluse dans le fichier.
- **Régénérer** : `blender -b --factory-startup --python-exit-code 1 -P models/monde2-desert/export_all.py`
  (options `--only cactus,pyramide,dirigeable,scaraballon,oasis`, `--elements Feu,Eau`, `--no-render`), puis
  `verify_fbx.py` et `make_docs.py`.

## Les types élémentaires

| Type | Corps | Décor planté au sommet (os `FX`) | Emblème en relief |
|---|---|---|---|
| Lumière | ivoire / jaune / or | étoile dorée et anneau-halo posé | soleil rayonnant |
| Ténèbres | violet / noir | colonne de fumée et lune violette | croissant + œil |
| Glace | bleu clair / blanc | grappe de cristaux | flocon |
| Feu | rouge / orange | flamme + cœur jaune | flamme |
| Eau | bleu / turquoise | goutte d'eau | vagues (signe « eau ») |
| Plante | vert / vert clair | fleur de cactus et feuilles | feuille nervurée |
| Éclair | jaune / bleu électrique | éclair | éclair |

## Galerie

""" + "\n\n".join(gal) + "\n\n## Familles et boss\n\n" + "\n".join(sections)
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("[docs] OK")


if __name__ == "__main__":
    main()
