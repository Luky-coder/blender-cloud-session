"""Petits utilitaires bpy pour écrire les scripts de modèles (Blender 5.x).

Dans models/<nom>/build.py :
    from helpers import material, assign, bevel, smooth
"""
import math

import bpy


def material(name, color, roughness=0.5, metallic=0.0, emission=None, emission_strength=1.0):
    """Matériau Principled BSDF. color = (r, g, b) entre 0 et 1, en couleur linéaire."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    mat.diffuse_color = (*color, 1.0)  # couleur dans le viewport
    return mat


def assign(obj, mat):
    """Remplace les matériaux de l'objet par `mat`."""
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def bevel(obj, width=0.005, segments=3, angle=30):
    """Arrondit les arêtes vives (modificateur Bevel, limité par angle)."""
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angle)
    mod.harden_normals = True
    return mod


def smooth(obj, angle=30):
    """Lissage des faces avec arêtes vives conservées au-delà de `angle` degrés (ex-"auto smooth")."""
    obj.data.set_sharp_from_angle(angle=math.radians(angle))
    return obj
