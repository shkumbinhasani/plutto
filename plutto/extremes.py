import math

import numpy
from fontTools.misc.roundTools import otRound

from .geometry import Contour, lerp, split
from .oblique import HEIGHTS

SPLIT_DEPTH = 0.5
SHORTEST_PIECE = 4.0
SHORTEST_HANDLE = 1.0
SMOOTH_JOIN = math.sin(math.radians(1))
AXIS_TANGENT = math.sin(math.radians(1))
MERGE_ERROR = 0.5
TIGHT_ERROR = 1.0
TIGHT_PIECE = 16.0
KEPT_HEIGHTS = {float(height) for height in HEIGHTS}
FIT_SAMPLES = 24
FIT_ROUNDS = 8
ROOT_EDGE = 1e-6
CLUSTER_SPAN = 0.2
FREE_SHARES = tuple(step / 8 for step in range(9))
TT_TOLERANCE = 1.0
SEARCH_REACH = 4
SEARCH_STEP = 0.1
SEARCH_FINEST = 0.05


def bezier_at(bezier, t):
    mt = 1 - t
    a, b, c, d = mt * mt * mt, 3 * mt * mt * t, 3 * mt * t * t, t * t * t
    return tuple(a * bezier[0][axis] + b * bezier[1][axis] + c * bezier[2][axis] + d * bezier[3][axis] for axis in (0, 1))


def stationary(bezier, axis):
    a, b, c, d = (point[axis] for point in bezier)
    qa = -a + 3 * b - 3 * c + d
    qb = 2 * (a - 2 * b + c)
    qc = b - a
    if abs(qa) < 1e-12:
        roots = [] if abs(qb) < 1e-12 else [-qc / qb]
    else:
        discriminant = qb * qb - 4 * qa * qc
        if discriminant < 0:
            return []
        root = math.sqrt(discriminant)
        roots = [(-qb - root) / (2 * qa), (-qb + root) / (2 * qa)]
    return sorted(t for t in roots if ROOT_EDGE < t < 1 - ROOT_EDGE)


def depth(bezier, axis, t):
    value = bezier_at(bezier, t)[axis]
    return min(abs(value - bezier[0][axis]), abs(value - bezier[3][axis]))


def unit(vector):
    length = math.hypot(vector[0], vector[1])
    if length < 1e-9:
        return None
    return (vector[0] / length, vector[1] / length)


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def root_clusters(beziers, axis):
    roots = [stationary(bezier, axis) for bezier in beziers]
    if len({len(found) for found in roots}) == 1:
        clusters = [{master: found[number] for master, found in enumerate(roots)} for number in range(len(roots[0]))]
    elif max(len(found) for found in roots) == 1:
        clusters = [{master: found[0] for master, found in enumerate(roots) if found}]
    else:
        clusters = []
        for t, master in sorted((t, master) for master, found in enumerate(roots) for t in found):
            cluster = clusters[-1] if clusters else None
            if cluster is not None and master not in cluster and t - min(cluster.values()) < CLUSTER_SPAN:
                cluster[master] = t
            else:
                clusters.append({master: t})
    return [cluster for cluster in clusters if any(depth(beziers[master], axis, t) > SPLIT_DEPTH for master, t in cluster.items())]


def extreme_cuts(beziers):
    cuts = []
    for axis in (0, 1):
        for cluster in root_clusters(beziers, axis):
            cluster = {master: t for master, t in cluster.items() if depth(beziers[master], axis, t) > SPLIT_DEPTH or roomy(beziers[master], t)}
            shared = sum(cluster.values()) / len(cluster)
            ts = [cluster[master] if master in cluster else free_place(bezier, shared) for master, bezier in enumerate(beziers)]
            deepest = max(depth(beziers[master], axis, t) for master, t in cluster.items())
            cuts.append((deepest, axis, ts, set(cluster)))
    cuts.sort(key=lambda cut: -cut[0])
    chosen = []
    for cut in cuts:
        trial = sorted(chosen + [cut], key=lambda item: item[2][0])
        if all(cuts_fit(bezier, [item[2][master] for item in trial]) for master, bezier in enumerate(beziers)) and steady(beziers, [item[2] for item in trial]):
            chosen = trial
    return [(axis, ts, real) for _, axis, ts, real in chosen]


def roomy(bezier, t):
    place = bezier_at(bezier, t)
    return min(math.dist(place, bezier[0]), math.dist(place, bezier[3])) >= SHORTEST_PIECE


def free_place(bezier, t):
    for share in FREE_SHARES:
        trial = t + (0.5 - t) * share
        if roomy(bezier, trial):
            return trial
    return t


def steady(beziers, cuts):
    places = [[bezier[0]] + [bezier_at(bezier, ts[master]) for ts in cuts] + [bezier[3]] for master, bezier in enumerate(beziers)]
    for low, high in zip(places, places[1:]):
        for number in range(len(low) - 1):
            first = (low[number + 1][0] - low[number][0], low[number + 1][1] - low[number][1])
            second = (high[number + 1][0] - high[number][0], high[number + 1][1] - high[number][1])
            if passes_near_zero(first, second):
                return False
    return True


def passes_near_zero(first, second):
    along = (second[0] - first[0], second[1] - first[1])
    reach = along[0] * along[0] + along[1] * along[1]
    share = 0.0 if reach == 0 else min(max(-(first[0] * along[0] + first[1] * along[1]) / reach, 0.0), 1.0)
    return math.hypot(first[0] + along[0] * share, first[1] + along[1] * share) < SHORTEST_PIECE


def cuts_fit(bezier, ts):
    if any(later <= earlier for earlier, later in zip(ts, ts[1:])):
        return False
    places = [bezier[0]] + [bezier_at(bezier, t) for t in ts] + [bezier[3]]
    if not all(math.dist(a, b) >= SHORTEST_PIECE for a, b in zip(places, places[1:])):
        return False
    pieces = cut_bezier(bezier, [(0, t, False) for t in ts])
    return all(math.dist(before[2], before[3]) >= SHORTEST_HANDLE and math.dist(after[0], after[1]) >= SHORTEST_HANDLE for before, after in zip(pieces, pieces[1:]))


def aligned(piece, axis, value, indices):
    points = list(piece)
    for index in indices:
        point = list(points[index])
        point[axis] = value
        points[index] = tuple(point)
    return tuple(points)


def cut_bezier(bezier, cuts):
    pieces = []
    rest, done = bezier, 0.0
    for axis, t, real in cuts:
        local = (t - done) / (1 - done)
        first, rest = split(rest, local)
        if real:
            value = first[3][axis]
            first = aligned(first, axis, value, (2, 3))
            rest = aligned(rest, axis, value, (0, 1))
        pieces.append(first)
        done = t
    pieces.append(rest)
    return pieces


def ring_of(contour):
    segments = list(contour.segments)
    implicit = not segments or segments[-1][-1] != contour.start
    if implicit:
        segments.append((contour.start,))
    return contour.start, segments, implicit


def contour_of(start, segments, implicit, hole):
    if implicit and len(segments[-1]) == 1 and segments[-1][0] == start:
        segments = segments[:-1]
    return Contour(start, segments, hole)


def node_at(start, segments, index):
    return start if index == 0 else segments[index - 1][-1]


def bezier_of(start, segments, index):
    return (node_at(start, segments, index), *segments[index])


def split_group(rings):
    count = len(rings[0][1])
    inserted = [False] * count
    new_segments = [[] for _ in rings]
    new_inserted = []
    for index in range(count):
        if all(len(ring[1][index]) == 3 for ring in rings):
            beziers = [bezier_of(ring[0], ring[1], index) for ring in rings]
            cuts = extreme_cuts(beziers)
        else:
            cuts = []
        new_inserted.append(inserted[index])
        if not cuts:
            for target, ring in zip(new_segments, rings):
                target.append(ring[1][index])
            continue
        for master, (target, bezier) in enumerate(zip(new_segments, beziers)):
            pieces = cut_bezier(bezier, [(axis, ts[master], master in real) for axis, ts, real in cuts])
            target.extend(piece[1:] for piece in pieces)
        new_inserted.extend([True] * len(cuts))
    return [(ring[0], segments, ring[2]) for ring, segments in zip(rings, new_segments)], new_inserted


def tangent_axis(direction):
    return any(abs(direction[axis]) < AXIS_TANGENT for axis in (0, 1))


def merge_ready(start, segments, index):
    count = len(segments)
    before, after = segments[index - 1], segments[index]
    if len(before) != 3 or len(after) != 3:
        return False
    node = node_at(start, segments, index)
    if round(node[1], 3) in KEPT_HEIGHTS:
        return False
    arrive = unit((node[0] - before[1][0], node[1] - before[1][1]))
    leave = unit((after[0][0] - node[0], after[0][1] - node[1]))
    if arrive is None or leave is None:
        return False
    if abs(cross(arrive, leave)) > SMOOTH_JOIN or arrive[0] * leave[0] + arrive[1] * leave[1] <= 0:
        return False
    if tangent_axis(arrive) or tangent_axis(leave):
        return False
    first = bezier_of(start, segments, (index - 1) % count)
    second = bezier_of(start, segments, index)
    return bend_of(first) * bend_of(second) > 0


def bend_of(bezier):
    leave = (bezier[1][0] - bezier[0][0], bezier[1][1] - bezier[0][1])
    arrive = (bezier[3][0] - bezier[2][0], bezier[3][1] - bezier[2][1])
    return cross(leave, arrive)


def samples_of(pieces):
    steps = numpy.linspace(0, 1, FIT_SAMPLES + 1)
    points = []
    for number, piece in enumerate(pieces):
        control = numpy.array(piece, dtype=float)
        for t in steps[1 if number else 0 :]:
            mt = 1 - t
            points.append(mt ** 3 * control[0] + 3 * mt * mt * t * control[1] + 3 * mt * t * t * control[2] + t ** 3 * control[3])
    return numpy.array(points)


def fitted(pieces):
    p0, p3 = numpy.array(pieces[0][0], dtype=float), numpy.array(pieces[-1][3], dtype=float)
    leave = unit((pieces[0][1][0] - p0[0], pieces[0][1][1] - p0[1]))
    arrive = unit((p3[0] - pieces[-1][2][0], p3[1] - pieces[-1][2][1]))
    if leave is None or arrive is None:
        return None
    d0, d3 = numpy.array(leave), numpy.array(arrive)
    samples = samples_of(pieces)
    lengths = numpy.concatenate([[0.0], numpy.cumsum(numpy.linalg.norm(numpy.diff(samples, axis=0), axis=1))])
    u = lengths / lengths[-1]
    first = second = None
    for _ in range(FIT_ROUNDS):
        mu = 1 - u
        b0, b1, b2, b3 = mu ** 3, 3 * mu * mu * u, 3 * mu * u * u, u ** 3
        fixed = numpy.outer(b0 + b1, p0) + numpy.outer(b2 + b3, p3)
        columns = numpy.stack([(b1[:, None] * d0).ravel(), (-b2[:, None] * d3).ravel()], axis=1)
        solution = numpy.linalg.lstsq(columns, (samples - fixed).ravel(), rcond=None)[0]
        first, second = solution
        if first <= 0 or second <= 0:
            return None
        u = refined(handled(p0, d0, p3, d3, first, second), samples, u)
    handles, error = (first, second), deviation(handled(p0, d0, p3, d3, first, second), samples, u)
    if MERGE_ERROR < error <= SEARCH_REACH * MERGE_ERROR:
        handles, error = searched(p0, d0, p3, d3, samples, u, handles, error)
    control = handled(p0, d0, p3, d3, *handles)
    return tuple(tuple(float(value) for value in point) for point in control), error


def handled(p0, d0, p3, d3, first, second):
    return numpy.array([p0, p0 + first * d0, p3 - second * d3, p3])


def deviation(control, samples, u):
    return numpy.linalg.norm(curve(control, refined(control, samples, u)) - samples, axis=1).max()


def searched(p0, d0, p3, d3, samples, u, handles, error):
    step = SEARCH_STEP * max(handles)
    while step > SEARCH_FINEST:
        for move in ((step, 0), (-step, 0), (0, step), (0, -step)):
            trial = (handles[0] + move[0], handles[1] + move[1])
            if min(trial) <= 0:
                continue
            spent = deviation(handled(p0, d0, p3, d3, *trial), samples, u)
            if spent < error:
                handles, error = trial, spent
                break
        else:
            step /= 2
    return handles, error


def curve(control, u):
    mu = 1 - u
    return numpy.outer(mu ** 3, control[0]) + numpy.outer(3 * mu * mu * u, control[1]) + numpy.outer(3 * mu * u * u, control[2]) + numpy.outer(u ** 3, control[3])


def refined(control, samples, u):
    for _ in range(2):
        mu = 1 - u
        point = curve(control, u)
        d1 = numpy.outer(3 * mu * mu, control[1] - control[0]) + numpy.outer(6 * mu * u, control[2] - control[1]) + numpy.outer(3 * u * u, control[3] - control[2])
        d2 = numpy.outer(6 * mu, control[2] - 2 * control[1] + control[0]) + numpy.outer(6 * u, control[3] - 2 * control[2] + control[1])
        offset = point - samples
        numerator = (offset * d1).sum(axis=1)
        denominator = (d1 * d1).sum(axis=1) + (offset * d2).sum(axis=1)
        step = numpy.where(numpy.abs(denominator) > 1e-9, numerator / numpy.where(denominator == 0, 1, denominator), 0)
        u = numpy.clip(u - step, 0, 1)
    return u


def no_inner_extremes(bezier):
    return all(depth(bezier, axis, t) <= SPLIT_DEPTH for axis in (0, 1) for t in stationary(bezier, axis))


def tight(rings, inserted, index):
    count = len(inserted)
    sides = [side for side, beside in (((index - 1) % count, (index - 1) % count), (index, (index + 1) % count)) if inserted[beside]]
    for start, segments, _ in rings:
        for side in sides:
            bezier = bezier_of(start, segments, side)
            if math.dist(bezier[0], bezier[3]) < TIGHT_PIECE:
                return True
    return False


def merged_group(rings, inserted):
    while True:
        count = len(rings[0][1])
        for index in range(count):
            if inserted[index] or not (inserted[(index - 1) % count] or inserted[(index + 1) % count]):
                continue
            if not all(merge_ready(start, segments, index) for start, segments, _ in rings):
                continue
            limit = TIGHT_ERROR if tight(rings, inserted, index) else MERGE_ERROR
            results = []
            for start, segments, _ in rings:
                pieces = [bezier_of(start, segments, (index - 1) % count), bezier_of(start, segments, index)]
                result = fitted(pieces)
                if result is None or result[1] > limit or not no_inner_extremes(result[0]):
                    break
                results.append(result[0])
            else:
                rings = [joined(ring, index, bezier) for ring, bezier in zip(rings, results)]
                inserted = inserted[:index] + inserted[index + 1 :] if index else inserted[1:]
                break
        else:
            return rings


def joined(ring, index, bezier):
    start, segments, implicit = ring
    segments = list(segments)
    merged = tuple(bezier[1:])
    if index:
        segments[index - 1 : index + 1] = [merged]
        return start, segments, implicit
    new_start = segments[0][-1]
    return new_start, segments[1:-1] + [merged], implicit


def with_extremes(outlines):
    result = [[] for _ in outlines]
    for group in zip(*outlines):
        shapes = {tuple(len(segment) for segment in contour.segments) for contour in group}
        if len(shapes) != 1 or len({contour.segments[-1][-1] == contour.start for contour in group}) != 1:
            for target, contour in zip(result, group):
                target.append(contour)
            continue
        rings = [ring_of(contour) for contour in group]
        rings, inserted = split_group(rings)
        if any(inserted):
            rings = merged_group(rings, inserted)
        for target, contour, (start, segments, implicit) in zip(result, group, rings):
            target.append(contour_of(start, segments, implicit, contour.hole))
    return result


def quad_at(piece, t):
    mt = 1 - t
    return tuple(mt * mt * piece[0][axis] + 2 * mt * t * piece[1][axis] + t * t * piece[2][axis] for axis in (0, 1))


def quad_stationary(piece, axis):
    a, b, c = (point[axis] for point in piece)
    bend = a - 2 * b + c
    if bend == 0:
        return None
    t = (a - b) / bend
    return t if ROOT_EDGE < t < 1 - ROOT_EDGE else None


def middle(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def quad_pieces(contour, first, last):
    count = len(contour)
    offs = [(first + step) % count for step in range(1, (last - first) % count)]
    start = contour[first][0]
    for number, off in enumerate(offs):
        end = contour[last][0] if number == len(offs) - 1 else middle(contour[off][0], contour[offs[number + 1]][0])
        yield number, offs, (start, contour[off][0], end)
        start = end


def rounded(point):
    return (otRound(point[0]), otRound(point[1]))


def levelled(point, axis, value):
    point = list(point)
    point[axis] = value
    return tuple(point)


def quad_misses(contour):
    count = len(contour)
    ons = [index for index, (_, on) in enumerate(contour) if on]
    for position, first in enumerate(ons):
        last = ons[(position + 1) % len(ons)]
        if (last - first) % count < 2:
            continue
        ends = (contour[first][0], contour[last][0])
        for number, offs, piece in quad_pieces(contour, first, last):
            for axis in (0, 1):
                t = quad_stationary(piece, axis)
                if t is None:
                    continue
                spot = quad_at(piece, t)
                if min(abs(spot[axis] - end[axis]) for end in ends) <= TT_TOLERANCE:
                    continue
                if min(math.dist(spot, end) for end in ends) < SHORTEST_PIECE:
                    continue
                yield offs, number, piece, axis, t


def mended(contour, miss):
    offs, number, piece, axis, t = miss
    spot = quad_at(piece, t)
    value = rounded(spot)[axis]
    off = offs[number]
    joints = []
    if number and math.dist(spot, piece[0]) < SHORTEST_PIECE:
        joints.append((offs[number - 1], off))
    if number < len(offs) - 1 and math.dist(spot, piece[2]) < SHORTEST_PIECE:
        joints.append((off, offs[number + 1]))
    if joints:
        if not all(abs(contour[index][0][axis] - value) <= TT_TOLERANCE for index in joints[0]):
            return None
        before, after = joints[0]
        on = levelled(rounded(spot), axis, value)
        changed = dict(enumerate(contour))
        changed[before] = (levelled(contour[before][0], axis, value), 0)
        changed[after] = (levelled(contour[after][0], axis, value), 0)
        points = []
        for index in range(len(contour)):
            points.append(changed[index])
            if index == before:
                points.append((on, 1))
        return points
    leading = (levelled(rounded(lerp(piece[0], piece[1], t)), axis, value), 0)
    trailing = (levelled(rounded(lerp(piece[1], piece[2], t)), axis, value), 0)
    on = (levelled(rounded(spot), axis, value), 1)
    replacement = []
    if number:
        replacement.append((rounded(piece[0]), 1))
    replacement += [leading, on, trailing]
    if number < len(offs) - 1:
        replacement.append((rounded(piece[2]), 1))
    points = []
    for index, point in enumerate(contour):
        if index == off:
            points += replacement
        else:
            points.append(point)
    return points


def with_quad_extremes(contour):
    for _ in range(len(contour)):
        if not any(on for _, on in contour):
            return contour
        for miss in quad_misses(contour):
            fixed = mended(contour, miss)
            if fixed is not None:
                contour = fixed
                break
        else:
            return contour
    return contour


def beside_extreme(contour, index):
    count = len(contour)
    point = contour[index][0]
    before, after = contour[index - 1], contour[(index + 1) % count]
    if before[1] or after[1]:
        return False
    previous = contour[index - 2]
    following = contour[(index + 2) % count]
    pieces = (
        (previous[0] if previous[1] else middle(previous[0], before[0]), before[0], point),
        (point, after[0], following[0] if following[1] else middle(after[0], following[0])),
    )
    for piece in pieces:
        for axis in (0, 1):
            t = quad_stationary(piece, axis)
            if t is not None and abs(quad_at(piece, t)[axis] - point[axis]) <= TT_TOLERANCE:
                return True
    return False
