import math
import unittest
from dataclasses import replace

import numpy
from PIL import Image, ImageDraw

from plutto.features import CLEARANCE, FIRST, ITALIC_CLEARANCE, PAIRS, SECOND, SMALLEST_KERN, needed_kern, nearest_gap, side_gap
from plutto.glyphs import GLYPHS, UPRIGHT_IN_ITALIC, drawn_alike, render, stays_upright
from plutto.masters import ASC, CAP, DESC, ITALIC_MASTERS, ITALIC_WIDTH, MASTERS, SLANT, XH
from plutto.oblique import Ink, flattened, joins, left_of, sheared, turn_between, unit
from plutto.parts import Glyph

from support import font
from test_shaping import kerning

ROUND_GLYPHS = ["o", "O", "zero", "c", "e", "s", "S", "C", "G"]
JOINED_GLYPHS = ["a", "g", "eight", "six", "nine", "three", "eth", "ae", "oe", "ampersand"]
STROKES = {
    "I": [(CAP / 2, 0)],
    "l": [(XH / 2, 0)],
    "H": [(CAP / 4, 0), (CAP / 4, 2)],
    "v": [(XH * 0.75, 0), (XH * 0.75, 2)],
    "x": [(XH * 0.26, 0), (XH * 0.74, 0)],
    "A": [(CAP / 5, 0), (CAP / 5, 2)],
    "V": [(CAP / 2, 0), (CAP / 2, 2)],
}
SHORT_STROKES = ["acute", "grave"]
SHORT_STROKE_TOLERANCE = 0.02
EVEN_TOLERANCE = 0.04
JOINED_TOLERANCE = 0.04
PERCENTILE_SLACK = 0.02
PERCENTILE_STEPS = 8
STROKE_TOLERANCE = 0.02
INNER_PERCENTILES = (0.25, 0.5, 0.75)
SAMPLES = 96
SLOPE = math.tan(math.radians(SLANT))
SLASHED = {"zero.slash": "zero", "zero.tnum.slash": "zero.tnum", "zero.numr.slash": "zero.numr", "zero.dnom.slash": "zero.dnom"}
SLASHED_ROUNDS = {"oslash": "o", "Oslash": "O"}
FRAME_SCALE = 0.5
FRAME_ORIGIN = (-200, -400)
FRAME_SIZE = (700, 800)
SPILL_PIXELS = 2
SIDEWAYS_SLACK = 2
SMOOTH_DEGREES = 2
OVERSHOOT_SLACK = 1
GAP_TOLERANCE = 6
SHALLOW_MEETING = 15
MEETING_TURN = 5
MEETING_REACH = 30
CORNER_CLEARANCE = 2
ITALIC_FORM_STROKES = {
    ("a", "d"): [(XH / 2, 0)],
    ("e", "e"): [(XH * 0.8, 0)],
    ("f", "f"): [(XH / 2, 0)],
    ("y", "v"): [(XH * 0.75, 0), (XH * 0.75, 2)],
    ("uni0438", "u"): [(XH / 2, 0), (XH / 2, 2)],
    ("uni0442", "m"): [(XH / 2, 0)],
    ("uni0433.loclSRB", "dotlessi"): [(XH / 2, 0)],
    ("v", "v"): [(XH * 0.75, 0), (XH * 0.75, 2)],
    ("w", "w"): [(XH * 0.75, 0), (XH * 0.75, 4)],
    ("x", "x"): [(XH * 0.26, 0), (XH * 0.74, 0)],
    ("z", "z"): [(XH * 0.6, 0)],
}
F_CLOSERS = ["quotesingle", "quotedbl", "quoteright", "quotedblright", "question", "exclam", "asterisk", "parenright", "bracketright"]
MODELLED_IN_ITALIC = {"a"}


def metric_heights(master):
    return {0, XH, CAP, ASC, DESC, -master.ov, XH + master.ov, CAP + master.ov}


def pairs():
    return list(zip(MASTERS, ITALIC_MASTERS))


def upright_of(italic):
    return replace(italic, slant=0)


def drawn_pairs():
    return [(upright_of(italic), italic) for italic in ITALIC_MASTERS]


def reference(name, roman, italic):
    return roman if drawn_alike(name) else upright_of(italic)



def thicknesses(glyph):
    contours = [contour.oriented() for contour in glyph.contours]
    ink = Ink(contours)
    outline = flattened(max(contours, key=lambda contour: abs(contour.area())))
    step = max(1, len(outline) // SAMPLES)
    points, directions = [], []
    for index in range(0, len(outline), step):
        before, after = outline[index - 1], outline[(index + 1) % len(outline)]
        tangent = unit((after[0] - before[0], after[1] - before[1]))
        if tangent is None:
            continue
        normal = left_of(tangent)
        for side in (1, -1):
            probe = (outline[index][0] + normal[0] * side, outline[index][1] + normal[1] * side)
            if ink.inside([probe])[0]:
                points.append(outline[index])
                directions.append((normal[0] * side, normal[1] * side))
                break
    return sorted(depth for depth in ink.depths(points, directions) if not math.isnan(depth))


def stroke_across(glyph, height, crossing):
    contours = [contour.oriented() for contour in glyph.contours]
    ink = Ink(contours)
    found = []
    for contour in contours:
        outline = flattened(contour)
        for here, after in zip(outline, outline[1:] + outline[:1]):
            if (here[1] - height) * (after[1] - height) < 0:
                t = (height - here[1]) / (after[1] - here[1])
                found.append((here[0] + (after[0] - here[0]) * t, unit((after[0] - here[0], after[1] - here[1]))))
    found.sort()
    x, tangent = found[crossing]
    normal = left_of(tangent)
    if normal[0] < 0:
        normal = (-normal[0], -normal[1])
    return float(ink.depths([(x, height)], [normal])[0])


def middle_width(glyph):
    contour = max(glyph.contours, key=lambda contour: abs(contour.area()))
    points = numpy.array(flattened(contour.oriented()), dtype=float)
    centre = points.mean(axis=0)
    _, _, axes = numpy.linalg.svd(points - centre)
    normal = axes[1]
    found = []
    for here, after in zip(points, numpy.roll(points, -1, axis=0)):
        step = after - here
        across = step[0] * normal[1] - step[1] * normal[0]
        if abs(across) < 1e-9:
            continue
        offset = here - centre
        share = (normal[0] * offset[1] - normal[1] * offset[0]) / across
        if 0 <= share < 1:
            found.append(float((here + step * share - centre) @ normal))
    return max(found) - min(found)


def percentile(values, share):
    return values[min(len(values) - 1, int(share * len(values)))]


def nearest_drift(upright, slanted, share):
    low, high = max(0.0, share - PERCENTILE_SLACK), min(1.0, share + PERCENTILE_SLACK)
    shares = [low + (high - low) * step / PERCENTILE_STEPS for step in range(PERCENTILE_STEPS + 1)]
    return min((percentile(slanted, share) / percentile(upright, other) - 1 for other in shares), key=abs)


def plain_shear(glyph, slope):
    return Glyph([contour.map(lambda point: sheared(point, slope)) for contour in glyph.contours], glyph.advance)


def spread(values):
    return values[-1] / values[0]


def corners(glyph):
    return [point for contour in glyph.contours for point in contour.points()]


def slanted_names():
    return [name for name in GLYPHS if not stays_upright(name)]


def frame_mask(contours):
    total = numpy.zeros(FRAME_SIZE[::-1], dtype=int)
    for contour in contours:
        image = Image.new("L", FRAME_SIZE, 0)
        points = [
            ((x - FRAME_ORIGIN[0]) * FRAME_SCALE, FRAME_SIZE[1] - (y - FRAME_ORIGIN[1]) * FRAME_SCALE)
            for x, y in flattened(contour.oriented())
        ]
        ImageDraw.Draw(image).polygon(points, fill=1)
        total += (1 if contour.oriented().area() > 0 else -1) * numpy.asarray(image, dtype=int)
    return total != 0


def grown(mask):
    spread = mask.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            spread |= numpy.roll(numpy.roll(mask, dy, axis=0), dx, axis=1)
    return spread


def ink_box(glyph):
    points = [point for contour in glyph.contours for point in flattened(contour)]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def polyline(contour):
    points = numpy.array(flattened(contour.oriented()), dtype=float)
    return points, numpy.roll(points, -1, axis=0) - points


def meetings(glyph):
    lines = [polyline(contour) for contour in glyph.contours]
    corners = [point for contour in glyph.contours for point in contour.corners()]
    found = []
    boxes = [(starts.min(axis=0), starts.max(axis=0)) for starts, _ in lines]
    for first in range(len(lines)):
        for second in range(first + 1, len(lines)):
            if (boxes[first][1] < boxes[second][0]).any() or (boxes[second][1] < boxes[first][0]).any():
                continue
            (starts, steps), (others, other_steps) = lines[first], lines[second]
            rest = [contour.oriented() for index, contour in enumerate(glyph.contours) if index not in (first, second)]
            covering = Ink(rest) if rest else None
            across = steps[:, None, 0] * other_steps[None, :, 1] - steps[:, None, 1] * other_steps[None, :, 0]
            offset = others[None, :, :] - starts[:, None, :]
            with numpy.errstate(divide="ignore", invalid="ignore"):
                share = (offset[..., 0] * other_steps[None, :, 1] - offset[..., 1] * other_steps[None, :, 0]) / across
                other_share = (offset[..., 0] * steps[:, None, 1] - offset[..., 1] * steps[:, None, 0]) / across
            hit = (across != 0) & (share >= 0) & (share < 1) & (other_share >= 0) & (other_share < 1)
            for a, b in zip(*numpy.nonzero(hit)):
                point = tuple(starts[a] + steps[a] * share[a, b])
                if any(math.dist(point, corner) < CORNER_CLEARANCE for corner in corners):
                    continue
                if covering and covering.inside([point])[0]:
                    continue
                cosine = abs(steps[a] @ other_steps[b]) / (numpy.hypot(*steps[a]) * numpy.hypot(*other_steps[b]))
                found.append((first, second, point, math.degrees(math.acos(min(1.0, cosine)))))
    return found


def kinked_meetings(name, roman, italic):
    upright = [meeting for meeting in meetings(render(name, roman)) if meeting[3] < SHALLOW_MEETING]
    kinks = []
    for first, second, point, angle in meetings(render(name, italic)):
        back = sheared(point, -italic.slope)
        near = [meeting for meeting in upright if meeting[:2] == (first, second) and math.dist(meeting[2], back) < MEETING_REACH]
        if near and angle > min(near, key=lambda meeting: math.dist(meeting[2], back))[3] + MEETING_TURN:
            kinks.append((round(point[0]), round(point[1]), round(angle, 1)))
    return kinks


def paired_contours(name, roman, italic):
    upright = [contour.oriented() for contour in render(name, roman).contours]
    return zip(upright, render(name, italic).contours)


def hidden(contours, index, point):
    others = [contour.oriented() for number, contour in enumerate(contours) if number != index]
    return bool(others) and bool(Ink(others).inside([point])[0])


class ItalicOutlineTest(unittest.TestCase):
    def test_stems_lean_by_the_slant(self):
        for style in ("LightItalic", "Italic", "BoldItalic", "BlackItalic"):
            coordinates = font(style)["glyf"]["I"].coordinates
            bottom = min(x for x, y in coordinates if y == 0)
            top = min(x for x, y in coordinates if y == CAP)
            with self.subTest(style=style):
                self.assertAlmostEqual((top - bottom) / CAP, SLOPE, delta=2 / CAP)

    def test_stems_and_diagonals_keep_their_weight(self):
        for roman, italic in pairs():
            for name, places in STROKES.items():
                for height, crossing in places:
                    upright = stroke_across(render(name, roman), height, crossing)
                    slanted = stroke_across(render(name, italic), height, crossing)
                    with self.subTest(master=italic.name, glyph=name, height=height, crossing=crossing):
                        self.assertAlmostEqual(slanted / upright, 1, delta=STROKE_TOLERANCE)

    def test_short_strokes_keep_their_weight(self):
        for roman, italic in pairs():
            for name in SHORT_STROKES:
                with self.subTest(master=italic.name, glyph=name):
                    self.assertAlmostEqual(middle_width(render(name, italic)) / middle_width(render(name, roman)), 1, delta=SHORT_STROKE_TOLERANCE)

    def drifts(self, name, roman, italic):
        model = reference(name, roman, italic)
        upright = thicknesses(render(name, model))
        slanted = thicknesses(render(name, italic))
        sheared_only = thicknesses(plain_shear(render(name, model), italic.slope))
        drift = [percentile(slanted, share) / percentile(upright, share) - 1 for share in INNER_PERCENTILES]
        shear_drift = [percentile(sheared_only, share) / percentile(upright, share) - 1 for share in INNER_PERCENTILES]
        return drift, shear_drift

    def test_round_letters_stay_even(self):
        for roman, italic in pairs():
            for name in ROUND_GLYPHS:
                drift, shear_drift = self.drifts(name, roman, italic)
                with self.subTest(master=italic.name, glyph=name):
                    self.assertLessEqual(max(map(abs, drift)), EVEN_TOLERANCE, drift)
                    self.assertLessEqual(sum(map(abs, drift)), sum(map(abs, shear_drift)) + 0.01, (drift, shear_drift))

    def test_joined_letters_stay_even(self):
        for roman, italic in pairs():
            for name in JOINED_GLYPHS:
                upright = thicknesses(render(name, reference(name, roman, italic)))
                slanted = thicknesses(render(name, italic))
                drift = [nearest_drift(upright, slanted, share) for share in INNER_PERCENTILES]
                with self.subTest(master=italic.name, glyph=name):
                    self.assertLessEqual(max(map(abs, drift)), JOINED_TOLERANCE, drift)

    def test_contours_meet_at_their_roman_angle(self):
        names = [name for name in slanted_names() if len(GLYPHS[name][1](MASTERS[0]).contours) > 1]
        for roman, italic in drawn_pairs():
            for name in names:
                with self.subTest(master=italic.name, glyph=name):
                    self.assertEqual(kinked_meetings(name, roman, italic), [])

    def test_upright_glyphs_only_move_sideways(self):
        names = [name for name in GLYPHS if stays_upright(name)]
        self.assertGreaterEqual(len(names), len(UPRIGHT_IN_ITALIC))
        for roman, italic in pairs():
            for name in names:
                upright = corners(render(name, roman))
                moved = corners(render(name, italic))
                shifts = {round(after[0] - before[0], 6) for before, after in zip(upright, moved)}
                with self.subTest(master=italic.name, glyph=name):
                    self.assertEqual([before[1] for before in upright], [after[1] for after in moved])
                    self.assertEqual(len(shifts), 1)

    def test_italic_narrows_the_roman_advances(self):
        for roman, italic in pairs():
            for name in GLYPHS:
                own = render(name, upright_of(italic)).advance / ITALIC_WIDTH
                with self.subTest(master=italic.name, glyph=name):
                    self.assertAlmostEqual(render(name, italic).advance, own * ITALIC_WIDTH, places=6)
                    if drawn_alike(name):
                        self.assertAlmostEqual(own, render(name, roman).advance, places=6)

    def test_italic_forms_keep_the_roman_weight(self):
        for roman, italic in pairs():
            for (name, model), places in ITALIC_FORM_STROKES.items():
                for height, crossing in places:
                    upright = stroke_across(render(model, italic if name in MODELLED_IN_ITALIC else roman), height, crossing)
                    slanted = stroke_across(render(name, italic), height, crossing)
                    with self.subTest(master=italic.name, glyph=name, model=model, height=height, crossing=crossing):
                        self.assertAlmostEqual(slanted / upright, 1, delta=EVEN_TOLERANCE)

    def test_slashed_zeros_stay_inside_their_bowl(self):
        for master in MASTERS + ITALIC_MASTERS:
            for slashed, plain in SLASHED.items():
                bowl = grown(frame_mask([contour for contour in render(plain, master).contours if not contour.hole]))
                spill = frame_mask(render(slashed, master).contours) & ~bowl
                with self.subTest(master=master.name, glyph=slashed):
                    self.assertLessEqual(int(spill.sum()), SPILL_PIXELS)

    def test_slashed_rounds_stay_within_the_bowl_sideways(self):
        for roman, italic in drawn_pairs():
            for slashed, plain in SLASHED_ROUNDS.items():
                left, _, right, _ = ink_box(render(plain, italic))
                slash_left, slash_bottom, slash_right, slash_top = ink_box(render(slashed, italic))
                _, roman_bottom, _, roman_top = ink_box(render(slashed, roman))
                with self.subTest(master=italic.name, glyph=slashed):
                    self.assertGreaterEqual(slash_left, left - SIDEWAYS_SLACK)
                    self.assertLessEqual(slash_right, right + SIDEWAYS_SLACK)
                    self.assertAlmostEqual(slash_bottom, roman_bottom, delta=OVERSHOOT_SLACK)
                    self.assertAlmostEqual(slash_top, roman_top, delta=OVERSHOOT_SLACK)

    def test_points_on_vertical_metrics_keep_their_height(self):
        for roman, italic in drawn_pairs():
            heights = metric_heights(roman)
            for name in slanted_names():
                moved = []
                for upright, slanted in paired_contours(name, roman, italic):
                    for before, after in zip(upright.corners(), slanted.corners()):
                        if round(before[1], 3) in heights and abs(after[1] - before[1]) > 1e-6:
                            moved.append((before, after))
                with self.subTest(master=italic.name, glyph=name):
                    self.assertEqual(moved, [])

    def test_round_extremes_keep_their_overshoot(self):
        for roman, italic in drawn_pairs():
            for name in ROUND_GLYPHS:
                _, upright_bottom, _, upright_top = ink_box(render(name, roman))
                _, bottom, _, top = ink_box(render(name, italic))
                with self.subTest(master=italic.name, glyph=name):
                    self.assertAlmostEqual(bottom, upright_bottom, delta=OVERSHOOT_SLACK)
                    self.assertAlmostEqual(top, upright_top, delta=OVERSHOOT_SLACK)

    def test_smooth_joins_stay_smooth(self):
        for roman, italic in drawn_pairs():
            for name in slanted_names():
                kinks = []
                outlines = render(name, italic).contours
                for index, (upright, slanted) in enumerate(paired_contours(name, roman, italic)):
                    for (_, _, arriving, leaving), (_, point, now_arriving, now_leaving) in zip(joins(upright), joins(slanted)):
                        if not (arriving and leaving and now_arriving and now_leaving):
                            continue
                        if hidden(outlines, index, point):
                            continue
                        if turn_between(arriving, leaving) < math.radians(SMOOTH_DEGREES) and turn_between(now_arriving, now_leaving) > math.radians(SMOOTH_DEGREES):
                            kinks.append(point)
                with self.subTest(master=italic.name, glyph=name):
                    self.assertEqual(kinks, [])

    def test_descenders_clear_opening_brackets_and_quotes(self):
        for italic in ITALIC_MASTERS:
            built = font(italic.name.replace(" ", ""))
            gap = side_gap(render("o", italic))
            for lefts, rights, share in ITALIC_CLEARANCE:
                for left in lefts:
                    for right in rights:
                        needed = needed_kern(render(left, italic), render(right, italic), gap * share)
                        if needed < SMALLEST_KERN:
                            continue
                        with self.subTest(master=italic.name, pair=(left, right)):
                            self.assertGreaterEqual(kerning(built, left, right), round(needed) - 1)

    def test_russian_italic_de_rises_like_a_partial_sign(self):
        for roman, italic in pairs():
            with self.subTest(master=italic.name):
                self.assertGreater(ink_box(render("uni0434", italic))[3], ASC * 0.9)
                self.assertGreaterEqual(ink_box(render("uni0434", italic))[1], -italic.ov - 1)
                self.assertLess(ink_box(render("uni0434", roman))[3], XH + roman.ov + 1)
                self.assertLess(ink_box(render("uni0434.loclSRB", italic))[1], DESC / 2)

    def test_f_clears_quotes_and_closing_punctuation(self):
        shares = {right: share for lefts, rights, share in CLEARANCE if "f" in lefts for right in rights}
        for master in MASTERS + ITALIC_MASTERS:
            built = font(master.name.replace(" ", ""))
            gap = side_gap(render("o", master))
            for right in F_CLOSERS:
                needed = needed_kern(render("f", master), render(right, master), gap * shares[right])
                with self.subTest(master=master.name, right=right):
                    self.assertGreaterEqual(kerning(built, "f", right), round(needed) - 1 if needed >= SMALLEST_KERN else 0)

    def test_kerned_pairs_keep_their_roman_gap(self):
        for roman, italic in pairs():
            upright_font, slanted_font = font(roman.name), font(italic.name.replace(" ", ""))
            for first, second, _, _ in PAIRS:
                for left in FIRST[first]:
                    for right in SECOND[second]:
                        upright_gap = nearest_gap(left, right, roman)
                        slanted_gap = nearest_gap(left, right, italic)
                        if upright_gap is None or slanted_gap is None or not (drawn_alike(left) and drawn_alike(right)):
                            continue
                        upright = (upright_gap + kerning(upright_font, left, right)) * ITALIC_WIDTH
                        slanted = slanted_gap + kerning(slanted_font, left, right)
                        with self.subTest(master=italic.name, pair=(left, right)):
                            self.assertAlmostEqual(slanted, upright, delta=GAP_TOLERANCE)


if __name__ == "__main__":
    unittest.main()
