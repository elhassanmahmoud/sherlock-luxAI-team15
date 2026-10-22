"""Symbol der App "Sherlock Demo": Lupe ueber einem kleinen Lux-Kartenausschnitt (Farben der Folien).

    .venv/bin/python scripts/make_demo_icon.py <ziel.iconset>   # danach: iconutil -c icns <ziel.iconset>

Wird von scripts/build_demo_app.sh aufgerufen.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

DARK_TOP, DARK_BOTTOM = (22, 66, 76), (13, 37, 44)
CREAM, RING, HANDLE = (247, 246, 241), (236, 244, 242), (43, 179, 168)
TILE, ASTEROID, NEBULA, GOLD, BLUE = (226, 230, 226), (52, 64, 70), (205, 186, 238), (242, 201, 76), (34, 139, 230)
GRID = [  # 5 x 5 Felder im Glas: . frei, A Asteroid, N Nebel, G Punktefeld
    "..NN.",
    ".A...",
    "..G.A",
    "N..AA",
    ".N...",
]


def draw_icon(size: int = 1024) -> Image.Image:
    s = size / 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # abgerundetes Quadrat mit Verlauf (macOS-Symbolraster: 824 px Kante, Radius 185)
    bg = Image.new("RGBA", (size, size))
    px = bg.load()
    for y in range(size):
        t = y / (size - 1)
        c = tuple(round(a + (b - a) * t) for a, b in zip(DARK_TOP, DARK_BOTTOM)) + (255,)
        for x in range(size):
            px[x, y] = c
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([100 * s, 100 * s, 924 * s, 924 * s], radius=185 * s, fill=255)
    img.paste(bg, (0, 0), mask)

    # Kartenausschnitt im Glas
    cx, cy, r = 452 * s, 452 * s, 214 * s
    lens = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(lens)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CREAM)
    cell = 2 * r / 5
    colors = {".": TILE, "A": ASTEROID, "N": NEBULA, "G": GOLD}
    for j, row in enumerate(GRID):
        for i, ch in enumerate(row):
            x0, y0 = cx - r + i * cell, cy - r + j * cell
            d.rectangle([x0 + 5 * s, y0 + 5 * s, x0 + cell - 5 * s, y0 + cell - 5 * s], fill=colors[ch])
    ux, uy = cx, cy  # Einheit auf dem Punktefeld (Mitte)
    d.ellipse([ux - 30 * s, uy - 30 * s, ux + 30 * s, uy + 30 * s], fill=BLUE, outline=(255, 255, 255), width=round(7 * s))
    clip = Image.new("L", (size, size), 0)
    ImageDraw.Draw(clip).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    img.paste(lens, (0, 0), clip)

    # Griff und Ring
    d = ImageDraw.Draw(img)
    d.line([(cx + 0.74 * (r + 40 * s), cy + 0.74 * (r + 40 * s)), (790 * s, 790 * s)], fill=HANDLE, width=round(96 * s))
    d.ellipse([790 * s - 48 * s, 790 * s - 48 * s, 790 * s + 48 * s, 790 * s + 48 * s], fill=HANDLE)
    w = 56 * s
    d.ellipse([cx - r - w / 2, cy - r - w / 2, cx + r + w / 2, cy + r + w / 2], outline=RING, width=round(w))
    return img


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    big = draw_icon(1024)
    for base in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            px = base * scale
            name = f"icon_{base}x{base}{'@2x' if scale == 2 else ''}.png"
            big.resize((px, px), Image.LANCZOS).save(out / name)


if __name__ == "__main__":
    main()
