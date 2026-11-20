import math
from dataclasses import dataclass, replace

from . import capitals, figures, latin, lowercase, marks
from .capitals import ess_shape
from .figures import terminal_high, terminal_low
from .geometry import Path, across, flip, intersect, quarter
from .lowercase import hooked_bowl_top, letter_c, stem_arch
from .marks import math_bearing, math_width
from .masters import CAP, DESC, UNITS, XH, interpolate, mix_at
from .oblique import Overlaid, stood
from .parts import Glyph, band, band_width, lobe, open_bowl, reach, spaced, vee
from .shapes import Node, aim, extent, mirror, oval, place, polygon, rect, ribbon, ring, shift, turn

MATH = 326
DOWN = (0, -1)
LEFT = (-1, 0)
RIGHT = (1, 0)
UP = (0, 1)
BULLET_SIZE = (222, 262, 204, 290)
BULLET_SIDE = (66, 54, 68, 46)
BULLET_ROUND = 0.56
DONG_GAP = (64, 56, 68, 50)
RUBLE_REACH = (106, 112, 102, 116)
RUBLE_BOWL = (300, 290, 304, 276)
RUBLE_LOW = (154, 150, 156, 146)
RUBLE_TAIL = (226, 240, 220, 250)
LIRA_WIDTH = (520, 584, 504, 636)
LIRA_POST = (104, 108, 102, 110)
LIRA_TURN = (250, 262, 246, 270)
LIRA_TERMINAL = (330, 322, 334, 316)
LIRA_LOW = (250, 250, 250, 252)
LIRA_GAP = (78, 74, 82, 76)
LIRA_REACH = (176, 186, 170, 194)
LIRA_RISE = 0.36
LIRA_BAR = (0.86, 0.74, 0.9, 0.6)
EURO_BAR = (0.84, 0.7, 0.9, 0.56)
EURO_REACH = (0.5, 0.42, 0.56, 0.24)
EURO_GAP = (126, 116, 130, 106)
HRYVNIA_BAR = (0.8, 0.62, 0.86, 0.48)
HRYVNIA_GAP = (74, 80, 78, 96)
HRYVNIA_OVER = (16, 14, 16, 12)
HRYVNIA_SPINE = (400, 640, 300, 760)
HRYVNIA_TERMINAL = (0, 30, 0, 56)
RUPEE_WIDTH = (500, 560, 484, 610)
RUPEE_BOWL = (34, 30, 36, 28)
RUPEE_BOTTOM = (306, 296, 310, 286)
RUPEE_ROUND = (168, 180, 164, 170)
RUPEE_INNER = (86, 40, 106, 24)
RUPEE_TIP = (36, 30, 38, 24)
RUPEE_SECOND = (114, 104, 118, 96)
TENGE_WIDTH = (516, 574, 500, 620)
TENGE_GAP = (66, 60, 70, 56)
MANAT_WIDTH = (560, 624, 544, 700)
MANAT_TOP = (500, 510, 496, 518)
MANAT_SIDE = (0.94, 0.9, 0.96, 0.86)
YEN_SNAP = 12
DOUBLE_ARROW_ARM = 1.2
DOUBLE_ARROW_GAP = (82, 70, 88, 58)
BOTH_ARROW_LENGTH = (760, 800, 744, 830)
UI_SIDE = (44, 36, 46, 30)
TABULAR_SIGNS = {
    "dollar": 1,
    "Euro": 1,
    "sterling": 1,
    "yen": 1,
    "cent": 1,
    "percent": 1.5,
    "plus": 1,
    "minus": 1,
    "equal": 1,
    "plusminus": 1,
    "multiply": 1,
    "divide": 1,
    "hyphen": 1,
}
TABULAR_SIGN_SIDE = (30, 24, 32, 18)
HAIR_SHARE = 0.6
OUTLINE_WEIGHT = (1.0, 0.86, 1.0, 0.72)
ERASE_GAP = 0.9
ERASE_SHARE = 0.55
COMMAND_SIZE = (640, 660, 632, 680)
COMMAND_WEIGHT = (0.9, 0.86, 0.94, 0.8)
COMMAND_LOOP = 1.08
COMMAND_RADIUS = 1.15
OPTION_WIDTH = (620, 650, 610, 680)
OPTION_HEIGHT = (500, 520, 492, 540)
OPTION_TURN = 0.3
OPTION_BAR = 1.0
SHIFT_WIDTH = (600, 630, 590, 660)
SHIFT_HEIGHT = (600, 620, 592, 640)
SHIFT_SHOULDER = 0.46
SHIFT_POST = 0.29
CONTROL_WIDTH = (520, 550, 510, 580)
CONTROL_RISE = 0.42
ERASE_WIDTH = (720, 750, 710, 780)
ERASE_HEIGHT = (520, 540, 512, 560)
ERASE_THIN = 0.86
RETURN_WIDTH = (600, 630, 590, 660)
RETURN_HEIGHT = (540, 560, 532, 580)
RETURN_ARM = (230, 240, 226, 250)
CHECK_WIDTH = (600, 630, 590, 660)
CHECK_HEIGHT = (560, 580, 552, 600)
CHECK_KNEE = 0.48
CHECK_FOOT = 0.36
BALLOT_SHARE = 0.92
SHAPE_SIZE = (560, 580, 552, 600)
TRIANGLE_HEIGHT = 0.88
CIRCLE_ROUND = 0.56
SQUARE_SHARE = 0.88
DIAGONAL_ARROW_LENGTH = (640, 660, 632, 680)
BITCOIN_STUB = (0.62, 0.6, 0.64, 0.56)
BITCOIN_REACH = (96, 100, 94, 104)
BITCOIN_SECOND = (230, 250, 222, 262)
CURRENCY_OVER = (40, 34, 42, 28)
WON_HIGH = (470, 476, 468, 480)
WON_LOW = (276, 270, 278, 264)
NAIRA_HIGH = (452, 458, 450, 462)
NAIRA_LOW = (260, 254, 262, 250)
PESO_HIGH = (604, 600, 606, 596)
PESO_LOW = (476, 470, 478, 466)
SHEKEL_WIDTH = (700, 770, 680, 900)
SHEKEL_LOW = (230, 240, 226, 250)
SHEKEL_SIDE = (0.9, 0.82, 0.92, 0.7)
SHEKEL_ROUND = 0.36
SHEKEL_INNER = 0.3


def math_glyph(m, shapes):
    return spaced(m, shapes, math_width(m), math_bearing(m), math_bearing(m))


def rotated(contours, cx, cy, degrees):
    angle = math.radians(degrees)
    cos, sin = math.cos(angle), math.sin(angle)

    def move(point):
        x, y = point[0] - cx, point[1] - cy
        return (cx + x * cos - y * sin, cy + x * sin + y * cos)

    return [contour.map(move) for contour in contours]


def stick(start, end, thickness):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    nx, ny = -dy / length * thickness / 2, dx / length * thickness / 2
    return polygon(
        [
            (start[0] + nx, start[1] + ny),
            (end[0] + nx, end[1] + ny),
            (end[0] - nx, end[1] - ny),
            (start[0] - nx, start[1] - ny),
        ]
    )


def minus(m):
    width = math_width(m)
    return math_glyph(m, [rect(0, MATH - m.bar / 2, width, MATH + m.bar / 2)])


def multiply(m):
    width = math_width(m)
    reach = m.v(160, 162)
    thickness = m.bar * m.v(1.04, 1.02)
    middle = width / 2
    shapes = [
        stick((middle - reach, MATH - reach), (middle + reach, MATH + reach), thickness),
        stick((middle - reach, MATH + reach), (middle + reach, MATH - reach), thickness),
    ]
    return math_glyph(m, shapes)


def divide(m):
    width = math_width(m)
    side = marks.square(m) * m.v(0.96, 0.72)
    lift = m.bar / 2 + m.v(62, 48) + side / 2
    left = (width - side) / 2
    shapes = [
        rect(0, MATH - m.bar / 2, width, MATH + m.bar / 2),
        rect(left, MATH + lift - side / 2, left + side, MATH + lift + side / 2),
        rect(left, MATH - lift - side / 2, left + side, MATH - lift + side / 2),
    ]
    return math_glyph(m, shapes)


def over_bar(m):
    centre = MATH + m.v(24, 36)
    return centre, centre - m.bar - m.v(82, 56)


def plusminus(m):
    width = math_width(m)
    bar = m.bar
    middle = width / 2
    centre, arm = over_bar(m)
    shapes = [
        rect(0, centre - bar / 2, width, centre + bar / 2),
        rect(middle - bar / 2, centre - arm, middle + bar / 2, centre + arm),
        rect(0, 0, width, bar),
    ]
    return math_glyph(m, shapes)


def bare(contours):
    left = min(point[0] for contour in contours for point in contour.corners())
    contours = shift(contours, -left)
    return contours, extent(contours)


def lessequal(m):
    chevron, width = marks.chevron(m)
    floor = min(point[1] for point in chevron.corners())
    gap = m.v(64, 60, light=66, black=56)
    shapes = shift([chevron], 0, m.bar + gap - floor) + [rect(0, 0, width, m.bar)]
    return marks.on_math_advance(m, shapes, width)


def greaterequal(m):
    glyph = lessequal(m)
    return Glyph(mirror(glyph.contours, glyph.advance / 2), glyph.advance)


def notequal(m):
    bars, width = bare(marks.equal(m).contours)
    rise = m.v(222, 230)
    run = rise * 0.42
    middle = width / 2
    stroke = across((2 * run, 2 * rise), m.v(72, 108, light=48, black=140))
    slash = band((middle + run - stroke / 2, MATH + rise), (middle - run - stroke / 2, MATH - rise), stroke)
    return math_glyph(m, bars + [slash])


def approxequal(m):
    wave, wide = bare(marks.asciitilde(m).contours)
    width = math_width(m)
    wave = [place(contour, 0, 0, width / wide) for contour in wave]
    lift = m.v(90, 98, black=112)
    return math_glyph(m, shift(wave, 0, lift) + shift(wave, 0, -lift))


def infinity(m):
    width = m.v(700, 764, black=824)
    height = m.v(372, 392, black=414)
    side = m.bar * m.v(1.08, 1.1, black=1.01)
    flat = m.bar * m.v(0.92, 0.9, black=0.81)
    cross = m.bar * m.v(1.04, 1.02, black=0.93)
    middle = width / 2
    centre = (middle, MATH)
    top, bottom = MATH + height / 2, MATH - height / 2
    rising = aim(m.v(50, 52))
    falling = (-rising[0], rising[1])
    loop = middle * 0.56
    reach = cross * 0.75

    def along(heading, distance):
        return (middle + heading[0] * distance, MATH + heading[1] * distance)

    def backward(heading):
        return (-heading[0], -heading[1])

    def loop_nodes(sign):
        x = middle + sign * loop
        return [
            Node((x, top - flat / 2), (sign, 0), flat),
            Node((middle + sign * (middle - side / 2), MATH), DOWN, side),
            Node((x, bottom + flat / 2), (-sign, 0), flat),
        ]

    crossing = ribbon(
        [
            Node(along(rising, reach), backward(rising), cross),
            Node(along(rising, -reach), backward(rising), cross, straight=True),
            *reversed([Node(node.point, backward(node.heading), node.thickness) for node in loop_nodes(-1)]),
            Node(along(falling, reach), backward(falling), cross),
            Node(along(falling, -reach), backward(falling), cross, straight=True),
        ],
        0.6,
    )
    right = ribbon(
        [
            Node(centre, rising, cross),
            Node(along(rising, reach), rising, cross, straight=True),
            *loop_nodes(1),
            Node(along(falling, -reach), falling, cross),
            Node(centre, falling, cross, straight=True),
        ],
        0.6,
    )
    return spaced(m, [crossing, right], width, m.v(44, 34), m.v(44, 34))


def prime_wedge(m):
    height = m.v(248, 256)
    top = m.v(90, 142, light=60, black=188)
    foot = m.v(46, 76, light=30, black=100)
    lean = m.v(66, 70)
    bottom = CAP - height
    return polygon([(0, bottom), (lean, CAP), (lean + top, CAP), (foot, bottom)]), lean + top, top


def minute(m):
    shape, width, _ = prime_wedge(m)
    return spaced(m, [shape], width, m.v(56, 44), m.v(56, 44))


def second(m):
    shape, width, top = prime_wedge(m)
    step = top + m.v(58, 46)
    return spaced(m, [shape, shift([shape], step)[0]], width + step, m.v(56, 44), m.v(56, 44))


def space_glyph(advance):
    def build(m):
        return Glyph([], advance(m))

    return build


def thin_space(m):
    return marks.space(m).advance * 0.64


def hair_space(m):
    return thin_space(m) * HAIR_SHARE


def em_share(share):
    def advance(m):
        return UNITS * share / m.narrowing

    return space_glyph(advance)


def figure_dash(m):
    length = tabular_width(m) - 2 * m.v(48, 40) / m.narrowing
    return figures.Figure([rect(0, marks.AXIS - m.bar / 2, length, marks.AXIS + m.bar / 2)], length, 0, 0)


def logicalnot(m):
    width = math_width(m)
    bar = m.bar
    top = MATH + m.v(66, 70)
    drop = m.v(176, 186)
    stem = bar * m.v(1.06, 1.06)
    shape = polygon(
        [
            (0, top),
            (width, top),
            (width, top - drop),
            (width - stem, top - drop),
            (width - stem, top - bar),
            (0, top - bar),
        ]
    )
    return math_glyph(m, [shape])


def brokenbar(m):
    width = m.v(78, 130, light=52, black=174)
    middle = (marks.TALL_TOP + marks.TALL_BOTTOM) / 2
    split = m.v(56, 52)
    shapes = [
        rect(0, marks.TALL_BOTTOM, width, middle - split),
        rect(0, middle + split, width, marks.TALL_TOP),
    ]
    return spaced(m, shapes, width, m.v(96, 78), m.v(96, 78))


def bullet(m):
    size = m.v(*BULLET_SIZE)
    shape = oval(0, marks.AXIS - size / 2, size, marks.AXIS + size / 2, BULLET_ROUND)
    return spaced(m, [shape], size, m.v(*BULLET_SIDE), m.v(*BULLET_SIDE))


def superior_stem(m):
    return m.v(62, 98, light=42, black=120)


def superior_thin(m):
    return m.v(54, 80, light=38, black=94)


def emblem_edge(m):
    return superior_stem(m) * m.v(0.85, 0.78, black=0.78)


def degree(m):
    size = m.v(240, 276)
    top = CAP + m.ov
    edge = superior_stem(m) * m.v(0.9, 0.78, black=0.75)
    shapes = ring(0, top - size, size, top, edge, edge * m.v(0.96, 0.94), m.k_out, m.k_in)
    return spaced(m, shapes, size, m.v(54, 44), m.v(54, 44))


def degree_letter(letter):
    def base(m):
        room = degree(m).advance
        glyph = letter(m)
        return Glyph(shift(glyph.contours, room), room + glyph.advance)

    def ring_mark(m, plain, drawn):
        return stood(degree(m), m).contours

    return Overlaid(base, ring_mark)


DAGGER_TOP = CAP
DAGGER_BOTTOM = DESC + 64


def dagger_parts(m, crossings):
    width = m.v(372, 410)
    stem = m.v(82, 136, light=54, black=180)
    bar = m.cap_bar
    middle = width / 2
    shapes = [rect(middle - stem / 2, DAGGER_BOTTOM, middle + stem / 2, DAGGER_TOP)]
    for centre in crossings:
        shapes.append(rect(0, centre - bar / 2, width, centre + bar / 2))
    return spaced(m, shapes, width, m.v(30, 24), m.v(30, 24))


def dagger_bar(m):
    return DAGGER_TOP - m.v(200, 206)


def dagger(m):
    return dagger_parts(m, [dagger_bar(m)])


def daggerdbl(m):
    return dagger_parts(m, [dagger_bar(m), DAGGER_TOP + DAGGER_BOTTOM - dagger_bar(m)])


def paragraph(m):
    stem = m.v(80, 128, light=52, black=168)
    gap = m.v(84, 112)
    right_stem = m.v(74, 112, light=48, black=146)
    bowl = m.v(270, 296)
    bottom = 0
    lobe_bottom = m.v(300, 290)
    right = bowl + gap + right_stem
    radius = (CAP - lobe_bottom) / 2
    rx = min(bowl * m.v(0.66, 0.62), bowl - stem)
    joint = bowl - stem / 2
    path = Path((joint, CAP))
    path.to((rx, CAP))
    path.arc((0, CAP - radius), "h", m.k_out)
    path.arc((rx, lobe_bottom), "v", m.k_out)
    path.to((joint, lobe_bottom))
    shapes = [
        path.close(),
        rect(bowl - stem, bottom, bowl, CAP),
        rect(right - right_stem, bottom, right, CAP),
        rect(bowl - stem, CAP - m.cap_bar, right, CAP),
    ]
    return spaced(m, shapes, right, m.v(36, 28), "cap")


def section_shapes(m, width, top, bottom):
    side = m.v(86, 132, light=56, black=158)
    flat = m.v(72, 98, light=48, black=110)
    spine = m.v(78, 114, light=52, black=126)
    end = m.v(80, 118, light=54, black=138)
    inset = m.v(10, 8)
    centre = (top + bottom) / 2
    middle = width / 2
    angle = m.v(20, 20)
    rise = m.v(124, 122)
    lap = m.v(40, 50)
    left = inset + side / 2
    right = width - inset - side / 2
    rising = aim(m.v(118, 120))

    def opposite(node):
        point = (width - node.point[0], 2 * centre - node.point[1])
        heading = (-node.heading[0], -node.heading[1])
        return Node(point, heading, node.thickness, node.straight, node.cut, node.arrive, node.leave)

    terminal = Node((width - inset - end / (2 * rising[1]) - m.v(6, 4), top - m.v(140, 150)), rising, end, cut="h")
    crown = Node((width * 0.5, top - flat / 2), LEFT, flat)
    shoulder = Node((left, top - m.v(166, 178)), aim(-90), side)
    upper_spine = Node((middle, centre + rise), aim(-angle), spine)
    flank = Node((right, centre - lap), DOWN, side, arrive=0.68, leave=0.68)
    upper = ribbon([terminal, crown, shoulder, upper_spine, flank, opposite(upper_spine)], 0.6)
    lower = turn([upper], middle, centre)[0]
    return [upper, lower]


def section(m):
    width = m.v(450, 540)
    shapes = section_shapes(m, width, CAP + m.ov, DESC + 30 - m.ov)
    return spaced(m, shapes, width, m.v(34, 26), m.v(34, 26))


def euro(m):
    width = m.v(548, 606, black=698)
    side = m.cap_round * m.v(1.0, 1.0, black=0.9)
    reach = m.v(84, 100)
    inner = (reach + side, m.cap_thin - m.ov, reach + width - side * 0.9, CAP + m.ov - m.cap_thin)
    shape = open_bowl(
        (reach, -m.ov, reach + width, CAP + m.ov),
        inner,
        m.k_out,
        m.k_in,
        terminal_high(m),
        terminal_low(m),
    )
    bar = m.cap_bar * m.v(*EURO_BAR)
    end = inner[0] + (inner[2] - inner[0]) * m.v(*EURO_REACH)
    lift = (bar + m.v(*EURO_GAP)) / 2
    middle = CAP / 2
    shapes = [
        shape,
        rect(0, middle + lift - bar / 2, end, middle + lift + bar / 2),
        rect(0, middle - lift - bar / 2, end, middle - lift + bar / 2),
    ]
    return spaced(m, shapes, extent([shape]), m.v(24, 18), m.v(30, 22))


def sterling(m):
    width = m.v(500, 560)
    stem = m.cap_stem
    flat = m.cap_thin
    post = m.v(150, 172)
    tip = (width - m.v(54, 80), CAP - m.v(176, 188))
    hook = ribbon(
        [
            Node(tip, aim(m.v(84, 82, black=84)), m.cap_round * m.v(0.92, 0.86), cut="h"),
            Node((post + (width - post) * 0.42, CAP + m.ov - flat / 2), LEFT, flat),
            Node((post, CAP - m.v(250, 262)), DOWN, stem),
            Node((post, m.cap_bar), DOWN, stem, straight=True),
        ],
        0.6,
    )
    bar = m.cap_bar * m.v(0.94, 0.9, black=0.8)
    centre = m.v(334, 330)
    shapes = [
        hook,
        rect(0, 0, width, m.cap_bar),
        rect(post - m.v(124, 126), centre - bar / 2, post + m.v(206, 220), centre + bar / 2),
    ]
    return spaced(m, shapes, width, m.v(30, 22), m.v(34, 26))


def yen(m):
    stem = m.cap_stem
    width = m.v(570, 640)
    middle = width / 2
    fork = m.v(330, 344)
    direction = (middle - stem / 2, fork - CAP)
    stroke = across(direction, m.cap_diag)
    notch = (middle, CAP + (middle - stroke) * direction[1] / direction[0])
    points = [
        (0, CAP),
        (stroke, CAP),
        notch,
        (width - stroke, CAP),
        (width, CAP),
        (middle + stem / 2, fork),
        (middle + stem / 2, 0),
        (middle - stem / 2, 0),
        (middle - stem / 2, fork),
    ]
    bar = m.cap_bar * m.v(0.86, 0.8, black=0.7)
    inset = m.v(112, 126)
    upper = fork - m.v(40, 44) - bar / 2
    lower = upper - bar - m.v(64, 60, black=66)
    if lower - bar / 2 < YEN_SNAP:
        lower = bar / 2
    shapes = [
        polygon(points),
        rect(inset, upper - bar / 2, width - inset, upper + bar / 2),
        rect(inset, lower - bar / 2, width - inset, lower + bar / 2),
    ]
    return spaced(m, shapes, width, "cap_diagonal", "cap_diagonal")


def dong(m):
    glyph = latin.dcroat(m)
    plain = lowercase.letter_d(m)
    left, right = latin.ink(plain)
    rule = m.bar * m.v(0.96, 0.9, light=1.0, black=0.84)
    top = -m.v(*DONG_GAP)
    return Glyph(glyph.contours + [rect(left, top - rule, right, top)], glyph.advance)


def hryvnia(m):
    shape, width = ess_shape(replace(m, mix=mix_at(m.v(*HRYVNIA_SPINE))), m.v(*HRYVNIA_TERMINAL))
    bar = m.cap_bar * m.v(*HRYVNIA_BAR)
    lift = (bar + m.v(*HRYVNIA_GAP)) / 2
    middle = CAP / 2
    over = m.v(*HRYVNIA_OVER)
    shapes = mirror([shape], width / 2) + [
        rect(-over, middle + lift - bar / 2, width + over, middle + lift + bar / 2),
        rect(-over, middle - lift - bar / 2, width + over, middle - lift + bar / 2),
    ]
    return spaced(m, shift(shapes, over), width + 2 * over, m.v(28, 20), m.v(28, 20))


def ruble(m):
    stem = m.cap_stem
    bar = m.cap_bar
    side = m.cap_round
    over = m.v(*RUBLE_REACH)
    post = over + stem
    right = over + m.v(500, 566, black=626)
    bottom = m.v(*RUBLE_BOWL)
    radius = (CAP - bottom) / 2
    middle = (CAP + bottom) / 2
    inner = radius - side * m.v(0.9, 0.92)
    bowl = Path((over + stem * 0.5, CAP))
    bowl.to((right - radius, CAP))
    bowl.arc((right, middle), "h", m.k_out)
    bowl.arc((right - radius, bottom), "v", m.k_out)
    bowl.to((0, bottom))
    bowl.to((0, bottom + bar))
    bowl.to((right - side - inner, bottom + bar))
    bowl.arc((right - side, middle), "h", m.k_in)
    bowl.arc((right - side - inner, CAP - bar), "v", m.k_in)
    bowl.to((over + stem * 0.8, CAP - bar))
    low = m.v(*RUBLE_LOW)
    cross = bar * m.v(0.94, 0.9, black=0.84)
    shapes = [
        rect(over, 0, post, CAP),
        bowl.close(),
        rect(0, low - cross / 2, over + m.v(*RUBLE_TAIL), low + cross / 2),
    ]
    return spaced(m, shapes, right, m.v(22, 16), m.v(30, 22))


def tenge(m):
    width = m.v(*TENGE_WIDTH)
    stem = m.cap_stem
    bar = m.cap_bar * m.v(0.92, 0.86, black=0.78)
    lower = CAP - bar - m.v(*TENGE_GAP)
    shapes = [
        rect(0, CAP - bar, width, CAP),
        rect(0, lower - bar, width, lower),
        rect((width - stem) / 2, 0, (width + stem) / 2, lower - bar / 2),
    ]
    return spaced(m, shapes, width, m.v(28, 20), m.v(28, 20))


def manat(m):
    width = m.v(*MANAT_WIDTH)
    side = m.cap_round * m.v(*MANAT_SIDE)
    flat = m.cap_thin
    stem = m.cap_stem * m.v(0.94, 0.88, black=0.8)
    top = m.v(*MANAT_TOP)
    shoulder = top - (width - side) / 2
    arch = ribbon(
        [
            Node((side / 2, 0), UP, side, cut="h"),
            Node((side / 2, shoulder), UP, side, straight=True),
            Node((width / 2, top + m.ov - flat / 2), RIGHT, flat),
            Node((width - side / 2, shoulder), DOWN, side),
            Node((width - side / 2, 0), DOWN, side, straight=True, cut="h"),
        ],
        0.6,
    )
    shapes = [arch, rect((width - stem) / 2, 0, (width + stem) / 2, CAP)]
    return spaced(m, shapes, width, m.v(30, 22), m.v(30, 22))


def slanted_bar(left, right, centre, x, rise, thickness):
    half = thickness / 2 * math.hypot(1, rise)
    low = centre + (left - x) * rise
    high = centre + (right - x) * rise
    return polygon([(left, low - half), (left, low + half), (right, high + half), (right, high - half)])


def lira(m):
    width = m.v(*LIRA_WIDTH)
    stem = m.cap_stem
    flat = m.cap_thin
    side = m.cap_round
    post = m.v(*LIRA_POST)
    centre = post + stem / 2
    bowl = ribbon(
        [
            Node((centre, CAP), DOWN, stem, cut="h"),
            Node((centre, m.v(*LIRA_TURN)), DOWN, stem, straight=True),
            Node(((centre + width - side / 2) / 2 + m.v(10, 8), flat / 2 - m.ov), RIGHT, flat),
            Node((width - side / 2, m.v(*LIRA_TERMINAL)), UP, side, cut="h"),
        ],
        0.6,
    )
    bar = m.cap_bar * m.v(*LIRA_BAR)
    low = m.v(*LIRA_LOW)
    high = low + bar + m.v(*LIRA_GAP)
    end = post + stem + m.v(*LIRA_REACH)
    shapes = [bowl] + [slanted_bar(0, end, height, centre, LIRA_RISE, bar) for height in (low, high)]
    return spaced(m, shapes, width, m.v(22, 16), m.v(30, 22))


def rupee(m):
    width = m.v(*RUPEE_WIDTH)
    bar = m.cap_bar
    side = m.cap_round
    edge = width - m.v(*RUPEE_BOWL)
    bottom = m.v(*RUPEE_BOTTOM)
    middle = (CAP + bottom) / 2
    round_out = m.v(*RUPEE_ROUND)
    round_in = m.v(*RUPEE_INNER)
    tip = (m.v(*RUPEE_TIP), bottom + bar)
    stroke = across((width - tip[0], tip[1]), m.cap_diag)
    for _ in range(8):
        stroke = across((width - stroke - tip[0], tip[1]), m.cap_diag)
    foot = (width - stroke, 0)
    join = intersect((width, 0), (width + tip[0] - foot[0], tip[1]), (0, bottom), (1, bottom))
    shoulder = reach(flip(quarter((edge - round_out, CAP), (edge, middle), "h", m.k_out)), 1, CAP - bar)
    path = Path((0, CAP))
    path.to((width, CAP))
    path.to((width, CAP - bar))
    path.to(shoulder[3])
    path.bez(flip(shoulder))
    path.arc((edge - round_out, bottom), "v", m.k_out)
    path.to(join)
    path.to((width, 0))
    path.to(foot)
    path.to(tip)
    path.to((edge - side - round_in, bottom + bar))
    path.arc((edge - side, middle), "h", m.k_in)
    path.arc((edge - side - round_in, CAP - bar), "v", m.k_in)
    path.to((0, CAP - bar))
    second = bar * m.v(0.9, 0.84, black=0.76)
    centre = CAP - bar - m.v(*RUPEE_SECOND)
    shapes = [path.close(), rect(0, centre - second / 2, width, centre + second / 2)]
    return spaced(m, shapes, width, m.v(24, 18), m.v(24, 18))


def cent(m):
    bowl, width = bare(letter_c(m).contours)
    height = XH
    stub = m.v(70, 112, light=46, black=146)
    reach = m.v(110, 108)
    left = width * 0.5 - stub / 2
    shapes = bowl + [
        rect(left, height - 30, left + stub, height + reach),
        rect(left, -reach, left + stub, 30),
    ]
    return spaced(m, shapes, width, "round", m.v(22, 14))


def currency(m):
    size = m.v(318, 356, black=392)
    edge = m.v(72, 108, light=48, black=124)
    reach = m.v(228, 248, black=266)
    thickness = m.v(70, 104, light=46, black=122)
    middle = reach
    low, high = middle - size / 2, middle + size / 2
    shapes = ring(low, MATH - size / 2, high, MATH + size / 2, edge, edge * m.v(0.92, 0.9), m.k_out, m.k_in)
    root = (size / 2 - edge / 2) * (4 + 3 * m.k_out) / 8
    diagonal = math.sqrt(0.5)
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        start = (middle + sx * root, MATH + sy * root)
        tip = reach - thickness * diagonal / 2
        end = (middle + sx * tip, MATH + sy * tip)
        shapes.append(stick(start, end, thickness))
    return spaced(m, shapes, reach * 2, m.v(30, 22), m.v(30, 22))


def angle(width, height, centre, thickness):
    rise = across((height / 2, width), thickness)
    reach = rise * width / (height / 2)
    points = [
        (width, centre + height / 2),
        (width, centre + height / 2 - rise),
        (reach, centre),
        (width, centre - height / 2 + rise),
        (width, centre - height / 2),
        (0, centre),
    ]
    return polygon(points), reach


def angle_quote_stroke(m):
    return m.v(74, 108, light=52, black=126)


def angle_quote(m):
    slope = math.radians(m.v(55, 56, light=54, black=57))
    height = m.v(356, 392, light=340, black=410)
    stroke = angle_quote_stroke(m)
    run = height / 2 / math.tan(slope)
    arm = stroke / math.sin(slope)
    centre = marks.AXIS
    top, bottom = centre + height / 2, centre - height / 2
    shape = polygon([(0, centre), (run, top), (run + arm, top), (arm, centre), (run + arm, bottom), (run, bottom)])
    return shape, run + arm, arm, slope


def angle_pair(m):
    shape, width, _, slope = angle_quote(m)
    pitch = angle_quote_stroke(m) + m.v(60, 58, light=60, black=58)
    lean = math.atan2(math.sin(slope), math.cos(slope) + math.sin(slope) * m.slope)
    upright = pitch / math.sin(slope)
    step = pitch / math.sin(lean)
    return shift([shape, shift([shape], step)[0]], (upright - step) / 2), width + upright


def guilsinglleft(m):
    shape, width, _, _ = angle_quote(m)
    return spaced(m, [shape], width, m.v(46, 36), m.v(46, 36))


def guilsinglright(m):
    shape, width, _, _ = angle_quote(m)
    return spaced(m, mirror([shape], width / 2), width, m.v(46, 36), m.v(46, 36))


def guillemotleft(m):
    shapes, width = angle_pair(m)
    return spaced(m, shapes, width, m.v(46, 36), m.v(46, 36))


def guillemotright(m):
    shapes, width = angle_pair(m)
    return spaced(m, mirror(shapes, width / 2), width, m.v(46, 36), m.v(46, 36))


def quotesinglbase(m):
    return spaced(m, [marks.tick(m)], marks.square(m), m.v(54, 44), m.v(54, 44))


def quotedblbase(m):
    shapes, width = marks.pair(m, marks.tick(m))
    return spaced(m, shapes, width, m.v(54, 44), m.v(54, 44))


def turned(glyph, height):
    return Glyph(turn(glyph.contours, glyph.advance / 2, height / 2), glyph.advance)


def exclamdown(m):
    return turned(marks.exclam(m), XH)


def respaced(m, contours, side):
    contours, width = bare(contours)
    return spaced(m, contours, width, side, side)


def questiondown(m):
    return respaced(m, turned(marks.question(m), XH).contours, m.v(40, 30))


def emblem(m, size, edge, flat):
    return ring(0, 0, size, size, edge, flat, m.k_out, m.k_in)


def copyright(m):
    size = CAP + 2 * m.ov
    centre = size / 2
    width = m.v(280, 326)
    height = m.v(372, 386)
    side = superior_stem(m) * m.v(0.98, 0.9, black=0.9)
    flat = superior_thin(m) * m.v(1.04, 1.0, black=1.03)
    left = centre - width / 2 + m.v(12, 10)
    bottom = centre - height / 2
    letter = open_bowl(
        (left, bottom, left + width, bottom + height),
        (left + side, bottom + flat, left + width - side * 0.9, bottom + height - flat),
        m.k_out,
        m.k_in,
        bottom + height * m.v(0.75, 0.72),
        bottom + height * m.v(0.25, 0.28),
    )
    edge = side * 0.92
    shapes = shift(emblem(m, size, edge, edge * 0.92) + [letter], 0, -m.ov)
    return spaced(m, shapes, size, m.v(36, 28), m.v(36, 28))


def registered(m):
    size = m.v(560, 560)
    centre = size / 2
    stem = superior_stem(m) * m.v(0.98, 0.76)
    side = stem * m.v(0.98, 0.92)
    bar = superior_thin(m) * m.v(0.86, 0.62)
    height = m.v(294, 274, black=270)
    width = m.v(222, 226, black=236)
    toe = m.v(4, 8)
    base = centre - height / 2
    left = centre - (width - toe) / 2
    waist = base + height * m.v(0.42, 0.4)
    right = left + width - m.v(14, 16)
    foot = left + width - toe
    shapes = [rect(left, base, left + stem, base + height)]
    shapes += lobe(m, left + stem * 0.5, left + stem * 0.8, right, base + height, waist, bar, side, rx=m.v(100, 108))
    knee = (left + width * m.v(0.44, 0.44), waist + bar * 0.5)
    leg = band_width(foot - knee[0], knee[1] - base, stem * m.v(1.0, 0.94))
    shapes.append(band(knee, (foot - leg, base), leg))
    edge = emblem_edge(m)
    shapes = shift(emblem(m, size, edge, edge * 0.92) + shapes, 0, CAP + m.ov - size)
    return spaced(m, shapes, size, m.v(36, 28), m.v(36, 28))


def trademark(m):
    height = m.v(330, 336)
    stem = superior_stem(m)
    bar = superior_thin(m)
    tee = m.v(236, 258, black=280)
    gap = m.v(64, 70)
    span = m.v(336, 376, black=420)
    base = CAP - height
    middle_x = tee / 2
    left = tee + gap
    thickness = stem * m.v(0.9, 0.82, light=0.88)
    inset = 0
    for _ in range(8):
        middle, stroke = vee(span - 2 * inset, thickness * m.v(1.15, 1.0), height, thickness)
        inset = max(0, stem - stroke)
    shapes = [
        rect(0, CAP - bar, tee, CAP),
        rect(middle_x - stem / 2, base, middle_x + stem / 2, CAP),
        rect(left, base, left + stem, CAP),
        rect(left + span - stem, base, left + span, CAP),
        shift([middle], left + inset, base)[0],
    ]
    return spaced(m, shapes, left + span, m.v(30, 24), m.v(30, 24))


@dataclass(frozen=True)
class ScaledMaster:
    stem: float
    round: float
    k_out: float
    k_in: float
    mix: float
    ov: float

    def v(self, regular, bold, light=None, black=None):
        return interpolate(self.mix, regular, bold, light, black)


def small_a(m, scale, stem, round, thin, thick):
    width = m.v(440, 508)
    crown_regular, crown_bold = 76, 110
    mix = (thin / scale - crown_regular) / (crown_bold - crown_regular)
    drawn = ScaledMaster(stem / scale, round / scale, m.k_out, m.k_in, mix, m.ov)
    top = place(hooked_bowl_top(drawn, width, m.v(406, 390, black=416)), 0, 0, scale, scale)
    width *= scale
    belly_top = m.v(322, 354, black=340) * scale
    belly = [
        oval(0, -m.ov * scale, width - stem * 0.5, belly_top, m.k_out),
        oval(round, thin * 0.95, width - stem * 0.75, belly_top - thick, m.k_in, hole=True),
    ]
    return [top] + belly, width


def ordinal_scale(m):
    return m.v(0.6, 0.63)


def ordinal_stem(m):
    return superior_stem(m) * m.v(1.0, 0.94, black=0.9)


def ordinal_thin(m):
    return superior_thin(m) * m.v(1.0, 0.86, black=0.82)


def ordfeminine(m):
    scale = ordinal_scale(m)
    stem = ordinal_stem(m)
    thin = ordinal_thin(m)
    shapes, width = small_a(m, scale, stem, stem * 1.02, thin, thin * m.v(0.94, 0.9))
    shapes = shift(shapes, 0, CAP - XH * scale)
    return spaced(m, shapes, width, m.v(40, 30), m.v(44, 34))


def ordmasculine(m):
    scale = ordinal_scale(m)
    width = m.v(476, 540) * scale
    base = CAP - XH * scale
    edge = ordinal_stem(m) * 1.04
    shapes = ring(0, base - m.ov * scale, width, CAP + m.ov * scale, edge, ordinal_thin(m), m.k_out, m.k_in)
    return spaced(m, shapes, width, m.v(40, 30), m.v(40, 30))


def mu(m):
    width = m.v(450, 520)
    stem = m.stem
    shapes = turn([stem_arch(m, 0, width)], width / 2, XH / 2)
    shapes += [rect(width - stem, 0, width, XH), rect(0, DESC, stem, XH / 2)]
    return spaced(m, shapes, width, "straight", "straight")


def perthousand(m):
    width = m.v(*marks.PERCENT_WIDTH)
    loop = m.v(*marks.PERCENT_LOOP)
    tall = m.v(*marks.PERCENT_TALL)
    edge = m.v(*marks.PERCENT_EDGE)
    flat = m.v(*marks.PERCENT_FLAT)
    gap = m.v(76, 76.64, light=220 / 3, black=69.6)
    small = loop * 0.92
    foot = loop * 0.6
    stroke = band_width(width - loop * 0.6 - foot, CAP, m.cap_diag * m.v(0.84, 0.82))
    shapes = ring(0, CAP + m.cap_ov - tall, loop, CAP + m.cap_ov, edge, flat, m.k_out, m.k_in)
    shapes += ring(width - small, -m.cap_ov, width, tall - m.cap_ov, edge, flat, m.k_out, m.k_in)
    shapes += ring(width + gap, -m.cap_ov, width + gap + small, tall - m.cap_ov, edge, flat, m.k_out, m.k_in)
    shapes.append(band((width - loop * 0.6 - stroke, CAP), (foot, 0), stroke))
    return spaced(m, shapes, width + gap + small, m.v(36, 28), m.v(36, 28))


def arrow_shapes(m):
    return arrow_of_length(m, m.v(660, 690))


def arrow_of_length(m, length):
    thickness = m.v(74, 116, light=50, black=152)
    arm = m.v(286, 296)
    diagonal = math.sqrt(0.5)
    tip = (length, 0)
    outer_up = (length - arm * diagonal, arm * diagonal)
    outer_down = (length - arm * diagonal, -arm * diagonal)
    inner_up = (outer_up[0] - thickness * diagonal, outer_up[1] - thickness * diagonal)
    inner_down = (outer_down[0] - thickness * diagonal, outer_down[1] + thickness * diagonal)
    notch = (length - thickness / diagonal, 0)
    head = polygon([tip, outer_up, inner_up, notch, inner_down, outer_down])
    shaft = rect(0, -thickness / 2, length - thickness, thickness / 2)
    span = arm * diagonal
    return [shaft, head], length, span


def arrow_head(m, length, arm):
    thickness = arrow_thickness(m)
    diagonal = math.sqrt(0.5)
    tip = (length, 0)
    outer_up = (length - arm * diagonal, arm * diagonal)
    outer_down = (length - arm * diagonal, -arm * diagonal)
    inner_up = (outer_up[0] - thickness * diagonal, outer_up[1] - thickness * diagonal)
    inner_down = (outer_down[0] - thickness * diagonal, outer_down[1] + thickness * diagonal)
    notch = (length - thickness / diagonal, 0)
    return polygon([tip, outer_up, inner_up, notch, inner_down, outer_down]), notch[0]


def arrow_thickness(m):
    return m.v(74, 116, light=50, black=152)


def shaft_end(m, notch, tip):
    thickness = double_thickness(m)
    offset = (m.v(*DOUBLE_ARROW_GAP) + thickness) / 2
    return (notch - offset + thickness / 2 + tip - offset - thickness / 2) / 2


def double_thickness(m):
    return arrow_thickness(m) * m.v(0.86, 0.8, light=0.9, black=0.72)


def double_shafts(m, start, end):
    thickness = double_thickness(m)
    offset = (m.v(*DOUBLE_ARROW_GAP) + thickness) / 2
    return [rect(start, sign * offset - thickness / 2, end, sign * offset + thickness / 2) for sign in (-1, 1)]


def double_arrow(m, length):
    head, notch = arrow_head(m, length, m.v(286, 296) * DOUBLE_ARROW_ARM)
    return [head] + double_shafts(m, 0, shaft_end(m, notch, length))


def double_both(m, length):
    head, notch = arrow_head(m, length, m.v(286, 296) * DOUBLE_ARROW_ARM)
    end = shaft_end(m, notch, length)
    return [head] + mirror([head], length / 2) + double_shafts(m, length - end, end)


def single_both(m, length):
    head, notch = arrow_head(m, length, m.v(286, 296))
    thickness = arrow_thickness(m)
    return [head] + mirror([head], length / 2) + [rect(thickness, -thickness / 2, length - thickness, thickness / 2)]


def arrow_glyph(m, shapes, length):
    return spaced(m, shift(shapes, 0, MATH), length, m.v(40, 32), m.v(40, 32))


def arrowdblright(m):
    length = m.v(660, 690)
    return arrow_glyph(m, double_arrow(m, length), length)


def arrowdblleft(m):
    length = m.v(660, 690)
    return arrow_glyph(m, mirror(double_arrow(m, length), length / 2), length)


def arrowboth(m):
    length = m.v(*BOTH_ARROW_LENGTH)
    return arrow_glyph(m, single_both(m, length), length)


def arrowdblboth(m):
    length = m.v(*BOTH_ARROW_LENGTH)
    return arrow_glyph(m, double_both(m, length), length)


def arrowright(m):
    shapes, length, _ = arrow_shapes(m)
    return spaced(m, shift(shapes, 0, MATH), length, m.v(40, 32), m.v(40, 32))


def arrowleft(m):
    shapes, length, _ = arrow_shapes(m)
    return spaced(m, mirror(shift(shapes, 0, MATH), length / 2), length, m.v(40, 32), m.v(40, 32))


def vertical_arrow(m, degrees):
    shapes, length, span = arrow_of_length(m, CAP)
    centre = CAP / 2
    shapes = rotated(shift(shapes, span - length / 2, centre), span, centre, degrees)
    return spaced(m, shapes, span * 2, m.v(40, 32), m.v(40, 32))


def arrowup(m):
    return vertical_arrow(m, 90)


def arrowdown(m):
    return vertical_arrow(m, -90)


def blank_figure(m):
    return figures.Figure([], 0, 0, 0)


def tabular_width(m):
    return figures.tabular(blank_figure)(m).advance


def tabular_punctuation(draw):
    def centred(m):
        glyph = draw(m)
        xs = [point[0] for contour in glyph.contours for point in contour.points()]
        return figures.Figure(shift(glyph.contours, -min(xs)), max(xs) - min(xs), 0, tabular_width(m) / 2)

    def build(m):
        glyph = figures.tabular(centred)(m)
        return Glyph(glyph.contours, glyph.advance / 2)

    return build


def punctuation_width(m):
    return marks.period(m).advance


def tabular_sign(name, share):
    def centred(m):
        from .glyphs import GLYPHS as everything

        draw = everything[name][1]
        room = tabular_width(m) * share - 2 * m.v(*TABULAR_SIGN_SIDE)
        contours = draw(m).contours
        left, right = ink_extent(contours)
        if right - left > room:
            sx = room / (right - left)
            narrow = figures.scaled_master(m, sx, 1, m.cap_stem, m.cap_round, m.cap_thin, m.cap_bar, m.cap_diag, figures.side(m))
            contours = figures.scaled(draw(narrow).contours, sx, 1)
            left, right = ink_extent(contours)
        return figures.Figure(shift(contours, -left), right - left, 0, tabular_width(m) * (1 - share))

    def build(m):
        glyph = figures.tabular(centred)(m)
        return Glyph(glyph.contours, glyph.advance * share)

    return build


def ink_extent(contours):
    xs = [point[0] for contour in contours for point in contour.points()]
    return min(xs), max(xs)


def tabular_blank(share):
    def build(m):
        return Glyph([], figures.tabular(blank_figure)(m).advance * share)

    return build


def ui_stroke(m):
    return arrow_thickness(m) * m.v(1.0, 0.94, light=1.0, black=0.86)


def mitred(points, thickness):
    half = thickness / 2
    lines = []
    for start, end in zip(points, points[1:]):
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        normal = (-(end[1] - start[1]) / length, (end[0] - start[0]) / length)
        lines.append((start, end, normal))
    sides = []
    for sign in (1, -1):
        offset = [((a[0] + n[0] * half * sign, a[1] + n[1] * half * sign), (b[0] + n[0] * half * sign, b[1] + n[1] * half * sign)) for a, b, n in lines]
        side = [offset[0][0]]
        for (a0, a1), (b0, b1) in zip(offset, offset[1:]):
            side.append(intersect(a0, a1, b0, b1))
        side.append(offset[-1][1])
        sides.append(side)
    return polygon(sides[0] + sides[1][::-1])


def inset(points, distance):
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1]))
    sign = 1 if area > 0 else -1
    lines = []
    for a, b in zip(points, points[1:] + points[:1]):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        normal = (-(b[1] - a[1]) / length * sign * distance, (b[0] - a[0]) / length * sign * distance)
        lines.append(((a[0] + normal[0], a[1] + normal[1]), (b[0] + normal[0], b[1] + normal[1])))
    return [intersect(*lines[index - 1], *lines[index]) for index in range(len(lines))]


def outline_stroke(m):
    return ui_stroke(m) * m.v(*OUTLINE_WEIGHT)


def outlined(points, thickness):
    hole = polygon(inset(points, thickness)[::-1])
    hole.hole = True
    return [polygon(points), hole]


def ui_glyph(m, shapes, width):
    return spaced(m, shapes, width, m.v(*UI_SIDE), m.v(*UI_SIDE))


def ui_centre():
    return CAP / 2


def command_key(m):
    stroke = ui_stroke(m) * m.v(*COMMAND_WEIGHT)
    loop = stroke * COMMAND_LOOP
    size = m.v(*COMMAND_SIZE)
    half = (size - loop) / (2 + 4 * COMMAND_RADIUS)
    radius = half * COMMAND_RADIUS
    tuck = loop * 0.25
    corner = ribbon(
        [
            Node((half, half - tuck), UP, loop),
            Node((half, half + radius), UP, loop, straight=True),
            Node((half + radius, half + 2 * radius), RIGHT, loop),
            Node((half + 2 * radius, half + radius), DOWN, loop),
            Node((half + radius, half), LEFT, loop),
            Node((half - tuck, half), LEFT, loop, straight=True),
        ],
        0.55,
    )
    loops = [corner] + rotated([corner], 0, 0, 90) + rotated([corner], 0, 0, 180) + rotated([corner], 0, 0, 270)
    sides = [
        rect(half - stroke / 2, -half, half + stroke / 2, half),
        rect(-half - stroke / 2, -half, -half + stroke / 2, half),
        rect(-half, half - stroke / 2, half, half + stroke / 2),
        rect(-half, -half - stroke / 2, half, -half + stroke / 2),
    ]
    reach = half + 2 * radius + loop / 2
    return ui_glyph(m, shift(loops + sides, reach, ui_centre()), 2 * reach)


def option_key(m):
    stroke = ui_stroke(m)
    width = m.v(*OPTION_WIDTH)
    height = m.v(*OPTION_HEIGHT)
    top, bottom = ui_centre() + height / 2 - stroke / 2, ui_centre() - height / 2 + stroke / 2
    turn = width * OPTION_TURN
    path = mitred([(0, top), (turn, top), (width - turn, bottom), (width, bottom)], stroke)
    bar = rect(width - turn * OPTION_BAR, top - stroke / 2, width, top + stroke / 2)
    return ui_glyph(m, [path, bar], width)


def shift_key(m):
    stroke = outline_stroke(m)
    width = m.v(*SHIFT_WIDTH)
    height = m.v(*SHIFT_HEIGHT)
    low = ui_centre() - height / 2
    shoulder = low + height * SHIFT_SHOULDER
    post = width * SHIFT_POST
    points = [
        (width / 2, low + height),
        (0, shoulder),
        (post, shoulder),
        (post, low),
        (width - post, low),
        (width - post, shoulder),
        (width, shoulder),
    ]
    return ui_glyph(m, outlined(points, stroke), width)


def control_key(m):
    stroke = ui_stroke(m)
    width = m.v(*CONTROL_WIDTH)
    rise = width * CONTROL_RISE
    top = ui_centre() + m.v(*SHIFT_HEIGHT) / 2 - stroke
    path = mitred([(0, top - rise), (width / 2, top), (width, top - rise)], stroke)
    return ui_glyph(m, [path], width)


def erase_key(m):
    stroke = outline_stroke(m)
    width = m.v(*ERASE_WIDTH)
    height = m.v(*ERASE_HEIGHT)
    low, high = ui_centre() - height / 2, ui_centre() + height / 2
    point = height / 2
    points = [(0, ui_centre()), (point, high), (width, high), (width, low), (point, low)]
    middle = (point + width) / 2 + stroke * 0.25
    arm = min(height / 2 - stroke * (1 + ERASE_GAP), (height / 2 - stroke) * ERASE_SHARE)
    cross = [
        stick((middle - arm, ui_centre() - arm), (middle + arm, ui_centre() + arm), stroke * ERASE_THIN),
        stick((middle - arm, ui_centre() + arm), (middle + arm, ui_centre() - arm), stroke * ERASE_THIN),
    ]
    return ui_glyph(m, outlined(points, stroke) + cross, width)


def return_key(m):
    stroke = ui_stroke(m)
    width = m.v(*RETURN_WIDTH)
    height = m.v(*RETURN_HEIGHT)
    arm = m.v(*RETURN_ARM)
    head, notch = arrow_head(m, arm * math.sqrt(0.5) + stroke, arm)
    low = ui_centre() - height / 2 + arm * math.sqrt(0.5)
    tip = arm * math.sqrt(0.5) + stroke
    shaft = mitred([(width - stroke / 2, ui_centre() + height / 2), (width - stroke / 2, low), (tip - notch * 0.5, low)], stroke)
    arrow = shift(mirror([head], tip / 2), 0, low)
    return ui_glyph(m, [shaft] + arrow, width)


def check_mark(m):
    stroke = ui_stroke(m)
    width = m.v(*CHECK_WIDTH)
    height = m.v(*CHECK_HEIGHT)
    low = ui_centre() - height / 2 + stroke / 2
    high = ui_centre() + height / 2 - stroke / 2
    path = mitred([(stroke / 2, low + (high - low) * CHECK_KNEE), (width * CHECK_FOOT, low), (width - stroke / 2, high)], stroke)
    return ui_glyph(m, [path], width)


def ballot_x(m):
    stroke = ui_stroke(m)
    width = m.v(*CHECK_HEIGHT) * BALLOT_SHARE
    low = ui_centre() - width / 2
    reach = stroke / 2 * math.sqrt(0.5)
    shapes = [
        stick((reach, low + reach), (width - reach, low + width - reach), stroke),
        stick((reach, low + width - reach), (width - reach, low + reach), stroke),
    ]
    return ui_glyph(m, shapes, width)


def triangle(degrees):
    def build(m):
        size = m.v(*SHAPE_SIZE)
        height = size * TRIANGLE_HEIGHT
        points = [(-height / 2, -size / 2), (height / 2, 0), (-height / 2, size / 2)]
        shape = rotated([polygon(points)], 0, 0, degrees)
        corners = [point for contour in shape for point in contour.corners()]
        left = min(point[0] for point in corners)
        right = max(point[0] for point in corners)
        return ui_glyph(m, shift(shape, -left, ui_centre()), right - left)

    return build


def circle(filled):
    def build(m):
        size = m.v(*SHAPE_SIZE)
        low = ui_centre() - size / 2
        if filled:
            shapes = [oval(0, low, size, low + size, CIRCLE_ROUND)]
        else:
            stroke = ui_stroke(m)
            shapes = ring(0, low, size, low + size, stroke, stroke, CIRCLE_ROUND, CIRCLE_ROUND)
        return ui_glyph(m, shapes, size)

    return build


def square_shape(filled):
    def build(m):
        size = m.v(*SHAPE_SIZE) * SQUARE_SHARE
        low = ui_centre() - size / 2
        shapes = [rect(0, low, size, low + size)]
        if not filled:
            stroke = ui_stroke(m)
            shapes.append(rect(stroke, low + stroke, size - stroke, low + size - stroke, hole=True))
        return ui_glyph(m, shapes, size)

    return build


def diagonal_arrow(degrees):
    def build(m):
        shapes, length, _ = arrow_of_length(m, m.v(*DIAGONAL_ARROW_LENGTH))
        turned = rotated(shift(shapes, -length / 2, 0), 0, 0, degrees)
        corners = [point for contour in turned for point in contour.corners()]
        left = min(point[0] for point in corners)
        right = max(point[0] for point in corners)
        return spaced(m, shift(turned, -left, ui_centre()), right - left, m.v(40, 32), m.v(40, 32))

    return build


def currency_bars(m, left, right, heights):
    bar = m.cap_bar * m.v(0.86, 0.8, black=0.7)
    return [rect(left, height - bar / 2, right, height + bar / 2) for height in heights]


def bitcoin(m):
    glyph = capitals.capital_b(m)
    xs = [point[0] for contour in glyph.contours for point in contour.corners()]
    inner = [point[1] for contour in glyph.contours if contour.hole for point in contour.corners()]
    stem_left = min(xs)
    stub = m.cap_stem * m.v(*BITCOIN_STUB)
    reach = m.v(*BITCOIN_REACH)
    low, high = min(inner) / 2, (CAP + max(inner)) / 2
    stubs = []
    for x in (stem_left + m.cap_stem * 0.2, stem_left + m.v(*BITCOIN_SECOND)):
        stubs.append(rect(x, high, x + stub, CAP + reach))
        stubs.append(rect(x, -reach, x + stub, low))
    return Glyph(glyph.contours + stubs, glyph.advance)


def won(m):
    glyph = capitals.capital_w(m)
    xs = [point[0] for contour in glyph.contours for point in contour.corners()]
    over = m.v(*CURRENCY_OVER)
    bars = currency_bars(m, min(xs) - over, max(xs) + over, [m.v(*WON_HIGH), m.v(*WON_LOW)])
    return Glyph(shift(glyph.contours + bars, over), glyph.advance + 2 * over)


def naira(m):
    glyph = capitals.capital_n(m)
    xs = [point[0] for contour in glyph.contours for point in contour.corners()]
    over = m.v(*CURRENCY_OVER)
    bars = currency_bars(m, min(xs) - over, max(xs) + over, [m.v(*NAIRA_HIGH), m.v(*NAIRA_LOW)])
    return Glyph(shift(glyph.contours + bars, over), glyph.advance + 2 * over)


def peso(m):
    glyph = capitals.capital_p(m)
    xs = [point[0] for contour in glyph.contours for point in contour.corners()]
    over = m.v(*CURRENCY_OVER)
    bars = currency_bars(m, min(xs) - over, max(xs) + over * 0.5, [m.v(*PESO_HIGH), m.v(*PESO_LOW)])
    return Glyph(shift(glyph.contours + bars, over), glyph.advance + over)


def shekel_half(m, side, leg, low):
    outer = leg * SHEKEL_ROUND
    inner = max(outer - side, side * SHEKEL_INNER)
    path = Path((0, 0))
    path.to((0, CAP - outer))
    path.arc((outer, CAP), "v", m.k_out)
    path.to((leg - outer, CAP))
    path.arc((leg, CAP - outer), "h", m.k_out)
    path.to((leg, low))
    path.to((leg - side, low))
    path.to((leg - side, CAP - side - inner))
    path.arc((leg - side - inner, CAP - side), "v", m.k_in)
    path.to((side + inner, CAP - side))
    path.arc((side, CAP - side - inner), "h", m.k_in)
    path.to((side, 0))
    return path.close()


def shekel(m):
    width = m.v(*SHEKEL_WIDTH)
    side = m.cap_round * m.v(*SHEKEL_SIDE)
    leg = (2 * width + side) / 3
    low = m.v(*SHEKEL_LOW)
    first = shekel_half(m, side, leg, low)
    second = turn([first], width / 2, CAP / 2)
    return spaced(m, [first] + second, width, m.v(36, 28), m.v(36, 28))


GLYPHS = {
    "Euro": (0x20AC, euro),
    "sterling": (0xA3, sterling),
    "yen": (0xA5, yen),
    "cent": (0xA2, cent),
    "currency": (0xA4, currency),
    "dong": (0x20AB, dong),
    "uni20B4": (0x20B4, hryvnia),
    "uni20B9": (0x20B9, rupee),
    "uni20BA": (0x20BA, lira),
    "uni20BD": (0x20BD, ruble),
    "uni20B8": (0x20B8, tenge),
    "uni20BC": (0x20BC, manat),
    "guillemotleft": (0xAB, guillemotleft),
    "guillemotright": (0xBB, guillemotright),
    "guilsinglleft": (0x2039, guilsinglleft),
    "guilsinglright": (0x203A, guilsinglright),
    "quotedblbase": (0x201E, quotedblbase),
    "quotesinglbase": (0x201A, quotesinglbase),
    "copyright": (0xA9, copyright),
    "registered": (0xAE, registered),
    "trademark": (0x2122, trademark),
    "degree": (0xB0, degree),
    "uni2103": (0x2103, degree_letter(capitals.capital_c)),
    "uni2109": (0x2109, degree_letter(capitals.capital_f)),
    "multiply": (0xD7, multiply),
    "divide": (0xF7, divide),
    "plusminus": (0xB1, plusminus),
    "minus": (0x2212, minus),
    "logicalnot": (0xAC, logicalnot),
    "brokenbar": (0xA6, brokenbar),
    "bullet": (0x2022, bullet),
    "section": (0xA7, section),
    "paragraph": (0xB6, paragraph),
    "dagger": (0x2020, dagger),
    "daggerdbl": (0x2021, daggerdbl),
    "perthousand": (0x2030, perthousand),
    "exclamdown": (0xA1, exclamdown),
    "questiondown": (0xBF, questiondown),
    "ordfeminine": (0xAA, ordfeminine),
    "ordmasculine": (0xBA, ordmasculine),
    "mu": (0xB5, mu),
    "arrowleft": (0x2190, arrowleft),
    "arrowup": (0x2191, arrowup),
    "arrowright": (0x2192, arrowright),
    "arrowdown": (0x2193, arrowdown),
    "arrowboth": (0x2194, arrowboth),
    "arrowdblleft": (0x21D0, arrowdblleft),
    "arrowdblright": (0x21D2, arrowdblright),
    "arrowdblboth": (0x21D4, arrowdblboth),
    "notequal": (0x2260, notequal),
    "lessequal": (0x2264, lessequal),
    "greaterequal": (0x2265, greaterequal),
    "approxequal": (0x2248, approxequal),
    "infinity": (0x221E, infinity),
    "minute": (0x2032, minute),
    "second": (0x2033, second),
    "uni2002": (0x2002, em_share(1 / 2)),
    "uni2003": (0x2003, em_share(1)),
    "uni2004": (0x2004, em_share(1 / 3)),
    "uni2005": (0x2005, em_share(1 / 4)),
    "uni2006": (0x2006, em_share(1 / 6)),
    "uni2007": (0x2007, tabular_blank(1)),
    "uni2008": (0x2008, space_glyph(punctuation_width)),
    "uni2009": (0x2009, space_glyph(thin_space)),
    "uni200A": (0x200A, space_glyph(hair_space)),
    "uni202F": (0x202F, space_glyph(thin_space)),
    "figuredash": (0x2012, figures.tabular(figure_dash)),
}

UI_SYMBOLS = {
    "uni2318": (0x2318, command_key),
    "uni2325": (0x2325, option_key),
    "uni21E7": (0x21E7, shift_key),
    "uni2303": (0x2303, control_key),
    "uni232B": (0x232B, erase_key),
    "uni23CE": (0x23CE, return_key),
    "uni2713": (0x2713, check_mark),
    "uni2717": (0x2717, ballot_x),
    "uni25B2": (0x25B2, triangle(90)),
    "uni25BC": (0x25BC, triangle(-90)),
    "uni25C0": (0x25C0, triangle(180)),
    "uni25B6": (0x25B6, triangle(0)),
    "uni25CF": (0x25CF, circle(True)),
    "uni25CB": (0x25CB, circle(False)),
    "uni25A0": (0x25A0, square_shape(True)),
    "uni25A1": (0x25A1, square_shape(False)),
    "uni2196": (0x2196, diagonal_arrow(135)),
    "uni2197": (0x2197, diagonal_arrow(45)),
    "uni2198": (0x2198, diagonal_arrow(-45)),
    "uni2199": (0x2199, diagonal_arrow(-135)),
}
GLYPHS.update(UI_SYMBOLS)
GLYPHS.update(
    {
        "uni20BF": (0x20BF, bitcoin),
        "uni20A9": (0x20A9, won),
        "uni20AA": (0x20AA, shekel),
        "uni20A6": (0x20A6, naira),
        "uni20B1": (0x20B1, peso),
        "uni2008.tab": (None, tabular_blank(0.5)),
        **{f"{name}.tab": (None, tabular_sign(name, share)) for name, share in TABULAR_SIGNS.items()},
        "comma.tab": (None, tabular_punctuation(marks.comma)),
        "period.tab": (None, tabular_punctuation(marks.period)),
        "colon.tab": (None, tabular_punctuation(marks.colon)),
        "semicolon.tab": (None, tabular_punctuation(marks.semicolon)),
    }
)

KERN_LIKE = {
    "quotesinglbase": "comma",
    "quotedblbase": "comma",
}


def features(master):
    return ""


TUGRIK_LOW = (232, 236, 230, 240)
TUGRIK_REACH = (150, 162, 144, 176)
LARI_WIDTH = (560, 624, 544, 700)
LARI_TOP = (520, 530, 516, 540)
LARI_END = (0.36, 0.36, 0.36, 0.36)
LARI_GAP = (58, 50, 62, 40)
LARI_STEM = (0.8, 0.74, 0.84, 0.66)
LARI_LOW = (300, 310, 296, 326)
LARI_FOOT = (0.46, 0.46, 0.46, 0.46)
COLON_LEAN = 72
STUB_SINK = 0.5
COLON_GAP = (70, 62, 74, 52)
LIRA_PAIR_GAP = (60, 54, 64, 46)


def letter_box(glyph):
    xs = [point[0] for contour in glyph.contours for point in contour.corners()]
    return min(xs), max(xs)


def tugrik(m):
    glyph = capitals.capital_t(m)
    left, right = letter_box(glyph)
    middle = (left + right) / 2
    bar = m.cap_bar * m.v(0.92, 0.86, black=0.78)
    reach = m.v(*TUGRIK_REACH)
    low = m.v(*TUGRIK_LOW)
    high = low + bar + m.v(*LIRA_GAP)
    bars = [slanted_bar(middle - reach, middle + reach, height, middle, LIRA_RISE, bar) for height in (low, high)]
    return Glyph(glyph.contours + bars, glyph.advance)


def lari(m):
    width = m.v(*LARI_WIDTH)
    side = m.cap_round * m.v(*MANAT_SIDE)
    flat = m.cap_thin
    base = m.cap_bar * m.v(0.92, 0.86, black=0.78)
    top = m.v(*LARI_TOP)
    shoulder = top - (width - side) / 2
    arch = ribbon(
        [
            Node((width - side / 2, CAP * m.v(*LARI_END)), UP, side, cut="h"),
            Node((width - side / 2, shoulder), UP, side, straight=True),
            Node((width / 2, top + m.ov - flat / 2), LEFT, flat),
            Node((side / 2, shoulder), DOWN, side),
            Node((width * m.v(*LARI_FOOT), base / 2), RIGHT, base, cut="v"),
        ],
        0.6,
    )
    stem = m.cap_stem * m.v(*LARI_STEM)
    offset = (m.v(*LARI_GAP) + stem) / 2
    low = m.v(*LARI_LOW)
    stems = [rect(width / 2 + sign * offset - stem / 2, low, width / 2 + sign * offset + stem / 2, CAP) for sign in (-1, 1)]
    return spaced(m, [arch, rect(0, 0, width, base)] + stems, width, m.v(30, 22), m.v(30, 22))


def stubbed(draw, lean=90, count=1):
    def build(m):
        glyph = draw(m)
        left, right = letter_box(glyph)
        stub = m.cap_stem * m.v(*BITCOIN_STUB)
        reach = m.v(*BITCOIN_REACH)
        run = 1 / math.tan(math.radians(lean))
        spread = stub + m.v(*COLON_GAP)
        middle = (left + right) / 2
        stubs = []
        for index in range(count):
            x = middle + (index - (count - 1) / 2) * spread
            sunk = m.cap_thin * STUB_SINK
            for low, high in ((CAP - sunk, CAP + reach), (-reach, sunk)):
                down, up = (low - high) / 2 * run, (high - low) / 2 * run
                stubs.append(polygon([(x + down - stub / 2, low), (x + down + stub / 2, low), (x + up + stub / 2, high), (x + up - stub / 2, high)]))
        return Glyph(glyph.contours + stubs, glyph.advance)

    return build


def kip(m):
    glyph = capitals.capital_k(m)
    left, right = letter_box(glyph)
    over = m.v(*CURRENCY_OVER)
    low_cut, high_cut, high_end, low_end = glyph.contours[1].corners()
    foot, crotch, _, _ = glyph.contours[2].corners()
    stem_right = max(point[0] for point in glyph.contours[0].corners())
    notch = intersect(low_cut, low_end, foot, crotch)[1]
    upper = intersect(high_cut, high_end, (stem_right, 0), (stem_right, 1))[1]
    bar = m.cap_bar * m.v(0.86, 0.8, black=0.7)
    bars = currency_bars(m, left - over, right + over, [max(notch - bar / 2, (notch + upper) / 2)])
    return Glyph(shift(glyph.contours + bars, over), glyph.advance + 2 * over)


def rupee_letters(m):
    from .features import needed_kern, side_gap

    first, second = capitals.capital_r(m), lowercase.letter_s(m)
    room = max(0, needed_kern(first, second, side_gap(lowercase.letter_o(m))))
    return latin.side_by_side(Glyph(first.contours, first.advance + room), second)


def franc(m):
    glyph = capitals.capital_f(m)
    left, _ = letter_box(glyph)
    over = m.v(*RUBLE_REACH)
    low = m.v(*RUBLE_LOW)
    cross = m.cap_bar * m.v(0.94, 0.9, black=0.84)
    bar = rect(left - over, low - cross / 2, left + m.v(*RUBLE_TAIL), low + cross / 2)
    return Glyph(shift(glyph.contours + [bar], over), glyph.advance + over)


def lira_sign(m):
    glyph = sterling(m)
    *letter, single = glyph.contours
    corners = list(single.corners())
    left, right = min(x for x, _ in corners), max(x for x, _ in corners)
    centre = sum(y for _, y in corners) / len(corners)
    bar = m.cap_bar * m.v(0.86, 0.8, black=0.7)
    offset = (bar + m.v(*LIRA_PAIR_GAP)) / 2
    return Glyph(letter + currency_bars(m, left, right, [centre - offset, centre + offset]), glyph.advance)


GLYPHS.update(
    {
        "uni20AE": (0x20AE, tugrik),
        "uni20BE": (0x20BE, lari),
        "colonmonetary": (0x20A1, stubbed(capitals.capital_c, COLON_LEAN, 2)),
        "uni20B5": (0x20B5, stubbed(capitals.capital_c)),
        "uni20B2": (0x20B2, stubbed(capitals.capital_g)),
        "kip": (0x20AD, kip),
        "rupee": (0x20A8, rupee_letters),
        "franc": (0x20A3, franc),
        "lira": (0x20A4, lira_sign),
    }
)


SOUND_WIDTH = (250, 270, 244, 284)
SOUND_SHIFT = (14, 12, 14, 10)
SOUND_WAIST = (0.4, 0.38, 0.4, 0.36)
ESTIMATED_WIDTH = (640, 680, 630, 720)
ESTIMATED_SIDE = (0.92, 0.9, 0.92, 0.86)
ESTIMATED_FLAT = (0.92, 0.9, 0.92, 0.86)
ESTIMATED_BAR = (0.92, 0.86, 0.92, 0.8)
ESTIMATED_TAIL = (0.24, 0.23, 0.24, 0.22)
ESTIMATED_SIDES = (40, 30, 42, 24)
INTERROBANG_ROOM = (60, 96, 50, 176)
INTERROBANG_EDGE = (1.0, 0.94, 1.0, 0.86)
INTERROBANG_REACH = 0.3
INTERROBANG_TILT = 0.15


def sound_recording(m):
    size = CAP + 2 * m.ov
    centre = size / 2
    height = m.v(372, 386)
    side = superior_stem(m) * m.v(0.98, 0.9, black=0.9)
    flat = superior_thin(m) * m.v(1.04, 1.0, black=1.03)
    width = m.v(*SOUND_WIDTH)
    left = centre - width / 2 + m.v(*SOUND_SHIFT)
    bottom = centre - height / 2
    top = bottom + height
    waist = bottom + height * m.v(*SOUND_WAIST)
    letter = [rect(left, bottom, left + side, top)]
    letter += lobe(m, left + side * 0.5, left + side * 0.8, left + width, top, waist, flat, side)
    edge = side * 0.92
    shapes = shift(emblem(m, size, edge, edge * 0.92) + letter, 0, -m.ov)
    return spaced(m, shapes, size, m.v(36, 28), m.v(36, 28))


def estimated(m):
    width = m.v(*ESTIMATED_WIDTH)
    side = m.cap_round * m.v(*ESTIMATED_SIDE)
    flat = m.cap_thin * m.v(*ESTIMATED_FLAT)
    bar = m.cap_bar * m.v(*ESTIMATED_BAR)
    top, bottom = CAP + m.cap_ov, -m.cap_ov
    middle_x, middle_y = width / 2, CAP / 2
    bar_bottom = middle_y - bar / 2
    inner_top, inner_bottom = top - flat, bottom + flat
    tail_y = CAP * m.v(*ESTIMATED_TAIL)
    tail_out = reach(quarter((middle_x, bottom), (width, middle_y), "h", m.k_out), 1, tail_y)
    tail_in = reach(quarter((middle_x, inner_bottom), (width - side, middle_y), "h", m.k_in), 1, tail_y)
    path = Path(tail_out[3])
    path.bez(flip(tail_out))
    path.arc((0, middle_y), "h", m.k_out)
    path.arc((middle_x, top), "v", m.k_out)
    path.arc((width, middle_y), "h", m.k_out)
    path.to((width, bar_bottom))
    path.to((width - side, bar_bottom))
    path.to((width - side, middle_y))
    path.arc((middle_x, inner_top), "v", m.k_in)
    path.arc((side, middle_y), "h", m.k_in)
    path.arc((middle_x, inner_bottom), "v", m.k_in)
    path.bez(tail_in)
    crossbar = rect(side * 0.5, bar_bottom, width - side * 0.5, bar_bottom + bar)
    return spaced(m, [path.close(), crossbar], width, m.v(*ESTIMATED_SIDES), m.v(*ESTIMATED_SIDES))


def interrobang(m):
    room = m.v(*INTERROBANG_ROOM)
    width = m.v(424, 474) + room
    edge = m.v(90, 152, light=58, black=200) * m.v(*INTERROBANG_EDGE)
    flat = m.cap_thin
    stem = m.cap_stem * m.v(0.96, 0.92)
    side = marks.square(m)
    top = CAP + m.cap_ov
    post = width / 2 + m.v(4, 2)
    foot = side + m.v(96, 74, black=66)
    turn = m.v(274, 288, black=290)
    neck = m.v(80, 128, light=54, black=162)
    hook = ribbon(
        [
            Node((m.v(46, 74), m.v(554, 544)), aim(m.v(62, 60)), neck, cut="h"),
            Node((width * 0.49, top - flat / 2), RIGHT, flat),
            Node((width - edge / 2, m.v(546, 552)), DOWN, edge),
            Node((post + m.v(66, 76) + room * INTERROBANG_REACH, m.v(398, 400)), aim(m.v(230, 228) - room * INTERROBANG_TILT), neck),
            Node((post, turn), DOWN, stem, arrive=0.8),
            Node((post, foot), DOWN, stem, straight=True),
        ],
        0.6,
    )
    bar = rect(post - stem / 2, (foot + turn) / 2, post + stem / 2, CAP)
    return spaced(m, [hook, bar, rect(post - side / 2, 0, post + side / 2, side)], width, m.v(34, 26), m.v(40, 30))


def interrobang_inverted(m):
    return respaced(m, turned(interrobang(m), XH).contours, m.v(40, 30))


def updown_arrow(m):
    span = m.v(286, 296) * math.sqrt(0.5)
    centre = CAP / 2
    shapes = rotated(shift(single_both(m, CAP), span - CAP / 2, centre), span, centre, 90)
    return spaced(m, shapes, span * 2, m.v(40, 32), m.v(40, 32))


def double_vertical(build, degrees):
    def draw(m):
        span = m.v(286, 296) * DOUBLE_ARROW_ARM * math.sqrt(0.5)
        centre = CAP / 2
        shapes = rotated(shift(build(m, CAP), span - CAP / 2, centre), span, centre, degrees)
        return spaced(m, shapes, span * 2, m.v(40, 32), m.v(40, 32))

    return draw


GLYPHS.update(
    {
        "uni2117": (0x2117, sound_recording),
        "estimated": (0x212E, estimated),
        "uni203D": (0x203D, interrobang),
        "uni2E18": (0x2E18, interrobang_inverted),
        "arrowupdn": (0x2195, updown_arrow),
        "arrowdblup": (0x21D1, double_vertical(double_arrow, 90)),
        "arrowdbldown": (0x21D3, double_vertical(double_arrow, -90)),
        "uni21D5": (0x21D5, double_vertical(double_both, 90)),
    }
)
