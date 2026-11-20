import atexit
import json
import math
import os
import shutil
import subprocess
import tempfile
import traceback
import unicodedata
import unittest
from functools import cache
from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.varLib.models import normalizeValue, piecewiseLinearMap

from plutto.compile import build
from plutto import accents
from plutto.glyphs import EXTENSIONS, GLYPHS
from plutto.hinting import UNHINTED_FOLDER, find_autohinter
from plutto.compile import VARIABLE_FILES, compact, production_name
from plutto.masters import BETWEEN_STATICS, FAMILY, ITALIC_BETWEEN_STATICS, ITALIC_MASTERS, MASTERS

BLANK_CATEGORIES = {"Zs", "Zl", "Zp", "Cc", "Cf"}
COMBINING_CATEGORIES = {"Mn", "Me"}
FORMAT_CATEGORIES = {"Cf"}
DEFAULT_IGNORABLE = {0x34F}
MARKS_ABOVE = (216, 230)
CURVE_STEPS = 32
CLEARANCE_SLACK = 4
INTERPOLATED_SLACK = 1
LOOSENESS_STEP = 6
MARK_CLEARANCE = {"Light": 75, "Regular": 72, "Bold": 64, "Black": 58}
MIDDLE_WEIGHT = 550
BETWEEN_WEIGHTS = [350, MIDDLE_WEIGHT, 800]
MASTER_WEIGHTS = sorted(master.weight for master in MASTERS)
INSTANCE_WEIGHTS = sorted(MASTER_WEIGHTS + BETWEEN_WEIGHTS)
LIGHTEST, HEAVIEST = MASTER_WEIGHTS[0], MASTER_WEIGHTS[-1]
STYLES = [compact(master.name) for master in MASTERS]
ITALIC_STYLES = [compact(master.name) for master in ITALIC_MASTERS]
BETWEEN_STYLES = [compact(master.name) for master in BETWEEN_STATICS]
ITALIC_BETWEEN_STYLES = [compact(master.name) for master in ITALIC_BETWEEN_STATICS]
ALL_STYLES = STYLES + BETWEEN_STYLES + ITALIC_STYLES + ITALIC_BETWEEN_STYLES
ROMAN_VARIABLE = VARIABLE_FILES[False]
ITALIC_VARIABLE = VARIABLE_FILES[True]
VARIABLES = [ROMAN_VARIABLE, ITALIC_VARIABLE]
SPACES = [(STYLES, MASTERS, ROMAN_VARIABLE), (ITALIC_STYLES, ITALIC_MASTERS, ITALIC_VARIABLE)]
STYLE_MASTERS = {compact(master.name): master for master in MASTERS + BETWEEN_STATICS + ITALIC_MASTERS + ITALIC_BETWEEN_STATICS}
HB_SHAPE = shutil.which("hb-shape")
REQUIRE_SHAPING = bool(os.environ.get("PLUTTO_REQUIRE_SHAPING"))
NO_HB_SHAPE = "hb-shape is not installed, so the HarfBuzz shaping checks did not run"
AUTOHINTER = find_autohinter()
REQUIRE_HINTING = bool(os.environ.get("PLUTTO_REQUIRE_HINTING"))
NO_AUTOHINTER = "ttfautohint is not installed, so the statics ship unhinted and the hinting checks did not run"


@cache
def attempt_build():
    directory = Path(tempfile.mkdtemp(prefix="plutto-test-"))
    atexit.register(shutil.rmtree, directory, ignore_errors=True)
    try:
        return directory, build(directory), None
    except Exception:
        return directory, [], traceback.format_exc()


def build_error():
    return attempt_build()[2]


def built():
    directory, paths, error = attempt_build()
    if error:
        reason = error.strip().splitlines()[-1]
        raise unittest.SkipTest(f"build failed ({reason}); BuildTest.test_build_succeeds has the traceback")
    return directory, paths


def needs_tool(found, required, setting, reason):
    def decorate(test_class):
        if found:
            return test_class
        if required:
            def refuse(cls):
                raise AssertionError(f"{setting} is set but {reason}")
            test_class.setUpClass = classmethod(refuse)
            return test_class
        return unittest.skip(reason)(test_class)
    return decorate


needs_hb_shape = needs_tool(HB_SHAPE, REQUIRE_SHAPING, "PLUTTO_REQUIRE_SHAPING", NO_HB_SHAPE)
needs_autohinter = needs_tool(AUTOHINTER, REQUIRE_HINTING, "PLUTTO_REQUIRE_HINTING", NO_AUTOHINTER)


def kern_like():
    like = {}
    for extension in EXTENSIONS:
        like.update(extension.KERN_LIKE)
    return {name: model for name, model in like.items() if name in GLYPHS and model in GLYPHS}


class FlatteningPen(BasePen):
    def __init__(self, glyph_set):
        super().__init__(glyph_set)
        self.polygons = []

    def _moveTo(self, point):
        self.polygons.append([point])

    def _lineTo(self, point):
        self.polygons[-1].append(point)

    def _qCurveToOne(self, control, end):
        start = self.polygons[-1][-1]
        for step in range(1, CURVE_STEPS + 1):
            t = step / CURVE_STEPS
            self.polygons[-1].append(tuple(
                (1 - t) ** 2 * a + 2 * (1 - t) * t * b + t ** 2 * c
                for a, b, c in zip(start, control, end)
            ))

    def _curveToOne(self, first, second, end):
        start = self.polygons[-1][-1]
        for step in range(1, CURVE_STEPS + 1):
            t = step / CURVE_STEPS
            self.polygons[-1].append(tuple(
                (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * d
                for a, b, c, d in zip(start, first, second, end)
            ))

    def _closePath(self):
        self.polygons[-1].append(self.polygons[-1][0])


def outline_polygons(glyph_set, name):
    pen = FlatteningPen(glyph_set)
    glyph_set[name].draw(pen)
    return pen.polygons


def ink_top(glyph_set, name):
    return max((y for polygon in outline_polygons(glyph_set, name) for _, y in polygon), default=None)


def master_at(weight):
    return next((master for master in MASTERS if master.weight == weight), None)


def wght_axis(variable=ROMAN_VARIABLE):
    return next(axis for axis in font(variable)["fvar"].axes if axis.axisTag == "wght")


def variable_default_weight(variable=ROMAN_VARIABLE):
    weight = wght_axis(variable).defaultValue
    if master_at(weight) is None:
        raise AssertionError(f"the variable default weight {weight} matches no master")
    return weight


def style_weight(style):
    if style in VARIABLES:
        return variable_default_weight(style)
    master = STYLE_MASTERS.get(style)
    if master is None:
        raise AssertionError(f"no master is named {style}")
    return master.weight


def is_italic_style(style):
    return style == ITALIC_VARIABLE or style in ITALIC_STYLES + ITALIC_BETWEEN_STYLES


def variable_for(style):
    return ITALIC_VARIABLE if is_italic_style(style) else ROMAN_VARIABLE


@cache
def instance(weight, variable=ROMAN_VARIABLE):
    return instantiateVariableFont(font(variable), {"wght": weight}, inplace=False)


def outline_font(style, weight):
    if style in ALL_STYLES:
        if style_weight(style) != weight:
            raise AssertionError(f"{style} is drawn at {style_weight(style)}, not {weight}")
        return font(style)
    return instance(weight, variable_for(style))


def axis_position(weight):
    axis = wght_axis()
    position = normalizeValue(weight, (axis.minValue, axis.defaultValue, axis.maxValue))
    variable = font("Variable")
    if "avar" in variable:
        position = piecewiseLinearMap(position, variable["avar"].segments[axis.axisTag])
    return position


def neighbouring_masters(weight):
    ordered = sorted(MASTERS, key=lambda master: master.weight)
    for low, high in zip(ordered, ordered[1:]):
        if low.weight <= weight <= high.weight:
            return low, high
    raise AssertionError(f"weight {weight} lies outside the masters")


def blend(weight, values):
    low, high = neighbouring_masters(weight)
    start, end = axis_position(low.weight), axis_position(high.weight)
    mix = (axis_position(weight) - start) / (end - start)
    return values[low.name] + (values[high.name] - values[low.name]) * mix


def needed_clearance(weight):
    return blend(weight, MARK_CLEARANCE)


@cache
def mark_floor(model):
    return accents.mark_floor(model.isupper())


def clipped(segment, floor):
    (x0, y0), (x1, y1) = segment
    if y0 < floor and y1 < floor:
        return None
    if y0 >= floor and y1 >= floor:
        return segment
    t = (floor - y0) / (y1 - y0)
    crossing = (x0 + (x1 - x0) * t, floor)
    return ((x0, y0), crossing) if y0 >= floor else (crossing, (x1, y1))


@cache
def ink_above(style, weight, name, floor):
    segments = []
    for polygon in outline_polygons(outline_font(style, weight).getGlyphSet(), name):
        for segment in zip(polygon, polygon[1:] + polygon[:1]):
            kept = clipped(segment, floor)
            if kept:
                segments.append(kept)
    return segments


def point_to_segment(point, segment):
    (x0, y0), (x1, y1) = segment
    dx, dy = x1 - x0, y1 - y0
    length = dx * dx + dy * dy
    t = 0 if length == 0 else max(0, min(1, ((point[0] - x0) * dx + (point[1] - y0) * dy) / length))
    return math.hypot(point[0] - x0 - t * dx, point[1] - y0 - t * dy)


def nearest_ink(style, weight, left, right, kern, left_floor, right_floor):
    offset = outline_font(style, weight)["hmtx"][left][0] + kern
    left_ink = ink_above(style, weight, left, left_floor)
    right_ink = [
        ((x0 + offset, y0), (x1 + offset, y1))
        for (x0, y0), (x1, y1) in ink_above(style, weight, right, right_floor)
    ]
    if not left_ink or not right_ink:
        return None
    one_way = min(point_to_segment(segment[0], other) for segment in left_ink for other in right_ink)
    other_way = min(point_to_segment(segment[0], other) for segment in right_ink for other in left_ink)
    return min(one_way, other_way)


def has_mark_above(glyph, model):
    family = [model] + [name for name, kin in kern_like().items() if kin == model]
    model_codes = {code for name in family for code in codepoints(name)}
    for code in codepoints(glyph):
        letters = unicodedata.normalize("NFD", chr(code))
        marks = letters[1:]
        if ord(letters[0]) in model_codes and marks and all(unicodedata.combining(mark) in MARKS_ABOVE for mark in marks):
            return True
    return False


def cleared_on_purpose(left, right, glyph, kern, model_kern):
    from plutto.features import CLEARANCE

    partner = kern_like().get(right, right)
    return left == glyph and kern > model_kern and any(glyph in lefts and partner in rights for lefts, rights, _ in CLEARANCE)


def kern_like_problem(style, weight, left, right, glyph, model, kern, model_kern):
    if kern == model_kern or cleared_on_purpose(left, right, glyph, kern, model_kern):
        return None
    pair = f"{left} {right} kerns {kern} where the model pair kerns {model_kern}"
    if not has_mark_above(glyph, model):
        return pair
    if kern < model_kern:
        return f"{pair}: tighter than the model"
    needed = needed_clearance(weight)
    floor = mark_floor(model)
    left_floor, right_floor = (floor, floor - needed) if left == glyph else (floor - needed, floor)
    distance = nearest_ink(style, weight, left, right, kern, left_floor, right_floor)
    if distance is None:
        return f"{pair}: eased, but no ink comes near the mark above {model}"
    if distance < needed - CLEARANCE_SLACK - (0 if weight in MASTER_WEIGHTS else INTERPOLATED_SLACK):
        return f"{pair}: eased, but leaves only {distance:.0f} between the mark and its neighbour where {needed:.0f} is needed"
    tighter = kern - LOOSENESS_STEP
    if tighter < model_kern or weight not in MASTER_WEIGHTS:
        return None
    closer = nearest_ink(style, weight, left, right, tighter, left_floor, right_floor)
    if closer >= needed + CLEARANCE_SLACK:
        return f"{pair}: eased further than needed: {tighter} would still leave {closer:.0f} where {needed:.0f} is needed"
    return None


def built_name(name):
    return production_name(name)


BUILT_ORDER = [built_name(name) for name in GLYPHS]


def font_path(style, suffix=".ttf"):
    return built()[0] / f"{FAMILY}-{style}{suffix}"


def unhinted_path(style):
    return built()[0] / UNHINTED_FOLDER / f"{FAMILY}-{style}.ttf"


@cache
def font(style, suffix=".ttf"):
    return TTFont(font_path(style, suffix))


def static_fonts(styles=ALL_STYLES):
    return [(style, font(style)) for style in styles]


def master_fonts(styles=ALL_STYLES):
    return [(style, instance(style_weight(style), variable_for(style))) for style in styles]


def variable_fonts():
    return [(variable, font(variable)) for variable in VARIABLES]


def all_fonts():
    return static_fonts() + variable_fonts()


def codepoints(name):
    return [code for code, glyph in font(STYLES[0]).getBestCmap().items() if glyph == name]


def base_name(name):
    return name.split(".")[0]


def is_blank(name):
    base = base_name(name)
    if base == "space":
        return True
    codes = codepoints(base) if base in GLYPHS else []
    return bool(codes) and all(unicodedata.category(chr(code)) in BLANK_CATEGORIES or code in DEFAULT_IGNORABLE for code in codes)


def is_zero_width(name):
    codes = codepoints(name) if name in GLYPHS else []
    return bool(codes) and all(unicodedata.category(chr(code)) in FORMAT_CATEGORIES for code in codes)


def is_combining(name):
    base = base_name(name)
    if base.endswith("comb"):
        return True
    codes = codepoints(base) if base in GLYPHS else []
    return bool(codes) and all(unicodedata.category(chr(code)) in COMBINING_CATEGORIES for code in codes)


def hb_shape(path, text_option, features, variations, language=None):
    command = [HB_SHAPE, "--output-format=json"]
    if language:
        command.append(f"--language={language}")
    if features:
        command.append(f"--features={features}")
    if variations:
        command.append(f"--variations={variations}")
    command += [str(path), text_option]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def shape(path, text, features=None, variations=None, language=None):
    return hb_shape(path, f"--text={text}", features, variations, language)[0]


def shape_lines(path, texts, features=None, variations=None):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt") as lines:
        lines.write("\n".join(texts) + "\n")
        lines.flush()
        runs = hb_shape(path, f"--text-file={lines.name}", features, variations)
    if len(runs) != len(texts):
        raise AssertionError(f"hb-shape returned {len(runs)} runs for {len(texts)} lines")
    return runs


def names(run):
    return [item["g"] for item in run]


def advances(run):
    return [item["ax"] for item in run]
