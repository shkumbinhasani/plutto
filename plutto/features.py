import math
import re
import unicodedata
from functools import lru_cache

import numpy

from .geometry import closed_segments, head
from . import accents, capitals, greek
from .glyphs import DIGITS, EXTENSIONS, GLYPHS, base_drawing, drawn_alike, render
from .masters import ALL_MASTERS, LIGHT, REGULAR, XH, family, roman_of
from .oblique import narrowed_x

FIRST = {
    "A": ["A", "Alphatonos"],
    "T": ["T"],
    "Ge": ["uni0413", "uni0490", "uni0403", "Gamma"],
    "V": ["V"],
    "W": ["W"],
    "Y": ["Y", "uni0423", "uni040E", "Upsilontonos"],
    "L": ["L"],
    "F": ["F"],
    "P": ["P"],
    "K": ["K", "X", "uni0416"],
    "R": ["R"],
    "O": ["O", "D", "Q", "Omicrontonos"],
    "r": ["r", "uni0433", "uni0491", "uni0453"],
    "v": ["v", "w", "y", "nu", "gamma"],
    "k": ["k", "x", "uni0436", "chi", "kgreenlandic"],
    "o": ["b", "e", "o", "p"],
    "soft": ["uni042C", "uni042A", "uni0409", "uni040A", "uni044C", "uni044A", "uni0459", "uni045A"],
    "Ef": ["uni0424", "Phi"],
    "Psi": ["Psi"],
    "zeta": ["zeta", "xi"],
    "f": ["f"],
    "dot": ["period", "comma", "ellipsis"],
    "dash": ["hyphen", "endash", "emdash"],
    "quote": ["quoteleft", "quotedblleft", "quotesingle", "quotedbl", "quoteright", "quotedblright"],
    "guillemet": ["guillemotleft", "guilsinglleft"],
    "guillemet_case": ["guillemotleft.case", "guilsinglleft.case"],
    "one": ["one"],
    "four": ["four"],
    "seven": ["seven"],
    "slash": ["slash"],
    "open": ["parenleft", "braceleft"],
    "Z": ["Z"],
}

SECOND = {
    "A": ["A"],
    "T": ["T"],
    "V": ["V"],
    "W": ["W"],
    "Y": ["Y", "uni0423", "uni040E"],
    "X": ["X", "uni0416"],
    "J": ["J"],
    "O": ["O", "C", "G", "Q"],
    "o": ["a", "c", "d", "e", "g", "o", "q", "epsilon", "sigma", "sigma1", "phi"],
    "s": ["s"],
    "n": [
        "m", "n", "p", "r", "u", "iota", "upsilon", "omega", "psi", "mu", "kgreenlandic",
        "uni0432", "uni0433", "uni043C", "uni0446", "uni0447", "uni0449", "uni044C", "uni0491", "uni045A", "uni049B", "uni04B7",
    ],
    "el": ["uni043B", "uni0459", "uni0434", "uni0437"],
    "El": ["uni041B", "uni0409", "uni0414"],
    "te": ["uni0442", "uni044A", "uni04AD"],
    "Ef": ["uni0424", "Phi"],
    "lambda": ["lambda"],
    "v": ["v", "w", "y", "nu", "gamma"],
    "x": ["x", "uni0436", "chi"],
    "z": ["z"],
    "t": ["t", "f", "tau", "pi", "fi", "fl"],
    "dot": ["period", "comma", "ellipsis"],
    "dash": ["hyphen", "endash", "emdash"],
    "quote": ["quoteright", "quotedblright", "quotesingle", "quotedbl", "quoteleft", "quotedblleft"],
    "guillemet": ["guillemotright", "guilsinglright"],
    "guillemet_case": ["guillemotright.case", "guilsinglright.case"],
    "one": ["one"],
    "four": ["four"],
    "seven": ["seven"],
    "slash": ["slash"],
    "round_figure": [name for name in ["zero", "zero.slash", "six", "eight", "nine"] if name in GLYPHS],
    "open_figure": ["three"],
    "five": ["five"],
    "colon": ["colon", "semicolon"],
    "U": ["U"],
    "Z": ["Z"],
    "close": ["parenright", "braceright"],
}

PAIRS = [
    ("A", "T", -96, -102),
    ("A", "V", -88, -106),
    ("A", "W", -82, -100),
    ("A", "Y", -98, -114),
    ("A", "O", -36, -50),
    ("A", "v", -36, -56),
    ("A", "t", -8, -6),
    ("A", "quote", -66, -74),
    ("A", "J", -28, -48),
    ("T", "A", -96, -102),
    ("T", "J", -70, -74),
    ("T", "O", -64, -64),
    ("T", "o", -88, -88),
    ("T", "s", -90, -86),
    ("T", "n", -78, -74),
    ("T", "v", -76, -84),
    ("T", "x", -76, -82),
    ("T", "z", -88, -82),
    ("T", "dot", -104, -98),
    ("T", "dash", -72, -68),
    ("V", "A", -88, -106),
    ("V", "J", -38, -56),
    ("V", "O", -36, -50),
    ("V", "o", -54, -68),
    ("V", "s", -58, -66),
    ("V", "n", -40, -50),
    ("V", "dot", -78, -84),
    ("V", "dash", -34, -46),
    ("W", "A", -80, -100),
    ("W", "J", -30, -50),
    ("W", "o", -42, -58),
    ("W", "s", -46, -56),
    ("W", "n", -28, -40),
    ("W", "dot", -66, -72),
    ("W", "dash", -32, -36),
    ("Y", "A", -98, -114),
    ("Y", "J", -50, -66),
    ("Y", "O", -50, -62),
    ("Y", "o", -76, -86),
    ("Y", "s", -72, -80),
    ("Y", "n", -58, -66),
    ("Y", "v", -58, -76),
    ("Y", "x", -56, -74),
    ("Y", "z", -72, -74),
    ("Y", "dot", -90, -94),
    ("Y", "dash", -54, -62),
    ("L", "T", -104, -98),
    ("L", "V", -76, -82),
    ("L", "W", -68, -76),
    ("L", "Y", -86, -92),
    ("L", "O", -36, -40),
    ("L", "v", -44, -54),
    ("L", "dash", -32, -34),
    ("L", "quote", -90, -80),
    ("F", "A", -66, -72),
    ("F", "J", -48, -52),
    ("F", "o", -40, -42),
    ("F", "s", -46, -40),
    ("F", "dot", -90, -84),
    ("F", "z", -44, -36),
    ("F", "n", -32, -26),
    ("F", "v", -30, -38),
    ("F", "x", -28, -36),
    ("P", "A", -58, -72),
    ("P", "J", -40, -52),
    ("P", "o", -30, -40),
    ("P", "dot", -100, -92),
    ("P", "s", -38, -40),
    ("K", "O", -36, -48),
    ("K", "o", -30, -44),
    ("K", "v", -36, -54),
    ("K", "dash", -50, -46),
    ("R", "T", -16, -14),
    ("R", "V", -18, -16),
    ("R", "Y", -26, -22),
    ("R", "o", -8, -6),
    ("O", "A", -34, -48),
    ("O", "T", -16, -14),
    ("O", "V", -14, -12),
    ("O", "W", -8, -6),
    ("O", "Y", -24, -20),
    ("O", "X", -20, -18),
    ("O", "dot", -20, -18),
    ("r", "n", 0, 0),
    ("r", "o", -20, -24),
    ("r", "dot", -70, -64),
    ("r", "dash", -24, -20),
    ("v", "o", -10, -20),
    ("v", "dot", -60, -54),
    ("k", "o", -20, -16),
    ("k", "dash", -30, -26),
    ("k", "s", -12, -22),
    ("o", "v", -10, -8),
    ("o", "x", -14, -12),
    ("f", "o", -26, -36),
    ("f", "dot", -60, -62),
    ("dot", "T", -104, -98),
    ("dot", "V", -78, -84),
    ("dot", "W", -66, -72),
    ("dot", "Y", -90, -94),
    ("dot", "quote", -50, -44),
    ("dash", "T", -72, -68),
    ("dash", "V", -34, -46),
    ("dash", "W", -32, -36),
    ("dash", "Y", -54, -62),
    ("dash", "X", -40, -36),
    ("quote", "A", -66, -74),
    ("T", "guillemet", -58, -42),
    ("V", "guillemet", -38, -40),
    ("V", "v", -38, -60),
    ("W", "guillemet", -36, -38),
    ("W", "v", -26, -50),
    ("Y", "guillemet", -44, -46),
    ("L", "guillemet", 10, 12),
    ("L", "J", -32, -40),
    ("r", "guillemet", 10, 12),
    ("guillemet", "T", -58, -42),
    ("guillemet", "V", -38, -40),
    ("guillemet", "W", -36, -38),
    ("guillemet", "Y", -44, -46),
    ("quote", "J", -44, -50),
    ("one", "seven", -8, -6),
    ("one", "one", -12, -10),
    ("one", "round_figure", -22, -16),
    ("one", "open_figure", -12, -8),
    ("one", "five", -22, -16),
    ("one", "dash", -16, -12),
    ("one", "dot", -8, -6),
    ("seven", "dot", -84, -74),
    ("seven", "colon", -22, -18),
    ("seven", "four", -42, -36),
    ("seven", "one", -16, -12),
    ("seven", "dash", -30, -26),
    ("seven", "slash", -36, -30),
    ("four", "seven", -10, -8),
    ("four", "one", -6, -4),
    ("dash", "one", -14, -12),
    ("dash", "seven", -26, -22),
    ("dot", "seven", -24, -20),
    ("dot", "one", -10, -8),
    ("slash", "four", -28, -24),
    ("slash", "one", -10, -8),
    ("Ge", "A", -90, -94),
    ("Ge", "J", -70, -74),
    ("Ge", "O", -64, -64),
    ("Ge", "o", -100, -92),
    ("Ge", "s", -90, -86),
    ("Ge", "n", -78, -74),
    ("Ge", "v", -76, -84),
    ("Ge", "x", -76, -82),
    ("Ge", "z", -88, -82),
    ("Ge", "dot", -150, -140),
    ("Ge", "dash", -110, -96),
    ("Ge", "guillemet", -58, -42),
    ("Ge", "el", -110, -116),
    ("Ge", "El", -80, -90),
    ("Ge", "Ef", -130, -120),
    ("T", "el", -130, -139),
    ("T", "Ef", -131, -123),
    ("Y", "el", -105, -124),
    ("Y", "Ef", -64, -76),
    ("v", "el", -52, -60),
    ("v", "lambda", -70, -74),
    ("r", "el", -56, -44),
    ("A", "te", -70, -50),
    ("A", "Ef", -57, -70),
    ("K", "te", -64, -62),
    ("K", "Ef", -70, -78),
    ("soft", "T", -131, -119),
    ("soft", "Y", -76, -74),
    ("soft", "te", -76, -76),
    ("Ef", "A", -50, -64),
    ("Ef", "T", -101, -85),
    ("Ef", "X", -64, -60),
    ("Ef", "dot", -70, -56),
    ("Psi", "dot", -120, -96),
    ("zeta", "o", -80, -60),
    ("o", "lambda", -36, -46),
    ("dot", "v", -44, -56),
    ("O", "J", -26, -34),
    ("L", "U", -24, -28),
    ("K", "n", -12, -20),
    ("K", "t", -12, -18),
    ("K", "s", -22, -30),
    ("K", "z", -20, -28),
    ("K", "x", -10, -14),
    ("k", "t", -10, -16),
    ("open", "A", -38, -42),
    ("A", "close", -38, -42),
    ("open", "X", -20, -24),
    ("K", "close", -20, -24),
    ("open", "x", -12, -16),
    ("k", "close", -12, -16),
    ("dash", "Z", -28, -24),
    ("Z", "dash", -28, -24),
    ("dash", "A", -22, -26),
    ("A", "dash", -22, -26),
    ("guillemet", "X", -14, -20),
    ("K", "guillemet", -14, -20),
    ("guillemet", "A", -38, -39),
    ("A", "guillemet", -38, -39),
    ("quote", "T", -44, -44),
    ("T", "quote", -44, -44),
    ("quote", "Y", -28, -37),
    ("Y", "quote", -28, -36),
    ("quote", "V", -22, -28),
    ("V", "quote", -22, -28),
    ("quote", "W", -22, -22),
    ("W", "quote", -22, -22),
    ("guillemet_case", "A", -39, -40),
    ("A", "guillemet_case", -39, -40),
    ("guillemet_case", "V", -39, -40),
    ("V", "guillemet_case", -39, -40),
    ("guillemet_case", "W", -36, -38),
    ("W", "guillemet_case", -36, -38),
    ("guillemet_case", "Y", -43, -46),
    ("Y", "guillemet_case", -43, -46),
    ("guillemet_case", "T", -59, -44),
    ("T", "guillemet_case", -59, -44),
    ("guillemet_case", "X", -13, -21),
    ("K", "guillemet_case", -13, -21),
]

BLACK_PAIRS = {
    ("K", "o"): -48,
    ("Y", "v"): -80,
    ("T", "J"): -56,
    ("V", "J"): -48,
    ("W", "J"): -44,
    ("Y", "J"): -58,
    ("F", "J"): -32,
    ("P", "J"): -38,
    ("A", "J"): -42,
    ("L", "J"): -26,
    ("quote", "J"): -36,
    ("O", "A"): -52,
    ("A", "O"): -54,
    ("V", "O"): -54,
    ("L", "T"): -88,
    ("L", "V"): -82,
    ("L", "Y"): -92,
    ("F", "A"): -70,
    ("F", "o"): -36,
    ("F", "s"): -32,
    ("T", "guillemet"): -32,
    ("guillemet", "T"): -32,
    ("Ge", "A"): -100,
    ("Ge", "n"): -54,
    ("Ge", "v"): -32,
    ("Ge", "x"): -31,
    ("r", "el"): -30,
    ("K", "te"): -46,
    ("Ge", "J"): -56,
    ("Ge", "guillemet"): -32,
    ("Ge", "Ef"): -78,
    ("T", "el"): -126,
    ("T", "Ef"): -84,
    ("Y", "el"): -128,
    ("Y", "Ef"): -66,
    ("A", "te"): -31,
    ("A", "Ef"): -74,
    ("K", "Ef"): -66,
    ("soft", "T"): -104,
    ("soft", "Y"): -70,
    ("soft", "te"): -66,
    ("Ef", "A"): -68,
    ("Ef", "T"): -62,
    ("Ef", "X"): -56,
    ("Ef", "dot"): -36,
    ("Psi", "dot"): -40,
    ("zeta", "o"): -36,
    ("o", "lambda"): -56,
    ("A", "V"): -110,
    ("V", "A"): -110,
    ("A", "W"): -104,
    ("W", "A"): -104,
    ("A", "Y"): -117,
    ("Y", "A"): -117,
    ("guillemet", "A"): -42,
    ("A", "guillemet"): -42,
    ("quote", "T"): -39,
    ("T", "quote"): -39,
    ("quote", "Y"): -41,
    ("Y", "quote"): -37,
    ("quote", "V"): -34,
    ("V", "quote"): -34,
    ("quote", "W"): -30,
    ("W", "quote"): -30,
    ("guillemet_case", "A"): -41,
    ("A", "guillemet_case"): -41,
    ("guillemet_case", "V"): -41,
    ("V", "guillemet_case"): -41,
    ("guillemet_case", "W"): -39,
    ("W", "guillemet_case"): -39,
    ("guillemet_case", "Y"): -46,
    ("Y", "guillemet_case"): -46,
    ("guillemet_case", "T"): -32,
    ("T", "guillemet_case"): -32,
    ("guillemet_case", "X"): -23,
    ("K", "guillemet_case"): -23,
}

MARKLESS = ("soft", "Ef", "Psi", "zeta", "lambda", "El", "te")
CLEARANCE = [
    (["parenleft", "bracketleft", "braceleft", "backslash", "q", "g", "j", "l", "bracketright", "comma", "semicolon", "underscore", "chi"], ["j"], 1.0),
    (["f"], ["parenright", "bracketright", "braceright"], 0.7),
    (["f"], ["quotesingle", "quotedbl", "quoteright", "quotedblright", "quoteleft", "quotedblleft", "question", "exclam", "asterisk"], 1.0),
    (["Aogonek", "Eogonek", "aogonek", "eogonek", "iogonek", "uogonek"], ["j", "y", "f", "parenright", "bracketright", "braceright"], 0.7),
    (["Aogonek", "Eogonek", "aogonek", "eogonek", "iogonek", "uogonek"], ["slash", "chi"], 0.3),
    (["uni0438", "uni0439", "uni045D", "uni04E3", "uni04E5"], ["x", "z", "Z", "A", "X", "two", "guillemotright", "guilsinglright", "uni0436"], 0.34),
]
OPENERS = [
    "parenleft", "bracketleft", "braceleft", "slash", "backslash",
    "quoteleft", "quotedblleft", "comma", "quotesingle", "quotedbl", "guillemotleft", "guilsinglleft",
]
ITALIC_CLEARANCE = [(OPENERS, ["f", "fi", "fl", "j"], 1.0)]
FLOOR_LEFT = [
    "f", "g", "i", "k", "l", "q", "r", "t", "v", "w", "x", "y", "longs", "A", "K", "L", "V", "W", "X", "Y",
    "comma", "semicolon", "colon", "slash", "backslash", "parenleft", "bracketleft", "bracketright",
    "plusminus", "lessequal", "greaterequal", "summation", "product", "integral", "increment", "currency",
    "uni0413", "uni0490", "uni0403", "uni0433", "uni0491", "uni0453", "uni0423", "uni040E", "uni0416", "uni0436",
    "Upsilontonos", "Upsilondieresis",
]
FLOOR_RIGHT = [
    "j", "t", "x", "A", "V", "W", "X", "Y", "AE", "four", "slash", "backslash", "parenright", "bracketright",
    "currency", "trademark", "copyright", "registered", "equal", "notequal", "approxequal", "arrowup", "arrowright",
    "summation", "product", "integral", "increment", "uni0423", "uni040E", "uni0416", "uni0436",
]
DIAGONAL = ["A", "K", "V", "W", "X", "Y", "k", "v", "w", "x", "y", "uni0416", "uni0436", "uni0423", "uni040E"]
CLEAR_GAP = 20
CORNER_GAP = 16
MARK_ROOM = 2 * CLEAR_GAP
BAND = 4
SMALLEST_KERN = 6
LARGEST_DRIFT = 40
STRAY_DRIFT = 5
NEAR_DEPTH = 80
NEAREST_SLACK = 5
KERNED_BAR_SIDE = (28, 20)
TONOS_BASES = {name: base for name, _, base in greek.CAPITAL_TONOS_LETTERS}
TIGHTENED = {
    capitals.capital_a: "diagonal",
    capitals.capital_v: "diagonal",
    capitals.capital_w: "diagonal",
    capitals.capital_y: "diagonal",
    capitals.capital_t: "bar",
}
KERN_ROUNDING = 1
ANCHOR = re.compile(r"<anchor (-?\d+) (-?\d+)>")
VALUE_RECORD = re.compile(r"pos (\S+?)('?) <(-?\d+) (-?\d+) (-?\d+) (-?\d+)>")


def widen(classes, like):
    widened = {}
    for name, members in classes.items():
        extra = [glyph for glyph, base in like.items() if base in members and glyph in GLYPHS]
        widened[name] = members + [glyph for glyph in extra if glyph not in members]
    return widened


def outline(glyph, step=4):
    for contour in glyph.contours:
        here = contour.start
        for segment in closed_segments(contour):
            bezier = (here, *segment) if len(segment) == 3 else (here, here, segment[0], segment[0])
            count = max(2, int(math.dist(here, segment[-1]) / step) + 1)
            for index in range(count):
                yield head(bezier, index / count)[3]
            here = segment[-1]


def profile(glyph, edge):
    extremes = {}
    for x, y in outline(glyph):
        band = round(y / BAND)
        extremes[band] = edge(extremes.get(band, x), x)
    return extremes


def side_gap(glyph):
    xs = [x for x, _ in outline(glyph)]
    return glyph.advance - max(xs) + min(xs)


def needed_kern(left, right, gap):
    ink = profile(left, max)
    other = profile(right, min)
    reach = int(gap / BAND)
    needed = None
    for band, x in other.items():
        for offset in range(-reach, reach + 1):
            if band + offset not in ink:
                continue
            rise = offset * BAND
            kern = ink[band + offset] - left.advance - x + math.sqrt(max(gap * gap - rise * rise, 0))
            needed = kern if needed is None else max(needed, kern)
    return needed or 0


@lru_cache(maxsize=None)
def edge_profile(name, master, right_side):
    return profile(render(name, master), max if right_side else min)


@lru_cache(maxsize=None)
def gap_profile(left, right, master):
    ink = edge_profile(left, master, True)
    other = edge_profile(right, master, False)
    advance = render(left, master).advance
    return {band: other[band] + advance - ink[band] for band in ink if band in other}


def nearest_gap(left, right, master):
    gaps = gap_profile(left, right, master)
    return min(gaps.values()) if gaps else None


def clipped_drift(change):
    return max(-LARGEST_DRIFT, min(LARGEST_DRIFT, change))


def italic_form(left, right):
    return not (drawn_alike(left) and drawn_alike(right))


@lru_cache(maxsize=None)
def nearest_drift(left, right, master):
    upright = nearest_gap(left, right, roman_of(master))
    slanted = nearest_gap(left, right, master)
    if upright is None or slanted is None or master.italic and italic_form(left, right):
        return None
    return clipped_drift(slanted - upright * master.narrowing)


def white_drift(left, right, master):
    upright = {band: gap * master.narrowing for band, gap in gap_profile(left, right, roman_of(master)).items()}
    slanted = gap_profile(left, right, master)
    bands = [band for band in upright if band in slanted]
    if not bands:
        return None
    limit = min(upright.values()) + NEAR_DEPTH * master.narrowing
    return sum(min(slanted[band], limit) - min(upright[band], limit) for band in bands) / len(bands)


def near_enough(left, right, master, drift):
    nearest = nearest_drift(left, right, master)
    return nearest is None or abs(drift - nearest) <= NEAREST_SLACK - KERN_ROUNDING


@lru_cache(maxsize=None)
def member_drift(left, right, master):
    nearest = nearest_drift(left, right, master)
    if nearest is None:
        return None
    white = white_drift(left, right, master)
    if white is None:
        return nearest
    slack = NEAREST_SLACK - KERN_ROUNDING
    return max(nearest - slack, min(nearest + slack, clipped_drift(white)))


@lru_cache(maxsize=None)
def gap_drift(first, second, master):
    changes = [member_drift(left, right, master) for left in FIRST[first] for right in SECOND[second]]
    changes = [change for change in changes if change is not None]
    if not changes:
        return 0.0
    return clipped_drift(sum(changes) / len(changes))


@lru_cache(maxsize=None)
def strays(first, second, master):
    found = []
    for left in FIRST[first]:
        for right in SECOND[second]:
            drifts = [(member_drift(left, right, each), gap_drift(first, second, each), each) for each in family(master)]
            if any(own is not None and (abs(own - shared) > STRAY_DRIFT or not near_enough(left, right, each, shared)) for own, shared, each in drifts):
                found.append((left, right))
    return found


def kin_of(name, like, classes=None):
    names = classes[name] if classes else [name]
    return names + [glyph for glyph, kin in like.items() if kin in names and glyph in GLYPHS and glyph not in names]


def letter_or_figure(name):
    base = all_like().get(name, name)
    return len(base) == 1 and base.isalpha() or base in DIGITS


def least_gap(master, left, right, designed):
    like = all_like()
    touching = 2 * master.bearing("cap_diagonal")
    if like.get(left, left) in DIAGONAL and like.get(right, right) in DIAGONAL:
        return touching
    if not letter_or_figure(left) and not letter_or_figure(right):
        return touching
    clear = master.bearing("cap_diagonal") / 2 + CLEAR_GAP
    if corners_meet(left, right, master):
        clear = min(clear, CORNER_GAP)
    return min(clear, designed)


def corners_meet(left, right, master):
    gaps = gap_profile(left, right, master)
    line = round(XH / BAND)
    if line not in gaps or len(gaps) < 2:
        return False
    below = [gap for band, gap in gaps.items() if band < line]
    above = [gap for band, gap in gaps.items() if band > line]
    if not below or gaps[line] + NEAR_DEPTH > min(below):
        return False
    if not above:
        return True
    like = all_like()
    return like.get(left, left) in FIRST["T"] and like.get(right, right) in DIAGONAL and min(above) - gaps[line] + CORNER_GAP >= MARK_ROOM


def designed_gap(left, right, regular=0, bold=0):
    gaps = [nearest_gap(left, right, master) for master in (LIGHT, REGULAR)]
    if None in gaps:
        return None
    return min(gap + master.v(regular, bold) for gap, master in zip(gaps, (LIGHT, REGULAR)))


def meet_in_text(left, right):
    like = all_like()
    for one, other in ((left, right), (right, left)):
        base = like.get(other, other)
        if one.endswith(".case") and len(base) == 1 and base.islower():
            return False
    return True


def worth_kerning(shortfall, least):
    return round(shortfall) >= min(SMALLEST_KERN, least / 2)


def spacing_like():
    like = {}
    for extension in EXTENSIONS:
        if extension is not accents:
            like.update(extension.KERN_LIKE)
    return like


def pair_weight(first, second, regular, bold, master):
    return master.v(regular, bold, black=BLACK_PAIRS.get((first, second)))


def tightening(name, master):
    kind = TIGHTENED.get(base_drawing(TONOS_BASES.get(name, name)))
    if kind == "diagonal":
        return master.bearing("cap_diagonal") - master.v(*capitals.OPEN_DIAGONAL_SIDE)
    if kind == "bar":
        return master.v(*KERNED_BAR_SIDE) - master.v(*capitals.BAR_SIDE)
    return 0.0


def designed(first, second, regular, bold, left, right, master):
    shift = tightening(left, master) + tightening(right, master)
    value = pair_weight(first, second, regular, bold, master) + shift
    return (min(0.0, value) if shift else value) * master.narrowing


def leads(first, second):
    return FIRST[first][0], SECOND[second][0]


def drifted_value(first, second, regular, bold, master, left=None, right=None):
    lead_left, lead_right = leads(first, second)
    value = designed(first, second, regular, bold, left or lead_left, right or lead_right, master)
    if master.italic:
        value -= gap_drift(first, second, master)
    return value


def member_value(first, second, regular, bold, left, right, master):
    if master.italic and (left, right) in strays(first, second, master):
        return designed(first, second, regular, bold, left, right, master) - member_drift(left, right, master)
    return drifted_value(first, second, regular, bold, master, left, right)


@lru_cache(maxsize=None)
def respaced(first, second, regular, bold, master):
    lead = [designed(first, second, regular, bold, *leads(first, second), each) for each in family(master)]
    return [
        (left, right)
        for left in FIRST[first]
        for right in SECOND[second]
        if [designed(first, second, regular, bold, left, right, each) for each in family(master)] != lead
    ]


@lru_cache(maxsize=None)
def shortfalls(first, second, regular, bold, master):
    like = spacing_like()
    found = {}
    for left in FIRST[first]:
        for right in SECOND[second]:
            value = member_value(first, second, regular, bold, left, right, master)
            lift, worth = 0.0, False
            for one in kin_of(left, like):
                for other in kin_of(right, like):
                    if not meet_in_text(one, other):
                        continue
                    gap = nearest_gap(one, other, master)
                    designed = designed_gap(one, other, regular, bold)
                    if gap is None or designed is None:
                        continue
                    least = least_gap(master, one, other, designed)
                    lift = max(lift, least - gap - value)
                    worth = worth or worth_kerning(least - gap - value, least)
            found[(left, right)] = (value, lift, worth)
    return found


@lru_cache(maxsize=None)
def lifts(first, second, regular, bold, master):
    found = {each: shortfalls(first, second, regular, bold, each) for each in ALL_MASTERS}
    kept = sorted(pair for pair in found[master] if any(values[pair][2] for values in found.values()))
    same_weight = [each for each in ALL_MASTERS if each.weight == master.weight]
    return {pair: found[master][pair][0] + max(found[each][pair][1] for each in same_weight) for pair in kept}


def class_value(first, second, regular, bold, master):
    return drifted_value(first, second, regular, bold, master)


def class_kern(first, second, regular, bold, master):
    return round(class_value(first, second, regular, bold, master))


def pair_value(left, right, master):
    for first, second, regular, bold in PAIRS:
        if left in FIRST[first] and right in SECOND[second]:
            lifted = lifts(first, second, regular, bold, master)
            return lifted.get((left, right), member_value(first, second, regular, bold, left, right, master))
    return floor_kerns(master).get((left, right), 0)


def exception_values(master, like):
    found = {}
    for first, second, regular, bold in PAIRS:
        lifted = lifts(first, second, regular, bold, master)
        for left, right in (strays(first, second, master) if master.italic else []) + respaced(first, second, regular, bold, master):
            value = pair_value(left, right, master)
            for one in kin_of(left, like):
                for other in kin_of(right, like):
                    found.setdefault((one, other), value)
        for (left, right), value in lifted.items():
            for one in kin_of(left, like):
                for other in kin_of(right, like):
                    found[(one, other)] = value
    return found


def stray_pairs(master, like):
    return [f"    pos {left} {right} {round(value)};" for (left, right), value in exception_values(master, like).items()]


def clearance(master):
    drawn = {}

    def glyph(name):
        if name not in drawn:
            drawn[name] = render(name, master)
        return drawn[name]

    found = {}
    for lefts, rights, share in CLEARANCE + (ITALIC_CLEARANCE if master.italic else []):
        gap = side_gap(glyph("o")) * share
        for left in lefts:
            for right in rights:
                if left in GLYPHS and right in GLYPHS:
                    found[(left, right)] = max(0, needed_kern(glyph(left), glyph(right), gap))
    return found


ITALIC_FLOOR_LEFT = ["a", "d", "u", "l", "t", "uni0501", "k", "v", "w", "x", "y", "uni0436"]
ITALIC_FLOOR_REACH = 2
EDGE_FLOOR = -100
EDGE_CEILING = 400


@lru_cache(maxsize=None)
def edge_array(name, master, right_side):
    found = edge_profile(name, master, right_side)
    edge = numpy.full(EDGE_CEILING - EDGE_FLOOR, numpy.nan)
    for band, x in found.items():
        if EDGE_FLOOR <= band < EDGE_CEILING:
            edge[band - EDGE_FLOOR] = x
    return edge


def plain_gap(left, right, master):
    gaps = edge_array(right, master, False) + render(left, master).advance - edge_array(left, master, True)
    return None if numpy.isnan(gaps).all() else float(numpy.nanmin(gaps))


@lru_cache(maxsize=None)
def floor_candidates():
    like = all_like()
    return [name for name, (code, _) in GLYPHS.items() if code is not None and name not in like and unicodedata.category(chr(code))[0] in "LNP"]


@lru_cache(maxsize=None)
def italic_floor_needs(master):
    target = master.bearing("cap_diagonal") / 2 + CLEAR_GAP
    roman = roman_of(master)
    found = {}
    for left in ITALIC_FLOOR_LEFT:
        for right in floor_candidates():
            gap = plain_gap(left, right, master)
            if gap is None or gap >= ITALIC_FLOOR_REACH * target:
                continue
            upright = plain_gap(left, right, roman)
            least = target if upright is None else min(target, upright + pair_value(left, right, roman))
            need = needed_kern(render(left, master), render(right, master), least)
            if need > 0:
                found[(left, right)] = need
    return found


def italic_floor_kerns(master):
    if not master.italic:
        return {}
    found = {each: italic_floor_needs(each) for each in family(master)}
    kept = sorted({pair for values in found.values() for pair, need in values.items() if round(need) >= SMALLEST_KERN})
    like = all_like()
    values = {}
    for left, right in kept:
        for one in kin_of(left, like):
            for other in kin_of(right, like):
                values[(one, other)] = found[master].get((left, right), 0.0)
    return values


def lookup_values(lines, classes):
    found = {}
    for line in lines:
        match = PAIR_RULE.match(line)
        if not match:
            continue
        left, right, value = match.groups()
        lefts, rights = glyph_set(left, classes), glyph_set(right, classes)
        if left.startswith("@") and lefts is None or right.startswith("@") and rights is None:
            continue
        for one in lefts or [left]:
            for other in rights or [right]:
                found.setdefault((one, other), int(value))
    return found


def kerned_values(text):
    classes = {name: members.split() for name, members in CLASS_DEFINITION.findall(text)}
    found = {}
    for block in KERN_BLOCK.findall(text):
        groups = [inner for _, _, inner in LOOKUP_BLOCK.findall(block)] + [LOOKUP_BLOCK.sub("", block)]
        for group in groups:
            for pair, value in lookup_values(group.split("\n"), classes).items():
                found[pair] = found.get(pair, 0) + value
    return found


def italic_floor_lookup(master, text):
    floors = italic_floor_kerns(master)
    if not floors:
        return []
    kerned = kerned_values(text)
    lines = [f"        pos {left} {right} {max(0, round(value - kerned.get((left, right), 0)))};" for (left, right), value in floors.items()]
    return ["feature kern {", "    lookup italic_floor {", *lines, "    } italic_floor;", "} kern;"]


def clearance_pairs(master, like):
    found = {each.name: clearance(each) for each in family(master)}
    kept = sorted(pair for pair in found[master.name] if any(values[pair] >= SMALLEST_KERN for values in found.values()))
    lines = []
    for left, right in kept:
        value = round(found[master.name][(left, right)])
        for first in [left] + [name for name, kin in like.items() if kin == left and name in GLYPHS]:
            for second in [right] + [name for name, kin in like.items() if kin == right and name in GLYPHS]:
                lines.append(f"    pos {first} {second} {value};")
    return lines


@lru_cache(maxsize=None)
def widened_classes():
    like = all_like()
    return widen(FIRST, like), widen(SECOND, like)


def classed(left, right, like):
    first_classes, second_classes = widened_classes()
    for first, second, _, _ in PAIRS:
        if left in first_classes[first] and right in second_classes[second]:
            return True
    return any(like.get(left, left) in lefts and like.get(right, right) in rights for lefts, rights, _ in CLEARANCE)


def all_like():
    like = {}
    for extension in EXTENSIONS:
        like.update(extension.KERN_LIKE)
    return like


@lru_cache(maxsize=None)
def floor_shortfalls(master):
    found = {}
    for left in FLOOR_LEFT:
        for right in FLOOR_RIGHT:
            gap = nearest_gap(left, right, master)
            designed = designed_gap(left, right)
            if gap is not None and designed is not None and not classed(left, right, all_like()):
                least = least_gap(master, left, right, designed)
                found[(left, right)] = (max(0.0, least - gap), least)
    return found


@lru_cache(maxsize=None)
def floor_kerns(master):
    found = {each: floor_shortfalls(each) for each in family(master)}
    kept = [pair for pair in found[master] if any(worth_kerning(*values[pair]) for values in found.values())]
    return {pair: found[master][pair][0] for pair in sorted(kept)}


def floor_pairs(master, like):
    lines = []
    for (left, right), value in floor_kerns(master).items():
        for first in kin_of(left, like):
            for second in kin_of(right, like):
                if first == left and second == right or not classed(first, second, like):
                    lines.append(f"    pos {first} {second} {round(value)};")
    return lines


def whole(value):
    return math.floor(value + 0.5)


def narrowed_anchor(match, master):
    x, y = int(match[1]), int(match[2])
    return f"<anchor {whole(narrowed_x((x, y), master.slope, master.narrowing))} {y}>"


def narrowed_record(match, master):
    name, marked = match[1], match[2]
    x, y, advance, rise = (int(value) for value in match.groups()[2:])
    own = render(name, master).advance
    room = whole(own + advance * master.narrowing) - whole(own)
    return f"pos {name}{marked} <{whole(x * master.narrowing)} {y} {room} {rise}>"


def narrowed_positions(text, master):
    if master.narrowing == 1:
        return text
    text = ANCHOR.sub(lambda match: narrowed_anchor(match, master), text)
    return VALUE_RECORD.sub(lambda match: narrowed_record(match, master), text)


def drawn_feature_text(master):
    like = {}
    for extension in EXTENSIONS:
        like.update(extension.KERN_LIKE)
    lines = ["languagesystem DFLT dflt;", "languagesystem latn dflt;"]
    lines += [f"languagesystem latn {tag};" for extension in EXTENSIONS for tag in getattr(extension, "LANGUAGES", ())]
    lines += ["languagesystem cyrl dflt;"]
    lines += [f"languagesystem cyrl {tag};" for extension in EXTENSIONS for tag in getattr(extension, "CYRILLIC_LANGUAGES", ())]
    lines += ["languagesystem grek dflt;"]
    for name, members in widen(FIRST, like).items():
        lines.append(f"@first_{name} = [{' '.join(members)}];")
    for name, members in widen(SECOND, like).items():
        lines.append(f"@second_{name} = [{' '.join(members)}];")
    kern = clearance_pairs(master, like) + stray_pairs(master, like) + floor_pairs(master, like)
    for first, second, regular, bold in PAIRS:
        kern.append(f"    pos @first_{first} @second_{second} {class_kern(first, second, regular, bold, master)};")
    lines += ["feature kern {", *kern, "} kern;"]
    extensions = [narrowed_positions(extension.features(master), master) for extension in EXTENSIONS]
    lines += italic_floor_lookup(master, "\n".join(lines + extensions))
    lines.append("feature tnum {")
    for name in DIGITS:
        lines.append(f"    sub {name} by {name}.tnum;")
    lines.append("} tnum;")
    lines += extensions
    return "\n".join(lines) + "\n"


FOLD = 1
PAIR_RULE = re.compile(r"^\s*pos\s+(@[\w.]+|\[[^\]]*\]|[\w.]+)\s+(@[\w.]+|\[[^\]]*\]|[\w.]+)\s+(-?\d+);\s*$")
CLASS_DEFINITION = re.compile(r"^\s*@([\w.]+)\s*=\s*\[([^\]]*)\];", re.M)
KERN_BLOCK = re.compile(r"feature kern \{\n(.*?)\n\} kern;", re.S)
LOOKUP_BLOCK = re.compile(r"( *)lookup (\w+) \{\n(.*?)\n *\} \2;", re.S)
SINGLE_BYTES = 4
CELL_BYTES = 2
CLASS_BYTES = 6


def glyph_set(token, classes):
    if token.startswith("@"):
        return classes.get(token[1:])
    if token.startswith("["):
        return token[1:-1].split()
    return None


def pair_rules(lines, classes):
    rules = []
    for line in lines:
        if not line.strip() or CLASS_DEFINITION.match(line):
            continue
        match = PAIR_RULE.match(line)
        if not match:
            return None
        left, right, value = match.groups()
        lefts, rights = glyph_set(left, classes), glyph_set(right, classes)
        if left.startswith("@") and lefts is None or right.startswith("@") and rights is None:
            return None
        rules.append((left, right, int(value), lefts, rights, line))
    return rules


def pair_values(rules):
    singles, base = {}, {}
    for left, right, value, lefts, rights, _ in rules:
        if lefts is None and rights is None:
            singles.setdefault((left, right), value)
        else:
            for one in lefts or [left]:
                for other in rights or [right]:
                    base.setdefault((one, other), value)
    return {pair: value - base.get(pair, 0) for pair, value in singles.items()}


def distance(first, second, zero):
    return max(max(abs(a - b) for a, b in zip(first.get(cell, zero), second.get(cell, zero))) for cell in set(first) | set(second))


def loosest(first, second, zero):
    return {cell: tuple(max(a, b) for a, b in zip(first.get(cell, zero), second.get(cell, zero))) for cell in set(first) | set(second)}


def clustered(rows, width):
    zero = (0,) * width
    groups = []
    for key, row in sorted(rows.items(), key=lambda item: (-len(item[1]), item[0])):
        for group in groups:
            if distance(group["row"], row, zero) <= FOLD and distance(group["seed"], row, zero) <= FOLD:
                group["members"].append(key)
                group["row"] = loosest(group["row"], row, zero)
                break
        else:
            groups.append({"row": dict(row), "seed": dict(row), "members": [key]})
    return groups


def folded_matrix(deltas, width):
    rows = {}
    for (left, right), values in deltas.items():
        rows.setdefault(left, {})[right] = values
    row_groups = clustered(rows, width)
    columns = {}
    for index, group in enumerate(row_groups):
        for right, values in group["row"].items():
            columns.setdefault(right, {})[index] = values
    return row_groups, clustered(columns, width)


def matrix_cost(row_groups, column_groups):
    glyphs = sum(len(group["members"]) for group in row_groups + column_groups)
    return len(row_groups) * len(column_groups) * CELL_BYTES + glyphs * CLASS_BYTES


def matrix_lines(name, row_groups, column_groups, master_index, indent):
    lines = []
    for index, group in enumerate(row_groups):
        lines.append(f"{indent}@{name}_left_{index} = [{' '.join(group['members'])}];")
    for index, group in enumerate(column_groups):
        lines.append(f"{indent}@{name}_right_{index} = [{' '.join(group['members'])}];")
    for column_index, column in enumerate(column_groups):
        for row_index, values in column["row"].items():
            lines.append(f"{indent}pos @{name}_left_{row_index} @{name}_right_{column_index} {values[master_index]};")
    return lines


def folded_block(name, bodies, classes, indent):
    rules = [pair_rules(body.split("\n"), each) for body, each in zip(bodies, classes)]
    if any(each is None for each in rules):
        return None
    values = [pair_values(each) for each in rules]
    pairs = sorted(set().union(*values))
    if not pairs:
        return None
    deltas = {pair: tuple(each.get(pair, 0) for each in values) for pair in pairs}
    kept = {pair: delta for pair, delta in deltas.items() if max(abs(value) for value in delta) > FOLD}
    row_groups, column_groups = folded_matrix(kept, len(bodies)) if kept else ([], [])
    if kept and matrix_cost(row_groups, column_groups) >= len(pairs) * SINGLE_BYTES:
        return None
    results = []
    for index, each in enumerate(rules):
        base = [rule[5] for rule in each if rule[3] is not None or rule[4] is not None]
        results.append((base, matrix_lines(name, row_groups, column_groups, index, indent + "    ") if kept else []))
    return results


def folded_texts(texts):
    classes = [dict((name, members.split()) for name, members in CLASS_DEFINITION.findall(text)) for text in texts]
    pieces = [[] for _ in texts]
    cursors = [0 for _ in texts]
    blocks = [list(KERN_BLOCK.finditer(text)) for text in texts]
    for number in range(len(blocks[0])):
        matches = [each[number] for each in blocks]
        bodies = [match.group(1) for match in matches]
        folded = [fold_kern_body(bodies, classes, number)]
        for index, (text, match) in enumerate(zip(texts, matches)):
            pieces[index].append(text[cursors[index] : match.start(1)])
            pieces[index].append(folded[0][index])
            cursors[index] = match.end(1)
    return ["".join(each) + text[cursor:] for each, text, cursor in zip(pieces, texts, cursors)]


def fold_kern_body(bodies, classes, number):
    lookups = [list(LOOKUP_BLOCK.finditer(body)) for body in bodies]
    outside = [LOOKUP_BLOCK.sub("", body) for body in bodies]
    results = [[] for _ in bodies]
    loose = [line for line in outside[0].split("\n") if line.strip()]
    if loose and not lookups[0]:
        folded = folded_block(f"kern_{number}_pairs", bodies, classes, "")
        if folded:
            return [base_and_matrix(base, matrix, f"kern_{number}_pairs", "    ") for base, matrix in folded]
        return bodies
    texts = [[] for _ in bodies]
    starts = [0 for _ in bodies]
    for position in range(len(lookups[0])):
        matches = [each[position] for each in lookups]
        name, indent = matches[0].group(2), matches[0].group(1)
        called = any(f"lookup {name};" in body for body in bodies)
        inner = [match.group(3) for match in matches]
        folded = None if called else folded_block(name, inner, classes, indent)
        context = None if called or folded else folded_context(name, inner, classes, indent)
        for index, (body, match) in enumerate(zip(bodies, matches)):
            texts[index].append(body[starts[index] : match.start()])
            if folded:
                base, matrix = folded[index]
                texts[index].append(lookup_pieces(name, base, matrix, indent))
            elif context:
                texts[index].append(context[index])
            else:
                texts[index].append(match.group(0))
            starts[index] = match.end()
    return ["".join(each) + body[start:] for each, body, start in zip(texts, bodies, starts)]


CONTEXT_GROWTH = 2
CONTEXT_ITEM = r"(?:@[\w.]+|\[[^\]]*\]|[\w.]+)'?(?:\s+lookup [\w.]+)?"
CONTEXT_RULE = re.compile(rf"^(\s*)pos\s+({CONTEXT_ITEM}(?:\s+{CONTEXT_ITEM})*)\s*;\s*$")
CONTEXT_TOKEN = re.compile(r"(@[\w.]+|\[[^\]]*\]|[\w.]+)('?)(?:\s+lookup ([\w.]+))?")


def context_rule(line, classes):
    match = CONTEXT_RULE.match(line)
    if not match or "'" not in line or "<" in line:
        return None
    tokens = CONTEXT_TOKEN.findall(match.group(2))
    marked = [index for index, (_, mark, _) in enumerate(tokens) if mark]
    called = [name for _, _, name in tokens if name]
    if len(marked) != 1 or len(called) != 1 or tokens[marked[0]][2] != called[0]:
        return None
    sets = []
    for token, _, _ in tokens:
        members = glyph_set(token, classes)
        if members is None and token.startswith("@"):
            return None
        sets.append(frozenset(members or [token]))
    return {"indent": match.group(1), "sets": sets, "marked": marked[0], "called": called[0]}


def context_parts(rule):
    sets, marked = rule["sets"], rule["marked"]
    return [sets[:marked], [sets[marked]], sets[marked + 1 :]]


def atoms(sets):
    found = []
    for members in dict.fromkeys(sets):
        rest = set(members)
        refined = []
        for atom in found:
            inside = atom & rest
            refined += [inside, atom - inside] if inside and inside != atom else [atom]
            rest -= atom
        found = refined + ([rest] if rest else [])
    return [frozenset(atom) for atom in found]


def class_ready(rules):
    contexts = [[], [], []]
    for rule in rules:
        for index, part in enumerate(context_parts(rule)):
            contexts[index] += part
    pieces = [atoms(each) for each in contexts]
    found = []
    for rule in rules:
        options = [[atom for atom in pieces[index] if atom <= members] for index, part in enumerate(context_parts(rule)) for members in part]
        combos = [[]]
        for choices in options:
            combos = [combo + [atom] for combo in combos for atom in choices]
        found += [dict(rule, sets=combo) for combo in combos]
    return found


def signature(rule):
    before, _, after = context_parts(rule)
    return tuple(before), tuple(after), rule["called"]


def unmergeable(rules):
    groups = {}
    for rule in rules:
        groups.setdefault(rule["sets"][rule["marked"]], []).append(rule)
    pending = list(groups.values())
    ordered = []
    while pending:
        last = signature(ordered[-1]) if ordered else None
        pick = next((index for index, group in enumerate(pending) if signature(group[0]) != last), 0)
        ordered += pending.pop(pick)
    return ordered


def overlapping(first, second):
    offset = first["marked"] - second["marked"]
    return all(
        first["sets"][index] & second["sets"][index - offset]
        for index in range(len(first["sets"]))
        if 0 <= index - offset < len(second["sets"])
    )


def merged_context(rules):
    rules = list(rules)
    changed = True
    while changed:
        changed = False
        for first_index in range(len(rules)):
            first = rules[first_index]
            for second_index in range(first_index + 1, len(rules)):
                second = rules[second_index]
                if (first["called"], first["marked"], len(first["sets"])) != (second["called"], second["marked"], len(second["sets"])):
                    continue
                differing = [index for index, (a, b) in enumerate(zip(first["sets"], second["sets"])) if a != b]
                if len(differing) != 1:
                    continue
                if any(overlapping(between, second) for between in rules[first_index + 1 : second_index]):
                    continue
                spot = differing[0]
                first["sets"] = first["sets"][:spot] + [first["sets"][spot] | second["sets"][spot]] + first["sets"][spot + 1 :]
                del rules[second_index]
                changed = True
                break
            if changed:
                break
    return rules


def fits_classes(taken, sets):
    return all(each == members or not each & members for members in sets for each in taken)


def class_chunks(rules):
    chunks = []
    for rule in rules:
        parts = context_parts(rule)
        if chunks and all(fits_classes(chunks[-1][1][index], part) for index, part in enumerate(parts)):
            chunks[-1][0].append(rule)
        else:
            chunks.append(([rule], [set(), set(), set()]))
        for index, part in enumerate(parts):
            chunks[-1][1][index].update(part)
    return [chunk for chunk, _ in chunks]


def context_lines(rules):
    expanded = unmergeable(class_ready(rules))
    if len(expanded) <= CONTEXT_GROWTH * len(rules):
        return [context_line(rule) for rule in expanded]
    lines = []
    for index, chunk in enumerate(class_chunks(merged_context(rules))):
        if index:
            lines.append(f"{chunk[0]['indent']}subtable;")
        lines += [context_line(rule) for rule in chunk]
    return lines


def context_line(rule):
    tokens = []
    for index, members in enumerate(rule["sets"]):
        token = next(iter(members)) if len(members) == 1 else f"[{' '.join(sorted(members))}]"
        if index == rule["marked"]:
            token += f"' lookup {rule['called']}"
        tokens.append(token)
    return f"{rule['indent']}pos {' '.join(tokens)};"


def folded_context(name, bodies, classes, indent):
    parsed = []
    for body, each in zip(bodies, classes):
        lines = [line for line in body.split("\n") if line.strip()]
        rules = [context_rule(line, each) for line in lines]
        if not rules or any(rule is None for rule in rules):
            return None
        parsed.append(rules)
    shapes = {tuple((rule["called"], rule["marked"], tuple(tuple(sorted(members)) for members in rule["sets"])) for rule in rules) for rules in parsed}
    if len(shapes) != 1:
        return None
    lines = context_lines(parsed[0])
    return ["\n".join([f"{indent}lookup {name} useExtension {{", *lines, f"{indent}}} {name};"]) for _ in bodies]


def lookup_pieces(name, base, matrix, indent):
    blocks = []
    if base:
        blocks.append("\n".join([f"{indent}lookup {name} {{", *base, f"{indent}}} {name};"]))
    if matrix:
        label = f"{name}_pairs" if base else name
        blocks.append("\n".join([f"{indent}lookup {label} {{", *matrix, f"{indent}}} {label};"]))
    return "\n".join(blocks)


def base_and_matrix(base, matrix, name, indent):
    lines = list(base)
    if matrix:
        lines += [f"{indent}lookup {name} {{", *matrix, f"{indent}}} {name};"]
    return "\n".join(lines)


@lru_cache(maxsize=None)
def family_feature_texts(masters):
    return dict(zip(masters, folded_texts([drawn_feature_text(master) for master in masters])))


def feature_text(master):
    return family_feature_texts(tuple(family(master)))[master]
