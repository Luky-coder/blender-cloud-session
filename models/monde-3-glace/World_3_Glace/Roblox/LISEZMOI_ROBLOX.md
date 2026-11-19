# Monde 3 — import dans Roblox Studio

Version des 23 ennemis préparée pour Roblox (les FBX de `../FBX/` visent les moteurs génériques).

```
Roblox/
  Ballon_Igloo/<Type>/Ballon_Igloo_<Type>.fbx                    modèle (maillage + rig + couleurs de sommets)
  Ballon_Igloo/<Type>/Animations/Ballon_Igloo_<Type>_FLY.fbx      vol
  Ballon_Igloo/<Type>/Animations/Ballon_Igloo_<Type>_ATTACK.fbx   attaque
  ... Ballon_Flocon, Dirigeable_Polaire (7 types chacun)
  Boss/MiniBoss_Pin_Gonflable_Eau/ ...                    mini-boss, type Eau
  Boss/Boss_Gardien_Glaciers_Glace/ ...                   boss final, type Glace
```

## Animations de chaque ennemi

Chaque ennemi a exactement deux animations :

| Fichier | Rôle | Durée | Boucle |
|---|---|---|---|
| `FLY` | **vol** : prend de l'altitude, virages inclinés, ficelle / racines / lianes au vent, hélices à fond | 2 s | oui |
| `ATTACK` | attaque physique vers l'avant (recul, projection, impact, rebond, retour) | 1,2 s (boss : 1,5–1,7 s) | non |

`FLY` monte le modèle de 0,4 à 1,4 m environ au-dessus de son point de départ.

## Les couleurs

Roblox n'accepte qu'un matériau par MeshPart : les couleurs sont stockées **dans le FBX, sur les
sommets du maillage** (couleurs de sommets, attribut `Couleur`), que l'importeur 3D lit directement.
Les grandes enveloppes portent un **motif de montgolfière** : fuseaux verticaux qui alternent les deux
couleurs du type (ex. rouge / orange pour Feu, jaune / bleu pour Éclair), séparés par des coutures
foncées et qui convergent vers les pôles.
Pour qu'elles s'affichent correctement sur chaque MeshPart importée :
- `Color` = blanc (255, 255, 255) — la couleur de la pièce se multiplie avec les couleurs de sommets ;
- `TextureID` vide (une texture masquerait les couleurs) ;
- dans l'importeur, ne pas cocher « Ignorer les couleurs de sommets » ;
- `Material` conseillé : `SmoothPlastic` (aspect plastique gonflable).

### Aspect toile de montgolfière en un clic

Sélectionne l'ennemi importé dans l'Explorateur puis colle ceci dans la *Barre de commande* (onglet
*Affichage*) : couleurs de sommets non assombries, toile lisse légèrement satinée.

```lua
for _, p in ipairs(game:GetService("Selection"):Get()[1]:GetDescendants()) do
	if p:IsA("MeshPart") then
		p.Color = Color3.new(1, 1, 1)                -- couleurs de sommets non assombries
		p.TextureID = ""
		p.Material = Enum.Material.SmoothPlastic    -- toile lisse
		p.Reflectance = 0.04                         -- léger satiné du nylon
	end
end
```

## Ce qui a été adapté pour Roblox

| Contrainte Roblox | Adaptation |
|---|---|
| 20 000 triangles max par maillage | Modèles conçus légers (mobs ≈ 12 000 à 25 000 triangles, boss ≈ 55 000) et découpés en MeshParts de 19 000 triangles max, sans allègement automatique (motifs nets) |
| 1 seul matériau par MeshPart | Couleurs des matériaux converties en couleurs de sommets |
| 4 os max par sommet | Poids limités à 4 et normalisés |
| Pas d'échelle d'os dans les animations | Animations en position + rotation, échelle retirée partout de façon cohérente : les yeux restent collés au corps (l'écrasement/étirement et les clignements sont perdus) |
| Pas de shape keys génériques | Supprimées |
| Éléments étrangers aux boss | Projectiles et aura retirés : les boss ne contiennent que leurs propres éléments |

Avant du modèle = LookVector de Roblox (-Z). Unités : mètres (un mob fait ≈ 5 studs de haut, le
Gardien ≈ 36).

## Importer un ennemi

1. **Modèle** : onglet *Accueil* → *Importer 3D* → choisir `<Nom>.fbx`. Si la taille n'est pas
   détectée, mettre l'unité du fichier sur **mètres**. Ne pas fusionner les maillages des boss.
   Puis régler `Color` en blanc sur chaque MeshPart (voir « Les couleurs »).
2. **Animations** : sélectionner le rig importé → *Éditeur d'animation* → menu `⋯` → *Importer* →
   *Depuis une animation FBX* → choisir `…_FLY.fbx` (cocher la boucle), puis **publier** l'animation pour
   obtenir son identifiant (`rbxassetid://…`). Recommencer avec `…_ATTACK.fbx` (sans boucle).
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

Phase 2 du Gardien (« attaques plus rapides ») : `attaque:AdjustSpeed(1.4)`.

## Éclats lumineux

Roblox n'importe pas l'émission des matériaux : pour le cœur du Gardien, l'étoile du Pin ou les halos
Lumière, ajouter un `PointLight` ou un `ParticleEmitter` attaché à l'os correspondant (`Coeur`,
`Etoile`, `Deco`).
