import math
import unicodedata
from dataclasses import dataclass, replace
from functools import lru_cache

import numpy

from . import capitals, lowercase, parts
from .geometry import Contour, Path, across, bend, closed_segments, flip, head, quarter, split
from .masters import ASC, CAP, DESC, OV, TOP_OV, XH, family
from .names import LETTERS
from .oblique import ORIGIN, Overlaid, finished, ink_bounds, slanted
from .parts import Glyph, band, band_width, lobe, spaced, vee
from .shapes import Node, aim, mirror, place, polygon, rect, ribbon, ring, shift, turn

DOWN = (0, -1)
UP = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

CROTCH = (108, 108, None, 128)
CROTCH_PULL = 0.6
OE_CROTCH = (432, 418, None, 448)
OE_INNER = (396, 372)
AE_BOWL_WIDTH = (420, 522, None, 590)
AE_EYE_WIDTH = (424, 492, None, 556)
OE_BOWL_WIDTH = (456, 516, None, 566)
OE_EYE_WIDTH = (436, 500, None, 558)
A_PEAK = 0.53
AE_LOW_CROTCH = (126, 150, None, 100)
AE_INNER_LOW = (146, 184, None, 152)
AE_BELLY_DROP = (64, 70)
AE_BELLY_CORNER = (48, 40)
AE_BELLY_HEADING = 140
CROTCH_FILLET = (40, 48, None, 18)
FILLET_PULL = 0.75
A_TERMINAL = (406, 390, None, 412)
A_BELLY_TOP = (322, 328, None, 342)
A_BELLY_FLAT = (70, 90, 54, 72)
A_BELLY_FLOOR = (0.95, 0.92, None, 0.6)
A_BELLY_SIDE = (1.0, 1.0, None, 0.78)
A_THICK = (76, 102, 56, 120)
E_TAIL = (130, 150, None, 124)
E_BAR_BOTTOM = (240, 214, None, 216)
OVERHANGS = ("T", "Ge", "V", "W", "Y", "F", "P", "f")
RISERS = ("b", "d", "f", "h", "i", "k", "l", "t")
PROFILE_BAND = 4
SMALLEST_KERN = 6
ACCENT_CLEARANCE = (72, 64, 75, 58)
LIGATURE_LEFT = {"AE": "A", "OE": "O"}
SLASH_INSET = 0.1
SLASH_WEIGHT = (0.84, 0.72, None, 0.56)
CAP_SLASH_WEIGHT = (0.86, 0.76, None, 0.64)
SLASHED_SIDE = (1.0, 0.9, 1.0, 0.86)
SLASHED_FLAT = (1.0, 0.94, 1.0, 0.9)
ROUND_TOPS = "aeoO"
ROUND_LIFT = (14, 0, None, 0)
ASCENDED = "bdfhklt"
ASCENDER_DOT_LIFT = (30, 30, 30, 30)
CAP_ROUND_LIFT = (14, 8)
SLIM_LIFT = (0, 0, 8, 14)
SLIM_SHARE = 0.96
DOTTED_MARK_MARGIN = 4
SLIM_SLANT_LIFT = (90, 0, 0, 0)
SLIM_CAP_LIFT = (-4, 8, 0, 0)
AE_POST = (404, 520, None, 604)
AE_WAIST = (0.5, 0.52)
AE_LEG_REACH = (0.4, 0.05, None, 0.02)
AE_SLAB_DROP = (24, 30)
SHARED_EDGE_GAP = 6
CEDILLA_DEPTH = (184, 192, None, 204)
CEDILLA_FLAT = (50, 66, 34, 72)
CEDILLA_TAIL = (47, 62, 32, 68)
CEDILLA_WEIGHT = (52, 66, 36, 72)
CEDILLA_CLEAR = 8
ETH_WIDTH = (468, 530, None, 596)
ETH_DROP = (22, 26)
ETH_ROOT_AT = 0.9
ETH_ROOT_WEIGHT = 0.8
ETH_LEAN = (130, 132)
ETH_TIP_X = (0.43, 0.42)
ETH_TIP = (68, 104, 46, 136)
ETH_SHOULDER_X = (0.88, 0.88, None, 0.93)
ETH_SHOULDER_Y = (494, 490)
ETH_RISE = (114, 116, 113, 112)
ETH_BAR_Y = (614, 622, None, 638)
ETH_BAR_REACH = (52, 56, 62, 58)
ETH_BAR_ANGLE = (8, 8)
ETH_BAR_WEIGHT = (0.84, 0.72, None, 0.62)
ESZETT_GAP = (104, 92, 100, 92)
ESZETT_BELLY = 0.6
ESZETT_EASE = (0.7, 0.2, 0.8, 0.15)
ESZETT_FOOT = (140, 152, None, 184)
ESZETT_END = (78, 102, 54, 96)
ESZETT_LEAN = (116, 114, None, 110)
CEDILLA_NUDGE = (6, 8)
CEDILLA_NECK = (60, 90, 40, 116)
CEDILLA_SWEEP = (52, 56, 44, 38)
SMALL_FLOOR = (66, 72, 70, 76)
SMALL_HEIGHT = (144, 152)
SMALL_HAT_HEIGHT = (146, 160)
SMALL_LOOP = (184, 206, 176, 240)
SMALL_LOOP_SIDE = (42, 58, 32, 54)
SMALL_LOOP_FLOOR = (80, 80, 66, 80)
TALL_FLOOR = (64, 68, 62, 72)
TALL_HEIGHT = (116, 122)
TALL_HAT_HEIGHT = (130, 148, 124, 160)
TALL_LOOP = (186, 198, 176, 212)
TALL_LOOP_SIDE = (40, 46, 30, 54)
TALL_LOOP_FLAT = (40, 42, 30, 52)
TALL_LOOP_FLOOR = (76, 88, 48, 62)
TILDE_RISE = (0.46, 0.6, 0.447, 0.7)
CAP_TILDE_RISE = (0.56, 0.68, 0.447, 0.7)
CARON_LIFT = (12, 10, 10, 10)
DOUBLE_STROKE = 0.8
DOUBLE_RUN = 0.62
DOUBLE_PITCH = (1.9, 1.8, None, 1.74)
OGONEK_NECK = (64, 98, 44, 140)
OGONEK_SIDE = (62, 96, 42, 138)
OGONEK_FLAT = (50, 72, 34, 104)
OGONEK_DEPTH = (176, 186, 170, 200)
OGONEK_LEAN = -125
OGONEK_REACH = (122, 146, 104, 182)
OGONEK_BELLY = (90, 92, 88, 90)
OGONEK_TURN = (40, 40, 38, 30)
OGONEK_TAIL = (34, 40)
OGONEK_TAPER = 0.84
STACK_GAP = (44, 50, 40, 54)
CAP_STACK_GAP = (30, 32, 28, 32)
STACK_HEIGHT = (0.8, 0.78, 0.82, 0.76)
STACK_HAT = (0.82, 0.82, 0.84, 0.8)
STACK_HAT_STROKE = (0.94, 0.88, 0.96, 0.8)
STACK_RUN = (0.7, 0.64, 0.74, 0.6)
STACK_STROKE = (0.92, 0.88, 0.96, 0.82)
STACK_LOOP = (0.8, 0.78, 0.82, 0.78)
STACK_DOT = (0.88, 0.84, 0.92, 0.76)
CAP_HOOK = (0.94, 0.9, 0.96, 0.84)
STACK_HOOK = (0.88, 0.8, 0.9, 0.74)
STACK_TILDE = (0.92, 0.76, 0.96, 0.68)
PRESS_DROP = (0, 10, 0, 16)
PRESS_HEIGHT = (0.94, 0.84, 0.96, 0.74)
PRESS_GAP = 0.7
HAT_PRESS_HEIGHT = (0.98, 0.93, 1.0, 0.85)
HAT_TONE_HEIGHT = (1.0, 0.72, 1.0, 0.64)
STACK_PRESS_GAP = (0.85, 0.7, 0.9, 0.7)
PRESSED_ACCENTS = ("hookabove", "tilde")
CARON_TICK = (74, 116, 52, 150)
CARON_FALL = (104, 92, 108, 84)
CARON_GAP = (40, 36, 42, 32)
CARON_ITALIC_GAP = (6, 10, 5, 18)
CARON_BASES = ("d", "l", "t", "L")
CARON_ALT = "caroncomb.alt"
CARON_SHORT = "caroncomb.alt.short"
SHORT_CARON_BASES = ("t",)
WEDGE_TOP = (68, 100, 50, 128)
WEDGE_DROP = (190, 194, 186, 198)
WEDGE_FOOT = (0.5, 0.5, 0.54, 0.5)
WEDGE_LEAN = 0.09
WEDGE_SHOULDER = 0.4
WEDGE_BELLY = 0.76
WEDGE_HEEL = 0.28
SHORT_WEDGE_TOP = 1.0
SHORT_WEDGE_DROP = 0.8
CARON_FOOT = (44, 52, 40, 56)
OGONEK_INSET = (6, 10)
CARON_SPACE = 0.6
STEM_TOPS = {"J": CAP * 0.7, "L": CAP * 0.7, "dotlessj": XH / 2, "Fhook": 0}
MARK_BASES = ("dottedcircle",)
CIRCLE_DOTS = 12
CIRCLE_RADIUS = (226, 230, 224, 234)
COMMA_SIDE = 0.82
COMMA_FALL = 0.8
COMMA_GAP = (44, 40, 46, 34)
LATVIAN_COMMAS = ("G", "K", "L", "N", "R", "k", "l", "n", "r")
BELOW_KINDS = ("bottom", "ogonek", "comma", "dotbelow", "horn")
DOT_BELOW_GAP = (58, 52, 62, 46)
DOT_BELOW_LEVELS = 8
LINE_BELOW_LENGTH = (140, 156, 134, 172)
LINE_BELOW_WEIGHT = 0.84
MACRON_BELOW_SPAN = 0.98
TILDE_BELOW_DEPTH = 0.8
MACRON_BELOW_WEIGHT = (0.9, 0.86, 0.92, 0.82)
HORN_HEIGHT = 0.84
HORN_INSET = (16, 24)
BESIDE_GAP = (14, 16, None, 20)
SIDE_MARK_MARGIN = (4, 6, None, 4)
BESIDE_RISE = 0.5
BESIDE_HEIGHT = (0.86, 0.86, None, 0.86)
BESIDE_RUN = 0.66
BESIDE_STROKE = (1.0, 1.0, None, 1.0)
BREVE_SIDE = (0.86, 0.76, None, 0.78)
BREVE_FLAT = (0.76, 0.64, None, 0.62)
BREVE_DEPTH = 1.08
TILDE_WEIGHT = (0.46, 0.4, None, 0.41)
HOOK_RUN = 1.0
HOOK_SPREAD = (0.9, 0.9, None, 0.6)
HOOK_COUNTER = (0.5, 0.36, None, 0.36)
HOOK_FLOAT = (0, 0, None, 10)
HOOK_LIFT = (0.6, 0.6, None, 0.4)
HOOK_EDGE = (0.92, 0.88, None, 0.6)
HOOK_FLAT = (0.76, 0.7, None, 0.56)
HOOK_END = (0.82, 0.76, None, 0.54)
HOOK_STEM = (0.86, 0.82, None, 0.74)
HOOK_LEAN = (64, 68, None, 72)
HOOK_DROP = (236, 236, None, 232)
HOOK_TERMINAL = 0.82
HOOK_SHOULDER = (0.76, 0.76, None, 0.78)
HOOK_SWEEP = 0.9
HOOK_GAP = 9
HOOK_NECK_ROOM = 0.12
KRESKA_RUN = 0.56
KRESKA_CAP_RUN = 0.78
KRESKA_HEIGHT = 0.94
KRESKA = ".loclPLK"
KRESKA_BASES = ("c", "n", "o", "s", "z", "C", "N", "O", "S", "Z")
LANGUAGES = ("PLK",)
LANGUAGES += ("ROM", "MOL", "LTH", "NLD")
COMMA_LANGUAGES = ("ROM", "MOL")
LITHUANIAN_ACCENTS = ("gravecomb", "acutecomb", "tildecomb")
CEDILLA_PAIRS = {"Scedilla": "Scommaaccent", "scedilla": "scommaaccent", "Tcedilla": "Tcommaaccent", "tcedilla": "tcommaaccent"}


@dataclass(frozen=True)
class Tier:
    floor: float
    stroke: float
    height: float
    run: float
    span: float
    hat_span: float
    hat_height: float
    hat_stroke: float
    dot: float
    dot_floor: float
    pitch: float
    loop: float
    loop_side: float
    loop_flat: float
    loop_floor: float
    tilde_rise: float
    hat_lift: float = 0
    stacked: bool = False


def small(m):
    return Tier(
        floor=XH + m.v(*SMALL_FLOOR),
        stroke=m.v(70, 112, light=46, black=148),
        height=m.v(*SMALL_HEIGHT),
        run=m.v(112, 124),
        span=m.v(252, 296),
        hat_span=m.v(250, 322),
        hat_height=m.v(*SMALL_HAT_HEIGHT),
        hat_stroke=m.v(68, 100, light=46, black=130),
        dot=m.v(92, 150, light=62, black=186),
        dot_floor=XH + m.v(82, 76, light=90, black=80),
        pitch=m.v(186, 236, light=168, black=256),
        loop=m.v(*SMALL_LOOP),
        loop_side=m.v(*SMALL_LOOP_SIDE),
        loop_flat=m.v(44, 56, light=32, black=48),
        loop_floor=XH + m.v(*SMALL_LOOP_FLOOR),
        tilde_rise=m.v(*TILDE_RISE),
    )


def tall(m):
    return Tier(
        floor=CAP + m.v(*TALL_FLOOR),
        stroke=m.v(72, 114, light=48, black=150),
        height=m.v(*TALL_HEIGHT),
        run=m.v(104, 116),
        span=m.v(286, 328),
        hat_span=m.v(266, 330, black=372),
        hat_height=m.v(*TALL_HAT_HEIGHT),
        hat_stroke=m.v(66, 92, light=44, black=112),
        dot=m.v(88, 136, light=60, black=172),
        dot_floor=CAP + m.v(60, 66, light=64, black=80),
        pitch=m.v(196, 256, light=176, black=278),
        loop=m.v(*TALL_LOOP),
        loop_side=m.v(*TALL_LOOP_SIDE),
        loop_flat=m.v(*TALL_LOOP_FLAT),
        loop_floor=CAP + m.v(*TALL_LOOP_FLOOR),
        tilde_rise=m.v(*CAP_TILDE_RISE),
    )


def bounds(contours):
    xs = [point[0] for contour in contours for point in contour.points()]
    return min(xs), max(xs)


def centred(contours):
    left, right = bounds(contours)
    return shift(contours, -(left + right) / 2)


def acute(m, tier):
    top = tier.floor + tier.height
    direction = (tier.run, tier.height)
    foot = across(direction, tier.stroke * 0.9)
    crown = across(direction, tier.stroke * 1.08)
    half = tier.run / 2
    shape = polygon(
        [
            (-half - foot / 2, tier.floor),
            (-half + foot / 2, tier.floor),
            (half + crown / 2, top),
            (half - crown / 2, top),
        ]
    )
    return centred([shape])


def kreska(m, tier):
    capital = tier.floor > CAP
    steeper = replace(tier, run=tier.run * (KRESKA_CAP_RUN if capital else KRESKA_RUN), height=tier.height * (1 if capital else KRESKA_HEIGHT))
    shape = acute(m, steeper)
    return shift(shape, bounds(acute(m, tier))[1] - bounds(shape)[1])


def grave(m, tier):
    return mirror(acute(m, tier), 0)


def chevron(tier):
    shape, _ = vee(tier.hat_span, tier.hat_stroke * 1.04, tier.hat_height, tier.hat_stroke)
    return shape


def circumflex(m, tier):
    return [place(chevron(tier), -tier.hat_span / 2, tier.floor + tier.hat_lift + tier.hat_height, fy=-1)]


def caron(m, tier):
    return [place(chevron(tier), -tier.hat_span / 2, tier.floor + tier.hat_lift + m.v(*CARON_LIFT))]


def dieresis(m, tier):
    side = tier.dot
    step = tier.pitch / 2
    bottom = tier.dot_floor
    return [
        rect(-step - side / 2, bottom, -step + side / 2, bottom + side),
        rect(step - side / 2, bottom, step + side / 2, bottom + side),
    ]


def dotaccent(m, tier):
    side = tier.dot
    return [rect(-side / 2, tier.dot_floor, side / 2, tier.dot_floor + side)]


def ring_mark(m, tier):
    size = tier.loop
    bottom = tier.loop_floor
    return ring(-size / 2, bottom, size / 2, bottom + size, tier.loop_side, tier.loop_flat, m.k_out, m.k_in)


def tilde(m, tier):
    width = tier.span * 1.04
    flat = m.v(*STACK_TILDE) if tier.stacked and tier.floor > CAP else 1.0
    lift = tier.height * m.v(0.2, 0.25)
    half = tier.stroke * m.v(*TILDE_WEIGHT)
    centre = tier.floor + tier.height * tier.tilde_rise - (lift + half) * (1 - flat)
    lift, half = lift * flat, half * flat
    step = width / 4

    def edge(y):
        return [
            ((0, y), (0.32613 * step, y + 0.51229 * lift), (0.63809 * step, y + lift), (step, y + lift)),
            ((step, y + lift), (1.36191 * step, y + lift), (1.67387 * step, y + 0.51229 * lift), (2 * step, y)),
            ((2 * step, y), (2.32613 * step, y - 0.51229 * lift), (2.63809 * step, y - lift), (3 * step, y - lift)),
            ((3 * step, y - lift), (3.36191 * step, y - lift), (3.67387 * step, y - 0.51229 * lift), (4 * step, y)),
        ]

    path = Path((0, centre + half))
    for bezier in edge(centre + half):
        path.bez(bezier)
    path.to((width, centre - half))
    for bezier in reversed(edge(centre - half)):
        path.bez(flip(bezier))
    return shift([path.close()], -width / 2)


def macron(m, tier):
    width = tier.span * 0.98
    thickness = tier.stroke * m.v(0.9, 0.86)
    middle = tier.floor + tier.height * 0.44
    return [rect(-width / 2, middle - thickness / 2, width / 2, middle + thickness / 2)]


def breve(m, tier):
    width = tier.span * m.v(1.0, 1.08)
    side = tier.stroke * m.v(*BREVE_SIDE)
    flat = tier.stroke * m.v(*BREVE_FLAT)
    top = tier.floor + max(tier.height * 0.82, flat * BREVE_DEPTH)
    shape = ribbon(
        [
            Node((-width / 2 + side / 2, top), DOWN, side, cut="h"),
            Node((0, tier.floor + flat / 2), RIGHT, flat),
            Node((width / 2 - side / 2, top), UP, side, cut="h"),
        ],
        0.6,
    )
    return [shape]


def cedilla_hook(m, x, neck_top, scale):
    neck = m.v(*CEDILLA_NECK) * scale
    flat = m.v(*CEDILLA_FLAT) * scale
    tail = m.v(*CEDILLA_TAIL) * scale
    sweep = m.v(*CEDILLA_WEIGHT) * scale
    lower = -m.v(*CEDILLA_DEPTH) * scale + flat / 2
    upper = min(-m.v(*CEDILLA_SWEEP) * scale, -(m.cap_ov + sweep / 2 + CEDILLA_CLEAR))
    counter = (upper - sweep * 0.47 + lower + flat / 2) / 2
    shape = ribbon(
        [
            Node((x, neck_top), DOWN, neck, cut="h"),
            Node((x, m.v(22, 26) * scale), DOWN, neck, straight=True),
            Node((x + m.v(50, 58) * scale, upper), aim(-8), sweep),
            Node((x + m.v(116, 136) * scale, counter), DOWN, neck * 0.84, arrive=0.74, leave=0.74),
            Node((x + m.v(44, 52) * scale, lower), LEFT, tail),
            Node((x - m.v(26, 34) * scale, lower), LEFT, tail, straight=True),
        ],
        0.6,
    )
    return shape


def dotted_circle(m):
    side = m.v(54, 74, light=40, black=82)
    radius = m.v(*CIRCLE_RADIUS)
    centre = XH / 2
    dots = []
    for index in range(CIRCLE_DOTS):
        angle = 2 * math.pi * index / CIRCLE_DOTS
        along, across_ = (math.cos(angle), math.sin(angle)), (-math.sin(angle), math.cos(angle))
        middle = (radius + radius * along[0], centre + radius * along[1])
        corners = [
            (middle[0] + (sx * along[0] + sy * across_[0]) * side / 2, middle[1] + (sx * along[1] + sy * across_[1]) * side / 2)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))
        ]
        dots.append(polygon(corners))
    return spaced(m, dots, 2 * radius, m.v(40, 32), m.v(40, 32))


def comma_size(m):
    return m.v(*CARON_TICK) * COMMA_SIDE, m.v(*CARON_FALL) * COMMA_FALL


def comma_below(m, x, top, scale):
    side, fall = (value * scale for value in comma_size(m))
    return shift([tick_shape(side, fall)], x - side / 2, -m.v(*COMMA_GAP) - side)[0]


def commaturned(m, tier):
    side, fall = comma_size(m)
    shape = turn([tick_shape(side, fall)], side / 2, 0)
    return centred(shift(shape, 0, tier.floor + fall))


def hookabove(m, tier):
    stroke = tier.stroke
    height = tier.height + stroke * m.v(*HOOK_LIFT)
    edge = stroke * m.v(*HOOK_EDGE)
    flat = stroke * m.v(*HOOK_FLAT)
    end = stroke * m.v(*HOOK_END)
    stem = stroke * m.v(*HOOK_STEM)
    lean = aim(m.v(*HOOK_LEAN))
    drop = aim(m.v(*HOOK_DROP))
    inside = height - flat
    low = tier.floor + m.v(*HOOK_FLOAT)
    cut = end / lean[1]
    reach = cut + inside * (1 - HOOK_TERMINAL) * lean[0] / lean[1]
    width = max(tier.run * HOOK_RUN + stroke * m.v(*HOOK_SPREAD), reach + edge + stroke * m.v(*HOOK_COUNTER))
    crown = max(width * 0.5, (reach + width - edge) / 2)
    shoulder = inside * m.v(*HOOK_SHOULDER)
    sweep = min(HOOK_SWEEP, 1 - HOOK_GAP / shoulder)
    swing = shoulder * drop[0] / drop[1] * sweep
    stem = min(stem, -(edge + swing) * drop[1] - stroke * HOOK_NECK_ROOM)
    post = width - edge - swing - stem / 2 / drop[1]
    shape = ribbon(
        [
            Node((cut / 2, low + inside * HOOK_TERMINAL), lean, end, cut="h"),
            Node((crown, low + height - flat / 2), RIGHT, flat),
            Node((width - edge / 2, low + shoulder), DOWN, edge),
            Node((post, low), drop, stem, cut="h"),
        ],
        0.6,
    )
    scale = mark_scale(m, tier)
    return [contour.map(lambda point: (point[0] * scale, low + (point[1] - low) * scale)) for contour in centred([shape])]


def flattened(m, tier):
    loop = m.v(*STACK_LOOP)
    dot = tier.dot * m.v(*STACK_DOT)
    return replace(
        tier,
        height=tier.height * m.v(*STACK_HEIGHT),
        run=tier.run * m.v(*STACK_RUN),
        hat_height=tier.hat_height * m.v(*STACK_HAT),
        stroke=tier.stroke * m.v(*STACK_STROKE),
        hat_stroke=tier.hat_stroke * m.v(*STACK_HAT_STROKE),
        loop=tier.loop * loop,
        loop_side=tier.loop_side * loop,
        loop_flat=tier.loop_flat * loop,
        loop_floor=min(tier.loop_floor, tier.floor),
        dot=dot,
        pitch=tier.pitch - (tier.dot - dot),
        stacked=True,
    )


def pressed(m, tier):
    tier = flattened(m, tier)
    press = m.v(*PRESS_HEIGHT)
    return replace(tier, floor=tier.floor - m.v(*PRESS_DROP), height=tier.height * press, hat_height=tier.hat_height * press, stroke=tier.stroke * press)


def pressing(tier):
    def build(m):
        return pressed(m, tier(m))

    return build


def mark_scale(m, tier):
    if tier.floor <= CAP:
        return 1.0
    return m.v(*(STACK_HOOK if tier.stacked else CAP_HOOK))


def stack_form(m, tier):
    return flattened(m, tier) if tier.floor > CAP else tier


def stacking(tier):
    def build(m):
        return flattened(m, tier(m))

    return build


def stack_gap(m, capital):
    return m.v(*(CAP_STACK_GAP if capital else STACK_GAP))


def beside_circumflex(second):
    def draw(m, tier):
        tier = stack_form(m, tier)
        height = tier.hat_height * m.v(*BESIDE_HEIGHT)
        smaller = replace(tier, height=height, run=height * BESIDE_RUN, stroke=tier.hat_stroke * m.v(*BESIDE_STROKE))
        mark = ACCENTS[second](m, smaller)
        left, _ = bounds(mark)
        dx = tier.hat_span / 2 + m.v(*BESIDE_GAP) - left
        return circumflex(m, tier) + shift(mark, dx, tier.hat_lift + tier.hat_height * BESIDE_RISE)

    return draw


def hat_pressed(m, tier):
    tier = pressed(m, tier)
    return replace(tier, hat_height=tier.hat_height / m.v(*PRESS_HEIGHT) * m.v(*HAT_PRESS_HEIGHT))


def above_circumflex(second):
    def draw(m, tier):
        capital = tier.floor > CAP
        upper = stack_form(m, tier)
        if capital:
            upper = replace(upper, height=upper.height * m.v(*HAT_TONE_HEIGHT))
        mark = ACCENTS[second](m, upper)
        tier = hat_pressed(m, tier) if capital else tier
        bottom = min(point[1] for contour in mark for point in contour.points())
        rise = tier.floor + tier.hat_lift + tier.hat_height + stack_gap(m, capital) * PRESS_GAP - bottom
        return circumflex(m, tier) + shift(mark, 0, rise)

    return draw


def dot_below(m, x, top, scale):
    side = small(m).dot * scale
    gap = m.v(*DOT_BELOW_GAP)
    return rect(x - side / 2, -gap - side, x + side / 2, -gap)


def macron_below(m, x, top, scale):
    tier = small(m)
    width = tier.span * MACRON_BELOW_SPAN * scale
    thickness = tier.stroke * m.v(*MACRON_BELOW_WEIGHT) * scale
    gap = m.v(*DOT_BELOW_GAP)
    return rect(x - width / 2, -gap - thickness, x + width / 2, -gap)


def dieresis_below(m, x, top, scale):
    tier = small(m)
    side = tier.dot * scale
    step = tier.pitch / 2 * scale
    gap = m.v(*DOT_BELOW_GAP)
    return [rect(x + offset - side / 2, -gap - side, x + offset + side / 2, -gap) for offset in (-step, step)]


def tilde_below(m, x, top, scale):
    shape = tilde(m, small(m))
    high = ink_bounds(Glyph(shape, 0))[3]
    gap = m.v(*DOT_BELOW_GAP)
    return [contour.map(lambda point: (x + point[0] * scale, -gap + (point[1] - high) * scale * TILDE_BELOW_DEPTH)) for contour in shape]


def line_below(m, x, top, scale):
    side = small(m).stroke * scale * LINE_BELOW_WEIGHT
    gap = m.v(*DOT_BELOW_GAP)
    return rect(x - side / 2, -gap - m.v(*LINE_BELOW_LENGTH) * scale, x + side / 2, -gap)


def horn_mark(capital):
    def draw(m):
        grow = 1.16 if capital else 1.0
        thick = m.v(66, 96, light=46, black=116) * grow
        width = m.v(92, 104, light=86, black=112) * grow
        height = m.v(118, 124, light=114, black=128) * grow
        shape = ribbon(
            [
                Node((-thick * 0.4, -thick * 0.3), aim(24), thick * 0.95),
                Node((width, height), aim(74), thick * 0.8, cut="h"),
            ],
            0.6,
        )
        return Glyph([shape], 0)

    return draw


def hungarumlaut(m, tier):
    single = replace(tier, stroke=tier.stroke * DOUBLE_STROKE, run=tier.run * DOUBLE_RUN)
    step = across((single.run, single.height), single.stroke) * m.v(*DOUBLE_PITCH) / 2
    shape = acute(m, single)
    return shift(shape, -step) + shift(shape, step)


def ogonek_hook(m, x, top, scale):
    neck = m.v(*OGONEK_NECK) * scale
    side = m.v(*OGONEK_SIDE) * scale
    flat = m.v(*OGONEK_FLAT) * scale
    bottom = -m.v(*OGONEK_DEPTH) * scale + flat / 2
    lean = aim(OGONEK_LEAN)
    return ribbon(
        [
            Node((x - neck / 2 / abs(lean[1]), top), lean, neck, cut="h"),
            Node((x - m.v(*OGONEK_REACH) * scale + side / 2, -m.v(*OGONEK_BELLY) * scale), DOWN, side),
            Node((x - m.v(*OGONEK_TURN) * scale, bottom), RIGHT, flat * OGONEK_TAPER),
            Node((x + m.v(*OGONEK_TAIL) * scale, bottom), RIGHT, flat * OGONEK_TAPER, straight=True),
        ],
        0.6,
    )


ACCENTS = {
    "grave": grave,
    "acute": acute,
    "circumflex": circumflex,
    "tilde": tilde,
    "dieresis": dieresis,
    "ring": ring_mark,
    "caron": caron,
    "macron": macron,
    "breve": breve,
    "dotaccent": dotaccent,
    "hungarumlaut": hungarumlaut,
    "commaturned": commaturned,
    "hookabove": hookabove,
}
for second in ("acute", "grave", "hookabove"):
    ACCENTS[f"circumflex_{second}"] = beside_circumflex(second)
ACCENTS["circumflex_tilde"] = above_circumflex("tilde")


def dotlessi(m):
    stem = m.stem
    return spaced(m, [rect(0, 0, stem, XH)], stem, "straight", "straight")


def joined_bowl(m, outer, inner, crotches, inner_ends, centres, headings=None):
    headings = headings or (-m.v(*CROTCH), m.v(*CROTCH))
    x0, y0, x1, y1 = outer
    ix0, iy0, ix1, iy1 = inner
    low, high = crotches
    inner_low, inner_high = inner_ends
    centre, inner_centre = centres
    middle = (y0 + y1) / 2
    inner_middle = (iy0 + iy1) / 2
    body = Path(low).to(along(low, high, x1, 0.25)).to(along(low, high, x1, 0.75)).to(high)
    body.bez(bend(high, aim(headings[1]), (centre, y1), LEFT, CROTCH_PULL, m.k_out))
    body.arc((x0, middle), "h", m.k_out)
    body.arc((centre, y0), "v", m.k_out)
    body.bez(bend((centre, y0), RIGHT, low, aim(headings[0]), m.k_out, CROTCH_PULL))
    counter = Path((ix1, inner_low)).to((ix1, inner_high))
    counter.arc((inner_centre, iy1), "v", m.k_in).arc((ix0, inner_middle), "h", m.k_in)
    counter.arc((inner_centre, iy0), "v", m.k_in).arc((ix1, inner_low), "h", m.k_in)
    return [body.close(), counter.close(hole=True)]


def joined_eye(m, width, crotches, inner_ends):
    side = m.round * m.v(1.0, 1.0, black=0.9)
    low, high = crotches
    bar_bottom = m.v(*E_BAR_BOTTOM)
    bar_top = bar_bottom + m.bar * m.v(*lowercase.E_BAR_WEIGHT)
    top, bottom = XH + m.ov, -m.ov
    inner_top, inner_bottom = XH - m.thin * m.v(1.0, 0.92, black=lowercase.E_TOP), m.thin * m.v(1.0, 0.95, black=0.69)
    middle_y = (top + bottom) / 2
    middle_x = (high[0] + width) / 2
    inner_x = width / 2
    floor_x = inner_x - m.v(0, 14, light=0, black=36)
    tail_y = m.v(*E_TAIL)
    tail_out = parts.reach(quarter((middle_x, bottom), (width, middle_y), "h", m.k_out), 1, tail_y)
    tail_in = parts.reach(quarter((floor_x, inner_bottom), (width - side * m.v(*lowercase.E_TAPER), middle_y), "h", m.k_in), 1, tail_y)
    inset = side * 0.25
    path = Path(tail_out[3])
    path.bez(flip(tail_out))
    path.bez(bend((middle_x, bottom), LEFT, low, aim(180 + m.v(*CROTCH)), m.k_out, CROTCH_PULL))
    path.to(along(low, high, inset, 0.25))
    path.to(along(low, high, inset, 0.75))
    path.to(high)
    path.bez(bend(high, aim(180 - m.v(*CROTCH)), (middle_x, top), RIGHT, CROTCH_PULL, m.k_out))
    path.arc((width, middle_y), "h", m.k_out)
    path.to((width, bar_bottom))
    path.to((width - side, bar_bottom))
    path.to((width - side, middle_y))
    path.arc((inner_x, inner_top), "v", m.k_in)
    path.arc((side, inner_ends[1]), "h", m.k_in)
    path.to((side, inner_ends[0]))
    path.arc((floor_x, inner_bottom), "v", m.k_in)
    path.bez(tail_in)
    return [path.close(), rect(side * 0.5, bar_bottom, width - side * 0.5, bar_top)]


def oe(m):
    side = m.round
    bowl_width = m.v(*OE_BOWL_WIDTH)
    eye_width = m.v(*OE_EYE_WIDTH)
    join = bowl_width - side
    stem_x = side / 2
    top_crotch = m.v(*OE_CROTCH)
    inner_high = m.v(*OE_INNER)
    crotches = ((stem_x, XH - top_crotch), (stem_x, top_crotch))
    inner_ends = (XH - inner_high, inner_high)
    bowl = joined_bowl(
        m,
        (0, -m.ov, join + side * 0.75, XH + m.ov),
        (side, -m.ov + m.thin, join, XH + m.ov - m.thin),
        shift_points(crotches, join),
        inner_ends,
        ((join + stem_x) / 2, (side + join) / 2),
    )
    eye = shift(joined_eye(m, eye_width, crotches, inner_ends), join)
    depth = m.v(*CROTCH_FILLET)
    body = round_arriving(bowl[0], -1, flip(segment_of(eye[0], 1)), depth)
    body = round_leaving(body, 3, flip(segment_of(eye[0], 5)), depth)
    return spaced(m, [body, bowl[1]] + shared_fillets(eye, depth), join + eye_width, "round", m.v(30, 22))


def joined_hook(m, peak, reach, join, crotch, base, inner_high):
    side = m.round
    thick = m.v(*A_THICK)
    top = XH + m.ov
    far_out = m.v(28, 22)
    y_out = top - m.v(190, 200)
    y_in = top - thick - m.v(104, 96)
    terminal_y = m.v(*A_TERMINAL)
    peak_in = peak + m.v(6, 8)
    end_out = parts.reach(quarter((peak, top), (far_out, y_out), "h", m.k_out), 1, terminal_y)
    end_in = parts.reach(quarter((peak_in, top - thick), (far_out + side, y_in), "h", m.k_in), 1, terminal_y)
    path = Path(end_out[3])
    path.bez(flip(end_out))
    path.bez(bend((peak, top), RIGHT, crotch, aim(m.v(*CROTCH)), m.k_out, CROTCH_PULL))
    path.to((reach, max(crotch[1] - side, base + SHARED_EDGE_GAP)))
    path.to((reach, base))
    path.to((join, base))
    path.to((join, inner_high))
    path.arc((peak_in, top - thick), "v", m.k_in)
    path.bez(end_in)
    return path.close()


def ae(m):
    side = m.round
    bowl_width = m.v(*AE_BOWL_WIDTH)
    eye_width = m.v(*AE_EYE_WIDTH)
    join = bowl_width - side
    stem_x = side / 2
    top_crotch = m.v(*OE_CROTCH)
    inner_high = m.v(*OE_INNER)
    low_crotch = m.v(*AE_LOW_CROTCH)
    inner_low = m.v(*AE_INNER_LOW)
    belly_top = m.v(*A_BELLY_TOP)
    belly_flat = m.v(*A_BELLY_FLAT)
    crotches = ((stem_x, low_crotch), (stem_x, top_crotch))
    hook = joined_hook(m, bowl_width * A_PEAK, join + side * 0.75, join, (join + stem_x, top_crotch), belly_top - belly_flat - m.v(*AE_SLAB_DROP), inner_high)
    belly = joined_bowl(
        m,
        (0, -m.ov, join + side * 0.75, belly_top),
        (side * m.v(*A_BELLY_SIDE), m.thin * m.v(*A_BELLY_FLOOR), join, belly_top - belly_flat),
        ((join + stem_x, low_crotch), (join + stem_x, belly_top - m.v(*AE_BELLY_DROP))),
        (inner_low, max(belly_top - belly_flat - m.v(*AE_BELLY_CORNER), inner_low + SHARED_EDGE_GAP)),
        ((join + stem_x) * 0.5, (side * m.v(*A_BELLY_SIDE) + join) * 0.5),
        (-m.v(*CROTCH), AE_BELLY_HEADING),
    )
    eye = shift(joined_eye(m, eye_width, crotches, (inner_low, inner_high)), join)
    depth = m.v(*CROTCH_FILLET)
    hook = round_arriving(hook, 1, segment_of(eye[0], 5), depth)
    body = round_arriving(belly[0], -1, flip(segment_of(eye[0], 1)), depth)
    return spaced(m, [hook, body, belly[1]] + shared_fillets(eye, depth), join + eye_width, "round", m.v(30, 22))


def shared_fillets(eye, depth):
    upper = segment_of(eye[0], 5)
    contour = split_where(eye[0], 5, point_at(upper, at_height(upper, upper[0][1] + depth)))
    lower = segment_of(contour, 1)
    contour = split_where(contour, 1, point_at(lower, at_height(lower, lower[3][1] - depth)))
    return [contour] + eye[1:]


def split_where(contour, index, point):
    bezier = segment_of(contour, index)
    first, second = split(bezier, at_height(bezier, point[1]))
    segments = list(contour.segments)
    segments[index : index + 1] = [(first[1], first[2], point), second[1:]]
    return Contour(contour.start, segments, contour.hole)


def along(low, high, x, t):
    return (x, low[1] + (high[1] - low[1]) * t)


def shift_points(points, dx):
    return tuple((x + dx, y) for x, y in points)


def point_at(bezier, t):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = bezier
    u = 1 - t
    a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
    return (a * x0 + b * x1 + c * x2 + d * x3, a * y0 + b * y1 + c * y2 + d * y3)


def tangent_at(bezier, t):
    u = 1 - t
    weights = (-3 * u * u, 3 * u * u - 6 * u * t, 6 * u * t - 3 * t * t, 3 * t * t)
    return (
        sum(weight * point[0] for weight, point in zip(weights, bezier)),
        sum(weight * point[1] for weight, point in zip(weights, bezier)),
    )


def segment_of(contour, index):
    index %= len(contour.segments)
    return (list(contour.corners())[index], *contour.segments[index])


def rounded_crotch(arriving, leaving, depth):
    crotch = arriving[3]
    edge = crotch[1] + (depth if arriving[0][1] > crotch[1] else -depth)
    t_in, t_out = at_height(arriving, edge), at_height(leaving, edge)
    trimmed = head(arriving, t_in)
    fillet = bend(trimmed[3], tangent_at(arriving, t_in), point_at(leaving, t_out), tangent_at(leaving, t_out), FILLET_PULL, FILLET_PULL)
    return trimmed, fillet


def round_arriving(contour, index, leaving, depth):
    index %= len(contour.segments)
    trimmed, fillet = rounded_crotch(segment_of(contour, index), leaving, depth)
    segments = list(contour.segments)
    segments[index : index + 1] = [trimmed[1:], fillet[1:]]
    start = fillet[3] if index == len(contour.segments) - 1 else contour.start
    return Contour(start, segments, contour.hole)


def round_leaving(contour, index, arriving, depth):
    trimmed, fillet = rounded_crotch(flip(segment_of(contour, index)), flip(arriving), depth)
    segments = list(contour.segments)
    segments[index - 1] = (fillet[3],)
    segments[index : index + 1] = [flip(fillet)[1:], flip(trimmed)[1:]]
    return Contour(contour.start, segments, contour.hole)


def solve(test):
    low, high = 0.0, 1.0
    for _ in range(48):
        middle = (low + high) / 2
        if test(middle) == test(0.0):
            low = middle
        else:
            high = middle
    return (low + high) / 2


def at_height(bezier, y):
    return solve(lambda t: point_at(bezier, t)[1] > y)


def tilted_bar(centre, length, thickness, degrees):
    along = aim(degrees)
    normal = (-along[1], along[0])
    corners = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        corners.append(
            (
                centre[0] + sx * along[0] * length / 2 + sy * normal[0] * thickness / 2,
                centre[1] + sx * along[1] * length / 2 + sy * normal[1] * thickness / 2,
            )
        )
    return polygon(corners)


def eth(m):
    width = m.v(*ETH_WIDTH)
    side = m.round
    top, bottom = XH + m.ov - m.v(*ETH_DROP), -m.ov
    middle = (top + bottom) / 2
    bowl = ring(0, bottom, width, top, side, m.thin, m.k_out, m.k_in)
    rim = segment_of(bowl[0], 1)
    edge, slope = point_at(rim, ETH_ROOT_AT), tangent_at(rim, ETH_ROOT_AT)
    length = math.hypot(*slope)
    upward = (-slope[0] / length, -slope[1] / length)
    root_weight = side * ETH_ROOT_WEIGHT
    root = (edge[0] - upward[1] * root_weight / 2, edge[1] + upward[0] * root_weight / 2)
    shoulder = (width * m.v(*ETH_SHOULDER_X) - side / 2, m.v(*ETH_SHOULDER_Y))
    rise = aim(m.v(*ETH_RISE))
    lean = aim(m.v(*ETH_LEAN))
    tip = (width * m.v(*ETH_TIP_X), ASC)
    upper = bend(shoulder, rise, tip, lean, 0.5, 0.5)
    tail = ribbon(
        [
            Node(root, upward, root_weight, leave=0.76),
            Node(shoulder, rise, side * m.v(0.94, 0.94, black=0.9), arrive=0.62, leave=0.5),
            Node(tip, lean, m.v(*ETH_TIP), cut="h", arrive=0.5),
        ],
        0.62,
    )
    bar_y = m.v(*ETH_BAR_Y)
    centre = point_at(upper, at_height(upper, bar_y))
    start, end = ink_runs([tail], bar_y)[0]
    bar = tilted_bar(centre, end - start + 2 * m.v(*ETH_BAR_REACH), m.bar * m.v(*ETH_BAR_WEIGHT), m.v(*ETH_BAR_ANGLE))
    return spaced(m, bowl + [tail, bar], width, "round", "round")


def thorn(m):
    width = m.v(472, 540)
    shapes = [rect(0, DESC, m.stem, ASC)] + lowercase.bowl(m, width)
    return spaced(m, shapes, width, "straight", "round")


def germandbls(m):
    stem = m.stem
    width = m.v(500, 566)
    flat = m.v(76, 112, light=54, black=128)
    side = m.round
    waist = m.v(410, 404, black=420)
    bar = m.v(64, 96, light=44, black=108)
    shoulder = width - m.v(44, 40)
    knot = stem + m.v(58, 84, black=72)
    lap = m.v(12, 14)
    end = m.v(*ESZETT_END)
    lean = aim(m.v(*ESZETT_LEAN))
    opening = stem + m.v(*ESZETT_GAP)
    foot = m.v(*ESZETT_FOOT)
    belly = opening + (width - side - opening) * ESZETT_BELLY
    upper = ribbon(
        [
            Node((stem / 2, 0), UP, stem, cut="h"),
            Node((stem / 2, ASC - m.v(170, 180)), UP, stem, straight=True),
            Node((m.v(236, 272), ASC + m.ov - flat / 2), RIGHT, flat),
            Node((shoulder - side / 2, (ASC + waist) / 2), DOWN, side * m.v(0.96, 0.96, black=0.86)),
            Node((knot + 2 * lap, waist), LEFT, bar, arrive=m.v(0.6, 0.6, black=0.5)),
            Node((knot, waist), LEFT, bar, straight=True),
        ],
        0.6,
    )
    lower = ribbon(
        [
            Node((knot + lap, waist), RIGHT, bar),
            Node((width - side / 2, waist / 2 - m.v(14, 12)), DOWN, side * m.v(1, 1, black=0.9)),
            Node((belly, -m.ov + m.thin / 2), LEFT, m.thin),
            Node((opening, -m.ov + m.thin / 2), LEFT, m.thin, straight=True, cut="v"),
        ],
        0.6,
    )
    return spaced(m, [upper, lower], width, "straight", "round")


def slashed_bowl(m, glyph, top, side, flat):
    left, right = bounds(glyph.contours)
    return left, right, ring(left, -m.ov, right, top + m.ov, side * m.v(*SLASHED_SIDE), flat * m.v(*SLASHED_FLAT), m.k_out, m.k_in)


def oslash(m):
    glyph = lowercase.letter_o(m)
    left, right, bowl = slashed_bowl(m, glyph, XH, m.round, m.thin)
    over = m.v(24, 22)
    return Glyph(bowl + [slash_across(m, left, right, XH, over, m.diag * m.v(*SLASH_WEIGHT))], glyph.advance)


def slash_across(m, left, right, height, over, thickness):
    inset = (right - left) * SLASH_INSET
    rise = height + 2 * over
    span = right - left - 2 * inset
    stroke = across((span, rise), thickness)
    middle = (left + right) / 2
    return band((middle + span / 2 - stroke, height + over), (middle - span / 2, -over), stroke)


def capital_ae(m):
    stem = m.cap_stem
    bar = m.cap_bar
    post = m.v(*AE_POST)
    arm = m.v(372, 418)
    span = post + stem * m.v(*AE_LEG_REACH)
    stroke = band_width(span, CAP, m.cap_diag * m.v(1, 0.92, black=0.8))
    leg = band((span - stroke, CAP), (0, 0), stroke)
    waist = CAP * m.v(*AE_WAIST)
    reach = (span - stroke) / CAP * waist + stroke * 0.5
    shapes = [
        leg,
        rect(post, 0, post + stem, CAP),
        rect(post + stem * 0.5, CAP - bar, post + arm, CAP),
        capitals.crossbar(m, reach, post + arm - m.v(34, 30), waist),
        rect(post + stem * 0.5, 0, post + arm, bar),
    ]
    return spaced(m, shapes, post + arm, "cap_diagonal", m.v(38, 28))


def capital_oe(m):
    stem = m.cap_stem
    bar = m.cap_bar
    bowl_width = m.v(560, 624, black=692)
    arm = m.v(372, 416)
    post = bowl_width - stem
    bowl = mirror(lobe(m, stem * 0.5, stem * 0.8, bowl_width, CAP, 0, bar, m.cap_round, rx=m.v(296, 316, black=342)), bowl_width / 2)
    shapes = bowl + [
        rect(post, 0, bowl_width, CAP),
        rect(post + stem * 0.5, CAP - bar, post + arm, CAP),
        capitals.crossbar(m, post + stem * 0.5, post + arm - m.v(34, 30), capitals.WAIST),
        rect(post + stem * 0.5, 0, post + arm, bar),
    ]
    return spaced(m, shapes, post + arm, "cap_round", m.v(38, 28))


def capital_eth(m):
    glyph = capitals.capital_d(m)
    left, _ = bounds(glyph.contours)
    over = m.v(64, 60)
    lead = m.v(36, 34) + over - left
    contours = shift(glyph.contours, lead)
    stem_left = left + lead
    middle = CAP / 2
    half = m.cap_bar / 2
    bar = rect(stem_left - over, middle - half, stem_left + m.cap_stem + m.v(98, 104), middle + half)
    return Glyph(contours + [bar], glyph.advance + lead)


def capital_thorn(m):
    stem = m.cap_stem
    width = m.v(500, 566)
    shapes = [rect(0, 0, stem, CAP)] + lobe(
        m, stem * 0.5, stem * 0.8, width, m.v(578, 584), m.v(158, 146), m.cap_bar * m.v(1, 1, black=0.68), m.cap_round
    )
    return spaced(m, shapes, width, "cap", m.v(30, 22))


def capital_oslash(m):
    glyph = capitals.capital_o(m)
    left, right, bowl = slashed_bowl(m, glyph, CAP, m.cap_round, m.cap_thin)
    over = m.v(22, 20)
    return Glyph(bowl + [slash_across(m, left, right, CAP, over, m.cap_diag * m.v(*CAP_SLASH_WEIGHT))], glyph.advance)


def whole(value):
    return math.floor(value + 0.5)


def placed(base, mark, place):
    def overlay(m, plain, drawn):
        dx, dy = place(m, plain)
        return shift(slanted(mark, m).contours, dx + m.slope * dy, dy)

    return Overlaid(base, overlay)


def top_name(letter):
    return f"dotless{letter}" if letter in DOTTED else letter


def topped(letter, accent):
    return topped_in(letter, accent, tier_for(letter))


def topped_in(letter, accent, tier):
    capital = letter.isupper()

    def place(m, plain):
        return top_x(top_name(letter), plain, m, capital), top_height(plain, capital) - (CAP if capital else XH)

    return placed(base_of(letter), mark_of(ACCENTS[accent], tier), place)


def stacked_letter(letter, base, accent, lower):
    capital = letter.isupper()

    def place(m, plain):
        x = top_x(top_name(letter), base_of(letter)(m), m, capital)
        return x, stacked(top_of(plain), m, capital) - (CAP if capital else XH)

    def pressed_place(m, plain):
        x, rise = place(m, plain)
        return x, rise - stack_gap(m, capital) * (1 - m.v(*STACK_PRESS_GAP))

    if capital and accent in PRESSED_ACCENTS:
        return placed(topped_in(letter, lower, pressing(tier_for(letter))), mark_of(ACCENTS[accent], stacking(tall)), pressed_place)
    if capital:
        return placed(topped_in(letter, lower, stacking(tier_for(letter))), mark_of(ACCENTS[accent], stacking(tall)), place)
    return placed(base, mark_of(ACCENTS[accent], small), place)


def accented_letter(name, base, accent, capital):
    def tier(m):
        shape = shape_of(name)
        known = len(shape) == 1 and shape.isalpha() and shape.isupper() == capital
        return (tier_for(shape) if known else tall if capital else small)(m)

    def place(m, plain):
        return top_x(name, plain, m, capital), top_height(plain, capital) - (CAP if capital else XH)

    return placed(base, mark_of(ACCENTS[accent], tier), place)


def below(letter, kind, base=None):
    capital = letter.isupper()
    neck, scale = (cap_neck, cap_scale) if capital else (small_neck, small_scale)
    measured = lowercase.letter_i if letter == "i" else base_of(letter)

    def place(m, _):
        plain = measured(m)
        if kind == "ogonek":
            return ogonek_x(plain, m, capital), 0
        if kind == "cedilla":
            return cedilla_x(letter, plain, m, capital), 0
        if kind == "dotbelow":
            return dotbelow_x(plain, m), 0
        return comma_x(plain), 0

    return placed(base or measured, hook_mark(BELOW_HOOKS[kind], neck, scale), place)


def horned(letter):
    capital = letter.isupper()

    def place(m, plain):
        return horn_point(plain, m, capital)

    return placed(base_of(letter), horn_mark(capital), place)


def topped_on(letter, base, accent):
    capital = letter.isupper()

    def place(m, _):
        plain = base_of(letter)(m)
        return top_x(top_name(letter), plain, m, capital), top_height(plain, capital) - (CAP if capital else XH)

    return placed(base, mark_of(ACCENTS[accent], tier_for(letter)), place)


def caron_room_for(letter, glyph, m):
    x, _ = caron_anchor(letter, glyph, m)
    side = (short_wedge_size(m) if letter in SHORT_CARON_BASES else wedge_size(m))[0]
    return whole(max(0, x + side + m.bearing("straight") * CARON_SPACE - glyph.advance))


def ticked(letter):
    base = base_of(letter)

    def widened(m):
        glyph = base(m)
        return Glyph(glyph.contours, glyph.advance + caron_room_for(letter, glyph, m))

    def place(m, plain):
        x, y = caron_anchor(letter, plain, m)
        return x, y - ASC

    return placed(widened, short_tick if letter in SHORT_CARON_BASES else caron_tick, place)


def lifted(tier):
    def build(m):
        size = tier(m)
        lift = CAP_ROUND_LIFT if tier is tall else ROUND_LIFT
        return replace(size, dot_floor=size.dot_floor + whole(m.v(*lift)))

    return build


def dots_raised(tier, lift):
    def build(m):
        size = tier(m)
        return replace(size, dot_floor=size.dot_floor + whole(m.v(*lift)))

    return build


def slim(tier):
    def build(m):
        size = tier(m)
        return replace(
            size,
            floor=size.floor + (m.v(*SLIM_LIFT) + m.slope * m.v(*SLIM_SLANT_LIFT) if tier is small else 0),
            hat_lift=0 if tier is small else m.v(*SLIM_CAP_LIFT),
            pitch=size.pitch * SLIM_SHARE,
            run=size.run * SLIM_SHARE,
            span=size.span * SLIM_SHARE,
            hat_span=size.hat_span * SLIM_SHARE,
        )

    return build


def raised_by(tier, lift):
    def build(m):
        size = tier(m)
        step = whole(m.v(*lift))
        return replace(size, floor=size.floor + step, dot_floor=size.dot_floor + step, loop_floor=size.loop_floor + step)

    return build


def tier_for(letter):
    if letter in LETTER_LIFTS:
        return raised_by(small, LETTER_LIFTS[letter])
    if letter in DOTTED:
        return slim(small)
    if letter == "I":
        return slim(tall)
    tier = tall if letter.isupper() else small
    if letter in ROUND_TOPS:
        return lifted(tier)
    if letter in ASCENDED:
        return dots_raised(tier, ASCENDER_DOT_LIFT)
    return tier


def small_neck(m):
    return m.thin


def small_scale(m):
    return m.v(0.96, 0.92)


def cap_neck(m):
    return m.cap_thin


def cap_scale(m):
    return m.v(0.99, 0.95)


def mark_of(accent, tier):
    def draw(m):
        return Glyph(accent(m, tier(m)), 0)

    return draw


def hook_mark(hook, neck, scale):
    def draw(m):
        drawn = hook(m, 0, neck(m) / 2, scale(m))
        return Glyph(drawn if isinstance(drawn, list) else [drawn], 0)

    return draw


def wedge_size(m):
    return m.v(*WEDGE_TOP), m.v(*WEDGE_DROP)


def short_wedge_size(m):
    top, drop = wedge_size(m)
    return top * SHORT_WEDGE_TOP, drop * SHORT_WEDGE_DROP


def wedge(m, top, drop):
    foot = top * m.v(*WEDGE_FOOT)
    lean = drop * WEDGE_LEAN
    toe = foot - lean
    path = Path((0, ASC)).to((top, ASC))
    path.bez(((top, ASC), (top, ASC - drop * WEDGE_SHOULDER), (toe + (top - toe) * WEDGE_HEEL, ASC - drop * WEDGE_BELLY), (toe, ASC - drop)))
    path.to((-lean, ASC - drop))
    return Glyph([path.close()], 0)


def caron_tick(m):
    return wedge(m, *wedge_size(m))


def short_tick(m):
    return wedge(m, *short_wedge_size(m))


def tick_shape(side, fall):
    toe = side * 0.68 - fall * 0.436
    return polygon(
        [
            (0, side),
            (side, side),
            (side, 0),
            (toe + side * 0.24, -fall),
            (toe - side * 0.24, -fall),
            (side * 0.36, 0),
            (0, 0),
        ]
    )


def dotlessj(m):
    glyph = lowercase.letter_j(m)
    return Glyph(glyph.contours[:1], glyph.advance)


def spacing(accent):
    def draw(m):
        contours = accent(m, small(m))
        left, right = bounds(contours)
        return spaced(m, shift(contours, -left), right - left, m.v(50, 44), m.v(50, 44))

    return draw


def spacing_cedilla(m):
    hook = cedilla_hook(m, 0, m.v(56, 60), m.v(0.96, 0.92))
    left, right = bounds([hook])
    return spaced(m, shift([hook], -left), right - left, m.v(50, 44), m.v(50, 44))


def spacing_ogonek(m):
    hook = ogonek_hook(m, 0, m.v(56, 60), m.v(0.96, 0.92))
    left, right = bounds([hook])
    return spaced(m, shift([hook], -left), right - left, m.v(50, 44), m.v(50, 44))


SERIES = [
    ("A", 0xC0, ["grave", "acute", "circumflex", "tilde", "dieresis", "ring"]),
    ("E", 0xC8, ["grave", "acute", "circumflex", "dieresis"]),
    ("I", 0xCC, ["grave", "acute", "circumflex", "dieresis"]),
    ("N", 0xD1, ["tilde"]),
    ("O", 0xD2, ["grave", "acute", "circumflex", "tilde", "dieresis"]),
    ("U", 0xD9, ["grave", "acute", "circumflex", "dieresis"]),
    ("Y", 0xDD, ["acute"]),
]

SINGLES = [
    ("Y", "dieresis", 0x178, 0xFF),
    ("S", "caron", 0x160, 0x161),
    ("Z", "caron", 0x17D, 0x17E),
    ("C", "cedilla", 0xC7, 0xE7),
    ("A", "macron", 0x100, 0x101),
    ("A", "breve", 0x102, 0x103),
    ("A", "ogonek", 0x104, 0x105),
    ("C", "acute", 0x106, 0x107),
    ("C", "circumflex", 0x108, 0x109),
    ("C", "dotaccent", 0x10A, 0x10B),
    ("C", "caron", 0x10C, 0x10D),
    ("D", "caron", 0x10E, 0x10F),
    ("E", "macron", 0x112, 0x113),
    ("E", "breve", 0x114, 0x115),
    ("E", "dotaccent", 0x116, 0x117),
    ("E", "ogonek", 0x118, 0x119),
    ("E", "caron", 0x11A, 0x11B),
    ("G", "circumflex", 0x11C, 0x11D),
    ("G", "breve", 0x11E, 0x11F),
    ("G", "dotaccent", 0x120, 0x121),
    ("H", "circumflex", 0x124, 0x125),
    ("I", "tilde", 0x128, 0x129),
    ("I", "macron", 0x12A, 0x12B),
    ("I", "breve", 0x12C, 0x12D),
    ("I", "ogonek", 0x12E, 0x12F),
    ("J", "circumflex", 0x134, 0x135),
    ("K", "commaaccent", 0x136, 0x137),
    ("L", "acute", 0x139, 0x13A),
    ("L", "commaaccent", 0x13B, 0x13C),
    ("L", "caron", 0x13D, 0x13E),
    ("N", "acute", 0x143, 0x144),
    ("N", "commaaccent", 0x145, 0x146),
    ("N", "caron", 0x147, 0x148),
    ("O", "macron", 0x14C, 0x14D),
    ("O", "breve", 0x14E, 0x14F),
    ("O", "hungarumlaut", 0x150, 0x151),
    ("R", "acute", 0x154, 0x155),
    ("R", "commaaccent", 0x156, 0x157),
    ("R", "caron", 0x158, 0x159),
    ("S", "acute", 0x15A, 0x15B),
    ("S", "circumflex", 0x15C, 0x15D),
    ("S", "cedilla", 0x15E, 0x15F),
    ("T", "cedilla", 0x162, 0x163),
    ("T", "caron", 0x164, 0x165),
    ("U", "tilde", 0x168, 0x169),
    ("U", "macron", 0x16A, 0x16B),
    ("U", "breve", 0x16C, 0x16D),
    ("U", "ring", 0x16E, 0x16F),
    ("U", "hungarumlaut", 0x170, 0x171),
    ("U", "ogonek", 0x172, 0x173),
    ("W", "circumflex", 0x174, 0x175),
    ("Y", "circumflex", 0x176, 0x177),
    ("Z", "acute", 0x179, 0x17A),
    ("Z", "dotaccent", 0x17B, 0x17C),
    ("S", "commaaccent", 0x218, 0x219),
    ("T", "commaaccent", 0x21A, 0x21B),
    ("A", "caron", 0x1CD, 0x1CE),
    ("I", "caron", 0x1CF, 0x1D0),
    ("O", "caron", 0x1D1, 0x1D2),
    ("U", "caron", 0x1D3, 0x1D4),
    ("G", "caron", 0x1E6, 0x1E7),
    ("K", "caron", 0x1E8, 0x1E9),
    ("O", "ogonek", 0x1EA, 0x1EB),
    ("H", "caron", 0x21E, 0x21F),
    ("W", "grave", 0x1E80, 0x1E81),
    ("W", "acute", 0x1E82, 0x1E83),
    ("W", "dieresis", 0x1E84, 0x1E85),
    ("E", "tilde", 0x1EBC, 0x1EBD),
    ("Y", "grave", 0x1EF2, 0x1EF3),
    ("N", "dotaccent", 0x1E44, 0x1E45),
    ("S", "dotbelow", 0x1E62, 0x1E63),
    ("N", "grave", 0x1F8, 0x1F9),
    ("M", "acute", 0x1E3E, 0x1E3F),
]

SINGLES += [
    ("G", "acute", 0x1F4, 0x1F5),
    ("B", "macronbelow", 0x1E06, 0x1E07),
    ("D", "macronbelow", 0x1E0E, 0x1E0F),
    ("K", "macronbelow", 0x1E34, 0x1E35),
    ("L", "macronbelow", 0x1E3A, 0x1E3B),
    ("N", "macronbelow", 0x1E48, 0x1E49),
    ("R", "macronbelow", 0x1E5E, 0x1E5F),
    ("T", "macronbelow", 0x1E6E, 0x1E6F),
    ("Z", "macronbelow", 0x1E94, 0x1E95),
    ("B", "dotaccent", 0x1E02, 0x1E03),
    ("D", "dotaccent", 0x1E0A, 0x1E0B),
    ("F", "dotaccent", 0x1E1E, 0x1E1F),
    ("M", "dotaccent", 0x1E40, 0x1E41),
    ("P", "dotaccent", 0x1E56, 0x1E57),
    ("S", "dotaccent", 0x1E60, 0x1E61),
    ("T", "dotaccent", 0x1E6A, 0x1E6B),
]

ON_DRAWN = [
    ("AE", "acute", 0x1FC),
    ("ae", "acute", 0x1FD),
    ("Oslash", "acute", 0x1FE),
    ("oslash", "acute", 0x1FF),
]

STACKED = [
    ("Aring", "acute", 0x1FA),
    ("aring", "acute", 0x1FB),
    ("Udieresis", "macron", 0x1D5),
    ("udieresis", "macron", 0x1D6),
    ("Udieresis", "acute", 0x1D7),
    ("udieresis", "acute", 0x1D8),
    ("Udieresis", "caron", 0x1D9),
    ("udieresis", "caron", 0x1DA),
    ("Udieresis", "grave", 0x1DB),
    ("udieresis", "grave", 0x1DC),
]

VIETNAMESE = [
    ("A", "dotbelow", 0x1EA0), ("A", "hookabove", 0x1EA2), ("A", "circumflex_acute", 0x1EA4), ("A", "circumflex_grave", 0x1EA6),
    ("A", "circumflex_hookabove", 0x1EA8), ("A", "circumflex_tilde", 0x1EAA), ("Acircumflex", "dotbelow", 0x1EAC),
    ("Abreve", "acute", 0x1EAE), ("Abreve", "grave", 0x1EB0), ("Abreve", "hookabove", 0x1EB2), ("Abreve", "tilde", 0x1EB4),
    ("Abreve", "dotbelow", 0x1EB6),
    ("E", "dotbelow", 0x1EB8), ("E", "hookabove", 0x1EBA), ("E", "circumflex_acute", 0x1EBE), ("E", "circumflex_grave", 0x1EC0),
    ("E", "circumflex_hookabove", 0x1EC2), ("E", "circumflex_tilde", 0x1EC4), ("Ecircumflex", "dotbelow", 0x1EC6),
    ("I", "hookabove", 0x1EC8), ("I", "dotbelow", 0x1ECA),
    ("O", "dotbelow", 0x1ECC), ("O", "hookabove", 0x1ECE), ("O", "circumflex_acute", 0x1ED0), ("O", "circumflex_grave", 0x1ED2),
    ("O", "circumflex_hookabove", 0x1ED4), ("O", "circumflex_tilde", 0x1ED6), ("Ocircumflex", "dotbelow", 0x1ED8),
    ("Ohorn", "acute", 0x1EDA), ("Ohorn", "grave", 0x1EDC), ("Ohorn", "hookabove", 0x1EDE), ("Ohorn", "tilde", 0x1EE0),
    ("Ohorn", "dotbelow", 0x1EE2),
    ("U", "dotbelow", 0x1EE4), ("U", "hookabove", 0x1EE6), ("Uhorn", "acute", 0x1EE8), ("Uhorn", "grave", 0x1EEA),
    ("Uhorn", "hookabove", 0x1EEC), ("Uhorn", "tilde", 0x1EEE), ("Uhorn", "dotbelow", 0x1EF0),
    ("Y", "dotbelow", 0x1EF4), ("Y", "hookabove", 0x1EF6), ("Y", "tilde", 0x1EF8),
]
HORNED = [("O", 0x1A0, 0x1A1), ("U", 0x1AF, 0x1B0)]

UNPAIRED = [
    ("G", "commaaccent", 0x122),
    ("g", "commaturned", 0x123),
    ("I", "dotaccent", 0x130),
    ("h", "macronbelow", 0x1E96),
]

NUDGES = {
    "a": (10, 10),
    "E": (-10, -10),
    "Ereversed": (10, 10),
    "u": (-6, -8),
    "n": (-4, -6),
}
LETTER_LIFTS = {"y": (0, 14, 0, 20)}

SPACING = {
    "acute": (0xB4, acute),
    "dieresis": (0xA8, dieresis),
    "macron": (0xAF, macron),
    "circumflex": (0x2C6, circumflex),
    "caron": (0x2C7, caron),
    "breve": (0x2D8, breve),
    "dotaccent": (0x2D9, dotaccent),
    "ring": (0x2DA, ring_mark),
    "tilde": (0x2DC, tilde),
    "hungarumlaut": (0x2DD, hungarumlaut),
}

TOP_MARKS = {
    "gravecomb": (0x300, "grave"),
    "acutecomb": (0x301, "acute"),
    "circumflexcomb": (0x302, "circumflex"),
    "tildecomb": (0x303, "tilde"),
    "macroncomb": (0x304, "macron"),
    "brevecomb": (0x306, "breve"),
    "dotaccentcomb": (0x307, "dotaccent"),
    "dieresiscomb": (0x308, "dieresis"),
    "ringcomb": (0x30A, "ring"),
    "hungarumlautcomb": (0x30B, "hungarumlaut"),
    "caroncomb": (0x30C, "caron"),
    "commaturnedcomb": (0x312, "commaturned"),
    "hookabovecomb": (0x309, "hookabove"),
}
BELOW_MARKS = {
    "cedillacomb": (0x327, cedilla_hook, "bottom"),
    "ogonekcomb": (0x328, ogonek_hook, "ogonek"),
    "commaaccentcomb": (0x326, comma_below, "comma"),
    "dotbelowcomb": (0x323, dot_below, "dotbelow"),
    "verticallinebelowcomb": (0x329, line_below, "dotbelow"),
    "macronbelowcomb": (0x331, macron_below, "comma"),
    "dieresisbelowcomb": (0x324, dieresis_below, "comma"),
    "tildebelowcomb": (0x330, tilde_below, "comma"),
}
BELOW_HOOKS = {"cedilla": cedilla_hook, "ogonek": ogonek_hook, "commaaccent": comma_below, "dotbelow": dot_below}
BELOW_HOOKS["macronbelow"] = macron_below
HORN_MARKS = {"horncomb": 0x31B}
LIGATED_MARKS = {
    f"{second}circumflexcomb": ("circumflexcomb", f"{second}comb", f"circumflex_{second}")
    for second in ("acute", "grave", "hookabove", "tilde")
}
DOT_ACCENTS = ("dotaccent", "dieresis")
NARROW_BASES = ("dotlessi", "dotlessj", "I")
DOTTED = ("i", "j")
CASE = ".case"
STACK = ".stack"
PRESS = ".press"
PRESSED_MARKS = ("brevecomb",)
NARROW = ".narrow"
SAME_ON_I = ("ring",)


def base_of(letter):
    if letter == "i":
        return dotlessi
    if letter == "j":
        return dotlessj
    if letter.isupper():
        return getattr(capitals, f"capital_{letter.lower()}")
    return getattr(lowercase, f"letter_{letter}")


def accented():
    entries = []
    for capital, code, marks in SERIES:
        for index, mark in enumerate(marks):
            entries.append((capital, mark, code + index))
            entries.append((capital.lower(), mark, code + index + 0x20))
    for letter, mark, upper_code, lower_code in SINGLES:
        entries.append((letter, mark, upper_code))
        entries.append((letter.lower(), mark, lower_code))
    return entries + UNPAIRED


def vietnamese_name(base, accent):
    return base + accent.replace("_", "")


def vietnamese(base, letter, accent, glyphs):
    if accent in BELOW_HOOKS:
        return below(letter, accent, glyphs[base][1] if base != letter else None)
    if base == letter:
        return topped(letter, accent)
    if base.endswith("horn"):
        return topped_on(letter, glyphs[base][1], accent)
    return stacked_letter(letter, glyphs[base][1], accent, base[len(letter):])


def composed(letter, mark):
    if mark in BELOW_HOOKS:
        return below(letter, mark)
    if mark == "caron" and letter in CARON_BASES:
        return ticked(letter)
    return topped(letter, mark)


def register():
    glyphs = {}
    like = {}
    for letter, mark, code in accented():
        name = f"{letter}{mark}"
        glyphs[name] = (code, composed(letter, mark))
        like[name] = letter
    for name, (code, accent) in SPACING.items():
        glyphs[name] = (code, spacing(accent))
    glyphs["cedilla"] = (0xB8, spacing_cedilla)
    glyphs["dottedcircle"] = (0x25CC, dotted_circle)
    glyphs["ogonek"] = (0x2DB, spacing_ogonek)
    letters = {
        "AE": (0xC6, capital_ae, None),
        "Eth": (0xD0, capital_eth, "D"),
        "Oslash": (0xD8, capital_oslash, "O"),
        "Thorn": (0xDE, capital_thorn, None),
        "germandbls": (0xDF, germandbls, "b"),
        "ae": (0xE6, ae, "e"),
        "eth": (0xF0, eth, "o"),
        "oslash": (0xF8, oslash, "o"),
        "thorn": (0xFE, thorn, "b"),
        "dotlessi": (0x131, dotlessi, "i"),
        "OE": (0x152, capital_oe, None),
        "oe": (0x153, oe, "e"),
        "dotlessj": (0x237, dotlessj, "j"),
    }
    for name, (code, draw, kin) in letters.items():
        glyphs[name] = (code, draw)
        if kin:
            like[name] = kin
    for base, accent, code in ON_DRAWN:
        glyphs[base + accent] = (code, accented_letter(base, glyphs[base][1], accent, base[0].isupper()))
        like[base + accent] = like.get(base, base)
    for base, accent, code in STACKED:
        letter = COMPOSED_BASES[base]
        glyphs[base + accent] = (code, stacked_letter(letter, glyphs[base][1], accent, base[len(letter):]))
        like[base + accent] = letter
    for letter, upper_code, lower_code in HORNED:
        for each, code in ((letter, upper_code), (letter.lower(), lower_code)):
            glyphs[each + "horn"] = (code, horned(each))
            like[each + "horn"] = each
    for base, accent, upper_code in VIETNAMESE:
        for each, code in ((base, upper_code), (base[0].lower() + base[1:], upper_code + 1)):
            letter = ROOTS.get(each, each)
            glyphs[vietnamese_name(each, accent)] = (code, vietnamese(each, letter, accent, glyphs))
            like[vietnamese_name(each, accent)] = letter
    for name, (code, accent) in TOP_MARKS.items():
        glyphs[name] = (code, mark_of(ACCENTS[accent], small))
        glyphs[name + CASE] = (None, mark_of(ACCENTS[accent], tall))
        glyphs[name + CASE + STACK] = (None, mark_of(ACCENTS[accent], stacking(tall)))
        if name in PRESSED_MARKS:
            glyphs[name + CASE + PRESS] = (None, mark_of(ACCENTS[accent], pressing(tall)))
    for name, (code, accent) in TOP_MARKS.items():
        if accent not in SAME_ON_I:
            glyphs[name + NARROW] = (None, mark_of(ACCENTS[accent], tier_for("i")))
            glyphs[name + CASE + NARROW] = (None, mark_of(ACCENTS[accent], tier_for("I")))
    glyphs["acutecomb" + KRESKA] = (None, mark_of(kreska, small))
    glyphs["acutecomb" + CASE + KRESKA] = (None, mark_of(kreska, tall))
    glyphs[CARON_ALT] = (None, caron_tick)
    glyphs[CARON_SHORT] = (None, short_tick)
    for name, (code, hook, _) in BELOW_MARKS.items():
        glyphs[name] = (code, hook_mark(hook, small_neck, small_scale))
        glyphs[name + CASE] = (None, hook_mark(hook, cap_neck, cap_scale))
    for name, code in HORN_MARKS.items():
        glyphs[name] = (code, horn_mark(False))
        glyphs[name + CASE] = (None, horn_mark(True))
    for name, (_, _, accent) in LIGATED_MARKS.items():
        glyphs[name] = (None, mark_of(ACCENTS[accent], small))
        glyphs[name + CASE] = (None, mark_of(ACCENTS[accent], tall))
    return glyphs, like


COMPOSED_BASES = {f"{letter}{mark}": letter for letter, mark, _ in accented()}
ROOTS = dict(COMPOSED_BASES)
ROOTS.update({each + "horn": each for letter, _, _ in HORNED for each in (letter, letter.lower())})
GLYPHS, KERN_LIKE = register()
COMPOSED = {f"{letter}{mark}": (letter, mark) for letter, mark, _ in accented()}
COMPOSED.update({base + accent: (base, accent) for base, accent, _ in ON_DRAWN + STACKED})
COMPOSED.update({each + "horn": (each, "horn") for letter, _, _ in HORNED for each in (letter, letter.lower())})
COMPOSED.update(
    {vietnamese_name(each, accent): (each, accent) for base, accent, _ in VIETNAMESE for each in (base, base[0].lower() + base[1:])}
)


def ink_right(glyph, floor):
    return max(point[0] for contour in glyph.contours for point in contour.points() if point[1] >= floor)


def ink_left(glyph, floor):
    return min(point[0] for contour in glyph.contours for point in contour.points() if point[1] >= floor)


def drawn(name, master):
    from .glyphs import GLYPHS as everything
    from .glyphs import stays_upright

    if name in GLYPHS:
        return finished(GLYPHS[name][1], master, stays_upright(name))
    if len(name) == 1:
        return finished(base_of(name), master, stays_upright(name))
    return finished(everything[name][1], master, stays_upright(name))


def outline(glyph, step=2):
    for contour in glyph.contours:
        here = contour.start
        for segment in closed_segments(contour):
            bezier = (here, *segment) if len(segment) == 3 else (here, here, segment[0], segment[0])
            count = max(2, int(math.dist(here, segment[-1]) / step) + 1)
            for index in range(count):
                yield point_at(bezier, index / count)
            here = segment[-1]


def outline_array(glyph, step=2):
    parts = []
    for contour in glyph.contours:
        here = contour.start
        for segment in closed_segments(contour):
            (x0, y0), (x1, y1), (x2, y2), (x3, y3) = (here, *segment) if len(segment) == 3 else (here, here, segment[0], segment[0])
            count = max(2, int(math.dist(here, segment[-1]) / step) + 1)
            t = numpy.arange(count) / count
            u = 1 - t
            a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
            parts.append(numpy.stack([a * x0 + b * x1 + c * x2 + d * x3, a * y0 + b * y1 + c * y2 + d * y3], axis=1))
            here = segment[-1]
    return numpy.concatenate(parts) if parts else numpy.zeros((0, 2))


def profile(glyph, edge, floor):
    points = outline_array(glyph)
    points = points[points[:, 1] >= floor]
    if not len(points):
        return {}
    bands = numpy.round(points[:, 1] / PROFILE_BAND).astype(int)
    reach = -points[:, 0] if edge is max else points[:, 0]
    order = numpy.lexsort((numpy.arange(len(points)), reach, bands))
    first = numpy.ones(len(order), dtype=bool)
    first[1:] = bands[order][1:] != bands[order][:-1]
    chosen = order[first]
    return {int(band): (float(x), float(y)) for band, (x, y) in zip(bands[chosen], points[chosen])}


def profile_arrays(extremes):
    bands = numpy.array(list(extremes), dtype=int)
    places = numpy.array(list(extremes.values()), dtype=float).reshape(-1, 2)
    return bands, places


def top_of(glyph):
    return max(point[1] for contour in glyph.contours for point in contour.points())


def mark_floor(capital):
    return (CAP if capital else XH) + OV + 4


def raised(master, capital=False):
    floor = mark_floor(capital)
    marked = {}
    for name, kin in KERN_LIKE.items():
        if COMPOSED.get(name, (None, None))[1] in BELOW_HOOKS:
            continue
        if kin[0].isupper() == capital and top_of(drawn(kin, master)) < floor:
            glyph = drawn(name, master)
            if top_of(glyph) > floor:
                marked[name] = (kin, glyph)
    return marked


def pair_kern(kerning, left, right, master):
    right = KERN_LIKE.get(right, right)
    return kerning.pair_value(KERN_LIKE.get(left, left), LIGATURE_LEFT.get(right, right), master)


def closest_kern(left, right, gap, left_floor=None, right_floor=None, measure=profile):
    floor = XH + OV + 4
    left_floor = floor - gap if left_floor is None else left_floor
    right_floor = floor if right_floor is None else right_floor
    ink = measure(left, max, left_floor)
    mark = measure(right, min, right_floor)
    if not ink or not mark:
        return None
    return closest_between(profile_arrays(ink), profile_arrays(mark), left.advance, gap)


def closest_between(ink, mark, advance, gap):
    reach = round(gap / PROFILE_BAND) + 1
    ink_bands, ink_places = ink
    mark_bands, mark_places = mark
    if not len(ink_bands) or not len(mark_bands):
        return None
    near = numpy.abs(ink_bands[None, :] - mark_bands[:, None]) <= reach
    rise = ink_places[None, :, 1] - mark_places[:, None, 1]
    near &= numpy.abs(rise) < gap
    if not near.any():
        return None
    with numpy.errstate(invalid="ignore"):
        kern = ink_places[None, :, 0] - advance - mark_places[:, None, 0] + numpy.sqrt(gap * gap - rise * rise)
    return float(kern[near].max())


def neighbours(kerning, marked):
    names = [member for group in OVERHANGS for member in kerning.FIRST[group]]
    names += [name for name, kin in KERN_LIKE.items() if any(kin in kerning.FIRST[group] for group in OVERHANGS)]
    names += list(RISERS) + [name for name, kin in KERN_LIKE.items() if kin in RISERS]
    names += [name for name, (kin, _) in marked.items() if kin in RISERS]
    return list(dict.fromkeys(names))


def capital_neighbours():
    names = [letter.upper() for letter in LETTERS]
    names += [name for name, kin in KERN_LIKE.items() if kin.isupper()]
    return list(dict.fromkeys(names))


def cached_profile():
    measured = {}
    kept = []

    def measure(glyph, edge, floor):
        key = (id(glyph), edge, floor)
        if key not in measured:
            kept.append(glyph)
            measured[key] = profile(glyph, edge, floor)
        return measured[key]

    return measure


@lru_cache(maxsize=None)
def clearance(master, kerning):
    gap = master.v(*ACCENT_CLEARANCE)
    found = {}
    measure = cached_profile()

    def settle(first, second, left, right, left_floor, right_floor):
        marked_name = second if second in KERN_LIKE else first
        room = gap + (master.v(*SIDE_MARK_MARGIN) if COMPOSED.get(marked_name, (None, ""))[1].startswith("circumflex_") else 0)
        room += DOTTED_MARK_MARGIN if COMPOSED.get(marked_name, ("", ""))[0] in DOTTED + ("I", "J") else 0
        needed = closest_kern(left, right, room, left_floor, right_floor, measure)
        if needed is None:
            return
        value = pair_kern(kerning, first, second, master)
        found[(first, second)] = max(value, needed) - value

    for capital in (False, True):
        floor = mark_floor(capital)
        marked = raised(master, capital)
        names = capital_neighbours() if capital else neighbours(kerning, marked)
        for name in names:
            neighbour = drawn(name, master)
            both_ways = capital or name in RISERS or KERN_LIKE.get(name) in RISERS
            for mark_name, (_, glyph) in marked.items():
                settle(name, mark_name, neighbour, glyph, floor - gap, floor)
                if both_ways:
                    settle(mark_name, name, glyph, neighbour, floor, floor - gap)
    return found


def clearance_pairs(master, kerning):
    deltas = {each: clearance(each, kerning) for each in family(master)}
    needed = set()
    for found in deltas.values():
        needed.update(pair for pair, delta in found.items() if round(delta) >= SMALLEST_KERN)
    found = clearance(master, kerning)
    return [f"    pos {first} {second} {round(found.get((first, second), 0))};" for first, second in sorted(needed)]


def ligature_pairs(master, kerning):
    lines = []
    ligatures = dict(LIGATURE_LEFT)
    ligatures.update({name: LIGATURE_LEFT[kin] for name, kin in KERN_LIKE.items() if kin in LIGATURE_LEFT})
    for first, second, regular, bold in kerning.PAIRS:
        for name, kin in ligatures.items():
            if second == kin:
                lines.append(f"    pos @first_{first} {name} {kerning.class_kern(first, second, regular, bold, master)};")
    return lines


def is_capital(name):
    from .glyphs import GLYPHS as everything

    return unicodedata.category(chr(everything[name][0])) == "Lu"


def base_letters():
    from .glyphs import GLYPHS as everything

    letters = [name for name, (code, _) in everything.items() if code is not None and unicodedata.category(chr(code)) in ("Lu", "Ll")]
    return letters + list(MARK_BASES)


def upright(name, master):
    from .glyphs import GLYPHS as everything

    return everything[name][1](master)


def band_centre(glyph, floor):
    points = outline_array(glyph)
    xs = points[points[:, 1] >= floor][:, 0]
    return (xs.min() + xs.max()) / 2


@lru_cache(maxsize=None)
def shape_of(name):
    from .glyphs import EXTENSIONS

    for extension in EXTENSIONS:
        if name in extension.KERN_LIKE:
            return extension.KERN_LIKE[name]
    return name


def top_x(letter, glyph, m, capital):
    shape = shape_of(letter)
    stem = STEM_TOPS.get(letter, STEM_TOPS.get(shape))
    if stem is not None:
        return whole(band_centre(glyph, stem))
    if not capital and top_of(glyph) > XH + m.ov + 1:
        return whole(band_centre(glyph, XH + m.ov + 4))
    left, right = body_bounds(glyph) if m.italic and shape in EXIT_STROKES else bounds(glyph.contours)
    return whole((left + right) / 2 + m.v(*NUDGES.get(shape, (0, 0))))


def body_bounds(glyph):
    runs = [run for share in BODY_HEIGHTS for run in ink_runs(glyph.contours, XH * share)]
    if not runs:
        return bounds(glyph.contours)
    return min(run[0] for run in runs), max(run[1] for run in runs)


def stacked(top, m, capital):
    tier = tall(m) if capital else small(m)
    return top + stack_gap(m, capital) - (tier.floor - (CAP if capital else XH))


ASCENDER_TUCK = 26
BODY_HEIGHTS = (0.3, 0.5, 0.7, 0.9)
EXIT_STROKES = {"a", "n", "u", "uni0430", "uni0438", "uni0448"}


def top_height(glyph, capital):
    if capital:
        return CAP
    top = top_of(glyph)
    return XH if top <= XH + TOP_OV + 1 else min(top, ASC - ASCENDER_TUCK)


def polyline(contour):
    return outline_array(Glyph([contour.oriented()], 0))


def ink_runs(contours, y):
    crossings = []
    for contour in contours:
        points = polyline(contour)
        following = numpy.roll(points, -1, axis=0)
        below, after = points[:, 1] <= y, following[:, 1] <= y
        for (x0, y0), (x1, y1) in zip(points[below != after], following[below != after]):
            crossings.append((x0 + (y - y0) * (x1 - x0) / (y1 - y0), 1 if y1 > y0 else -1))
    runs = []
    winding = 0
    start = None
    for x, turn in sorted(crossings):
        before, winding = winding, winding + turn
        if not before and winding:
            start = x
        elif before and not winding:
            runs.append((start, x))
    return runs


def cedilla_x(letter, glyph, m, capital):
    left, right = bounds(glyph.contours)
    x = (left + right) / 2 - m.v(*CEDILLA_NUDGE)
    neck = (cap_neck if capital else small_neck)(m)
    half = m.v(*CEDILLA_NECK) / 2
    runs = ink_runs(glyph.contours, neck / 2)
    if letter in "cC" or not runs or any(start <= x - half and x + half <= end for start, end in runs):
        return whole(x)
    start, end = min(runs, key=lambda run: (abs((run[0] + run[1]) / 2 - x), run[0]))
    return whole((start + end) / 2)


def dotbelow_x(glyph, m):
    side = small(m).dot
    gap = m.v(*DOT_BELOW_GAP)
    x = (bounds(glyph.contours)[0] + bounds(glyph.contours)[1]) / 2
    middle = [-gap - side / 2]
    for levels in (middle, [-gap - side * step / DOT_BELOW_LEVELS for step in range(DOT_BELOW_LEVELS + 1)]):
        start_x = x
        for start, end in sorted(run for y in levels for run in ink_runs(glyph.contours, y)):
            if start - gap < x + side / 2 and x - side / 2 < end + gap:
                x = max(x, end + gap + side / 2)
        if x == start_x:
            break
    return whole(x)


def horn_point(glyph, m, capital):
    height = (CAP if capital else XH) * HORN_HEIGHT
    runs = ink_runs(glyph.contours, height)
    right = runs[-1][1] if runs else bounds(glyph.contours)[1]
    return whole(right - m.v(*HORN_INSET)), whole(height)


def comma_x(glyph):
    left, right = bounds(glyph.contours)
    return whole((left + right) / 2)


def ogonek_x(glyph, m, capital):
    neck = (cap_neck if capital else small_neck)(m)
    runs = ink_runs(glyph.contours, neck / 2)
    start, end = runs[-1]
    return whole(end - min(m.v(*OGONEK_INSET), (end - start) / 2))


def mark_twins():
    from .glyphs import EXTENSIONS

    return {twin: model for extension in EXTENSIONS for twin, model in getattr(extension, "MARK_TWINS", {}).items()}


@lru_cache(maxsize=None)
def base_anchors(master):
    anchors = {}
    twins = mark_twins()
    for name in base_letters() + list(twins):
        capital = is_capital(twins.get(name, name))
        glyph = upright(name, master)
        letter, mark = COMPOSED.get(name, (name, None))
        plain = upright(letter, master) if letter != name else glyph
        if letter in ("i", "j"):
            plain = upright(f"dotless{letter}", master)
        x = top_x(f"dotless{letter}" if letter in ("i", "j") else letter, plain, master, capital)
        if mark in ACCENTS or letter in ("i", "j"):
            top = (x, stacked(top_of(glyph), master, capital))
            dots = top
        else:
            top = (x, top_height(glyph, capital) + whole(master.v(*LETTER_LIFTS.get(shape_of(letter), (0, 0)))))
            lift = master.v(*(CAP_ROUND_LIFT if capital else ROUND_LIFT)) if shape_of(letter) in ROUND_TOPS else 0
            if shape_of(letter) in ASCENDED:
                lift = master.v(*ASCENDER_DOT_LIFT)
            dots = (x, top[1] + whole(lift))
        found = {"top": top, "dots": dots}
        if mark not in BELOW_HOOKS:
            found["bottom"] = (cedilla_x(letter, plain, master, capital), 0)
            found["ogonek"] = (ogonek_x(plain, master, capital), 0)
            found["comma"] = (comma_x(plain), 0)
            found["dotbelow"] = (dotbelow_x(plain, master), 0)
        if mark != "horn":
            found["horn"] = horn_point(plain, master, capital)
        if name in CARON_BASES:
            found["caron"] = caron_anchor(name, glyph, master)
        anchors[name] = found
    return anchors


def caron_anchor(name, glyph, m):
    top = top_of(glyph)
    start, end = ink_runs(glyph.contours, top - m.stem / 2)[0]
    x = whole(end + m.v(*CARON_GAP) + (m.v(*CARON_ITALIC_GAP) if m.italic else 0))
    if name in SHORT_CARON_BASES:
        return (x, whole(XH + m.v(*CARON_FOOT) + short_wedge_size(m)[1]))
    return (x, min(top, ASC))


def caron_room(master):
    lines = []
    for name in CARON_BASES:
        room = caron_room_for(name, upright(name, master), master)
        lines.append(f"    pos {name}' <0 0 {room} 0> {CARON_SHORT if name in SHORT_CARON_BASES else CARON_ALT};")
    return lines


@lru_cache(maxsize=None)
def mark_names():
    found = {}
    for name, (_, accent) in TOP_MARKS.items():
        kind = "dots" if accent in DOT_ACCENTS else "top"
        found[name] = (kind, False)
        found[name + CASE] = (kind, True)
        found[name + CASE + STACK] = (kind, True)
        if name in PRESSED_MARKS:
            found[name + CASE + PRESS] = (kind, True)
        if accent not in SAME_ON_I:
            found[name + NARROW] = (kind, False)
            found[name + CASE + NARROW] = (kind, True)
    for name, (_, _, kind) in BELOW_MARKS.items():
        found[name] = (kind, False)
        found[name + CASE] = (kind, True)
    for name in HORN_MARKS:
        found[name] = ("horn", False)
        found[name + CASE] = ("horn", True)
    for name in LIGATED_MARKS:
        found[name] = ("top", False)
        found[name + CASE] = ("top", True)
    found["acutecomb" + KRESKA] = ("top", False)
    found["acutecomb" + CASE + KRESKA] = ("top", True)
    found[CARON_ALT] = ("caron", False)
    found[CARON_SHORT] = ("caron", False)
    return found


@lru_cache(maxsize=None)
def mark_anchors(master):
    anchors = {}
    for name, (kind, capital) in mark_names().items():
        if kind in BELOW_KINDS:
            anchors[name] = ((0, 0), None)
            continue
        if kind == "caron":
            anchors[name] = ((0, ASC), None)
            continue
        glyph = upright(name, master)
        attach = (0, CAP if capital else XH)
        closer = stack_gap(master, capital) * (1 - master.v(*STACK_PRESS_GAP)) if name.endswith(PRESS) else 0
        anchors[name] = (attach, (0, stacked(top_of(glyph), master, capital) - closer))
    return anchors


def anchor_at(point, master):
    x, y = point
    return whole(x + master.slope * (y - ORIGIN)), whole(y)


def anchor(point, master):
    x, y = anchor_at(point, master)
    return f"<anchor {x} {y}>"


def top_mark_on(base, mark):
    name = mark + (CASE if is_capital(base) else "")
    if base in NARROW_BASES and name + NARROW in mark_names():
        name += NARROW
    return name


def marks_on(base):
    found = [top_mark_on(base, name) for name in TOP_MARKS]
    if base in KRESKA_BASES:
        found.append(top_mark_on(base, "acutecomb") + KRESKA)
    return found


def kreska_feature():
    lower = [name for name in KRESKA_BASES if name.islower()]
    upper = [name for name in KRESKA_BASES if name.isupper()]
    return [
        "lookup kreska_mark {",
        f"    sub acutecomb by acutecomb{KRESKA};",
        f"    sub acutecomb{CASE} by acutecomb{CASE}{KRESKA};",
        "} kreska_mark;",
        "feature locl {",
        "    script latn;",
        "    language PLK;",
        "    lookup kreska_letters {",
        *[f"        sub {name}acute by {name} {top_mark_on(name, 'acutecomb')}{KRESKA};" for name in KRESKA_BASES],
        "    } kreska_letters;",
        "    lookup kreska_marks {",
        f"        sub [{' '.join(lower)}] acutecomb' lookup kreska_mark;",
        f"        sub [{' '.join(upper)}] acutecomb{CASE}' lookup kreska_mark;",
        "    } kreska_marks;",
        "} locl;",
    ]


def language_feature():
    accents_above = " ".join(LITHUANIAN_ACCENTS)
    lines = [
        "lookup lithuanian_dot {",
        "    sub i by i dotaccentcomb;",
        "    sub j by j dotaccentcomb;",
        "    sub iogonek by i ogonekcomb dotaccentcomb;",
        "} lithuanian_dot;",
        "lookup comma_below_letters {",
        f"    sub [{' '.join(CEDILLA_PAIRS)}] by [{' '.join(CEDILLA_PAIRS.values())}];",
        "} comma_below_letters;",
        "lookup comma_below_marks {",
        "    sub [S s T t] cedillacomb' by commaaccentcomb;",
        "} comma_below_marks;",
        "lookup dutch_acute {",
        "    sub j by j acutecomb;",
        "    sub J by J acutecomb;",
        "} dutch_acute;",
        "feature locl {",
        "    script latn;",
        "    language LTH;",
        "    lookup lithuanian_soft_dot {",
        f"        sub [i j iogonek]' lookup lithuanian_dot [{accents_above}];",
        "    } lithuanian_soft_dot;",
        "    language NLD;",
        "    lookup dutch_ij {",
        "        sub [iacute Iacute] [j J]' lookup dutch_acute;",
        "        sub [i I] acutecomb [j J]' lookup dutch_acute;",
        "    } dutch_ij;",
    ]
    for language in COMMA_LANGUAGES:
        lines += [f"    language {language};", "    lookup comma_below_letters;", "    lookup comma_below_marks;"]
    return lines + ["} locl;"]


def cyrillic_descender(draw, capital):
    def build(m):
        from . import cyrillic

        glyph = draw(m)
        sz = cyrillic.size(m, capital)
        foot, depth = cyrillic.spur(m, sz)
        contours = list(glyph.contours)
        legs = []
        for index, contour in enumerate(contours):
            corners = list(contour.corners())
            for position, segment in enumerate(contour.segments):
                if len(segment) == 1 and segment[0][1] == 0 and corners[position][0] == segment[0][0] and corners[position][1] > sz.bar:
                    legs.append((segment[0][0], index, position))
        right, index, position = max(legs)
        contour = contours[index]
        tail = [(right, sz.bar), (right + foot, sz.bar), (right + foot, depth), (right, depth), (right, 0)]
        segments = contour.segments[:position] + [(point,) for point in tail] + contour.segments[position + 1 :]
        contours[index] = Contour(contour.start, segments, contour.hole)
        advance = right + foot + cyrillic.pick(m, sz, *cyrillic.SPUR_RIGHT) + m.track + parts.opening(m, capital)
        return Glyph(contours, advance)

    return build


def cyrillic_supplement():
    from . import cyrillic

    return {
        "uni0524": (0x524, cyrillic_descender(lambda m: cyrillic.pe(m, True), True)),
        "uni0525": (0x525, cyrillic_descender(lambda m: cyrillic.pe(m, False), False)),
        "uni0526": (0x526, cyrillic_descender(cyrillic.shha, True)),
        "uni0527": (0x527, cyrillic_descender(lowercase.letter_h, False)),
        "uni052E": (0x52E, cyrillic_descender(lambda m: cyrillic.el(m, True), True)),
        "uni052F": (0x52F, cyrillic_descender(lambda m: cyrillic.el(m, False), False)),
    }


def mark_offset(base, mark, master):
    kind = mark_names()[mark][0]
    bx, by = anchor_at(base_anchors(master)[base][kind], master)
    mx, my = anchor_at(mark_anchors(master)[mark][0], master)
    return bx - mx, by - my


@lru_cache(maxsize=None)
def sequence_bases(master):
    from .glyphs import EXTENSIONS

    render = rendered
    own = {name for extension in EXTENSIONS if getattr(extension, "OWN_MARKS", False) for name in extension.GLYPHS}
    found = []
    for name in base_letters():
        if name in COMPOSED or name in DOTTED or name in own:
            continue
        floor = mark_floor(is_capital(name))
        if all(top_of(render(name, each)) < floor for each in family(master)):
            found.append(name)
    return found


@lru_cache(maxsize=None)
def rendered(name, master):
    from .glyphs import render

    return render(name, master)


@lru_cache(maxsize=None)
def sequence_clearance(master, kerning):
    render = rendered
    gap = master.v(*ACCENT_CLEARANCE)
    found = {}
    for base in sequence_bases(master):
        capital = is_capital(base)
        floor = mark_floor(capital)
        plain = render(base, master)
        reading = lambda name, edge, low, dy=0: edge_arrays(name, master, edge, low, dy)
        lefts = capital_letters() if capital else list(dict.fromkeys(member for group in OVERHANGS for member in kerning.FIRST[group]))
        rights = capital_letters() if capital else list(RISERS)
        marks = []
        for mark in marks_on(base):
            dx, dy = mark_offset(base, mark, master)
            marks.append((mark, dx, reading(mark, min, floor - dy, dy), reading(mark, max, floor - dy, dy)))
        for neighbour in dict.fromkeys(lefts + rights):
            other = render(neighbour, master)
            if neighbour in lefts:
                ink = reading(neighbour, max, floor - gap)
                bare = closest_between(ink, reading(base, min, floor), other.advance, gap)
                value = pair_kern(kerning, neighbour, base, master)
                for mark, dx, left_edge, _ in marks:
                    topped = shifted_kern(closest_between(ink, left_edge, other.advance, gap), -dx)
                    keep_needed(found, ("left", neighbour, base, mark), (bare, topped), value)
            if neighbour in rights:
                ink = reading(neighbour, min, floor - gap)
                bare = closest_between(reading(base, max, floor), ink, plain.advance, gap)
                value = pair_kern(kerning, base, neighbour, master)
                for mark, dx, _, right_edge in marks:
                    topped = shifted_kern(closest_between(right_edge, ink, 0, gap), dx - plain.advance)
                    keep_needed(found, ("right", neighbour, base, mark), (bare, topped), value)
    return found


def edge_arrays(name, master, edge, floor, dy=0):
    bands, places = edge_profile(name, master, edge, whole(floor))
    if dy:
        places = places + (0, dy)
        bands = numpy.round(places[:, 1] / PROFILE_BAND).astype(int)
    return bands, places


@lru_cache(maxsize=None)
def edge_profile(name, master, edge, floor):
    found = profile(rendered(name, master), edge, floor)
    return profile_arrays(found) if found else (numpy.zeros(0, dtype=int), numpy.zeros((0, 2)))


def shifted_kern(kern, dx):
    return None if kern is None else kern + dx


def keep_needed(found, key, parts, value):
    needed = [part for part in parts if part is not None]
    if needed:
        found[key] = max(value, max(needed)) - value


def capital_letters():
    return [letter.upper() for letter in LETTERS if letter.isalpha()]


def family_values(master, compute):
    members = family(master)
    return members.index(master), {each: compute(each) for each in members}


def sequence_rules(master, kerning):
    here, found = family_values(master, lambda each: sequence_clearance(each, kerning))
    members = list(found)
    keys = sorted({key for deltas in found.values() for key, delta in deltas.items() if round(delta) >= SMALLEST_KERN})
    by_base = {}
    for side, neighbour, base, mark in keys:
        values = tuple(round(found[each].get((side, neighbour, base, mark), 0)) for each in members)
        by_base.setdefault((side, neighbour, base, values), []).append(mark)
    rules = {}
    for (side, neighbour, base, values), marks in by_base.items():
        rules.setdefault((side, neighbour, tuple(marks), values), []).append(base)
    placed = []
    for (side, neighbour, marks, values), bases in sorted(rules.items()):
        moved = (neighbour,) if side == "left" else tuple(bases)
        placed.append((side, neighbour, bases, marks, moved, values[here]))
    return placed


def slotted(rules, prefix):
    slots = []
    lines = []
    for side, neighbour, bases, marks, moved, value in rules:
        index = next((index for index, used in enumerate(slots) if not used & set(moved)), len(slots))
        if index == len(slots):
            slots.append(set())
        slots[index] |= set(moved)
        lines.append((index, side, neighbour, bases, marks, moved, value))
    lookups = []
    for index in range(len(slots)):
        lookups.append(f"lookup {prefix}_{index} {{")
        lookups += [f"    pos {glyph_set(moved)} {value};" for slot, _, _, _, _, moved, value in lines if slot == index]
        lookups.append(f"}} {prefix}_{index};")
    return lookups, lines


def glyph_set(names):
    return names[0] if len(names) == 1 else f"[{' '.join(names)}]"


def sequence_feature(master, kerning):
    lookups, lines = slotted(sequence_rules(master, kerning), "accent_room")
    rules = []
    for index, side, neighbour, bases, marks, _, _ in lines:
        if side == "left":
            rules.append(f"        pos {neighbour}' lookup accent_room_{index} {glyph_set(bases)} {glyph_set(marks)};")
        else:
            rules.append(f"        pos {glyph_set(bases)}' lookup accent_room_{index} {glyph_set(marks)} {neighbour};")
    return lookups, rules


def lettered(kerning):
    letters = set(base_letters())
    return [name for name, members in kerning.FIRST.items() if any(member in letters for member in members)]


def across_feature(master, kerning):
    firsts = lettered(kerning)
    counts = {}
    entries = []
    for first, second, regular, bold in kerning.PAIRS:
        if first in firsts and first not in kerning.MARKLESS and second not in kerning.MARKLESS:
            index = counts.get(first, 0)
            counts[first] = index + 1
            entries.append((index, first, second, kerning.class_kern(first, second, regular, bold, master)))
    lookups = []
    for index in range(max(counts.values(), default=0)):
        lookups.append(f"lookup accent_across_{index} {{")
        lookups += [f"    pos @first_{first} {value};" for slot, first, _, value in entries if slot == index]
        lookups.append(f"}} accent_across_{index};")
    rules = []
    for index, first, second, _ in entries:
        rules.append(f"        pos @first_{first}' lookup accent_across_{index} @comb_any @second_{second};")
        rules.append(f"        pos @first_{first}' lookup accent_across_{index} @comb_any @comb_any @second_{second};")
    return lookups, rules


def mark_feature(master):
    marks = mark_anchors(master)
    kinds = mark_names()
    lines = [f"markClass {name} {anchor(attach, master)} @mark_{kinds[name][0]};" for name, (attach, _) in marks.items()]
    lines.append("feature mark {")
    for name, found in base_anchors(master).items():
        listed = " ".join(f"{anchor(point, master)} mark @mark_{kind}" for kind, point in found.items())
        lines.append(f"    pos base {name} {listed};")
    lines.append("} mark;")
    lines.append("feature mkmk {")
    for name, (_, stack) in marks.items():
        if stack:
            lines.append(f"    pos mark {name} {anchor(stack, master)} mark @mark_top {anchor(stack, master)} mark @mark_dots;")
    lines.append("} mkmk;")
    return lines


def composition_feature():
    kinds = mark_names()
    top = [name for name in TOP_MARKS]
    below = list(BELOW_MARKS) + list(HORN_MARKS)
    narrowable = [name for name in top if name + NARROW in kinds]
    case_top = [name + CASE for name in top] + [name + CASE + NARROW for name in narrowable]
    uppercase = [name for name in base_letters() if is_capital(name)]
    group = " ".join
    return [
        f"@comb_top = [{group(top)}];",
        f"@comb_below = [{group(below)}];",
        f"@comb_below_case = [{group(name + CASE for name in below)}];",
        f"@comb_narrowable = [{group(narrowable)}];",
        f"@comb_case_top = [{group(case_top)}];",
        f"@comb_capitals = [{group(uppercase)}];",
        f"@comb_case_plain = [{group(name + CASE for name in top)}];",
        f"@comb_case_stack = [{group(name + CASE + STACK for name in top)}];",
        f"@comb_case_narrow = [{group(name + CASE + NARROW for name in narrowable)}];",
        "lookup comb_split_soft {",
        "    sub iogonek by dotlessi ogonekcomb;",
        "    sub idotbelow by dotlessi dotbelowcomb;",
        "} comb_split_soft;",
        "lookup comb_dotless {",
        "    sub i by dotlessi;",
        "    sub j by dotlessj;",
        "} comb_dotless;",
        "lookup comb_narrow {",
        f"    sub @comb_narrowable by [{group(name + NARROW for name in narrowable)}];",
        "} comb_narrow;",
        "lookup comb_case_narrow {",
        f"    sub @comb_narrowable by [{group(name + CASE + NARROW for name in narrowable)}];",
        "} comb_case_narrow;",
        "lookup comb_caron_alt {",
        f"    sub caroncomb by {CARON_ALT};",
        "} comb_caron_alt;",
        "lookup comb_caron_short {",
        f"    sub caroncomb by {CARON_SHORT};",
        "} comb_caron_short;",
        "lookup comb_comma {",
        "    sub cedillacomb by commaaccentcomb;",
        "} comb_comma;",
        "lookup comb_turned {",
        "    sub cedillacomb by commaturnedcomb;",
        "} comb_turned;",
        "lookup comb_stack {",
        "    sub @comb_case_plain by @comb_case_stack;",
        "} comb_stack;",
        "lookup comb_press {",
        *[f"    sub {name}{CASE}{STACK} by {name}{CASE}{PRESS};" for name in PRESSED_MARKS],
        "} comb_press;",
        "lookup comb_case {",
        f"    sub [{group(top + below)}] by [{group(name + CASE for name in top + below)}];",
        "} comb_case;",
        "feature ccmp {",
        "    lookup comb_soft_dots {",
        "        sub [i j]' lookup comb_dotless @comb_top;",
        "        sub [i j]' lookup comb_dotless @comb_below @comb_top;",
        "        sub [i j]' lookup comb_dotless @comb_below @comb_below @comb_top;",
        "        sub [iogonek idotbelow]' lookup comb_split_soft @comb_top;",
        "        sub [iogonek idotbelow]' lookup comb_split_soft @comb_below @comb_top;",
        "        sub [iogonek idotbelow]' lookup comb_split_soft @comb_below @comb_below @comb_top;",
        "    } comb_soft_dots;",
        "    lookup comb_latvian {",
        f"        sub [{group(LATVIAN_COMMAS)}] cedillacomb' lookup comb_comma;",
        "        sub g cedillacomb' lookup comb_turned;",
        "    } comb_latvian;",
        "    lookup comb_caron {",
        f"        sub [{group(name for name in CARON_BASES if name not in SHORT_CARON_BASES)}] caroncomb' lookup comb_caron_alt;",
        f"        sub [{group(SHORT_CARON_BASES)}] caroncomb' lookup comb_caron_short;",
        "    } comb_caron;",
        "    lookup comb_on_i {",
        "        sub [dotlessi dotlessj] @comb_narrowable' lookup comb_narrow;",
        "        sub [dotlessi dotlessj] @comb_below @comb_narrowable' lookup comb_narrow;",
        "        sub I @comb_narrowable' lookup comb_case_narrow;",
        "        sub I @comb_below @comb_narrowable' lookup comb_case_narrow;",
        "    } comb_on_i;",
        "    lookup comb_on_capitals {",
        "        sub @comb_capitals [@comb_top @comb_below]' lookup comb_case;",
        "        sub @comb_capitals @comb_below_case @comb_top' lookup comb_case;",
        "        sub @comb_capitals @comb_below_case @comb_below' lookup comb_case;",
        "        sub @comb_case_top @comb_top' lookup comb_case;",
        "    } comb_on_capitals;",
        "    lookup comb_vietnamese {",
        *[f"        sub {first} {second} by {name};" for name, (first, second, _) in LIGATED_MARKS.items()],
        *[f"        sub {first}{CASE} {second}{CASE} by {name}{CASE};" for name, (first, second, _) in LIGATED_MARKS.items()],
        "    } comb_vietnamese;",
        "    lookup comb_capital_stacks {",
        "        sub @comb_case_plain' lookup comb_stack @comb_case_plain;",
        "        sub [@comb_case_stack @comb_case_narrow] @comb_case_plain' lookup comb_stack;",
        "    } comb_capital_stacks;",
        "    lookup comb_capital_press {",
        *[f"        sub {name}{CASE}{STACK}' lookup comb_press [{group(name + CASE + STACK for name, (_, accent) in TOP_MARKS.items() if accent in PRESSED_ACCENTS)}];" for name in PRESSED_MARKS],
        "    } comb_capital_press;",
        "} ccmp;",
    ]


def glyph_classes():
    from .glyphs import GLYPHS as everything

    marks = set(mark_names())
    bases = [name for name in everything if name not in marks and name != ".notdef"]
    return [
        "table GDEF {",
        f"    GlyphClassDef [{' '.join(bases)}], , [{' '.join(name for name in everything if name in marks)}], ;",
        "} GDEF;",
    ]


def features(master):
    from . import features as kerning

    lines = ligature_pairs(master, kerning) + clearance_pairs(master, kerning) + caron_room(master)
    room_lookups, room_rules = sequence_feature(master, kerning)
    across_lookups, across_rules = across_feature(master, kerning)
    lines += ["    lookup accent_sequences {"] + room_rules + ["    } accent_sequences;"]
    lines += ["    lookup accent_across {"] + across_rules + ["    } accent_across;"]
    layout = glyph_classes() + language_feature() + composition_feature() + mark_feature(master)
    layout += [f"@comb_any = [{' '.join(mark_names())}];"] + room_lookups + across_lookups + kreska_feature()
    return "\n".join(layout) + "\nfeature kern {\n" + "\n".join(lines) + "\n} kern;"
