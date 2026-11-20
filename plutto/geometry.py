import math
from dataclasses import dataclass


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def split(bezier, t):
    p01 = lerp(bezier[0], bezier[1], t)
    p12 = lerp(bezier[1], bezier[2], t)
    p23 = lerp(bezier[2], bezier[3], t)
    p012 = lerp(p01, p12, t)
    p123 = lerp(p12, p23, t)
    middle = lerp(p012, p123, t)
    return (bezier[0], p01, p012, middle), (middle, p123, p23, bezier[3])


def head(bezier, t):
    return split(bezier, t)[0]


def flip(bezier):
    return (bezier[3], bezier[2], bezier[1], bezier[0])


def quarter(p0, p1, start, k):
    x0, y0 = p0
    x1, y1 = p1
    if start == "h":
        return (p0, (x0 + k * (x1 - x0), y0), (x1, y1 - k * (y1 - y0)), p1)
    return (p0, (x0, y0 + k * (y1 - y0)), (x1 - k * (x1 - x0), y1), p1)


def intersect(a0, a1, b0, b1):
    ax, ay = a1[0] - a0[0], a1[1] - a0[1]
    bx, by = b1[0] - b0[0], b1[1] - b0[1]
    denominator = ax * by - ay * bx
    t = ((b0[0] - a0[0]) * by - (b0[1] - a0[1]) * bx) / denominator
    return (a0[0] + ax * t, a0[1] + ay * t)


def bend(p0, d0, p1, d1, pull0, pull1):
    corner = intersect(p0, (p0[0] + d0[0], p0[1] + d0[1]), p1, (p1[0] + d1[0], p1[1] + d1[1]))
    return (p0, lerp(p0, corner, pull0), lerp(p1, corner, pull1), p1)


def across(direction, thickness):
    return thickness * math.hypot(direction[0], direction[1]) / abs(direction[1])


def closed_segments(contour):
    segments = list(contour.segments)
    if segments and segments[-1][-1] != contour.start:
        segments.append((contour.start,))
    return segments


class Contour:
    def __init__(self, start, segments, hole=False):
        self.start = start
        self.segments = list(segments)
        self.hole = hole

    def points(self):
        yield self.start
        for segment in self.segments:
            yield from segment

    def corners(self):
        yield self.start
        for segment in self.segments:
            yield segment[-1]

    def map(self, transform):
        segments = [tuple(transform(point) for point in segment) for segment in self.segments]
        return Contour(transform(self.start), segments, self.hole)

    def reversed(self):
        corners = list(self.corners())
        segments = []
        for index in range(len(self.segments) - 1, -1, -1):
            segment = self.segments[index]
            target = corners[index]
            if len(segment) == 1:
                segments.append((target,))
            else:
                segments.append((segment[1], segment[0], target))
        return Contour(corners[-1], segments, self.hole)

    def area(self):
        points = list(self.points())
        total = 0
        for index, (x0, y0) in enumerate(points):
            x1, y1 = points[(index + 1) % len(points)]
            total += x0 * y1 - x1 * y0
        return total / 2

    def oriented(self):
        clockwise = self.area() < 0
        if clockwise == self.hole:
            return self.reversed()
        return self


class Path:
    def __init__(self, start):
        self.start = start
        self.segments = []

    @property
    def here(self):
        return self.segments[-1][-1] if self.segments else self.start

    def to(self, point):
        self.segments.append((point,))
        return self

    def arc(self, point, start, k):
        self.segments.append(quarter(self.here, point, start, k)[1:])
        return self

    def bez(self, bezier):
        self.segments.append(tuple(bezier[1:]))
        return self

    def close(self, hole=False, smooth=True):
        contour = Contour(self.start, self.segments, hole)
        return faired(contour) if smooth else contour


FAIR_SMOOTH = math.sin(math.radians(1))
FAIR_SWEEPS = 16
FAIR_RANGE = (0.8, 1.25)


@dataclass
class Handles:
    start: tuple
    end: tuple
    leave: tuple
    arrive: tuple
    first: float
    second: float

    @classmethod
    def of(cls, start, segment):
        leave = direction(start, segment[0])
        arrive = direction(segment[1], segment[2])
        if leave is None or arrive is None:
            return None
        return cls(start, segment[2], leave, arrive, math.dist(start, segment[0]), math.dist(segment[1], segment[2]))

    @property
    def span(self):
        return (self.end[0] - self.start[0], self.end[1] - self.start[1])

    @property
    def turn(self):
        return cross(self.leave, self.arrive)

    def arriving_bend(self, first):
        return cross(self.span, self.arrive) - first * self.turn

    def leaving_bend(self, second):
        return cross(self.leave, self.span) - second * self.turn

    def segment(self, first, second):
        return (
            (self.start[0] + self.leave[0] * first, self.start[1] + self.leave[1] * first),
            (self.end[0] - self.arrive[0] * second, self.end[1] - self.arrive[1] * second),
            self.end,
        )


def direction(a, b):
    length = math.dist(a, b)
    if length < 1e-9:
        return None
    return ((b[0] - a[0]) / length, (b[1] - a[1]) / length)


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def smooth_joins(curves, count, closed):
    for index, before in curves.items():
        after_index = (index + 1) % count
        if after_index == 0 and not closed or after_index == index or after_index not in curves:
            continue
        after = curves[after_index]
        aligned = before.arrive[0] * after.leave[0] + before.arrive[1] * after.leave[1] > 0
        if aligned and abs(cross(before.arrive, after.leave)) < FAIR_SMOOTH:
            yield index, after_index


def faired(contour):
    starts = [contour.start] + [segment[-1] for segment in contour.segments[:-1]]
    curves = {}
    for index, (start, segment) in enumerate(zip(starts, contour.segments)):
        if len(segment) == 3:
            handles = Handles.of(start, segment)
            if handles:
                curves[index] = handles
    closed = bool(contour.segments) and contour.segments[-1][-1] == contour.start
    joins = list(smooth_joins(curves, len(contour.segments), closed))
    if not joins:
        return contour
    first = {index: handles.first for index, handles in curves.items()}
    second = {index: handles.second for index, handles in curves.items()}
    low, high = FAIR_RANGE
    for _ in range(FAIR_SWEEPS):
        for before, after in joins:
            arriving = curves[before].arriving_bend(first[before])
            leaving = curves[after].leaving_bend(second[after])
            if arriving * leaving <= 0:
                continue
            ratio = math.sqrt(leaving / arriving)
            product = curves[before].second * curves[after].first
            second[before] = min(max(math.sqrt(product / ratio), low * curves[before].second), high * curves[before].second)
            first[after] = min(max(math.sqrt(product * ratio), low * curves[after].first), high * curves[after].first)
    segments = list(contour.segments)
    for index, handles in curves.items():
        segments[index] = handles.segment(first[index], second[index])
    return Contour(contour.start, segments, contour.hole)
