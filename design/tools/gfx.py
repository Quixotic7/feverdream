"""Drawing for the mock-ups: a 128 x 64 one-bit screen with lines, shapes and one 5 x 7 face (fonts.json holds
Ableton Move Designer's Pixel 5x7). Used by screens.py and mock.py."""
import base64
import json
import math
import os

from PIL import Image

W, H = 128, 64
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
F5 = json.load(open(os.path.join(HERE, "fonts.json")))["f5"]


# ------------------------------------------------------------------ a 1-bit screen
class Scr:
    def __init__(self):
        self.p = bytearray(W * H)

    def set(self, x, y, v=1):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H:
            self.p[y * W + x] = v

    def get(self, x, y):
        return self.p[y * W + x] if 0 <= x < W and 0 <= y < H else 0

    def hl(self, x, y, w, v=1):
        for i in range(w):
            self.set(x + i, y, v)

    def vl(self, x, y, h, v=1):
        for i in range(h):
            self.set(x, y + i, v)

    def rect(self, x, y, w, h, v=1):
        self.hl(x, y, w, v)
        self.hl(x, y + h - 1, w, v)
        self.vl(x, y, h, v)
        self.vl(x + w - 1, y, h, v)

    def fill(self, x, y, w, h, v=1):
        for j in range(h):
            self.hl(x, y + j, w, v)

    def inv(self, x, y, w, h):
        for j in range(h):
            for i in range(w):
                self.set(x + i, y + j, 1 - self.get(x + i, y + j))

    def dith(self, x, y, w, h, k=2):
        for j in range(h):
            for i in range(w):
                if (x + i + y + j) % k == 0:
                    self.set(x + i, y + j, 1)

    def dots(self, x, y, w, step=2, v=1):
        for i in range(0, w, step):
            self.set(x + i, y, v)

    def vdots(self, x, y, h, step=2, v=1):
        for i in range(0, h, step):
            self.set(x, y + i, v)

    def line(self, x0, y0, x1, y1, v=1):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.set(x0, y0, v)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def poly(self, pts, v=1):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], v)

    def circ(self, cx, cy, r, v=1):
        n = max(12, int(r * 8))
        pts = [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]
        self.poly(pts, v)

    def disc(self, cx, cy, r, v=1):
        for j in range(-int(r) - 1, int(r) + 2):
            for i in range(-int(r) - 1, int(r) + 2):
                if i * i + j * j <= r * r + 0.3:
                    self.set(cx + i, cy + j, v)

    # --- text: one 5 x 7 face, drawn k times its size (advance 6 * k). No smaller face: docs/DESIGN.md 3.1
    def t5(self, x, y, s, v=1, k=1):
        for ch in s:
            g = F5[ord(ch) - 32] if 32 <= ord(ch) <= 126 else F5[0]
            for c in range(5):
                for r in range(8):
                    if g[c] & (1 << r):
                        self.fill(x + c * k, y + r * k, k, k, v)
            x += 6 * k
        return x

    def t5c(self, xc, y, s, v=1, k=1):
        return self.t5(xc - w5(s, k) // 2, y, s, v, k)

    def b64(self):
        out = bytearray(W * H // 8)
        for i, v in enumerate(self.p):
            if v:
                out[i >> 3] |= 0x80 >> (i & 7)
        return base64.b64encode(bytes(out)).decode()

    def image(self, k=4):
        im = Image.new("RGB", (W * k + 16, H * k + 16), (10, 10, 12))
        px = im.load()
        for y in range(H):
            for x in range(W):
                if self.p[y * W + x]:
                    for j in range(k):
                        for i in range(k):
                            px[8 + x * k + i, 8 + y * k + j] = (238, 240, 232)
        return im


def w5(s, k=1):
    return (len(s) * 6 - 1) * k


