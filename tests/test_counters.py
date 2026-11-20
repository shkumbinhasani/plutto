import re
import unittest
from dataclasses import replace
from functools import cache

import numpy
from PIL import Image, ImageDraw

from plutto.glyphs import render
from plutto.masters import ALL_MASTERS, ITALIC_MASTERS, default_of, family

SCALE = 0.25
CURVE_STEPS = 12
MARGIN = 8
INK = 255
BLANK = re.compile(b"\x00+")
PINHOLE = 4
NOTCH = 16
SMALLEST_SHARE = 0.12
ITALIC_SHARE = 0.75
APERTURE_RADIUS = 5
COUNTER_GLYPHS = [
    "a", "e", "g", "four", "six", "nine", "eight", "A", "B", "R", "section", "ae", "oe", "aring", "AE",
    "eth", "oslash", "Oslash", "perthousand", "infinity", "ordfeminine", "at", "zero.slash", "zero.numr.slash",
    "four.numr", "six.dnom",
]
APERTURE_GLYPHS = [
    "a", "c", "e", "s", "two", "three", "five", "six", "C", "G", "J", "S", "dollar", "section", "oe",
    "germandbls", "eth", "question",
]


def flatten(contour):
    points = [contour.start]
    here = contour.start
    for segment in contour.segments:
        if len(segment) == 1:
            points.append(segment[0])
        else:
            first, second, end = segment
            for step in range(1, CURVE_STEPS + 1):
                t = step / CURVE_STEPS
                u = 1 - t
                points.append(tuple(
                    u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d
                    for a, b, c, d in zip(here, first, second, end)
                ))
        here = segment[-1]
    return points


def edges_of(polygons):
    return [
        (x0, y0, x1, y1)
        for polygon in polygons
        for (x0, y0), (x1, y1) in zip(polygon, polygon[1:] + polygon[:1])
        if y0 != y1
    ]


@cache
def raster(name, master):
    glyph = render(name, master)
    polygons = [[(x * SCALE, y * SCALE) for x, y in flatten(contour.oriented())] for contour in glyph.contours]
    xs = [x for polygon in polygons for x, _ in polygon]
    ys = [y for polygon in polygons for _, y in polygon]
    left, bottom = int(min(xs)) - MARGIN, int(min(ys)) - MARGIN
    width, height = int(max(xs)) - left + MARGIN, int(max(ys)) - bottom + MARGIN
    image = Image.new("L", (width, height), 0)
    pen = ImageDraw.Draw(image)
    edges = edges_of(polygons)
    for row in range(height):
        y = bottom + row + 0.5
        crossings = sorted(
            (x0 + (y - y0) * (x1 - x0) / (y1 - y0), 1 if y1 > y0 else -1)
            for x0, y0, x1, y1 in edges
            if min(y0, y1) <= y < max(y0, y1)
        )
        winding = 0
        for (x, direction), (following, _) in zip(crossings, crossings[1:]):
            winding += direction
            if winding and following - x >= 0.5:
                line = height - 1 - row
                pen.line([(round(x - left), line), (round(following - left) - 1, line)], fill=INK)
    return image


def white_runs(image):
    width, height = image.size
    data = image.tobytes()
    return [
        [(match.start(), match.end()) for match in BLANK.finditer(data, row * width, (row + 1) * width)]
        for row in range(height)
    ]


def root(parents, index):
    while parents[index] != index:
        parents[index] = parents[parents[index]]
        index = parents[index]
    return index


def counters(image):
    width, height = image.size
    rows = white_runs(image)
    parents, sizes, outside = [], [], set()
    previous = []
    for row, runs in enumerate(rows):
        current = []
        for start, end in runs:
            index = len(parents)
            parents.append(index)
            sizes.append(end - start)
            left, right = start - row * width, end - row * width
            if row in (0, height - 1) or left == 0 or right == width:
                outside.add(index)
            for other, other_left, other_right in previous:
                if other_left < right and left < other_right:
                    parents[root(parents, other)] = root(parents, index)
            current.append((index, left, right))
        previous = current
    totals = {}
    for index in range(len(parents)):
        top = root(parents, index)
        totals[top] = totals.get(top, 0) + sizes[index]
    border = {root(parents, index) for index in outside}
    return sorted(size for top, size in totals.items() if top not in border and size >= PINHOLE)


def thickened(image, radius):
    ink = numpy.asarray(image) > 0
    height, width = ink.shape
    padded = numpy.pad(ink, radius)
    spread = numpy.zeros_like(ink)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                spread |= padded[radius + dy : radius + dy + height, radius + dx : radius + dx + width]
    return Image.fromarray(numpy.where(spread, INK, 0).astype(numpy.uint8))


class CounterTest(unittest.TestCase):
    def test_masters_keep_the_regular_counters(self):
        for name in COUNTER_GLYPHS:
            for master in ALL_MASTERS:
                regular = counters(raster(name, default_of(family(master))))
                with self.subTest(glyph=name, master=master.name):
                    found = counters(raster(name, master))
                    self.assertEqual(len(found), len(regular), f"{name} {master.name} counters {found} against Regular {regular}")
                    if master.italic:
                        continue
                    for size, regular_size in zip(found, regular):
                        self.assertGreaterEqual(size / regular_size, SMALLEST_SHARE, f"{name} {master.name} counters {found} against Regular {regular}")

    def test_italic_keeps_the_roman_counters(self):
        for name in COUNTER_GLYPHS:
            for italic in ITALIC_MASTERS:
                roman = replace(italic, slant=0)
                upright = counters(raster(name, roman))
                slanted = counters(raster(name, italic))
                with self.subTest(glyph=name, master=italic.name):
                    for size, upright_size in zip(slanted, upright):
                        self.assertGreaterEqual(size / upright_size, ITALIC_SHARE, f"{name} {italic.name} counters {slanted} against {roman.name} {upright}")

    def test_apertures_stay_open(self):
        for name in APERTURE_GLYPHS:
            for master in ALL_MASTERS:
                with self.subTest(glyph=name, master=master.name):
                    image = raster(name, master)
                    closed = [size for size in counters(thickened(image, APERTURE_RADIUS)) if size >= NOTCH]
                    self.assertLessEqual(len(closed), len(counters(image)), f"{name} {master.name} closes an aperture narrower than {2 * APERTURE_RADIUS / SCALE:.0f} units")


if __name__ == "__main__":
    unittest.main()
