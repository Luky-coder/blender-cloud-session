"""Matériaux Principled BSDF : matière gonflable brillante commune + palettes des 7 éléments."""
import bpy


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def mat(name, hexcol, rough=0.35, metal=0.0, coat=0.0, emit=0.0, emit_hex=None, transmission=0.0,
        alpha=1.0, ior=1.45, sheen=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    col = srgb(hexcol)
    i = b.inputs
    i["Base Color"].default_value = (*col, 1.0)
    i["Roughness"].default_value = rough
    i["Metallic"].default_value = metal
    i["Coat Weight"].default_value = coat
    i["Coat Roughness"].default_value = 0.04
    i["IOR"].default_value = ior
    i["Sheen Weight"].default_value = sheen
    if emit > 0:
        i["Emission Color"].default_value = (*srgb(emit_hex or hexcol), 1.0)
        i["Emission Strength"].default_value = emit
    if transmission > 0:
        i["Transmission Weight"].default_value = transmission
    if alpha < 1:
        i["Alpha"].default_value = alpha
    m.diffuse_color = (*col, alpha)
    m.roughness = rough
    m.metallic = metal
    return m


def inflatable(name, hexcol, rough=0.16, coat=0.8):
    """Matière gonflable : latex / vinyle brillant avec vernis (reflets nets)."""
    return mat(name, hexcol, rough=rough, coat=coat)


def foil(name, hexcol):
    """Ballon métallisé (mylar) : ballon étoile."""
    return mat(name, hexcol, rough=0.18, metal=0.75, coat=0.5)


def common():
    """Matériaux partagés par tous les ennemis."""
    return {
        "eye_white": mat("Commun_Oeil_Blanc", "#FFFFFF", rough=0.2, coat=0.6),
        "pupil": mat("Commun_Pupille", "#16121C", rough=0.15, coat=0.8),
        "shine": mat("Commun_Reflet", "#FFFFFF", rough=0.3, emit=1.5),
        "metal": mat("Commun_Metal", "#9097A3", rough=0.3, metal=1.0),
        "metal_dark": mat("Commun_Metal_Sombre", "#3B3F47", rough=0.35, metal=1.0),
        "rubber": mat("Commun_Caoutchouc", "#26262B", rough=0.6),
        "glass": mat("Commun_Vitre", "#203A55", rough=0.05, coat=1.0),
        "wood": mat("Commun_Bois", "#8A5A2B", rough=0.6),
        "wood_dark": mat("Commun_Bois_Fonce", "#5C3A1C", rough=0.65),
        "rope": mat("Commun_Corde", "#C9AE7C", rough=0.85),
    }


def palette(el):
    """Palette d'un élément. Clés : body, body2, seam, accent, accent2, glow, string, brow, pupil, iris..."""
    P = common()
    if el == "lumiere":
        P.update(
            body=inflatable("Lumiere_Enveloppe", "#FFCB2E"),
            body2=inflatable("Lumiere_Blanc_Nacre", "#FFF6E0"),
            seam=mat("Lumiere_Couture_Or", "#F0B030", rough=0.22, metal=1.0),
            accent=mat("Lumiere_Or", "#FFC83A", rough=0.2, metal=1.0, coat=0.5),
            accent2=mat("Lumiere_Blanc_Lumineux", "#FFFBEA", rough=0.3, emit=3.0, emit_hex="#FFF2C0"),
            glow=mat("Lumiere_Halo", "#FFE27A", rough=0.3, emit=6.0, emit_hex="#FFD24A"),
            string=mat("Lumiere_Ficelle", "#F5C451", rough=0.4, metal=0.6),
            brow=mat("Lumiere_Sourcil", "#B57A12", rough=0.3),
            iris=None,
        )
    elif el == "tenebres":
        P.update(
            body=inflatable("Tenebres_Enveloppe", "#2B1840"),
            body2=inflatable("Tenebres_Noir", "#0E0A14"),
            seam=mat("Tenebres_Couture_Violette", "#B44CFF", rough=0.3, emit=5.0, emit_hex="#A23CFF"),
            accent=inflatable("Tenebres_Violet", "#5E2A8C"),
            accent2=mat("Tenebres_Rune", "#D27BFF", rough=0.3, emit=6.0, emit_hex="#B65CFF"),
            glow=mat("Tenebres_Lueur", "#C27BFF", rough=0.3, emit=8.0, emit_hex="#A64DFF"),
            smoke=mat("Tenebres_Fumee", "#2C2536", rough=0.95, sheen=0.6),
            smoke2=mat("Tenebres_Fumee_Violette", "#46325E", rough=0.95, sheen=0.6),
            string=mat("Tenebres_Ficelle", "#3C2A52", rough=0.5),
            brow=mat("Tenebres_Sourcil", "#07040A", rough=0.4),
            iris=mat("Tenebres_Oeil", "#E7B8FF", rough=0.3, emit=7.0, emit_hex="#C27BFF"),
        )
    elif el == "glace":
        P.update(
            body=inflatable("Glace_Enveloppe", "#9ED8F2"),
            body2=inflatable("Glace_Blanc", "#EEF8FF"),
            seam=mat("Glace_Couture", "#E8F7FF", rough=0.25, coat=0.6),
            accent=mat("Glace_Cristal", "#B8E8FF", rough=0.05, transmission=0.85, ior=1.31, coat=1.0),
            accent2=mat("Glace_Cristal_Profond", "#6CC4F0", rough=0.08, transmission=0.6, ior=1.31, coat=1.0),
            glow=mat("Glace_Lueur", "#D9F4FF", rough=0.2, emit=2.0, emit_hex="#BFEAFF"),
            frost=mat("Glace_Givre", "#F6FBFF", rough=0.75, sheen=0.5),
            string=mat("Glace_Ficelle", "#DDF1FB", rough=0.5),
            brow=mat("Glace_Sourcil", "#2E6E95", rough=0.3),
            iris=None,
        )
    elif el == "feu":
        P.update(
            body=inflatable("Feu_Enveloppe", "#E5321B"),
            body2=inflatable("Feu_Orange", "#FF8A1E"),
            seam=mat("Feu_Couture", "#FFB21E", rough=0.3, emit=1.5, emit_hex="#FF9A10"),
            accent=mat("Feu_Flamme", "#FF5A0A", rough=0.4, emit=2.2, emit_hex="#FF3C00"),
            accent2=mat("Feu_Flamme_Coeur", "#FFC83A", rough=0.4, emit=2.5, emit_hex="#FFB020"),
            glow=mat("Feu_Braise", "#FFB040", rough=0.4, emit=8.0, emit_hex="#FF8A10"),
            string=mat("Feu_Ficelle", "#3A1D12", rough=0.6),
            brow=mat("Feu_Sourcil", "#5A0E06", rough=0.4),
            iris=None,
        )
    elif el == "eau":
        P.update(
            body=inflatable("Eau_Enveloppe", "#1C78D6"),
            body2=inflatable("Eau_Turquoise", "#24CFC4"),
            seam=mat("Eau_Couture", "#A8F0F4", rough=0.2, coat=0.6),
            accent=mat("Eau_Goutte", "#4CC8FF", rough=0.03, transmission=0.9, ior=1.33, coat=1.0),
            accent2=mat("Eau_Vague", "#3FE0D0", rough=0.12, coat=0.8),
            glow=mat("Eau_Bulle", "#D8F6FF", rough=0.02, transmission=1.0, ior=1.2, coat=1.0),
            string=mat("Eau_Ficelle", "#BDEFFF", rough=0.4),
            brow=mat("Eau_Sourcil", "#0B3A6E", rough=0.3),
            iris=None,
        )
    elif el == "plante":
        P.update(
            body=inflatable("Plante_Enveloppe", "#4DB847"),
            body2=inflatable("Plante_Vert_Fonce", "#2D7F34"),
            seam=mat("Plante_Couture", "#A6E05A", rough=0.3, coat=0.5),
            accent=mat("Plante_Feuille", "#3FA83A", rough=0.35, coat=0.4, sheen=0.3),
            accent2=mat("Plante_Feuille_Claire", "#8BD448", rough=0.35, coat=0.4, sheen=0.3),
            glow=mat("Plante_Coeur_Fleur", "#FFD23F", rough=0.4, emit=0.6),
            petal=mat("Plante_Petale", "#FF8FBF", rough=0.35, coat=0.3, sheen=0.4),
            petal2=mat("Plante_Petale_Blanc", "#FFF4F8", rough=0.35, coat=0.3, sheen=0.4),
            vine=mat("Plante_Liane", "#2F6B2A", rough=0.5),
            string=mat("Plante_Ficelle_Liane", "#3D7A2C", rough=0.5),
            brow=mat("Plante_Sourcil", "#1A4A1E", rough=0.3),
            iris=None,
        )
    elif el == "eclair":
        P.update(
            body=inflatable("Eclair_Enveloppe", "#FFD21F"),
            body2=inflatable("Eclair_Bleu", "#2A8CFF"),
            seam=mat("Eclair_Couture", "#2A6BFF", rough=0.25, emit=3.0, emit_hex="#2A8CFF"),
            accent=mat("Eclair_Eclair", "#FFE95A", rough=0.3, emit=3.0, emit_hex="#FFE030"),
            accent2=mat("Eclair_Bleu_Electrique", "#5CCBFF", rough=0.3, emit=7.0, emit_hex="#2AA8FF"),
            glow=mat("Eclair_Etincelle", "#F0FAFF", rough=0.3, emit=10.0, emit_hex="#9FE0FF"),
            string=mat("Eclair_Ficelle", "#1E3E7A", rough=0.45, metal=0.5),
            brow=mat("Eclair_Sourcil", "#1A2E66", rough=0.3),
            iris=None,
        )
    else:
        raise ValueError(el)
    return P
