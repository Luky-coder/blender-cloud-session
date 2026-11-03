"""Point d'entrée : construit un ennemi complet (maillage unique + armature + 5 actions)."""
import bpy
from mathutils import Matrix

from . import anim, elements, families, geo, rig
from .materials import palette

ELEMENTS = {  # id -> (nom affiché, nom de fichier)
    "lumiere": ("Lumière", "Lumiere"),
    "tenebres": ("Ténèbres", "Tenebres"),
    "glace": ("Glace", "Glace"),
    "feu": ("Feu", "Feu"),
    "eau": ("Eau", "Eau"),
    "plante": ("Plante", "Plante"),
    "eclair": ("Éclair", "Eclair"),
}
FAMILIES = {  # id -> (nom affiché, dossier, PV)
    "classique": ("Ballon Classique", "Ballon_Classique", 15),
    "etoile": ("Ballon Étoile", "Ballon_Etoile", 20),
    "dirigeable": ("Mini-dirigeable", "Mini_Dirigeable", 30),
}
BOSSES = {  # id -> (nom affiché, fichier, PV, rang)
    "montgolfiere": ("Montgolfière Solaire", "MiniBoss_Montgolfiere_Plante", 250, "Mini-boss"),
    "zeppelin": ("Grand Zeppelin des Prairies", "Boss_Zeppelin_Plante", 1000, "Boss"),
}


def enemy_id(family, element):
    if family in BOSSES:
        return BOSSES[family][1]
    return f"{FAMILIES[family][1]}_{ELEMENTS[element][1]}"


def setup_scene():
    scene = bpy.context.scene
    scene.render.fps = anim.FPS
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0


def build_enemy(family, element="plante", with_anims=True, offset=None):
    """Construit l'ennemi dans sa propre collection. Renvoie (armature, maillage, frame)."""
    setup_scene()
    name = enemy_id(family, element)
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    geo.COLLECTION = coll
    rig.reset()
    P = palette(element)
    if family in BOSSES:
        from . import bosses
        F = bosses.BUILDERS[family](P)
    else:
        F = families.BUILDERS[family](P)
        elements.face(F, P)
        elements.shine(F, P)
        elements.DECOR[element](F, P)
    arm = rig.build_armature(F, name + "_Rig")
    mesh = rig.skin_and_join(F, arm, name)
    if family in BOSSES:
        disp, _f, pv, rank = BOSSES[family]
        arm["Famille"] = rank
        arm["Nom"] = disp
    else:
        disp, _f, pv = FAMILIES[family]
        arm["Famille"] = disp
        arm["Nom"] = f"{disp} {ELEMENTS[element][0]}"
    arm["Element"] = ELEMENTS[element][0]
    arm["PV"] = pv
    arm["Avant"] = "+Y"
    if with_anims:
        acts = anim.make_all(arm, F)
        A = anim.PARAMS[F.kind]
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = 1 + A["idle"]
        arm["Animations"] = ", ".join(f"{k} ({int(a.frame_end - a.frame_start)} i)" for k, a in acts.items())
    if offset is not None:
        arm.matrix_world = Matrix.Translation(offset)
    geo.COLLECTION = None
    return arm, mesh, F
