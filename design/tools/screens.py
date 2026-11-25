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
BOX_W = 36


def name_line(s, trk, text, y=24):
    """The one large line. The box at its left is one width whatever it holds: the track's number, or S and a
    step's number while that step is held. Beside it the name of what the wheel is on; a touched encoder's name,
    then its value a moment later or as it turns; a held step's notes."""
    box = str(trk)
    s.fill(0, y - 1, BOX_W, 17)
    L(s, (BOX_W - (len(box) * 12 - 2)) // 2, y, box, 0)
    L(s, BOX_W + 4, y, text)


def strip(s, n, cur, y=1, front=False, boxes=False):
    """The page marks, along the top of the screen: where you are in a row, a segment each, the current one thick.
    front: a square first (a preset's place). boxes: small boxes, not segments: the marks of a belt, a box a kind."""
    if boxes:
        seg = (W - (n - 1) * 3) // n
        for i in range(n):
            x = i * (seg + 3)
            if i == cur:
                s.fill(x, y - 1, seg, 4)
            else:
                s.rect(x, y - 1, seg, 4)
        return
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


def ic_arp(s, x, y):
    """A MIDI effect: an arp, notes climbing in steps."""
    for i in range(4):
        s.fill(x + 1 + i * 4, y + 13 - i * 3, 3, 3)
    s.hl(x + 1, y + 16, 16)


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


CHAIN = [ic_rack, ic_macro, ic_seq, ic_arp, ic_synth, ic_filter, ic_delay, ic_mix]   # MIX: the last box


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
CHAIN_NAMES = ["GLASS", "MACROS", "SEQ", "ARP", "DRIFT", "FILTER", "DELAY", "MIX"]   # PADS: Shift + Step 8


def belt(s, y, x1, phase):
    """The conveyor (section 3.5): a line the boxes ride on, with a tread under it that moves as the belt does."""
    s.hl(0, y, x1)
    for x in range(-6, x1, 6):
        xx = x + int(phase) % 6
        if 0 <= xx < x1 - 1:
            s.hl(xx, y + 2, 2)
    s.disc(2, y + 2, 1)
    s.disc(x1 - 3, y + 2, 1)


def big(s, fn, x, y):
    """An icon at twice its size: the chosen box of a belt."""
    tmp = Scr()
    fn(tmp, 0, 0)
    for j in range(18):
        for i in range(18):
            if tmp.get(i, j):
                s.fill(x + 2 * i, y + 2 * j, 2, 2)


def scr_chain(sel=4, off=0):
    """The chain's belt, which shows only while the wheel turns and takes the whole screen: the device under the
    wheel at twice the size in the middle, its neighbours small beside it; MIX is the last box and rides the belt
    as the others do; the name large under the belt. off: dots still to slide, on the way to sel."""
    s = Scr()
    for i, fn in enumerate(CHAIN):
        d = i - sel
        if off == 0 and d == 0:
            big(s, fn, 46, 1)
            s.inv(45, 0, 38, 38)
            continue
        x = 55 + d * 22 + off if off else 55 + d * 22 + (10 if d > 0 else -10)
        if 0 <= x and x + 17 <= 126:
            fn(s, x, 20)
    belt(s, 38, 128, -(sel * 22) + off)
    Lc(s, 64, 47, CHAIN_NAMES[sel if abs(off) < 11 else sel - (1 if off > 0 else -1)])
    return s


MACROS = [("bar", 0.7), ("lp", 0.45), ("sine", 0.3), ("env", 0.6), ("steps", 0.75), ("bar", 0.35), ("peak", 0.8),
          ("bar", 0.9)]


def picto_big(s, kind, x, y, w, h, v):
    """A pictogram drawn large, its lines two dots thick: the same picture, big."""
    tmp = Scr()
    picto(tmp, kind, 0, 2, w, h, v)
    for j in range(h + 3):
        for i in range(w + 1):
            if tmp.get(i, j):
                s.fill(x + i, y + j - 2, 2, 2)


def scr_chain_rest(sel=1, t=0.0):
    """The chain at rest: no belt, no marks, no name. The main page of the device under the wheel as eight big
    boxes, one a knob, down to the steps row. Here the wheel is on MACROS, where home puts it."""
    s = Scr()
    for i, (kind, v) in enumerate(FILTER if sel == 5 else MACROS[::-1] if sel == 4 else MACROS):
        live = min(1.0, max(0.0, v + 0.12 * math.sin(t))) if i == 1 else v
        x, y = (i % 4) * 32, (i // 4) * 26
        picto_big(s, kind, x + 3, y + 3, 25, 18, live)
    steps_row(s)
    return s


def scr_card(kind="lp", v=0.62, name="CUTOFF", num="1.24", unit="KHZ", enc=0):
    """A knob touched or turned at the chain: the whole screen, its name, its value large, its pictogram large."""
    s = Scr()
    L(s, 2, 2, name)
    k = 4
    while k > 2 and len(num) * 6 * k - k > 76:
        k -= 1
    s.t5(2, 19 if k == 4 else 24, num, 1, k)
    picto_big(s, kind, 80, 19, 44, 19, v)
    S(s, 126 - len(unit) * 6 + 1, 41, unit)
    s.dots(2, 57, 124, 2)
    s.vl(2 + int(v * 123), 55, 5)
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


    elif kind == "out":                           # the limiter and the way out, drawn as a speaker
        s.circ(x + n // 2, y + n // 2, n // 2 - 1)
        if n > 10:
            s.circ(x + n // 2, y + n // 2, n // 5)
        s.set(x + n // 2, y + n // 2)
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
    elif kind == "clip":                          # the clips: a grid, one playing
        c = n // 4
        for r in range(4):
            for q in range(4):
                if (r, q) == (1, 2):
                    s.fill(x + q * c, y + r * c, c - 1, c - 1)
                else:
                    s.set(x + q * c + c // 2, y + r * c + c // 2)
    elif kind == "track":                         # one track's strip: a fader and a knob
        s.vl(x + n // 4, y, n)
        s.fill(x + n // 4 - 2, y + n // 2, 5, 3)
        s.circ(x + 3 * n // 4, y + n // 4, max(2, n // 6))
        s.vl(x + 3 * n // 4, y + n // 2, n // 2)
    elif kind in ("1", "2", "3"):                 # a send: an arrow out, and its number in dots
        s.hl(x, y + n // 3, n - 1)
        s.line(x + n - 5, y + n // 3 - 3, x + n - 1, y + n // 3)
        s.line(x + n - 5, y + n // 3 + 3, x + n - 1, y + n // 3)
        for i in range(int(kind)):
            s.fill(x + i * (n // 3), y + n - 3, 3, 3)
    elif kind in ("A", "B"):
        k = 2 if n >= 14 else 1
        s.t5(x + (n - 5 * k) // 2 + 1, y + (n - 7 * k) // 2, kind, 1, k)
    elif kind == "fx":
        w = n // 4
        for q, k in enumerate((0.9, 0.6, 0.4, 0.2)):
            s.fill(x + q * w, y + n - int(k * n), max(1, w - 2), int(k * n))


SESSION = [("clip", "CLIP"), ("track", "TRACK"), ("level", "LEVEL"), ("pan", "PAN"), ("1", "SEND 1"), ("2", "SEND 2"),
           ("3", "SEND 3")]
PICK = [("inkey", "IN KEY"), ("chrom", "CHROMATIC"), ("keys", "KEYBOARD"), ("chords", "CHORDS"), ("prog", "PROGRESS")]


def scr_belt(sel=2, off=0):
    """A picker belt, after EvilGenius: the kinds as boxes of pixel art on a conveyor, the chosen one large in the
    middle, its name large under the belt. Here the pad layouts of Shift + Step 8."""
    return _belt(PICK, sel, off)


def _belt(items, sel, off=0):
    s = Scr()
    x1 = 128
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
    Lc(s, 64, 37, items[sel][1])
    strip(s, len(items), sel, 58)
    return s


def scr_sbelt(sel=3, off=0):
    """Session Mode's belt: CLIP, TRACK, LEVEL, PAN and the three sends."""
    return _belt(SESSION, sel, off)


def scr_sclip(prog=0.4, blink=True):
    """CLIP, Session Mode's home: RemoteFM4Move's session view, as core/ui.c draws it."""
    s = Scr()
    used = {(0, 0), (1, 0), (1, 1), (1, 2), (2, 0), (3, 0), (3, 1), (5, 0), (6, 2)}
    playing = {(0, 0), (1, 0), (3, 1), (5, 0)}
    queued = {(1, 1)}
    for c in range(8):
        x = c * 16 + 1
        if c == 1:
            s.fill(x, 0, 14, 2)
        elif c == 4:
            s.dots(x, 1, 14, 2)
    for r in range(4):
        for c in range(8):
            x, y = c * 16 + 1, 4 + r * 15
            if (c, r) in playing:
                s.fill(x, y, 14, 13)
                for k in range(4):
                    s.vl(x + 5 + k, y + 3 + k, 7 - 2 * k, 0)
            elif (c, r) in queued and blink:
                s.rect(x, y, 14, 13)
                s.rect(x + 2, y + 2, 10, 9)
            elif (c, r) in used or (c, r) in queued:
                s.rect(x, y, 14, 13)
            else:
                s.fill(x + 6, y + 5, 2, 2)
    return s


def env_shape(s, x, y, w, h, a, d, su, r):
    """An envelope in a box of w x h dots, as core/ui.c draws it: the times by their root, two dots thick."""
    hold, seg, base = w // 6, (w - 6 - w // 6) // 3, y + h - 1
    x1 = x + 2 + int(math.sqrt(a) * seg)
    x2 = x1 + 2 + int(math.sqrt(d) * seg)
    x3 = x2 + hold
    x4 = x3 + 2 + int(math.sqrt(r) * seg)
    ys = min(base, y + int((1 - su) * (h - 1)) + 1)
    for k in range(2):
        s.poly([(x, base - k), (x1, y - k + 1), (x2, ys - k), (x3, ys - k), (x4, base - k)])
    s.dots(x, base + 2, w, 3)


def filter_bars(s, x, y, w, h, cut, res, env):
    """A low-pass filter as spaced bars over ten octaves; a mark above where the envelope takes the corner."""
    n, q = w // 3, 0.7 + res * 9.0
    for k in range(n):
        r = 2.0 ** ((k / (n - 1.0) - cut) * 10.0)
        m = 1.0 / math.sqrt((1 - r * r) ** 2 + (r / q) ** 2)
        db = max(-30.0, min(18.0, 20 * math.log10(max(m, 0.0001))))
        bh = 1 + int((db + 30) / 48 * (h - 1))
        s.fill(x + k * 3, y + h - bh, 2, bh)
    if abs(env) > 0.02:
        c2 = max(0.0, min(1.0, cut + env * 0.5))
        s.fill(x + int(c2 * (n - 1)) * 3, y - 3, 2, 2)


def scr_page(mod=0.0, touched=None, txt="FILTER"):
    """Inside a device, a page that is one thing drawn as that thing: the synth's FILTER page as one filter beside
    one envelope. mod: where an LFO has the cutoff now. touched: 'f' or 'e', the half a touched knob belongs to,
    underlined. No steps row inside a device: the name line sits at the bottom."""
    s = Scr()
    filter_bars(s, 1, 10, 62, 33, 0.5 + mod, 0.55, 0.3)
    env_shape(s, 68, 9, 58, 32, 0.05, 0.35, 0.45, 0.4)
    if touched == "f":
        s.hl(1, 45, 62)
    elif touched == "e":
        s.hl(68, 45, 58)
    name_line(s, 3, txt, 48)
    strip(s, 6, 2, front=True)
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
    strip(s, 4, 1, y=47)
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
def scr_touch(v=0.62, txt="1.24", live=0.74, turned=True):
    """An encoder touched or turned inside a device: the page stays, the half the knob belongs to is underlined,
    and the name line gives its name, then its value a moment later or as it turns. Nothing covers the page."""
    return scr_page(v - 0.5, touched="f", txt=txt + "KHZ" if turned else "CUTOFF")


def scr_wheel():
    """The wheel touched: where you are, in words."""
    s = Scr()
    s.fill(0, 1, 14, 17)
    L(s, 2, 2, "3", 0)
    L(s, 18, 2, "BASS")
    L(s, 2, 21, "DRIFT")
    L(s, 2, 40, "FILTER 3/6")
    strip(s, 6, 2, y=60, front=True)       # with words on the screen the marks go to the bottom
    return s


def scr_step():
    """A step held: the page stays, now showing that step's values; the box says S and the step's number in
    place of the track's, at the same width, and the line names the step's notes."""
    s = Scr()
    for i, (kind, pv) in enumerate(FILTER):
        picto(s, kind, (i % 4) * 32 + 3, 7 + (i // 4) * 11, 26, 9, pv)
    name_line(s, "S5", "C MAJ", 30)
    strip(s, 6, 2, front=True)
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
    """Shift held: the view stays, with S in the corner. The step icons are printed on the surface and light there."""
    s = scr_chain_rest()
    s.fill(115, 31, 13, 15, 0)
    s.fill(117, 33, 11, 11)
    S(s, 120, 35, "S", 0)
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
    ("note-device-view", "The chain: at rest, then the wheel turned", scr_chain_rest,
     "Home in Note Mode. At rest there is no belt, no marks and no name: the main page as eight big boxes, one "
     "a knob, down to the steps row: the main page of the device under the wheel, which is what the encoders "
     "turn. Here the wheel is on MACROS. Turn the wheel and the belt comes up: the devices ride it in signal order, MIX the last of them, "
     "and the one under the wheel stays in the middle. A second after the last click the "
     "belt is gone again. The steps row: solid a note, dithered a chance, hollow a condition, a triangle a lock "
     "with no note."),
    ("chain-belt", "The chain's belt, while the wheel turns", scr_chain,
     "What a turn of the wheel shows at the chain, and only while it turns: the track's devices as boxes on a "
     "conveyor, the one under the wheel in the middle, its name large. MIX is the last box and rides the belt as "
     "the others do."),
    ("belt-pick", "A picker belt", scr_belt,
     "Where the wheel chooses one of several kinds of thing, the kinds ride a conveyor as boxes of pixel art, after "
     "EvilGenius: the chosen one large in the middle, its name large under the belt. Here the pad layouts of "
     "Shift + Step 8. A turn moves the belt a box; a press takes the one in the middle."),
    ("belt-session", "Session Mode's belt", scr_sbelt,
     "The wheel turned in Session Mode: CLIP, TRACK, LEVEL, PAN, SEND 1, SEND 2, SEND 3. A page is live as it "
     "reaches the middle. Let go, and the screen is that page again."),
    ("session-clip", "Session Mode: CLIP", scr_sclip,
     "Home in Session Mode: RemoteFM4Move's session view. The eight tracks across, the four scenes on the pads "
     "down; a bar over the selected track, dashed over a muted one; playing filled with a black play mark; queued "
     "doubled and blinking; a clip outlined; an empty slot a dot. The pads launch."),
    ("param-page", "A device page at rest", scr_page,
     "Inside a device: a page that is one thing is drawn as that thing, large, and moves as its knobs turn. The "
     "synth's FILTER page is one filter as spaced bars, the dot above them where the envelope takes the corner, "
     "beside its envelope. No steps row; the page's name at the bottom. The strip: a square for the device's "
     "preset, then a segment a page. A page of unrelated values is eight pictograms."),
    ("chain-card", "A knob touched at the chain", scr_card,
     "At the chain, or on a page of pictograms, a touched or turned knob takes the whole screen: its name, its "
     "value as the largest thing, its pictogram drawn large with the unit under it, the bar of where it stands, "
     "and which of the eight it is. A second after it is let go the boxes are back."),
    ("param-touch", "An encoder touched or turned", scr_touch,
     "In a rest view the page stays on the screen and the name line gives the touched encoder's name, then its "
     "value 0.6 s into the touch, or at once as it turns, so the picture is seen to change. On a page of pictograms the touched one is "
     "inverted; on a page drawn as one thing, a line under the half the knob belongs to. A second after the "
     "encoder is let go the line is the page's name again."),
    ("shift-map", "Shift held", scr_shift,
     "Nothing of its own: the view stays, with S in the corner. The step icons are printed on the surface and "
     "light there. Pressing one shows its name large."),
    ("hint-copy", "Copy held", scr_copy,
     "A held modifier is its picture and its one word. The lights on the surface are the list of what it can act "
     "on; the screen does not spell it out."),
    ("projects", "Projects", scr_projects,
     "Shift + Step 1: the 32 pads as a grid, the selected slot framed, its name large."),
    ("browser", "A list", scr_browser,
     "The item under the wheel large, its neighbours small above and below, where the list is at the bottom."),
    ("step-held", "A step held", scr_step,
     "The page stays and shows the held step's values. The box at the left of the name line says S and the "
     "step's number in place of the track's, at the same width; the line names its notes, or the value being "
     "set. The held step is framed in the steps row."),
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
    # at rest: the marks and the macros. A turn: the belt comes up, slides a box, stays a second, and goes
    "note-device-view": ([(scr_chain_rest(4, i * 0.8), 180) for i in range(8)]
                         + [(scr_chain(5, o), 45) for o in (22, 15, 9, 4, 1)] + [(scr_chain(5, 0), 900)]
                         + [(scr_chain_rest(5, i * 0.8), 180) for i in range(8)]
                         + [(scr_chain(4, o), 45) for o in (-22, -15, -9, -4, -1)] + [(scr_chain(4, 0), 900)]),
    "chain-belt": ([(scr_chain(4, o), 45) for o in (22, 15, 9, 4, 1)] + [(scr_chain(4, 0), 1400)]
                   + [(scr_chain(5, o), 45) for o in (22, 15, 9, 4, 1)] + [(scr_chain(5, 0), 1400)]
                   + [(scr_chain(4, o), 45) for o in (-22, -15, -9, -4, -1)]),
    "session-clip": [(scr_sclip(0, i % 2 == 0), 250) for i in range(4)],
    "belt-session": ([(scr_sbelt(0, 0), 1200)] + [(scr_sbelt(1, o), 45) for o in (22, 15, 9, 4, 1)]
                     + [(scr_sbelt(1, 0), 1200)] + [(scr_sbelt(0, o), 45) for o in (-22, -15, -9, -4, -1)]),
    "belt-pick": ([(scr_belt(2, 0), 1200)] + [(scr_belt(3, o), 45) for o in (22, 15, 9, 4, 1)]
                  + [(scr_belt(3, 0), 1200)] + [(scr_belt(2, o), 45) for o in (-22, -15, -9, -4, -1)]),
    "sampling": [(scr_sampling(i * 0.35), 120) for i in range(6)],
    # the number is the value set by hand and holds still; only the mark for the modulated value moves
    "param-touch": ([(scr_touch(0.62, "1.24", 0.62, turned=False), 900)]
                    + [(scr_touch(0.62 + 0.03 * i, "%.2f" % (1.24 + 0.2 * i), 0.62 + 0.03 * i), 160) for i in range(6)]),
    # at rest the cutoff's pictogram moves as the LFO sweeps it, against the fixed tick of the value set by hand
    "param-page": [(scr_page(0.16 * math.sin(i * math.pi / 4)), 120) for i in range(8)],
    "view-scene": [(scr_scene(i * 0.33), 140) for i in range(6)],
    "device-main": [(scr_main(i * 0.25), 110) for i in range(12)],
    "view-scope": [(scr_scope(i * 0.5), 140) for i in range(6)],
    "map-row": [(scr_map(d, t), 140) for d, t in ((0.1, "+10"), (0.2, "+20"), (0.3, "+30"), (0.4, "+40"))],
}


# ------------------------------------------------------------------ Screen system 2 (24 November 2026)
# The owner's screen rules, drawn by redesign.py (which refuses text that does not fit its slot). These replace the
# mock-ups above where the two differ, and add the screens the redesign brought in.
import redesign as R  # noqa: E402

_N = 24


def _sw(f, a=0.35, c=0.5):
    return c + a * math.sin(f / float(_N) * 2 * math.pi)


S2 = [
    ("note-device-view", "The chain at rest",
     lambda: R.chain_rest(R.PARAMS["SUB  MAIN"], 0),
     [(R.chain_rest(R.PARAMS["SUB  MAIN"], f / _N), 110) for f in range(_N)],
     "Home in Note Mode, nothing touched: the main page of the device under the wheel as eight icons, as the "
     "knobs lie, each drawing what it does and moving with modulation (here the cutoff swept by an LFO). No name, "
     "no track number, no marks: the belt names the device when the wheel turns, the card names a knob when "
     "touched. The steps row under them."),
    ("param-page", "A page drawn as one thing: FILTER",
     lambda: R.filter_scene(0.2), [(R.filter_scene(f / 32.), 80) for f in range(32)],
     "Inside SUB on FILTER: one filter of spaced bars beside its envelope. The bars follow the cutoff as the "
     "envelope sweeps it, a tick where the knob has it, a dot where the envelope takes it; a box rides the "
     "envelope with the newest note. Page marks on top, the page's name in its slot, no track number."),
    ("page-amp", "A page drawn as one thing: AMP",
     lambda: R.amp_scene(0.2), [(R.amp_scene(f / 32.), 80) for f in range(32)],
     "Inside SUB on AMP: one wide envelope with the box riding it as a note plays and is let go; the level beside "
     "it, its fill the note's loudness. Any page past the main one that holds an envelope is drawn this way."),
    ("page-trig", "A page of icons: TRIG",
     lambda: R.page_rest(R.PARAMS["SEQ  TRIG"], "TRIG", 0, 2, 0, chosen=[0, 0, 0, 3, 3, 0, 0, 1]),
     [(R.page_rest(R.PARAMS["SEQ  TRIG"], "TRIG", 0, 2, f / _N, chosen=[0, 0, 0, 3, 3, 0, 0, 1]), 110)
      for f in range(_N)],
     "Inside SEQ on TRIG: micro (a note beside the step line), ratchet (a step split, one dot between strikes), "
     "chance (a rolling die and its percentage), condition (a:b as two groups of boxes either side of a colon); "
     "function (a sign above the steps, the playhead moving as it moves it), amount, length, slide."),
    ("param-touch", "A knob touched: the card",
     lambda: R.card("CUTOFF", 0.5, 0), [(R.card("CUTOFF", _sw(f), f / _N), 100) for f in range(_N)],
     "Any knob touched or turned, anywhere: its NAME (2x, 10 characters) on top, its ICON in the middle (the "
     "page's icon, each dot doubled) moving with modulation, its VALUE in a white strip (2x, 10 characters with "
     "the unit). A second after it is let go the view comes back."),
    ("chain-card", "The card: FUNCTION",
     lambda: R.card("FUNCTION", 0, 0, chosen=3), [(R.card("FUNCTION", 0, f / _N, chosen=3), 100) for f in range(_N)],
     "FUNCTION's sign has its own band above the steps (a solid arrowhead), and the playhead moves through them as "
     "the function moves it. The value has its own strip, so nothing is written over the picture."),
    ("card-chance", "The card: CHANCE",
     lambda: R.card("CHANCE", 0.62, 0), [(R.card("CHANCE", 0.62, f / _N), 100) for f in range(_N)],
     "CHANCE: a die rolling, a new face each roll, beside the percentage."),
    ("card-condition", "The card: CONDITION",
     lambda: R.card("CONDITION", 0, 0, chosen=3), [(R.card("CONDITION", 0, f / _N, chosen=3), 100) for f in range(_N)],
     "CONDITION 2:4: four boxes with the second filled, a colon, four boxes all filled; the pass the loop is on "
     "underlined."),
    ("card-ratchet", "The card: RATCHET",
     lambda: R.card("RATCHET", 3 / 7., 0), [(R.card("RATCHET", (f // 3) / 7.0, f / _N), 100) for f in range(_N)],
     "RATCHET: one step split into its strikes, 1 to 8, whole dots each and one dot between, always."),
    ("card-direction", "The card: DIRECTION",
     lambda: R.card("DIRECTION", 0, 0, chosen=2), [(R.card("DIRECTION", 0, f / _N, chosen=2), 100) for f in range(_N)],
     "DIRECTION PENDULUM: one line with a solid head at each end, above the steps; the playhead bounces."),
    ("card-send", "The card: SEND",
     lambda: R.card("SEND 1", 0.32, 0), [(R.card("SEND 1", 0.32, f / _N), 100) for f in range(_N)],
     "SEND 1: a bar filled as far as the send, flowing into the bus's box with its number in it."),
    ("card-level", "The card: a track's level",
     lambda: R.card("MIX LEVEL", 0.76, 0), [(R.card("MIX LEVEL", 0.76, f / _N), 100) for f in range(_N)],
     "LEVEL in Session Mode or the mixer: the track's live meter lying down, the level a tall mark across it."),
    ("step-held", "A step held",
     lambda: R.held_step(0), [(R.held_step(f / _N), 110) for f in range(_N)],
     "A step held at the chain: the icons give up height to the step card, S4 in its 3-character box and the "
     "notes or chord in a 7-character slot; the held step framed in the steps row."),
    ("flow-page-turn", "The wheel turned while a knob is touched",
     lambda: R.page_flash("AMP", 3, 5),
     ([(R.card("CUTOFF", 0.5, f / 10.), 100) for f in range(10)] + [(R.page_flash("AMP", 3, 5), 600)]
      + [(R.card("ATTACK", 0.25, f / 10.), 100) for f in range(14)]),
     "CUTOFF's card; the wheel turns to AMP, which shows for 0.6 s with its place among the pages; then the card "
     "of the same knob on AMP. The finger never leaves the knob."),
    ("pop-track", "A track chosen",
     lambda: R.track_pop(3, "SYNTH", "WARM PAD 2", 0),
     ([(R.track_pop(3, "SYNTH", "WARM PAD 2", 0), 800)]
      + [(R.track_pop(3, "SYNTH", "WARM PAD 2", o), 100) for o in range(0, 40, 4)]
      + [(R.track_pop(3, "SYNTH", "WARM PAD 2", 36), 800)]),
     "The only place the track's number appears: in a box the height of the screen at 3x, then the type and the "
     "preset (which slides inside its 6-character slot when longer), and the type's picture. Shown for a second "
     "when the track changes, and while a track button is held."),
]
_pos = {k: i for i, (k, _n, _f, _d) in enumerate(SCREENS)}
for _k, _name, _fn, _frames, _desc in S2:
    if _k in _pos:
        SCREENS[_pos[_k]] = (_k, _name, _fn, _desc)
    else:
        SCREENS.append((_k, _name, _fn, _desc))
    ANIM[_k] = _frames
