from functools import cache
from pathlib import Path

import numpy
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.ttProgram import Program
from PIL import Image, ImageDraw, ImageFont

INK = 128
CLEAR_GAP = 64
MARGIN = 2
SUBSAMPLES = 4
LARGE_SIZE = 64
NEIGHBOURS = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]


def strip_glyph_programs(source, target):
    font = TTFont(source)
    table = font["glyf"]
    for name in font.getGlyphOrder():
        if table[name].numberOfContours > 0:
            empty = Program()
            empty.fromBytecode(b"")
            table[name].program = empty
    font.save(target)
    return target


@cache
def face(path, size):
    return ImageFont.truetype(str(path), size)


@cache
def glyph_image(path, size, char):
    width, height = 2 * size + 2 * MARGIN, 2 * size + 2 * MARGIN
    baseline = round(1.4 * size) + MARGIN
    image = Image.new("L", (width, height), 0)
    ImageDraw.Draw(image).text((MARGIN, baseline), char, font=face(path, size), fill=255, anchor="ls")
    return numpy.asarray(image), baseline


def grow(seed, allowed):
    region = seed & allowed
    height, width = region.shape
    while True:
        padded = numpy.pad(region, 1)
        spread = numpy.zeros_like(region)
        for dy, dx in NEIGHBOURS:
            spread |= padded[1 + dy : 1 + dy + height, 1 + dx : 1 + dx + width]
        spread &= allowed
        if (spread == region).all():
            return region
        region = spread


def contour_heights(font, name):
    table = font["glyf"]
    glyph = table[name]
    coordinates, ends, _ = glyph.getCoordinates(table)
    spans, start = [], 0
    for end in ends:
        ys = [y for _, y in coordinates[start : end + 1]]
        spans.append((min(ys), max(ys)))
        start = end + 1
    return sorted(spans, key=lambda span: span[1])


def mark_floor(font, name):
    spans = contour_heights(font, name)
    for index in range(1, len(spans)):
        below = max(top for _, top in spans[:index])
        above = min(bottom for bottom, _ in spans[index:])
        if below < above:
            return below
    raise ValueError(f"{name} has no mark that sits clear of its base")


def mark_meets_base(data, baseline, base_top, threshold=INK):
    ink = data >= threshold
    rows = numpy.arange(ink.shape[0])[:, None]
    heights = baseline - rows
    above = ink & (heights - 1 >= base_top + 0.5)
    deep = heights <= base_top - 1
    return bool((grow(above, ink) & deep).any())


def runs_of(row):
    edges = numpy.flatnonzero(numpy.diff(numpy.concatenate(([0], row.astype(numpy.int8), [0]))))
    return list(zip(edges[::2], edges[1::2]))


def root(parents, index):
    while parents[index] != index:
        parents[index] = parents[parents[index]]
        index = parents[index]
    return index


def background_regions(data):
    clear = data < INK
    parents, placed, previous = [], [], []
    for row in range(clear.shape[0]):
        current = []
        for start, end in runs_of(clear[row]):
            index = len(parents)
            parents.append(index)
            placed.append((row, start, end))
            for other, other_start, other_end in previous:
                if other_start < end and start < other_end:
                    parents[root(parents, other)] = root(parents, index)
            current.append((index, start, end))
        previous = current
    labels = numpy.zeros(clear.shape, dtype=int)
    for index, (row, start, end) in enumerate(placed):
        labels[row, start:end] = root(parents, index) + 1
    return labels


@cache
def true_counters(path, char):
    data, baseline = glyph_image(path, LARGE_SIZE, char)
    labels = background_regions(data)
    edge = set(labels[0]) | set(labels[-1]) | set(labels[:, 0]) | set(labels[:, -1])
    counters = sorted(set(numpy.unique(labels)) - edge - {0})
    return labels, baseline, counters


def counter_shares(path, char, size, shape, baseline):
    labels, large_baseline, counters = true_counters(path, char)
    ratio = LARGE_SIZE / size
    offsets = (numpy.arange(SUBSAMPLES) + 0.5) / SUBSAMPLES
    rows = numpy.arange(shape[0])[:, None] + offsets[None, :]
    columns = numpy.arange(shape[1])[:, None] + offsets[None, :]
    large_rows = numpy.clip((large_baseline - (baseline - rows) * ratio).astype(int), 0, labels.shape[0] - 1)
    large_columns = numpy.clip((MARGIN + (columns - MARGIN) * ratio).astype(int), 0, labels.shape[1] - 1)
    sampled = labels[large_rows[:, None, :, None], large_columns[None, :, None, :]]
    return [(sampled == counter).mean(axis=(2, 3)) for counter in counters]


def closed_counters(hinted, reference, char, size):
    plain, baseline = glyph_image(reference, size, char)
    fitted, _ = glyph_image(hinted, size, char)
    closed = 0
    for share in counter_shares(reference, char, size, plain.shape, baseline):
        inside = share >= 0.5
        if not inside.any() or plain[inside].min() >= INK:
            continue
        if fitted[share > 0].min() >= INK:
            closed += 1
    return closed
