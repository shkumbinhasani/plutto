import sys
from pathlib import Path

from .compile import build


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("fonts")
    for path in build(target):
        print(path)


main()
