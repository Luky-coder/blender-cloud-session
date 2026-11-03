"""Assemble la planche d'animations (et le GIF d'attaque) d'un ennemi. Python 3 + Pillow, hors Blender.

    python3 compose.py job.json
"""
import json
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
LABELS = {"Idle": "IDLE", "Move": "MOVE", "Attack": "ATTACK", "Hit": "HIT", "Death": "DEATH"}


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def main(job_path):
    with open(job_path) as fh:
        job = json.load(fh)
    rows = list(job["tiles"].items())
    first = Image.open(rows[0][1][0][1])
    tw, th = first.size
    scale = 0.6
    tw, th = int(tw * scale), int(th * scale)
    cols = max(len(r[1]) for r in rows)
    lw, top, cap = 120, 56, 22
    W = lw + cols * (tw + 4) + 8
    H = top + len(rows) * (th + cap + 6) + 8
    sheet = Image.new("RGB", (W, H), (246, 246, 240))
    d = ImageDraw.Draw(sheet)
    d.text((14, 14), job["title"], fill=(30, 40, 30), font=font(FONT, 24))
    f_lab, f_cap = font(FONT, 18), font(FONT_R, 13)
    for r, (name, tiles) in enumerate(rows):
        y = top + r * (th + cap + 6)
        color = (200, 60, 30) if name == "Attack" else (40, 70, 40)
        d.text((12, y + th // 2 - 10), LABELS.get(name, name), fill=color, font=f_lab)
        for c, (frame, path) in enumerate(tiles):
            im = Image.open(path).convert("RGB").resize((tw, th), Image.LANCZOS)
            x = lw + c * (tw + 4)
            sheet.paste(im, (x, y))
            d.text((x + 4, y + th + 3), f"image {frame}", fill=(80, 80, 80), font=f_cap)
    sheet.save(job["out"], quality=88)
    if job.get("gif"):
        frames = [Image.open(p).convert("RGB") for p in job["gif"]]
        frames = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in frames]
        frames[0].save(job["gif_out"], save_all=True, append_images=frames[1:], duration=33, loop=0, optimize=True)


if __name__ == "__main__":
    main(sys.argv[1])
