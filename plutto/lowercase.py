import math

from .geometry import Contour, Path, across, flip, intersect, quarter
from .masters import ASC, DESC, XH
from .parts import HOOK_SPREAD, band, band_width, double_vee, ess, hook, kay, open_bowl, reach, shoulder_inner, shoulder_spring, spaced, vee, zed
from .shapes import (
    arch,
    crossed,
    extent,
    mirror,
    leaning_oval,
    place,
    polygon,
    rect,
    ring,
    turn,
)
from .geometry import bend, lerp, split
from .oblique import ItalicForm
from .shapes import Node, aim, edges, ribbon

G_THICK = (76, 102, 56, 116)
G_PEAK = (0.53, 0.52, 0.53, 0.47)
G_RISE_OUT = (190, 200, None, 250)
G_RISE_IN = (104, 96, 108, 96)
G_FAR_IN = (36, 52)
G_TERMINAL = (114, 144, 100, 90)
G_LEAN = (0, 0, 0, 30)
J_TIP = 3
K_LIFT = (0, 0, 0, 24)
VEE_DEEPEN = (0, 0, 0, 24)
BOWL_NECK = (0.03, 0.14, 0.03, 0.1)
BOWL_SHOULDER = (0.1, 0.24, 0.1, 0.16)
BOWL_REACH = (0.7, 0.7, 0.7, 0.7)
BOWL_FLAT = (1.0, 1.0, 1.0, 0.9)
A_ARCH = (76, 102, 56, 134)
A_TERMINAL = (406, 390, None, 406)
A_BELLY_TOP = (322, 328, None, 358)
A_BELLY_SIDE = (1.0, 1.0, None, 0.76)
A_BELLY_FOOT = (0.95, 0.92, None, 0.7)
A_BELLY_FLAT = (70, 90, 54, 98)
A_BELLY_LEAN = (0, 0, None, 0.05)
A_COUNTER_LEAN = (0, 0, None, 0.08)
S_SIDE = (86, 160, 58, 200)
S_FLAT = (72, 118, 50, 138)
S_SPINE = (88, 148, 58, 152)
S_UPPER = (394, 390, 390, 372)
S_LOWER = (148, 152, 150, 166)
S_ANGLE = (20, 24, 58 / 3, 22)
S_PULL = (0.6, 0.55, 0.6, 0.7)
S_SHOULDER = (0.25, 0.26, None, 0.27)
S_TILT = (0, 6, 0, 0)
S_TIP = (0.9, 0.9, None, 0.8)
E_LEVEL = (0, 1, 0, 0)
E_BAR_WEIGHT = (1.0, 0.88, None, 0.76)
E_LEVEL_RUN = (0, 80, 0, 0)
E_LEVEL_PULL = 0.5
E_TAPER = (1.0, 1.0, None, 0.62)
E_TAIL = (130, 120, 123.33, 122)
E_FLOOR = (74, 120, 52.87, 102)
M_POST = 0.75
M_POST_FOOT = 0.25
M_POST_LAP = 20


def stem_arch(m, x, width):
    stem = m.stem
    shape = arch(
        left_out=x + stem * shoulder_spring(m),
        left_in=x + stem * shoulder_inner(m),
        peak_out=x + width * 0.55,
        peak_in=x + stem + (width - 2 * stem) * 0.52,
        right=x + width,
        top=XH + m.arch_ov,
        base=0,
        stem=stem,
        thick=m.v(76, 112, light=54, black=140),
        ry_out=m.v(200, 214),
        ry_in=m.v(142, 136),
        k_out=m.k_out,
        k_in=m.k_in,
    )
    return crossed(shape, x + stem)


def bowl(m, width):
    stem = m.stem
    return [
        leaning_oval(stem * m.v(0.25, 0.42), -m.ov, width, XH + m.ov, m.k_out, m.k_out - m.v(*BOWL_NECK)),
        leaning_oval(stem * m.v(*BOWL_REACH), m.thin * m.v(*BOWL_FLAT), width - m.round, XH - m.thin * m.v(*BOWL_FLAT), m.k_in, m.k_in + m.v(*BOWL_SHOULDER), hole=True),
    ]


def hook_inner(m):
    return m.v(74, 80)


def descender_hook(m, run, inner_width):
    return hook(m, m.stem, m.v(74, 110, light=52, black=124), XH - DESC, run, inner_width)


def dot(m, x):
    side = m.v(92, 146, light=62, black=182)
    y = XH + m.v(82, 88, light=90, black=94)
    return rect(x - side / 2, y, x + side / 2, y + side)


def hooked_bowl_top(m, width, terminal_y):
    stem = m.stem
    far_out = m.v(28, 22)
    peak_out = width * 0.53
    peak_in = peak_out + m.v(6, 8)
    top = XH + m.ov
    thick = m.v(*A_ARCH)
    y_out = top - m.v(190, 200)
    y_in = top - thick - m.v(104, 96)
    end_out = reach(quarter((peak_out, top), (far_out, y_out), "h", m.k_out), 1, terminal_y)
    end_in = reach(quarter((peak_in, top - thick), (far_out + m.round, y_in), "h", m.k_in), 1, terminal_y)
    path = Path(end_out[3])
    path.bez(flip(end_out))
    path.arc((width, y_out), "h", m.k_out)
    path.to((width, 0))
    path.to((width - stem, 0))
    path.to((width - stem, y_in))
    path.arc((peak_in, top - thick), "v", m.k_in)
    path.bez(end_in)
    return path.close()


def tilted(contour, box, lean):
    x0, y0, x1, y1 = box
    half_x, half_y = (x1 - x0) / 2, (y1 - y0) / 2
    lift = math.hypot(half_y, lean * half_x) - half_y
    pivot = (x0 + x1) / 2
    return contour.map(lambda point: (point[0], point[1] + lean * (point[0] - pivot) + lift))


def levelled_foot(source, moved):
    segments = [list(segment) for segment in moved.segments]
    count = len(segments)
    lowest = min(point[1] for point in source.corners())
    for index, segment in enumerate(source.segments):
        following = source.segments[(index + 1) % count]
        if len(segment) != 3 or len(following) != 3:
            continue
        point = segment[2]
        if segment[1][1] == point[1] == following[0][1] == lowest:
            level = segments[index][2][1]
            segments[index][1] = (segments[index][1][0], level)
            segments[(index + 1) % count][0] = (segments[(index + 1) % count][0][0], level)
    return Contour(moved.start, [tuple(segment) for segment in segments], moved.hole)


def letter_a(m):
    width = m.v(440, 512, light=420, black=590)
    stem = m.stem
    top = hooked_bowl_top(m, width, m.v(*A_TERMINAL))
    belly_top = m.v(*A_BELLY_TOP)
    outer = (0, -m.ov, width - stem * 0.5, belly_top)
    inner = (
        m.round * m.v(*A_BELLY_SIDE),
        m.thin * m.v(*A_BELLY_FOOT),
        width - stem * m.v(*BOWL_REACH),
        belly_top - m.v(*A_BELLY_FLAT),
    )
    rim = leaning_oval(*outer, m.k_out, m.k_out - m.v(*BOWL_NECK), right=True)
    belly = [
        crossed(levelled_foot(rim, tilted(rim, outer, m.v(*A_BELLY_LEAN))), width - stem),
        crossed(tilted(leaning_oval(*inner, m.k_in, m.k_in + m.v(*BOWL_SHOULDER), hole=True, right=True), inner, m.v(*A_COUNTER_LEAN)), width - stem),
    ]
    return spaced(m, [top] + belly, width, "round", "straight")


def letter_b(m):
    width = m.v(472, 540, black=596)
    return spaced(m, [rect(0, 0, m.stem, ASC)] + bowl(m, width), width, "straight", "round")


def letter_c(m):
    width = m.v(428, 476, light=414, black=532)
    side = m.round * m.v(1.0, 1.0, black=0.93)
    thin = m.thin * m.v(1.0, 1.0, black=0.94)
    shape = open_bowl(
        (0, -m.ov, width, XH + m.ov),
        (side, thin, width - side * 0.9, XH - thin),
        m.k_out,
        m.k_in,
        m.v(406, 380, black=350),
        m.v(130, 156, black=190),
    )
    return spaced(m, [shape], extent([shape]), "round", m.v(22, 14))


def letter_d(m):
    width = m.v(472, 540, black=596)
    shapes = [rect(width - m.stem, 0, width, ASC)] + mirror(bowl(m, width), width / 2)
    return spaced(m, shapes, width, "round", "straight")


def levelled(bezier, share, run):
    start, near, far, end = bezier
    end = (end[0] + run, end[1])
    span = (end[0] - start[0]) * E_LEVEL_PULL
    near = lerp(near, (start[0] + span, start[1]), share)
    far = lerp(far, (end[0] - span, end[1]), share)
    return (start, near, far, end)


def letter_e(m):
    width = m.v(462, 524, light=446, black=612)
    side = m.round * m.v(1.0, 1.0, black=0.9)
    bar_bottom = m.v(240, 214, black=212)
    bar_top = bar_bottom + m.bar * m.v(*E_BAR_WEIGHT)
    top, bottom = XH + m.ov, -m.ov
    middle_y = (top + bottom) / 2
    middle_x = width / 2
    inner_top, inner_bottom = XH - m.thin * m.v(1.0, 0.92, black=E_TOP), m.v(*E_FLOOR)
    tail_y = max(m.v(*E_TAIL), inner_bottom)
    floor_x = middle_x - m.v(0, 14, light=0, black=36)
    tail_out = reach(quarter((middle_x, bottom), (width, middle_y), "h", m.k_out), 1, tail_y)
    tail_in = levelled(reach(quarter((floor_x, inner_bottom), (width - side * m.v(*E_TAPER), middle_y), "h", m.k_in), 1, tail_y), m.v(*E_LEVEL), m.v(*E_LEVEL_RUN))
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
    path.arc((floor_x, inner_bottom), "v", m.k_in)
    path.bez(tail_in)
    crossbar = rect(side * 0.5, bar_bottom, width - side * 0.5, bar_top)
    return spaced(m, [path.close(), crossbar], width, "round", m.v(30, 22))


def letter_f(m):
    stem = m.stem
    left = m.v(68, 62, light=60)
    stroke = place(hook(m, stem, m.thin, ASC, stem + m.v(128, 140, light=118), hook_inner(m)), left, ASC, fy=-1)
    crossbar = rect(0, XH - m.bar, left + stem + m.v(104, 112, light=92), XH)
    return spaced(m, [stroke, crossbar], extent([stroke, crossbar]), m.v(18, 12), m.v(8, 4), capital=False)


def descender_tail(m, width, terminal_x):
    stem = m.stem
    bottom = DESC - m.ov
    thick = m.v(*G_THICK)
    peak_out = width * m.v(*G_PEAK)
    peak_in = peak_out + m.v(6, 8)
    y_out = bottom + m.v(*G_RISE_OUT)
    y_in = bottom + thick + m.v(*G_RISE_IN)
    end_out = reach(quarter((peak_out, bottom), (0, y_out), "h", m.k_out), 0, terminal_x)
    end_in = reach(quarter((peak_in, bottom + thick), (m.v(*G_FAR_IN), y_in), "h", m.k_in), 0, terminal_x + m.v(*G_LEAN))
    path = Path(end_out[3])
    path.bez(flip(end_out))
    path.arc((width, y_out), "h", m.k_out)
    path.to((width, XH))
    path.to((width - stem, XH))
    path.to((width - stem, y_in))
    path.arc((peak_in, bottom + thick), "v", m.k_in)
    path.bez(end_in)
    return path.close()


def letter_g(m):
    width = m.v(472, 540, black=586)
    tail = descender_tail(m, width, m.v(*G_TERMINAL))
    return spaced(m, [tail] + mirror(bowl(m, width), width / 2), width, "round", "straight")


def letter_h(m):
    width = m.v(450, 520, black=590)
    return spaced(m, [rect(0, 0, m.stem, ASC), stem_arch(m, 0, width)], width, "straight", m.v(66, 50))


def letter_i(m):
    stem = m.stem
    return spaced(m, [rect(0, 0, stem, XH), dot(m, stem / 2)], stem, "straight", "straight")


def letter_j(m):
    stem = m.stem
    hook_reach = m.v(88, 88, black=90)
    inner = (hook_reach - J_TIP) / HOOK_SPREAD
    left = m.bearing("straight") + m.v(0, 6, light=0, black=10)
    tail = place(descender_hook(m, hook_reach + stem, inner), hook_reach + stem, DESC, fx=-1)
    return spaced(m, [tail, dot(m, hook_reach + stem / 2)], hook_reach + stem, left - hook_reach, "straight")


def letter_k(m):
    width = m.v(446, 536)
    shapes = kay(m, m.stem, width, XH, ASC, m.v(196, 160), m.v(14, 12), m.diag, m.v(*K_LIFT))
    return spaced(m, shapes, width, "straight", "diagonal")


def letter_l(m):
    stem = m.stem
    run = stem + m.v(96, 102)
    shape = hook(m, stem, m.thin, ASC, run, hook_inner(m))
    return spaced(m, [shape], run, "straight", m.v(8, 4))


def letter_m(m):
    stem = m.stem
    span = m.v(418, 496, black=568)
    second = stem_arch(m, span - stem, span)
    joins = [point[1] for point in second.corners() if point[0] == span]
    post = rect(span - stem / 2, XH * M_POST_FOOT, span, min(joins, default=XH * M_POST) + M_POST_LAP)
    shapes = [rect(0, 0, stem, XH), stem_arch(m, 0, span), second, post]
    return spaced(m, shapes, span * 2 - stem, "straight", m.v(66, 50))


def letter_n(m):
    width = m.v(450, 520, black=590)
    return spaced(m, [rect(0, 0, m.stem, XH), stem_arch(m, 0, width)], width, "straight", m.v(66, 50))


def letter_o(m):
    width = m.v(476, 540, black=602)
    return spaced(m, ring(0, -m.ov, width, XH + m.ov, m.round, m.thin, m.k_out, m.k_in), width, "round", "round")


def letter_p(m):
    width = m.v(472, 540, black=596)
    return spaced(m, [rect(0, DESC, m.stem, XH)] + bowl(m, width), width, "straight", "round")


def letter_q(m):
    width = m.v(472, 540, black=596)
    shapes = [rect(width - m.stem, DESC, width, XH)] + mirror(bowl(m, width), width / 2)
    return spaced(m, shapes, width, "round", "straight")


def letter_r(m):
    stem = m.stem
    top = XH + m.arch_ov
    thick = m.v(76, 110, light=56, black=138)
    end = m.v(318, 392, light=282)
    peak_out = m.v(214, 278, light=190)
    peak_in = m.v(206, 256, light=188)
    y_out = top - m.v(184, 200)
    y_in = top - thick - m.v(118, 132)
    end_out = reach(quarter((peak_out, top), (m.v(360, 452, light=320), y_out), "h", m.k_out), 0, end)
    end_in = reach(quarter((peak_in, top - thick), (m.v(352, 446, light=312), y_in), "h", m.k_in), 0, end)
    path = Path((stem * shoulder_spring(m), y_out))
    path.arc((peak_out, top), "v", m.k_out)
    path.bez(end_out)
    path.to(end_in[3])
    path.bez(flip(end_in))
    path.arc((stem * shoulder_inner(m), y_in), "h", m.k_in)
    shapes = [rect(0, 0, stem, XH), path.close()]
    return spaced(m, shapes, end, "straight", m.v(16, 11, light=13, black=6))


def letter_s(m):
    width = m.v(412, 496, light=396, black=584)
    shape = ess(
        m,
        width=width,
        height=XH,
        side=m.v(*S_SIDE),
        flat=m.v(*S_FLAT),
        spine=m.v(*S_SPINE),
        inset=m.v(14, 8, light=16, black=4),
        upper_y=m.v(*S_UPPER),
        lower_y=m.v(*S_LOWER),
        angle=m.v(*S_ANGLE),
        t=m.v(0.56, 0.5),
        pull=m.v(*S_PULL),
        shoulder=m.v(*S_SHOULDER),
        tilt=m.v(*S_TILT),
        tip=m.v(*S_TIP),
    )
    return spaced(m, [shape], width, m.v(30, 22), m.v(32, 24), capital=False)


def letter_t(m):
    stem = m.stem
    left = m.v(68, 62, light=60)
    right = m.v(104, 112, light=92)
    width = left + stem + right
    foot = place(hook(m, stem, m.thin, XH + m.v(132, 128), stem + right, hook_inner(m)), left, 0)
    return spaced(m, [foot, rect(0, XH - m.bar, width, XH)], width, m.v(18, 12), m.v(22, 14), capital=False)


def letter_u(m):
    width = m.v(450, 520, black=590)
    shapes = turn([stem_arch(m, 0, width)], width / 2, XH / 2) + [rect(width - m.stem, 0, width, XH)]
    return spaced(m, shapes, width, m.v(66, 50), "straight")


def letter_v(m):
    width = m.v(440, 510, black=578)
    shape, _ = vee(width, m.diag * m.v(1.2, 1.1), XH, m.diag, m.v(*VEE_DEEPEN))
    return spaced(m, [shape], width, "diagonal", "diagonal")


def letter_w(m):
    span = m.v(372, 452, black=514)
    shape, stroke = double_vee(span, m.diag * m.v(1.15, 1.05), XH, m.diag)
    return spaced(m, [shape], span * 2 - stroke, "diagonal", "diagonal")


def letter_x(m):
    width = m.v(432, 504, black=570)
    stroke = band_width(width, XH, m.diag)
    shapes = [
        band((0, XH), (width - stroke, 0), stroke),
        band((width - stroke, XH), (0, 0), stroke),
    ]
    return spaced(m, shapes, width, "diagonal", "diagonal")


def letter_y(m):
    width = m.v(440, 510, black=578)
    middle = width / 2
    flat = m.diag * m.v(1.2, 1.1)
    direction = (middle - flat / 2, -XH)
    stroke = across(direction, m.diag)
    slope = direction[0] / XH
    foot = width - slope * (XH - DESC)
    tail = polygon([(width - stroke, XH), (width, XH), (foot, DESC), (foot - stroke, DESC)])
    notch = intersect((stroke, XH), (stroke + direction[0], 0), (middle, 0), (middle, XH))
    notch = (notch[0], notch[1] - m.v(*VEE_DEEPEN))
    join = intersect((0, XH), (direction[0], 0), (width - stroke, XH), (foot - stroke, DESC))
    branch = polygon([(0, XH), (stroke, XH), notch, (join[0] + stroke * 0.6, join[1]), join])
    return spaced(m, [tail, branch], width, "diagonal", "diagonal")


def letter_z(m):
    width = m.v(404, 474, black=546)
    shape = zed(width, XH, m.bar, m.diag * m.v(1.0, 0.96))
    return spaced(m, [shape], width, m.v(34, 26), m.v(34, 26), capital=False)


LEFT = (-1, 0)
DOWN = (0, -1)
E_BAR_LOW = (226, 200, 234, 204)
E_RISE = (28, 26, 28, 24)
E_OUTER_TURN = (58, 64, 54, 72)
E_OUTER_REACH = (66, 78, 60, 98)
E_INNER_TURN = (36, 30, 38, 22)
E_INNER_REACH = (46, 42, 44, 34)
E_TURN_PULL = 0.6
E_ITALIC_TAIL = (130, 120, 123.33, 122)
E_ITALIC_FLOOR = (74, 120, 52.87, 108)
E_SIDE = 0.9
E_TOP = 0.72
F_TAIL = (74, 110, 52, 124)
F_REACH = (88, 88, 88, 90)
Y_STRAIGHT = (-58, -52, -60, -48)
Y_TURN = (65, 75, 46, 84)
Y_THICK = (74, 104, 54, 112)
Y_TERMINAL = (34, 30, 36, 26)
Y_TERMINAL_RISE = (8, 10, 8, 10)
Y_TERMINAL_WEIGHT = (0.94, 0.92, 0.95, 0.9)
Y_SWEEP = 164
CURSIVE_PULL = 0.58


def met(bezier, above):
    low, high = 0.0, 1.0
    for _ in range(48):
        middle = (low + high) / 2
        if above(split(bezier, middle)[0][3]) == above(bezier[0]):
            low = middle
        else:
            high = middle
    return split(bezier, (low + high) / 2)[1]


def italic_e(m):
    shapes, width = italic_e_shapes(m)
    return spaced(m, shapes, width, "round", m.v(30, 22))


def italic_e_shapes(m):
    width = m.v(462, 524, light=446, black=602)
    side = m.round * m.v(1.0, 1.0, black=E_SIDE)
    thick = m.bar * m.v(*E_BAR_WEIGHT)
    top, bottom = XH + m.ov, -m.ov
    middle_x, middle_y = width / 2, (top + bottom) / 2
    inner_top, inner_bottom = XH - m.thin * m.v(1.0, 0.92, black=E_TOP), m.v(*E_ITALIC_FLOOR)
    floor_x = middle_x - m.v(0, 14, light=0, black=36)
    tail_y = m.v(*E_ITALIC_TAIL)
    low, rise = m.v(*E_BAR_LOW), m.v(*E_RISE)
    run = width - 2 * side
    lean = (-run / math.hypot(run, rise), -rise / math.hypot(run, rise))
    lift = thick * math.hypot(run, rise) / run

    def under(x):
        return low + (x - side) * rise / run

    def over(x):
        return under(x) + lift

    left_y = middle_y
    shoulder_y = under(width) + m.v(*E_OUTER_TURN)
    outer_corner = (width - m.v(*E_OUTER_REACH), under(width - m.v(*E_OUTER_REACH)))
    tail_out = reach(quarter((middle_x, bottom), (width, middle_y), "h", m.k_out), 1, tail_y)
    tail_in = levelled(reach(quarter((floor_x, inner_bottom), (width - side * m.v(*E_TAPER), middle_y), "h", m.k_in), 1, tail_y), m.v(*E_LEVEL), m.v(*E_LEVEL_RUN))
    lower = met(quarter((side, left_y), (floor_x, inner_bottom), "v", m.k_in), lambda point: point[1] > under(point[0]))
    path = Path(tail_out[3])
    path.bez(flip(tail_out))
    path.arc((0, middle_y), "h", m.k_out)
    path.arc((middle_x, top), "v", m.k_out)
    path.arc((width, shoulder_y), "h", m.k_out)
    path.bez(bend((width, shoulder_y), DOWN, outer_corner, lean, E_TURN_PULL, E_TURN_PULL))
    path.to(lower[0])
    path.bez(lower)
    path.bez(tail_in)
    eye_y = over(width - side) + m.v(*E_INNER_TURN)
    inner_corner = (width - side - m.v(*E_INNER_REACH), over(width - side - m.v(*E_INNER_REACH)))
    upper = met(quarter((side, left_y), (middle_x, inner_top), "v", m.k_in), lambda point: point[1] > over(point[0]))
    eye = Path(upper[0])
    eye.bez(upper)
    eye.arc((width - side, eye_y), "h", m.k_in)
    eye.bez(bend((width - side, eye_y), DOWN, inner_corner, lean, E_TURN_PULL, E_TURN_PULL))
    return [path.close(smooth=False), eye.close(hole=True, smooth=False)], width


def italic_f(m):
    stem = m.stem
    left = m.v(68, 62, light=60)
    thin = m.thin
    top_run = stem + m.v(128, 140, light=118)
    top_width = hook_inner(m)
    top_height = top_width * 1.15
    tail = m.v(*F_TAIL)
    hook_reach = m.v(*F_REACH)
    bottom_width = (hook_reach - J_TIP) / HOOK_SPREAD
    bottom_height = bottom_width * 1.15
    path = Path((0, DESC + tail + bottom_height))
    path.to((0, ASC - thin - top_height * 1.25))
    path.arc((stem + top_width * HOOK_SPREAD, ASC), "v", m.k_out - 0.02)
    path.to((top_run, ASC))
    path.to((top_run, ASC - thin))
    path.to((stem + top_width, ASC - thin))
    path.arc((stem, ASC - thin - top_height), "h", m.k_in + 0.02)
    path.to((stem, DESC + tail + bottom_height * 1.25))
    path.arc((-bottom_width * HOOK_SPREAD, DESC), "v", m.k_out - 0.02)
    path.to((-hook_reach, DESC))
    path.to((-hook_reach, DESC + tail))
    path.to((-bottom_width, DESC + tail))
    path.arc((0, DESC + tail + bottom_height), "h", m.k_in + 0.02)
    stroke = place(path.close(), left, 0)
    crossbar = rect(0, XH - m.bar, left + stem + m.v(104, 112, light=92), XH)
    return spaced(m, [stroke, crossbar], extent([stroke, crossbar]), m.v(18, 12), m.v(8, 4), capital=False)


def italic_y(m):
    width = m.v(440, 510, black=578)
    middle = width / 2
    flat = m.diag * m.v(1.2, 1.1)
    direction = (middle - flat / 2, -XH)
    stroke = across(direction, m.diag)
    slope = direction[0] / XH
    heading = (-direction[0] / math.hypot(*direction), direction[1] / math.hypot(*direction))
    straight_y = m.v(*Y_STRAIGHT)
    thick = m.v(*Y_THICK)
    floor_y = DESC - m.ov + thick / 2
    floor_x = width - stroke / 2 - slope * (XH - floor_y) - m.v(*Y_TURN)
    terminal_x = m.v(*Y_TERMINAL)
    tail = ribbon(
        [
            Node((width - stroke / 2, XH), heading, m.diag, cut="h"),
            Node((width - stroke / 2 - slope * (XH - straight_y), straight_y), heading, m.diag, straight=True),
            Node((floor_x, floor_y), LEFT, thick),
            Node((terminal_x, floor_y + m.v(*Y_TERMINAL_RISE)), aim(Y_SWEEP), thick * m.v(*Y_TERMINAL_WEIGHT), cut="v"),
        ],
        CURSIVE_PULL,
    )
    notch = intersect((stroke, XH), (stroke + direction[0], 0), (middle, 0), (middle, XH))
    join = intersect((0, XH), (direction[0], 0), (width - stroke, XH), (width - stroke - direction[0], 0))
    branch = polygon([(0, XH), (stroke, XH), notch, (join[0] + stroke * 0.6, join[1]), join])
    return spaced(m, [tail, branch], width, "diagonal", "diagonal")


SHOULDER_PEAK = 0.6
SHOULDER_DROP = (44, 40, 46, 36)
SHOULDER_INNER_DROP = (34, 30, 36, 26)
EXIT_KNEE = (190, 220, 184, 240)
EXIT_TURN = (48, -14, 46, -34)
EXIT_REACH = (64, 124, 60, 156)
EXIT_LIFT = (34, 36, 30, 40)
EXIT_ANGLE = (32, 24, 30, 24)
EXIT_TAPER = (0.8, 0.66, 0.82, 0.62)
EXIT_PULL = 0.6
EXIT_KNEE_PULL = (0.6, 0.8, 0.6, 0.8)
EXIT_INNER_PULL = (0.6, 0.6, 0.6, 0.6)
EXIT_SIDE = (-30, -30, -20, -36)
EXIT_DIP = (56, 64, 52, 80)
EXIT_DIP_RISE = (0, 4, 0, 4)
EXIT_KNEE_IN = (131, 194, 104, 243)
RIGHT = (1, 0)
UP = (0, 1)


def italic_arch(m, x, width):
    stem = m.stem
    return arch(
        left_out=x + stem * shoulder_spring(m),
        left_in=x + stem * shoulder_inner(m),
        peak_out=x + width * SHOULDER_PEAK,
        peak_in=x + stem + (width - 2 * stem) * SHOULDER_PEAK,
        right=x + width,
        top=XH + m.arch_ov,
        base=0,
        stem=stem,
        thick=m.v(76, 112, light=54, black=140),
        ry_out=m.v(200, 214) + m.v(*SHOULDER_DROP),
        ry_in=m.v(142, 136) + m.v(*SHOULDER_INNER_DROP),
        k_out=m.k_out,
        k_in=m.k_in,
    )


def exit_stroke(m, rise):
    stem, foot = m.stem, m.thin
    bottom = foot / 2 - m.ov
    heel = (stem + m.v(*EXIT_TURN), -m.ov)
    dip = (stem + m.v(*EXIT_DIP), foot - m.ov + m.v(*EXIT_DIP_RISE))
    lean = aim(m.v(*EXIT_ANGLE))
    back = (-lean[0], -lean[1])
    tip_top, tip_bottom = edges(Node((heel[0] + m.v(*EXIT_REACH), bottom + m.v(*EXIT_LIFT)), lean, foot * m.v(*EXIT_TAPER)))
    knee_in, knee_out = (stem, m.v(*EXIT_KNEE_IN)), (0, m.v(*EXIT_KNEE))
    inner_pull = m.v(*EXIT_INNER_PULL)
    path = Path((stem, rise)).to(knee_in)
    path.bez(bend(knee_in, DOWN, dip, RIGHT, inner_pull, inner_pull))
    path.bez(bend(dip, RIGHT, tip_top, lean, EXIT_PULL, EXIT_PULL))
    path.to(tip_bottom)
    path.bez(bend(tip_bottom, back, heel, LEFT, EXIT_PULL, EXIT_PULL))
    path.bez(bend(heel, LEFT, knee_out, UP, EXIT_PULL, m.v(*EXIT_KNEE_PULL)))
    path.to((0, rise))
    return path.close()


def exit_stem(m, x, rise):
    return place(exit_stroke(m, rise), x, 0)


def exit_run(m):
    return extent([exit_stroke(m, XH)])


def italic_n(m):
    width = m.v(450, 520)
    return spaced(m, [rect(0, 0, m.stem, XH), italic_arch(m, 0, width)], width, "straight", m.v(66, 50))


def italic_h(m):
    width = m.v(450, 520)
    return spaced(m, [rect(0, 0, m.stem, ASC), italic_arch(m, 0, width)], width, "straight", m.v(66, 50))


def italic_m(m):
    stem = m.stem
    span = m.v(418, 496)
    shapes = [rect(0, 0, stem, XH), italic_arch(m, 0, span), italic_arch(m, span - stem, span)]
    return spaced(m, shapes, span * 2 - stem, "straight", m.v(66, 50))


def italic_u_parts(m):
    width = m.v(450, 520)
    return turn([italic_arch(m, 0, width)], width / 2, XH / 2), width


def italic_u(m):
    bowl, width = italic_u_parts(m)
    post = exit_stem(m, width - m.stem, XH)
    return spaced(m, bowl + [post], width - m.stem + exit_run(m), m.v(66, 50), m.v(*EXIT_SIDE))


def italic_u_upright_post(m):
    bowl, width = italic_u_parts(m)
    return spaced(m, bowl + [rect(width - m.stem, 0, width, XH)], width, m.v(66, 50), "straight")


def italic_d(m):
    width = m.v(472, 540, black=596)
    shapes = [exit_stem(m, width - m.stem, ASC)] + mirror(bowl(m, width), width / 2)
    return spaced(m, shapes, width - m.stem + exit_run(m), "round", m.v(*EXIT_SIDE))


def italic_a(m):
    width = m.v(472, 540, black=596)
    shapes = [exit_stem(m, width - m.stem, XH)] + mirror(bowl(m, width), width / 2)
    return spaced(m, shapes, width - m.stem + exit_run(m), "round", m.v(*EXIT_SIDE))


AE_JOIN = (4, 4, 3, 6)


def italic_a_plain(m):
    width = m.v(472, 540, black=596)
    shapes = [rect(width - m.stem, 0, width, XH)] + mirror(bowl(m, width), width / 2)
    return spaced(m, shapes, width, "round", "straight")


def italic_ae(m):
    width = m.v(472, 540)
    join = width - m.stem + m.v(*AE_JOIN)
    eye, eye_width = italic_e_shapes(m)
    shapes = [rect(width - m.stem, 0, width, XH)] + mirror(bowl(m, width), width / 2) + [contour.map(lambda point: (point[0] + join, point[1])) for contour in eye]
    return spaced(m, shapes, join + eye_width, "round", m.v(30, 22))


KAY_LEG_FOOT = (34, 30, 36, 26)
KAY_PULL = 0.62
KAY_KNEE = (0.62, 0.6, 0.62, 0.52)
KAY_LEG_WEIGHT = 0.92
BOW = 8
BOW_PULL = 0.55
X_BOW = -7
Z_BOW = 6
Z_FIT = 48
Z_WEIGHT = (1.0, 1.04, 1.0, 1.07)


def curved_kay(m, width, branch, rise):
    stem = m.stem
    arm = m.diag * m.v(0.96, 0.92)
    tip = (width - arm * 0.62, XH)
    join = (stem * 0.55, branch + arm * 0.3)
    chord = math.degrees(math.atan2(join[1] - tip[1], join[0] - tip[0]))
    top, low = aim(chord + BOW), aim(chord - BOW)
    arm_stroke = ribbon([Node(tip, top, arm, cut="h"), Node(join, low, arm)], KAY_PULL)
    foot = (width - m.v(*KAY_LEG_FOOT), 0)
    start = split(bend(tip, top, join, low, KAY_PULL, KAY_PULL), m.v(*KAY_KNEE))[0][3]
    heading = (foot[0] - start[0], foot[1] - start[1])
    leg_weight = m.diag * m.v(1, 1, black=KAY_LEG_WEIGHT)
    leg = ribbon([Node(start, heading, leg_weight), Node((foot[0] - leg_weight * 0.5, 0), heading, leg_weight, straight=True, cut="h")], KAY_PULL)
    return [rect(0, 0, stem, rise), arm_stroke, leg]


def italic_k(m):
    width = m.v(446, 536)
    return spaced(m, curved_kay(m, width, m.v(196, 160), ASC), width, "straight", "diagonal")


def italic_kra(m):
    width = m.v(446, 536)
    return spaced(m, curved_kay(m, width, m.v(196, 160), XH), width, "straight", "diagonal")


def bowed(start, end, bow):
    angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))
    return bend(start, aim(angle + bow), end, aim(angle - bow), BOW_PULL, BOW_PULL)


def shifted_leg(a, b, distance):
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    normal = (-(b[1] - a[1]) / length * distance, (b[0] - a[0]) / length * distance)
    return (a[0] + normal[0], a[1] + normal[1]), (b[0] + normal[0], b[1] + normal[1])


def parallel(bezier, distance, start_y, end_y):
    legs = [shifted_leg(bezier[index], bezier[index + 1], distance) for index in range(3)]
    return (
        intersect(*legs[0], (0, start_y), (1, start_y)),
        intersect(*legs[0], *legs[1]),
        intersect(*legs[1], *legs[2]),
        intersect(*legs[2], (0, end_y), (1, end_y)),
    )


def crossing(bezier, origin, direction):
    def side(point):
        return (point[0] - origin[0]) * direction[1] - (point[1] - origin[1]) * direction[0] > 0

    low, high = 0.0, 1.0
    for _ in range(48):
        middle = (low + high) / 2
        if side(split(bezier, middle)[0][3]) == side(bezier[0]):
            low = middle
        else:
            high = middle
    return split(bezier, (low + high) / 2)[0]


def bowed_arm(m, path, notch_line, top_out, bottom_out, bow):
    outer = bowed(top_out, bottom_out, bow)
    inner = crossing(parallel(outer, -m.diag, top_out[1], bottom_out[1]), *notch_line)
    path.to(inner[3])
    path.bez(flip(inner))
    path.to(top_out)
    path.bez(outer)


def italic_v(m):
    width = m.v(440, 510, black=578)
    height = XH
    flat = m.diag * m.v(1.2, 1.1)
    middle = width / 2
    direction = (middle - flat / 2, -height)
    stroke = across(direction, m.diag)
    path = Path((0, height))
    path.to((stroke, height))
    bowed_arm(m, path, ((stroke, height), direction), (width, height), (middle + flat / 2, 0), BOW)
    path.to((middle - flat / 2, 0))
    return spaced(m, [path.close()], width, "diagonal", "diagonal")


def italic_w(m):
    span = m.v(372, 452, black=514)
    height = XH
    flat = m.diag * m.v(1.15, 1.05)
    middle = span / 2
    direction = (middle - flat / 2, -height)
    stroke = across(direction, m.diag)
    step = span - stroke
    notch = intersect((stroke, height), (stroke + direction[0], 0), (middle, 0), (middle, height))
    first_foot = (middle + flat / 2, 0)
    second_foot = (step + middle - flat / 2, 0)
    crotch = intersect((span, height), first_foot, (step, height), second_foot)
    path = Path((0, height))
    path.to((stroke, height))
    path.to(notch)
    path.to((step, height))
    path.to((span, height))
    bowed_arm(m, path, ((span, height), direction), (step + span, height), (step + middle + flat / 2, 0), BOW)
    path.to(second_foot)
    path.to(crotch)
    path.to(first_foot)
    path.to((middle - flat / 2, 0))
    return spaced(m, [path.close()], span * 2 - stroke, "diagonal", "diagonal")


def italic_x(m):
    width = m.v(432, 504, black=570)
    stroke = band_width(width, XH, m.diag)
    left = bowed((0, XH), (width - stroke, 0), X_BOW)
    right = parallel(left, m.diag, XH, 0)
    back = Path((0, XH))
    back.to(right[0])
    back.bez(right)
    back.to(left[3])
    back.bez(flip(left))
    shapes = [back.close(), band((width - stroke, XH), (0, 0), stroke)]
    return spaced(m, shapes, width, "diagonal", "diagonal")


def italic_z(m):
    width = m.v(404, 474, black=546)
    height, bar = XH, m.bar
    thickness = m.diag * m.v(1.0, 0.96) * m.v(*Z_WEIGHT)
    low, high = 0.0, width
    for _ in range(Z_FIT):
        end = (low + high) / 2
        upper = bowed((width, height - bar), (end, bar), Z_BOW)
        lower = parallel(upper, -thickness, height - bar, bar)
        if lower[3][0] < 0:
            low = end
        else:
            high = end
    lower = (lower[0], lower[1], lower[2], (0, bar))
    path = Path((0, height))
    path.to((width, height))
    path.to(upper[0])
    path.bez(upper)
    path.to((width, bar))
    path.to((width, 0))
    path.to((0, 0))
    path.to(lower[3])
    path.bez(flip(lower))
    path.to((0, height - bar))
    return spaced(m, [path.close()], width, m.v(34, 26), m.v(34, 26), capital=False)


letter_a = ItalicForm(letter_a, italic_a)
letter_d = ItalicForm(letter_d, italic_d)
letter_e = ItalicForm(letter_e, italic_e)
letter_f = ItalicForm(letter_f, italic_f)
letter_h = ItalicForm(letter_h, italic_h)
letter_m = ItalicForm(letter_m, italic_m)
letter_n = ItalicForm(letter_n, italic_n)
letter_u = ItalicForm(letter_u, italic_u)
letter_y = ItalicForm(letter_y, italic_y)
letter_k = ItalicForm(letter_k, italic_k)
letter_v = ItalicForm(letter_v, italic_v)
letter_w = ItalicForm(letter_w, italic_w)
letter_x = ItalicForm(letter_x, italic_x)
letter_z = ItalicForm(letter_z, italic_z)
