# Textures

Chaque ennemi a sa texture-palette dans `<Famille>/<Nom>_Couleur.png` (avec `_Rugosite.png` et `_Metal.png`) : une case de 32 px par couleur, les UV de chaque face pointent au centre de sa case. Elle est aussi incluse dans les FBX et dans les .blend.

Les fichiers `Palette_<Type>.png` sont des nuanciers de référence (une case de 64 px par rôle, dans l'ordre) pour recréer les matériaux dans un moteur :

`corps` · `corps2` · `couture` · `glyphe` · `epine` · `fx` · `fx2` · `pupille` · `joue` · `or` · `sable` · `ocre` · `cuir` · `turquoise` · `terre`

Les rôles `corps` à `joue` changent selon le type élémentaire ; `or`, `sable`, `ocre`, `cuir`, `turquoise`, `terre` sont communs à tout le monde 2 (identité désert).
