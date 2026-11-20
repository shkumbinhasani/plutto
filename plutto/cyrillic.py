from dataclasses import dataclass
from functools import lru_cache
import math
import unicodedata

import numpy

from . import accents, capitals, greek, latin, lowercase, symbols
from .geometry import Path, across, intersect, quarter
from .masters import ASC, CAP, DESC, LIGHT, REGULAR, XH, family
from .oblique import ItalicForm
from .parts import HOOK_SPREAD, Glyph, band, band_width, ess, kay, lobe, reach, shoulder_inner, shoulder_spring, spaced, vee
from .shapes import Node, aim, arch, flop, mirror, oval, polygon, rect, ribbon, ring, shift, turn
from .parts import hook
from .shapes import place

DOWN = (0, -1)
UP = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
HOOK_DEPTH = 1.15
HOOK_BELLY = 1.25


@dataclass(frozen=True)
class Size:
    capital: bool
    height: float
    stem: float
    bar: float
    thin: float
    side: float
    diag: float
    straight: str
    round: str
    diagonal: str


def size(m, capital):
    if capital:
        return Size(True, CAP, m.cap_stem, m.cap_bar, m.cap_thin, m.cap_round, m.cap_diag, "cap", "cap_round", "cap_diagonal")
    return Size(False, XH, m.stem, m.bar, m.thin, m.round, m.diag, "straight", "round", "diagonal")


def pick(m, sz, capital, small):
    return m.v(*(capital if sz.capital else small))


PE_WIDTH = ((560, 626, 540, 672), (446, 514, 428, 562))
EN_WIDTH = (448, 516, 430, 566)
GE_WIDTH = ((446, 500, 430, 540), (352, 404, 338, 446))
GE_RIGHT = ((28, 20, 30, 14), (14, 8, 16, 4))
UPTURN = ((146, 150, 144, 152), (126, 132, 124, 136))
SPUR_DEPTH = ((146, 148, 144, 150), (150, 152, 148, 154))
SPUR_RIGHT = ((34, 26, 36, 20), (28, 22, 30, 16))
DE_SIDES = ((30, 22, 32, 16), (26, 20, 28, 14))
SHA_WIDTH = ((770, 876, 742, 952), (690, 806, 662, 890))
SHA_MIDDLE = (1.0, 0.94, 1.0, 0.9)
II_WIDTH = ((590, 660, 566, 712), (454, 524, 436, 574))
II_DIAG = ((1.0, 0.94, 1.0, 0.92), (0.98, 0.93, 1.0, 0.92))
SOFT_WIDTH = ((516, 584, 496, 634), (414, 480, 398, 528))
SOFT_TOP = ((418, 426, 414, 432), (318, 334, 312, 354))
SOFT_BAR = ((76, 108, 54, 138), (70, 96, 52, 108))
SOFT_SIDE = (0.98, 0.92, 1.0, 0.88)
HARD_SPUR = ((134, 136, 130, 140), (108, 112, 104, 116))
YERU_BOWL = ((470, 532, 452, 584), (380, 440, 364, 496))
YERU_GAP = ((86, 76, 92, 66), (72, 62, 78, 54))
BE_ARM = ((30, 26, 32, 22), (24, 20, 26, 16))
IU_RING = ((540, 600, 520, 690), (424, 486, 408, 546))
IU_GAP = ((98, 86, 104, 76), (82, 72, 88, 64))
EF_WIDTH = ((648, 720, 624, 790), (560, 640, 536, 730))
EF_INSET = (88, 84, 90, 80)
EF_SIDE = (0.96, 0.88, 0.98, 0.82)
TE_WIDTH = (420, 482, 404, 528)
EM_WIDTH = ((716, 812, 690, 876), (580, 672, 556, 740))
REVERSED_BAR = ((0.34, 0.37, 0.34, 0.41), (0.3, 0.34, 0.3, 0.39))
UKRAINIAN_BAR = ((0.6, 0.6, 0.6, 0.6), (0.62, 0.62, 0.62, 0.62))
YAT_OVER = ((60, 64, 58, 68), (60, 62, 58, 64))
YAT_REACH = ((150, 160, 146, 172), (120, 128, 116, 134))
YAT_BAR_TOP = ((606, 624, 600, 650), (540, 540, 540, 540))
YAT_BAR = (1.0, 0.9, 1.0, 0.8)
YUS_WIDTH = ((690, 790, 664, 900), (560, 652, 540, 770))
YUS_APEX = (0.5, 0.48, 0.5, 0.44)
YUS_BAR = (1.0, 0.88, 1.0, 0.74)
YUS_FLAT = 1.2
YUS_FOOT = 1.08
YUS_JOIN = 0.5
YUS_STEM = 0.8


def ge_shape(sz, width, up=0, rise=0):
    h, stem, bar = sz.height, sz.stem, sz.bar
    top = [(width, h)] if not up else [(width - up, h), (width - up, h + rise), (width, h + rise)]
    return polygon([(0, 0), (0, h)] + top + [(width, h - bar), (stem, h - bar), (stem, 0)])


def ge(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *GE_WIDTH)
    return spaced(m, [ge_shape(sz, width)], width, sz.straight, pick(m, sz, *GE_RIGHT))


def gheupturn(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *GE_WIDTH) - m.v(10, 8)
    up = sz.stem * m.v(0.9, 0.86, light=0.92, black=0.82)
    shape = ge_shape(sz, width, up, pick(m, sz, *UPTURN))
    return spaced(m, [shape], width, sz.straight, pick(m, sz, *GE_RIGHT))


def pe(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    width = pick(m, sz, *PE_WIDTH)
    shape = polygon([(0, 0), (0, h), (width, h), (width, 0), (width - stem, 0), (width - stem, h - bar), (stem, h - bar), (stem, 0)])
    return spaced(m, [shape], width, sz.straight, sz.straight)


def en(m):
    sz = size(m, False)
    width = m.v(*EN_WIDTH)
    centre = sz.height * 0.5
    shapes = [
        rect(0, 0, sz.stem, sz.height),
        rect(width - sz.stem, 0, width, sz.height),
        rect(sz.stem * 0.5, centre - sz.bar / 2, width - sz.stem * 0.5, centre + sz.bar / 2),
    ]
    return spaced(m, shapes, width, sz.straight, sz.straight)


def spur(m, sz):
    return sz.stem * m.v(0.94, 0.9, light=0.96, black=0.86), -pick(m, sz, *SPUR_DEPTH)


def tail_points(m, sz, x, start=None):
    foot, depth = spur(m, sz)
    return [(x if start is None else start, sz.bar), (x + foot, sz.bar), (x + foot, depth), (x, depth), (x, 0)]


def tailed(m, sz, contour):
    points = list(contour.corners())
    index = max(range(len(points)), key=lambda i: (points[i][1] <= 0, points[i][0]))
    points = points[index + 1 :] + points[: index + 1]
    corner, above = points[-1], points[-2]
    edge = intersect(above, corner, (0, sz.bar), (1, sz.bar))
    return polygon(points[:-1] + tail_points(m, sz, corner[0], edge[0]))


def tail_spaced(m, sz, shapes, width, left):
    foot, _ = spur(m, sz)
    return spaced(m, shapes, width + foot, left, pick(m, sz, *SPUR_RIGHT), capital=sz.capital)


def combs(m, sz, width, stems, tail):
    h, stem, bar = sz.height, sz.stem, sz.bar
    points = [(0, 0), (0, h), (stem, h), (stem, bar)]
    for left, thickness in stems:
        points += [(left, bar), (left, h), (left + thickness, h), (left + thickness, bar)]
    points += [(width - stem, bar), (width - stem, h), (width, h)]
    points += tail_points(m, sz, width) if tail else [(width, 0)]
    return polygon(points)


def tse(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *PE_WIDTH)
    foot, _ = spur(m, sz)
    return spaced(m, [combs(m, sz, width, [], True)], width + foot, sz.straight, pick(m, sz, *SPUR_RIGHT))


def sha_stems(m, sz, width):
    middle = sz.stem * m.v(*SHA_MIDDLE)
    return [((width - middle) / 2, middle)]


def sha(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *SHA_WIDTH)
    return spaced(m, [combs(m, sz, width, sha_stems(m, sz, width), False)], width, sz.straight, sz.straight)


def shcha(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *SHA_WIDTH)
    foot, _ = spur(m, sz)
    shape = combs(m, sz, width, sha_stems(m, sz, width), True)
    return spaced(m, [shape], width + foot, sz.straight, pick(m, sz, *SPUR_RIGHT))


def dzhe(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    width = pick(m, sz, *PE_WIDTH)
    foot, depth = spur(m, sz)
    centre = width / 2
    shape = polygon(
        [
            (0, 0), (0, h), (stem, h), (stem, bar), (width - stem, bar), (width - stem, h), (width, h), (width, 0),
            (centre + foot / 2, 0), (centre + foot / 2, depth), (centre - foot / 2, depth), (centre - foot / 2, 0),
        ]
    )
    return spaced(m, [shape], width, sz.straight, sz.straight)


def ii(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *II_WIDTH)
    stroke = band_width(width, sz.height, sz.diag * pick(m, sz, *II_DIAG))
    shapes = [
        rect(0, 0, sz.stem, sz.height),
        rect(width - sz.stem, 0, width, sz.height),
        band((width - stroke, sz.height), (0, 0), stroke),
    ]
    return spaced(m, shapes, width, sz.straight, sz.straight)


def soft_bowl(m, sz, left, width):
    top = pick(m, sz, *SOFT_TOP)
    bar = pick(m, sz, *SOFT_BAR)
    return lobe(m, left + sz.stem * 0.5, left + sz.stem * 0.8, width, top, 0, bar, sz.side * m.v(*SOFT_SIDE))


def soft(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *SOFT_WIDTH)
    shapes = [rect(0, 0, sz.stem, sz.height)] + soft_bowl(m, sz, 0, width)
    return spaced(m, shapes, width, sz.straight, sz.round)


def yat(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *SOFT_WIDTH)
    over = pick(m, sz, *YAT_OVER)
    top = pick(m, sz, *YAT_BAR_TOP)
    bar = sz.bar * m.v(*YAT_BAR)
    shapes = [rect(0, 0, sz.stem, sz.height if capital else ASC)] + soft_bowl(m, sz, 0, width)
    shapes.append(rect(-over, top - bar, sz.stem + pick(m, sz, *YAT_REACH), top))
    return spaced(m, shift(shapes, over), width + over, m.v(24, 16), sz.round)


def big_yus(m, capital):
    sz = size(m, capital)
    h = sz.height
    width = pick(m, sz, *YUS_WIDTH)
    thickness = sz.diag * pick(m, sz, *ZHE_DIAG)
    middle = width / 2
    apex = h * m.v(*YUS_APEX)
    upper, stroke = vee(width, thickness * YUS_FLAT, h - apex, thickness)
    solid = (h - apex) * (thickness * YUS_FLAT / 2) / (middle - stroke + thickness * YUS_FLAT / 2)
    join = apex + solid * YUS_JOIN
    lower, _ = vee(width, thickness * YUS_FOOT, join, thickness)
    shapes = [
        rect(0, h - sz.bar * m.v(*YUS_BAR), width, h),
        shift([upper], 0, apex)[0],
        flop([lower], join / 2)[0],
        rect(middle - sz.stem / 2, 0, middle + sz.stem / 2, apex + solid * YUS_STEM),
    ]
    return spaced(m, shapes, width, sz.diagonal, sz.diagonal)


def hard(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    reach = pick(m, sz, *HARD_SPUR)
    width = reach + pick(m, sz, *SOFT_WIDTH)
    post = polygon([(0, h), (reach + stem, h), (reach + stem, 0), (reach, 0), (reach, h - bar), (0, h - bar)])
    return spaced(m, [post] + soft_bowl(m, sz, reach, width), width, m.v(24, 16), sz.round)


def yeru(m, capital):
    sz = size(m, capital)
    bowl = pick(m, sz, *YERU_BOWL)
    post = bowl + pick(m, sz, *YERU_GAP)
    shapes = [rect(0, 0, sz.stem, sz.height)] + soft_bowl(m, sz, 0, bowl) + [rect(post, 0, post + sz.stem, sz.height)]
    return spaced(m, shapes, post + sz.stem, sz.straight, sz.straight)


def be(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    width = pick(m, sz, *SOFT_WIDTH) + m.v(4, 6)
    arm = width - pick(m, sz, *BE_ARM)
    post = polygon([(0, 0), (0, h), (arm, h), (arm, h - bar), (stem, h - bar), (stem, 0)])
    return spaced(m, [post] + soft_bowl(m, sz, 0, width), width, sz.straight, sz.round)


def ve(m):
    sz = size(m, False)
    stem = sz.stem
    width = m.v(440, 506, light=424, black=574)
    bar = m.v(68, 94, light=50, black=106)
    waist = XH * m.v(0.53, 0.525)
    side = sz.side
    round_out = m.v(1.0, 1.04, light=1.0, black=1.16)
    upper_top, upper_bottom = XH, waist - bar / 2
    upper_side = side * m.v(0.94, 0.84, black=0.8)
    upper = lobe(m, stem * 0.5, stem * 0.8, width - m.v(24, 26), upper_top, upper_bottom, bar, upper_side, (upper_top - upper_bottom) / 2 * round_out)
    lower_top = waist + bar / 2
    lower = lobe(m, stem * 0.5, stem * 0.8, width, lower_top, 0, bar, side * m.v(1.0, 0.94, black=0.9), lower_top / 2 * round_out)
    return spaced(m, [rect(0, 0, stem, XH)] + upper + lower, width, "straight", m.v(30, 22))


def iu(m, capital, top=None):
    sz = size(m, capital)
    stem = sz.stem
    left = stem + pick(m, sz, *IU_GAP)
    width = left + pick(m, sz, *IU_RING)
    side = sz.side * m.v(0.98, 0.94, black=0.92)
    centre = sz.height * 0.5
    shapes = [rect(0, 0, stem, top or sz.height)]
    over = m.cap_ov if capital else m.ov
    shapes += ring(left, -over, width, sz.height + over, side, sz.thin, m.k_out, m.k_in)
    shapes.append(rect(stem * 0.5, centre - sz.bar / 2, left + side * 0.5, centre + sz.bar / 2))
    return spaced(m, shapes, width, sz.straight, sz.round)


def ef(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *EF_WIDTH)
    inset = m.v(*EF_INSET)
    bottom, top = (inset, CAP - inset) if capital else (-m.ov, XH + m.ov)
    low, high = (0, CAP) if capital else (DESC, ASC)
    side = sz.side * m.v(*EF_SIDE)
    cuts = ((width - sz.stem) / 2, (width + sz.stem) / 2)
    shapes = ring(0, bottom, width, top, side, sz.thin * m.v(1.0, 0.94, black=0.9), m.k_out, m.k_in, cuts)
    shapes.append(rect((width - sz.stem) / 2, low, (width + sz.stem) / 2, high))
    return spaced(m, shapes, width, sz.round, sz.round)


def te(m):
    sz = size(m, False)
    width = m.v(*TE_WIDTH)
    shapes = [rect(0, XH - sz.bar, width, XH), rect((width - sz.stem) / 2, 0, (width + sz.stem) / 2, XH - sz.bar * 0.5)]
    return spaced(m, shapes, width, m.v(18, 12), m.v(18, 12), capital=False)


def reversed_round(m, glyph, sz, share):
    left, right = accents.bounds(glyph.contours)
    contours = mirror(glyph.contours, glyph.advance / 2)
    left, right = glyph.advance - right, glyph.advance - left
    centre = sz.height * 0.5 + (0 if sz.capital else m.v(6, 4))
    start = left + (right - left) * share
    end = right - sz.side * 0.5
    bar = rect(start, centre - sz.bar / 2, end, centre + sz.bar / 2)
    return Glyph(contours + [bar], glyph.advance)


def ereversed(m, capital):
    sz = size(m, capital)
    glyph = capitals.capital_c(m) if capital else lowercase.letter_c(m)
    return reversed_round(m, glyph, sz, pick(m, sz, *REVERSED_BAR))


def ukrainian_ie(m, capital):
    sz = size(m, capital)
    glyph = capitals.capital_c(m) if capital else lowercase.letter_c(m)
    left, right = accents.bounds(glyph.contours)
    centre = sz.height * 0.5 + (0 if capital else m.v(6, 4))
    start = left + sz.side * 0.5
    end = left + (right - left) * pick(m, sz, *UKRAINIAN_BAR)
    return Glyph(glyph.contours + [rect(start, centre - sz.bar / 2, end, centre + sz.bar / 2)], glyph.advance)


LEG_INNER = ((100, 104, 98, 104), (78, 82, 76, 82))
LEG_FOOT = ((80, 116, 56, 142), (74, 110, 52, 124))
LEG_FLAT = ((26, 22, 28, 18), (20, 16, 22, 12))
EL_WIDTH = ((616, 684, 594, 732), (494, 562, 474, 610))
DE_WIDTH = ((656, 730, 632, 784), (520, 592, 500, 642))
DE_SLAB = (1.04, 1.0, 1.06, 0.96)
DE_EXTENSION = 0.42
ZHE_HALF = ((462, 526, 446, 584), (378, 438, 364, 496))
ZHE_BRANCH = ((300, 282, 304, 270), (236, 220, 238, 210))
ZHE_INSET = ((16, 12, 18, 8), (12, 10, 14, 6))
ZHE_DIAG = ((0.98, 0.9, 1.0, 0.8), (0.98, 0.9, 1.0, 0.78))
ZHE_CUT = 0.3
ZE_WIDTH = ((520, 584, 500, 636), (414, 476, 398, 528))
ZE_TONGUE = (0.3, 0.32, 0.29, 0.34)
ZE_WAIST = 0.54
ZE_END = ((84, 134, 58, 176), (76, 120, 52, 140))
ZE_HIGH = ((554, 544, 556, 540), (410, 396, 414, 390))
ZE_LOW = ((150, 166, 148, 172), (128, 146, 126, 152))
U_WIDTH = (590, 660, 570, 716)
U_JOIN = 0.3
CHE_WIDTH = ((544, 610, 524, 656), (434, 500, 418, 548))
CHE_BOWL = ((256, 250, 258, 244), (204, 198, 206, 194))
CHE_THICK = ((80, 118, 56, 148), (76, 112, 54, 140))
CHE_OUT = ((200, 214, 196, 222), (156, 168, 152, 176))
CHE_IN = ((150, 144, 152, 138), (112, 106, 114, 100))
YA_WIDTH = ((542, 614, 520, 672), (430, 494, 414, 540))
YA_BOTTOM = ((316, 304, 320, 288), (236, 228, 238, 216))
YA_REACH = ((236, 250, 230, 258), (176, 188, 172, 196))
TSHE_HANG = (118, 112, 120, 104)
TSHE_BAR = (214, 206, 216, 196)
TSHE_SPAN = (470, 532, 452, 576)
TSHE_TOP = (452, 460, 448, 466)
LJE_EL = ((540, 600, 520, 640), (430, 490, 412, 562))
LJE_BOWL = ((400, 458, 384, 500), (326, 390, 312, 428))
NJE_LEFT = ((470, 528, 452, 566), (380, 436, 366, 474))
NUMERO_GAP = (34, 28, 36, 22)
NUMERO_RULE = (26, 26, 32, 24)
NUMERO_RULE_WEIGHT = (1.0, 0.9)
BE_SMALL_WIDTH = (480, 540, 464, 584)
BE_TOP = (26, 22, 28, 18)
H_WIDTH = (566, 632)
X_WIDTH = ((574, 652), (432, 504, None, 570))
T_WIDTH = (516, 574)
V_WIDTH = (440, 510, None, 578)
CROSS_WEIGHT = (0.8, 0.7, 0.86, 0.6)
CHE_CROSS_EXTRA = ((10, 44, 0, 120), (10, 56, 0, 130))
KA_CROSS_EXTRA = ((40, 88, 30, 156), (34, 78, 26, 140))
KA_CROSS_GAP = ((64, 60, 68, 68), (56, 52, 60, 64))
CHE_CROSS_REACH = ((126, 120, 128, 112), (100, 96, 102, 90))
KA_CROSS_STUB = ((84, 76, 86, 70), (66, 60, 68, 54))
KA_CROSS_LOW = ((176, 160, 180, 140), (130, 118, 132, 104))
GHAYN_OVER = ((58, 62, 54, 66), (52, 56, 48, 60))
GHAYN_AFTER = ((150, 166, 142, 178), (112, 124, 106, 134))
GHAYN_HEIGHT = ((0.48, 0.48), (0.47, 0.47))
STRAIGHT_U_BAR = ((236, 216, 244, 200), (-52, -56, -50, -60))
STRAIGHT_U_REACH = ((160, 176, 152, 190), (132, 146, 124, 160))
STRAIGHT_U_SNAP = 12
SHHA_SPAN = (520, 584, 502, 630)
VE_ROUND_WIDTH = (456, 524, 440, 598)
VE_ROUND_WAIST = (398, 404, 396, 410)
VE_ROUND_LOOP = (418, 482, 402, 558)
VE_ROUND_FLAT = (68, 94, 50, 102)
VE_ROUND_SIDE = (50, 38, 52, 30)
GE_ROUND_WIDTH = (392, 462, 378, 528)
ZE_LONG_WIDTH = (444, 506, 428, 556)
ZE_LONG_HIGH = (566, 556, 568, 550)
ZE_LONG_LOW = (150, 166, 148, 172)
SOFT_ROUND_WIDTH = (430, 496, 414, 546)
SOFT_ROUND_TOP = (352, 370, 346, 392)
SOFT_ROUND_BAR = (72, 98, 52, 106)
SERBIAN_WIDTH = (468, 532, 452, 584)
SERBIAN_TIP = (30, 24, 32, 18)
SERBIAN_TOP_RUN = 0.6
SERBIAN_STEM_X = (0.44, 0.45, 0.44, 0.46)
SERBIAN_STEM = (0.86, 0.8, 0.9, 0.74)
SERBIAN_JOINT_X = 0.56
SERBIAN_JOINT_HEADING = (-40, -36, -42, -32)
SERBIAN_JOINT = (0.8, 0.76, 0.82, 0.72)


def leg(m, sz):
    inner = pick(m, sz, *LEG_INNER)
    return inner, pick(m, sz, *LEG_FOOT), inner * HOOK_SPREAD + pick(m, sz, *LEG_FLAT)


def leg_curves(m, sz, base):
    inner, foot, left = leg(m, sz)
    right = left + sz.stem
    inner_height = inner * HOOK_DEPTH
    outer_x = sz.stem + inner * HOOK_SPREAD
    outer_y = foot + inner_height * HOOK_BELLY
    outer = quarter((right, base + outer_y), (right - outer_x, base), "v", m.k_out - 0.02)
    return left, right, inner, inner_height, foot, outer


def el_shape(m, sz, width):
    h, stem, bar = sz.height, sz.stem, sz.bar
    left, right, inner, inner_height, foot, outer = leg_curves(m, sz, 0)
    path = Path((right, h - bar))
    path.to(outer[0])
    path.bez(outer)
    path.to((0, 0))
    path.to((0, foot))
    path.to((left - inner, foot))
    path.arc((left, foot + inner_height), "h", m.k_in + 0.02)
    path.to((left, h))
    path.to((width, h))
    path.to((width, 0))
    path.to((width - stem, 0))
    path.to((width - stem, h - bar))
    return path.close()


def el(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *EL_WIDTH)
    return spaced(m, [el_shape(m, sz, width)], width, m.v(18, 12, light=20, black=8), sz.straight)


def de(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    width = pick(m, sz, *DE_WIDTH)
    foot, depth = spur(m, sz)
    slab = bar * m.v(*DE_SLAB)
    post = width - foot * DE_EXTENSION
    tip = leg(m, sz)[1]
    left, right, inner, inner_height, _, outer = leg_curves(m, sz, slab - tip)
    rim = reach(outer, 1, slab)
    path = Path((0, depth))
    path.to((0, slab))
    path.to((left - inner, slab))
    path.arc((left, slab + inner_height), "h", m.k_in + 0.02)
    path.to((left, h))
    path.to((post, h))
    path.to((post, slab))
    path.to((width, slab))
    path.to((width, depth))
    path.to((width - foot, depth))
    path.to((width - foot, 0))
    path.to((foot, 0))
    path.to((foot, depth))
    hole = Path((right, h - bar))
    hole.to(rim[0])
    hole.bez(rim)
    hole.to((post - stem, slab))
    hole.to((post - stem, h - bar))
    sides = pick(m, sz, *DE_SIDES)
    return spaced(m, [path.close(), hole.close(hole=True)], width, sides, sides, capital=capital)


def arms(m, stem, cut, width, height, branch, inset, thickness):
    low0, low1 = (stem, branch), (width - inset, height)
    direction = (low1[0] - low0[0], low1[1] - low0[1])
    slope = direction[1] / direction[0]
    stroke = across(direction, thickness)
    high1 = (low1[0] - stroke, height)
    low_cut = (cut, low0[1] + (cut - stem) * slope)
    high_cut = (cut, height + (cut - high1[0]) * slope)
    upper = polygon([low_cut, high_cut, high1, low1])
    centre0 = (cut, (low_cut[1] + high_cut[1]) / 2)
    centre1 = ((low1[0] + high1[0]) / 2, height)
    knee_x = stem + direction[0] * m.v(0.42, 0.44)
    knee = (knee_x, centre0[1] + (knee_x - cut) * slope)
    leg_direction = (knee[0] - width, knee[1])
    leg_stroke = across(leg_direction, thickness * m.v(1.02, 1.02))
    foot = (width - leg_stroke, 0)
    crotch = intersect(foot, (foot[0] + leg_direction[0], leg_direction[1]), centre0, centre1)
    lower = polygon([foot, crotch, knee, (width, 0)])
    return [upper, lower]


def zhe_parts(m, sz, top=None):
    stem = sz.stem * m.v(1.0, 0.94, light=1.0, black=0.86)
    half = pick(m, sz, *ZHE_HALF)
    thickness = sz.diag * pick(m, sz, *ZHE_DIAG)
    right = arms(m, stem, stem * ZHE_CUT, half, sz.height, pick(m, sz, *ZHE_BRANCH), pick(m, sz, *ZHE_INSET), thickness)
    offset = half - stem
    placed = shift(right, offset)
    return rect(offset, 0, offset + stem, top or sz.height), placed, mirror(placed, offset + stem / 2), 2 * half - stem


def zhe(m, capital):
    sz = size(m, capital)
    post, right, left, width = zhe_parts(m, sz)
    return spaced(m, [post] + right + left, width, sz.diagonal, sz.diagonal)


def zhe_descender(m, capital):
    sz = size(m, capital)
    post, (upper, lower), left, width = zhe_parts(m, sz)
    return tail_spaced(m, sz, [post, upper, tailed(m, sz, lower)] + left, width, sz.diagonal)


def ze(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *ZE_WIDTH)
    strokes = ze_strokes(m, sz, sz.height, width, pick(m, sz, *ZE_HIGH), pick(m, sz, *ZE_LOW))
    return spaced(m, strokes, width, m.v(30, 22), sz.round)


def ze_strokes(m, sz, h, width, high, low):
    edge = sz.side * m.v(1.0, 0.96, light=1.0, black=0.94)
    flat = sz.thin * m.v(1.0, 0.96, light=1.0, black=0.9)
    waist_y = h * ZE_WAIST
    waist = flat * m.v(0.94, 0.9, light=0.96, black=0.84)
    end = pick(m, sz, *ZE_END)
    inset = m.v(26, 22, light=28, black=18)
    rise, fall = aim(m.v(62, 60)), aim(m.v(118, 120))
    upper = ribbon(
        [
            Node((inset + end / (2 * rise[1]), high), rise, end, cut="h"),
            Node((width * 0.5, h + m.ov - flat / 2), RIGHT, flat),
            Node((width - m.v(26, 22) - edge * 0.44, h - (h - waist_y) * m.v(0.48, 0.5, light=0.47, black=0.56)), DOWN, edge * m.v(0.9, 0.86)),
            Node((width * 0.52, waist_y), LEFT, waist),
            Node((width * m.v(*ZE_TONGUE), waist_y), LEFT, waist, straight=True, cut="v"),
        ],
        0.6,
    )
    lower = ribbon(
        [
            Node((width * 0.42, waist_y), RIGHT, waist, cut="v"),
            Node((width * 0.54, waist_y), RIGHT, waist, straight=True),
            Node((width - edge / 2, waist_y * 0.47), DOWN, edge),
            Node((width * 0.49, flat / 2 - m.ov), LEFT, flat),
            Node((inset + end / (2 * fall[1]), low), fall, end, cut="h"),
        ],
        0.6,
    )
    return [upper, lower]


def u_shape(m, sz, width):
    h = sz.height
    join = h * U_JOIN
    rise = h - join
    middle = width / 2
    flat = sz.diag * m.v(1.2, 1.1)
    direction = (middle - flat / 2, -rise)
    stroke = across(direction, sz.diag)
    slope = direction[0] / rise
    foot = width - slope * h
    tail = polygon([(width - stroke, h), (width, h), (foot, 0), (foot - stroke, 0)])
    notch = intersect((stroke, h), (stroke + direction[0], join), (middle, join), (middle, h))
    meet = intersect((0, h), (direction[0], join), (width - stroke, h), (foot - stroke, 0))
    branch = polygon([(0, h), (stroke, h), notch, (meet[0] + stroke * 0.6, meet[1]), meet])
    return [tail, branch]


def u(m):
    sz = size(m, True)
    width = m.v(*U_WIDTH)
    return spaced(m, u_shape(m, sz, width), width, sz.diagonal, sz.diagonal)


def che_parts(m, sz, extra=0):
    h, stem = sz.height, sz.stem
    width = pick(m, sz, *CHE_WIDTH) + extra
    bowl = arch(
        left_out=stem * shoulder_spring(m),
        left_in=stem * shoulder_inner(m),
        peak_out=width * 0.55,
        peak_in=stem + (width - 2 * stem) * 0.52,
        right=width,
        top=h - pick(m, sz, *CHE_BOWL),
        base=0,
        stem=stem,
        thick=pick(m, sz, *CHE_THICK),
        ry_out=pick(m, sz, *CHE_OUT),
        ry_in=pick(m, sz, *CHE_IN),
        k_out=m.k_out,
        k_in=m.k_in,
    )
    return turn([rect(0, 0, stem, h), bowl], width / 2, h / 2), width


def che(m, capital):
    sz = size(m, capital)
    shapes, width = che_parts(m, sz)
    return spaced(m, shapes, width, sz.straight, sz.straight)


def che_descender(m, capital):
    sz = size(m, capital)
    (post, bowl), width = che_parts(m, sz)
    return tail_spaced(m, sz, [tailed(m, sz, post), bowl], width, sz.straight)


def che_stroke(m, capital):
    sz = size(m, capital)
    shapes, width = che_parts(m, sz, pick(m, sz, *CHE_CROSS_EXTRA))
    low = pick(m, sz, *CHE_BOWL)
    high = low + pick(m, sz, *CHE_THICK)
    reach = pick(m, sz, *CHE_CROSS_REACH)
    half = sz.stem * m.v(*CROSS_WEIGHT) / 2
    stroke = rect(width / 2 - half, low - reach, width / 2 + half, high + reach)
    return spaced(m, shapes + [stroke], width, sz.straight, sz.straight)


def ar(m, sz):
    h, stem = sz.height, sz.stem
    width = pick(m, sz, *YA_WIDTH)
    bar = (sz.bar if sz.capital else m.v(68, 98, light=50, black=118)) * m.v(1, 1, black=0.92)
    bottom = pick(m, sz, *YA_BOTTOM)
    shapes = [rect(0, 0, stem, h)] + lobe(m, stem * 0.5, stem * 0.8, width - m.v(18, 16), h, bottom, bar, sz.side)
    top = (pick(m, sz, *YA_REACH), bottom + bar * 0.5)
    stroke = band_width(width - top[0], top[1], sz.diag * m.v(1.0, 0.96))
    shapes.append(band(top, (width - stroke, 0), stroke))
    return shapes, width


def ya(m, capital):
    sz = size(m, capital)
    shapes, width = ar(m, sz)
    return spaced(m, mirror(shapes, width / 2), width, m.v(26, 16) if capital else m.v(14, 8), sz.straight)


def tshe_top(m, sz):
    stem = sz.stem
    hang = m.v(*TSHE_HANG)
    end = hang + stem + m.v(*TSHE_BAR)
    return hang, polygon([(0, CAP), (end, CAP), (end, CAP - sz.bar), (hang + stem, CAP - sz.bar), (hang + stem, 0), (hang, 0), (hang, CAP - sz.bar), (0, CAP - sz.bar)]), end


def shoulder_edges(m, x, stem, span):
    return (
        x + stem * shoulder_spring(m),
        x + stem * shoulder_inner(m),
        x + span * 0.55,
        x + stem + (span - 2 * stem) * 0.52,
        x + span,
    )


def tshe(m):
    sz = size(m, True)
    stem = sz.stem
    hang, top, end = tshe_top(m, sz)
    span = m.v(*TSHE_SPAN)
    edges = shoulder_edges(m, hang, stem, span)
    shoulder = arch(
        left_out=edges[0],
        left_in=edges[1],
        peak_out=edges[2],
        peak_in=edges[3],
        right=edges[4],
        top=m.v(*TSHE_TOP),
        base=0,
        stem=stem,
        thick=m.v(76, 112, light=54, black=140),
        ry_out=m.v(204, 218),
        ry_in=m.v(146, 140),
        k_out=m.k_out,
        k_in=m.k_in,
    )
    width = max(end, hang + span)
    return spaced(m, [top, shoulder], width, m.v(28, 20), sz.straight)


def dje(m):
    sz = size(m, True)
    stem = sz.stem
    hang, top, end = tshe_top(m, sz)
    span = m.v(*TSHE_SPAN)
    shoulder = latin.descending_arch(
        m,
        shoulder_edges(m, hang, stem, span),
        m.v(*TSHE_TOP),
        m.v(76, 112, light=54, black=140),
        m.v(204, 218),
        m.v(146, 140),
        stem,
        DESC,
        m.v(78, 114, light=55, black=130),
        m.v(110, 114, light=106, black=118),
    )
    width = max(end, hang + span)
    return spaced(m, [top, shoulder], width, m.v(28, 20), sz.straight)


def small_dje(m):
    stem = m.stem
    width = m.v(450, 520)
    shoulder = latin.descending_arch(
        m,
        shoulder_edges(m, 0, stem, width),
        XH + m.arch_ov,
        m.v(76, 112, light=54, black=140),
        m.v(200, 214),
        m.v(142, 136),
        stem,
        DESC,
        m.v(74, 110, light=52, black=124),
        m.v(88, 88, black=90),
    )
    glyph = spaced(m, [rect(0, 0, stem, ASC), shoulder], width, "straight", m.v(66, 50))
    left, right = latin.ink(glyph)
    bottom, top = latin.ascender_bar(m)
    over = m.v(44, 48, light=40, black=50)
    end = left + (right - left) * m.v(0.56, 0.58, black=0.6)
    return latin.widened(glyph, [rect(left - over, bottom, end, top)], over * 0.5)


def lje(m, capital):
    sz = size(m, capital)
    stem = sz.stem
    el_width = pick(m, sz, *LJE_EL)
    width = el_width - stem + pick(m, sz, *LJE_BOWL)
    shapes = [el_shape(m, sz, el_width)] + soft_bowl(m, sz, el_width - stem, width)
    return spaced(m, shapes, width, m.v(18, 12, light=20, black=8), sz.round)


def nje(m, capital):
    sz = size(m, capital)
    stem = sz.stem
    post = pick(m, sz, *NJE_LEFT)
    width = post - stem + pick(m, sz, *LJE_BOWL)
    top = pick(m, sz, *SOFT_TOP)
    bar = pick(m, sz, *SOFT_BAR)
    shapes = [rect(0, 0, stem, sz.height), rect(post - stem, 0, post, sz.height), rect(stem * 0.5, top - bar, post - stem * 0.6, top)]
    shapes += soft_bowl(m, sz, post - stem, width)
    return spaced(m, shapes, width, sz.straight, sz.round)


def em(m, capital):
    sz = size(m, capital)
    stem = sz.stem
    width = pick(m, sz, *EM_WIDTH)
    thickness = sz.diag * m.v(0.94, 0.88, black=0.84)
    inset = 0
    for _ in range(8):
        middle, stroke = vee(width - 2 * inset, thickness * m.v(1.15, 1.0, black=0.8), sz.height, thickness)
        inset = max(0, stem - stroke + m.v(2, 3))
    shapes = [rect(0, 0, stem, sz.height), rect(width - stem, 0, width, sz.height), shift([middle], inset)[0]]
    return spaced(m, shapes, width, sz.straight, sz.straight)


def small_be(m):
    width = m.v(*BE_SMALL_WIDTH)
    edge = m.round
    flat = m.thin
    top = ASC - flat / 2
    tip = width - m.v(*BE_TOP)
    shape = ribbon(
        [
            Node((tip, top), LEFT, flat, cut="v"),
            Node((width * m.v(0.5, 0.52), top), LEFT, flat, straight=True),
            Node((edge / 2, ASC - m.v(210, 230)), DOWN, edge, arrive=m.v(0.62, 0.66)),
            Node((edge / 2, XH * 0.5), DOWN, edge, straight=True),
            Node((width * 0.5, flat / 2 - m.ov), RIGHT, flat),
            Node((width - edge / 2, XH * 0.5 - m.v(4, 6)), UP, edge),
            Node((width * 0.5, XH + m.ov - flat * 0.46), LEFT, flat * 0.92),
            Node((edge * 0.5, XH * m.v(0.6, 0.58)), aim(m.v(246, 250)), m.v(50, 80, light=34, black=102), arrive=0.5),
        ],
        0.6,
    )
    return spaced(m, [shape], width, "round", "round")


def numero(m):
    n = capitals.capital_n(m)
    o = symbols.ordmasculine(m)
    left, right = accents.bounds(o.contours)
    start = n.advance - m.bearing("cap") + m.v(*NUMERO_GAP)
    ring_part = shift(o.contours, start - left)
    base = min(point[1] for contour in o.contours for point in contour.points())
    rule_top = base - m.v(*NUMERO_RULE)
    rule = rect(start, rule_top - symbols.ordinal_stem(m) * m.v(*NUMERO_RULE_WEIGHT), start + right - left, rule_top)
    return Glyph(n.contours + ring_part + [rule], start + right - left + m.v(40, 30))


def en_descender(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    width = m.v(*H_WIDTH) if capital else m.v(*EN_WIDTH)
    centre = capitals.WAIST if capital else h * 0.5
    shapes = [
        rect(0, 0, stem, h),
        tailed(m, sz, rect(width - stem, 0, width, h)),
        rect(stem * 0.5, centre - bar / 2, width - stem * 0.5, centre + bar / 2),
    ]
    return tail_spaced(m, sz, shapes, width, sz.straight)


def en_ghe(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    width = m.v(*H_WIDTH) if capital else m.v(*EN_WIDTH)
    centre = capitals.WAIST if capital else h * 0.5
    arm = width + (pick(m, sz, *GE_WIDTH) - stem) * 0.7
    shapes = [
        rect(0, 0, stem, h),
        polygon([(width - stem, 0), (width - stem, h), (arm, h), (arm, h - bar), (width, h - bar), (width, 0)]),
        rect(stem * 0.5, centre - bar / 2, width - stem * 0.5, centre + bar / 2),
    ]
    return spaced(m, shapes, arm, sz.straight, pick(m, sz, *GE_RIGHT))


def ghe_hook(m, capital):
    sz = size(m, capital)
    stem = sz.stem
    width = pick(m, sz, *GE_WIDTH)
    if capital:
        span, top, ry_out, ry_in = m.v(*TSHE_SPAN), m.v(*TSHE_TOP), m.v(204, 218), m.v(146, 140)
        thin, reach = m.v(78, 114, light=55, black=130), m.v(110, 114, light=106, black=118)
    else:
        span, top, ry_out, ry_in = m.v(430, 494, light=414, black=536), m.v(368, 350, light=376, black=334), m.v(170, 178), m.v(116, 104, light=120, black=96)
        thin, reach = m.v(74, 110, light=52, black=124), m.v(88, 88, black=90)
    hook = latin.descending_arch(
        m,
        shoulder_edges(m, 0, stem, span),
        top,
        m.v(76, 112, light=54, black=140),
        ry_out,
        ry_in,
        stem,
        DESC,
        thin,
        reach,
    )
    return spaced(m, [ge_shape(sz, width), hook], max(width, span), sz.straight, m.v(40, 30))


def te_descender(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    width = m.v(*T_WIDTH) if capital else m.v(*TE_WIDTH)
    left = (width - stem) / 2
    shapes = [rect(0, h - bar, width, h), tailed(m, sz, rect(left, 0, left + stem, h - bar * 0.5))]
    side = m.v(28, 20) if capital else m.v(18, 12)
    return spaced(m, shapes, width, side, side, capital=capital)


def ka_parts(m, capital):
    glyph, side = (capitals.capital_k(m), "cap") if capital else (latin.kgreenlandic(m), "straight")
    stem, upper, lower = shift(glyph.contours, -m.bearing(side))
    return stem, upper, lower, max(x for x, _ in lower.corners())


def ka_descender(m, capital):
    sz = size(m, capital)
    stem, upper, lower, width = ka_parts(m, capital)
    return tail_spaced(m, sz, [stem, upper, tailed(m, sz, lower)], width, sz.straight)


def bashkir_ka(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    _, upper, lower, width = ka_parts(m, capital)
    spur_reach = pick(m, sz, *HARD_SPUR)
    post = polygon([(0, h), (spur_reach + stem, h), (spur_reach + stem, 0), (spur_reach, 0), (spur_reach, h - bar), (0, h - bar)])
    return spaced(m, [post] + shift([upper, lower], spur_reach), spur_reach + width, m.v(24, 16), sz.diagonal)


def ka_stroke(m, capital):
    sz = size(m, capital)
    if capital:
        width, branch, inset = m.v(576, 660), m.v(252, 214), m.v(18, 14)
    else:
        width, branch, inset = m.v(446, 536), m.v(196, 160), m.v(14, 12)
    width += pick(m, sz, *KA_CROSS_EXTRA)
    shapes = kay(m, sz.stem, width, sz.height, sz.height, branch, inset, sz.diag)
    low_cut, high_cut, high, low = shapes[1].corners()
    start = ((low_cut[0] + high_cut[0]) / 2, (low_cut[1] + high_cut[1]) / 2)
    end = ((high[0] + low[0]) / 2, (high[1] + low[1]) / 2)
    half = sz.stem * m.v(*CROSS_WEIGHT) / 2
    x = sz.stem + pick(m, sz, *KA_CROSS_GAP) + half
    y = start[1] + (end[1] - start[1]) * (x - start[0]) / (end[0] - start[0])
    top = y + (high_cut[1] - low_cut[1]) / 2 + pick(m, sz, *KA_CROSS_STUB)
    stroke = rect(x - half, pick(m, sz, *KA_CROSS_LOW), x + half, top)
    return spaced(m, shapes + [stroke], width, sz.straight, sz.diagonal)


def ha_descender(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *X_WIDTH)
    stroke = band_width(width, sz.height, sz.diag)
    falling = band((0, sz.height), (width - stroke, 0), stroke)
    rising = band((width - stroke, sz.height), (0, 0), stroke)
    return tail_spaced(m, sz, [tailed(m, sz, falling), rising], width, sz.diagonal)


def ghayn(m, capital, draw=None):
    sz = size(m, capital)
    glyph = (draw or ge)(m, capital)
    left = m.bearing(sz.straight)
    over = pick(m, sz, *GHAYN_OVER)
    centre = sz.height * pick(m, sz, *GHAYN_HEIGHT)
    half = sz.bar * m.v(0.96, 0.92, light=1.0, black=0.88) / 2
    bar = rect(left - over, centre - half, left + sz.stem + pick(m, sz, *GHAYN_AFTER), centre + half)
    return latin.widened(glyph, [bar], over * 0.5)


def straight_u(m):
    sz = size(m, False)
    width = m.v(*V_WIDTH)
    middle = width / 2
    stem = sz.stem
    direction = (middle - stem / 2, -XH)
    stroke = across(direction, sz.diag)
    notch = (middle, XH + (middle - stroke) * direction[1] / direction[0])
    points = [
        (0, XH),
        (stroke, XH),
        notch,
        (width - stroke, XH),
        (width, XH),
        (middle + stem / 2, 0),
        (middle + stem / 2, DESC),
        (middle - stem / 2, DESC),
        (middle - stem / 2, 0),
    ]
    return spaced(m, [polygon(points)], width, "diagonal", "diagonal")


def barred_straight_u(m, capital):
    sz = size(m, capital)
    glyph = capitals.capital_y(m) if capital else straight_u(m)
    left, right = accents.bounds(glyph.contours)
    middle = (left + right) / 2
    centre = pick(m, sz, *STRAIGHT_U_BAR)
    reach = pick(m, sz, *STRAIGHT_U_REACH)
    half = sz.bar * m.v(0.96, 0.9, light=1.0, black=0.84) / 2
    if centre < 0 < centre + half + STRAIGHT_U_SNAP:
        centre = -half
    return Glyph(glyph.contours + [rect(middle - reach, centre - half, middle + reach, centre + half)], glyph.advance)


def shha(m):
    sz = size(m, True)
    stem = sz.stem
    span = m.v(*SHHA_SPAN)
    edges = shoulder_edges(m, 0, stem, span)
    shoulder = arch(
        left_out=edges[0],
        left_in=edges[1],
        peak_out=edges[2],
        peak_in=edges[3],
        right=edges[4],
        top=m.v(*TSHE_TOP),
        base=0,
        stem=stem,
        thick=m.v(76, 112, light=54, black=140),
        ry_out=m.v(204, 218),
        ry_in=m.v(146, 140),
        k_out=m.k_out,
        k_in=m.k_in,
    )
    return spaced(m, [rect(0, 0, stem, CAP), shoulder], span, sz.straight, m.v(74, 58))


def barred_o(m):
    width = m.v(476, 540, black=592)
    left = m.bearing("round")
    half = m.bar * m.v(1.0, 0.9, light=1.0, black=0.8) / 2
    glyph = lowercase.letter_o(m)
    bar = rect(left + m.round * 0.5, XH / 2 - half, left + width - m.round * 0.5, XH / 2 + half)
    return Glyph(glyph.contours + [bar], glyph.advance)


def bottom_x(glyph):
    corners = [point for contour in glyph.contours for point in contour.corners()]
    low = min(y for _, y in corners)
    xs = [x for x, y in corners if y < low + 0.5]
    return sum(xs) / len(xs)


def centre_tail(draw, capital):
    def build(m):
        sz = size(m, capital)
        glyph = draw(m)
        foot, depth = spur(m, sz)
        x = bottom_x(glyph)
        tail = rect(x - foot / 2, depth, x + foot / 2, sz.thin * 0.4 - m.ov)
        return Glyph(glyph.contours + [tail], glyph.advance)

    return build


def round_ve(m):
    width = m.v(*VE_ROUND_WIDTH)
    side = m.round
    flat = m.v(*VE_ROUND_FLAT)
    waist = m.v(*VE_ROUND_WAIST)
    loop = m.v(*VE_ROUND_LOOP)
    edge = side * m.v(0.92, 0.86, light=0.94, black=0.8)
    corner = (ASC + m.ov - waist) * 0.42
    top = ASC + m.ov - flat / 2
    upper = ribbon(
        [
            Node((side / 2, (waist - m.ov) / 2), UP, side),
            Node((side / 2, top - corner), UP, side, straight=True),
            Node((side / 2 + corner, top), RIGHT, flat),
            Node((loop - edge / 2 - corner, top), RIGHT, flat, straight=True),
            Node((loop - edge / 2, waist + (ASC - waist) * 0.5), DOWN, edge),
            Node((width * 0.46, waist - flat / 2), LEFT, flat * 0.9),
        ],
        0.6,
    )
    lower = ring(0, -m.ov, width, waist, side, flat, m.k_out, m.k_in)
    return spaced(m, lower + [upper], width, m.v(*VE_ROUND_SIDE), "round")


def round_ge(m):
    width = m.v(*GE_ROUND_WIDTH)
    shape = ess(
        m,
        width=width,
        height=XH,
        side=m.v(84, 152, light=58, black=180),
        flat=m.v(72, 116, light=50, black=116),
        spine=m.v(86, 136, light=58, black=134),
        inset=m.v(14, 8, light=16, black=4),
        upper_y=m.v(394, 404, light=390, black=420),
        lower_y=m.v(148, 138, light=150, black=116),
        angle=m.v(20, 22),
        t=m.v(0.56, 0.5),
    )
    return spaced(m, mirror([shape], width / 2), width, m.v(32, 24), m.v(30, 22), capital=False)


def long_ze(m):
    sz = size(m, False)
    width = m.v(*ZE_LONG_WIDTH)
    strokes = ze_strokes(m, sz, XH - DESC, width, m.v(*ZE_LONG_HIGH), m.v(*ZE_LONG_LOW))
    return spaced(m, shift(strokes, 0, DESC), width, m.v(30, 22), sz.round)


def tall_zhe(m):
    sz = size(m, False)
    post, right, left, width = zhe_parts(m, sz, ASC)
    return spaced(m, [post] + right + left, width, sz.diagonal, sz.diagonal)


def turned_vee(m):
    width = m.v(*V_WIDTH)
    shape, _ = vee(width, m.diag * m.v(1.2, 1.1), XH, m.diag, m.v(*lowercase.VEE_DEEPEN))
    return spaced(m, flop([shape], XH / 2), width, "diagonal", "diagonal")


def letter_parts(draw, m):
    glyph = draw(m)
    left, right = accents.bounds(glyph.contours)
    return shift(glyph.contours, -left), right - left, left, glyph.advance - right


def tailed_u(m):
    sz = size(m, False)
    (bowl, post), width, left, _ = letter_parts(lowercase.letter_u, m)
    return tail_spaced(m, sz, [bowl, tailed(m, sz, post)], width, left)


def turned_m(m):
    contours, width, left, right = letter_parts(lowercase.letter_m, m)
    return turn(contours, width / 2, XH / 2), width, right, left


def round_sha(m):
    shapes, width, left, right = turned_m(m)
    return spaced(m, shapes, width, left, right, capital=False)


def round_shcha(m):
    sz = size(m, False)
    (post, *bowls), width, left, _ = turned_m(m)
    return tail_spaced(m, sz, [tailed(m, sz, post)] + bowls, width, left)


def round_soft(m, flag=0):
    stem = m.stem
    width = flag + m.v(*SOFT_ROUND_WIDTH)
    if flag:
        post = polygon([(0, XH), (flag + stem, XH), (flag + stem, 0), (flag, 0), (flag, XH - m.bar), (0, XH - m.bar)])
    else:
        post = rect(0, 0, stem, XH)
    top = m.v(*SOFT_ROUND_TOP)
    bar = m.v(*SOFT_ROUND_BAR)
    bowl = [
        oval(flag + stem * m.v(0.25, 0.42), -m.ov, width, top + m.ov, m.k_out),
        oval(flag + stem * m.v(0.8, 0.66), bar - m.ov, width - m.round, top + m.ov - bar, m.k_in, hole=True),
    ]
    return spaced(m, [post] + bowl, width, m.v(24, 16) if flag else "straight", "round")


def round_hard(m):
    sz = size(m, False)
    return round_soft(m, pick(m, sz, *HARD_SPUR))


def tall_iu(m):
    return iu(m, False, ASC)


def serbian_be(m):
    width = m.v(*SERBIAN_WIDTH)
    side = m.round
    thin = m.thin
    flat = thin * m.v(0.96, 0.9, light=1.0, black=0.84)
    top = ASC - flat / 2
    branch = ribbon(
        [
            Node((width - m.v(*SERBIAN_TIP), top), LEFT, flat, cut="v"),
            Node((width * SERBIAN_TOP_RUN, top), LEFT, flat, straight=True),
            Node((width * m.v(*SERBIAN_STEM_X), (XH + m.ov + ASC - flat) / 2), DOWN, side * m.v(*SERBIAN_STEM)),
            Node((width * SERBIAN_JOINT_X, XH + m.ov - thin / 2), aim(m.v(*SERBIAN_JOINT_HEADING)), thin * m.v(*SERBIAN_JOINT)),
        ],
        0.6,
    )
    bowl = ring(0, -m.ov, width, XH + m.ov, side, thin, m.k_out, m.k_in)
    return spaced(m, bowl + [branch], width, "round", "round")


HOOK_THIN = ((78, 114, 55, 130), (74, 110, 52, 124))
HOOK_REACH = ((114, 118, 110, 122), (88, 88, 88, 90))
HOOK_RIGHT = ((-20, -30, -16, -50), (-16, -24, -12, -40))
HOOK_TURN = ((60, 64, 58, 70), (48, 52, 46, 56))
HOOK_BOTTOM = 0.35
HOOK_ROOM = ((40, 40, 40, 40), (32, 32, 32, 32))
KA_HOOK_SIDE = (0.96, 0.92, 0.98, 0.88)
HA_HOOK_START = 0.42
HOOK_LAP = 8
STROKE_BAR_REACH = 0.62
TICK_WEIGHT = (0.92, 0.86, 0.96, 0.8)
TICK_IN = ((70, 54, 76, 40), (56, 42, 60, 30))
TICK_OUT = ((110, 104, 112, 100), (92, 88, 94, 84))
TICK_LEAN = 56
SEMISOFT_OVER = ((62, 66, 60, 70), (48, 52, 46, 54))
TE_TSE_REACH = 0.6
TE_TSE_SIDE = ((28, 20, 30, 14), (18, 12, 20, 10))
EAR_GAP = ((46, 44, 46, 42), (40, 38, 40, 36))
EAR_RISE = ((150, 156, 146, 162), (116, 122, 112, 128))
EAR_WEIGHT = (0.94, 0.9, 0.96, 0.86)
EAR_JOIN = 0.75


def ge_descender(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *GE_WIDTH)
    return spaced(m, [tailed(m, sz, ge_shape(sz, width))], width, sz.straight, pick(m, sz, *GE_RIGHT))


def descender_post(m, sz, x0, top):
    post = Path((x0, top)).to((x0 + sz.stem, top))
    latin.descend(post, m, x0 + sz.stem, sz.stem, DESC, pick(m, sz, *HOOK_THIN), pick(m, sz, *HOOK_REACH))
    return post.close()


def en_hook(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    width = m.v(*H_WIDTH) if capital else m.v(*EN_WIDTH)
    centre = capitals.WAIST if capital else h * 0.5
    shapes = [
        rect(0, 0, stem, h),
        descender_post(m, sz, width - stem, h),
        rect(stem * 0.5, centre - bar / 2, width - stem * 0.5, centre + bar / 2),
    ]
    return spaced(m, shapes, width, sz.straight, sz.straight)


def ge_hook(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    width = pick(m, sz, *GE_WIDTH)
    path = Path((width, h - bar)).to((stem, h - bar))
    latin.descend(path, m, stem, stem, DESC, pick(m, sz, *HOOK_THIN), pick(m, sz, *HOOK_REACH))
    path.to((0, h)).to((width, h))
    return spaced(m, [path.close()], width, sz.straight, pick(m, sz, *GE_RIGHT))


def hooked_curve(m, sz, start, heading, thickness, right):
    flat = pick(m, sz, *HOOK_THIN)
    side = sz.stem * m.v(*KA_HOOK_SIDE)
    bottom = DESC - m.ov + flat / 2
    reach = pick(m, sz, *HOOK_REACH)
    tip = right - side - reach
    crossing = start[1] + (right - side / 2 - start[0]) * heading[1] / heading[0]
    turn = max(crossing - pick(m, sz, *HOOK_TURN), bottom + flat / 2 + pick(m, sz, *HOOK_ROOM))
    return ribbon(
        [
            Node(start, heading, thickness, cut="h"),
            Node((right - side / 2, turn), DOWN, side),
            Node((right - side - reach * HOOK_BOTTOM, bottom), LEFT, flat),
            Node((tip, bottom), LEFT, flat, straight=True, cut="v"),
        ],
        0.6,
    )


def hooked_leg(m, sz, top_left, top_right, heading, right):
    run = heading[0] / heading[1]
    low = sz.height * HA_HOOK_START
    lap = low - HOOK_LAP

    def at(point, y):
        return (point[0] + (y - point[1]) * run, y)

    straight = polygon([top_left, top_right, at(top_right, lap), at(top_left, lap)])
    left, right_edge = at(top_left, low)[0], at(top_right, low)[0]
    across_width = (right_edge - left) * abs(heading[1]) / math.hypot(*heading)
    return [straight, hooked_curve(m, sz, ((left + right_edge) / 2, low), heading, across_width, right)]


def ka_hook(m, capital):
    sz = size(m, capital)
    stem, upper, lower, width = ka_parts(m, capital)
    _, crotch, knee, corner = lower.corners()
    heading = (corner[0] - knee[0], corner[1] - knee[1])
    right = width + pick(m, sz, *HOOK_RIGHT)
    shapes = [stem, upper] + hooked_leg(m, sz, crotch, knee, heading, right)
    return spaced(m, shapes, right, sz.straight, sz.round)


def ha_hook(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *X_WIDTH)
    stroke = band_width(width, sz.height, sz.diag)
    rising = band((width - stroke, sz.height), (0, 0), stroke)
    right = width + pick(m, sz, *HOOK_RIGHT)
    falling = hooked_leg(m, sz, (0, sz.height), (stroke, sz.height), (width - stroke, -sz.height), right)
    return spaced(m, falling + [rising], right, sz.diagonal, sz.round)


def ha_stroke(m, capital):
    sz = size(m, capital)
    glyph = capitals.capital_x(m) if capital else lowercase.letter_x(m)
    left, right = accents.bounds(glyph.contours)
    middle = (left + right) / 2
    reach = (right - left) * STROKE_BAR_REACH / 2
    half = sz.bar * m.v(0.96, 0.9, light=1.0, black=0.84) / 2
    centre = sz.height / 2
    return Glyph(glyph.contours + [rect(middle - reach, centre - half, middle + reach, centre + half)], glyph.advance)


def ii_tail(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *II_WIDTH)
    stroke = band_width(width, sz.height, sz.diag * pick(m, sz, *II_DIAG))
    shapes = [
        rect(0, 0, sz.stem, sz.height),
        tailed(m, sz, rect(width - sz.stem, 0, width, sz.height)),
        band((width - stroke, sz.height), (0, 0), stroke),
    ]
    return tail_spaced(m, sz, shapes, width, sz.straight)


def semisoft(m, capital):
    sz = size(m, capital)
    width = pick(m, sz, *SOFT_WIDTH)
    over = pick(m, sz, *SEMISOFT_OVER)
    if capital:
        top = CAP
        bottom = top - m.cap_bar * m.v(0.92, 0.86, light=0.96, black=0.8)
    else:
        bottom, top = latin.ascender_bar(m)
    shapes = [rect(0, 0, sz.stem, ASC)] + soft_bowl(m, sz, 0, width) + [rect(-over, bottom, sz.stem + over, top)]
    return spaced(m, shift(shapes, over), width + over, m.v(24, 16), sz.round)


def er_tick(m, capital):
    sz = size(m, capital)
    glyph = capitals.capital_p(m) if capital else lowercase.letter_p(m)
    stem_left, _ = accents.bounds(glyph.contours)
    points = [point for contour in glyph.contours for point in contour.points() if point[0] > stem_left + sz.stem + 1]
    left = stem_left + sz.stem
    right = max(x for x, _ in points)
    bottom = min(y for x, y in points if y > -1) if capital else -m.ov
    top = max(y for _, y in points)
    cx, cy = (left + right) / 2, (bottom + top) / 2
    rx, ry = (right - left) / 2, (top - bottom) / 2
    angle = math.radians(-TICK_LEAN)
    centre = (cx + rx * math.cos(angle) * 0.9, cy + ry * math.sin(angle) * 0.9)
    direction = (math.cos(angle), math.sin(angle))
    inside = sz.side / 2 + pick(m, sz, *TICK_IN)
    outside = sz.side / 2 + pick(m, sz, *TICK_OUT)
    start = (centre[0] - direction[0] * inside, centre[1] - direction[1] * inside)
    end = (centre[0] + direction[0] * outside, centre[1] + direction[1] * outside)
    tick = symbols.stick(start, end, sz.bar * m.v(*TICK_WEIGHT))
    return Glyph(glyph.contours + [tick], max(glyph.advance, end[0] + m.bearing(sz.diagonal)))


def te_tse(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    width = pick(m, sz, *PE_WIDTH)
    foot, _ = spur(m, sz)
    half = (m.v(*T_WIDTH) if capital else m.v(*TE_WIDTH)) / 2
    over = min(half - stem / 2, (width - 2 * stem) * TE_TSE_REACH)
    shapes = [rect(-over, h - bar, stem + over, h), combs(m, sz, width, [], True)]
    return spaced(m, shift(shapes, over), over + width + foot, pick(m, sz, *TE_TSE_SIDE), pick(m, sz, *SPUR_RIGHT), capital=capital)


def eared(m, capital):
    sz = size(m, capital)
    if capital:
        plain = latin.capital_schwa(m)
        contours = turn(plain.contours, plain.advance / 2, CAP / 2)
    else:
        plain = lowercase.letter_e(m)
        contours = plain.contours
    inner = contours[1]
    _, low, _, high = box(inner)
    if not all(len(segment) == 1 for segment in inner.segments):
        low, high = low - m.bar * m.v(*lowercase.E_BAR_WEIGHT), low
    ink_left, _ = accents.bounds(contours)
    stub = sz.stem * m.v(*EAR_WEIGHT)
    left = ink_left - stub - pick(m, sz, *EAR_GAP)
    join = ink_left + sz.side * EAR_JOIN
    rise = high + pick(m, sz, *EAR_RISE)
    ear = polygon([(join, low), (left, low), (left, rise), (left + stub, rise), (left + stub, high), (join, high)])
    shifted = shift(contours + [ear], -left + m.bearing(sz.straight))
    return Glyph(shifted, plain.advance - left + m.bearing(sz.straight) - ink_left)


def box(contour):
    xs = [point[0] for point in contour.corners()]
    ys = [point[1] for point in contour.corners()]
    return min(xs), min(ys), max(xs), max(ys)



def capital(draw):
    return lambda m: draw(m, True)


def small(draw):
    return lambda m: draw(m, False)


REUSED = {
    "А": (capitals.capital_a, "A"),
    "В": (capitals.capital_b, "B"),
    "Е": (capitals.capital_e, "E"),
    "К": (capitals.capital_k, "K"),
    "М": (capitals.capital_m, "M"),
    "Н": (capitals.capital_h, "H"),
    "О": (capitals.capital_o, "O"),
    "Р": (capitals.capital_p, "P"),
    "С": (capitals.capital_c, "C"),
    "Т": (capitals.capital_t, "T"),
    "Х": (capitals.capital_x, "X"),
    "Ѕ": (capitals.capital_s, "S"),
    "І": (capitals.capital_i, "I"),
    "Ј": (capitals.capital_j, "J"),
    "а": (lowercase.letter_a, "a"),
    "е": (lowercase.letter_e, "e"),
    "к": (latin.kgreenlandic, "kgreenlandic"),
    "о": (lowercase.letter_o, "o"),
    "р": (lowercase.letter_p, "p"),
    "с": (lowercase.letter_c, "c"),
    "у": (lowercase.letter_y, "y"),
    "х": (lowercase.letter_x, "x"),
    "ѕ": (lowercase.letter_s, "s"),
    "і": (lowercase.letter_i, "i"),
    "ј": (lowercase.letter_j, "j"),
    "ћ": (latin.hbar, "h"),
    "Ә": (latin.capital_schwa, "O"),
    "ә": (latin.schwa, "o"),
    "Ө": (greek.capital_theta, "O"),
    "Ү": (capitals.capital_y, "Y"),
    "һ": (lowercase.letter_h, "h"),
    "Ӏ": (capitals.capital_i, "I"),
    "ӏ": (capitals.capital_i, "I"),
}

DRAWN = {
    "Б": (capital(be), None),
    "Г": (capital(ge), None),
    "И": (capital(ii), "N"),
    "П": (capital(pe), "H"),
    "Ф": (capital(ef), None),
    "Ц": (capital(tse), None),
    "Ш": (capital(sha), "H"),
    "Щ": (capital(shcha), None),
    "Ъ": (capital(hard), None),
    "Ы": (capital(yeru), "H"),
    "Ь": (capital(soft), None),
    "Э": (capital(ereversed), "O"),
    "Ю": (capital(iu), "D"),
    "Є": (capital(ukrainian_ie), "C"),
    "Џ": (capital(dzhe), "H"),
    "Ґ": (capital(gheupturn), None),
    "Д": (capital(de), None),
    "Ж": (capital(zhe), None),
    "З": (capital(ze), None),
    "Л": (capital(el), None),
    "У": (u, None),
    "Ч": (capital(che), None),
    "Я": (capital(ya), None),
    "Ђ": (dje, None),
    "Ћ": (tshe, None),
    "Љ": (capital(lje), None),
    "Њ": (capital(nje), None),
    "№": (numero, None),
    "б": (small_be, None),
    "ж": (small(zhe), None),
    "з": (small(ze), None),
    "л": (small(el), None),
    "д": (small(de), None),
    "м": (small(em), None),
    "ч": (small(che), None),
    "я": (small(ya), None),
    "ђ": (small_dje, "h"),
    "љ": (small(lje), None),
    "њ": (small(nje), None),
    "в": (ve, None),
    "г": (small(ge), None),
    "и": (small(ii), "n"),
    "н": (en, "n"),
    "п": (small(pe), "n"),
    "т": (te, None),
    "ф": (small(ef), "o"),
    "ц": (small(tse), None),
    "ш": (small(sha), "n"),
    "щ": (small(shcha), None),
    "ъ": (small(hard), None),
    "ы": (small(yeru), "n"),
    "ь": (small(soft), None),
    "э": (small(ereversed), "o"),
    "ю": (small(iu), "p"),
    "є": (small(ukrainian_ie), "c"),
    "џ": (small(dzhe), "n"),
    "ґ": (small(gheupturn), None),
    "Ғ": (capital(ghayn), "Г"),
    "ғ": (small(ghayn), "г"),
    "Қ": (capital(ka_descender), None),
    "қ": (small(ka_descender), None),
    "Ң": (capital(en_descender), None),
    "ң": (small(en_descender), None),
    "ө": (barred_o, "o"),
    "Ұ": (capital(barred_straight_u), None),
    "ұ": (small(barred_straight_u), None),
    "ү": (straight_u, "v"),
    "Һ": (shha, None),
    "Җ": (capital(zhe_descender), None),
    "җ": (small(zhe_descender), None),
    "Ҳ": (capital(ha_descender), None),
    "ҳ": (small(ha_descender), None),
    "Ҷ": (capital(che_descender), None),
    "ҷ": (small(che_descender), None),
    "Ҫ": (centre_tail(capitals.capital_c, True), "C"),
    "ҫ": (centre_tail(lowercase.letter_c, False), "c"),
    "Ҙ": (centre_tail(capital(ze), True), None),
    "ҙ": (centre_tail(small(ze), False), None),
    "Ҡ": (capital(bashkir_ka), None),
    "ҡ": (small(bashkir_ka), None),
    "Ҝ": (capital(ka_stroke), "K"),
    "ҝ": (small(ka_stroke), "k"),
    "Ҹ": (capital(che_stroke), None),
    "ҹ": (small(che_stroke), None),
    "Ҭ": (capital(te_descender), None),
    "ҭ": (small(te_descender), None),
    "Ҥ": (capital(en_ghe), None),
    "ҥ": (small(en_ghe), None),
    "Ҕ": (capital(ghe_hook), None),
    "ҕ": (small(ghe_hook), None),
    "Ѣ": (capital(yat), None),
    "ѣ": (small(yat), None),
    "Ѫ": (capital(big_yus), None),
    "ѫ": (small(big_yus), None),
}
DRAWN.update(
    {
        "Ӄ": (capital(ka_hook), "K"),
        "ӄ": (small(ka_hook), "kgreenlandic"),
        "Ӈ": (capital(en_hook), None),
        "ӈ": (small(en_hook), None),
        "Ӽ": (capital(ha_hook), "X"),
        "ӽ": (small(ha_hook), "x"),
        "Ӿ": (capital(ha_stroke), "X"),
        "ӿ": (small(ha_stroke), "x"),
        "Ӻ": (lambda m: ghayn(m, True, ge_hook), None),
        "ӻ": (lambda m: ghayn(m, False, ge_hook), None),
        "Ҍ": (capital(semisoft), None),
        "ҍ": (small(semisoft), None),
        "Ҏ": (capital(er_tick), None),
        "ҏ": (small(er_tick), None),
        "Ҵ": (capital(te_tse), None),
        "ҵ": (small(te_tse), None),
        "Ҽ": (capital(eared), None),
        "ҽ": (small(eared), None),
        "Ӷ": (capital(ge_descender), None),
        "ӷ": (small(ge_descender), None),
        "Ҿ": (centre_tail(capital(eared), True), None),
        "ҿ": (centre_tail(small(eared), False), None),
    }
)

ACCENTED = {
    "Ё": (capitals.capital_e, "dieresis", True, "E"),
    "Ѓ": (capital(ge), "acute", True, "Г"),
    "Ї": (capitals.capital_i, "dieresis", True, "I"),
    "Ќ": (capitals.capital_k, "acute", True, "K"),
    "Ў": (u, "breve", True, "У"),
    "Й": (capital(ii), "breve", True, "N"),
    "й": (small(ii), "breve", False, "n"),
    "ё": (lowercase.letter_e, "dieresis", False, "e"),
    "ѓ": (small(ge), "acute", False, "г"),
    "ї": (accents.dotlessi, "dieresis", False, "i"),
    "ќ": (latin.kgreenlandic, "acute", False, "kgreenlandic"),
    "ў": (lowercase.letter_y, "breve", False, "y"),
    "Ӑ": (capitals.capital_a, "breve", True, "A"),
    "ӑ": (lowercase.letter_a, "breve", False, "a"),
    "Ӗ": (capitals.capital_e, "breve", True, "E"),
    "ӗ": (lowercase.letter_e, "breve", False, "e"),
    "Ӣ": (capital(ii), "macron", True, "N"),
    "ӣ": (small(ii), "macron", False, "n"),
    "Ӯ": (u, "macron", True, "У"),
    "ӯ": (lowercase.letter_y, "macron", False, "y"),
    "Ӱ": (u, "dieresis", True, "У"),
    "ӱ": (lowercase.letter_y, "dieresis", False, "y"),
    "Ӳ": (u, "hungarumlaut", True, "У"),
    "ӳ": (lowercase.letter_y, "hungarumlaut", False, "y"),
    "Ӥ": (capital(ii), "dieresis", True, "N"),
    "ӥ": (small(ii), "dieresis", False, "n"),
    "Ӝ": (capital(zhe), "dieresis", True, "Ж"),
    "ӝ": (small(zhe), "dieresis", False, "ж"),
    "Ӟ": (capital(ze), "dieresis", True, "З"),
    "ӟ": (small(ze), "dieresis", False, "з"),
    "Ӧ": (capitals.capital_o, "dieresis", True, "O"),
    "ӧ": (lowercase.letter_o, "dieresis", False, "o"),
    "Ӵ": (capital(che), "dieresis", True, "Ч"),
    "ӵ": (small(che), "dieresis", False, "ч"),
    "Ѐ": (capitals.capital_e, "grave", True, "E"),
    "ѐ": (lowercase.letter_e, "grave", False, "e"),
    "Ѝ": (capital(ii), "grave", True, "N"),
    "ѝ": (small(ii), "grave", False, "n"),
}
ACCENTED.update(
    {
        "Ӓ": (capitals.capital_a, "dieresis", True, "A"),
        "ӓ": (lowercase.letter_a, "dieresis", False, "a"),
        "Ӹ": (capital(yeru), "dieresis", True, "H"),
        "ӹ": (small(yeru), "dieresis", False, "n"),
        "Ӛ": (latin.capital_schwa, "dieresis", True, "O"),
        "ӛ": (latin.schwa, "dieresis", False, "o"),
        "Ӫ": (greek.capital_theta, "dieresis", True, "O"),
        "ӫ": (barred_o, "dieresis", False, "o"),
        "Ӂ": (capital(zhe), "breve", True, "Ж"),
        "ӂ": (small(zhe), "breve", False, "ж"),
        "Ӭ": (capital(ereversed), "dieresis", True, "O"),
        "ӭ": (small(ereversed), "dieresis", False, "o"),
    }
)

BULGARIAN = {
    "в": (round_ve, None),
    "г": (round_ge, None),
    "д": (lowercase.letter_g, "g"),
    "ж": (tall_zhe, "ж"),
    "з": (long_ze, None),
    "и": (lowercase.letter_u, "u"),
    "й": (accents.GLYPHS["ubreve"][1], None),
    "ѝ": (accents.GLYPHS["ugrave"][1], None),
    "к": (lowercase.letter_k, "k"),
    "л": (turned_vee, None),
    "п": (lowercase.letter_n, "n"),
    "т": (lowercase.letter_m, "m"),
    "ц": (tailed_u, None),
    "ш": (round_sha, "u"),
    "щ": (round_shcha, None),
    "ъ": (round_hard, None),
    "ь": (round_soft, None),
    "ю": (tall_iu, "b"),
}
SERBIAN = {"б": (serbian_be, None)}
LOCAL_FORMS = {"BGR": BULGARIAN, "SRB": SERBIAN}
LOCAL_LANGUAGES = {"BGR": "BGR", "SRB": "SRB", "MKD": "SRB"}
LOCAL_SETS = {"BGR": ("ss05", "Bulgarian forms"), "SRB": ("ss06", "Serbian and Macedonian forms")}
CYRILLIC_LANGUAGES = tuple(LOCAL_LANGUAGES)

def glyph_name(letter):
    return letter if letter.isascii() else f"uni{ord(letter):04X}"


def local_name(letter, forms):
    return f"{glyph_name(letter)}.locl{forms}"


GLYPHS = {}
KERN_LIKE = {}
LATIN_BARRED = {"Ɵ": (greek.capital_theta, "O"), "ɵ": (barred_o, "o")}
for letter, (draw, model) in {**REUSED, **DRAWN, **LATIN_BARRED}.items():
    GLYPHS[glyph_name(letter)] = (ord(letter), draw)
    if model:
        KERN_LIKE[glyph_name(letter)] = glyph_name(model)
for letter, (base, accent, upper, model) in ACCENTED.items():
    name = glyph_name(letter)
    GLYPHS[name] = (ord(letter), accents.accented_letter(name, base, accent, upper))
    KERN_LIKE[name] = glyph_name(model)
LOCAL = {}
for forms, letters in LOCAL_FORMS.items():
    for letter, (draw, model) in letters.items():
        name = local_name(letter, forms)
        LOCAL[name] = glyph_name(letter)
        GLYPHS[name] = (None, draw)
        if model:
            KERN_LIKE[name] = glyph_name(model)
LOCAL_MARKED = [local_name(letter, "BGR") for letter in "йѝ"]


SOFT_I = glyph_name("і")
SOFT_J = glyph_name("ј")
DOTTED_I = glyph_name("І")
DESCENDING = [glyph_name(letter) for letter in "ДЦЩдцщҚқҢңҖҗҲҳҶҷҬҭҔҕӇӈӺӻԒԓҴҵҾҿҊҋӶӷ"] + [local_name(letter, "BGR") for letter in "зцщ"]
HOOKED = ["j", glyph_name("ј")]
SMALLEST_KERN = 6


def drawn(name, master):
    from .glyphs import render

    return render(name, master)


@lru_cache(maxsize=None)
def accent_room(master):
    from . import features as kerning

    gap = master.v(*accents.ACCENT_CLEARANCE)
    measure = accents.cached_profile()
    found = {}
    for letter, (_, _, upper, _) in ACCENTED.items():
        marked = glyph_name(letter)
        floor = accents.mark_floor(upper)
        glyph = drawn(marked, master)
        for name in KERN_LIKE:
            other = drawn(name, master)
            for left, right, ink, mark, low, high in (
                (name, marked, other, glyph, floor - gap, floor),
                (marked, name, glyph, other, floor, floor - gap),
            ):
                needed = accents.closest_kern(ink, mark, gap, low, high, measure)
                if needed is not None:
                    value = kerning.pair_value(KERN_LIKE[left], KERN_LIKE[right], master)
                    found[(left, right)] = max(value, needed) - value
    return found


@lru_cache(maxsize=None)
def hook_room(master):
    from . import features as kerning

    gap = kerning.side_gap(drawn("o", master))
    hooked = sorted(kin()[0]["j"])
    found = {}
    for left in DESCENDING:
        value = max(max(0, kerning.needed_kern(drawn(left, master), drawn(right, master), gap)) for right in HOOKED)
        found.update({(left, right): value for right in hooked})
    return found


CLASSED = [glyph_name(letter) for letter in "ГҐЃгґѓУЎЖж"]
UNMAPPED = [glyph_name(letter) for letter, (_, model) in {**REUSED, **DRAWN}.items() if not model and glyph_name(letter) not in CLASSED]
UNMAPPED += [name for name in LOCAL if name not in KERN_LIKE]
EARED = [glyph_name(letter) for letter in "ҼҽҾҿ"]
UNMAPPED = [name for name in UNMAPPED if name not in EARED]
SLOPED = [glyph_name(letter) for letter in "ЖжУЯяҖҗҲҳ"] + [local_name("л", "BGR")]
NUMERO = glyph_name("№")
QUOTES = ["guillemotleft", "guillemotright", "guilsinglleft", "guilsinglright", "quotesinglbase", "quotedblbase"]
LOWEST_BAND = -80
BANDS = 340


def partners():
    from .glyphs import GLYPHS as everything
    from .glyphs import MARKS
    from .names import DIGITS

    names = list(GLYPHS) + [name for name in everything if len(name) == 1 and name.isalpha()]
    return names + list(DIGITS) + [name for name in list(MARKS) + QUOTES if name in everything]


def edge_arrays(names, master):
    from . import features as kerning

    left = numpy.full((len(names), BANDS), numpy.inf)
    right = numpy.full((len(names), BANDS), -numpy.inf)
    for index, name in enumerate(names):
        for band, x in kerning.edge_profile(name, master, False).items():
            left[index, band - LOWEST_BAND] = x
        for band, x in kerning.edge_profile(name, master, True).items():
            right[index, band - LOWEST_BAND] = x
    return left, right, numpy.array([drawn(name, master).advance for name in names])


def gap_matrix(master, names, firsts, seconds):
    left, right, advances = edge_arrays(names, master)
    return (left[seconds][None, :, :] + advances[firsts][:, None, None] - right[firsts][:, None, :]).min(axis=2)


def least_gap(master, left, right, designed):
    from . import features as kerning

    like = kerning.all_like()
    touching = 2 * master.bearing("cap_diagonal")
    sloped = [name in SLOPED or like.get(name, name) in kerning.DIAGONAL for name in (left, right)]
    lettered = [name in GLYPHS and name != NUMERO or kerning.letter_or_figure(name) for name in (left, right)]
    if all(sloped) or not any(lettered):
        return touching
    return min(master.bearing("cap_diagonal") / 2 + kerning.CLEAR_GAP, designed)


@lru_cache(maxsize=None)
def shortfalls(master):
    from . import features as kerning

    like = kerning.all_like()
    names = partners()
    places = {name: index for index, name in enumerate(names)}
    loose = [places[name] for name in UNMAPPED]
    everyone = list(range(len(names)))
    hooks = hook_room(master)
    found = {}
    for firsts, seconds in ((loose, everyone), (everyone, loose)):
        now, light, regular = (gap_matrix(each, names, firsts, seconds) for each in (master, LIGHT, REGULAR))
        for row, first in enumerate(firsts):
            for column, second in enumerate(seconds):
                gap = now[row, column]
                if not numpy.isfinite(gap):
                    continue
                left, right = names[first], names[second]
                if kerning.classed(left, right, like):
                    continue
                least = least_gap(master, left, right, min(light[row, column], regular[row, column]))
                found[(left, right)] = (least - gap - hooks.get((left, right), 0), least)
    return found


def kin():
    from . import features as kerning
    from .glyphs import GLYPHS as everything

    like = kerning.all_like()
    groups = {}
    for name in partners():
        groups.setdefault(like.get(name, name), {like.get(name, name)}).add(name)
    for name, model in like.items():
        if model in groups and name in everything:
            groups[model].add(name)
    return groups, like


@lru_cache(maxsize=None)
def floor_room(master):
    from . import features as kerning

    groups, like = kin()
    found = {}
    for (left, right), (shortfall, least) in shortfalls(master).items():
        key = (like.get(left, left), like.get(right, right))
        before = found.get(key, (-numpy.inf, least))
        found[key] = max(before, (shortfall, least))
    return {key: (value, kerning.worth_kerning(value, least)) for key, (value, least) in found.items()}


TWINS = {glyph_name(letter): glyph_name(model) for letter, model in zip("ҰұҬҭҚқҲҳҖҗҢңҶҷ", "ҮүТтКкХхЖжНнЧч")}
TWINS.update({glyph_name(letter): glyph_name(model) for letter, model in zip("ӇӈҊҋ", "НнЙй")})
TWINS.update({local_name(letter, "BGR"): glyph_name(model) for letter, model in zip("йѝцщв", "йѝuub")})


@lru_cache(maxsize=None)
def twin_kerns(master):
    from . import features as kerning

    like = kerning.all_like()
    names = partners()
    places = {name: index for index, name in enumerate(names)}
    twins = [places[name] for name in TWINS]
    models = [places[TWINS[name]] for name in TWINS]
    everyone = list(range(len(names)))
    hooks = hook_room(master)
    found = {}
    for twin_first in (True, False):
        own, model = (twins, everyone), (models, everyone)
        if not twin_first:
            own, model = (everyone, twins), (everyone, models)
        now, light, regular = (gap_matrix(each, names, *own) for each in (master, LIGHT, REGULAR))
        modelled = gap_matrix(master, names, *model)
        for row, first in enumerate(own[0]):
            for column, second in enumerate(own[1]):
                gap = now[row, column]
                if not numpy.isfinite(gap) or not numpy.isfinite(modelled[row, column]):
                    continue
                left, right = names[first], names[second]
                if (left, right) in hooks or kerning.classed(left, right, like):
                    continue
                model_left, model_right = names[model[0][row]], names[model[1][column]]
                kern = kerning.pair_value(like.get(model_left, model_left), like.get(model_right, model_right), master)
                if kern >= 0:
                    continue
                least = least_gap(master, left, right, min(light[row, column], regular[row, column]))
                value = min(0.0, max(modelled[row, column] + kern, least) - gap)
                key = (like.get(left, left), like.get(right, right))
                found[key] = max(found.get(key, -numpy.inf), value)
    return {key: value for key, value in found.items() if value < 0}


def room(master):
    groups, _ = kin()
    measured = {each: floor_room(each) for each in family(master)}
    kept = sorted(key for key in measured[master] if any(values.get(key, (0, False))[1] for values in measured.values()))
    hooks = hook_room(master)
    found = dict(hooks)
    for key in kept:
        value = max(0.0, measured[master][key][0])
        for left in sorted(groups.get(key[0], {key[0]})):
            for right in sorted(groups.get(key[1], {key[1]})):
                found[(left, right)] = found.get((left, right), 0) + value
    for key, value in twin_kerns(master).items():
        for left in sorted(groups.get(key[0], {key[0]})):
            for right in sorted(groups.get(key[1], {key[1]})):
                if (left, right) not in hooks and found.get((left, right), 0) <= 0:
                    found[(left, right)] = value
    return found


def kept_pairs(master, measure):
    found = {each: measure(each) for each in family(master)}
    needed = sorted({pair for values in found.values() for pair, value in values.items() if abs(round(value)) >= SMALLEST_KERN})
    return [f"        pos {left} {right} {round(found[master].get((left, right), 0))};" for left, right in needed]


def kern_feature(master):
    lines = ["feature kern {", "    lookup cyrillic_room {"]
    lines += kept_pairs(master, accent_room) + kept_pairs(master, room)
    return lines + ["    } cyrillic_room;", "} kern;"]


ANCHORED = ("top", "dots")
ANCHOR_SOURCES = {local_name("ю", "BGR"): glyph_name("ю")}


def local_lookup(forms):
    pairs = [f"        sub {LOCAL[name]} by {name};" for name in LOCAL if name.endswith(f".locl{forms}")]
    return [f"    lookup cyrillic_{forms.lower()} {{"] + pairs + [f"    }} cyrillic_{forms.lower()};"]


def local_feature():
    lines = ["feature locl {", "    script cyrl;"]
    written = set()
    for language, forms in LOCAL_LANGUAGES.items():
        lines.append(f"    language {language};")
        lines += [f"    lookup cyrillic_{forms.lower()};"] if forms in written else local_lookup(forms)
        written.add(forms)
    return lines + ["} locl;"]


def local_sets():
    lines = []
    for forms, (tag, label) in LOCAL_SETS.items():
        lines += [f"feature {tag} {{", "    featureNames {", f'        name "{label}";', "    };", f"    lookup cyrillic_{forms.lower()};", f"}} {tag};"]
    return lines


def local_marks(master):
    lines = ["feature mark {", "    lookup cyrillic_local_marks {"]
    for name in LOCAL:
        if name in LOCAL_MARKED:
            continue
        source = ANCHOR_SOURCES.get(name, name)
        glyph = GLYPHS[source][1](master)
        point = (accents.top_x(source, glyph, master, False), accents.top_height(glyph, False))
        listed = " ".join(f"{accents.anchor(point, master)} mark @mark_{kind}" for kind in ANCHORED)
        lines.append(f"        pos base {name} {listed};")
    return lines + ["    } cyrillic_local_marks;", "} mark;"]


def features(master):
    narrowable = [name for name in accents.TOP_MARKS if name + accents.NARROW in accents.mark_names()]
    cased = " ".join(name + accents.CASE for name in narrowable)
    narrowed = " ".join(name + accents.CASE + accents.NARROW for name in narrowable)
    return "\n".join(
        [
            "lookup cyrillic_dotless {",
            f"    sub {SOFT_I} by dotlessi;",
            f"    sub {SOFT_J} by dotlessj;",
            "} cyrillic_dotless;",
            "lookup cyrillic_case_narrow {",
            f"    sub [{cased}] by [{narrowed}];",
            "} cyrillic_case_narrow;",
            "feature ccmp {",
            "    lookup cyrillic_soft_dots {",
            f"        sub [{SOFT_I} {SOFT_J}]' lookup cyrillic_dotless @comb_top;",
            f"        sub [{SOFT_I} {SOFT_J}]' lookup cyrillic_dotless @comb_below @comb_top;",
            *[
                f"        sub [{SOFT_I} {SOFT_J}]' lookup cyrillic_dotless {'@comb_below ' * count}{greek.glyph_set(greek.ABOVE_MARKS)};"
                for count in range(3)
            ],
            "    } cyrillic_soft_dots;",
            "    lookup cyrillic_on_i {",
            "        sub [dotlessi dotlessj] @comb_narrowable' lookup comb_narrow;",
            "        sub [dotlessi dotlessj] @comb_below @comb_narrowable' lookup comb_narrow;",
            f"        sub {DOTTED_I} [{cased}]' lookup cyrillic_case_narrow;",
            f"        sub {DOTTED_I} @comb_below_case [{cased}]' lookup cyrillic_case_narrow;",
            "    } cyrillic_on_i;",
            "} ccmp;",
        ]
        + kern_feature(master)
        + local_feature()
        + local_sets()
        + local_marks(master)
    )


SERBIAN_BAR_GAP = (82, 88, 90, 94)
SERBIAN_BAR_WEIGHT = (0.92, 0.86, 0.96, 0.8)
SERBIAN_BAR_SHARE = 0.62
SERBIAN_GE_BAR = (176, 214, 160, 246)


def serbian_bar(m, left, right):
    bottom = XH + m.v(*SERBIAN_BAR_GAP)
    return rect(left, bottom, right, bottom + m.bar * m.v(*SERBIAN_BAR_WEIGHT))


def barred(draw):
    def build(m):
        glyph = draw(m)
        left, right = accents.bounds(glyph.contours)
        reach = (right - left) * SERBIAN_BAR_SHARE / 2
        middle = (left + right) / 2
        return Glyph(glyph.contours + [serbian_bar(m, middle - reach, middle + reach)], glyph.advance)

    return build


def serbian_ge(m):
    width = m.v(*SERBIAN_GE_BAR)
    stem = rect((width - m.stem) / 2, 0, (width + m.stem) / 2, XH)
    return spaced(m, [stem, serbian_bar(m, 0, width)], width, m.v(30, 22), m.v(30, 22), capital=False)


def italic_de(m):
    glyph = accents.eth(m)
    return Glyph(glyph.contours[:-1], glyph.advance)


def italic_tse(m):
    sz = size(m, False)
    (bowl, post), width, left, _ = letter_parts(lowercase.italic_u_upright_post, m)
    return tail_spaced(m, sz, [bowl, tailed(m, sz, post)], width, left)


ITALIC_FORMS = {"д": italic_de, "и": lowercase.letter_u, "п": lowercase.letter_n, "т": lowercase.letter_m, "ц": italic_tse, "ш": round_sha, "щ": round_shcha}
ITALIC_MARKED = "йѝӣӥ"
SERBIAN_ITALIC = {"г": serbian_ge, "д": lowercase.letter_g, "п": barred(lowercase.letter_n), "т": barred(lowercase.letter_m)}
for letter, form in ITALIC_FORMS.items():
    code, draw = GLYPHS[glyph_name(letter)]
    GLYPHS[glyph_name(letter)] = (code, ItalicForm(draw, form))
for letter in ITALIC_MARKED:
    base, accent, upper, _ = ACCENTED[letter]
    GLYPHS[glyph_name(letter)] = (ord(letter), accents.accented_letter(glyph_name(letter), ItalicForm(base, lowercase.letter_u), accent, upper))
for letter, form in SERBIAN_ITALIC.items():
    name = local_name(letter, "SRB")
    LOCAL[name] = glyph_name(letter)
    GLYPHS[name] = (None, ItalicForm(GLYPHS[glyph_name(letter)][1], form))
    TWINS[name] = glyph_name(letter)
    UNMAPPED.append(name)
DESCENDING.append(local_name("д", "SRB"))
SERBIAN_ITALIC_MARKED = {"ѓ": "г"}
for letter, plain in SERBIAN_ITALIC_MARKED.items():
    base, accent, upper, _ = ACCENTED[letter]
    name = local_name(letter, "SRB")
    LOCAL[name] = glyph_name(letter)
    GLYPHS[name] = (None, accents.accented_letter(name, ItalicForm(base, SERBIAN_ITALIC[plain]), accent, upper))
    TWINS[name] = glyph_name(letter)
    UNMAPPED.append(name)
    LOCAL_MARKED.append(name)
GLYPHS[local_name("ц", "BGR")] = (None, ItalicForm(GLYPHS[local_name("ц", "BGR")][1], italic_tse))


KOMI_HOOK_SCALE = 1.12
KOMI_SIDE = (10, 6, 12, 4)
TAIL_REACH = (88, 88, 88, 90)


def hook_size(m, sz):
    scale = KOMI_HOOK_SCALE if sz.capital else 1.0
    return sz.stem + m.v(96, 102) * scale, lowercase.hook_inner(m) * scale


def foot_hook(m, sz, x0, top):
    run, inner = hook_size(m, sz)
    return place(hook(m, sz.stem, sz.thin, top, run, inner), x0, 0), run


def tail_size(m, sz):
    scale = KOMI_HOOK_SCALE if sz.capital else 1.0
    reach = m.v(*TAIL_REACH) * scale
    return sz.stem + reach, (reach - lowercase.J_TIP) / HOOK_SPREAD


def tail_hook(m, sz, x0, top):
    run, inner = tail_size(m, sz)
    depth = -pick(m, sz, *SPUR_DEPTH)
    return place(hook(m, sz.stem, sz.thin, top - depth, run, inner), x0 + sz.stem, depth, fx=-1)


def hooked_en(tail):
    def build(m, capital):
        sz = size(m, capital)
        h, stem, bar = sz.height, sz.stem, sz.bar
        width = m.v(*H_WIDTH) if capital else m.v(*EN_WIDTH)
        centre = capitals.WAIST if capital else h * 0.5
        crossbar = rect(stem * 0.5, centre - bar / 2, width - stem * 0.5, centre + bar / 2)
        if tail:
            return spaced(m, [rect(0, 0, stem, h), tail_hook(m, sz, width - stem, h), crossbar], width, sz.straight, sz.straight)
        right, run = foot_hook(m, sz, width - stem, h)
        return spaced(m, [rect(0, 0, stem, h), right, crossbar], width - stem + run, sz.straight, m.v(*KOMI_SIDE))

    return build


def em_with_tail(m, capital):
    sz = size(m, capital)
    stem = sz.stem
    width = pick(m, sz, *EM_WIDTH)
    thickness = sz.diag * m.v(0.94, 0.88, black=0.84)
    inset = 0
    for _ in range(8):
        middle, stroke = vee(width - 2 * inset, thickness * m.v(1.15, 1.0, black=0.8), sz.height, thickness)
        inset = max(0, stem - stroke + m.v(2, 3))
    shapes = [rect(0, 0, stem, sz.height), tail_hook(m, sz, width - stem, sz.height), shift([middle], inset)[0]]
    return spaced(m, shapes, width, sz.straight, sz.straight)


def hooked_el(tail, deep=False):
    def build(m, capital):
        sz = size(m, capital)
        h, stem, bar, thin = sz.height, sz.stem, sz.bar, sz.thin
        width = pick(m, sz, *EL_WIDTH)
        left, right, inner, inner_height, foot, outer = leg_curves(m, sz, 0)
        x0 = width - stem
        path = Path((right, h - bar))
        path.to(outer[0])
        path.bez(outer)
        path.to((0, 0))
        path.to((0, foot))
        path.to((left - inner, foot))
        path.arc((left, foot + inner_height), "h", m.k_in + 0.02)
        path.to((left, h))
        path.to((width, h))
        if deep:
            latin.descend(path, m, width, stem, DESC, pick(m, sz, *HOOK_THIN), pick(m, sz, *HOOK_REACH))
            advance = width
        elif tail:
            run, reach = tail_size(m, sz)
            depth = -pick(m, sz, *SPUR_DEPTH)
            bend = reach * HOOK_SPREAD
            path.to((width, depth + thin + reach * 1.15 * 1.25))
            path.arc((width - stem - bend, depth), "v", m.k_out - 0.02)
            path.to((width - run, depth))
            path.to((width - run, depth + thin))
            path.to((x0 - reach, depth + thin))
            path.arc((x0, depth + thin + reach * 1.15), "h", m.k_in + 0.02)
            advance = width
        else:
            run, reach = hook_size(m, sz)
            path.to((width, thin + reach * 1.15))
            path.arc((width + reach, thin), "v", m.k_in + 0.02)
            path.to((x0 + run, thin))
            path.to((x0 + run, 0))
            path.to((x0 + stem + reach * HOOK_SPREAD, 0))
            path.arc((x0, thin + reach * 1.15 * 1.25), "h", m.k_out - 0.02)
            advance = x0 + run
        path.to((x0, h - bar))
        right_side = sz.straight if tail or deep else m.v(*KOMI_SIDE)
        return spaced(m, [path.close()], advance, m.v(18, 12, light=20, black=8), right_side)

    return build


def komi_tje(m, capital):
    sz = size(m, capital)
    h, stem, bar = sz.height, sz.stem, sz.bar
    width = m.v(516, 574) if capital else m.v(*TE_WIDTH)
    post, run = foot_hook(m, sz, (width - stem) / 2, h - bar * 0.5)
    side = m.v(28, 20) if capital else m.v(18, 12)
    return spaced(m, [rect(0, h - bar, width, h), post], max(width, (width - stem) / 2 + run), side, side, capital=capital)


def komi_de(m):
    glyph = capitals.capital_p(m)
    return Glyph(turn(glyph.contours, glyph.advance / 2, CAP / 2), glyph.advance)


def foot(m, sz, x0):
    run, inner = hook_size(m, sz)
    stem, thin = sz.stem, sz.thin
    rise = thin + inner * 1.15
    path = Path((x0 + stem, 0))
    path.to((x0 + stem * 0.5, thin * 0.5))
    path.to((x0 + stem * 0.5, rise))
    path.to((x0 + stem, rise))
    path.arc((x0 + stem + inner, thin), "v", m.k_in + 0.02)
    path.to((x0 + run, thin))
    path.to((x0 + run, 0))
    return path.close(), run


def komi_dje(m):
    glyph = komi_de(m)
    sz = size(m, True)
    stem = glyph.contours[0]
    x0 = min(point[0] for point in stem.corners())
    tail, run = foot(m, sz, x0)
    return Glyph(glyph.contours + [tail], glyph.advance + run - sz.stem)


def small_komi_dje(m):
    sz = size(m, False)
    width = m.v(472, 540, black=596)
    tail, run = foot(m, sz, width - sz.stem)
    shapes = [rect(width - sz.stem, 0, width, ASC), tail] + mirror(lowercase.bowl(m, width), width / 2)
    return spaced(m, shapes, width - sz.stem + run, "round", m.v(*KOMI_SIDE))


KOMI = {
    0x500: komi_de,
    0x501: lowercase.letter_d,
    0x502: komi_dje,
    0x503: small_komi_dje,
    0x508: capital(hooked_el(False)),
    0x509: small(hooked_el(False)),
    0x50A: capital(hooked_en(False)),
    0x50B: small(hooked_en(False)),
    0x50E: capital(komi_tje),
    0x50F: small(komi_tje),
    0x4C5: capital(hooked_el(True)),
    0x4C6: small(hooked_el(True)),
    0x4C9: capital(hooked_en(True)),
    0x4CA: small(hooked_en(True)),
    0x4CD: capital(em_with_tail),
    0x4CE: small(em_with_tail),
}
KHANTY_HOOKED = {0x512: capital(hooked_el(True, deep=True)), 0x513: small(hooked_el(True, deep=True))}
KOMI.update(KHANTY_HOOKED)
for code, draw in KOMI.items():
    GLYPHS[f"uni{code:04X}"] = (code, draw)
UNMAPPED += [f"uni{code:04X}" for code in KHANTY_HOOKED]


from .alternates import small_cap as small_cap_of
from .alternates import small_cap_drawing

SMALL_CAP_CODES = [code for code in range(0x410, 0x430) if code != 0x419]
SMALL_CAP_MARKED = {
    "uni0401": ("uni0415.sc", "dieresiscomb"),
    "uni0451": ("uni0415.sc", "dieresiscomb"),
    "uni0419": ("uni0418.sc", "brevecomb"),
    "uni0439": ("uni0418.sc", "brevecomb"),
}
MARK_TWINS = {f"uni{code:04X}.sc": f"uni{code + 0x20:04X}" for code in SMALL_CAP_CODES}
for code in SMALL_CAP_CODES:
    GLYPHS[f"uni{code:04X}.sc"] = (None, small_cap_of(f"uni{code:04X}"))


STROKE_HEIGHT = (552, 556, 550, 560)
STROKE_OVER = (48, 52, 46, 54)


def ka_stroke_bar(capital):
    def build(m):
        glyph = capitals.capital_k(m) if capital else lowercase.letter_k(m)
        stem = m.cap_stem if capital else m.stem
        left = min(point[0] for contour in glyph.contours for point in contour.points())
        over = m.v(*STROKE_OVER)
        if capital:
            centre = m.v(*STROKE_HEIGHT)
            half = m.cap_bar * m.v(0.92, 0.86, light=0.96, black=0.8) / 2
            bottom, top = centre - half, centre + half
        else:
            bottom, top = latin.ascender_bar(m)
        bar = rect(left - over, bottom, left + stem + over, top)
        return Glyph(shift(glyph.contours + [bar], over * 0.5), glyph.advance + over)

    return build


ABKHAZ = {
    0x49E: ka_stroke_bar(True),
    0x49F: ka_stroke_bar(False),
    0x4E0: latin.GLYPHS["Ezh"][1],
    0x4E1: latin.GLYPHS["ezh"][1],
}
for code, draw in ABKHAZ.items():
    GLYPHS[f"uni{code:04X}"] = (code, draw)


SMALL_CAP_SHARED = {"Ѕ": "S", "І": "I", "Ј": "J", "Ү": "Y", "Ӏ": "I", "Ә": "Schwa", "Ө": "Theta", "Ӡ": "Ezh", "Ɵ": "Theta"}
SMALL_CAP_DRAWN = "ЄЏҐЂЋЉЊҒҚҢҰҺҖҲҶҪҘҠҜҸҬҤҔѢѪԀԂԈԊԎӅӉӍҞԤԦԮӃӇӼӾӺԒҌҎҴҼҾӶ"
COMBINING = {chr(code): name for name, (code, _) in accents.TOP_MARKS.items()}


def small_cap_name(letter):
    return f"{SMALL_CAP_SHARED.get(letter, glyph_name(letter))}.sc"


for letter in SMALL_CAP_DRAWN:
    GLYPHS[small_cap_name(letter)] = (None, small_cap_of(glyph_name(letter)))
SMALL_CAP_UPPER = {glyph_name(letter): small_cap_name(letter) for letter in SMALL_CAP_SHARED}
SMALL_CAP_LOWER = {glyph_name(letter.lower()): small_cap_name(letter) for letter in SMALL_CAP_SHARED}
for letter in ACCENTED:
    base, mark = unicodedata.normalize("NFD", letter)
    SMALL_CAP_MARKED[glyph_name(letter)] = (small_cap_name(base.upper()), COMBINING[mark])


TAILED_II_SMALL_CAP = glyph_name("И") + ".tail.sc"
SHORT_II_TAILED = {"Ҋ": True, "ҋ": False}
for letter, upper in SHORT_II_TAILED.items():
    base = capital(ii_tail) if upper else ItalicForm(small(ii_tail), italic_tse)
    GLYPHS[glyph_name(letter)] = (ord(letter), accents.accented_letter(glyph_name(letter), base, "breve", upper))
    SMALL_CAP_MARKED[glyph_name(letter)] = (TAILED_II_SMALL_CAP, "brevecomb")
GLYPHS[TAILED_II_SMALL_CAP] = (None, small_cap_drawing(capital(ii_tail)))
MARK_TWINS[TAILED_II_SMALL_CAP] = glyph_name("и")
UNMAPPED += [glyph_name(letter) for letter in SHORT_II_TAILED]
