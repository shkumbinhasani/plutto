import math
from dataclasses import dataclass

from .geometry import across, intersect
from .masters import CAP
from .masters import XH, Master, interpolate
from .parts import Glyph, band_width, spaced
from .shapes import Node, aim, oval, polygon, rect, ribbon, ring, shift, turn

WAIST = CAP * 0.53
DOWN = (0, -1)
UP = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
FIVE_TUCK = 2
COIL_ENTRY_WEIGHT = 0.7
COIL_ENTRY_PULL = 0.62
COIL_PULL = 0.6
COIL_BACK = (290, 282)
COIL_RISE = (116, 118, None, 106)
THREE_WAIST = (0.94, 0.9, None, 0.8)
THREE_LOWER = (1.0, 1.0, None, 0.9)
THREE_SHELF = (0.52, 0.52, None, 0.46)
THREE_FLANK = (196, 192, None, 204)


@dataclass
class Figure:
    contours: list
    width: float
    left: float
    right: float


def proportional(draw):
    def build(m):
        drawn = draw(m)
        return spaced(m, drawn.contours, drawn.width, drawn.left, drawn.right, capital=False)

    return build


def tabular(draw):
    def build(m):
        drawn = draw(m)
        advance = m.v(580, 580, light=566, black=676) / m.narrowing
        slack = advance - drawn.width - drawn.left - drawn.right
        return Glyph(shift(drawn.contours, drawn.left + slack / 2), advance)

    return build


def body(m):
    return m.v(476, 526, light=454, black=596)


def side(m):
    return m.v(92, 160, light=60, black=194)


def terminal_high(m):
    return m.v(554, 536, black=500)


def terminal_low(m):
    return m.v(150, 172, black=204)


def zero(m):
    return zero_ring(m, 1.0)


def slashed_zero_ring(m):
    return zero_ring(m, m.v(1.0, 0.97, light=1.0, black=0.93))


def zero_ring(m, lightness):
    width = body(m)
    shapes = ring(0, -m.cap_ov, width, CAP + m.cap_ov, side(m) * lightness, m.cap_thin * lightness, m.k_out, m.k_in)
    return Figure(shapes, width, m.v(36, 28), m.v(36, 28))


def one(m):
    stem = m.cap_stem
    left = m.v(150, 146)
    reach = left + stem * 0.5
    drop = m.v(150, 150)
    rise = across((drop, reach), m.cap_diag * m.v(0.96, 0.9))
    flag = polygon([(reach, CAP), (0, CAP - drop), (0, CAP - drop - rise), (reach, CAP - rise)])
    return Figure([rect(left, 0, left + stem, CAP), flag], left + stem, m.v(30, 22), m.v(62, 50))


def two(m):
    width = body(m)
    edge = side(m)
    flat = m.cap_thin
    bar = m.cap_bar
    top = CAP + m.cap_ov
    fall = aim(m.v(221, 220))
    slope = -fall[1] / -fall[0]
    stroke = m.cap_diag * m.v(0.98, 0.94)
    foot = (stroke / 2 * math.hypot(fall[0], fall[1]) / -fall[1], bar)
    waist_y = m.v(282, 290)
    waist = (foot[0] + (waist_y - bar) / slope, waist_y)
    spine = ribbon(
        [
            Node((m.v(52, 76), terminal_high(m)), aim(m.v(64, 62)), m.v(84, 136, light=56, black=152), cut="h"),
            Node((width * 0.49, top - flat * 0.96 / 2), RIGHT, flat * 0.96),
            Node((width - edge / 2, m.v(536, 530)), DOWN, edge, leave=0.72),
            Node(waist, fall, stroke, arrive=0.5),
            Node(foot, fall, stroke, straight=True, cut="h"),
        ],
        0.6,
    )
    return Figure([spine, rect(0, 0, width, bar)], width, m.v(32, 24), m.v(34, 26))


def three(m):
    width = body(m)
    edge = side(m)
    flat = m.cap_thin * m.v(1.0, 1.0, black=0.9)
    top = CAP + m.cap_ov
    waist = flat * m.v(*THREE_WAIST)
    tongue = m.v(150, 172)
    terminal = m.v(80, 128, light=54, black=136)
    upper = ribbon(
        [
            Node((m.v(50, 76), m.v(554, 544, black=522)), aim(m.v(62, 60)), terminal, cut="h"),
            Node((width * 0.51, top - flat / 2), RIGHT, flat),
            Node((width - m.v(22, 20) - edge * m.v(0.46, 0.42), m.v(550, 540)), DOWN, edge * m.v(0.92, 0.84)),
            Node((width * 0.5, WAIST), LEFT, waist),
            Node((tongue, WAIST), LEFT, waist, straight=True, cut="v"),
        ],
        0.6,
    )
    lower = ribbon(
        [
            Node((width * 0.4, WAIST), RIGHT, waist, cut="v"),
            Node((width * m.v(*THREE_SHELF), WAIST), RIGHT, waist, straight=True),
            Node((width - edge * m.v(*THREE_LOWER) / 2, m.v(*THREE_FLANK)), DOWN, edge * m.v(*THREE_LOWER)),
            Node((width * 0.49, flat / 2 - m.cap_ov), LEFT, flat),
            Node((m.v(46, 74), terminal_low(m)), aim(m.v(118, 120)), terminal, cut="h"),
        ],
        0.6,
    )
    return Figure([upper, lower], width, m.v(30, 22), m.v(36, 28))


def four(m):
    width = m.v(524, 568, light=506, black=620)
    stem = m.cap_stem
    bar = m.cap_bar * m.v(1, 0.86, light=1, black=0.76)
    post = width - stem - m.v(76, 60, light=79, black=38)
    shelf = m.v(168, 148, light=171, black=106)
    stroke = band_width(post + stem, CAP - shelf, m.cap_diag * m.v(1, 0.88, light=1, black=0.68))
    inside_post = intersect((stroke, shelf), (post + stem, CAP), (post + stem / 2, 0), (post + stem / 2, CAP))
    shapes = [
        rect(post, 0, post + stem, CAP),
        rect(0, shelf, width, shelf + bar),
        polygon([(0, shelf), (post + stem - stroke, CAP), (post + stem / 2, CAP), inside_post, (stroke, shelf)]),
    ]
    return Figure(shapes, width, m.v(22, 16), m.v(28, 20))


def five(m):
    width = body(m)
    edge = side(m)
    flat = m.cap_thin
    stem = m.cap_stem * m.v(0.98, 0.94)
    left = m.v(34, 26)
    bowl_top = m.v(462, 476)
    entry = aim(m.v(62, 60))
    entry_thickness = m.v(52, 84, light=34, black=108)
    entry_y = m.v(352, 344)
    entry_x = left + stem - FIVE_TUCK - entry_thickness / 2 * entry[1]
    stem_bottom = entry_y - entry_thickness / 2 * entry[0] - FIVE_TUCK
    bowl = ribbon(
        [
            Node((entry_x, entry_y), entry, entry_thickness),
            Node((width * 0.5, bowl_top - flat / 2), RIGHT, flat),
            Node((width - edge / 2, m.v(226, 230)), DOWN, edge),
            Node((width * 0.48, flat / 2 - m.cap_ov), LEFT, flat),
            Node((m.v(46, 74), terminal_low(m)), aim(m.v(118, 120)), m.v(80, 128, light=54, black=146), cut="h"),
        ],
        0.6,
    )
    shapes = [
        bowl,
        rect(left, stem_bottom, left + stem, CAP),
        rect(left, CAP - m.cap_bar, width - m.v(26, 20), CAP),
    ]
    return Figure(shapes, width, m.v(40, 30), m.v(36, 28))


def tucked(node, thickness, pull):
    inward = (-node.heading[1], node.heading[0])
    step = (node.thickness - thickness) / 2
    return Node((node.point[0] + inward[0] * step, node.point[1] + inward[1] * step), node.heading, thickness, arrive=pull)


def coil(m, terminal_y, bowl_top, bowl_middle):
    width = body(m)
    edge = side(m)
    flat = m.cap_thin
    top = CAP + m.cap_ov
    terminal = Node((width * m.v(0.85, 0.84), terminal_y), aim(m.v(*COIL_RISE)), m.v(76, 120, light=52, black=140), cut="h")
    crown = Node((width * 0.52, top - flat / 2), LEFT, flat)
    back = Node((edge / 2, m.v(*COIL_BACK)), DOWN, edge * m.v(1.02, 1.0))
    base = Node((width * 0.5, flat / 2 - m.cap_ov), RIGHT, flat)
    flank = width - edge / 2
    entry = edge * COIL_ENTRY_WEIGHT
    shape = ribbon(
        [
            terminal,
            crown,
            back,
            base,
            Node((flank, bowl_middle), UP, edge),
            Node((width * 0.53, bowl_top - flat * 0.46), LEFT, flat * 0.92),
            tucked(back, entry, COIL_ENTRY_PULL),
        ],
        COIL_PULL,
    )
    return [shape]


def six_shapes(m):
    return coil(m, m.v(604, 566, black=524), m.v(468, 482, black=494), m.v(232, 236, black=244))


def six(m):
    return Figure(six_shapes(m), body(m), m.v(36, 28), m.v(34, 26))


def seven(m):
    width = m.v(470, 520, black=572)
    bar = m.cap_bar
    foot = m.v(138, 124)
    stroke = band_width(width - foot, CAP - bar, m.cap_diag * m.v(1.0, 0.96))
    points = [
        (0, CAP),
        (width, CAP),
        (width, CAP - bar),
        (foot + stroke, 0),
        (foot, 0),
        (width - stroke, CAP - bar),
        (0, CAP - bar),
    ]
    return Figure([polygon(points)], width, m.v(28, 20), m.v(22, 14))


def eight(m):
    width = body(m)
    edge = side(m)
    flat = m.cap_thin
    inset = m.v(20, 24)
    waist = flat * m.v(1.0, 0.84)
    upper_side = edge * m.v(0.96, 0.86)
    lower_side = edge * m.v(1.0, 0.94)
    shapes = [
        oval(inset, WAIST - waist / 2, width - inset, CAP + m.cap_ov, m.k_out),
        oval(inset + upper_side, WAIST + waist / 2, width - inset - upper_side, CAP + m.cap_ov - flat * m.v(1.0, 0.94), m.k_in, hole=True),
        oval(0, -m.cap_ov, width, WAIST + waist / 2, m.k_out),
        oval(lower_side, flat - m.cap_ov, width - lower_side, WAIST - waist / 2, m.k_in, hole=True),
    ]
    return Figure(shapes, width, m.v(34, 26), m.v(34, 26))


def nine(m):
    width = body(m)
    shapes = coil(m, m.v(562, 554, light=567, black=524), m.v(476, 486, light=471, black=490), m.v(236, 240, black=246))
    return Figure(turn(shapes, width / 2, CAP / 2), width, m.v(34, 26), m.v(36, 28))


OLDSTYLE_SMALL = ("zero", "one", "two")
OLDSTYLE_DESCENDING = ("three", "four", "five", "seven", "nine")
OLDSTYLE_WIDTH = 0.92
OLDSTYLE_WEIGHT = 0.96
OLDSTYLE_FLAT = (1.0, 1.0, 1.0, 0.88)
SIDE_RANGE = (92, 160)


@dataclass(frozen=True)
class ScaledMaster(Master):
    shift: float = 0.0
    weights: tuple = ()

    def v(self, regular, bold, light=None, black=None):
        return interpolate(self.mix, regular, bold, light, black) + (bold - regular) * self.shift

    @property
    def cap_stem(self):
        return self.weights[0]

    @property
    def cap_round(self):
        return self.weights[1]

    @property
    def cap_thin(self):
        return self.weights[2]

    @property
    def cap_bar(self):
        return self.weights[3]

    @property
    def cap_diag(self):
        return self.weights[4]


def scaled_master(m, sx, sy, vertical, round_, thin, bar, diag, side_target=None):
    shift = 0.0
    if side_target is not None:
        shift = (side_target / sx - side(m)) / (SIDE_RANGE[1] - SIDE_RANGE[0])
    weights = (vertical / sx, round_ / sx, thin / sy, bar / sy, diag / ((sx + sy) / 2))
    return ScaledMaster(m.name, m.weight, m.mix, m.italic, m.slant, shift, weights)


def scaled(contours, sx, sy):
    return [contour.map(lambda point: (point[0] * sx, point[1] * sy)) for contour in contours]


def oldstyle(name):
    draw = globals()[name]

    def build(m):
        if name in OLDSTYLE_SMALL:
            sx, sy = OLDSTYLE_WIDTH, XH / CAP
            weight = OLDSTYLE_WEIGHT
            flat = weight * m.v(*OLDSTYLE_FLAT)
            small = scaled_master(m, sx, sy, m.cap_stem * weight, m.cap_round * weight, m.cap_thin * flat, m.cap_bar * flat, m.cap_diag * weight, side(m) * weight)
            drawn = draw(small)
            return Figure(scaled(drawn.contours, sx, sy), drawn.width * sx, drawn.left * sx, drawn.right * sx)
        drawn = draw(m)
        if name in OLDSTYLE_DESCENDING:
            return Figure(shift(drawn.contours, 0, XH - CAP), drawn.width, drawn.left, drawn.right)
        return drawn

    return build



SMALL_CAP_FIGURE_HEIGHT = XH + 32
SMALL_CAP_FIGURE_WIDTH = 0.9


def small_cap_figure(name):
    draw = globals()[name]

    def build(m):
        sx, sy = SMALL_CAP_FIGURE_WIDTH, SMALL_CAP_FIGURE_HEIGHT / CAP
        weight = OLDSTYLE_WEIGHT
        flat = weight * m.v(*OLDSTYLE_FLAT)
        small = scaled_master(m, sx, sy, m.cap_stem * weight, m.cap_round * weight, m.cap_thin * flat, m.cap_bar * flat, m.cap_diag * weight, side(m) * weight)
        drawn = draw(small)
        return Figure(scaled(drawn.contours, sx, sy), drawn.width * sx, drawn.left * sx, drawn.right * sx)

    return build
