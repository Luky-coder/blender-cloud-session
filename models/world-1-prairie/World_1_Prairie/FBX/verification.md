# Vérification des FBX

Chaque FBX est réimporté dans Blender et comparé au .blend source (boîte englobante du maillage déformé à 5 instants de chaque prise) ; on contrôle aussi que les couleurs sont portées par la texture palette incrustée, les UV et les couleurs de sommets, et que les yeux restent au-dessus de l'enveloppe à chaque image de chaque prise.

```
OK  Ballon_Classique/Eau.fbx : 5105 sommets, 27 os (27 réimportés), 11 matériaux, prises : Ballon_Classique_Eau_Rig|Ballon_Classique_Eau_Rig|Attack, Ballon_Classique_Eau_Rig|Ballon_Classique_Eau_Rig|Death, Ballon_Classique_Eau_Rig|Ballon_Classique_Eau_Rig|Hit, Ballon_Classique_Eau_Rig|Ballon_Classique_Eau_Rig|Idle, Ballon_Classique_Eau_Rig|Ballon_Classique_Eau_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.8, Move +2.9, Attack +2.5, Hit +3.3, Death +3.1
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.64 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.11 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.26 m, taille fin/début 0.03
OK  Ballon_Classique/Eclair.fbx : 2811 sommets, 27 os (27 réimportés), 11 matériaux, prises : Ballon_Classique_Eclair_Rig|Ballon_Classique_Eclair_Rig|Attack, Ballon_Classique_Eclair_Rig|Ballon_Classique_Eclair_Rig|Death, Ballon_Classique_Eclair_Rig|Ballon_Classique_Eclair_Rig|Hit, Ballon_Classique_Eclair_Rig|Ballon_Classique_Eclair_Rig|Idle, Ballon_Classique_Eclair_Rig|Ballon_Classique_Eclair_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.8, Move +2.9, Attack +2.5, Hit +3.3, Death +3.1
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.03 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.65 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.12 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.29 m, taille fin/début 0.03
OK  Ballon_Classique/Feu.fbx : 4423 sommets, 27 os (27 réimportés), 11 matériaux, prises : Ballon_Classique_Feu_Rig|Ballon_Classique_Feu_Rig|Attack, Ballon_Classique_Feu_Rig|Ballon_Classique_Feu_Rig|Death, Ballon_Classique_Feu_Rig|Ballon_Classique_Feu_Rig|Hit, Ballon_Classique_Feu_Rig|Ballon_Classique_Feu_Rig|Idle, Ballon_Classique_Feu_Rig|Ballon_Classique_Feu_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.8, Move +2.9, Attack +2.5, Hit +3.3, Death +3.1
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.07 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.03 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.65 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.12 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.28 m, taille fin/début 0.03
OK  Ballon_Classique/Glace.fbx : 4507 sommets, 27 os (27 réimportés), 11 matériaux, prises : Ballon_Classique_Glace_Rig|Ballon_Classique_Glace_Rig|Attack, Ballon_Classique_Glace_Rig|Ballon_Classique_Glace_Rig|Death, Ballon_Classique_Glace_Rig|Ballon_Classique_Glace_Rig|Hit, Ballon_Classique_Glace_Rig|Ballon_Classique_Glace_Rig|Idle, Ballon_Classique_Glace_Rig|Ballon_Classique_Glace_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.8, Move +2.9, Attack +2.5, Hit +3.3, Death +3.1
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.06 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.64 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.11 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.27 m, taille fin/début 0.03
OK  Ballon_Classique/Lumiere.fbx : 3383 sommets, 27 os (27 réimportés), 10 matériaux, prises : Ballon_Classique_Lumiere_Rig|Ballon_Classique_Lumiere_Rig|Attack, Ballon_Classique_Lumiere_Rig|Ballon_Classique_Lumiere_Rig|Death, Ballon_Classique_Lumiere_Rig|Ballon_Classique_Lumiere_Rig|Hit, Ballon_Classique_Lumiere_Rig|Ballon_Classique_Lumiere_Rig|Idle, Ballon_Classique_Lumiere_Rig|Ballon_Classique_Lumiere_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.8, Move +2.9, Attack +2.5, Hit +3.3, Death +3.1
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.09 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.63 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.13 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.31 m, taille fin/début 0.03
OK  Ballon_Classique/Plante.fbx : 4389 sommets, 27 os (27 réimportés), 13 matériaux, prises : Ballon_Classique_Plante_Rig|Ballon_Classique_Plante_Rig|Attack, Ballon_Classique_Plante_Rig|Ballon_Classique_Plante_Rig|Death, Ballon_Classique_Plante_Rig|Ballon_Classique_Plante_Rig|Hit, Ballon_Classique_Plante_Rig|Ballon_Classique_Plante_Rig|Idle, Ballon_Classique_Plante_Rig|Ballon_Classique_Plante_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.8, Move +2.9, Attack +2.5, Hit +3.3, Death +3.1
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.70 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.13 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.28 m, taille fin/début 0.03
OK  Ballon_Classique/Tenebres.fbx : 5003 sommets, 27 os (27 réimportés), 12 matériaux, prises : Ballon_Classique_Tenebres_Rig|Ballon_Classique_Tenebres_Rig|Attack, Ballon_Classique_Tenebres_Rig|Ballon_Classique_Tenebres_Rig|Death, Ballon_Classique_Tenebres_Rig|Ballon_Classique_Tenebres_Rig|Hit, Ballon_Classique_Tenebres_Rig|Ballon_Classique_Tenebres_Rig|Idle, Ballon_Classique_Tenebres_Rig|Ballon_Classique_Tenebres_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.8, Move +2.9, Attack +2.5, Hit +3.3, Death +3.1
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.06 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.68 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.11 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.19 m, taille fin/début 0.03
OK  Ballon_Etoile/Eau.fbx : 6808 sommets, 27 os (27 réimportés), 11 matériaux, prises : Ballon_Etoile_Eau_Rig|Ballon_Etoile_Eau_Rig|Attack, Ballon_Etoile_Eau_Rig|Ballon_Etoile_Eau_Rig|Death, Ballon_Etoile_Eau_Rig|Ballon_Etoile_Eau_Rig|Hit, Ballon_Etoile_Eau_Rig|Ballon_Etoile_Eau_Rig|Idle, Ballon_Etoile_Eau_Rig|Ballon_Etoile_Eau_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.9, Move +2.7, Attack +3.0, Hit +3.0, Death +3.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.67 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.08 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.30 m, taille fin/début 0.02
OK  Ballon_Etoile/Eclair.fbx : 4466 sommets, 27 os (27 réimportés), 11 matériaux, prises : Ballon_Etoile_Eclair_Rig|Ballon_Etoile_Eclair_Rig|Attack, Ballon_Etoile_Eclair_Rig|Ballon_Etoile_Eclair_Rig|Death, Ballon_Etoile_Eclair_Rig|Ballon_Etoile_Eclair_Rig|Hit, Ballon_Etoile_Eclair_Rig|Ballon_Etoile_Eclair_Rig|Idle, Ballon_Etoile_Eclair_Rig|Ballon_Etoile_Eclair_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.9, Move +2.7, Attack +3.0, Hit +3.0, Death +3.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.03 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.73 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.10 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.33 m, taille fin/début 0.02
OK  Ballon_Etoile/Feu.fbx : 6318 sommets, 27 os (27 réimportés), 11 matériaux, prises : Ballon_Etoile_Feu_Rig|Ballon_Etoile_Feu_Rig|Attack, Ballon_Etoile_Feu_Rig|Ballon_Etoile_Feu_Rig|Death, Ballon_Etoile_Feu_Rig|Ballon_Etoile_Feu_Rig|Hit, Ballon_Etoile_Feu_Rig|Ballon_Etoile_Feu_Rig|Idle, Ballon_Etoile_Feu_Rig|Ballon_Etoile_Feu_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.9, Move +2.7, Attack +3.0, Hit +3.0, Death +3.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.72 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.08 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.31 m, taille fin/début 0.02
OK  Ballon_Etoile/Glace.fbx : 6135 sommets, 27 os (27 réimportés), 11 matériaux, prises : Ballon_Etoile_Glace_Rig|Ballon_Etoile_Glace_Rig|Attack, Ballon_Etoile_Glace_Rig|Ballon_Etoile_Glace_Rig|Death, Ballon_Etoile_Glace_Rig|Ballon_Etoile_Glace_Rig|Hit, Ballon_Etoile_Glace_Rig|Ballon_Etoile_Glace_Rig|Idle, Ballon_Etoile_Glace_Rig|Ballon_Etoile_Glace_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.9, Move +2.7, Attack +3.0, Hit +3.0, Death +3.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.06 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.06 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.71 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.08 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.30 m, taille fin/début 0.02
OK  Ballon_Etoile/Lumiere.fbx : 5046 sommets, 27 os (27 réimportés), 10 matériaux, prises : Ballon_Etoile_Lumiere_Rig|Ballon_Etoile_Lumiere_Rig|Attack, Ballon_Etoile_Lumiere_Rig|Ballon_Etoile_Lumiere_Rig|Death, Ballon_Etoile_Lumiere_Rig|Ballon_Etoile_Lumiere_Rig|Hit, Ballon_Etoile_Lumiere_Rig|Ballon_Etoile_Lumiere_Rig|Idle, Ballon_Etoile_Lumiere_Rig|Ballon_Etoile_Lumiere_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.9, Move +2.7, Attack +3.0, Hit +3.0, Death +3.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.06 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.73 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.15 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.34 m, taille fin/début 0.02
OK  Ballon_Etoile/Plante.fbx : 6357 sommets, 27 os (27 réimportés), 13 matériaux, prises : Ballon_Etoile_Plante_Rig|Ballon_Etoile_Plante_Rig|Attack, Ballon_Etoile_Plante_Rig|Ballon_Etoile_Plante_Rig|Death, Ballon_Etoile_Plante_Rig|Ballon_Etoile_Plante_Rig|Hit, Ballon_Etoile_Plante_Rig|Ballon_Etoile_Plante_Rig|Idle, Ballon_Etoile_Plante_Rig|Ballon_Etoile_Plante_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.9, Move +2.7, Attack +3.0, Hit +3.0, Death +3.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.06 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.03 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.72 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.11 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.34 m, taille fin/début 0.02
OK  Ballon_Etoile/Tenebres.fbx : 6184 sommets, 27 os (27 réimportés), 12 matériaux, prises : Ballon_Etoile_Tenebres_Rig|Ballon_Etoile_Tenebres_Rig|Attack, Ballon_Etoile_Tenebres_Rig|Ballon_Etoile_Tenebres_Rig|Death, Ballon_Etoile_Tenebres_Rig|Ballon_Etoile_Tenebres_Rig|Hit, Ballon_Etoile_Tenebres_Rig|Ballon_Etoile_Tenebres_Rig|Idle, Ballon_Etoile_Tenebres_Rig|Ballon_Etoile_Tenebres_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.9, Move +2.7, Attack +3.0, Hit +3.0, Death +3.0
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.07 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Attack: 42 images (source 42), écart max 0.0 mm, déplacement max 0.65 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.09 m, taille fin/début 1.00
  Death: 60 images (source 60), écart max 0.0 mm, déplacement max 0.29 m, taille fin/début 0.02
OK  Boss_Zeppelin_Plante.fbx : 10839 sommets, 29 os (29 réimportés), 18 matériaux, prises : Boss_Zeppelin_Plante_Rig|Boss_Zeppelin_Plante_Rig|Attack, Boss_Zeppelin_Plante_Rig|Boss_Zeppelin_Plante_Rig|Death, Boss_Zeppelin_Plante_Rig|Boss_Zeppelin_Plante_Rig|Hit, Boss_Zeppelin_Plante_Rig|Boss_Zeppelin_Plante_Rig|Idle, Boss_Zeppelin_Plante_Rig|Boss_Zeppelin_Plante_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +11.9, Move +15.7, Attack +9.7, Hit +15.4, Death +12.5
  Idle: 120 images (source 120), écart max 0.0 mm, déplacement max 0.19 m, taille fin/début 1.00
  Move: 60 images (source 60), écart max 0.0 mm, déplacement max 0.09 m, taille fin/début 1.00
  Attack: 72 images (source 72), écart max 0.0 mm, déplacement max 3.03 m, taille fin/début 1.00
  Hit: 30 images (source 30), écart max 0.0 mm, déplacement max 0.68 m, taille fin/début 1.00
  Death: 110 images (source 110), écart max 0.0 mm, déplacement max 2.08 m, taille fin/début 0.03
OK  MiniBoss_Montgolfiere_Plante.fbx : 10734 sommets, 25 os (25 réimportés), 18 matériaux, prises : MiniBoss_Montgolfiere_Plante_Rig|MiniBoss_Montgolfiere_Plante_Rig|Attack, MiniBoss_Montgolfiere_Plante_Rig|MiniBoss_Montgolfiere_Plante_Rig|Death, MiniBoss_Montgolfiere_Plante_Rig|MiniBoss_Montgolfiere_Plante_Rig|Hit, MiniBoss_Montgolfiere_Plante_Rig|MiniBoss_Montgolfiere_Plante_Rig|Idle, MiniBoss_Montgolfiere_Plante_Rig|MiniBoss_Montgolfiere_Plante_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +11.8, Move +12.5, Attack +4.5, Hit +12.2, Death +6.6
  Idle: 96 images (source 96), écart max 0.0 mm, déplacement max 0.14 m, taille fin/début 1.00
  Move: 48 images (source 48), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Attack: 60 images (source 60), écart max 0.0 mm, déplacement max 1.56 m, taille fin/début 1.00
  Hit: 24 images (source 24), écart max 0.0 mm, déplacement max 0.32 m, taille fin/début 1.00
  Death: 90 images (source 90), écart max 0.0 mm, déplacement max 0.54 m, taille fin/début 0.03
OK  Mini_Dirigeable/Eau.fbx : 7256 sommets, 25 os (25 réimportés), 13 matériaux, prises : Mini_Dirigeable_Eau_Rig|Mini_Dirigeable_Eau_Rig|Attack, Mini_Dirigeable_Eau_Rig|Mini_Dirigeable_Eau_Rig|Death, Mini_Dirigeable_Eau_Rig|Mini_Dirigeable_Eau_Rig|Hit, Mini_Dirigeable_Eau_Rig|Mini_Dirigeable_Eau_Rig|Idle, Mini_Dirigeable_Eau_Rig|Mini_Dirigeable_Eau_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.1, Move +3.8, Attack +0.4, Hit +1.6, Death +0.7
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.06 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.94 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.15 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.29 m, taille fin/début 0.03
OK  Mini_Dirigeable/Eclair.fbx : 4982 sommets, 25 os (25 réimportés), 13 matériaux, prises : Mini_Dirigeable_Eclair_Rig|Mini_Dirigeable_Eclair_Rig|Attack, Mini_Dirigeable_Eclair_Rig|Mini_Dirigeable_Eclair_Rig|Death, Mini_Dirigeable_Eclair_Rig|Mini_Dirigeable_Eclair_Rig|Hit, Mini_Dirigeable_Eclair_Rig|Mini_Dirigeable_Eclair_Rig|Idle, Mini_Dirigeable_Eclair_Rig|Mini_Dirigeable_Eclair_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.1, Move +3.8, Attack +0.4, Hit +1.6, Death +0.7
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.03 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.94 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.15 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.35 m, taille fin/début 0.03
OK  Mini_Dirigeable/Feu.fbx : 6654 sommets, 25 os (25 réimportés), 13 matériaux, prises : Mini_Dirigeable_Feu_Rig|Mini_Dirigeable_Feu_Rig|Attack, Mini_Dirigeable_Feu_Rig|Mini_Dirigeable_Feu_Rig|Death, Mini_Dirigeable_Feu_Rig|Mini_Dirigeable_Feu_Rig|Hit, Mini_Dirigeable_Feu_Rig|Mini_Dirigeable_Feu_Rig|Idle, Mini_Dirigeable_Feu_Rig|Mini_Dirigeable_Feu_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.1, Move +3.8, Attack +0.4, Hit +1.6, Death +0.7
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.03 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.94 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.15 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.33 m, taille fin/début 0.03
OK  Mini_Dirigeable/Glace.fbx : 6155 sommets, 25 os (25 réimportés), 13 matériaux, prises : Mini_Dirigeable_Glace_Rig|Mini_Dirigeable_Glace_Rig|Attack, Mini_Dirigeable_Glace_Rig|Mini_Dirigeable_Glace_Rig|Death, Mini_Dirigeable_Glace_Rig|Mini_Dirigeable_Glace_Rig|Hit, Mini_Dirigeable_Glace_Rig|Mini_Dirigeable_Glace_Rig|Idle, Mini_Dirigeable_Glace_Rig|Mini_Dirigeable_Glace_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.1, Move +3.8, Attack +0.4, Hit +1.6, Death +0.7
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.94 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.15 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.31 m, taille fin/début 0.03
OK  Mini_Dirigeable/Lumiere.fbx : 5326 sommets, 25 os (25 réimportés), 13 matériaux, prises : Mini_Dirigeable_Lumiere_Rig|Mini_Dirigeable_Lumiere_Rig|Attack, Mini_Dirigeable_Lumiere_Rig|Mini_Dirigeable_Lumiere_Rig|Death, Mini_Dirigeable_Lumiere_Rig|Mini_Dirigeable_Lumiere_Rig|Hit, Mini_Dirigeable_Lumiere_Rig|Mini_Dirigeable_Lumiere_Rig|Idle, Mini_Dirigeable_Lumiere_Rig|Mini_Dirigeable_Lumiere_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.1, Move +3.8, Attack +0.4, Hit +1.6, Death +0.7
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.05 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.94 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.16 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.36 m, taille fin/début 0.03
OK  Mini_Dirigeable/Plante.fbx : 6712 sommets, 25 os (25 réimportés), 15 matériaux, prises : Mini_Dirigeable_Plante_Rig|Mini_Dirigeable_Plante_Rig|Attack, Mini_Dirigeable_Plante_Rig|Mini_Dirigeable_Plante_Rig|Death, Mini_Dirigeable_Plante_Rig|Mini_Dirigeable_Plante_Rig|Hit, Mini_Dirigeable_Plante_Rig|Mini_Dirigeable_Plante_Rig|Idle, Mini_Dirigeable_Plante_Rig|Mini_Dirigeable_Plante_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.1, Move +3.8, Attack +0.4, Hit +1.6, Death +0.7
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.04 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.94 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.15 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.32 m, taille fin/début 0.03
OK  Mini_Dirigeable/Tenebres.fbx : 7136 sommets, 25 os (25 réimportés), 15 matériaux, prises : Mini_Dirigeable_Tenebres_Rig|Mini_Dirigeable_Tenebres_Rig|Attack, Mini_Dirigeable_Tenebres_Rig|Mini_Dirigeable_Tenebres_Rig|Death, Mini_Dirigeable_Tenebres_Rig|Mini_Dirigeable_Tenebres_Rig|Hit, Mini_Dirigeable_Tenebres_Rig|Mini_Dirigeable_Tenebres_Rig|Idle, Mini_Dirigeable_Tenebres_Rig|Mini_Dirigeable_Tenebres_Rig|Move
  Couleurs : texture palette incrustée oui, UV oui, couleurs de sommets oui, texture sur tous les matériaux oui
  Yeux : toujours au-dessus de l'enveloppe
  Yeux (marge minimale, mm) : Idle +2.1, Move +3.8, Attack +0.4, Hit +1.6, Death +0.7
  Idle: 72 images (source 72), écart max 0.0 mm, déplacement max 0.07 m, taille fin/début 1.00
  Move: 36 images (source 36), écart max 0.0 mm, déplacement max 0.02 m, taille fin/début 1.00
  Attack: 44 images (source 44), écart max 0.0 mm, déplacement max 0.94 m, taille fin/début 1.00
  Hit: 18 images (source 18), écart max 0.0 mm, déplacement max 0.15 m, taille fin/début 1.00
  Death: 66 images (source 66), écart max 0.0 mm, déplacement max 0.29 m, taille fin/début 0.03
```
