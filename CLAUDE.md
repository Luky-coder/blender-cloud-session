# Atelier Blender headless

Ce repo sert à créer des modèles 3D avec Blender **sans écran ni GPU**, dans une session Claude Code cloud.
L'utilisateur décrit un objet ; tu écris un script Python `bpy` qui le construit, tu le génères, tu regardes
les rendus, tu corriges, puis tu pousses le résultat (fichiers + screenshots) sur la branche de la session.
Réponds à l'utilisateur en français.

## Environnement

- Blender 5.2 est installé au démarrage par le hook SessionStart (`.claude/hooks/session-start.sh` →
  `scripts/setup_blender.sh`). Commande : `blender`. Vérifier avec `blender --version`.
- Si `blender` est introuvable : `bash scripts/setup_blender.sh`. Si le téléchargement échoue (403,
  host not allowed…), `download.blender.org` n'est pas autorisé dans l'accès réseau de l'environnement :
  dis-le à l'utilisateur en renvoyant vers la section Configuration du `README.md`, sans chercher de
  contournement.
- Pas de GPU : rendu **Cycles sur CPU** uniquement. Pas d'EEVEE ni de Workbench (ils ont besoin d'OpenGL).

## Workflow pour chaque modèle

1. Créer `models/<nom>/build.py` (`<nom>` en kebab-case, ex. `lampe-bureau`). Ce script construit tout le
   modèle à partir d'une scène vide, sans la nettoyer au préalable. Sa docstring décrit le modèle en 1-3
   phrases et se retrouve dans le README du modèle.
   Conventions : unités en mètres, Z vers le haut, l'avant du modèle tourné vers -Y, posé sur Z = 0.
2. Générer :
   ```bash
   bash tools/build.sh models/<nom>
   ```
   Donner un timeout Bash de 600000 ms, car le rendu CPU peut être long. Cela produit :
   - `models/<nom>/<nom>.blend` : le fichier Blender
   - `models/<nom>/<nom>.glb` : l'export glTF
   - `models/<nom>/screenshots/{iso,front,right,top}.png` et `preview.png` (grille 2×2 : iso | front / right | top)
   - `models/<nom>/README.md` : aperçu, dimensions, stats (généré, ne pas l'éditer à la main)
3. **Regarder** `models/<nom>/screenshots/preview.png` avec l'outil Read, et les vues individuelles pour
   les détails. Vérifier proportions, matériaux, pièces manquantes ou qui se chevauchent. Corriger
   `build.py` et régénérer tant que le résultat ne correspond pas à la demande.
4. Commit + push (voir plus bas), **à chaque itération montrable**, pas seulement à la fin.

Options de `tools/build.sh` :

- `--samples N` : 32 par défaut.
- `--width W --height H` : 800×600 par vue par défaut.
- `--views` : parmi `iso,iso_back,front,back,right,left,top`.
- `--no-render` et `--no-glb`.

Pour itérer vite : `--samples 8 --width 480 --height 360`. Garder les valeurs par défaut pour la version
poussée.

## Écrire `build.py`

- Exemple complet et commenté : `models/exemple-table/build.py`.
- Helpers disponibles (`tools/helpers.py`) : `from helpers import material, assign, bevel, smooth`.
  - `material(nom, (r, g, b), roughness, metallic, emission)` : Principled BSDF.
  - `assign(obj, mat)`.
  - `bevel(obj, width)` : arêtes arrondies.
  - `smooth(obj, angle)` : lissage avec arêtes vives.
- API Blender 5.x :
  - Les matériaux et mondes ont déjà leurs nœuds : ne pas toucher à `use_nodes`, qui est déprécié.
  - `use_auto_smooth` n'existe plus : utiliser `smooth()`, qui appelle `mesh.set_sharp_from_angle`.
  - En cas d'erreur d'API, lire le message et l'aide (`help(...)`, `bl_rna`) plutôt que deviner.
- `bpy.ops.mesh.primitive_*_add`, `bmesh` et les modificateurs fonctionnent en headless. Penser à
  `transform_apply(scale=True)` avant un bevel sur un objet mis à l'échelle.
- Les caméras et lumières d'aperçu sont ajoutées automatiquement pour les screenshots, sans être
  enregistrées dans le `.blend`. N'en mettre dans la scène que si l'utilisateur le demande. Si la scène a
  ses propres lumières, l'éclairage d'aperçu n'est pas ajouté.
- Matériaux procéduraux (nœuds) uniquement : pas de textures téléchargées.

## Modifier un `.blend` existant (fourni par l'utilisateur)

1. Écrire un script qui modifie la scène et termine par `bpy.ops.wm.save_mainfile()`, puis le lancer :
   `blender -b --factory-startup chemin/fichier.blend --python-exit-code 1 -P script.py`
2. Faire les screenshots :
   `blender -b --factory-startup chemin/fichier.blend -P tools/preview.py -- --out chemin/screenshots`

## Git : livrer à chaque itération

- Travailler sur la branche courante de la session ; ne jamais pousser sur `main`.
- Après chaque génération réussie et vérifiée visuellement :
  ```bash
  git add models/<nom>
  git commit -m "<nom> : <ce qui a changé>"
  git push -u origin HEAD
  ```
- Aucun fichier de plus de 50 Mo (GitHub refuse au-delà de 100 Mo). Si un fichier est trop gros, réduire
  la géométrie : moins de segments, moins de subdivisions.
- Dans le message final à l'utilisateur :
  - ce qui a été fait ;
  - les dimensions ;
  - le lien GitHub vers le README du modèle, qui affiche les screenshots :
    `https://github.com/Gregoire-W/blender-cloud-session/blob/<branche>/models/<nom>/README.md`
    (`<branche>` = `git branch --show-current`).

## Outils du repo

Ne pas modifier `tools/` pour un modèle particulier. Si un outil a un bug, le corriger et le signaler.
