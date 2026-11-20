import argparse
import atexit
import shutil
import subprocess
import tempfile
from pathlib import Path

import freetype

SIZES = range(11, 25)
LETTERS = "zHl"


def tops(path, size, flags):
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, size)
    found = []
    for char in LETTERS:
        face.load_char(char, flags)
        found.append(max(y for _, y in face.glyph.outline.points) / 64)
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--options", action="append", default=[])
    parser.add_argument("--style", default="Regular")
    args = parser.parse_args()
    source = args.source / f"Plutto-{args.style}.ttf"
    work = Path(tempfile.mkdtemp(prefix="plutto-heights-"))
    atexit.register(shutil.rmtree, work, ignore_errors=True)
    variants = []
    for number, options in enumerate(args.options):
        target = work / f"{number}.ttf"
        subprocess.run(["ttfautohint", *options.split(), str(source), str(target)], check=True)
        variants.append(target)
    print(f"{'size':>4} {'natural z/H/l':>18}  " + "  ".join(f"variant {n}" for n in range(len(variants))))
    worst = [0.0] * len(variants)
    for size in SIZES:
        natural = tops(source, size, freetype.FT_LOAD_NO_HINTING)
        row = f"{size:4} {'/'.join(f'{v:.2f}' for v in natural):>18}  "
        for number, variant in enumerate(variants):
            hinted = tops(variant, size, freetype.FT_LOAD_DEFAULT)
            moves = [h - n for h, n in zip(hinted, natural)]
            worst[number] = max(worst[number], max(abs(m) for m in moves[1:]))
            row += f"{'/'.join(f'{h:.0f}' for h in hinted):>9} ({max(moves[1:], key=abs):+.2f})  "
        print(row)
    print("largest cap or ascender move:", " ".join(f"{w:.2f}" for w in worst))


if __name__ == "__main__":
    main()
