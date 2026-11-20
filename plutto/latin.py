import math

from . import accents, capitals, lowercase, marks
from .figures import terminal_high
from .geometry import Path, across, intersect
from .masters import ASC, CAP, DESC, XH
from .parts import HOOK_SPREAD, Glyph, band, band_width, hook, kay, shoulder_inner, shoulder_spring, spaced
from .shapes import Node, aim, mirror, place, polygon, rect, ribbon, shift, turn

DOWN = (0, -1)
UP = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
HOOK_TIP = 3
HOOK_DEPTH = 1.15
HOOK_BELLY = 1.25
OPEN_E_WAIST = 0.54
ASCENDER_HOOK = (118, 128, 110, 136)
CAPITAL_HOOK = (108, 120, 100, 128)
ARM_CROWN = (0.9, 0.8)
ARM_TURN = 0.9
ARM_NOTCH = (40, 44, 40, 48)
ARM_THIN = (1, 0.92, 1, 0.8)
ARM_REACH = (54, 60)
SMALL_ARM_RISE = (70, 86, 64, 104)
CAP_ARM_OVERLAP = (40, 44)
CAP_ARM_REACH = (62, 70)
OPEN_E_TOP_TERMINAL = (0.78, 0.78, 0.78, 0.77)
OPEN_E_CAP_TERMINAL = (554, 544, 554, 522)
OPEN_E_UPPER_SIDE = 0.74
OPEN_E_LOWER_SIDE = 0.27
OPEN_E_LOW_TERMINAL = 0.22
GAMMA_CROSS = (96, 126, 86, 176)
GAMMA_WIDTH = (492, 566, 474, 640)
GAMMA_COUNTER = (84, 72, 90, 70)
GAMMA_SIDE = (0.88, 0.8, 0.9, 0.72)
GAMMA_FLAT = (0.94, 0.88, 0.96, 0.82)
GAMMA_WAIST = 0.5
GAMMA_NECK = (0.92, 0.86, 0.94, 0.8)
CAP_GAMMA_CROSS = (300, 340, 290, 410)
CAP_GAMMA_WIDTH = (616, 700, 594, 770)
CAP_GAMMA_COUNTER = (92, 78, 100, 68)
VHOOK_TURN = (240, 250, 236, 262)
VHOOK_SIDE = (270, 270, 270, 270)
VHOOK_PEAK = (56, 52, 58, 44)
VHOOK_TIP = (34, 38, 32, 40)
CAP_VHOOK_TURN = (252, 262, 248, 272)
CAP_VHOOK_SIDE = (350, 350, 350, 350)
CAP_HOOK_REACH = (114, 118, 110, 122)
CAP_HOOK_TAIL = (78, 114, 55, 130)
CAP_HOOK_SIDE = (12, 10, 12, 10)
TAIL_REACH = (88, 88, 88, 90)
TAIL_THIN = (74, 110, 52, 124)
TAIL_SIDE = (30, 28, 32, 30)
REVERSED_E_ROOM = (4, 6, 4, 10)


def ink(glyph):
    return accents.bounds(glyph.contours)


def widened(glyph, extra, before=0):
    return Glyph(shift(glyph.contours + extra, before), glyph.advance + before)


def side_by_side(*glyphs):
    contours, advance = [], 0
    for glyph in glyphs:
        contours += shift(glyph.contours, advance)
        advance += glyph.advance
    return Glyph(contours, advance)


def ascender_bar(m):
    centre = m.v(640, 644, light=638, black=650)
    half = m.bar * m.v(0.88, 0.8, light=0.92, black=0.78) / 2
    return centre - half, centre + half


def dcroat(m):
    glyph = lowercase.letter_d(m)
    left, right = ink(glyph)
    bottom, top = ascender_bar(m)
    start = left + (right - left) * m.v(0.44, 0.42, black=0.4)
    over = m.v(44, 48, light=40, black=50)
    bar = rect(start, bottom, right + over, top)
    return Glyph(glyph.contours + [bar], glyph.advance + over * 0.5)


def hbar(m):
    glyph = lowercase.letter_h(m)
    left, right = ink(glyph)
    bottom, top = ascender_bar(m)
    over = m.v(44, 48, light=40, black=50)
    end = left + (right - left) * m.v(0.56, 0.58, black=0.6)
    bar = rect(left - over, bottom, end, top)
    return widened(glyph, [bar], over * 0.5)


def capital_hbar(m):
    glyph = capitals.capital_h(m)
    left, right = ink(glyph)
    centre = m.v(552, 556, light=550, black=560)
    half = m.cap_bar * m.v(0.92, 0.86, light=0.96, black=0.8) / 2
    over = m.v(48, 52, light=46, black=54)
    bar = rect(left - over, centre - half, right + over, centre + half)
    return Glyph(shift(glyph.contours + [bar], over * 0.5), glyph.advance + over)


def capital_tbar(m):
    glyph = capitals.capital_t(m)
    left, right = ink(glyph)
    middle = (left + right) / 2
    reach = m.v(138, 152, light=132, black=164)
    centre = m.v(334, 330, light=336, black=326)
    half = m.cap_bar * m.v(0.96, 0.9, light=1.0, black=0.84) / 2
    return widened(glyph, [rect(middle - reach, centre - half, middle + reach, centre + half)])


def tbar(m):
    glyph = lowercase.letter_t(m)
    left, _ = ink(glyph)
    overhang = m.v(68, 62, light=60)
    end = left + overhang + m.stem + overhang
    centre = m.v(300, 292, light=304, black=290)
    half = m.bar * m.v(0.92, 0.84, light=0.96, black=0.78) / 2
    return widened(glyph, [rect(left, centre - half, end, centre + half)])


def slash(m, stem_left, stem, centre, before, after, slope, thickness):
    middle = stem_left + stem / 2
    half = thickness * (1 + slope * slope) ** 0.5 / 2
    start, end = stem_left - before, stem_left + stem + after
    low, high = centre + (start - middle) * slope, centre + (end - middle) * slope
    return polygon([(start, low - half), (end, high - half), (end, high + half), (start, low + half)])


def capital_lslash(m):
    glyph = capitals.capital_l(m)
    left, _ = ink(glyph)
    before = m.v(44, 52, light=40, black=58)
    stroke = slash(
        m,
        left,
        m.cap_stem,
        m.v(318, 314),
        before,
        m.v(124, 160, light=112, black=186),
        m.v(0.82, 0.8),
        m.cap_bar * m.v(0.94, 0.88, light=0.98, black=0.8),
    )
    return widened(glyph, [stroke], before * 0.5)


def lslash(m):
    glyph = lowercase.letter_l(m)
    left, _ = ink(glyph)
    before = m.v(44, 50, light=40, black=54)
    after = m.v(100, 136, light=92, black=158)
    stroke = slash(
        m,
        left,
        m.stem,
        m.v(396, 392),
        before,
        after,
        m.v(0.84, 0.82),
        m.bar * m.v(0.92, 0.86, light=0.96, black=0.8),
    )
    room = max(0, left + m.stem + after + m.v(24, 16, light=28, black=12) - glyph.advance)
    shifted = widened(glyph, [stroke], before * 0.5)
    return Glyph(shifted.contours, shifted.advance + room)


def descend(path, m, right, leg, bottom, thin, reach):
    inner = (reach - HOOK_TIP) / HOOK_SPREAD
    inner_height = inner * HOOK_DEPTH
    outer_x = leg + inner * HOOK_SPREAD
    outer_y = thin + inner_height * HOOK_BELLY
    path.to((right, bottom + outer_y))
    path.arc((right - outer_x, bottom), "v", m.k_out - 0.02)
    path.to((right - leg - reach, bottom))
    path.to((right - leg - reach, bottom + thin))
    path.to((right - leg - inner, bottom + thin))
    path.arc((right - leg, bottom + thin + inner_height), "h", m.k_in + 0.02)
    return path


def descending_arch(m, edges, top, thick, ry_out, ry_in, leg, bottom, thin, reach):
    left_out, left_in, peak_out, peak_in, right = edges
    y_out = top - ry_out
    y_in = top - thick - ry_in
    path = Path((left_out, y_out))
    path.arc((peak_out, top), "v", m.k_out)
    path.arc((right, y_out), "h", m.k_out)
    descend(path, m, right, leg, bottom, thin, reach)
    path.to((right - leg, y_in))
    path.arc((peak_in, top - thick), "v", m.k_in)
    path.arc((left_in, y_in), "h", m.k_in)
    return path.close()


def eng(m):
    stem = m.stem
    width = m.v(450, 520)
    edges = (
        stem * shoulder_spring(m),
        stem * shoulder_inner(m),
        width * 0.55,
        stem + (width - 2 * stem) * 0.52,
        width,
    )
    arch = descending_arch(
        m,
        edges,
        XH + m.arch_ov,
        m.v(76, 112, light=54, black=140),
        m.v(200, 214),
        m.v(142, 136),
        stem,
        DESC,
        m.v(74, 110, light=52, black=124),
        m.v(88, 88, black=90),
    )
    return spaced(m, [rect(0, 0, stem, XH), arch], width, "straight", m.v(66, 50))


def capital_eng(m):
    stem = m.cap_stem
    width = m.v(562, 628, light=546, black=676)
    edges = (
        stem * shoulder_spring(m),
        stem * shoulder_inner(m),
        width * 0.55,
        stem + (width - 2 * stem) * 0.52,
        width,
    )
    arch = descending_arch(
        m,
        edges,
        CAP + m.ov,
        m.v(80, 118, light=56, black=148),
        m.v(262, 276),
        m.v(188, 180),
        stem,
        DESC,
        m.v(78, 114, light=55, black=130),
        m.v(114, 118, light=110, black=122),
    )
    return spaced(m, [rect(0, 0, stem, CAP), arch], width, "cap", m.v(74, 58))


def sami_eng(m):
    stem = m.cap_stem
    width = m.v(590, 660)
    stroke = band_width(width, CAP, m.cap_diag * m.v(1.0, 0.94))
    post = Path((width - stem, CAP)).to((width, CAP))
    descend(post, m, width, stem, DESC, m.v(78, 114, light=55, black=130), m.v(114, 118, light=110, black=122))
    shapes = [rect(0, 0, stem, CAP), band((0, CAP), (width - stroke, 0), stroke), post.close()]
    return spaced(m, shapes, width, "cap", "cap")


def hooked_post(m, stem, top, thin, reach):
    post = Path((0, top)).to((stem, top))
    descend(post, m, stem, stem, DESC, thin, reach)
    return post.close()


def nhookleft(m):
    stem = m.stem
    width = m.v(450, 520)
    reach = m.v(88, 88, black=90)
    post = hooked_post(m, stem, XH, m.v(74, 110, light=52, black=124), reach)
    shapes = shift([post, lowercase.stem_arch(m, 0, width)], reach)
    return spaced(m, shapes, width + reach, m.v(24, 16), m.v(66, 50))


def capital_nhookleft(m):
    stem = m.cap_stem
    width = m.v(590, 660)
    reach = m.v(114, 118, light=110, black=122)
    stroke = band_width(width, CAP, m.cap_diag * m.v(1.0, 0.94))
    shapes = [
        hooked_post(m, stem, CAP, m.v(78, 114, light=55, black=130), reach),
        rect(width - stem, 0, width, CAP),
        band((0, CAP), (width - stroke, 0), stroke),
    ]
    return spaced(m, shift(shapes, reach), width + reach, m.v(24, 16), "cap")


def kgreenlandic(m):
    width = m.v(446, 536)
    shapes = kay(m, m.stem, width, XH, XH, m.v(196, 160), m.v(14, 12), m.diag, m.v(*lowercase.K_LIFT))
    return spaced(m, shapes, width, "straight", "diagonal")


def dot_side(m):
    return m.v(92, 146, light=62, black=182)


def middle_dot(m, x, y):
    side = dot_side(m)
    return rect(x, y - side / 2, x + side, y + side / 2)


def capital_ldot(m):
    glyph = capitals.capital_l(m)
    left, _ = ink(glyph)
    x = left + m.cap_stem + m.v(96, 82, light=100, black=64)
    return widened(glyph, [middle_dot(m, x, m.v(340, 334, black=318))])


def ldot(m):
    glyph = lowercase.letter_l(m)
    left, _ = ink(glyph)
    gap = m.v(62, 54, light=66, black=54)
    x = left + m.stem + gap
    floor = m.thin + lowercase.hook_inner(m) * lowercase.HOOK_SPREAD + m.v(48, 44, light=50, black=40)
    dot = middle_dot(m, x, max(marks.AXIS, floor + dot_side(m) / 2))
    return Glyph(glyph.contours + [dot], x + dot_side(m) + marks.gap(m))


def capital_ij(m):
    return side_by_side(capitals.capital_i(m), capitals.capital_j(m))


def ij(m):
    return side_by_side(lowercase.letter_i(m), lowercase.letter_j(m))


def longs(m):
    stem = m.stem
    run = stem + m.v(128, 140, light=118)
    stroke = place(lowercase.hook(m, stem, m.thin, ASC, run, lowercase.hook_inner(m)), 0, ASC, fy=-1)
    return spaced(m, [stroke], run, "straight", m.v(8, 4))


def napostrophe(m):
    side = marks.square(m)
    mark = shift([marks.raised(m, False)], m.v(54, 44))
    n = lowercase.letter_n(m)
    lead = m.v(54, 44) + side + m.v(44, 34) - m.bearing("straight")
    return Glyph(mark + shift(n.contours, lead), lead + n.advance)


def capital_germandbls(m):
    stem = m.cap_stem
    width = m.v(560, 630, light=540, black=712)
    bar = m.cap_bar
    edge = m.cap_round * m.v(1.0, 0.94, black=0.88)
    flat = m.cap_thin
    waist_y = m.v(394, 390, black=386)
    waist = flat * m.v(0.96, 0.88, black=0.8)
    corner = width - m.v(30, 28)
    foot = m.v(220, 246, light=210, black=296)
    thickness = m.cap_diag * m.v(0.94, 0.9, black=0.78)
    rise = CAP - bar - waist_y
    run = thickness * ((corner - foot) ** 2 + rise ** 2) ** 0.5 / rise
    for _ in range(6):
        run = thickness * ((corner - run - foot) ** 2 + rise ** 2) ** 0.5 / rise
    top = polygon(
        [
            (stem * 0.5, CAP),
            (corner, CAP),
            (corner, CAP - bar),
            (foot + run, waist_y),
            (foot, waist_y),
            (corner - run, CAP - bar),
            (stem * 0.5, CAP - bar),
        ]
    )
    gap = m.v(116, 146, light=110, black=140)
    bowl = ribbon(
        [
            Node((foot - m.v(14, 12), waist_y), RIGHT, waist, cut="v"),
            Node((width * 0.52, waist_y), RIGHT, waist, straight=True),
            Node((width - edge / 2, waist_y / 2 - m.v(8, 6)), DOWN, edge),
            Node((stem + gap + m.v(96, 66, light=100, black=60), flat / 2 - m.ov), LEFT, flat),
            Node((stem + gap, flat / 2 - m.ov), LEFT, flat, straight=True),
        ],
        0.6,
    )
    return spaced(m, [rect(0, 0, stem, CAP), top, bowl], width, "cap", m.v(36, 26))


def ezh_shape(m, top, bottom, width, weights):
    bar, edge, flat, diagonal = weights
    height = top - bottom
    waist_y = top - height * 0.45
    waist = flat * m.v(0.96, 0.88, black=0.8)
    corner = width - m.v(30, 28)
    foot = width * m.v(0.3, 0.32)
    rise = top - bar - waist_y
    run = diagonal * ((corner - foot) ** 2 + rise ** 2) ** 0.5 / rise
    for _ in range(6):
        run = diagonal * ((corner - run - foot) ** 2 + rise ** 2) ** 0.5 / rise
    arm = polygon(
        [
            (0, top),
            (corner, top),
            (corner, top - bar),
            (foot + run, waist_y),
            (foot, waist_y),
            (corner - run, top - bar),
            (0, top - bar),
        ]
    )
    bowl = ribbon(
        [
            Node((foot - m.v(14, 12), waist_y), RIGHT, waist, cut="v"),
            Node((width * 0.52, waist_y), RIGHT, waist, straight=True),
            Node((width - edge / 2, (waist_y + bottom) / 2 - m.v(8, 6)), DOWN, edge),
            Node((width * 0.49, bottom + flat / 2 - m.ov), LEFT, flat),
            Node((m.v(46, 74), bottom + height * m.v(0.21, 0.21, black=0.27)), aim(m.v(118, 120)), m.v(80, 128, light=54, black=140), cut="h"),
        ],
        0.6,
    )
    return [arm, bowl]


def capital_ezh(m):
    width = m.v(500, 556, light=482, black=620)
    weights = (m.cap_bar, m.cap_round * m.v(1.0, 0.94, black=0.88), m.cap_thin, m.cap_diag * m.v(0.94, 0.9, black=0.78))
    return spaced(m, ezh_shape(m, CAP, 0, width, weights), width, m.v(30, 22), m.v(36, 28), capital=True)


def ezh(m):
    width = m.v(448, 506, light=430, black=566)
    weights = (m.bar, m.round * m.v(1.0, 0.94, black=0.88), m.thin, m.diag * m.v(0.94, 0.9, black=0.78))
    return spaced(m, ezh_shape(m, XH, DESC, width, weights), width, m.v(30, 22), m.v(36, 28), capital=False)


def crossed(draw, height, reach, over):
    def build(m):
        glyph = draw(m)
        _, right = ink(glyph)
        half = m.bar * m.v(0.92, 0.84, light=0.96, black=0.78) / 2
        y = height(m)
        end = right + over(m)
        return Glyph(glyph.contours + [rect(right - reach(m), y - half, end, y + half)], glyph.advance + over(m))

    return build


def schwa(m):
    glyph = lowercase.letter_e(m)
    return Glyph(turn(glyph.contours, glyph.advance / 2, XH / 2), glyph.advance)


def capital_schwa(m):
    width = m.v(590, 652, light=560, black=700)
    side = m.cap_round
    flat = m.cap_thin
    bar = m.cap_bar
    end = m.v(84, 134, light=58, black=176)
    rise = aim(m.v(63, 61))
    inset = m.v(40, 34)
    bar_top = m.v(380, 384)
    shape = ribbon(
        [
            Node((inset + end / (2 * rise[1]), terminal_high(m)), rise, end, cut="h"),
            Node((width * 0.48, CAP + m.cap_ov - flat / 2), RIGHT, flat),
            Node((width - side / 2, CAP / 2), DOWN, side),
            Node((width * 0.5, flat / 2 - m.cap_ov), LEFT, flat),
            Node((side / 2, m.v(200, 206)), UP, side),
            Node((side / 2, bar_top), UP, side, straight=True, cut="h"),
        ],
        0.6,
    )
    crossbar = rect(side * 0.5, bar_top - bar, width - side * 0.5, bar_top)
    return spaced(m, [shape, crossbar], width, m.v(36, 28), "cap_round")


def florin(m):
    stem = m.stem
    thin = m.thin
    tail = m.v(74, 110, light=52, black=124)
    top_run = stem + m.v(118, 128, light=110)
    top_inner = lowercase.hook_inner(m)
    reach = m.v(84, 86, black=88)
    bottom_inner = (reach - HOOK_TIP) / HOOK_SPREAD
    top_height = top_inner * HOOK_DEPTH
    bottom_height = bottom_inner * HOOK_DEPTH
    path = Path((-reach, DESC))
    path.to((-bottom_inner * HOOK_SPREAD, DESC))
    path.arc((stem, DESC + tail + bottom_height * HOOK_BELLY), "h", m.k_out - 0.02)
    path.to((stem, ASC - thin - top_height))
    path.arc((stem + top_inner, ASC - thin), "v", m.k_in + 0.02)
    path.to((top_run, ASC - thin))
    path.to((top_run, ASC))
    path.to((stem + top_inner * HOOK_SPREAD, ASC))
    path.arc((0, ASC - thin - top_height * HOOK_BELLY), "h", m.k_out - 0.02)
    path.to((0, DESC + tail + bottom_height))
    path.arc((-bottom_inner, DESC + tail), "v", m.k_in + 0.02)
    path.to((-reach, DESC + tail))
    crossbar = rect(-m.v(68, 62, light=60), XH - m.bar, stem + m.v(98, 106, light=88), XH)
    contours = shift([path.close(), crossbar], reach)
    return spaced(m, contours, reach + top_run, m.v(20, 14), m.v(14, 10), capital=False)


def open_e(m, height, width, side, flat, terminal, terminal_y):
    top = height + m.ov
    waist_y = height * OPEN_E_WAIST
    waist = flat * m.v(0.94, 0.9, black=0.86)
    upper_side = side * m.v(0.92, 0.84)
    upper = ribbon(
        [
            Node((width - m.v(50, 76) * height / CAP, terminal_y), aim(180 - m.v(62, 60)), terminal, cut="h"),
            Node((width * 0.49, top - flat / 2), LEFT, flat),
            Node((m.v(22, 20) + upper_side / 2, height * OPEN_E_UPPER_SIDE), DOWN, upper_side),
            Node((width * 0.5, waist_y), RIGHT, waist),
            Node((width * m.v(0.68, 0.66), waist_y), RIGHT, waist, straight=True, cut="v"),
        ],
        0.6,
    )
    lower = ribbon(
        [
            Node((width * 0.6, waist_y), LEFT, waist, cut="v"),
            Node((width * 0.48, waist_y), LEFT, waist, straight=True),
            Node((side / 2, height * OPEN_E_LOWER_SIDE), DOWN, side),
            Node((width * 0.51, flat / 2 - m.ov), RIGHT, flat),
            Node((width - m.v(46, 74) * height / CAP, height * OPEN_E_LOW_TERMINAL), aim(180 - m.v(118, 120)), terminal, cut="h"),
        ],
        0.6,
    )
    return [upper, lower]


def capital_open_e(m):
    width = m.v(520, 576, light=504, black=624)
    shapes = open_e(m, CAP, width, m.cap_round, m.cap_thin, m.v(82, 130, light=56, black=138), m.v(*OPEN_E_CAP_TERMINAL))
    return spaced(m, shapes, width, "cap_round", m.v(30, 22))


def small_open_e(m):
    width = m.v(420, 470, light=406, black=520)
    shapes = open_e(m, XH, width, m.round, m.thin * m.v(1, 0.92, black=0.8), m.v(72, 104, light=50, black=112), XH * m.v(*OPEN_E_TOP_TERMINAL))
    return spaced(m, shapes, width, "round", m.v(22, 14))


def turned_open(draw):
    def build(m):
        glyph = draw(m)
        return Glyph(mirror(glyph.contours, glyph.advance / 2), glyph.advance)

    return build


def loop_arms(width, top, cross, thickness):
    middle = width / 2
    stroke = thickness
    for _ in range(8):
        stroke = across((middle - stroke / 2, cross - top), thickness)
    return middle, stroke, (middle - stroke / 2, cross - top)


def gamma_loop(m, width, top, bottom, cross, counter, weights, overshoot):
    thickness, side, flat = weights
    loop = side + counter / 2
    middle, stroke, heading = loop_arms(width, top, cross, thickness)
    floor = bottom - overshoot + flat / 2
    join = m.v(16, 14, light=16, black=12)
    length = math.hypot(*heading)
    unit = (heading[0] / length, heading[1] / length)
    neck = thickness * m.v(*GAMMA_NECK)
    inner = (middle + unit[1] * neck / 2, cross - unit[0] * neck / 2)
    corner = inner[1] + (middle + loop - side - inner[0]) * unit[1] / unit[0]
    waist = floor + flat / 2 + (corner - floor - flat / 2) * GAMMA_WAIST

    def arm(end):
        return ribbon(
            [
                Node((stroke / 2, top), heading, thickness, cut="h"),
                Node((middle, cross), heading, neck, straight=True),
                Node((middle + loop - side / 2, waist), DOWN, side),
                Node((middle + join, floor), LEFT, flat),
                Node((middle - end, floor), LEFT, flat, straight=True, cut="v"),
            ],
            0.6,
        )

    return [arm(0)] + mirror([arm(join / 2)], middle)


def small_gamma(m):
    width = m.v(*GAMMA_WIDTH)
    weights = (m.diag, m.diag * m.v(*GAMMA_SIDE), m.thin * m.v(*GAMMA_FLAT))
    shapes = gamma_loop(m, width, XH, DESC, m.v(*GAMMA_CROSS), m.v(*GAMMA_COUNTER), weights, m.ov)
    return spaced(m, shapes, width, "diagonal", "diagonal")


def capital_gamma(m):
    width = m.v(*CAP_GAMMA_WIDTH)
    weights = (m.cap_diag, m.cap_diag * m.v(*GAMMA_SIDE), m.cap_thin * m.v(*GAMMA_FLAT))
    shapes = gamma_loop(m, width, CAP, 0, m.v(*CAP_GAMMA_CROSS), m.v(*CAP_GAMMA_COUNTER), weights, m.cap_ov)
    return spaced(m, shapes, width, "cap_diagonal", "cap_diagonal", capital=True)


def hooked_cup(m, width, top, overshoot, weights, turn, side_y, peak, tip):
    stem, side, flat = weights
    crown = top + overshoot - flat / 2
    stroke = ribbon(
        [
            Node((stem / 2, top), DOWN, stem, cut="h"),
            Node((stem / 2, turn), DOWN, stem, straight=True),
            Node((width * 0.5, flat / 2 - overshoot), RIGHT, flat),
            Node((width - side / 2, side_y), UP, side),
            Node((width - side - peak, crown), LEFT, flat),
            Node((width - side - peak - tip, crown), LEFT, flat, straight=True, cut="v"),
        ],
        0.6,
    )
    return [stroke]


def vhook(m):
    width = m.v(452, 520, light=438, black=578)
    weights = (m.stem, m.round, m.thin)
    shapes = hooked_cup(m, width, XH, m.ov, weights, m.v(*VHOOK_TURN), m.v(*VHOOK_SIDE), m.v(*VHOOK_PEAK), m.v(*VHOOK_TIP))
    return spaced(m, shapes, width, m.v(62, 48), "round", capital=False)


def capital_vhook(m):
    width = m.v(564, 630, light=546, black=684)
    weights = (m.cap_stem, m.cap_round, m.cap_thin)
    shapes = hooked_cup(m, width, CAP, m.cap_ov, weights, m.v(*CAP_VHOOK_TURN), m.v(*CAP_VHOOK_SIDE), m.v(*VHOOK_PEAK), m.v(*VHOOK_TIP))
    return spaced(m, shapes, width, m.v(74, 58), "cap_round", capital=True)


def capital_fhook(m):
    stem = m.cap_stem
    width = m.v(452, 508)
    reach = m.v(*CAP_HOOK_REACH)
    inner = (reach - HOOK_TIP) / HOOK_SPREAD
    arms = [rect(stem * 0.5, CAP - m.cap_bar, width, CAP), capitals.crossbar(m, stem * 0.5, width - m.v(34, 30), CAP * 0.5)]
    tail = place(hook(m, stem, m.v(*CAP_HOOK_TAIL), CAP - DESC, reach + stem, inner), reach + stem, DESC, fx=-1)
    return spaced(m, [tail] + shift(arms, reach), reach + width, m.v(*CAP_HOOK_SIDE), m.v(28, 20), capital=True)


def ascript(m):
    from .alternates import single_storey_a

    return single_storey_a(m)


def dtail(m):
    width = m.v(472, 540, black=596)
    stem = m.stem
    reach = m.v(*TAIL_REACH)
    inner = (reach - HOOK_TIP) / HOOK_SPREAD
    tail = place(hook(m, stem, m.v(*TAIL_THIN), ASC - DESC, stem + reach, inner), width - stem, DESC)
    return spaced(m, [tail] + mirror(lowercase.bowl(m, width), width / 2), width + reach, "round", m.v(*TAIL_SIDE))


def reversed_e(m):
    glyph = capitals.capital_e(m)
    room = m.v(*REVERSED_E_ROOM)
    return Glyph(shift(mirror(glyph.contours, glyph.advance / 2), room), glyph.advance + room)


def ascender_hook(m, x):
    return place(hook(m, m.stem, m.thin, ASC, m.stem + m.v(*ASCENDER_HOOK), lowercase.hook_inner(m)), x, ASC, fy=-1)


def bhook(m):
    width = m.v(472, 540)
    return spaced(m, [ascender_hook(m, 0)] + lowercase.bowl(m, width), width, "straight", "round")


def dhook(m):
    width = m.v(472, 540)
    stem_x = width - m.stem
    shapes = [ascender_hook(m, stem_x)] + mirror(lowercase.bowl(m, width), width / 2)
    return spaced(m, shapes, stem_x + m.stem + m.v(*ASCENDER_HOOK), "round", m.v(14, 10))


def khook(m):
    width = m.v(446, 536)
    shapes = kay(m, m.stem, width, XH, ASC, m.v(196, 160), m.v(14, 12), m.diag, m.v(*lowercase.K_LIFT))
    return spaced(m, [ascender_hook(m, 0)] + shapes[1:], width, "straight", "diagonal")


def capital_hook(m, glyph):
    stem = m.cap_stem
    run = stem + m.v(*CAPITAL_HOOK)
    left, _ = ink(glyph)
    hooked = place(hook(m, stem, m.cap_thin, CAP, run, lowercase.hook_inner(m)), left + stem, CAP, fx=-1, fy=-1)
    lead = run - stem
    return Glyph(shift(glyph.contours[1:] + [hooked], lead), glyph.advance + lead)


def capital_bhook(m):
    return capital_hook(m, capitals.capital_b(m))


def capital_dhook(m):
    return capital_hook(m, capitals.capital_d(m))


def arm_bend(top, thin, thickness):
    return top - thin / 2 - thickness * ARM_TURN


def hooked_arm(m, foot, direction, thickness, top, thin, reach, bend_y=None):
    bend_y = arm_bend(top, thin, thickness) if bend_y is None else bend_y
    unit = (direction[0] / direction[1], 1)
    bend = (foot[0] + (bend_y - foot[1]) * unit[0], bend_y)
    corner = foot[0] + (top - thin / 2 - foot[1]) * unit[0]
    crown = (corner + thin * m.v(*ARM_CROWN), top - thin / 2)
    return ribbon(
        [
            Node(foot, direction, thickness, cut="h"),
            Node(bend, direction, thickness, straight=True, cut="h"),
            Node(crown, RIGHT, thin),
            Node((crown[0] + reach, crown[1]), RIGHT, thin, straight=True),
        ],
        0.6,
    )


def yhook(m):
    width = m.v(440, 510, black=578)
    middle = width / 2
    flat = m.diag * m.v(1.2, 1.1)
    direction = (middle - flat / 2, -XH)
    stroke = across(direction, m.diag)
    slope = direction[0] / XH
    foot = width - slope * (XH - DESC)
    notch = intersect((stroke, XH), (stroke + direction[0], 0), (middle, 0), (middle, XH))
    join = intersect((0, XH), (direction[0], 0), (width - stroke, XH), (foot - stroke, DESC))
    branch = polygon([(0, XH), (stroke, XH), notch, (join[0] + stroke * 0.6, join[1]), join])
    top = XH + m.v(*SMALL_ARM_RISE)
    arm = hooked_arm(m, (foot - stroke / 2, DESC), (width - foot, XH - DESC), m.diag, top, m.thin * m.v(*ARM_THIN), m.v(*ARM_REACH))
    return spaced(m, [arm, branch], extent_of([arm, branch]), "diagonal", m.v(10, 6))


def capital_yhook(m):
    stem = m.cap_stem
    width = m.v(578, 656)
    middle = width / 2
    fork = m.v(300, 292)
    direction = (middle - stem / 2, fork - CAP)
    stroke = across(direction, m.cap_diag)
    notch = (middle, CAP + (middle - stroke) * direction[1] / direction[0])
    cut = max(arm_bend(CAP, m.cap_thin, m.cap_diag), notch[1] + m.v(*ARM_NOTCH))
    inner = notch[0] + (cut - notch[1]) * (width - stroke - notch[0]) / (CAP - notch[1])
    outer = middle + stem / 2 + (cut - fork) * (width - middle - stem / 2) / (CAP - fork)
    body = polygon(
        [
            (0, CAP),
            (stroke, CAP),
            notch,
            (inner, cut),
            (outer, cut),
            (middle + stem / 2, fork),
            (middle + stem / 2, 0),
            (middle - stem / 2, 0),
            (middle - stem / 2, fork),
        ]
    )
    low = cut - m.v(*CAP_ARM_OVERLAP)
    arm_foot = ((inner + outer) / 2 - (cut - low) * (width - middle - stem / 2) / (CAP - fork), low)
    arm = hooked_arm(m, arm_foot, (width - middle - stem / 2, CAP - fork), m.cap_diag, CAP, m.cap_thin, m.v(*CAP_ARM_REACH), cut)
    return spaced(m, [body, arm], extent_of([body, arm]), "cap_diagonal", m.v(10, 6))


def capital_khook(m):
    stem = m.cap_stem
    width = m.v(576, 660)
    branch = m.v(252, 214)
    inset = m.v(18, 14)
    thickness = m.cap_diag
    stem_, upper, lower = kay(m, stem, width, CAP, CAP, branch, inset, thickness)
    direction = (width - inset - stem, CAP - branch)
    stroke = across(direction, thickness * m.v(0.98, 0.94))
    cut = arm_bend(CAP, m.cap_thin, thickness * m.v(0.98, 0.94))
    low = cut - m.v(*CAP_ARM_OVERLAP)
    centre = width - inset - stroke / 2 - (CAP - low) * direction[0] / direction[1]
    upper = clipped_arm(upper, cut)
    arm = hooked_arm(m, (centre, low), direction, thickness * m.v(0.98, 0.94), CAP, m.cap_thin, m.v(*CAP_ARM_REACH))
    return spaced(m, [stem_, upper, lower, arm], extent_of([stem_, upper, lower, arm]), "cap", m.v(10, 6))


def clipped_arm(contour, cut):
    low_cut, high_cut, high1, low1 = contour.corners()
    inner = along_to(low_cut, low1, cut)
    outer = along_to(high_cut, high1, cut)
    return polygon([low_cut, high_cut, outer, inner])


def along_to(start, end, y):
    t = (y - start[1]) / (end[1] - start[1])
    return (start[0] + (end[0] - start[0]) * t, y)


def extent_of(contours):
    return max(point[0] for contour in contours for point in contour.points())


def fi(m):
    return side_by_side(lowercase.letter_f(m), lowercase.letter_i(m))


def fl(m):
    return side_by_side(lowercase.letter_f(m), lowercase.letter_l(m))


def digraph(first, second):
    def build(m):
        from .features import needed_kern, side_gap

        left = accents.GLYPHS[first][1](m) if first in accents.GLYPHS else DIGRAPH_PARTS[first](m)
        right = accents.GLYPHS[second][1](m) if second in accents.GLYPHS else DIGRAPH_PARTS[second](m)
        room = max(0, needed_kern(left, right, side_gap(lowercase.letter_o(m))))
        return side_by_side(Glyph(left.contours, left.advance + room), right)

    return build


DIGRAPH_PARTS = {
    "D": capitals.capital_d,
    "L": capitals.capital_l,
    "N": capitals.capital_n,
    "J": capitals.capital_j,
    "d": lowercase.letter_d,
    "l": lowercase.letter_l,
    "n": lowercase.letter_n,
    "j": lowercase.letter_j,
    "Z": capitals.capital_z,
    "z": lowercase.letter_z,
}
DIGRAPHS = {
    "DZcaron": (0x1C4, "D", "Zcaron"),
    "Dzcaron": (0x1C5, "D", "zcaron"),
    "dzcaron": (0x1C6, "d", "zcaron"),
    "LJ": (0x1C7, "L", "J"),
    "Lj": (0x1C8, "L", "j"),
    "lj": (0x1C9, "l", "j"),
    "NJ": (0x1CA, "N", "J"),
    "Nj": (0x1CB, "N", "j"),
    "nj": (0x1CC, "n", "j"),
    "DZ": (0x1F1, "D", "Z"),
    "Dz": (0x1F2, "D", "z"),
    "dz": (0x1F3, "d", "z"),
}


GLYPHS = {
    "Dcroat": (0x110, accents.capital_eth),
    "dcroat": (0x111, dcroat),
    "Hbar": (0x126, capital_hbar),
    "hbar": (0x127, hbar),
    **{name: (code, digraph(first, second)) for name, (code, first, second) in DIGRAPHS.items()},
    "IJ": (0x132, capital_ij),
    "ij": (0x133, ij),
    "kgreenlandic": (0x138, kgreenlandic),
    "Ldot": (0x13F, capital_ldot),
    "ldot": (0x140, ldot),
    "Lslash": (0x141, capital_lslash),
    "lslash": (0x142, lslash),
    "napostrophe": (0x149, napostrophe),
    "Eng": (0x14A, capital_eng),
    "Eng.sami": (None, sami_eng),
    "eng": (0x14B, eng),
    "Nhookleft": (0x19D, capital_nhookleft),
    "nhookleft": (0x272, nhookleft),
    "Tbar": (0x166, capital_tbar),
    "tbar": (0x167, tbar),
    "longs": (0x17F, longs),
    "Schwa": (0x18F, capital_schwa),
    "florin": (0x192, florin),
    "schwa": (0x259, schwa),
    "Germandbls": (0x1E9E, capital_germandbls),
    "Ezh": (0x1B7, capital_ezh),
    "ezh": (0x292, ezh),
    "Ezhcaron": (0x1EE, accents.accented_letter("Ezh", capital_ezh, "caron", True)),
    "ezhcaron": (0x1EF, accents.accented_letter("ezh", ezh, "caron", False)),
    "Gstroke": (0x1E4, crossed(capitals.capital_g, lambda m: CAP * 0.36, lambda m: m.v(170, 190), lambda m: m.v(48, 40))),
    "gstroke": (0x1E5, crossed(lowercase.letter_g, lambda m: -m.v(64, 70), lambda m: m.stem + m.v(64, 56), lambda m: m.v(46, 38))),
    "Bhook": (0x181, capital_bhook),
    "Oopen": (0x186, turned_open(capitals.capital_c)),
    "Dhook": (0x18A, capital_dhook),
    "Eopen": (0x190, capital_open_e),
    "Khook": (0x198, capital_khook),
    "khook": (0x199, khook),
    "Yhook": (0x1B3, capital_yhook),
    "yhook": (0x1B4, yhook),
    "bhook": (0x253, bhook),
    "oopen": (0x254, turned_open(lowercase.letter_c)),
    "dhook": (0x257, dhook),
    "eopen": (0x25B, small_open_e),
    "Fhook": (0x191, capital_fhook),
    "Dafrican": (0x189, accents.capital_eth),
    "Ereversed": (0x18E, reversed_e),
    "Gammaafrican": (0x194, capital_gamma),
    "Vhook": (0x1B2, capital_vhook),
    "eturned": (0x1DD, schwa),
    "ascript": (0x251, ascript),
    "dtail": (0x256, dtail),
    "gammalatinsmall": (0x263, small_gamma),
    "vhook": (0x28B, vhook),
    "fi": (0xFB01, fi),
    "fl": (0xFB02, fl),
}

KERN_LIKE = {
    "Dcroat": "D",
    "dcroat": "d",
    "Hbar": "H",
    "hbar": "h",
    "ij": "i",
    "Ldot": "L",
    "Lslash": "L",
    "lslash": "l",
    "eng": "n",
    "nhookleft": "n",
    "Nhookleft": "N",
    "Tbar": "T",
    "tbar": "t",
    "Schwa": "O",
    "Eng.sami": "N",
    "schwa": "o",
    "Bhook": "B",
    "Dhook": "D",
    "Eopen": "C",
    "Khook": "K",
    "khook": "k",
    "Yhook": "Y",
    "yhook": "y",
    "bhook": "b",
    "eopen": "c",
    "Fhook": "F",
    "Dafrican": "D",
    "Gammaafrican": "V",
    "Vhook": "U",
    "eturned": "o",
    "ascript": "a",
    "dtail": "d",
    "gammalatinsmall": "v",
    "vhook": "upsilon",
}


SAMI = ("NSM", "LSM", "ISM", "SKS")
LANGUAGES = SAMI


def features(master):
    languages = "".join(f"    language {tag};\n    lookup sami_eng;\n" for tag in SAMI[1:])
    return f"feature locl {{\n    script latn;\n    language {SAMI[0]};\n    lookup sami_eng {{\n        sub Eng by Eng.sami;\n    }} sami_eng;\n{languages}}} locl;\n"
