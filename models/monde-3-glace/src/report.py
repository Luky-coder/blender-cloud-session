"""Assemble le rapport final à partir des fiches JSON de chaque ennemi et de la vérification FBX.

    python3 src/report.py

Produit : World_3_Glace/RAPPORT.md, World_3_Glace/Previews/_Galerie.jpg,
          World_3_Glace/Textures/materiaux.json et Textures/LISEZMOI.txt
"""
import glob
import json
import os
import unicodedata

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "World_3_Glace")
ORDER = ["Lumière", "Ténèbres", "Glace", "Feu", "Eau", "Plante", "Éclair"]


def load():
    items = [json.load(open(f, encoding="utf-8")) for f in glob.glob(os.path.join(ROOT, "Previews", "**", "*.json"),
                                                                      recursive=True)]
    fam_order = {"Ballon Igloo": 0, "Ballon Flocon": 1, "Dirigeable Polaire": 2}
    items.sort(key=lambda d: (fam_order.get(d["family"], 3), ORDER.index(d["element"]) if d["element"] in ORDER else 0,
                              d["hp"]))
    return items


def gallery(items):
    tiles = []
    for d in items:
        img = os.path.join(ROOT, os.path.splitext(d["blend"].replace("Blender", "Previews", 1))[0] + ".jpg")
        im = Image.open(img)
        w, h = im.size
        im = im.crop((0, 0, w // 2, h // 2)).resize((320, 240))   # vue 3/4 avant
        dr = ImageDraw.Draw(im)
        dr.rectangle((0, 0, 320, 16), fill=(25, 35, 55))
        label = unicodedata.normalize("NFKD", f"{d['title']} - PV {d['hp']}").encode("ascii", "ignore").decode()
        dr.text((4, 2), label, fill=(255, 255, 255))
        tiles.append(im)
    cols = 7
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 320, rows * 240), (150, 152, 158))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * 320, (i // cols) * 240))
    sheet.save(os.path.join(ROOT, "Previews", "_Galerie.jpg"), quality=88)


def main():
    items = load()
    gallery(items)
    os.makedirs(os.path.join(ROOT, "Textures"), exist_ok=True)
    json.dump({d["name"]: d["materials"] for d in items},
              open(os.path.join(ROOT, "Textures", "materiaux.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "Textures", "LISEZMOI.txt"), "w", encoding="utf-8") as f:
        f.write("Aucune texture image n'est nécessaire.\n\n"
                "Tous les matériaux sont des Principled BSDF à couleurs unies (plastique gonflable brillant) : le\n"
                "FBX transporte la couleur de base, la rugosité, le métal et l'émission. Les motifs élémentaires\n"
                "(flammes, cristaux, bulles, feuilles, éclairs, montagnes...) sont de la vraie géométrie.\n\n"
                "materiaux.json liste, pour chaque ennemi, les réglages exacts de chaque matériau (couleur sRGB,\n"
                "rugosité, métal, vernis/coat, émission, transparence) pour recréer les shaders dans le moteur :\n"
                "le vernis (coat) et la transmission ne passent pas par le FBX.\n")
    ver_path = os.path.join(ROOT, "verification_fbx.json")
    ver = {v["file"]: v for v in json.load(open(ver_path, encoding="utf-8"))} if os.path.exists(ver_path) else {}

    L = ["# Monde 3 — Le Royaume Givré : rapport de production", "",
         "![Galerie](Previews/_Galerie.jpg)", "",
         "23 ennemis gonflables (3 familles × 7 types + mini-boss + boss), chacun en `.blend` et en `.fbx`",
         "individuels, avec armature, shape keys et animations indépendantes (une Action = une prise FBX).", "",
         "## Fichiers créés", "",
         "| Ennemi | PV | Dimensions X×Y×Z (m) | Sommets | Triangles | Os | Actions | .blend | .fbx | FBX vérifié |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for d in items:
        v = ver.get(os.path.basename(d["fbx"]))
        ok = "—" if v is None else ("OK" if not v["errors"] else "ERREUR : " + "; ".join(v["errors"]))
        L.append(f"| {d['title']} | {d['hp']} | {' × '.join(f'{x:.2f}' for x in d['dims'])} | {d['verts']:,} | "
                 f"{d['tris']:,} | {d['deform_bones']} | {len(d['actions'])} | [`{os.path.basename(d['blend'])}`]({d['blend']}) | "
                 f"[`{os.path.basename(d['fbx'])}`]({d['fbx']}) | {ok} |".replace(",", " "))
    L += ["", "Aperçus : `Previews/<Famille>/<Type>.jpg` (3/4 avant · face · profil droit · 3/4 arrière) et",
          "`Previews/<Famille>/<Type>_animations.jpg` (une ligne par Action, 6 images réparties sur sa durée).", "",
          "## Animations", "",
          "Toutes à 30 images/s. Les boucles (IDLE, MOVE, IDLE_Phase2) ont leur dernière image identique à la",
          "première (et un modificateur Cycles dans Blender).", ""]
    seen = set()
    for d in items:
        key = d["family"]
        if key in seen:
            continue
        seen.add(key)
        acts = ", ".join(f"`{a['name']}` ({a['frames']} im., {a['seconds']} s{', boucle' if a['loop'] else ''})"
                         for a in d["actions"])
        L.append(f"- **{d['family'] if d['hp'] < 900 else d['title']}** : {acts}")
    L += ["", "Shape keys (sur tous les modèles) : `Respiration` (gonflement), `Impact` (écrasement de l'avant),",
          "`Degonfle` (froissé, aplati). Elles sont pilotées dans Blender par l'os de contrôle `CTRL_Formes`",
          "(X/Y/Z) et cuites dans chaque prise FBX comme courbes de blend shapes ; l'os de contrôle n'est pas",
          "exporté (os de déformation uniquement).", "",
          "## Conventions", "",
          "- Unités : mètres. Z vers le haut. **Avant du modèle vers +Y** (comme demandé). Pivot au sol sous le",
          "  modèle (os `Root`), le corps flottant au-dessus.",
          "- Un seul maillage par ennemi (multi-matériaux), skinné sur une armature (`<Nom>_Rig`). Les os ont",
          "  une orientation de repos alignée sur les axes du monde.",
          "- Export FBX : axes par défaut de Blender (-Z avant, Y haut côté FBX), unités en mètres,",
          "  `add_leaf_bones` désactivé, une prise par Action nommée `<Nom>_Rig|<ACTION>`.",
          "- Projectiles (pomme de pin, racines surgissantes, bloc de neige, graine, mini-ballons, tempête) :",
          "  intégrés aux boss sur des os `Proj_*`, à l'échelle 0 hors de leurs attaques.", "",
          "## Régénérer", "",
          "```bash", "bash src/run_batch.sh \"igloo:glace flocon:feu pin:plante\"   # ou n'importe quelle liste",
          "blender -b --factory-startup -q -P src/verify_fbx.py -- World_3_Glace/FBX World_3_Glace/verification_fbx.json",
          "python3 src/report.py", "```", ""]
    open(os.path.join(ROOT, "RAPPORT.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"rapport : {len(items)} ennemis")


if __name__ == "__main__":
    main()
