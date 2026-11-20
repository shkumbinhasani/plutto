import math
import unicodedata
from dataclasses import replace
from functools import lru_cache

import numpy

from . import accents, capitals, latin, lowercase, maths, symbols
from . import marks as punctuation
from .accents import anchor, bounds, centred, outline_array, whole
from .capitals import end_x
from .geometry import Contour, Path, across, flip, head, intersect, quarter
from .masters import ASC, CAP, DESC, XH, family
from .oblique import Overlaid, slanted
from .parts import Glyph, band, band_width, hook, reach, shoulder_inner, shoulder_spring, spaced
from .shapes import Node, aim, arch, mirror, oval, place, polygon, rect, ribbon, ring, shift, turn

DOWN = (0, -1)
UP = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
TAIL_WEIGHT = (0.96, 0.94, 0.98, 0.9)
TAIL_TAPER = (0.84, 0.74, 0.9, 0.68)
JOINT_WEIGHT = (0.88, 0.8, 0.92, 0.72)
TAIL_INSET = (4, 2, 6, 0)
TAIL_KNEE = (96, 100, 94, 104)
TAIL_END = (0.42, 0.4, 0.42, 0.37)
ZETA_PULL = (0.6, 0.62, 0.6, 0.66)
ZETA_SIDE = (160, 196, 150, 224)
XI_BAR_END = 0.6
XI_SIDE_DROP = 10
XI_PULL = 0.55
XI_UPPER_SIDE = (0.9, 0.86, None, 0.76)
XI_TONGUE = (0.86, 0.8, 0.9, 0.74)
XI_TONGUE_END = 0.6
ALPHA_MIDDLE = (0.44, 0.45, 0.44, 0.46)
ALPHA_JOINT = (236, 236, 236, 236)
ALPHA_LEAN = (56, 62, 52, 72)
ALPHA_HEADING = (107, 107, 107, 107)
ALPHA_HORN = (0.94, 0.92, 0.96, 0.9)
ALPHA_NECK = (0.8, 0.74, 0.82, 0.64)
ALPHA_UPPER = (390, 376, 394, 352)
ALPHA_LOWER = (168, 178, 164, 196)
ALPHA_ENTRY = (42, 42, 40, 38)
ALPHA_EXIT = (46, 46, 44, 44)
ALPHA_PULL = 0.75
GAMMA_SIDE = (0.9, 0.86, 0.92, 0.8)
GAMMA_FLOOR = (0.86, 0.8, 0.9, 0.7)
GAMMA_LOOP = (66, 90, 58, 118)
GAMMA_MIDDLE = (-104, -94, -108, -82)
GAMMA_FALL = (58, 57, 59, 56)
GAMMA_SWING = (86, 84, 88, 82)
GAMMA_LEAN = (64, 62, 65, 60)
GAMMA_OVERLAP = 4


def a_frame(m):
    width = m.v(612, 692, black=756)
    middle = width / 2
    flat = m.cap_diag * m.v(1.15, 1.05, black=1.02)
    direction = (middle - flat / 2, CAP)
    stroke = across(direction, m.cap_diag * m.v(1, 1, black=0.96))
    return width, middle, flat, direction, stroke


def capital_gamma(m):
    stem = m.cap_stem
    width = m.v(452, 508)
    bar = m.cap_bar
    shape = polygon([(0, 0), (0, CAP), (width, CAP), (width, CAP - bar), (stem, CAP - bar), (stem, 0)])
    return spaced(m, [shape], width, "cap", m.v(28, 20))


def capital_delta(m):
    width, middle, flat, direction, stroke = a_frame(m)
    bar = m.cap_bar * m.v(1.04, 1.02, black=0.98)
    falling = (-direction[0], direction[1])
    low_left = intersect((stroke, 0), (stroke + direction[0], CAP), (0, bar), (1, bar))
    low_right = intersect((width - stroke, 0), (width - stroke + falling[0], CAP), (0, bar), (1, bar))
    apex = intersect((stroke, 0), (stroke + direction[0], CAP), (width - stroke, 0), (width - stroke + falling[0], CAP))
    outer = polygon([(0, 0), (middle - flat / 2, CAP), (middle + flat / 2, CAP), (width, 0)])
    counter = Path(low_left).to(apex).to(low_right).close(hole=True)
    return spaced(m, [outer, counter], width, "cap_diagonal", "cap_diagonal")


def capital_theta(m):
    width = m.v(*capitals.ROUND_WIDTH)
    side = m.cap_round
    shapes = ring(0, -m.cap_ov, width, CAP + m.cap_ov, side, m.cap_thin, m.k_out, m.k_in)
    shapes.append(capitals.crossbar(m, side * 0.5, width - side * 0.5, CAP / 2))
    return spaced(m, shapes, width, "cap_round", "cap_round")


def capital_lambda(m):
    width, middle, flat, direction, stroke = a_frame(m)
    notch = intersect((stroke, 0), (stroke + direction[0], CAP), (middle, 0), (middle, CAP))
    body = polygon([(0, 0), (middle - flat / 2, CAP), (middle + flat / 2, CAP), (width, 0), (width - stroke, 0), notch, (stroke, 0)])
    return spaced(m, [body], width, "cap_diagonal", "cap_diagonal")


def capital_xi(m):
    width = m.v(512, 572, light=496, black=620)
    bar = m.cap_bar * m.v(1.08, 1.06, light=1.1, black=1.02)
    middle = m.cap_bar * m.v(1.02, 1.0, light=1.04, black=0.96)
    inset = width * m.v(0.11, 0.1)
    centre = CAP * 0.51
    shapes = [
        rect(0, CAP - bar, width, CAP),
        rect(inset, centre - middle / 2, width - inset, centre + middle / 2),
        rect(0, 0, width, bar),
    ]
    return spaced(m, shapes, width, m.v(40, 30), m.v(40, 30), capital=True)


def capital_pi(m):
    stem = m.cap_stem
    width = m.v(566, 632)
    bar = m.cap_bar
    shape = polygon([
        (0, 0),
        (0, CAP),
        (width, CAP),
        (width, 0),
        (width - stem, 0),
        (width - stem, CAP - bar),
        (stem, CAP - bar),
        (stem, 0),
    ])
    return spaced(m, [shape], width, "cap", "cap")


def capital_sigma(m):
    width = m.v(540, 600, light=522, black=648)
    bar = m.cap_bar
    middle = CAP / 2
    tip = (width * m.v(0.6, 0.62), middle)
    upper_y, lower_y = CAP - bar / 2, bar / 2
    thick = m.cap_diag * m.v(1.0, 0.96, black=0.92)
    thin = m.cap_bar * m.v(1.04, 1.0)
    upper = band_width(tip[0], upper_y - middle, thick)
    lower = band_width(tip[0], middle - lower_y, thin)
    notch = intersect((0, upper_y), (tip[0] - upper, tip[1]), (0, lower_y), (tip[0] - lower, tip[1]))
    chevron = polygon([(0, upper_y), (upper, upper_y), tip, (lower, lower_y), (0, lower_y), notch])
    shapes = [rect(0, CAP - bar, width - m.v(14, 12), CAP), chevron, rect(0, 0, width, bar)]
    return spaced(m, shapes, width, m.v(36, 28), m.v(36, 28), capital=True)


def capital_phi(m):
    stem = m.cap_stem
    width = m.v(668, 736, light=644, black=830)
    low = m.v(104, 98, light=108, black=94)
    centre = width / 2
    side = m.cap_round * m.v(1.0, 0.96, light=1.0, black=0.88)
    post = stem * m.v(1, 1, black=0.94) / 2
    shapes = ring(0, low, width, CAP - low, side, m.cap_thin, m.k_out, m.k_in, (centre - post, centre + post))
    shapes.append(rect(centre - post, 0, centre + post, CAP))
    return spaced(m, shapes, width, "cap_round", "cap_round")


def capital_psi(m):
    stem = m.cap_stem
    width = m.v(660, 734, light=636, black=796)
    side = stem * m.v(0.94, 0.9, black=0.86)
    centre = width / 2
    bottom = m.v(226, 218)
    thin = m.cap_thin
    outer_y = bottom + m.v(196, 204)
    inner_y = outer_y - m.v(6, 14)
    cup = Path((0, CAP))
    cup.to((side, CAP))
    cup.to((side, inner_y))
    cup.arc((centre, bottom + thin), "v", m.k_in)
    cup.arc((width - side, inner_y), "h", m.k_in)
    cup.to((width - side, CAP))
    cup.to((width, CAP))
    cup.to((width, outer_y))
    cup.arc((centre, bottom), "v", m.k_out)
    cup.arc((0, outer_y), "h", m.k_out)
    shapes = [cup.close(), rect(centre - stem / 2, 0, centre + stem / 2, CAP)]
    return spaced(m, shapes, width, m.v(54, 42), m.v(54, 42), capital=True)


def alpha(m):
    width = m.v(472, 540, light=456, black=592)
    stem = m.stem
    side = m.round
    flat = m.thin
    inner = m.v(62, 66, light=60, black=68)
    run = stem + inner * 1.15 + m.v(14, 12)
    spine = width - stem / 2
    end = width - stem + run
    middle = width * m.v(*ALPHA_MIDDLE)
    joint = m.v(*ALPHA_JOINT)
    stroke = ribbon(
        [
            Node((spine + m.v(*ALPHA_LEAN), XH), aim(-m.v(*ALPHA_HEADING)), stem * m.v(*ALPHA_HORN), cut="h"),
            Node((spine, joint), DOWN, stem),
            Node((spine + stem / 2 + inner * 1.15, flat / 2), RIGHT, flat),
            Node((end, flat / 2), RIGHT, flat, straight=True, cut="v"),
        ],
        0.6,
    )
    neck = flat * m.v(*ALPHA_NECK)
    bowl = ribbon(
        [
            Node((spine, m.v(*ALPHA_UPPER)), aim(180 - m.v(*ALPHA_ENTRY)), neck, leave=ALPHA_PULL),
            Node((middle, XH + m.ov - flat / 2), LEFT, flat, arrive=ALPHA_PULL),
            Node((side / 2, XH / 2), DOWN, side),
            Node((middle, flat / 2 - m.ov), RIGHT, flat, leave=ALPHA_PULL),
            Node((spine, m.v(*ALPHA_LOWER)), aim(m.v(*ALPHA_EXIT)), neck, arrive=ALPHA_PULL),
        ],
        0.6,
    )
    return spaced(m, [bowl, stroke], end, "round", m.v(10, 6))


def beta(m):
    stem = m.stem
    side = m.round
    flat = m.thin
    width = m.v(468, 536, light=452, black=604)
    upper = width - m.v(36, 40, light=34, black=44)
    waist = m.v(404, 400, light=406, black=396)
    joint = m.thin * m.v(0.94, 0.84, light=1.0, black=0.72)
    flat = m.thin * m.v(1.0, 0.94, light=1.0, black=0.84)
    top = ASC + m.ov
    head = ribbon(
        [
            Node((stem / 2, DESC), UP, stem, cut="h"),
            Node((stem / 2, ASC - m.v(150, 160)), UP, stem, straight=True),
            Node(((stem + upper - side) / 2 + m.v(10, 6), top - flat / 2), RIGHT, flat),
            Node((upper - side / 2, (top - flat + waist + joint / 2) / 2), DOWN, side),
            Node((stem + m.v(92, 96), waist), LEFT, joint),
            Node((stem * 0.45, waist), LEFT, joint, straight=True, cut="v"),
        ],
        0.6,
    )
    drop = m.v(10, 12)
    belly = ribbon(
        [
            Node((stem * 0.55, waist - drop), RIGHT, joint, cut="v"),
            Node((stem + m.v(104, 108), waist - drop), RIGHT, joint, straight=True),
            Node((width - side / 2, (waist - drop - joint / 2 + flat - m.ov) / 2), DOWN, side),
            Node(((stem + width - side) / 2 + m.v(12, 8), flat / 2 - m.ov), LEFT, flat),
            Node((stem * 0.5, flat / 2 - m.ov), LEFT, flat, straight=True, cut="v"),
        ],
        0.6,
    )
    return spaced(m, [head, belly], width, "straight", "round")


def gamma(m):
    width = m.v(440, 510, light=426, black=574)
    arm = m.diag
    side = m.thin * m.v(*GAMMA_SIDE)
    floor = m.thin * m.v(*GAMMA_FLOOR)
    centre = width / 2
    loop = m.v(*GAMMA_LOOP)
    middle = m.v(*GAMMA_MIDDLE)
    bottom = DESC - m.ov + floor / 2
    falling = aim(-m.v(*GAMMA_FALL))
    leaning = aim(m.v(*GAMMA_LEAN) - 180)
    left = ribbon(
        [
            Node((across(falling, arm) / 2, XH), falling, arm, cut="h"),
            Node((centre + loop, middle), aim(-m.v(*GAMMA_SWING)), side),
            Node((centre - GAMMA_OVERLAP, bottom), LEFT, floor),
        ],
        0.6,
    )
    right = ribbon(
        [
            Node((width - across(leaning, arm) / 2, XH), leaning, arm, cut="h"),
            Node((centre - loop, middle), DOWN, side),
            Node((centre + GAMMA_OVERLAP, bottom), RIGHT, floor),
        ],
        0.6,
    )
    return spaced(m, [left, right], width, "diagonal", "diagonal")


def delta(m):
    width = m.v(468, 532, light=452, black=584)
    side = m.round
    thin = m.thin
    bowl = ring(0, -m.ov, width, XH + m.ov, side, thin, m.k_out, m.k_in)
    flat = thin * m.v(0.96, 0.88, light=1.0, black=0.8)
    end = m.v(80, 124, light=54, black=152)
    rise = aim(m.v(117, 119))
    reach_x = width - m.v(30, 26)
    neck = ribbon(
        [
            Node((end_x(reach_x, rise, end), ASC - m.v(98, 132, light=86, black=156)), rise, end, cut="h"),
            Node((width * 0.5, ASC + m.ov - flat / 2), LEFT, flat),
            Node((width * m.v(0.22, 0.24), m.v(616, 596, light=622, black=576)), aim(-m.v(64, 60)), side * m.v(0.9, 0.82, black=0.74)),
            Node((width * 0.6, XH + m.ov - thin / 2 - 3), aim(-12), thin * 0.8),
        ],
        0.6,
    )
    return spaced(m, bowl + [neck], width, "round", "round")


def epsilon(m):
    width = m.v(404, 462, light=390, black=508)
    side = m.round * m.v(0.96, 0.92)
    flat = m.thin * m.v(1.0, 0.92, light=1.0, black=0.8)
    waist = m.v(292, 296)
    joint = m.thin * m.v(*JOINT_WEIGHT)
    end = m.v(78, 120, light=54, black=146)
    rise = aim(m.v(117, 119))
    fall = aim(m.v(63, 61))
    inset = m.v(22, 26)
    upper = ribbon(
        [
            Node((end_x(width - m.v(26, 22), rise, end), XH - m.v(122, 136, black=150)), rise, end, cut="h"),
            Node((width * 0.54, XH + m.ov - flat / 2), LEFT, flat),
            Node((inset + side * 0.47, (XH + m.ov - flat + waist + joint / 2) / 2 + m.v(6, 4)), DOWN, side * 0.94),
            Node((width * m.v(0.44, 0.5), waist), RIGHT, joint),
            Node((width * m.v(0.66, 0.7), waist), RIGHT, joint, straight=True, cut="v"),
        ],
        0.6,
    )
    lower = ribbon(
        [
            Node((width * m.v(0.5, 0.56), waist - 2), LEFT, joint * 0.86),
            Node((side / 2, (waist - joint / 2 + flat - m.ov) / 2), DOWN, side),
            Node((width * 0.52, flat / 2 - m.ov), RIGHT, flat),
            Node((width - end / (2 * fall[1]), m.v(128, 140)), fall, end, cut="h"),
        ],
        0.6,
    )
    return spaced(m, [upper, lower], width, "round", m.v(24, 16))


def descent(m, width, flat):
    turn = m.round * m.v(*TAIL_WEIGHT)
    end = m.thin * m.v(*TAIL_TAPER)
    bend_at = (width - turn / 2 - m.v(*TAIL_INSET), -m.v(*TAIL_KNEE))
    return [
        Node((width * 0.5, flat / 2 - m.ov), RIGHT, flat),
        Node(bend_at, DOWN, turn),
        Node((width * m.v(*TAIL_END), DESC - m.ov + end / 2), LEFT, end, cut="v"),
    ]


def zeta(m):
    width = m.v(404, 464, light=390, black=512)
    side = m.round
    flat = m.thin
    bar = m.bar * m.v(1.0, 0.96)
    stroke = m.diag * m.v(0.96, 0.94)
    heading = aim(-128)
    top = (width - across(heading, stroke) / 2 - m.v(10, 8), ASC)
    nodes = [
        Node(top, heading, stroke, cut="h", leave=m.v(*ZETA_PULL)),
        Node((side / 2 + m.v(4, 2), m.v(*ZETA_SIDE)), DOWN, side, arrive=m.v(*ZETA_PULL)),
    ] + descent(m, width, flat)
    body = ribbon(nodes, 0.6)
    return spaced(m, [barred(body, m.v(14, 10), bar)], width, m.v(26, 20), m.v(28, 20), capital=False)


def barred(contour, left, bar):
    segments = list(contour.segments)
    inner_top = segments[-2][-1]
    *_, last = segments
    if len(last) == 3:
        segments[-1] = head((inner_top, *last), rising_to((inner_top, *last), ASC - bar))[1:]
    else:
        below = intersect(inner_top, last[-1], (0, ASC - bar), (1, ASC - bar))
        segments[-1] = (below,)
    segments += [((left, ASC - bar),), ((left, ASC),)]
    return Contour(contour.start, segments)


def rising_to(bezier, y):
    low, high = 0.0, 1.0
    for _ in range(40):
        middle = (low + high) / 2
        if head(bezier, middle)[3][1] < y:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def eta(m):
    stem = m.stem
    width = m.v(450, 520)
    shape = arch(
        left_out=stem * shoulder_spring(m),
        left_in=stem * shoulder_inner(m),
        peak_out=width * 0.55,
        peak_in=stem + (width - 2 * stem) * 0.52,
        right=width,
        top=XH + m.arch_ov,
        base=DESC,
        stem=stem,
        thick=m.v(76, 112, light=54, black=140),
        ry_out=m.v(200, 214),
        ry_in=m.v(142, 136),
        k_out=m.k_out,
        k_in=m.k_in,
    )
    return spaced(m, [rect(0, 0, stem, XH), shape], width, "straight", "straight")


def theta(m):
    width = m.v(452, 512, light=436, black=566)
    side = m.round
    shapes = ring(0, -m.ov, width, ASC + m.ov, side, m.thin, m.k_out, m.k_in)
    centre = ASC / 2 + m.v(4, 4)
    half = m.bar * m.v(1.0, 0.96) / 2
    shapes.append(rect(side * 0.5, centre - half, width - side * 0.5, centre + half))
    return spaced(m, shapes, width, "round", "round")


def iota(m):
    stem = m.stem
    inner = m.v(54, 58, light=52, black=60)
    run = stem + inner * 1.15 + m.v(16, 14)
    shape = hook(m, stem, m.thin, XH, run, inner)
    return spaced(m, [shape], run, "straight", m.v(8, 4))


def lamda(m):
    width = m.v(456, 522, light=440, black=584)
    start = m.v(24, 18)
    stroke = band_width(width - start, ASC, m.diag)
    long = band((start, ASC), (width - stroke, 0), stroke)
    join = m.v(366, 356)
    slope = (width - stroke - start) / ASC
    meet = (start + slope * (ASC - join), join)
    leg = across((meet[0], join), m.diag * m.v(0.96, 0.94))
    centre_top = (start + stroke / 2, ASC)
    centre_low = (width - stroke / 2, 0)
    outer = intersect((0, 0), meet, centre_top, centre_low)
    inner = intersect((leg, 0), (leg + meet[0], join), centre_top, centre_low)
    branch = polygon([(0, 0), outer, inner, (leg, 0)])
    return spaced(m, [long, branch], width, m.v(18, 14, light=20, black=12), "diagonal")


def nu(m):
    width = m.v(440, 508, light=426, black=572)
    flat = m.diag * m.v(1.16, 1.08)
    middle = width * 0.42
    left_dir = (middle - flat / 2, -XH)
    right_dir = (middle + flat / 2 - width, -XH)
    left = across(left_dir, m.diag * m.v(1.02, 1.0))
    right = across(right_dir, m.diag)
    notch = intersect((left, XH), (left + left_dir[0], 0), (width - right, XH), (width - right + right_dir[0], 0))
    shape = polygon([
        (0, XH),
        (left, XH),
        notch,
        (width - right, XH),
        (width, XH),
        (middle + flat / 2, 0),
        (middle - flat / 2, 0),
    ])
    return spaced(m, [shape], width, m.v(28, 20), "diagonal")


def xi(m):
    width = m.v(404, 462, light=390, black=508)
    side = m.round
    flat = m.thin * m.v(1.0, 0.92, light=1.0, black=0.8)
    bar = m.bar * m.v(1.0, 0.96)
    waist = m.v(408, 412)
    joint = m.thin * m.v(*JOINT_WEIGHT)
    upper_side = side * m.v(*XI_UPPER_SIDE)
    inset = m.v(34, 36)
    crown = ribbon(
        [
            Node((width - m.v(16, 12), ASC - bar / 2), LEFT, bar, cut="v"),
            Node((width * XI_BAR_END, ASC - bar / 2), LEFT, bar, straight=True),
            Node((inset + upper_side / 2, (ASC - bar + waist) / 2 - XI_SIDE_DROP), DOWN, upper_side),
            Node((width * 0.42, waist), RIGHT, joint),
            Node((width * XI_TONGUE_END, waist + joint * (1 - m.v(*XI_TONGUE)) / 2), RIGHT, joint * m.v(*XI_TONGUE), straight=True, cut="v"),
        ],
        XI_PULL,
    )
    lower = ribbon(
        [
            Node((width * 0.46, waist - 2), LEFT, joint * 0.86),
            Node((side / 2, waist / 2), DOWN, side),
        ]
        + descent(m, width, flat),
        0.6,
    )
    return spaced(m, [crown, lower], width, "round", m.v(28, 20))


def rho(m):
    width = m.v(476, 540, black=592)
    stem = m.stem
    cx, cy = width / 2, XH / 2
    turn = reach(quarter((cx, -m.ov), (0, cy), "h", m.k_out), 0, stem)
    outer = Path((0, DESC))
    outer.to((0, cy))
    outer.arc((cx, XH + m.ov), "v", m.k_out)
    outer.arc((width, cy), "h", m.k_out)
    outer.arc((cx, -m.ov), "v", m.k_out)
    outer.bez(turn)
    outer.to((stem, DESC))
    counter = oval(m.round, m.thin, width - m.round, XH - m.thin, m.k_in, hole=True)
    return spaced(m, [outer.close(), counter], width, "straight", "round")


def sigma(m):
    width = m.v(468, 532, light=452, black=584)
    bar = m.thin * m.v(1.0, 0.96)
    overhang = m.v(84, 92, light=80, black=98)
    cx, cy = width / 2, (XH - m.ov) / 2
    right = width + overhang
    shoulder = reach(quarter((width, cy), (cx, XH), "v", m.k_out), 1, XH - bar)
    outer = Path((right, XH))
    outer.to((cx, XH))
    outer.arc((0, cy), "h", m.k_out)
    outer.arc((cx, -m.ov), "v", m.k_out)
    outer.arc((width, cy), "h", m.k_out)
    outer.bez(shoulder)
    outer.to((right, XH - bar))
    counter = oval(m.round, m.thin, width - m.round, XH - bar, m.k_in, hole=True)
    return spaced(m, [outer.close(), counter], right, "round", m.v(10, 6))


def final_sigma(m):
    width = m.v(420, 470, light=406, black=524)
    side = m.round
    flat = m.thin
    end = m.v(78, 120, light=54, black=146)
    rise = aim(m.v(117, 119))
    nodes = [
        Node((end_x(width - m.v(10, 8), rise, end), XH - m.v(128, 144)), rise, end, cut="h"),
        Node((width * 0.52, XH + m.ov - flat / 2), LEFT, flat),
        Node((side / 2, m.v(272, 268)), DOWN, side),
    ] + descent(m, width, flat)
    return spaced(m, [ribbon(nodes, 0.6)], width, "round", m.v(22, 14))


def tau(m):
    stem = m.stem
    left = m.v(110, 116, light=104, black=124)
    right = m.v(112, 120, light=106, black=126)
    width = left + stem + right
    bar = m.bar
    foot = place(hook(m, stem, m.thin, XH - bar / 2, stem + right, lowercase.hook_inner(m)), left, 0)
    return spaced(m, [foot, rect(0, XH - bar, width, XH)], width, m.v(18, 12), m.v(22, 14), capital=False)


def cup(m, width, side, top, outer_y, inner_y, bottom, floor):
    middle = width / 2
    path = Path((0, top))
    path.to((side, top))
    path.to((side, inner_y))
    path.arc((middle, floor), "v", m.k_in)
    path.arc((width - side, inner_y), "h", m.k_in)
    path.to((width - side, top))
    path.to((width, top))
    path.to((width, outer_y))
    path.arc((middle, bottom), "v", m.k_out)
    path.arc((0, outer_y), "h", m.k_out)
    return path.close()


def upsilon(m):
    width = m.v(446, 512, light=432, black=566)
    stem = m.stem
    outer_y = m.v(236, 248)
    shape = cup(m, width, stem, XH, outer_y, outer_y - m.v(4, 12), -m.ov, m.thin - m.ov)
    return spaced(m, [shape], width, m.v(62, 48), m.v(62, 48), capital=False)


def phi(m):
    width = m.v(604, 680, light=584, black=790)
    stem = m.stem * m.v(1.0, 1.0, light=1.0, black=0.94)
    centre = width / 2
    cuts = (centre - stem / 2, centre + stem / 2)
    shapes = ring(0, -m.ov, width, XH + m.ov, m.round * m.v(1.0, 0.96, light=1.0, black=0.88), m.thin, m.k_out, m.k_in, cuts)
    shapes.append(rect(centre - stem / 2, DESC, centre + stem / 2, ASC))
    return spaced(m, shapes, width, "round", "round")


def chi(m):
    width = m.v(452, 520, light=438, black=586)
    height = XH - DESC
    stroke = band_width(width, height, m.diag)
    shapes = [
        band((0, XH), (width - stroke, DESC), stroke),
        band((width - stroke, XH), (0, DESC), stroke),
    ]
    return spaced(m, shapes, width, "diagonal", "diagonal")


def psi(m):
    width = m.v(580, 660, light=560, black=770)
    stem = m.stem * m.v(1.0, 1.0, light=1.0, black=0.94)
    side = m.stem * m.v(0.96, 0.9, light=0.98, black=0.82)
    centre = width / 2
    outer_y = m.v(232, 246)
    shape = cup(m, width, side, XH, outer_y, outer_y - m.v(4, 12), -m.ov, m.thin - m.ov)
    return spaced(m, [shape, rect(centre - stem / 2, DESC, centre + stem / 2, ASC)], width, m.v(58, 46), m.v(58, 46), capital=False)


def omega(m):
    width = m.v(712, 812, light=686, black=884)
    side = m.stem
    middle = width / 2
    post = m.stem * m.v(0.9, 0.86, black=0.82)
    post_top = m.v(318, 312, light=320, black=306)
    outer_y = m.v(220, 232)
    inner_y = outer_y - m.v(4, 12)
    floor = m.thin - m.ov
    bowl_right = middle + post / 2
    bowl_centre = bowl_right / 2
    inner_left = (side + middle - post / 2) / 2
    inner_right = width - inner_left
    left_turn = reach(quarter((bowl_centre, -m.ov), (bowl_right, outer_y), "h", m.k_out), 0, middle)
    right_turn = reach(quarter((width - bowl_centre, -m.ov), (width - bowl_right, outer_y), "h", m.k_out), 0, middle)
    path = Path((0, XH))
    path.to((side, XH))
    path.to((side, inner_y))
    path.arc((inner_left, floor), "v", m.k_in)
    path.arc((middle - post / 2, inner_y), "h", m.k_in)
    path.to((middle - post / 2, post_top))
    path.to((middle + post / 2, post_top))
    path.to((middle + post / 2, inner_y))
    path.arc((inner_right, floor), "v", m.k_in)
    path.arc((width - side, inner_y), "h", m.k_in)
    path.to((width - side, XH))
    path.to((width, XH))
    path.to((width, outer_y))
    path.arc((width - bowl_centre, -m.ov), "v", m.k_out)
    path.bez(right_turn)
    path.bez(flip(left_turn))
    path.arc((0, outer_y), "h", m.k_out)
    return spaced(m, [path.close()], width, m.v(56, 44), m.v(56, 44), capital=False)


LETTERS = {
    "Alpha": (0x391, capitals.capital_a),
    "Beta": (0x392, capitals.capital_b),
    "Gamma": (0x393, capital_gamma),
    "Delta": (0x394, capital_delta),
    "Epsilon": (0x395, capitals.capital_e),
    "Zeta": (0x396, capitals.capital_z),
    "Eta": (0x397, capitals.capital_h),
    "Theta": (0x398, capital_theta),
    "Iota": (0x399, capitals.capital_i),
    "Kappa": (0x39A, capitals.capital_k),
    "Lambda": (0x39B, capital_lambda),
    "Mu": (0x39C, capitals.capital_m),
    "Nu": (0x39D, capitals.capital_n),
    "Xi": (0x39E, capital_xi),
    "Omicron": (0x39F, capitals.capital_o),
    "Pi": (0x3A0, capital_pi),
    "Rho": (0x3A1, capitals.capital_p),
    "Sigma": (0x3A3, capital_sigma),
    "Tau": (0x3A4, capitals.capital_t),
    "Upsilon": (0x3A5, capitals.capital_y),
    "Phi": (0x3A6, capital_phi),
    "Chi": (0x3A7, capitals.capital_x),
    "Psi": (0x3A8, capital_psi),
    "alpha": (0x3B1, alpha),
    "beta": (0x3B2, beta),
    "gamma": (0x3B3, gamma),
    "delta": (0x3B4, delta),
    "epsilon": (0x3B5, epsilon),
    "zeta": (0x3B6, zeta),
    "eta": (0x3B7, eta),
    "theta": (0x3B8, theta),
    "iota": (0x3B9, iota),
    "kappa": (0x3BA, latin.kgreenlandic),
    "lambda": (0x3BB, lamda),
    "uni03BC": (0x3BC, symbols.mu),
    "nu": (0x3BD, nu),
    "xi": (0x3BE, xi),
    "omicron": (0x3BF, lowercase.letter_o),
    "rho": (0x3C1, rho),
    "sigma1": (0x3C2, final_sigma),
    "sigma": (0x3C3, sigma),
    "tau": (0x3C4, tau),
    "upsilon": (0x3C5, upsilon),
    "phi": (0x3C6, phi),
    "chi": (0x3C7, chi),
    "psi": (0x3C8, psi),
    "omega": (0x3C9, omega),
}

TONOS_FOOT = 0.78
TONOS_CROWN = 1.14
TONOS_GAP = (92, 86, 94, 80)
TONOS_SIDE = (38, 30, 40, 24)
DIALYTIKA_GAP = (28, 24, 30, 20)
MARK_MARGIN = (10, 10, 12, 14)
WIDE_DOT = 0.9
TOP_BAND = 60
SMALL_TONOS = ((72, 82, 74, 88), (160, 168, 156, 172), (56, 62, 52, 66), (70, 112, 46, 148))
CAPITAL_TONOS = ((176, 184, 172, 190), (60, 66, 56, 70), (72, 114, 48, 150))


def per(m, values):
    regular, bold, light, black = values
    return m.v(regular, bold, light=light, black=black)


def wedge(height, run, stroke):
    factor = math.hypot(run, height) / height
    foot = stroke * TONOS_FOOT * factor
    crown = stroke * TONOS_CROWN * factor
    return polygon([(-run / 2 - foot / 2, 0), (-run / 2 + foot / 2, 0), (run / 2 + crown / 2, height), (run / 2 - crown / 2, height)])


def small_tonos(m):
    floor, height, run, stroke = (per(m, values) for values in SMALL_TONOS)
    return centred(shift([wedge(height, run, stroke)], 0, XH + floor))


def capital_tonos(m):
    height, run, stroke = (per(m, values) for values in CAPITAL_TONOS)
    return centred(shift([wedge(height, run, stroke)], 0, CAP - height))


def dots(m):
    return accents.dieresis(m, accents.small(m))


def wide_tier(m):
    tier = accents.small(m)
    left, right = bounds(small_tonos(m))
    dot = tier.dot * WIDE_DOT
    return replace(tier, dot=dot, dot_floor=tier.dot_floor + tier.dot - dot, pitch=right - left + 2 * per(m, DIALYTIKA_GAP) + dot)


def wide_dots(m):
    return accents.dieresis(m, wide_tier(m))


def stack_height(m):
    floor = per(m, SMALL_TONOS[0])
    return XH + whole(wide_tier(m).dot_floor - XH - floor)


def mark(draw):
    def build(m):
        return Glyph(draw(m), 0)

    return build


def spacing(*draws):
    def build(m):
        contours = [contour for draw in draws for contour in draw(m)]
        left, right = bounds(contours)
        return spaced(m, shift(contours, -left), right - left, m.v(50, 44), m.v(50, 44))

    return build


def spacing_layout(m):
    marks = wide_dots(m)
    left, right = bounds(marks)
    start = m.v(50, 44)
    return start - left, right - left + start + m.v(50, 44)


def spaced_dialytika(m):
    offset, advance = spacing_layout(m)
    return Glyph(shift(wide_dots(m), offset), advance)


def spaced_dialytika_tonos(m):
    offset, advance = spacing_layout(m)
    return Glyph(shift(wide_dots(m) + shift(small_tonos(m), 0, stack_height(m) - XH), offset), advance)


TONOS = mark(small_tonos)
TONOS_CASE = mark(capital_tonos)
DIALYTIKA = mark(dots)
DIALYTIKA_WIDE = mark(wide_dots)
MARKS = {
    "tonoscomb": (TONOS, XH),
    "tonoscomb.case": (TONOS_CASE, CAP),
    "dialytikacomb": (DIALYTIKA, XH),
    "dialytikacomb.wide": (DIALYTIKA_WIDE, XH),
}
BASES = {name: draw for name, (_, draw) in LETTERS.items()}
BASES.update({"Omega": maths.omega, "pi": maths.pi})
LOWER = [name for name in BASES if name[0].islower() or name == "uni03BC"]
UPPER = [name for name in BASES if name not in LOWER]


def top_of(glyph):
    return max(point[1] for contour in glyph.contours for point in contour.points())


@lru_cache(maxsize=None)
def lower_anchor(name, m):
    glyph = BASES[name](m)
    top = XH if top_of(glyph) <= XH + m.ov + 1 else ASC
    points = outline_array(glyph)
    xs = points[points[:, 1] >= top - TOP_BAND][:, 0]
    return whole((xs.min() + xs.max()) / 2), top


def nearest(first, second):
    return numpy.sqrt(((first[:, None, :] - second[None, :, :]) ** 2).sum(axis=2).min())


@lru_cache(maxsize=None)
def capital_place(name, m):
    glyph = BASES[name](m)
    tonos = capital_tonos(m)
    marks = outline_array(Glyph(tonos, 0), PLACE_STEP)
    floor = marks[:, 1].min()
    gap = per(m, TONOS_GAP)
    points = outline_array(glyph, PLACE_STEP)
    near = points[points[:, 1] >= floor - gap]
    near = near[near[:, 0] <= near[:, 0].min() + numpy.ptp(marks[:, 0]) + 2 * gap]
    low, high = near[:, 0].min() - 1000, near[:, 0].min()
    for _ in range(40):
        middle = (low + high) / 2
        if nearest(marks + (middle, 0), near) > gap:
            low = middle
        else:
            high = middle
    centre = whole(low)
    room = max(0, whole(per(m, TONOS_SIDE) - centre - marks[:, 0].min()))
    return centre, room


def roomy(name):
    def draw(m):
        glyph = BASES[name](m)
        room = capital_place(name, m)[1]
        return Glyph(shift(glyph.contours, room), glyph.advance + room)

    return draw


def overlaid(base, marks):
    def overlay(m, plain, drawn):
        contours = []
        for draw, place in marks:
            dx, dy = place(m, plain)
            contours += shift(slanted(draw, m).contours, dx + m.slope * dy, dy)
        return contours

    return Overlaid(base, overlay)


def capital_with_tonos(name):
    def place(m, plain):
        centre, room = capital_place(name, m)
        return centre + room, 0

    return overlaid(roomy(name), [(TONOS_CASE, place)])


CASE_DOTS = accents.GLYPHS["dieresiscomb.case.narrow"][1]


@lru_cache(maxsize=None)
def mark_room(name, m, kind):
    glyph = BASES[name](m)
    if kind == "case":
        centre = accents.top_x(name, glyph, m, True)
        left, right = bounds(CASE_DOTS(m).contours)
    else:
        centre = lower_anchor(name, m)[0]
        left, right = bounds(wide_dots(m) if kind == "wide" else dots(m))
    margin = per(m, MARK_MARGIN)
    return max(0, whole(margin - centre - left)), max(0, whole(centre + right + margin - glyph.advance))


def widened(name, kind):
    def draw(m):
        glyph = BASES[name](m)
        before, after = mark_room(name, m, kind)
        return Glyph(shift(glyph.contours, before), glyph.advance + before + after)

    return draw


def lower_with(name, *kinds):
    kind = ("wide" if "tonos" in kinds else "dots") if "dots" in kinds else None

    def place_dots(m, plain):
        return lower_anchor(name, m)[0] + (mark_room(name, m, kind)[0] if kind else 0), 0

    def place_tonos(m, plain):
        x, _ = place_dots(m, plain)
        return x, stack_height(m) - XH if kind else 0

    marks = []
    if kind:
        marks.append((DIALYTIKA_WIDE if kind == "wide" else DIALYTIKA, place_dots))
    if "tonos" in kinds:
        marks.append((TONOS, place_tonos))
    return overlaid(widened(name, kind) if kind else BASES[name], marks)


def capital_with_dots(name):
    def place(m, plain):
        return accents.top_x(name, BASES[name](m), m, True) + mark_room(name, m, "case")[0], 0

    return overlaid(widened(name, "case"), [(CASE_DOTS, place)])


CAPITAL_TONOS_LETTERS = [
    ("Alphatonos", 0x386, "Alpha"),
    ("Epsilontonos", 0x388, "Epsilon"),
    ("Etatonos", 0x389, "Eta"),
    ("Iotatonos", 0x38A, "Iota"),
    ("Omicrontonos", 0x38C, "Omicron"),
    ("Upsilontonos", 0x38E, "Upsilon"),
    ("Omegatonos", 0x38F, "Omega"),
]
LOWER_MARKED = [
    ("iotadieresistonos", 0x390, "iota", ("dots", "tonos")),
    ("alphatonos", 0x3AC, "alpha", ("tonos",)),
    ("epsilontonos", 0x3AD, "epsilon", ("tonos",)),
    ("etatonos", 0x3AE, "eta", ("tonos",)),
    ("iotatonos", 0x3AF, "iota", ("tonos",)),
    ("upsilondieresistonos", 0x3B0, "upsilon", ("dots", "tonos")),
    ("iotadieresis", 0x3CA, "iota", ("dots",)),
    ("upsilondieresis", 0x3CB, "upsilon", ("dots",)),
    ("omicrontonos", 0x3CC, "omicron", ("tonos",)),
    ("upsilontonos", 0x3CD, "upsilon", ("tonos",)),
    ("omegatonos", 0x3CE, "omega", ("tonos",)),
]
CAPITAL_DIALYTIKA = [
    ("Iotadieresis", 0x3AA, "Iota"),
]


SMALL_BREATH = ((70, 104, 50, 130), (74, 66, 80, 64))
CASE_BREATH = ((78, 114, 54, 142), (82, 74, 88, 70))
BREATH_DROP = (4, 4, 4, 4)
PAIR_GAP = (54, 46, 58, 40)
CASE_PAIR_GAP = (62, 54, 66, 46)
PERI = ((240, 280, 228, 310), (96, 116, 92, 132), (58, 86, 40, 108), (50, 72, 36, 88))
CASE_PERI = ((254, 294, 240, 324), (100, 120, 94, 136), (60, 88, 42, 112), (52, 74, 38, 92))
PERI_FLOOR = (84, 88, 84, 92)
PERI_LEAN = 66
PERI_STACK = (32, 36, 30, 42)
CASE_PERI_OVER = (40, 44, 38, 48)
YPO = ((52, 80, 38, 100), (150, 158, 146, 166), (30, 32, 28, 32), (46, 40, 48, 34))
ADSCRIPT = ((392, 396, 390, 400), (44, 48, 42, 50), 0.88)
ADSCRIPT_GAP = (52, 44, 56, 38)
ADSCRIPT_AFTER = (40, 30, 42, 24)
PSILI, DASIA, VARIA, OXIA, PERISPOMENI, DIALYTIKA_MARK, YPOGEGRAMMENI = "̓", "̔", "̀", "́", "͂", "̈", "ͅ"
BREATHINGS = {PSILI: "psili", DASIA: "dasia"}
ACCENT_MARKS = {VARIA: "variacomb", OXIA: "tonoscomb", PERISPOMENI: "perispomenicomb", YPOGEGRAMMENI: "ypogegrammenicomb"}
LENGTH_MARKS = {"̄": "macroncomb", "̆": "brevecomb"}
FOLLOWING = {OXIA: "oxia", VARIA: "varia", PERISPOMENI: "peri"}
NARROW_LETTERS = ("iota", "Iota")


def even(value):
    return 2 * whole(value / 2)


def comma_mark(m, sizes, rough):
    side, fall = (per(m, values) for values in sizes)
    shape = accents.tick_shape(side, fall)
    if rough:
        shape = turn([shape], side / 2, (side - fall) / 2)[0]
    return [shape], side, fall


def small_breath(m, rough):
    shapes, side, _ = comma_mark(m, SMALL_BREATH, rough)
    floor, height, _, _ = (per(m, values) for values in SMALL_TONOS)
    return centred(shift(shapes, 0, XH + floor + height - per(m, BREATH_DROP) - side))


def case_breath(m, rough):
    shapes, side, _ = comma_mark(m, CASE_BREATH, rough)
    return centred(shift(shapes, 0, CAP - side))


def small_varia(m):
    return mirror(small_tonos(m), 0)


def case_varia(m):
    return mirror(capital_tonos(m), 0)


def cap_arc(m, sizes, floor):
    width, rise, side, flat = (per(m, values) for values in sizes)
    return [
        ribbon(
            [
                Node((side / 2 - width / 2, floor), aim(PERI_LEAN), side, cut="h"),
                Node((0, floor + rise - flat / 2), RIGHT, flat),
                Node((width / 2 - side / 2, floor), aim(-PERI_LEAN), side, cut="h"),
            ],
            0.6,
        )
    ]


def small_peri(m):
    return cap_arc(m, PERI, XH + per(m, PERI_FLOOR))


def case_peri(m):
    return cap_arc(m, CASE_PERI, CAP)


def ypogegrammeni(m):
    stem, rise, inner, gap = (per(m, values) for values in YPO)
    shape = hook(m, stem, stem * 0.72, rise, stem + inner * 1.4 + stem * 0.3, inner)
    return shift([shape], -stem / 2, -gap - rise)


def adscript(m):
    height, inner, scale = per(m, ADSCRIPT[0]), per(m, ADSCRIPT[1]), ADSCRIPT[2]
    stem = m.stem * scale
    return [hook(m, stem, m.thin * scale, height, stem + inner * 1.15 + m.v(14, 12), inner)]


def ink_points(contours):
    return outline_array(Glyph(contours, 0), PLACE_STEP)


def top_y(contours):
    return max(point[1] for contour in contours for point in contour.points())


def bottom_y(contours):
    return min(point[1] for contour in contours for point in contour.points())


def beside(first, second, gap):
    left, right = ink_points(first), ink_points(second)
    start = left[:, 0].max() - right[:, 0].min()
    low, high = start - min(numpy.ptp(left[:, 0]), numpy.ptp(right[:, 0])) / 2, start + gap
    for _ in range(40):
        middle = (low + high) / 2
        if nearest(left, right + (middle, 0)) > gap:
            high = middle
        else:
            low = middle
    return high


@lru_cache(maxsize=None)
def small_pair(m, rough, grave):
    breath = small_breath(m, rough)
    accent = small_varia(m) if grave else small_tonos(m)
    reach = beside(breath, accent, per(m, PAIR_GAP))
    left, right = bounds(breath + shift(accent, reach))
    centre = (left + right) / 2
    return even(-centre), even(reach - centre)


def peri_lift(m, below):
    return even(top_y(below) + per(m, PERI_STACK) - bottom_y(small_peri(m)))


@lru_cache(maxsize=None)
def case_pair(m, rough, grave):
    accent = case_varia(m) if grave else capital_tonos(m)
    return even(beside(case_breath(m, rough), accent, per(m, CASE_PAIR_GAP)))


@lru_cache(maxsize=None)
def case_drop(m):
    _, rise, _, _ = (per(m, values) for values in CASE_PERI)
    return even(per(m, PERI_STACK) + rise - per(m, CASE_PERI_OVER))


def lowered_breath(m, rough):
    return shift(case_breath(m, rough), 0, -case_drop(m))


def paired(rough, grave):
    def draw(m):
        return shift(small_breath(m, rough), small_pair(m, rough, grave)[0])

    return draw


def breath_drawing(rough):
    def draw(m):
        return small_breath(m, rough)

    return draw


def case_breath_drawing(rough, lowered=False):
    def draw(m):
        return lowered_breath(m, rough) if lowered else case_breath(m, rough)

    return draw


POLY_MARKS = {
    "variacomb": (small_varia, XH, "tonos"),
    "perispomenicomb": (small_peri, XH, "tonos"),
    "ypogegrammenicomb": (ypogegrammeni, 0, "below"),
    "variacomb.case": (case_varia, CAP, "case_varia"),
    "perispomenicomb.case": (case_peri, CAP, "tonos"),
    "ypogegrammenicomb.case": (adscript, 0, "below"),
}
for _rough, _breath in ((False, "psili"), (True, "dasia")):
    POLY_MARKS[f"{_breath}comb"] = (breath_drawing(_rough), XH, "breath")
    POLY_MARKS[f"{_breath}comb.oxia"] = (paired(_rough, False), XH, "breath")
    POLY_MARKS[f"{_breath}comb.varia"] = (paired(_rough, True), XH, "breath")
    POLY_MARKS[f"{_breath}comb.case"] = (case_breath_drawing(_rough), CAP, f"case_{_breath}")
    for _kind in ("oxia", "varia"):
        POLY_MARKS[f"{_breath}comb.case.{_kind}"] = (case_breath_drawing(_rough), CAP, f"case_{_breath}_{_kind}")
    POLY_MARKS[f"{_breath}comb.case.peri"] = (case_breath_drawing(_rough, True), CAP, f"case_{_breath}_peri")
MARK_DRAWS = {name: mark(draw) for name, (draw, _, _) in POLY_MARKS.items()}
MARK_DRAWS.update({name: draw for name, (draw, _) in MARKS.items()})
MARK_CLASSES = {name: kind for name, (_, _, kind) in POLY_MARKS.items()}
MARK_CLASSES.update({name: "dots" if "dialytika" in name else "tonos" for name in MARKS})
ATTACH = {name: height for name, (_, height, _) in POLY_MARKS.items()}
ATTACH.update({name: height for name, (_, height) in MARKS.items()})
CODES = {"Omega": 0x3A9, "pi": 0x3C0}
CODES.update({name: code for name, (code, _) in LETTERS.items()})
LETTER_OF = {code: name for name, code in CODES.items()}


def case_group(key, m):
    if key == "tonos":
        return capital_tonos(m)
    if key == "case_varia":
        return case_varia(m)
    _, breath, *rest = key.split("_")
    rough = breath == "dasia"
    if not rest:
        return case_breath(m, rough)
    if rest[0] == "peri":
        lowered = lowered_breath(m, rough)
        return lowered + shift(case_peri(m), 0, top_y(lowered) + per(m, PERI_STACK) - CAP)
    grave = rest[0] == "varia"
    accent = case_varia(m) if grave else capital_tonos(m)
    return case_breath(m, rough) + shift(accent, case_pair(m, rough, grave))


@lru_cache(maxsize=None)
def group_place(name, key, m):
    glyph = BASES[name](m)
    marks = ink_points(case_group(key, m))
    floor = marks[:, 1].min()
    gap = per(m, TONOS_GAP)
    points = outline_array(glyph, PLACE_STEP)
    near = points[points[:, 1] >= floor - gap]
    near = near[near[:, 0] <= near[:, 0].min() + numpy.ptp(marks[:, 0]) + 2 * gap]
    low, high = near[:, 0].min() - 1000, near[:, 0].min()
    for _ in range(40):
        middle = (low + high) / 2
        if nearest(marks + (middle, 0), near) > gap:
            low = middle
        else:
            high = middle
    centre = even(low)
    room = max(0, even(per(m, TONOS_SIDE) - centre - marks[:, 0].min()))
    return centre, room


@lru_cache(maxsize=None)
def adscript_place(name, m):
    glyph = BASES[name](m)
    iota = ink_points(adscript(m))
    gap = per(m, ADSCRIPT_GAP)
    points = outline_array(glyph, PLACE_STEP)
    near = points[points[:, 1] <= iota[:, 1].max() + gap]
    edge = near[:, 0].max()
    low, high = edge - iota[:, 0].max(), edge + gap
    for _ in range(40):
        middle = (low + high) / 2
        if nearest(iota + (middle, 0), near) > gap:
            high = middle
        else:
            low = middle
    x = even(high)
    return x, max(0, even(x + iota[:, 0].max() + per(m, ADSCRIPT_AFTER) - glyph.advance))


@lru_cache(maxsize=None)
def below_x(name, m):
    glyph = BASES[name](m)
    if name == "eta":
        start, end = accents.ink_runs(glyph.contours, XH / 2)[0]
        return even((start + end) / 2)
    left, right = bounds(glyph.contours)
    return even((left + right) / 2)


def dots_centre(m):
    left, right = bounds(accents.GLYPHS["dieresis"][1](m).contours)
    return even((left + right) / 2)


@lru_cache(maxsize=None)
def spacing_group(m, rough, kind):
    if kind == "peri":
        breath, accent = small_breath(m, rough), (0, peri_lift(m, tuple(small_breath(m, rough))) + XH)
        drawn = shift(small_peri(m), 0, accent[1] - XH)
    else:
        offset, reach = small_pair(m, rough, kind == "varia")
        breath = shift(small_breath(m, rough), offset)
        accent = (reach, XH)
        drawn = shift(small_varia(m) if kind == "varia" else small_tonos(m), reach)
    left, right = bounds(breath + drawn)
    start = m.v(50, 44)
    return start - left, right - left + 2 * start, breath, accent


def spacing_breath(rough, kind):
    def draw(m):
        offset, advance, breath, _ = spacing_group(m, rough, kind)
        return Glyph(shift(breath, offset), advance)

    return draw


SPACING_BASES = {f"{breath}.{kind}": (rough, kind) for rough, breath in ((False, "psili"), (True, "dasia")) for kind in ("oxia", "varia", "peri")}


def stack_anchor(name, kind, m):
    if name.endswith(".case.varia"):
        return (case_pair(m, name.startswith("dasia"), True), CAP) if kind == "case_varia" else None
    if kind != "tonos":
        return None
    if name == "dialytikacomb.wide":
        return 0, stack_height(m)
    if name == "dialytikacomb":
        return 0, XH + peri_lift(m, tuple(dots(m)))
    if name in ("psilicomb", "dasiacomb"):
        return 0, XH + peri_lift(m, tuple(small_breath(m, name == "dasiacomb")))
    rough = name.startswith("dasia")
    if name.endswith(".case.peri"):
        return 0, top_y(lowered_breath(m, rough)) + per(m, PERI_STACK)
    if name.endswith(".case.oxia") or name.endswith(".case.varia"):
        return case_pair(m, rough, name.endswith("varia")), CAP
    if name.endswith(".oxia") or name.endswith(".varia"):
        return small_pair(m, rough, name.endswith("varia"))[1], XH
    return None


def base_anchor(base, kind, m):
    if base in SOFT_BASES:
        return accents.base_anchors(m)[base]["top"]
    if base in SPACING_BASES:
        rough, group = SPACING_BASES[base]
        offset, _, _, (x, y) = spacing_group(m, rough, group)
        return (offset + x, y) if kind == "tonos" else None
    if base == "dieresis":
        return (dots_centre(m), XH + peri_lift(m, tuple(dots(m)))) if kind == "tonos" else None
    if base == "dieresis.tonos":
        return (spacing_layout(m)[0], stack_height(m)) if kind == "tonos" else None
    if base in LOWER:
        if kind == "below":
            return below_x(base, m), 0
        return lower_anchor(base, m)
    if kind == "tonos":
        return capital_place(base, m)[0], CAP
    if kind == "below":
        return adscript_place(base, m)[0], 0
    if kind == "top":
        return accents.top_x(base, BASES[base](m), m, True), CAP
    return group_place(base, kind, m)[0], CAP


def class_of(name):
    return MARK_CLASSES.get(name, "top")


def attach_of(name, m):
    if name in ATTACH:
        return 0, ATTACH[name]
    return accents.mark_anchors(m)[name][0]


def placements(base, marks, m):
    placed = []
    for name in marks:
        kind = class_of(name)
        ax, ay = attach_of(name, m)
        point = None
        if placed:
            previous, px, py = placed[-1]
            stack = stack_anchor(previous, kind, m)
            if stack:
                point = (px + stack[0], py + stack[1])
        if point is None:
            point = base_anchor(base, kind, m)
        placed.append((name, point[0] - ax, point[1] - ay))
    return placed


def mark_drawing(name):
    if name in MARK_DRAWS:
        return MARK_DRAWS[name]
    return accents.GLYPHS[name][1]


def above(marks):
    return tuple(name for name in marks if class_of(name) != "below")


def room_key(base, marks):
    shown = above(marks) if base in UPPER else tuple(name.replace("dasia", "psili") for name in above(marks))
    return shown, "ypogegrammenicomb.case" in marks


EXISTING_ROOMS = {(): None, ("tonoscomb",): None, ("dialytikacomb",): "dots"}


@lru_cache(maxsize=None)
def rooms_for(base, key, m):
    shown, adscripted = key
    after_room = adscript_place(base, m)[1] if adscripted else 0
    if base in UPPER:
        if not shown:
            return 0, after_room
        kind = class_of(shown[0])
        if kind == "tonos":
            return capital_place(base, m)[1], after_room
        if kind != "top":
            return group_place(base, kind, m)[1], after_room
    elif shown[:1] == ("dialytikacomb.wide",):
        return mark_room(base, m, "wide")
    elif shown in EXISTING_ROOMS:
        kind = EXISTING_ROOMS[shown]
        return mark_room(base, m, kind) if kind else (0, 0)
    contours = []
    for name, dx, dy in placements(base, shown, m):
        contours += shift(mark_drawing(name)(m).contours, dx, dy)
    left, right = bounds(contours)
    margin = per(m, MARK_MARGIN)
    advance = BASES[base](m).advance
    return max(0, even(margin - left)), max(0, even(right + margin - advance)) + after_room


def base_drawing(base):
    if base in BASES:
        return BASES[base]
    if base in SPACING_BASES:
        return SPACING_DRAWS[base]
    if base == "dieresis.tonos":
        return spaced_dialytika
    return accents.GLYPHS[base][1]


@lru_cache(maxsize=None)
def roomed(base, key):
    plain = base_drawing(base)

    def draw(m):
        glyph = plain(m)
        before, after = rooms_for(base, key, m)
        return Glyph(shift(glyph.contours, before), glyph.advance + before + after)

    return draw


def composed(base, marks):
    key = room_key(base, marks)
    roomy_base = roomed(base, key) if base in BASES else base_drawing(base)

    def overlay(m, plain, drawn):
        before = rooms_for(base, key, m)[0] if base in BASES else 0
        contours = []
        for name, dx, dy in placements(base, marks, m):
            contours += shift(slanted(mark_drawing(name), m).contours, before + dx + m.slope * dy, dy)
        return contours

    return Overlaid(roomy_base, overlay)


def shaped(base, chars):
    upper = base in UPPER
    names = []
    for index, char in enumerate(chars):
        following = chars[index + 1] if index + 1 < len(chars) else None
        if char in BREATHINGS:
            name = BREATHINGS[char] + "comb"
            if upper:
                name += ".case" + (f".{FOLLOWING[following]}" if following in FOLLOWING else "")
            elif following in (OXIA, VARIA):
                name += f".{FOLLOWING[following]}"
        elif char == DIALYTIKA_MARK:
            name = "dialytikacomb.wide" if following in (OXIA, VARIA) else "dialytikacomb"
        elif char in ACCENT_MARKS:
            name = ACCENT_MARKS[char] + (".case" if upper else "")
        else:
            name = LENGTH_MARKS[char] + (".case" if upper else "") + (".narrow" if base in NARROW_LETTERS else "")
        names.append(name)
    return names


def glyph_name(code):
    words = unicodedata.name(chr(code)).split()
    if words[1] == "CAPITAL":
        return words[3].capitalize() + "".join(word.lower() for word in words[5:] if word != "AND")
    if words[1] == "SMALL":
        return words[3].lower() + "".join(word.lower() for word in words[5:] if word != "AND")
    return "".join(word.lower() for word in words[1:] if word != "AND")


COMBINING_CODES = {"psilicomb": 0x313, "dasiacomb": 0x314, "perispomenicomb": 0x342, "ypogegrammenicomb": 0x345}
SPACING_LETTERS = {0x1FBF: "psili", 0x1FFE: "dasia", 0xA8: "dieresis"}
ABOVE_MARKS = [name for name in COMBINING_CODES if ATTACH[name]]
SOFT_BASES = ("dotlessi", "dotlessj")


def spacing_base(base, chars):
    if base in ("psili", "dasia"):
        return f"{base}.{FOLLOWING[chars[0]]}"
    if chars[0] in (OXIA, VARIA):
        return "dieresis.tonos"
    return base


def polytonic():
    glyphs = {}
    existing = {code: name for name, code, _ in CAPITAL_TONOS_LETTERS + CAPITAL_DIALYTIKA}
    existing.update({code: name for name, code, _, _ in LOWER_MARKED})
    existing.update({0x385: "dieresistonos", 0xB4: "acute", 0x60: "grave", 0x3B9: "iota"})
    for code in range(0x1F00, 0x2000):
        char = chr(code)
        if unicodedata.category(char) == "Cn":
            continue
        name = glyph_name(code)
        decomposition = unicodedata.decomposition(char)
        if decomposition and " " not in decomposition and not decomposition.startswith("<"):
            glyphs[name] = (code, ("same", existing[int(decomposition, 16)]))
            continue
        parts = unicodedata.normalize("NFD", char)
        if len(parts) == 1:
            glyphs[name] = (code, ("spacing", None))
            continue
        first, chars = ord(parts[0]), parts[1:]
        if first in SPACING_LETTERS:
            base = spacing_base(SPACING_LETTERS[first], chars)
            marks = shaped(base, chars)
            if base == "dieresis.tonos" and marks[0] == "tonoscomb":
                glyphs[name] = (code, ("same", "dieresistonos"))
                continue
            glyphs[name] = (code, ("composed", (base, tuple(marks))))
            continue
        base = LETTER_OF[first]
        glyphs[name] = (code, ("composed", (base, tuple(shaped(base, chars)))))
    return glyphs


SPACING_DRAWS = {name: spacing_breath(rough, kind) for name, (rough, kind) in SPACING_BASES.items()}
LONE_SPACING = {
    "koronis": spacing(breath_drawing(False)),
    "psili": spacing(breath_drawing(False)),
    "dasia": spacing(breath_drawing(True)),
    "perispomeni": spacing(small_peri),
}
POLYTONIC = polytonic()


def register():
    glyphs = dict(LETTERS)
    for name, code, base in CAPITAL_TONOS_LETTERS:
        glyphs[name] = (code, capital_with_tonos(base))
    for name, code, base in CAPITAL_DIALYTIKA:
        glyphs[name] = (code, capital_with_dots(base))
    glyphs["Upsilondieresis"] = (0x3AB, accents.accented_letter("Upsilon", capitals.capital_y, "dieresis", True))
    for name, code, base, kinds in LOWER_MARKED:
        glyphs[name] = (code, lower_with(base, *kinds))
    glyphs["tonos"] = (0x384, spacing(small_tonos))
    glyphs["dieresistonos"] = (0x385, spaced_dialytika_tonos)
    glyphs["dieresis.tonos"] = (None, spaced_dialytika)
    for name, (draw, _) in MARKS.items():
        glyphs[name] = (None, draw)
    outside = {"acute": accents.GLYPHS["acute"][1], "grave": punctuation.grave}
    for name, (code, (kind, data)) in POLYTONIC.items():
        if kind == "same":
            draw = glyphs[data][1] if data in glyphs else outside[data]
        elif kind == "spacing":
            draw = LONE_SPACING[name]
        else:
            draw = composed(*data)
        glyphs[name] = (code, draw)
    for name, draw in SPACING_DRAWS.items():
        glyphs[name] = (None, draw)
    for name in POLY_MARKS:
        glyphs[name] = (COMBINING_CODES.get(name), MARK_DRAWS[name])
    return glyphs


def ano_teleia(m):
    side = punctuation.square(m)
    return spaced(m, [rect(0, XH - side, side, XH)], side, punctuation.gap(m), punctuation.gap(m))


KAI_DEPTH = (168, 168, 168, 172)
KAI_LEAN = 54
KAI_LAP = 12


def lower_numeral(m):
    return shift(capital_tonos(m), 0, -CAP)


def kai_tail(contours, m):
    found = []
    for index, contour in enumerate(contours):
        corners = list(contour.corners())
        for position, point in enumerate(corners):
            if abs(point[1]) < 0.5:
                neighbours = [corners[position - 1], corners[(position + 1) % len(corners)]]
                above = [other for other in neighbours if other[1] > 0.5]
                if above:
                    found.append((point, above[0]))
    (left, left_up), (right, right_up) = sorted(found, key=lambda pair: pair[0][0])[-2:]

    def lifted(point, up):
        t = KAI_LAP / (up[1] - point[1])
        return (point[0] + (up[0] - point[0]) * t, KAI_LAP)

    depth = m.v(*KAI_DEPTH)
    run = depth / math.tan(math.radians(KAI_LEAN))
    return polygon([lifted(left, left_up), lifted(right, right_up), right, (right[0] - run, -depth), (left[0] - run, -depth), left])


def kai(draw):
    def build(m):
        glyph = draw(m)
        return Glyph(glyph.contours + [kai_tail(glyph.contours, m)], glyph.advance)

    return build


GLYPHS = register()
GLYPHS["anoteleia"] = (0x387, ano_teleia)
GLYPHS["uni0374"] = (0x374, spacing(capital_tonos))
GLYPHS["uni0375"] = (0x375, spacing(lower_numeral))
GLYPHS["uni03CF"] = (0x3CF, kai(capitals.capital_k))
GLYPHS["uni03D7"] = (0x3D7, kai(latin.kgreenlandic))
OWN_MARKS = True
PLACE_STEP = 4
KERN_LIKE = {
    "Alpha": "A",
    "Beta": "B",
    "Delta": "A",
    "Epsilon": "E",
    "Zeta": "Z",
    "Eta": "H",
    "Theta": "O",
    "Iota": "I",
    "Kappa": "K",
    "Lambda": "A",
    "Mu": "M",
    "Nu": "N",
    "Omicron": "O",
    "Pi": "H",
    "Rho": "P",
    "Tau": "T",
    "Upsilon": "Y",
    "Chi": "X",
    "Upsilondieresis": "Y",
    "alpha": "a",
    "eta": "n",
    "kappa": "kgreenlandic",
    "uni03CF": "K",
    "uni03D7": "kgreenlandic",
    "uni03BC": "mu",
    "omicron": "o",
    "rho": "o",
}


LOWER_MODELS = {"alpha": "a", "epsilon": "epsilon", "eta": "n", "iota": "iota", "omicron": "o", "upsilon": "upsilon", "omega": "omega", "rho": "o"}
CAPITAL_MODELS = {"Alpha": "A", "Epsilon": "E", "Eta": "H", "Iota": "I", "Omicron": "O", "Upsilon": "Y", "Omega": "Omega", "Rho": "P"}
ASCENDERS = ["b", "d", "f", "h", "i", "k", "l", "t", "beta", "delta", "zeta", "theta", "lambda", "xi", "phi", "psi"]
SMALLEST_EASE = 6


def letter_marks():
    found = {name: (base, ("tonoscomb",) if "tonos" in kinds else ()) for name, _, base, kinds in LOWER_MARKED}
    found.update({name: (base, ("dialytikacomb.wide", "tonoscomb") if "tonos" in kinds else ("dialytikacomb",)) for name, _, base, kinds in LOWER_MARKED if "dots" in kinds})
    found.update({name: (base, ("tonoscomb.case",)) for name, _, base in CAPITAL_TONOS_LETTERS})
    found.update({name: (base, ("dieresiscomb.case.narrow",)) for name, _, base in CAPITAL_DIALYTIKA})
    for name, (_, (kind, data)) in POLYTONIC.items():
        if kind == "composed" and data[0] in BASES:
            found[name] = data
        elif kind == "same" and data in found:
            found[name] = found[data]
    return found


MARKED = letter_marks()
LOWER_LIKE = {
    name: LOWER_MODELS[base]
    for name, (base, marks) in MARKED.items()
    if base in LOWER_MODELS and LOWER_MODELS[base] not in BASES and "ypogegrammenicomb" not in marks
}
MIRRORED = {name: (LOWER_MODELS[base] if base in LOWER_MODELS else CAPITAL_MODELS[base]) for name, (base, marks) in MARKED.items() if name not in LOWER_LIKE and base in {**LOWER_MODELS, **CAPITAL_MODELS}}
EXISTING_LETTERS = {name for name, *_ in CAPITAL_TONOS_LETTERS + CAPITAL_DIALYTIKA}
MIRRORED = {name: model for name, model in MIRRORED.items() if name not in EXISTING_LETTERS}
KERN_LIKE.update(LOWER_LIKE)
KERN_LIKE["prosgegrammeni"] = "iota"


def mirror_sides(name):
    base, marks = MARKED[name]
    if base in LOWER_MODELS:
        return True, True
    shown = above(marks)
    beside = bool(shown) and class_of(shown[0]) != "top"
    return not beside, "ypogegrammenicomb.case" not in marks


def mirrored_pairs(master):
    from . import features as kerning

    first_classes, second_classes = kerning.widened_classes()
    exceptions = family_exceptions(master)
    lines = []
    for (one, other), value in sorted(exceptions.items()):
        for name, model in MIRRORED.items():
            left_side, right_side = mirror_sides(name)
            if right_side and one == model:
                lines.append(f"    pos {name} {other} {round(value)};")
            if left_side and other == model:
                lines.append(f"    pos {one} {name} {round(value)};")
    for first, second, regular, bold in kerning.PAIRS:
        value = kerning.class_kern(first, second, regular, bold, master)
        for name, model in MIRRORED.items():
            left_side, right_side = mirror_sides(name)
            if right_side and model in first_classes[first] and reaches_greek(second_classes[second]):
                lines.append(f"    pos {name} @second_{second} {value};")
            if left_side and model in second_classes[second]:
                lines.append(f"    pos @first_{first} {name} {value};")
    return lines


def exceptions_at(master):
    from . import features as kerning

    found = dict(kerning.floor_kerns(master))
    found.update(kerning.exception_values(master, kerning.all_like()))
    return found


def class_value(left, right, master):
    from . import features as kerning

    first_classes, second_classes = kerning.widened_classes()
    for first, second, regular, bold in kerning.PAIRS:
        if left in first_classes[first] and right in second_classes[second]:
            return kerning.class_kern(first, second, regular, bold, master)
    return 0


@lru_cache(maxsize=None)
def kin_table():
    from . import features as kerning
    from .glyphs import GLYPHS as everything

    found = {}
    for name, model in kerning.all_like().items():
        if name in everything and model in everything:
            found.setdefault(model, [model]).append(name)
    return found


def kin(name):
    return kin_table().get(name, [name])


def with_kin(pairs):
    found = {}
    for (one, other), value in pairs.items():
        for left in kin(one):
            for right in kin(other):
                found.setdefault((left, right), value)
    return found


@lru_cache(maxsize=None)
def family_exceptions(master):
    found = {each: with_kin(exceptions_at(each)) for each in family(master)}
    pairs = sorted({pair for values in found.values() for pair in values})
    return {pair: round(found[master].get(pair, class_value(*pair, master))) for pair in pairs}


def model_of(name):
    return LOWER_LIKE.get(name) or MIRRORED.get(name)


def partners(name):
    from . import features as kerning
    from .glyphs import GLYPHS as everything

    first_classes, second_classes = kerning.widened_classes()
    model = model_of(name)
    lefts, rights = set(ASCENDERS), set(ASCENDERS)
    for first, second, _, _ in kerning.PAIRS:
        if model in second_classes[second]:
            lefts.update(first_classes[first])
        if model in first_classes[first]:
            rights.update(second_classes[second])
    like = kerning.all_like()
    return (
        sorted(other for other in lefts if other in everything and other not in like),
        sorted(other for other in rights if other in everything and other not in like),
    )


def eased_letters():
    return [name for name, (base, marks) in MARKED.items() if base in LOWER_MODELS and above(marks)]


@lru_cache(maxsize=None)
def clearance(master):
    from . import features as kerning
    from .glyphs import render

    like = kerning.all_like()
    gap = master.v(*accents.ACCENT_CLEARANCE)
    floor = accents.mark_floor(False)
    measure = accents.cached_profile()
    found = {}
    for name in eased_letters():
        glyph = render(name, master)
        lefts, rights = partners(name)
        for others, marked_right in ((lefts, True), (rights, False)):
            for other in others:
                neighbour = render(other, master)
                left, right = (other, name) if marked_right else (name, other)
                left_glyph, right_glyph = (neighbour, glyph) if marked_right else (glyph, neighbour)
                floors = (floor - gap, floor) if marked_right else (floor, floor - gap)
                needed = accents.closest_kern(left_glyph, right_glyph, gap, *floors, measure)
                if needed is None:
                    continue
                plain = {name: model_of(name) or name, other: like.get(other, other)}
                value = kerning.pair_value(plain[left], plain[right], master)
                found[(left, right)] = max(value, needed) - value
    return found


def eased_pairs(master):
    deltas = {each: with_kin(clearance(each)) for each in family(master)}
    kept = sorted({pair for found in deltas.values() for pair, delta in found.items() if round(delta) >= SMALLEST_EASE})
    found = deltas[master]
    return {pair: round(found.get(pair, 0)) for pair in kept}


def left_kerning(model, master):
    from . import features as kerning

    first_classes, second_classes = kerning.widened_classes()
    found = {}
    for first, second, regular, bold in kerning.PAIRS:
        if model in second_classes[second]:
            value = kerning.class_kern(first, second, regular, bold, master)
            found.update({member: value for member in first_classes[first] if member not in found})
    for (one, other), value in family_exceptions(master).items():
        if other == model:
            found[one] = value
    return {name: value for name, value in found.items() if name not in MARKED}


def beside_marks():
    found = {}
    for base, sequences in marked_letters().items():
        if base in UPPER:
            for marks in sequences:
                shown = above(marks)
                if shown and class_of(shown[0]) != "top":
                    found.setdefault(base, set()).add(shown[0])
    for _, _, base in CAPITAL_TONOS_LETTERS:
        found.setdefault(base, set()).add("tonoscomb.case")
    return found


def sequence_entries(master):
    from . import features as kerning

    like = kerning.all_like()
    entries = []
    for (left, right), value in eased_pairs(master).items():
        marked_right = right in MARKED
        base, marks = MARKED[right if marked_right else left]
        shown = " ".join(above(marks))
        if marked_right:
            entries.append((left, value, f"{base} {shown}"))
        else:
            entries.append((base, value, f"{shown} {right}"))
    for base, firsts in sorted(beside_marks().items()):
        kerns = {each: left_kerning(like.get(base, base), each) for each in family(master)}
        lefts = sorted({left for found in kerns.values() for left, value in found.items() if value})
        for left in lefts:
            entries.append((left, -kerns[master].get(left, 0), f"{base} {glyph_set(sorted(firsts))}"))
    return entries


def reaches_greek(members):
    from . import features as kerning

    return any(member in GLYPHS or not kerning.letter_or_figure(member) for member in members)


def across_entries(master):
    from . import features as kerning

    like = kerning.all_like()
    first_classes, second_classes = kerning.widened_classes()
    bases = sorted({base for name, (base, marks) in MARKED.items() if mirror_sides(name)[1] and above(marks)})
    entries = []
    for base in bases:
        model = like.get(base, base)
        for (one, other), value in family_exceptions(master).items():
            if one == model and other not in MARKED:
                entries += [(base, value, f"{'@greek_marks_above ' * count}{other}") for count in (1, 2, 3)]
        for first, second, regular, bold in kerning.PAIRS:
            if model in first_classes[first] and reaches_greek(second_classes[second]):
                value = kerning.class_kern(first, second, regular, bold, master)
                entries += [(base, value, f"{'@greek_marks_above ' * count}@second_{second}") for count in (1, 2, 3)]
    return entries


def slotted(master, compute, prefix):
    members = family(master)
    columns = [compute(each) for each in members]
    here = members.index(master)
    slots, rules = [], []
    for row in zip(*columns):
        moved, _, context = row[0]
        values = tuple(value for _, value, _ in row)
        index = next((index for index, used in enumerate(slots) if used.get(moved, values) == values), len(slots))
        if index == len(slots):
            slots.append({})
        slots[index][moved] = values
        rules.append(f"        pos {moved}' lookup {prefix}_{index} {context};")
    lookups = {index: [f"    pos {moved} {values[here]};" for moved, values in used.items()] for index, used in enumerate(slots)}
    lines = []
    for index, found in sorted(lookups.items()):
        lines += [f"lookup {prefix}_{index} {{"] + found + [f"}} {prefix}_{index};"]
    return lines, rules


MARKS_ABOVE = sorted(name for name in MARK_CLASSES if class_of(name) != "below") + ["ypogegrammenicomb"]


def sequence_rules(master):
    return slotted(master, sequence_entries, "greek_ease")


def kerning_lines(master):
    ease_lookups, ease_rules = sequence_rules(master)
    across_lookups, across_rules = slotted(master, across_entries, "greek_across")
    lines = [f"@greek_marks_above = {glyph_set(MARKS_ABOVE)};"] + ease_lookups + across_lookups
    lines += ["feature kern {", "    lookup greek_kern_across {"] + across_rules + ["    } greek_kern_across;"]
    lines += ["    lookup greek_kern_mirror {"] + mirrored_pairs(master) + ["    } greek_kern_mirror;"]
    lines += ["    lookup greek_kern_clearance {"]
    lines += [f"        pos {left} {right} {value};" for (left, right), value in eased_pairs(master).items()]
    lines += ["    } greek_kern_clearance;", "    lookup greek_kern_sequences {"] + ease_rules
    lines += ["    } greek_kern_sequences;", "} kern;"]
    return lines


def glyph_set(names):
    return f"[{' '.join(names)}]"


def alternatives(name):
    return f"[{name} {name.replace('psili', 'dasia')}]" if "psili" in name else name


def single(label, pairs):
    return [f"lookup {label} {{"] + [f"    sub {source} by {target};" for source, target in pairs] + [f"}} {label};"]


def breathing_lookup(label, suffix, spacing=False):
    stem = "" if spacing else "comb"
    return single(label, [(f"{breath}{stem}", f"{breath}{stem}{suffix}") for breath in ("psili", "dasia")])


CASE_MARKS = [name for name in GLYPHS if name.split(".")[0].endswith("comb") and ".case" in name and name in MARK_CLASSES]


def substitutions():
    lines = single("greek_tonos", [("acutecomb", "tonoscomb")])
    lines += single("greek_tonos_case", [("[acutecomb acutecomb.case]", "tonoscomb.case")])
    lines += single("greek_varia", [("gravecomb", "variacomb")])
    lines += single("greek_varia_case", [("[gravecomb gravecomb.case]", "variacomb.case")])
    lines += single("greek_peri_case", [("perispomenicomb", "perispomenicomb.case")])
    lines += single("greek_ypo_case", [("ypogegrammenicomb", "ypogegrammenicomb.case")])
    lines += single("greek_dialytika", [("dieresiscomb", "dialytikacomb")])
    lines += single("greek_dialytika_wide", [("dieresiscomb", "dialytikacomb.wide")])
    lines += single("greek_spacing_dots", [("dieresis", "dieresis.tonos")])
    lines += single("greek_narrow", [(name, f"{name}.narrow") for name in ("macroncomb", "brevecomb")])
    lines += single("greek_case_narrow", [(f"{name}.case", f"{name}.case.narrow") for name in ("dieresiscomb", "macroncomb", "brevecomb")])
    for kind in ("oxia", "varia"):
        lines += breathing_lookup(f"greek_breath_{kind}", f".{kind}")
    lines += breathing_lookup("greek_breath_case", ".case")
    for kind in ("oxia", "varia", "peri"):
        lines += breathing_lookup(f"greek_breath_case_{kind}", f".case.{kind}")
        lines += breathing_lookup(f"greek_spacing_{kind}", f".{kind}", True)
    above = glyph_set(ABOVE_MARKS)
    lines += [
        f"@greek_lower = {glyph_set(LOWER)};",
        f"@greek_upper = {glyph_set(UPPER)};",
        f"@greek_case_marks = {glyph_set(CASE_MARKS)};",
        "feature ccmp {",
        "    lookup greek_marks {",
        "        sub @greek_lower dieresiscomb' lookup greek_dialytika_wide [acutecomb gravecomb];",
        "        sub @greek_lower dieresiscomb' lookup greek_dialytika;",
        "        sub @greek_lower [psilicomb dasiacomb]' lookup greek_breath_oxia acutecomb;",
        "        sub @greek_lower [psilicomb dasiacomb]' lookup greek_breath_varia gravecomb;",
        "        sub @greek_lower acutecomb' lookup greek_tonos;",
        "        sub @greek_lower gravecomb' lookup greek_varia;",
        "        sub @greek_lower [dialytikacomb.wide psilicomb.oxia dasiacomb.oxia] acutecomb' lookup greek_tonos;",
        "        sub @greek_lower [dialytikacomb.wide psilicomb.varia dasiacomb.varia] gravecomb' lookup greek_varia;",
        "        sub iota [macroncomb brevecomb]' lookup greek_narrow;",
        "        sub @greek_upper [psilicomb dasiacomb]' lookup greek_breath_case_oxia acutecomb;",
        "        sub @greek_upper [psilicomb dasiacomb]' lookup greek_breath_case_varia gravecomb;",
        "        sub @greek_upper [psilicomb dasiacomb]' lookup greek_breath_case_peri perispomenicomb;",
        "        sub @greek_upper [psilicomb dasiacomb]' lookup greek_breath_case;",
        "        sub @greek_upper acutecomb.case' lookup greek_tonos_case;",
        "        sub @greek_upper gravecomb.case' lookup greek_varia_case;",
        "        sub @greek_upper [psilicomb.case.oxia dasiacomb.case.oxia] acutecomb' lookup greek_tonos_case;",
        "        sub @greek_upper [psilicomb.case.varia dasiacomb.case.varia] gravecomb' lookup greek_varia_case;",
        "        sub @greek_upper [psilicomb.case.peri dasiacomb.case.peri] perispomenicomb' lookup greek_peri_case;",
        "        sub @greek_upper ypogegrammenicomb' lookup greek_ypo_case;",
        "        sub @greek_upper @greek_case_marks ypogegrammenicomb' lookup greek_ypo_case;",
        "        sub @greek_upper @greek_case_marks @greek_case_marks ypogegrammenicomb' lookup greek_ypo_case;",
        "        sub Iota [dieresiscomb.case macroncomb.case brevecomb.case]' lookup greek_case_narrow;",
        "        sub [psili dasia]' lookup greek_spacing_oxia acutecomb;",
        "        sub [psili dasia]' lookup greek_spacing_varia gravecomb;",
        "        sub [psili dasia]' lookup greek_spacing_peri perispomenicomb;",
        "        sub [psili.oxia dasia.oxia] acutecomb' lookup greek_tonos;",
        "        sub [psili.varia dasia.varia] gravecomb' lookup greek_varia;",
        "        sub dieresis' lookup greek_spacing_dots [acutecomb gravecomb];",
        "        sub dieresis.tonos acutecomb' lookup greek_tonos;",
        "        sub dieresis.tonos gravecomb' lookup greek_varia;",
        "    } greek_marks;",
        "    lookup greek_soft_dots {",
        *[f"        sub [i j]' lookup comb_dotless {'@comb_below ' * count}{above};" for count in range(3)],
        *[f"        sub [iogonek idotbelow]' lookup comb_split_soft {'@comb_below ' * count}{above};" for count in range(3)],
        "    } greek_soft_dots;",
        "} ccmp;",
    ]
    return lines


def rooms(label, entries):
    lines = [f"lookup {label} {{"]
    for name, before, after in entries:
        lines.append(f"    pos {name} <{before} 0 {before + after} 0>;")
    lines.append(f"}} {label};")
    return lines


def marked_letters():
    found = {}
    for kind, data in (entry for _, entry in POLYTONIC.values()):
        if kind == "composed" and data[0] in BASES:
            found.setdefault(data[0], set()).add(data[1])
    return found


def lower_signatures():
    found = {}
    for base, sequences in marked_letters().items():
        if base not in LOWER:
            continue
        for marks in sequences:
            shown, _ = room_key(base, marks)
            if shown in EXISTING_ROOMS or shown[:1] == ("dialytikacomb.wide",):
                continue
            found.setdefault(shown, set()).add(base)
    return sorted(found.items(), key=lambda item: (-len(item[0]), item[0]))


def capital_kinds():
    found = {}
    for base, sequences in marked_letters().items():
        if base not in UPPER:
            continue
        for marks in sequences:
            shown = above(marks)
            if shown:
                found.setdefault(shown[0], set()).add(base)
    return found


def mark_kinds(base):
    kinds = {class_of(name) for marks in marked_letters().get(base, ()) for name in marks}
    if base in LOWER:
        return ["tonos", "dots", "breath", "below"] + (["top"] if "top" in kinds else [])
    return ["tonos"] + sorted(kind for kind in kinds if kind not in ("tonos", "top"))


def class_name(kind):
    return "@mark_top" if kind == "top" else f"@greek_{kind}"


def anchored(base, kinds, master):
    listed = []
    for kind in kinds:
        point = base_anchor(base, kind, master)
        if point:
            listed.append(f"{anchor(point, master)} mark {class_name(kind)}")
    return f"        pos base {base} {' '.join(listed)};"


def room_lines(master):
    lines = rooms("greek_room_tonos", [(name, capital_place(name, master)[1], 0) for name in UPPER])
    for kind in ("wide", "dots"):
        lines += rooms(f"greek_room_{kind}", [(name, *mark_room(name, master, kind)) for name in LOWER])
    lines += rooms("greek_room_case", [("Iota", *mark_room("Iota", master, "case"))])
    rules = []
    for index, (shown, bases) in enumerate(lower_signatures()):
        label = f"greek_room_lower_{index}"
        lines += rooms(label, [(base, *rooms_for(base, (shown, False), master)) for base in sorted(bases)])
        rules.append(f"        pos @greek_lower' lookup {label} {' '.join(alternatives(name) for name in shown)};")
    rules += [
        "        pos @greek_lower' lookup greek_room_wide dialytikacomb.wide;",
        "        pos @greek_lower' lookup greek_room_dots dialytikacomb;",
        "        pos @greek_upper' lookup greek_room_tonos tonoscomb.case;",
    ]
    for index, (first, bases) in enumerate(sorted(capital_kinds().items())):
        if first == "tonoscomb.case":
            continue
        label = f"greek_room_upper_{index}"
        lines += rooms(label, [(base, *rooms_for(base, ((first,), False), master)) for base in sorted(bases)])
        rules.append(f"        pos @greek_upper' lookup {label} {first};")
    adscripted = sorted(base for base, sequences in marked_letters().items() if any("ypogegrammenicomb.case" in marks for marks in sequences))
    lines += rooms("greek_room_adscript", [(base, 0, adscript_place(base, master)[1]) for base in adscripted])
    adscript_rules = [
        f"        pos @greek_upper' lookup greek_room_adscript {'@greek_case_marks ' * count}ypogegrammenicomb.case;" for count in range(3)
    ]
    return lines, rules, adscript_rules


def stacks(master):
    lines = []
    for name in MARK_CLASSES:
        listed = []
        for kind in sorted(set(MARK_CLASSES.values())):
            point = stack_anchor(name, kind, master)
            if point:
                listed.append(f"{anchor(point, master)} mark @greek_{kind}")
        if listed:
            lines.append(f"        pos mark {name} {' '.join(listed)};")
    return lines


def positions(master):
    lines = [f"markClass {name} {anchor((0, ATTACH[name]), master)} @greek_{kind};" for name, kind in MARK_CLASSES.items()]
    room_lookups, room_rules, adscript_rules = room_lines(master)
    lines += room_lookups
    lines += ["feature mark {", "    lookup greek_mark {"]
    for name in LOWER + UPPER:
        lines.append(anchored(name, mark_kinds(name), master))
    for name in ["dieresis", "dieresis.tonos"] + list(SPACING_BASES):
        lines.append(anchored(name, ["tonos"], master))
    for name in SOFT_BASES:
        lines.append(anchored(name, sorted({class_of(mark) for mark in ABOVE_MARKS}), master))
    left, right = bounds(accents.dotted_circle(master).contours)
    lines.append(f"        pos base dottedcircle {anchor((even((left + right) / 2), 0), master)} mark @greek_below;")
    lines += ["    } greek_mark;", "    lookup greek_room {"] + room_rules
    lines.append("        pos Iota' lookup greek_room_case dieresiscomb.case.narrow;")
    lines += ["    } greek_room;", "    lookup greek_adscript {"] + adscript_rules + ["    } greek_adscript;"]
    lines += ["} mark;", "feature mkmk {", "    lookup greek_stack {"] + stacks(master)
    lines += ["    } greek_stack;", "} mkmk;"]
    return lines


def local_feature():
    return [
        "feature locl {",
        "    script grek;",
        "    lookup greek_ano_teleia {",
        "        sub periodcentered by anoteleia;",
        "    } greek_ano_teleia;",
        "} locl;",
    ]


def features(master):
    return "\n".join(substitutions() + local_feature() + positions(master) + kerning_lines(master)) + "\n"


from .alternates import small_cap as small_cap_of

GREEK_NAMES = {code: name for table in (maths.GLYPHS, symbols.GLYPHS, GLYPHS) for name, (code, _) in table.items() if code is not None}
SMALL_CAP_CODES = [code for code in range(0x391, 0x3AA) if code in GREEK_NAMES]
KEPT_MARKS = {chr(0x308): "dieresiscomb"}
YPOGEGRAMMENI_MARK = chr(0x345)
TONOS_MARK = chr(0x301)
DISJUNCTIVE = {"smcp": (0x3AE, 0x1F75), "c2sc": (0x389, 0x1FCB)}
DISJUNCTIVE_SMALL_CAP = f"{GREEK_NAMES[0x389]}.sc"
DIPHTHONGS = {0x3B9: "αεου", 0x3C5: "αεο"}


def greek_cased(code):
    char = chr(code)
    return "GREEK" in unicodedata.name(char, "") and unicodedata.category(char) in ("Ll", "Lu", "Lt")


def small_cap_spelling(code):
    letter, *marks = unicodedata.normalize("NFD", chr(code))
    kept = [KEPT_MARKS[mark] for mark in marks if mark in KEPT_MARKS]
    adscript = [f"{GREEK_NAMES[0x399]}.sc" for mark in marks if mark == YPOGEGRAMMENI_MARK]
    return (f"{GREEK_NAMES[ord(letter.upper())]}.sc", *kept, *adscript)


SPELLED = {code: small_cap_spelling(code) for code in sorted(GREEK_NAMES) if greek_cased(code) and ord(unicodedata.normalize("NFD", chr(code))[0].upper()) in SMALL_CAP_CODES}
SMALL_CAP_LOWER = {GREEK_NAMES[code]: spelled[0] for code, spelled in SPELLED.items() if len(spelled) == 1 and unicodedata.category(chr(code)) == "Ll"}
SMALL_CAP_UPPER = {GREEK_NAMES[code]: spelled[0] for code, spelled in SPELLED.items() if len(spelled) == 1 and unicodedata.category(chr(code)) != "Ll"}
SMALL_CAP_MARKED = {GREEK_NAMES[code]: spelled for code, spelled in SPELLED.items() if len(spelled) > 1}
MARK_TWINS = {f"{GREEK_NAMES[code]}.sc": GREEK_NAMES[code + 0x20] for code in SMALL_CAP_CODES if code + 0x20 in GREEK_NAMES}
for code in SMALL_CAP_CODES:
    if f"{GREEK_NAMES[code]}.sc" not in GLYPHS:
        GLYPHS[f"{GREEK_NAMES[code]}.sc"] = (None, small_cap_of(GREEK_NAMES[code]))
GLYPHS[DISJUNCTIVE_SMALL_CAP] = (None, small_cap_of(GREEK_NAMES[0x389]))
KAI = GREEK_NAMES[0x3CF]
GLYPHS[f"{KAI}.sc"] = (None, small_cap_of(KAI))
MARK_TWINS[f"{KAI}.sc"] = GREEK_NAMES[0x3D7]


def accented_vowels(vowels):
    wanted = {vowel + TONOS_MARK for vowel in vowels + vowels.upper()}
    return [GREEK_NAMES[code] for code in sorted(GREEK_NAMES) if unicodedata.normalize("NFD", chr(code)) in wanted]


def small_cap_context():
    letters = [GREEK_NAMES[code] for code in sorted(GREEK_NAMES) if greek_cased(code)]
    lines = [f"@greek_letters = [{' '.join(letters)}];", "lookup greek_split_vowel {"]
    lines += [f"    sub {GREEK_NAMES[code]} by {GREEK_NAMES[code - 0x20]}.sc {KEPT_MARKS[chr(0x308)]};" for code in DIPHTHONGS]
    lines += ["} greek_split_vowel;", "lookup greek_diphthongs {"]
    lines += [f"    sub [{' '.join(accented_vowels(vowels))}] {GREEK_NAMES[code]}' lookup greek_split_vowel;" for code, vowels in DIPHTHONGS.items()]
    lines.append("} greek_diphthongs;")
    references = {"smcp": ["greek_diphthongs"], "c2sc": []}
    for tag, codes in DISJUNCTIVE.items():
        eta = " ".join(GREEK_NAMES[code] for code in codes)
        lines += [
            f"lookup greek_disjunctive_{tag} {{",
            f"    ignore sub @greek_letters [{eta}]';",
            f"    ignore sub [{eta}]' @greek_letters;",
            f"    sub [{eta}]' by {DISJUNCTIVE_SMALL_CAP};",
            f"}} greek_disjunctive_{tag};",
        ]
        references[tag].append(f"greek_disjunctive_{tag}")
    return lines, references
