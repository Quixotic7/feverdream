"""Screen system 2: the proposal drawn to the owner's rules of 24 November 2026 (docs/DESIGN.md decisions log).

  - Text never overlaps anything, and always fits a slot defined in advance.
  - One face (Move Designer's Pixel 5 x 7) and one size per role; a size never changes to fit a name.
  - A touched knob always shows its name, its value and its icon, animated.
  - Icons say what they mean, and move whenever the thing they draw is modulated.
  - No track number on screen at rest; a track change is a popup: number, type, preset.
  - A page turned while a knob is touched shows the page for a moment, then the knob again.
  - A knob's LED is as bright as its value.

Run: python3 design/tools/redesign.py  ->  design/redesign/*.gif (animated, 4x) and *.png
The slots below are the contract: txt() raises if a text does not fit its slot, so a design that breaks the rules
does not render.
"""
import math
import os
import random

from PIL import Image

from gfx import Scr, W, H, w5, ROOT

OUT = os.path.join(ROOT, "design", "redesign")
K = 4                                   # 4 screen dots a picture dot
FG, BG = (238, 240, 232), (10, 10, 12)

# ------------------------------------------------------------------ the type: roles, sizes and slots
# role: (scale, slot width in dots). The size of a role never changes; the text is written to fit the slot.
ROLES = {
    "name": (2, 126),       # a parameter's, a page's, a device's name: 10 characters
    "value": (2, 124),      # a value with its unit, in the value strip: 10 characters
    "num": (3, 36),         # a track's number in the track popup: 2 characters
    "side": (2, 82),        # beside the number box: 6 characters
    "step": (2, 34),        # a held step's box: S16 = 3 characters
    "notes": (2, 86),       # a held step's notes: 7 characters
}


def fits(role, text):
    k, slot = ROLES[role]
    return w5(text, k) <= slot


def txt(s, x, y, text, role, v=1):
    k, slot = ROLES[role]
    if not fits(role, text):
        raise ValueError("%r does not fit the %s slot (%d dots at %dx)" % (text, role, slot, k))
    s.t5(x, y, text, v, k)


def chars(role):
    k, slot = ROLES[role]
    return (slot + k) // (6 * k)


# ------------------------------------------------------------------ the icons
# One drawing per parameter, for any box: 30 x 21 on a page of eight, 124 x 27 on the knob card. v is the value the
# sound is using now (0..1), ph the time (0..1) for things that move by themselves (a wave, noise, a playhead).
def clamp(v):
    return 0.0 if v < 0 else 1.0 if v > 1 else v


def lp(s, x, y, w, h, corner, peak=0.0, thick=True):
    """a low-pass curve: flat, a peak at the corner as tall as the resonance, then down"""
    xc = x + int(corner * (w - 8)) + 2
    top = y + 3 + int(h * 0.15)
    pts = [(x, top), (xc - 3, top), (xc, top - int(peak * (h * 0.45))), (xc + 3, top + 2), (xc + 6, y + h - 1),
           (x + w - 1, y + h - 1)]
    s.poly(pts)
    if thick:
        s.poly([(a, b + 1) for a, b in pts[:3]])


def adsr_pts(x, y, w, h, a, d, su, r):
    seg = (w - 4) / 4.0
    x1 = x + 1 + a * seg
    x2 = x1 + 1 + d * seg
    x3 = x + w - 2 - r * seg - 1
    x4 = x + w - 1
    ys = y + (1 - su) * (h - 2)
    return [(x, y + h - 1), (x1, y), (x2, ys), (x3, ys), (x4, y + h - 1)]


def adsr(s, x, y, w, h, part, v, filt=False):
    vals = {"a": 0.25, "d": 0.4, "s": 0.55, "r": 0.4}
    vals[part] = v
    pts = adsr_pts(x, y, w, h, vals["a"], vals["d"], vals["s"], vals["r"])
    s.poly(pts)
    if filt:                                    # a filter's envelope: shaded under, an amp's is bare
        for i in range(int(pts[0][0]), int(pts[-1][0])):
            for j in range(y, y + h):
                if (i + j) % 3 == 0 and below(pts, i, j):
                    s.set(i, j)
    seg = {"a": (0, 1), "d": (1, 2), "s": (2, 3), "r": (3, 4)}[part]
    (ax, ay), (bx, by) = pts[seg[0]], pts[seg[1]]
    for o in (-1, 1):                           # the part this knob sets, three dots thick
        s.line(ax, ay + o, bx, by + o)
        s.line(ax + o, ay, bx + o, by)


def below(pts, i, j):
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if ax <= i <= bx and bx != ax:
            yy = ay + (by - ay) * (i - ax) / (bx - ax)
            return j > yy
    return False


def wave(s, x, y, w, h, kind, ph=0.0, cycles=2.0, dotted=False, duty=0.5, amp=1.0):
    prev = None
    for i in range(w):
        t = (i / float(w) * cycles + ph) % 1.0
        if kind == 0:   # saw
            u = 1 - 2 * t
        elif kind == 1:  # square / pulse
            u = 1 if t < duty else -1
        elif kind == 2:  # triangle
            u = 1 - 4 * abs(t - 0.5)
        else:           # sine
            u = math.cos(t * 2 * math.pi)
        yy = y + h / 2.0 - u * amp * (h / 2.0 - 1)
        if dotted and i % 3 == 2:
            prev = None
            continue
        if prev is not None:
            s.line(x + i - 1, prev, x + i, yy)
        prev = yy


def bar(s, x, y, w, h, v):
    s.rect(x, y + h // 2 - 3, w, 7)
    s.fill(x + 1, y + h // 2 - 2, int(v * (w - 2)), 5)


def fader(s, x, y, w, h, v):
    """a level: the volume wedge, filled as far as the level"""
    pts = [(x, y + h - 1), (x + w - 1, y + h - 1), (x + w - 1, y)]
    s.poly(pts + [pts[0]])
    for i in range(int(v * (w - 1))):
        top = y + h - 1 - int(i * (h - 1) / float(w - 1))
        s.vl(x + i, top, y + h - top)


def keys(s, x, y, w, h, lit=(), dots=()):
    """an octave of keys, C to B. A note in lit or dots is FILLED: a white key filled below the black keys, a black
    key solid; a note not in it is hollow, black keys too, so a scale's black keys read as clearly as its white."""
    on = set(lit) | set(dots)
    kw = w / 7.0
    bh = max(4, int(h * 0.55))                  # the black keys' height
    for i, n in enumerate([0, 2, 4, 5, 7, 9, 11]):
        x0 = int(x + i * kw)
        x1 = int(x + (i + 1) * kw) if i < 6 else x + w - 1
        s.rect(x0, y, x1 - x0 + 1, h)
        if n in on:
            s.fill(x0 + 2, y + bh + 2, max(1, x1 - x0 - 3), max(1, h - bh - 4))
    bw = max(3, int(round(kw * 0.65)))
    for n, pos in ((1, 1), (3, 2), (6, 4), (8, 5), (10, 6)):
        x0 = int(x + pos * kw) - bw // 2
        s.fill(x0 - 1, y, bw + 2, bh + 1, 0)            # a dot of black around it, off the white keys' lines
        if n in on:
            s.fill(x0, y, bw, bh)
        else:
            s.rect(x0, y, bw, bh)


def steps(s, x, y, w, h, n=8):
    sw = w / float(n)
    return [(int(x + i * sw), int(sw) - 2) for i in range(n)]


def head_tri(s, x1, y, d, head):
    """a solid triangle pointing d (1 right, -1 left), its tip at x1"""
    for k in range(head + 1):
        s.vl(x1 - d * k, y - k, 2 * k + 1)


def arrow(s, x0, y, x1, head=3):
    d = 1 if x1 > x0 else -1
    s.line(x0, y, x1 - d * head, y)
    head_tri(s, x1, y, d, head)


def ladder(s, x, y, w, h, v, n):
    """a few rungs and a marker on one: octaves"""
    for i in range(n):
        yy = y + int(i * (h - 1) / (n - 1))
        s.hl(x + w // 4, yy, w // 2)
    k = int(round(v * (n - 1)))
    yy = y + int((n - 1 - k) * (h - 1) / (n - 1))
    s.fill(x + w // 4 - 3, yy - 1, w // 2 + 6, 3)


def icon(s, pid, x, y, w, h, v, ph=0.0, chosen=0):
    v = clamp(v)
    m = y + h // 2
    if pid in ("CUTOFF",):
        lp(s, x, y, w, h, v, 0.25)
    elif pid == "RESONANCE":
        lp(s, x, y, w, h, 0.5, v)
    elif pid == "ENV AMT":                      # the filter at full height; just above its bottom line an arrow from the
        hd = 2 if h < 16 else 3                 # corner to where the envelope takes it, a solid head
        lp(s, x, y, w, h, 0.35, 0.2, thick=False)
        xc = x + int(0.35 * (w - 8)) + 2
        ay = y + h - 3 - hd                     # its head's lowest dot one dot above the filter's bottom line
        e = (v - 0.5) * 2
        x1 = xc + int(e * w * 0.45)
        if abs(x1 - xc) > hd + 1:
            d = 1 if x1 > xc else -1
            s.line(xc, ay, x1 - d * hd, ay)
            head_tri(s, x1, ay, d, hd)
    elif pid == "KEY TRACK":                    # keys under, a line as steep as the tracking
        keys(s, x, y + h - max(6, h // 3), w, max(6, h // 3))
        s.line(x, y + h - max(6, h // 3) - 2, x + w - 1, y + h - max(6, h // 3) - 2 - int(v * (h * 0.6)))
    elif pid in ("F ATTACK", "F DECAY", "F SUSTAIN", "F RELEASE"):
        adsr(s, x, y, w, h, {"F ATTACK": "a", "F DECAY": "d", "F SUSTAIN": "s", "F RELEASE": "r"}[pid], v, filt=True)
    elif pid in ("ATTACK", "DECAY", "SUSTAIN", "RELEASE"):
        adsr(s, x, y, w, h, pid[0].lower(), v)
    elif pid in ("WAVE 1", "WAVE 2", "LFO WAVE"):
        kind = chosen
        if pid == "LFO WAVE" and kind == 3:     # random: steps held
            random.seed(int(ph * 8))
            seg = w // 6
            for i in range(6):
                yy = y + random.randint(1, h - 2)
                s.hl(x + i * seg, yy, seg)
        else:
            wave(s, x, y, w, h, kind, ph, cycles=2 if w > 40 else 1.5, dotted=pid == "WAVE 2")
    elif pid == "OCTAVE 2" or pid == "OCTAVE":
        ladder(s, x, y, w, h, v, 5 if pid == "OCTAVE 2" else 8)
    elif pid == "DETUNE":                       # two waves apart by the detune
        wave(s, x, y, w, h, 3, ph, cycles=2)
        wave(s, x, y, w, h, 3, ph + v * 0.25, cycles=2 + v * 0.6, dotted=True)
    elif pid == "OSC MIX":                      # wave 1 shrinking as wave 2 grows
        wave(s, x, y, w // 2 - 2, h, 0, ph, cycles=1, amp=max(0.1, 1 - v))
        wave(s, x + w // 2 + 2, y, w // 2 - 2, h, 1, ph, cycles=1, amp=max(0.1, v), dotted=True)
        s.vl(x + w // 2, y, h)
    elif pid == "SUB":                          # a slow, deep wave under the oscillator
        wave(s, x, y, w, h // 2, 0, ph, cycles=3)
        wave(s, x, y + h // 2, w, h // 2, 3, ph / 2, cycles=1, amp=max(0.08, v))
    elif pid == "NOISE":
        random.seed(int(ph * 997))
        for _ in range(int(v * w * h * 0.3)):
            s.set(x + random.randrange(w), y + random.randrange(h))
        s.rect(x, y, w, h)
    elif pid == "GLIDE":                        # one note to the next, as slow as the glide
        a = x + 2 + int(v * (w - 14))
        s.fill(x, y + h - 4, 6, 3)
        s.line(x + 6, y + h - 3, a + 2, y + 2)
        s.fill(a + 2, y + 1, w - (a - x) - 2, 3)
    elif pid == "VELOCITY":                     # louder as harder: bars of rising height, as steep as the amount
        for i in range(5):
            hh = int((h - 2) * (1 - v + v * (i + 1) / 5.0))
            s.fill(x + i * (w // 5) + 1, y + h - max(2, hh), max(2, w // 5 - 3), max(2, hh))
    elif pid in ("LEVEL",):
        fader(s, x, y, w, h, v)
    elif pid == "LFO RATE":
        wave(s, x, y, w, h, 3, ph * (1 + 4 * v), cycles=0.6 + v * 4)
    elif pid == "LFO PITCH":                    # a note bobbing by the depth
        wave(s, x, y, w, h, 3, ph, cycles=1.5, amp=max(0.05, v), dotted=True)
        cy = m - math.sin(ph * 2 * math.pi) * v * (h / 2 - 3)
        s.disc(x + w // 2, cy, 2)
        s.vl(x + w // 2 + 2, cy - 6, 6)
    elif pid == "LFO CUTOFF":                   # a corner swung by the depth
        lp(s, x, y, w, h, 0.5 + 0.4 * v * math.sin(ph * 2 * math.pi), 0.2)
    elif pid == "PULSE W":
        wave(s, x, y, w, h, 1, 0, cycles=2, duty=0.05 + 0.9 * v)
    elif pid == "START" or pid == "LENGTH S":   # a sample, the start marked / the part played
        random.seed(3)
        for i in range(w):
            a = int((h / 2 - 1) * abs(math.sin(i * 0.31)) * (1 - i / float(w) * 0.7))
            s.vl(x + i, m - a, 2 * a + 1) if i % 2 == 0 else None
        st = x + int(v * (w - 1)) if pid == "START" else x + 2
        en = x + w - 1 if pid == "START" else x + 2 + int(v * (w - 3))
        s.fill(st, y, 2, h)
        if pid == "LENGTH S":
            s.fill(en - 1, y, 2, h)
        s.inv(x, y, max(0, st - x), h) if pid == "START" else s.inv(en + 1, y, x + w - en - 1, h)
    elif pid == "TUNE":                         # a ruler of semitones, the middle tall, the pitch marked on it
        for i in range(0, w, 2):
            s.vl(x + i, y + h - 3, 3)
        s.vl(x + w // 2, y + 1, h - 1)
        px = x + int(v * (w - 5))
        s.fill(px, y + h // 2 - 3, 5, 6)
    elif pid == "PAN":
        s.hl(x, m, w)
        s.vl(x + w // 2, m - 3, 7)
        px = x + int(v * (w - 6)) + 3
        s.disc(px, m, 3)
        s.t5(x, y, "L", 1, 1) if h >= 20 else None
        s.t5(x + w - 5, y, "R", 1, 1) if h >= 20 else None
    elif pid == "MODE":                         # one shot: the whole sample; gate: cut where the pad lets go
        icon(s, "LENGTH S", x, y, w, h, 1.0 if chosen == 0 else 0.45)
    elif pid == "REVERSE":
        icon(s, "LENGTH S", x, y, w, h, 1.0)
        arrow(s, x + w - 3, y + 2, x + 2, 3) if chosen else arrow(s, x + 2, y + 2, x + w - 3, 3)
    elif pid == "LAYOUT":                       # the pads: which are lit for the layout
        pat = [[1, 0, 1, 0, 1, 1, 0, 1], [1, 1, 1, 1, 1, 1, 1, 1], [0, 1, 1, 0, 1, 1, 1, 0]][chosen % 3]
        cw = w / 8.0
        for r in range(4):
            for c in range(8):
                xx, yy = int(x + c * cw), int(y + r * h / 4.0)
                if pat[(c + r * 3) % 8]:
                    s.fill(xx, yy, max(1, int(cw) - 1), max(1, int(h / 4.0) - 1))
                else:
                    s.set(xx + int(cw) // 2, yy + int(h / 8.0))
    elif pid == "KEY":
        keys(s, x, y, w, h, lit=(chosen,))
    elif pid == "SCALE":                        # the scale's notes on the key's octave: E major, D minor, C major
        root, steps_ = [(4, (0, 2, 4, 5, 7, 9, 11)), (2, (0, 2, 3, 5, 7, 8, 10)), (0, (0, 2, 4, 5, 7, 9, 11))][chosen % 3]
        keys(s, x, y, w, h, dots=[(root + k) % 12 for k in steps_])
    elif pid == "MICRO":                        # the step's line, and the note early or late of it
        s.vdots(x + w // 2, y, h, 2)
        off = int((v - 0.5) * (w - 12))
        s.fill(x + w // 2 + off - 4, m - 3, 9, 7)
    elif pid == "RATCHET":                      # one step played n times
        n = 1 + int(round(v * 7))
        bw = (w - (n - 1)) // n                 # whole dots each, one dot between, always
        off = (w - (n * bw + n - 1)) // 2       # what is left over split either side
        for i in range(n):
            s.fill(x + off + i * (bw + 1), y + 3, bw, h - 6)
    elif pid == "CHANCE":                       # a die rolling, and beside it the percentage: no bar
        small = w < 40
        ds = 9 if small else min(h - 1, 13) - 1  # the die: a square, one dot short of the box so its hop stays inside
        roll = int(ph * 12)
        face = (roll * 5 + 2) % 6 + 1           # a new face each roll
        top = y + (h - ds - 1) // 2
        dy = top + (roll % 2)                   # a dot's hop as it tumbles, never out of the box
        pc = "%d%%" % max(1, round(v * 100))
        gx = x + (w - (ds + 3 + w5(pc))) // 2   # the die and the number together, in the middle
        s.rect(gx, dy, ds, ds)
        q = (ds - 3) // 4 + 1                    # the pips at a quarter, the middle, three quarters
        px = [gx + q, gx + ds // 2, gx + ds - 1 - q]
        py = [dy + q, dy + ds // 2, dy + ds - 1 - q]
        pips = {1: [(1, 1)], 2: [(0, 0), (2, 2)], 3: [(0, 0), (1, 1), (2, 2)], 4: [(0, 0), (2, 0), (0, 2), (2, 2)],
                5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)], 6: [(0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)]}[face]
        for i, j in pips:
            s.fill(px[i], py[j], 2 if ds >= 11 else 1, 2 if ds >= 11 else 1)
        s.t5(gx + ds + 3, y + (h - 7) // 2, pc, 1, 1)
    elif pid == "CONDITION":                    # a:b as two groups of b boxes and a colon: on the left box a filled,
        a, b = COND[chosen % len(COND)]          # on the right all filled; the pass now underlined on the left
        gw = (w - 5) // 2
        bw = gw / float(b)
        cur = int(ph * b * 2) % b
        bh = h - 3 if h < 16 else h - 6
        top = y + (h - bh) // 2 - 1
        for i in range(b):
            xl = int(x + i * bw)
            xr = int(x + gw + 5 + i * bw)
            ww = max(2, int(bw) - 1)
            (s.fill if i + 1 == a else s.rect)(xl, top, ww, bh)
            s.fill(xr, top, ww, bh)
            if i == cur:
                s.hl(xl, top + bh + 1, ww)
        s.set(x + gw + 2, top + bh // 3)
        s.set(x + gw + 2, top + 2 * bh // 3)
    elif pid == "FUNCTION":                     # what the playhead does at the step: a sign above, the steps under it,
        f = chosen                              # the playhead moving through them as that function moves it
        ah = (h - 2) // 2                       # the sign's band and the steps' band never touch
        ay = y + ah // 2
        hd = max(1, min(3, ah // 2))
        by, bh = y + ah + 2, h - ah - 2
        ns = 8 if w >= 48 else 4                # four steps when small, so each stays a box
        cells = steps(s, x, by, w, bh, ns)
        t = int(ph * 16)
        if f == 1:      # restart: on to the step that has it (three quarters along), then back to the first
            cur = t % (ns * 3 // 4)
        elif f == 2:    # reverse
            cur = ns - 1 - t % ns
        elif f == 4:    # random
            cur = (t * 5 + 3) % ns
        else:           # none, forward
            cur = t % ns
        for i, (xx, ww) in enumerate(cells):
            (s.fill if i == cur else s.rect)(xx, by, max(2, ww), bh)
        if f == 1:
            arrow(s, x + w - 3, ay, x + 2, hd)
            s.vl(x, ay - hd, 2 * hd + 1)
        elif f == 2:
            arrow(s, x + w - 3, ay, x + 2, hd)
        elif f == 3:
            arrow(s, x + 2, ay, x + w - 3, hd)
        elif f == 4:
            for k in range(3):
                s.fill(x + w // 2 - 6 + k * 5, ay - 1 + (k % 2) * 2 - 1, 2, 2)
        else:
            s.dots(x, ay, w, 3)
    elif pid == "AMOUNT":
        s.hl(x, m, w)
        s.vl(x + w // 2, y + 2, h - 4)
        e = int((v - 0.5) * (w - 4))
        s.fill(min(x + w // 2, x + w // 2 + e), m - 3, abs(e), 7)
    elif pid == "LENGTH":                       # a note as long as it is held, over the steps
        for i in range(8):
            s.vl(x + int(i * w / 8.0), y + h - 4, 4)
        s.fill(x, y + 4, max(3, int(v * (w - 1))), h - 10)
    elif pid == "SLIDE":                        # two notes, joined when sliding
        s.fill(x, y + h - 6, w // 3, 4)
        s.fill(x + 2 * w // 3, y + 2, w // 3, 4)
        if chosen:
            s.line(x + w // 3, y + h - 5, x + 2 * w // 3, y + 3)
            s.line(x + w // 3, y + h - 4, x + 2 * w // 3, y + 4)
    elif pid == "SPEED":                        # a playhead over the steps, as fast as the speed
        sp = [1 / 16., 1 / 8., 1 / 4., 1 / 2., 3 / 4., 1, 1.5, 2][chosen]
        cells = steps(s, x, y, w, h, 8)
        cur = int(ph * 8 * sp * 2) % 8
        for i, (xx, ww) in enumerate(cells):
            (s.fill if i == cur else s.rect)(xx, y + h // 2 - 3, max(2, ww), 7)
        arrow(s, x + 1, y + 2, x + 1 + int(sp / 2.0 * (w - 4)), 2)
    elif pid == "FEEL":                         # four even, or three in the time of four
        n = 3 if chosen else 4
        for i in range(n):
            s.disc(x + int((i + 0.5) * w / n), m, max(2, min(h, w // n) // 3))
    elif pid == "LOOP LEN":                     # sixteen steps, the loop's bracket over them
        for i in range(16):
            s.fill(x + int(i * w / 16.0), m, max(1, int(w / 16.0) - 1), 3)
        e = x + int(v * (w - 1))
        s.hl(x, y + 2, e - x)
        s.vl(x, y + 2, 5)
        s.vl(e, y + 2, 5)
    elif pid == "DIRECTION":                    # a sign above, the steps under it, the playhead moving as the direction does
        d = chosen
        ah = (h - 2) // 2                       # the two bands never touch
        ay = y + ah // 2
        hd = max(1, min(3, ah // 2))
        by, bh = y + ah + 2, h - ah - 2
        ns = 8 if w >= 48 else 4
        cells = steps(s, x, by, w, bh, ns)
        t = int(ph * ns * 2)
        cur = [t % ns, ns - 1 - t % ns, t % ns if (t // ns) % 2 == 0 else ns - 1 - t % ns, (t * 5 + 3) % ns][d]
        for i, (xx, ww) in enumerate(cells):
            (s.fill if i == cur else s.rect)(xx, by, max(2, ww), bh)
        if d == 0:
            arrow(s, x + 2, ay, x + w - 3, hd)
        elif d == 1:
            arrow(s, x + w - 3, ay, x + 2, hd)
        elif d == 2:                            # pendulum: one line, a head at each end
            s.line(x + 2 + hd, ay, x + w - 3 - hd, ay)
            head_tri(s, x + 2, ay, -1, hd)
            head_tri(s, x + w - 3, ay, 1, hd)
        else:                                   # random: scattered dots
            for k in range(3):
                s.fill(x + w // 2 - 6 + k * 5, ay - 1 + (k % 2) * 2 - 1, 2, 2)
    elif pid == "MIX LEVEL":                    # the track's meter, live, lying down; the level a tall mark across it
        mtr = clamp(0.55 + 0.35 * math.sin(ph * 2 * math.pi * 3) * math.sin(ph * 7))
        s.rect(x, m - 4, w, 9)
        s.fill(x + 2, m - 2, int(mtr * (w - 4)), 5)
        xv = x + 1 + int(v * (w - 4))
        s.fill(xv, y, 2, h)
    elif pid.startswith("SEND"):                # a bar filled as far as the send, pouring into the bus's box, its number in it
        n = pid[-1]
        bw = 9                                  # the box: the digit (5 x 7) and a dot of room around it
        bh = 11
        by = y + (h - bh) // 2
        bx = x + w - bw
        s.rect(bx, by, bw, bh)
        s.t5(bx + 2, by + 2, n, 1, 1)
        lw = w - bw - 5                          # the bar, then a short arrow into the box
        th = min(7, h - 4)
        ty = y + (h - th) // 2
        s.rect(x, ty, lw, th)
        fw = int(v * (lw - 2))
        s.fill(x + 1, ty + 1, fw, th - 2)
        if fw > 3:                              # the flow: gaps moving through the fill toward the bus
            for k in range(-4, fw, 4):
                gx = x + 1 + k + int(ph * 4 * (1 + 2 * v)) % 4
                if x + 1 <= gx < x + 1 + fw:
                    s.vl(gx, ty + 2, th - 4, 0)
        s.hl(x + lw, ty + th // 2, 4)
        s.set(x + lw + 3, ty + th // 2 - 1)
        s.set(x + lw + 3, ty + th // 2 + 1)
    else:
        bar(s, x, y, w, h, v)


# the devices and what their knobs are now; choices are listed so a sheet can step through them
PARAMS = {
    "SUB  MAIN": ["CUTOFF", "RESONANCE", "ENV AMT", "F DECAY", "WAVE 1", "DETUNE", "RELEASE", "LEVEL"],
    "SUB  OSC": ["WAVE 1", "WAVE 2", "OCTAVE 2", "DETUNE", "OSC MIX", "SUB", "NOISE", "GLIDE"],
    "SUB  FILTER": ["CUTOFF", "RESONANCE", "ENV AMT", "KEY TRACK", "F ATTACK", "F DECAY", "F SUSTAIN", "F RELEASE"],
    "SUB  AMP": ["ATTACK", "DECAY", "SUSTAIN", "RELEASE", "VELOCITY", "LEVEL"],
    "SUB  LFO": ["LFO RATE", "LFO WAVE", "LFO PITCH", "LFO CUTOFF", "PULSE W"],
    "SAMPLER  MAIN": ["START", "LENGTH S", "TUNE", "ATTACK", "DECAY", "CUTOFF", "PAN", "LEVEL"],
    "SAMPLER  PLAY": ["MODE", "REVERSE"],
    "PADS  LAYOUT": ["LAYOUT", "KEY", "SCALE", "OCTAVE"],
    "SEQ  TRIG": ["MICRO", "RATCHET", "CHANCE", "CONDITION", "FUNCTION", "AMOUNT", "LENGTH", "SLIDE"],
    "SEQ  CLIP": ["SPEED", "FEEL", "LOOP LEN", "DIRECTION"],
    "MIX": ["MIX LEVEL", "PAN", "SEND 1", "SEND 2", "SEND 3"],
}
COND = [(1, 2), (2, 2), (1, 4), (2, 4), (4, 8)]
CHOICES = {"WAVE 1": 4, "WAVE 2": 4, "LFO WAVE": 4, "MODE": 2, "REVERSE": 2, "LAYOUT": 3, "KEY": 12, "SCALE": 3,
           "CONDITION": 5, "FUNCTION": 5, "SLIDE": 2, "SPEED": 8, "FEEL": 2, "DIRECTION": 4}
# the name each shows, at most 10 characters (the name slot); the screen never shrinks a name
NAME = {"LENGTH S": "LENGTH", "MIX LEVEL": "LEVEL", "F SUSTAIN": "F SUSTAIN", "LFO CUTOFF": "LFO CUTOFF",
        "LFO PITCH": "LFO PITCH", "KEY TRACK": "KEY TRACK"}
# a value as the card shows it: at most 10 characters with its unit
VALUES = {
    "CUTOFF": lambda v: "%.2f KHZ" % (0.03 * 600 ** v),
    "RESONANCE": lambda v: "%d %%" % round(v * 100),
    "ENV AMT": lambda v: "%+d %%" % round((v - .5) * 200),
    "FUNCTION": lambda c: ["NONE", "RESTART", "REVERSE", "FORWARD", "RANDOM"][c],
    "RATCHET": lambda v: "%d X" % (1 + round(v * 7)),
    "TUNE": lambda v: "%+d ST" % round((v - .5) * 48),
    "CHANCE": lambda v: "%d %%" % max(1, round(v * 100)),
    "CONDITION": lambda c: "%d:%d" % COND[c],
    "MIX LEVEL": lambda v: "%.1f DB" % (20 * math.log10(max(1e-4, v * 1.25)) if v > 0 else -99),
    "DIRECTION": lambda c: ["FORWARD", "REVERSE", "PENDULUM", "RANDOM"][c],
    "WAVE 1": lambda c: ["SAW", "SQUARE", "TRIANGLE", "SINE"][c],
    "F DECAY": lambda v: "%d MS" % round(8000 ** v),
    "SEND 1": lambda v: "%d %%" % round(v * 100),
    "PAN": lambda v: "C" if abs(v - .5) < .02 else ("L%d" % round((.5 - v) * 200) if v < .5 else "R%d" % round((v - .5) * 200)),
}


def name_of(pid):
    return NAME.get(pid, pid)


# ------------------------------------------------------------------ the screens
def card(pid, v, ph, chosen=0, page_marks=None):
    """A knob touched or turned: its NAME (top), its ICON (the middle, animated), its VALUE in the strip (bottom)."""
    s = Scr()
    txt(s, 1, 1, name_of(pid), "name")
    big = Scr()                                 # the page's icon, made bigger: drawn at 62 x 13, then each dot doubled
    icon(big, pid, 0, 0, 62, 13, v, ph, chosen)
    for j in range(14):
        for i in range(63):
            if big.get(i, j):
                s.fill(2 + 2 * i, 18 + 2 * j, 2, 2)
    s.fill(0, 48, W, 16)
    val = VALUES[pid](chosen if pid in CHOICES else v) if pid in VALUES else "%d %%" % round(v * 100)
    txt(s, 2, 49, val, "value", 0)
    return s


def grid8(s, pids, y0, rh, vals, ph, chosen, touched=-1):
    for i, pid in enumerate(pids):
        x, y = (i % 4) * 32 + 1, y0 + (i // 4) * (rh + 2)
        icon(s, pid, x, y, 30, rh, vals[i], ph, chosen[i])
        if i == touched:
            s.inv(x - 1, y - 1, 32, rh + 2)


def steps_row(s, y=53, play=-1):
    pat = "n...n..%n.k.c.n."
    for i, c in enumerate(pat):
        x = i * 8 + 2
        if c == "n":
            s.fill(x, y + 1, 5, 5)
        elif c == "%":
            s.dith(x, y + 1, 5, 5)
        elif c == "c":
            s.rect(x, y + 1, 5, 5)
        elif c == "k":
            s.line(x, y + 5, x + 2, y + 1)
            s.line(x + 2, y + 1, x + 4, y + 5)
            s.hl(x, y + 5, 5)
        else:
            s.set(x + 2, y + 3)
        if i == play:
            s.hl(x - 1, y + 7, 7)
        if i % 4 == 0:
            s.hl(x, y + 9, 5)


def chain_rest(pids, ph, mod_i=0):
    """The chain at rest: the device's main page as eight icons, no words; the steps row under them."""
    s = Scr()
    vals = [0.5] * 8
    vals[mod_i] = 0.5 + 0.35 * math.sin(ph * 2 * math.pi)
    grid8(s, pids, 1, 23, vals, ph, [0] * 8)
    steps_row(s, play=int(ph * 16))
    return s


def page_rest(pids, name, cur, n, ph, chosen=None, mod_i=-1):
    """Inside a device: the page marks, the page's icons, its name in the name slot. No track number."""
    s = Scr()
    marks(s, n, cur)
    vals = [0.55] * len(pids)
    if mod_i >= 0:
        vals[mod_i] = 0.5 + 0.35 * math.sin(ph * 2 * math.pi)
    grid8(s, pids, 6, 19, vals, ph, chosen or [0] * len(pids))
    txt(s, 1, 49, name, "name")
    return s


def marks(s, n, cur, y=1):
    seg = (W - (n - 1) * 2) // n
    for i in range(n):
        x = i * (seg + 2)
        s.hl(x, y, seg)
        if i == cur:
            s.hl(x, y - 1, seg)
            s.hl(x, y + 1, seg)


def filter_scene(ph):
    """FILTER as the unit draws it now (core/ui.c draw_scene): one filter of spaced bars beside its envelope. The
    bars follow the cutoff as the envelope sweeps it, a fixed tick where the knob has it, a dot where the envelope
    takes it; a box rides the envelope with the newest note. Page marks on top, the page's name in its slot."""
    from screens import filter_bars, env_shape
    s = Scr()
    marks(s, 5, 2)
    a, d, su, r = 0.05, 0.35, 0.3, 0.4
    gate = ph < 0.7                                     # a note held for 70 % of the loop, then let go
    if ph < 0.08:
        lvl, stage = ph / 0.08, 0
    elif gate:
        lvl, stage = su + (1 - su) * math.exp(-(ph - 0.08) * 12), 1
    else:
        lvl, stage = su * math.exp(-(ph - 0.7) * 10), 2
    cut_set, amt = 0.35, 0.3
    filter_bars(s, 1, 10, 62, 33, min(1.0, cut_set + amt * 0.76 * lvl), 0.55, 0)
    n = 62 // 3
    s.vl(1 + int(cut_set * (n - 1)) * 3, 7, 2)          # the knob's cutoff: a fixed tick
    s.fill(1 + int(min(1.0, cut_set + amt * 0.76) * (n - 1)) * 3, 4, 2, 2)   # where the envelope takes it
    env_shape(s, 68, 9, 58, 32, a, d, su, r)
    x, y, w, h = 68, 9, 58, 32                          # the box riding the envelope, as core/ui.c places it
    hold, seg, base = w // 6, (w - 6 - w // 6) // 3, y + h - 1
    x1 = x + 2 + int(math.sqrt(a) * seg)
    x2 = x1 + 2 + int(math.sqrt(d) * seg)
    x3 = x2 + hold
    x4 = x3 + 2 + int(math.sqrt(r) * seg)
    if stage == 0:
        px = x + int(lvl * (x1 - x))
    elif stage == 1:
        f = (1 - lvl) / (1 - su)
        px = x2 + hold // 2 if f > 0.97 else x1 + int(f * (x2 - x1))
    else:
        px = x3 + int((1 - lvl / su) * (x4 - x3))
    py = base - int(lvl * (h - 1))
    if not (stage == 2 and lvl < 0.01):
        s.fill(px - 2, py - 2, 5, 5, 0)
        s.rect(px - 2, py - 2, 5, 5)
    txt(s, 1, 49, "FILTER", "name")
    return s


def env_stage(ph, su):
    """a note held for 70 % of the loop, then let go: the envelope's stage and level"""
    if ph < 0.08:
        return ph / 0.08, 0
    if ph < 0.7:
        return su + (1 - su) * math.exp(-(ph - 0.08) * 12), 1
    return su * math.exp(-(ph - 0.7) * 10), 2


def env_rider(s, x, y, w, h, a, d, su, r, lvl, stage):
    """the box that rides an envelope where the newest note is in it, placed as core/ui.c places it"""
    hold, seg, base = w // 6, (w - 6 - w // 6) // 3, y + h - 1
    x1 = x + 2 + int(math.sqrt(a) * seg)
    x2 = x1 + 2 + int(math.sqrt(d) * seg)
    x3 = x2 + hold
    x4 = x3 + 2 + int(math.sqrt(r) * seg)
    if stage == 2 and lvl < 0.01:
        return
    if stage == 0:
        px = x + int(lvl * (x1 - x))
    elif stage == 1:
        f = (1 - lvl) / (1 - su)
        px = x2 + hold // 2 if f > 0.97 else x1 + int(f * (x2 - x1))
    else:
        px = x3 + int((1 - lvl / su) * (x4 - x3))
    py = base - int(lvl * (h - 1))
    s.fill(px - 2, py - 2, 5, 5, 0)
    s.rect(px - 2, py - 2, 5, 5)


def amp_scene(ph):
    """AMP as the unit draws it: one wide envelope, the box riding it with the note, the level beside it as a bar
    that the note's loudness fills. Page marks on top, the page's name in its slot."""
    from screens import env_shape
    s = Scr()
    marks(s, 5, 3)
    a, d, su, r = 0.1, 0.4, 0.5, 0.45
    lvl, stage = env_stage(ph, su)
    env_shape(s, 2, 9, 100, 32, a, d, su, r)
    env_rider(s, 2, 9, 100, 32, a, d, su, r, lvl, stage)
    lv = int(0.75 * 32)
    s.rect(112, 8, 12, 35)
    s.fill(114, 41 - lv, 8, lv)
    out = int(lvl * lv)                                 # the note's loudness now, inside the level
    s.fill(116, 41 - out, 4, out, 0) if out > 1 else None
    txt(s, 1, 49, "AMP", "name")
    return s


def page_flash(name, cur, n):
    """The page turned while a knob is touched: the page's name and where it is, for 0.6 s; then the knob again."""
    s = Scr()
    marks(s, n, cur)
    txt(s, 1, 20, name, "name")
    for i in range(n):
        (s.fill if i == cur else s.rect)(1 + i * 14, 42, 10, 10)
    return s


def track_pop(num, typ, preset, off=0):
    """A track chosen: its number large in a box, its type, its preset (slides inside its slot when longer)."""
    s = Scr()
    s.fill(0, 0, 40, 64)
    t = str(num)
    txt(s, (40 - w5(t, 3)) // 2, 22, t, "num", 0)
    txt(s, 44, 4, typ, "side")
    # the preset: a slot of 6 characters; a longer name slides through it and never leaves it
    slot = Scr()
    slot.t5(-off, 0, preset, 1, 2)
    for j in range(14):
        for i in range(ROLES["side"][1]):
            if slot.get(i, j):
                s.set(44 + i, 26 + j)
    type_glyph(s, typ, 44, 46)
    return s


def type_glyph(s, typ, x, y):
    if typ == "SYNTH":
        wave(s, x, y, 40, 14, 0, 0, cycles=2)
    elif typ == "SAMPLR":
        for i in range(0, 40, 2):
            a = int(6 * abs(math.sin(i * 0.4)) * (1 - i / 50.0))
            s.vl(x + i, y + 7 - a, 2 * a + 1)
    else:
        for r in range(2):
            for c in range(5):
                (s.fill if (r + c) % 3 == 0 else s.rect)(x + c * 8, y + r * 8, 6, 6)


def held_step(ph):
    """A step held at the chain: the icons stay, shorter; the step card in its two slots; the steps row."""
    s = Scr()
    grid8(s, PARAMS["SUB  MAIN"], 1, 15, [0.5] * 8, ph, [0] * 8)
    s.fill(0, 35, 38, 16)
    txt(s, 2, 36, "S4", "step", 0)
    txt(s, 40, 36, "C MAJ", "notes")
    steps_row(s)
    s.rect(3 * 8, 53, 9, 9)
    return s


# ------------------------------------------------------------------ writing the pictures
def frame_img(s, k=K):
    im = Image.new("P", (W * k, H * k), 0)
    im.putpalette(list(BG) + list(FG) + [0] * 762)
    px = im.load()
    for y in range(H):
        for x in range(W):
            if s.get(x, y):
                for j in range(k):
                    for i in range(k):
                        px[x * k + i, y * k + j] = 1
    return im


def gif(name, frames, ms=100):
    ims = [frame_img(f) for f in frames]
    path = os.path.join(OUT, name + ".gif")
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=ms, loop=0, disposal=1)
    return path


def sheet(name, title, pids, n=16, ms=110):
    """every icon of a page, small (as on the page) and large (as on the card), all moving"""
    frames = []
    rows = len(pids)
    cw, ch = 300, 36
    for f in range(n):
        ph = f / float(n)
        im = Image.new("P", (cw * 2 + 16, rows * (ch * 2 + 8) + 8), 0)
        im.putpalette(list(BG) + list(FG) + [0] * 762)
        for r, pid in enumerate(pids):
            s = Scr()
            nch = CHOICES.get(pid, 0)
            ch_i = (f * nch // n) if nch else 0
            v = 0.5 + 0.4 * math.sin(ph * 2 * math.pi)
            icon(s, pid, 1, 1, 30, 21, v, ph, ch_i)
            icon(s, pid, 36, 1, 88, 26, v, ph, ch_i)
            sub = frame_img(s, 2).crop((0, 0, 128 * 2, 30 * 2))
            im.paste(sub, (8, 8 + r * (ch * 2 + 8)))
        frames.append(im)
    path = os.path.join(OUT, name + ".gif")
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=ms, loop=0, disposal=1)
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    N = 24
    sweep = lambda f, a=0.35, c=0.5: c + a * math.sin(f / float(N) * 2 * math.pi)
    # the knob cards
    gif("card-cutoff", [card("CUTOFF", sweep(f), f / N) for f in range(N)])
    gif("card-function", [card("FUNCTION", 0, f / N, chosen=3) for f in range(N)])
    gif("card-ratchet", [card("RATCHET", (f // 3) / 7.0, f / N) for f in range(N)])
    gif("card-tune", [card("TUNE", 0.5 - 7 / 48., f / N) for f in range(N)])
    gif("card-chance", [card("CHANCE", 0.62, f / N) for f in range(N)])
    gif("card-condition", [card("CONDITION", 0, f / N, chosen=3) for f in range(N)])
    gif("card-direction", [card("DIRECTION", 0, f / N, chosen=2) for f in range(N)])
    gif("card-level", [card("MIX LEVEL", 0.76, f / N) for f in range(N)])
    gif("card-send", [card("SEND 1", 0.32, f / N) for f in range(N)])
    # rest views
    gif("rest-chain", [chain_rest(PARAMS["SUB  MAIN"], f / N) for f in range(N)])
    gif("rest-trig", [page_rest(PARAMS["SEQ  TRIG"], "TRIG", 0, 2, f / N, chosen=[0, 0, 0, 1, 3, 0, 0, 1])
                      for f in range(N)])
    gif("rest-amp", [amp_scene(f / 32.) for f in range(32)], ms=80)
    gif("rest-filter", [filter_scene(f / 32.) for f in range(32)], ms=80)
    gif("rest-held", [held_step(f / N) for f in range(N)])
    # the page turned while a knob is touched: the card, the page for 0.6 s, the card of the new page's knob
    flow = ([card("CUTOFF", 0.5, f / 10.) for f in range(10)] + [page_flash("AMP", 3, 5)] * 6
            + [card("ATTACK", 0.25, f / 10.) for f in range(14)])
    gif("flow-page-turn", flow)
    # the track popup, its preset sliding through its slot
    pre = "WARM PAD 2"
    slide = list(range(0, w5(pre, 2) - ROLES["side"][1] + 1, 4))
    gif("pop-track", [track_pop(3, "SYNTH", pre, 0)] * 8 + [track_pop(3, "SYNTH", pre, o) for o in slide]
        + [track_pop(3, "SYNTH", pre, slide[-1])] * 8)
    gif("pop-track-kit", [track_pop(5, "KIT", "808 CORE", 0)] * 6 + [track_pop(5, "KIT", "808 CORE", o)
                                                                      for o in (4, 8, 12)] * 2)
    # the icon sheets
    for key, pids in PARAMS.items():
        sheet("icons-" + key.lower().replace("  ", "-").replace(" ", "-"), key, pids)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
