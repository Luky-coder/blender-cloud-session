# Monde 2 — export Roblox

Une version de chaque ennemi préparée pour Roblox Studio (3D Importer + Animation Editor).
Le contrôle automatique (ré-import de tous les FBX) est dans [VERIFICATION_ROBLOX.md](VERIFICATION_ROBLOX.md),
avec une planche `Apercu_Roblox.jpg` par ennemi rendue à partir des FBX ré-importés.

## Contenu d'un dossier d'ennemi

```
<Nom>.fbx                     modèle : rig + maillage skinné, 1 matériau à texture-palette incluse, <= 20 000 triangles
<Nom>_Couleur.png             texture-palette (couleurs) — aussi présente en couleurs de sommets
<Nom>_Rugosite.png            carte de rugosité (SurfaceAppearance.RoughnessMap)
<Nom>_Metal.png               carte de métal (SurfaceAppearance.MetalnessMap)
Animations/<Nom>_Fly.fbx      vol (en boucle)
Animations/<Nom>_Hit.fbx      coup reçu
Apercu_Roblox.jpg             images clés rendues depuis les FBX ré-importés
```

## Import dans Roblox Studio

1. **Modèle** : menu *Import 3D*, choisis `<Nom>.fbx` (un fichier à la fois : l'import groupé gère mal les
   maillages skinnés). Le fichier est en **mètres** : si Studio demande les dimensions du fichier, choisis
   *Meters* (un cactus fait alors environ 6 studs, le boss environ 50 studs de long). Garde les os : c'est un
   modèle riggé (os `Root` au sol sous l'ennemi, avant vers +Y de Blender).
2. **Couleurs** : la texture-palette est incluse dans le FBX et les couleurs sont aussi en couleurs de
   sommets. Si Studio affiche le modèle gris, ajoute au MeshPart une `SurfaceAppearance` avec
   `ColorMap = <Nom>_Couleur.png` (et `RoughnessMap`, `MetalnessMap`), ou mets `<Nom>_Couleur.png` dans
   `TextureID`. Laisse la couleur du MeshPart en blanc.
3. **Animations** : sélectionne le modèle, ouvre l'*Animation Editor*, menu « ⋯ » > *Import* >
   *From FBX Animation*, puis choisis `Animations/<Nom>_Fly.fbx` (coche *Loop*) et `Animations/<Nom>_Hit.fbx`.
   Publie-les et joue-les avec l'`Animator` du modèle (Humanoid ou AnimationController).

Les animations n'utilisent que des positions et rotations d'os (aucune échelle, que Roblox ne lit pas).
Le visage est pondéré comme la peau du ballon : les yeux restent collés au corps dans toutes les poses.
