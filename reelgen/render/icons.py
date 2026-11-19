"""Simple shape-drawn icons (no emoji fonts, no logos). Each fits in a ~140x140 box
centred on (cx, cy) and may animate with local time t."""
from __future__ import annotations

import math

from .canvas import (AMBER, BUBBLE, MUTED, RED, TEAL, TEAL_BG, VIOLET, WHITE, CARD, Ctx, back, clamp,
                     mix, p, sc)

PAPER = (236, 240, 252)
DB = (44, 40, 92)


def draw(c: Ctx, name: str, cx: float, cy: float, t: float, a: float, base, k: float = 1.0):
    fn = ICONS.get(name, _spark)
    fn(c, cx, cy, t, a, base, k)


def _chat(c, cx, cy, t, a, base, k):
    c.rrect(cx - 70 * k, cy - 50 * k, cx + 70 * k, cy + 35 * k, 24 * k, fill=BUBBLE, a=a, base=base)
    c.poly([(cx - 40 * k, cy + 30 * k), (cx - 10 * k, cy + 30 * k), (cx - 45 * k, cy + 60 * k)], BUBBLE, a, base)
    for i, dx in enumerate((-35, 0, 35)):
        bob = 6 * math.sin(t * 8 - i)
        c.circle(cx + dx * k, cy - 8 * k + bob, 10 * k, fill=WHITE, a=a, base=BUBBLE)


def _robot(c, cx, cy, t, a, base, k):
    c.line([(cx, cy - 75 * k), (cx, cy - 55 * k)], VIOLET, 5, a, base)
    c.circle(cx, cy - 80 * k, 9 * k, fill=VIOLET, a=a, base=base)
    c.rrect(cx - 70 * k, cy - 55 * k, cx + 70 * k, cy + 55 * k, 22 * k, fill=CARD, outline=VIOLET, w=4, a=a, base=base)
    blink = 0.15 if (t % 1.6) < 0.12 else 1
    for ex in (-28, 28):
        c.rrect(cx + (ex - 10) * k, cy - (10 + 12 * blink) * k, cx + (ex + 10) * k, cy - (10 - 12 * blink) * k,
                6 * k, fill=VIOLET, a=a, base=CARD)
    c.line([(cx - 25 * k, cy + 25 * k), (cx + 25 * k, cy + 25 * k)], VIOLET, 4, a, CARD)


def _database(c, cx, cy, t, a, base, k):
    w2, top, bot = 65 * k, cy - 50 * k, cy + 50 * k
    c.rrect(cx - w2, top, cx + w2, bot, 8, fill=DB, a=a, base=base)
    c.ellipse(cx - w2, bot - 18 * k, cx + w2, bot + 18 * k, DB, a, base)
    c.ellipse(cx - w2, top - 18 * k, cx + w2, top + 18 * k, VIOLET, a, base)
    for i, (dx, dy) in enumerate([(-35, -5), (-5, 20), (25, -15), (35, 25), (-25, 30)]):
        col = TEAL if (i == 2 and t > 0.8) else (130, 120, 200)
        c.circle(cx + dx * k, cy + dy * k, 7 * k, fill=col, a=a, base=DB)
    sy = top + 10 + (bot - top) * ((t * 1.3) % 1.0)
    c.line([(cx - w2 - 10, sy), (cx + w2 + 10, sy)], TEAL, 4, a * 0.9, base)


def _docs(c, cx, cy, t, a, base, k):
    for i in range(3):
        ai = a * p(t, i * 0.2, 0.3)
        ox, oy = cx - 55 * k + i * 20 * k, cy - 55 * k + i * 22 * k
        c.rrect(ox, oy, ox + 100 * k, oy + 72 * k, 10, fill=PAPER, a=ai, base=base)
        for ln in range(3):
            c.line([(ox + 14 * k, oy + (16 + ln * 17) * k), (ox + (86 - ln * 18) * k, oy + (16 + ln * 17) * k)],
                   (150, 160, 190), 4, ai, PAPER)


def _check(c, cx, cy, t, a, base, k):
    kk = back(t / 0.5)
    r = 56 * k * clamp(kk, 0, 1.15)
    c.circle(cx, cy, r, fill=(20, 80, 70), outline=TEAL, w=5, a=a, base=base)
    c.check(cx, cy, 54 * k * clamp(kk), TEAL, 10, a, (20, 80, 70))


def _cross(c, cx, cy, t, a, base, k):
    kk = back(t / 0.5)
    r = 56 * k * clamp(kk, 0, 1.15)
    c.circle(cx, cy, r, fill=(70, 30, 44), outline=RED, w=5, a=a, base=base)
    c.cross(cx, cy, 46 * k * clamp(kk), RED, 9, a, (70, 30, 44))


def _numbers(c, cx, cy, t, a, base, k):
    nums = ["0.21", "-0.84", "0.47", "0.09"]
    n = min(len(nums), int(len(nums) * clamp(t / 1.0)) + 1)
    for i, s in enumerate(nums[:n]):
        c.text(cx, cy - 66 * k + i * 44 * k, s, "mono", 30 * k, AMBER, a, base=base)
    c.text(cx - 82 * k, cy, "[", "pm", 140 * k, MUTED, a, base=base)
    c.text(cx + 82 * k, cy, "]", "pm", 140 * k, MUTED, a, base=base)


def _search(c, cx, cy, t, a, base, k):
    ox = 10 * math.sin(t * 3) * k
    c.circle(cx - 12 * k + ox, cy - 12 * k, 42 * k, outline=TEAL, w=9, a=a, base=base)
    c.line([(cx + 18 * k + ox, cy + 18 * k), (cx + 58 * k + ox, cy + 58 * k)], TEAL, 14, a, base)


def _gear(c, cx, cy, t, a, base, k):
    rot = t * 1.5
    for i in range(8):
        ang = rot + i * math.pi / 4
        x, y = cx + math.cos(ang) * 50 * k, cy + math.sin(ang) * 50 * k
        c.circle(x, y, 14 * k, fill=MUTED, a=a, base=base)
    c.circle(cx, cy, 48 * k, fill=MUTED, a=a, base=base)
    c.circle(cx, cy, 20 * k, fill=base, a=a, base=base)


def _bulb(c, cx, cy, t, a, base, k):
    glow = 0.5 + 0.5 * math.sin(t * 4)
    c.circle(cx, cy - 15 * k, (52 + 8 * glow) * k, fill=mix(AMBER, 0.25, base), a=a, base=base)
    c.circle(cx, cy - 15 * k, 42 * k, fill=AMBER, a=a, base=base)
    c.rrect(cx - 20 * k, cy + 25 * k, cx + 20 * k, cy + 55 * k, 6, fill=MUTED, a=a, base=base)


def _lock(c, cx, cy, t, a, base, k):
    c.arc(cx, cy - 20 * k, 32 * k, 180, 360, MUTED, 10, a, base)
    c.line([(cx - 32 * k, cy - 20 * k), (cx - 32 * k, cy)], MUTED, 10, a, base)
    c.line([(cx + 32 * k, cy - 20 * k), (cx + 32 * k, cy)], MUTED, 10, a, base)
    c.rrect(cx - 52 * k, cy - 5 * k, cx + 52 * k, cy + 65 * k, 12, fill=AMBER, a=a, base=base)
    c.circle(cx, cy + 28 * k, 9 * k, fill=(60, 40, 10), a=a, base=AMBER)


def _chart(c, cx, cy, t, a, base, k):
    hs = [0.4, 0.65, 0.5, 0.95]
    for i, h in enumerate(hs):
        hh = 110 * k * h * p(t, i * 0.15, 0.4)
        x0 = cx - 70 * k + i * 37 * k
        c.rrect(x0, cy + 55 * k - hh, x0 + 26 * k, cy + 55 * k, 5, fill=TEAL if i == 3 else MUTED, a=a, base=base)


def _cloud(c, cx, cy, t, a, base, k):
    dy = 4 * math.sin(t * 2)
    for (dx, yy, r) in [(-35, 10, 32), (0, -10, 42), (38, 8, 30)]:
        c.circle(cx + dx * k, cy + yy * k + dy, r * k, fill=(200, 210, 240), a=a, base=base)
    c.rrect(cx - 65 * k, cy + 5 * k + dy, cx + 65 * k, cy + 40 * k + dy, 16, fill=(200, 210, 240), a=a, base=base)


def _code(c, cx, cy, t, a, base, k):
    c.rrect(cx - 72 * k, cy - 52 * k, cx + 72 * k, cy + 52 * k, 14, fill=(16, 20, 40), outline=MUTED, w=3, a=a, base=base)
    c.text(cx, cy, "</>", "mono", 46 * k, TEAL, a, base=(16, 20, 40))


def _user(c, cx, cy, t, a, base, k):
    c.circle(cx, cy - 25 * k, 28 * k, fill=BUBBLE, a=a, base=base)
    c.rrect(cx - 52 * k, cy + 10 * k, cx + 52 * k, cy + 62 * k, 26, fill=BUBBLE, a=a, base=base)


def _globe(c, cx, cy, t, a, base, k):
    r = 55 * k
    c.circle(cx, cy, r, outline=TEAL, w=5, a=a, base=base)
    c.line([(cx - r, cy), (cx + r, cy)], TEAL, 4, a, base)
    w = abs(math.cos(t * 1.5)) * r
    c.d.ellipse([sc(cx - w), sc(cy - r), sc(cx + w), sc(cy + r)], outline=mix(TEAL, a, base), width=int(sc(4)))


def _clock(c, cx, cy, t, a, base, k):
    r = 55 * k
    c.circle(cx, cy, r, fill=CARD, outline=AMBER, w=5, a=a, base=base)
    ang = t * 3
    c.line([(cx, cy), (cx + math.cos(ang) * 38 * k, cy + math.sin(ang) * 38 * k)], WHITE, 5, a, CARD)
    c.line([(cx, cy), (cx, cy - 26 * k)], AMBER, 6, a, CARD)


def _warning(c, cx, cy, t, a, base, k):
    s = 1 + 0.05 * math.sin(t * 6)
    c.poly([(cx, cy - 60 * k * s), (cx + 62 * k * s, cy + 48 * k * s), (cx - 62 * k * s, cy + 48 * k * s)], RED, a, base)
    c.text(cx, cy + 10 * k, "!", "pb", 70 * k, (60, 20, 30), a, base=RED)


def _brain(c, cx, cy, t, a, base, k):
    for (dx, dy, r) in [(-25, -20, 32), (22, -22, 30), (-30, 18, 30), (25, 20, 32), (0, 0, 30)]:
        c.circle(cx + dx * k, cy + dy * k, r * k, fill=VIOLET, a=a, base=base)
    for i in range(3):
        on = (int(t * 4) + i) % 3 == 0
        c.circle(cx + (-20 + i * 20) * k, cy, 6 * k, fill=WHITE if on else (120, 100, 200), a=a, base=VIOLET)


def _layers(c, cx, cy, t, a, base, k):
    for i in range(3):
        y = cy + (30 - i * 30) * k
        ai = a * p(t, i * 0.2, 0.3)
        col = [MUTED, VIOLET, TEAL][i]
        c.poly([(cx, y - 25 * k), (cx + 70 * k, y), (cx, y + 25 * k), (cx - 70 * k, y)], col, ai, base)


def _link(c, cx, cy, t, a, base, k):
    c.rrect(cx - 72 * k, cy - 22 * k, cx + 4 * k, cy + 22 * k, 22, outline=TEAL, w=8, a=a, base=base)
    c.rrect(cx - 4 * k, cy - 22 * k, cx + 72 * k, cy + 22 * k, 22, outline=AMBER, w=8, a=a, base=base)


def _spark(c, cx, cy, t, a, base, k):
    s = (1 + 0.08 * math.sin(t * 5)) * k
    pts = []
    for i in range(8):
        ang = i * math.pi / 4 - math.pi / 2
        r = 62 * s if i % 2 == 0 else 20 * s
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    c.poly(pts, AMBER, a, base)


ICONS = {
    "chat": _chat, "robot": _robot, "database": _database, "docs": _docs, "check": _check,
    "cross": _cross, "numbers": _numbers, "search": _search, "gear": _gear, "bulb": _bulb,
    "lock": _lock, "chart": _chart, "cloud": _cloud, "code": _code, "user": _user, "globe": _globe,
    "clock": _clock, "warning": _warning, "brain": _brain, "layers": _layers, "link": _link,
    "spark": _spark,
}
