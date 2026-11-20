import atexit
import shutil
import tempfile
import unicodedata
import unittest
from functools import cache
from pathlib import Path

import numpy
from fontTools.ttLib import TTFont

from plutto.accents import LIGATED_MARKS, TOP_MARKS
from plutto.masters import MASTERS
from plutto.names import DIGITS

from support import (
    BETWEEN_WEIGHTS,
    COMBINING_CATEGORIES,
    MIDDLE_WEIGHT,
    INSTANCE_WEIGHTS,
    MARK_CLEARANCE,
    MASTER_WEIGHTS,
    ALL_STYLES,
    BETWEEN_STYLES,
    ITALIC_BETWEEN_STYLES,
    ITALIC_STYLES,
    STYLES,
    VARIABLES,
    advances,
    all_fonts,
    font,
    font_path,
    instance,
    is_italic_style,
    kern_like,
    kern_like_problem,
    names,
    needs_hb_shape,
    outline_polygons,
    shape,
    shape_lines,
    style_weight,
)

KERNED_PAIRS = ["AV", "To", "LT", "Yo", "LY"]
KERNED_FIGURES = {"7.": ["seven", "period"], "7,": ["seven", "comma"], "7:": ["seven", "colon"]}
SUBSTITUTIONS = [
    ("zero", "0", ["zero.slash"]),
    ("case", "(H)-@", ["parenleft.case", "H", "parenright.case", "hyphen.case", "at.case"]),
    ("frac", "1/4 3/16", ["one.numr", "fraction", "four.dnom", "space", "three.numr", "fraction", "one.dnom", "six.dnom"]),
    ("numr", "12", ["one.numr", "two.numr"]),
    ("dnom", "12", ["one.dnom", "two.dnom"]),
    ("sups", "2", ["twosuperior"]),
    ("sups", "Mme", ["M", "m.sups", "e.sups"]),
    ("subs", "2", ["two.subs"]),
    ("sinf", "H2O", ["H", "two.subs", "O"]),
    ("ss01", "a", ["a.ss01"]),
    ("ss02", "l", ["l.ss02"]),
    ("ss05", "двт", ["uni0434.loclBGR", "uni0432.loclBGR", "uni0442.loclBGR"]),
    ("ss06", "бвт", ["uni0431.loclSRB", "uni0432", "uni0442.loclSRB"]),
    ("ss03", "a->b<=>2x3", ["a", "arrowright", "b", "less", "equal", "greater", "two", "multiply", "three"]),
    ("tnum,pnum", "0123", ["zero", "one", "two", "three"]),
    ("tnum,cv01,cv07,pnum", "13", ["one.cv01", "three.cv07"]),
    ("aalt", "gt", ["g.cv06", "t.cv08"]),
    ("cv06", "gğ", ["g.cv06", "g.cv06", "brevecomb"]),
    ("cv07", "3", ["three.cv07"]),
    ("cv08", "tťţŧ", ["t.cv08", "tcaron.cv08", "t.cv08", "cedillacomb", "tbar.cv08"]),
]
UNCHANGED_BY_DEFAULT = [
    "a -> b <- c => d <-> e", "2x3 10x20", "No. 1a", "1/2",
    "e-mail (see) a:b «hi» ‹ok› [x] {y} @home x-ray 3-d a – b", "(Hello) Hi-fi A-b a-B 1-a", "re: 10 TIME: now",
]
CASE_IN_CONTEXT = [
    ("A-B", ["A", "hyphen.case", "B"]),
    ("10:30", ["one", "zero", "colon.case", "three", "zero"]),
    ("1–2", ["one", "endash.case", "two"]),
    ("A — B", ["A", "space", "emdash.case", "space", "B"]),
    ("(ABC)", ["parenleft.case", "A", "B", "C", "parenright.case"]),
    ("[1]", ["bracketleft.case", "one", "bracketright.case"]),
    ("«ÉTÉ»", ["guillemotleft.case", "Eacute", "T", "Eacute", "guillemotright.case"]),
    ("@NASA", ["at.case", "N", "A", "S", "A"]),
]
TABULAR_TEXT = ("1,2.3:4;", ["one.tnum", "comma.tab", "two.tnum", "period.tab", "three.tnum", "colon.tab.case", "four.tnum", "semicolon.tab"])
OLDSTYLE_FIGURES = [f"{name}.osf" for name in DIGITS]
NEW_FEATURES = [
    ("onum", "0123456789", OLDSTYLE_FIGURES),
    ("onum,tnum", "09", ["zero.tosf", "nine.tosf"]),
    ("onum,tnum,pnum", "09", ["zero.osf", "nine.osf"]),
    ("onum,lnum", "09", ["zero", "nine"]),
    ("smcp", "Ab ß", ["A", "B.sc", "space", "S.sc", "S.sc"]),
    ("c2sc", "Ab", ["A.sc", "b"]),
    ("smcp,c2sc", "Éé", ["E.sc", "acutecomb", "E.sc", "acutecomb"]),
    ("smcp", "æøıj", ["AE.sc", "Oslash.sc", "I.sc", "J.sc"]),
    ("ss04", "1Il0", ["one.cv01", "I.cv02", "l", "zero.slash"]),
    ("ss02,ss04", "l", ["l"]),
    ("tnum", "1.2\u2008", ["one.tnum", "period.tab", "two.tnum", "uni2008.tab"]),
    ("tnum", "$€£¥¢%+−=±×÷", [f"{name}.tab" for name in ("dollar", "Euro", "sterling", "yen", "cent", "percent", "plus", "minus", "equal", "plusminus", "multiply", "divide")]),
    ("tnum", "1-2", ["one.tnum", "hyphen.tab.case", "two.tnum"]),
    ("tnum,pnum", "$-", ["dollar", "hyphen"]),
    ("smcp", "ŀǿſǥʒǯ", ["Ldot.sc", "Oslash.sc", "acutecomb", "S.sc", "Gstroke.sc", "Ezh.sc", "Ezh.sc", "caroncomb"]),
    ("smcp", "абвёй", ["uni0410.sc", "uni0411.sc", "uni0412.sc", "uni0415.sc", "dieresiscomb", "uni0418.sc", "brevecomb"]),
    ("c2sc", "ЖЁ", ["uni0416.sc", "uni0415.sc", "dieresiscomb"]),
    ("smcp", "αλςάϊ", ["Alpha.sc", "Lambda.sc", "Sigma.sc", "Alpha.sc", "Iota.sc", "dieresiscomb"]),
    ("c2sc", "ΩΆ", ["Omega.sc", "Alpha.sc"]),
    ("smcp", "ѕіїјґўәө", ["S.sc", "I.sc", "I.sc", "dieresiscomb", "J.sc", "uni0490.sc", "uni0423.sc", "brevecomb", "Schwa.sc", "Theta.sc"]),
    ("c2sc", "ЉЏЋҚ", ["uni0409.sc", "uni040F.sc", "uni040B.sc", "uni049A.sc"]),
    ("smcp", "ἄᾳῗ", ["Alpha.sc", "Alpha.sc", "Iota.sc", "Iota.sc", "dieresiscomb"]),
    ("c2sc", "Ἀᾼ", ["Alpha.sc", "Alpha.sc", "Iota.sc"]),
    ("smcp", "μάιος ή α", ["Mu.sc", "Alpha.sc", "Iota.sc", "dieresiscomb", "Omicron.sc", "Sigma.sc", "space", "Etatonos.sc", "space", "Alpha.sc"]),
    ("smcp", "ήλιος", ["Eta.sc", "Lambda.sc", "Iota.sc", "Omicron.sc", "Sigma.sc"]),
    ("smcp", "ấợǘ", ["A.sc", "acutecircumflexcomb", "O.sc", "horncomb", "dotbelowcomb", "U.sc", "dieresiscomb", "acutecomb"]),
    ("smcp", "əɣɖǉ", ["Schwa.sc", "Gammaafrican.sc", "Dcroat.sc", "L.sc", "J.sc"]),
    ("ss02", "l\u030C", ["lcaron.ss02"]),
    ("c2sc", "2024", ["two.sc", "zero.sc", "two.sc", "four.sc"]),
    ("smcp", "a1", ["A.sc", "one.sc"]),
]
SINGLE_STOREY_ROOTS = ("a", "æ")
TAILLESS_ROOTS = ("l",)
LANGUAGE_FORMS = [
    ("ro", "şţŞŢ", ["scommaaccent", "tcommaaccent", "Scommaaccent", "Tcommaaccent"]),
    ("mo", "ş", ["scommaaccent"]),
    ("tr", "şţ", ["scedilla", "tcedilla"]),
    ("lt", "j\u0301\u012f\u0301", ["dotlessj", "dotaccentcomb.narrow", "acutecomb", "dotlessi", "ogonekcomb", "dotaccentcomb.narrow", "acutecomb"]),
    ("lt", "ìíĩ", ["igrave", "iacute", "itilde"]),
    ("en", "ì", ["igrave"]),
    ("nl", "íj ÍJ", ["iacute", "dotlessj", "acutecomb.narrow", "space", "Iacute", "J", "acutecomb.case"]),
    ("en", "íj", ["iacute", "j"]),
    ("sr", "гѓ", ["uni0433.loclSRB", "uni0453.loclSRB"]),
    ("mk", "гѓ", ["uni0433.loclSRB", "uni0453.loclSRB"]),
    ("ru", "гѓ", ["uni0433", "uni0453"]),
    ("tr", "iı", ["i.loclTRK", "dotlessi"]),
    ("el", "α·β", ["alpha", "anoteleia", "beta"]),
    ("ca", "l·l", ["l", "periodcentered.loclCAT", "l"]),
    ("en", "l·l", ["l", "periodcentered", "l"]),
]
TURKIC_SMALL_CAPS = [
    ("tr", "smcp", "iı", ["I.sc", "dotaccentcomb", "I.sc"]),
    ("az", "smcp", "iı", ["I.sc", "dotaccentcomb", "I.sc"]),
    ("crh", "smcp", "iı", ["I.sc", "dotaccentcomb", "I.sc"]),
    ("kk", "smcp", "iı", ["I.sc", "dotaccentcomb", "I.sc"]),
    ("tt", "smcp", "iı", ["I.sc", "dotaccentcomb", "I.sc"]),
    ("tr", "c2sc", "İI", ["I.sc", "dotaccentcomb", "I.sc"]),
    ("tr", "smcp,cv02", "iı", ["I.cv02.sc", "dotaccentcomb", "I.cv02.sc"]),
    ("tr", "smcp,ss04", "iı", ["I.cv02.sc", "dotaccentcomb", "I.cv02.sc"]),
    ("en", "smcp", "iı", ["I.sc", "I.sc"]),
]
LOCAL_SMALL_CAPS = [
    ("bg", "дйѝ", ["uni0414.sc", "uni0418.sc", "brevecomb", "uni0418.sc", "gravecomb"]),
    ("sr", "бгѓ", ["uni0411.sc", "uni0413.sc", "uni0413.sc", "acutecomb"]),
    ("mk", "бѓ", ["uni0411.sc", "uni0413.sc", "acutecomb"]),
]
NOT_SMALL_CAPS = {0xB5}
NAMED_FEATURES = ["ss01", "ss02", "ss03", "ss04", "ss05", "ss06", "cv01", "cv02", "cv03", "cv04", "cv05", "cv06", "cv07", "cv08"]
PINNED_ACCENT_KERNS = {
    "Regular": {("T", "idieresis"): 74, ("V", "idieresis"): 79, ("T", "icircumflex"): 52, ("Icircumflex", "V"): 13, ("V", "igrave"): 31},
    "Bold": {("T", "idieresis"): 101, ("V", "idieresis"): 108, ("T", "icircumflex"): 68, ("V", "icircumflex"): 43, ("V", "igrave"): 27},
}
FIGURES = "0123456789"
SAMPLE = "Hamburgefonstiv 0123"
KERN_PARTNERS = ["A", "T", "V", "Y", "o", "period", "hyphen", "quotesingle"]
PAIR_ADJUSTMENT = 2
NO_REQUIRED_FEATURE = 0xFFFF
RASTER_SCALE = 0.25
RASTER_PAD = 2
COMPOSED_SLACK = 0.02
NARROWED_COMPOSED_SLACK = 0.03
NARROWING_ROUNDING = 1
INTERPOLATION_ROUNDING = 1
ROUNDING_NUDGES = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
BETWEEN_INSTANCES = [MIDDLE_WEIGHT, 800]
LONE_MARKS = [("n", "\u0308", "u"), ("m", "\u0301", "u"), ("H", "\u0302", "E")]
STACKED_MARKS = [("e", "\u0304\u0301"), ("a", "\u0306\u0300")]
JOINED_MARKS = {(chr(TOP_MARKS[first][0]), chr(TOP_MARKS[second][0])) for first, second, _ in LIGATED_MARKS.values()}
LONE_MARK_SLACK = 2
STACKED_GAP = 20
CONTEXT_RULES = {
    "SubRuleSet": "SubRule",
    "SubClassSet": "SubClassRule",
    "ChainSubRuleSet": "ChainSubRule",
    "ChainSubClassSet": "ChainSubClassRule",
}


def feature_tags(built_font, table):
    if table not in built_font:
        return set()
    return {record.FeatureTag for record in built_font[table].table.FeatureList.FeatureRecord}


def feature_lookups(built_font, table, tag):
    layout = built_font[table].table
    indices = sorted({
        index
        for record in layout.FeatureList.FeatureRecord
        if record.FeatureTag == tag
        for index in record.Feature.LookupListIndex
    })
    return [layout.LookupList.Lookup[index] for index in indices]


def lookup_type(lookup):
    first = lookup.SubTable[0] if lookup.SubTable else None
    return getattr(first, "ExtensionLookupType", lookup.LookupType)


def subtables(lookup):
    for subtable in lookup.SubTable:
        yield getattr(subtable, "ExtSubTable", subtable)


def x_advance(value):
    return getattr(value, "XAdvance", 0) if value else 0


def pair_table(subtable):
    if subtable.Format == 1:
        return {
            left: {record.SecondGlyph: x_advance(record.Value1) for record in pair_set.PairValueRecord}
            for left, pair_set in zip(subtable.Coverage.glyphs, subtable.PairSet)
        }
    first_classes = subtable.ClassDef1.classDefs
    second_classes = subtable.ClassDef2.classDefs
    rows = [[x_advance(record.Value1) for record in row.Class2Record] for row in subtable.Class1Record]
    return {
        left: (rows[first_classes.get(left, 0)], second_classes)
        for left in subtable.Coverage.glyphs
    }


def pair_in_table(table, left, right):
    if left not in table:
        return None
    entry = table[left]
    if isinstance(entry, dict):
        return entry.get(right)
    row, second_classes = entry
    return row[second_classes.get(right, 0)]


@cache
def kern_tables(built_font):
    tables = []
    for lookup in feature_lookups(built_font, "GPOS", "kern"):
        if lookup_type(lookup) == PAIR_ADJUSTMENT:
            tables.append([pair_table(subtable) for subtable in subtables(lookup)])
    return tables


def kerning(built_font, left, right):
    total = 0
    for lookup in kern_tables(built_font):
        for table in lookup:
            value = pair_in_table(table, left, right)
            if value is not None:
                total += value
                break
    return total


def substitutions(built_font, tag):
    mapping = {}
    for lookup in feature_lookups(built_font, "GSUB", tag):
        for subtable in subtables(lookup):
            mapping.update(getattr(subtable, "mapping", {}))
    return mapping


def language_systems(layout):
    for record in layout.ScriptList.ScriptRecord:
        if record.Script.DefaultLangSys:
            yield record.Script.DefaultLangSys
        for language in record.Script.LangSysRecord:
            yield language.LangSys


def active_features(layout):
    indices = set()
    for system in language_systems(layout):
        indices.update(system.FeatureIndex)
        if system.ReqFeatureIndex != NO_REQUIRED_FEATURE:
            indices.add(system.ReqFeatureIndex)
    return indices


def nested_lookups(subtable):
    records = list(getattr(subtable, "SubstLookupRecord", None) or [])
    for set_name, rule_name in CONTEXT_RULES.items():
        for rule_set in getattr(subtable, set_name, None) or []:
            for rule in getattr(rule_set, rule_name, None) or []:
                records.extend(rule.SubstLookupRecord)
    return {record.LookupListIndex for record in records}


def active_lookups(built_font):
    layout = built_font["GSUB"].table
    found = {
        index
        for feature in active_features(layout)
        for index in layout.FeatureList.FeatureRecord[feature].Feature.LookupListIndex
    }
    pending = list(found)
    while pending:
        for subtable in subtables(layout.LookupList.Lookup[pending.pop()]):
            fresh = nested_lookups(subtable) - found
            found |= fresh
            pending.extend(fresh)
    return [layout.LookupList.Lookup[index] for index in sorted(found)]


def substituted_glyphs(built_font):
    outputs = set()
    for lookup in active_lookups(built_font):
        for subtable in subtables(lookup):
            for value in getattr(subtable, "mapping", {}).values():
                outputs.update([value] if isinstance(value, str) else value)
            for choices in getattr(subtable, "alternates", {}).values():
                outputs.update(choices)
            for ligatures in getattr(subtable, "ligatures", {}).values():
                outputs.update(ligature.LigGlyph for ligature in ligatures)
            outputs.update(getattr(subtable, "Substitute", []))
    return outputs


class FeatureTableTest(unittest.TestCase):
    def test_kern_and_tnum_present(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                self.assertIn("kern", feature_tags(built_font, "GPOS"))
                self.assertIn("tnum", feature_tags(built_font, "GSUB"))

    def test_every_glyph_is_reachable(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                reachable = set(built_font.getBestCmap().values()) | substituted_glyphs(built_font)
                unreachable = [name for name in built_font.getGlyphOrder()[1:] if name not in reachable]
                self.assertEqual(unreachable, [])

    def test_stylistic_sets_and_variants_carry_names(self):
        packed = [(f"{style}.woff2", font(style, ".woff2")) for style in ALL_STYLES + VARIABLES]
        for style, built_font in all_fonts() + packed:
            records = {record.FeatureTag: record.Feature for record in built_font["GSUB"].table.FeatureList.FeatureRecord}
            for tag in NAMED_FEATURES:
                with self.subTest(style=style, feature=tag):
                    params = records[tag].FeatureParams
                    name_id = getattr(params, "UINameID", None) or getattr(params, "FeatUILabelNameID", None)
                    self.assertTrue(built_font["name"].getDebugName(name_id))

    def test_tabular_figures_exist(self):
        order = set(font(STYLES[0]).getGlyphOrder())
        for name in DIGITS:
            self.assertIn(f"{name}.tnum", order)

    def test_kern_lookups_tighten_pairs(self):
        for style, built_font in all_fonts():
            for left, right in KERNED_PAIRS + list(KERNED_FIGURES.values()):
                with self.subTest(style=style, pair=left + right):
                    self.assertLess(kerning(built_font, left, right), 0)

    def test_tnum_lookup_maps_figures_to_equal_widths(self):
        for style, built_font in all_fonts():
            with self.subTest(style=style):
                mapping = substitutions(built_font, "tnum")
                self.assertEqual([mapping.get(name) for name in DIGITS], [f"{name}.tnum" for name in DIGITS])
                widths = {built_font["hmtx"][f"{name}.tnum"][0] for name in DIGITS}
                self.assertEqual(len(widths), 1)

    def test_accent_clearance_matches_the_test(self):
        from plutto.accents import ACCENT_CLEARANCE

        order = [master for name in ("Regular", "Bold", "Light", "Black") for master in MASTERS if master.name == name]
        self.assertEqual(ACCENT_CLEARANCE, tuple(MARK_CLEARANCE[master.name] for master in order))

    def test_regular_and_bold_accent_kerns_stay_pinned(self):
        for style, pairs in PINNED_ACCENT_KERNS.items():
            for (left, right), value in pairs.items():
                with self.subTest(style=style, pair=f"{left} {right}"):
                    self.assertEqual(kerning(font(style), left, right), value)

    def test_kern_like_glyphs_share_model_kerning(self):
        like = kern_like()
        if not like:
            self.skipTest("no extension declares KERN_LIKE glyphs")
        sources = [(style, style, style_weight(style), built_font) for style, built_font in all_fonts()]
        sources += [(f"{variable} wght={weight}", variable, weight, instance(weight, variable)) for variable in VARIABLES for weight in BETWEEN_WEIGHTS]
        for label, style, weight, built_font in sources:
            partners = built_font.getGlyphOrder()
            for glyph, model in like.items():
                with self.subTest(font=label, glyph=glyph, model=model):
                    problems = []
                    for partner in partners:
                        if partner in like:
                            continue
                        for left, right, model_left, model_right in (
                            (partner, glyph, partner, model),
                            (glyph, partner, model, partner),
                        ):
                            problems.append(kern_like_problem(
                                style, weight, left, right, glyph, model,
                                kerning(built_font, left, right), kerning(built_font, model_left, model_right),
                            ))
                    self.assertEqual([problem for problem in problems if problem], [])


def shaped_length(sequence):
    return len(sequence) - sum(1 for pair in zip(sequence[1:], sequence[2:]) if pair in JOINED_MARKS)


def decomposable(cmap):
    found = []
    for code in sorted(cmap):
        parts = unicodedata.normalize("NFD", chr(code))
        if len(parts) < 2 or not all(ord(part) in cmap for part in parts):
            continue
        if any(unicodedata.category(part) in COMBINING_CATEGORIES for part in parts[1:]):
            found.append((chr(code), parts))
    return found


def without_precomposed(label, codes):
    stripped = TTFont(font_path(label))
    for table in stripped["cmap"].tables:
        for code in codes:
            table.cmap.pop(code, None)
    folder = Path(tempfile.mkdtemp(prefix="plutto-decomposed-"))
    atexit.register(shutil.rmtree, folder, ignore_errors=True)
    target = folder / font_path(label).name
    stripped.save(target)
    return target


def placed_polygons(glyph_set, run):
    polygons, pen = [], 0
    for item in run:
        for polygon in outline_polygons(glyph_set, item["g"]):
            polygons.append([(x + pen + item["dx"], y + item["dy"]) for x, y in polygon])
        pen += item["ax"]
    return polygons, pen


def ink_masks(*shapes):
    points = numpy.array([point for polygons in shapes for polygon in polygons for point in polygon], dtype=float)
    low, high = points.min(axis=0), points.max(axis=0)
    size = tuple(int(value) + 2 * RASTER_PAD for value in numpy.ceil((high - low) * RASTER_SCALE))
    masks = []
    for polygons in shapes:
        placed = [[((x - low[0]) * RASTER_SCALE + RASTER_PAD, (high[1] - y) * RASTER_SCALE + RASTER_PAD) for x, y in polygon] for polygon in polygons]
        masks.append(nonzero_mask(placed, size))
    return masks


def nonzero_mask(polygons, size):
    width, height = size
    if not polygons:
        return numpy.zeros((height, width), dtype=bool)
    starts = numpy.concatenate([numpy.asarray(polygon, dtype=float) for polygon in polygons])
    ends = numpy.concatenate([numpy.roll(numpy.asarray(polygon, dtype=float), -1, axis=0) for polygon in polygons])
    rows = numpy.arange(height) + 0.5
    low, high = numpy.minimum(starts[:, 1], ends[:, 1]), numpy.maximum(starts[:, 1], ends[:, 1])
    row, edge = numpy.nonzero((rows[:, None] >= low[None, :]) & (rows[:, None] < high[None, :]))
    (x0, y0), (x1, y1) = starts[edge].T, ends[edge].T
    crossing = x0 + (rows[row] - y0) * (x1 - x0) / (y1 - y0)
    columns = numpy.clip(numpy.ceil(crossing - 0.5).astype(int), 0, width)
    steps = numpy.zeros((height, width + 1), dtype=int)
    numpy.add.at(steps, (row, columns), numpy.where(y1 > y0, 1, -1))
    return numpy.cumsum(steps[:, :width], axis=1) != 0


def ink_mismatch(polygons, others, nudges, slack=COMPOSED_SLACK):
    mine, theirs = ink_masks(polygons, others)
    allowed = slack * mine.sum()
    best = (mine ^ theirs).sum()
    for dx, dy in nudges:
        if best <= allowed:
            break
        moved = [[(x + dx, y + dy) for x, y in polygon] for polygon in others]
        shifted, nudged = ink_masks(polygons, moved)
        best = min(best, (shifted ^ nudged).sum())
    return best, allowed


def ink_span(glyph_set, run, index):
    pen = sum(item["ax"] for item in run[:index])
    item = run[index]
    points = [(x + pen + item["dx"], y + item["dy"]) for polygon in outline_polygons(glyph_set, item["g"]) for x, y in polygon]
    xs, ys = [x for x, _ in points], [y for _, y in points]
    return min(xs), min(ys), max(xs), max(ys)


def shaping_sources():
    sources = [(style, style, None) for style in ALL_STYLES]
    sources += [(f"{variable} wght={weight}", variable, weight) for variable in VARIABLES for weight in BETWEEN_INSTANCES]
    return sources


def glyph_set_at(label, weight):
    built_font = font(label)
    return built_font.getGlyphSet(location={"wght": weight}) if weight else built_font.getGlyphSet()


@needs_hb_shape
class ShapingTest(unittest.TestCase):
    def test_decomposed_letters_shape_like_precomposed_ones(self):
        letters = decomposable(font(STYLES[0]).getBestCmap())
        if not letters:
            self.skipTest("the fonts have no combining marks yet")
        codes = {ord(letter) for letter, _ in letters}
        for label, path_label, weight in shaping_sources():
            glyph_set = glyph_set_at(path_label, weight)
            variations = f"wght={weight}" if weight else None
            whole = shape_lines(font_path(path_label), [letter for letter, _ in letters], variations=variations)
            parts = shape_lines(without_precomposed(path_label, codes), [sequence for _, sequence in letters], variations=variations)
            narrowed = is_italic_style(path_label)
            interpolated = weight or path_label in BETWEEN_STYLES + ITALIC_BETWEEN_STYLES
            rounding = (INTERPOLATION_ROUNDING if interpolated else 0) + (NARROWING_ROUNDING if narrowed else 0)
            slack = NARROWED_COMPOSED_SLACK if narrowed else COMPOSED_SLACK
            for (letter, sequence), composed, decomposed in zip(letters, whole, parts):
                with self.subTest(font=label, letter=letter, sequence=names(decomposed)):
                    self.assertEqual(len(decomposed), shaped_length(sequence), "the marks were not shaped as separate glyphs")
                    composed_polygons, composed_width = placed_polygons(glyph_set, composed)
                    decomposed_polygons, decomposed_width = placed_polygons(glyph_set, decomposed)
                    self.assertAlmostEqual(decomposed_width, composed_width, delta=rounding)
                    self.assertLessEqual(*ink_mismatch(composed_polygons, decomposed_polygons, ROUNDING_NUDGES if interpolated else [], slack))

    def test_marks_without_a_precomposed_letter_sit_like_their_model(self):
        letters = decomposable(font(STYLES[0]).getBestCmap())
        if not letters:
            self.skipTest("the fonts have no combining marks yet")
        codes = {ord(letter) for letter, _ in letters}
        for label, path_label, weight in shaping_sources():
            glyph_set = glyph_set_at(path_label, weight)
            variations = f"wght={weight}" if weight else None
            path = without_precomposed(path_label, codes)
            for base, mark, model in LONE_MARKS:
                lone, modelled = shape_lines(path, [base + mark, model + mark], variations=variations)
                with self.subTest(font=label, sequence=names(lone), model=names(modelled)):
                    self.assertEqual(len(lone), 2)
                    lone_box, model_box = ink_span(glyph_set, lone, 1), ink_span(glyph_set, modelled, 1)
                    self.assertAlmostEqual(lone_box[1], model_box[1], delta=LONE_MARK_SLACK)
                    base_box = ink_span(glyph_set, lone, 0)
                    self.assertLess(base_box[0], (lone_box[0] + lone_box[2]) / 2)
                    self.assertLess((lone_box[0] + lone_box[2]) / 2, base_box[2])
            for base, marks in STACKED_MARKS:
                (stacked,) = shape_lines(path, [base + marks], variations=variations)
                with self.subTest(font=label, sequence=names(stacked)):
                    self.assertEqual(len(stacked), 1 + len(marks))
                    for lower, upper in zip(range(1, len(marks)), range(2, len(marks) + 1)):
                        gap = ink_span(glyph_set, stacked, upper)[1] - ink_span(glyph_set, stacked, lower)[3]
                        self.assertGreaterEqual(gap, STACKED_GAP)

    def test_kerning_tightens_pairs(self):
        for style in ALL_STYLES + VARIABLES:
            path = font_path(style)
            for pair in KERNED_PAIRS + list(KERNED_FIGURES):
                with self.subTest(style=style, pair=pair):
                    kerned = shape(path, pair)
                    plain = shape(path, pair, features="-kern")
                    self.assertEqual(names(kerned), KERNED_FIGURES.get(pair, list(pair)))
                    self.assertLess(advances(kerned)[0], advances(plain)[0])
                    self.assertEqual(advances(kerned)[1], advances(plain)[1])

    def test_tnum_swaps_to_equal_width_figures(self):
        for style in ALL_STYLES + VARIABLES:
            path = font_path(style)
            with self.subTest(style=style):
                proportional = shape(path, FIGURES)
                tabular = shape(path, FIGURES, features="tnum")
                self.assertEqual(names(proportional), DIGITS)
                self.assertEqual(names(tabular), [f"{name}.tnum" for name in DIGITS])
                self.assertEqual(len(set(advances(tabular))), 1)
                self.assertGreater(len(set(advances(proportional))), 1)

    def test_kern_like_glyphs_shape_like_their_model(self):
        cmap = {name: chr(code) for code, name in sorted(font(STYLES[0]).getBestCmap().items(), reverse=True)}
        pairs = {glyph: model for glyph, model in kern_like().items() if glyph in cmap and model in cmap}
        if not pairs:
            self.skipTest("no KERN_LIKE glyph with a codepoint")
        partners = [name for name in KERN_PARTNERS if name in cmap]
        cases = []
        for glyph, model in pairs.items():
            for partner in partners:
                cases.append((glyph, model, (glyph, partner), (model, partner)))
                cases.append((glyph, model, (partner, glyph), (partner, model)))
        texts = [cmap[left] + cmap[right] for _, _, pair, model_pair in cases for left, right in (pair, model_pair)]
        runs = [(style, style, style_weight(style), None) for style in ALL_STYLES + VARIABLES]
        runs += [(f"{variable} wght={weight}", variable, weight, f"wght={weight}") for variable in VARIABLES for weight in BETWEEN_WEIGHTS]
        adjustments = {}
        for label, style, _, variations in runs:
            path = font_path(style)
            kerned = shape_lines(path, texts, variations=variations)
            plain = shape_lines(path, texts, features="-kern", variations=variations)
            adjustments[label] = {
                text: [a - b for a, b in zip(advances(run), advances(base))]
                for text, run, base in zip(texts, kerned, plain)
            }
        for label, style, weight, _ in runs:
            for glyph, model, pair, model_pair in cases:
                text = cmap[pair[0]] + cmap[pair[1]]
                model_text = cmap[model_pair[0]] + cmap[model_pair[1]]
                with self.subTest(font=label, text=text, model=model_text):
                    (kern, trailing), (model_kern, model_trailing) = adjustments[label][text], adjustments[label][model_text]
                    self.assertEqual(trailing, model_trailing)
                    problem = kern_like_problem(style, weight, *pair, glyph, model, kern, model_kern)
                    if problem:
                        self.fail(problem)

    def test_substitution_features_shape(self):
        runs = [(style, None) for style in ALL_STYLES]
        runs += [(variable, f"wght={weight}") for variable in VARIABLES for weight in INSTANCE_WEIGHTS]
        for style, variations in runs:
            path = font_path(style)
            for feature, text, expected in SUBSTITUTIONS:
                with self.subTest(style=style, variations=variations, feature=feature):
                    self.assertEqual(names(shape(path, text, features=feature, variations=variations)), expected)

    def test_default_shaping_changes_no_text(self):
        for style in ALL_STYLES + VARIABLES:
            path = font_path(style)
            cmap = font(style).getBestCmap()
            for text in UNCHANGED_BY_DEFAULT:
                with self.subTest(style=style, text=text):
                    self.assertEqual(names(shape(path, text)), [cmap[ord(char)] for char in text])

    def test_calt_raises_punctuation_between_capitals_and_figures(self):
        for style in ALL_STYLES + VARIABLES:
            path = font_path(style)
            for text, expected in CASE_IN_CONTEXT:
                with self.subTest(style=style, text=text):
                    self.assertEqual(names(shape(path, text)), expected)

    def test_alternate_letters_cover_every_letter_built_on_them(self):
        cmap = font(STYLES[0]).getBestCmap()
        for feature, roots, extras, suffix in (("ss01", SINGLE_STOREY_ROOTS, "", ".ss01"), ("ss02", TAILLESS_ROOTS, "ŀł", ".ss02")):
            letters = [chr(code) for code in sorted(cmap) if unicodedata.normalize("NFD", chr(code))[0] in roots or chr(code) in extras]
            letters += [root + "\u0323\u0306" for root in roots]
            for style in ALL_STYLES + VARIABLES:
                runs = shape_lines(font_path(style), letters, features=feature)
                for letter, run in zip(letters, runs):
                    with self.subTest(style=style, feature=feature, letter=letter):
                        self.assertTrue(names(run)[0].endswith(suffix), names(run))

    def test_new_features_shape(self):
        for style in ALL_STYLES + VARIABLES:
            path = font_path(style)
            for feature, text, expected in NEW_FEATURES:
                with self.subTest(style=style, feature=feature, text=text):
                    self.assertEqual(names(shape(path, text, features=feature)), expected)

    def test_capital_spacing_adds_room_around_capitals(self):
        for style in ALL_STYLES + VARIABLES:
            path = font_path(style)
            with self.subTest(style=style):
                plain, spaced_out = shape(path, "HAMBURG"), shape(path, "HAMBURG", features="cpsp")
                room = [after["ax"] - before["ax"] for before, after in zip(plain, spaced_out)]
                self.assertEqual(len(set(room)), 1)
                self.assertGreater(room[0], 0)
                for item in spaced_out:
                    self.assertLessEqual(abs(2 * item["dx"] - room[0]), INTERPOLATION_ROUNDING * 2)

    def test_tnum_reaches_the_tabular_punctuation(self):
        text, expected = TABULAR_TEXT
        for style in ALL_STYLES + VARIABLES:
            with self.subTest(style=style):
                run = shape(font_path(style), text, features="tnum")
                self.assertEqual(names(run), expected)
                self.assertEqual(len(set(advances(run[::2]))), 1)
                self.assertEqual(len(set(advances(run[1::2]))), 1)

    def test_local_forms_follow_the_language(self):
        for style in ALL_STYLES:
            path = font_path(style)
            for language, text, expected in LANGUAGE_FORMS:
                with self.subTest(style=style, language=language, text=text):
                    self.assertEqual(names(shape(path, text, language=language)), expected)

    def test_turkic_small_caps_keep_i_and_dotless_i_apart(self):
        for style in ALL_STYLES + VARIABLES:
            path = font_path(style)
            for language, feature, text, expected in TURKIC_SMALL_CAPS:
                with self.subTest(style=style, language=language, feature=feature):
                    self.assertEqual(names(shape(path, text, features=feature, language=language)), expected)

    def test_local_forms_give_way_to_small_caps(self):
        for style in ALL_STYLES:
            path = font_path(style)
            for language, text, expected in LOCAL_SMALL_CAPS:
                with self.subTest(style=style, language=language):
                    self.assertEqual(names(shape(path, text, features="smcp", language=language)), expected)

    def test_small_caps_reach_every_cased_letter(self):
        cmap = font(STYLES[0]).getBestCmap()
        for feature, category, flip in (("smcp", "Ll", str.upper), ("c2sc", "Lu", str.lower)):
            letters = [chr(code) for code in sorted(cmap) if code not in NOT_SMALL_CAPS and unicodedata.category(chr(code)) == category]
            letters = [letter for letter in letters if flip(letter) != letter and all(ord(char) in cmap for char in flip(letter))]
            for style in ALL_STYLES + VARIABLES:
                for letter, run in zip(letters, shape_lines(font_path(style), letters, features=feature)):
                    with self.subTest(style=style, feature=feature, letter=letter):
                        self.assertTrue(any(name.endswith(".sc") for name in names(run)), names(run))

    def test_variable_instances_shape(self):
        for styles, variable in ((STYLES, VARIABLES[0]), (ITALIC_STYLES, VARIABLES[1])):
            path = font_path(variable)
            totals = {}
            for weight in INSTANCE_WEIGHTS:
                with self.subTest(variable=variable, weight=weight):
                    run = shape(path, SAMPLE, variations=f"wght={weight}")
                    self.assertEqual(len(run), len(SAMPLE))
                    self.assertNotIn(".notdef", names(run))
                    self.assertTrue(all(advance > 0 for advance in advances(run)))
                    totals[weight] = sum(advances(run))
            statics = {
                font(style)["OS/2"].usWeightClass: sum(advances(shape(font_path(style), SAMPLE)))
                for style in styles
            }
            for weight in MASTER_WEIGHTS:
                self.assertEqual(totals[weight], statics[weight])
            ordered = [totals[weight] for weight in INSTANCE_WEIGHTS]
            self.assertEqual(ordered, sorted(set(ordered)))


if __name__ == "__main__":
    unittest.main()
