# Vérification des FBX

Chaque FBX est réimporté dans Blender et comparé au .blend source (boîte englobante du maillage déformé à 5 instants de chaque prise) ; on contrôle aussi que les couleurs sont portées par la texture palette incrustée, les UV et les couleurs de sommets, que les yeux restent au-dessus de l'enveloppe à chaque image de chaque prise et que les pièces animées (hélices, ficelle, nacelle) restent collées au corps ; les mêmes contrôles sont refaits après une compression d'animation simulée (une clé sur 4, os par os), comme dans un moteur de jeu.

```
OK  Ballon_Classique/Eau.fbx : 5883 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Classique_Eau_Rig|Ballon_Classique_Eau_Rig|Attack, Ballon_Classique_Eau_Rig|Ballon_Classique_Eau_Rig|Death, Ballon_Classique_Eau_Rig|Ballon_Classique_Eau_Rig|Hit, Ballon_Classique_Eau_Rig|Ballon_Classique_Eau_Rig|Idle, Ballon_Classique_Eau_Rig|Ballon_Classique_Eau_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.3 mm
  Pièces détachées au repos : 0 sur 46 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.4, Move +2.4, Attack +2.3, Hit +2.4, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.64 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.12 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.27 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +2.4 mm, pièces attachées : Ficelle +0.4 mm
OK  Ballon_Classique/Eclair.fbx : 3537 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Classique_Eclair_Rig|Ballon_Classique_Eclair_Rig|Attack, Ballon_Classique_Eclair_Rig|Ballon_Classique_Eclair_Rig|Death, Ballon_Classique_Eclair_Rig|Ballon_Classique_Eclair_Rig|Hit, Ballon_Classique_Eclair_Rig|Ballon_Classique_Eclair_Rig|Idle, Ballon_Classique_Eclair_Rig|Ballon_Classique_Eclair_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.3 mm
  Pièces détachées au repos : 0 sur 30 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.4, Move +2.4, Attack +2.3, Hit +2.4, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.64 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.12 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.30 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +2.4 mm, pièces attachées : Ficelle +0.4 mm
OK  Ballon_Classique/Feu.fbx : 5305 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Classique_Feu_Rig|Ballon_Classique_Feu_Rig|Attack, Ballon_Classique_Feu_Rig|Ballon_Classique_Feu_Rig|Death, Ballon_Classique_Feu_Rig|Ballon_Classique_Feu_Rig|Hit, Ballon_Classique_Feu_Rig|Ballon_Classique_Feu_Rig|Idle, Ballon_Classique_Feu_Rig|Ballon_Classique_Feu_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.3 mm
  Pièces détachées au repos : 0 sur 41 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.4, Move +2.4, Attack +2.3, Hit +2.4, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.03 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.64 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.13 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.29 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +2.4 mm, pièces attachées : Ficelle +0.4 mm
OK  Ballon_Classique/Glace.fbx : 6655 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Classique_Glace_Rig|Ballon_Classique_Glace_Rig|Attack, Ballon_Classique_Glace_Rig|Ballon_Classique_Glace_Rig|Death, Ballon_Classique_Glace_Rig|Ballon_Classique_Glace_Rig|Hit, Ballon_Classique_Glace_Rig|Ballon_Classique_Glace_Rig|Idle, Ballon_Classique_Glace_Rig|Ballon_Classique_Glace_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.3 mm
  Pièces détachées au repos : 0 sur 127 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.4, Move +2.4, Attack +2.3, Hit +2.4, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.64 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.12 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.27 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +2.4 mm, pièces attachées : Ficelle +0.4 mm
OK  Ballon_Classique/Lumiere.fbx : 4707 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Classique_Lumiere_Rig|Ballon_Classique_Lumiere_Rig|Attack, Ballon_Classique_Lumiere_Rig|Ballon_Classique_Lumiere_Rig|Death, Ballon_Classique_Lumiere_Rig|Ballon_Classique_Lumiere_Rig|Hit, Ballon_Classique_Lumiere_Rig|Ballon_Classique_Lumiere_Rig|Idle, Ballon_Classique_Lumiere_Rig|Ballon_Classique_Lumiere_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.3 mm
  Pièces détachées au repos : 0 sur 42 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.4, Move +2.4, Attack +2.3, Hit +2.4, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.72 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.13 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.30 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +2.4 mm, pièces attachées : Ficelle +0.4 mm
OK  Ballon_Classique/Plante.fbx : 5397 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Classique_Plante_Rig|Ballon_Classique_Plante_Rig|Attack, Ballon_Classique_Plante_Rig|Ballon_Classique_Plante_Rig|Death, Ballon_Classique_Plante_Rig|Ballon_Classique_Plante_Rig|Hit, Ballon_Classique_Plante_Rig|Ballon_Classique_Plante_Rig|Idle, Ballon_Classique_Plante_Rig|Ballon_Classique_Plante_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.3 mm
  Pièces détachées au repos : 0 sur 100 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.4, Move +2.4, Attack +2.3, Hit +2.4, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.68 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.13 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.28 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +2.4 mm, pièces attachées : Ficelle +0.4 mm
OK  Ballon_Classique/Tenebres.fbx : 6103 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Classique_Tenebres_Rig|Ballon_Classique_Tenebres_Rig|Attack, Ballon_Classique_Tenebres_Rig|Ballon_Classique_Tenebres_Rig|Death, Ballon_Classique_Tenebres_Rig|Ballon_Classique_Tenebres_Rig|Hit, Ballon_Classique_Tenebres_Rig|Ballon_Classique_Tenebres_Rig|Idle, Ballon_Classique_Tenebres_Rig|Ballon_Classique_Tenebres_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.3 mm
  Pièces détachées au repos : 0 sur 73 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.4, Move +2.4, Attack +2.3, Hit +2.4, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.62 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.12 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.21 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +2.4 mm, pièces attachées : Ficelle +0.4 mm
OK  Ballon_Etoile/Eau.fbx : 7586 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Etoile_Eau_Rig|Ballon_Etoile_Eau_Rig|Attack, Ballon_Etoile_Eau_Rig|Ballon_Etoile_Eau_Rig|Death, Ballon_Etoile_Eau_Rig|Ballon_Etoile_Eau_Rig|Hit, Ballon_Etoile_Eau_Rig|Ballon_Etoile_Eau_Rig|Idle, Ballon_Etoile_Eau_Rig|Ballon_Etoile_Eau_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.7 mm
  Pièces détachées au repos : 0 sur 40 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.3, Move +1.6, Attack +0.3, Hit +1.3, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.03 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.74 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.08 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.31 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +0.3 mm, pièces attachées : Ficelle +0.7 mm
OK  Ballon_Etoile/Eclair.fbx : 5192 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Etoile_Eclair_Rig|Ballon_Etoile_Eclair_Rig|Attack, Ballon_Etoile_Eclair_Rig|Ballon_Etoile_Eclair_Rig|Death, Ballon_Etoile_Eclair_Rig|Ballon_Etoile_Eclair_Rig|Hit, Ballon_Etoile_Eclair_Rig|Ballon_Etoile_Eclair_Rig|Idle, Ballon_Etoile_Eclair_Rig|Ballon_Etoile_Eclair_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.7 mm
  Pièces détachées au repos : 0 sur 27 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.3, Move +1.6, Attack +0.3, Hit +1.3, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.03 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.76 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.09 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.34 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +0.3 mm, pièces attachées : Ficelle +0.7 mm
OK  Ballon_Etoile/Feu.fbx : 7200 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Etoile_Feu_Rig|Ballon_Etoile_Feu_Rig|Attack, Ballon_Etoile_Feu_Rig|Ballon_Etoile_Feu_Rig|Death, Ballon_Etoile_Feu_Rig|Ballon_Etoile_Feu_Rig|Hit, Ballon_Etoile_Feu_Rig|Ballon_Etoile_Feu_Rig|Idle, Ballon_Etoile_Feu_Rig|Ballon_Etoile_Feu_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.7 mm
  Pièces détachées au repos : 0 sur 38 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.3, Move +1.6, Attack +0.3, Hit +1.3, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.03 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.76 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.07 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.32 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +0.3 mm, pièces attachées : Ficelle +0.7 mm
OK  Ballon_Etoile/Glace.fbx : 8283 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Etoile_Glace_Rig|Ballon_Etoile_Glace_Rig|Attack, Ballon_Etoile_Glace_Rig|Ballon_Etoile_Glace_Rig|Death, Ballon_Etoile_Glace_Rig|Ballon_Etoile_Glace_Rig|Hit, Ballon_Etoile_Glace_Rig|Ballon_Etoile_Glace_Rig|Idle, Ballon_Etoile_Glace_Rig|Ballon_Etoile_Glace_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.7 mm
  Pièces détachées au repos : 0 sur 121 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.3, Move +1.6, Attack +0.3, Hit +1.3, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.03 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.74 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.08 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.31 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +0.3 mm, pièces attachées : Ficelle +0.7 mm
OK  Ballon_Etoile/Lumiere.fbx : 6330 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Etoile_Lumiere_Rig|Ballon_Etoile_Lumiere_Rig|Attack, Ballon_Etoile_Lumiere_Rig|Ballon_Etoile_Lumiere_Rig|Death, Ballon_Etoile_Lumiere_Rig|Ballon_Etoile_Lumiere_Rig|Hit, Ballon_Etoile_Lumiere_Rig|Ballon_Etoile_Lumiere_Rig|Idle, Ballon_Etoile_Lumiere_Rig|Ballon_Etoile_Lumiere_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.7 mm
  Pièces détachées au repos : 0 sur 38 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.3, Move +1.6, Attack +0.3, Hit +1.3, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.06 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.76 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.14 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.35 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +0.3 mm, pièces attachées : Ficelle +0.7 mm
OK  Ballon_Etoile/Plante.fbx : 7365 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Etoile_Plante_Rig|Ballon_Etoile_Plante_Rig|Attack, Ballon_Etoile_Plante_Rig|Ballon_Etoile_Plante_Rig|Death, Ballon_Etoile_Plante_Rig|Ballon_Etoile_Plante_Rig|Hit, Ballon_Etoile_Plante_Rig|Ballon_Etoile_Plante_Rig|Idle, Ballon_Etoile_Plante_Rig|Ballon_Etoile_Plante_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.8 mm
  Pièces détachées au repos : 0 sur 113 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.3, Move +1.6, Attack +0.3, Hit +1.3, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.06 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.03 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.72 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.11 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.35 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +0.3 mm, pièces attachées : Ficelle +0.8 mm
OK  Ballon_Etoile/Tenebres.fbx : 7284 sommets, 32 os (32 réimportés), 1 matériaux, prises : Ballon_Etoile_Tenebres_Rig|Ballon_Etoile_Tenebres_Rig|Attack, Ballon_Etoile_Tenebres_Rig|Ballon_Etoile_Tenebres_Rig|Death, Ballon_Etoile_Tenebres_Rig|Ballon_Etoile_Tenebres_Rig|Hit, Ballon_Etoile_Tenebres_Rig|Ballon_Etoile_Tenebres_Rig|Idle, Ballon_Etoile_Tenebres_Rig|Ballon_Etoile_Tenebres_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Ficelle +0.7 mm
  Pièces détachées au repos : 0 sur 55 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.3, Move +1.6, Attack +0.3, Hit +1.3, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.70 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.08 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.25 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +0.3 mm, pièces attachées : Ficelle +0.7 mm
OK  Boss_Zeppelin_Plante.fbx : 10795 sommets, 34 os (34 réimportés), 1 matériaux, prises : Boss_Zeppelin_Plante_Rig|Boss_Zeppelin_Plante_Rig|Attack, Boss_Zeppelin_Plante_Rig|Boss_Zeppelin_Plante_Rig|Death, Boss_Zeppelin_Plante_Rig|Boss_Zeppelin_Plante_Rig|Hit, Boss_Zeppelin_Plante_Rig|Boss_Zeppelin_Plante_Rig|Idle, Boss_Zeppelin_Plante_Rig|Boss_Zeppelin_Plante_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Helice_ArD +12.0 mm, Helice_ArG +6.0 mm, Helice_AvD +0.0 mm, Helice_AvG +12.0 mm, Helice_Queue +12.5 mm
  Pièces détachées au repos : 0 sur 237 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +8.6, Move +12.8, Attack +0.9, Hit +9.3, Death +0.0
  Idle: 120 images (source 120), écart max 0.0 mm, déplacement max 0.18 m, taille fin/début 1.00
  Move: 60 images (source 60), écart max 0.0 mm, déplacement max 0.10 m, taille fin/début 1.00
  Attack: 72 images (source 72), écart max 0.0 mm, déplacement max 3.11 m, taille fin/début 1.00
  Hit: 30 images (source 30), écart max 0.0 mm, déplacement max 0.65 m, taille fin/début 1.00
  Death: 110 images (source 110), écart max 0.0 mm, déplacement max 2.22 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +0.9 mm, pièces attachées : Helice_ArD +9.7 mm, Helice_ArG +6.0 mm, Helice_AvD +0.0 mm, Helice_AvG +11.6 mm, Helice_Queue +12.5 mm
OK  MiniBoss_Montgolfiere_Plante.fbx : 11166 sommets, 30 os (30 réimportés), 1 matériaux, prises : MiniBoss_Montgolfiere_Plante_Rig|MiniBoss_Montgolfiere_Plante_Rig|Attack, MiniBoss_Montgolfiere_Plante_Rig|MiniBoss_Montgolfiere_Plante_Rig|Death, MiniBoss_Montgolfiere_Plante_Rig|MiniBoss_Montgolfiere_Plante_Rig|Hit, MiniBoss_Montgolfiere_Plante_Rig|MiniBoss_Montgolfiere_Plante_Rig|Idle, MiniBoss_Montgolfiere_Plante_Rig|MiniBoss_Montgolfiere_Plante_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Nacelle +2.0 mm
  Pièces détachées au repos : 0 sur 282 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +3.1, Move +8.0, Attack -0.2, Hit +4.8, Death +0.0
  Idle: 96 images (source 96), écart max 0.0 mm, déplacement max 0.14 m, taille fin/début 1.00
  Move: 48 images (source 48), écart max 0.0 mm, déplacement max 0.06 m, taille fin/début 1.00
  Attack: 60 images (source 60), écart max 0.0 mm, déplacement max 1.50 m, taille fin/début 1.00
  Hit: 24 images (source 24), écart max 0.0 mm, déplacement max 0.33 m, taille fin/début 1.00
  Death: 90 images (source 90), écart max 0.0 mm, déplacement max 0.58 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min +0.1 mm, pièces attachées : Nacelle +1.9 mm
OK  Mini_Dirigeable/Eau.fbx : 7910 sommets, 30 os (30 réimportés), 1 matériaux, prises : Mini_Dirigeable_Eau_Rig|Mini_Dirigeable_Eau_Rig|Attack, Mini_Dirigeable_Eau_Rig|Mini_Dirigeable_Eau_Rig|Death, Mini_Dirigeable_Eau_Rig|Mini_Dirigeable_Eau_Rig|Hit, Mini_Dirigeable_Eau_Rig|Mini_Dirigeable_Eau_Rig|Idle, Mini_Dirigeable_Eau_Rig|Mini_Dirigeable_Eau_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Helice +1.3 mm
  Pièces détachées au repos : 0 sur 74 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.4, Move +1.6, Attack -0.8, Hit +0.1, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.95 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.14 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.33 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min -0.7 mm, pièces attachées : Helice +2.0 mm
OK  Mini_Dirigeable/Eclair.fbx : 5690 sommets, 30 os (30 réimportés), 1 matériaux, prises : Mini_Dirigeable_Eclair_Rig|Mini_Dirigeable_Eclair_Rig|Attack, Mini_Dirigeable_Eclair_Rig|Mini_Dirigeable_Eclair_Rig|Death, Mini_Dirigeable_Eclair_Rig|Mini_Dirigeable_Eclair_Rig|Hit, Mini_Dirigeable_Eclair_Rig|Mini_Dirigeable_Eclair_Rig|Idle, Mini_Dirigeable_Eclair_Rig|Mini_Dirigeable_Eclair_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Helice +1.3 mm
  Pièces détachées au repos : 0 sur 58 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.4, Move +1.6, Attack -0.8, Hit +0.1, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.95 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.14 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.36 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min -0.7 mm, pièces attachées : Helice +2.0 mm
OK  Mini_Dirigeable/Feu.fbx : 7424 sommets, 30 os (30 réimportés), 1 matériaux, prises : Mini_Dirigeable_Feu_Rig|Mini_Dirigeable_Feu_Rig|Attack, Mini_Dirigeable_Feu_Rig|Mini_Dirigeable_Feu_Rig|Death, Mini_Dirigeable_Feu_Rig|Mini_Dirigeable_Feu_Rig|Hit, Mini_Dirigeable_Feu_Rig|Mini_Dirigeable_Feu_Rig|Idle, Mini_Dirigeable_Feu_Rig|Mini_Dirigeable_Feu_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Helice +1.3 mm
  Pièces détachées au repos : 0 sur 70 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.4, Move +1.6, Attack -0.8, Hit +0.1, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.95 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.14 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.35 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min -0.7 mm, pièces attachées : Helice +2.0 mm
OK  Mini_Dirigeable/Glace.fbx : 7811 sommets, 30 os (30 réimportés), 1 matériaux, prises : Mini_Dirigeable_Glace_Rig|Mini_Dirigeable_Glace_Rig|Attack, Mini_Dirigeable_Glace_Rig|Mini_Dirigeable_Glace_Rig|Death, Mini_Dirigeable_Glace_Rig|Mini_Dirigeable_Glace_Rig|Hit, Mini_Dirigeable_Glace_Rig|Mini_Dirigeable_Glace_Rig|Idle, Mini_Dirigeable_Glace_Rig|Mini_Dirigeable_Glace_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Helice +1.3 mm
  Pièces détachées au repos : 0 sur 125 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.4, Move +1.6, Attack -0.8, Hit +0.1, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.95 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.14 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.33 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min -0.7 mm, pièces attachées : Helice +2.0 mm
OK  Mini_Dirigeable/Lumiere.fbx : 6478 sommets, 30 os (30 réimportés), 1 matériaux, prises : Mini_Dirigeable_Lumiere_Rig|Mini_Dirigeable_Lumiere_Rig|Attack, Mini_Dirigeable_Lumiere_Rig|Mini_Dirigeable_Lumiere_Rig|Death, Mini_Dirigeable_Lumiere_Rig|Mini_Dirigeable_Lumiere_Rig|Hit, Mini_Dirigeable_Lumiere_Rig|Mini_Dirigeable_Lumiere_Rig|Idle, Mini_Dirigeable_Lumiere_Rig|Mini_Dirigeable_Lumiere_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Helice +1.3 mm
  Pièces détachées au repos : 0 sur 68 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.4, Move +1.6, Attack -0.8, Hit +0.1, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.95 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.14 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.37 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min -0.7 mm, pièces attachées : Helice +2.0 mm
OK  Mini_Dirigeable/Plante.fbx : 7608 sommets, 30 os (30 réimportés), 1 matériaux, prises : Mini_Dirigeable_Plante_Rig|Mini_Dirigeable_Plante_Rig|Attack, Mini_Dirigeable_Plante_Rig|Mini_Dirigeable_Plante_Rig|Death, Mini_Dirigeable_Plante_Rig|Mini_Dirigeable_Plante_Rig|Hit, Mini_Dirigeable_Plante_Rig|Mini_Dirigeable_Plante_Rig|Idle, Mini_Dirigeable_Plante_Rig|Mini_Dirigeable_Plante_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Helice +1.3 mm
  Pièces détachées au repos : 0 sur 144 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.4, Move +1.6, Attack -0.8, Hit +0.1, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.95 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.14 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.34 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min -0.7 mm, pièces attachées : Helice +2.0 mm
OK  Mini_Dirigeable/Tenebres.fbx : 8080 sommets, 30 os (30 réimportés), 1 matériaux, prises : Mini_Dirigeable_Tenebres_Rig|Mini_Dirigeable_Tenebres_Rig|Attack, Mini_Dirigeable_Tenebres_Rig|Mini_Dirigeable_Tenebres_Rig|Death, Mini_Dirigeable_Tenebres_Rig|Mini_Dirigeable_Tenebres_Rig|Hit, Mini_Dirigeable_Tenebres_Rig|Mini_Dirigeable_Tenebres_Rig|Idle, Mini_Dirigeable_Tenebres_Rig|Mini_Dirigeable_Tenebres_Rig|Move
  Échelles d'os animées : aucune (hors disparition finale de Death)
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Pièces attachées (écart max au corps vs repos) : Helice +1.3 mm
  Pièces détachées au repos : 0 sur 105 morceaux (tout est fixé)
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +0.4, Move +1.6, Attack -0.8, Hit +0.1, Death +0.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.95 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.14 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.30 m, taille fin/début 0.00
  Moteur sans échelle d'os + compression (1 clé sur 4) : yeux marge min -0.7 mm, pièces attachées : Helice +2.0 mm
```
