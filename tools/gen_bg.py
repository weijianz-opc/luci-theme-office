#!/usr/bin/env python3
"""
Generate the isometric "network office" background for luci-theme-office.

Pure-python, no deps. Writes htdocs/luci-static/office/bg.svg
Run:  python3 tools/gen_bg.py
"""
import math
import os
import random

random.seed(7)

# ---------------------------------------------------------------- projection
S_UNIT = 46.0                     # px per world unit (floor grid)
C = math.cos(math.radians(30)) * S_UNIT
S = 0.5 * S_UNIT
H = 0.82 * S_UNIT                 # px per world unit of height

W_VIEW, H_VIEW = 1920, 1080
OX, OY = 1010.0, 70.0             # screen position of world origin


def P(x, y, z=0.0):
    return (OX + (x - y) * C, OY + (x + y) * S - z * H)


def fmt(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def poly(pts, fill, extra=""):
    d = "M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + "Z"
    return f'<path d="{d}" fill="{fill}" stroke="{fill}" stroke-width=".6" stroke-linejoin="round"{extra}/>'


# ---------------------------------------------------------------- colours
def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in c)


def mix(a, b, t):
    a, b = hex2rgb(a), hex2rgb(b)
    return rgb2hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def shade(h, k, tint="#7a4a8a", tk=0.0):
    r = tuple(v * k for v in hex2rgb(h))
    out = rgb2hex(r)
    return mix(out, tint, tk) if tk else out


def faces(base):
    """top / left(+y) / right(+x) face colours with warm-purple ambient."""
    return (mix(base, "#ffe6ee", 0.10),
            shade(base, 0.86, "#8a5a9a", 0.10),
            shade(base, 0.70, "#5a3a7a", 0.16))


# ---------------------------------------------------------------- primitives
def box(x, y, z, w, d, h, base, top=None):
    t, l, r = faces(base)
    if top:
        t = top
    out = []
    # +y face (visible, lower-left)
    out.append(poly([P(x, y + d, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x, y + d, z + h)], l))
    # +x face (visible, lower-right)
    out.append(poly([P(x + w, y, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x + w, y, z + h)], r))
    # top
    out.append(poly([P(x, y, z + h), P(x + w, y, z + h), P(x + w, y + d, z + h), P(x, y + d, z + h)], t))
    return "".join(out)


def face_y(x0, y, ztop, inner):
    """Draw `inner` svg on a +y face. Local coords: 1 world unit == S_UNIT px, v grows downward."""
    e, f = P(x0, y, ztop)
    return (f'<g transform="matrix({C / S_UNIT:.4f} {S / S_UNIT:.4f} 0 {H / S_UNIT:.4f} {fmt(e)} {fmt(f)})">'
            f'{inner}</g>')


def face_x(x, y_end, ztop, inner):
    """Draw `inner` on a +x face; local u runs toward decreasing y (reads left->right)."""
    e, f = P(x, y_end, ztop)
    return (f'<g transform="matrix({C / S_UNIT:.4f} {-S / S_UNIT:.4f} 0 {H / S_UNIT:.4f} {fmt(e)} {fmt(f)})">'
            f'{inner}</g>')


def floor_ellipse(cx, cy, r, fill, z=0.0, extra=""):
    X, Y = P(cx, cy, z)
    return (f'<ellipse cx="{fmt(X)}" cy="{fmt(Y)}" rx="{fmt(r * C * math.sqrt(2))}" '
            f'ry="{fmt(r * S * math.sqrt(2))}" fill="{fill}"{extra}/>')


def cylinder(cx, cy, z, r, h, side, top):
    X, Yb = P(cx, cy, z)
    _, Yt = P(cx, cy, z + h)
    rx, ry = r * C * math.sqrt(2), r * S * math.sqrt(2)
    return (f'<ellipse cx="{fmt(X)}" cy="{fmt(Yb)}" rx="{fmt(rx)}" ry="{fmt(ry)}" fill="{side}"/>'
            f'<rect x="{fmt(X - rx)}" y="{fmt(Yt)}" width="{fmt(2 * rx)}" height="{fmt(Yb - Yt)}" fill="{side}"/>'
            f'<rect x="{fmt(X - rx)}" y="{fmt(Yt)}" width="{fmt(2 * rx)}" height="{fmt(Yb - Yt + ry)}" fill="url(#cyl)"/>'
            f'<ellipse cx="{fmt(X)}" cy="{fmt(Yt)}" rx="{fmt(rx)}" ry="{fmt(ry)}" fill="{top}"/>')


# ---------------------------------------------------------------- low-poly foliage
PHI = (1 + 5 ** 0.5) / 2
ICO_V = [(-1, PHI, 0), (1, PHI, 0), (-1, -PHI, 0), (1, -PHI, 0),
         (0, -1, PHI), (0, 1, PHI), (0, -1, -PHI), (0, 1, -PHI),
         (PHI, 0, -1), (PHI, 0, 1), (-PHI, 0, -1), (-PHI, 0, 1)]
ICO_F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2),
         (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5),
         (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
LIGHT = (-0.45, 0.75, 0.5)
_ln = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _ln for v in LIGHT)


def lowpoly_ball(cx, cy, r, dark="#355f3a", light="#9cc463", squash=0.92):
    rot = random.random() * math.pi
    tilt = 0.35
    verts = []
    for vx, vy, vz in ICO_V:
        n = math.sqrt(vx * vx + vy * vy + vz * vz)
        j = 1 + (random.random() - 0.5) * 0.28
        vx, vy, vz = vx / n * j, vy / n * j * squash, vz / n * j
        # rotate around y then tilt around x
        x1 = vx * math.cos(rot) + vz * math.sin(rot)
        z1 = -vx * math.sin(rot) + vz * math.cos(rot)
        y2 = vy * math.cos(tilt) - z1 * math.sin(tilt)
        z2 = vy * math.sin(tilt) + z1 * math.cos(tilt)
        verts.append((x1, y2, z2))
    tris = []
    for a, b, c in ICO_F:
        A, B, Cc = verts[a], verts[b], verts[c]
        u = [B[i] - A[i] for i in range(3)]
        v = [Cc[i] - A[i] for i in range(3)]
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        nl = math.sqrt(sum(q * q for q in n)) or 1
        n = tuple(q / nl for q in n)
        cen = [(A[i] + B[i] + Cc[i]) / 3 for i in range(3)]
        if sum(n[i] * cen[i] for i in range(3)) < 0:
            n = tuple(-q for q in n)
        if n[2] <= 0:
            continue
        lum = max(0.0, sum(n[i] * LIGHT[i] for i in range(3)))
        col = mix(dark, light, min(1.0, 0.15 + lum * 0.95))
        pts = [(cx + p[0] * r, cy - p[1] * r) for p in (A, B, Cc)]
        tris.append((cen[2], poly(pts, col)))
    tris.sort(key=lambda t: t[0])
    return "".join(t[1] for t in tris)


def plant(x, y, size=1.0, pot="#3b3550", kind="bush"):
    out = []
    r = 0.26 * size
    out.append(floor_ellipse(x, y, r * 1.5, "rgba(60,30,70,.22)"))
    out.append(cylinder(x, y, 0, r, 0.42 * size, shade(pot, 0.85), mix(pot, "#ffffff", 0.12)))
    X, Y = P(x, y, 0.42 * size)
    if kind == "tree":
        out.append(f'<rect x="{fmt(X - 1.5)}" y="{fmt(Y - 40 * size)}" width="3" height="{fmt(40 * size)}" fill="#6b4a3a"/>')
        out.append(lowpoly_ball(X - 6 * size, Y - 46 * size, 17 * size))
        out.append(lowpoly_ball(X + 7 * size, Y - 58 * size, 15 * size))
        out.append(lowpoly_ball(X - 1 * size, Y - 72 * size, 13 * size))
    else:
        out.append(lowpoly_ball(X, Y - 16 * size, 20 * size))
        out.append(lowpoly_ball(X + 4 * size, Y - 34 * size, 13 * size))
    return "".join(out)


def hedge(x, y):
    X, Y = P(x, y, 0.5)
    return (box(x - 0.4, y - 0.4, 0, 0.8, 0.8, 0.5, "#d8c3c9") +
            lowpoly_ball(X, Y - 14, 24, "#2f5a36", "#8fbf5c") +
            lowpoly_ball(X + 2, Y - 34, 18, "#2f5a36", "#9cc865"))


def lamp(x, y, hgt=1.9):
    out = [floor_ellipse(x, y, 0.22, "rgba(60,30,70,.25)")]
    out.append(cylinder(x, y, 0, 0.16, 0.05, "#3a3546", "#55506a"))
    X, Yb = P(x, y, 0.05)
    _, Yt = P(x, y, hgt)
    out.append(f'<rect x="{fmt(X - 1.6)}" y="{fmt(Yt)}" width="3.2" height="{fmt(Yb - Yt)}" fill="#3a3546"/>')
    out.append(f'<circle cx="{fmt(X)}" cy="{fmt(Yt - 4)}" r="70" fill="url(#halo)"/>')
    out.append(cylinder(x, y, hgt - 0.1, 0.24, 0.42, "#fff4e2", "#fffaf2"))
    return "".join(out)


ROBOT_CACHE = {}


def robot(x, y, z=0.0, face=True, phones=None, scale=1.0, eyes="#5ee6ff"):
    X, Y = P(x, y, z)
    k = scale
    o = [f'<ellipse cx="{fmt(X)}" cy="{fmt(Y)}" rx="{fmt(17 * k)}" ry="{fmt(6.5 * k)}" fill="rgba(50,25,60,.28)"/>']
    o.append(f'<g transform="translate({fmt(X)} {fmt(Y)}) scale({k})">')
    o.append('<ellipse cx="0" cy="-17" rx="12.5" ry="15" fill="url(#rw)"/>')
    o.append('<rect x="-4.5" y="-31" width="9" height="5" rx="2" fill="#bdb3cc"/>')
    o.append('<rect x="-19" y="-56" width="38" height="29" rx="13" fill="url(#rw)"/>')
    if face:
        o.append('<rect x="-14" y="-50.5" width="28" height="17" rx="7.5" fill="#1b2133"/>')
        o.append(f'<rect x="-9.5" y="-45" width="6.5" height="5" rx="2.5" fill="{eyes}" filter="url(#glow)"/>')
        o.append(f'<rect x="3" y="-45" width="6.5" height="5" rx="2.5" fill="{eyes}" filter="url(#glow)"/>')
    else:
        o.append('<rect x="-12" y="-50" width="24" height="3" rx="1.5" fill="#d9d1e3"/>')
    if phones:
        o.append(f'<path d="M-17 -44 C-17 -66 17 -66 17 -44" fill="none" stroke="{phones}" stroke-width="3.6" stroke-linecap="round"/>')
        o.append(f'<rect x="-23" y="-49" width="7" height="13" rx="3.5" fill="{phones}"/>')
        o.append(f'<rect x="16" y="-49" width="7" height="13" rx="3.5" fill="{phones}"/>')
    else:
        o.append('<line x1="0" y1="-56" x2="0" y2="-63" stroke="#bdb3cc" stroke-width="2"/>')
        o.append(f'<circle cx="0" cy="-65" r="3" fill="{eyes}" filter="url(#glow)"/>')
    o.append('</g>')
    return "".join(o)


def chair(x, y, facing_y=True):
    out = []
    out.append(cylinder(x, y, 0, 0.05, 0.36, "#2b2f42", "#2b2f42"))
    out.append(box(x - 0.3, y - 0.3, 0.36, 0.6, 0.6, 0.1, "#2c3045"))
    return "".join(out)


def chair_back(x, y):
    # back rest behind a robot that faces +y (towards viewer)
    return box(x - 0.3, y - 0.42, 0.42, 0.6, 0.1, 0.75, "#272b3e")


def desk(x0, y0, w, d, monitors=2, top="#f3eaee", screen_glow="#5ee6ff"):
    out = []
    leg = "#3a3650"
    out.append(box(x0, y0, 0, 0.08, d, 0.72, leg))
    out.append(box(x0 + w - 0.08, y0, 0, 0.08, d, 0.72, leg))
    out.append(box(x0 + 0.08, y0 + d - 0.1, 0.2, w - 0.16, 0.05, 0.45, "#e2d6de"))
    out.append(box(x0, y0, 0.72, w, d, 0.07, top))
    # monitors – backs face viewer (+y); glow leaks over the top edge
    span = w / monitors
    for i in range(monitors):
        mx = x0 + span * i + span / 2
        X, Y = P(mx, y0 + 0.25, 1.25)
        out.append(f'<ellipse cx="{fmt(X)}" cy="{fmt(Y - 4)}" rx="34" ry="16" fill="{screen_glow}" opacity=".22" filter="url(#soft)"/>')
        out.append(box(mx - 0.06, y0 + 0.35, 0.79, 0.12, 0.12, 0.2, "#2b2f42"))
        out.append(box(mx - 0.42, y0 + 0.22, 0.95, 0.84, 0.07, 0.5, "#23273a", top="#3a3f58"))
        out.append(face_y(mx - 0.42, y0 + 0.29, 1.45,
                          f'<rect x="4" y="4" width="{0.84 * S_UNIT - 8:.1f}" height="2" rx="1" fill="{screen_glow}" opacity=".55"/>'))
    return "".join(out)


def rack(x, y, h=2.1, seed=0):
    rnd = random.Random(seed)
    out = [floor_ellipse(x + 0.45, y + 0.45, 0.7, "rgba(40,20,60,.18)")]
    out.append(box(x, y, 0, 0.9, 0.9, h, "#2a2e44", top="#3d425d"))
    # front: units with LEDs
    inner = []
    w = 0.9 * S_UNIT
    units = int(h * S_UNIT / 9)
    for u in range(units):
        yy = 5 + u * 9
        if yy > h * S_UNIT - 8:
            break
        inner.append(f'<rect x="4" y="{yy}" width="{w - 8:.1f}" height="7" rx="1.5" fill="#20243a"/>')
        for l in range(rnd.randint(1, 4)):
            col = rnd.choice(["#5df2a0", "#5df2a0", "#5ee6ff", "#ffc94a", "#5df2a0", "#ff7eb6"])
            inner.append(f'<rect x="{w - 10 - l * 5}" y="{yy + 2.5}" width="2.6" height="2.2" fill="{col}"/>')
        inner.append(f'<rect x="7" y="{yy + 3}" width="{rnd.randint(8, 18)}" height="1.2" fill="#4a5070"/>')
    out.append(face_y(x, y + 0.9, h, "".join(inner)))
    # side vents
    vents = "".join(f'<rect x="6" y="{8 + i * 6}" width="{0.9 * S_UNIT - 12:.1f}" height="1.3" fill="#1d2032"/>'
                    for i in range(int(h * S_UNIT / 6) - 3))
    out.append(face_x(x + 0.9, y + 0.9, h, vents))
    return "".join(out)


def low_wall_x(x0, x1, y, h=0.5, t=0.2):
    """partition running along x at row y; split into 1-unit segments for depth sorting"""
    items = []
    x = x0
    while x < x1 - 1e-6:
        w = min(1.0, x1 - x)
        g = box(x, y, 0, w, t, h, "#efe2e6") + box(x - 0.03, y - 0.05, h, w + 0.06, t + 0.1, 0.07, "#d29b6c")
        items.append((x + w / 2 + y + t / 2, g))
        x += w
    return items


def low_wall_y(x, y0, y1, h=0.5, t=0.2):
    items = []
    y = y0
    while y < y1 - 1e-6:
        d = min(1.0, y1 - y)
        g = box(x, y, 0, t, d, h, "#efe2e6") + box(x - 0.05, y - 0.03, h, t + 0.1, d + 0.06, 0.07, "#d29b6c")
        items.append((x + t / 2 + y + d / 2, g))
        y += d
    return items


def pill(x, y, z, icon, label, value, vcol="#ffc94a"):
    X, Y = P(x, y, z)
    tw = 7.2 * len(label) + 7.4 * len(value) + 44
    x0 = X - tw / 2
    return (f'<g transform="translate({fmt(x0)} {fmt(Y - 13)})">'
            f'<rect width="{tw:.0f}" height="24" rx="12" fill="#1c2033" fill-opacity=".9" stroke="#ffffff" stroke-opacity=".12"/>'
            f'<rect x="5" y="5" width="14" height="14" rx="4" fill="#ece6f2"/>'
            f'<text x="12" y="16" font-size="9.5" font-weight="700" fill="#1c2033" text-anchor="middle">{icon}</text>'
            f'<text x="25" y="16.5" font-size="11.5" font-weight="600" fill="#ffffff">{label}</text>'
            f'<text x="{tw - 10:.0f}" y="16.5" font-size="11.5" font-weight="600" fill="{vcol}" text-anchor="end" font-family="ui-monospace,Menlo,monospace">{value}</text>'
            f'</g>')


def wall_screen(kind, w, h, rnd):
    """Dashboard content for wall screens (local px)."""
    o = [f'<rect width="{w}" height="{h}" rx="5" fill="#161a2b"/>',
         f'<rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="4" fill="url(#scr)"/>']
    if kind == "line":
        for col, amp, ph in (("#5ee6ff", 0.32, 0), ("#5df2a0", 0.22, 1.7), ("#ff7eb6", 0.15, 3.1)):
            pts = []
            for i in range(25):
                xx = 8 + (w - 16) * i / 24
                yy = h * 0.62 - math.sin(i / 3.2 + ph) * h * amp * 0.5 - rnd.random() * h * 0.12
                pts.append(f"{xx:.1f},{yy:.1f}")
            o.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round"/>')
        o.append(f'<rect x="8" y="7" width="{w * 0.3:.0f}" height="4" rx="2" fill="#ffffff" opacity=".5"/>')
    elif kind == "bars":
        n = 12
        bw = (w - 16) / n
        for i in range(n):
            bh = (0.2 + rnd.random() * 0.65) * (h - 24)
            col = "#ffc94a" if i == 7 else "#a78bfa"
            o.append(f'<rect x="{8 + i * bw + 1:.1f}" y="{h - 8 - bh:.1f}" width="{bw - 3:.1f}" height="{bh:.1f}" rx="1.5" fill="{col}"/>')
        o.append(f'<rect x="8" y="7" width="{w * 0.25:.0f}" height="4" rx="2" fill="#ffffff" opacity=".5"/>')
    else:  # topology
        nodes = [(w * 0.5, h * 0.3)] + [(w * (0.15 + 0.7 * i / 4), h * 0.75) for i in range(5)]
        for nx, ny in nodes[1:]:
            o.append(f'<line x1="{nodes[0][0]:.1f}" y1="{nodes[0][1]:.1f}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="#5ee6ff" stroke-opacity=".6" stroke-width="1.5"/>')
        o.append(f'<circle cx="{nodes[0][0]:.1f}" cy="{nodes[0][1]:.1f}" r="7" fill="#ffc94a"/>')
        for i, (nx, ny) in enumerate(nodes[1:]):
            o.append(f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="4.5" fill="{["#5df2a0", "#5ee6ff", "#a78bfa", "#ff7eb6", "#5df2a0"][i]}"/>')
    return "".join(o)


def iso_sign(x, y, z, num, title, sub):
    """Floating dark signboard (like '4 Operations') standing on the floor, text on +y face."""
    w, h = 4.2, 1.15
    out = [floor_ellipse(x + w / 2, y + 0.2, 1.6, "rgba(40,20,60,.25)")]
    out.append(box(x, y, z, w, 0.32, h, "#1c2033", top="#2c3150"))
    inner = (f'<rect x="10" y="9" width="{h * S_UNIT - 18:.0f}" height="{h * S_UNIT - 18:.0f}" rx="8" fill="#ffc94a"/>'
             f'<text x="{(h * S_UNIT - 18) / 2 + 10:.0f}" y="{h * S_UNIT - 20:.0f}" font-size="30" font-weight="800" fill="#1c2033" text-anchor="middle">{num}</text>'
             f'<text x="{h * S_UNIT + 2:.0f}" y="25" font-size="21" font-weight="800" fill="#ffffff">{title}</text>'
             f'<text x="{h * S_UNIT + 2:.0f}" y="40" font-size="9.5" font-weight="500" fill="#ffffff" opacity=".85">{sub}</text>'
             f'<rect x="{h * S_UNIT + 2:.0f}" y="44" width="92" height="4" rx="2" fill="#ffc94a" opacity=".85"/>')
    out.append(face_y(x, y + 0.32, z + h, inner))
    return "".join(out)


# ---------------------------------------------------------------- scene
FX, FY = 30, 22          # floor size
items = []               # (depth, svg)
under = []               # floor decals (drawn before items)

# --- walls (far edges) – drawn explicitly before everything
walls = []
walls.append(box(-0.3, -0.3, 0, FX + 0.3, 0.3, 2.7, "#e7dbe9", top="#f6eef6"))
# back wall content: shelves + dashboard screens
rnd = random.Random(3)
for i, (sx, kind) in enumerate([(2.0, "line"), (6.6, "bars"), (17.2, "topo"), (21.8, "line"), (26.0, "bars")]):
    walls.append(face_y(sx, 0, 2.35, wall_screen(kind, 3.4 * S_UNIT, 1.25 * S_UNIT, rnd)))
# accent light strip along the back wall
walls.append(face_y(0, 0, 0.32, f'<rect x="0" y="0" width="{FX * S_UNIT}" height="3" fill="#ffb3d1" opacity=".55"/>'))
walls.append(box(-0.3, 0, 0, 0.3, FY, 2.7, "#e3d6e6", top="#f6eef6"))
for sy, kind in [(2.0, "topo"), (7.2, "line")]:
    walls.append(face_x(0, sy + 3.4, 2.35, wall_screen(kind, 3.4 * S_UNIT, 1.25 * S_UNIT, rnd)))
walls.append(face_x(0, FY, 0.32, f'<rect x="0" y="0" width="{FY * S_UNIT}" height="3" fill="#ffb3d1" opacity=".55"/>'))
# big wall title
walls.append(face_y(11.3, 0, 2.55,
                    '<text x="0" y="22" font-size="26" font-weight="800" fill="#2b2440" opacity=".78" letter-spacing="1">NETWORK OPS</text>'
                    '<text x="0" y="40" font-size="11" font-weight="600" fill="#2b2440" opacity=".5" letter-spacing="2">EVERY PACKET HAS A DESK</text>'))

# --- floor slab
floor = []
floor.append(poly([P(0, FY, -0.9), P(FX, FY, -0.9), P(FX, FY, 0), P(0, FY, 0)], "#b98260"))
floor.append(poly([P(FX, 0, -0.9), P(FX, FY, -0.9), P(FX, FY, 0), P(FX, 0, 0)], "#9c6a52"))
floor.append(poly([P(0, FY, -0.12), P(FX, FY, -0.12), P(FX, FY, 0), P(0, FY, 0)], "#d8a57c"))
floor.append(poly([P(FX, 0, -0.12), P(FX, FY, -0.12), P(FX, FY, 0), P(FX, 0, 0)], "#c38f6c"))
floor.append(poly([P(0, 0), P(FX, 0), P(FX, FY), P(0, FY)], "#ecd8dc"))
# room tints
for (x0, y0, x1, y1, col) in [(0, 0, 13.9, 10.4, "#e9d2d9"), (14.3, 0, FX, 10.4, "#e4d3de"),
                              (0, 10.8, 13.9, FY, "#efdcdc"), (14.3, 10.8, FX, FY, "#e8d0d6")]:
    floor.append(poly([P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)], col))
# grid
g = []
for i in range(1, FX):
    a, b = P(i, 0), P(i, FY)
    g.append(f"M{fmt(a[0])} {fmt(a[1])}L{fmt(b[0])} {fmt(b[1])}")
for j in range(1, FY):
    a, b = P(0, j), P(FX, j)
    g.append(f"M{fmt(a[0])} {fmt(a[1])}L{fmt(b[0])} {fmt(b[1])}")
floor.append(f'<path d="{"".join(g)}" stroke="#8a5f7a" stroke-opacity=".09" stroke-width="1" fill="none"/>')

# --- network cables on the floor (glowing)
RX, RY = 15.4, 11.6
cable_paths = [
    [(RX, RY), (RX, 6.2), (19, 6.2)],
    [(RX, RY), (RX, 8.6), (7.0, 8.6), (7.0, 5.4)],
    [(RX, RY), (21.0, RY), (21.0, 16.0)],
    [(RX, RY), (RX - 1, RY), (RX - 1, 16.6), (6.0, 16.6)],
]
cab = []
for pts in cable_paths:
    d = "M" + "L".join(f"{fmt(P(x, y, .01)[0])} {fmt(P(x, y, .01)[1])}" for x, y in pts)
    cab.append(d)
under.append(f'<path d="{"".join(cab)}" fill="none" stroke="#5ee6ff" stroke-width="7" stroke-opacity=".25" filter="url(#soft)"/>')
under.append(f'<path d="{"".join(cab)}" fill="none" stroke="#7af0ff" stroke-width="2" stroke-opacity=".85" stroke-dasharray="14 8" stroke-linecap="round"/>')

# --- center: router on glowing pad
under.append(floor_ellipse(RX + 1, RY + 0.7, 2.5, "url(#padglow)"))
under.append(floor_ellipse(RX + 1, RY + 0.7, 1.75, "#2a2840"))
under.append(floor_ellipse(RX + 1, RY + 0.7, 1.75, "none", extra=' stroke="#5ee6ff" stroke-width="2.5" stroke-opacity=".9" filter="url(#glow)"'))
under.append(floor_ellipse(RX + 1, RY + 0.7, 1.35, "none", extra=' stroke="#ffffff" stroke-opacity=".18" stroke-width="1"'))

router = []
router.append(box(RX, RY, 0.05, 2.0, 1.4, 0.5, "#232738", top="#353a52"))
router.append(face_y(RX, RY + 1.4, 0.55,
                     "".join(f'<rect x="{10 + i * 11}" y="9" width="6" height="4" rx="1" fill="{c}" filter="url(#glow)"/>'
                             for i, c in enumerate(["#5df2a0", "#5df2a0", "#5ee6ff", "#ffc94a", "#5df2a0"])) +
                     f'<rect x="72" y="7" width="{2.0 * S_UNIT - 82:.0f}" height="8" rx="2" fill="#151827"/>'))
router.append(face_x(RX + 2.0, RY + 1.4, 0.55,
                     "".join(f'<rect x="{8 + i * 14}" y="6" width="10" height="9" rx="1.5" fill="#12141f" stroke="#5ee6ff" stroke-opacity=".4"/>' for i in range(4))))
for ax in (RX + 0.25, RX + 0.75, RX + 1.25, RX + 1.75):
    router.append(box(ax - 0.05, RY + 0.08, 0.55, 0.1, 0.1, 1.15, "#2a2e42", top="#5ee6ff"))
items.append((RX + 1 + RY + 0.7, "".join(router)))
items.append((RX + RY + 50, pill(RX + 1, RY + 0.7, 2.25, "R", "NanoPi R6S", "2.5G", "#5df2a0")))

# --- Room 1 (back-left): desks with robots facing viewer
phones = ["#a78bfa", None, "#ff9f5a", "#5ee6ff", None, "#ff7eb6"]
pi = 0
for row_y in (2.2, 6.0):
    for col_x in (2.0, 7.0):
        for k in range(2):
            rx_ = col_x + 0.9 + k * 1.8
            items.append((rx_ + row_y - 0.4, chair_back(rx_, row_y)))
            items.append((rx_ + row_y - 0.05, chair(rx_, row_y)))
            items.append((rx_ + row_y, robot(rx_, row_y, 0.46, True, phones[pi % len(phones)])))
            pi += 1
        items.append((col_x + 1.8 + row_y + 1.0, desk(col_x, row_y + 0.45, 3.6, 0.9, 2,
                                                     screen_glow=["#5ee6ff", "#5df2a0"][int(col_x) % 2])))
items.append((50, pill(4.7, 3.1, 2.3, "W", "WAN uplink", "0.8ms", "#5df2a0")))

# --- Room 2 (back-right): server racks
for i in range(6):
    x = 16.0 + i * 1.05
    items.append((x + 0.45 + 2.0 + 0.45, rack(x, 2.0, 2.15, seed=i)))
for i in range(5):
    x = 16.5 + i * 1.05
    items.append((x + 0.45 + 5.6 + 0.45, rack(x, 5.6, 1.7, seed=10 + i)))
items.append((rx_ + 60, pill(19.6, 3.0, 2.8, "S", "Switch fabric", "40 Gb", "#ffc94a")))
# technician robot in server room
items.append((26.5 + 8.6, robot(26.5, 8.6, 0, True, "#ffc94a")))
items.append((28.4 + 3.0, lamp(28.4, 3.0, 1.8)))

# --- Room 3 (front-left): lounge
under.append(floor_ellipse(5.5, 15.5, 2.6, "#3b3550", extra=' opacity=".85"'))
under.append(floor_ellipse(5.5, 15.5, 2.6, "none", extra=' stroke="#ffffff" stroke-opacity=".15" stroke-width="1.5"'))
items.append((5.5 + 15.5, cylinder(5.5, 15.5, 0, 0.9, 0.55, "#e9e1ea", "#fbf7fb")))
items.append((5.5 + 15.5 + .1, box(5.1, 15.2, 0.55, 0.5, 0.35, 0.04, "#2b2f42")))
for (bx, by, ph, fc) in [(3.9, 14.3, "#ff9f5a", True), (7.2, 15.0, None, True), (4.3, 17.2, "#a78bfa", False)]:
    items.append((bx + by - 0.05, cylinder(bx, by, 0, 0.42, 0.3, "#c56f7f", "#e08a98")))
    items.append((bx + by, robot(bx, by, 0.3, fc, ph, 0.95)))
items.append((2.0 + 12.2, plant(2.0, 12.2, 1.1, "#c9775a", "tree")))
items.append((10.8 + 19.8, plant(10.8, 19.8, 1.2, "#3b3550", "tree")))
items.append((11.8 + 12.6, plant(11.8, 12.6, 0.9, "#c9775a")))
items.append((1.6 + 20.0, lamp(1.6, 20.0, 1.9)))
items.append((9.6 + 13.0, lamp(9.6, 13.0, 1.7)))
items.append((50 + 15, pill(5.5, 15.5, 2.9, "D", "DHCP lounge", "24 leases", "#5ee6ff")))

# --- Room 4 (front-right): ops desks + sign
for row_y in (15.4,):
    for col_x in (18.6, 23.8):
        for k in range(2):
            rx_ = col_x + 0.9 + k * 1.8
            items.append((rx_ + row_y - 0.4, chair_back(rx_, row_y)))
            items.append((rx_ + row_y - 0.05, chair(rx_, row_y)))
            items.append((rx_ + row_y, robot(rx_, row_y, 0.46, True, ["#ff9f5a", "#a78bfa", None, "#5ee6ff"][int(col_x + k) % 4])))
        items.append((col_x + 1.8 + row_y + 1.0, desk(col_x, row_y + 0.45, 3.6, 0.9, 2, screen_glow="#ffc94a")))
items.append((16.4 + 19.4 + 1, iso_sign(16.4, 19.4, 0.0, "4", "Operations", "Route the packets. Guard the edge.")))
items.append((70, pill(25.6, 16.4, 2.35, "F", "Firewall", "0 drops", "#5df2a0")))
items.append((27.6 + 18.8, lamp(27.6, 18.8, 1.9)))
items.append((16.0 + 20.6, plant(15.2, 17.4, 1.0, "#c9775a")))
items.append((19.4 + 12.0, robot(19.4, 12.0, 0, True, "#5ee6ff")))

# --- partitions
items += low_wall_x(0.2, 13.0, 10.4)
items += low_wall_x(17.4, FX - 0.2, 10.4)
items += low_wall_y(13.9, 0.2, 8.4)
items += low_wall_y(13.9, 14.6, FY - 0.2)
for (px, py) in [(13.0, 10.0), (17.6, 10.0), (12.6, 9.0), (13.4, 13.8)]:
    items.append((px + py + 0.6, plant(px, py, 0.85, "#3b3550")))

# --- hedges along the open front edges
for j in range(1, FY, 2):
    items.append((FX - 0.6 + j, hedge(FX - 0.6, j + 0.5)))
for i in range(1, 12, 2):
    items.append((i + FY - 0.6, hedge(i + 0.5, FY - 0.6)))

items.sort(key=lambda t: t[0])

# ---------------------------------------------------------------- output
defs = f"""
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#241d36"/>
    <stop offset=".45" stop-color="#5e4a78"/>
    <stop offset="1" stop-color="#b48aae"/>
  </linearGradient>
  <radialGradient id="warm" cx=".55" cy=".55" r=".6">
    <stop offset="0" stop-color="#ffd6c2" stop-opacity=".35"/>
    <stop offset="1" stop-color="#ffd6c2" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="vig" cx=".5" cy=".5" r=".75">
    <stop offset=".55" stop-color="#1a1428" stop-opacity="0"/>
    <stop offset="1" stop-color="#1a1428" stop-opacity=".55"/>
  </radialGradient>
  <radialGradient id="rw" cx=".35" cy=".3" r=".9">
    <stop offset="0" stop-color="#ffffff"/>
    <stop offset=".6" stop-color="#f1edf6"/>
    <stop offset="1" stop-color="#c9bfd8"/>
  </radialGradient>
  <radialGradient id="halo">
    <stop offset="0" stop-color="#fff2d8" stop-opacity=".6"/>
    <stop offset=".35" stop-color="#ffd9c0" stop-opacity=".18"/>
    <stop offset="1" stop-color="#ffd9c0" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="padglow">
    <stop offset=".55" stop-color="#5ee6ff" stop-opacity=".35"/>
    <stop offset="1" stop-color="#5ee6ff" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="cyl" x1="0" x2="1">
    <stop offset="0" stop-color="#fff" stop-opacity=".18"/>
    <stop offset=".45" stop-color="#fff" stop-opacity="0"/>
    <stop offset="1" stop-color="#2a1040" stop-opacity=".28"/>
  </linearGradient>
  <linearGradient id="scr" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#232a45"/>
    <stop offset="1" stop-color="#151a2c"/>
  </linearGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
</defs>"""

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W_VIEW} {H_VIEW}" '
       f'preserveAspectRatio="xMidYMid slice" font-family="Outfit,\'Helvetica Neue\',Arial,sans-serif">',
       defs,
       f'<rect width="{W_VIEW}" height="{H_VIEW}" fill="url(#sky)"/>',
       # faint far-away bokeh blobs
       '<g filter="url(#soft)" opacity=".5">'
       '<circle cx="140" cy="160" r="60" fill="#ff9fc8" opacity=".25"/>'
       '<circle cx="1800" cy="120" r="90" fill="#a78bfa" opacity=".25"/>'
       '<circle cx="1760" cy="980" r="120" fill="#ffc6a8" opacity=".25"/></g>',
       "".join(floor), "".join(walls), "".join(under),
       "".join(s for _, s in items),
       f'<rect width="{W_VIEW}" height="{H_VIEW}" fill="url(#warm)"/>',
       f'<rect width="{W_VIEW}" height="{H_VIEW}" fill="url(#vig)"/>',
       "</svg>"]

out_path = os.path.join(os.path.dirname(__file__), "..", "htdocs", "luci-static", "office", "bg.svg")
with open(out_path, "w") as fh:
    fh.write("".join(svg))
print("wrote", os.path.abspath(out_path), os.path.getsize(out_path), "bytes")
