import argparse
from pathlib import Path

import freetype
import numpy
from PIL import Image, ImageDraw

SIZES = range(11, 17)
LINES = ["Hamburgefonstiv quick zephyrs, 0123456789 HOxn", "Jiji îlot ñandú ÿý ÀÉÎÕÜÅÑ àéîõüåñ æœ&"]
ZOOM = 3
LABEL_WIDTH = 30
HINTED = freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_AUTOHINT
UNHINTED = freetype.FT_LOAD_NO_HINTING


def strip(path, size, text, flags):
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, size)
    height, baseline = size * 2, round(size * 1.4)
    canvas = numpy.zeros((height, size * len(text)), dtype=numpy.float64)
    pen = 2
    for char in text:
        face.load_char(char, flags | freetype.FT_LOAD_RENDER)
        slot = face.glyph
        bitmap = slot.bitmap
        if bitmap.rows and bitmap.width:
            data = numpy.array(bitmap.buffer, dtype=numpy.float64).reshape(bitmap.rows, bitmap.pitch)[:, : bitmap.width]
            top, left = baseline - slot.bitmap_top, pen + slot.bitmap_left
            area = canvas[top : top + bitmap.rows, left : left + bitmap.width]
            numpy.maximum(area, data[: area.shape[0], : area.shape[1]], out=area)
        pen += round(slot.advance.x / 64)
    used = numpy.nonzero(canvas.max(axis=0) > 0)[0]
    return Image.fromarray((255 - canvas[:, : used[-1] + 3]).astype("uint8"), "L")


def labelled(image, label):
    row = Image.new("L", (image.width + LABEL_WIDTH, image.height), 255)
    row.paste(image, (LABEL_WIDTH, 0))
    ImageDraw.Draw(row).text((1, image.height // 3), label, fill=96)
    return row


def sheet(hinted, unhinted):
    rows = []
    for text in LINES:
        for size in SIZES:
            rows.append(labelled(strip(hinted, size, text, HINTED), f"{size} h"))
            rows.append(labelled(strip(unhinted, size, text, UNHINTED), f"{size} u"))
    width = max(row.width for row in rows)
    page = Image.new("L", (width, sum(row.height for row in rows)), 255)
    y = 0
    for row in rows:
        page.paste(row, (0, y))
        y += row.height
    return page.resize((width * ZOOM, page.height * ZOOM), Image.NEAREST)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fonts", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("styles", nargs="+")
    args = parser.parse_args()
    args.target.mkdir(parents=True, exist_ok=True)
    for style in args.styles:
        name = f"Plutto-{style}.ttf"
        sheet(args.fonts / name, args.fonts / "unhinted" / name).save(args.target / f"{style}.png")


if __name__ == "__main__":
    main()
