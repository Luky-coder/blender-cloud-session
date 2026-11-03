"""Monde 1 - La Prairie : bibliothèque commune des 23 ennemis gonflables.

Modules :
    geo        maillages de base (lathe, tube, coussin gonflable, feuille, étoile, flamme...)
    materials  matériaux Principled BSDF et palettes des 7 éléments
    surface    projection sur l'enveloppe (BVH) : décalcomanies, patchs, chemins
    families   géométrie de base des 3 familles (Ballon Classique, Ballon Étoile, Mini-dirigeable)
    elements   détails propres à chaque élément (halo, cristaux, flammes, bulles, feuilles, éclairs...)
    bosses     Montgolfière Solaire (mini-boss) et Grand Zeppelin des Prairies (boss)
    rig        armature, pondérations (skinning) et assemblage en un seul maillage
    anim       actions Idle / Move / Attack / Hit / Death
    enemy      point d'entrée : build_enemy(famille, element)
"""
