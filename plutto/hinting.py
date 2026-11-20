import shutil
import subprocess
import tempfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor

import numpy
from fontTools.ttLib import TTFont

from .masters import ALL_MASTERS, ASC, BETWEEN_STATICS, CAP, DESC, ITALIC_BETWEEN_STATICS, OV, XH, Master, mix_at

AUTOHINTER = "ttfautohint"
NATURAL_STEMS = "nsn"
X_HEIGHT_EXCEPTIONS = "11,13,15,17,19,21,23-24"
DEEP_X_HEIGHT_EXCEPTIONS = "11,13,15,17,19-24"
SNAPPING = "--x-height-snapping-exceptions="
AUTOHINT_OPTIONS = (
    f"--stem-width-mode={NATURAL_STEMS}",
    f"{SNAPPING}{X_HEIGHT_EXCEPTIONS}",
    "--increase-x-height=0",
    "--windows-compatibility",
    "--no-info",
)
OPENED_COUNTERS = {
    "Bold": {"oslash": (10,), "uni045A": (13,)},
    "BoldItalic": {"oslash": (10, 11), "uni0459": (13,)},
    "Black": {"a": (10, 11), "e": (11,), "oe": (10, 11, 17), "oslash": (14, 17), "A": (12,), "at": (11, 13), "ae": (12, 13)},
    "ExtraBold": {"oe": (11,), "ae": (12, 13), "e": (14,)},
    "ExtraBoldItalic": {"ae": (11,), "oe": (11,), "oslash": (11,)},
    "BlackItalic": {"a": (10, 11), "ae": (10, 11, 12), "oe": (10, 11, 14, 15, 17), "oslash": (11, 17), "e": (10, 11), "ampersand": (13,), "at": (11, 13)},
}
COUNTER_SHIFT = 0.5
LIFTED_MARKS = {
    "Light": {"gbreve": (12, 16), "ytilde": (12,)},
    "LightItalic": {"gbreve": (16,), "uni0439": (12,)},
    "Regular": {"alphavrachy": (11, 14), "ibreve": (11,), "ubreve": (11,), "uni045E": (16,), "ytilde": (11,)},
    "Italic": {"Ahookabove": (11,), "Aring": (11,), "Ntilde": (11,), "Ytilde": (11,), "alphavrachy": (11,), "ccaron": (11,), "scaron": (11,), "ubreve": (11,), "uni045E": (16,)},
    "Bold": {"Ahookabove": (15,), "Aring": (11,), "etatonos": (16,), "obreve": (11,), "ocaron": (11,), "odieresis": (11,), "ohungarumlaut": (11,), "gcircumflex": (16,), "jcircumflex": (11, 16), "ycircumflex": (16,)},
    "BoldItalic": {"Aring": (11,), "Rcaron": (11,), "etatonos": (15, 16), "gcircumflex": (16,), "jcircumflex": (11, 16), "ycircumflex": (16,)},
    "Black": {"Aring": (11,), "obreve": (11,), "ocaron": (11,), "odieresis": (11,), "ohungarumlaut": (11,), "atilde": (14,), "etilde": (14,), "jcircumflex": (16,), "ntilde": (14,), "otilde": (14,), "utilde": (14,), "lacute": (12,), "hcaron": (16,), "kcaron": (16,)},
    "BlackItalic": {"Uring": (11,), "atilde": (14,), "etilde": (14,), "jcircumflex": (16,), "ngrave": (12,), "ntilde": (14,), "otilde": (14,), "utilde": (14,), "lacute": (12,), "hcaron": (16,), "kcaron": (16,)},
    "Medium": {"Aring": (11,), "Itilde": (11,), "i": (14,), "j": (14,), "ydieresis": (14,)},
    "MediumItalic": {"Itilde": (11,), "ccaron": (11,), "gcircumflex": (11,), "jcircumflex": (11,), "scaron": (11,), "ycircumflex": (11,), "i": (14,), "j": (14,), "Aring": (11,)},
    "SemiBold": {"Aring": (11,), "agrave": (11,), "i": (12,), "j": (12,), "racute": (11,), "wgrave": (11,), "yacute": (11,), "ycircumflex": (11, 16), "ygrave": (11,)},
    "ExtraBold": {"Aring": (11,), "ahookabove": (16,), "obreve": (11,), "ocaron": (11,), "odieresis": (11,), "ohungarumlaut": (11,), "ehookabove": (16,), "ohookabove": (16,)},
    "ExtraBoldItalic": {"Aring": (11,)},
    "SemiBoldItalic": {"Aring": (11,), "gbreve": (11,), "gcircumflex": (11,), "i": (12,), "Ihookabove": (11, 15), "j": (12,), "jcircumflex": (11,), "ycircumflex": (11, 16)},
}
RING_SIZES = (11, 12, 13, 14, 15, 16)
RING_LIFT = 1
OPENED_RINGS = ("aring", "Aring", "Aringacute", "ringcomb", "ringcomb.case")
LIFTED_STACKS = {
    "Light": {"Abreve": (16,), "Abreveacute": (16,), "Abrevedotbelow": (16,), "Abrevegrave": (16,), "Abrevehookabove": (16,), "Abrevetilde": (16,), "Acircumflexhookabove": (15, 16), "Acircumflextilde": (15, 16), "Ecircumflexhookabove": (16,), "Ecircumflextilde": (16,), "Ehookabove": (19,), "Ocircumflexhookabove": (15, 16), "Ocircumflextilde": (15, 16), "Ohookabove": (19,)},
    "Regular": {"Abrevetilde": (11,), "Acircumflexhookabove": (15,), "Acircumflextilde": (15, 19), "Ecircumflexhookabove": (15,), "Ecircumflextilde": (15, 19), "Ocircumflexhookabove": (15,), "Ocircumflextilde": (15, 19), "Ohookabove": (11,)},
    "Medium": {"Abrevetilde": (11,), "Acircumflextilde": (15, 19), "Ecircumflextilde": (15, 19), "Ehookabove": (16,), "Ocircumflextilde": (15, 19)},
    "SemiBold": {"Abrevetilde": (11,), "Acircumflexdotbelow": (15,), "Acircumflextilde": (15, 19), "Ecircumflexdotbelow": (15,), "Ecircumflextilde": (15, 19), "Ihookabove": (11,), "Ocircumflextilde": (15, 19)},
    "Bold": {"Abrevedotbelow": (22,), "Abrevetilde": (11,), "Acircumflexdotbelow": (17, 18, 19, 22), "Acircumflextilde": (15, 19), "Ecircumflexdotbelow": (13, 15, 17, 18, 19, 22), "Ecircumflextilde": (15, 19), "Ehookabove": (15,), "Ocircumflexdotbelow": (15, 17, 18, 19, 22), "Ocircumflextilde": (15, 19)},
    "ExtraBold": {"Abrevedotbelow": (22,), "Abrevetilde": (11,), "Acircumflextilde": (15, 19), "Ecircumflextilde": (15, 19), "Ocircumflexacute": (11,), "Ocircumflexgrave": (11,), "Ocircumflextilde": (15, 19)},
    "Black": {"Abrevetilde": (11,)},
    "LightItalic": {"Abreve": (15, 16), "Abreveacute": (15, 16), "Abrevedotbelow": (15, 16), "Abrevegrave": (15, 16), "Abrevehookabove": (16,), "Abrevetilde": (16,), "Acircumflexhookabove": (15,), "Ecircumflexhookabove": (16,), "Ecircumflextilde": (16,), "Ehookabove": (19,), "Ocircumflexhookabove": (15,), "Ocircumflextilde": (15, 16), "Ohookabove": (19,)},
    "Italic": {"Abrevetilde": (11,), "Acircumflexhookabove": (15,), "Ecircumflexhookabove": (15,), "Ecircumflextilde": (15, 19), "Ehookabove": (11,), "Ocircumflexhookabove": (15,), "Ocircumflextilde": (15, 19)},
    "MediumItalic": {"Abrevehookabove": (15,), "Abrevetilde": (11, 15), "Ecircumflextilde": (15, 19), "Ehookabove": (11,), "Ocircumflextilde": (15, 19), "Ohookabove": (11,)},
    "SemiBoldItalic": {"Abreve": (11,), "Abrevedotbelow": (11,), "Abrevetilde": (11,), "Acircumflexdotbelow": (11,), "Ecircumflexdotbelow": (11,), "Ecircumflextilde": (15, 19), "Ocircumflextilde": (15, 19)},
    "BoldItalic": {"Abreve": (11,), "Abrevedotbelow": (11, 12, 22), "Abrevetilde": (11,), "Acircumflexdotbelow": (12, 17, 19, 22), "Ecircumflexdotbelow": (12, 17, 19, 22), "Ecircumflextilde": (15, 19), "Ehookabove": (15,), "Ihookabove": (15,), "Ocircumflexdotbelow": (12, 17, 19, 22), "Ocircumflextilde": (15, 19)},
    "ExtraBoldItalic": {"Abrevedotbelow": (22,), "Abrevetilde": (11,), "Ecircumflextilde": (15, 19), "Ocircumflextilde": (15, 19)},
    "BlackItalic": {"Abrevetilde": (11,), "Ecircumflextilde": (15,)},
}
LIFTED_TOPS = {
    "Light": {"Acircumflextilde": (16, 20, 21, 22), "Ecircumflextilde": (16, 21, 22, 23), "Ocircumflextilde": (16, 20, 21, 22)},
    "Regular": {"Acircumflextilde": (15,), "Ecircumflextilde": (15,), "Ocircumflextilde": (15,)},
    "Medium": {"Acircumflextilde": (15,), "Ecircumflextilde": (15,), "Ocircumflextilde": (15,)},
    "SemiBold": {"Acircumflextilde": (15,), "Ecircumflextilde": (15,), "Ocircumflextilde": (15,)},
    "Bold": {"Abrevetilde": (11,), "Acircumflextilde": (15,), "Ecircumflextilde": (15,), "Ocircumflextilde": (15,)},
    "ExtraBold": {"Abrevetilde": (11,), "Acircumflextilde": (15,), "Ecircumflextilde": (15, 24), "Ocircumflextilde": (15, 24)},
    "Black": {"Abreveacute": (21,), "Abrevegrave": (21,), "Abrevetilde": (11,), "Acircumflextilde": (23, 24), "Ecircumflextilde": (23, 24), "Ocircumflextilde": (23, 24)},
    "LightItalic": {"Acircumflextilde": (21, 22), "Ecircumflextilde": (16, 21, 22), "Ocircumflextilde": (16, 21, 22)},
    "Italic": {"Ecircumflextilde": (15,), "Ocircumflextilde": (15,)},
    "MediumItalic": {"Ecircumflextilde": (15,), "Ocircumflextilde": (15,)},
    "SemiBoldItalic": {"Ecircumflextilde": (15,), "Ocircumflextilde": (15,)},
    "BoldItalic": {"Abrevetilde": (11,), "Ecircumflextilde": (15,), "Ocircumflextilde": (15,)},
    "ExtraBoldItalic": {"Abrevetilde": (11,), "Ecircumflextilde": (15, 24), "Ocircumflextilde": (15, 24)},
    "BlackItalic": {"Abrevetilde": (11,), "Acircumflextilde": (23, 24), "Ecircumflextilde": (15, 23, 24), "Ocircumflextilde": (24,)},
}
HALF_LIFT = 0.5
CUT_STATICS = BETWEEN_STATICS + ITALIC_BETWEEN_STATICS
HINTED_WHOLE = {"Aring", "aring", "hcaron", "hcircumflex", "ihookabove", "itilde", "kcaron", "lacute", "yhookabove"}
MARK_LIFT = 1
COUNTER_REACH = XH
GRID = 6
PROBES = (1, 2)
SAMPLES = 8
FLATTEST_SIDE = 0.5
NEAR_CELLS = 4
ZONES = (0, XH, CAP, ASC, DESC)
UNHINTED_FOLDER = "unhinted"
INTEGER_PPEM = 1 << 3


def find_autohinter():
    return shutil.which(AUTOHINTER)


def style_of(font):
    table = font["OS/2"]
    italic = bool(table.fsSelection & 1)
    for master in ALL_MASTERS + CUT_STATICS:
        if master.weight == table.usWeightClass and master.italic == italic:
            return master.name.replace(" ", "")
    return None


def weight_of(font):
    weight = font["OS/2"].usWeightClass
    return Master(str(weight), weight, mix_at(weight))


def body_top(font, capital):
    master = weight_of(font)
    return CAP + master.cap_ov if capital else XH + master.ov


def autohint_options(font):
    if round(weight_of(font).ov) <= OV:
        return AUTOHINT_OPTIONS
    return tuple(f"{SNAPPING}{DEEP_X_HEIGHT_EXCEPTIONS}" if option.startswith(SNAPPING) else option for option in AUTOHINT_OPTIONS)


def contours_of(font, name):
    table = font["glyf"]
    glyph = table[name]
    if glyph.numberOfContours <= 0:
        return []
    coordinates, ends, flags = glyph.getCoordinates(table)
    contours, start = [], 0
    for end in ends:
        contours.append([(index, coordinates[index], flags[index] & 1) for index in range(start, end + 1)])
        start = end + 1
    return contours


def runs_of(contour):
    first = next(index for index, point in enumerate(contour) if point[2])
    ring = contour[first:] + contour[: first + 1]
    run = [ring[0]]
    for point in ring[1:]:
        run.append(point)
        if point[2]:
            yield run
            run = [point]


def traced(run):
    points = [numpy.array(point[1], dtype=float) for point in run]
    controls = points[1:-1] or [(points[0] + points[-1]) / 2]
    joins = [points[0]] + [(a + b) / 2 for a, b in zip(controls, controls[1:])] + [points[-1]]
    t = ((numpy.arange(SAMPLES) + 0.5) / SAMPLES)[:, None]
    places, headings = [], []
    for start, control, end in zip(joins, controls, joins[1:]):
        places.append((1 - t) ** 2 * start + 2 * t * (1 - t) * control + t**2 * end)
        headings.append(2 * (1 - t) * (control - start) + 2 * t * (end - control))
    return numpy.concatenate(places), numpy.concatenate(headings)


def winding(columns, rows, polygon):
    ahead = numpy.roll(polygon, -1, axis=0)
    low, high = polygon[:, 1], ahead[:, 1]
    level = rows[:, None]
    rising = (low <= level) & (level < high)
    falling = (high <= level) & (level < low)
    rise = numpy.where(high == low, 1, high - low)
    crossing = polygon[:, 0] + (level - low) * (ahead[:, 0] - polygon[:, 0]) / rise
    direction = rising.astype(int) - falling.astype(int)
    return ((crossing[:, None, :] > columns[None, :, None]) * direction[:, None, :]).sum(axis=2)


def label_counters(clear):
    labels = numpy.zeros(clear.shape, dtype=int)
    height, width = clear.shape
    count = 0
    for seed in zip(*numpy.nonzero(clear)):
        if labels[seed]:
            continue
        count += 1
        labels[seed] = count
        waiting = deque([seed])
        while waiting:
            row, column = waiting.popleft()
            for step_row, step_column in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                near = (row + step_row, column + step_column)
                if 0 <= near[0] < height and 0 <= near[1] < width and clear[near] and not labels[near]:
                    labels[near] = count
                    waiting.append(near)
    edge = set(labels[0]) | set(labels[-1]) | set(labels[:, 0]) | set(labels[:, -1])
    return labels, [label for label in range(1, count + 1) if label not in edge]


def ring_shifts(font, name):
    floor = body_top(font, name[0].isupper() or name.endswith(".case"))
    rings = [contour for contour in contours_of(font, name) if min(point[1][1] for point in contour) > floor]
    if len(rings) < 2:
        return {}
    ys = [point[1][1] for contour in rings for point in contour]
    middle = (min(ys) + max(ys)) / 2
    return {index: RING_LIFT for contour in rings for index, (_, y), _ in contour if y > middle}


def counter_shifts(font, name):
    runs = [list(runs_of(contour)) for contour in contours_of(font, name) if any(point[2] for point in contour)]
    traces = [[traced(run) for run in contour] for contour in runs]
    outline = [numpy.concatenate([places for places, _ in contour]) for contour in traces]
    if not outline:
        return {}
    reach = weight_of(font).cap_ov
    every = numpy.concatenate(outline)
    low, high = every.min(axis=0) - 3 * GRID, every.max(axis=0) + 3 * GRID
    columns = numpy.arange(low[0], high[0], GRID)
    rows = numpy.arange(low[1], high[1], GRID)
    turns = [winding(columns, rows, polygon) for polygon in outline]
    total = sum(turns)
    labels, counters = label_counters(total == 0)
    reached = [label for label in counters if rows[numpy.nonzero(labels == label)[0]].min() < COUNTER_REACH]
    near = numpy.isin(labels, reached)
    for _ in range(NEAR_CELLS):
        near = grown(near)

    def cell(point):
        column = min(max(int((point[0] - low[0]) / GRID), 0), len(columns) - 1)
        row = min(max(int((point[1] - low[1]) / GRID), 0), len(rows) - 1)
        return row, column

    votes = {}
    for contour, trace, own in zip(runs, traces, turns):
        others = total - own
        for run, (places, headings) in zip(contour, trace):
            lengths = numpy.hypot(headings[:, 0], headings[:, 1])
            usable = lengths > 0
            normals = numpy.stack([-headings[:, 1], headings[:, 0]], axis=1) / numpy.where(usable, lengths, 1)[:, None]
            facing = numpy.zeros(len(places), dtype=bool)
            for probe in PROBES:
                spot = places + normals * probe * GRID
                cells = numpy.clip(((spot - low) / GRID).astype(int), 0, [len(columns) - 1, len(rows) - 1])
                facing |= numpy.isin(labels[cells[:, 1], cells[:, 0]], reached) & usable
            facing &= numpy.abs(normals[:, 1]) >= FLATTEST_SIDE
            upward = int((facing & (normals[:, 1] < 0)).sum())
            downward = int((facing & (normals[:, 1] > 0)).sum())
            if upward == downward:
                continue
            sign = COUNTER_SHIFT if upward > downward else -COUNTER_SHIFT
            for index, point, _ in run:
                if any(abs(point[1] - zone) <= reach for zone in ZONES):
                    continue
                if near[cell(point)] or others[cell(point)]:
                    votes.setdefault(index, set()).add(sign)
    return {index: signs.pop() for index, signs in votes.items() if len(signs) == 1}


def grown(mask):
    padded = numpy.pad(mask, 1)
    return mask | padded[:-2, 1:-1] | padded[2:, 1:-1] | padded[1:-1, :-2] | padded[1:-1, 2:]


def built_on(font, name):
    def shapes(glyph):
        return {tuple(point[1] for point in contour) for contour in contours_of(font, glyph)}

    base = shapes(name)
    return [glyph for glyph in font.getGlyphOrder() if glyph == name or base and base <= shapes(glyph)]


def mark_points(font, name):
    floor = body_top(font, name[0].isupper())
    return sorted(index for contour in contours_of(font, name) if min(point[1][1] for point in contour) > floor for index, _, _ in contour)


def control_lines(font, style):
    lines = []
    for name, sizes in LIFTED_MARKS.get(style, {}).items():
        points = mark_points(font, name)
        if points:
            lines.append(f"{name} t {', '.join(str(point) for point in points)} y {MARK_LIFT} @ {', '.join(str(size) for size in sizes)}")
    for name in sorted(set(LIFTED_STACKS.get(style, {})) | set(LIFTED_TOPS.get(style, {}))):
        lines += stack_lines(font, name, set(LIFTED_STACKS.get(style, {}).get(name, ())), set(LIFTED_TOPS.get(style, {}).get(name, ())))
    for base, sizes in OPENED_COUNTERS.get(style, {}).items():
        for name in built_on(font, base):
            lines += shift_lines(name, counter_shifts(font, name), sizes)
    for name in OPENED_RINGS:
        points = sorted(ring_shifts(font, name))
        sizes = [size for size in RING_SIZES if size not in LIFTED_MARKS.get(style, {}).get(name, ())]
        if points and sizes:
            lines.append(f"{name} t {', '.join(str(point) for point in points)} y {RING_LIFT} @ {', '.join(str(size) for size in sizes)}")
    return lines


def top_points(font, name):
    floor = body_top(font, name[0].isupper())
    marks = sorted((contour for contour in contours_of(font, name) if min(point[1][1] for point in contour) > floor), key=lambda contour: max(point[1][1] for point in contour))
    for index in range(1, len(marks)):
        below = max(point[1][1] for contour in marks[:index] for point in contour)
        if below < min(point[1][1] for contour in marks[index:] for point in contour):
            return sorted(point[0] for contour in marks[index:] for point in contour)
    return []


def stack_lines(font, name, base, top):
    upper = top_points(font, name)
    lower = [point for point in mark_points(font, name) if point not in upper]
    shifts = {}
    for size in sorted(base | top):
        low = 0 if size not in base else HALF_LIFT if size in top else MARK_LIFT
        shifts.setdefault((low, MARK_LIFT), []).append(size)
    lines = []
    for (low, high), sizes in shifts.items():
        ppems = ", ".join(str(size) for size in sizes)
        for points, shift in ((lower, low), (upper, high)):
            if points and shift:
                lines.append(f"{name} t {', '.join(str(point) for point in points)} y {shift} @ {ppems}")
    return lines


def shift_lines(name, shifts, sizes):
    ppems = ", ".join(str(size) for size in sizes)
    lines = []
    for shift in (COUNTER_SHIFT, -COUNTER_SHIFT):
        points = sorted(index for index, value in shifts.items() if value == shift)
        if points:
            lines.append(f"{name} t {', '.join(str(point) for point in points)} y {shift} @ {ppems}")
    return lines


def autohint(source, target, autohinter):
    font = TTFont(source)
    command = [autohinter, *autohint_options(font)]
    lines = control_lines(font, style_of(font))
    with tempfile.NamedTemporaryFile("w", suffix=".txt") as control:
        if lines:
            control.write("\n".join(lines) + "\n")
            control.flush()
            command.append(f"--control-file={control.name}")
        result = subprocess.run([*command, str(source), str(target)], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"{AUTOHINTER} failed on {source.name}: {result.stderr.strip()}")
    hinted = TTFont(target)
    hinted["head"].flags |= INTEGER_PPEM
    hinted.save(target)


def hint_statics(pairs, autohinter):
    if autohinter is None:
        for source, target in pairs:
            shutil.copyfile(source, target)
        return False
    with ThreadPoolExecutor() as pool:
        list(pool.map(lambda pair: autohint(*pair, autohinter), pairs))
    return True
