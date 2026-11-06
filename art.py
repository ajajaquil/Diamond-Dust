import os
import re
import sys
import time
import bisect
import keyword
import numpy as np
import pygame

NAME = "Aquil"      # Change name according to your name
HANDLE = "@aquil • 2026" 
FPS = 60
W, H = 478, 850
STAGE_BOTTOM = 458
CX, CY, SC = 239, 322, 155.0
CW, CH = 3, 4
PANEL_TOP = 530
LH = 16

TAU = 2 * np.pi
BAND, PRONG, GEM = 0, 1, 2
R_BAND = 0.55
CULET_Y = R_BAND + 0.05
GIRDLE_Y = R_BAND + 0.28
TABLE_Y = R_BAND + 0.40
GIRDLE_R = 0.28
TABLE_R = 0.16
TURN = 8.0
CHARS = " .,-~:;=!*#$@"

def band():
    u, v = [x.ravel() for x in np.meshgrid(
        np.linspace(0, TAU, 180, endpoint=False),
        np.linspace(0, TAU, 40, endpoint=False)
    )]
    r_tube = 0.065
    cx, cy = R_BAND * np.cos(u), R_BAND * np.sin(u)
    nx = np.cos(v) * np.cos(u)
    ny = np.cos(v) * np.sin(u)
    nz = np.sin(v)
    pts = np.stack([cx + r_tube * nx, cy + r_tube * ny, r_tube * nz], axis=-1)
    norms = np.stack([nx, ny, nz], axis=-1)
    return pts, norms

def diamond():
    P, N, F = [], [], []
    k = 0

    def facet(corners, n):
        nonlocal k
        u, v = [x.ravel() for x in np.meshgrid(np.linspace(0, 1, 16), np.linspace(0, 1, 16))]
        keep = u + v <= 1
        a, b, c = corners
        pts = a + (b - a) * u[keep, None] + (c - a) * v[keep, None]
        P.append(pts), N.append(np.tile(n / np.linalg.norm(n), (len(pts), 1))), F.append(np.full(len(pts), k))
        k += 1

    m = 16
    for i in range(m):
        a0, a1 = TAU * i / m, TAU * (i + 1) / m
        g0 = np.array([GIRDLE_R * np.cos(a0), GIRDLE_Y, GIRDLE_R * np.sin(a0)])
        g1 = np.array([GIRDLE_R * np.cos(a1), GIRDLE_Y, GIRDLE_R * np.sin(a1)])
        t0 = np.array([TABLE_R * np.cos(a0), TABLE_Y, TABLE_R * np.sin(a0)])
        t1 = np.array([TABLE_R * np.cos(a1), TABLE_Y, TABLE_R * np.sin(a1)])
        culet = np.array([0, CULET_Y, 0])
        crown = np.cross(g1 - g0, t0 - g0)
        crown *= np.sign(crown[1]) or 1
        facet((g0, g1, t0), crown)
        facet((g1, t1, t0), crown * [1, 1.15, 1])
        pav = np.cross(culet - g0, g1 - g0)
        pav *= -np.sign(pav[1]) or 1
        facet((g0, g1, culet), pav)
        facet((np.array([0, TABLE_Y, 0]), t0, t1), np.array([0, 1.0, 0]))
    return np.concatenate(P), np.concatenate(N), np.concatenate(F)

def prongs():
    P, N = [], []
    for i in range(4):
        a = TAU * (i + 0.5) / 4
        base = np.array([0.08 * np.cos(a), R_BAND + 0.02, 0.08 * np.sin(a)])
        tip = np.array([(GIRDLE_R + 0.015) * np.cos(a), TABLE_Y - 0.03, (GIRDLE_R + 0.015) * np.sin(a)])
        u, phi = [x.ravel() for x in np.meshgrid(np.linspace(0, 1, 40), np.linspace(0, TAU, 12, endpoint=False))]
        d = (tip - base) / np.linalg.norm(tip - base)
        s = np.cross(d, [0, 0, 1.0]); s /= np.linalg.norm(s)
        w = np.cross(s, d)
        n = np.cos(phi)[:, None] * s + np.sin(phi)[:, None] * w
        P.append(base + u[:, None] * (tip - base) + n * 0.022), N.append(n)
    return np.concatenate(P), np.concatenate(N)

BAND_P, BAND_N = band()
GEM_P, GEM_N, GEM_F = diamond()
PRONG_P, PRONG_N = prongs()
RING_P = np.concatenate([BAND_P, PRONG_P, GEM_P])
RING_N = np.concatenate([BAND_N, PRONG_N, GEM_N])
RING_PART = np.concatenate([np.zeros(len(BAND_P), int), np.ones(len(PRONG_P), int), GEM_F + 2])
RING_KIND = np.concatenate([np.full(len(BAND_P), BAND), np.full(len(PRONG_P), PRONG), np.full(len(GEM_P), GEM)])
SEED = np.random.default_rng(1).random(len(RING_P) + 32)
SEED_P = SEED[:len(RING_P)]
GEM_MASK = RING_KIND == GEM
FACET = RING_PART - 2
SPEC_EXP = np.where(GEM_MASK, 12, 4)

def lights(t):
    key = np.array([0.6, 0.8, 0.6])
    rim = np.array([np.cos(t * 0.9), 0.5, np.sin(t * 0.9)])
    return key / np.linalg.norm(key), rim / np.linalg.norm(rim)

def spin(t):
    return TAU * max(t - DRAW[1] - 0.6, 0) / TURN

def rot_y(p, a):
    c, s = np.cos(a), np.sin(a)
    return np.stack([c * p[:, 0] + s * p[:, 2], p[:, 1], -s * p[:, 0] + c * p[:, 2]], axis=-1)

def draw_order():
    p = RING_P
    up_band = np.abs(np.angle(np.exp(1j * (np.arctan2(p[:, 1], p[:, 0]) + np.pi / 2)))) / np.pi
    prong = 1.0 + (p[:, 1] - R_BAND) / (TABLE_Y - R_BAND) * 0.25
    gem = 1.25 + (p[:, 1] - CULET_Y) / (TABLE_Y - CULET_Y) * 0.45
    return np.select([RING_KIND == BAND, RING_KIND == PRONG], [up_band, prong], gem)

ORDER = draw_order()
DRAW = (0.3, 5.6)

def gather(t):
    head = (t - DRAW[0]) / (DRAW[1] - DRAW[0]) * ORDER.max()
    on = (ORDER <= head) & (t >= DRAW[0])
    glow = on & (np.abs(head - ORDER) < 0.035)
    return head, on, glow

pygame.display.init()
pygame.font.init()

def mono(size, bold=False):
    return pygame.font.SysFont("consolas,menlo,dejavusansmono,liberationmono,couriernew,monospace", size, bold=bold)

F_GLYPH = mono(6)
F_SMALL = mono(11)
F_CODE = mono(12)
F_NAME = mono(17, bold=True)

GLYPHS = {}
for _i, _ch in enumerate(CHARS):
    if _ch == " ":
        continue
    _v = int(70 + 185 * _i / (len(CHARS) - 1))
    GLYPHS[_i] = F_GLYPH.render(_ch, True, (_v, _v, min(255, _v + 6)))
GLOW_GLYPH = F_GLYPH.render("8", True, (255, 255, 255))

_STAR_CACHE = {}

def star(sw, sh, level):
    key = (sw, sh, level)
    if key not in _STAR_CACHE:
        w, h = 2 * sw + 1, 2 * sh + 1
        X, Y = np.meshgrid(np.arange(w) - sw, np.arange(h) - sh)
        horiz = np.exp(-np.abs(Y) / 0.9) * np.clip(1 - np.abs(X) / sw, 0, 1) ** 2
        vert = np.exp(-np.abs(X) / 0.9) * np.clip(1 - np.abs(Y) / sh, 0, 1) ** 2
        core = np.exp(-(X ** 2 + Y ** 2) / (2 * (max(sw, sh) * 0.07 + 1) ** 2))
        I = np.clip(horiz * 0.9 + vert * 0.9 + core, 0, 1) * (level / 5.0)
        rgb = np.stack([I * 255, I * 250, I * 255], -1).astype(np.uint8)
        _STAR_CACHE[key] = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
    return _STAR_CACHE[key]

def blit_star(surf, x, y, sw, sh, strength):
    level = int(np.clip(round(strength * 5), 1, 5))
    s = star(sw, sh, level)
    surf.blit(s, (int(x) - sw, int(y) - sh), special_flags=pygame.BLEND_RGB_ADD)

_rng = np.random.default_rng(7)
ORBITS = [
    (1.28, 1.25, 0.35, 0.30, 0.0),
    (1.08, 1.00, -0.50, -0.35, 2.1),
    (0.92, 1.40, 0.62, 0.10, 4.0),
]
ORB_N = 130
DUST = np.stack([_rng.uniform(6, W - 6, 170), _rng.uniform(40, STAGE_BOTTOM - 4, 170),
                 _rng.uniform(0, TAU, 170)], axis=1)

def orbit_points(t):
    xs, ys, vs = [], [], []
    phi = np.linspace(0, TAU, ORB_N, endpoint=False)
    for rho, tilt, w, roll, ph in ORBITS:
        x = rho * np.cos(phi)
        y = rho * np.sin(phi) * np.cos(tilt)
        z = rho * np.sin(phi) * np.sin(tilt)
        a = w * t
        x, z = np.cos(a) * x + np.sin(a) * z, -np.sin(a) * x + np.cos(a) * z
        x, y = np.cos(roll) * x - np.sin(roll) * y, np.sin(roll) * x + np.cos(roll) * y
        head = (t * 1.1 + ph) % TAU
        trail = np.exp(-((head - phi) % TAU) / 1.1)
        depth = 0.5 + 0.5 * z / rho
        v = np.clip(0.05 + 0.16 * depth + 0.55 * trail, 0, 1) * 0.8
        xs.append(CX + x * SC); ys.append(CY - (y + 0.42) * SC); vs.append(v)
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(vs)

def put_dots(surf, xs, ys, vs, tint=(1.0, 1.0, 1.0)):
    xi, yi = xs.astype(int), ys.astype(int)
    ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < STAGE_BOTTOM)
    xi, yi, vs = xi[ok], yi[ok], vs[ok]
    col = (vs[:, None] * 255 * np.array(tint)).astype(np.int32)
    arr = pygame.surfarray.pixels3d(surf)
    arr[xi, yi] = np.maximum(arr[xi, yi], col)
    big = vs > 0.7
    for dx, dy in ((1, 0), (0, 1)):
        x2, y2 = np.clip(xi[big] + dx, 0, W - 1), np.clip(yi[big] + dy, 0, STAGE_BOTTOM - 1)
        arr[x2, y2] = np.maximum(arr[x2, y2], (col[big] * 0.6).astype(np.int32))
    del arr

def ring_layer(surf, t):
    angle = spin(t)
    p = rot_y(RING_P, angle)
    n = rot_y(RING_N, angle)
    head, on, glow = gather(t)
    sweeping = DRAW[0] <= t < DRAW[1] + 0.3
    if sweeping:
        ahead = (ORDER > head) & (ORDER <= head + 0.10) & (SEED_P < 0.30)
        jx = np.sin(SEED_P[ahead] * 91 + t * 7) * 11
        jy = np.cos(SEED_P[ahead] * 57 + t * 6) * 11
        put_dots(surf, CX + p[ahead, 0] * SC + jx, CY - p[ahead, 1] * SC + jy,
                 np.full(ahead.sum(), 0.55))

    pp, nn, gl_pts, gm = p[on], n[on], glow[on], GEM_MASK[on]
    if len(pp) == 0:
        return 0.0, 0, 0

    key, rim = lights(t)
    diff = np.clip(nn @ key, 0, 1) * 0.65 + np.clip(nn @ rim, 0, 1) * 0.35
    spec = np.clip(nn[:, 2], 0, 1) ** SPEC_EXP[on]
    shimmer = np.where(gm, 0.14 * np.sin(t * 2.3 + FACET[on] * 1.7), 0.0)
    lum = np.clip(0.22 + 0.80 * diff + spec * 0.55 + shimmer, 0, 1)

    sx = CX + pp[:, 0] * SC
    sy = CY - pp[:, 1] * SC
    z = pp[:, 2]
    ok = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < STAGE_BOTTOM)
    sx, sy, z, lum, gl_pts, gm, spec = sx[ok], sy[ok], z[ok], lum[ok], gl_pts[ok], gm[ok], spec[ok]
    seed = SEED_P[on][ok]

    gx, gy = (sx // CW).astype(int), (sy // CH).astype(int)
    cell = gy * (W // CW + 2) + gx
    order = np.lexsort((z, cell))
    c = cell[order]
    last = np.r_[c[1:] != c[:-1], True]
    sel = order[last]

    blits = []
    steps = (lum[sel] * (len(CHARS) - 1)).astype(int)
    for i, k in enumerate(sel):
        pos = (gx[k] * CW, gy[k] * CH)
        if gl_pts[k]:
            blits.append((GLOW_GLYPH, pos))
        elif steps[i] > 0:
            blits.append((GLYPHS[steps[i]], pos))
    surf.blits(blits, doreturn=False)

    flick = (spec + 0.12 * gm) * (0.55 + 0.45 * np.sin(t * 5.0 + seed * 40))
    hot = gm & (flick > 0.12)
    glints = int(hot.sum())
    if glints:
        bx, by, bs = sx[hot], sy[hot], flick[hot]
        bucket = (bx // 22).astype(int) * 1000 + (by // 22).astype(int)
        o = np.lexsort((-bs, bucket))
        first = np.r_[True, bucket[o][1:] != bucket[o][:-1]]
        pick = o[first]
        pick = pick[np.argsort(-bs[pick])][:8]
        for k in pick:
            r = int(7 + 11 * min(1.0, bs[k] * 3))
            blit_star(surf, bx[k], by[k], r, r, min(1.0, bs[k] * 3 + 0.3))

    fa = float(np.clip((head - 1.45) / 0.25, 0, 1)) if t >= DRAW[0] else 0.0
    if fa > 0:
        pulse = 0.65 + 0.35 * np.sin(t * 2.1)
        blit_star(surf, CX, CY - TABLE_Y * SC, 40, 72, pulse * fa)
        blit_star(surf, CX, CY - TABLE_Y * SC, 16, 16, fa)

    return float(np.degrees(angle) % 360), len(sel), glints

SYN = re.compile(r'(#.*$)|("""[^"]*"""?|\'[^\']*\'?|"[^"]*"?)|([A-Za-z_]\w*)|(\d[\d.]*)|(\s+|.)')
KW = set(keyword.kwlist)
C_DEF, C_COM, C_STR, C_KW, C_NUM = (228, 228, 234), (130, 134, 150), (222, 204, 160), (244, 154, 182), (156, 204, 234)

def spans(line):
    out = []
    for m in SYN.finditer(line):
        txt = m.group(0)
        if m.group(1):
            col = C_COM
        elif m.group(2):
            col = C_STR
        elif m.group(3):
            col = C_KW if txt in KW else C_DEF
        elif m.group(4):
            col = C_NUM
        else:
            col = C_DEF
        out.append((txt, col))
    return out

CODE_CW = F_CODE.size("M")[0]
try:
    with open(__file__, encoding="utf-8") as _f:
        SRC = [ln.rstrip("\n").expandtabs(4) for ln in _f]
except Exception:
    SRC = ["art.py"]
COST = [len(s) + 5 for s in SRC]
FIRST = next((i for i, s in enumerate(SRC) if s.startswith("def band")), 0)
STARTS = [0] * (FIRST + 1)
for _c in COST[FIRST:]:
    STARTS.append(STARTS[-1] + _c)
TOTAL = STARTS[-1]
CPS = 170.0
_LINE_CACHE = {}

def render_line(i, upto=None):
    line = SRC[i] if upto is None else SRC[i][:upto]
    line = line[:80]
    s = pygame.Surface((W - 50, LH), pygame.SRCALPHA)
    x = 0
    for txt, col in spans(line):
        s.blit(F_CODE.render(txt, True, col), (x, 0))
        x += CODE_CW * len(txt)
    return s

def full_line(i):
    if i not in _LINE_CACHE:
        _LINE_CACHE[i] = render_line(i)
    return _LINE_CACHE[i]

def _fade_overlay():
    ov = pygame.Surface((W, H - PANEL_TOP), pygame.SRCALPHA)
    h = ov.get_height()
    for y in range(h):
        a = 0
        if y < 50:
            a = 255 * (1 - y / 50)
        if y > h - 95:
            a = max(a, 205 * (y - (h - 95)) / 95)
        ov.fill((0, 0, 0, int(a)), (0, y, W, 1))
    return ov

FADE = _fade_overlay()

def code_panel(surf, t):
    tt = max(t - 0.3, 0.0)
    cycle = TOTAL / CPS + 3.0
    typed = min((tt % cycle) * CPS, TOTAL - 1)
    cur = bisect.bisect_right(STARTS, typed) - 1
    into = typed - STARTS[cur]
    pos = cur + into / COST[cur]
    shown = int(min(into, len(SRC[cur])))
    anchor = min(PANEL_TOP + 150, PANEL_TOP + 22 + (pos - FIRST) * LH)

    surf.set_clip(pygame.Rect(0, PANEL_TOP, W, H - PANEL_TOP))
    for i in range(max(FIRST, cur - 22), min(len(SRC), cur + 24)):
        y = int(anchor + (i - pos) * LH)
        if y < PANEL_TOP - LH or y > H:
            continue
        is_cur = i == cur
        if is_cur:
            surf.fill((30, 16, 22), (0, y - 2, W, LH))
            surf.fill((228, 78, 118), (14, y, 3, LH - 4))
        num = F_CODE.render(str(i + 1), True, (235, 235, 242) if is_cur else (128, 132, 150))
        surf.blit(num, (38 - num.get_width(), y))
        ln = full_line(i)
        ln.set_alpha(255 if i < cur else 165)
        surf.blit(ln, (50, y))
        if is_cur:
            part = render_line(i, shown)
            surf.blit(part, (50, y))
            bx = 50 + shown * CODE_CW
            if int(t * 2.5) % 2 == 0:
                surf.fill((236, 84, 124), (bx, y + 1, CODE_CW, LH - 4))
    surf.set_clip(None)
    surf.blit(FADE, (0, PANEL_TOP))

def text(surf, s, pos, col, font=F_SMALL, right=False):
    img = font.render(s, True, col)
    surf.blit(img, (pos[0] - img.get_width() if right else pos[0], pos[1]))

def signature(surf):
    gap = 3
    imgs = [F_NAME.render(ch, True, (236, 236, 242)) for ch in NAME]
    total = sum(i.get_width() for i in imgs) + gap * (len(imgs) - 1)
    x = W - 20 - total
    y = 474
    for i in imgs:
        surf.blit(i, (x, y))
        x += i.get_width() + gap
    surf.fill((228, 78, 118), (W - 20 - total, y + imgs[0].get_height() + 1, 14, 2))

def draw_frame(surf, t, fps=FPS):
    surf.fill((0, 0, 0))

    ax = np.clip((t - 5.8) / 2.0, 0, 1)
    if ax > 0:
        ox, oy, ov = orbit_points(t)
        put_dots(surf, ox, oy, ov * ax)
    tw = np.clip(np.sin(t * 1.7 + DUST[:, 2] * 3) , 0, 1) ** 4 * 0.55 + 0.10
    put_dots(surf, DUST[:, 0], DUST[:, 1], tw)
    surf.set_clip(pygame.Rect(0, 0, W, STAGE_BOTTOM))
    deg, letters, glints = ring_layer(surf, t)
    surf.set_clip(None)

    pygame.draw.circle(surf, (236, 80, 112), (W - 82, 104), 2)
    text(surf, f"t {t % 100:05.2f}s", (W - 20, 98), (236, 140, 162), right=True)

    dim, lite = (178, 181, 194), (240, 240, 246)
    text(surf, HANDLE, (14, 466), lite)
    text(surf, f"rotation {deg:06.2f}°   glints {glints}", (14, 479), dim)
    text(surf, f"letters {letters:,}", (14, 492), dim)

    surf.fill((38, 38, 44), (0, 503, W, 1))
    text(surf, "$", (14, 509), (228, 78, 118))
    text(surf, f"py {os.path.basename(__file__)}", (28, 509), lite)
    text(surf, f"running • {int(round(min(fps, FPS)))} fps", (W - 14, 509), dim, right=True)
    surf.fill((38, 38, 44), (0, 524, W, 1))

    code_panel(surf, t)
    signature(surf)

def main():
    pygame.display.set_caption(os.path.basename(__file__))
    dw, dh = pygame.display.get_desktop_sizes()[0]
    k = min(1.0, (dh - 120) / H)
    win = pygame.display.set_mode((int(W * k), int(H * k)), pygame.RESIZABLE)
    canvas = pygame.Surface((W, H))
    clock = pygame.time.Clock()
    t0 = time.perf_counter()
    fps = FPS
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_q)):
                pygame.quit()
                return
        draw_frame(canvas, time.perf_counter() - t0, fps)
        win = pygame.display.get_surface()
        ww, wh = win.get_size()
        win.fill((0, 0, 0))
        if (ww, wh) == (W, H):
            win.blit(canvas, (0, 0))
        else:
            s = min(ww / W, wh / H)
            size = (max(1, int(W * s)), max(1, int(H * s)))
            win.blit(pygame.transform.smoothscale(canvas, size), ((ww - size[0]) // 2, (wh - size[1]) // 2))
        pygame.display.flip()
        clock.tick(FPS)
        fps = clock.get_fps() or FPS

if __name__ == "__main__":
    main()