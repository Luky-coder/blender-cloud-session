# Textures

Aucune texture image n'est nécessaire : toutes les couleurs sont des matériaux Principled BSDF (couleur, rugosité, métal, vernis, émission) exportés dans les FBX, et tous les motifs (hiéroglyphes, dunes, rayures, losanges berbères, coutures, épines) sont de la vraie géométrie ou des matériaux assignés par face.

Les fichiers `Palette_<Type>.png` sont des nuanciers de référence (une case de 64 px par rôle, dans l'ordre) pour recréer les matériaux dans un moteur :

`corps` · `corps2` · `couture` · `glyphe` · `epine` · `fx` · `fx2` · `pupille` · `joue` · `or` · `sable` · `ocre` · `cuir` · `turquoise` · `terre`

Les rôles `corps` à `joue` changent selon le type élémentaire ; `or`, `sable`, `ocre`, `cuir`, `turquoise`, `terre` sont communs à tout le monde 2 (identité désert).
