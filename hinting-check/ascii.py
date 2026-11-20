import sys

import freetype
import numpy

SHADES = " .:-=+*#%@"


def show(path, char, size, flags):
    face = freetype.Face(path)
    face.set_pixel_sizes(0, size)
    face.load_char(char, flags)
    b = face.glyph.bitmap
    data = numpy.array(b.buffer, dtype=numpy.uint8).reshape(b.rows, b.pitch)[:, : b.width]
    return ["".join("#" if v >= 128 else ("+" if v >= 64 else ("." if v else " ")) for v in row) for row in data]


folder, style, char, size = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
hinted = show(f"{folder}/Plutto-{style}.ttf", char, size, freetype.FT_LOAD_RENDER)
plain = show(f"{folder}/unhinted/Plutto-{style}.ttf", char, size, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
width = max(len(row) for row in hinted) + 4
for index in range(max(len(hinted), len(plain))):
    left = hinted[index] if index < len(hinted) else ""
    right = plain[index] if index < len(plain) else ""
    print(f"{left:<{width}}{right}")
