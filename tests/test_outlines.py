import math
import unittest

import numpy
from fontTools.misc.roundTools import otRound
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from plutto.compile import CMAP_ALIASES, SNAP_REACH, line_marks
from plutto.glyphs import GLYPHS, render
from plutto.masters import ALL_MASTERS, line_heights

from support import INSTANCE_WEIGHTS, SPACES, STYLE_MASTERS, VARIABLES, all_fonts, built_name, font, instance, is_blank, is_combining, is_zero_width, master_fonts, static_fonts, style_weight, unhinted_path, variable_for

PRINTABLE_ASCII = range(0x20, 0x7F)
MINIMUM_SEGMENT = 0.5
ROUNDING_REACH = 1.0 - 1e-6
NARROW = ".narrow"
FULL_WIDTH_SHARE = 0.95


def bounds(glyph_set, name):
    pen = BoundsPen(glyph_set)
    glyph_set[name].draw(pen)
    return pen.bounds


def area(glyph_set, name):
    pen = AreaPen(glyph_set)
    glyph_set[name].draw(pen)
    return abs(pen.value)


def instances():
    for variable in VARIABLES:
        for weight in INSTANCE_WEIGHTS:
            yield f"{variable} {weight}", instance(weight, variable)


def outline_fonts():
    yield from master_fonts()
    yield from instances()


def shipped_outline_fonts():
    yield from outline_fonts()
    yield from static_fonts()


def rounded(point):
    return tuple(otRound(value) for value in point)


def segment_problems(contour):
    problems = []
    here = contour.start
    for index, segment in enumerate(contour.segments):
        end = segment[-1]
        points = [here, *segment]
        length = math.dist(here, end)
        if len(segment) == 1 and length < MINIMUM_SEGMENT:
            problems.append(f"line {index} has zero length at {here}")
        if len(segment) > 1:
            reach = max(math.dist(here, point) for point in points)
            if reach < MINIMUM_SEGMENT:
                problems.append(f"curve {index} collapses to a point at {here}")
            elif length < MINIMUM_SEGMENT and max(math.dist(end, point) for point in segment[:-1]) < MINIMUM_SEGMENT:
                problems.append(f"curve {index} is a loop of zero size at {here}")
        here = end
    if len(contour.segments) < 2:
        problems.append("contour has fewer than two segments")
    if abs(contour.area()) < MINIMUM_SEGMENT:
        problems.append("contour encloses no area")
    return problems


def duplicate_segments(glyph_set, name):
    pen = DecomposingRecordingPen(glyph_set)
    glyph_set[name].draw(pen)
    seen = set()
    duplicates = []
    start = here = None
    for operator, points in pen.value:
        if operator == "moveTo":
            start = here = points[0]
            continue
        if operator in ("closePath", "endPath"):
            points = (start,)
            if here == start:
                continue
        segment = tuple(rounded(point) for point in (here, *points))
        key = min(segment, segment[::-1])
        if key in seen:
            duplicates.append(key)
        seen.add(key)
        here = points[-1]
    return duplicates


def point_segments(table, name):
    coordinates, ends, flags = table[name].getCoordinates(table)
    points = numpy.array(coordinates, dtype=float).reshape(-1, 2)
    segments = []
    start = 0
    for end in ends:
        indices = list(range(start, end + 1))
        on_curve = [index for index in indices if flags[index] & 1]
        if on_curve:
            first = indices.index(on_curve[0])
            ring = indices[first:] + indices[:first] + [on_curve[0]]
            current = [ring[0]]
            for index in ring[1:]:
                current.append(index)
                if flags[index] & 1:
                    segments.append(tuple(current))
                    current = [index]
        start = end + 1
    return points, segments


def ever_within_rounding(low, high):
    change = high - low
    with numpy.errstate(divide="ignore", invalid="ignore"):
        first = (-ROUNDING_REACH - low) / change
        second = (ROUNDING_REACH - low) / change
    still = change == 0
    near = numpy.abs(low) <= ROUNDING_REACH
    starts = numpy.where(still, numpy.where(near, 0.0, 2.0), numpy.minimum(first, second))
    stops = numpy.where(still, numpy.where(near, 1.0, -1.0), numpy.maximum(first, second))
    return numpy.maximum(0.0, starts.max(axis=-1)) <= numpy.minimum(1.0, stops.min(axis=-1))


def meetings_between(low_font, high_font, name):
    low, segments = point_segments(low_font["glyf"], name)
    high, _ = point_segments(high_font["glyf"], name)
    found = []
    for segment in segments:
        start, end = segment[0], segment[-1]
        if ever_within_rounding((low[end] - low[start])[None], (high[end] - high[start])[None])[0]:
            found.append(f"segment from {tuple(low[start])} collapses")
    groups = {}
    for segment in segments:
        groups.setdefault(len(segment), []).append(segment)
    for group in groups.values():
        indices = numpy.array(group)
        here_low, here_high = low[indices].reshape(len(group), -1), high[indices].reshape(len(group), -1)
        for others in (indices, indices[:, ::-1]):
            there_low, there_high = low[others].reshape(len(group), -1), high[others].reshape(len(group), -1)
            hits = ever_within_rounding(here_low[:, None, :] - there_low[None, :, :], here_high[:, None, :] - there_high[None, :, :])
            numpy.fill_diagonal(hits, False)
            for first, second in zip(*numpy.nonzero(numpy.triu(hits))):
                found.append(f"segments {group[first]} and {group[second]} meet")
    return found


class CoverageTest(unittest.TestCase):
    def test_printable_ascii_mapped(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                cmap = built_font.getBestCmap()
                missing = [f"U+{code:04X}" for code in PRINTABLE_ASCII if code not in cmap]
                self.assertEqual(missing, [])

    def test_registry_codepoints_mapped(self):
        for style, built_font in all_fonts():
            cmap = built_font.getBestCmap()
            for name, (code, _) in GLYPHS.items():
                if code is not None:
                    with self.subTest(style=style, glyph=name):
                        self.assertEqual(cmap.get(code), built_name(name))

    def test_aliases_share_their_glyph(self):
        for style, built_font in all_fonts():
            cmap = built_font.getBestCmap()
            for code, name in CMAP_ALIASES.items():
                with self.subTest(style=style, code=f"U+{code:04X}"):
                    self.assertEqual(cmap.get(code), name)


class InkTest(unittest.TestCase):
    def test_glyphs_have_ink(self):
        for style, built_font in all_fonts():
            glyph_set = built_font.getGlyphSet()
            for name in GLYPHS:
                if is_blank(name):
                    continue
                with self.subTest(style=style, glyph=name):
                    self.assertIsNotNone(bounds(glyph_set, built_name(name)))
                    self.assertGreater(area(glyph_set, built_name(name)), 0)

    def test_blank_glyphs_are_empty(self):
        for style, built_font in all_fonts():
            glyph_set = built_font.getGlyphSet()
            for name in GLYPHS:
                if is_blank(name):
                    with self.subTest(style=style, glyph=name):
                        self.assertIsNone(bounds(glyph_set, built_name(name)))

    def test_marks_over_i_and_j_keep_their_full_width(self):
        for style, built_font in static_fonts():
            table = built_font["glyf"]
            for name in built_font.getGlyphOrder():
                if not name.endswith(NARROW):
                    continue
                plain = name[: -len(NARROW)]
                with self.subTest(style=style, glyph=name):
                    narrow, full = table[name], table[plain]
                    self.assertGreaterEqual(narrow.xMax - narrow.xMin, (full.xMax - full.xMin) * FULL_WIDTH_SHARE)

    def test_advances_positive(self):
        for style, built_font in all_fonts():
            metrics = built_font["hmtx"]
            for name in GLYPHS:
                if is_combining(name) or is_zero_width(name):
                    continue
                with self.subTest(style=style, glyph=name):
                    self.assertGreater(metrics[built_name(name)][0], 0)

    def test_ink_inside_win_metrics(self):
        for style, built_font in static_fonts():
            self.check_win_metrics(style, built_font, built_font)

    def test_instance_ink_inside_win_metrics(self):
        for label, instance in instances():
            self.check_win_metrics(label, instance, font(label.split()[0]))

    def check_win_metrics(self, label, built_font, metrics_font):
        os2 = metrics_font["OS/2"]
        glyph_set = built_font.getGlyphSet()
        for name in GLYPHS:
            box = bounds(glyph_set, built_name(name))
            if box is None:
                continue
            with self.subTest(font=label, glyph=name):
                self.assertLessEqual(box[3], os2.usWinAscent)
                self.assertGreaterEqual(box[1], -os2.usWinDescent)


class SegmentTest(unittest.TestCase):
    def test_overlap_removal_keeps_points_on_their_lines(self):
        for styles, _, _ in SPACES:
            for style in styles:
                static = TTFont(unhinted_path(style))["glyf"]
                drawn = instance(style_weight(style), variable_for(style))["glyf"]
                for name in static.keys():
                    if static[name].numberOfContours <= 0 or drawn[name].numberOfContours <= 0:
                        continue
                    lines = line_marks(drawn[name], line_heights(STYLE_MASTERS[style]))
                    off = [
                        (x, y)
                        for x, y in static[name].coordinates
                        for line, spans in lines.items()
                        if 0 < abs(y - line) <= SNAP_REACH and any(low - SNAP_REACH <= x <= high + SNAP_REACH for low, high in spans)
                    ]
                    with self.subTest(style=style, glyph=name):
                        self.assertEqual(off, [])

    def test_source_contours_have_no_degenerate_segments(self):
        for master in ALL_MASTERS:
            for name in GLYPHS:
                with self.subTest(master=master.name, glyph=name):
                    problems = []
                    for index, contour in enumerate(render(name, master).contours):
                        problems += [f"contour {index}: {problem}" for problem in segment_problems(contour)]
                    self.assertEqual(problems, [])

    def test_no_segment_drawn_twice(self):
        for style, built_font in outline_fonts():
            glyph_set = built_font.getGlyphSet()
            for name in GLYPHS:
                with self.subTest(style=style, glyph=name):
                    self.assertEqual(duplicate_segments(glyph_set, built_name(name)), [])

    def test_no_segment_meets_another_between_masters(self):
        for styles, _, _ in SPACES:
            ordered = sorted(styles, key=style_weight)
            for low_style, high_style in zip(ordered, ordered[1:]):
                low_font, high_font = (instance(style_weight(style), variable_for(style)) for style in (low_style, high_style))
                for name in GLYPHS:
                    with self.subTest(between=(low_style, high_style), glyph=name):
                        self.assertEqual(meetings_between(low_font, high_font, built_name(name)), [])

    def test_compiled_contours_have_no_repeated_points(self):
        for style, built_font in shipped_outline_fonts():
            table = built_font["glyf"]
            for name in GLYPHS:
                glyph = table[built_name(name)]
                if glyph.numberOfContours <= 0:
                    continue
                with self.subTest(style=style, glyph=name):
                    problems = []
                    start = 0
                    for index, end in enumerate(glyph.endPtsOfContours):
                        points = [rounded(point) for point in glyph.coordinates[start:end + 1]]
                        if len(points) < 3:
                            problems.append(f"contour {index} has {len(points)} points")
                        for position, point in enumerate(points):
                            if point == points[position - 1]:
                                problems.append(f"contour {index} repeats {tuple(point)}")
                        start = end + 1
                    self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
