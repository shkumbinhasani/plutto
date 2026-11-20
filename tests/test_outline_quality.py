import json
import math
import unittest
from pathlib import Path

from support import ALL_STYLES, font, unhinted_path

from fontTools.ttLib import TTFont

DELIBERATE_CORNERS = json.loads((Path(__file__).parent / "deliberate_corners.json").read_text())
LEAN_RANGE = (1, 3)
LEAN_RATIO = 20
WOBBLE_TURN = math.radians(12)
WOBBLE_REACH = 3
WOBBLE_RUN = 20
JAG_ANGLE = math.radians(25)
SMOOTH = math.radians(5)


def contours(table, name):
    coordinates, ends, flags = table[name].getCoordinates(table)
    start = 0
    for end in ends:
        yield [((float(x), float(y)), flags[index] & 1) for index, (x, y) in enumerate(coordinates[start : end + 1], start)]
        start = end + 1


def segments(contour):
    if not any(on for _, on in contour):
        first, last = contour[0][0], contour[-1][0]
        contour = [(((first[0] + last[0]) / 2, (first[1] + last[1]) / 2), 1)] + contour
    shift = next(index for index, (_, on) in enumerate(contour) if on)
    ring = contour[shift:] + contour[:shift]
    found, current = [], [ring[0][0]]
    for point, on in ring[1:] + ring[:1]:
        if on:
            found.append(current + [point])
            current = [point]
            continue
        if len(current) > 1:
            middle = ((current[-1][0] + point[0]) / 2, (current[-1][1] + point[1]) / 2)
            found.append(current + [middle])
            current = [middle]
        current.append(point)
    return found


def vector(a, b):
    return b[0] - a[0], b[1] - a[1]


def angle(u, v):
    lengths = math.hypot(*u) * math.hypot(*v)
    if not lengths:
        return None
    return math.acos(max(-1.0, min(1.0, (u[0] * v[0] + u[1] * v[1]) / lengths)))


def tangent(segment, end):
    points = segment if end else segment[::-1]
    for point in points[1:]:
        if point != points[0]:
            return vector(points[0], point)
    return (0.0, 0.0)


def flowing(pieces, index):
    piece = pieces[index]
    before, after = pieces[index - 1], pieces[(index + 1) % len(pieces)]
    if len(before) == 2 or len(after) == 2:
        return False
    line = vector(*piece)
    turns = (angle(tangent(before, False), (-line[0], -line[1])), angle(line, tangent(after, True)))
    return all(turn is not None and turn < SMOOTH for turn in turns)


def leaning_lines(pieces, upright):
    found = []
    for index, piece in enumerate(pieces):
        if len(piece) != 2 or flowing(pieces, index):
            continue
        dx, dy = vector(*piece)
        for small, big, kind in ((abs(dy), abs(dx), "horizontal"), (abs(dx), abs(dy), "vertical")):
            if kind == "vertical" and not upright:
                continue
            if LEAN_RANGE[0] <= small <= LEAN_RANGE[1] and big >= LEAN_RATIO * small:
                found.append(f"{kind} line {piece[0]}-{piece[1]} leans {small:g}")
    return found


def wobbles(pieces):
    found = []
    for before, after in zip(pieces[-1:] + pieces[:-1], pieces):
        if len(before) != 2 or len(after) != 2:
            continue
        if min(math.hypot(*vector(*before)), math.hypot(*vector(*after))) < WOBBLE_RUN:
            continue
        turn = angle(vector(*before), vector(*after))
        if not turn or turn > WOBBLE_TURN:
            continue
        chord = vector(before[0], after[1])
        off = abs(chord[0] * (before[1][1] - before[0][1]) - chord[1] * (before[1][0] - before[0][0])) / math.hypot(*chord)
        if 0 < off <= WOBBLE_REACH:
            found.append(f"{before[0]}-{before[1]}-{after[1]} bends {math.degrees(turn):.1f} degrees")
    return found


def jags(pieces):
    found = []
    for before, after in zip(pieces[-1:] + pieces[:-1], pieces):
        back = tangent(before, False)
        turn = angle(back, tangent(after, True))
        if turn and turn < JAG_ANGLE:
            found.append(f"{before[-1]} turns back at {math.degrees(turn):.1f} degrees")
    return found


def problems(built, name, upright):
    table = built["glyf"]
    leaning, wobbling, jagged = [], [], []
    for contour in contours(table, name):
        pieces = segments(contour)
        leaning += leaning_lines(pieces, upright)
        wobbling += wobbles(pieces)
        jagged += jags(pieces)
    return leaning, wobbling, jagged


class OutlineQualityTest(unittest.TestCase):
    def test_statics_have_clean_lines_and_corners(self):
        for style in ALL_STYLES:
            built = TTFont(unhinted_path(style))
            upright = not built["post"].italicAngle
            leaning, wobbling, jagged = {}, {}, {}
            for name in built.getGlyphOrder():
                if built["glyf"][name].numberOfContours == 0:
                    continue
                lines, bends, corners = problems(built, name, upright)
                if lines:
                    leaning[name] = lines
                if bends:
                    wobbling[name] = bends
                if corners and name not in DELIBERATE_CORNERS:
                    jagged[name] = corners
            with self.subTest(style=style, defect="lines off true by 1 to 3 units"):
                self.assertEqual(leaning, {})
            with self.subTest(style=style, defect="wobbling straight edges"):
                self.assertEqual(wobbling, {})
            with self.subTest(style=style, defect="jaggy corners"):
                self.assertEqual(jagged, {})

    def test_deliberate_corners_are_still_drawn(self):
        names = set(font(ALL_STYLES[0]).getGlyphOrder())
        self.assertEqual(sorted(set(DELIBERATE_CORNERS) - names), [])


if __name__ == "__main__":
    unittest.main()
