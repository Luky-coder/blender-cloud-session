# Monde 3 — import dans Roblox Studio

Version des 23 ennemis préparée pour Roblox (les FBX de `../FBX/` visent les moteurs génériques).

```
Roblox/
  Ballon_Igloo/<Type>/Ballon_Igloo_<Type>.fbx            modèle (maillage + rig + texture des couleurs intégrée)
  Ballon_Igloo/<Type>/Ballon_Igloo_<Type>_Couleurs.png   la même texture, en secours
  Ballon_Igloo/<Type>/Animations/Ballon_Igloo_<Type>_IDLE.fbx   une animation par fichier
  ... Ballon_Flocon, Dirigeable_Polaire (7 types chacun)
  Boss/MiniBoss_Pin_Gonflable_Eau/ ...                    mini-boss, type Eau, 11 animations
  Boss/Boss_Gardien_Glaciers_Glace/ ...                   boss final, type Glace, 12 animations
  Projectiles/                                            projectiles des boss (objets statiques texturés)
```

## Animations de chaque ennemi

| Fichier | Rôle | Durée | Boucle |
|---|---|---|---|
| `IDLE` | attente, flottement | 2 s | oui |
| `MOVE` | déplacement au ras du sol | 1,33 s | oui |
| `FLY` | **vol** : prend de l'altitude, virages inclinés, ficelle/racines au vent | 2 s | oui |
| `ATTACK` | attaque physique vers l'avant (recul, projection, impact, rebond, retour) | 1,2 s (boss : 1,5–1,7 s) | non |
| `HIT` | coup reçu | 0,6 s | non |
| `DEATH` | mort (s'enfonce dans la neige à la fin) | 2 s (boss : 2,7–3 s) | non |

Boss en plus : Pin (Eau) `ATTACK_PommesDePin`, `ATTACK_Racines`, `ATTACK_ChuteNeige`,
`PHASE2_Deploiement`, `IDLE_Phase2` ; Gardien (Glace) `ATTACK_VagueRacines`,
`ATTACK_GrainesExplosives`, `ATTACK_TempeteNeige`, `ATTACK_Invocation`, `PHASE2_Eveil`, `IDLE_Phase2`.

`FLY` monte le modèle de 0,4 à 1,4 m environ au-dessus de son point de départ : si ton script gère
déjà l'altitude, joue plutôt `MOVE`.

## Les couleurs

Roblox n'accepte qu'un matériau par MeshPart : toutes les couleurs d'un ennemi sont rassemblées dans
une petite **texture-palette** (une case par couleur), **intégrée dans le FBX**. À l'import, la
texture s'applique toute seule. Si une MeshPart apparaît grise ou blanche :
1. importer `<Nom>_Couleurs.png` (*Gestionnaire de ressources* → *Importer*) ;
2. coller son identifiant dans la propriété `TextureID` de chaque MeshPart de l'ennemi ;
3. laisser `Color` en blanc (255, 255, 255), sinon la couleur se multiplie avec la texture.

`Material` conseillé : `SmoothPlastic` (aspect plastique gonflable).

## Ce qui a été adapté pour Roblox

| Contrainte Roblox | Adaptation |
|---|---|
| 20 000 triangles max par maillage | Mobs allégés à 9 500 triangles (1 MeshPart) ; boss à 36 000 triangles en 2 MeshParts |
| 1 seul matériau par MeshPart | Couleurs dans une texture-palette intégrée |
| 4 os max par sommet | Poids limités à 4 et normalisés |
| Pas d'échelle d'os dans les animations | Animations recalculées en position + rotation (écrasement/étirement, clignements et rétrécissement perdus ; la mort se termine en s'enfonçant dans la neige) |
| Pas de shape keys génériques | Supprimées |
| Projectiles cachés par échelle 0 | Retirés des boss, fournis dans `Projectiles/` pour être lancés par ton script |

Avant du modèle = LookVector de Roblox (-Z). Unités : mètres (un mob fait ≈ 5 studs de haut, le
Gardien ≈ 36).

## Importer un ennemi

1. **Modèle** : onglet *Accueil* → *Importer 3D* → choisir `<Nom>.fbx`. Si la taille n'est pas
   détectée, mettre l'unité du fichier sur **mètres**. Ne pas fusionner les maillages des boss.
2. **Animations** : sélectionner le rig importé → *Éditeur d'animation* → menu `⋯` → *Importer* →
   *Depuis une animation FBX* → choisir un fichier de `Animations/`. Cocher la boucle pour `IDLE`,
   `MOVE`, `FLY`, `IDLE_Phase2`, puis **publier** l'animation pour obtenir son identifiant
   (`rbxassetid://…`). Recommencer pour chaque fichier.
3. **Jouer une animation** (script serveur dans le modèle) :

```lua
local modele = script.Parent
local controleur = modele:FindFirstChildOfClass("AnimationController") or Instance.new("AnimationController", modele)
local animator = controleur:FindFirstChildOfClass("Animator") or Instance.new("Animator", controleur)

local function charger(id, boucle)
	local anim = Instance.new("Animation")
	anim.AnimationId = "rbxassetid://" .. id
	local piste = animator:LoadAnimation(anim)
	piste.Looped = boucle
	return piste
end

local vol = charger(0000000000, true)        -- identifiant publié de FLY
local attaque = charger(0000000000, false)   -- identifiant publié de ATTACK
vol:Play()
-- attaque:Play()  quand le joueur est à portée
```

Phase 2 du Gardien (« attaques plus rapides ») : `piste:AdjustSpeed(1.4)` sur ses attaques.

## Éclats lumineux

Roblox n'importe pas l'émission des matériaux : pour le cœur du Gardien, l'étoile du Pin ou les halos
Lumière, ajouter un `PointLight` ou un `ParticleEmitter` attaché à l'os correspondant (`Coeur`,
`Etoile`, `Deco`).
