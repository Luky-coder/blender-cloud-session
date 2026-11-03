"""Planche de comparaison : quart haut-gauche (vue 3/4 avant) et haut-droit (face) de chaque aperçu.
    python3 src/montage.py sortie.jpg img1.jpg img2.jpg ... [--cols 4] [--full]"""
import sys

from PIL import Image, ImageDraw

args = sys.argv[1:]
cols = 4
full = "--full" in args
if "--cols" in args:
    i = args.index("--cols")
    cols = int(args[i + 1])
    del args[i:i + 2]
args = [a for a in args if a != "--full"]
out, files = args[0], args[1:]
tiles = []
for f in files:
    im = Image.open(f)
    w, h = im.size
    if not full:
        im = im.crop((0, 0, w, h // 2))  # rangée du haut : 3/4 avant + face
    label = f.split("/")[-2] + " " + f.split("/")[-1].rsplit(".", 1)[0]
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 8 * len(label) + 10, 18), fill=(30, 30, 40))
    d.text((5, 3), label, fill=(255, 255, 255))
    tiles.append(im)
tw, th = tiles[0].size
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * th), (160, 160, 165))
for i, t in enumerate(tiles):
    sheet.paste(t.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
sheet.save(out, quality=88)
