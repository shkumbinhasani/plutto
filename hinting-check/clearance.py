import sys

from plutto import accents, lowercase
from plutto.accents import base_of, compose, outline
from plutto.glyphs import GLYPHS, render
from plutto.masters import MASTERS, XH


def top(contours):
    return max(point[1] for point in outline(type("G", (), {"contours": contours})))


def bottom(contours):
    return min(point[1] for point in outline(type("G", (), {"contours": contours})))


def gaps(master):
    rows = {}
    for name in ("i", "j"):
        glyph = render(name, master)
        rows[name] = bottom(glyph.contours[-1:]) - top(glyph.contours[:-1])
    for name, letter in accents.KERN_LIKE.items():
        if name == letter or len(name) - len(letter) < 4 or not name.startswith(letter):
            continue
        if name.endswith("cedilla"):
            continue
        base = base_of(letter)(master).contours
        glyph = render(name, master)
        mark = glyph.contours[len(base):]
        rows[name] = bottom(mark) - top(glyph.contours[: len(base)])
    return rows


if __name__ == "__main__":
    table = {master.name: gaps(master) for master in MASTERS}
    names = list(table[MASTERS[0].name])
    print(f"{'glyph':16}" + "".join(f"{m.name:>8}" for m in MASTERS))
    for name in names:
        print(f"{name:16}" + "".join(f"{table[m.name][name]:8.0f}" for m in MASTERS))
