"""The screen mock-ups of docs/DESIGN.md, drawn to its screen rules (section 3.1):

  pictures at rest, words on touch; one thing, full screen; big type only.

Three sizes of one 5 x 7 face and nothing smaller: XL (four times, the one number), L (twice, names and words) and
one S line (its drawn size) where a second fact is needed. No screen has more than three lines of text.
The pictures are drawn by hand to show the rules. They are not the instrument's renderer.
"""
import math
import random

from gfx import Scr, W, w5


def XL(s, x, y, t, v=1):
    return s.t5(x, y, t, v, 4)


def L(s, x, y, t, v=1):
    return s.t5(x, y, t, v, 2)


def Lc(s, xc, y, t, v=1):
    return s.t5(xc - w5(t, 2) // 2, y, t, v, 2)


def S(s, x, y, t, v=1):
    return s.t5(x, y, t, v, 1)


# ------------------------------------------------------------------ the parts of a rest view
def name_line(s, trk, text, y=24):
    """The one large line: the track's number in a box, then the name of what the wheel is on."""
    s.fill(0, y - 1, 14, 17)
    L(s, 2, y, str(trk), 0)
    L(s, 18, y, text)


def strip(s, n, cur, y=47, front=False):
    """Where you are in a row: a segment each, the current one thick. front: a square first (a preset's place)."""
    x0 = 8 if front else 0
    if front:
        s.fill(0, y - 1, 4, 3) if cur < 0 else s.hl(1, y, 2)
    seg = (W - x0 - (n - 1) * 2) // n
    for i in range(n):
        x = x0 + i * (seg + 2)
        s.hl(x, y, seg)
        if i == cur:
            s.hl(x, y - 1, seg)
            s.hl(x, y + 1, seg)


def steps_row(s, steps="n...n..%n.k.c.n.", playstep=6, y=53, held=None, last=16):
    """The 16 steps of the page shown, as marks: solid a note, dithered a chance, hollow a condition, a triangle a
    lock with no note, a tick over a note with locks. A line under each beat."""
    for i, c in enumerate(steps):
        x = i * 8
        if i % 4 == 0:
            s.hl(x + 1, y + 9, 5)
        if i >= last:
            continue
        if c == ".":
            s.set(x + 3, y + 4)
        elif c == "k":
            s.poly([(x + 1, y + 6), (x + 3, y + 2), (x + 5, y + 6), (x + 1, y + 6)])
        else:
            if c == "%":
                s.rect(x + 1, y + 2, 5, 5)
                s.dith(x + 1, y + 2, 5, 5)
            elif c == "c":
                s.rect(x + 1, y + 2, 5, 5)
                s.set(x + 3, y + 4)
            else:
                s.fill(x + 1, y + 2, 5, 5)
            if c == "L":
                s.hl(x + 2, y, 3)
        if i == playstep:
            s.inv(x, y + 1, 7, 7)
        if i == held:
            s.rect(x - 1, y - 1, 9, 10)


def corner(s, kind):
    """One symbol at the top right for a latched state."""
    x, y = 117, 1
    if kind == "rec":
        s.disc(x + 5, y + 5, 4)
    elif kind == "loop":
        s.rect(x, y + 2, 11, 7)
        s.poly([(x + 7, y), (x + 9, y + 2), (x + 7, y + 4)])
    elif kind == "map":
        s.rect(x, y, 11, 4)
        s.hl(x + 5, y + 4, 1)
        s.vl(x + 5, y + 4, 4)
        s.poly([(x + 3, y + 7), (x + 5, y + 9), (x + 7, y + 7)])


# ------------------------------------------------------------------ device icons, 18 x 18
def ic_rack(s, x, y):
    s.rect(x + 3, y + 2, 12, 14)
    s.rect(x + 6, y + 2, 6, 5)
    s.hl(x + 5, y + 10, 8)
    s.hl(x + 5, y + 12, 8)


def ic_macro(s, x, y):
    for r in range(2):
        for c in range(3):
            cx, cy = x + 3 + c * 6, y + 5 + r * 8
            s.circ(cx, cy, 2)
            s.set(cx, cy - 1)


def ic_pads(s, x, y):
    for r in range(3):
        for c in range(3):
            if (r, c) in ((2, 0), (1, 2)):
                s.fill(x + 2 + c * 5, y + 2 + r * 5, 4, 4)
            else:
                s.rect(x + 2 + c * 5, y + 2 + r * 5, 4, 4)


def ic_seq(s, x, y):
    for r in range(2):
        for c in range(4):
            bx, by = x + 1 + c * 4, y + 4 + r * 6
            if (r, c) in ((0, 0), (0, 2), (1, 1), (1, 2)):
                s.fill(bx, by, 3, 4)
            else:
                s.rect(bx, by, 3, 4)


def ic_synth(s, x, y):
    s.poly([(x + 1, y + 13), (x + 7, y + 4), (x + 7, y + 13), (x + 13, y + 4), (x + 13, y + 13), (x + 16, y + 9)])
    s.dots(x + 1, y + 15, 16, 2)


def ic_filter(s, x, y):
    s.poly([(x + 1, y + 7), (x + 8, y + 7), (x + 10, y + 4), (x + 12, y + 7), (x + 16, y + 14)])
    s.dots(x + 1, y + 15, 16, 2)


def ic_delay(s, x, y):
    for i, hgt in enumerate((12, 8, 5, 3)):
        s.fill(x + 2 + i * 4, y + 15 - hgt, 2, hgt)


def ic_mix(s, x, y):
    for i, k in enumerate((9, 4, 11)):
        cx = x + 3 + i * 6
        s.vl(cx, y + 2, 14)
        s.fill(cx - 2, y + k, 5, 3)


CHAIN = [ic_rack, ic_macro, ic_pads, ic_seq, ic_synth, ic_filter, ic_delay]   # MIX is past the right edge


# ------------------------------------------------------------------ pictograms, drawn from a value 0..1
def picto(s, kind, x, y, w, h, v):
    b = y + h - 1
    if kind == "lp":
        xc = x + int(v * (w - 6)) + 1
        s.poly([(x, y + 2), (xc, y + 2), (xc + 4, b)])
        s.dots(xc + 5, b, x + w - xc - 5, 2)
    elif kind == "peak":
        m = x + w // 2
        s.poly([(x, b - 1), (m - 4, b - 1), (m, b - 1 - int(v * (h - 2))), (m + 4, b - 1), (x + w - 1, b - 1)])
    elif kind == "env":
        a = int(v * 6)
        s.poly([(x, b), (x + 3 + a, y), (x + 9 + a, y + h // 2), (x + w - 6, y + h // 2), (x + w - 1, b)])
    elif kind == "bar":
        s.rect(x, y + 2, w, h - 4)
        s.fill(x + 1, y + 3, int(v * (w - 2)), h - 6)
    elif kind == "sine":
        n = 1 + v * 3
        s.poly([(x + i, y + h / 2 - 0.5 - math.sin(i / (w - 1.0) * 2 * math.pi * n) * (h / 2 - 1)) for i in range(w)])
    elif kind == "steps":
        for i in range(4):
            if i < 1 + int(v * 3.99):
                s.fill(x + i * 7, y + 1, 5, h - 2)
            else:
                s.rect(x + i * 7, y + 1, 5, h - 2)


FILTER = [("lp", 0.62), ("peak", 0.5), ("env", 0.4), ("steps", 0.5), ("bar", 0.2), ("sine", 0.25), ("sine", 0.7),
          ("bar", 1.0)]


# ------------------------------------------------------------------ rest views
CHAIN_NAMES = ["GLASS", "MACROS", "PADS", "SEQ", "DRIFT", "FILTER", "DELAY", "MIX"]


def belt(s, y, x1, phase):
    """The conveyor (section 3.5): a line the boxes ride on, with a tread under it that moves as the belt does."""
    s.hl(0, y, x1)
    for x in range(-6, x1, 6):
        xx = x + int(phase) % 6
        if 0 <= xx < x1 - 1:
            s.hl(xx, y + 2, 2)
    s.disc(2, y + 2, 1)
    s.disc(x1 - 3, y + 2, 1)


def scr_chain(sel=4, off=0):
    """The chain as a belt: the device under the wheel stays in the middle and the belt moves under it, in signal
    order, into the machine at the right, which is MIX. off: dots still to slide, on the way to sel."""
    s = Scr()
    for i, fn in enumerate(CHAIN):
        x = 55 + (i - sel) * 18 + off
        if 0 <= x and x + 17 <= 104:
            fn(s, x, 0)
    if off == 0 and sel < 7:
        s.inv(54, 0, 20, 18)
    belt(s, 18, 106, -(sel * 18) + off)
    # the machine the belt runs into: the mix strip
    s.rect(106, 0, 22, 22)
    s.vl(106, 3, 14, 0)
    ic_mix(s, 109, 2)
    if sel == 7:
        s.inv(107, 1, 20, 20)
    name_line(s, 3, CHAIN_NAMES[sel if off < 9 else sel - 1], 25)
    strip(s, 8, sel if off < 9 else sel - 1, 45)
    steps_row(s)
    return s


def _glyph(s, kind, x, y, n):
    """Pixel art for a box on a picker belt, drawn to fit n dots square."""
    if kind == "inkey":
        c = n // 3
        for r in range(3):
            for q in range(3):
                (s.fill if (r + q) % 3 == 2 else s.rect)(x + q * c, y + r * c, c - 1, c - 1)
    elif kind == "chrom":
        c = n // 4
        for r in range(4):
            for q in range(4):
                s.fill(x + q * c, y + r * c, c - 1, c - 1)
    elif kind == "keys":
        s.rect(x, y, n, n)
        c = n // 4
        for q in range(1, 4):
            s.vl(x + q * c, y, n)
        for q in (1, 3):
            s.fill(x + q * c - c // 3, y, 2 * (c // 3) + 1, n * 3 // 5)
    elif kind == "chords":
        for r, w in enumerate((n, n * 2 // 3, n, n // 2)):
            s.fill(x, y + r * (n // 4), w, max(1, n // 4 - 2))
    elif kind == "prog":
        c = n // 3
        for q in range(3):
            s.rect(x + q * c, y + n - (q + 1) * c, c - 1, c - 1)
        s.fill(x + c, y + n - 2 * c, c - 1, c - 1)


    elif kind == "scope":
        for i in range(n):
            s.set(x + i, y + n // 2 - round(math.sin(i / n * 2 * math.pi) * n / 3))
    elif kind == "level":
        w = n // 4
        for q, k in enumerate((0.5, 0.9, 0.3, 0.7)):
            s.fill(x + q * w, y + n - int(k * n), w - 1, int(k * n))
    elif kind == "pan":
        s.hl(x, y + n // 2, n)
        s.vl(x + n // 2, y + n // 2 - 1, 3)
        s.fill(x + n * 2 // 3, y + n // 2 - n // 4, max(2, n // 6), n // 2 + 1)
    elif kind in ("A", "B"):
        k = 2 if n >= 14 else 1
        s.t5(x + (n - 5 * k) // 2 + 1, y + (n - 7 * k) // 2, kind, 1, k)
    elif kind == "fx":
        w = n // 4
        for q, k in enumerate((0.9, 0.6, 0.4, 0.2)):
            s.fill(x + q * w, y + n - int(k * n), max(1, w - 2), int(k * n))


SESSION = [("scope", "SCOPES"), ("level", "LEVEL"), ("pan", "PAN"), ("A", "SEND A"), ("B", "SEND B"), ("fx", "A DELAY"),
           ("fx", "B REVERB"), ("fx", "M COMP")]
PICK = [("inkey", "IN KEY"), ("chrom", "CHROMATIC"), ("keys", "KEYBOARD"), ("chords", "CHORDS"), ("prog", "PROGRESS")]


def scr_belt(sel=2, off=0):
    """A picker belt, after EvilGenius: the kinds as boxes of pixel art on a conveyor, the chosen one large in the
    middle, its name large under the belt. Here the pad layouts of Shift + Step 8."""
    return _belt(PICK, sel, off)


def _belt(items, sel, off=0, machine=False):
    s = Scr()
    x1 = 106 if machine else 128
    for i, (kind, _) in enumerate(items):
        d = i - sel
        if d == 0 and off == 0:
            s.rect(50, 2, 28, 28)
            s.rect(51, 3, 26, 26)
            _glyph(s, kind, 55, 7, 18)
        else:
            x = 57 + d * 22 + (10 if d > 0 else -10 if d < 0 else 0) + off
            if 0 <= x and x + 14 <= x1 - 2:
                s.rect(x, 16, 14, 14)
                _glyph(s, kind, x + 3, 19, 8)
    belt(s, 30, x1, -(sel * 22) + off)
    if machine:                                   # OUT: the limiter and the way out, drawn as a speaker
        s.rect(106, 6, 22, 28)
        s.vl(106, 17, 12, 0)
        s.circ(117, 20, 7)
        s.circ(117, 20, 3)
        s.set(117, 20)
    Lc(s, 64, 37, items[sel][1])
    strip(s, len(items) + (1 if machine else 0), sel, 58)
    return s


def scr_sbelt(sel=3, off=0):
    """Session Mode's belt: the mixer's pages, then the buses' effects, into OUT."""
    return _belt(SESSION, sel, off, machine=True)


def scr_page(mod=0.0):
    """mod: where an LFO has the cutoff now, either side of the value set by hand (the fixed tick)."""
    s = Scr()
    for i, (kind, v) in enumerate(FILTER):
        live = min(1.0, max(0.0, v + mod)) if i == 0 else v
        picto(s, kind, (i % 4) * 32 + 3, 1 + (i // 4) * 11, 26, 9, live)
        if i == 0:
            s.vl(3 + int(v * 20) + 1, 0, 2)
    name_line(s, 3, "FILTER")
    strip(s, 6, 2, front=True)
    steps_row(s)
    return s


def scr_session():
    s = Scr()
    levels = (0.8, 0.7, 0.75, 0.5, 0.6, 0.85, 0.0, 0.4)
    meters = (0.6, 0.3, 0.7, 0.2, 0.0, 0.5, 0.0, 0.3)
    prog = (0.3, 0.3, 0.8, 0.55, None, 0.3, None, 0.1)
    for i in range(8):
        x = i * 16
        s.rect(x + 5, 1, 6, 24)
        mh = int(meters[i] * 22)
        s.fill(x + 6, 24 - mh, 4, mh)
        ly = 24 - int(levels[i] * 22)
        s.fill(x + 2, ly, 12, 2)
        if prog[i] is None:
            s.rect(x + 6, 30, 4, 4)
        else:
            s.circ(x + 8, 32, 4)
            a = prog[i] * 2 * math.pi - math.pi / 2
            s.line(x + 8, 32, x + 8 + 3 * math.cos(a), 32 + 3 * math.sin(a))
            s.line(x + 8, 32, x + 8, 29)
        S(s, x + 6, 40, str(i + 1))
        if i == 2:
            s.inv(x + 3, 39, 10, 9)
    for i in range(16):
        x = i * 8
        if i in (0, 1, 2, 3, 5, 8):
            s.rect(x + 1, 53, 6, 7)
        else:
            s.set(x + 3, 56)
        if i == 2:
            s.fill(x + 1, 53, 6, 7)
        if i == 3:
            s.dith(x + 1, 53, 6, 7)
    s.hl(0, 62, 31)
    return s


def scr_projects():
    s = Scr()
    used = {0, 1, 2, 3, 4, 8, 9, 10, 16, 17, 24, 25}
    for r in range(4):
        for c in range(8):
            x, y = 13 + c * 13, 1 + r * 9
            if r * 8 + c in used:
                s.fill(x, y, 11, 7)
            else:
                s.rect(x, y, 11, 7)
    s.rect(13 + 2 * 13 - 2, 1 + 9 - 2, 15, 11)
    Lc(s, 64, 42, "FEVER 07")
    return s


def scr_loop():
    s = Scr()
    npages, last = 4, 5
    for i in range(16):
        x, y = 1 + (i % 8) * 14, 1 + (i // 8) * 12
        if i < npages:
            s.rect(x, y, 12, 10)
            random.seed(i + 2)
            for k in range(last if i == npages - 1 else 16):
                if random.random() < 0.4:
                    s.fill(x + 2 + (k % 8), y + 2 + (k // 8) * 4, 1, 2)
            if i == 1:
                s.inv(x, y, 12, 10)
        else:
            s.dots(x, y, 12, 2)
            s.dots(x, y + 9, 12, 2)
            s.vdots(x, y, 10, 2)
            s.vdots(x + 11, y, 10, 2)
            if i == npages:
                s.hl(x + 4, y + 5, 5)
                s.vl(x + 6, y + 3, 5)
    L(s, 2, 27, "53 STEPS")
    corner(s, "loop")
    strip(s, 4, 1)
    steps_row(s, steps="n.n.n" + "." * 11, playstep=None, last=5)
    return s


def scr_sampling(phase=0.0):
    s = Scr()
    s.rect(2, 2, 54, 36)
    for cx in (16, 42):
        s.circ(cx, 17, 9)
        s.circ(cx, 17, 3)
        for k in range(3):
            a = phase + k * 2 * math.pi / 3
            s.line(cx + 3 * math.cos(a), 17 + 3 * math.sin(a), cx + 8 * math.cos(a), 17 + 8 * math.sin(a))
    s.hl(16, 28, 27)
    s.rect(20, 31, 18, 5)
    s.fill(21, 32, 4 + int(8 * abs(math.sin(phase))), 3)
    random.seed(11)
    shift = int(phase * 5)
    amps = [random.random() for _ in range(200)]
    for i in range(54):
        e = math.exp(-((i + shift) % 22) / 7.0)
        a = int(1 + amps[(i + shift) % 200] * 11 * e)
        s.vl(60 + i, 15 - a, 2 * a)
    corner(s, "rec")
    L(s, 60, 32, "3.2 S")
    S(s, 2, 50, "MIC   PAD 6")
    return s


def scr_chords():
    s = Scr()
    x = XL(s, 2, 2, "Dm")
    L(s, x, 2, "7")
    down = {(0, 1), (1, 1)}
    for r in range(2):
        for c in range(4):
            bx, by = 72 + c * 14, 4 + r * 12
            s.rect(bx, by, 12, 10)
            if (r, c) in down:
                s.fill(bx, by, 12, 10)
    S(s, 2, 36, "D3 F3 A3 C4")
    steps_row(s)
    return s


# ------------------------------------------------------------------ touch views
def scr_touch(v=0.62, txt="1.24", live=0.74):
    """An encoder touched or turned: its name, the value being set as the largest thing and holding still, a thin
    bar with a fixed tick for that value and a moving mark for where modulation has it now, which encoder it is."""
    s = Scr()
    L(s, 2, 2, "CUTOFF")
    XL(s, 2, 19, txt)
    S(s, 104, 40, "KHZ")
    s.dots(2, 51, 124, 2)
    s.vl(2 + int(v * 123), 49, 5)
    s.fill(1 + int(live * 123), 50, 3, 3)
    for i in range(8):
        if i == 0:
            s.fill(2 + i * 16, 56, 12, 6)
        else:
            s.rect(2 + i * 16, 56, 12, 6)
    return s


def scr_wheel():
    """The wheel touched: where you are, in words."""
    s = Scr()
    s.fill(0, 1, 14, 17)
    L(s, 2, 2, "3", 0)
    L(s, 18, 2, "BASS")
    L(s, 2, 21, "DRIFT")
    L(s, 2, 40, "FILTER 3/6")
    strip(s, 6, 2, y=60, front=True)
    return s


def scr_step():
    """A step held: its notes named large, what is set on it in one line."""
    s = Scr()
    L(s, 2, 2, "C3 E3 G3")
    S(s, 2, 24, "CHANCE 75  1:2  X2")
    S(s, 2, 34, "LOCKS 2")
    strip(s, 4, 0)
    steps_row(s, steps="n...L..%n.k.c.n.", playstep=None, held=4)
    return s


def scr_map(depth=0.4, txt="+40"):
    """A source key held on the map row and an encoder turned: the routing and its depth."""
    s = Scr()
    s.poly([(2 + i, 10 - math.sin(i / 35.0 * 4 * math.pi) * 7) for i in range(36)])
    S(s, 2, 22, "LFO 1")
    s.hl(8, 36, 20)
    s.poly([(24, 32), (28, 36), (24, 40)])
    L(s, 42, 2, "CUTOFF")
    XL(s, 42, 20, txt)
    s.rect(2, 54, 124, 7)
    s.vl(64, 52, 11)
    w = int(abs(depth) * 60)
    s.fill(64 if depth >= 0 else 64 - w, 56, w, 3)
    corner(s, "map")
    return s


def scr_toast():
    """A message: the whole screen for a second, two large lines."""
    s = Scr()
    Lc(s, 64, 14, "CLIP")
    Lc(s, 64, 34, "DUPLICATED")
    return s


# ------------------------------------------------------------------ held modifiers, lists
def _icons():
    """The sixteen step icons, each in a 12 x 12 box: (step number, draw function)."""
    def page(s, x, y):
        s.poly([(x + 2, y), (x + 7, y), (x + 10, y + 3), (x + 10, y + 11), (x + 2, y + 11), (x + 2, y)])

    def gear(s, x, y):
        s.poly([(x + 3, y), (x + 8, y), (x + 11, y + 5), (x + 8, y + 11), (x + 3, y + 11), (x, y + 5), (x + 3, y)])
        s.circ(x + 5.5, y + 5.5, 2)

    def nodes(s, x, y):
        s.line(x + 2, y + 9, x + 6, y + 3)
        s.line(x + 6, y + 3, x + 10, y + 9)
        for cx, cy in ((2, 9), (6, 3), (10, 9)):
            s.disc(x + cx, y + cy, 1.5)

    def cylinder(s, x, y):
        s.poly([(x + 2, y + 11), (x + 2, y + 2), (x + 4, y), (x + 7, y), (x + 9, y + 2), (x + 9, y + 11)])
        s.hl(x + 3, y + 3, 6)

    def clock(s, x, y):
        s.circ(x + 5.5, y + 5.5, 5)
        s.vl(x + 5, y + 2, 4)
        s.hl(x + 5, y + 6, 4)

    def metro(s, x, y):
        s.circ(x + 3, y + 6, 2.5)
        s.disc(x + 9, y + 6, 2.5)

    def wave(s, x, y):
        for o in (3, 8):
            s.poly([(x + i, y + o - math.sin(i / 11.0 * 2 * math.pi) * 2) for i in range(12)])

    def grid(s, x, y):
        s.rect(x + 1, y + 2, 10, 8)
        s.hl(x + 1, y + 5, 10)
        s.vl(x + 6, y + 5, 5)

    def note(s, x, y):
        s.disc(x + 4, y + 9, 2)
        s.vl(x + 6, y + 1, 8)
        s.hl(x + 6, y + 1, 4)
        s.hl(x + 6, y + 2, 4)

    def bars(s, x, y):
        s.disc(x + 3, y + 2, 1.5)
        for i, w in enumerate((8, 6, 4)):
            s.hl(x + 3, y + 5 + i * 3, w)

    def repeat(s, x, y):
        s.circ(x + 3, y + 6, 2.5)
        for i in range(3):
            s.vl(x + 7 + i * 2, y + 4 + (i == 1), 5 - 2 * (i == 1))

    def merge(s, x, y):
        for i in range(4):
            s.line(x, y + 1 + i * 3, x + 6, y + 4 + i + (i > 1))
        s.hl(x + 6, y + 5, 6)
        s.hl(x + 6, y + 6, 6)

    def star(s, x, y):
        s.poly([(x + 5, y), (x + 7, y + 4), (x + 11, y + 5), (x + 7, y + 7), (x + 5, y + 11), (x + 4, y + 7),
                (x, y + 5), (x + 4, y + 4), (x + 5, y)])

    def newclip(s, x, y):
        s.hl(x, y + 2, 5)
        s.vl(x + 2, y, 5)
        s.rect(x + 4, y + 6, 8, 6)

    def double(s, x, y):
        s.rect(x + 3, y, 8, 6)
        s.rect(x, y + 4, 8, 7)
        s.fill(x + 1, y + 5, 6, 5, 0)

    def quant(s, x, y):
        s.vl(x + 2, y, 12)
        s.rect(x + 5, y + 2, 4, 3)
        s.rect(x + 5, y + 7, 6, 3)

    return [page, gear, nodes, cylinder, clock, metro, wave, grid, note, bars, repeat, merge, star, newclip, double,
            quant]


def scr_shift():
    """Shift held: the sixteen step icons, large, as the steps lie. No words until one is pressed."""
    s = Scr()
    for i, fn in enumerate(_icons()):
        fn(s, 2 + (i % 8) * 16, 10 + (i // 8) * 30)
    for b in range(4):
        s.hl(b * 32 + 2, 27, 12)
        s.hl(b * 32 + 2, 57, 12)
    return s


def scr_copy():
    """Copy held: its picture and its one word."""
    s = Scr()
    s.rect(8, 14, 22, 30)
    s.rect(16, 22, 22, 30)
    s.fill(17, 23, 20, 28, 0)
    L(s, 52, 26, "COPY")
    return s


def scr_browser():
    """A list: the item under the wheel large, its neighbours small. A long name slides."""
    s = Scr()
    S(s, 4, 3, "ACID LINE")
    L(s, 4, 17, "DARK POLY")
    s.inv(0, 15, 122, 18)
    S(s, 4, 38, "GLASS KEYS")
    s.vl(125, 2, 44)
    s.fill(124, 15, 3, 18)
    s.dots(0, 50, 128, 2)
    S(s, 4, 54, "SYNTHS / BASS")
    return s


def scr_sheet():
    """A press on a front item: the one sheet for saving and loading."""
    s = Scr()
    x = L(s, 2, 2, "DARK POLY")
    s.fill(x, 3, 4, 4)
    L(s, 6, 22, "LOAD")
    s.inv(0, 20, 122, 18)
    L(s, 6, 42, "SAVE")
    s.vl(125, 20, 42)
    s.fill(124, 20, 3, 16)
    return s


# ------------------------------------------------------------------ views: a scene, the scopes, the tracks
def _ellipse(s, cx, cy, rx, ry, dotted=False):
    n = max(16, int(rx * 4))
    pts = [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]
    if dotted:
        for p in pts[::2]:
            s.set(p[0], p[1])
    else:
        s.poly(pts)


def scr_scene(t=0.0):
    """A scene, after h1's: a pond at night. Each note is a fish that jumps where its pitch puts it; its ripples
    spread and fade; a macro raises the moon."""
    s = Scr()
    random.seed(5)
    for _ in range(14):
        s.set(random.randrange(128), random.randrange(22))
    s.circ(104, 12 - 2 * math.sin(t), 8)
    s.circ(101, 10 - 2 * math.sin(t), 2)
    s.dots(0, 30, 128, 3)
    for cx, cy, r0 in ((26, 46, 0.0), (70, 40, 0.5), (108, 52, 0.25)):
        for k in range(3):
            r = ((t * 0.5 + r0 + k / 3.0) % 1.0) * 16 + 2
            _ellipse(s, cx, cy, r, r * 0.35, dotted=r > 10)
    for cx, cy in ((48, 54), (88, 46), (12, 38)):
        _ellipse(s, cx, cy, 6, 2.4)
        s.line(cx, cy, cx + 5, cy - 1)
    a = (t * 0.5) % 1.0
    fx, fy = 60 + a * 22, 40 - math.sin(a * math.pi) * 22
    s.poly([(fx - 5, fy), (fx, fy - 3), (fx + 5, fy), (fx, fy + 3), (fx - 5, fy)])
    s.poly([(fx - 5, fy), (fx - 9, fy - 3), (fx - 9, fy + 3), (fx - 5, fy)])
    s.set(fx + 2, fy - 1)
    for x in (2, 5, 122, 125):
        s.vl(x, 34 - (x % 3) * 3, 30)
    return s


def scr_main(t=0.0, fb=0.7):
    """A device's main page: its theme, full screen. A sketch for a delay: a canyon and a ball. Time is how far
    apart it lands, feedback how many times it bounces, the filter on the repeats the fog it bounces into."""
    s = Scr()
    s.poly([(0, 14), (10, 6), (20, 12), (30, 3), (42, 13), (54, 7), (66, 14)])
    s.poly([(74, 13), (86, 5), (98, 12), (110, 4), (127, 12)])
    s.vl(66, 14, 26)
    s.vl(74, 13, 27)
    s.dots(0, 40, 128, 2)
    x, h = 6.0, 30.0
    hops = []
    while h > 2 and x < 124:
        w = 22 if not hops else 22 * 0.92 ** len(hops)
        hops.append((x, w, h))
        x += w
        h *= fb
    for k, (x0, w, hh) in enumerate(hops):
        pts = [(x0 + w * i / 12.0, 39 - hh * math.sin(math.pi * i / 12.0)) for i in range(13)]
        if k >= 3:
            for p in pts:
                s.set(p[0], p[1])
        else:
            s.poly(pts)
    k = int(t) % max(1, len(hops))
    x0, w, hh = hops[k]
    a = t % 1.0
    s.disc(x0 + w * a, 39 - hh * math.sin(math.pi * a) - 2, 2)
    for i in range(3):
        s.dith(96 + i * 10, 20 + i * 3, 9, 20 - i * 3, 3)
    strip(s, 2, 0, front=True)
    steps_row(s)
    return s


def _wave(kind, i, n, ph=0.0):
    x = i / float(n)
    if kind == "rich":
        return 0.6 * math.sin(2 * math.pi * (2 * x) + ph) + 0.3 * math.sin(2 * math.pi * 6 * x + 2 * ph) \
            + 0.15 * math.sin(2 * math.pi * 11 * x)
    if kind == "sine":
        return math.sin(2 * math.pi * 2 * x + ph)
    if kind == "saw":
        return 2 * ((2 * x + ph) % 1.0) - 1
    if kind == "square":
        return 1.0 if (3 * x + ph) % 1.0 < 0.5 else -1.0
    if kind == "pluck":
        return math.sin(2 * math.pi * 5 * x) * math.exp(-3 * x)
    if kind == "noise":
        return random.uniform(-1, 1) * math.exp(-4 * ((x * 2) % 1.0))
    return 0.0


def scr_scope(ph=0.0):
    """Scope: the track's sound as one waveform, held still on its pitch."""
    s = Scr()
    s.dots(0, 32, 128, 4)
    s.poly([(i, 32 - _wave("rich", i, 127, ph) * 26) for i in range(128)])
    return s


def scr_scope8():
    """Scope 8: all eight tracks, two rows of four as the encoders lie. Track 3 selected, 5 silent, 7 muted."""
    s = Scr()
    kinds = ["noise", "saw", "rich", "pluck", "flat", "square", "sine", "sine"]
    random.seed(9)
    for t, kind in enumerate(kinds):
        x0, y0 = (t % 4) * 32, (t // 4) * 32
        pts = [(x0 + 2 + i, y0 + 16 - _wave(kind, i, 27) * 12) for i in range(28)]
        if t == 6:
            for p in pts[::2]:
                s.set(p[0], p[1])
        else:
            s.poly(pts)
        if t == 2:
            s.rect(x0, y0, 32, 32)
    return s


def scr_tracks():
    """Tracks: the four tracks of the bank, a row each, with its own page and playhead. Track 3 selected."""
    s = Scr()
    rows = ["n...n...n..n.n..", "..n...n...n...%.", "n...L..%n.k.c.n.", "n.nnn.n.n.nnn.c."]
    heads = [6, 6, 6, 2]
    for r, steps in enumerate(rows):
        y = r * 16
        if r == 2:
            s.fill(0, y, 13, 15)
        L(s, 1, y + 1, str(r + 1), 0 if r == 2 else 1)
        for i, c in enumerate(steps):
            x = 16 + i * 7
            if c == ".":
                s.set(x + 2, y + 7)
            elif c == "k":
                s.poly([(x, y + 9), (x + 2, y + 5), (x + 4, y + 9), (x, y + 9)])
            elif c in "%c":
                s.rect(x, y + 5, 5, 5)
                if c == "%":
                    s.dith(x, y + 5, 5, 5)
            else:
                s.fill(x, y + 5, 5, 5)
            if i == heads[r]:
                s.inv(x - 1, y + 3, 7, 9)
        if r:
            s.dots(16, y - 1, 112, 4)
    return s


SCREENS = [
    ("view-scene", "View: a scene", scr_scene,
     "A track's rest picture can be its instrument's scene, after the h1 firmware: here a pond at night. Each note "
     "is a fish that jumps where its pitch puts it and leaves ripples; a macro raises the moon. No words."),
    ("device-main", "A device's main page: its theme", scr_main,
     "The first page of a device after its name: its own weird world, full screen, with its eight key parameters "
     "on the encoders. A sketch for a delay: a canyon and a ball. Time is how far apart it lands, feedback how "
     "many times it bounces, the filter on the repeats the fog it bounces into. No words: a touch names a "
     "parameter. The strip: the device's name, then this page, then its plain pages."),
    ("view-scope", "View: Scope", scr_scope,
     "The track's sound as one waveform across the screen, held still on its pitch. Inside a device it is the "
     "sound as it leaves that device."),
    ("view-scope8", "View: Scope 8", scr_scope8,
     "All eight tracks' waveforms, two rows of four as the encoders lie: the selected track's framed, a muted "
     "one dotted, a silent one flat."),
    ("view-tracks", "View: Tracks", scr_tracks,
     "The four tracks of the bank, a row each in the order of the track buttons, each its own page and playhead. "
     "The track's number large at the left, the selected one boxed."),
    ("note-device-view", "The chain at rest", scr_chain,
     "Home in Note Mode: a picture and one large line. The chain is a belt: the devices ride it in signal order "
     "into the machine at the right, which is MIX, and the one under the wheel stays in the middle while the belt "
     "moves. The track's number boxed, the device's name. The strip: where the wheel is along the chain. The "
     "steps row: solid a note, dithered a chance, hollow a condition, a triangle a lock with no note. No small "
     "text: a touch tells the rest."),
    ("belt-pick", "A picker belt", scr_belt,
     "Where the wheel chooses one of several kinds of thing, the kinds ride a conveyor as boxes of pixel art, after "
     "EvilGenius: the chosen one large in the middle, its name large under the belt. Here the pad layouts of "
     "Shift + Step 8. A turn moves the belt a box; a press takes the one in the middle."),
    ("belt-session", "Session Mode's belt", scr_sbelt,
     "The wheel touched or turned in Session Mode: the mixer's pages (SCOPES, LEVEL, PAN, SEND A, SEND B), then "
     "each bus's effects, riding into OUT at the right. A page is live as it reaches the middle; an effect is "
     "entered with a press. Let go, and the screen goes back to the meters."),
    ("param-page", "A device page at rest", scr_page,
     "Inside a device: its page as eight pictograms, two rows of four as the encoders lie, each drawing its own "
     "value, with no words. The page's name large. The strip: a square for the device's preset, then a segment a "
     "page."),
    ("param-touch", "An encoder touched or turned", scr_touch,
     "The touched parameter takes the screen: its name, its value as the largest thing, its unit, and eight marks "
     "showing which encoder it is. It stays for a second after the encoder is let go."),
    ("wheel-touch", "The wheel touched", scr_wheel,
     "Where you are, in words: track, device, page and its place. With Speech on Jog this is also said."),
    ("shift-map", "Shift held", scr_shift,
     "The sixteen step icons drawn large, two rows of eight as the steps lie, a line under each beat. Pressing one "
     "shows its name large."),
    ("hint-copy", "Copy held", scr_copy,
     "A held modifier is its picture and its one word. The lights on the surface are the list of what it can act "
     "on; the screen does not spell it out."),
    ("projects", "Projects", scr_projects,
     "Shift + Step 1: the 32 pads as a grid, the selected slot framed, its name large."),
    ("browser", "A list", scr_browser,
     "The item under the wheel large, its neighbours small above and below, where the list is at the bottom."),
    ("step-held", "A step held", scr_step,
     "The step's notes named large; one smaller line for what is set on it. Turning a control shows that value "
     "alone, as an encoder does. The held step is framed in the steps row."),
    ("loop-pages", "Loop Mode", scr_loop,
     "The clip's pages as boxes, the shown one inverted, a + after the last; the length large. The corner symbol "
     "says Loop Mode is latched. The steps row is the last page: five steps, the rest dark."),
    ("session", "Session Mode", scr_session,
     "Eight tracks, each under its encoder and over its column of pads: meter, the level mark, the playing clip as "
     "a ring, the track's number, the selected one inverted. Bottom: the sixteen scenes, four underlined."),
    ("preset-sheet", "Saving and loading: the sheet", scr_sheet,
     "A press on a rack's or a device's front item: the preset's name with a mark because it has changed, and the "
     "sheet in large type: Load, Save, then Save As, Init and Revert below."),
    ("map-row", "The map row: a source held, an encoder turned", scr_map,
     "LFO 1's key held and the Cutoff encoder turned: the source as a picture, the parameter's name, the depth as "
     "the largest thing, a bar either side of zero. The corner symbol says the map row is on."),
    ("chords", "PADS: the Chords layout", scr_chords,
     "The chord is the one subject: its name as the largest thing, the chord keys that are down as filled boxes, "
     "its notes in one smaller line."),
    ("sampling", "Sampling Mode", scr_sampling,
     "The tape face: reels turn while recording, the waveform runs out to the right, the time large. The corner "
     "symbol is the record dot."),
    ("toast", "A message", scr_toast,
     "A message takes the whole screen for a second, in at most two large lines."),
]

# animations for the board: key -> [(screen, milliseconds)]
ANIM = {
    # a turn of the wheel: the belt slides a box, then rests
    "note-device-view": ([(scr_chain(4, o), 45) for o in (18, 13, 8, 4, 1)] + [(scr_chain(4, 0), 1400)]
                         + [(scr_chain(5, o), 45) for o in (18, 13, 8, 4, 1)] + [(scr_chain(5, 0), 1400)]
                         + [(scr_chain(4, o), 45) for o in (-18, -13, -8, -4, -1)]),
    "belt-session": ([(scr_sbelt(3, 0), 1200)] + [(scr_sbelt(4, o), 45) for o in (22, 15, 9, 4, 1)]
                     + [(scr_sbelt(4, 0), 1200)] + [(scr_sbelt(3, o), 45) for o in (-22, -15, -9, -4, -1)]),
    "belt-pick": ([(scr_belt(2, 0), 1200)] + [(scr_belt(3, o), 45) for o in (22, 15, 9, 4, 1)]
                  + [(scr_belt(3, 0), 1200)] + [(scr_belt(2, o), 45) for o in (-22, -15, -9, -4, -1)]),
    "sampling": [(scr_sampling(i * 0.35), 120) for i in range(6)],
    # the number is the value set by hand and holds still; only the mark for the modulated value moves
    "param-touch": [(scr_touch(0.62, "1.24", 0.62 + 0.14 * math.sin(i * math.pi / 4)), 120) for i in range(8)],
    # at rest the cutoff's pictogram moves as the LFO sweeps it, against the fixed tick of the value set by hand
    "param-page": [(scr_page(0.16 * math.sin(i * math.pi / 4)), 120) for i in range(8)],
    "view-scene": [(scr_scene(i * 0.33), 140) for i in range(6)],
    "device-main": [(scr_main(i * 0.25), 110) for i in range(12)],
    "view-scope": [(scr_scope(i * 0.5), 140) for i in range(6)],
    "map-row": [(scr_map(d, t), 140) for d, t in ((0.1, "+10"), (0.2, "+20"), (0.3, "+30"), (0.4, "+40"))],
}
