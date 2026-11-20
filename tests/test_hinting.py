import atexit
import shutil
import tempfile
import unittest
from functools import cache
from pathlib import Path

from fontTools.ttLib import TTFont

from plutto.accents import ACCENTS, CARON_BASES
from plutto.compile import SMART_DROPOUT, SMOOTH_AT_ALL_SIZES
from plutto.glyphs import GLYPHS
from plutto.hinting import INTEGER_PPEM, UNHINTED_FOLDER, autohint, hint_statics
from plutto.masters import FAMILY, UNITS

from rendering import CLEAR_GAP, INK, closed_counters, face, glyph_image, mark_floor, mark_meets_base, strip_glyph_programs

from support import (
    ALL_STYLES,
    BUILT_ORDER,
    AUTOHINTER,
    MIDDLE_WEIGHT,
    VARIABLES,
    built,
    built_name,
    font_path,
    instance,
    kern_like,
    needs_autohinter,
    unhinted_path,
)

ON_CURVE = 0x01
OVERLAP_SIMPLE = 0x40
INSTRUCTION_TABLES = ("fpgm", "cvt ", "prep")
OUTLINE_TABLES = ("cmap", "hmtx", "hhea", "OS/2", "post", "GSUB", "GPOS", "gasp")
SMALL_SIZES = range(11, 17)
FLAT_TOPPED = "uvwxzmnr"
SAMPLE = "Hamburgefonstiv quick zephyrs blow, vexing daft Jim 0123456789"
INK_DRIFT = 0.08
COUNTED_GLYPHS = [
    "a", "aacute", "agrave", "acircumflex", "adieresis", "atilde", "aring", "e", "g", "o", "oslash",
    "six", "eight", "nine", "zero", "A", "B", "P", "R", "ampersand", "ae", "oe", "four", "at",
]
KNOWN_JOINS = {}
KNOWN_CLOSED_COUNTERS = {}
ALIGNED_SIZES = range(11, 25)
ALIGNED_LETTERS = "xHdE"
KNOWN_DOT_JOINS = {}


def glyph_programs(built_font):
    table = built_font["glyf"]
    return {
        name: table[name].program.getBytecode() if hasattr(table[name], "program") else b""
        for name in built_font.getGlyphOrder()
    }


def name_records(built_font):
    return sorted((record.nameID, record.platformID, record.platEncID, record.langID, record.toUnicode()) for record in built_font["name"].names)


def drawn_glyphs(built_font):
    table = built_font["glyf"]
    return [name for name in built_font.getGlyphOrder() if table[name].numberOfContours > 0]


def hinting_problems(built_font):
    missing = [tag for tag in INSTRUCTION_TABLES if tag not in built_font]
    if missing:
        return [f"no {tag} table" for tag in missing]
    programs = glyph_programs(built_font)
    problems = [f"{name} has no instructions" for name in drawn_glyphs(built_font) if not programs[name]]
    if not built_font["head"].flags & INTEGER_PPEM:
        problems.append("head does not round the ppem to an integer")
    return problems


def unhinted_problems(built_font):
    problems = [f"carries a {tag} table" for tag in ("fpgm", "cvt ") if tag in built_font]
    if built_font["head"].flags & INTEGER_PPEM:
        problems.append("head rounds the ppem to an integer without hints that need it")
    if built_font["prep"].program.getBytecode() != SMART_DROPOUT:
        problems.append("prep does more than switch on smart dropout control")
    problems += [f"{name} has instructions" for name, program in glyph_programs(built_font).items() if program]
    return problems


def shipped_statics():
    return [font_path(style, suffix) for style in ALL_STYLES for suffix in (".ttf", ".woff2")]


def unhinted_files():
    return [font_path(style, suffix) for style in VARIABLES for suffix in (".ttf", ".woff2")] + [unhinted_path(style) for style in ALL_STYLES]


@cache
def without_glyph_hints(style):
    folder = Path(tempfile.mkdtemp(prefix="plutto-no-glyph-hints-"))
    atexit.register(shutil.rmtree, folder, ignore_errors=True)
    return strip_glyph_programs(font_path(style), folder / font_path(style).name)


def marked_glyphs():
    accented = [
        name
        for name, model in kern_like().items()
        if name.startswith(model) and name[len(model) :] in ACCENTS and not (model in CARON_BASES and name[len(model) :] == "caron")
    ]
    return ["i", "j"] + sorted(accented)


def character(name):
    return chr(GLYPHS[name][0])


def joins_mark(path, size, name, floor, threshold=INK):
    data, baseline = glyph_image(path, size, character(name))
    return mark_meets_base(data, baseline, floor * size / UNITS, threshold)


def joined_by_hinting(style):
    hinted, reference = font_path(style), without_glyph_hints(style)
    outlines = TTFont(hinted)
    floors = {name: mark_floor(outlines, name) for name in marked_glyphs()}
    return {
        (size, name)
        for size in SMALL_SIZES
        for name in floors
        if joins_mark(hinted, size, name, floors[name]) and not joins_mark(reference, size, name, floors[name], CLEAR_GAP)
    }


def closed_by_hinting(style):
    hinted, reference = font_path(style), without_glyph_hints(style)
    return {
        (size, name)
        for size in SMALL_SIZES
        for name in COUNTED_GLYPHS
        if closed_counters(hinted, reference, character(name), size)
    }


def flat_tops(path, size):
    return {face(path, size).getbbox(letter)[1] for letter in FLAT_TOPPED}


def baselines(path, size):
    return {face(path, size).getbbox(letter)[3] for letter in FLAT_TOPPED}


def ink(path, size):
    mask = face(path, size).getmask(SAMPLE, mode="L")
    return sum(mask.getpixel((x, y)) for y in range(mask.size[1]) for x in range(mask.size[0])) / 255


class OutputFilesTest(unittest.TestCase):
    def test_every_file_in_the_folder_is_expected_and_loads(self):
        directory, paths = built()
        found = sorted(path for path in directory.rglob("*") if path.is_file())
        self.assertEqual(found, sorted(paths))
        for path in found:
            with self.subTest(file=path.relative_to(directory).as_posix()):
                loaded = TTFont(path)
                self.assertEqual(loaded.flavor, "woff2" if path.suffix == ".woff2" else None)
                self.assertEqual(loaded.getGlyphOrder(), BUILT_ORDER)
                self.assertEqual(loaded["gasp"].gaspRange, SMOOTH_AT_ALL_SIZES)
                self.assertTrue(loaded["glyf"]["H"].numberOfContours)

    def test_variable_fonts_and_sources_stay_unhinted(self):
        directory = built()[0]
        for path in unhinted_files():
            with self.subTest(file=path.relative_to(directory).as_posix()):
                self.assertEqual(unhinted_problems(TTFont(path)), [])

    def test_unhinted_sources_sit_in_their_own_folder(self):
        directory = built()[0]
        for style in ALL_STYLES:
            with self.subTest(style=style):
                self.assertEqual(unhinted_path(style), directory / UNHINTED_FOLDER / f"{FAMILY}-{style}.ttf")
                self.assertTrue(unhinted_path(style).is_file())

    def test_statics_match_how_the_build_was_hinted(self):
        directory = built()[0]
        for path in shipped_statics():
            with self.subTest(file=path.relative_to(directory).as_posix()):
                loaded = TTFont(path)
                if AUTOHINTER:
                    self.assertEqual(hinting_problems(loaded), [])
                else:
                    self.assertEqual(unhinted_problems(loaded), [])

    def test_missing_autohinter_ships_the_sources(self):
        target = Path(tempfile.mkdtemp(prefix="plutto-unhinted-"))
        self.addCleanup(shutil.rmtree, target, ignore_errors=True)
        pairs = [(unhinted_path(style), target / unhinted_path(style).name) for style in ALL_STYLES[:2]]
        self.assertFalse(hint_statics(pairs, None))
        for source, copy in pairs:
            with self.subTest(file=source.name):
                self.assertEqual(copy.read_bytes(), source.read_bytes())


@needs_autohinter
class HintedStaticsTest(unittest.TestCase):
    def test_a_weight_between_masters_hints_with_the_shared_settings(self):
        target = Path(tempfile.mkdtemp(prefix="plutto-between-"))
        self.addCleanup(shutil.rmtree, target, ignore_errors=True)
        source, hinted = target / "between.ttf", target / "between-hinted.ttf"
        between = instance(MIDDLE_WEIGHT)
        between["OS/2"].usWeightClass = MIDDLE_WEIGHT
        between.save(source)
        autohint(source, hinted, AUTOHINTER)
        self.assertIn("fpgm", TTFont(hinted))

    def test_hinted_outlines_match_the_sources(self):
        for style in ALL_STYLES:
            hinted, source = TTFont(font_path(style)), TTFont(unhinted_path(style))
            for tag in OUTLINE_TABLES:
                with self.subTest(style=style, table=tag):
                    self.assertEqual(hinted.getTableData(tag), source.getTableData(tag))
            with self.subTest(style=style, table="name"):
                self.assertEqual(name_records(hinted), name_records(source))
            for tag in ("unitsPerEm", "xMin", "yMin", "xMax", "yMax", "macStyle", "fontRevision"):
                with self.subTest(style=style, head=tag):
                    self.assertEqual(getattr(hinted["head"], tag), getattr(source["head"], tag))
            ours, theirs = hinted["glyf"], source["glyf"]
            for name in GLYPHS:
                with self.subTest(style=style, glyph=name):
                    here, there = ours[built_name(name)], theirs[built_name(name)]
                    self.assertEqual(here.numberOfContours, there.numberOfContours)
                    if there.isComposite():
                        self.assertEqual([(component.glyphName, component.x, component.y) for component in here.components], [(component.glyphName, component.x, component.y) for component in there.components])
                    if there.numberOfContours > 0:
                        self.assertEqual(here.endPtsOfContours, there.endPtsOfContours)
                        self.assertEqual(list(here.coordinates), list(there.coordinates))
                        mask = ON_CURVE | OVERLAP_SIMPLE
                        self.assertEqual([flag & mask for flag in here.flags], [flag & mask for flag in there.flags])

    def test_web_fonts_keep_the_hints(self):
        for style in ALL_STYLES:
            with self.subTest(style=style):
                plain, packed = TTFont(font_path(style)), TTFont(font_path(style, ".woff2"))
                for tag in INSTRUCTION_TABLES:
                    self.assertEqual(packed.getTableData(tag), plain.getTableData(tag))
                self.assertEqual(glyph_programs(packed), glyph_programs(plain))

    def test_small_text_keeps_one_x_height_and_baseline(self):
        for style in ALL_STYLES:
            for size in SMALL_SIZES:
                with self.subTest(style=style, size=size):
                    self.assertEqual(len(flat_tops(font_path(style), size)), 1)
                    self.assertEqual(len(baselines(font_path(style), size)), 1)

    def test_every_style_shares_its_heights(self):
        for size in ALIGNED_SIZES:
            rows = {style: tuple(face(font_path(style), size).getbbox(letter)[1] for letter in ALIGNED_LETTERS) for style in ALL_STYLES}
            with self.subTest(size=size):
                self.assertEqual(len(set(rows.values())), 1, rows)

    def test_small_text_keeps_its_colour(self):
        for style in ALL_STYLES:
            for size in SMALL_SIZES:
                with self.subTest(style=style, size=size):
                    ratio = ink(font_path(style), size) / ink(without_glyph_hints(style), size)
                    self.assertLess(abs(ratio - 1), INK_DRIFT)

    def test_hinting_keeps_marks_apart_from_their_letters(self):
        for style in ALL_STYLES:
            with self.subTest(style=style):
                joined = joined_by_hinting(style)
                self.assertLessEqual(joined, KNOWN_JOINS.get(style, set()), f"hinting joins {sorted(joined - KNOWN_JOINS.get(style, set()))}")

    def test_hinting_keeps_counters_open(self):
        for style in ALL_STYLES:
            with self.subTest(style=style):
                closed = closed_by_hinting(style)
                self.assertLessEqual(closed, KNOWN_CLOSED_COUNTERS.get(style, set()), f"hinting closes {sorted(closed - KNOWN_CLOSED_COUNTERS.get(style, set()))}")

    def test_dots_of_i_and_j_stand_clear(self):
        for style in ALL_STYLES:
            outlines = TTFont(font_path(style))
            for size in SMALL_SIZES:
                for name in ("i", "j"):
                    if (size, name) in KNOWN_DOT_JOINS.get(style, set()):
                        continue
                    with self.subTest(style=style, size=size, glyph=name):
                        self.assertFalse(joins_mark(font_path(style), size, name, mark_floor(outlines, name)))


if __name__ == "__main__":
    unittest.main()
