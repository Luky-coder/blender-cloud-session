# Monde 2 — Le Désert des Ballons Perdus

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
| Ballon Cactus Lumière | Lumière | 35 | [`.blend`](Blender/Ballon_Cactus/Lumiere.blend) · [`.fbx`](FBX/Ballon_Cactus/Lumiere.fbx) | [vues](Previews/Ballon_Cactus/Lumiere.jpg) · [anim](Previews/Ballon_Cactus/Lumiere_anim.jpg) |
| Ballon Cactus Ténèbres | Ténèbres | 35 | [`.blend`](Blender/Ballon_Cactus/Tenebres.blend) · [`.fbx`](FBX/Ballon_Cactus/Tenebres.fbx) | [vues](Previews/Ballon_Cactus/Tenebres.jpg) · [anim](Previews/Ballon_Cactus/Tenebres_anim.jpg) |
| Ballon Cactus Glace | Glace | 35 | [`.blend`](Blender/Ballon_Cactus/Glace.blend) · [`.fbx`](FBX/Ballon_Cactus/Glace.fbx) | [vues](Previews/Ballon_Cactus/Glace.jpg) · [anim](Previews/Ballon_Cactus/Glace_anim.jpg) |
| Ballon Cactus Feu | Feu | 35 | [`.blend`](Blender/Ballon_Cactus/Feu.blend) · [`.fbx`](FBX/Ballon_Cactus/Feu.fbx) | [vues](Previews/Ballon_Cactus/Feu.jpg) · [anim](Previews/Ballon_Cactus/Feu_anim.jpg) |
| Ballon Cactus Eau | Eau | 35 | [`.blend`](Blender/Ballon_Cactus/Eau.blend) · [`.fbx`](FBX/Ballon_Cactus/Eau.fbx) | [vues](Previews/Ballon_Cactus/Eau.jpg) · [anim](Previews/Ballon_Cactus/Eau_anim.jpg) |
| Ballon Cactus Plante | Plante | 35 | [`.blend`](Blender/Ballon_Cactus/Plante.blend) · [`.fbx`](FBX/Ballon_Cactus/Plante.fbx) | [vues](Previews/Ballon_Cactus/Plante.jpg) · [anim](Previews/Ballon_Cactus/Plante_anim.jpg) |
| Ballon Cactus Éclair | Éclair | 35 | [`.blend`](Blender/Ballon_Cactus/Eclair.blend) · [`.fbx`](FBX/Ballon_Cactus/Eclair.fbx) | [vues](Previews/Ballon_Cactus/Eclair.jpg) · [anim](Previews/Ballon_Cactus/Eclair_anim.jpg) |
| Ballon Pyramide Lumière | Lumière | 45 | [`.blend`](Blender/Ballon_Pyramide/Lumiere.blend) · [`.fbx`](FBX/Ballon_Pyramide/Lumiere.fbx) | [vues](Previews/Ballon_Pyramide/Lumiere.jpg) · [anim](Previews/Ballon_Pyramide/Lumiere_anim.jpg) |
| Ballon Pyramide Ténèbres | Ténèbres | 45 | [`.blend`](Blender/Ballon_Pyramide/Tenebres.blend) · [`.fbx`](FBX/Ballon_Pyramide/Tenebres.fbx) | [vues](Previews/Ballon_Pyramide/Tenebres.jpg) · [anim](Previews/Ballon_Pyramide/Tenebres_anim.jpg) |
| Ballon Pyramide Glace | Glace | 45 | [`.blend`](Blender/Ballon_Pyramide/Glace.blend) · [`.fbx`](FBX/Ballon_Pyramide/Glace.fbx) | [vues](Previews/Ballon_Pyramide/Glace.jpg) · [anim](Previews/Ballon_Pyramide/Glace_anim.jpg) |
| Ballon Pyramide Feu | Feu | 45 | [`.blend`](Blender/Ballon_Pyramide/Feu.blend) · [`.fbx`](FBX/Ballon_Pyramide/Feu.fbx) | [vues](Previews/Ballon_Pyramide/Feu.jpg) · [anim](Previews/Ballon_Pyramide/Feu_anim.jpg) |
| Ballon Pyramide Eau | Eau | 45 | [`.blend`](Blender/Ballon_Pyramide/Eau.blend) · [`.fbx`](FBX/Ballon_Pyramide/Eau.fbx) | [vues](Previews/Ballon_Pyramide/Eau.jpg) · [anim](Previews/Ballon_Pyramide/Eau_anim.jpg) |
| Ballon Pyramide Plante | Plante | 45 | [`.blend`](Blender/Ballon_Pyramide/Plante.blend) · [`.fbx`](FBX/Ballon_Pyramide/Plante.fbx) | [vues](Previews/Ballon_Pyramide/Plante.jpg) · [anim](Previews/Ballon_Pyramide/Plante_anim.jpg) |
| Ballon Pyramide Éclair | Éclair | 45 | [`.blend`](Blender/Ballon_Pyramide/Eclair.blend) · [`.fbx`](FBX/Ballon_Pyramide/Eclair.fbx) | [vues](Previews/Ballon_Pyramide/Eclair.jpg) · [anim](Previews/Ballon_Pyramide/Eclair_anim.jpg) |
| Dirigeable du Désert Lumière | Lumière | 55 | [`.blend`](Blender/Dirigeable_Desert/Lumiere.blend) · [`.fbx`](FBX/Dirigeable_Desert/Lumiere.fbx) | [vues](Previews/Dirigeable_Desert/Lumiere.jpg) · [anim](Previews/Dirigeable_Desert/Lumiere_anim.jpg) |
| Dirigeable du Désert Ténèbres | Ténèbres | 55 | [`.blend`](Blender/Dirigeable_Desert/Tenebres.blend) · [`.fbx`](FBX/Dirigeable_Desert/Tenebres.fbx) | [vues](Previews/Dirigeable_Desert/Tenebres.jpg) · [anim](Previews/Dirigeable_Desert/Tenebres_anim.jpg) |
| Dirigeable du Désert Glace | Glace | 55 | [`.blend`](Blender/Dirigeable_Desert/Glace.blend) · [`.fbx`](FBX/Dirigeable_Desert/Glace.fbx) | [vues](Previews/Dirigeable_Desert/Glace.jpg) · [anim](Previews/Dirigeable_Desert/Glace_anim.jpg) |
| Dirigeable du Désert Feu | Feu | 55 | [`.blend`](Blender/Dirigeable_Desert/Feu.blend) · [`.fbx`](FBX/Dirigeable_Desert/Feu.fbx) | [vues](Previews/Dirigeable_Desert/Feu.jpg) · [anim](Previews/Dirigeable_Desert/Feu_anim.jpg) |
| Dirigeable du Désert Eau | Eau | 55 | [`.blend`](Blender/Dirigeable_Desert/Eau.blend) · [`.fbx`](FBX/Dirigeable_Desert/Eau.fbx) | [vues](Previews/Dirigeable_Desert/Eau.jpg) · [anim](Previews/Dirigeable_Desert/Eau_anim.jpg) |
| Dirigeable du Désert Plante | Plante | 55 | [`.blend`](Blender/Dirigeable_Desert/Plante.blend) · [`.fbx`](FBX/Dirigeable_Desert/Plante.fbx) | [vues](Previews/Dirigeable_Desert/Plante.jpg) · [anim](Previews/Dirigeable_Desert/Plante_anim.jpg) |
| Dirigeable du Désert Éclair | Éclair | 55 | [`.blend`](Blender/Dirigeable_Desert/Eclair.blend) · [`.fbx`](FBX/Dirigeable_Desert/Eclair.fbx) | [vues](Previews/Dirigeable_Desert/Eclair.jpg) · [anim](Previews/Dirigeable_Desert/Eclair_anim.jpg) |
| Le Scaraballon (mini-boss) (Plante) | Plante | 450 | [`.blend`](Blender/MiniBoss_Scaraballon_Plante.blend) · [`.fbx`](FBX/MiniBoss_Scaraballon_Plante.fbx) | [vues](Previews/MiniBoss_Scaraballon_Plante.jpg) · [anim](Previews/MiniBoss_Scaraballon_Plante_anim.jpg) |
| Le Grand Ballon Oasis (boss final) (Plante) | Plante | 1800 | [`.blend`](Blender/Boss_Grand_Ballon_Oasis_Plante.blend) · [`.fbx`](FBX/Boss_Grand_Ballon_Oasis_Plante.fbx) | [vues](Previews/Boss_Grand_Ballon_Oasis_Plante.jpg) · [anim](Previews/Boss_Grand_Ballon_Oasis_Plante_anim.jpg) |

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
- **Budget polygones : 20 000 triangles maximum par ennemi** (boss compris), contrôlé par `verify_fbx.py` :
  mobs ~10,5 à 14 k triangles, mini-boss ~17 k, boss ~19,5 k (détail du nombre exact dans VERIFICATION.md).
- **Yeux animés** : os `Eye_L/R` (clignement, plissement, yeux écarquillés ; `_L` = côté +X), `Pupil_L/R`
  (regard, dilatation) et `Brow_L/R` (sourcils levés / froncés). Idle : saccades du regard et clignements ;
  Move : regard concentré ; attaques : yeux plissés puis effort à l'impact ; Hit : yeux fermés de douleur puis
  écarquillés ; Death : regard choqué, pupilles qui tournent (étourdi), yeux qui se ferment.
- **Ficelles de ballon** : nœud de gonflage + ficelle portée par une chaîne `String<i>_1..3`, animée en
  mouvement secondaire (ondule, traîne, fouette, retombe).
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

<img src="Previews/Ballon_Cactus/Lumiere.jpg" width="24%"> <img src="Previews/Ballon_Cactus/Tenebres.jpg" width="24%"> <img src="Previews/Ballon_Cactus/Glace.jpg" width="24%"> <img src="Previews/Ballon_Cactus/Feu.jpg" width="24%">

<img src="Previews/Ballon_Cactus/Eau.jpg" width="24%"> <img src="Previews/Ballon_Cactus/Plante.jpg" width="24%"> <img src="Previews/Ballon_Cactus/Eclair.jpg" width="24%">

<img src="Previews/Ballon_Pyramide/Lumiere.jpg" width="24%"> <img src="Previews/Ballon_Pyramide/Tenebres.jpg" width="24%"> <img src="Previews/Ballon_Pyramide/Glace.jpg" width="24%"> <img src="Previews/Ballon_Pyramide/Feu.jpg" width="24%">

<img src="Previews/Ballon_Pyramide/Eau.jpg" width="24%"> <img src="Previews/Ballon_Pyramide/Plante.jpg" width="24%"> <img src="Previews/Ballon_Pyramide/Eclair.jpg" width="24%">

<img src="Previews/Dirigeable_Desert/Lumiere.jpg" width="24%"> <img src="Previews/Dirigeable_Desert/Tenebres.jpg" width="24%"> <img src="Previews/Dirigeable_Desert/Glace.jpg" width="24%"> <img src="Previews/Dirigeable_Desert/Feu.jpg" width="24%">

<img src="Previews/Dirigeable_Desert/Eau.jpg" width="24%"> <img src="Previews/Dirigeable_Desert/Plante.jpg" width="24%"> <img src="Previews/Dirigeable_Desert/Eclair.jpg" width="24%">

## Familles et boss

### Ballon Cactus — PV 35

Cactus-saguaro gonflable posé dans un pot gonflable en terre cuite : 8 fuseaux pincés par des coutures, deux bras coudés, touffes d'épines arrondies sur les crêtes, bandana d'explorateur rayé, valve dorée. Hauteur ~1,7 m (couronne élémentaire comprise), avant vers +Y, pivot au sol.

Actions : `Idle` (60 im., boucle), `Move` (30 im., boucle), `Attack` (40 im.), `Hit` (20 im.), `Death` (60 im.).

![Cactus Lumiere](Previews/Ballon_Cactus/Lumiere.jpg)

![Cactus Tenebres](Previews/Ballon_Cactus/Tenebres.jpg)

![Cactus Glace](Previews/Ballon_Cactus/Glace.jpg)

![Cactus Feu](Previews/Ballon_Cactus/Feu.jpg)

![Cactus Eau](Previews/Ballon_Cactus/Eau.jpg)

![Cactus Plante](Previews/Ballon_Cactus/Plante.jpg)

![Cactus Eclair](Previews/Ballon_Cactus/Eclair.jpg)


### Ballon Pyramide — PV 45

Pyramide gonflable à base carrée arrondie : quatre panneaux bombés, assises de « pierres » marquées par des coutures (horizontales, joints décalés, arêtes), frise de dunes sur l'assise basse, hiéroglyphes en relief sur les trois autres faces, pyramidion doré, quatre pieds-coussins et une petite valve. Base ~1,6 m, hauteur ~1,65 m (pyramidion compris), avant (visage) vers +Y, pivot au sol.

Actions : `Idle` (60 im., boucle), `Move` (30 im., boucle), `Attack` (40 im.), `Hit` (20 im.), `Death` (60 im.).

![Pyramide Lumiere](Previews/Ballon_Pyramide/Lumiere.jpg)

![Pyramide Tenebres](Previews/Ballon_Pyramide/Tenebres.jpg)

![Pyramide Glace](Previews/Ballon_Pyramide/Glace.jpg)

![Pyramide Feu](Previews/Ballon_Pyramide/Feu.jpg)

![Pyramide Eau](Previews/Ballon_Pyramide/Eau.jpg)

![Pyramide Plante](Previews/Ballon_Pyramide/Plante.jpg)

![Pyramide Eclair](Previews/Ballon_Pyramide/Eclair.jpg)


### Dirigeable du Désert — PV 55

Petit dirigeable-jouet gonflable : enveloppe allongée à 8 fuseaux cousus, bandes de tissu désertique (rayures et losanges berbères), visage sur le nez, 4 ailerons gonflables, hélice arrière dorée, nacelle gonflable tressée suspendue par 4 cordages, sacs de sable, longue-vue d'explorateur et fanion. Longueur ~2,9 m, vol stationnaire à 1,5 m (centre de l'enveloppe), avant vers +Y, pivot au sol.

Actions : `Idle` (60 im., boucle), `Move` (30 im., boucle), `Attack` (40 im.), `Hit` (20 im.), `Death` (70 im.).

![Dirigeable Lumiere](Previews/Dirigeable_Desert/Lumiere.jpg)

![Dirigeable Tenebres](Previews/Dirigeable_Desert/Tenebres.jpg)

![Dirigeable Glace](Previews/Dirigeable_Desert/Glace.jpg)

![Dirigeable Feu](Previews/Dirigeable_Desert/Feu.jpg)

![Dirigeable Eau](Previews/Dirigeable_Desert/Eau.jpg)

![Dirigeable Plante](Previews/Dirigeable_Desert/Plante.jpg)

![Dirigeable Eclair](Previews/Dirigeable_Desert/Eclair.jpg)


### Le Scaraballon (mini-boss) — PV 450

Énorme scarabée entièrement gonflable : grande carapace verte à élytres côtelés et bordure dorée, pronotum doré, tête expressive, deux antennes à bourgeons, deux ailes-feuilles décoratives, six pattes gonflables à genouillères dorées, motifs végétaux dorés et gemmes turquoise sur la carapace, pousses et fleur au sommet. Trois racines-accessoires (cachées) servent à l'attaque « Racines ». Longueur ~3,3 m, hauteur ~2 m, avant vers +Y, pivot au sol. Actions : Idle, Move, Attack (charge frontale), Hit, Death, Attack_Roll (boule qui roule), Attack_Roots (racines qui surgissent du sol).

Actions : `Idle` (60 im., boucle), `Move` (30 im., boucle), `Attack` (50 im.), `Hit` (20 im.), `Death` (80 im.), `Attack_Roll` (80 im.), `Attack_Roots` (72 im.).

![Scaraballon Plante](Previews/MiniBoss_Scaraballon_Plante.jpg)


### Le Grand Ballon Oasis (boss final) — PV 1800

Immense dirigeable gonflable portant une oasis volante : enveloppe verte à 12 fuseaux, bandes dorées et turquoise à losanges berbères, frise de hiéroglyphes dorés, visage de boss sur le nez ; sur le dos, une île de sable aux rides de dunes avec un bassin gonflable turquoise, trois palmiers gonflables (troncs annelés, palmes, noix de coco), buissons et grande fleur ; dessous, une réserve d'eau gonflable suspendue à des cordages ; lianes feuillues pendantes ; deux nacelles-moteurs latérales et une grande hélice arrière (3 hélices) ; 4 grands ailerons. Accessoires d'attaque (cachés hors de leur action) : 3 noix de coco gonflables, une vague de sable, 2 tornades, 3 cactus gonflables qui surgissent du sol. Longueur ~15 m, centre de l'enveloppe à 7 m, avant vers +Y, pivot au sol. Actions : Idle, Move, Attack (charge éperon), Hit, Death, Attack_SandWave, Attack_Coconuts, Attack_Tornado, Attack_CactusSpawn.

Actions : `Idle` (90 im., boucle), `Move` (60 im., boucle), `Attack` (60 im.), `Hit` (24 im.), `Death` (120 im.), `Attack_SandWave` (90 im.), `Attack_Coconuts` (90 im.), `Attack_Tornado` (110 im.), `Attack_CactusSpawn` (90 im.).

![Oasis Plante](Previews/Boss_Grand_Ballon_Oasis_Plante.jpg)

