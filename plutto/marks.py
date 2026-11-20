import math

from .capitals import ess_shape
from .lowercase import letter_a
from .geometry import Contour, Path, across, bend, flip, lerp
from .masters import ASC, BOLD_WEIGHT, CAP, DESC, XH, family
from .parts import Glyph, band, band_width, spaced, vee
from .shapes import Node, aim, extent, flop, mirror, place, polygon, rect, ribbon, ring, shift, turn

DOWN = (0, -1)
UP = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
AXIS = 262
TALL_TOP = CAP + 38
TALL_BOTTOM = DESC + 22


def square(m):
    return m.v(100, 162, light=68, black=212)


def gap(m):
    return m.v(70, 56)


def drop(m):
    return m.v(126, 108, light=132, black=96)


def quote_bottom(m):
    return CAP - square(m) - drop(m)


def tick(m):
    side = square(m)
    fall = drop(m)
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


def raised(m, turned):
    side = square(m)
    shape = tick(m)
    if turned:
        shape = turn([shape], side / 2, (side - drop(m)) / 2)[0]
    return shift([shape], 0, CAP - side)[0]


def pair(m, shape):
    step = square(m) + m.v(62, 56, light=66, black=68)
    return [shape, shift([shape], step)[0]], step + square(m)


def space(m):
    return Glyph([], m.v(258, 275, light=253, black=289))


def notdef(m):
    edge = m.v(60, 96, light=40, black=126)
    shapes = [rect(0, 0, 500, CAP), rect(edge, edge, 500 - edge, CAP - edge, hole=True)]
    return spaced(m, shapes, 500, 50, 50)


def period(m):
    side = square(m)
    return spaced(m, [rect(0, 0, side, side)], side, gap(m), gap(m))


def comma(m):
    return spaced(m, [tick(m)], square(m), gap(m), gap(m))


def colon(m):
    side = square(m)
    shapes = [rect(0, 0, side, side), rect(0, XH - side, side, XH)]
    return spaced(m, shapes, side, gap(m), gap(m))


def semicolon(m):
    side = square(m)
    return spaced(m, [tick(m), rect(0, XH - side, side, XH)], side, gap(m), gap(m))


def ellipsis(m):
    side = square(m)
    step = side + m.v(96, 78)
    shapes = [rect(index * step, 0, index * step + side, side) for index in range(3)]
    return spaced(m, shapes, step * 2 + side, gap(m), gap(m))


def periodcentered(m):
    side = square(m)
    return spaced(m, [rect(0, AXIS - side / 2, side, AXIS + side / 2)], side, gap(m), gap(m))


def exclam(m):
    side = square(m)
    stem = m.cap_stem
    inset = (side - stem) / 2
    shapes = [rect(0, 0, side, side), rect(inset, side + m.v(96, 74, black=66), inset + stem, CAP)]
    return spaced(m, shapes, side, m.v(76, 60), m.v(76, 60))


def question(m):
    width = m.v(424, 474)
    edge = m.v(90, 152, light=58, black=200)
    flat = m.cap_thin
    stem = m.cap_stem * m.v(0.96, 0.92)
    side = square(m)
    top = CAP + m.cap_ov
    post = width / 2 + m.v(4, 2)
    foot = side + m.v(96, 74, black=66)
    hook = ribbon(
        [
            Node((m.v(46, 74), m.v(554, 544)), aim(m.v(62, 60)), m.v(80, 128, light=54, black=162), cut="h"),
            Node((width * 0.49, top - flat / 2), RIGHT, flat),
            Node((width - edge / 2, m.v(546, 552)), DOWN, edge),
            Node((post + m.v(66, 76), m.v(398, 400)), aim(m.v(230, 228)), m.v(80, 128, light=54, black=162)),
            Node((post, m.v(274, 288, black=290)), DOWN, stem, arrive=0.8),
            Node((post, foot), DOWN, stem, straight=True),
        ],
        0.6,
    )
    return spaced(m, [hook, rect(post - side / 2, 0, post + side / 2, side)], width, m.v(34, 26), m.v(40, 30))


def quotesingle(m):
    width = m.v(80, 132, light=54, black=176)
    return spaced(m, [rect(0, quote_bottom(m), width, CAP)], width, m.v(60, 48), m.v(60, 48))


def quotedbl(m):
    width = m.v(80, 132, light=54, black=176)
    step = width + m.v(72, 64, light=76, black=80)
    bottom = quote_bottom(m)
    shapes = [rect(0, bottom, width, CAP), rect(step, bottom, step + width, CAP)]
    return spaced(m, shapes, step + width, m.v(60, 48), m.v(60, 48))


def quoteright(m):
    return spaced(m, [raised(m, False)], square(m), m.v(54, 44), m.v(54, 44))


def quoteleft(m):
    return spaced(m, [raised(m, True)], square(m), m.v(54, 44), m.v(54, 44))


def quotedblright(m):
    shapes, width = pair(m, raised(m, False))
    return spaced(m, shapes, width, m.v(54, 44), m.v(54, 44))


def quotedblleft(m):
    shapes, width = pair(m, raised(m, True))
    return spaced(m, shapes, width, m.v(54, 44), m.v(54, 44))


def paren(m):
    stroke = m.v(82, 142, light=54, black=190)
    depth = m.v(118, 132)
    middle = (TALL_TOP + TALL_BOTTOM) / 2
    lean = 2 * math.atan(depth / (TALL_TOP - middle))
    upper = (-math.sin(lean), -math.cos(lean))
    lower = (math.sin(lean), -math.cos(lean))
    path = Path((depth, TALL_TOP))
    path.bez(bend((depth, TALL_TOP), upper, (0, middle), DOWN, 0.56, 0.56))
    path.bez(bend((0, middle), DOWN, (depth, TALL_BOTTOM), lower, 0.56, 0.56))
    path.to((depth + stroke, TALL_BOTTOM))
    path.bez(bend((depth + stroke, TALL_BOTTOM), lower, (stroke, middle), DOWN, 0.56, 0.56))
    path.bez(bend((stroke, middle), DOWN, (depth + stroke, TALL_TOP), upper, 0.56, 0.56))
    return path.close(), depth + stroke


def parenleft(m):
    shape, width = paren(m)
    return spaced(m, [shape], width, m.v(52, 40), m.v(14, 8))


def parenright(m):
    shape, width = paren(m)
    return spaced(m, turn([shape], width / 2, (TALL_TOP + TALL_BOTTOM) / 2), width, m.v(14, 8), m.v(52, 40))


def slash(m):
    width = m.v(360, 410)
    stroke = band_width(width, TALL_TOP - TALL_BOTTOM, m.cap_diag * m.v(0.92, 0.9))
    shape = band((width - stroke, TALL_TOP), (0, TALL_BOTTOM), stroke)
    return spaced(m, [shape], width, m.v(10, 6), m.v(10, 6))


def dash(m, width):
    return spaced(m, [rect(0, AXIS - m.bar / 2, width, AXIS + m.bar / 2)], width, m.v(48, 40), m.v(48, 40))


def hyphen(m):
    return dash(m, m.v(280, 304))


def endash(m):
    return dash(m, m.v(464, 486))


def emdash(m):
    return dash(m, m.v(820, 842))


def underscore(m):
    width = m.v(520, 540)
    return Glyph([rect(0, DESC + 14, width, DESC + 14 + m.v(64, 100, light=44, black=126))], width)


def plus(m):
    width = m.v(420, 444)
    bar = m.bar
    centre = m.v(326, 326)
    shapes = [
        rect(0, centre - bar / 2, width, centre + bar / 2),
        rect((width - bar) / 2, centre - width / 2, (width + bar) / 2, centre + width / 2),
    ]
    return spaced(m, shapes, width, m.v(62, 52), m.v(62, 52))


def equal(m):
    width = m.v(420, 444)
    bar = m.bar
    centre = m.v(326, 326)
    lift = m.v(86, 96)
    shapes = [
        rect(0, centre + lift - bar / 2, width, centre + lift + bar / 2),
        rect(0, centre - lift - bar / 2, width, centre - lift + bar / 2),
    ]
    return spaced(m, shapes, width, m.v(62, 52), m.v(62, 52))


def backslash(m):
    width = m.v(360, 410)
    stroke = band_width(width, TALL_TOP - TALL_BOTTOM, m.cap_diag * m.v(0.92, 0.9))
    shape = band((0, TALL_TOP), (width - stroke, TALL_BOTTOM), stroke)
    return spaced(m, [shape], width, m.v(10, 6), m.v(10, 6))


def bar(m):
    width = m.v(78, 130, light=52, black=174)
    return spaced(m, [rect(0, TALL_BOTTOM, width, TALL_TOP)], width, m.v(96, 78), m.v(96, 78))


def bracket(m):
    stem = m.v(80, 136, light=52, black=182)
    flat = m.v(68, 104, light=48, black=134)
    width = m.v(190, 250)
    shapes = [
        rect(0, TALL_BOTTOM, stem, TALL_TOP),
        rect(0, TALL_TOP - flat, width, TALL_TOP),
        rect(0, TALL_BOTTOM, width, TALL_BOTTOM + flat),
    ]
    return shapes, width


def bracketleft(m):
    shapes, width = bracket(m)
    return spaced(m, shapes, width, m.v(74, 58), m.v(14, 8))


def bracketright(m):
    shapes, width = bracket(m)
    return spaced(m, mirror(shapes, width / 2), width, m.v(14, 8), m.v(74, 58))


def brace(m):
    stem = m.v(86, 144, light=56, black=190)
    flat = m.v(58, 90, light=46, black=116)
    tip = m.v(28, 44, light=26)
    lap = m.v(6, 10)
    centre = m.v(122, 156)
    reach = centre + m.v(118, 134)
    middle = (TALL_TOP + TALL_BOTTOM) / 2
    top = TALL_TOP - flat / 2
    upper = ribbon(
        [
            Node((reach, top), LEFT, flat),
            Node((centre, top - m.v(124, 122)), DOWN, stem, arrive=0.62),
            Node((centre, middle + m.v(124, 128)), DOWN, stem, straight=True),
            Node((0, middle + tip / 2 - lap), LEFT, tip, arrive=0.56),
        ],
        0.6,
    )
    return [upper] + flop([upper], middle), reach


def braceleft(m):
    shapes, width = brace(m)
    return spaced(m, shapes, width, m.v(30, 22), m.v(46, 38))


def braceright(m):
    shapes, width = brace(m)
    return spaced(m, mirror(shapes, width / 2), width, m.v(46, 38), m.v(30, 22))


def math_width(m):
    return m.v(420, 444)


def math_bearing(m):
    return m.v(62, 52)


def on_math_advance(m, shapes, width):
    bearing = (math_width(m) - width) / 2 + math_bearing(m)
    return spaced(m, shapes, width, bearing, bearing)


def chevron(m):
    width = m.v(400, 430)
    height = m.v(420, 440)
    centre = 326
    rise = across((height / 2, width), m.v(74, 116, light=50, black=150))
    reach = rise * width / (height / 2)
    points = [
        (width, centre + height / 2),
        (width, centre + height / 2 - rise),
        (reach, centre),
        (width, centre - height / 2 + rise),
        (width, centre - height / 2),
        (0, centre),
    ]
    return polygon(points), width


def less(m):
    shape, width = chevron(m)
    return on_math_advance(m, [shape], width)


def greater(m):
    shape, width = chevron(m)
    return on_math_advance(m, mirror([shape], width / 2), width)


def asciicircum(m):
    width = m.v(420, 450)
    thickness = m.v(72, 118, light=48, black=156)
    shape, _ = vee(width, thickness * 1.1, m.v(320, 330), thickness)
    return spaced(m, [place(shape, 0, CAP, fy=-1)], width, m.v(56, 46), m.v(56, 46))


def grave(m):
    run = m.v(116, 128)
    stroke = across((run, 150), m.v(64, 104, light=44, black=136))
    shape = band((0, ASC + 16), (run, ASC - 134), stroke)
    return spaced(m, [shape], run + stroke, m.v(80, 70), m.v(80, 70))


def asciitilde(m):
    width = m.v(440, 476)
    lift = m.v(50, 46)
    half = m.v(72, 118, light=48, black=152) / 2
    centre = 326
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
    return spaced(m, [path.close()], width, m.v(56, 46), m.v(56, 46))


def numbersign(m):
    width = m.v(566, 620)
    lean = 64
    stroke = across((lean, CAP), m.v(70, 112, light=46, black=146))
    flat = m.bar * m.v(0.94, 0.9)
    first = m.v(104, 96)
    step = m.v(206, 232)
    shapes = [
        band((first + lean, CAP), (first, 0), stroke),
        band((first + step + lean, CAP), (first + step, 0), stroke),
        rect(lean * 0.5, CAP * 0.62, width, CAP * 0.62 + flat),
        rect(0, CAP * 0.26, width - lean * 0.5, CAP * 0.26 + flat),
    ]
    return spaced(m, shapes, width, m.v(34, 26), m.v(34, 26))


PERCENT_WIDTH = (780, 872, 748, 982)
PERCENT_LOOP = (304, 360, 292, 420)
PERCENT_TALL = (362, 380, 360, 404)
PERCENT_EDGE = (70, 108, 47, 130)
PERCENT_FLAT = (60, 86, 43, 94)


def percent(m):
    width = m.v(*PERCENT_WIDTH)
    loop = m.v(*PERCENT_LOOP)
    tall = m.v(*PERCENT_TALL)
    edge = m.v(*PERCENT_EDGE)
    flat = m.v(*PERCENT_FLAT)
    foot = loop * 0.6
    stroke = band_width(width - loop * 0.6 - foot, CAP, m.cap_diag * m.v(0.84, 0.82))
    shapes = ring(0, CAP + m.cap_ov - tall, loop, CAP + m.cap_ov, edge, flat, m.k_out, m.k_in)
    shapes += ring(width - loop, -m.cap_ov, width, tall - m.cap_ov, edge, flat, m.k_out, m.k_in)
    shapes.append(band((width - loop * 0.6 - stroke, CAP), (foot, 0), stroke))
    return spaced(m, shapes, width, m.v(36, 28), m.v(36, 28))


def asterisk(m):
    radius = m.v(150, 164, black=186)
    half = m.v(33, 54, light=22, black=52)
    shapes = []
    for degrees in (90, 30, -30):
        angle = math.radians(degrees)
        ux, uy = math.cos(angle) * radius, math.sin(angle) * radius
        nx, ny = -math.sin(angle) * half, math.cos(angle) * half
        shapes.append(polygon([(ux + nx, uy + ny), (ux - nx, uy - ny), (-ux - nx, -uy - ny), (-ux + nx, -uy + ny)]))
    reach = math.cos(math.radians(30)) * radius + math.sin(math.radians(30)) * half
    shapes = shift(shapes, reach, CAP - radius + 8)
    return spaced(m, shapes, reach * 2, m.v(44, 36), m.v(44, 36))


def dollar(m):
    shape, width = ess_shape(m)
    stub = m.v(70, 112, light=46, black=146)
    reach = m.v(84, 80)
    left = (width - stub) / 2
    shapes = [
        shape,
        rect(left, CAP - 30, left + stub, CAP + reach),
        rect(left, -reach, left + stub, 30),
    ]
    return spaced(m, shapes, width, m.v(36, 26), m.v(38, 28))


def blend_value(own, other, share):
    return own + (other - own) * share


def blend(own, other, share):
    return [
        Contour(
            lerp(mine.start, theirs.start, share),
            [tuple(lerp(a, b, share) for a, b in zip(first, second)) for first, second in zip(mine.segments, theirs.segments)],
            mine.hole,
        )
        for mine, theirs in zip(own, other)
    ]


def at(m):
    width = m.v(804, 900, black=948)
    bottom, top = -150, 690
    middle = (top + bottom) / 2
    edge = m.v(70, 116, light=46, black=146)
    flat = m.v(56, 86, light=38, black=106)
    scale = m.v(0.78, 0.74, black=0.8)
    right = m.v(572, 640, black=680)
    base = m.v(68, 80)
    knee = base + m.v(80, 110)
    lighter = next(each for each in family(m) if each.weight == BOLD_WEIGHT)
    share = m.v(0, 0, black=0.6)
    head, *belly = shift(blend(letter_a(m).contours, letter_a(lighter).contours, share), -blend_value(m.bearing("round"), lighter.bearing("round"), share))
    floor = blend_value(m.thin, lighter.thin, share) * m.v(0.95, 0.92)
    head = head.map(lambda point: (point[0], max(point[1], floor)))
    letter = [head] + belly
    left = right - extent(letter) * scale
    inner = [place(contour, left, base, scale, scale) for contour in letter]
    stem = blend_value(m.stem, lighter.stem, share) * scale
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


AMP_SWING = (134, 160, 124, 200)
AMP_LOOP_LEFT = (146, 168, None, 224)
AMP_CROWN = (76, 122, None, 142)
AMP_CROSS = (68, 112, None, 134)
AMP_LOOP_X = (398, 430, None, 494)
AMP_LOOP_SIDE = (76, 122, None, 144)
AMP_LOOP_FLAT = (66, 88, None, 108)
AMP_CROSS_AT = (238, 276, None, 320)
AMP_FOOT = (548, 588, None, 618)
AMP_CROWN_RISE = (63, 50, None, 40)
AMP_HIP = (72, 118, None, 146)
AMP_SOLE = (84, 138, None, 172)
AMP_TIP_X = (552, 604, None, 650)
AMP_TIP_Y = (318, 326, None, 330)
AMP_FLARE = (84, 140, None, 164)
AMP_SWING_X = (469, 518, None, 530)
AMP_SWING_ANGLE = (226, 222.4, None, 220)
AMP_SWING_WEIGHT = (70, 116, None, 136)
AMP_BASE_X = (270, 300, None, 326)
AMP_BASE_Y = (22, 41, None, 56)
AMP_BASE = (72, 110, None, 138)
AMP_BACK_X = (43, 75, None, 94)
AMP_BACK_Y = (178, 182, None, 186)
AMP_BACK = (86, 150, None, 186)
AMP_LOOP_Y = (580, 585, None, 580)
AMP_LOOP_TOP_X = (268, 300, None, 352)


def ampersand(m):
    fall = 52
    drop = aim(-fall)
    slope = math.tan(math.radians(fall))
    foot = (m.v(*AMP_FOOT), 0)

    def on_leg(x):
        return (x, (foot[0] - x) * slope)

    loop_left = m.v(*AMP_LOOP_LEFT)
    turn_at = on_leg(loop_left)
    run = m.v(80, 84)
    crown = Node((loop_left, turn_at[1] + m.v(*AMP_CROWN_RISE)), DOWN, m.v(*AMP_CROWN))
    hip = Node((turn_at[0] + run * drop[0], turn_at[1] + run * drop[1]), drop, m.v(*AMP_HIP))
    sole = m.v(*AMP_SOLE)
    lap = (hip.point[1] - on_leg(m.v(*AMP_CROSS_AT))[1]) / hip.point[1]
    overlap = Node(
        (hip.point[0] + (foot[0] - hip.point[0]) * lap, hip.point[1] + (foot[1] - hip.point[1]) * lap),
        drop,
        hip.thickness + (sole - hip.thickness) * lap,
        straight=True,
    )
    loop_flat = m.v(*AMP_LOOP_FLAT)
    tip = (m.v(*AMP_TIP_X), m.v(*AMP_TIP_Y))
    flare = m.v(*AMP_FLARE)
    body = ribbon(
        [
            Node(tip, aim(262), flare, cut="h"),
            Node((m.v(*AMP_SWING_X), m.v(*AMP_SWING)), aim(m.v(*AMP_SWING_ANGLE)), m.v(*AMP_SWING_WEIGHT)),
            Node((m.v(*AMP_BASE_X), m.v(*AMP_BASE_Y)), LEFT, m.v(*AMP_BASE)),
            Node((m.v(*AMP_BACK_X), m.v(*AMP_BACK_Y)), UP, m.v(*AMP_BACK), leave=0.72),
            Node(on_leg(m.v(*AMP_CROSS_AT)), aim(28), m.v(*AMP_CROSS), arrive=0.5, leave=0.5),
            Node((m.v(*AMP_LOOP_X), m.v(*AMP_LOOP_Y)), UP, m.v(*AMP_LOOP_SIDE), arrive=0.72),
            Node((m.v(*AMP_LOOP_TOP_X), CAP + m.cap_ov - loop_flat / 2), LEFT, loop_flat),
            crown,
            hip,
            overlap,
        ],
        0.6,
    )
    leg = ribbon([hip, Node(foot, drop, sole, straight=True, cut="h")], 0.6)
    width = max(foot[0] + sole / math.sin(math.radians(fall)) / 2, tip[0] + flare / 2)
    return spaced(m, [body, leg], width, m.v(34, 26), m.v(10, 6))