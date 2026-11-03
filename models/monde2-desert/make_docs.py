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
        f.write("# Textures\n\nAucune texture image n'est nécessaire : toutes les couleurs sont des matériaux "
                "Principled BSDF (couleur, rugosité, métal, vernis, émission) exportés dans les FBX, et tous les "
                "motifs (hiéroglyphes, dunes, rayures, losanges berbères, coutures, épines) sont de la vraie "
                "géométrie ou des matériaux assignés par face.\n\n"
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
(1 armature + 1 maillage skinné), avec 5 animations obligatoires (Idle, Move, Attack, Hit, Death) et des
attaques spéciales pour les boss. Le contrôle automatique des 23 FBX est dans [VERIFICATION.md](VERIFICATION.md).

## Fichiers

```
World_2_Desert/
  Blender/<Famille>/<Type>.blend        21 mobs (+ MiniBoss_..., Boss_... à la racine)
  Blender/_References/                  géométrie de référence de chaque famille (palette neutre)
  FBX/<Famille>/<Type>.fbx              mêmes chemins, un FBX par ennemi
  Textures/                             nuanciers (aucune texture image n'est nécessaire)
  Previews/<Famille>/<Type>.jpg         4 vues (3/4 avant, face, profil, 3/4 arrière)
  Previews/<Famille>/<Type>_anim.jpg    images clés des actions
```

| Ennemi | Type | PV | Fichiers | Aperçus |
|---|---|---|---|---|
""" + "\n".join(rows) + f"""

## Conventions techniques

- **Unités** : mètres. **Haut** : +Z. **Avant : +Y** (le visage regarde +Y). **Pivot** : os `Root` au sol,
  sous l'ennemi (les volants planent au-dessus : dirigeables à 1,5 m, boss à 7 m).
- **Rig** : os orientés comme le monde (pointant vers +Y, roll 0) ; `Root` porte le déplacement global.
  Hiérarchie typique : `Root > Body > Body_Mid > Body_Top` (+ membres, `FX` = décor élémentaire de sommet,
  `Aura` = particules en orbite). Dirigeables : `Root > Hover > Envelope > Env_Front / Env_Back`, `Prop`
  (hélice), `Gondola`.
- **Déformation gonflable** : squash & stretch à volume constant sur les os + 2 shape keys sur le maillage :
  `Gonfle` (sur-gonflage : respiration, préparation des attaques) et `Degonfle` (ratatinement plissé de la
  mort). Les shape keys sont pilotées par des drivers lisant la position X des os de contrôle
  `CTRL_Gonfle` / `CTRL_Degonfle` (non déformants, non exportés) : chaque action ne contient que des
  courbes d'armature, et le FBX contient des blendshapes animés par prise.
- **Actions** : une action Blender indépendante par animation (`<Famille>_<Type>_<Anim>`), 30 im/s,
  tous les os keyés à chaque clé. Boucles (Idle, Move) : plage 1..N, l'image N+1 égale l'image 1.
  Aucune caméra, aucune contrainte : rien ne dépend de la caméra.
- **Accessoires d'attaque des boss** (racines, noix de coco, vague, tornades, cactus) : géométrie du
  maillage portée par leurs propres os, mis à l'échelle 0,001 et repliés dans le corps hors de leur action.
- **Matériaux** : Principled BSDF (rugosité basse + vernis) par rôle ; motifs en vraie géométrie.
- **Polygones** : mobs 20 à 30 k triangles, mini-boss ~30 k, boss ~75 k.
- **Export FBX** : sélection armature + maillage, « All Actions » (une prise par action), os déformants
  seulement, sans os feuilles, échelle `FBX_SCALE_UNITS` (1 unité = 1 m dans Unity), axes par défaut de
  Blender (-Z avant / Y haut côté FBX), propriétés personnalisées incluses (`PV`, `Element`, `Famille`).
  La triangulation est laissée au moteur (l'option de triangulation de l'exporteur casse les blendshapes
  animés).
- **Régénérer** : `blender -b --factory-startup --python-exit-code 1 -P models/monde2-desert/export_all.py`
  (options `--only cactus,pyramide,dirigeable,scaraballon,oasis`, `--elements Feu,Eau`, `--no-render`), puis
  `verify_fbx.py` et `make_docs.py`.

## Les types élémentaires

| Type | Corps | Couronne (os `FX`) | Aura (os `Aura`) | Emblème en relief |
|---|---|---|---|---|
| Lumière | ivoire / jaune / or | halo doré, étoile, perles | étincelles à 4 branches | soleil rayonnant |
| Ténèbres | violet / noir | colonne de fumée, lune violette | bouffées de fumée | croissant + œil |
| Glace | bleu clair / blanc | grappe de cristaux | flocons | flocon |
| Feu | rouge / orange | flamme + cœur jaune | braises | flamme |
| Eau | bleu / turquoise | goutte et bulles | bulles | vagues (signe « eau ») |
| Plante | vert / vert clair | fleur de cactus et feuilles | feuilles | feuille nervurée |
| Éclair | jaune / bleu électrique | éclair, étincelles | mini-éclairs | éclair |

## Galerie

""" + "\n\n".join(gal) + "\n\n## Familles et boss\n\n" + "\n".join(sections)
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("[docs] OK")


if __name__ == "__main__":
    main()
