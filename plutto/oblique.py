import math
from dataclasses import dataclass, replace
from functools import lru_cache

import numpy

from .geometry import Contour, closed_segments, head
from .masters import ARCH_OV, ASC, CAP, CAP_OV, DESC, DRAWN_HEIGHTS, OV, XH, default_of, family, line_heights
from .parts import Glyph

ORIGIN = XH / 2
HEIGHTS = DRAWN_HEIGHTS
CURVE_STEPS = 16
STEPS = (numpy.arange(CURVE_STEPS) / CURVE_STEPS)[None, :, None]
RAY_START = 0.5
SIDE_STEP = 1.0
PROBE_OUT = 0.5
PROBE_ALONG = 3.0
PROBE = (math.cos(0.6158), math.sin(0.6158))
SMALLEST_SEGMENT = 4.0
LINE_SHARES = (0.25, 0.5, 0.75)
PARALLEL = 0.2
CORNER_REACH = 2.0
THICKEST = 1.6
STEADY = (0.8, 1.25)
FACING = math.cos(math.radians(35))
HANDLE_RANGE = 0.25
STRETCH_SHARES = (1.0, 0.5, 0.25, 0.0)
SMALLEST_LEVER = 1.0
SHORTEST_HANDLE = 3.0
ROUNDS = 2
MEETING_DIGITS = 3
NEIGHBOUR_GAP = 24.0
LEVEL = 1e-3
SMOOTH = math.radians(2)
ON_LINE = 1e-6
FAN = tuple(math.radians(angle) for angle in (-12, 0, 12))
BOWL_CORRECTION = (1.0, 1.0, 1.0, 0.55)
TURN = (0.6, 0.6, 0.5, 0.45)
ROUND_NARROWING = (1.0, 0.7, 1.0, 0.4)
ROUND_THIN = (0.0, 0.02, 0.0, 0.065)
ROUND_CURVES = 4
ROUND_LINE = 1.3
ROUND_LEAD = 3.0
ROUND_SHAPE = 0.45
ROUND_HEIGHT = XH / 2
SHALLOW_CROSSING = math.sin(math.radians(20))
FIT_ROUNDS = 4
FIT_CLOSE = 0.01


def sheared(point, slope):
    return (point[0] + slope * (point[1] - ORIGIN), point[1])


def transformed(point, slope, width):
    return (width * point[0] + slope * (point[1] - ORIGIN), point[1])


def narrowed_x(point, slope, width):
    return width * (point[0] - slope * (point[1] - ORIGIN)) + slope * (point[1] - ORIGIN)


def widened_x(point, slope, width):
    return (point[0] - slope * (point[1] - ORIGIN)) / width + slope * (point[1] - ORIGIN)


@dataclass(frozen=True)
class ItalicForm:
    roman: object
    italic: object

    def __call__(self, master):
        return (self.italic if master.italic else self.roman)(master)


@dataclass(frozen=True)
class Overlaid:
    base: object
    overlay: object

    def __call__(self, master):
        glyph = self.base(master)
        return Glyph(glyph.contours + self.overlay(master, glyph, glyph), glyph.advance)


def unit(vector):
    length = math.hypot(vector[0], vector[1])
    if length == 0:
        return None
    return (vector[0] / length, vector[1] / length)


def left_of(direction):
    return (-direction[1], direction[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def plus(a, b, scale=1.0):
    return (a[0] + b[0] * scale, a[1] + b[1] * scale)


def bezier_at(bezier, t):
    return head(bezier, t)[3]


def start_tangent(bezier):
    for point in bezier[1:]:
        direction = unit((point[0] - bezier[0][0], point[1] - bezier[0][1]))
        if direction:
            return direction
    return None


def end_tangent(bezier):
    for point in reversed(bezier[:-1]):
        direction = unit((bezier[3][0] - point[0], bezier[3][1] - point[1]))
        if direction:
            return direction
    return None


def middle_tangent(bezier):
    half = head(bezier, 0.5)
    return unit((half[3][0] - half[2][0], half[3][1] - half[2][1]))


def lerp_all(a, b, t):
    return a + (b - a) * t


def curve_points(beziers):
    p0, p1, p2, p3 = (beziers[:, None, index, :] for index in range(4))
    p01, p12, p23 = lerp_all(p0, p1, STEPS), lerp_all(p1, p2, STEPS), lerp_all(p2, p3, STEPS)
    return lerp_all(lerp_all(p01, p12, STEPS), lerp_all(p12, p23, STEPS), STEPS)


def flattened(contour):
    pieces = []
    curves = []
    here = contour.start
    for segment in closed_segments(contour):
        if len(segment) == 1:
            pieces.append(here)
        else:
            pieces.append(len(curves))
            curves.append((here, *segment))
        here = segment[-1]
    traced = curve_points(numpy.array(curves, dtype=float)).tolist() if curves else []
    points = []
    for piece in pieces:
        if isinstance(piece, int):
            points.extend(map(tuple, traced[piece]))
        else:
            points.append(piece)
    return points


class Ink:
    def __init__(self, contours):
        starts, ends = [], []
        for contour in contours:
            points = flattened(contour)
            starts += points
            ends += points[1:] + points[:1]
        self.starts = numpy.array(starts, dtype=float).reshape(-1, 2)
        self.edges = numpy.array(ends, dtype=float).reshape(-1, 2) - self.starts

    def hits(self, points, directions):
        offsets = self.starts[None, :, :] - points[:, None, :]
        dx, dy = directions[:, None, 0], directions[:, None, 1]
        ex, ey = self.edges[None, :, 0], self.edges[None, :, 1]
        across = dx * ey - dy * ex
        with numpy.errstate(divide="ignore", invalid="ignore"):
            along = (offsets[:, :, 0] * ey - offsets[:, :, 1] * ex) / across
            share = (offsets[:, :, 0] * dy - offsets[:, :, 1] * dx) / across
        hit = (across != 0) & (along > 0) & (share >= 0) & (share < 1)
        return numpy.where(hit, along, numpy.inf), numpy.where(hit, numpy.sign(across), 0)

    def encloses(self, low, high):
        return bool((self.starts.min(axis=0) <= low).all() and (high <= self.starts.max(axis=0)).all())

    def inside(self, points):
        if not len(points):
            return numpy.zeros(0, dtype=bool)
        points = numpy.array(points, dtype=float)
        directions = numpy.tile(PROBE, (len(points), 1))
        _, signs = self.hits(points, directions)
        return signs.sum(axis=1) != 0

    def exits(self, points, directions):
        if not len(points):
            return numpy.zeros(0), numpy.zeros((0, 2))
        points = numpy.array(points, dtype=float)
        directions = numpy.array(directions, dtype=float)
        distances, signs = self.hits(points + directions * RAY_START, directions)
        winding = signs.sum(axis=1)
        order = numpy.argsort(distances, axis=1)
        distances = numpy.take_along_axis(distances, order, axis=1)
        remaining = winding[:, None] - numpy.cumsum(numpy.take_along_axis(signs, order, axis=1), axis=1)
        leaving = (remaining == 0) & numpy.isfinite(distances)
        first = numpy.argmax(leaving, axis=1)
        rows = numpy.arange(len(points))
        found = leaving[rows, first] & (winding != 0)
        edges = self.edges[order[rows, first]]
        lengths = numpy.hypot(edges[:, 0], edges[:, 1])
        lengths[lengths == 0] = 1
        return numpy.where(found, distances[rows, first] + RAY_START, numpy.nan), edges / lengths[:, None]

    def depths(self, points, directions):
        return self.exits(points, directions)[0]


@dataclass
class Sample:
    contour: int
    segment: int
    place: str
    point: tuple
    tangent: tuple
    side: float = 0.0
    thickness: float = math.nan
    facing: float = 0.0
    offset: float = 0.0
    steady: bool = False
    level: bool = False


def segment_bezier(here, segment):
    if len(segment) == 1:
        return None
    return (here, *segment)


def samples_of(contours):
    found = []
    for index, contour in enumerate(contours):
        here = contour.start
        for number, segment in enumerate(closed_segments(contour)):
            bezier = segment_bezier(here, segment)
            if bezier is None:
                tangent = unit((segment[0][0] - here[0], segment[0][1] - here[1]))
                if tangent and math.dist(here, segment[0]) >= SMALLEST_SEGMENT:
                    for share in LINE_SHARES:
                        point = (here[0] + (segment[0][0] - here[0]) * share, here[1] + (segment[0][1] - here[1]) * share)
                        found.append(Sample(index, number, f"line {share}", point, tangent))
            else:
                for place, point, tangent in (
                    ("start", bezier[0], start_tangent(bezier)),
                    ("middle", bezier_at(bezier, 0.5), middle_tangent(bezier)),
                    ("end", bezier[3], end_tangent(bezier)),
                ):
                    if tangent:
                        found.append(Sample(index, number, place, point, tangent))
            here = segment[-1]
    return found


def place_on(contour, number, place):
    segments = closed_segments(contour)
    here = contour.start if number == 0 else segments[number - 1][-1]
    segment = segments[number]
    bezier = segment_bezier(here, segment)
    if bezier is None:
        share = float(place.split()[1])
        point = (here[0] + (segment[0][0] - here[0]) * share, here[1] + (segment[0][1] - here[1]) * share)
        return point, unit((segment[0][0] - here[0], segment[0][1] - here[1]))
    if place == "start":
        return bezier[0], start_tangent(bezier)
    if place == "end":
        return bezier[3], end_tangent(bezier)
    return bezier_at(bezier, 0.5), middle_tangent(bezier)


def samples_like(contours, model, slope, width):
    found = []
    for sample in model:
        point, tangent = place_on(contours[sample.contour], sample.segment, sample.place)
        if tangent is None:
            tangent = unit((width * sample.tangent[0] + slope * sample.tangent[1], sample.tangent[1]))
        found.append(Sample(sample.contour, sample.segment, sample.place, point, tangent, sample.side))
    return found


def strokes_of(contours):
    outers = [index for index, contour in enumerate(contours) if not contour.hole]
    alone = {index: Ink([contours[index]]) for index in outers}
    owner = {index: index for index in outers}
    unowned = False
    for index, contour in enumerate(contours):
        if not contour.hole:
            continue
        outline = flattened(contour)
        low, high = numpy.min(outline, axis=0), numpy.max(outline, axis=0)
        around = [outer for outer in outers if alone[outer].encloses(low, high) and alone[outer].inside(outline).all()]
        if around:
            owner[index] = min(around, key=lambda outer: abs(contours[outer].area()))
        else:
            unowned = True
    groups = {}
    for index, outer in owner.items():
        groups.setdefault(outer, []).append(index)
    found = {}
    for outer, members in groups.items():
        ink = alone[outer] if len(members) == 1 else Ink([contours[member] for member in members])
        for member in members:
            found[member] = ink
    whole = Ink(contours) if unowned else None
    return [found.get(index, whole) for index in range(len(contours))]


def by_stroke(strokes, samples):
    if isinstance(strokes, Ink):
        return [(strokes, samples)]
    groups = {}
    for sample in samples:
        groups.setdefault(id(strokes[sample.contour]), (strokes[sample.contour], []))[1].append(sample)
    return groups.values()


def choose_sides(ink, samples):
    for stroke, group in by_stroke(ink, samples):
        lefts = [plus(sample.point, left_of(sample.tangent), SIDE_STEP) for sample in group]
        rights = [plus(sample.point, left_of(sample.tangent), -SIDE_STEP) for sample in group]
        left_ink, right_ink = stroke.inside(lefts), stroke.inside(rights)
        for sample, on_left, on_right in zip(group, left_ink, right_ink):
            if on_left != on_right:
                sample.side = 1.0 if on_left else -1.0


def inward(sample):
    normal = left_of(sample.tangent)
    side = sample.side or 1.0
    return (normal[0] * side, normal[1] * side)


def turned(direction, angle):
    cosine, sine = math.cos(angle), math.sin(angle)
    return (direction[0] * cosine - direction[1] * sine, direction[0] * sine + direction[1] * cosine)


def fan_of(sample):
    return (0.0,) if sample.place.startswith("line") else FAN


def measure(ink, samples):
    for stroke, group in by_stroke(ink, samples):
        sided = [sample for sample in group if sample.side]
        if not sided:
            continue
        rays = [(row, angle) for row, sample in enumerate(sided) for angle in fan_of(sample)]
        points = [sided[row].point for row, _ in rays]
        directions = [turned(inward(sided[row]), angle) for row, angle in rays]
        depths, edges = stroke.exits(points, directions)
        best = {}
        for (row, angle), depth, edge in zip(rays, depths, edges):
            if math.isnan(depth):
                continue
            facing = abs(dot(sided[row].tangent, edge))
            if angle and facing < FACING:
                continue
            if row not in best or depth < best[row][0]:
                best[row] = (float(depth), facing)
        for row, sample in enumerate(sided):
            sample.thickness, sample.facing = best.get(row, (math.nan, 0.0))


def similar_handles(bezier, slope, width):
    moved = [transformed(point, slope, width) for point in bezier]
    chord = math.dist(bezier[0], bezier[3])
    if chord == 0:
        return tuple(moved)
    ratio = math.dist(moved[0], moved[3]) / chord

    def handle(anchor, original_anchor, point, original_point):
        direction = unit((point[0] - anchor[0], point[1] - anchor[1]))
        if direction is None:
            return point
        return plus(anchor, direction, math.dist(original_anchor, original_point) * ratio)

    return (
        moved[0],
        handle(moved[0], bezier[0], moved[1], bezier[1]),
        handle(moved[3], bezier[3], moved[2], bezier[2]),
        moved[3],
    )


def slanted_contour(contour, slope, width):
    segments = []
    here = contour.start
    for segment in contour.segments:
        bezier = segment_bezier(here, segment)
        if bezier is None:
            segments.append((transformed(segment[0], slope, width),))
        else:
            segments.append(similar_handles(bezier, slope, width)[1:])
        here = segment[-1]
    return Contour(transformed(contour.start, slope, width), segments, contour.hole)


def flat(direction):
    return direction is not None and abs(direction[1]) < LEVEL


def curvy(contour, limit):
    here = contour.start
    curves = 0
    for segment in closed_segments(contour):
        if len(segment) == 3:
            curves += 1
        elif abs(segment[0][1] - here[1]) >= LEVEL and math.dist(here, segment[0]) > limit:
            return False
        here = segment[-1]
    return curves >= ROUND_CURVES


def corner_box(contours):
    points = [point for contour in contours for point in contour.points()]
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def boxes_meet(first, second):
    return first[0] < second[2] and second[0] < first[2] and first[1] < second[3] and second[1] < first[3]


def leading(contours, members):
    box = corner_box([contours[index] for index in members])
    own = abs(sum(contours[index].area() for index in members))
    others = [abs(contour.area()) for index, contour in enumerate(contours) if index not in members and boxes_meet(box, corner_box([contour]))]
    return all(own >= ROUND_LEAD * other for other in others)


def polyline(contour):
    points = numpy.array(flattened(contour), dtype=float)
    return points, numpy.roll(points, -1, axis=0) - points


def crossing_angles(first, second):
    (starts, steps), (others, other_steps) = polyline(first), polyline(second)
    across = steps[:, None, 0] * other_steps[None, :, 1] - steps[:, None, 1] * other_steps[None, :, 0]
    offset = others[None, :, :] - starts[:, None, :]
    with numpy.errstate(divide="ignore", invalid="ignore"):
        share = (offset[..., 0] * other_steps[None, :, 1] - offset[..., 1] * other_steps[None, :, 0]) / across
        other_share = (offset[..., 0] * steps[:, None, 1] - offset[..., 1] * steps[:, None, 0]) / across
    hit = (across != 0) & (share >= 0) & (share < 1) & (other_share >= 0) & (other_share < 1)
    rows, columns = numpy.nonzero(hit)
    lengths = numpy.hypot(*steps[rows].T) * numpy.hypot(*other_steps[columns].T)
    return numpy.abs(across[rows, columns]) / lengths


def crossed_steeply(contours, members):
    for index in members:
        for number, other in enumerate(contours):
            if number not in members and (crossing_angles(contours[index], other) < SHALLOW_CROSSING).any():
                return False
    return True


def broad(contours, members):
    left, bottom, right, top = corner_box([contours[index] for index in members])
    return top - bottom >= ROUND_HEIGHT and right - left >= ROUND_SHAPE * (top - bottom)


def round_groups(contours, strokes, limit):
    groups = {}
    for index, stroke in enumerate(strokes):
        groups.setdefault(id(stroke), []).append(index)
    return [
        members
        for members in groups.values()
        if all(curvy(contours[index], limit) for index in members) and broad(contours, members) and leading(contours, members) and crossed_steeply(contours, members)
    ]


def turning(centre, slope, angle):
    lean = slope - math.tan(angle)
    target = sheared(centre, slope)

    def along(vector):
        x, y = turned(vector, -angle)
        return (x + lean * y, y)

    def place(point):
        return plus(target, along((point[0] - centre[0], point[1] - centre[1])))

    return along, place


def turned_handle(anchor, old_anchor, old_handle, level, along, ratio):
    pull = (old_handle[0] - old_anchor[0], old_handle[1] - old_anchor[1])
    length = math.hypot(*pull)
    if length == 0:
        return anchor
    direction = (math.copysign(1.0, pull[0]), 0.0) if level and flat(unit(pull)) else unit(along(pull))
    return plus(anchor, direction, length * ratio)


def level_places(contours, rows):
    return {
        meeting_key(corner)
        for contour in contours
        for _, corner, arriving, leaving in joins(contour)
        if round(corner[1], MEETING_DIGITS) in rows or flat(arriving) or flat(leaving)
    }


def thinned(corner, hole, rows, middle, gain):
    if not hole or round(corner[1], MEETING_DIGITS) in rows:
        return corner[1]
    return corner[1] - math.copysign(gain, corner[1] - middle)


def turned_contour(contour, along, place, levels, rows, middle, gain):
    segments = closed_segments(contour)
    count = len(segments)
    corners = [contour.start] + [segment[-1] for segment in segments[:-1]]
    level = {number for number, corner in enumerate(corners) if meeting_key(corner) in levels}
    moved = [(place(corner)[0], thinned(corner, contour.hole, rows, middle, gain)) if number in level else place(corner) for number, corner in enumerate(corners)]
    rebuilt = []
    for number, segment in enumerate(segments[: len(contour.segments)]):
        following = (number + 1) % count
        end = moved[following]
        if len(segment) == 1:
            rebuilt.append((end,))
            continue
        start, old_start, old_end = moved[number], corners[number], corners[following]
        chord = math.dist(old_start, old_end)
        ratio = math.dist(start, end) / chord if chord else 1.0
        rebuilt.append(
            (
                turned_handle(start, old_start, segment[0], number in level, along, ratio),
                turned_handle(end, old_end, segment[1], following in level, along, ratio),
                end,
            )
        )
    return Contour(moved[0], rebuilt, contour.hole)


def x_extent(contours):
    xs = [point[0] for contour in contours for point in flattened(contour)]
    return min(xs), max(xs)


def refitted(contours, wanted, slope, centre):
    for _ in range(FIT_ROUNDS):
        low, high = x_extent(contours)
        if abs(low - wanted[0]) < FIT_CLOSE and abs(high - wanted[1]) < FIT_CLOSE:
            break
        scale = (wanted[1] - wanted[0]) / (high - low)
        middle = (low + high) / 2
        goal = (wanted[0] + wanted[1]) / 2

        def moved(point):
            return (goal + scale * (point[0] - middle - slope * (point[1] - centre)) + slope * (point[1] - centre), point[1])

        contours = [contour.map(moved) for contour in contours]
    return contours


def slanted_outline(contours, groups, slope, width, master, rows):
    italic = [slanted_contour(contour, slope, width) for contour in contours]
    if not slope:
        return italic
    angle = math.radians(master.slant) * master.v(*TURN)
    for members in groups:
        group = [contours[index] for index in members]
        points = [point for contour in group for point in flattened(contour)]
        xs, ys = [point[0] for point in points], [point[1] for point in points]
        centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
        along, place = turning(centre, slope, angle)
        levels = level_places(group, rows)
        gain = master.v(*ROUND_THIN) * master.thin
        turned_group = [turned_contour(contour, along, place, levels, rows, centre[1], gain) for contour in group]
        fitted = refitted(turned_group, x_extent([italic[index] for index in members]), slope, centre[1])
        for index, contour in zip(members, fitted):
            italic[index] = contour
    return italic


def bowl_contours(contours, strokes):
    holes = [index for index, contour in enumerate(contours) if contour.hole]
    return {index for index in range(len(contours)) if any(strokes[index] is strokes[hole] for hole in holes)}


def wanted_offsets(roman, italic, limit, bowls, strength, rounds, round_strength):
    for before, after in zip(roman, italic):
        after.side = before.side
        after.level = abs(before.tangent[1]) < LEVEL
        if after.level or not before.side or math.isnan(before.thickness) or math.isnan(after.thickness):
            continue
        if before.thickness > limit or min(before.facing, after.facing) < FACING:
            continue
        ratio = after.thickness / before.thickness
        if STEADY[0] <= ratio <= STEADY[1]:
            curved = not before.place.startswith("line")
            share = round_strength if curved and before.contour in rounds else strength if curved and before.contour in bowls else 1.0
            after.offset = (before.thickness - after.thickness) / 2 * share
            after.steady = True


def outward(sample):
    normal = inward(sample)
    return (-normal[0], -normal[1])


def sideways_shift(pushes):
    weight = sum(normal[0] ** 2 for normal, _ in pushes)
    if weight < LEVEL:
        return (0.0, 0.0)
    x = sum(normal[0] * offset for normal, offset in pushes) / weight
    largest = CORNER_REACH * max(abs(offset) for _, offset in pushes)
    return (max(-largest, min(largest, x)), 0.0)


def corner_shift(incoming, outgoing, locked=False):
    pushes = [(outward(sample), sample.offset) for sample in (incoming, outgoing) if sample is not None]
    if not pushes:
        return (0.0, 0.0)
    if locked:
        return sideways_shift(pushes)
    if len(pushes) == 1:
        normal, offset = pushes[0]
        return (normal[0] * offset, normal[1] * offset)
    (first, a), (second, b) = pushes
    turn = first[0] * second[1] - first[1] * second[0]
    if abs(turn) < PARALLEL:
        middle = unit(plus(first, second)) or first
        average = (a + b) / 2
        return (middle[0] * average, middle[1] * average)
    x = (a * second[1] - b * first[1]) / turn
    y = (first[0] * b - second[0] * a) / turn
    reach = math.hypot(x, y)
    largest = CORNER_REACH * max(abs(a), abs(b))
    if reach > largest:
        x, y = x * largest / reach, y * largest / reach
    return (x, y)


def scaled_handle(anchor, handle, stretch):
    return (anchor[0] + (handle[0] - anchor[0]) * (1 + stretch), anchor[1] + (handle[1] - anchor[1]) * (1 + stretch))


def handle_stretch(middle, start, first, second, end, start_shift, end_shift):
    if middle is None or not middle.side or not middle.offset:
        return 0.0
    normal = outward(middle)
    moved = dot(((start_shift[0] + end_shift[0]) / 2, (start_shift[1] + end_shift[1]) / 2), normal)
    pull = ((first[0] - start[0]) + (second[0] - end[0]), (first[1] - start[1]) + (second[1] - end[1]))
    lever = 0.375 * dot(pull, normal)
    if abs(lever) < SMALLEST_LEVER:
        return 0.0
    return max(-HANDLE_RANGE, min(HANDLE_RANGE, (middle.offset - moved) / lever))


def folded(start, first, second, end):
    chord = (end[0] - start[0], end[1] - start[1])
    return dot((second[0] - start[0], second[1] - start[1]), chord) < 0 or dot((end[0] - first[0], end[1] - first[1]), chord) < 0


def unfolded(start, first, second, end, stretch):
    for share in STRETCH_SHARES:
        handles = (scaled_handle(start, first, stretch * share), scaled_handle(end, second, stretch * share))
        if not folded(start, *handles, end):
            return handles
    return handles


def line_sample(parts):
    steady = [part for part in parts if part.steady]
    offset = sum(part.offset for part in steady) / len(steady) if steady else 0.0
    first = (steady or parts)[0]
    level = all(part.level for part in parts)
    return Sample(first.contour, first.segment, "line", first.point, first.tangent, first.side, offset=offset, steady=bool(steady), level=level)


def pinned(sample):
    return replace(sample, offset=0.0, steady=False)


def adjusted(contours, samples, ink, rows=(), metrics=HEIGHTS):
    by_place = {}
    lines = {}
    for sample in samples:
        if sample.place.startswith("line"):
            lines.setdefault((sample.contour, sample.segment), []).append(sample)
        else:
            by_place[(sample.contour, sample.segment, sample.place)] = sample
    for (index, number), parts in lines.items():
        by_place[(index, number, "line")] = line_sample(parts)

    def sample_at(index, number, place):
        return by_place.get((index, number, place)) or by_place.get((index, number, "line"))

    plans = []
    meetings = []
    meeting_contours = []
    probes = []
    for index, contour in enumerate(contours):
        segments = closed_segments(contour)
        count = len(segments)
        corners = [contour.start] + [segment[-1] for segment in segments[:-1]]
        for number, corner in enumerate(corners):
            incoming = sample_at(index, (number - 1) % count, "end")
            outgoing = sample_at(index, number, "start")
            for sample, sign in ((incoming, -1.0), (outgoing, 1.0)):
                if sample is not None:
                    normal = outward(sample)
                    heading = (sample.tangent[0] * sign, sample.tangent[1] * sign)
                    probes.append(plus(plus(corner, normal, PROBE_OUT), heading, PROBE_ALONG))
            meetings.append((corner, incoming, outgoing))
            meeting_contours.append(index)
        plans.append((contour, segments, corners))
    covered = iter(ink.inside(probes))
    shared = {}
    owners = {}
    levels = set()
    for (corner, incoming, outgoing), index in zip(meetings, meeting_contours):
        if incoming is not None and next(covered):
            incoming = pinned(incoming)
        if outgoing is not None and next(covered):
            outgoing = pinned(outgoing)
        key = meeting_key(corner)
        locked = round(corner[1], MEETING_DIGITS) in rows or any(sample is not None and sample.level for sample in (incoming, outgoing))
        shared.setdefault(key, []).append(corner_shift(incoming, outgoing, locked))
        owners.setdefault(key, set()).add(index)
        if locked:
            levels.add(key)
    averaged = {key: (sum(shift[0] for shift in group) / len(group), sum(shift[1] for shift in group) / len(group)) for key, group in shared.items()}
    keep_gaps(averaged, owners)
    for key in levels:
        averaged[key] = (averaged[key][0], 0.0)
    ride_along(averaged, plans, {round(height, MEETING_DIGITS) for height in metrics})
    result = []
    for index, (contour, segments, corners) in enumerate(plans):
        count = len(segments)
        shifts = [averaged[meeting_key(corner)] for corner in corners]
        moved = [plus(corner, shift) for corner, shift in zip(corners, shifts)]
        rebuilt = []
        for number, segment in enumerate(segments[: len(contour.segments)]):
            start, end = moved[number], moved[(number + 1) % count]
            if len(segment) == 1:
                rebuilt.append((end,))
                continue
            start_shift, end_shift = shifts[number], shifts[(number + 1) % count]
            first, second = plus(segment[0], start_shift), plus(segment[1], end_shift)
            stretch = handle_stretch(sample_at(index, number, "middle"), start, first, second, end, start_shift, end_shift)
            rebuilt.append((*unfolded(start, first, second, end, stretch), end))
        result.append(Contour(moved[0], rebuilt, contour.hole))
    return result


def straight_lines(plans):
    for index, (_, segments, corners) in enumerate(plans):
        for number, segment in enumerate(segments):
            if len(segment) == 1:
                yield index, corners[number], segment[0]


def riding(point, start, end):
    along = (end[0] - start[0], end[1] - start[1])
    length = dot(along, along)
    if length == 0:
        return None
    share = dot((point[0] - start[0], point[1] - start[1]), along) / length
    if not 0 < share < 1:
        return None
    foot = plus(start, along, share)
    return share if math.dist(point, foot) < ON_LINE else None


def level_ride(corner, start, end, shift):
    rise = end[1] - start[1]
    if abs(rise) < ON_LINE:
        return (shift[0], 0.0)
    share = (corner[1] - start[1]) / rise
    return (start[0] + (end[0] - start[0]) * share - corner[0], 0.0)


def ride_along(shifts, plans, levels):
    lines = list(straight_lines(plans))
    moved = {}
    for index, (_, _, corners) in enumerate(plans):
        for corner in corners:
            for owner, start, end in lines:
                if owner == index:
                    continue
                share = riding(corner, start, end)
                if share is None:
                    continue
                first, last = shifts[meeting_key(start)], shifts[meeting_key(end)]
                shift = plus(first, (last[0] - first[0], last[1] - first[1]), share)
                if round(corner[1], MEETING_DIGITS) in levels:
                    shift = level_ride(corner, plus(start, first), plus(end, last), shift)
                moved[meeting_key(corner)] = shift
                break
    shifts.update(moved)


def keep_gaps(shifts, owners):
    rows = {}
    for key in shifts:
        rows.setdefault(key[1], []).append(key)
    for row in rows.values():
        row.sort()
        group = [row[0]]
        for key in row[1:] + [None]:
            if key is not None and owners[key] != owners[group[-1]] and key[0] - group[-1][0] < NEIGHBOUR_GAP:
                group.append(key)
                continue
            if len(group) > 1:
                along = sum(shifts[member][0] for member in group) / len(group)
                for member in group:
                    shifts[member] = (along, shifts[member][1])
            group = [key]


def turn_between(incoming, outgoing):
    return abs(math.atan2(incoming[0] * outgoing[1] - incoming[1] * outgoing[0], dot(incoming, outgoing)))


def joins(contour):
    segments = closed_segments(contour)
    corners = [contour.start] + [segment[-1] for segment in segments[:-1]]
    for number, corner in enumerate(corners):
        before = segments[number - 1]
        after = segments[number]
        previous = corners[number - 1]
        following = after[-1] if len(after) == 1 else after[0]
        arriving = before[1] if len(before) == 3 else previous
        yield number, corner, unit((corner[0] - arriving[0], corner[1] - arriving[1])), unit((following[0] - corner[0], following[1] - corner[1]))


def smoothed(roman, italic):
    segments = closed_segments(italic)
    smooth = [
        number
        for number, _, arriving, leaving in joins(roman)
        if arriving and leaving and turn_between(arriving, leaving) < SMOOTH
    ]
    for number, corner, arriving, leaving in joins(italic):
        if number not in smooth or not arriving or not leaving:
            continue
        before, after = segments[number - 1], segments[number]
        arriving_length = math.dist(before[1], corner) if len(before) == 3 else math.inf
        leaving_length = math.dist(corner, after[0]) if len(after) == 3 else math.inf
        if arriving_length == leaving_length:
            continue
        if arriving_length < leaving_length:
            segments[number - 1] = (before[0], plus(corner, leaving, -arriving_length), before[2])
        else:
            segments[number] = (plus(corner, arriving, leaving_length), after[1], after[2])
    return Contour(italic.start, segments[: len(italic.segments)], italic.hole)


def lengthened(anchor, handle):
    length = math.dist(anchor, handle)
    if length == 0 or length >= SHORTEST_HANDLE:
        return handle
    return plus(anchor, unit((handle[0] - anchor[0], handle[1] - anchor[1])), SHORTEST_HANDLE)


def kept_apart(contour):
    segments = []
    here = contour.start
    for segment in contour.segments:
        if len(segment) == 3:
            segment = (lengthened(here, segment[0]), lengthened(segment[2], segment[1]), segment[2])
        segments.append(segment)
        here = segment[-1]
    return Contour(contour.start, segments, contour.hole)


def meeting_key(point):
    return (round(point[0], MEETING_DIGITS), round(point[1], MEETING_DIGITS))


def corrected(roman, master, slope, width, strength, round_strength, groups):
    roman_samples = samples_of(roman)
    roman_strokes = strokes_of(roman)
    choose_sides(roman_strokes, roman_samples)
    measure(roman_strokes, roman_samples)
    limit = THICKEST * master.cap_round
    bowls = bowl_contours(roman, roman_strokes)
    heights = [point[1] for contour in roman for point in contour.corners()]
    metrics = line_heights(master)
    rows = {round(height, MEETING_DIGITS) for height in (*metrics, min(heights), max(heights))}
    rounds = {index for members in groups for index in members}
    italic = slanted_outline(roman, groups, slope, width, master, rows)
    for _ in range(ROUNDS):
        italic_samples = samples_like(italic, roman_samples, slope, width)
        ink = Ink(italic)
        measure(strokes_of(italic), italic_samples)
        wanted_offsets(roman_samples, italic_samples, limit, bowls, strength, rounds, round_strength)
        italic = adjusted(italic, italic_samples, ink, rows, metrics)
    return [kept_apart(smoothed(before, after)) for before, after in zip(roman, italic)]


def round_plan(draw, master):
    return planned(draw, default_of(family(master)))


@lru_cache(maxsize=None)
def planned(draw, reference):
    outline = [contour.oriented() for contour in draw(reference).contours]
    return round_groups(outline, strokes_of(outline), ROUND_LINE * reference.thin)


def italicized(glyph, master, groups=()):
    slope, width = master.slope, master.narrowing
    if not slope and width == 1 or not glyph.contours:
        return glyph
    outline = [contour.oriented() for contour in glyph.contours]
    strength = master.v(*BOWL_CORRECTION)
    if width != 1:
        outline = corrected(outline, master, 0.0, width, strength, master.v(*ROUND_NARROWING), groups)
    if slope:
        outline = corrected(outline, master, slope, 1.0, strength, 1.0, groups)
    return Glyph([contour.map(lambda point: (widened_x(point, slope, width), point[1])) for contour in outline], glyph.advance)


def stood(glyph, master):
    slope = master.slope
    if not slope or not glyph.contours:
        return glyph
    heights = [point[1] for contour in glyph.contours for point in contour.points()]
    lift = slope * ((min(heights) + max(heights)) / 2 - ORIGIN)
    return Glyph([contour.map(lambda point: (point[0] + lift, point[1])) for contour in glyph.contours], glyph.advance)


def ink_bounds(glyph):
    points = [point for contour in glyph.contours for point in flattened(contour)]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


@lru_cache(maxsize=None)
def slanted(draw, master, upright=False):
    if isinstance(draw, Overlaid) and master.slope and not upright:
        drawn = slanted(draw.base, master)
        return Glyph(drawn.contours + draw.overlay(master, draw.base(master), drawn), drawn.advance)
    glyph = draw(master)
    if upright:
        return stood(glyph, master)
    return italicized(glyph, master, round_plan(draw, master) if glyph.contours and master.slope else ())


def narrowed(glyph, master, upright=False):
    slope, width = master.slope, master.narrowing
    if width == 1:
        return glyph
    if upright and glyph.contours:
        points = [point for contour in glyph.contours for point in contour.points()]
        xs, ys = [point[0] for point in points], [point[1] for point in points]
        centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
        move = narrowed_x(centre, slope, width) - centre[0]
        return Glyph([contour.map(lambda point: (point[0] + move, point[1])) for contour in glyph.contours], glyph.advance * width)
    return Glyph([contour.map(lambda point: (narrowed_x(point, slope, width), point[1])) for contour in glyph.contours], glyph.advance * width)


@lru_cache(maxsize=None)
def finished(draw, master, upright=False):
    return narrowed(slanted(draw, master, upright), master, upright)
