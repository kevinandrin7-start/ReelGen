"""Drawing primitives and the channel's visual style (adapted from rag_reel.py).

Frames are drawn at SUPERSAMPLE x size and scaled down for smooth edges."""
from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from .. import config

W, H, S = config.W, config.H, config.SUPERSAMPLE

BG_TOP, BG_BOT = (10, 14, 30), (20, 26, 56)
BG = (14, 19, 40)
WHITE = (241, 245, 255)
MUTED = (148, 160, 196)
TEAL = (45, 212, 191)
AMBER = (251, 191, 36)
RED = (248, 113, 113)
VIOLET = (167, 139, 250)
CARD = (27, 34, 68)
CARD_HI = (34, 44, 90)
TEAL_BG = (20, 60, 64)
RED_BG = (70, 30, 44)
RED_BG2 = (52, 26, 40)
BUBBLE = (48, 62, 120)
DARK = (20, 20, 30)

F = config.FONTS_DIR
FONTS = {
    "pb": F / "Poppins-Bold.ttf",
    "pm": F / "Poppins-Medium.ttf",
    "ir": F / "Inter-Regular.otf",
    "is": F / "Inter-SemiBold.otf",
    "ib": F / "Inter-Bold.otf",
    "mono": F / "DejaVuSansMono-Bold.ttf",
}


@lru_cache(None)
def font(name: str, size: float):
    return ImageFont.truetype(str(FONTS[name]), max(1, int(size * S)))


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def back(x):
    x = clamp(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def p(t, start, dur=0.4):
    return ease((t - start) / dur)


def mix(c, a, base=BG):
    a = clamp(a)
    return tuple(int(base[i] + (c[i] - base[i]) * a) for i in range(3))


def sc(v):
    return v * S


def _make_bg():
    img = Image.new("RGB", (W * S, H * S))
    d = ImageDraw.Draw(img)
    for y in range(H * S):
        k = y / (H * S)
        d.line([(0, y), (W * S, y)], fill=tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * k) for i in range(3)))
    for gx in range(60, W, 60):
        for gy in range(60, H, 60):
            r = 1.6 * S
            d.ellipse([gx * S - r, gy * S - r, gx * S + r, gy * S + r], fill=(36, 44, 80))
    return img


_BASE = None


def base_bg():
    global _BASE
    if _BASE is None:
        _BASE = _make_bg()
    return _BASE


class Ctx:
    def __init__(self):
        self.img = base_bg().copy()
        self.d = ImageDraw.Draw(self.img)

    # ---- text ----
    def text(self, x, y, s, f, size, color, a=1.0, anchor="mm", base=BG):
        if a <= 0 or not s:
            return
        self.d.text((sc(x), sc(y)), s, font=font(f, size), fill=mix(color, a, base), anchor=anchor)

    def tw(self, s, f, size):
        return font(f, size).getlength(s) / S

    def fit(self, s, f, size, max_w, min_size=18):
        """Largest size <= size at which s fits in max_w."""
        while size > min_size and self.tw(s, f, size) > max_w:
            size -= 2
        return size

    def text_fit(self, x, y, s, f, size, color, max_w, a=1.0, anchor="mm", base=BG):
        self.text(x, y, s, f, self.fit(s, f, size, max_w), color, a, anchor, base)

    def wrap(self, s, f, size, max_w, max_lines=2, min_size=24):
        """Wrap into <= max_lines, shrinking font if needed. Returns (lines, size)."""
        while True:
            words, lines, cur = s.split(), [], ""
            for w in words:
                trial = (cur + " " + w).strip()
                if self.tw(trial, f, size) <= max_w or not cur:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            if (len(lines) <= max_lines and all(self.tw(l, f, size) <= max_w for l in lines)) or size <= min_size:
                return lines[:max_lines], size
            size -= 2

    # ---- shapes ----
    def rrect(self, x0, y0, x1, y1, r, fill=None, outline=None, w=0, a=1.0, base=BG):
        if a <= 0 or x1 <= x0 or y1 <= y0:
            return
        self.d.rounded_rectangle([sc(x0), sc(y0), sc(x1), sc(y1)], radius=sc(min(r, (x1 - x0) / 2, (y1 - y0) / 2)),
                                 fill=mix(fill, a, base) if fill else None,
                                 outline=mix(outline, a, base) if outline else None, width=int(sc(w)))

    def circle(self, x, y, r, fill=None, outline=None, w=0, a=1.0, base=BG):
        if a <= 0 or r <= 0:
            return
        self.d.ellipse([sc(x - r), sc(y - r), sc(x + r), sc(y + r)],
                       fill=mix(fill, a, base) if fill else None,
                       outline=mix(outline, a, base) if outline else None, width=int(sc(w)))

    def ellipse(self, x0, y0, x1, y1, fill, a=1.0, base=BG):
        if a <= 0:
            return
        self.d.ellipse([sc(x0), sc(y0), sc(x1), sc(y1)], fill=mix(fill, a, base))

    def arc(self, x, y, r, start, end, color, w, a=1.0, base=BG):
        if a <= 0:
            return
        self.d.arc([sc(x - r), sc(y - r), sc(x + r), sc(y + r)], start, end, fill=mix(color, a, base), width=int(sc(w)))

    def line(self, pts, color, w, a=1.0, base=BG):
        if a <= 0:
            return
        self.d.line([(sc(x), sc(y)) for x, y in pts], fill=mix(color, a, base), width=int(sc(w)), joint="curve")

    def poly(self, pts, color, a=1.0, base=BG):
        if a <= 0:
            return
        self.d.polygon([(sc(x), sc(y)) for x, y in pts], fill=mix(color, a, base))

    def check(self, x, y, s, color, w=8, a=1.0, base=BG):
        self.line([(x - s * .5, y), (x - s * .15, y + s * .35), (x + s * .5, y - s * .35)], color, w, a, base)

    def cross(self, x, y, s, color, w=7, a=1.0, base=BG):
        self.line([(x - s / 2, y - s / 2), (x + s / 2, y + s / 2)], color, w, a, base)
        self.line([(x - s / 2, y + s / 2), (x + s / 2, y - s / 2)], color, w, a, base)

    def arrow_down(self, x, y0, y1, color, a=1.0, w=6):
        if a <= 0:
            return
        self.line([(x, y0), (x, y1 - 12)], color, w, a)
        self.poly([(x - 13, y1 - 16), (x + 13, y1 - 16), (x, y1)], color, a)

    def done(self):
        return self.img.reduce(S)


def chrome(c: Ctx, t: float, total: float):
    """Brand label + progress bar on every frame (kept clear of Instagram's top UI)."""
    c.text(540, 190, config.CHANNEL_LABEL, "is", 26, MUTED, 1.0)
    c.rrect(240, 222, 840, 230, 4, fill=(40, 48, 88))
    c.rrect(240, 222, 240 + 600 * clamp(t / total), 230, 4, fill=TEAL)


def pulse(t, speed=6, amt=0.04):
    return 1 + amt * math.sin(t * speed)
