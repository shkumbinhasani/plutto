import math

from .geometry import Path, across, intersect
from .lowercase import hook_inner
from .marks import TALL_BOTTOM, TALL_TOP
from .masters import CAP, XH
from .parts import band_width, hook, spaced
from .shapes import Node, aim, place, polygon, rect, ribbon

DOWN = (0, -1)
UP = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)


def reflected(node, width):
    point = (width - node.point[0], node.point[1])
    heading = (node.heading[0], -node.heading[1])
    return Node(point, heading, node.thickness, cut=node.cut, arrive=node.leave, leave=node.arrive)


def rotated(node, centre):
    point = (2 * centre[0] - node.point[0], 2 * centre[1] - node.point[1])
    return Node(point, node.heading, node.thickness, cut=node.cut, arrive=node.leave, leave=node.arrive)


def omega(m):
    width = m.v(640, 704, black=766)
    side = m.cap_round
    flat = m.cap_thin
    leg = m.cap_stem * m.v(0.88, 0.84, black=0.74)
    foot = m.cap_bar
    leg_x = width * m.v(0.27, 0.29, black=0.3)
    belly = m.v(372, 378)
    left = [
        Node((leg_x, 0), aim(95), leg, cut="h"),
        Node((leg_x - (leg_x - side / 2) * 0.4, m.v(166, 172)), aim(m.v(117, 118)), (leg + side) / 2),
        Node((side / 2, belly), UP, side),
    ]
    crown = Node((width / 2, CAP + m.ov - flat / 2), RIGHT, flat)
    right = [reflected(node, width) for node in reversed(left)]
    bowl = ribbon(left + [crown] + right, 0.6)
    inset = m.v(14, 10)
    shapes = [
        bowl,
        rect(inset, 0, leg_x, foot),
        rect(width - leg_x, 0, width - inset, foot),
    ]
    return spaced(m, shapes, width, m.v(36, 28), m.v(36, 28), capital=True)


def pi(m):
    stem = m.stem
    bar = m.thin
    hang = m.v(44, 40)
    span = m.v(404, 462, light=384, black=540)
    run = stem + m.v(100, 106)
    right = hang + span - stem
    reach = right + run - m.v(22, 18)
    foot = hook(m, stem, m.thin, XH - bar / 2, run, hook_inner(m))
    shapes = [
        rect(0, XH - bar, reach, XH),
        rect(hang, 0, hang + stem, XH - bar / 2),
        place(foot, right, 0),
    ]
    return spaced(m, shapes, right + run, m.v(18, 12), m.v(10, 6, black=8), capital=False)


def partialdiff(m):
    width = m.v(486, 536, black=584)
    edge = m.cap_round
    flat = m.cap_thin
    top = CAP + m.ov
    bowl_top = m.v(446, 456, black=462)
    shape = ribbon(
        [
            Node((width * m.v(0.1, 0.12), m.v(596, 582, light=604, black=540)), aim(m.v(64, 62)), m.v(80, 124, light=54, black=144), cut="h"),
            Node((width * 0.44, top - flat / 2), RIGHT, flat),
            Node((width - edge / 2, m.v(300, 296)), DOWN, edge),
            Node((width * 0.5, flat / 2 - m.ov), LEFT, flat),
            Node((edge / 2, m.v(222, 226)), UP, edge),
            Node((width * 0.5, bowl_top - flat * 0.44), RIGHT, flat * m.v(0.88, 0.84, black=0.8)),
            Node((width - edge * 0.6, m.v(300, 284)), aim(-56), m.v(50, 78, light=34, black=96), arrive=0.5),
        ],
        0.6,
    )
    return spaced(m, [shape], width, m.v(34, 26), m.v(36, 28))


def increment(m):
    width = m.v(612, 680, black=736)
    middle = width / 2
    flat = m.cap_diag * m.v(1.0, 0.92)
    direction = (middle - flat / 2, CAP)
    stroke = across(direction, m.cap_diag * m.v(0.94, 0.9, black=0.86))
    bar = m.cap_bar
    falling = (-direction[0], direction[1])
    low_left = intersect((stroke, 0), (stroke + direction[0], CAP), (0, bar), (1, bar))
    low_right = intersect((width - stroke, 0), (width - stroke + falling[0], CAP), (0, bar), (1, bar))
    apex = intersect((stroke, 0), (stroke + direction[0], CAP), (width - stroke, 0), (width - stroke + falling[0], CAP))
    outer = polygon([(0, 0), (middle - flat / 2, CAP), (middle + flat / 2, CAP), (width, 0)])
    counter = Path(low_left).to(apex).to(low_right).close(hole=True)
    return spaced(m, [outer, counter], width, "cap_diagonal", "cap_diagonal")


def product(m):
    stem = m.cap_stem
    bar = m.cap_bar
    width = m.v(612, 676, black=728)
    hang = m.v(46, 42)
    shapes = [
        rect(0, TALL_TOP - bar, width, TALL_TOP),
        rect(hang, TALL_BOTTOM, hang + stem, TALL_TOP - bar / 2),
        rect(width - hang - stem, TALL_BOTTOM, width - hang, TALL_TOP - bar / 2),
    ]
    return spaced(m, shapes, width, m.v(44, 34), m.v(44, 34))


def summation(m):
    width = m.v(572, 632, black=684)
    bar = m.cap_bar
    top, bottom = TALL_TOP, TALL_BOTTOM
    middle = (top + bottom) / 2
    tip = (width * m.v(0.6, 0.62), middle)
    upper_y, lower_y = top - bar / 2, bottom + bar / 2
    thick = m.cap_diag * m.v(1.0, 0.96, black=0.92)
    thin = m.cap_bar * m.v(1.04, 1.0)
    upper = band_width(tip[0], upper_y - middle, thick)
    lower = band_width(tip[0], middle - lower_y, thin)
    notch = intersect((0, upper_y), (tip[0] - upper, tip[1]), (0, lower_y), (tip[0] - lower, tip[1]))
    chevron = polygon([(0, upper_y), (upper, upper_y), tip, (lower, lower_y), (0, lower_y), notch])
    shapes = [
        rect(0, top - bar, width - m.v(14, 12), top),
        chevron,
        rect(0, bottom, width, bottom + bar),
    ]
    return spaced(m, shapes, width, m.v(36, 28), m.v(36, 28))


def radical(m):
    width = m.v(560, 604, black=640)
    top = TALL_TOP
    flat = m.v(60, 92, light=42, black=112)
    vertex = m.v(250, 268, black=284)
    entry = (m.v(54, 62, light=50, black=68), m.v(330, 340))
    tick_direction = (vertex - flat / 2 - entry[0], -entry[1])
    tick = across(tick_direction, m.cap_diag * m.v(0.94, 0.9))
    long_direction = (width - vertex - flat / 2, top)
    long = across(long_direction, m.v(70, 106, light=48, black=134))
    notch = intersect(
        (width - long, top),
        (width - long - long_direction[0], 0),
        (entry[0] + tick, entry[1]),
        (entry[0] + tick + tick_direction[0], 0),
    )
    check = polygon(
        [
            entry,
            (vertex - flat / 2, 0),
            (vertex + flat / 2, 0),
            (width, top),
            (width - long, top),
            notch,
            (entry[0] + tick, entry[1]),
        ]
    )
    flag = rect(0, entry[1] - m.bar, entry[0] + tick / 2, entry[1])
    return spaced(m, [check, flag], width, m.v(24, 18), m.v(14, 10))


def integral(m):
    stem = m.v(82, 140, light=54, black=176)
    flat = m.v(62, 90, light=44, black=106)
    end = m.v(70, 100, light=48, black=116)
    gap = m.v(112, 104, light=114, black=100)
    top = TALL_TOP + m.ov
    bottom = TALL_BOTTOM - m.ov
    heading = aim(-93)
    along = m.v(206, 196)
    lean = -heading[0] * along
    width = stem + 2 * (lean + gap + end)
    centre = (width / 2, (top + bottom) / 2)
    shoulder = (centre[0] + lean, centre[1] - heading[1] * along)
    rise = aim(m.v(116, 114))
    tip = width - end / (2 * rise[1])
    terminal = top - m.v(172, 190, light=166, black=206)
    inner = top - flat
    terminal_reach = tip - end / (2 * rise[1]) + (inner - terminal) * rise[0] / rise[1]
    stem_reach = shoulder[0] + stem / 2 + (inner - shoulder[1]) * heading[0] / heading[1]
    upper = [
        Node((tip, terminal), rise, end, cut="h"),
        Node(((terminal_reach + stem_reach) / 2, top - flat / 2), LEFT, flat),
        Node(shoulder, heading, stem, arrive=0.62),
    ]
    lower = [rotated(node, centre) for node in reversed(upper)]
    lower[0].straight = True
    return spaced(m, [ribbon(upper + lower, 0.6)], width, m.v(34, 30), m.v(34, 30))


def lozenge(m):
    width = m.v(452, 496, black=550)
    height = CAP + 2 * m.ov
    stroke = m.cap_diag * m.v(0.84, 0.78, light=0.86, black=0.7)
    half_w, half_h = width / 2, height / 2
    slant = math.hypot(half_w, half_h)
    inner_w = half_w - stroke * slant / half_h
    inner_h = half_h - stroke * slant / half_w
    cx, cy = half_w, height / 2 - m.ov
    outer = polygon([(cx, cy - half_h), (cx + half_w, cy), (cx, cy + half_h), (cx - half_w, cy)])
    counter = Path((cx, cy - inner_h)).to((cx - inner_w, cy)).to((cx, cy + inner_h)).to((cx + inner_w, cy)).close(hole=True)
    return spaced(m, [outer, counter], width, m.v(30, 24), m.v(30, 24))


GLYPHS = {
    "Omega": (0x03A9, omega),
    "pi": (0x03C0, pi),
    "partialdiff": (0x2202, partialdiff),
    "increment": (0x2206, increment),
    "product": (0x220F, product),
    "summation": (0x2211, summation),
    "radical": (0x221A, radical),
    "integral": (0x222B, integral),
    "lozenge": (0x25CA, lozenge),
}
KERN_LIKE = {}


def features(master):
    return ""
