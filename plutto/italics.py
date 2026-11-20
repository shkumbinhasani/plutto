import math

from . import accents, alternates, greek, latin, lowercase, marks, symbols
from .masters import BOLD_WEIGHT, XH, family
from .oblique import ItalicForm
from .parts import Glyph, spaced
from .shapes import Node, aim, extent, place, rect, ribbon, shift

DOWN = (0, -1)
UP = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)


AT_STEM_DROP = (30, 40, 24, 52)
AT_INSET = (0, 12, 0, 40)
KAPPA_WIDTH = (430, 520, 410, 566)
KAPPA_BRANCH = (214, 196, 220, 184)
def italic_kappa(m):
    return spaced(m, lowercase.curved_kay(m, m.v(*KAPPA_WIDTH), m.v(*KAPPA_BRANCH), XH), m.v(*KAPPA_WIDTH), "straight", "diagonal")


def stem_right(glyph):
    return max(point[0] for point in glyph.contours[0].points() if point[1] > XH)


def italic_dcroat(m):
    glyph = lowercase.italic_d(m)
    left, _ = latin.ink(glyph)
    right = stem_right(glyph)
    bottom, top = latin.ascender_bar(m)
    start = left + (right - left) * m.v(0.44, 0.42, black=0.4)
    over = m.v(44, 48, light=40, black=50)
    return Glyph(glyph.contours + [rect(start, bottom, right + over, top)], glyph.advance)


def italic_dong(m):
    glyph = italic_dcroat(m)
    left = latin.ink(glyph)[0]
    right = stem_right(glyph)
    rule = m.bar * m.v(0.96, 0.9, light=1.0, black=0.84)
    top = -m.v(*symbols.DONG_GAP)
    return Glyph(glyph.contours + [rect(left, top - rule, right, top)], glyph.advance)


def italic_at(m):
    width = m.v(804, 900, black=948)
    bottom, top = -150, 690
    middle = (top + bottom) / 2
    edge = m.v(70, 116, light=46, black=146)
    flat = m.v(56, 86, light=38, black=106)
    scale = m.v(0.78, 0.74, black=0.8)
    right = m.v(572, 640, black=680) - m.v(*AT_INSET)
    base = m.v(68, 80)
    knee = base + m.v(80, 110)
    lighter = next(each for each in family(m) if each.weight == BOLD_WEIGHT)
    share = m.v(0, 0, black=0.6)
    own, other = lowercase.italic_a_plain(m), lowercase.italic_a_plain(lighter)
    stem_drop = m.v(*AT_STEM_DROP)
    post_contour, *belly = shift(marks.blend(own.contours, other.contours, share), -marks.blend_value(m.bearing("round"), lighter.bearing("round"), share))
    letter = [post_contour.map(lambda point: (point[0], point[1] if point[1] > 0 else -stem_drop))] + belly
    left = right - extent(letter) * scale
    inner = [place(contour, left, base, scale, scale) for contour in letter]
    stem = marks.blend_value(m.stem, lighter.stem, share) * scale
    post = right - stem / 2
    sweep = math.radians(m.v(42, 40))
    rx, ry = (width - edge) / 2, (top - bottom - flat) / 2
    tail = (width / 2 + rx * math.sin(sweep), middle - ry * math.cos(sweep))
    foot = m.v(62, 96, light=42, black=124)
    stroke = ribbon(
        [
            Node((post, knee + m.v(40, 50)), DOWN, stem),
            Node((post, knee), DOWN, stem, straight=True),
            Node(((post + width - edge / 2) / 2, base - m.v(20, 24) + foot / 2), RIGHT, foot),
            Node((width - edge / 2, middle + 10), UP, edge),
            Node((width / 2, top - flat / 2), LEFT, flat),
            Node((edge / 2, middle), DOWN, edge),
            Node((width / 2 - 6, bottom + flat / 2), RIGHT, flat),
            Node(tail, aim(m.v(61, 60)), m.v(60, 94, light=40, black=122), cut="h"),
        ],
        0.6,
    )
    return spaced(m, [stroke] + inner, width, m.v(40, 32), m.v(40, 32))


FORMS = {
    "ae": lowercase.italic_ae,
    "ae.ss01": lowercase.italic_ae,
    "at": italic_at,
    "at.case": alternates.raised_for_capitals(italic_at, alternates.CASE_LIFTS["at"]),
    "dcroat": italic_dcroat,
    "dong": italic_dong,
    "kappa": italic_kappa,
    "uni03D7": greek.kai(italic_kappa),
    "kgreenlandic": lowercase.italic_kra,
    "uni043A": lowercase.italic_kra,
    "ordfeminine": alternates.single_storey_ordinal,
}


def italicized(glyphs):
    for name, form in FORMS.items():
        code, draw = glyphs[name]
        glyphs[name] = (code, ItalicForm(draw, form))
    code, _ = glyphs["aeacute"]
    glyphs["aeacute"] = (code, accents.accented_letter("aeacute", glyphs["ae"][1], "acute", False))
    code, _ = glyphs["uni045C"]
    glyphs["uni045C"] = (code, accents.accented_letter("uni045C", glyphs["uni043A"][1], "acute", False))
