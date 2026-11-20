import itertools
import math
import sys
import unicodedata
from pathlib import Path

import numpy

from fontTools import varLib
from fontTools.cu2qu import curves_to_quadratic
from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
    SourceDescriptor,
)
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.roundTools import otRound
from fontTools.otlLib.builder import buildStatTable
from fontTools.otlLib.maxContextCalc import maxCtxFont
from fontTools.otlLib.optimize import compact as compact_layout
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent, GlyphCoordinates
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables.O_S_2f_2 import Panose
from fontTools.ttLib.tables.ttProgram import Program
from fontTools.varLib.instancer import instantiateVariableFont

from .extremes import beside_extreme, with_extremes, with_quad_extremes
from .features import feature_text
from .glyphs import GLYPHS, render
from .hinting import AUTOHINTER, HINTED_WHOLE, LIFTED_MARKS, LIFTED_STACKS, LIFTED_TOPS, UNHINTED_FOLDER, find_autohinter, hint_statics
from .masters import (
    ASC,
    BETWEEN_STATICS,
    CAP,
    DESC,
    DEFAULT,
    DESIGN_SPACES,
    FAMILY,
    INSTANCES,
    ITALIC_BETWEEN_STATICS,
    LINE_ASCENT,
    LINE_DESCENT,
    MASTERS,
    UNITS,
    XH,
    default_of,
    line_heights,
    style_name,
    weight_name,
)
from .oblique import ORIGIN

CURVE_ERROR = 1.0
FLOAT_PLACES = 6
OVERLAP_SIMPLE = 0x40
ROUND_TO_GRID = 0x4
OVERLAP_COMPOUND = 0x400
COMPONENT_SLACK = {False: 0, True: 1}
VERSION = "1.000"
SAMPLE_TEXT = "Quick zephyrs blow, vexing daft Jim. 0123456789"
VENDOR = "PLTO"
COPYRIGHT = "Copyright 2026 Pluto Labs LLC"
LICENSE_URL = "https://openfontlicense.org"
LICENSE = f"This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: {LICENSE_URL}"
VARIABLE_FAMILY = f"{FAMILY} Variable"
VARIABLE_PS_PREFIX = f"{FAMILY}Variable"
VARIABLE_FILES = {False: "Variable", True: "Italic-Variable"}
ITALIC_AXIS = {False: (0, "Roman"), True: (1, "Italic")}
USE_TYPO_METRICS = 0x80
FS_ITALIC = 0x01
FS_BOLD = 0x20
FS_REGULAR = 0x40
MAC_BOLD = 0x1
MAC_ITALIC = 0x2
LATIN_TEXT = 2
ELIDABLE = 0x2
PANOSE_WEIGHTS = {300: 3, 400: 5, 500: 6, 600: 7, 700: 8, 800: 9, 900: 10}
PANOSE_CLASSES = {
    "bSerifStyle": 11,
    "bProportion": 4,
    "bContrast": 2,
    "bStrokeVariation": 2,
    "bArmStyle": 2,
    "bMidline": 2,
    "bXHeight": 4,
}
PANOSE_NORMAL_CONTACT = 2
PANOSE_OBLIQUE_CONTACT = 9
STATIC_NAME_IDS = {"familyName": 1, "styleName": 2, "uniqueFontIdentifier": 3, "fullName": 4, "psName": 6, "typographicFamily": 16, "typographicSubfamily": 17}
VARIABLE_ONLY_NAME_IDS = (25,)
BETWEEN = {False: BETWEEN_STATICS, True: ITALIC_BETWEEN_STATICS}
LINKED_WEIGHTS = {"Regular", "Bold"}
SMART_DROPOUT = b"\xb8\x01\xff\x85\xb0\x04\x8d"
SMOOTH_AT_ALL_SIZES = {0xFFFF: 0x000F}
HINTING_SKIPPED = f"hinting skipped: {AUTOHINTER} is not on the PATH, so the static fonts ship unhinted"
OVERLAPS_KEPT = "overlap removal skipped: skia-pathops is not installed, so the static fonts keep overlapping contours"
NO_BREAK_SPACE = 0xA0
OHM = 0x2126
TURNED_COMMA_LETTER = 0x2BB
APOSTROPHE_LETTER = 0x2BC
GREEK_QUESTION = 0x37E
CYRILLIC_AE = 0x4D4
NON_BREAKING_HYPHEN = 0x2011
HYPHEN = 0x2010
CYRILLIC_SMALL_AE = 0x4D5
REVERSED_ZE = 0x510
KURDISH_QA = 0x51A
KURDISH_WE = 0x51C
MODIFIER_PRIME = 0x2B9
CMAP_ALIASES = {
    NO_BREAK_SPACE: "space",
    OHM: "Omega",
    TURNED_COMMA_LETTER: "quoteleft",
    APOSTROPHE_LETTER: "quoteright",
    GREEK_QUESTION: "semicolon",
    CYRILLIC_AE: "AE",
    NON_BREAKING_HYPHEN: "hyphen",
    HYPHEN: "hyphen",
    CYRILLIC_SMALL_AE: "ae",
    REVERSED_ZE: "Eopen",
    REVERSED_ZE + 1: "eopen",
    KURDISH_QA: "Q",
    KURDISH_QA + 1: "q",
    KURDISH_WE: "W",
    KURDISH_WE + 1: "w",
    MODIFIER_PRIME: "uni0374",
}
SCRIPTS = "Latn, Grek, Cyrl"
NOTDEF = ".notdef"
BASE_GLYPH = 1
LIGATURE_GLYPH = 2
MARK_GLYPH = 3
COMPONENT_GLYPH = 4
KEPT_CLASSES = {LIGATURE_GLYPH, COMPONENT_GLYPH}
COMBINING = {"Mn", "Me"}
GDEF_VERSION = 0x00010000
MARK_TO_BASE, MARK_TO_LIGATURE, MARK_TO_MARK, EXTENSION = 4, 5, 6, 9
LIGATURE_SUBSTITUTION, SUBSTITUTION_EXTENSION = 4, 7
KEPT_OUTLINES = HINTED_WHOLE | {name for table in (LIFTED_MARKS, LIFTED_STACKS, LIFTED_TOPS) for marks in table.values() for name in marks}
LOOSE_PARTS = 2
LONGEST_NAME = 31
SNAP_REACH = 2
SLIVER = 4.0
NEAR_SMOOTH = math.radians(12)
IMPLIED_REACH = 1.0
NUDGES = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
NUDGE_PRICE = 1e-4
KINK_FROM = math.radians(2)
LINE_KINK_FROM = math.radians(1)
LEAN_REACH = 3
LEAN_RATIO = 20
KINK_UP_TO = math.radians(12)
KINK_GAP = 3.0
STUB_LENGTH = 7.0
LINE_STUB = 2.0
SHARP_STUB = math.radians(45)
SPIKE = math.radians(165)
COLINEAR_REACH = 1.5
STUB_KEEP = 4
SQUARE_REACH = 3
SQUARE_RATIO = 10
SQUARE_EDGE = 8
TALLEST_CAPITAL = "Abreveacute"
LAYOUT_COMPACTION = 9
FAINT_KERN = 2
PRODUCTION_NAMES = {name: f"uni{code:04X}" for name, (code, _) in GLYPHS.items() if len(name) > LONGEST_NAME and code is not None}


def production_name(name):
    return PRODUCTION_NAMES.get(name, name)


def renamed(path):
    font = TTFont(path)
    font.setGlyphOrder([production_name(name) for name in font.getGlyphOrder()])
    font["post"].mapping = {}
    font.save(path)


def snap(point):
    return (otRound(round(point[0], FLOAT_PLACES)), otRound(round(point[1], FLOAT_PLACES)))


def compact(style):
    return style.replace(" ", "")


def draw_master(name, master):
    try:
        return render(name, master)
    except Exception as error:
        raise RuntimeError(f"{name} ({master.name}): {type(error).__name__}: {error}") from error


def draw(name, masters=MASTERS):
    drawn = [draw_master(name, master) for master in masters]
    outlines = [[contour.oriented() for contour in glyph.contours] for glyph in drawn]
    counts = {len(contours) for contours in outlines}
    if len(counts) != 1:
        raise ValueError(f"{name}: masters disagree on contour count")
    return with_extremes(outlines), [glyph.advance for glyph in drawn]


def quadratic(name, outlines, masters=MASTERS):
    pens = [TTGlyphPen(None) for _ in outlines]
    for group in zip(*outlines):
        shapes = {tuple(len(segment) for segment in contour.segments) for contour in group}
        if len(shapes) != 1:
            raise ValueError(f"{name}: masters disagree on contour structure")
        here = [contour.start for contour in group]
        for pen, point in zip(pens, here):
            pen.moveTo(snap(point))
        for segments in zip(*[contour.segments for contour in group]):
            if len(segments[0]) == 1:
                for pen, segment in zip(pens, segments):
                    pen.lineTo(snap(segment[0]))
            else:
                curves = [(start, *segment) for start, segment in zip(here, segments)]
                splines = curves_to_quadratic(curves, [CURVE_ERROR] * len(curves))
                for pen, spline in zip(pens, splines):
                    pen.qCurveTo(*[snap(point) for point in spline[1:]])
            here = [segment[-1] for segment in segments]
        for pen in pens:
            pen.closePath()
    glyphs = [settled(pen.glyph(), line_heights(master)) for pen, master in zip(pens, masters)]
    layouts = {(tuple(glyph.endPtsOfContours), bytes(glyph.flags)) for glyph in glyphs if glyph.numberOfContours}
    if len(layouts) > 1:
        raise ValueError(f"{name}: masters disagree on point layout")
    for glyph in glyphs:
        if glyph.numberOfContours > 0:
            glyph.flags[0] |= OVERLAP_SIMPLE
    return glyphs


def settled(glyph, heights):
    if glyph.numberOfContours <= 0:
        return glyph
    lines, box = line_marks(glyph, heights), box_of(glyph)
    points = []
    for contour in contours_of(glyph):
        for index in range(len(contour)):
            if rounding_kink(contour, index):
                straightened(contour, index, lines, box)
        trued(contour, heights)
        points += [point for point, _ in contour]
    glyph.coordinates = GlyphCoordinates(points)
    return glyph


def trued(contour, heights):
    count = len(contour)
    for index in range(count):
        following = (index + 1) % count
        (here, here_on), (after, after_on) = contour[index], contour[following]
        if not (here_on and after_on):
            continue
        for axis in (0, 1):
            off = abs(after[axis] - here[axis])
            if not 0 < off <= SQUARE_REACH or abs(after[1 - axis] - here[1 - axis]) < 2 * SQUARE_RATIO * off:
                continue
            fixed = [axis == 1 and point[1] in heights for point in (here, after)]
            if all(fixed):
                continue
            mover, target = (index, after) if fixed[1] or not contour[index - 1][1] and contour[(following + 1) % count][1] else (following, here)
            point = list(contour[mover][0])
            point[axis] = target[axis]
            contour[mover] = (tuple(point), 1)


def rounding_kink(contour, index):
    count = len(contour)
    before, after = contour[index - 1][1], contour[(index + 1) % count][1]
    if not contour[index][1] or before and after:
        return False
    least = LINE_KINK_FROM if before or after else KINK_FROM
    return least <= bend_at(contour, index) < KINK_UP_TO


def crowded(contour, mover, original):
    count = len(contour)
    for neighbour in (mover - 1, mover + 1):
        neighbour %= count
        gap = math.dist(contour[mover][0], contour[neighbour][0])
        before = math.dist(original.get(mover, contour[mover])[0], original.get(neighbour, contour[neighbour])[0])
        if gap < min(KINK_GAP, before):
            return True
    return False


def straightened(contour, index, lines, box):
    count = len(contour)
    movers = [index] + [
        neighbour % count
        for neighbour in (index - 1, index + 1)
        if not contour[neighbour % count][1] and not level_pair(contour, neighbour % count, 2 * neighbour - index)
    ]
    if on_edge(contour[index][0], box):
        movers.remove(index)
    watched = {index}
    for mover in movers:
        for neighbour in (mover - 1, mover + 1):
            if contour[neighbour % count][1] and bend_at(contour, neighbour % count) < NEAR_SMOOTH:
                watched.add(neighbour % count)
    original = {mover: contour[mover] for mover in movers}

    def cost():
        return sum(bend_at(contour, watch) for watch in watched)

    best, best_cost = None, cost()
    for moves in itertools.product(NUDGES, repeat=len(movers)):
        placed = {mover: (original[mover][0][0] + dx, original[mover][0][1] + dy) for mover, (dx, dy) in zip(movers, moves)}
        if not all(clear_of_lines(placed[mover], original[mover][0], lines) and within(placed[mover], box) and keeps_box(placed[mover], original[mover][0], box) and keeps_axes(contour, mover, original[mover], placed[mover]) for mover in movers):
            continue
        for mover in movers:
            contour[mover] = (placed[mover], original[mover][1])
        if any(crowded(contour, mover, original) for mover in movers):
            continue
        spent = cost() + NUDGE_PRICE * sum(abs(dx) + abs(dy) for dx, dy in moves)
        if spent < best_cost:
            best, best_cost = placed, spent
    for mover in movers:
        contour[mover] = (best[mover] if best else original[mover][0], original[mover][1])


def keeps_box(point, original, box):
    return all(point[axis] == original[axis] for axis in (0, 1) if original[axis] in (box[axis], box[axis + 2]))


def keeps_axes(contour, mover, original, point):
    here, on = original
    if not on:
        return True
    count = len(contour)
    for neighbour in (contour[mover - 1], contour[(mover + 1) % count]):
        if neighbour[1] and any(neighbour[0][axis] == here[axis] and point[axis] != here[axis] for axis in (0, 1)):
            return False
        if neighbour[1] and leans(neighbour[0], point) and not leans(neighbour[0], here):
            return False
    return True


def leans(a, b):
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    return any(1 <= small <= LEAN_REACH and big >= LEAN_RATIO * small for small, big in ((dy, dx), (dx, dy)))


def point_contours(glyph):
    if glyph.numberOfContours <= 0:
        return []
    points = numpy.array(glyph.coordinates, dtype=float)
    found, start = [], 0
    for end in glyph.endPtsOfContours:
        found.append((points[start : end + 1], bytes(flag & 1 for flag in glyph.flags[start : end + 1])))
        start = end + 1
    return found


def shape_key(contour):
    return contour[1]


def offset_of(contours, own, start, slack):
    moves = numpy.concatenate([contours[start + index][0] - points for index, (points, _) in enumerate(own)])
    offset = numpy.round(moves.mean(axis=0))
    if numpy.abs(moves - offset).max() > slack:
        return None
    return int(offset[0]), int(offset[1])


def fitted(name, per_master, start, masters_contours, slack):
    own = [contours[name] for contours in masters_contours]
    first = masters_contours[0][name]
    reference = per_master[0]
    if start + len(first) > len(reference):
        return None
    if any(shape_key(contour) != shape_key(reference[start + index]) for index, contour in enumerate(first)):
        return None
    offsets = [offset_of(contours, mine, start, slack) for contours, mine in zip(per_master, own)]
    return None if None in offsets else offsets


def decomposition(name, masters_contours, index, allowed, slack):
    per_master = [contours[name] for contours in masters_contours]
    found, start = [], 0
    while start < len(per_master[0]):
        for candidate in index.get(shape_key(per_master[0][start]), []):
            if candidate == name or candidate not in allowed:
                continue
            offsets = fitted(candidate, per_master, start, masters_contours, slack)
            if offsets is not None:
                found.append((candidate, offsets))
                start += len(masters_contours[0][candidate])
                break
        else:
            return None
    return found


def lettered(name):
    code = GLYPHS[name][0]
    return code is not None and unicodedata.category(chr(code)).startswith("L")


def decompositions(order, masters_contours, allowed, targets, slack):
    rank = {name: place for place, name in enumerate(order)}
    index = {}
    for name in sorted(order, key=lambda name: (-len(masters_contours[0][name]), rank[name])):
        if masters_contours[0][name]:
            index.setdefault(shape_key(masters_contours[0][name][0]), []).append(name)
    found = {}
    for name in targets:
        if not masters_contours[0][name] or name in KEPT_OUTLINES:
            continue
        parts = decomposition(name, masters_contours, index, allowed, slack)
        if parts and slack and (len(parts) > LOOSE_PARTS or not lettered(parts[0][0])):
            parts = decomposition(name, masters_contours, index, allowed, 0)
        if parts and (len(parts) > 1 or rank[parts[0][0]] < rank[name]):
            found[name] = parts
    return found


def overlapping(parts, masters_contours):
    for master, contours in enumerate(masters_contours):
        boxes = []
        for name, offsets in parts:
            points = numpy.concatenate([points for points, _ in contours[name]]) + offsets[master]
            boxes.append((points.min(axis=0), points.max(axis=0)))
        for first in range(len(boxes)):
            for second in range(first + 1, len(boxes)):
                if (boxes[first][0] <= boxes[second][1]).all() and (boxes[second][0] <= boxes[first][1]).all():
                    return True
    return False


def composite(parts, master, overlap):
    glyph = Glyph()
    glyph.numberOfContours = -1
    glyph.components = []
    for number, (name, offsets) in enumerate(parts):
        component = GlyphComponent()
        component.glyphName = name
        component.x, component.y = offsets[master]
        component.flags = ROUND_TO_GRID | (OVERLAP_COMPOUND if overlap and number == 0 else 0)
        glyph.components.append(component)
    return glyph


def composed(per_master, order, italic):
    slack = COMPONENT_SLACK[italic]
    masters_contours = [{name: point_contours(glyphs[name]) for name in order} for glyphs in per_master]
    found = decompositions(order, masters_contours, set(order), order, slack)
    atomic = {name for name in order if name not in found}
    found = decompositions(order, masters_contours, atomic, [name for name in order if name in found], slack)
    result = [dict(glyphs) for glyphs in per_master]
    for name, parts in found.items():
        overlap = overlapping(parts, masters_contours)
        for master, glyphs in enumerate(result):
            glyphs[name] = composite(parts, master, overlap)
    return result


def vertical_extent(glyph):
    if glyph.numberOfContours == 0:
        return None
    ys = [y for _, y in glyph.coordinates]
    return min(ys), max(ys)


def line_ascent(*per_master):
    tops = [vertical_extent(glyphs[TALLEST_CAPITAL])[1] for glyphs in per_master if TALLEST_CAPITAL in glyphs]
    return max([LINE_ASCENT, *tops])


def win_metrics(*per_master):
    top, bottom = LINE_ASCENT, LINE_DESCENT
    for glyphs in per_master:
        for glyph in glyphs.values():
            extent = vertical_extent(glyph)
            if extent:
                bottom = min(bottom, extent[0])
                top = max(top, extent[1])
    return top, -bottom


def stroke(glyphs, name, fallback):
    extent = vertical_extent(glyphs[name]) if name in glyphs else None
    if not extent:
        return fallback
    return extent[1], extent[1] - extent[0]


def panose(weight, italic=False):
    numbers = Panose()
    numbers.bFamilyType = LATIN_TEXT
    numbers.bWeight = PANOSE_WEIGHTS.get(weight, 0)
    for field, value in PANOSE_CLASSES.items():
        setattr(numbers, field, value)
    numbers.bLetterForm = PANOSE_OBLIQUE_CONTACT if italic else PANOSE_NORMAL_CONTACT
    return numbers


def script_meta():
    meta = newTable("meta")
    meta.data = {"dlng": SCRIPTS, "slng": SCRIPTS}
    return meta


def smooth_gasp():
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = dict(SMOOTH_AT_ALL_SIZES)
    return gasp


def dropout_control():
    prep = newTable("prep")
    prep.program = Program()
    prep.program.fromBytecode(SMART_DROPOUT)
    return prep


def static_names(master):
    names = {
        "copyright": COPYRIGHT,
        "licenseDescription": LICENSE,
        "licenseInfoURL": LICENSE_URL,
        "familyName": FAMILY,
        "styleName": master.name,
        "uniqueFontIdentifier": f"{VERSION};{VENDOR};{FAMILY}-{compact(master.name)}",
        "fullName": f"{FAMILY} {master.name}",
        "version": f"Version {VERSION}",
        "psName": f"{FAMILY}-{compact(master.name)}",
        "sampleText": SAMPLE_TEXT,
    }
    weight = weight_name(master)
    if weight not in LINKED_WEIGHTS:
        names["familyName"] = f"{FAMILY} {weight}"
        names["styleName"] = style_name("Regular", master.italic)
        names["typographicFamily"] = FAMILY
        names["typographicSubfamily"] = master.name
    return names


def style_bits(master):
    bold = weight_name(master) == "Bold"
    selection = USE_TYPO_METRICS
    if bold:
        selection |= FS_BOLD
    if master.italic:
        selection |= FS_ITALIC
    if not bold and not master.italic:
        selection |= FS_REGULAR
    mac = (MAC_BOLD if bold else 0) | (MAC_ITALIC if master.italic else 0)
    return selection, mac


def caret_slope(master):
    if not master.slant:
        return {}
    return {
        "caretSlopeRise": UNITS,
        "caretSlopeRun": otRound(UNITS * master.slope),
        "caretOffset": -otRound(master.slope * ORIGIN),
    }


def combining_marks(order, cmap):
    coded = {name for code, name in cmap.items() if unicodedata.category(chr(code)) in COMBINING}
    return {name for name in order if name in coded or name.split(".")[0] in coded}


def lookup_subtables(lookup, extension=EXTENSION):
    for subtable in lookup.SubTable:
        if lookup.LookupType == extension:
            yield subtable.ExtensionLookupType, subtable.ExtSubTable
        else:
            yield lookup.LookupType, subtable


def positioned_marks(font):
    if "GPOS" not in font or not font["GPOS"].table.LookupList:
        return set()
    found = set()
    for lookup in font["GPOS"].table.LookupList.Lookup:
        for kind, subtable in lookup_subtables(lookup):
            if kind in (MARK_TO_BASE, MARK_TO_LIGATURE):
                found.update(subtable.MarkCoverage.glyphs)
            elif kind == MARK_TO_MARK:
                found.update(subtable.Mark1Coverage.glyphs)
                found.update(subtable.Mark2Coverage.glyphs)
    return found


def ligatures(font):
    if "GSUB" not in font or not font["GSUB"].table.LookupList:
        return set()
    found = set()
    for lookup in font["GSUB"].table.LookupList.Lookup:
        for kind, subtable in lookup_subtables(lookup, SUBSTITUTION_EXTENSION):
            if kind == LIGATURE_SUBSTITUTION:
                found.update(ligature.LigGlyph for group in subtable.ligatures.values() for ligature in group)
    return found


def declared_classes(font):
    classes = getattr(font["GDEF"].table, "GlyphClassDef", None) if "GDEF" in font else None
    return dict(classes.classDefs) if classes else {}


def glyph_classes(font):
    order = font.getGlyphOrder()
    declared = declared_classes(font)
    marks = combining_marks(order, font.getBestCmap()) | positioned_marks(font)
    marks |= {name for name, kind in declared.items() if kind == MARK_GLYPH}
    kept = {name: kind for name, kind in declared.items() if kind in KEPT_CLASSES}
    kept.update({name: LIGATURE_GLYPH for name in ligatures(font)})
    return {name: MARK_GLYPH if name in marks else kept.get(name, BASE_GLYPH) for name in order if name != NOTDEF}


def classify_glyphs(font):
    if "GDEF" not in font:
        table = otTables.GDEF()
        table.Version = GDEF_VERSION
        table.AttachList = None
        table.LigCaretList = None
        table.MarkAttachClassDef = None
        font["GDEF"] = newTable("GDEF")
        font["GDEF"].table = table
    classes = otTables.GlyphClassDef()
    classes.classDefs = glyph_classes(font)
    font["GDEF"].table.GlyphClassDef = classes


def build_static(master, order, cmap, glyphs, advances, win=None, underline=None, ascent=None):
    win = win or win_metrics(glyphs)
    ascent = ascent or line_ascent(glyphs)
    underline = underline or stroke(glyphs, "underscore", (LINE_DESCENT // 2, otRound(master.bar)))
    builder = FontBuilder(UNITS, isTTF=True)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    table = builder.font["glyf"]
    metrics = {}
    for name in order:
        if table[name].isComposite():
            table[name].recalcBounds(table)
        left = getattr(table[name], "xMin", 0) if table[name].numberOfContours else 0
        metrics[name] = (otRound(advances[name]), left)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=ascent, descent=LINE_DESCENT, lineGap=0, **caret_slope(master))
    builder.setupNameTable(static_names(master), mac=False)
    selection, mac_style = style_bits(master)
    strikeout_top, strikeout_size = stroke(glyphs, "hyphen", (XH // 2, otRound(master.bar)))
    script_size = otRound(UNITS * 0.65)
    builder.setupOS2(
        version=4,
        usWeightClass=master.weight,
        fsType=0,
        ySubscriptXSize=script_size,
        ySubscriptYSize=script_size,
        ySubscriptYOffset=otRound(UNITS * 0.075),
        ySuperscriptXSize=script_size,
        ySuperscriptYSize=script_size,
        ySuperscriptYOffset=otRound(UNITS * 0.35),
        yStrikeoutSize=strikeout_size,
        yStrikeoutPosition=strikeout_top,
        panose=panose(master.weight, master.italic),
        achVendID=VENDOR,
        fsSelection=selection,
        sTypoAscender=ascent,
        sTypoDescender=LINE_DESCENT,
        sTypoLineGap=0,
        usWinAscent=win[0],
        usWinDescent=win[1],
        sxHeight=XH,
        sCapHeight=CAP,
        usDefaultChar=0,
        usBreakChar=0x20,
    )
    os2 = builder.font["OS/2"]
    os2.recalcUnicodeRanges(builder.font)
    os2.recalcCodePageRanges(builder.font)
    builder.setupPost(
        italicAngle=-master.slant,
        isFixedPitch=0,
        underlinePosition=underline[0],
        underlineThickness=underline[1],
    )
    builder.addOpenTypeFeatures(feature_text(master))
    classify_glyphs(builder.font)
    os2.usMaxContext = maxCtxFont(builder.font)
    head = builder.font["head"]
    head.fontRevision = float(VERSION)
    head.macStyle = mac_style
    head.lowestRecPPEM = 6
    builder.font["gasp"] = smooth_gasp()
    builder.font["meta"] = script_meta()
    builder.font["prep"] = dropout_control()
    add_stat(builder.font, master.italic, [(weight_name(master), master.weight)])
    return builder.font


def add_stat(font, italic=False, instances=INSTANCES):
    default = DEFAULT.weight
    bold = next(weight for name, weight in INSTANCES if name == "Bold")
    values = []
    for name, weight in instances:
        value = {"value": weight, "name": name}
        if weight == default:
            value["flags"] = ELIDABLE
            value["linkedValue"] = bold
        values.append(value)
    slope_value, slope_name = ITALIC_AXIS[italic]
    slope = {"value": slope_value, "name": slope_name}
    if not italic:
        slope["flags"] = ELIDABLE
        slope["linkedValue"] = ITALIC_AXIS[True][0]
    axes = [
        {"tag": "wght", "name": "Weight", "ordering": 0, "values": values},
        {"tag": "ital", "name": "Italic", "ordering": 1, "values": [slope]},
    ]
    buildStatTable(font, axes, elidedFallbackName=style_name(DEFAULT.name, italic), macNames=False)


def identity_avar(tag):
    avar = newTable("avar")
    avar.segments = {tag: {-1.0: -1.0, 0.0: 0.0, 1.0: 1.0}}
    return avar


def variable_prefix(italic):
    return VARIABLE_PS_PREFIX + ("Italic" if italic else "")


def name_variable(font, italic=False):
    names = font["name"]
    style = style_name(DEFAULT.name, italic)
    for name_id in (1, 2, 3, 4, 6, 25):
        names.removeNames(nameID=name_id)
    names.setName(VARIABLE_FAMILY, 1, 3, 1, 0x409)
    names.setName(style, 2, 3, 1, 0x409)
    names.setName(f"{VERSION};{VENDOR};{VARIABLE_PS_PREFIX}-{compact(style)}", 3, 3, 1, 0x409)
    names.setName(f"{VARIABLE_FAMILY} {style}", 4, 3, 1, 0x409)
    names.setName(f"{VARIABLE_PS_PREFIX}-{compact(style)}", 6, 3, 1, 0x409)
    names.setName(variable_prefix(italic), 25, 3, 1, 0x409)
    names.removeNames(platformID=1)


def build_variable(paths, masters=MASTERS):
    italic = masters[0].italic
    default = default_of(masters)
    document = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.name = "Weight"
    axis.tag = "wght"
    axis.minimum = min(master.weight for master in masters)
    axis.default = default.weight
    axis.maximum = max(master.weight for master in masters)
    document.addAxis(axis)
    for master, path in zip(masters, paths):
        source = SourceDescriptor()
        source.font = TTFont(path)
        source.familyName = FAMILY
        source.styleName = master.name
        source.location = {"Weight": master.weight}
        document.addSource(source)
    for name, weight in INSTANCES:
        style = style_name(name, italic)
        instance = InstanceDescriptor()
        instance.familyName = VARIABLE_FAMILY
        instance.styleName = style
        instance.postScriptFontName = f"{VARIABLE_PS_PREFIX}-{compact(style)}"
        instance.location = {"Weight": weight}
        document.addInstance(instance)
    font, _, _ = varLib.build(document, exclude=["STAT"])
    name_variable(font, italic)
    font["avar"] = identity_avar(axis.tag)
    font["gasp"] = smooth_gasp()
    font["meta"] = script_meta()
    add_stat(font, italic)
    return font


def build_between(variable, master):
    font = instantiateVariableFont(TTFont(variable), {"wght": master.weight}, inplace=False)
    names = font["name"]
    for name_id in [*STATIC_NAME_IDS.values(), *VARIABLE_ONLY_NAME_IDS]:
        names.removeNames(nameID=name_id)
    for key, value in static_names(master).items():
        if key in STATIC_NAME_IDS:
            names.setName(value, STATIC_NAME_IDS[key], 3, 1, 0x409)
    del font["STAT"]
    names.removeUnusedNames(font)
    add_stat(font, master.italic, [(weight_name(master), master.weight)])
    selection, mac_style = style_bits(master)
    os2 = font["OS/2"]
    os2.usWeightClass = master.weight
    os2.fsSelection = selection
    os2.panose = panose(master.weight, master.italic)
    font["head"].macStyle = mac_style
    return font


def compress(path):
    font = TTFont(path)
    font.flavor = "woff2"
    target = path.with_suffix(".woff2")
    font.save(target)
    return target


def build_space(masters, order):
    per_master = [{} for _ in masters]
    advances = [{} for _ in masters]
    for name in order:
        outlines, widths = draw(name, masters)
        for index, glyph in enumerate(quadratic(name, outlines, masters)):
            per_master[index][name] = glyph
            advances[index][name] = widths[index]
    return per_master, advances


def build(directory):
    directory = Path(directory)
    unhinted = directory / UNHINTED_FOLDER
    unhinted.mkdir(parents=True, exist_ok=True)
    order = list(GLYPHS)
    cmap = {code: name for name, (code, _) in GLYPHS.items() if code is not None}
    for code, name in CMAP_ALIASES.items():
        cmap.setdefault(code, name)
    spaces = [build_space(masters, order) for masters in DESIGN_SPACES]
    win = win_metrics(*[glyphs for per_master, _ in spaces for glyphs in per_master])
    ascent = line_ascent(*[glyphs for per_master, _ in spaces for glyphs in per_master])
    spaces = [(composed(per_master, order, masters[0].italic), advances) for masters, (per_master, advances) in zip(DESIGN_SPACES, spaces)]
    default = MASTERS.index(DEFAULT)
    underline = stroke(spaces[0][0][default], "underscore", (LINE_DESCENT // 2, otRound(DEFAULT.bar)))
    sources, variables, heights = [], [], []
    for masters, (per_master, advances) in zip(DESIGN_SPACES, spaces):
        paths = []
        for index, master in enumerate(masters):
            font = build_static(master, order, cmap, per_master[index], advances[index], win, underline, ascent)
            path = unhinted / f"{FAMILY}-{compact(master.name)}.ttf"
            font.save(path)
            paths.append(path)
        variable = directory / f"{FAMILY}-{VARIABLE_FILES[masters[0].italic]}.ttf"
        build_variable(paths, masters).save(variable)
        for master in BETWEEN[masters[0].italic]:
            path = unhinted / f"{FAMILY}-{compact(master.name)}.ttf"
            build_between(variable, master).save(path)
            paths.append(path)
        sources += paths
        heights += [line_heights(master) for master in masters + BETWEEN[masters[0].italic]]
        variables.append(variable)
    for path in sources:
        compacted(path)
    for path in variables:
        compacted(path, variable=True)
    if not merge_overlaps(sources, heights):
        print(OVERLAPS_KEPT, file=sys.stderr)
    for path in sources + variables:
        renamed(path)
    statics = [directory / source.name for source in sources]
    if not hint_statics(list(zip(sources, statics)), find_autohinter()):
        print(HINTING_SKIPPED, file=sys.stderr)
    shipped = statics + variables
    written = shipped + [compress(path) for path in shipped] + sources
    for path in stale_outputs(directory, written):
        path.unlink()
        print(f"removed {path}, which this build no longer writes", file=sys.stderr)
    return written


def faint(record):
    value = record.Value1
    return record.Value2 is None and value is not None and set(vars(value)) == {"XAdvance"} and -FAINT_KERN <= value.XAdvance <= 0


def without_faint_pairs(font):
    for lookup in font["GPOS"].table.LookupList.Lookup:
        tables = [getattr(table, "ExtSubTable", table) for table in lookup.SubTable]
        last = tables[-1] if tables else None
        if not isinstance(last, otTables.PairPos) or last.Format != 1:
            continue
        kept = []
        for glyph, pairs in zip(last.Coverage.glyphs, last.PairSet):
            pairs.PairValueRecord = [record for record in pairs.PairValueRecord if not faint(record)]
            pairs.PairValueCount = len(pairs.PairValueRecord)
            if pairs.PairValueRecord:
                kept.append((glyph, pairs))
        last.Coverage.glyphs = [glyph for glyph, _ in kept]
        last.PairSet = [pairs for _, pairs in kept]
        last.PairSetCount = len(kept)


def compacted(path, variable=False):
    font = TTFont(path)
    if not variable:
        without_faint_pairs(font)
    compact_layout(font, LAYOUT_COMPACTION)
    font.save(path)


def merge_overlaps(paths, heights):
    try:
        from fontTools.ttLib.removeOverlaps import removeOverlaps
    except ImportError:
        return False
    for path, levels in zip(paths, heights):
        font = TTFont(path)
        table = font["glyf"]
        lines = {name: line_marks(table[name], levels) for name in font.getGlyphOrder() if table[name].numberOfContours > 0}
        edges = {name: axis_edges(table[name], table) for name in font.getGlyphOrder() if table[name].numberOfContours}
        removeOverlaps(font)
        for name in font.getGlyphOrder():
            if table[name].numberOfContours > 0:
                without_repeats(table[name])
                without_slivers(table[name])
                without_stubs(table[name], levels)
                if snapped(table[name], lines.get(name, {})):
                    without_repeats(table[name])
                smoothed_joins(table[name], lines.get(name, {}))
                squared(table[name], edges.get(name, ({}, {})))
                without_repeats(table[name])
                stored(table[name], [with_quad_extremes(contour) for contour in contours_of(table[name])])
                if snapped(table[name], lines.get(name, {})):
                    without_repeats(table[name])
        font.save(path)
    return True


def line_marks(glyph, heights):
    found = {}
    for contour in contours_of(glyph):
        for (here, _), (after, _) in zip(contour, contour[1:] + contour[:1]):
            if here[1] in heights:
                spans = found.setdefault(here[1], [])
                spans.append((here[0], here[0]))
                if after[1] == here[1]:
                    spans.append((min(here[0], after[0]), max(here[0], after[0])))
    return found


def axis_edges(glyph, table):
    coordinates, ends, flags = glyph.getCoordinates(table)
    found = ({}, {})
    start = 0
    for end in ends:
        ring = [(tuple(coordinates[index]), flags[index] & 1) for index in range(start, end + 1)]
        for (here, here_on), (after, after_on) in zip(ring, ring[1:] + ring[:1]):
            if not (here_on and after_on) or math.dist(here, after) < SQUARE_EDGE:
                continue
            for axis in (0, 1):
                if here[axis] == after[axis]:
                    found[axis].setdefault(here[axis], []).append(tuple(sorted((here[1 - axis], after[1 - axis]))))
        start = end + 1
    return found


def on_edge_line(point, axis, edges):
    return any(low - SQUARE_REACH <= point[1 - axis] <= high + SQUARE_REACH for low, high in edges[axis].get(point[axis], ()))


def squared(glyph, edges):
    contours = list(contours_of(glyph))
    moved = False
    for contour in contours:
        count = len(contour)
        for index in range(count):
            (here, here_on), (after, after_on) = contour[index], contour[(index + 1) % count]
            if not (here_on and after_on):
                continue
            for axis in (0, 1):
                off = abs(after[axis] - here[axis])
                if not 0 < off <= SQUARE_REACH or abs(after[1 - axis] - here[1 - axis]) < SQUARE_RATIO * off:
                    continue
                anchored = [on_edge_line(point, axis, edges) for point in (here, after)]
                if anchored.count(True) != 1:
                    continue
                mover = (index + 1) % count if anchored[0] else index
                target = after if anchored[1] else here
                point = list(contour[mover][0])
                point[axis] = target[axis]
                contour[mover] = (tuple(point), 1)
                moved = True
    if moved:
        stored(glyph, contours)
    return moved


def snapped(glyph, lines):
    moved = False
    points = list(glyph.coordinates)
    for index, (x, y) in enumerate(points):
        for line, spans in lines.items():
            if 0 < abs(y - line) <= SNAP_REACH and any(low - SNAP_REACH <= x <= high + SNAP_REACH for low, high in spans):
                points[index] = (x, line)
                moved = True
                break
    if moved:
        glyph.coordinates = GlyphCoordinates(points)
    return moved


def contours_of(glyph):
    start = 0
    for end in glyph.endPtsOfContours:
        yield [(tuple(glyph.coordinates[index]), glyph.flags[index] & 1) for index in range(start, end + 1)]
        start = end + 1


def settle_repeat(contour):
    for index, (point, on) in enumerate(contour):
        before, before_on = contour[index - 1]
        if point != before:
            continue
        if on and before_on:
            del contour[index]
        elif not on and not before_on:
            contour[index - 1] = (point, 1)
            del contour[index]
        else:
            loose = index if not on else index - 1
            other, other_on = contour[(loose + 1) % len(contour)] if loose == index else contour[loose - 1]
            if other_on:
                del contour[loose]
            else:
                contour[loose] = (tuple(otRound((a + b) / 2) for a, b in zip(point, other)), 1)
        return True
    return False


def turn_at(before, here, after):
    first = (here[0] - before[0], here[1] - before[1])
    second = (after[0] - here[0], after[1] - here[1])
    if first == (0, 0) or second == (0, 0):
        return 0.0
    return abs(math.atan2(first[0] * second[1] - first[1] * second[0], first[0] * second[0] + first[1] * second[1]))


def stub_points(contour, heights):
    count = len(contour)
    for index in range(count):
        (first, first_on), (middle, middle_on), (last, last_on) = (contour[(index + step) % count] for step in range(3))
        if not first_on:
            continue
        if middle_on:
            span, last, reach = (index, index + 1), middle, LINE_STUB
        elif last_on:
            span, reach = (index, index + 1, index + 2), STUB_LENGTH
        else:
            continue
        if math.dist(first, middle) + (math.dist(middle, last) if len(span) == 3 else 0) >= reach:
            continue
        before, after = contour[index - 1][0], contour[(span[-1] + 1) % count][0]
        turns = (turn_at(before, first, last), turn_at(first, last, after))
        if max(turns) < SHARP_STUB or min(turns) > SHARP_STUB:
            continue
        loose, corner, dropped = (first, last, span[:-1]) if turns[0] < turns[1] else (last, first, span[1:])
        if loose[1] in heights or turn_at(before, corner, after) > max(SPIKE, *turns):
            continue
        return {step % count for step in dropped}
    return None


def off_line(point, start, end):
    along = (end[0] - start[0], end[1] - start[1])
    length = math.hypot(*along)
    if not length:
        return math.inf
    return abs(along[0] * (point[1] - start[1]) - along[1] * (point[0] - start[0])) / length


def colinear_points(contour):
    count = len(contour)
    for index in range(count):
        (before, before_on), (here, here_on), (after, after_on) = (contour[(index + step) % count] for step in (-1, 0, 1))
        if not (before_on and here_on and after_on):
            continue
        if (after[0] - here[0]) * (here[0] - before[0]) + (after[1] - here[1]) * (here[1] - before[1]) <= 0:
            continue
        if off_line(here, before, after) < COLINEAR_REACH:
            return {index}
    return None


def without_stubs(glyph, heights):
    contours = list(contours_of(glyph))
    changed = False
    for contour in contours:
        while len(contour) > STUB_KEEP:
            dropped = stub_points(contour, heights) or colinear_points(contour)
            if dropped is None:
                break
            for index in sorted(dropped, reverse=True):
                del contour[index]
            changed = True
    if changed:
        stored(glyph, contours)
    return changed


def without_repeats(glyph):
    contours = list(contours_of(glyph))
    for contour in contours:
        while len(contour) > 1 and settle_repeat(contour):
            pass
    stored(glyph, contours)


def stored(glyph, contours):
    points, flags, ends = [], [], []
    for contour in contours:
        if len(contour) < 3:
            continue
        points += [point for point, _ in contour]
        flags += [on for _, on in contour]
        ends.append(len(points) - 1)
    glyph.coordinates = GlyphCoordinates(points)
    glyph.flags = bytearray(flags)
    glyph.endPtsOfContours = ends
    glyph.numberOfContours = len(ends)


def sliver_length(contour, first, last):
    length, index = 0.0, first
    while index != last:
        following = (index + 1) % len(contour)
        length += math.dist(contour[index][0], contour[following][0])
        index = following
    return length


def box_of(glyph):
    xs, ys = [x for x, _ in glyph.coordinates], [y for _, y in glyph.coordinates]
    return min(xs), min(ys), max(xs), max(ys)


def on_edge(point, box):
    return point[0] in (box[0], box[2]) or point[1] in (box[1], box[3])


def holds_edge(point, kept, box):
    sides = [(axis, value) for axis, value in ((0, box[0]), (1, box[1]), (0, box[2]), (1, box[3])) if point[axis] == value]
    return all(any(other[axis] == value for other in kept) for axis, value in sides)


def within(point, box):
    return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]


def settle_sliver(contour, box):
    count = len(contour)
    corners = [index for index, (_, on) in enumerate(contour) if on]
    if len(corners) < 3:
        return False
    for position, first in enumerate(corners):
        last = corners[(position + 1) % len(corners)]
        if sliver_length(contour, first, last) >= SLIVER:
            continue
        line_before = contour[first - 1][1]
        line_after = contour[(last + 1) % count][1]
        between = {(first + step) % count for step in range(1, (last - first) % count)}
        if line_before and not line_after:
            between.add(last)
        elif line_after and not line_before:
            between.add(first)
        else:
            between |= {first, last}
        kept = [point for index, (point, _) in enumerate(contour) if index not in between]
        if any(on_edge(contour[index][0], box) and not holds_edge(contour[index][0], kept, box) for index in between):
            continue
        if first in between and last in between:
            middle = tuple(otRound((a + b) / 2) for a, b in zip(contour[first][0], contour[last][0]))
            contour[first] = (middle, 1)
            between.discard(first)
        contour[:] = [point for index, point in enumerate(contour) if index not in between]
        return True
    return False


def without_slivers(glyph):
    box = box_of(glyph)
    points, flags, ends = [], [], []
    for contour in contours_of(glyph):
        while len(contour) > 3 and settle_sliver(contour, box):
            pass
        points += [point for point, _ in contour]
        flags += [on for _, on in contour]
        ends.append(len(points) - 1)
    glyph.coordinates = GlyphCoordinates(points)
    glyph.flags = bytearray(flags)
    glyph.endPtsOfContours = ends
    glyph.numberOfContours = len(ends)


def bend_at(contour, index):
    before, point, after = contour[index - 1][0], contour[index][0], contour[(index + 1) % len(contour)][0]
    incoming = (point[0] - before[0], point[1] - before[1])
    outgoing = (after[0] - point[0], after[1] - point[1])
    if incoming == (0, 0) or outgoing == (0, 0):
        return 0.0
    return abs(math.atan2(incoming[0] * outgoing[1] - incoming[1] * outgoing[0], incoming[0] * outgoing[0] + incoming[1] * outgoing[1]))


def meant_smooth(contour, index):
    count = len(contour)
    if not contour[index][1] or contour[index - 1][1] and contour[(index + 1) % count][1]:
        return False
    return 0 < bend_at(contour, index) < NEAR_SMOOTH


def turning_point(before, point, after):
    return any(point[axis] >= max(before[axis], after[axis]) or point[axis] <= min(before[axis], after[axis]) for axis in (0, 1))


def implied_corner(contour, box):
    count = len(contour)
    for index, (point, on) in enumerate(contour):
        before, after = contour[index - 1], contour[(index + 1) % count]
        if not on or before[1] or after[1] or not meant_smooth(contour, index):
            continue
        middle = ((before[0][0] + after[0][0]) / 2, (before[0][1] + after[0][1]) / 2)
        if math.dist(point, middle) <= IMPLIED_REACH and not turning_point(before[0], point, after[0]) and not on_edge(point, box) and not beside_extreme(contour, index):
            del contour[index]
            return True
    return False


def clear_of_lines(point, original, lines):
    for line, spans in lines.items():
        if not any(low - SNAP_REACH <= point[0] <= high + SNAP_REACH for low, high in spans):
            continue
        if original[1] == line and point[1] != line or 0 < abs(point[1] - line) <= SNAP_REACH:
            return False
    return True


def level_pair(contour, mover, beyond):
    point, (other, on) = contour[mover][0], contour[beyond % len(contour)]
    return not on and (point[0] == other[0] or point[1] == other[1])


def nudged(contour, index, lines, box):
    count = len(contour)
    movers = [
        neighbour % count
        for neighbour in (index - 1, index + 1)
        if not contour[neighbour % count][1] and not on_edge(contour[neighbour % count][0], box) and not level_pair(contour, neighbour % count, 2 * neighbour - index)
    ]
    watched = {index}
    for mover in movers:
        for neighbour in (mover - 1, mover + 1):
            if contour[neighbour % count][1] and bend_at(contour, neighbour % count) < NEAR_SMOOTH:
                watched.add(neighbour % count)
    original = {mover: contour[mover][0] for mover in movers}

    def cost():
        return sum(bend_at(contour, watch) for watch in watched)

    best, best_cost = None, cost()
    for moves in itertools.product(NUDGES, repeat=len(movers)):
        placed = {mover: (original[mover][0] + dx, original[mover][1] + dy) for mover, (dx, dy) in zip(movers, moves)}
        if not all(clear_of_lines(placed[mover], original[mover], lines) and within(placed[mover], box) for mover in movers):
            continue
        for mover in movers:
            contour[mover] = (placed[mover], 0)
        spent = cost() + NUDGE_PRICE * sum(abs(dx) + abs(dy) for dx, dy in moves)
        if spent < best_cost:
            best, best_cost = placed, spent
    for mover in movers:
        contour[mover] = ((best or original)[mover], 0)


def smoothed_joins(glyph, lines):
    box = box_of(glyph)
    points, flags, ends = [], [], []
    for contour in contours_of(glyph):
        while len(contour) > 3 and implied_corner(contour, box):
            pass
        for index in range(len(contour)):
            if rounding_kink(contour, index):
                straightened(contour, index, lines, box)
            elif meant_smooth(contour, index):
                nudged(contour, index, lines, box)
        points += [point for point, _ in contour]
        flags += [on for _, on in contour]
        ends.append(len(points) - 1)
    glyph.coordinates = GlyphCoordinates(points)
    glyph.flags = bytearray(flags)
    glyph.endPtsOfContours = ends
    glyph.numberOfContours = len(ends)


def stale_outputs(directory, written):
    patterns = (f"{FAMILY}-*.ttf", f"{FAMILY}-*.woff2", f"{UNHINTED_FOLDER}/{FAMILY}-*.ttf")
    return sorted({path for pattern in patterns for path in directory.glob(pattern)} - set(written))
