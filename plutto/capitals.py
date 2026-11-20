from .geometry import Path, across, intersect
from .figures import terminal_high, terminal_low
from .masters import CAP
from .parts import band, band_width, kay, lobe, spaced, vee, zed
from .shapes import Node, aim, edges, polygon, rect, ribbon, ring, shift

WAIST = CAP * 0.52
OPEN_DIAGONAL_SIDE = (-12, -14, -12, -12)
BAR_SIDE = (-7, -7, -9, -5)
DOWN = (0, -1)
UP = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
CUT_RISE = 106
Q_SLOPE = (-47, -51, -47, -55)
Q_DEPTH = (110, 98, 106, 86)
Q_ENTRY = 0.53
Q_SEAT = (0, 1, 0, 1)
Q_BURY = 6
Q_SAMPLES = 32
BOWL_BAR = 0.8
ROUND_WIDTH = (606, 670, None, 762)
C_WIDTH = (560, 618, 522, 702)
G_WIDTH = (588, 652, 550, 738)
D_WIDTH = (574, 638, None, 718)
D_RX = (300, 322, None, 354)


def crossbar(m, left, right, centre):
    return rect(left, centre - m.cap_bar / 2, right, centre + m.cap_bar / 2)


def capital_a(m):
    width = m.v(612, 692, black=756)
    middle = width / 2
    flat = m.cap_diag * m.v(1.15, 1.05, black=1.02)
    direction = (middle - flat / 2, CAP)
    stroke = across(direction, m.cap_diag * m.v(1, 1, black=0.96))
    notch = intersect((stroke, 0), (stroke + direction[0], CAP), (middle, 0), (middle, CAP))
    body = polygon(
        [
            (0, 0),
            (middle - flat / 2, CAP),
            (middle + flat / 2, CAP),
            (width, 0),
            (width - stroke, 0),
            notch,
            (stroke, 0),
        ]
    )
    bar_bottom = m.v(172, 160, black=144)
    bar_top = bar_bottom + m.cap_bar * m.v(0.95, 0.95, black=0.84)
    left = direction[0] / CAP * bar_top + stroke * 0.5
    return spaced(m, [body, rect(left, bar_bottom, width - left, bar_top)], width, m.v(*OPEN_DIAGONAL_SIDE), m.v(*OPEN_DIAGONAL_SIDE), capital=True)


def capital_b(m):
    stem = m.cap_stem
    width = m.v(528, 598, black=652)
    bar = m.v(76, 118, light=54, black=130)
    waist = CAP * m.v(0.53, 0.525, black=0.512)
    upper = lobe(m, stem * 0.5, stem * 0.8, width - m.v(26, 30), CAP, waist - bar / 2, bar, m.cap_round * m.v(0.96, 0.86, black=0.8))
    lower = lobe(m, stem * 0.5, stem * 0.8, width, waist + bar / 2, 0, bar, m.cap_round * m.v(1.0, 0.95, black=0.9))
    return spaced(m, [rect(0, 0, stem, CAP)] + upper + lower, width, "cap", m.v(34, 24))


def end_x(reach, heading, thickness):
    return reach - thickness / (2 * abs(heading[1]))


def capital_c(m):
    width = m.v(*C_WIDTH)
    side = m.cap_round
    flat = m.cap_thin
    reach = width - m.v(40, 34)
    end = m.v(84, 134, light=58, black=154)
    rise = aim(m.v(117, 119, black=CUT_RISE))
    fall = aim(m.v(63, 61, black=180 - CUT_RISE))
    shape = ribbon(
        [
            Node((end_x(reach, rise, end), terminal_high(m)), rise, end, cut="h"),
            Node((width * 0.52, CAP + m.cap_ov - flat / 2), LEFT, flat),
            Node((side / 2, CAP / 2), DOWN, side),
            Node((width * 0.52, flat / 2 - m.cap_ov), RIGHT, flat),
            Node((end_x(reach, fall, end), terminal_low(m)), fall, end, cut="h"),
        ],
        0.6,
    )
    return spaced(m, [shape], reach, "cap_round", m.v(14, 2))


def capital_d(m):
    stem = m.cap_stem
    width = m.v(*D_WIDTH)
    shapes = [rect(0, 0, stem, CAP)] + lobe(
        m, stem * 0.5, stem * 0.8, width, CAP, 0, m.cap_bar * m.v(1, 1, black=BOWL_BAR), m.cap_round, rx=m.v(*D_RX)
    )
    return spaced(m, shapes, width, "cap", "cap_round")


def capital_e(m):
    stem = m.cap_stem
    width = m.v(468, 526)
    bar = m.cap_bar
    shapes = [
        rect(0, 0, stem, CAP),
        rect(stem * 0.5, CAP - bar, width, CAP),
        crossbar(m, stem * 0.5, width - m.v(34, 30), WAIST),
        rect(stem * 0.5, 0, width, bar),
    ]
    return spaced(m, shapes, width, "cap", m.v(32, 28, black=21))


def capital_f(m):
    stem = m.cap_stem
    width = m.v(452, 508)
    shapes = [
        rect(0, 0, stem, CAP),
        rect(stem * 0.5, CAP - m.cap_bar, width, CAP),
        crossbar(m, stem * 0.5, width - m.v(34, 30), CAP * 0.5),
    ]
    return spaced(m, shapes, width, "cap", m.v(14, 12))


def capital_g(m):
    width = m.v(*G_WIDTH)
    side = m.cap_round
    flat = m.cap_thin
    spur = m.cap_stem * m.v(0.98, 0.96)
    bar_top = m.v(362, 374)
    reach = width - m.v(26, 22)
    end = m.v(84, 134, light=58, black=154)
    rise = aim(m.v(117, 119, black=CUT_RISE))
    shape = ribbon(
        [
            Node((end_x(reach, rise, end), terminal_high(m)), rise, end, cut="h"),
            Node((width * 0.52, CAP + m.cap_ov - flat / 2), LEFT, flat),
            Node((side / 2, CAP / 2), DOWN, side),
            Node((width * 0.52, flat / 2 - m.cap_ov), RIGHT, flat),
            Node((width - spur / 2, m.v(292, 284)), UP, spur),
            Node((width - spur / 2, bar_top), UP, spur, straight=True, cut="h"),
        ],
        0.6,
    )
    bar = rect(width * m.v(0.52, 0.5), bar_top - m.cap_bar, width - spur / 2, bar_top)
    return spaced(m, [shape, bar], width, "cap_round", m.v(46, 28))


def capital_h(m):
    stem = m.cap_stem
    width = m.v(566, 632)
    shapes = [
        rect(0, 0, stem, CAP),
        rect(width - stem, 0, width, CAP),
        crossbar(m, stem * 0.5, width - stem * 0.5, WAIST),
    ]
    return spaced(m, shapes, width, "cap", "cap")


def capital_i(m):
    stem = m.cap_stem
    return spaced(m, [rect(0, 0, stem, CAP)], stem, m.v(84, 66), m.v(84, 66), capital=True)


def capital_j(m):
    width = m.v(404, 458, black=506)
    stem = m.cap_stem
    flat = m.cap_thin
    post = width - stem / 2
    shape = ribbon(
        [
            Node((post, CAP), DOWN, stem, cut="h"),
            Node((post, m.v(240, 252, black=268)), DOWN, stem, straight=True),
            Node((width * m.v(0.47, 0.46, black=0.45), flat / 2 - m.cap_ov), LEFT, flat),
            Node((m.v(48, 76, black=70), m.v(146, 162, black=226)), aim(m.v(122, 124, black=118)), m.v(82, 128, light=56, black=148), cut="h"),
        ],
        0.6,
    )
    return spaced(m, [shape], width, m.v(-16, -22), "cap")


def capital_k(m):
    width = m.v(576, 660)
    shapes = kay(m, m.cap_stem, width, CAP, CAP, m.v(252, 214), m.v(18, 14), m.cap_diag)
    return spaced(m, shapes, width, "cap", "cap_diagonal")


def capital_l(m):
    stem = m.cap_stem
    width = m.v(436, 490)
    shapes = [rect(0, 0, stem, CAP), rect(stem * 0.5, 0, width, m.cap_bar)]
    return spaced(m, shapes, width, "cap", m.v(4, -2))


def capital_m(m):
    stem = m.cap_stem
    width = m.v(716, 812, black=876)
    thickness = m.cap_diag * m.v(0.94, 0.88, black=0.84)
    inset = 0
    for _ in range(8):
        middle, stroke = vee(width - 2 * inset, thickness * m.v(1.15, 1.0, black=0.8), CAP, thickness)
        inset = max(0, stem - stroke + m.v(2, 3))
    shapes = [rect(0, 0, stem, CAP), rect(width - stem, 0, width, CAP), shift([middle], inset)[0]]
    return spaced(m, shapes, width, "cap", "cap")


def capital_n(m):
    stem = m.cap_stem
    width = m.v(590, 660)
    stroke = band_width(width, CAP, m.cap_diag * m.v(1.0, 0.94))
    shapes = [
        rect(0, 0, stem, CAP),
        rect(width - stem, 0, width, CAP),
        band((0, CAP), (width - stroke, 0), stroke),
    ]
    return spaced(m, shapes, width, "cap", "cap")


def capital_o(m):
    width = m.v(*ROUND_WIDTH)
    shapes = ring(0, -m.cap_ov, width, CAP + m.cap_ov, m.cap_round, m.cap_thin, m.k_out, m.k_in)
    return spaced(m, shapes, width, "cap_round", "cap_round")


def capital_p(m):
    stem = m.cap_stem
    width = m.v(500, 566, black=634)
    shapes = [rect(0, 0, stem, CAP)] + lobe(
        m, stem * 0.5, stem * 0.8, width, CAP, m.v(296, 282, black=256), m.cap_bar * m.v(1, 1, black=BOWL_BAR), m.cap_round * m.v(1, 1, black=0.94)
    )
    return spaced(m, shapes, width, "cap", m.v(30, 22))


def capital_q(m):
    width = m.v(*ROUND_WIDTH)
    shapes = ring(0, -m.cap_ov, width, CAP + m.cap_ov, m.cap_round, m.cap_thin, m.k_out, m.k_in)
    slope = aim(m.v(*Q_SLOPE))
    stroke = m.cap_diag * m.v(0.92, 0.9, light=0.94, black=0.86)
    entry = (width * Q_ENTRY, m.cap_thin - m.cap_ov + m.v(92, 84, light=96, black=70))
    depth = m.v(*Q_DEPTH)
    run = (entry[1] + depth) / -slope[1]
    exit = (entry[0] + slope[0] * run, entry[1] + slope[1] * run)
    tip, heel = edges(Node(entry, slope, stroke))
    low, high = edges(Node(exit, slope, stroke, cut="h"))
    cut = ((heel[0] - tip[0]) / stroke, (heel[1] - tip[1]) / stroke)
    sunk = m.v(*Q_SEAT) * (reach_into(shapes[1], heel, cut) + Q_BURY)
    seat = (heel[0] + cut[0] * sunk, heel[1] + cut[1] * sunk)
    buried = (reach_into(shapes[1], heel, slope) + reach_into(shapes[0], heel, slope)) / 2
    knee = (heel[0] + slope[0] * buried, heel[1] + slope[1] * buried)
    return spaced(m, shapes + [polygon([tip, low, high, knee, seat])], width, "cap_round", "cap_round")


def reach_into(contour, start, heading):
    here = contour.start
    nearest = None
    for segment in contour.segments:
        curve = (here, *segment) if len(segment) == 3 else (here, here, segment[0], segment[0])
        for t in range(Q_SAMPLES):
            a, b = point_at(curve, t / Q_SAMPLES), point_at(curve, (t + 1) / Q_SAMPLES)
            hit = crossed_at(start, heading, a, b)
            if hit is not None and (nearest is None or hit < nearest):
                nearest = hit
        here = segment[-1]
    return nearest or 0


def point_at(curve, t):
    s = 1 - t
    weights = (s * s * s, 3 * s * s * t, 3 * s * t * t, t * t * t)
    return tuple(sum(weight * point[axis] for weight, point in zip(weights, curve)) for axis in (0, 1))


def crossed_at(start, heading, a, b):
    edge = (b[0] - a[0], b[1] - a[1])
    denominator = heading[0] * edge[1] - heading[1] * edge[0]
    if abs(denominator) < 1e-9:
        return None
    offset = (a[0] - start[0], a[1] - start[1])
    along = (offset[0] * edge[1] - offset[1] * edge[0]) / denominator
    share = (offset[0] * heading[1] - offset[1] * heading[0]) / denominator
    if along >= 0 and 0 <= share <= 1:
        return along
    return None


def capital_r(m):
    stem = m.cap_stem
    width = m.v(542, 614, black=682)
    bar = m.cap_bar * m.v(1, 1, black=BOWL_BAR)
    bottom = m.v(316, 304, black=274)
    shapes = [rect(0, 0, stem, CAP)] + lobe(
        m, stem * 0.5, stem * 0.8, width - m.v(18, 16), CAP, bottom, bar, m.cap_round * m.v(1, 1, black=0.94)
    )
    top = (m.v(236, 250), bottom + bar * 0.5)
    stroke = band_width(width - top[0], top[1], m.cap_diag * m.v(1.0, 0.96))
    shapes.append(band(top, (width - stroke, 0), stroke))
    return spaced(m, shapes, width, "cap", m.v(26, 16))


def ess_shape(m, lift=0):
    width = m.v(522, 594, light=482)
    flat = m.cap_thin * m.v(1, 1, black=0.9)
    inset = m.v(12, 10)
    upper_side = m.v(92, 152, light=60, black=190)
    lower_side = m.v(96, 160, light=62, black=198)
    end = m.v(84, 134, light=58, black=150)
    rise = aim(m.v(117, 119, black=CUT_RISE))
    top_reach = width - inset - m.v(8, 6)
    crown = m.v(5, 8)
    shoulder = m.v(0.84, 0.8)
    shape = ribbon(
        [
            Node((end_x(top_reach, rise, end), terminal_high(m) + m.v(0, 0, black=14) + lift), rise, end, cut="h"),
            Node((width * 0.5 + crown, CAP + m.cap_ov - flat / 2), LEFT, flat),
            Node((inset + upper_side / 2, m.v(526, 520)), DOWN, upper_side, leave=shoulder),
            Node((width * 0.5, CAP * 0.5 + m.v(6, 8)), aim(-m.v(20, 16)), m.v(88, 142, light=58, black=152)),
            Node((width - lower_side / 2, m.v(196, 200)), DOWN, lower_side, arrive=shoulder),
            Node((width * 0.5 - crown, flat / 2 - m.cap_ov), LEFT, flat),
            Node((end / (2 * rise[1]), terminal_low(m) - m.v(0, 0, black=16) - lift), rise, end, cut="h"),
        ],
        0.6,
    )
    return shape, width


def capital_s(m):
    shape, width = ess_shape(m)
    return spaced(m, [shape], width, m.v(28, 16), m.v(30, 18), capital=True)


def capital_t(m):
    stem = m.cap_stem
    width = m.v(516, 574)
    shapes = [
        rect(0, CAP - m.cap_bar, width, CAP),
        rect((width - stem) / 2, 0, (width + stem) / 2, CAP),
    ]
    return spaced(m, shapes, width, m.v(*BAR_SIDE), m.v(*BAR_SIDE), capital=True)


def capital_u(m):
    stem = m.cap_stem
    width = m.v(564, 630)
    middle = width / 2
    outer_y = m.v(252, 262)
    inner_y = outer_y - m.v(0, 10)
    path = Path((0, CAP))
    path.to((stem, CAP))
    path.to((stem, inner_y))
    path.arc((middle, m.cap_thin - m.cap_ov), "v", m.k_in)
    path.arc((width - stem, inner_y), "h", m.k_in)
    path.to((width - stem, CAP))
    path.to((width, CAP))
    path.to((width, outer_y))
    path.arc((middle, -m.cap_ov), "v", m.k_out)
    path.arc((0, outer_y), "h", m.k_out)
    return spaced(m, [path.close()], width, m.v(74, 58), m.v(74, 58), capital=True)


def capital_v(m):
    width = m.v(590, 670)
    shape, _ = vee(width, m.cap_diag * m.v(1.15, 1.05), CAP, m.cap_diag)
    return spaced(m, [shape], width, m.v(*OPEN_DIAGONAL_SIDE), m.v(*OPEN_DIAGONAL_SIDE), capital=True)


def capital_w(m):
    span = m.v(478, 548, black=592)
    thickness = m.cap_diag * m.v(0.96, 0.9, black=0.84)
    first, stroke = vee(span, thickness * m.v(1.1, 1.0, black=0.8), CAP, thickness)
    offset = span - stroke
    corners = list(first.corners())
    left_feet = [corners[6], corners[0], corners[1], corners[2], corners[3], corners[4]]
    right_feet = [(x + offset, y) for x, y in corners[2:6]]
    crotch = intersect(corners[4], corners[5], (offset, CAP), (corners[6][0] + offset, 0))
    points = left_feet + right_feet + [(corners[6][0] + offset, 0), crotch, corners[5]]
    return spaced(m, [polygon(points)], span * 2 - stroke, m.v(*OPEN_DIAGONAL_SIDE), m.v(*OPEN_DIAGONAL_SIDE), capital=True)


def capital_x(m):
    width = m.v(574, 652)
    stroke = band_width(width, CAP, m.cap_diag)
    shapes = [
        band((0, CAP), (width - stroke, 0), stroke),
        band((width - stroke, CAP), (0, 0), stroke),
    ]
    return spaced(m, shapes, width, "cap_diagonal", "cap_diagonal")


def capital_y(m):
    stem = m.cap_stem
    width = m.v(578, 656)
    middle = width / 2
    fork = m.v(300, 292)
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
    return spaced(m, [polygon(points)], width, m.v(*OPEN_DIAGONAL_SIDE), m.v(*OPEN_DIAGONAL_SIDE), capital=True)


def capital_z(m):
    width = m.v(522, 584)
    shape = zed(width, CAP, m.cap_bar, m.cap_diag * m.v(1.0, 0.96))
    return spaced(m, [shape], width, m.v(30, 20), m.v(30, 20), capital=True)
