from dataclasses import dataclass

from .geometry import Path, across, flip, head, intersect, quarter
from .shapes import Node, aim, polygon, rect, ribbon, shift

LEFT = (-1, 0)
RIGHT = (1, 0)
DOWN = (0, -1)
HOOK_SPREAD = 1.15
SPINE_PULL = 0.75
SHOULDER_SPRING = (0.30, 0.6, 0.25, 0.74)
SHOULDER_INNER = (0.62, 0.66, None, 0.80)


@dataclass
class Glyph:
    contours: list
    advance: float


CAPITAL_SIDES = {"cap", "cap_round", "cap_diagonal"}
SMALL_SIDES = {"straight", "round", "diagonal"}


def shoulder_spring(m):
    return m.v(*SHOULDER_SPRING)


def shoulder_inner(m):
    return m.v(*SHOULDER_INNER)


def opening(m, capital):
    if capital:
        return m.v(22, 20, light=24, black=14)
    return m.v(10, 9, light=11, black=8)


def letter_opening(m, left, right, capital):
    if capital is None:
        named = {left, right} & (CAPITAL_SIDES | SMALL_SIDES)
        if not named:
            return 0
        capital = bool(named & CAPITAL_SIDES)
    return opening(m, capital)


def spaced(m, contours, width, left, right, capital=None):
    extra = m.track + letter_opening(m, left, right, capital)
    lsb = m.bearing(left) + extra
    return Glyph(shift(contours, lsb), lsb + width + m.bearing(right) + extra)


def band(top, bottom, width):
    return polygon([top, (top[0] + width, top[1]), (bottom[0] + width, bottom[1]), bottom])


def band_width(span, height, thickness):
    width = thickness
    for _ in range(8):
        width = across((span - width, height), thickness)
    return width


def vee(width, flat, height, thickness, deepen=0):
    middle = width / 2
    direction = (middle - flat / 2, -height)
    stroke = across(direction, thickness)
    notch = intersect((stroke, height), (stroke + direction[0], 0), (middle, 0), (middle, height))
    notch = (notch[0], notch[1] - deepen)
    points = [
        (0, height),
        (stroke, height),
        notch,
        (width - stroke, height),
        (width, height),
        (middle + flat / 2, 0),
        (middle - flat / 2, 0),
    ]
    return polygon(points), stroke


def double_vee(span, flat, height, thickness):
    middle = span / 2
    direction = (middle - flat / 2, -height)
    stroke = across(direction, thickness)
    step = span - stroke
    notch = intersect((stroke, height), (stroke + direction[0], 0), (middle, 0), (middle, height))
    second_notch = (notch[0] + step, notch[1])
    first_foot = (middle + flat / 2, 0)
    second_foot = (step + middle - flat / 2, 0)
    crotch = intersect((span, height), first_foot, (step, height), second_foot)
    points = [
        (0, height),
        (stroke, height),
        notch,
        (step, height),
        (span, height),
        second_notch,
        (step + span - stroke, height),
        (step + span, height),
        (step + middle + flat / 2, 0),
        second_foot,
        crotch,
        first_foot,
        (middle - flat / 2, 0),
    ]
    return polygon(points), stroke


def zed(width, height, bar, thickness):
    stroke = band_width(width, height - 2 * bar, thickness)
    points = [
        (0, height),
        (width, height),
        (width, height - bar),
        (stroke, bar),
        (width, bar),
        (width, 0),
        (0, 0),
        (0, bar),
        (width - stroke, height - bar),
        (0, height - bar),
    ]
    return polygon(points)


def kay(m, stem, width, height, ascent, branch, inset, thickness, lift=0):
    cut = stem / 2
    low0, low1 = (stem, branch), (width - inset, height)
    direction = (low1[0] - low0[0], low1[1] - low0[1])
    slope = direction[1] / direction[0]
    stroke = across(direction, thickness * m.v(0.98, 0.94))
    high1 = (low1[0] - stroke, height)
    low_cut = (cut, low0[1] + (cut - stem) * slope)
    high_cut = (cut, height + (cut - high1[0]) * slope)
    upper = polygon([(cut, low_cut[1] + lift), high_cut, high1, low1])
    centre0 = (cut, (low_cut[1] + high_cut[1]) / 2)
    centre1 = ((low1[0] + high1[0]) / 2, height)
    knee_x = stem + direction[0] * m.v(0.42, 0.44)
    knee = (knee_x, centre0[1] + (knee_x - cut) * slope)
    leg_direction = (knee[0] - width, knee[1])
    leg_stroke = across(leg_direction, thickness * m.v(1.04, 1.02))
    foot = (width - leg_stroke, 0)
    crotch = intersect(foot, (foot[0] + leg_direction[0], leg_direction[1]), centre0, centre1)
    lower = polygon([foot, crotch, knee, (width, 0)])
    return [rect(0, 0, stem, ascent), upper, lower]


def ess(m, width, height, side, flat, spine, inset, upper_y, lower_y, angle, t, pull=None, shoulder=None, tilt=0, tip=0.9):
    top, bottom = height + m.ov, -m.ov
    tip = side * tip
    lift = aim(110)
    shoulder = height * (m.v(0.25, 0.26, black=0.3) if shoulder is None else shoulder)
    upper = [
        Node((width - inset - tip / 2, upper_y), lift, tip, cut="h"),
        Node((width / 2 + side * 0.05, top - flat / 2), LEFT, flat),
        Node((inset + side / 2, height - shoulder), aim(tilt - 90), side, leave=m.v(0.9, 0.8)),
    ]
    lower = [
        Node((width - inset - side / 2, shoulder), aim(tilt - 90), side, arrive=m.v(0.9, 0.8)),
        Node((width / 2 - side * 0.05, bottom + flat / 2), LEFT, flat),
        Node((inset + tip / 2, lower_y), lift, tip, cut="h"),
    ]
    pull = m.v(0.6, 0.6, black=SPINE_PULL) if pull is None else pull
    middle = Node((width / 2, height / 2), aim(-angle - m.v(2, -6)), spine, arrive=pull, leave=pull)
    return ribbon(upper + [middle] + lower, 0.62, smooth=False)


def hook(m, stem, thin, rise, run, inner):
    return shaped_hook(m, stem, thin, rise, run, inner, inner * 1.15)


def shaped_hook(m, stem, thin, rise, run, inner_width, inner_height):
    outer_x = stem + inner_width * HOOK_SPREAD
    outer_y = thin + inner_height * 1.25
    path = Path((0, rise))
    path.to((0, outer_y))
    path.arc((outer_x, 0), "v", m.k_out - 0.02)
    path.to((run, 0))
    path.to((run, thin))
    path.to((stem + inner_width, thin))
    path.arc((stem, thin + inner_height), "h", m.k_in + 0.02)
    path.to((stem, rise))
    return path.close()


def reach(bezier, axis, value):
    rising = bezier[3][axis] > bezier[0][axis]
    low, high = 0.0, 1.0
    for _ in range(40):
        middle = (low + high) / 2
        if (head(bezier, middle)[3][axis] < value) == rising:
            low = middle
        else:
            high = middle
    return head(bezier, (low + high) / 2)


def open_bowl(outer, inner, k_out, k_in, top_y, bottom_y):
    ox0, oy0, ox1, oy1 = outer
    ix0, iy0, ix1, iy1 = inner
    ocx, ocy = (ox0 + ox1) / 2, (oy0 + oy1) / 2
    icx, icy = (ix0 + ix1) / 2, (iy0 + iy1) / 2
    top_out = reach(quarter((ocx, oy1), (ox1, ocy), "h", k_out), 1, top_y)
    top_in = reach(quarter((icx, iy1), (ix1, icy), "h", k_in), 1, top_y)
    bottom_out = reach(quarter((ocx, oy0), (ox1, ocy), "h", k_out), 1, bottom_y)
    bottom_in = reach(quarter((icx, iy0), (ix1, icy), "h", k_in), 1, bottom_y)
    path = Path(top_out[3])
    path.bez(flip(top_out))
    path.arc((ox0, ocy), "h", k_out)
    path.arc((ocx, oy0), "v", k_out)
    path.bez(bottom_out)
    path.to(bottom_in[3])
    path.bez(flip(bottom_in))
    path.arc((ix0, icy), "h", k_in)
    path.arc((icx, iy1), "v", k_in)
    path.bez(top_in)
    return path.close()


def lobe(m, left_out, left_in, right, top, bottom, bar, side, rx=None):
    radius = (top - bottom) / 2
    middle = (top + bottom) / 2
    rx = radius if rx is None else rx
    inner_rx = max(rx - side * m.v(0.9, 0.92, black=0.8), side * 0.15)
    outer = Path((left_out, top))
    outer.to((right - rx, top))
    outer.arc((right, middle), "h", m.k_out)
    outer.arc((right - rx, bottom), "v", m.k_out)
    outer.to((left_out, bottom))
    inner = Path((left_in, top - bar))
    inner.to((right - side - inner_rx, top - bar))
    inner.arc((right - side, middle), "h", m.k_in)
    inner.arc((right - side - inner_rx, bottom + bar), "v", m.k_in)
    inner.to((left_in, bottom + bar))
    return [outer.close(), inner.close(hole=True)]
