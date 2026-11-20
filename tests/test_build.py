import math
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from plutto.compile import COPYRIGHT, LICENSE, LICENSE_URL, PANOSE_WEIGHTS, classify_glyphs, compact, draw, quadratic, stale_outputs
from plutto.hinting import UNHINTED_FOLDER
from plutto.glyphs import GLYPHS, drawn_alike
from plutto.masters import (
    DEFAULT,
    DESIGN_SPACES,
    FAMILY,
    INSTANCES,
    ITALIC_MASTERS,
    ITALIC_WIDTH,
    LINE_ASCENT,
    LINE_DESCENT,
    MASTERS,
    SLANT,
    UNITS,
    family,
    weight_name,
)

from support import (
    ALL_STYLES,
    BETWEEN_WEIGHTS,
    HEAVIEST,
    INSTANCE_WEIGHTS,
    ITALIC_VARIABLE,
    LIGHTEST,
    MASTER_WEIGHTS,
    ROMAN_VARIABLE,
    SPACES,
    STYLE_MASTERS,
    VARIABLES,
    BUILT_ORDER,
    all_fonts,
    built_name,
    build_error,
    built,
    font,
    font_path,
    instance,
    is_combining,
    is_zero_width,
    is_italic_style,
    master_fonts,
    outline_polygons,
    static_fonts,
    variable_fonts,
)
from test_shaping import ink_masks

MERGE_SLACK_PIXELS = 2
NARROWING_ROUNDING = 2
LARGEST_GPOS = 181 * 1024
COMPOSED_LETTERS = ["aacute", "Eacute", "ocircumflex", "dcaron", "lcaron", "Lcaron", "tcaron", "uni0430"]
LONGEST_GLYPH_NAME = 31
TALLEST_CAPITAL = "Abreveacute"
VIETNAMESE_CAPITALS = [code for code in range(0x1EA0, 0x1EFA) if chr(code).isupper()]
OPEN_DIAGONALS = {"A": (8, 12), "V": (8, 12), "W": (8, 12), "Y": (8, 12), "T": (13, 17)}
TABULAR_SPACES = ("uni2007",)
SHIPPED = [f"{FAMILY}-{style}{suffix}" for suffix in (".ttf", ".woff2") for style in ALL_STYLES + VARIABLES]
SOURCES = [f"{UNHINTED_FOLDER}/{FAMILY}-{style}.ttf" for style in ALL_STYLES]
OUTPUTS = SHIPPED + SOURCES
EXPECTED_FILES = [
    "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black",
    "LightItalic", "Italic", "MediumItalic", "SemiBoldItalic", "BoldItalic", "ExtraBoldItalic", "BlackItalic",
    "Variable", "Italic-Variable",
]
EXPECTED_STATIC_WEIGHTS = [("Light", 300), ("Regular", 400), ("Medium", 500), ("SemiBold", 600), ("Bold", 700), ("ExtraBold", 800), ("Black", 900)]
PANOSE_SANS = {"bFamilyType": 2, "bSerifStyle": 11, "bProportion": 4, "bContrast": 2, "bStrokeVariation": 2, "bArmStyle": 2, "bMidline": 2, "bXHeight": 4}
PANOSE_LETTERFORMS = {False: 2, True: 9}
TABULAR_FIGURES = [f"{name}.tnum" for name in ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")]
TABULAR_PUNCTUATION = ["comma.tab", "period.tab", "colon.tab", "semicolon.tab", "colon.tab.case", "uni2008.tab"]
TABULAR_SIGNS = [f"{name}.tab" for name in ("dollar", "Euro", "sterling", "yen", "cent", "plus", "minus", "equal", "plusminus", "multiply", "divide", "hyphen")] + ["hyphen.tab.case"]
OLDSTYLE_TABULAR = [f"{name}.tosf" for name in ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")]
FIGURE_SPACE = 0x2007
PUNCTUATION_SPACE = 0x2008
ITALIC_BIT = 0x01
BOLD_BIT = 0x20
REGULAR_BIT = 0x40
SAMPLE = "Hamburgefonstiv 0123"
LICENSING_NAMES = {0: COPYRIGHT, 13: LICENSE, 14: LICENSE_URL}
INSTALLATION_NAME_IDS = (1, 4, 6)
LINKED_STYLES = {"Regular", "Bold"}
EXPECTED_INSTANCES = [
    ("Light", 300),
    ("Regular", 400),
    ("Medium", 500),
    ("SemiBold", 600),
    ("Bold", 700),
    ("ExtraBold", 800),
    ("Black", 900),
]
EXPECTED_MASTERS = [("Light", 300), ("Regular", 400), ("Bold", 700), ("Black", 900)]
BASE_CLASS = 1
LIGATURE_CLASS = 2
MARK_CLASS = 3
LIGATURE_SUBSTITUTION = 4
SUBSTITUTION_EXTENSION = 7
SMALL_FONT_GLYPHS = [".notdef", "f", "i", "f_i", "acutecomb"]
SMALL_FONT_CMAP = {ord("f"): "f", ord("i"): "i", 0x0301: "acutecomb"}
SMALL_FONT_FEATURES = """
languagesystem DFLT dflt;
feature liga { sub f i by f_i; } liga;
markClass acutecomb <anchor 0 0> @TOP;
feature mark { pos base [f i] <anchor 100 500> mark @TOP; } mark;
"""
MARK_LOOKUPS = {4: ("MarkCoverage",), 5: ("MarkCoverage",), 6: ("Mark1Coverage", "Mark2Coverage")}
EXTENSION_LOOKUP = 9


def glyph_classes(built_font):
    table = built_font["GDEF"].table if "GDEF" in built_font else None
    classes = getattr(table, "GlyphClassDef", None)
    return classes.classDefs if classes else None


def gsub_ligatures(built_font):
    found = set()
    for lookup in built_font["GSUB"].table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            kind = lookup.LookupType
            if kind == SUBSTITUTION_EXTENSION:
                kind, subtable = subtable.ExtensionLookupType, subtable.ExtSubTable
            if kind == LIGATURE_SUBSTITUTION:
                found.update(ligature.LigGlyph for group in subtable.ligatures.values() for ligature in group)
    return found


def expected_classes(built_font):
    marks = {name for name in built_font.getGlyphOrder() if is_combining(name)} | gpos_marks(built_font)
    ligatures = gsub_ligatures(built_font)
    return {
        name: MARK_CLASS if name in marks else LIGATURE_CLASS if name in ligatures else BASE_CLASS
        for name in built_font.getGlyphOrder()
        if name != ".notdef"
    }


def small_font():
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(SMALL_FONT_GLYPHS)
    builder.setupCharacterMap(SMALL_FONT_CMAP)
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((0, 500))
    pen.lineTo((100, 500))
    pen.closePath()
    builder.setupGlyf({name: pen.glyph() for name in SMALL_FONT_GLYPHS})
    builder.setupHorizontalMetrics({name: (500, 0) for name in SMALL_FONT_GLYPHS})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.addOpenTypeFeatures(SMALL_FONT_FEATURES)
    return builder.font


def gpos_marks(built_font):
    found = set()
    for lookup in built_font["GPOS"].table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            kind = lookup.LookupType
            if kind == EXTENSION_LOOKUP:
                kind, subtable = subtable.ExtensionLookupType, subtable.ExtSubTable
            for coverage in MARK_LOOKUPS.get(kind, ()):
                found.update(getattr(subtable, coverage).glyphs)
    return found


def neighbours(weight):
    below = max(master for master in MASTER_WEIGHTS if master < weight)
    above = min(master for master in MASTER_WEIGHTS if master > weight)
    return below, above


def neighbourhood(mask):
    padded = numpy.pad(mask, 1)
    return [padded[1:-1, 1:-1], padded[:-2, 1:-1], padded[2:, 1:-1], padded[1:-1, :-2], padded[1:-1, 2:]]


def edge_band(mask):
    around = neighbourhood(mask)
    return numpy.logical_or.reduce(around) & ~numpy.logical_and.reduce(around)


class BuildTest(unittest.TestCase):
    def test_build_succeeds(self):
        error = build_error()
        if error:
            self.fail(f"the build raised an exception\n\n{error}")

    def test_build_writes_every_output(self):
        directory, paths = built()
        self.assertEqual(sorted(path.relative_to(directory).as_posix() for path in paths), sorted(OUTPUTS))
        for name in OUTPUTS:
            self.assertTrue((directory / name).is_file(), name)

    def test_rebuild_finds_only_stale_family_files(self):
        directory = Path(tempfile.mkdtemp(prefix="plutto-stale-"))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        (directory / UNHINTED_FOLDER).mkdir()
        kept = [directory / f"{FAMILY}-Regular.ttf", directory / f"{FAMILY}-Regular.woff2", directory / UNHINTED_FOLDER / f"{FAMILY}-Regular.ttf"]
        stale = [directory / f"{FAMILY}-Retired.ttf", directory / f"{FAMILY}-Retired.woff2", directory / UNHINTED_FOLDER / f"{FAMILY}-Retired.ttf"]
        unrelated = [directory / "notes.txt", directory / "Other-Regular.ttf"]
        for path in kept + stale + unrelated:
            path.write_bytes(b"")
        self.assertEqual(stale_outputs(directory, kept), sorted(stale))

    def test_build_writes_both_design_spaces(self):
        self.assertEqual(sorted(f"{FAMILY}-{name}.ttf" for name in EXPECTED_FILES), sorted(name for name in SHIPPED if name.endswith(".ttf")))

    def test_every_glyph_compiles_with_matching_masters(self):
        for masters in DESIGN_SPACES:
            for name in GLYPHS:
                with self.subTest(space=masters[0].name, glyph=name):
                    outlines, widths = draw(name, masters)
                    self.assertEqual(len(quadratic(name, outlines)), len(widths))

    def test_masters_share_point_structure(self):
        for styles, _, _ in SPACES:
            tables = [built_font["glyf"] for _, built_font in master_fonts(styles)]
            for name in GLYPHS:
                with self.subTest(space=styles[0], glyph=name):
                    glyphs = [table[built_name(name)] for table in tables]
                    contours = {glyph.numberOfContours for glyph in glyphs}
                    self.assertEqual(len(contours), 1)
                    if glyphs[0].isComposite():
                        self.assertEqual(len({tuple(component.glyphName for component in glyph.components) for glyph in glyphs}), 1)
                    elif glyphs[0].numberOfContours:
                        self.assertEqual(len({tuple(glyph.endPtsOfContours) for glyph in glyphs}), 1)
                        self.assertEqual(len({bytes(flag & 1 for flag in glyph.flags) for glyph in glyphs}), 1)

    def test_glyph_order_covers_registry(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                self.assertEqual(built_font.getGlyphOrder(), BUILT_ORDER)

    def test_woff2_files_load(self):
        for style in ALL_STYLES + VARIABLES:
            with self.subTest(style=style):
                packed = TTFont(font_path(style, ".woff2"))
                plain = font(style)
                self.assertEqual(packed.flavor, "woff2")
                self.assertEqual(packed.getGlyphOrder(), plain.getGlyphOrder())
                self.assertEqual(packed.getBestCmap(), plain.getBestCmap())
                for name in plain.getGlyphOrder():
                    self.assertEqual(packed["hmtx"][name], plain["hmtx"][name])
                self.assertEqual(sorted(packed.keys()), sorted(plain.keys()))


class VariableInstanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spaces = []
        for styles, _, variable in SPACES:
            instances = {weight: instance(weight, variable) for weight in INSTANCE_WEIGHTS}
            statics = {built_font["OS/2"].usWeightClass: built_font for _, built_font in static_fonts(styles)}
            cls.spaces.append((variable, instances, statics))

    def widths(self, built_font):
        return {name: built_font["hmtx"][built_name(name)][0] for name in GLYPHS}

    def test_instances_keep_every_glyph(self):
        for variable, instances, _ in self.spaces:
            for weight, instance in instances.items():
                with self.subTest(variable=variable, weight=weight):
                    self.assertEqual(instance.getGlyphOrder(), BUILT_ORDER)
                    self.assertNotIn("fvar", instance)

    def test_instance_advances_are_positive(self):
        for variable, instances, _ in self.spaces:
            for weight, instance in instances.items():
                widths = self.widths(instance)
                for name in GLYPHS:
                    if is_combining(name) or is_zero_width(name):
                        continue
                    with self.subTest(variable=variable, weight=weight, glyph=name):
                        self.assertGreater(widths[name], 0)

    def test_master_instances_match_static_fonts(self):
        for variable, instances, statics in self.spaces:
            for weight in MASTER_WEIGHTS:
                with self.subTest(variable=variable, weight=weight):
                    self.assertEqual(self.widths(instances[weight]), self.widths(statics[weight]))

    def test_master_instances_match_static_outlines(self):
        for variable, instances, statics in self.spaces:
            for weight in MASTER_WEIGHTS:
                instance_glyphs = instances[weight]["glyf"]
                static_glyphs = statics[weight]["glyf"]
                instance_set, static_set = instances[weight].getGlyphSet(), statics[weight].getGlyphSet()
                for name in GLYPHS:
                    with self.subTest(variable=variable, weight=weight, glyph=name):
                        ours, theirs = outline_polygons(instance_set, built_name(name)), outline_polygons(static_set, built_name(name))
                        self.assertEqual(bool(ours), bool(theirs))
                        if ours:
                            drawn, shipped = ink_masks(ours, theirs)
                            self.assertLessEqual(((drawn ^ shipped) & ~edge_band(drawn)).sum(), MERGE_SLACK_PIXELS)

    def test_between_instance_advances_lie_between_masters(self):
        for variable, instances, statics in self.spaces:
            for weight in BETWEEN_WEIGHTS:
                below, above = (self.widths(statics[master]) for master in neighbours(weight))
                middle = self.widths(instances[weight])
                for name in GLYPHS:
                    with self.subTest(variable=variable, weight=weight, glyph=name):
                        low, high = sorted((below[name], above[name]))
                        self.assertGreaterEqual(middle[name], low)
                        self.assertLessEqual(middle[name], high)

    def test_sample_widens_with_weight(self):
        cmap = font(ALL_STYLES[0]).getBestCmap()
        sample = [cmap[ord(char)] for char in SAMPLE]
        for variable, instances, _ in self.spaces:
            with self.subTest(variable=variable):
                totals = [sum(instances[weight]["hmtx"][name][0] for name in sample) for weight in INSTANCE_WEIGHTS]
                self.assertEqual(totals, sorted(set(totals)))

    def test_italic_narrows_the_roman_advances(self):
        (_, roman, _), (_, italic, _) = self.spaces
        alike = [name for name in GLYPHS if drawn_alike(name)]
        self.assertGreater(len(alike), len(GLYPHS) * 0.8)
        for weight in INSTANCE_WEIGHTS:
            upright, slanted = self.widths(roman[weight]), self.widths(italic[weight])
            for name in alike:
                with self.subTest(weight=weight, glyph=name):
                    self.assertAlmostEqual(slanted[name], upright[name] * ITALIC_WIDTH, delta=NARROWING_ROUNDING)


def tabular_names(built_font):
    return [name for name in built_font.getGlyphOrder() if ".tnum" in name or name in TABULAR_SPACES]


def unhinted_fonts():
    return [(f"unhinted {style}", TTFont(font_path(style).parent / UNHINTED_FOLDER / font_path(style).name)) for style in ALL_STYLES]


def top_of(built_font, name):
    pen = BoundsPen(built_font.getGlyphSet())
    built_font.getGlyphSet()[name].draw(pen)
    return pen.bounds[3]


class CompositeTest(unittest.TestCase):
    def test_accented_letters_are_composites(self):
        for label, built_font in all_fonts() + unhinted_fonts():
            table = built_font["glyf"]
            for name in COMPOSED_LETTERS:
                with self.subTest(font=label, glyph=name):
                    self.assertTrue(table[name].isComposite())

    def test_components_are_simple_glyphs(self):
        for label, built_font in all_fonts() + unhinted_fonts():
            table = built_font["glyf"]
            nested = [name for name in built_font.getGlyphOrder() if table[name].isComposite() and any(table[component.glyphName].isComposite() for component in table[name].components)]
            with self.subTest(font=label):
                self.assertEqual(nested, [])

    def test_glyph_names_fit_legacy_systems(self):
        for label, built_font in all_fonts():
            with self.subTest(font=label):
                self.assertEqual([name for name in built_font.getGlyphOrder() if len(name) > LONGEST_GLYPH_NAME], [])

    def test_ascender_covers_the_tallest_vietnamese_capital(self):
        fonts = all_fonts()
        ascents = {(built_font["hhea"].ascent, built_font["OS/2"].sTypoAscender) for _, built_font in fonts}
        self.assertEqual(len(ascents), 1)
        ascent = ascents.pop()[0]
        for label, built_font in fonts:
            with self.subTest(font=label):
                cmap = built_font.getBestCmap()
                self.assertGreaterEqual(ascent, top_of(built_font, TALLEST_CAPITAL))
                self.assertGreaterEqual(ascent, max(top_of(built_font, cmap[code]) for code in VIETNAMESE_CAPITALS))
                self.assertEqual((built_font["hhea"].lineGap, built_font["OS/2"].sTypoLineGap), (0, 0))

    def test_diagonal_capitals_sit_close(self):
        built_font = font("Regular")
        table = built_font["glyf"]
        for name, (low, high) in OPEN_DIAGONALS.items():
            glyph = table[name]
            glyph.recalcBounds(table)
            advance, left = built_font["hmtx"][name]
            with self.subTest(glyph=name):
                self.assertTrue(low <= left <= high, left)
                self.assertTrue(low <= advance - glyph.xMax <= high, advance - glyph.xMax)


class KerningSizeTest(unittest.TestCase):
    def test_positioning_tables_stay_compact(self):
        for style, built_font in static_fonts():
            with self.subTest(style=style):
                self.assertLess(len(built_font.reader["GPOS"]), LARGEST_GPOS)


class TabularTest(unittest.TestCase):
    def test_italic_tabular_glyphs_keep_the_roman_width(self):
        for style, built_font in static_fonts():
            if not is_italic_style(style):
                continue
            roman = font(compact(weight_name(STYLE_MASTERS[style])))
            names = tabular_names(built_font)
            with self.subTest(style=style):
                self.assertGreater(len(names), 9)
                self.assertEqual({name: built_font["hmtx"][name][0] for name in names}, {name: roman["hmtx"][name][0] for name in names})


class MetadataTest(unittest.TestCase):
    def test_every_font_classifies_its_glyphs(self):
        expected = None
        for style, built_font in all_fonts():
            classes = glyph_classes(built_font)
            with self.subTest(style=style):
                self.assertIsNotNone(classes, "no GDEF glyph classes")
                self.assertEqual(classes, expected_classes(built_font))
                if expected is None:
                    expected = classes
                self.assertEqual(classes, expected)

    def test_classes_follow_ligatures_and_marks(self):
        built_font = small_font()
        del built_font["GDEF"]
        classify_glyphs(built_font)
        self.assertEqual(glyph_classes(built_font), {"f": BASE_CLASS, "i": BASE_CLASS, "f_i": LIGATURE_CLASS, "acutecomb": MARK_CLASS})

    def test_version_matches_head(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                version = built_font["name"].getDebugName(5)
                self.assertRegex(version, r"^Version \d+\.\d{3}$")
                number = float(version.split()[1])
                self.assertAlmostEqual(built_font["head"].fontRevision, number, places=3)

    def test_sample_text_present(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                sample = built_font["name"].getDebugName(19)
                self.assertTrue(sample)
                missing = [char for char in sample if ord(char) not in built_font.getBestCmap()]
                self.assertEqual(missing, [])

    def test_licensing_names(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                names = built_font["name"]
                self.assertEqual({name_id: names.getDebugName(name_id) for name_id in LICENSING_NAMES}, LICENSING_NAMES)

    def test_windows_names_only(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                self.assertEqual({record.platformID for record in built_font["name"].names}, {3})

    def test_smart_dropout_control(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                self.assertIn("prep", built_font)
                self.assertTrue(built_font["prep"].program.getBytecode())

    def test_variable_names_differ_from_statics(self):
        for variable_style, variable_font in variable_fonts():
            variable = variable_font["name"]
            for style, built_font in static_fonts():
                for name_id in INSTALLATION_NAME_IDS:
                    with self.subTest(variable=variable_style, style=style, name_id=name_id):
                        self.assertNotEqual(variable.getDebugName(name_id), built_font["name"].getDebugName(name_id))

    def test_variable_fonts_pair_as_regular_and_italic(self):
        roman, italic = font(ROMAN_VARIABLE)["name"], font(ITALIC_VARIABLE)["name"]
        self.assertEqual(roman.getDebugName(1), italic.getDebugName(1))
        self.assertEqual((roman.getDebugName(2), italic.getDebugName(2)), ("Regular", "Italic"))
        for name_id in (3, 4, 6, 25):
            with self.subTest(name_id=name_id):
                self.assertNotEqual(roman.getDebugName(name_id), italic.getDebugName(name_id))

    def test_variable_has_avar(self):
        for style, variable in variable_fonts():
            with self.subTest(variable=style):
                self.assertIn("avar", variable)
                self.assertEqual(set(variable["avar"].segments), {axis.axisTag for axis in variable["fvar"].axes})

    def test_underline_consistent_across_family(self):
        thicknesses = {built_font["post"].underlineThickness for _, built_font in all_fonts()}
        self.assertEqual(len(thicknesses), 1)

    def test_os2_flags(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                os2 = built_font["OS/2"]
                self.assertEqual(os2.fsType, 0)
                self.assertTrue(os2.fsSelection & 0x80)
                self.assertGreaterEqual(os2.version, 4)

    def test_ranges_follow_cmap(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                os2 = built_font["OS/2"]
                unicode_ranges = os2.getUnicodeRanges()
                code_pages = os2.getCodePageRanges()
                self.assertEqual(os2.recalcUnicodeRanges(built_font), unicode_ranges)
                self.assertEqual(os2.recalcCodePageRanges(built_font), code_pages)
                self.assertIn(0, unicode_ranges)
                self.assertIn(0, code_pages)

    def test_vertical_metrics(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                os2 = built_font["OS/2"]
                hhea = built_font["hhea"]
                self.assertGreaterEqual(os2.usWinAscent, LINE_ASCENT)
                self.assertGreaterEqual(os2.usWinDescent, -LINE_DESCENT)
                self.assertEqual((hhea.ascent, hhea.descent, hhea.lineGap), (os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap))

    def test_post_angle_and_caret_follow_the_slant(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                post = built_font["post"]
                hhea = built_font["hhea"]
                self.assertEqual(post.isFixedPitch, 0)
                self.assertGreater(post.underlineThickness, 0)
                self.assertLess(post.underlinePosition, 0)
                if is_italic_style(style):
                    self.assertEqual(post.italicAngle, -SLANT)
                    self.assertEqual(hhea.caretSlopeRise, UNITS)
                    self.assertAlmostEqual(hhea.caretSlopeRun / hhea.caretSlopeRise, math.tan(math.radians(SLANT)), places=3)
                    self.assertLess(hhea.caretOffset, 0)
                else:
                    self.assertEqual(post.italicAngle, 0)
                    self.assertEqual(hhea.caretSlopeRun, 0)
                    self.assertEqual(hhea.caretOffset, 0)

    def test_style_bits(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                bold = style in ("Bold", "BoldItalic")
                italic = is_italic_style(style)
                selection = built_font["OS/2"].fsSelection
                self.assertEqual(bool(built_font["head"].macStyle & 1), bold)
                self.assertEqual(bool(built_font["head"].macStyle & 2), italic)
                self.assertEqual(bool(selection & BOLD_BIT), bold)
                self.assertEqual(bool(selection & ITALIC_BIT), italic)
                self.assertEqual(bool(selection & REGULAR_BIT), not bold and not italic)

    def test_variable_stat(self):
        for style, variable in variable_fonts():
            with self.subTest(variable=style):
                self.assertIn("STAT", variable)
                stat = variable["STAT"].table
                self.assertEqual([axis.AxisTag for axis in stat.DesignAxisRecord.Axis], ["wght", "ital"])
                weights = {value.Value: value for value in stat.AxisValueArray.AxisValue if value.AxisIndex == 0}
                axis = variable["fvar"].axes[0]
                self.assertIn(axis.defaultValue, weights)
                self.assertIn(axis.maxValue, weights)
                self.assertTrue(weights[axis.defaultValue].Flags & 0x2)
                for value in weights.values():
                    self.assertGreaterEqual(value.Value, axis.minValue)
                    self.assertLessEqual(value.Value, axis.maxValue)
                    self.assertTrue(variable["name"].getDebugName(value.ValueNameID))

    def test_stat_links_roman_and_italic(self):
        found = {}
        for style, variable in variable_fonts():
            stat = variable["STAT"].table
            slopes = [value for value in stat.AxisValueArray.AxisValue if value.AxisIndex == 1]
            self.assertEqual(len(slopes), 1, style)
            found[style] = (slopes[0], variable["name"].getDebugName(slopes[0].ValueNameID))
        roman, roman_name = found[ROMAN_VARIABLE]
        italic, italic_name = found[ITALIC_VARIABLE]
        self.assertEqual((roman.Value, roman_name, italic.Value, italic_name), (0, "Roman", 1, "Italic"))
        self.assertTrue(roman.Flags & 0x2)
        self.assertEqual(roman.Format, 3)
        self.assertEqual(roman.LinkedValue, 1)
        self.assertFalse(italic.Flags & 0x2)
        self.assertEqual(font(ITALIC_VARIABLE)["name"].getDebugName(font(ITALIC_VARIABLE)["STAT"].table.ElidedFallbackNameID), "Italic")


class WeightRangeTest(unittest.TestCase):
    def test_masters_span_light_to_black(self):
        self.assertEqual([(master.name, master.weight) for master in MASTERS], EXPECTED_MASTERS)
        self.assertEqual(DEFAULT.weight, 400)
        self.assertEqual(INSTANCES, EXPECTED_INSTANCES)

    def test_italic_masters_mirror_the_roman(self):
        expected = [("Light Italic", 300), ("Italic", 400), ("Bold Italic", 700), ("Black Italic", 900)]
        self.assertEqual([(master.name, master.weight) for master in ITALIC_MASTERS], expected)
        for roman, italic in zip(MASTERS, ITALIC_MASTERS):
            with self.subTest(master=italic.name):
                self.assertEqual((roman.italic, roman.slant), (False, 0))
                self.assertEqual((italic.italic, italic.slant, italic.mix), (True, SLANT, roman.mix))
                self.assertEqual(family(roman), MASTERS)
                self.assertEqual(family(italic), ITALIC_MASTERS)

    def test_static_weight_classes(self):
        for style, built_font in static_fonts():
            with self.subTest(style=style):
                os2 = built_font["OS/2"]
                self.assertEqual(os2.usWeightClass, STYLE_MASTERS[style].weight)
                self.assertEqual(os2.panose.bWeight, PANOSE_WEIGHTS[os2.usWeightClass])

    def test_static_panose_classifies_the_design(self):
        for style, built_font in static_fonts():
            with self.subTest(style=style):
                panose = built_font["OS/2"].panose
                self.assertEqual({field: getattr(panose, field) for field in PANOSE_SANS}, PANOSE_SANS)
                self.assertEqual(panose.bLetterForm, PANOSE_LETTERFORMS[is_italic_style(style)])

    def test_tabular_widths_hold_within_a_font_and_its_family(self):
        widths = {}
        for style, built_font in static_fonts():
            metrics, cmap = built_font["hmtx"], built_font.getBestCmap()
            figure = metrics[TABULAR_FIGURES[0]][0]
            with self.subTest(style=style):
                self.assertEqual({metrics[name][0] for name in TABULAR_FIGURES + OLDSTYLE_TABULAR + TABULAR_SIGNS}, {figure})
                self.assertEqual(metrics["percent.tab"][0], figure * 1.5)
                self.assertEqual({metrics[name][0] for name in TABULAR_PUNCTUATION}, {figure / 2})
                self.assertEqual(metrics[cmap[FIGURE_SPACE]][0], figure)
                self.assertEqual(metrics[cmap[PUNCTUATION_SPACE]][0], metrics["period"][0])
                self.assertEqual([name for name in built_font.getGlyphOrder() if name.endswith(".tnum")], TABULAR_FIGURES)
            if not is_italic_style(style):
                widths.setdefault(built_font["name"].getDebugName(1), set()).add(figure)
        for family_name, found in widths.items():
            with self.subTest(family=family_name):
                self.assertEqual(len(found), 1)

    def test_static_names(self):
        for style, built_font in static_fonts():
            names = built_font["name"]
            master = STYLE_MASTERS[style]
            weight_style = next(name for name, value in EXPECTED_STATIC_WEIGHTS if value == master.weight)
            italic = is_italic_style(style)
            with self.subTest(style=style):
                self.assertEqual(names.getDebugName(4), f"{FAMILY} {master.name}")
                self.assertEqual(names.getDebugName(6), f"{FAMILY}-{style}")
                if weight_style in LINKED_STYLES:
                    self.assertEqual((names.getDebugName(1), names.getDebugName(2)), (FAMILY, master.name))
                    self.assertIsNone(names.getDebugName(16))
                else:
                    self.assertEqual((names.getDebugName(1), names.getDebugName(2)), (f"{FAMILY} {weight_style}", "Italic" if italic else "Regular"))
                    self.assertEqual((names.getDebugName(16), names.getDebugName(17)), (FAMILY, master.name))

    def test_static_stat_places_the_font(self):
        weight_styles = {weight: name for name, weight in EXPECTED_STATIC_WEIGHTS}
        for style, built_font in static_fonts():
            master = STYLE_MASTERS[style]
            italic = is_italic_style(style)
            with self.subTest(style=style):
                stat = built_font["STAT"].table
                names = built_font["name"]
                self.assertEqual([axis.AxisTag for axis in stat.DesignAxisRecord.Axis], ["wght", "ital"])
                found = sorted((value.AxisIndex, value.Value, names.getDebugName(value.ValueNameID)) for value in stat.AxisValueArray.AxisValue)
                slope = (1, 1, "Italic") if italic else (1, 0, "Roman")
                self.assertEqual(found, [(0, master.weight, weight_styles[master.weight]), slope])

    def test_ribbi_group(self):
        group = {
            built_font["name"].getDebugName(2): style
            for style, built_font in static_fonts()
            if built_font["name"].getDebugName(1) == FAMILY
        }
        self.assertEqual(group, {"Regular": "Regular", "Italic": "Italic", "Bold": "Bold", "Bold Italic": "BoldItalic"})

    def test_static_names_are_unique(self):
        for name_id in (3, 4, 6):
            with self.subTest(name_id=name_id):
                values = [built_font["name"].getDebugName(name_id) for _, built_font in all_fonts()]
                self.assertEqual(len(set(values)), len(values))

    def test_variable_axis(self):
        for style, variable in variable_fonts():
            with self.subTest(variable=style):
                axis = variable["fvar"].axes[0]
                self.assertEqual(len(variable["fvar"].axes), 1)
                self.assertEqual((axis.axisTag, axis.minValue, axis.defaultValue, axis.maxValue), ("wght", LIGHTEST, DEFAULT.weight, HEAVIEST))
                self.assertEqual(variable["OS/2"].usWeightClass, DEFAULT.weight)

    def test_variable_named_instances(self):
        for style, variable in variable_fonts():
            italic = style == ITALIC_VARIABLE
            names = variable["name"]
            found = [
                (names.getDebugName(record.subfamilyNameID), record.coordinates["wght"], names.getDebugName(record.postscriptNameID))
                for record in variable["fvar"].instances
            ]
            expected = []
            for name, weight in EXPECTED_INSTANCES:
                styled = ("Italic" if name == "Regular" else f"{name} Italic") if italic else name
                expected.append((styled, weight, f"{FAMILY}Variable-{compact(styled)}"))
            with self.subTest(variable=style):
                self.assertEqual(found, expected)

    def test_variable_stat_names_every_instance(self):
        for style, variable in variable_fonts():
            with self.subTest(variable=style):
                stat = variable["STAT"].table
                values = {
                    value.Value: variable["name"].getDebugName(value.ValueNameID)
                    for value in stat.AxisValueArray.AxisValue
                    if value.AxisIndex == 0
                }
                self.assertEqual(values, {float(weight): name for name, weight in EXPECTED_INSTANCES})
        self.assertEqual(font(ROMAN_VARIABLE)["name"].getDebugName(font(ROMAN_VARIABLE)["STAT"].table.ElidedFallbackNameID), DEFAULT.name)

    def test_math_signs_share_one_width(self):
        signs = ["plus", "minus", "multiply", "divide", "equal", "notequal", "less", "greater", "lessequal", "greaterequal", "plusminus", "approxequal", "logicalnot"]
        for style, built_font in static_fonts():
            with self.subTest(style=style):
                self.assertEqual(len({built_font["hmtx"][name][0] for name in signs}), 1)

    def test_stems_thicken_with_weight(self):
        for _, _, variable in SPACES:
            stems = []
            for weight in INSTANCE_WEIGHTS:
                xs = [x for x, y in instance(weight, variable)["glyf"]["I"].coordinates if y == 0]
                stems.append(max(xs) - min(xs))
            with self.subTest(variable=variable):
                self.assertEqual(stems, sorted(set(stems)))


if __name__ == "__main__":
    unittest.main()
