from functools import lru_cache

from . import accents, alternates, capitals, cyrillic, figures, greek, italics, latin, lowercase, marks, maths, symbols
from .masters import DEFAULT, ITALIC_DEFAULT
from .names import DIGITS, LETTERS
from .oblique import Overlaid, finished
from .parts import Glyph

EXTENSIONS = [accents, symbols, alternates, latin, maths, greek, cyrillic]
MARKS = {
    "exclam": 0x21,
    "quotedbl": 0x22,
    "numbersign": 0x23,
    "dollar": 0x24,
    "percent": 0x25,
    "ampersand": 0x26,
    "quotesingle": 0x27,
    "parenleft": 0x28,
    "parenright": 0x29,
    "asterisk": 0x2A,
    "plus": 0x2B,
    "comma": 0x2C,
    "hyphen": 0x2D,
    "period": 0x2E,
    "slash": 0x2F,
    "colon": 0x3A,
    "semicolon": 0x3B,
    "less": 0x3C,
    "equal": 0x3D,
    "greater": 0x3E,
    "question": 0x3F,
    "at": 0x40,
    "bracketleft": 0x5B,
    "backslash": 0x5C,
    "bracketright": 0x5D,
    "asciicircum": 0x5E,
    "underscore": 0x5F,
    "grave": 0x60,
    "braceleft": 0x7B,
    "bar": 0x7C,
    "braceright": 0x7D,
    "asciitilde": 0x7E,
    "periodcentered": 0xB7,
    "endash": 0x2013,
    "emdash": 0x2014,
    "quoteleft": 0x2018,
    "quoteright": 0x2019,
    "quotedblleft": 0x201C,
    "quotedblright": 0x201D,
    "ellipsis": 0x2026,
}

ZERO_WIDTH = {"uni034F": 0x34F, "uni200B": 0x200B, "uni200C": 0x200C, "uni200D": 0x200D, "uni2060": 0x2060, "uniFEFF": 0xFEFF}


def zero_width(m):
    return Glyph([], 0)


GLYPHS = {".notdef": (None, marks.notdef), "space": (0x20, marks.space)}
for letter in LETTERS.upper():
    GLYPHS[letter] = (ord(letter), getattr(capitals, f"capital_{letter.lower()}"))
for letter in LETTERS:
    GLYPHS[letter] = (ord(letter), getattr(lowercase, f"letter_{letter}"))
for value, name in enumerate(DIGITS):
    GLYPHS[name] = (0x30 + value, figures.proportional(getattr(figures, name)))
for name, code in MARKS.items():
    GLYPHS[name] = (code, getattr(marks, name))
for name in DIGITS:
    GLYPHS[f"{name}.tnum"] = (None, figures.tabular(getattr(figures, name)))
for name, code in ZERO_WIDTH.items():
    GLYPHS[name] = (code, zero_width)
for extension in EXTENSIONS:
    for name, entry in extension.GLYPHS.items():
        if name in GLYPHS:
            raise ValueError(f"{extension.__name__} redefines {name}")
        GLYPHS[name] = entry
GLYPHS.update(accents.cyrillic_supplement())

italics.italicized(GLYPHS)

UPRIGHT_IN_ITALIC = {
    ".notdef",
    "plus",
    "minus",
    "equal",
    "notequal",
    "less",
    "greater",
    "lessequal",
    "greaterequal",
    "multiply",
    "divide",
    "plusminus",
    "approxequal",
    "asciitilde",
    "asciicircum",
    "logicalnot",
    "infinity",
    "degree",
    "currency",
    "copyright",
    "registered",
    "trademark",
    "bullet",
    "arrowleft",
    "arrowright",
    "arrowup",
    "arrowdown",
    "arrowboth",
    "arrowdblleft",
    "arrowdblright",
    "arrowdblboth",
    "arrowupdn",
    "arrowdblup",
    "arrowdbldown",
    "uni21D5",
    "uni2117",
    "estimated",
    "radical",
    "lozenge",
}


UPRIGHT_IN_ITALIC.update(symbols.UI_SYMBOLS)


def stays_upright(name):
    return name in UPRIGHT_IN_ITALIC or name.split(".")[0] in UPRIGHT_IN_ITALIC


def render(name, master):
    return finished(GLYPHS[name][1], master, stays_upright(name))


def base_drawing(name):
    draw = GLYPHS[name][1]
    while isinstance(draw, Overlaid):
        draw = draw.base
    return draw


@lru_cache(maxsize=None)
def drawn_alike(name):
    upright, italic = base_drawing(name)(DEFAULT), base_drawing(name)(ITALIC_DEFAULT)
    outlines = [[list(contour.points()) for contour in glyph.contours] for glyph in (upright, italic)]
    return upright.advance == italic.advance and outlines[0] == outlines[1]
