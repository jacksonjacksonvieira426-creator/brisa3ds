#!/usr/bin/env python3
"""Builds the Brisa3DS icon set from assets/logo.png.

Run it again whenever the logo changes. The outputs go into overlay/, which apply.sh copies over
the Azahar resources (the old Azahar vector icons are removed by rename.py).
"""
import statistics
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "overlay" / "src" / "android" / "app" / "src" / "main" / "res"
LOGO = Image.open(ROOT / "assets" / "logo.png").convert("RGBA")

# Where things are inside the 1600x1600 source (measured on the logo).
SQUARE = (168, 160, 1432, 1445)        # the rounded blue square
CONSOLE = (425, 435, 1185, 1180)       # the white console body
CENTER = ((SQUARE[0] + SQUARE[2]) / 2, (SQUARE[1] + SQUARE[3]) / 2)


def is_blue(px):
    r, g, b, a = px
    return a == 255 and b > 200 and r < 150


def row_colors():
    """Per-row background colour taken from the logo's own blue, so the extension is seamless."""
    px = LOGO.load()
    rows = {}
    for y in range(SQUARE[1] + 40, SQUARE[3] - 40):
        samples = [px[x, y] for x in range(185, 420) if is_blue(px[x, y])]
        if samples:
            rows[y] = tuple(int(statistics.median(s[i] for s in samples)) for i in range(3))
    ys = sorted(rows)
    smooth = {}
    for y in ys:
        window = [rows[k] for k in ys if abs(k - y) <= 12]
        smooth[y] = tuple(int(sum(c[i] for c in window) / len(window)) for i in range(3))
    return smooth


def defringe(logo, colors):
    """Paints the faint grey/pink anti-aliasing edge of the rounded square with the background
    colour, so the square melts into the extended background. White swirls are left alone."""
    out = logo.copy()
    px = out.load()
    top_y, bottom_y = min(colors), max(colors)
    for y in range(SQUARE[1] - 12, SQUARE[3] + 12):
        c = colors[min(max(y, top_y), bottom_y)]
        for x in range(SQUARE[0] - 12, SQUARE[2] + 12):
            r, g, b, a = px[x, y]
            if a == 0 or (a < 255 and min(r, g, b) < 225):
                px[x, y] = (c[0], c[1], c[2], a)
    return out


def adaptive_foreground(size=864, scale=0.52):
    """Full 108dp canvas: logo scaled down, on a background that continues the logo's blue."""
    colors = row_colors()
    top_y, bottom_y = min(colors), max(colors)
    canvas = Image.new("RGBA", (size, size))
    draw = canvas.load()
    k = scale * size / 1264  # the 1264 px wide blue square becomes `scale` of the canvas
    for cy in range(size):
        # canvas row -> source row
        sy = int(round((cy - size / 2) / k + CENTER[1]))
        sy = min(max(sy, top_y), bottom_y)
        c = colors[sy]
        for cx in range(size):
            draw[cx, cy] = (c[0], c[1], c[2], 255)
    resized = defringe(LOGO, colors).resize((round(1600 * k), round(1600 * k)), Image.LANCZOS)
    ox = round(size / 2 - CENTER[0] * k)
    oy = round(size / 2 - CENTER[1] * k)
    canvas.paste(resized, (ox, oy), resized)
    return canvas


def whiteness_mask(image, box=None):
    """White pixels of the logo as an alpha mask."""
    px = image.load()
    out = Image.new("L", image.size, 0)
    o = out.load()
    x0, y0, x1, y1 = box or (0, 0, image.size[0], image.size[1])
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = px[x, y]
            if a > 200 and min(r, g, b) > 228:
                o[x, y] = 255
    return out


def monochrome(size=864, scale=0.52):
    mask = whiteness_mask(LOGO)
    white = Image.new("RGBA", LOGO.size, (255, 255, 255, 0))
    white.putalpha(mask)
    k = scale * size / 1264
    resized = white.resize((round(1600 * k), round(1600 * k)), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ox = round(size / 2 - CENTER[0] * k)
    oy = round(size / 2 - CENTER[1] * k)
    canvas.alpha_composite(resized, (ox, oy))
    return canvas


def full_logo(size=512):
    """The logo with its swirls on a transparent square, for the in-app screens."""
    box = (90, 150, 1510, 1450)
    cropped = LOGO.crop(box)
    side = max(cropped.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.alpha_composite(cropped, ((side - cropped.size[0]) // 2, (side - cropped.size[1]) // 2))
    return square.resize((size, size), Image.LANCZOS)


def notification_icon(size):
    """White console silhouette on transparent, as Android status bar icons must be."""
    mask = whiteness_mask(LOGO, CONSOLE)
    white = Image.new("RGBA", LOGO.size, (255, 255, 255, 0))
    white.putalpha(mask)
    cropped = white.crop(CONSOLE)
    side = max(cropped.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.alpha_composite(cropped, ((side - cropped.size[0]) // 2, (side - cropped.size[1]) // 2))
    return square.resize((size, size), Image.LANCZOS)


def main():
    for folder in ("drawable-nodpi", "drawable-hdpi", "drawable-xhdpi", "drawable-xxhdpi"):
        (RES / folder).mkdir(parents=True, exist_ok=True)
    adaptive_foreground().save(RES / "drawable-nodpi" / "ic_citra.png", optimize=True)
    monochrome().save(RES / "drawable-nodpi" / "ic_citra_monochrome.png", optimize=True)
    full_logo().save(RES / "drawable-nodpi" / "ic_citra_full.png", optimize=True)
    for folder, px in (("hdpi", 36), ("xhdpi", 48), ("xxhdpi", 72)):
        notification_icon(px).save(RES / f"drawable-{folder}" / "ic_stat_notification_logo.png", optimize=True)
    print("== icons written to", RES)


if __name__ == "__main__":
    main()
