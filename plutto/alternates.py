import math
import unicodedata
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from functools import lru_cache

from . import accents, capitals, figures, lowercase, marks, symbols
from .geometry import Path, split
from .masters import ASC, CAP, DESC, XH, Master, family, interpolate, roman_of
from .names import DIGITS, LETTERS
from .oblique import Overlaid, slanted, sheared
from .parts import Glyph, band, band_width, hook, spaced
from .shapes import Node, aim, mirror, oval, polygon, rect, ribbon, ring, shift, turn

DOWN = (0, -1)
UP = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
SMALL_SCALE = 0.54
SLASH_CORNER_KEEP = 0.05
FRACTION_GAP = 26
FRACTION_CLEARANCE = 44
FRACTION_TOLERANCE = 10
FRACTION_PULL = 80
FRACTION_DEEPEST = 3 * FRACTION_PULL
FRACTION_REFERENCE = "H"
DEEP_NEAREST = 2
DEEP_AVERAGE = 0.9
FIGURE_DEPTH = 280
FIGURE_BLEND = 0.6
NUMERATOR_BASE = CAP - CAP * SMALL_SCALE
SUBSCRIPT_BASE = -140
SUBSCRIPT_CODE = 0x2080
SUBSCRIPT_MARKS = {"plus": 0x208A, "minus": 0x208B, "parenleft": 0x208D, "parenright": 0x208E}
SUBSCRIPT_SOURCES = {"hyphen": "minus.subs", "minus": "minus.subs", "plus": "plus.subs", "parenleft": "parenleft.subs", "parenright": "parenright.subs"}
SUPERIORS = {"one": ("onesuperior", 0xB9), "two": ("twosuperior", 0xB2), "three": ("threesuperior", 0xB3)}
VULGAR_FRACTIONS = {
    "onehalf": (0xBD, "one", "two"),
    "onequarter": (0xBC, "one", "four"),
    "threequarters": (0xBE, "three", "four"),
    "uni2150": (0x2150, "one", "seven"),
    "uni2151": (0x2151, "one", "nine"),
    "uni2152": (0x2152, "one", "one zero"),
    "onethird": (0x2153, "one", "three"),
    "twothirds": (0x2154, "two", "three"),
    "uni2155": (0x2155, "one", "five"),
    "uni2156": (0x2156, "two", "five"),
    "uni2157": (0x2157, "three", "five"),
    "uni2158": (0x2158, "four", "five"),
    "uni2159": (0x2159, "one", "six"),
    "uni215A": (0x215A, "five", "six"),
    "oneeighth": (0x215B, "one", "eight"),
    "threeeighths": (0x215C, "three", "eight"),
    "fiveeighths": (0x215D, "five", "eight"),
    "seveneighths": (0x215E, "seven", "eight"),
    "uni2189": (0x2189, "zero", "three"),
}

TALL_CENTRE = (marks.TALL_TOP + marks.TALL_BOTTOM) / 2
CAPITAL_CENTRE = CAP / 2
LOWERCASE_TO_CAPITAL = (CAP - XH) / 2
CASE_LIFTS = {
    "parenleft": CAPITAL_CENTRE - TALL_CENTRE,
    "parenright": CAPITAL_CENTRE - TALL_CENTRE,
    "bracketleft": CAPITAL_CENTRE - TALL_CENTRE,
    "bracketright": CAPITAL_CENTRE - TALL_CENTRE,
    "braceleft": CAPITAL_CENTRE - TALL_CENTRE,
    "braceright": CAPITAL_CENTRE - TALL_CENTRE,
    "hyphen": CAPITAL_CENTRE - marks.AXIS,
    "endash": CAPITAL_CENTRE - marks.AXIS,
    "emdash": CAPITAL_CENTRE - marks.AXIS,
    "periodcentered": CAPITAL_CENTRE - marks.AXIS,
    "guilsinglleft": CAPITAL_CENTRE - marks.AXIS,
    "guilsinglright": CAPITAL_CENTRE - marks.AXIS,
    "guillemotleft": CAPITAL_CENTRE - marks.AXIS,
    "guillemotright": CAPITAL_CENTRE - marks.AXIS,
    "bullet": CAPITAL_CENTRE - marks.AXIS,
    "at": LOWERCASE_TO_CAPITAL,
    "plus": CAPITAL_CENTRE - symbols.MATH,
    "equal": CAPITAL_CENTRE - symbols.MATH,
    "less": CAPITAL_CENTRE - symbols.MATH,
    "greater": CAPITAL_CENTRE - symbols.MATH,
    "minus": CAPITAL_CENTRE - symbols.MATH,
    "multiply": CAPITAL_CENTRE - symbols.MATH,
    "divide": CAPITAL_CENTRE - symbols.MATH,
    "plusminus": CAPITAL_CENTRE - symbols.MATH,
    "asciitilde": CAPITAL_CENTRE - symbols.MATH,
    "logicalnot": CAPITAL_CENTRE - symbols.MATH,
    "arrowleft": CAPITAL_CENTRE - symbols.MATH,
    "arrowright": CAPITAL_CENTRE - symbols.MATH,
    "arrowboth": CAPITAL_CENTRE - symbols.MATH,
    "arrowdblleft": CAPITAL_CENTRE - symbols.MATH,
    "arrowdblright": CAPITAL_CENTRE - symbols.MATH,
    "arrowdblboth": CAPITAL_CENTRE - symbols.MATH,
    "exclamdown": CAP - XH,
    "questiondown": CAP - XH,
    "colon": LOWERCASE_TO_CAPITAL,
}
CASE_SPACED_ALONE = {"guilsinglleft", "guilsinglright", "guillemotleft", "guillemotright"}
CASE_KERN_LIKE = {name: symbols.KERN_LIKE.get(name, name) for name in CASE_LIFTS if name not in CASE_SPACED_ALONE}
SUPERIOR_MARKS = {"minus": 0x207B, "plus": 0x207A, "parenleft": 0x207D, "parenright": 0x207E}
SUPERIOR_SOURCES = {"hyphen": "minus.sups", "minus": "minus.sups", "plus": "plus.sups", "parenleft": "parenleft.sups", "parenright": "parenright.sups"}
SUPERIOR_CODES = {"zero": 0x2070, "four": 0x2074, "five": 0x2075, "six": 0x2076, "seven": 0x2077, "eight": 0x2078, "nine": 0x2079}
def composed_root(name):
    while name in accents.COMPOSED:
        name = accents.COMPOSED[name][0]
    return name


def composed_marks(name):
    found = []
    while name in accents.COMPOSED:
        name, mark = accents.COMPOSED[name]
        found.append(mark)
    return found


SINGLE_STOREY_ROOTS = ("a", "ae")
TAILLESS_ROOTS = ("l",)
TAILLESS_EXTRAS = ("ldot", "lslash")
BESIDE_SHARE = 0.9
SINGLE_STOREY_BASED = [name for name in accents.COMPOSED if composed_root(name) in SINGLE_STOREY_ROOTS and name in accents.GLYPHS]
TAILLESS_BASED = [name for name in accents.COMPOSED if composed_root(name) in TAILLESS_ROOTS and name in accents.GLYPHS] + list(TAILLESS_EXTRAS)
SINGLE_STOREY_AE_BOWL = (440, 508)
SINGLE_STOREY_AE_EYE = (424, 486, None, 556)
SINGLE_STOREY_FAMILY = [f"{name}.ss01" for name in SINGLE_STOREY_BASED]
ORDINALS = {"a": "ordfeminine", "a.ss01": "ordfeminine.ss01", "o": "ordmasculine"}
NUMERO = "uni2116"
PUNT_VOLAT = "periodcentered.loclCAT"
PUNT_GAP = (58, 50, 62, 42)
PUNT_LEAST = 20
PUNT_HEIGHT = (262, 282, 262, 312)
PUNT_CAP_GAP = (66, 56, 70, 48)
PUNT_CAP_ADVANCE = (60, 52, 62, 44)
LANGUAGES = ("CAT",)
TURKIC_LANGUAGES = ("TRK", "AZE", "CRT", "KAZ", "TAT")
LANGUAGES += TURKIC_LANGUAGES
TURKIC_I = "i.loclTRK"
SERIF_SMALL_CAP = "I.cv02.sc"
ONE_BASE = (166, 178, 158, 196)
SERIF_HALF = (152, 170, 144, 192)
SERIF_BAR = (1.0, 0.9, 1.0, 0.8)
SERIF_SIDE = (40, 30, 42, 22)
OPEN_FOUR_GAP = (64, 58, 66, 50)
OPEN_FOUR_STEM = (590, 580, 594, 566)
STRAIGHT_SIX_TOP = (0.64, 0.62, 0.65, 0.6)
STRAIGHT_SIX_LEAN = (0.18, 0.17, 0.19, 0.15)
STRAIGHT_SIX_BACK = (300, 290, 304, 280)
STRAIGHT_SIX_BOWL = (440, 452, 436, 456)
FLAT_THREE_BAR = (1.0, 0.92, 1.0, 0.84)
FLAT_THREE_REACH = (0.92, 0.92, 0.92, 0.94)
FLAT_THREE_APEX = 0.6
FLAT_THREE_LEAN = (56, 58, 58, 60)
FLAT_THREE_DIAGONAL = (0.96, 0.9, 0.98, 0.84)
FLAT_THREE_BOWL = (470, 474, 468, 490)
FLAT_THREE_JOIN = 0.4
FLAT_THREE_DROP = 0.9
FLAT_THREE_RISE = 30
BINOCULAR_WIDTH = (476, 552, 458, 620)
BINOCULAR_BOWL = ((0.08, 0.07, 0.09, 0.06), (0.84, 0.86, 0.83, 0.88))
BINOCULAR_WAIST = (176, 190, 170, 184)
BINOCULAR_LOOP = (72, 92, 66, 112)
BINOCULAR_THIN = (0.92, 0.84, 0.95, 0.8)
BINOCULAR_LOOP_THIN = (0.9, 0.8, 0.95, 0.72)
BINOCULAR_SIDE = (0.94, 0.9, 0.96, 0.88)
BINOCULAR_EAR = 6
BINOCULAR_LINK = (0.86, 0.82, 0.9, 0.8)
BINOCULAR_NECK = 0.46
BINOCULAR_NECK_ANGLE = 242
BINOCULAR_JOIN = 0.5
BINOCULAR_PULL = 0.6
ARROWS = {
    ("less", "hyphen", "greater"): "arrowboth",
    ("less", "hyphen"): "arrowleft",
    ("hyphen", "greater"): "arrowright",
    ("equal", "greater"): "arrowdblright",
}
VARIANTS = {
    "cv01": ("1 with base", 0x31, {"one": "one.cv01", "one.tnum": "one.tnum.cv01"}),
    "cv02": ("I with serifs", 0x49, {"I": "I.cv02"}),
    "cv03": ("Open 4", 0x34, {"four": "four.cv03", "four.tnum": "four.tnum.cv03"}),
    "cv04": ("6 with straight tail", 0x36, {"six": "six.cv04", "six.tnum": "six.tnum.cv04"}),
    "cv05": ("9 with straight tail", 0x39, {"nine": "nine.cv05", "nine.tnum": "nine.tnum.cv05"}),
    "cv06": ("Double-storey g", 0x67, {"g": "g.cv06"}),
    "cv07": ("3 with flat top", 0x33, {"three": "three.cv07", "three.tnum": "three.tnum.cv07"}),
    "cv08": ("t without left spur", 0x74, {"t": "t.cv08", "tcaron": "tcaron.cv08", "tbar": "tbar.cv08"}),
}
SERIF_I = "I.cv02"
DOUBLE_STOREY_G = "g.cv06"
SPURLESS_T = "t.cv08"
MARK_TWINS = {SERIF_I: "I", DOUBLE_STOREY_G: "g", SPURLESS_T: "t", "a.ss01": "a", "l.ss02": "l", "i.loclTRK": "i", "I.cv02.sc": "i"}
SMALL_CAP = ".sc"
SMALL_CAP_HEIGHT = XH + 32
SMALL_CAP_WIDTH = 0.88
SMALL_CAP_WEIGHT = 1.03
SMALL_CAP_EXTRAS = {"AE": "ae", "OE": "oe", "Oslash": "oslash", "Eth": "eth", "Thorn": "thorn", "Lslash": "lslash", "Eng": "eng", "Hbar": "hbar", "Dcroat": "dcroat", "Tbar": "tbar", "Ldot": "ldot", "Gstroke": "gstroke", "Ezh": "ezh", "IJ": "ij", "Eopen": "eopen", "Oopen": "oopen", "Bhook": "bhook", "Dhook": "dhook", "Yhook": "yhook"}
SMALL_CAP_EXTRAS.update({"Schwa": "schwa", "Ereversed": "eturned", "Nhookleft": "nhookleft", "Khook": "khook", "Fhook": "florin", "Gammaafrican": "gammalatinsmall", "Vhook": "vhook"})
NO_EASE = (1, 1, 1, 1)
SMALL_CAP_EASE = {"Eopen": ((1, 1, 1, 0.86), NO_EASE), "Yhook": ((1, 0.9, 1, 0.92), (1, 0.9, 1, 0.88))}
SMALL_CAP_ALIASES = {"longs": "S", "dotlessi": "I", "dotlessj": "J", "dtail": "Dcroat"}
SMALL_CAP_UPPER = {"Dafrican": "Dcroat.sc"}
SMALL_CAP_MARKED = {"ezhcaron": ("Ezh.sc", "caroncomb"), "Ezhcaron": ("Ezh.sc", "caroncomb")}
SMALL_CAP_MARKED.update({name: ("D.sc", "Z.sc", "caroncomb") for name in ("DZcaron", "dzcaron")})
SMALL_CAP_MARKED.update({name: ("D.sc", "Z.sc") for name in ("DZ", "dz")})
SMALL_CAP_MARKED.update({name: (f"{name[0].upper()}.sc", "J.sc") for name in ("LJ", "lj", "NJ", "nj")})
SMALL_CAP_MARKED.update({"fi": ("F.sc", "I.sc"), "fl": ("F.sc", "L.sc"), "napostrophe": ("quoteright", "N.sc")})
SMALL_CAP_LETTERS = {letter.upper(): letter for letter in LETTERS}
SMALL_CAP_LETTERS.update(SMALL_CAP_EXTRAS)
MARK_TWINS.update({f"{capital}{SMALL_CAP}": lower for capital, lower in SMALL_CAP_LETTERS.items()})
DOUBLE_S = ("germandbls", "Germandbls")
SMALL_CAP_PUNCTUATION = ("dot", "dash", "quote", "guillemet")
CAPITAL_SPACING = (10, 8, 12, 6)
DISAMBIGUATION_SET = "ss04"
DISAMBIGUATION_LABEL = "Disambiguation"
DISAMBIGUATION = {"one": "one.cv01", "one.tnum": "one.tnum.cv01", "I": SERIF_I, "zero": "zero.slash", "zero.tnum": "zero.tnum.slash", "l.ss02": "l"}
DISAMBIGUATION.update({f"{name}.ss02": name for name in TAILLESS_BASED})
OLDSTYLE = ".osf"
TABULAR_OLDSTYLE = ".tosf"
DECOMPOSED_VARIANTS = {"cv02": SERIF_I, "cv06": DOUBLE_STOREY_G, "cv08": SPURLESS_T}
VARIANT_LIGATURES = {"cv08": {("t", accents.CARON_SHORT): "tcaron.cv08"}}
ARROWS_SET = "ss03"
TABULAR_PUNCTUATION = ["comma", "period", "colon", "semicolon"]
TABULAR_COLON_CASE = "colon.tab.case"
PUNCTUATION_SPACE = "uni2008"
CASE_BETWEEN = ["hyphen", "endash", "emdash", "colon", "colon.tab", "hyphen.tab"]
TABULAR_CASE = {"colon.tab": TABULAR_COLON_CASE, "hyphen.tab": "hyphen.tab.case"}
CASE_SPACED = ["hyphen", "endash", "emdash"]
CASE_OPENING = ["parenleft", "bracketleft", "braceleft", "guillemotleft", "guillemotright", "guilsinglleft", "guilsinglright", "at"]
CASE_CLOSING = ["parenright", "bracketright", "braceright", "guillemotleft", "guillemotright", "guilsinglleft", "guilsinglright"]
ARROWS_LABEL = "Arrows and multiplication sign"
SMALL_CAP_SOURCES = ["smcp", "c2sc"]
ALTERNATE_SOURCES = ["tnum", "pnum", "onum", "lnum", "case", "zero", "sups", "subs", "sinf", "numr", "dnom", "frac", "ordn", "locl", "ss01", "ss02", ARROWS_SET, DISAMBIGUATION_SET]


def bezier_point(bezier, t):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = bezier
    s = 1 - t
    a, b, c, d = s * s * s, 3 * s * s * t, 3 * s * t * t, t * t * t
    return (a * x0 + b * x1 + c * x2 + d * x3, a * y0 + b * y1 + c * y2 + d * y3)


def outline_points(contour, steps=64):
    here = contour.start
    for segment in contour.segments:
        if len(segment) == 1:
            yield here
        else:
            bezier = (here, *segment)
            for index in range(steps):
                yield bezier_point(bezier, index / steps)
        here = segment[-1]
    if here != contour.start:
        yield here


def reach(contour, centre, direction):
    nx, ny = -direction[1], direction[0]
    points = list(outline_points(contour))
    best = None
    for index, a in enumerate(points):
        b = points[(index + 1) % len(points)]
        side_a = (a[0] - centre[0]) * nx + (a[1] - centre[1]) * ny
        side_b = (b[0] - centre[0]) * nx + (b[1] - centre[1]) * ny
        if side_a * side_b > 0 or side_a == side_b:
            continue
        t = side_a / (side_a - side_b)
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        distance = (x - centre[0]) * direction[0] + (y - centre[1]) * direction[1]
        if distance > 0 and (best is None or distance < best):
            best = distance
    return best


def box(contour):
    corners = list(contour.corners())
    xs = [point[0] for point in corners]
    ys = [point[1] for point in corners]
    return min(xs), min(ys), max(xs), max(ys)


def slash_direction(inner, lean, m):
    inner_left, inner_bottom, inner_right, inner_top = box(inner)
    rise = inner_top - inner_bottom
    angle = math.atan2(rise, (inner_right - inner_left) * lean) - math.radians(m.slant)
    return math.cos(angle), math.sin(angle)


def slash_end(outer, inner, centre, direction, across):
    inside = reach(inner, centre, direction)
    outside = reach(outer, centre, direction)
    ring = outside - inside
    ends = [inside + ring * 0.5]
    for heading in (direction, (-direction[0], -direction[1])):
        for side in (-across, across):
            corner = (centre[0] + side, centre[1])
            ends.append(reach(outer, corner, heading) - ring * SLASH_CORNER_KEEP)
    return min(ends)


def slash_through(outer, inner, thickness, lean, m, drawn=None):
    drawn_outer, drawn_inner = drawn or (outer, inner)
    left, bottom, right, top = box(outer)
    centre = sheared(((left + right) / 2, (bottom + top) / 2), m.slope)
    direction = slash_direction(inner, lean, m)
    across = thickness / direction[1] / 2
    distance = slash_end(drawn_outer, drawn_inner, centre, direction, across)
    dx, dy = direction[0] * distance, direction[1] * distance
    upper = (centre[0] + dx, centre[1] + dy)
    lower = (centre[0] - dx, centre[1] - dy)
    return polygon(
        [
            (lower[0] - across, lower[1]),
            (upper[0] - across, upper[1]),
            (upper[0] + across, upper[1]),
            (lower[0] + across, lower[1]),
        ]
    )


def slash_lean(m):
    return m.v(1.08, 1.16, light=1.04, black=1.9)


def small_slash_lean(m):
    return m.v(1.08, 0.9, light=1.16, black=1.3)


def slash_weight(m):
    return m.v(78, 100, light=52, black=104)


def side_stroke(outer, inner):
    return box(inner)[0] - box(outer)[0]


def small_slash_weight(m, outer, inner):
    return slash_weight(m) * m.v(1, 1, black=1.15) / figures.side(m) * side_stroke(outer, inner)


def slashed_zero(m):
    plain = figures.slashed_zero_ring(m)
    outer, inner = plain.contours
    stroke = slash_through(outer, inner, slash_weight(m), slash_lean(m), m)
    return figures.Figure(plain.contours + [stroke], plain.width, plain.left, plain.right)


def zero_slash(m, upright, drawn):
    outer, inner = upright.contours
    return [slash_through(outer, inner, slash_weight(m), slash_lean(m), m, drawn.contours)]


def small_zero_slash(m, upright, drawn):
    outer, inner = upright.contours
    return [slash_through(outer, inner, small_slash_weight(m, outer, inner), small_slash_lean(m), m, drawn.contours)]


def case_source(name):
    return getattr(marks, name, None) or getattr(symbols, name)


def raised_for_capitals(draw, lift):
    def build(m):
        drawn = draw(m)
        return Glyph(shift(drawn.contours, 0, lift), drawn.advance)

    return build


def turkic_i(m):
    from .glyphs import GLYPHS as everything

    return everything["i"][1](m)


def single_storey_a(m):
    width = m.v(472, 540)
    shapes = [rect(width - m.stem, 0, width, XH)] + mirror(lowercase.bowl(m, width), width / 2)
    return spaced(m, shapes, width, "round", "straight")


def ink_x(contours):
    xs = [point[0] for contour in contours for point in contour.points()]
    return min(xs), max(xs)


def base_swapped(name, root, replacement):
    marks_along = composed_marks(name)

    def build(m):
        from .glyphs import GLYPHS as everything

        glyph = everything[name][1](m)
        old, new = everything[root][1](m), replacement(m)
        count = len(old.contours)
        base, added = glyph.contours[:count], glyph.contours[count:]
        offset = ink_x(base)[0] - ink_x(old.contours)[0]
        top = accents.top_x(root, new, m, False) - accents.top_x(root, old, m, False)
        if "ogonek" in marks_along:
            low = accents.ogonek_x(new, m, False) - accents.ogonek_x(old, m, False)
        elif "dotbelow" in marks_along:
            low = accents.dotbelow_x(new, m) - accents.dotbelow_x(old, m)
        else:
            low = accents.comma_x(new) - accents.comma_x(old)
        base_top = max(point[1] for contour in base for point in contour.points())
        moved, beside = [], []
        for contour in added:
            ys = [point[1] for point in contour.points()]
            placed = shift([contour], low if min(ys) < 0 else top if min(ys) >= base_top * BESIDE_SHARE else 0)
            moved += placed
            if 0 < min(ys) and max(ys) < base_top:
                beside += placed
        advance = glyph.advance + new.advance - old.advance
        if "caron" in marks_along and root in accents.CARON_BASES:
            advance = new.advance + accents.caron_room_for(root, new, m) + offset
        elif beside:
            advance = max(advance, ink_x(beside)[1] + glyph.advance - ink_x(glyph.contours)[1])
        return Glyph(shift(new.contours, offset) + moved, advance)

    return build


def single_storey_accented(name):
    root = composed_root(name)
    return base_swapped(name, root, single_storey_ae if root == "ae" else single_storey_a)


def tailless(name):
    return base_swapped(name, "l", l_without_tail)


def single_storey_ae(m):
    width = m.v(*SINGLE_STOREY_AE_BOWL)
    side = m.round
    crotches = ((side / 2, XH - m.v(*accents.OE_CROTCH)), (side / 2, m.v(*accents.OE_CROTCH)))
    inner_high = m.v(*accents.OE_INNER)
    eye = accents.joined_eye(m, m.v(*SINGLE_STOREY_AE_EYE), crotches, (XH - inner_high, inner_high))
    shapes = [rect(width - m.stem, 0, width, XH)] + mirror(lowercase.bowl(m, width), width / 2) + shift(eye, width - side)
    return spaced(m, shapes, width - side + m.v(*SINGLE_STOREY_AE_EYE), "round", m.v(30, 22))


def single_storey_ordinal(m):
    scale = symbols.ordinal_scale(m)
    stem = symbols.ordinal_stem(m)
    thin = symbols.ordinal_thin(m)
    width = m.v(472, 540, light=455, black=582) * scale
    height = XH * scale
    overshoot = m.ov * scale
    shapes = [
        rect(width - stem, 0, width, height),
        oval(0, -overshoot, width - stem * m.v(0.25, 0.42), height + overshoot, m.k_out),
        oval(stem * 1.02, thin, width - stem * m.v(0.80, 0.66, light=0.6), height - thin, m.k_in, hole=True),
    ]
    return spaced(m, shift(shapes, 0, CAP - height), width, m.v(40, 30), m.v(44, 34))


def punt_volat_parts(m):
    l = lowercase.letter_l(m)
    side = marks.square(m)
    middle = m.v(*PUNT_HEIGHT)
    gap = m.v(*PUNT_GAP)
    stem_left = accents.ink_runs(l.contours, middle)[0][0]
    points = accents.outline_array(l)
    right = points[points[:, 1] >= middle - side / 2 - gap / 2][:, 0].max()
    left = right + gap - l.advance
    return [rect(left, middle - side / 2, left + side, middle + side / 2)], left + side + gap - stem_left


def punt_volat(m):
    shapes, reach = punt_volat_parts(m)
    return Glyph(shapes, max(PUNT_LEAST, reach))


def l_kin():
    from .features import all_like

    return ["l"] + sorted(name for name, model in all_like().items() if model == "l")


def punt_volat_kern(m):
    reach = punt_volat_parts(m)[1]
    return reach - max(PUNT_LEAST, reach)


def punt_volat_case(m):
    capital = capitals.capital_l(m)
    side = marks.square(m)
    middle = CAPITAL_CENTRE
    _, stem_right = accents.ink_runs(capital.contours, middle)[0]
    left = stem_right + m.v(*PUNT_CAP_GAP) - capital.advance
    return Glyph([rect(left, middle - side / 2, left + side, middle + side / 2)], m.v(*PUNT_CAP_ADVANCE))


def one_with_base(m):
    drawn = figures.one(m)
    stem_left, _, stem_right, _ = box(drawn.contours[0])
    middle = (stem_left + stem_right) / 2
    half = m.v(*ONE_BASE)
    base = rect(middle - half, 0, middle + half, m.cap_bar)
    lead = max(0, half - middle)
    width = max(drawn.width, middle + half) + lead
    return figures.Figure(shift(drawn.contours + [base], lead), width, m.v(30, 22), m.v(30, 22))


def open_four(m):
    width = m.v(524, 568, light=506, black=620)
    stem = m.cap_stem
    bar = m.cap_bar * m.v(1, 0.86, light=1, black=0.76)
    post = width - stem - m.v(76, 60, light=79, black=38)
    shelf = m.v(168, 148, light=171, black=106)
    reach = post - m.v(*OPEN_FOUR_GAP)
    stroke = band_width(reach, CAP - shelf, m.cap_diag * m.v(1, 0.88, light=1, black=0.68))
    shapes = [
        rect(post, 0, post + stem, m.v(*OPEN_FOUR_STEM)),
        rect(0, shelf, width, shelf + bar),
        band((reach - stroke, CAP), (0, shelf), stroke),
    ]
    return figures.Figure(shapes, width, m.v(22, 16), m.v(28, 20))


def straight_six_shapes(m):
    width = figures.body(m)
    edge = figures.side(m)
    flat = m.cap_thin
    top = (width * m.v(*STRAIGHT_SIX_TOP), CAP)
    back_y = m.v(*STRAIGHT_SIX_BACK)
    bowl_top = m.v(*STRAIGHT_SIX_BOWL)
    low = (edge * 0.5 + width * m.v(*STRAIGHT_SIX_LEAN), bowl_top)
    heading = (low[0] - top[0], low[1] - top[1])
    shape = ribbon(
        [
            Node(top, heading, edge * m.v(0.96, 0.92), cut="h"),
            Node(low, heading, edge * m.v(0.96, 0.92), straight=True),
            Node((edge / 2, back_y * 0.8), DOWN, edge),
            Node((width * 0.5, flat / 2 - m.ov), RIGHT, flat),
            Node((width - edge / 2, back_y * 0.78), UP, edge),
            Node((width * 0.53, bowl_top - flat * 0.46), LEFT, flat * 0.92),
            Node((edge / 2 + (low[0] - edge / 2) * (back_y * 0.2) / (low[1] - back_y * 0.8), back_y), aim(m.v(238, 240)), m.v(50, 80, light=34, black=102), arrive=0.5),
        ],
        0.6,
    )
    return [shape], width


def straight_six(m):
    shapes, width = straight_six_shapes(m)
    return figures.Figure(shapes, width, m.v(36, 28), m.v(34, 26))


def straight_nine(m):
    shapes, width = straight_six_shapes(m)
    return figures.Figure(turn(shapes, width / 2, CAP / 2), width, m.v(34, 26), m.v(36, 28))


def side_of(line, point):
    (x, y), (dx, dy) = line
    return dx * (point[1] - y) - dy * (point[0] - x)


def crossing(start, segment, line, last=False):
    bezier = (start, *segment)
    steps = [index / 64 for index in range(65)]
    signs = [side_of(line, bezier_point(bezier, t)) for t in steps]
    changes = [index for index in range(64) if signs[index] * signs[index + 1] <= 0]
    index = changes[-1] if last else changes[0]
    low, high = steps[index], steps[index + 1]
    for _ in range(40):
        middle = (low + high) / 2
        if side_of(line, bezier_point(bezier, middle)) * signs[index] > 0:
            low = middle
        else:
            high = middle
    return split(bezier, (low + high) / 2)


def flat_three(m):
    width = figures.body(m)
    edge = figures.side(m)
    flat = m.cap_thin
    bar = m.cap_bar * m.v(*FLAT_THREE_BAR)
    right = width * m.v(*FLAT_THREE_REACH)
    lean = aim(180 + m.v(*FLAT_THREE_LEAN))
    thickness = m.cap_diag * m.v(*FLAT_THREE_DIAGONAL)
    outer_line = ((right, CAP - bar), lean)
    shift_x = thickness / abs(lean[1])
    inner_line = ((right - shift_x, CAP - bar), lean)
    bowl_top = m.v(*FLAT_THREE_BOWL)
    rise = aim(FLAT_THREE_RISE)
    low = bowl_top - flat * FLAT_THREE_DROP - rise[0] * flat / 2
    edge_x = right - shift_x + (CAP - bar - low) * lean[0] / -lean[1]
    junction = (edge_x - flat * FLAT_THREE_JOIN - rise[1] * flat / 2, low + rise[0] * flat / 2)
    bowl = ribbon(
        [
            Node(junction, rise, flat),
            Node((width * FLAT_THREE_APEX, bowl_top - flat / 2), RIGHT, flat),
            Node((width - edge / 2, m.v(222, 226)), DOWN, edge),
            Node((width * 0.48, flat / 2 - m.cap_ov), LEFT, flat),
            Node((m.v(46, 74), figures.terminal_low(m)), aim(m.v(118, 120)), m.v(80, 128, light=54, black=146), cut="h"),
        ],
        0.6,
    )
    corners = list(bowl.corners())
    _, after = crossing(corners[1], bowl.segments[1], outer_line)
    before, _ = crossing(corners[-2], bowl.segments[-1], inner_line, last=True)
    path = Path((0, CAP)).to((right, CAP)).to((right, CAP - bar)).to(after[0]).bez(after)
    path.segments.extend(bowl.segments[2:-1])
    path.bez(before)
    path.to((right - shift_x, CAP - bar)).to((0, CAP - bar))
    return figures.Figure([path.close()], width, m.v(40, 30), m.v(36, 28))


def double_storey_g(m):
    width = m.v(*BINOCULAR_WIDTH)
    thin = m.thin * m.v(*BINOCULAR_THIN)
    loop_thin = m.thin * m.v(*BINOCULAR_LOOP_THIN)
    side = m.round * m.v(*BINOCULAR_SIDE)
    left, right = (width * m.v(*share) for share in BINOCULAR_BOWL)
    middle = (left + right) / 2
    waist = m.v(*BINOCULAR_WAIST)
    loop_top = m.v(*BINOCULAR_LOOP)
    upper = ring(left, waist, right, XH + m.ov, side, thin, m.k_out, m.k_in)
    lower = ring(0, DESC - m.ov, width, loop_top, side, loop_thin, m.k_out, m.k_in)
    ear = rect(middle, XH + m.ov - thin + BINOCULAR_EAR, width, XH)
    link_width = m.thin * m.v(*BINOCULAR_LINK)
    link = ribbon(
        [
            Node((width * BINOCULAR_NECK, waist + thin * 0.5), aim(BINOCULAR_NECK_ANGLE), link_width, cut="h"),
            Node((width * BINOCULAR_JOIN, loop_top - loop_thin / 2), RIGHT, loop_thin * 0.7, cut="v"),
        ],
        BINOCULAR_PULL,
    )
    return spaced(m, upper + lower + [ear, link], width, "round", "round")


def spurless_t(m):
    stem = m.stem
    width = stem + m.v(104, 112, light=92)
    foot = hook(m, stem, m.thin, XH + m.v(132, 128), width, lowercase.hook_inner(m))
    return spaced(m, [foot, rect(stem / 2, XH - m.bar, width, XH)], width, "straight", m.v(22, 14), capital=False)


def spurless_t_caron():
    def widened(m):
        glyph = spurless_t(m)
        return Glyph(glyph.contours, glyph.advance + accents.caron_room_for("t", glyph, m))

    def place(m, plain):
        x, y = accents.caron_anchor("t", plain, m)
        return x, y - ASC

    return accents.placed(widened, accents.short_tick, place)


def spurless_t_bar(m):
    glyph = spurless_t(m)
    left = accents.bounds(glyph.contours)[0]
    overhang = m.v(68, 62, light=60)
    centre = m.v(300, 292, light=304, black=290)
    half = m.bar * m.v(0.92, 0.84, light=0.96, black=0.66) / 2
    return Glyph(glyph.contours + [rect(left - overhang, centre - half, left + m.stem + overhang, centre + half)], glyph.advance)


def serif_i(m):
    stem = m.cap_stem
    half = m.v(*SERIF_HALF)
    bar = m.cap_bar * m.v(*SERIF_BAR)
    shapes = [rect(half - stem / 2, 0, half + stem / 2, CAP), rect(0, 0, 2 * half, bar), rect(0, CAP - bar, 2 * half, CAP)]
    return spaced(m, shapes, 2 * half, m.v(*SERIF_SIDE), m.v(*SERIF_SIDE))


def serif_i_marks():
    return twin_marks("I")


def twin_marks(base, kept=()):
    case = accents.CASE if base.isupper() else ""
    found = {}
    for name, (letter, mark) in accents.COMPOSED.items():
        if letter != base or name in kept:
            continue
        if mark in accents.BELOW_HOOKS:
            found[name] = f"{mark}comb{case}"
        else:
            comb = next(comb for comb, (_, accent) in accents.TOP_MARKS.items() if accent == mark)
            found[name] = accents.top_mark_on(base, comb)
    return found


def l_without_tail(m):
    return spaced(m, [rect(0, 0, m.stem, ASC)], m.stem, "straight", "straight")


@dataclass(frozen=True)
class HeavierMaster(Master):
    shift: float = 0.0

    def v(self, regular, bold, light=None, black=None):
        return interpolate(self.mix, regular, bold, light, black) + (bold - regular) * self.shift


def heavier(m):
    return HeavierMaster(m.name, m.weight, m.mix, m.italic, m.slant, m.v(0.5, 0.1, light=0.36, black=-0.4))


def small_width(m):
    return m.v(0.55, 0.58, light=0.54, black=0.6)


def small_padding(m):
    return m.v(22, 30, light=20, black=27)


def scaled(contours, lift, wide=SMALL_SCALE):
    return [contour.map(lambda point: (point[0] * wide, point[1] * SMALL_SCALE + lift)) for contour in contours]


def small_figure(draw, lift):
    def build(m):
        drawn = draw(heavier(m))
        wide = small_width(m)
        padding = small_padding(m)
        left = drawn.left * wide + padding
        right = drawn.right * wide + padding
        return spaced(m, scaled(drawn.contours, lift, wide), drawn.width * wide, left, right)

    return build


def small_mark(draw, lift):
    def build(m):
        drawn = draw(heavier(m))
        corners = [point[0] for contour in drawn.contours for point in contour.corners()]
        low, high = min(corners), max(corners)
        wide = small_width(m)
        padding = small_padding(m)
        left = low * wide + padding
        right = (drawn.advance - high) * wide + padding
        contours = scaled(shift(drawn.contours, -low), lift, wide)
        return spaced(m, contours, (high - low) * wide, left, right)

    return build


def superior_letter(name):
    def build(m):
        from .glyphs import GLYPHS as everything

        return small_mark(everything[name][1], NUMERATOR_BASE)(m)

    return build


def superior_letters():
    return [f"{letter}.sups" for letter in LETTERS]


def small_slashed_zero(lift):
    return Overlaid(small_figure(figures.slashed_zero_ring, lift), small_zero_slash)


def fraction_slant(m):
    width = m.v(470, 500)
    return width, band_width(width, CAP, m.v(64, 100, light=44, black=120))


def fraction_bearing(m):
    return m.v(-30, -14)


def fraction_kern(m):
    width, stroke = fraction_slant(m)
    overhang = (width - stroke) * (1 - SMALL_SCALE)
    return round(FRACTION_GAP - overhang - fraction_bearing(m))


def fraction(m):
    width, stroke = fraction_slant(m)
    shape = band((width - stroke, CAP), (0, 0), stroke)
    return spaced(m, [shape], width, fraction_bearing(m), fraction_bearing(m))


def crossings(a, b, heights):
    for height in heights:
        if (a[1] - height) * (b[1] - height) < 0:
            t = (height - a[1]) / (b[1] - a[1])
            yield (a[0] + (b[0] - a[0]) * t, height)


def ink_beside_fraction(glyph):
    ink = []
    for contour in glyph.contours:
        points = list(outline_points(contour))
        for here, after in zip(points, points[1:] + points[:1]):
            if 0 <= here[1] <= CAP:
                ink.append(here)
            ink.extend(crossings(here, after, (0, CAP)))
    return ink


def edge_through(bottom, top):
    lean = (top[0] - bottom[0]) / (top[1] - bottom[1])
    return lambda y: bottom[0] + lean * (y - bottom[1])


@lru_cache(maxsize=None)
def fraction_corners(m):
    corners = set(slanted(fraction, m).contours[0].corners())
    low = sorted(point for point in corners if point[1] < CAP / 2)
    high = sorted(point for point in corners if point[1] >= CAP / 2)
    return low, high


def fraction_lean(m):
    low, high = fraction_corners(m)
    return (high[0][0] - low[0][0]) / (high[0][1] - low[0][1])


def fraction_edges(m):
    low, high = fraction_corners(m)
    return edge_through(low[0], high[0]), edge_through(low[-1], high[-1])


def level_clearance(m, clearance):
    return clearance / math.cos(math.atan(fraction_lean(m)))


@lru_cache(maxsize=None)
def fraction_neighbours():
    drawings = {letter: getattr(lowercase, f"letter_{letter}") for letter in LETTERS}
    drawings.update({letter.upper(): getattr(capitals, f"capital_{letter}") for letter in LETTERS})
    drawings.update({name: figures.proportional(getattr(figures, name)) for name in DIGITS})
    drawings.update({name: draw for name, (code, draw) in accents.GLYPHS.items() if code and chr(code).isalpha()})
    drawings["a.ss01"] = single_storey_a
    drawings["ae.ss01"] = single_storey_ae
    drawings.update({f"{name}.ss01": single_storey_accented(name) for name in SINGLE_STOREY_BASED})
    drawings["l.ss02"] = l_without_tail
    drawings.update({name: vulgar_fraction(numerator, denominator) for name, (_, numerator, denominator) in VULGAR_FRACTIONS.items()})
    return drawings


@lru_cache(maxsize=None)
def fraction_shortfalls(m):
    left_edge, right_edge = fraction_edges(m)
    advance = fraction(m).advance
    clearance = level_clearance(m, FRACTION_CLEARANCE)
    before, after = {}, {}
    for name, draw in fraction_neighbours().items():
        glyph = slanted(draw, m)
        ink = ink_beside_fraction(glyph)
        if not ink:
            continue
        before[name] = clearance - min(glyph.advance - x + left_edge(y) for x, y in ink)
        after[name] = clearance - min(advance - right_edge(y) + x for x, y in ink)
    return before, after


def gap_average(gaps):
    return sum(min(gap, FIGURE_DEPTH) for gap in gaps) / len(gaps)


def deep_pull_limits(m, before):
    glyph = slanted(fraction_neighbours()[FRACTION_REFERENCE], m)
    shortfall = fraction_shortfalls(m)[0 if before else 1][FRACTION_REFERENCE]
    kern = clearance_kern(shortfall)
    gaps = [gap + kern for gap in fraction_gap_profile(m, glyph, before)]
    return looseness(gaps), min(gaps) * DEEP_NEAREST, gap_average(gaps) * DEEP_AVERAGE


def too_close(gaps, limits):
    loose, nearest, average = limits
    return looseness(gaps) < loose or min(gaps) < nearest or gap_average(gaps) < average


@lru_cache(maxsize=None)
def fraction_floors(m):
    drawings = fraction_neighbours()
    floors = []
    for side, shortfalls in enumerate(fraction_shortfalls(m)):
        before = side == 0
        limits = deep_pull_limits(m, before)
        floor = {}
        for name, shortfall in shortfalls.items():
            deepest = max(round(shortfall + FRACTION_TOLERANCE), -FRACTION_DEEPEST)
            if deepest < -FRACTION_PULL:
                glyph = slanted(drawings[name], m)
                if min(box(contour)[1] for contour in glyph.contours) < CAP / 2:
                    floor[name] = deep_pull(fraction_gap_profile(m, glyph, before), limits, deepest)
        floors.append(floor)
    return floors


def deep_pull(gaps, limits, deepest):
    near, far = deepest, -FRACTION_PULL
    while far - near > 1:
        middle = (near + far) // 2
        if too_close([gap + middle for gap in gaps], limits):
            near = middle
        else:
            far = middle
    return far


def clearance_kern(shortfall, floor=-FRACTION_PULL):
    if shortfall > 0:
        return math.ceil(shortfall)
    return max(floor, min(0, round(shortfall + FRACTION_TOLERANCE)))


def fraction_model(name, after):
    if name in SINGLE_STOREY_FAMILY:
        return SINGLE_STOREY_FAMILY[0]
    model = {**accents.KERN_LIKE, **KERN_LIKE}.get(name, name)
    if after and model in accents.LIGATURE_LEFT:
        return accents.LIGATURE_LEFT[model]
    return model


def fraction_kerning(shortfalls, floors=None, after=False):
    floors = floors or {}
    family = {}
    for name in shortfalls:
        model = fraction_model(name, after)
        family[name] = model if model in shortfalls else name
    wanted = {name: clearance_kern(shortfalls[name], floors.get(name, -FRACTION_PULL)) for name in shortfalls}
    loosest = {}
    for name, model in family.items():
        loosest[model] = max(loosest.get(model, wanted[name]), wanted[name])
    return {name: loosest[model] for name, model in family.items()}


def fraction_clearance_pairs(master):
    every = [(fraction_shortfalls(each), fraction_floors(each)) for each in family(master)]
    here, floors = fraction_shortfalls(master), fraction_floors(master)
    lines = []
    for side, pattern in enumerate(["pos {} fraction {};", "pos fraction {} {};"]):
        kerned = sorted(
            {
                name
                for shortfalls, limits in every
                for name, value in fraction_kerning(shortfalls[side], limits[side], side == 1).items()
                if value
            }
        )
        values = fraction_kerning(here[side], floors[side], side == 1)
        lines.extend(f"    {pattern.format(name, values[name])}" for name in kerned)
        lines.extend(f"    {pattern.format(kin, values[name])}" for name in kerned for kin in kin_of(name, fraction_neighbours()))
    return lines


def kin_of(name, skip):
    from .glyphs import EXTENSIONS

    like = {}
    for extension in EXTENSIONS:
        like.update(extension.KERN_LIKE)
    return sorted(glyph for glyph, model in like.items() if model == name and glyph not in skip)


def outline_edges(glyph):
    edges = []
    for contour in glyph.contours:
        points = list(outline_points(contour))
        edges.extend(zip(points, points[1:] + points[:1]))
    return edges


def ink_span(glyph, height):
    return ink_spans(glyph, (height,)).get(height)


PROFILE_HEIGHTS = tuple(range(0, CAP + 1, 4))


def ink_spans(glyph, heights=PROFILE_HEIGHTS):
    ordered = sorted(set(heights))
    wanted = set(ordered)
    found = {}

    def mark(height, x):
        low, high = found.get(height, (x, x))
        found[height] = (min(low, x), max(high, x))

    for here, after in outline_edges(glyph):
        if here[1] in wanted:
            mark(here[1], here[0])
        low, high = sorted((here[1], after[1]))
        for height in ordered[bisect_right(ordered, low) : bisect_left(ordered, high)]:
            t = (height - here[1]) / (after[1] - here[1])
            mark(height, here[0] + (after[0] - here[0]) * t)
    return found


def fraction_gap_profile(m, glyph, before):
    left_edge, right_edge = fraction_edges(m)
    advance = fraction(m).advance
    spans = ink_spans(glyph)
    gaps = []
    for height in PROFILE_HEIGHTS:
        span = spans.get(height)
        if span is None:
            continue
        if before:
            gaps.append(glyph.advance - span[1] + left_edge(height))
        else:
            gaps.append(advance - right_edge(height) + span[0])
    return gaps


def looseness(gaps):
    nearest = min(gaps)
    average = sum(min(gap, FIGURE_DEPTH) for gap in gaps) / len(gaps)
    return FIGURE_BLEND * nearest + (1 - FIGURE_BLEND) * average


@lru_cache(maxsize=None)
def figure_fraction_kerning(m, before):
    lift = NUMERATOR_BASE if before else 0
    tuck = fraction_kern(m)
    spread = {}
    for name in DIGITS:
        glyph = slanted(small_figure(getattr(figures, name), lift), m)
        spread[name] = looseness([gap + tuck for gap in fraction_gap_profile(m, glyph, before)])
    even = sum(spread.values()) / len(spread)
    return {name: round(tuck + even - value) for name, value in spread.items()}


def figure_fraction_pairs(master):
    numerators = {f"{name}.numr": value for name, value in figure_fraction_kerning(master, True).items()}
    denominators = {f"{name}.dnom": value for name, value in figure_fraction_kerning(master, False).items()}
    numerators["zero.numr.slash"] = numerators["zero.numr"]
    denominators["zero.dnom.slash"] = denominators["zero.dnom"]
    lines = [f"    pos {name} fraction {value};" for name, value in numerators.items()]
    lines += [f"    pos fraction {name} {value};" for name, value in denominators.items()]
    return lines


def vulgar_fraction(numerator, denominator):
    def build(m):
        top = small_figure(getattr(figures, numerator), NUMERATOR_BASE)(m)
        slant = fraction(m)
        names = denominator.split()
        upright = roman_of(m)
        slant_x = top.advance + figure_fraction_kerning(upright, True)[numerator]
        bottom_x = slant_x + slant.advance + figure_fraction_kerning(upright, False)[names[0]]
        contours = top.contours + shift(slant.contours, slant_x)
        for name in names:
            bottom = small_figure(getattr(figures, name), 0)(m)
            contours += shift(bottom.contours, bottom_x)
            bottom_x += bottom.advance
        return Glyph(contours, bottom_x)

    return build


def figure_names(suffix):
    return [f"{name}.{suffix}" for name in DIGITS]


def superior_names():
    return [SUPERIORS[name][0] if name in SUPERIORS else f"{name}.numr" for name in DIGITS]


def small_cap(name):
    def build(m):
        from .glyphs import GLYPHS as everything

        return small_cap_drawing(everything[name][1], SMALL_CAP_EASE.get(name, (NO_EASE, NO_EASE)))(m)

    return build


def small_cap_drawing(draw, ease=(NO_EASE, NO_EASE)):
    def build(m):
        sx, sy = SMALL_CAP_WIDTH, SMALL_CAP_HEIGHT / CAP
        weight = SMALL_CAP_WEIGHT
        flat, slant = (m.v(*values) for values in ease)
        master = figures.scaled_master(m, sx, sy, m.stem * weight, m.round * weight, m.thin * flat, m.bar, m.diag * weight * slant)
        glyph = draw(master)
        return Glyph(figures.scaled(glyph.contours, sx, sy), glyph.advance * sx)

    return build


GLYPHS = {
    "zero.slash": (None, Overlaid(figures.proportional(figures.slashed_zero_ring), zero_slash)),
    "zero.tnum.slash": (None, Overlaid(figures.tabular(figures.slashed_zero_ring), zero_slash)),
    "a.ss01": (None, single_storey_a),
    "ae.ss01": (None, single_storey_ae),
    "ordfeminine.ss01": (None, single_storey_ordinal),
    "l.ss02": (None, l_without_tail),
    PUNT_VOLAT: (None, punt_volat),
    PUNT_VOLAT + ".case": (None, punt_volat_case),
    "one.cv01": (None, figures.proportional(one_with_base)),
    "one.tnum.cv01": (None, figures.tabular(one_with_base)),
    SERIF_I: (None, serif_i),
    "four.cv03": (None, figures.proportional(open_four)),
    "four.tnum.cv03": (None, figures.tabular(open_four)),
    "six.cv04": (None, figures.proportional(straight_six)),
    "six.tnum.cv04": (None, figures.tabular(straight_six)),
    "nine.cv05": (None, figures.proportional(straight_nine)),
    "nine.tnum.cv05": (None, figures.tabular(straight_nine)),
    "three.cv07": (None, figures.proportional(flat_three)),
    "three.tnum.cv07": (None, figures.tabular(flat_three)),
    DOUBLE_STOREY_G: (None, double_storey_g),
    SPURLESS_T: (None, spurless_t),
    "tcaron.cv08": (None, spurless_t_caron()),
    "tbar.cv08": (None, spurless_t_bar),
    "fraction": (0x2044, fraction),
}
for name in SINGLE_STOREY_BASED:
    GLYPHS[f"{name}.ss01"] = (None, single_storey_accented(name))
for name in TAILLESS_BASED:
    GLYPHS[f"{name}.ss02"] = (None, tailless(name))
for name, lift in CASE_LIFTS.items():
    GLYPHS[f"{name}.case"] = (None, raised_for_capitals(case_source(name), lift))
for name, code in SUPERIOR_MARKS.items():
    GLYPHS[f"{name}.sups"] = (code, small_mark(raised_for_capitals(case_source(name), CASE_LIFTS[name]), NUMERATOR_BASE))
for name in DIGITS:
    GLYPHS[f"{name}{OLDSTYLE}"] = (None, figures.proportional(figures.oldstyle(name)))
    GLYPHS[f"{name}{TABULAR_OLDSTYLE}"] = (None, figures.tabular(figures.oldstyle(name)))
for capital in SMALL_CAP_LETTERS:
    GLYPHS[f"{capital}{SMALL_CAP}"] = (None, small_cap(capital))
GLYPHS[TURKIC_I] = (None, turkic_i)
GLYPHS[SERIF_SMALL_CAP] = (None, small_cap(SERIF_I))
for name in DIGITS:
    GLYPHS[f"{name}{SMALL_CAP}"] = (None, figures.proportional(figures.small_cap_figure(name)))
GLYPHS[TABULAR_COLON_CASE] = (None, raised_for_capitals(symbols.tabular_punctuation(marks.colon), LOWERCASE_TO_CAPITAL))
GLYPHS["hyphen.tab.case"] = (None, raised_for_capitals(symbols.tabular_sign("hyphen", 1), CASE_LIFTS["hyphen"]))
GLYPHS["zero.numr.slash"] = (None, small_slashed_zero(NUMERATOR_BASE))
GLYPHS["zero.dnom.slash"] = (None, small_slashed_zero(0))
for name, code in SUBSCRIPT_MARKS.items():
    GLYPHS[f"{name}.subs"] = (code, small_mark(raised_for_capitals(case_source(name), CASE_LIFTS[name]), SUBSCRIPT_BASE))
for index, name in enumerate(DIGITS):
    GLYPHS[f"{name}.numr"] = (SUPERIOR_CODES.get(name), small_figure(getattr(figures, name), NUMERATOR_BASE))
    GLYPHS[f"{name}.dnom"] = (None, small_figure(getattr(figures, name), 0))
    GLYPHS[f"{name}.subs"] = (SUBSCRIPT_CODE + index, small_figure(getattr(figures, name), SUBSCRIPT_BASE))
for name, (superior, code) in SUPERIORS.items():
    GLYPHS[superior] = (code, small_figure(getattr(figures, name), NUMERATOR_BASE))
for letter in LETTERS:
    GLYPHS[f"{letter}.sups"] = (None, superior_letter(letter))
for name, (code, numerator, denominator) in VULGAR_FRACTIONS.items():
    GLYPHS[name] = (code, vulgar_fraction(numerator, denominator))

KERN_LIKE = {f"{name}.case": model for name, model in CASE_KERN_LIKE.items()}
KERN_LIKE["a.ss01"] = "a"
KERN_LIKE["ae.ss01"] = accents.KERN_LIKE["ae"]
KERN_LIKE["ordfeminine.ss01"] = "ordfeminine"
KERN_LIKE["l.ss02"] = "l"
KERN_LIKE["i.loclTRK"] = "i"
KERN_LIKE.update({f"{name}.ss02": "l" for name in TAILLESS_BASED})
for _, _, forms in VARIANTS.values():
    KERN_LIKE.update({variant: accents.KERN_LIKE.get(plain, plain) for plain, variant in forms.items()})
KERN_LIKE["tbar.cv08"] = "t"


@lru_cache(maxsize=None)
def single_storey_clearance(master):
    from . import features as kerning

    gap = master.v(*accents.ACCENT_CLEARANCE)
    floor = accents.mark_floor(False)
    found = {}
    measure = accents.cached_profile()

    def settle(first, second, left, right, left_floor, right_floor, model):
        needed = accents.closest_kern(left, right, gap, left_floor, right_floor, measure)
        if needed is not None:
            value = accents.pair_kern(kerning, *model, master)
            found[(first, second)] = max(value, needed) - value

    like = kerning.all_like()
    for name in accents.neighbours(kerning, accents.raised(master)):
        if like.get(name, name) != name:
            continue
        neighbour = accents.drawn(name, master)
        both_ways = name in accents.RISERS or accents.KERN_LIKE.get(name) in accents.RISERS
        for plain in SINGLE_STOREY_BASED:
            target = f"{plain}.ss01"
            glyph = accents.drawn(target, master)
            settle(name, target, neighbour, glyph, floor - gap, floor, (name, "a"))
            if both_ways:
                settle(target, name, glyph, neighbour, floor, floor - gap, ("a", name))
    return found


def single_storey_class_pairs(master):
    from . import features as kerning

    family = glyph_class(SINGLE_STOREY_FAMILY)
    lines = []
    for first, second, regular, bold in kerning.PAIRS:
        value = kerning.class_kern(first, second, regular, bold, master)
        if "a" in kerning.SECOND[second]:
            lines.append(f"        pos @first_{first} {family} {value};")
        if "a" in kerning.FIRST[first]:
            lines.append(f"        pos {family} @second_{second} {value};")
    return lines


def single_storey_clearance_pairs(master):
    needed = {pair for each in family(master) for pair, delta in single_storey_clearance(each).items() if round(delta) >= accents.SMALLEST_KERN}
    found = single_storey_clearance(master)
    present = {name for pair in needed for name in pair}
    lines = []
    for first, second in sorted(needed):
        value = round(found.get((first, second), 0))
        lines.append(f"    pos {first} {second} {value};")
        lines.extend(f"    pos {kin} {second} {value};" for kin in kin_of(first, present))
        lines.extend(f"    pos {first} {kin} {value};" for kin in kin_of(second, present))
    return lines


def cased(names):
    return [glyph_class([name, f"{name}.case"]) for name in names]


def contextual_features():
    figures_all = glyph_class(DIGITS + figure_names("tnum") + ["zero.slash", "zero.tnum.slash"] + variant_figures())
    zeros = glyph_class(["zero", "zero.tnum", "zero.slash", "zero.tnum.slash"])
    hyphen, less, greater, equal = cased(["hyphen", "less", "greater", "equal"])
    lines = ["lookup ss03_arrow_forms {"]
    for parts, arrow in ARROWS.items():
        lines.append(f"    sub {' '.join(parts)} by {arrow};")
        lines.append(f"    sub {' '.join(part + '.case' for part in parts)} by {arrow}.case;")
    lines += [
        "} ss03_arrow_forms;",
        "lookup ss03_times_form {",
        "    sub x by multiply;",
        "} ss03_times_form;",
        f"feature {ARROWS_SET} {{",
        "    featureNames {",
        f'        name "{ARROWS_LABEL}";',
        "    };",
        "    lookup ss03_arrows {",
        f"        ignore sub {hyphen} {hyphen}' {greater}';",
        f"        ignore sub {less}' {hyphen}' {hyphen};",
        f"        ignore sub {less} {less}' {hyphen}';",
        f"        ignore sub {hyphen}' {greater}' {greater};",
        f"        ignore sub {equal} {equal}' {greater}';",
        f"        ignore sub {equal}' {greater}' {greater};",
        f"        ignore sub {equal}' {greater}' {equal};",
        f"        ignore sub {less} {equal}' {greater}';",
        f"        sub {less}' lookup ss03_arrow_forms {hyphen}' {greater}';",
        f"        ignore sub {less}' {hyphen}' {figures_all};",
        f"        sub {less}' lookup ss03_arrow_forms {hyphen}';",
        f"        sub {hyphen}' lookup ss03_arrow_forms {greater}';",
        f"        sub {equal}' lookup ss03_arrow_forms {greater}';",
        "    } ss03_arrows;",
        "    lookup ss03_times {",
        f"        sub {figures_all} {zeros} x' lookup ss03_times_form {figures_all};",
        f"        ignore sub {zeros} x';",
        f"        sub {figures_all} x' lookup ss03_times_form {figures_all};",
        "    } ss03_times;",
        f"}} {ARROWS_SET};",
    ]
    return lines


def variant_figures():
    return [variant for _, _, forms in VARIANTS.values() for plain, variant in forms.items() if plain.split(".")[0] in DIGITS]


def proportional_features():
    tabular = {f"{name}.tnum": name for name in DIGITS}
    tabular["zero.tnum.slash"] = "zero.slash"
    tabular.update({f"{name}.tab": name for name in TABULAR_PUNCTUATION + [PUNCTUATION_SPACE]})
    tabular[TABULAR_COLON_CASE] = "colon.case"
    tabular.update({f"{name}.tab": name for name in symbols.TABULAR_SIGNS})
    tabular["hyphen.tab.case"] = "hyphen.case"
    for _, _, forms in VARIANTS.values():
        for plain, variant in forms.items():
            if plain in tabular:
                tabular[variant] = forms[tabular[plain]]
    return ["feature pnum {", *[f"    sub {source} by {target};" for source, target in tabular.items()], "} pnum;"]


def tabular_punctuation_feature():
    return ["feature tnum {", *[f"    sub {name} by {name}.tab;" for name in TABULAR_PUNCTUATION + [PUNCTUATION_SPACE] + list(symbols.TABULAR_SIGNS)], "} tnum;"]


def case_context():
    from .glyphs import GLYPHS as everything

    def capital(name):
        code = everything.get(name.split(".")[0], (None,))[0]
        return code is not None and unicodedata.category(chr(code)) == "Lu"

    letters = [name for name in everything if capital(name) and not name.endswith(".case")]
    return letters + DIGITS + figure_names("tnum") + ["zero.slash", "zero.tnum.slash"] + variant_figures()


def contextual_case_feature():
    targets = CASE_BETWEEN + CASE_OPENING + CASE_CLOSING
    opening = glyph_class(CASE_OPENING)
    closing = glyph_class(CASE_CLOSING)
    raised = glyph_class([f"{name}.case" for name in CASE_OPENING])
    between = glyph_class(CASE_BETWEEN)
    spaced_dashes = glyph_class(CASE_SPACED)
    return [
        f"@case_context = {glyph_class(case_context())};",
        "lookup calt_case_forms {",
        *[f"    sub {name} by {name}.case;" for name in targets if name not in TABULAR_CASE],
        *[f"    sub {name} by {raised};" for name, raised in TABULAR_CASE.items()],
        "} calt_case_forms;",
        "feature calt {",
        "    lookup calt_case {",
        "        lookupflag IgnoreMarks;",
        f"        sub @case_context {between}' lookup calt_case_forms @case_context;",
        f"        sub @case_context space {spaced_dashes}' lookup calt_case_forms space @case_context;",
        f"        sub {opening}' lookup calt_case_forms @case_context @case_context;",
        f"        sub {opening}' lookup calt_case_forms @case_context {closing};",
        f"        sub @case_context @case_context {closing}' lookup calt_case_forms;",
        f"        sub {raised} @case_context {closing}' lookup calt_case_forms;",
        "    } calt_case;",
        "} calt;",
    ]


def all_alternates_feature():
    tags = [tag for tag in ALTERNATE_SOURCES if tag != "sups"] + list(VARIANTS) + SMALL_CAP_SOURCES + ["sups"]
    return ["feature aalt {", *[f"    feature {tag};" for tag in tags], "} aalt;"]


def variant_features():
    lines = []
    for tag, (label, code, forms) in VARIANTS.items():
        lines += [
            f"feature {tag} {{",
            "    cvParameters {",
            "        FeatUILabelNameID {",
            f'            name "{label}";',
            "        };",
            f"        Character 0x{code:X};",
            "    };",
            *[f"    sub {' '.join(parts)} by {variant};" for parts, variant in VARIANT_LIGATURES.get(tag, {}).items()],
            *[f"    sub {plain} by {variant};" for plain, variant in forms.items()],
        ]
        if tag in DECOMPOSED_VARIANTS:
            twin = DECOMPOSED_VARIANTS[tag]
            lines += [f"    sub {name} by {twin} {mark};" for name, mark in sorted(twin_marks(MARK_TWINS[twin], forms).items())]
        lines.append(f"}} {tag};")
    return lines


def turkic_feature():
    lines = ["lookup turkic_dotted_i {", f"    sub i by {TURKIC_I};", "} turkic_dotted_i;", "feature locl {", "    script latn;"]
    for language in TURKIC_LANGUAGES:
        lines += [f"    language {language};", "    lookup turkic_dotted_i;"]
    return lines + ["} locl;"]


def small_cap_serif_features():
    lines = ["lookup small_cap_serif {", f"    sub I{SMALL_CAP} by {SERIF_SMALL_CAP};", "} small_cap_serif;"]
    for tag in ("cv02", DISAMBIGUATION_SET):
        lines += [f"feature {tag} {{", "    lookup small_cap_serif;", f"}} {tag};"]
    return lines


def comb_for(letter, mark):
    if mark in accents.BELOW_HOOKS:
        return f"{mark}comb"
    if mark == "horn":
        return next(iter(accents.HORN_MARKS))
    ligated = [name for name, (_, _, accent) in accents.LIGATED_MARKS.items() if accent == mark]
    return next(iter(ligated), None) or next((comb for comb, (_, accent) in accents.TOP_MARKS.items() if accent == mark), None)


def small_cap_marks():
    capital_of = {lower: capital for capital, lower in SMALL_CAP_LETTERS.items()}
    capital_of.update({capital: capital for capital in SMALL_CAP_LETTERS})

    def spelled(name):
        if name in capital_of:
            return (f"{capital_of[name]}{SMALL_CAP}",)
        if name not in accents.COMPOSED:
            return None
        letter, mark = accents.COMPOSED[name]
        base, comb = spelled(letter), comb_for(letter, mark)
        return base + (comb,) if base and comb else None

    found = dict(SMALL_CAP_MARKED)
    for name in accents.COMPOSED:
        sequence = spelled(name)
        if sequence and len(sequence) > 1:
            found[name] = sequence
    from .glyphs import EXTENSIONS

    for extension in EXTENSIONS:
        found.update(getattr(extension, "SMALL_CAP_MARKED", {}))
    return found


def small_cap_pairs():
    from .glyphs import EXTENSIONS, GLYPHS as everything

    by_code = {code: name for name, (code, _) in everything.items() if code is not None}
    lower, upper = {}, {}
    for name in everything:
        base = name[: -len(SMALL_CAP)]
        if not name.endswith(SMALL_CAP) or base not in everything:
            continue
        code = everything[base][0]
        if code is None or unicodedata.category(chr(code)) != "Lu":
            continue
        upper[base] = name
        small = by_code.get(ord(chr(code).lower()))
        if small and small != base:
            lower[small] = name
    lower.update({small: f"{capital}{SMALL_CAP}" for capital, small in SMALL_CAP_LETTERS.items()})
    lower.update({alias: f"{capital}{SMALL_CAP}" for alias, capital in SMALL_CAP_ALIASES.items()})
    for extension in EXTENSIONS:
        lower.update(getattr(extension, "SMALL_CAP_LOWER", {}))
        upper.update(getattr(extension, "SMALL_CAP_UPPER", {}))
    return lower, upper


def small_cap_features():
    lower, upper = small_cap_pairs()
    marked = small_cap_marks()
    lines = []
    from .glyphs import EXTENSIONS, GLYPHS as everything

    def cased(*categories):
        return lambda name: name in everything and everything[name][0] is not None and unicodedata.category(chr(everything[name][0])) in categories

    contexts = {}
    for extension in EXTENSIONS:
        if hasattr(extension, "small_cap_context"):
            definitions, references = extension.small_cap_context()
            lines += definitions
            for tag, names in references.items():
                contexts.setdefault(tag, []).extend(names)
    for tag, singles, case in (("smcp", lower, cased("Ll")), ("c2sc", upper, cased("Lu", "Lt"))):
        lines.append(f"feature {tag} {{")
        lines += [f"    lookup {name};" for name in contexts.get(tag, [])]
        lines += [f"    sub {plain} by {target};" for plain, target in singles.items()]
        lines += [f"    sub {name} by {' '.join(sequence)};" for name, sequence in sorted(marked.items()) if case(name)]
        lines.append(f"    sub {DOUBLE_S[0] if tag == 'smcp' else DOUBLE_S[1]} by S{SMALL_CAP} S{SMALL_CAP};")
        lines += [f"    sub {name} by {name}{SMALL_CAP};" for name in DIGITS]
        lines.append(f"    sub {TURKIC_I} by I{SMALL_CAP} dotaccentcomb;" if tag == "smcp" else f"    sub {SERIF_I} by {SERIF_SMALL_CAP};")
        lines.append(f"}} {tag};")
    return lines


def small_cap_kern_lines(master):
    from . import features as kerning

    from .glyphs import GLYPHS as everything

    names = {name for name in everything if name.endswith(SMALL_CAP)}

    def small(members):
        return [f"{name}{SMALL_CAP}" for name in members if f"{name}{SMALL_CAP}" in names]

    like = kerning.all_like()

    def capitals_in(members):
        return [name for name in members if f"{like.get(name, name)}{SMALL_CAP}" in names and not name.endswith(SMALL_CAP)]

    widened_first, widened_second = kerning.widened_classes()
    lines = []
    for first, second, regular, bold in kerning.PAIRS:
        value = round(kerning.class_kern(first, second, regular, bold, master) * SMALL_CAP_WIDTH)
        lefts, rights = widened_first[first], widened_second[second]
        left_other = lefts if first in SMALL_CAP_PUNCTUATION else []
        right_other = rights if second in SMALL_CAP_PUNCTUATION else []
        for left, right in ((small(lefts), small(rights)), (small(lefts), right_other), (left_other, small(rights)), (capitals_in(lefts), small(rights))):
            if value and left and right:
                lines.append(f"        pos {glyph_class(left)} {glyph_class(right)} {value};")
    return lines


def capital_spacing_feature(master):
    from .glyphs import GLYPHS as everything

    capitals_only = [name for name in case_context() if name in everything and everything[name][0] and unicodedata.category(chr(everything[name][0])) == "Lu"]
    room = round(master.v(*CAPITAL_SPACING))
    return ["feature cpsp {", f"    pos {glyph_class(capitals_only)} <{room} 0 {2 * room} 0>;", "} cpsp;"]


def disambiguation_feature():
    return [
        f"feature {DISAMBIGUATION_SET} {{",
        "    featureNames {",
        f'        name "{DISAMBIGUATION_LABEL}";',
        "    };",
        *[f"    sub {plain} by {variant};" for plain, variant in DISAMBIGUATION.items()],
        *[f"    sub {name} by {SERIF_I} {mark};" for name, mark in sorted(serif_i_marks().items())],
        f"}} {DISAMBIGUATION_SET};",
    ]


def oldstyle_features():
    lines = ["feature onum {"]
    lines += [f"    sub {name} by {name}{OLDSTYLE};" for name in DIGITS]
    lines += [f"    sub {name}.tnum by {name}{TABULAR_OLDSTYLE};" for name in DIGITS]
    lines += ["} onum;", "feature lnum {"]
    lines += [f"    sub {name}{OLDSTYLE} by {name};" for name in DIGITS]
    lines += [f"    sub {name}{TABULAR_OLDSTYLE} by {name}.tnum;" for name in DIGITS]
    lines += ["} lnum;", "feature tnum {"]
    lines += [f"    sub {name}{OLDSTYLE} by {name}{TABULAR_OLDSTYLE};" for name in DIGITS]
    lines += ["} tnum;", "feature pnum {"]
    lines += [f"    sub {name}{TABULAR_OLDSTYLE} by {name}{OLDSTYLE};" for name in DIGITS]
    lines += ["} pnum;"]
    return lines


def glyph_class(names):
    return f"[{' '.join(names)}]"


def features(master):
    figures_any = DIGITS + figure_names("tnum")
    numerators = figure_names("numr") * 2
    denominators = figure_names("dnom") * 2
    superiors = superior_names() * 2
    small_cap_kern = "\n".join(small_cap_kern_lines(master))
    case_pairs = "\n".join([f"    sub {name} by {name}.case;" for name in CASE_LIFTS] + [f"    sub {name} by {raised};" for name, raised in TABULAR_CASE.items()])
    superior_marks = "\n".join(f"    sub {name} by {target};" for name, target in SUPERIOR_SOURCES.items())
    subscripts = glyph_class(figure_names("subs") * 2)
    subscript_marks = "\n".join(f"    sub {name} by {target};" for name, target in SUBSCRIPT_SOURCES.items())
    single_storey = ["a"] + SINGLE_STOREY_BASED + ["ae", "ordfeminine"]
    single_storey_from = glyph_class(single_storey)
    single_storey_to = glyph_class([f"{name}.ss01" for name in single_storey])
    single_storey_kern = "\n".join(single_storey_class_pairs(master))
    ordinal_from = glyph_class(list(ORDINALS))
    ordinal_to = glyph_class(list(ORDINALS.values()))
    pairs = "\n".join(figure_fraction_pairs(master) + fraction_clearance_pairs(master) + single_storey_clearance_pairs(master))
    return f"""
@figures_any = {glyph_class(figures_any)};
@numerators = {glyph_class(numerators)};
@denominators = {glyph_class(denominators)};
@superiors = {glyph_class(superiors)};

lookup fraction_bar {{
    sub slash by fraction;
}} fraction_bar;

lookup fraction_slash_between_figures {{
    sub @figures_any slash' lookup fraction_bar @figures_any;
}} fraction_slash_between_figures;

lookup fraction_denominators {{
    sub [fraction @denominators] @figures_any' by @denominators;
}} fraction_denominators;

lookup fraction_numerators {{
    rsub @figures_any' [fraction @numerators] by @numerators;
}} fraction_numerators;

feature frac {{
    lookup fraction_slash_between_figures;
    lookup fraction_denominators;
    lookup fraction_numerators;
}} frac;

feature kern {{
    lookup single_storey_kern {{
{single_storey_kern}
    }} single_storey_kern;
    lookup catalan_dot {{
        pos {PUNT_VOLAT} {glyph_class(l_kin())} {round(punt_volat_kern(master))};
    }} catalan_dot;
    lookup small_cap_kern {{
{small_cap_kern}
    }} small_cap_kern;
{pairs}
}} kern;

feature numr {{
    sub @figures_any by @numerators;
}} numr;

feature dnom {{
    sub @figures_any by @denominators;
}} dnom;

feature sups {{
    sub @figures_any by @superiors;
{superior_marks}
    sub {glyph_class(list(LETTERS))} by {glyph_class(superior_letters())};
}} sups;

lookup subscript_forms {{
    sub @figures_any by {subscripts};
{subscript_marks}
}} subscript_forms;

feature subs {{
    lookup subscript_forms;
}} subs;

feature sinf {{
    lookup subscript_forms;
}} sinf;

feature case {{
{case_pairs}
}} case;

feature ss01 {{
    featureNames {{
        name "Single-storey a";
    }};
    sub {single_storey_from} by {single_storey_to};
}} ss01;

feature ss02 {{
    featureNames {{
        name "l without tail";
    }};
    sub l {accents.CARON_ALT} by lcaron.ss02;
    sub {glyph_class(["l"] + TAILLESS_BASED)} by {glyph_class(["l.ss02"] + [f"{name}.ss02" for name in TAILLESS_BASED])};
}} ss02;

feature ordn {{
    sub @figures_any {ordinal_from}' by {ordinal_to};
    sub @figures_any period {ordinal_from}' by {ordinal_to};
    sub N o period by {NUMERO};
}} ordn;

feature locl {{
    script latn;
    language CAT;
    lookup punt_volat {{
        sub l periodcentered' l by {PUNT_VOLAT};
        sub L [periodcentered periodcentered.case]' L by {PUNT_VOLAT}.case;
    }} punt_volat;
}} locl;

feature zero {{
    sub zero by zero.slash;
    sub zero.tnum by zero.tnum.slash;
    sub zero.numr by zero.numr.slash;
    sub zero.dnom by zero.dnom.slash;
}} zero;
""" + "\n".join(turkic_feature() + tabular_punctuation_feature() + contextual_features() + contextual_case_feature() + variant_features() + disambiguation_feature() + proportional_features() + oldstyle_features() + small_cap_features() + small_cap_serif_features() + capital_spacing_feature(master) + all_alternates_feature()) + "\n"
