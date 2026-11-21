#!/usr/bin/env python3
"""THE WORLD IN ONE DAY -- front page for Saturday 21 November 2026.

  news21 (22 Nov 2026): 47 stories, all dated Saturday 21 November 2026.
  Layout follows the rank-1 news20 reference (date as masthead, stat
  strip, region bar, 3 illustrated leads, 10 featured with thumbnails,
  world map + ALSO list, DATE CHECK box, footer).

  THE #1 FIX -- TRUE SERIF TYPOGRAPHY. The 5x7 and 7x9 bitmap fonts are
  GONE. Every letter on the page is drawn from a hand-built VECTOR
  serif font: each glyph is a set of strokes (polylines and elliptical
  arcs) in a 100-unit em, with thick vertical stems, thin horizontals,
  diagonal contrast and serif feet, rasterised at SS=4 supersampling
  and blended by per-pixel coverage. That is what makes the masthead,
  headlines and body read as a real newspaper instead of pixel art:
  the shapes themselves are smooth curves, not a finer grid of blocks.
  Bold weights are done by widening the strokes (masthead 1.45x,
  headlines 1.3x); the subline is a sheared (italic) serif.

  Stdlib only, no network, no external files, no randomness: two runs
  produce byte-identical output. Writes $MAKEFUN_OUTPUT_DIR/entry.png
  (fallback /output). 1024x1024 PNG.

  Stories (47): 3 leads + 10 featured + 34 ALSO, every one dated
  Saturday 21 November 2026, every one carrying its source in
  parentheses. Regions (recounted from the 47): AMERICAS 13, EUROPE 9,
  ASIA 8, AFRICA 6, MIDDLE EAST 5, GLOBAL 5, OCEANIA 1.
  DATE CHECK lists the items deliberately left out (19-20 Nov news).
"""
import hashlib
import math
import os
import struct
import zlib

W = H = 1024
SS = 4  # text supersampling factor

PAPER = (250, 246, 236)
INK = (17, 17, 17)
GRAY = (74, 74, 74)
RED = (176, 30, 30)
PANEL = (238, 232, 214)
NAVY = (24, 40, 72)
SEA = (70, 110, 170)
LAND = (198, 180, 140)
GREEN = (46, 110, 60)
YELLOW = (255, 200, 60)
BLUE = (30, 70, 160)

# ------------------------------------------------------- vector serif ----
# Glyph strokes in a 100-unit em: cap top y=0, baseline y=70,
# descender bottom y=92, x-height top y=22.
#   ('L', width, [(x, y), ...])      polyline stroke
#   ('A', width, cx, cy, rx, ry, a0, a1)  elliptical arc, degrees;
#       sampled from a0 to a1 (increasing if a1 > a0, else decreasing);
#       0 deg = east, 90 deg = south (y grows downwards)
#   ('D', radius, x, y)              filled dot
def L(w, pts):
    return ('L', w, pts)

def A(w, cx, cy, rx, ry, a0, a1):
    return ('A', w, cx, cy, rx, ry, a0, a1)

def D(r, x, y):
    return ('D', r, x, y)

def HB(x0, x1, y, w):
    return ('L', w, [(x0, y), (x1, y)])

def V(x, y0, y1, w):
    """Vertical stem with serif feet top and bottom."""
    return [('L', w, [(x, y0), (x, y1)]),
            ('L', 4, [(x - 7, y0 + 2), (x + 7, y0 + 2)]),
            ('L', 4, [(x - 7, y1 - 2), (x + 7, y1 - 2)])]

GLYPHS = {
    # ---- uppercase: cap top 0, baseline 70 ----
    'A': (68, [L(11, [(6, 70), (34, 2)]), L(11, [(34, 2), (62, 70)]),
              L(6, [(18, 46), (50, 46)]),
              HB(0, 14, 68, 4), HB(54, 68, 68, 4)]),
    'B': (52, [*V(10, 2, 68, 13),
               A(9, 10, 20, 26, 16, -90, 90),
               A(9, 10, 53, 28, 17, -90, 90)]),
    'C': (62, [A(10, 34, 35, 30, 35, 300, 60),
               HB(44, 60, 4, 4), HB(44, 60, 66, 4)]),
    'D': (58, [*V(10, 2, 68, 13), A(10, 10, 35, 42, 35, -90, 90)]),
    'E': (54, [*V(10, 2, 68, 13), HB(10, 52, 4, 6), HB(10, 44, 36, 6),
               HB(10, 54, 66, 6)]),
    'F': (52, [*V(10, 2, 68, 13), HB(10, 50, 4, 6), HB(10, 42, 36, 6)]),
    'G': (62, [A(10, 34, 35, 30, 35, 300, 60),
               HB(34, 58, 44, 6), L(6, [(56, 44), (56, 66)])]),
    'H': (68, [*V(10, 2, 68, 13), *V(58, 2, 68, 13), HB(16, 52, 36, 7)]),
    'I': (46, [*V(23, 2, 68, 13), HB(10, 36, 4, 5), HB(10, 36, 66, 5)]),
    'J': (60, [L(11, [(48, 2), (48, 54)]),
               A(10, 30, 54, 20, 16, 0, 180), HB(34, 62, 4, 5)]),
    'K': (60, [*V(10, 2, 68, 13), L(10, [(22, 38), (54, 4)]),
               L(10, [(28, 32), (56, 68)])]),
    'L': (56, [*V(10, 2, 68, 13), HB(10, 56, 66, 6)]),
    'M': (70, [*V(8, 2, 68, 12), *V(62, 2, 68, 12),
               L(9, [(14, 4), (35, 44)]), L(9, [(35, 44), (56, 4)])]),
    'N': (66, [*V(8, 2, 68, 12), *V(58, 2, 68, 12),
               L(9, [(14, 4), (52, 66)])]),
    'O': (68, [A(11, 34, 35, 28, 35, 0, 360)]),
    'P': (52, [*V(10, 2, 68, 13), A(9, 10, 19, 26, 19, -90, 90),
               HB(10, 34, 38, 6)]),
    'Q': (68, [A(11, 34, 35, 28, 35, 0, 360), L(8, [(44, 52), (62, 72)])]),
    'R': (54, [*V(10, 2, 68, 13), A(9, 10, 19, 26, 19, -90, 90),
               HB(10, 34, 38, 6), L(9, [(30, 38), (56, 68)])]),
    'S': (56, [A(10, 28, 20, 24, 17, 180, 360),
               A(10, 28, 50, 24, 17, 0, 180)]),
    'T': (64, [HB(4, 60, 4, 7), *V(32, 4, 68, 12)]),
    'U': (66, [L(12, [(8, 2), (8, 52)]), L(12, [(58, 2), (58, 52)]),
               A(11, 33, 50, 25, 20, 0, 180),
               HB(0, 16, 4, 4), HB(50, 66, 4, 4)]),
    'V': (62, [L(11, [(6, 2), (31, 68)]), L(11, [(31, 68), (56, 2)]),
               HB(0, 12, 4, 4), HB(50, 62, 4, 4)]),
    'W': (72, [L(10, [(4, 2), (18, 68)]), L(10, [(18, 68), (36, 14)]),
               L(10, [(36, 14), (54, 68)]), L(10, [(54, 68), (68, 2)])]),
    'X': (62, [L(10, [(8, 2), (54, 68)]), L(10, [(54, 2), (8, 68)]),
               HB(2, 14, 4, 4), HB(48, 60, 4, 4),
               HB(2, 14, 66, 4), HB(48, 60, 66, 4)]),
    'Y': (62, [L(11, [(6, 2), (31, 36)]), L(11, [(56, 2), (31, 36)]),
               *V(31, 36, 68, 12), HB(0, 12, 4, 4), HB(50, 62, 4, 4)]),
    'Z': (58, [HB(4, 54, 4, 7), L(9, [(52, 6), (8, 64)]), HB(4, 54, 66, 7)]),
    # ---- lowercase: x-height top 22, baseline 70, descender 92 ----
    'a': (54, [A(9, 26, 48, 20, 24, 0, 360), *V(46, 20, 68, 9)]),
    'b': (56, [*V(8, 0, 68, 11), A(9, 28, 48, 20, 22, 0, 360)]),
    'c': (50, [A(9, 27, 46, 20, 24, 300, 60)]),
    'd': (56, [A(9, 26, 48, 20, 22, 0, 360), *V(46, 0, 68, 11)]),
    'e': (52, [A(9, 26, 46, 20, 24, 300, 60), HB(6, 46, 44, 6)]),
    'f': (46, [L(10, [(26, 12), (26, 68)]),
               A(10, 26, 14, 16, 14, 180, 300), HB(10, 42, 34, 6)]),
    'g': (54, [A(9, 26, 46, 20, 22, 0, 360), *V(46, 20, 80, 9),
               A(9, 30, 80, 16, 12, 0, 180)]),
    'h': (56, [*V(8, 0, 68, 11), A(10, 28, 46, 20, 24, 180, 360),
               L(10, [(48, 46), (48, 68)])]),
    'i': (30, [L(10, [(15, 22), (15, 68)]), D(6, 15, 9), HB(8, 22, 66, 4)]),
    'j': (34, [L(10, [(19, 22), (19, 78)]),
               A(10, 19, 78, 11, 12, 0, 180), D(6, 19, 9)]),
    'k': (54, [*V(8, 0, 68, 11), L(9, [(20, 40), (44, 22)]),
               L(9, [(26, 36), (48, 68)])]),
    'l': (30, [*V(15, 0, 68, 11), HB(8, 22, 66, 4)]),
    'm': (78, [L(10, [(6, 22), (6, 68)]),
               A(9, 22, 44, 16, 22, 180, 360), L(9, [(38, 44), (38, 68)]),
               A(9, 54, 44, 16, 22, 180, 360), L(9, [(70, 44), (70, 68)])]),
    'n': (56, [*V(8, 22, 68, 10), A(10, 28, 46, 20, 24, 180, 360),
               L(10, [(48, 46), (48, 68)])]),
    'o': (52, [A(10, 26, 46, 20, 24, 0, 360)]),
    'p': (56, [*V(8, 22, 90, 11), A(9, 28, 48, 20, 22, 0, 360)]),
    'q': (56, [A(9, 26, 48, 20, 22, 0, 360), *V(46, 22, 90, 11)]),
    'r': (46, [*V(8, 22, 68, 10), A(9, 24, 36, 16, 14, 180, 360)]),
    's': (50, [A(9, 25, 34, 18, 13, 180, 360),
               A(9, 25, 58, 18, 13, 0, 180)]),
    't': (44, [L(10, [(22, 6), (22, 64)]),
               A(9, 32, 62, 12, 10, 90, 180), HB(8, 36, 32, 6)]),
    'u': (50, [L(10, [(8, 22), (8, 56)]), L(10, [(42, 22), (42, 56)]),
               A(10, 25, 54, 17, 16, 0, 180)]),
    'v': (50, [L(9, [(6, 22), (25, 68)]), L(9, [(25, 68), (44, 22)])]),
    'w': (52, [L(9, [(4, 22), (13, 68)]), L(9, [(13, 68), (25, 30)]),
               L(9, [(25, 30), (37, 68)]), L(9, [(37, 68), (48, 22)])]),
    'x': (50, [L(9, [(6, 22), (44, 68)]), L(9, [(44, 22), (6, 68)])]),
    'y': (50, [L(9, [(6, 22), (25, 58)]), L(9, [(44, 22), (25, 58)]),
               L(9, [(25, 58), (13, 90)])]),
    'z': (52, [HB(6, 46, 24, 6), L(8, [(44, 26), (8, 66)]), HB(6, 46, 66, 6)]),
    # ---- digits: cap top 0, baseline 70 ----
    '0': (56, [A(11, 28, 35, 24, 35, 0, 360)]),
    '1': (48, [L(9, [(10, 26), (28, 4)]), *V(28, 2, 68, 11),
               HB(12, 44, 66, 5)]),
    '2': (56, [A(9, 28, 20, 22, 18, 180, 360), L(9, [(50, 20), (10, 64)]),
               HB(8, 50, 66, 6)]),
    '3': (56, [A(10, 28, 19, 20, 16, 220, 400),
               A(10, 28, 52, 22, 17, 320, 540)]),
    '4': (54, [L(9, [(38, 2), (10, 48)]), HB(6, 50, 48, 7),
               *V(38, 2, 68, 11)]),
    '5': (54, [HB(10, 48, 4, 6), L(10, [(10, 4), (10, 34)]),
               A(10, 30, 50, 20, 17, 320, 540)]),
    '6': (56, [A(10, 28, 46, 22, 24, 0, 360), L(9, [(38, 26), (50, 6)])]),
    '7': (54, [HB(8, 50, 4, 7), L(10, [(48, 6), (20, 68)])]),
    '8': (52, [A(9, 26, 20, 18, 16, 0, 360),
               A(9, 26, 51, 20, 19, 0, 360)]),
    '9': (56, [A(10, 28, 24, 22, 22, 0, 360), L(9, [(46, 28), (32, 68)])]),
    # ---- punctuation ----
    ' ': (28, []),
    '.': (20, [D(5, 10, 66)]),
    ',': (20, [D(5, 10, 66), L(6, [(10, 66), (4, 80)])]),
    ':': (20, [D(5, 10, 26), D(5, 10, 58)]),
    ';': (20, [D(5, 10, 26), D(5, 10, 58), L(6, [(10, 58), (4, 72)])]),
    '-': (48, [HB(8, 40, 36, 6)]),
    '/': (48, [L(8, [(38, 2), (10, 68)])]),
    '(': (30, [A(7, 34, 35, 20, 35, 250, 110)]),
    ')': (30, [A(7, 8, 35, 20, 35, 290, 70)]),
    '%': (64, [A(7, 18, 18, 10, 10, 0, 360),
               A(7, 46, 52, 10, 10, 0, 360), L(7, [(52, 4), (12, 66)])]),
    '&': (56, [A(7, 26, 24, 13, 12, 0, 360), L(7, [(38, 14), (14, 68)]),
               A(7, 26, 54, 16, 14, 0, 180)]),
    '+': (48, [HB(8, 40, 34, 7), L(7, [(24, 16), (24, 52)])]),
    '$': (52, [A(9, 26, 22, 16, 12, 180, 360),
               A(9, 26, 48, 16, 12, 0, 180), L(6, [(26, 2), (26, 68)])]),
    "'": (20, [L(7, [(12, 2), (8, 20)])]),
    '"': (36, [L(7, [(10, 2), (6, 20)]), L(7, [(26, 2), (22, 20)])]),
    '!': (20, [L(10, [(10, 2), (10, 52)]), D(5, 10, 64)]),
    '?': (52, [A(9, 26, 18, 18, 16, 200, 380), L(9, [(42, 26), (28, 44)]),
               D(5, 28, 62)]),
    '=': (48, [HB(8, 40, 26, 5), HB(8, 40, 46, 5)]),
    '•': (24, [D(6, 12, 40)]),
}

# characters normalised before lookup
NORMALISE = {'’': "'", '‘': "'", '“': '"', '”': '"',
             '–': '-', '—': '-', '…': '.', '×': 'x'}

# ------------------------------------------------------ font rendering ----
# Each glyph is rasterised once per (char, em_px, weight, italic) into a
# coverage map at output resolution, cached, then blended onto the page.
# Coverage comes from a SS=4 supersampled mask: smooth curves get grey
# edge pixels instead of stair-steps. A sqrt gamma keeps 1 px strokes
# dark, as in the v6 bitmap renderer.
_GLYPH_CACHE = {}


def _arc_points(cx, cy, rx, ry, a0, a1):
    step = 12.0
    pts = []
    if a1 >= a0:
        n = max(2, int((a1 - a0) / step) + 1)
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    else:
        n = max(2, int((a0 - a1) / step) + 1)
        for i in range(n + 1):
            a = math.radians(a0 - (a0 - a1) * i / n)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


def _fill_poly_mask(mask, mw, mh, pts):
    """Scanline-fill a polygon (float coords) into a bytearray mask."""
    if len(pts) < 3:
        return
    ys = [p[1] for p in pts]
    y0 = max(0, int(math.floor(min(ys))))
    y1 = min(mh - 1, int(math.ceil(max(ys))))
    n = len(pts)
    for y in range(y0, y1 + 1):
        yc = y + 0.5
        xs = []
        for i in range(n):
            x1, yy1 = pts[i]
            x2, yy2 = pts[(i + 1) % n]
            if (yy1 <= yc < yy2) or (yy2 <= yc < yy1):
                xs.append(x1 + (yc - yy1) * (x2 - x1) / (yy2 - yy1))
        xs.sort()
        row = y * mw
        for i in range(0, len(xs) - 1, 2):
            xa = max(0, int(math.floor(xs[i])))
            xb = min(mw - 1, int(math.ceil(xs[i + 1])))
            if xb >= xa:
                mask[row + xa:row + xb + 1] = b'\x01' * (xb - xa + 1)


def _fill_circle_mask(mask, mw, mh, cx, cy, r):
    y0 = max(0, int(math.floor(cy - r)))
    y1 = min(mh - 1, int(math.ceil(cy + r)))
    for y in range(y0, y1 + 1):
        dy = (y + 0.5) - cy
        if r * r <= dy * dy:
            continue  # row is outside the circle: fill nothing
        dx = (r * r - dy * dy) ** 0.5
        xa = max(0, int(math.floor(cx - dx)))
        xb = min(mw - 1, int(math.ceil(cx + dx)))
        if xb >= xa:
            mask[y * mw + xa:y * mw + xb + 1] = b'\x01' * (xb - xa + 1)


def _stroke_segment(mask, mw, mh, p0, p1, half_w, caps=True):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = (dx * dx + dy * dy) ** 0.5
    if ln < 1e-6:
        _fill_circle_mask(mask, mw, mh, p0[0], p0[1], half_w)
        return
    nx, ny = -dy / ln * half_w, dx / ln * half_w
    _fill_poly_mask(mask, mw, mh, [
        (p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny),
        (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)])
    if caps:
        _fill_circle_mask(mask, mw, mh, p0[0], p0[1], half_w)
        _fill_circle_mask(mask, mw, mh, p1[0], p1[1], half_w)


def _render_glyph(ch, em, weight, italic):
    """Return (advance_px, w_px, h_px, [(dx, dy, alpha), ...]) where
    alpha is 0..1 coverage for each inked output pixel."""
    key = (ch, em, weight, italic)
    hit = _GLYPH_CACHE.get(key)
    if hit is not None:
        return hit
    width, strokes = GLYPHS.get(ch, GLYPHS[' '])
    k = em * SS / 100.0          # mask px per em unit
    shear = 0.16 if italic else 0.0
    # mask size: em box is 100 units tall. Italic shear moves the cap
    # top left by up to 11.2 units and descenders right by ~3.5 units;
    # allow ~21 units of left margin plus stroke half-width.
    pad = 2
    pad_l = pad + (int(math.ceil(21 * k)) if italic else 0)
    mw = int(math.ceil((width + 34) * k)) + 2 * pad
    mh = int(math.ceil(100 * k)) + 2 * pad
    mask = bytearray(mw * mh)

    def tx(x, y):
        return pad_l + (x + shear * (y - 70)) * k, pad + y * k

    for st in strokes:
        kind = st[0]
        if kind == 'L':
            wdt = st[1] * weight
            pts = [tx(x, y) for x, y in st[2]]
            hw = wdt * k / 2.0
            for a, b in zip(pts, pts[1:]):
                _stroke_segment(mask, mw, mh, a, b, hw, caps=False)
            for p in pts:
                _fill_circle_mask(mask, mw, mh, p[0], p[1], hw)
        elif kind == 'A':
            wdt = st[1] * weight
            pts = [tx(x, y) for x, y in
                   _arc_points(st[2], st[3], st[4], st[5], st[6], st[7])]
            hw = wdt * k / 2.0
            for a, b in zip(pts, pts[1:]):
                _stroke_segment(mask, mw, mh, a, b, hw, caps=False)
            for p in pts[::4]:
                _fill_circle_mask(mask, mw, mh, p[0], p[1], hw)
        elif kind == 'D':
            cx, cy = tx(st[2], st[3])
            _fill_circle_mask(mask, mw, mh, cx, cy, st[1] * weight * k)
    # downsample SSxSS -> coverage; collect inked output pixels
    out_w = (mw + SS - 1) // SS
    out_h = (mh + SS - 1) // SS
    ink = []
    for oy in range(out_h):
        for ox in range(out_w):
            s = 0
            for my in range(oy * SS, min(mh, (oy + 1) * SS)):
                row = my * mw + ox * SS
                # clamp the window to the row: never bleed into the
                # next row's first columns (that painted a phantom
                # vertical line at every glyph's right edge).
                s += sum(mask[row:min(row + SS, (my + 1) * mw)])
            if s:
                ink.append((ox, oy, (s / (SS * SS)) ** 0.5))
    adv = int(round(width * em / 100.0)) + max(0, int(round(0.03 * em)))
    res = (adv, out_w, out_h, ink)
    _GLYPH_CACHE[key] = res
    return res


def _glyph_adv(ch, em, weight, italic):
    return _render_glyph(ch, em, weight, italic)[0]


# -------------------------------------------------------------- canvas ----
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return (self.buf[i], self.buf[i + 1], self.buf[i + 2])

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = c[0]
                self.buf[i + 1] = c[1]
                self.buf[i + 2] = c[2]

    def hline(self, x0, x1, y, c, t=1):
        if x1 < x0:
            x0, x1 = x1, x0
        for yy in range(y, y + t):
            for xx in range(x0, x1 + 1):
                self.set(xx, yy, c)

    def vline(self, x, y0, y1, c, t=1):
        if y1 < y0:
            y0, y1 = y1, y0
        for xx in range(x, x + t):
            for yy in range(y0, y1 + 1):
                self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.fill_rect(x, y, t, t, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def fill_circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.hline(cx - dx, cx + dx, cy + dy, c)

    def circle(self, cx, cy, r, c, t=1):
        x, y, d = 0, r, 1 - r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.fill_rect(px, py, t, t, c)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

    def fill_poly(self, pts, c):
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(xs[i]), int(xs[i + 1]), y, c)

    def star(self, cx, cy, r, c, t=2):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                       (1, 1), (1, -1), (-1, 1), (-1, -1)):
            self.line(cx, cy, cx + dx * r, cy + dy * r, c, t)
        self.fill_circle(cx, cy, max(2, r // 4), c)

    # ------------------------------------------------------------ text ----
    def vtext(self, x, y, s, em, c, weight=1.0, italic=False):
        """Draw smooth vector serif text. (x, y) = top-left of the em
        box; em = em height in px. Returns x just past the last glyph."""
        for ch in s:
            ch = NORMALISE.get(ch, ch)
            adv, gw, gh, ink = _render_glyph(ch, em, weight, italic)
            for dx, dy, a in ink:
                px, py = x + dx, y + dy
                if 0 <= px < self.w and 0 <= py < self.h:
                    if a >= 1.0:
                        self.set(px, py, c)
                    else:
                        bg = self.get(px, py)
                        self.set(px, py, tuple(
                            int(bg[i] + (c[i] - bg[i]) * a + 0.5)
                            for i in range(3)))
            x += adv
        return x

    def vtext_width(self, s, em, weight=1.0, italic=False):
        w = 0
        for ch in s:
            ch = NORMALISE.get(ch, ch)
            w += _glyph_adv(ch, em, weight, italic)
        return w

    def vtext_centred(self, cx, y, s, em, c, weight=1.0, italic=False):
        x = cx - self.vtext_width(s, em, weight, italic) // 2
        self.vtext(x, y, s, em, c, weight, italic)
        return x

    def vtext_right(self, x_right, y, s, em, c, weight=1.0, italic=False):
        x = x_right - self.vtext_width(s, em, weight, italic)
        self.vtext(x, y, s, em, c, weight, italic)
        return x

    def vwrap(self, s, em, max_w, weight=1.0, italic=False):
        lines, cur = [], ''
        for word in s.split(' '):
            trial = (cur + ' ' + word).strip() if cur else word
            if self.vtext_width(trial, em, weight, italic) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


# ------------------------------------------------------------------ png ----
def write_png(path, canvas):
    w, h = canvas.w, canvas.h
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += canvas.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack('>I', len(data)) + typ + data
        out += struct.pack('>I', zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
           + chunk(b'IDAT', comp) + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)
    return png


# ------------------------------------------------------- drawing helpers ----
def grad_v(cv, x, y, w, h, c1, c2):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        cv.hline(x, x + w - 1, y + yy, c)

def grad_h(cv, x, y, w, h, c1, c2):
    for xx in range(w):
        t = xx / max(1, w - 1)
        c = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        cv.vline(x + xx, y, y + h - 1, c)

def hatch_diag(cv, x, y, w, h, c, step=6):
    for k in range(-h, w + h, step):
        cv.line(x + k, y + h - 1, x + k + h, y, c, 1)

def stipple(cv, x, y, w, h, c, seed=7, density=3):
    s = seed
    for yy in range(y, y + h, 2):
        for xx in range(x, x + w, 2):
            s = (s * 1103515245 + 12345) & 0x7FFFFFFF
            if s % 10 < density:
                cv.set(xx, yy, c)

def apply_grain(cv, amp=1, cov=0.45):
    """Fine deterministic newsprint grain. amp 1 on 45% of pixels
    keeps the file well under 1 MiB (v5: ~720 KB at this setting)."""
    buf = cv.buf
    state = 987654321
    span = 2 * amp + 1
    for i in range(0, len(buf), 3):
        state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
        px = i // 3
        h = ((px * 2654435761) & 0xFFFFFFFF) / 4294967296.0
        if h >= cov:
            continue
        d = (state >> 24) % span - amp
        if d:
            v = buf[i] + d
            buf[i] = 255 if v > 255 else (0 if v < 0 else v)
        d = ((state >> 16) & 0xFF) % span - amp
        if d:
            v = buf[i + 1] + d
            buf[i + 1] = 255 if v > 255 else (0 if v < 0 else v)
        d = ((state >> 8) & 0xFF) % span - amp
        if d:
            v = buf[i + 2] + d
            buf[i + 2] = 255 if v > 255 else (0 if v < 0 else v)

# ---------------------------------------------------------- pictograms ----
# Every picture is drawn from geometric primitives in code -- original
# work, no images, no copying of any reference artwork.

def dashed(cv, x0, y0, x1, y1, c):
    n = max(abs(x1 - x0), abs(y1 - y0)) // 8
    if n == 0:
        return
    for i in range(n):
        t0 = i / n
        t1 = (i + 0.55) / n
        cv.line(int(x0 + (x1 - x0) * t0), int(y0 + (y1 - y0) * t0),
                int(x0 + (x1 - x0) * t1), int(y0 + (y1 - y0) * t1), c, 1)


def pic_box(cv, x, y, w, h, bg=PANEL):
    cv.fill_rect(x, y, w, h, bg)
    cv.hline(x, x + w - 1, y, INK, 1)
    cv.hline(x, x + w - 1, y + h - 1, INK, 1)
    cv.vline(x, y, y + h - 1, INK, 1)
    cv.vline(x + w - 1, y, y + h - 1, INK, 1)


def tag(cv, x, y, s, em=10):
    """Red tag with paper text; returns its width."""
    w = cv.vtext_width(s, em, 1.3) + 8
    h = em + 5
    cv.fill_rect(x, y, w, h, RED)
    cv.vtext(x + 4, y + 2, s, em, PAPER, 1.3)
    return w


def tag_white(cv, x, y, s, em=10):
    """Paper tag with ink text and ink frame; returns its width."""
    w = cv.vtext_width(s, em, 1.3) + 8
    h = em + 5
    cv.fill_rect(x, y, w, h, PAPER)
    cv.hline(x, x + w - 1, y, INK, 1)
    cv.hline(x, x + w - 1, y + h - 1, INK, 1)
    cv.vline(x, y, y + h - 1, INK, 1)
    cv.vline(x + w - 1, y, y + h - 1, INK, 1)
    cv.vtext(x + 4, y + 2, s, em, INK, 1.3)
    return w


def caption_strip(cv, x, y, w, s, em=9):
    cv.fill_rect(x, y, w, em + 4, NAVY)
    cv.vtext(x + 4, y + 2, s, em, PAPER, 1.2)


def pic_kyiv(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (16, 26, 54), (38, 58, 96))
    mx, my = ox + int(w * 0.88), oy + int(h * 0.16)
    cv.fill_circle(mx, my, 11, (210, 210, 190))
    cv.fill_circle(mx, my, 7, (240, 238, 220))
    cv.fill_circle(mx - 2, my - 2, 2, (200, 200, 185))
    for sx, sy in ((0.06, 0.12), (0.14, 0.07), (0.24, 0.18), (0.33, 0.08),
                   (0.44, 0.14), (0.55, 0.07), (0.66, 0.16), (0.76, 0.06),
                   (0.05, 0.30), (0.20, 0.28), (0.38, 0.26), (0.60, 0.28),
                   (0.82, 0.30), (0.94, 0.10), (0.48, 0.20), (0.70, 0.24)):
        px, py = ox + int(w * sx), oy + int(h * sy)
        cv.fill_rect(px, py, 2, 2, PAPER)
        if (int(sx * 100) + int(sy * 100)) % 3 == 0:
            cv.hline(px - 2, px + 3, py, PAPER, 1)
            cv.vline(px, py - 2, py + 3, PAPER, 1)
    base = oy + int(h * 0.58)
    bx = ox + 4
    bi = 0
    while bx < ox + w - 8:
        bw = 14 + (bi * 7) % 18
        bh = 12 + (bi * 11) % 22
        cv.fill_rect(bx, base - bh, bw, bh, (10, 16, 34))
        cv.hline(bx, bx + bw - 1, base - bh, (90, 100, 130), 1)
        for wy in range(base - bh + 3, base - 2, 5):
            for wx in range(bx + 3, bx + bw - 3, 5):
                if (wx * 3 + wy * 7 + bi) % 5 < 2:
                    cv.fill_rect(wx, wy, 2, 2, (255, 205, 90))
        bx += bw + 3
        bi += 1
    for (tx0, tx1) in ((0.98, 0.62), (0.80, 0.45), (0.62, 0.30)):
        dashed(cv, ox + int(w * tx0), oy + 2,
               ox + int(w * tx1), oy + int(h * 0.55), PAPER)
        cv.fill_circle(ox + int(w * tx0) - 6, oy + 8, 2, YELLOW)
    dy = base
    cv.hline(ox + 6, ox + w - 7, dy, (170, 170, 170), 4)
    cv.hline(ox + 6, ox + w - 7, dy + 4, (110, 110, 110), 1)
    cv.line(ox + int(w * 0.15), dy + 4, ox + w // 2, dy + 14,
            (150, 150, 150), 3)
    cv.line(ox + w // 2, dy + 14, ox + int(w * 0.85), dy + 4,
            (150, 150, 150), 3)
    for fx in (0.12, 0.28, 0.50, 0.72, 0.88):
        cv.vline(ox + int(w * fx), dy + 4, oy + int(h * 0.82),
                 (140, 140, 140), 3)
    for bfx, bc in ((0.30, YELLOW), (0.66, RED), (0.84, YELLOW)):
        px, py = ox + int(w * bfx), dy - 6
        cv.fill_circle(px, py, 12, (200, 90, 20))
        cv.fill_circle(px, py, 8, (240, 140, 40))
        cv.star(px, py, 9, bc, 2)
        cv.fill_circle(px, py, 3, PAPER)
        cv.fill_circle(px - 8, py - 12, 4, (120, 120, 120))
        cv.fill_circle(px + 6, py - 14, 5, (100, 100, 100))
        cv.vline(px, oy + int(h * 0.86), oy + h - 4, (240, 160, 60), 2)
    wy = oy + int(h * 0.84)
    grad_v(cv, ox, wy, w, h - int(h * 0.84), (46, 78, 130), (24, 48, 92))
    for wx in range(ox + 6, ox + w - 10, 14):
        cv.line(wx, wy + 5, wx + 7, wy + 2, (180, 200, 230), 1)
        cv.line(wx + 7, wy + 2, wx + 14, wy + 5, (180, 200, 230), 1)


def pic_cyclone(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (86, 132, 190), (52, 96, 158))
    for wy in range(oy + 8, oy + h - 6, 12):
        for wx in range(ox + 4, ox + int(w * 0.80), 18):
            if (wx + wy) % 36 < 18:
                cv.hline(wx, wx + 8, wy, (150, 190, 230), 1)
    for cx0, cy0, r0 in ((0.10, 0.10, 7), (0.16, 0.08, 9), (0.22, 0.11, 6),
                         (0.70, 0.09, 6), (0.76, 0.12, 8)):
        cv.fill_circle(ox + int(w * cx0), oy + int(h * cy0), r0,
                       (225, 232, 240))
    cx, cy = ox + int(w * 0.42), oy + int(h * 0.52)
    for i, r in enumerate((5, 10, 15, 20, 25, 30, 35)):
        cv.circle(cx - i * 2, cy - i, r, PAPER, 2)
        cv.circle(cx - i * 2, cy - i, r - 1, (190, 210, 235), 1)
    cv.fill_circle(cx, cy, 5, (240, 240, 235))
    cv.circle(cx, cy, 8, RED, 2)
    for k in range(12):
        a = 2 * math.pi * k / 12
        x0 = cx + int(10 * math.cos(a))
        y0 = cy + int(10 * math.sin(a))
        x1 = cx + int(34 * math.cos(a + 0.5))
        y1 = cy + int(34 * math.sin(a + 0.5))
        cv.line(x0, y0, x1, y1, (200, 220, 240), 1)
    for rx, ry in ((0.05, 0.15), (0.11, 0.32), (0.03, 0.52), (0.09, 0.72),
                   (0.14, 0.88), (0.60, 0.82), (0.66, 0.68), (0.58, 0.20)):
        cv.line(ox + int(w * rx), oy + int(h * ry),
                ox + int(w * rx) + 7, oy + int(h * ry) + 9, PAPER, 2)
    lx0 = ox + int(w * 0.82)
    grad_v(cv, lx0, oy, w - int(w * 0.82), h, (214, 196, 152), (186, 166, 122))
    cv.line(lx0, oy, lx0 + 6, oy + h // 3, (120, 100, 60), 2)
    cv.line(lx0 + 6, oy + h // 3, lx0 - 2, oy + 2 * h // 3, (120, 100, 60), 2)
    cv.line(lx0 - 2, oy + 2 * h // 3, lx0 + 4, oy + h, (120, 100, 60), 2)
    for tx, ty in ((0.87, 0.20), (0.90, 0.38), (0.86, 0.60), (0.92, 0.78)):
        cv.fill_rect(ox + int(w * tx), oy + int(h * ty), 3, 3, (90, 70, 40))
    lx, ly = ox + int(w * 0.80), oy + int(h * 0.45)
    dashed(cv, cx + 30, cy, lx - 4, ly, RED)
    cv.fill_circle(lx, ly, 5, RED)
    cv.circle(lx, ly, 9, PAPER, 2)
    cv.circle(lx, ly, 12, RED, 1)
    cv.line(lx - 16, ly + 14, lx - 6, ly + 14, PAPER, 2)
    cv.fill_poly([(lx - 6, ly + 14), (lx - 12, ly + 10),
                  (lx - 12, ly + 18)], PAPER)


def pic_selloff(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (30, 48, 84), (16, 28, 58))
    for gy in range(oy + 10, oy + h - 8, 14):
        cv.hline(ox + 4, ox + int(w * 0.52), gy, (60, 80, 120), 1)
    for gx in range(ox + 8, ox + int(w * 0.52), 16):
        cv.vline(gx, oy + 6, oy + int(h * 0.82), (60, 80, 120), 1)
    bw = int(w * 0.055)
    bx0 = ox + int(w * 0.05)
    tops = (0.18, 0.24, 0.32, 0.40, 0.48, 0.56)
    bots = (0.42, 0.50, 0.55, 0.62, 0.68, 0.74)
    for i, (t0, b0) in enumerate(zip(tops, bots)):
        x = bx0 + i * (bw + 5)
        cv.vline(x + bw // 2, oy + int(h * t0) - 4, oy + int(h * b0) + 4,
                 (200, 200, 200), 1)
        cv.fill_rect(x, oy + int(h * t0), bw, int(h * (b0 - t0)),
                     (214, 48, 48) if i % 2 == 0 else (220, 90, 70))
    x0, y0 = ox + int(w * 0.05), oy + int(h * 0.12)
    x1, y1 = ox + int(w * 0.50), oy + int(h * 0.72)
    for yy in range(y0, y1):
        xx = x0 + (yy - y0) * (x1 - x0) // max(1, y1 - y0)
        cv.vline(xx, yy, oy + int(h * 0.80), (120, 30, 30), 1)
    cv.line(x0, y0, x1, y1, RED, 3)
    cv.line(x0, y0, x1, y1, (255, 120, 120), 1)
    cv.fill_poly([(x1, y1), (x1 - 12, y1 - 2), (x1 - 2, y1 - 12)], RED)
    nx = ox + int(w * 0.55)
    for i, (s, v) in enumerate((("S&P -3.7%", 37), ("NASDAQ -5.28%", 53),
                                ("NIKKEI -5.06%", 51), ("GOLD -4.6%", 46),
                                ("BITCOIN $58K", 58))):
        yy = oy + 10 + i * 17
        cv.fill_rect(nx, yy + 2, v // 2, 5, RED)
        cv.fill_rect(nx, yy + 2, v // 4, 5, (255, 120, 120))
        cv.vtext(nx + 36, yy, s, 9, PAPER, 1.1)
        cv.fill_poly([(nx + 32, yy + 2), (nx + 28, yy + 2),
                      (nx + 30, yy + 7)], RED)


def pic_riyadh(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (18, 24, 52), (44, 52, 88))
    mx, my = ox + int(w * 0.12), oy + int(h * 0.14)
    cv.fill_circle(mx, my, 8, (225, 225, 205))
    cv.fill_circle(mx, my, 5, (245, 244, 228))
    for sx, sy in ((0.30, 0.08), (0.45, 0.14), (0.62, 0.07), (0.80, 0.12),
                   (0.92, 0.20), (0.22, 0.22), (0.55, 0.20)):
        cv.fill_rect(ox + int(w * sx), oy + int(h * sy), 2, 2, PAPER)
    base = oy + int(h * 0.72)
    # skyline: low blocks with lit windows + Kingdom Centre tower
    bx = ox + 4
    bi = 0
    while bx < ox + w - 10:
        bw = 12 + (bi * 5) % 14
        bh = 10 + (bi * 9) % 18
        cv.fill_rect(bx, base - bh, bw, bh, (10, 14, 30))
        for wy in range(base - bh + 3, base - 2, 5):
            for wx in range(bx + 3, bx + bw - 3, 5):
                if (wx * 3 + wy * 7 + bi) % 4 < 2:
                    cv.fill_rect(wx, wy, 2, 2, (255, 205, 90))
        bx += bw + 3
        bi += 1
    # Kingdom Centre tower: tall slab with arched opening near the top
    tx = ox + int(w * 0.62)
    tw = 26
    cv.fill_rect(tx, oy + int(h * 0.06), tw, base - oy - int(h * 0.06),
                 (14, 20, 40))
    cv.hline(tx, tx + tw - 1, oy + int(h * 0.06), (120, 130, 160), 1)
    cv.fill_poly([(tx + 4, oy + int(h * 0.10)),
                  (tx + tw - 4, oy + int(h * 0.10)),
                  (tx + tw // 2, oy + int(h * 0.30))], (18, 24, 52))
    for wy in range(oy + int(h * 0.34), base - 4, 6):
        cv.fill_rect(tx + 4, wy, 3, 3, (255, 205, 90))
        cv.fill_rect(tx + tw - 7, wy, 3, 3, (255, 205, 90))
    # interceptor trails rising + bursts
    for (ix0, ix1) in ((0.18, 0.34), (0.42, 0.55), (0.78, 0.88)):
        dashed(cv, ox + int(w * ix0), oy + h - 14,
               ox + int(w * ix1), oy + int(h * 0.30), PAPER)
    for bfx, bfy in ((0.34, 0.30), (0.55, 0.26), (0.88, 0.32)):
        px, py = ox + int(w * bfx), oy + int(h * bfy)
        cv.fill_circle(px, py, 10, (200, 90, 20))
        cv.fill_circle(px, py, 6, (240, 140, 40))
        cv.star(px, py, 8, YELLOW, 2)
        cv.fill_circle(px, py, 2, PAPER)
    cv.hline(ox, ox + w - 1, base, (90, 90, 110), 2)
    for wx in range(ox + 6, ox + w - 10, 16):
        cv.fill_rect(wx, base + 5, 8, 2, (255, 205, 90))


def pic_flags(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (242, 236, 220), (228, 220, 200))
    stipple(cv, ox, oy, w, h, (200, 192, 170), seed=11, density=1)
    ex, ey, ew, eh = ox + int(w * 0.06), oy + int(h * 0.18), \
        int(w * 0.40), int(h * 0.62)
    cv.vline(ex - 3, ey - 4, ey + eh + 4, INK, 2)
    cv.fill_circle(ex - 2, ey - 5, 2, YELLOW)
    ux, uy, uw, uh = ox + int(w * 0.54), oy + int(h * 0.18), \
        int(w * 0.40), int(h * 0.62)
    cv.vline(ux - 3, uy - 4, uy + uh + 4, INK, 2)
    cv.fill_circle(ux - 2, uy - 5, 2, YELLOW)
    cv.fill_rect(ex, ey + eh + 1, ew, 3, (180, 172, 150))
    cv.fill_rect(ux, uy + uh + 1, uw, 3, (180, 172, 150))
    grad_v(cv, ex, ey, ew, eh, (40, 84, 180), (24, 58, 140))
    ecx, ecy = ex + ew // 2, ey + eh // 2
    for k in range(12):
        a = 2 * math.pi * k / 12 - math.pi / 2
        px = int(ecx + (eh * 0.30) * math.cos(a))
        py = int(ecy + (eh * 0.30) * math.sin(a))
        cv.fill_circle(px, py, 2, YELLOW)
        cv.hline(px - 3, px + 3, py, YELLOW, 1)
        cv.vline(px, py - 3, py + 3, YELLOW, 1)
    grad_v(cv, ux, uy, uw, uh, (40, 84, 180), (24, 58, 140))
    cv.line(ux, uy, ux + uw, uy + uh, PAPER, 4)
    cv.line(ux + uw, uy, ux, uy + uh, PAPER, 4)
    cv.line(ux, uy, ux + uw, uy + uh, RED, 2)
    cv.line(ux + uw, uy, ux, uy + uh, RED, 2)
    cv.fill_rect(ux + uw // 2 - 5, uy, 10, uh, PAPER)
    cv.fill_rect(ux, uy + uh // 2 - 5, uw, 10, PAPER)
    cv.fill_rect(ux + uw // 2 - 2, uy, 4, uh, RED)
    cv.fill_rect(ux, uy + uh // 2 - 2, uw, 4, RED)


def pic_globe(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (242, 236, 220), (226, 218, 198))
    stipple(cv, ox, oy, w, h, (200, 192, 170), seed=23, density=1)
    cx, cy = ox + w // 2, oy + int(h * 0.48)
    r = int(h * 0.30)
    cv.fill_circle(cx, cy, r, (120, 170, 215))
    cv.fill_circle(cx - 6, cy - 8, 7, (90, 160, 100))
    cv.fill_circle(cx + 8, cy + 2, 6, (90, 160, 100))
    cv.fill_circle(cx - 2, cy + 10, 5, (110, 170, 110))
    cv.fill_circle(cx + 10, cy - 10, 4, (90, 160, 100))
    cv.circle(cx, cy, r, INK, 2)
    cv.vline(cx, cy - r, cy + r, INK, 1)
    cv.hline(cx - r, cx + r, cy, INK, 1)
    cv.line(cx - int(r * 0.7), cy - int(r * 0.7),
            cx - int(r * 0.7), cy + int(r * 0.7), INK, 1)
    cv.line(cx + int(r * 0.7), cy - int(r * 0.7),
            cx + int(r * 0.7), cy + int(r * 0.7), INK, 1)
    cv.hline(cx - int(r * 0.85), cx + int(r * 0.85),
             cy - int(r * 0.55), INK, 1)
    cv.hline(cx - int(r * 0.85), cx + int(r * 0.85),
             cy + int(r * 0.55), INK, 1)
    cv.line(cx - r - 4, cy + r + 4, cx + r + 4, cy - r - 4, RED, 4)
    cv.line(cx - r - 2, cy + r + 2, cx + r + 2, cy - r - 2,
            (255, 130, 130), 1)
    cv.fill_circle(cx + r - 2, cy - r + 2, 6, RED)
    cv.vtext(cx + r - 5, cy - r - 2, "X", 9, PAPER, 1.2)


def pic_hack(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (20, 26, 40), (34, 44, 66))
    # server racks with blinking lights
    for i in range(3):
        rx = ox + int(w * (0.06 + i * 0.24))
        rw = int(w * 0.18)
        cv.fill_rect(rx, oy + int(h * 0.12), rw, int(h * 0.76), (12, 14, 22))
        cv.hline(rx, rx + rw - 1, oy + int(h * 0.12), (90, 100, 130), 1)
        for sy in range(oy + int(h * 0.18), oy + int(h * 0.84), 7):
            cv.fill_rect(rx + 3, sy, rw - 6, 2, (60, 70, 95))
            cv.fill_rect(rx + rw - 6, sy, 3, 3,
                         RED if (sy // 7 + i) % 3 == 0 else (80, 200, 120))
    # red padlock + warning triangle
    lx, ly = ox + int(w * 0.80), oy + int(h * 0.42)
    cv.circle(lx, ly - 8, 8, RED, 3)
    cv.fill_rect(lx - 12, ly - 2, 24, 18, RED)
    cv.fill_rect(lx - 2, ly + 4, 4, 8, PAPER)
    cv.fill_circle(lx, ly + 3, 2, PAPER)
    cv.fill_poly([(ox + int(w * 0.06), oy + int(h * 0.88)),
                  (ox + int(w * 0.20), oy + int(h * 0.88)),
                  (ox + int(w * 0.13), oy + int(h * 0.70))], YELLOW)
    cv.vtext(ox + int(w * 0.115), oy + int(h * 0.78), "!", 10, INK, 1.3)
    # breach dashes across the racks
    for dx in range(ox + 4, ox + w - 8, 10):
        if (dx // 10) % 2 == 0:
            cv.hline(dx, dx + 5, oy + int(h * 0.52), (255, 120, 120), 1)


def pic_quake(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (235, 228, 210), (210, 200, 175))
    # Andes peaks
    cv.fill_poly([(ox, oy + h), (ox + int(w * 0.28), oy + int(h * 0.18)),
                  (ox + int(w * 0.52), oy + h)], (120, 130, 140))
    cv.fill_poly([(ox + int(w * 0.30), oy + h),
                  (ox + int(w * 0.62), oy + int(h * 0.08)),
                  (ox + w, oy + h)], (100, 112, 124))
    cv.fill_poly([(ox + int(w * 0.24), oy + int(h * 0.26)),
                  (ox + int(w * 0.32), oy + int(h * 0.18)),
                  (ox + int(w * 0.28), oy + int(h * 0.30))], PAPER)
    cv.fill_poly([(ox + int(w * 0.58), oy + int(h * 0.16)),
                  (ox + int(w * 0.66), oy + int(h * 0.08)),
                  (ox + int(w * 0.62), oy + int(h * 0.20))], PAPER)
    # ground + jagged cracks
    gy = oy + int(h * 0.72)
    cv.fill_rect(ox, gy, w, h - int(h * 0.72), (150, 135, 105))
    cv.hline(ox, ox + w - 1, gy, INK, 2)
    cx = ox + int(w * 0.20)
    for dx, dy in ((0, 0), (8, 5), (4, 10), (12, 15), (6, 20)):
        cv.line(cx + dx, gy + dy, cx + dx + 6, gy + dy + 4, INK, 2)
    # shaking house: tilted block + roof + dust
    hx, hy = ox + int(w * 0.58), oy + int(h * 0.52)
    cv.fill_poly([(hx, hy), (hx + 34, hy - 6), (hx + 34, hy + 14),
                  (hx, hy + 20)], (90, 70, 50))
    cv.fill_poly([(hx - 4, hy), (hx + 17, hy - 14), (hx + 38, hy - 6),
                  (hx + 17, hy + 2)], INK)
    cv.fill_rect(hx + 6, hy + 4, 5, 6, PAPER)
    cv.fill_rect(hx + 20, hy + 2, 5, 6, PAPER)
    for dx, dy in ((-6, -8), (40, -12), (30, 6), (-2, 4)):
        cv.fill_circle(hx + dx, hy + dy, 3, (180, 170, 150))
    cv.vtext(ox + 4, oy + 4, "6.8", 11, RED, 1.3)


def pic_seaquake(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (150, 190, 220), (60, 110, 165))
    for cx0, cy0, r0 in ((0.14, 0.12, 6), (0.22, 0.09, 8), (0.70, 0.08, 6)):
        cv.fill_circle(ox + int(w * cx0), oy + int(h * cy0), r0, PAPER)
    # epicentre rings on the water
    cx, cy = ox + int(w * 0.42), oy + int(h * 0.58)
    for r in (6, 12, 18, 24, 30):
        cv.circle(cx, cy, r, PAPER, 2)
    cv.fill_circle(cx, cy, 4, RED)
    cv.star(cx, cy, 6, RED, 2)
    # wave lines + small island
    for wy in range(oy + int(h * 0.30), oy + h - 4, 10):
        for wx in range(ox + 4, ox + w - 10, 18):
            if (wx + wy) % 36 < 18:
                cv.hline(wx, wx + 8, wy, (200, 225, 245), 1)
    ix = ox + int(w * 0.80)
    cv.fill_poly([(ix - 14, oy + int(h * 0.82)), (ix + 14, oy + int(h * 0.82)),
                  (ix + 6, oy + int(h * 0.66)),
                  (ix - 6, oy + int(h * 0.66))], LAND)
    cv.fill_circle(ix, oy + int(h * 0.60), 5, GREEN)
    cv.vtext(ox + 4, oy + 4, "6.8", 11, RED, 1.3)


def pic_mercury(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (12, 14, 26), (30, 32, 52))
    for sx, sy in ((0.06, 0.10), (0.16, 0.06), (0.30, 0.14), (0.48, 0.08),
                   (0.66, 0.12), (0.80, 0.06), (0.90, 0.18), (0.10, 0.30),
                   (0.88, 0.32), (0.55, 0.22)):
        cv.fill_rect(ox + int(w * sx), oy + int(h * sy), 2, 2, PAPER)
    # Mercury: grey cratered disc + orbit ellipse
    cx, cy = ox + int(w * 0.38), oy + int(h * 0.55)
    r = int(h * 0.32)
    cv.fill_circle(cx, cy, r, (150, 140, 130))
    cv.fill_circle(cx - 6, cy - 8, 5, (120, 112, 104))
    cv.fill_circle(cx + 8, cy + 4, 4, (120, 112, 104))
    cv.fill_circle(cx - 2, cy + 10, 3, (125, 116, 108))
    cv.fill_circle(cx + 10, cy - 10, 3, (120, 112, 104))
    cv.fill_circle(cx - 12, cy + 2, 2, (125, 116, 108))
    cv.circle(cx, cy, r, (200, 195, 185), 1)
    # orbit ellipse (dashed) + spacecraft: body, panels, dish
    for k in range(24):
        a = 2 * math.pi * k / 24
        px = cx + int(52 * math.cos(a))
        py = cy + int(20 * math.sin(a))
        if k % 2 == 0:
            cv.fill_rect(px, py, 2, 2, PAPER)
    sx, sy = ox + int(w * 0.78), oy + int(h * 0.22)
    cv.fill_rect(sx - 8, sy - 5, 16, 10, (200, 200, 205))
    cv.fill_rect(sx - 22, sy - 3, 12, 6, (40, 90, 160))
    cv.fill_rect(sx + 10, sy - 3, 12, 6, (40, 90, 160))
    cv.line(sx, sy - 5, sx + 6, sy - 12, PAPER, 1)
    cv.fill_circle(sx + 7, sy - 13, 3, PAPER)
    cv.line(sx - 8, sy + 5, sx - 12, sy + 10, (255, 180, 80), 2)


def pic_summit(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (242, 236, 220), (226, 218, 198))
    stipple(cv, ox, oy, w, h, (200, 192, 170), seed=53, density=1)
    # three flags on poles behind a table
    for i, (fx, cols) in enumerate((
            (0.18, [(RED, 0.14), (PAPER, 0.14), (BLUE, 0.14)]),
            (0.50, [(RED, 0.42)]),
            (0.80, [(BLUE, 0.42)]))):
        px = ox + int(w * fx)
        cv.vline(px, oy + int(h * 0.10), oy + int(h * 0.62), INK, 2)
        cv.fill_circle(px, oy + int(h * 0.09), 2, YELLOW)
        fy = oy + int(h * 0.12)
        fh = int(h * 0.30)
        fw = int(w * 0.16)
        y = fy
        for col, frac in cols:
            cv.fill_rect(px + 2, y, fw, int(fh * frac), col)
            y += int(fh * frac)
        if i == 0:  # stars canton on the first flag
            for kx in range(3):
                for ky in range(2):
                    cv.fill_rect(px + 4 + kx * 5, fy + 2 + ky * 5, 2, 2,
                                 PAPER)
        if i == 1:  # star on the red flag
            cv.star(px + 2 + fw // 2, fy + fh // 2, 5, YELLOW, 1)
    # table + microphones + name cards
    ty = oy + int(h * 0.62)
    cv.fill_rect(ox + int(w * 0.06), ty, int(w * 0.88), 6, (90, 60, 35))
    cv.fill_rect(ox + int(w * 0.10), ty + 6, 4, oy + h - ty - 6, INK)
    cv.fill_rect(ox + int(w * 0.86), ty + 6, 4, oy + h - ty - 6, INK)
    for mx0 in (0.30, 0.50, 0.70):
        mx = ox + int(w * mx0)
        cv.line(mx, ty, mx + 4, ty - 12, INK, 2)
        cv.fill_circle(mx + 4, ty - 13, 3, INK)
        cv.fill_rect(mx - 8, ty - 22, 16, 7, PAPER)
        cv.hline(mx - 8, mx + 7, ty - 22, INK, 1)
        cv.hline(mx - 8, mx + 7, ty - 15, INK, 1)


def pic_fire(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (60, 60, 70), (35, 35, 45))
    # cooling tower + chimneys
    tx = ox + int(w * 0.14)
    cv.fill_poly([(tx, oy + h), (tx + 8, oy + int(h * 0.18)),
                  (tx + 30, oy + int(h * 0.18)), (tx + 38, oy + h)],
                 (140, 135, 125))
    cv.hline(tx + 8, tx + 30, oy + int(h * 0.18), (90, 85, 75), 2)
    for cx0 in (0.55, 0.68, 0.81):
        cxp = ox + int(w * cx0)
        cv.fill_rect(cxp, oy + int(h * 0.30), 10, oy + h - int(h * 0.30),
                     (110, 105, 95))
        cv.fill_rect(cxp - 1, oy + int(h * 0.28), 12, 3, INK)
    # flames licking the plant
    base = oy + int(h * 0.86)
    for fx, fh, col in ((0.30, 0.30, (230, 90, 30)),
                        (0.48, 0.42, (245, 140, 40)),
                        (0.66, 0.34, (230, 90, 30)),
                        (0.84, 0.26, (245, 160, 60))):
        px = ox + int(w * fx)
        ph = int(h * fh)
        cv.fill_poly([(px - 12, base), (px - 6, base - ph),
                      (px, base - ph - 8), (px + 6, base - ph),
                      (px + 12, base)], col)
        cv.fill_poly([(px - 5, base), (px - 2, base - ph + 6),
                      (px + 2, base - ph + 6), (px + 5, base)], YELLOW)
    # smoke + embers
    for sx0, sy0, r0 in ((0.48, 0.22, 7), (0.56, 0.14, 9), (0.66, 0.20, 6),
                         (0.36, 0.16, 5)):
        cv.fill_circle(ox + int(w * sx0), oy + int(h * sy0), r0,
                       (100, 100, 105))
    for ex0, ey0 in ((0.40, 0.55), (0.60, 0.45), (0.74, 0.60)):
        cv.fill_rect(ox + int(w * ex0), oy + int(h * ey0), 2, 2, YELLOW)
    cv.hline(ox, ox + w - 1, base, INK, 2)


def pic_plane(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (150, 190, 225), (205, 225, 240))
    for cx0, cy0, r0 in ((0.12, 0.14, 7), (0.20, 0.11, 9), (0.70, 0.10, 6),
                         (0.78, 0.14, 8), (0.45, 0.06, 5)):
        cv.fill_circle(ox + int(w * cx0), oy + int(h * cy0), r0, PAPER)
    # runway + terminal block
    ry = oy + int(h * 0.78)
    cv.fill_rect(ox, ry, w, h - int(h * 0.78), (120, 120, 125))
    cv.hline(ox, ox + w - 1, ry, INK, 2)
    for dx in range(ox + 6, ox + w - 8, 18):
        cv.fill_rect(dx, ry + 5, 10, 2, PAPER)
    cv.fill_rect(ox + int(w * 0.06), ry - 14, int(w * 0.22), 14,
                 (150, 145, 135))
    for wx in range(ox + int(w * 0.08), ox + int(w * 0.26), 8):
        cv.fill_rect(wx, ry - 10, 4, 4, (60, 70, 90))
    # plane taking off: fuselage, nose, tail, wings, engines
    px, py = ox + int(w * 0.52), oy + int(h * 0.48)
    cv.fill_poly([(px - 34, py), (px + 26, py - 6), (px + 38, py - 2),
                  (px + 30, py + 4), (px - 30, py + 6)], (30, 40, 60))
    cv.fill_poly([(px + 26, py - 6), (px + 38, py - 2), (px + 34, py + 2),
                  (px + 24, py - 2)], (200, 210, 225))
    cv.fill_poly([(px - 26, py - 2), (px - 34, py - 16), (px - 28, py - 16),
                  (px - 18, py - 3)], (30, 40, 60))
    cv.fill_poly([(px - 6, py - 2), (px + 2, py + 14), (px + 8, py + 14),
                  (px + 6, py - 1)], (30, 40, 60))
    cv.fill_poly([(px - 2, py + 4), (px + 10, py + 18), (px + 16, py + 18),
                  (px + 10, py + 3)], (30, 40, 60))
    cv.fill_circle(px + 4, py + 6, 3, (60, 70, 85))
    cv.fill_circle(px + 14, py + 5, 3, (60, 70, 85))
    # climb trail
    dashed(cv, px - 34, py + 8, ox + int(w * 0.10), oy + int(h * 0.72),
           (90, 90, 100))

# ------------------------------------------------------------------- map ----
MAP_SPANS = {
    1: [(3, 10), (17, 20), (32, 46)],
    2: [(2, 11), (17, 21), (24, 27), (31, 46)],
    3: [(2, 12), (23, 27), (30, 46)],
    4: [(2, 11), (24, 26), (30, 45)],
    5: [(3, 10), (24, 26), (31, 44)],
    6: [(4, 9), (25, 30), (32, 42)],
    7: [(5, 8), (24, 31), (33, 40)],
    8: [(6, 8), (25, 31), (35, 38)],
    9: [(7, 8), (26, 30), (36, 37)],
    10: [(8, 9), (10, 14), (27, 30)],
    11: [(10, 15), (27, 29)],
    12: [(11, 15), (28, 29)],
    13: [(12, 14), (28, 28), (39, 44)],
    14: [(12, 14), (38, 44)],
    15: [(13, 14), (39, 43)],
    16: [(13, 13)],
}
# story number -> (map col, map row, label dx, label dy)
# 10 (BepiColombo) is in orbit round Mercury: off the map, noted below.
MAP_DOTS = [
    (1, 26, 3, 8, -4), (2, 8, 4, -12, -8), (3, 31, 7, 6, 4),
    (4, 36, 7, 6, -4), (5, 27, 4, -14, -6), (6, 24, 3, -10, -10),
    (7, 10, 6, 6, 4), (8, 12, 11, -12, 2), (9, 42, 11, 6, -4),
    (11, 38, 5, 6, -4), (12, 30, 5, -4, -12), (13, 25, 2, 6, -6),
]

def draw_map(cv, ox, oy, cell=5):
    cv.fill_rect(ox, oy, 48 * cell, 18 * cell, (214, 228, 238))
    for gx in range(0, 48, 6):
        cv.vline(ox + gx * cell, oy, oy + 18 * cell, (190, 205, 220), 1)
    for gy in range(0, 18, 6):
        cv.hline(ox, ox + 48 * cell, oy + gy * cell, (190, 205, 220), 1)
    for row, spans in MAP_SPANS.items():
        for c0, c1 in spans:
            for c in range(c0, c1 + 1):
                cv.fill_rect(ox + c * cell, oy + row * cell,
                             cell, cell, LAND)
                if (c * 7 + row * 3) % 4 == 0:
                    cv.set(ox + c * cell + 1, oy + row * cell + 1,
                           (170, 152, 112))
    cv.hline(ox, ox + 48 * cell - 1, oy + 9 * cell, (150, 150, 150), 1)
    for num, col, row, dx, dy in MAP_DOTS:
        px = ox + col * cell + cell // 2
        py = oy + row * cell + cell // 2
        cv.fill_circle(px, py, 4, PAPER)
        cv.fill_circle(px, py, 3, RED)
        cv.vtext(px + dx, py + dy, str(num), 9, RED, 1.3)

# -------------------------------------------------------------- layout ----
MARGIN = 36
RIGHT = W - MARGIN  # 988

# Verification tags: CONFIRMED = 2+ outlets; OFFICIAL = on the record
# (IMD, CERN, UKMTO, government); REPORTED = one outlet;
# CLAIM = one side's account. Shown in each story's caption strip
# (leads/featured) or at the end of the line (ALSO), with the source.
LEGEND = ("HOW WE CHECKED — CONFIRMED = 2+ OUTLETS · OFFICIAL = ON THE "
          "RECORD · REPORTED = ONE OUTLET · CLAIM = ONE SIDE'S ACCOUNT")

STATS = [
    ("400+", "DRONES AND MISSILES", "FIRED AT UKRAINE"),
    ("-5.28%", "NASDAQ'S WORST WEEK", "SINCE 2020"),
    ("300,000+", "PEOPLE EVACUATED", "BEFORE CYCLONE AKVAN"),
    ("6.8", "MAGNITUDE OF THE PERU", "AND BANDA SEA QUAKES"),
    ("$7.25bn", "BAYER ROUNDUP DEAL", "APPROVED IN THE US"),
    ("7.1m", "ACRES BURNED IN", "INDONESIA'S 2026 FIRES"),
]

REGIONS = [
    ("EUROPE", 9, (36, 64, 120)),
    ("ASIA", 8, RED),
    ("MIDDLE EAST", 5, (150, 100, 20)),
    ("AFRICA", 6, GREEN),
    ("AMERICAS", 13, (90, 60, 140)),
    ("OCEANIA", 1, (20, 120, 120)),
    ("GLOBAL", 5, (70, 70, 70)),
]

# Grounded times only: Peru quake 00:09 UTC (research); US market close
# 21:00 UTC (16:00 EST); the rest are coarse labels, not invented times.
TIMELINE = [
    ("00:09 UTC", "PERU QUAKE 6.8 STRIKES"),
    ("MORNING", "TANKER HIT NEAR HORMUZ"),
    ("AFTERNOON", "COP31 INTO OVERTIME"),
    ("21:00 UTC", "S&P -3.7%, NASDAQ -5.28%"),
    ("NIGHT", "MISSILES FIRED AT RIYADH"),
]

TOP3 = [
    dict(pic=pic_kyiv, tag="KYIV + POLAND", tag2="MISSILES DOWN IN POLAND",
         cap="CONFIRMED · BBC", w=304, pic_h=102, head_em=19,
         kicker="1 KYIV AND EASTERN POLAND — WAR",
         head="Russia strikes Kyiv; missiles land in Poland",
         body="Russia fired 400+ drones and 110 missiles at Ukraine, "
              "killing at least eight in Kyiv and cutting power in ten "
              "regions. Two missiles and a drone came down in eastern "
              "Poland; PM Tusk called it a provocation. (BBC)"),
    dict(pic=pic_selloff, tag="AI SELL-OFF", tag2="WORST WEEK SINCE 2020",
         cap="CONFIRMED · BBC", w=304, pic_h=102, head_em=19,
         kicker="2 NEW YORK — LONDON — TOKYO — MARKETS",
         head="AI sell-off sinks world markets",
         body="The S&P 500 fell 3.7% into correction and the Nasdaq "
              "dropped 5.28% in its worst week since 2020, as doubts "
              "over AI spending crushed chip stocks. Nikkei fell 5.06%, "
              "gold 4.6%, Bitcoin to about $58,000. (BBC)"),
    dict(pic=pic_riyadh, tag="RIYADH", tag2="THIRD NIGHT OF ALERTS",
         cap="REPORTED · AL JAZEERA", w=304, pic_h=102, head_em=19,
         kicker="3 RIYADH — MISSILES",
         head="Houthis fire missiles at Riyadh",
         body="The coalition intercepted three Houthi ballistic missiles "
              "headed for Riyadh, the third straight night of alerts, as "
              "the Houthis threatened ports and a power station. Strikes "
              "hit Hodeida and Sanaa. (Al Jazeera)"),
]

MID5 = [
    dict(pic=pic_cyclone, tag="CYCLONE AKVAN", cap="OFFICIAL · IMD",
         kicker="4 ODISHA, INDIA — CYCLONE",
         head="Cyclone Akvan weakens over Odisha",
         body="Landfall near Gopalpur; 209 mm rain. 300,000+ evacuated. (IMD)"),
    dict(pic=pic_globe, tag="COP31: NO DEAL", cap="CONFIRMED · BBC",
         kicker="5 ANTALYA — CLIMATE",
         head="COP31 deadlocked over fossil fuels",
         body="Summit in Antalya into overtime; EU warns of a step back. (BBC)"),
    dict(pic=pic_flags, tag="UK-EU DEAL", cap="CONFIRMED · BBC",
         kicker="6 BRUSSELS — DIPLOMACY",
         head="UK and EU sign three post-Brexit deals",
         body="Food, carbon and youth mobility deals signed in Brussels. (BBC)"),
    dict(pic=pic_hack, tag="FBI HACKED", cap="REPORTED · BBC",
         kicker="7 WASHINGTON — CYBER",
         head="FBI database and USDA hacked",
         body="Hackers entered the FBI crime database and a USDA system. (BBC)"),
    dict(pic=pic_quake, tag="PERU QUAKE", cap="REPORTED · XINHUA",
         kicker="8 JUNIN, PERU — QUAKE",
         head="Peru quake shakes Andes, felt in Lima",
         body="Magnitude 6.8 in Junin, 129 km deep; felt in Lima. (Xinhua)"),
]

BOT5 = [
    dict(pic=pic_seaquake, tag="BANDA SEA QUAKE", cap="REPORTED · REUTERS",
         kicker="9 BANDA SEA — QUAKE",
         head="Banda Sea quake near Timor-Leste",
         body="Magnitude 6.8 at 143 km deep; no tsunami threat. (Reuters)"),
    dict(pic=pic_mercury, tag="MERCURY ORBIT", cap="CONFIRMED · BBC",
         kicker="10 MERCURY — SPACE",
         head="BepiColombo enters Mercury orbit",
         body="After eight years and six billion miles in space. (BBC)"),
    dict(pic=pic_summit, tag="TRUMP SUMMIT", cap="REPORTED · BBC",
         kicker="11 SHENZHEN — SUMMIT",
         head="Trump defends Putin and Xi ties",
         body="After the Shenzhen summit; Zelensky called Putin a killer. (BBC)"),
    dict(pic=pic_fire, tag="BASRA FIRE", cap="REPORTED · REUTERS",
         kicker="12 BASRA, IRAQ — FIRE",
         head="Basra power plant fire kills four",
         body="Gas blast at Hartha station; four dead, about 30 hurt. (Reuters)"),
    dict(pic=pic_plane, tag="DENMARK EXPELS", cap="CONFIRMED · BBC",
         kicker="13 COPENHAGEN — SECURITY",
         head="Denmark expels Russian diplomat over murder plot",
         body="Two arrested; attache expelled over plot on Kyivstoner. (BBC)"),
]

# 22 ALSO items (14-35). Dropped 12 of the 34 candidates: killer-robot
# talks, Nepal PM visit, Myanmar sanctions, Somalia UAE claims, ANC
# cities, Afghan mortar, Voyager 1, Harden 50-point game, Bolsonaro
# hospital, Gupta sentencing, Zecler sentences, Anthropic IPO slide —
# the weakest / least visual / most duplicative. Every item carries
# its source in parentheses plus its verification tag.
ALSO_LEFT = [
    "14 HORMUZ — TANKER HIT BY PROJECTILE (UKMTO) · OFFICIAL",
    "15 GAZA — CIVIL DEFENCE CRIPPLED (AL JAZEERA) · REPORTED",
    "16 IRAQ — ARMY IN MILITIA STRONGHOLD (REUTERS) · REPORTED",
    "17 KRYVYI RIH — MISSILE KILLS 2, WOUNDS 47 (AP) · REPORTED",
    "18 ESTONIA — BORDER WITH RUSSIA CLOSED (REUTERS) · REPORTED",
    "19 LATVIA — SHUT EU BORDERS TO RUSSIANS (POLITICO) · REPORTED",
    "20 TURKEY — IMAMOGLU DIPLOMA VOID (STRAITS TIMES) · REPORTED",
    "21 MOGADISHU — RALLY BACKS UAE OUSTER (QNC NEWS) · REPORTED",
    "22 S AFRICA — TRIBUTES FOR MLAMBO-NGCUKA, 71 (AFP) · REPORTED",
    "23 S AFRICA — 600 WOMEN KILLED IN 3 MONTHS (BBC) · REPORTED",
    "24 NIGERIA — BOAT SINKS, 4 DEAD (AL JAZEERA) · REPORTED",
]

ALSO_RIGHT = [
    "25 INDIA — TOXIC ALCOHOL KILLS 11 (STRAITS TIMES) · REPORTED",
    "26 S KOREA — 111 CAUGHT CHEATING IN SUNEUNG (BBC) · REPORTED",
    "27 AIR NIUGINI — EMERGENCY LANDING (STRAITS TIMES) · REPORTED",
    "28 INDONESIA — 7.1M ACRES BURNED (NUSANTARA ATLAS) · REPORTED",
    "29 BAYER — $7.25BN ROUNDUP DEAL APPROVED (BBC) · REPORTED",
    "30 CERN — FIRST ULTRA-RARE DECAY FOUND (CERN) · OFFICIAL",
    "31 VERSTAPPEN — ON POLE IN LAS VEGAS (BBC) · REPORTED",
    "32 PALISADES — MAN CONVICTED OF ARSON (BBC) · REPORTED",
    "33 TEXAS — SCREAMS IN HOUR-LONG EXECUTION (BBC) · REPORTED",
    "34 TRUMP — DATA-CENTRE TAX THREAT (BBC) · REPORTED",
    "35 NVIDIA — SEC PROBES ACCOUNTING (REUTERS) · REPORTED",
]

DATE_CHECK = ("DATE CHECK — LEFT OUT: ICJ MYANMAR GENOCIDE RULING "
              "(19 NOV) · GTA VI $3.79BN DAY ONE (ANNOUNCED 20 NOV) · "
              "KENYA TURKANA OIL DRILLING (20 NOV) · MAMDANI RIKERS PLAN "
              "(20 NOV) · UGANDA EBOLA BAN (19 NOV) · KYIV BRIDGES STRIKE "
              "(OVERNIGHT 20 NOV — ONLY THE POLAND LANDINGS, KRYVYI RIH, "
              "THE TOLL OF 8 AND THE NATO RESPONSE ARE 21 NOV) · PERU "
              "QUAKE STRUCK 19:09 LOCAL FRI (00:09 UTC SAT, REPORTED SAT) "
              "· DARAXONRASIB CANCER PILL (DATA 19-20 NOV). NOT YET — "
              "22 NOV: NEPAL PM'S INDIA VISIT (22-23 NOV) · BEPICOLOMBO "
              "ORBITERS SEPARATE IN DECEMBER · COP31 DEAL STILL PENDING.")

FOOTER_1 = ("Every story here happened, or was first reported, on "
            "Saturday 21 November 2026.")
FOOTER_2 = ("Sources: BBC · Reuters · AP · Al Jazeera · IMD · Xinhua · "
            "UKMTO · CERN · AFP · Politico · Straits Times · QNC News · "
            "Nusantara Atlas — Original drawings")


def draw_list_col(cv, x, y, items, w=336, em=10, leading=12):
    y0 = y
    for i, s in enumerate(items):
        assert cv.vtext_width(s, em) <= w + 4, s
        if i % 2 == 0:
            cv.fill_rect(x - 3, y - 2, w + 6, leading - 1, (243, 238, 226))
        cv.hline(x - 3, x + w + 2, y + leading - 2, (214, 206, 188), 1)
        cv.fill_rect(x - 3, y - 2, 2, leading - 1,
                     RED if i % 2 == 0 else (200, 120, 120))
        cv.vtext(x, y, s, em, GRAY)
        cv.vtext(x, y, s.split(' ')[0], em, RED, 1.3)
        y += leading
    return y


def draw():
    cv = Canvas(W, H, PAPER)

    # page frame
    cv.hline(12, 1011, 12, INK, 2)
    cv.hline(12, 1011, 1010, INK, 2)
    cv.vline(12, 12, 1010, INK, 2)
    cv.vline(1011, 12, 1010, INK, 2)

    # ---- kicker: paper name left, story count right ----
    cv.vtext(MARGIN, 20, "THE WORLD IN ONE DAY", 12, RED, 1.4)
    cv.vtext_right(RIGHT, 21,
                   "35 STORIES · 7 REGIONS · EVERY ONE DATED SATURDAY "
                   "21 NOVEMBER 2026", 10, INK, 1.2)
    cv.hline(MARGIN, RIGHT, 34, INK, 1)

    # ---- masthead: the date itself, huge smooth serif (rank 1 style) ----
    cv.vtext_centred(W // 2, 38, "Saturday 21 November 2026", 62, INK, 1.45)
    cv.vtext_centred(W // 2, 104,
                     "Russian missiles land in Poland · AI sell-off sinks "
                     "world markets · Houthis fire on Riyadh",
                     13, GRAY, 1.0, italic=True)
    cv.hline(MARGIN, RIGHT, 124, INK, 3)
    cv.hline(MARGIN, RIGHT, 129, INK, 1)

    # ---- THE DAY IN NUMBERS strip ----
    cv.fill_rect(MARGIN, 134, 952, 54, (244, 239, 228))
    cv.hline(MARGIN, RIGHT, 134, RED, 1)
    cv.hline(MARGIN, RIGHT, 187, INK, 1)
    cv.vtext(MARGIN, 137, "THE DAY IN NUMBERS", 9, RED, 1.3)
    widths = []
    for num, l1, l2 in STATS:
        widths.append(max(cv.vtext_width(num, 21, 1.3),
                          cv.vtext_width(l1, 8), cv.vtext_width(l2, 8)) + 14)
    extra = 952 - sum(widths)
    widths = [w + extra // len(widths) for w in widths]
    widths[-1] += 952 - sum(widths)
    x = MARGIN
    for (num, l1, l2), wseg in zip(STATS, widths):
        if x > MARGIN:
            cv.vline(x - 7, 148, 183, RED, 2)
        cv.vtext(x, 149, num, 21, INK, 1.3)
        cv.vtext(x, 170, l1, 8, GRAY)
        cv.vtext(x, 178, l2, 8, GRAY)
        x += wseg

    # ---- region bar ----
    total = sum(c for _, c, _ in REGIONS)
    widths = [max(64, 952 * c // total) for _, c, _ in REGIONS]
    _widest = widths.index(max(widths))
    widths[_widest] -= sum(widths) - 952
    x = MARGIN
    for (name, count, col), wseg in zip(REGIONS, widths):
        cv.fill_rect(x, 192, wseg, 17, col)
        cv.vtext_centred(x + wseg // 2, 196, "%s %d" % (name, count), 10,
                         PAPER, 1.2)
        x += wseg

    # ---- THE DAY IN UTC timeline ----
    cv.vtext(MARGIN, 216, "THE DAY IN UTC", 10, RED, 1.3)
    tx = 150
    for t, ev in TIMELINE:
        if tx > 150:
            cv.vline(tx - 6, 218, 238, (200, 192, 172), 1)
        cv.vtext(tx, 216, t, 10, RED, 1.3)
        cv.vtext(tx, 227, ev, 9, INK)
        tx += 167

    # ---- top 3 stories ----
    cv.vtext(MARGIN, 244, "TOP STORIES", 11, RED, 1.4)
    cv.hline(MARGIN + 92, RIGHT, 247, RED, 1)
    top_x = [MARGIN, 360, 684]
    for (sx, story) in zip(top_x, TOP3):
        w = story['w']
        ph = story['pic_h']
        pic_box(cv, sx, 254, w, ph)
        story['pic'](cv, sx + 1, 255, w - 2, ph - 2)
        tag(cv, sx + 5, 259, story['tag'])
        tag_white(cv, sx + 5, 276, story['tag2'])
        caption_strip(cv, sx + 1, 254 + ph - 14, w - 2, story['cap'])
        cv.vtext(sx, 362, story['kicker'], 10, RED, 1.3)
        y = 374
        for line in cv.vwrap(story['head'], story['head_em'], w, 1.3):
            cv.vtext(sx, y, line, story['head_em'], INK, 1.3)
            y += story['head_em'] + 4
        y += 4
        for line in cv.vwrap(story['body'], 11, w, 1.0):
            cv.vtext(sx, y, line, 11, GRAY)
            y += 13
    cv.hline(MARGIN, RIGHT, 488, INK, 1)

    # ---- five-story rows (middle + bottom) ----
    def five_row(y0, stories):
        xs = [MARGIN, 229, 422, 615, 808]
        for sx, story in zip(xs, stories):
            pic_box(cv, sx, y0, 180, 56)
            story['pic'](cv, sx + 1, y0 + 1, 178, 54)
            tag(cv, sx + 5, y0 + 5, story['tag'], em=9)
            caption_strip(cv, sx + 1, y0 + 56 - 13, 178, story['cap'])
            cv.vtext(sx, y0 + 60, story['kicker'], 9, RED, 1.3)
            y = y0 + 71
            for line in cv.vwrap(story['head'], 12, 180, 1.25):
                cv.vtext(sx, y, line, 12, INK, 1.25)
                y += 13
            y += 2
            for line in cv.vwrap(story['body'], 10, 180, 1.0):
                cv.vtext(sx, y, line, 10, GRAY)
                y += 11

    cv.vtext(MARGIN, 494, "MORE FROM THE DAY", 11, RED, 1.4)
    cv.hline(MARGIN + 148, RIGHT, 497, RED, 1)
    five_row(504, MID5)
    five_row(632, BOT5)
    cv.hline(MARGIN, RIGHT, 760, INK, 1)

    # ---- map + also list ----
    cv.vtext(MARGIN, 766, "WHERE IT HAPPENED", 11, RED, 1.4)
    cv.vtext(252, 766, "ALSO ON SATURDAY 21 NOVEMBER — 22 MORE STORIES",
             11, INK, 1.3)
    pic_box(cv, MARGIN, 778, 204, 102)
    draw_map(cv, MARGIN + 5, 783, cell=4)
    for i, line in enumerate(cv.vwrap(
            "EACH NUMBER MATCHES A STORY ON THIS PAGE. "
            "10 IS IN ORBIT ROUND MERCURY — OFF THE MAP.", 7, 192)):
        cv.vtext(MARGIN, 884 + i * 9, line, 7, GRAY)
    draw_list_col(cv, 252, 778, ALSO_LEFT, w=360, em=9)
    draw_list_col(cv, 624, 778, ALSO_RIGHT, w=360, em=9)

    # ---- legend ----
    cv.vtext(MARGIN, 910, LEGEND, 9, INK, 1.1)
    cv.hline(MARGIN, RIGHT, 922, INK, 1)

    # ---- date check ----
    cv.fill_rect(MARGIN, 928, 952, 56, (253, 238, 232))
    hatch_diag(cv, MARGIN + 2, 930, 952 - 4, 52, (245, 228, 220), step=14)
    cv.hline(MARGIN, RIGHT, 928, RED, 2)
    cv.hline(MARGIN, RIGHT, 983, RED, 2)
    cv.vline(MARGIN, 928, 983, RED, 2)
    cv.vline(RIGHT, 928, 983, RED, 2)
    cv.vtext(MARGIN + 8, 932, "DATE CHECK", 9, RED, 1.3)
    y = 943
    for line in cv.vwrap(DATE_CHECK, 9, 920):
        cv.vtext(MARGIN + 8, y, line, 9, INK)
        y += 10

    # ---- footer (exact wording required) ----
    cv.vtext_centred(W // 2, 990, FOOTER_1, 9, GRAY)
    cv.vtext_centred(W // 2, 1000, FOOTER_2, 8, GRAY)

    apply_grain(cv, 1, 0.45)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    try:
        os.makedirs(outdir, exist_ok=True)
    except OSError:
        outdir = "."
    path = os.path.join(outdir, "entry.png")
    cv = draw()
    png = write_png(path, cv)
    print("path:  ", path)
    print("sha256:", hashlib.sha256(png).hexdigest())
    print("bytes: ", len(png))
    print("size:  ", cv.w, "x", cv.h)


if __name__ == "__main__":
    main()
