# Atelier Blender headless

Ce repo sert à créer des modèles 3D avec Blender **sans écran ni GPU**, dans une session Claude Code cloud.
L'utilisateur décrit un objet ; tu écris un script Python `bpy` qui le construit, tu le génères, tu regardes
les rendus, tu corriges, puis, **seulement avec l'accord explicite de l'utilisateur**, tu pousses le
résultat (fichiers + screenshots) sur une branche `model/<nom>` dédiée à l'objet (voir la section Git).
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

0. Choisir `<nom>` (kebab-case, court, ex. `lampe-bureau`) et se placer sur la branche
   `model/<nom>` **avant d'écrire le moindre fichier** (voir la section Git).
1. Créer `models/<nom>/build.py`. Ce script construit tout le
   modèle à partir d'une scène vide, sans la nettoyer au préalable. Sa docstring décrit le modèle en 1-3
   phrases et se retrouve dans le README du modèle.
   Conventions : unités en mètres, Z vers le haut, l'avant du modèle tourné vers -Y, posé sur Z = 0.
2. Générer :
   ```bash
   bash tools/build.sh models/<nom>
   ```
   Donner un timeout Bash de 600000 ms, car le rendu CPU peut être long. Cela produit :
   - `models/<nom>/<nom>.blend` : le fichier Blender
   - `models/<nom>/screenshots/{iso,front,right,top}.jpg` et `preview.jpg` (grille 2×2 : iso | front / right | top)
   - `models/<nom>/README.md` : aperçu, dimensions, stats (généré, ne pas l'éditer à la main)
3. **Regarder** `models/<nom>/screenshots/preview.jpg` avec l'outil Read, et les vues individuelles pour
   les détails. Vérifier proportions, matériaux, pièces manquantes ou qui se chevauchent. Corriger
   `build.py` et régénérer tant que le résultat ne correspond pas à la demande.
4. Quand le résultat est bon : décrire les rendus à l'utilisateur et lui demander s'il veut pousser.
   **Ne jamais pousser sans réponse explicite** (voir « Push : seulement sur accord » plus bas). Sans
   accord, tout reste en local.

Options de `tools/build.sh` :

- `--samples N` : 32 par défaut.
- `--width W --height H` : 800×600 par vue par défaut.
- `--views` : parmi `iso,iso_back,front,back,right,left,top`.
- `--no-render` : pas de screenshots.

Pas d'export `.glb`, `.fbx` ou autre : l'utilisateur ne veut que le `.blend`.

Pour itérer vite : `--samples 8 --width 480 --height 360`. Garder les valeurs par défaut pour la version
proposée au push.

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

## Git : une branche par objet

**Demande explicite de l'utilisateur** : chaque objet vit sur une branche au nom lisible `model/<nom>`
(même `<nom>` que le dossier `models/<nom>`). Ne pas pousser sur la branche automatique de la session
(`claude/<nom-aléatoire>`), ni sur `main`. Le proxy GitHub de la session autorise le push vers une autre
branche.

- **Nouvel objet** : avant d'écrire des fichiers, partir de `main` :
  ```bash
  git ls-remote --heads origin model/<nom>   # doit être vide, sinon choisir un autre <nom>
  git fetch origin main
  git checkout -b model/<nom> FETCH_HEAD
  ```
- **Retouche d'un objet existant** (la branche `model/<nom>` existe déjà sur origin) : continuer dessus.
  ```bash
  git fetch origin model/<nom>
  git checkout -B model/<nom> FETCH_HEAD
  ```
- **Plusieurs objets dans la même session** : une branche par objet, chacune partant de `main`. Avant de
  quitter un objet dont le travail n'est pas poussé, demander à l'utilisateur s'il veut le pousser. Sinon,
  faire un commit local sur sa branche, sans pousser, avant de changer de branche :
  `git add models/<nom> && git commit -m "<nom> : en cours (non poussé)"`.
- Aucun fichier de plus de 50 Mo (GitHub refuse au-delà de 100 Mo). Si un fichier est trop gros, réduire
  la géométrie : moins de segments, moins de subdivisions.

### Push : seulement sur accord explicite

**Demande explicite de l'utilisateur** : ne pas pousser en boucle. Chaque push ajoute au dépôt un `.blend`
et des images que Git compresse mal, et qui restent dans l'historique.

- **Pendant les itérations** : ne pas committer. Les fichiers restent dans la copie de travail.
- **Quand le résultat est bon** : l'utilisateur ne voit pas les rendus avant le push. Lui décrire ce qu'ils
  montrent (proportions, matériaux, défauts éventuels restants), puis demander « Je pousse sur
  `model/<nom>` ? ». Attendre une réponse explicite (« oui », « pousse », etc.).
- **Un accord vaut pour un seul push**, sauf si l'utilisateur dit explicitement qu'il vaut pour la suite
  de la session. Une nouvelle retouche demande un nouvel accord.
- **Après accord**, un seul commit par push :
  ```bash
  git add models/<nom>
  git commit -m "<nom> : <ce qui a changé>"
  git push -u origin model/<nom>
  ```
  Si la branche a déjà un commit local non poussé (cas du changement d'objet ci-dessus), le compléter avec
  `git commit --amend` au lieu d'en créer un second.
- `git push` est en `ask` dans `.claude/settings.json` : une demande de permission s'affiche aussi. C'est
  un filet de sécurité, pas un remplacement de la question dans la conversation.
- **Rappel** : la VM cloud est éphémère, et ce qui n'est pas poussé est perdu à la fin de la session.
  Tant qu'il reste du travail non poussé, le rappeler en une ligne à la fin de chaque réponse.

### Message de fin d'itération

- ce qui a été fait ;
- les dimensions ;
- le nom de la branche (`model/<nom>`) ;
- si c'est poussé : le lien GitHub vers le README du modèle, qui affiche les screenshots :
  `https://github.com/Gregoire-W/blender-cloud-session/blob/model/<nom>/models/<nom>/README.md` ;
- sinon : préciser que rien n'est poussé et demander si l'utilisateur veut pousser. Ne pas donner le lien,
  qui ne fonctionne pas avant le push.

## Outils du repo

Ne pas modifier `tools/` pour un modèle particulier. Si un outil a un bug, le corriger et le signaler.
