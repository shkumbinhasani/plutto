import argparse
import atexit
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import freetype
import numpy
from fontTools.ttLib import TTFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from plutto.accents import ACCENTS, CARON_BASES, KERN_LIKE
from plutto.glyphs import GLYPHS
from plutto.hinting import AUTOHINTER, autohint
from plutto.masters import ALL_MASTERS
from rendering import closed_counters, mark_floor, strip_glyph_programs

STYLES = [master.name.replace(" ", "") for master in ALL_MASTERS]
SIZES = range(11, 17)
INK = 128
CLEAR_GAP = 64
MARKED = ["i", "j"] + sorted(name for name, letter in KERN_LIKE.items() if name.startswith(letter) and name[len(letter) :] in ACCENTS)
BESIDE_STEM = {f"{letter}caron" for letter in CARON_BASES}
COUNTED = [
    "a", "aacute", "agrave", "acircumflex", "adieresis", "atilde", "aring", "e", "g", "o", "oslash",
    "six", "eight", "nine", "zero", "A", "B", "P", "R", "ampersand", "ae", "oe", "four", "at",
]
TEXT = "Hamburgefonstiv quick zephyrs blow, vexing daft Jim"
EIGHT_NEIGHBOURS = numpy.ones((3, 3))
HINTED = freetype.FT_LOAD_RENDER
UNHINTED = freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING


def face_at(path, size):
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, size)
    return face


def bitmap(face, index, flags):
    face.load_glyph(index, flags)
    b = face.glyph.bitmap
    if not b.rows or not b.width:
        return numpy.zeros((1, 1), dtype=numpy.uint8)
    return numpy.array(b.buffer, dtype=numpy.uint8).reshape(b.rows, b.pitch)[:, : b.width]


def joined(face, data, floor, threshold):
    ink = data >= threshold
    labels = ndimage.label(ink, structure=EIGHT_NEIGHBOURS)[0]
    top = face.glyph.bitmap_top
    above = [row for row in range(ink.shape[0]) if top - row - 1 >= floor + 0.5]
    deep = [row for row in range(ink.shape[0]) if top - row <= floor - 1]
    marks = {label for row in above for label in labels[row] if label}
    return any(label in marks for row in deep for label in labels[row])


def parts(data, threshold):
    return ndimage.label(data >= threshold, structure=EIGHT_NEIGHBOURS)[1]


def joins(hinted, source, unhinted_ink, sizes=SIZES):
    font = TTFont(source)
    order = font.getGlyphOrder()
    units = font["head"].unitsPerEm
    floors = {name: mark_floor(font, name) for name in MARKED if name not in BESIDE_STEM}
    found = []
    for size in sizes:
        fitted, plain = face_at(hinted, size), face_at(source, size)
        for name in MARKED:
            index = order.index(name)
            if name in BESIDE_STEM:
                if parts(bitmap(fitted, index, HINTED), INK) < parts(bitmap(plain, index, UNHINTED), unhinted_ink):
                    found.append(f"{size}:{name}")
                continue
            floor = floors[name] * size / units
            if joined(fitted, bitmap(fitted, index, HINTED), floor, INK) and not joined(plain, bitmap(plain, index, UNHINTED), floor, unhinted_ink):
                found.append(f"{size}:{name}")
    return found


def size_range(text):
    low, _, high = text.partition("-")
    return range(int(low), int(high or low) + 1)


def closed(hinted, work, sizes=SIZES):
    reference = strip_glyph_programs(hinted, work / f"stripped-{hinted.name}")
    return [f"{size}:{name}" for size in sizes for name in COUNTED if closed_counters(hinted, reference, chr(GLYPHS[name][0]), size)]


def text_ink(path, size, flags):
    face = face_at(path, size)
    total = 0
    for char in TEXT:
        face.load_char(char, flags)
        total += int(bitmap(face, face.get_char_index(char), flags).sum())
    return total / 255


def main():
    parser = argparse.ArgumentParser(description="Compare hinted statics with their unhinted sources, at 11-16 px unless --sizes says otherwise.")
    parser.add_argument("source", type=Path, help="folder with the unhinted statics")
    parser.add_argument("--hinted", type=Path, help="folder with hinted statics; without it, the script hints the sources")
    parser.add_argument("--options", help="ttfautohint options to use instead of the build's settings and counter deltas")
    parser.add_argument("--styles", default=",".join(STYLES))
    parser.add_argument("--clear", type=int, default=INK, help=f"ink level that bridges an unhinted gap; {CLEAR_GAP} counts only clean gaps")
    parser.add_argument("--sizes", type=size_range, default=SIZES, help="pixel sizes to check, such as 11-18")
    args = parser.parse_args()
    work = Path(tempfile.mkdtemp(prefix="plutto-joins-"))
    atexit.register(shutil.rmtree, work, ignore_errors=True)
    for style in args.styles.split(","):
        source = args.source / f"Plutto-{style}.ttf"
        if args.hinted:
            hinted = args.hinted / source.name
        else:
            hinted = work / source.name
            if args.options:
                subprocess.run([AUTOHINTER, *args.options.split(), str(source), str(hinted)], check=True)
            else:
                autohint(source, hinted, AUTOHINTER)
        found = joins(hinted, source, args.clear, args.sizes)
        shut = closed(hinted, work, args.sizes)
        ink = " ".join(f"{text_ink(hinted, size, HINTED) / text_ink(source, size, UNHINTED):.3f}" for size in args.sizes)
        print(f"{style:12} joins {len(found):3} closed counters {len(shut):3} ink {ink}")
        print(f"{'':12} joined: {' '.join(found)}")
        print(f"{'':12} closed: {' '.join(shut)}")


if __name__ == "__main__":
    main()
