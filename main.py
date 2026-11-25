#!/usr/bin/env python3
"""The World in One Day -- Wednesday 25 November 2026.

Draws a newspaper-style front page (1024x1024 PNG) summing up the day's
world news in eight stories. Python 3.13 standard library only, no network.
Deterministic: the same bytes are written on every run.

Usage: MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 228)      # warm newsprint
PANEL = (255, 253, 247)      # panel paper
INK = (25, 23, 19)           # near-black ink
RED = (163, 22, 33)          # masthead accent
ORANGE = (198, 96, 18)       # flame / highlight
BLUE = (31, 78, 121)
GREEN = (46, 107, 52)
PURPLE = (91, 45, 142)
TEAL = (14, 107, 122)
DARKRED = (139, 30, 30)
GOLD = (146, 104, 20)
GREY = (110, 105, 95)

# ------------------------------------------------- 5x7 bitmap font (authored here)
# Each glyph is 7 rows of 5 cells; '#' is a set pixel.
FONT = {
    'A': ("..#..", ".#.#.", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '(': ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ')': ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    '%': ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    '*': (".....", "#...#", ".#.#.", "#####", ".#.#.", "#...#", "....."),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
}


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        # Bresenham
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=2):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d <= r * r:
                    self.set(xx, yy, c)

    def triangle(self, x0, y0, x1, y1, x2, y2, c):
        # filled triangle via scanline spans
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return
        def edge_x(y, p, q):
            if q[1] == p[1]:
                return p[0]
            return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])
        for y in range(ay, cy + 1):
            if y < by:
                xa, xb = edge_x(y, (ax, ay), (bx, by)), edge_x(y, (ax, ay), (cx, cy))
            else:
                xa, xb = edge_x(y, (bx, by), (cx, cy)), edge_x(y, (ax, ay), (cx, cy))
            lo, hi = int(min(xa, xb)), int(max(xa, xb))
            for x in range(lo, hi + 1):
                self.set(x, y, c)

    # ------------------------------------------------------------ text
    def text_width(self, s, scale):
        return len(s) * (6 * scale) - scale

    def draw_text(self, x, y, s, scale, c):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[' '])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '#':
                        self.rect(cx + col * scale, y + row * scale, scale, scale, c)
            cx += 6 * scale
        return cx

    def draw_text_centered(self, cx, y, s, scale, c):
        self.draw_text(cx - self.text_width(s, scale) // 2, y, s, scale, c)

    def wrap(self, s, max_w, scale):
        """Greedy word wrap; returns list of lines, each <= max_w px."""
        cw = 6 * scale
        lines, cur = [], ""
        for word in s.split(" "):
            trial = word if not cur else cur + " " + word
            if len(trial) * cw - scale <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


# ------------------------------------------------------------------ emblems
def emblem(cv, kind, x, y, s=64):
    """Small drawn pictogram in a s x s box at (x, y)."""
    ink, red, org, blu = INK, RED, ORANGE, BLUE
    if kind == "tanker":
        # hull + bow, flame above, waves below
        cv.rect(x + 4, y + 34, 48, 12, ink)
        cv.triangle(x + 52, y + 34, x + 60, y + 40, x + 52, y + 46, ink)
        cv.rect(x + 12, y + 26, 10, 8, ink)
        cv.rect(x + 30, y + 28, 10, 6, ink)
        cv.triangle(x + 16, y + 26, x + 12, y + 12, x + 22, y + 26, org)
        cv.triangle(x + 20, y + 26, x + 17, y + 16, x + 24, y + 26, red)
        cv.hline(x + 2, y + 52, 56, blu)
        cv.hline(x + 8, y + 57, 44, blu)
    elif kind == "refinery":
        cv.rect(x + 8, y + 22, 10, 30, ink)
        cv.rect(x + 24, y + 12, 12, 40, ink)
        cv.rect(x + 42, y + 28, 10, 24, ink)
        cv.triangle(x + 28, y + 12, x + 24, y + 2, x + 34, y + 12, org)
        cv.circle(x + 13, y + 16, 4, GREY)
        cv.circle(x + 30, y + 6, 3, GREY)
        cv.hline(x + 4, y + 54, 56, ink)
    elif kind == "tariff":
        cv.rect(x + 14, y + 6, 36, 50, PANEL)
        cv.rect(x + 14, y + 6, 36, 50, ink)  # placeholder overwritten below
        cv.rect(x + 16, y + 8, 32, 46, PANEL)
        cv.rect(x + 14, y + 6, 36, 2, ink)
        cv.rect(x + 14, y + 6, 2, 50, ink)
        cv.rect(x + 48, y + 6, 2, 50, ink)
        cv.rect(x + 14, y + 54, 36, 2, ink)
        cv.triangle(x + 38, y + 6, x + 50, y + 6, x + 50, y + 18, GREY)
        cv.draw_text(x + 20, y + 20, "%", 3, red)
        cv.hline(x + 20, y + 44, 24, ink)
        cv.hline(x + 20, y + 49, 24, ink)
    elif kind == "chart":
        cv.hline(x + 6, y + 54, 52, ink)
        cv.vline(x + 6, y + 6, 48, ink)
        pts = [(10, 12), (20, 20), (30, 16), (40, 30), (50, 44)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            cv.line(x + ax, y + ay, x + bx, y + by, red)
            cv.line(x + ax, y + ay + 1, x + bx, y + by + 1, red)
        cv.triangle(x + 50, y + 44, x + 42, y + 40, x + 50, y + 36, red)
        cv.draw_text(x + 34, y + 2, "-6%", 1, red)
    elif kind == "gavel":
        cv.rect(x + 10, y + 12, 34, 12, ink)
        cv.rect(x + 10, y + 12, 34, 4, RED)
        cv.line(x + 44, y + 24, x + 54, y + 44, ink)
        cv.line(x + 45, y + 24, x + 55, y + 44, ink)
        cv.hline(x + 8, y + 52, 48, ink)
        cv.hline(x + 8, y + 55, 48, ink)
    elif kind == "blast":
        cv.circle(x + 32, y + 30, 9, org)
        cv.circle(x + 32, y + 30, 5, red)
        for dx, dy in [(0, -24), (17, -17), (24, 0), (17, 17), (0, 24),
                       (-17, 17), (-24, 0), (-17, -17)]:
            cv.line(x + 32, y + 30, x + 32 + dx, y + 30 + dy, ink)
        cv.circle(x + 12, y + 12, 2, ink)
        cv.circle(x + 52, y + 48, 2, ink)
        cv.circle(x + 52, y + 14, 2, ink)
    elif kind == "flags":
        cv.vline(x + 14, y + 6, 48, ink)
        cv.vline(x + 40, y + 6, 48, ink)
        cv.rect(x + 15, y + 8, 20, 12, RED)
        cv.rect(x + 41, y + 8, 20, 12, BLUE)
        cv.hline(x + 6, y + 54, 52, ink)
        cv.circle(x + 27, y + 34, 5, GOLD)
        cv.circle(x + 27, y + 34, 2, PANEL)
    elif kind == "rocket":
        cv.rect(x + 26, y + 14, 12, 30, ink)
        cv.triangle(x + 26, y + 14, x + 38, y + 14, x + 32, y + 2, red)
        cv.triangle(x + 26, y + 34, x + 18, y + 48, x + 26, y + 44, ink)
        cv.triangle(x + 38, y + 34, x + 46, y + 48, x + 38, y + 44, ink)
        cv.triangle(x + 28, y + 44, x + 36, y + 44, x + 32, y + 58, org)
        cv.circle(x + 32, y + 26, 4, PANEL)
        cv.ring(x + 32, y + 26, 4, ink, 1)
        cv.draw_text(x + 6, y + 8, "+", 1, GREY)
        cv.draw_text(x + 52, y + 20, "+", 1, GREY)


# ------------------------------------------------------------------ stories
# (tag, tag colour, headline, summary, emblem)
STORIES = [
    ("MIDDLE EAST", DARKRED, "TWO OIL TANKERS HIT MINES IN STRAIT OF HORMUZ",
     "Both tankers caught fire after striking sea mines, Iran says. "
     "Tehran deploys new systems to control the strait.", "tanker"),
    ("MIDDLE EAST", DARKRED, "HOUTHIS STRIKE SAUDI REFINERY AND RIYADH TOWER",
     "Yemen's Houthis claim an attack on Ras Tanura, Saudi Arabia's "
     "largest refinery. A drone strike on a Riyadh tower a day earlier "
     "injured 11.", "refinery"),
    ("USA - TRADE", BLUE, "US PROPOSES NEW TARIFFS ON 14 TRADING PARTNERS",
     "Washington targets China, the EU and India after a months-long "
     "probe into industrial subsidies.", "tariff"),
    ("MARKETS - TECH", GREEN, "GLOBAL STOCKS SLIDE AS AI DOUBTS SPREAD",
     "Asia falls: KOSPI -6.16%, Nikkei -2.78%. S&P 500 -2.2% early. "
     "The Dow defies the slide, closing above 50,000 for the first time "
     "at 50,018.70.", "chart"),
    ("USA - CHINA - LAW", PURPLE, "HUAWEI GUILTY ON 10 OF 12 COUNTS",
     "A Brooklyn jury convicts Huawei of bank and wire fraud, sanctions "
     "violations and trade-secret theft. The racketeering charge fails.",
     "gavel"),
    ("EUROPE - WAR", TEAL, "RUSSIAN STRIKES HIT ODESA AND KYIV",
     "Two killed in Odesa, three hurt including a child. Leaked Russian "
     "data cited by the BBC puts Russian war dead at 490,334 since 2022.",
     "blast"),
    ("PACIFIC", TEAL, "AUSTRALIA AND SOLOMON ISLANDS SIGN SECURITY PACT",
     "The deal bars foreign military bases in the Solomons. Honiara is "
     "said to have told China its 2022 security pact will not be renewed.",
     "flags"),
    ("SPACE", PURPLE, "SHENZHOU-24 DOCKS AT TIANGONG WITH FIRST PAKISTANI ASTRONAUT",
     "China's crew spacecraft docks about 3.5 hours after launch, "
     "carrying Pakistan's first astronaut into orbit.", "rocket"),
]


def draw_panel(cv, px, py, pw, ph, story):
    tag, tcol, headline, summary, kind = story
    # font is uppercase-only: normalise text so no glyph falls back to blank
    headline, summary = headline.upper(), summary.upper()
    cv.rect(px, py, pw, ph, PANEL)
    cv.rect(px, py, pw, 2, INK)
    cv.rect(px, py, 2, ph, INK)
    cv.rect(px + pw - 2, py, 2, ph, INK)
    cv.rect(px, py + ph - 2, pw, 2, INK)
    pad = 12
    # region tag pill
    tw = cv.text_width(tag, 2) + 16
    cv.rect(px + pad, py + pad, tw, 24, tcol)
    cv.draw_text(px + pad + 8, py + pad + 5, tag, 2, PANEL)
    # emblem, top right
    emblem(cv, kind, px + pw - pad - 64, py + pad + 2)
    # headline (left of emblem)
    hx = px + pad
    hy = py + pad + 24 + 8
    hw = pw - 2 * pad - 76
    lines = cv.wrap(headline, hw, 3)[:3]
    y = hy
    for ln in lines:
        cv.draw_text(hx, y, ln, 3, INK)
        y += 21
    # rule under headline
    cv.hline(hx, y + 2, pw - 2 * pad, GREY)
    # summary, full width
    sy = y + 10
    for ln in cv.wrap(summary, pw - 2 * pad, 2)[:4]:
        cv.draw_text(hx, sy, ln, 2, INK)
        sy += 15


def draw(cv):
    cv.rect(0, 0, W, H, PAPER)
    # masthead
    cv.draw_text_centered(W // 2, 24, "THE WORLD IN ONE DAY", 7, INK)
    cv.rect(24, 84, W - 48, 3, RED)
    # date band
    cv.rect(24, 94, W - 48, 42, INK)
    cv.draw_text_centered(W // 2, 105, "WEDNESDAY 25 NOVEMBER 2026", 4, PAPER)
    cv.draw_text_centered(W // 2, 146, "EIGHT STORIES FROM AROUND THE WORLD", 2, RED)
    # grid of 8 panels: 2 cols x 4 rows
    gx, gy = 24, 168
    pw, ph, gap = 480, 197, 12
    for i, story in enumerate(STORIES):
        col, row = i % 2, i // 2
        draw_panel(cv, gx + col * (pw + gap), gy + row * (ph + gap),
                   pw, ph, story)
    # footer
    cv.draw_text_centered(
        W // 2, 1004,
        "EVENTS OF WEDNESDAY 25 NOVEMBER 2026, AS REPORTED THAT DAY", 2, INK)


# ---------------------------------------------------------------------- png
def write_png(cv, path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    draw(cv)
    n = write_png(cv, os.path.join(out, "entry.png"))
    print(f"wrote {os.path.join(out, 'entry.png')} ({n} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
