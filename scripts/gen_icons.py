"""One-off script to generate PWA icons from the app's color scheme. Not part of the runtime app."""
from PIL import Image, ImageDraw, ImageFont

BG = (10, 10, 15, 255)       # --bg
CYAN = (0, 229, 255, 255)    # --accent
ORANGE = (255, 107, 53, 255) # --accent2
FONT_PATH = r"C:\Windows\Fonts\impact.ttf"

OUT_DIR = r"C:\Users\adam_\PycharmProjects\Fantasy Football HQ\static\icons"


def make_icon(size, path, maskable=False):
    img = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(img)

    if maskable:
        # keep content inside the ~80% safe zone for maskable icons
        radius = 0
    else:
        radius = int(size * 0.22)
        mask = Image.new("L", (size, size), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
        img.putalpha(mask)

    font_size = int(size * 0.5)
    font = ImageFont.truetype(FONT_PATH, font_size)

    text = "HQ"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=ORANGE)

    # cyan underline accent
    bar_w = tw * 0.9
    bar_h = max(2, int(size * 0.035))
    bar_x = (size - bar_w) / 2
    bar_y = y + th + size * 0.06
    draw.rounded_rectangle(
        [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
        radius=bar_h / 2,
        fill=CYAN,
    )

    img.save(path)
    print("wrote", path)


if __name__ == "__main__":
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    make_icon(192, os.path.join(OUT_DIR, "icon-192.png"))
    make_icon(512, os.path.join(OUT_DIR, "icon-512.png"))
    make_icon(512, os.path.join(OUT_DIR, "icon-maskable-512.png"), maskable=True)
    make_icon(180, os.path.join(OUT_DIR, "apple-touch-icon.png"))
    make_icon(32, os.path.join(OUT_DIR, "favicon-32.png"))
