import math
from dataclasses import dataclass

from .geometry import Contour, Path, bend, flip, head, intersect, quarter, split


CROSSING_STEPS = 48


def crossing(bezier, x):
    low, high = 0.0, 1.0
    rising = bezier[3][0] > bezier[0][0]
    for _ in range(CROSSING_STEPS):
        middle = (low + high) / 2
        if (head(bezier, middle)[3][0] < x) == rising:
            low = middle
        else:
            high = middle
    return split(bezier, (low + high) / 2)


def crossed(contour, x):
    segments = []
    here = contour.start
    for segment in contour.segments:
        if len(segment) == 3 and (here[0] - x) * (segment[2][0] - x) < 0:
            first, second = crossing((here, *segment), x)
            segments += [first[1:], second[1:]]
        else:
            segments.append(segment)
        here = segment[-1]
    return Contour(contour.start, segments, contour.hole)


def rect(x0, y0, x1, y1, hole=False):
    return Path((x0, y0)).to((x0, y1)).to((x1, y1)).to((x1, y0)).close(hole)


def polygon(points):
    path = Path(points[0])
    for point in points[1:]:
        path.to(point)
    return path.close()


def oval(x0, y0, x1, y1, k, hole=False):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    path = Path((x0, cy))
    path.arc((cx, y1), "v", k).arc((x1, cy), "h", k).arc((cx, y0), "v", k).arc((x0, cy), "h", k)
    return path.close(hole)


def leaning_oval(x0, y0, x1, y1, k, near, hole=False, right=False):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    left_k, right_k = (k, near) if right else (near, k)
    path = Path((x0, cy))
    path.arc((cx, y1), "v", left_k).arc((x1, cy), "h", right_k).arc((cx, y0), "v", right_k).arc((x0, cy), "h", left_k)
    return path.close(hole)


def ring(x0, y0, x1, y1, side, flat, k_out, k_in, cuts=()):
    hole = oval(x0 + side, y0 + flat, x1 - side, y1 - flat, k_in, hole=True)
    for x in cuts:
        hole = crossed(hole, x)
    return [oval(x0, y0, x1, y1, k_out), hole]


def open_ring(outer, inner, k_out, k_in, t_top, t_bottom):
    ox0, oy0, ox1, oy1 = outer
    ix0, iy0, ix1, iy1 = inner
    ocx, ocy = (ox0 + ox1) / 2, (oy0 + oy1) / 2
    icx, icy = (ix0 + ix1) / 2, (iy0 + iy1) / 2
    top_out = head(quarter((ocx, oy1), (ox1, ocy), "h", k_out), t_top)
    top_in = head(quarter((icx, iy1), (ix1, icy), "h", k_in), t_top)
    bottom_out = head(quarter((ocx, oy0), (ox1, ocy), "h", k_out), t_bottom)
    bottom_in = head(quarter((icx, iy0), (ix1, icy), "h", k_in), t_bottom)
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


def arch(left_out, left_in, peak_out, peak_in, right, top, base, stem, thick, ry_out, ry_in, k_out, k_in):
    y_out = top - ry_out
    y_in = top - thick - ry_in
    path = Path((left_out, y_out))
    path.arc((peak_out, top), "v", k_out)
    path.arc((right, y_out), "h", k_out)
    path.to((right, base))
    path.to((right - stem, base))
    path.to((right - stem, y_in))
    path.arc((peak_in, top - thick), "v", k_in)
    path.arc((left_in, y_in), "h", k_in)
    return path.close()


def arm(left_out, left_in, peak_out, peak_in, reach_out, reach_in, top, thick, ry_out, ry_in, t, k_out, k_in):
    y_out = top - ry_out
    y_in = top - thick - ry_in
    end_out = head(quarter((peak_out, top), (reach_out, y_out), "h", k_out), t)
    end_in = head(quarter((peak_in, top - thick), (reach_in, y_in), "h", k_in), t)
    path = Path((left_out, y_out))
    path.arc((peak_out, top), "v", k_out)
    path.bez(end_out)
    path.to(end_in[3])
    path.bez(flip(end_in))
    path.arc((left_in, y_in), "h", k_in)
    return path.close()


def hooked_arch(far_out, far_in, peak_out, peak_in, right, top, base, stem, thick, ry_out, ry_in, t, k_out, k_in):
    y_out = top - ry_out
    y_in = top - thick - ry_in
    end_out = head(quarter((peak_out, top), (far_out, y_out), "h", k_out), t)
    end_in = head(quarter((peak_in, top - thick), (far_in, y_in), "h", k_in), t)
    path = Path(end_out[3])
    path.bez(flip(end_out))
    path.arc((right, y_out), "h", k_out)
    path.to((right, base))
    path.to((right - stem, base))
    path.to((right - stem, y_in))
    path.arc((peak_in, top - thick), "v", k_in)
    path.bez(end_in)
    return path.close()


def elbow(stem, flat, rise, run, radius, k):
    path = Path((0, rise))
    path.to((stem, rise))
    path.to((stem, flat + radius))
    path.arc((stem + radius, flat), "v", k)
    path.to((run, flat))
    path.to((run, 0))
    path.to((stem + radius, 0))
    path.arc((0, flat + radius), "h", k)
    return path.close()


@dataclass
class Node:
    point: tuple
    heading: tuple
    thickness: float
    straight: bool = False
    cut: str = ""
    arrive: float = 0
    leave: float = 0
    right_arrive: float = 0
    right_leave: float = 0


def aim(degrees):
    angle = math.radians(degrees)
    return (math.cos(angle), math.sin(angle))


def edges(node):
    x, y = node.point
    length = math.hypot(node.heading[0], node.heading[1])
    ux, uy = node.heading[0] / length, node.heading[1] / length
    half = node.thickness / 2
    left = (x - uy * half, y + ux * half)
    right = (x + uy * half, y - ux * half)
    if node.cut:
        across = ((x, y), (x + 1, y)) if node.cut == "h" else ((x, y), (x, y + 1))
        left = intersect(left, (left[0] + ux, left[1] + uy), across[0], across[1])
        right = intersect(right, (right[0] + ux, right[1] + uy), across[0], across[1])
    return left, right


def joined(start, heading0, end, heading1, pull0, pull1):
    curve = bend(start, heading0, end, heading1, pull0, pull1)
    corner = intersect(start, (start[0] + heading0[0], start[1] + heading0[1]), end, (end[0] + heading1[0], end[1] + heading1[1]))
    ahead = (corner[0] - start[0]) * heading0[0] + (corner[1] - start[1]) * heading0[1]
    behind = (end[0] - corner[0]) * heading1[0] + (end[1] - corner[1]) * heading1[1]
    if ahead <= 0 or behind <= 0:
        raise ValueError(f"stroke cannot turn from {start} to {end}")
    return curve


def ribbon(nodes, pull, smooth=True):
    sides = [edges(node) for node in nodes]
    leave = [node.leave or pull for node in nodes]
    arrive = [node.arrive or pull for node in nodes]
    right_leave = [node.right_leave or pulled for node, pulled in zip(nodes, leave)]
    right_arrive = [node.right_arrive or pulled for node, pulled in zip(nodes, arrive)]
    path = Path(sides[0][0])
    for index in range(1, len(nodes)):
        if nodes[index].straight:
            path.to(sides[index][0])
        else:
            before, after = nodes[index - 1], nodes[index]
            path.bez(joined(sides[index - 1][0], before.heading, sides[index][0], after.heading, leave[index - 1], arrive[index]))
    path.to(sides[-1][1])
    for index in range(len(nodes) - 2, -1, -1):
        if nodes[index + 1].straight:
            path.to(sides[index][1])
        else:
            back = (-nodes[index + 1].heading[0], -nodes[index + 1].heading[1])
            ahead = (-nodes[index].heading[0], -nodes[index].heading[1])
            path.bez(joined(sides[index + 1][1], back, sides[index][1], ahead, right_arrive[index + 1], right_leave[index]))
    return path.close(smooth=smooth)


def place(contour, ox, oy, fx=1, fy=1):
    return contour.map(lambda point: (ox + fx * point[0], oy + fy * point[1]))


def shift(contours, dx, dy=0):
    return [contour.map(lambda point: (point[0] + dx, point[1] + dy)) for contour in contours]


def mirror(contours, axis):
    return [contour.map(lambda point: (2 * axis - point[0], point[1])) for contour in contours]


def flop(contours, axis):
    return [contour.map(lambda point: (point[0], 2 * axis - point[1])) for contour in contours]


def turn(contours, cx, cy):
    return [contour.map(lambda point: (2 * cx - point[0], 2 * cy - point[1])) for contour in contours]


def extent(contours):
    return max(point[0] for contour in contours for point in contour.corners())
