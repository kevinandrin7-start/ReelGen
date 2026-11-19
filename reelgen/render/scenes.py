"""The five scene templates. Each draws one frame at local time lt of a scene lasting D seconds."""
from __future__ import annotations

import math

from .. import config
from ..models import DefineScene, HookScene, PayoffScene, ProblemScene, StepsScene
from . import icons
from .canvas import (AMBER, CARD, CARD_HI, DARK, MUTED, RED, RED_BG, RED_BG2, TEAL, TEAL_BG, WHITE, Ctx,
                     back, clamp, p)

MAXW = 900  # usable text width (keeps 90px side margins)


def hook(c: Ctx, lt: float, D: float, s: HookScene):
    a1, a2 = p(lt, 0.1, 0.45), p(lt, 0.5, 0.45)
    size = min(c.fit(s.line1, "pb", 92, MAXW), c.fit(s.line2, "pb", 92, MAXW))
    c.text(540, 520 + 40 * (1 - a1), s.line1, "pb", size, WHITE, a1)
    c.text(540, 640 + 40 * (1 - a2), s.line2, "pb", size, AMBER, a2)
    if lt > 0.9:
        k = back((lt - 0.9) / 0.5)
        pul = 1 + 0.04 * math.sin((lt - 1.4) * 6) if lt > 1.4 else 1
        r = 190 * k * pul
        c.circle(540, 1010, r + 26, fill=(32, 30, 50), a=clamp(k))
        c.circle(540, 1010, r, outline=AMBER, w=10, a=clamp(k))
        icons.draw(c, s.icon, 540, 1010, lt - 0.9, clamp(k), (32, 30, 50), 1.6 * clamp(k, 0.01, 1.1))
    a3 = p(lt, min(2.0, D - 0.8), 0.4)
    c.text_fit(540, 1330 + 20 * (1 - a3), s.subline, "is", 46, WHITE, MAXW, a3)
    c.line([(380, 1395), (700, 1395)], TEAL, 6, a3)


def problem(c: Ctx, lt: float, D: float, s: ProblemScene):
    a0 = p(lt, 0.0, 0.35)
    c.text(540, 330, "THE PROBLEM", "is", 32, RED, a0)
    c.text_fit(540, 405, s.headline, "pb", 58, WHITE, MAXW, a0)
    pains = s.pains[:3]
    ch, gap, y0 = 190, 40, 500
    step = max(0.35, (D * 0.55) / max(1, len(pains)))
    for i, pain in enumerate(pains):
        st = 0.4 + i * step
        if lt < st:
            continue
        a = p(lt, st, 0.35)
        y = y0 + i * (ch + gap)
        dx = 50 * (1 - a)
        c.rrect(90 + dx, y, 990 + dx, y + ch, 32, fill=CARD, a=a)
        icons.draw(c, pain.icon, 200 + dx, y + ch / 2, lt - st, a, CARD, 0.85)
        lines, size = c.wrap(pain.text, "is", 42, 640)
        for j, ln in enumerate(lines):
            yy = y + ch / 2 + (j - (len(lines) - 1) / 2) * size * 1.25
            c.text(300 + dx, yy, ln, "is", size, WHITE, a, anchor="lm", base=CARD)
    tags = s.tags[:3]
    tstart = 0.4 + len(pains) * step
    ty = y0 + len(pains) * (ch + gap) + 40
    n = len(tags)
    tw = 290 if n == 3 else 360
    xs = [540 + (i - (n - 1) / 2) * (tw + 35) for i in range(n)]
    for i, (tg, x) in enumerate(zip(tags, xs)):
        st = tstart + i * 0.3
        if lt < st:
            continue
        k = back((lt - st) / 0.35)
        aa = clamp(k)
        wdt = tw * (0.6 + 0.4 * clamp(k))
        c.rrect(x - wdt / 2, ty, x + wdt / 2, ty + 90, 45, fill=RED_BG, outline=RED, w=4, a=aa)
        c.cross(x - tw / 2 + 50, ty + 45, 22, RED, 6, aa, base=RED_BG)
        c.text_fit(x + 22, ty + 45, tg.upper(), "ib", 30, RED, tw - 110, aa, base=RED_BG)


def define(c: Ctx, lt: float, D: float, s: DefineScene):
    a0 = p(lt, 0.0, 0.3)
    c.text_fit(540, 560, s.intro, "pm", 56, MUTED, MAXW, a0)
    if lt > 0.25:
        k = back((lt - 0.25) / 0.5)
        size = c.fit(s.term, "pb", 300, 940, min_size=80)
        c.text(540, 790, s.term, "pb", size * clamp(k, 0, 1.2) + 1, TEAL, clamp(k))
    y = 1040
    if s.expansion:
        a1 = p(lt, 1.0, 0.4)
        lines, size = c.wrap(s.expansion, "pb", 58, MAXW, max_lines=2, min_size=34)
        for j, ln in enumerate(lines):
            x = 540 - c.tw(ln, "pb", size) / 2
            for w in ln.split():
                # highlight the initial letter of each word (and hyphen part) in teal
                parts = w.split("-")
                for pi, part in enumerate(parts):
                    if part:
                        c.text(x, y, part[0], "pb", size, TEAL, a1, anchor="lm")
                        x += c.tw(part[0], "pb", size)
                    rest = part[1:] + ("-" if pi < len(parts) - 1 else "")
                    c.text(x, y, rest, "pb", size, WHITE, a1, anchor="lm")
                    x += c.tw(rest, "pb", size)
                x += c.tw(" ", "pb", size)
            y += size * 1.35
    a3 = p(lt, min(1.9, D - 1.0), 0.4)
    ytop = max(y + 60, 1250)
    c.rrect(160, ytop, 920, ytop + 110, 55, fill=TEAL_BG, outline=TEAL, w=4, a=a3)
    c.text_fit(540, ytop + 55, s.analogy, "is", 42, WHITE, 700, a3, base=TEAL_BG)


def steps(c: Ctx, lt: float, D: float, s: StepsScene):
    a0 = p(lt, 0.0, 0.3)
    c.text_fit(540, 315, s.label.upper(), "is", 32, TEAL, MAXW, a0)
    items = s.steps[:5]
    n = max(1, len(items))
    STEP = (D - 1.4) / n
    avail = 1560 - 390
    gap = 40
    ch = min(196, (avail - gap * (n - 1)) / n)
    y0 = 390 + (avail - (ch * n + gap * (n - 1))) / 2
    for i, st_item in enumerate(items):
        st = 0.3 + i * STEP
        if lt < st:
            continue
        a = p(lt, st, 0.35)
        active = (st <= lt < st + STEP) or (i == n - 1)
        yt = y0 + i * (ch + gap)
        dx = -60 * (1 - a)
        base = CARD_HI if active else CARD
        dim = 1.0 if active else 0.62
        if i > 0:
            c.arrow_down(165, yt - gap + 4, yt - 2, TEAL if active else (70, 80, 130), a)
        c.rrect(90 + dx, yt, 990 + dx, yt + ch, 32, fill=base, outline=TEAL if active else None, w=4, a=a)
        numbase = TEAL if active else (60, 72, 120)
        c.circle(165 + dx, yt + ch / 2, 40, fill=numbase, a=a, base=base)
        c.text(165 + dx, yt + ch / 2 + 2, str(i + 1), "pb", 44, (10, 20, 30) if active else WHITE, a, base=numbase)
        c.text_fit(235 + dx, yt + ch / 2 - 30, st_item.title, "pb", 44, WHITE, 520, a * dim, anchor="lm", base=base)
        c.text_fit(235 + dx, yt + ch / 2 + 32, st_item.sub, "ir", 31, (200, 210, 235) if active else MUTED, 520,
                   a * dim, anchor="lm", base=base)
        icons.draw(c, st_item.icon, 870 + dx, yt + ch / 2, lt - st, a * dim, base, min(1.0, ch / 196))
    fa = p(lt, min(0.3 + (n - 1) * STEP + 1.0, D - 0.8), 0.4)
    c.rrect(140, 1590, 940, 1690, 50, fill=TEAL_BG, a=fa)
    c.text_fit(540, 1640, s.result, "is", 38, WHITE, 740, fa, base=TEAL_BG)


def payoff(c: Ctx, lt: float, D: float, s: PayoffScene):
    a1, a2, a3 = p(lt, 0.0, 0.35), p(lt, 0.3, 0.4), p(lt, 0.6, 0.35)
    c.text_fit(540, 440 + 30 * (1 - a1), s.line1, "pb", 84, WHITE, MAXW, a1)
    c.text_fit(540, 560 + 30 * (1 - a2), s.highlight, "pb", 80, TEAL, MAXW, a2)
    if s.line3:
        c.text_fit(540, 670 + 30 * (1 - a3), s.line3, "pb", 84, WHITE, MAXW, a3)
    b1, b2 = p(lt, 1.0, 0.4), p(lt, 1.3, 0.4)
    c.rrect(110, 830, 970, 960, 36, fill=RED_BG2, a=b1)
    c.cross(185, 895, 34, RED, 8, b1, RED_BG2)
    c.text_fit(240, 870, s.bad.title, "pb", 42, WHITE, 700, b1, anchor="lm", base=RED_BG2)
    c.text_fit(240, 922, s.bad.sub, "ir", 32, (230, 170, 175), 700, b1, anchor="lm", base=RED_BG2)
    c.rrect(110, 990, 970, 1120, 36, fill=TEAL_BG, a=b2)
    c.check(185, 1055, 44, TEAL, 9, b2, TEAL_BG)
    c.text_fit(240, 1030, s.good.title, "pb", 42, WHITE, 700, b2, anchor="lm", base=TEAL_BG)
    c.text_fit(240, 1082, s.good.sub, "ir", 32, (170, 230, 220), 700, b2, anchor="lm", base=TEAL_BG)
    cta_t = min(2.2, max(1.6, D - 1.6))
    if lt > cta_t:
        k = back((lt - cta_t) / 0.45)
        aa = clamp(k)
        wd = 380 * clamp(k, 0, 1.08)
        c.rrect(540 - wd, 1260, 540 + wd, 1380, 60, fill=AMBER, a=aa)
        c.text_fit(540, 1320, config.CTA_TEXT, "pb", 44, DARK, 700, aa, base=AMBER)
    a4 = p(lt, cta_t + 0.5, 0.4)
    c.text(540, 1450, "Save this for later", "is", 36, MUTED, a4)


TEMPLATES = {"hook": hook, "problem": problem, "define": define, "steps": steps, "payoff": payoff}
