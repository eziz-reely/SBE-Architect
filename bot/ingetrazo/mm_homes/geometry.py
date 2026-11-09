# SPDX-License-Identifier: GPL-3.0-or-later
"""MM Homes model.json -> 3D parts for IngeTrazo (metres, X east, Y north, Z up).

Pure Python, no Qt and no IngeTrazo imports, so it can be tested anywhere.
The geometry follows the SBE-Architect editor's 3D/SketchUp export
(bot/sablons/redaktors/lapa.html, skpRb): outer walls by the plan outline with
window / door / gable-window openings, partitions between rooms, floor slab,
loft slab, gable or hip roof, stairs, plus an optional terrace.

Plan coordinates in model.json are millimetres, x east and y SOUTH. They are
mapped to (x, D - y, z) / 1000, so north is +Y like in IngeTrazo.

build(model) returns a list of parts:
    {"name", "ifc", "color", "faces": [(loop, holes, color_or_None, opacity_or_None), ...]}
Every part with a solid is a watertight set of faces (see tests/test_geometry.py).
"""
from __future__ import annotations

import json
import math

T_DEFAULT, T_PART = 283.5, 195.0      # exterior wall / partition thickness, mm
ROOF_TH, FLOOR_TH = 295.0, 300.0
PANEL_DEFAULT = 164.5

TONES = {   # bot/sablons/mm-config.json -> toni
    "peleks": {"sw": "#3B3C40", "logi": "RAL 7016"}, "sarkans": {"sw": "#7A382A", "logi": "RAL 9016"},
    "koks": {"sw": "#A56D37", "logi": "RAL 7016"}, "zals": {"sw": "#46564A", "logi": "RAL 9016"},
    "balts": {"sw": "#BABBC0", "logi": "RAL 9005"},
}
RAL = {"RAL 7016": "#383E42", "RAL 7024": "#474A50", "RAL 7021": "#2F3234", "RAL 7035": "#C5C7C4", "RAL 9005": "#0E0E10",
       "RAL 9010": "#F1ECE1", "RAL 9016": "#F1F0EA", "RAL 8017": "#45322E", "RAL 8019": "#3D3635"}
CLR_INT, CLR_ROOF, CLR_GLASS, CLR_STAIR, CLR_DECK, CLR_CONCRETE = "#f2efe9", "#40464b", "#9fc3d6", "#c9a77c", "#3d4247", "#9a9a96"


def rgb(hex_):
    h = (hex_ or "#888888").lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


# ---------------- vector helpers ----------------
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))


def unit(a):
    l = length(a)
    return (a[0] / l, a[1] / l, a[2] / l) if l > 1e-12 else (0.0, 0.0, 1.0)


def newell(loop):
    nx = ny = nz = 0.0
    for i, a in enumerate(loop):
        b = loop[(i + 1) % len(loop)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return (nx, ny, nz)


def dedupe(loop, tol=0.0005):
    out = [p for i, p in enumerate(loop) if length(sub(p, loop[i - 1])) > tol]
    return out if len(out) > 2 else []


def solid(outer, holes, d, direction):
    """Closed prism: `outer` (+ `holes`) extruded by `d` metres to the side `direction` points to.
    Returns a list of (loop, holes) faces with outward winding."""
    outer = dedupe(outer)
    if len(outer) < 3 or d <= 0:
        return []
    n = unit(newell(outer))
    if dot(n, direction) < 0:
        n = mul(n, -1.0)

    def orient(loop, ccw):
        return loop if (dot(newell(loop), n) > 0) == ccw else loop[::-1]

    outer = orient(outer, True)
    holes = [orient(dedupe(h), False) for h in holes if len(dedupe(h)) > 2]
    off = mul(n, d)
    shift = lambda loop: [add(p, off) for p in loop]
    faces = [(outer[::-1], [h[::-1] for h in holes]), (shift(outer), [shift(h) for h in holes])]
    for loop in [outer, *holes]:
        for i, a in enumerate(loop):
            b = loop[(i + 1) % len(loop)]
            faces.append(([a, b, add(b, off), add(a, off)], []))
    return [(l, h, None, None) for l, h in faces]


# ---------------- model ----------------
class Ctx:
    def __init__(self, m):
        self.m = m
        self.W, self.D = float(m["W"]), float(m["D"])
        J = m.get("jumts") or {}
        self.J = J
        self.pitch = float(J.get("pitch") or 30)
        self.tan = math.tan(math.radians(self.pitch))
        self.eave = float(J.get("eave") or 2600)
        self.ov = float(J.get("ov") or 0)
        self.T, self.t = T_DEFAULT, T_PART
        self.ceil = float(m.get("ceiling") or (self.eave - 300))
        loft = m.get("loft") or {}
        self.panel = (loft["level"] - m["ceiling"]) if loft.get("level") and m.get("ceiling") else PANEL_DEFAULT
        self.H2 = float(loft["level"]) if loft.get("level") else self.ceil + self.panel
        hip = float(J.get("hip") or 0)
        if not hip and str(J.get("forma", "")).lower().startswith(("cetr", "četr")):
            hip = self.pitch
        self.tanH = math.tan(math.radians(hip)) if hip else 0.0
        poly = m.get("poly")
        self.poly = [(float(p[0]), float(p[1])) for p in poly] if poly and len(poly) > 2 else [(0, 0), (self.W, 0), (self.W, self.D), (0, self.D)]
        P = m.get("projekts") or {}
        self.P = P
        self.tone = P.get("tonis") if P.get("tonis") in TONES else "peleks"
        self.edges = self._edges()

    def P3(self, p):   # plan mm -> metres, north = +Y
        return (p[0] / 1000.0, (self.D - p[1]) / 1000.0, p[2] / 1000.0)

    def V3(self, v):   # direction
        return (v[0], -v[1], v[2])

    def roof_z(self, x, y):
        return self.eave + min(min(y, self.D - y) * self.tan, min(x, self.W - x) * self.tanH if self.tanH else math.inf)

    def in_poly(self, px, py):
        c = False
        j = len(self.poly) - 1
        for i, (xi, yi) in enumerate(self.poly):
            xj, yj = self.poly[j]
            if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
                c = not c
            j = i
        return c

    def _edges(self):
        out = []
        for i, a in enumerate(self.poly):
            b = self.poly[(i + 1) % len(self.poly)]
            L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            n = (-d[1], d[0])
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            if not self.in_poly(mx + n[0] * 5, my + n[1] * 5):
                n = (-n[0], -n[1])
            o = "h" if abs(d[1]) < 1e-6 else "v" if abs(d[0]) < 1e-6 else "d"
            st = (a[1] if n[1] > 0 else a[1] - self.T) if o == "h" else (a[0] if n[0] > 0 else a[0] - self.T) if o == "v" else None
            lo = min(a[0], b[0]) if o == "h" else min(a[1], b[1])
            hi = max(a[0], b[0]) if o == "h" else max(a[1], b[1])
            out.append({"a": a, "b": b, "L": L, "d": d, "n": n, "o": o, "st": st, "lo": lo, "hi": hi})
        return out

    def on_edge(self, o, s, p0, p1):
        for e in self.edges:
            if e["o"] == o and e["st"] is not None and abs(e["st"] - s) < 2 and p0 >= e["lo"] - 2 and p1 <= e["hi"] + 2:
                return e
        return None

    def gw_pts(self, g):
        west = g["side"] == "west"
        yy = (lambda u: self.D - u) if west else (lambda u: u)
        u0, u1, xs = g["u0"], g["u1"], (0.0 if west else self.W)
        top = lambda u: self.roof_z(xs, yy(u)) - 350
        if g.get("win"):
            pts = [(u0, g["z0"]), (u1, g["z0"]), (u1, g["z1"]), (u0, g["z1"])]
        else:
            pts = [(u0, g["z0"]), (u1, g["z0"]), (u1, top(u1))]
            um = self.D / 2
            if min(u0, u1) < um < max(u0, u1):
                pts.append((um, top(um)))
            pts.append((u0, top(u0)))
        return [(yy(u), z) for u, z in pts]


def wall_outer(c, p0, p1, top, notches):
    """Wall outline in a vertical plane: base p0->p1 at z=0 (plan mm) with door notches, then `top` (p1 -> p0)."""
    d = unit(sub(p1, p0))
    pts = [p0]
    for u0, u1, zt in sorted(notches):
        pts += [add(p0, mul(d, u0)), (p0[0] + d[0] * u0, p0[1] + d[1] * u0, zt), (p0[0] + d[0] * u1, p0[1] + d[1] * u1, zt), add(p0, mul(d, u1))]
    pts.append(p1)
    return pts + top


def _tone_colors(c):
    t = TONES[c.tone]
    wall = c.P.get("sienas_hex") or t["sw"]
    frame = RAL.get(c.P.get("logu_tonis") or t["logi"], "#383E42")
    plinth = CLR_CONCRETE if c.P.get("pamati") == "platne" else RAL.get(c.P.get("cokols") or "RAL 9005", "#0E0E10")
    return wall, frame, plinth


def build(m, tone=None):
    c = Ctx(m)
    if tone in TONES:
        c.tone = tone
    wall_hex, frame_hex, plinth_hex = _tone_colors(c)
    W, D, T = c.W, c.D, c.T
    parts = []

    def part(name, ifc, color, faces):
        if faces:
            parts.append({"name": name, "ifc": ifc, "color": color, "faces": faces})

    P3 = c.P3
    # ---- exterior doors and walls ----
    doors = m.get("doors") or []
    ex_doors = [d for d in doors if c.on_edge(d["o"], d["y"] if d["o"] == "h" else d["x"], d["x"] if d["o"] == "h" else d["y"], (d["x"] if d["o"] == "h" else d["y"]) + d["w"])]
    wins = [w for w in (m.get("windows") or []) if not w.get("shape")]
    for ei, e in enumerate(c.edges):
        (ax, ay), (bx, by) = e["a"], e["b"]
        N = max(2, math.ceil(e["L"] / 100))
        top = [(ax + (bx - ax) * k / N, ay + (by - ay) * k / N) for k in range(N, -1, -1)]
        top3 = [(x, y, c.roof_z(x, y)) for x, y in top]
        top3 = [p for i, p in enumerate(top3) if i in (0, len(top3) - 1) or abs((p[2] - top3[i - 1][2]) - (top3[i + 1][2] - p[2])) > 0.5]
        notches, holes, glazing, leaves = [], [], [], []
        at = (lambda u, z: (u, ay, z)) if e["o"] == "h" else (lambda u, z: (ax, u, z))
        proj = lambda u: (u - ax) * e["d"][0] if e["o"] == "h" else (u - ay) * e["d"][1]   # distance along a->b
        if e["o"] != "d":
            for w in wins:
                if w["o"] != e["o"]:
                    continue
                u = w["x"] if e["o"] == "h" else w["y"]
                if c.on_edge(e["o"], w["y"] if e["o"] == "h" else w["x"], u, u + w["len"]) is not e:
                    continue
                rect = [at(u, w["sill"]), at(u + w["len"], w["sill"]), at(u + w["len"], w["head"]), at(u, w["head"])]
                if w["sill"] <= 1:
                    a0, a1 = sorted((proj(u), proj(u + w["len"])))
                    notches.append((a0, a1, w["head"]))
                else:
                    holes.append(rect)
                glazing.append(("win", rect, w))
            for d in ex_doors:
                if d["o"] != e["o"]:
                    continue
                u = d["x"] if e["o"] == "h" else d["y"]
                if c.on_edge(d["o"], d["y"] if e["o"] == "h" else d["x"], u, u + d["w"]) is not e:
                    continue
                a0, a1 = sorted((proj(u), proj(u + d["w"])))
                notches.append((a0, a1, 2100.0))
                leaves.append((at(u, 0), at(u + d["w"], 0), at(u + d["w"], 2100), at(u, 2100), d))
            if e["o"] == "v" and (abs(ax) < 1 or abs(ax - W) < 1):
                for g in m.get("gableWins") or []:
                    if g["side"] == ("west" if abs(ax) < 1 else "east"):
                        pp = c.gw_pts(g)
                        if all(e["lo"] - 1 <= y <= e["hi"] + 1 for y, _ in pp):
                            h = [(ax, y, z) for y, z in pp]
                            holes.append(h)
                            glazing.append(("gable", h, g))
        outer = wall_outer(c, (ax, ay, 0.0), (bx, by, 0.0), top3, notches)
        n3 = c.V3((e["n"][0], e["n"][1], 0.0))
        part(f"Ārsiena {ei + 1}", "IfcWall", wall_hex, solid([P3(p) for p in outer], [[P3(p) for p in h] for h in holes], T / 1000.0, n3))
        mid = lambda p: (p[0] + e["n"][0] * T / 2, p[1] + e["n"][1] * T / 2, p[2])
        for k, (kind, rect, src) in enumerate(glazing):
            gl = [mid(p) for p in rect]
            if kind == "win":
                fw = 60.0
                u_dir = unit(sub(rect[1], rect[0]))
                inner = [add(add(gl[0], mul(u_dir, fw)), (0, 0, fw)), add(sub(gl[1], mul(u_dir, fw)), (0, 0, fw)),
                         sub(sub(gl[2], mul(u_dir, fw)), (0, 0, fw)), sub(add(gl[3], mul(u_dir, fw)), (0, 0, fw))]
                inner = [(p[0], p[1], p[2]) for p in inner]
                shiftn = lambda p: (p[0] - e["n"][0] * 40, p[1] - e["n"][1] * 40, p[2])
                faces = solid([P3(shiftn(p)) for p in gl], [[P3(shiftn(p)) for p in inner]], 0.08, n3)
                faces.append(([P3(p) for p in inner], [], rgb(CLR_GLASS), 0.35))
                part(f"Logs {ei + 1}.{k + 1}", "IfcWindow", frame_hex, faces)
            else:
                part(f"Slīpais logs {ei + 1}.{k + 1}", "IfcWindow", frame_hex, [([P3(p) for p in gl], [], rgb(CLR_GLASS), 0.35)])
        for k, (a, b, cc, dd_, d) in enumerate(leaves):
            pts = [mid(p) for p in (a, b, cc, dd_)]
            part(f"Ārdurvis {ei + 1}.{k + 1}", "IfcDoor", frame_hex, solid([P3(p) for p in pts], [], 0.06, n3))

    # ---- partitions between rooms (gaps of 100..200 mm) ----
    R = [r for room in (m.get("rooms") or []) for r in room.get("r", [])]
    in_room = lambda px, py: any(rx < px < rx + rw and ry < py < ry + rh for rx, ry, rw, rh in R)
    seg_d = lambda px, py, a, b: _seg_d(px, py, a, b)
    inside = lambda px, py: c.in_poly(px, py) and all(seg_d(px, py, e["a"], e["b"]) > T - 1 for e in c.edges)

    def reach(px, py, dx, dy):
        e = 0
        while e <= 260:
            qx, qy = px + dx * (e + 2.5), py + dy * (e + 2.5)
            if in_room(qx, qy) or not inside(qx, qy):
                return e
            e += 5
        return 0

    walls, seen = [], set()
    for a in R:
        for b in R:
            if a is b:
                continue
            gx, gy = b[0] - (a[0] + a[2]), b[1] - (a[1] + a[3])
            if 100 <= gx <= 200:
                y0, y1 = max(a[1], b[1]), min(a[1] + a[3], b[1] + b[3])
                if y1 - y0 > 50:
                    walls.append([a[0] + a[2], y0, gx, y1 - y0, "v"])
            if 100 <= gy <= 200:
                x0, x1 = max(a[0], b[0]), min(a[0] + a[2], b[0] + b[2])
                if x1 - x0 > 50:
                    walls.append([x0, a[1] + a[3], x1 - x0, gy, "h"])
    ceil = c.ceil
    for x, y, w, h, o in walls:
        k = tuple(round(v, 1) if not isinstance(v, str) else v for v in (x, y, w, h, o))
        if k in seen:
            continue
        seen.add(k)
        if o == "v":
            a_, b_ = reach(x + w / 2, y, 0, -1), reach(x + w / 2, y + h, 0, 1)
            y, h = y - a_, h + a_ + b_
        else:
            a_, b_ = reach(x, y + h / 2, -1, 0), reach(x + w, y + h / 2, 1, 0)
            x, w = x - a_, w + a_ + b_
        ds = [d for d in doors if d not in ex_doors and d["o"] == o and
              ((abs(d["x"] - x) < 30 and d["y"] < y + h and d["y"] + d["w"] > y) if o == "v" else (abs(d["y"] - y) < 30 and d["x"] < x + w and d["x"] + d["w"] > x))]
        if o == "v":
            p0, p1 = (x, y, 0.0), (x, y + h, 0.0)
            top = [(x, y + h, ceil), (x, y, ceil)]
            nt = [(max(0.0, d["y"] - y), min(h, d["y"] + d["w"] - y), 2100.0) for d in ds]
            dirv, thick = (1.0, 0.0, 0.0), w
        else:
            p0, p1 = (x, y, 0.0), (x + w, y, 0.0)
            top = [(x + w, y, ceil), (x, y, ceil)]
            nt = [(max(0.0, d["x"] - x), min(w, d["x"] + d["w"] - x), 2100.0) for d in ds]
            dirv, thick = (0.0, 1.0, 0.0), h
        outer = wall_outer(c, p0, p1, top, nt)
        part("Starpsiena", "IfcWall", CLR_INT, solid([P3(p) for p in outer], [], thick / 1000.0, c.V3(dirv)))

    # ---- floor slab, loft slab ----
    part("Grīda", "IfcSlab", plinth_hex, solid([P3((x, y, -FLOOR_TH)) for x, y in c.poly], [], FLOOR_TH / 1000.0, (0, 0, 1)))
    loft = m.get("loft")
    if loft:
        for room in loft.get("rooms") or []:
            if room.get("void"):
                continue
            for x, y, w, h in room.get("r", []):
                part("Mansarda pārsegums", "IfcSlab", CLR_INT, solid([P3(p) for p in [(x, y, ceil), (x + w, y, ceil), (x + w, y + h, ceil), (x, y + h, ceil)]], [], (c.H2 - ceil) / 1000.0, (0, 0, 1)))

    # ---- roof ----
    ov, tan = c.ov, c.tan
    zE = c.eave - ov * tan
    zR = zE + (D / 2 + ov) * tan
    rI = min((D / 2 + ov) * tan / c.tanH, W / 2 + ov) if c.tanH else 0.0
    rth = ROOF_TH / 1000.0
    roof = [
        ("Jumts ziemeļi", [(-ov, -ov, zE), (W + ov, -ov, zE), (W + ov - rI, D / 2, zR), (-ov + rI, D / 2, zR)], (0, -1, 2)),
        ("Jumts dienvidi", [(-ov, D + ov, zE), (W + ov, D + ov, zE), (W + ov - rI, D / 2, zR), (-ov + rI, D / 2, zR)], (0, 1, 2)),
    ]
    if c.tanH:
        roof += [("Jumts rietumi", [(-ov, -ov, zE), (-ov, D + ov, zE), (-ov + rI, D / 2, zR)], (-1, 0, 2)),
                 ("Jumts austrumi", [(W + ov, -ov, zE), (W + ov, D + ov, zE), (W + ov - rI, D / 2, zR)], (1, 0, 2))]
    for name, pts, dv in roof:
        part(name, "IfcRoof", CLR_ROOF, solid([P3(p) for p in pts], [], rth, c.V3(dv)))

    # ---- stairs (solid steps up to the loft floor) ----
    for f0 in m.get("furniture") or []:
        rot = f0 if f0 and f0[0] == "_rot" else None
        f = rot[4] if rot else f0
        if not f or not isinstance(f[0], str):
            continue
        k = f[0].rstrip("13")
        if k not in ("kapnes", "kapnesL"):
            continue
        blocks = []
        if k == "kapnes":
            _, x, y, w, h, up = (list(f) + [None] * 6)[:6]
            n = max(2, round(c.H2 / 180))
            go = w / n
            for i in range(n):
                a = x + w - (i + 1) * go if up == "w" else x + i * go
                blocks.append((a, y, a + go, y + h, (i + 1) * c.H2 / n))
        else:
            vals = list(f) + [None] * 9
            x, y, w, h = vals[1:5]
            b0 = vals[5] if vals[5] is not None else 900
            side = vals[6] or "r"
            rev = vals[8] or 0
            b = min(b0, w - 300, h - 300)
            x1, y1 = x + w - b, y + h - b
            X = (lambda u: 2 * x + w - u) if side == "l" else (lambda u: u)
            n1, n2 = max(2, round((x1 - x) / 250)), max(2, round((y1 - y) / 250))
            r = c.H2 / (n1 + n2 + 1)
            s1, s2 = (x1 - x) / n1, (y1 - y) / n2
            seq = [(x + i * s1, y1, x + (i + 1) * s1, y + h) for i in range(n1)] + [(x1, y1, x + w, y + h)] + \
                  [(x1, y1 - (i + 1) * s2, x + w, y1 - i * s2) for i in range(n2)]
            if rev:
                seq.reverse()
            for i, q in enumerate(seq):
                xa, xb = X(q[0]), X(q[2])
                blocks.append((min(xa, xb), q[1], max(xa, xb), q[3], (i + 1) * r))

        def tf(px, py):
            if not rot:
                return px, py
            a = math.radians(rot[1])
            dx, dy = px - rot[2], py - rot[3]
            return rot[2] + dx * math.cos(a) - dy * math.sin(a), rot[3] + dx * math.sin(a) + dy * math.cos(a)

        faces = []
        for xa, ya, xb, yb, z in blocks:
            g_ = 0.5   # 1 mm gap between steps: each step stays its own watertight solid
            base = [(*tf(px, py), 0.0) for px, py in ((xa + g_, ya + g_), (xb - g_, ya + g_), (xb - g_, yb - g_), (xa + g_, yb - g_))]
            faces += solid([P3(p) for p in base], [], z / 1000.0, (0, 0, 1))
        part("Kāpnes", "IfcStair", CLR_STAIR, faces)

    # ---- terrace ----
    t = m.get("terase")
    if t and t.get("side"):
        dp, a, b = float(t.get("depth") or 1100), float(t.get("a") or 0), float(t.get("b") or 0)
        rect = {"south": (-a, D, W + b, D + dp), "north": (-a, -dp, W + b, 0), "west": (-dp, -a, 0, D + b), "east": (W, -a, W + dp, D + b)}.get(t["side"])
        if rect:
            x0, y0, x1, y1 = rect
            base = [(x0, y0, -FLOOR_TH), (x1, y0, -FLOOR_TH), (x1, y1, -FLOOR_TH), (x0, y1, -FLOOR_TH)]
            part("Terase", "IfcSlab", CLR_DECK, solid([P3(p) for p in base], [], (FLOOR_TH - 25) / 1000.0, (0, 0, 1)))
    return parts


def _seg_d(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = dx * dx + dy * dy or 1.0
    u = max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / l))
    return math.hypot(px - a[0] - u * dx, py - a[1] - u * dy)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def summary(parts):
    cnt = {}
    for p in parts:
        cnt[p["ifc"]] = cnt.get(p["ifc"], 0) + 1
    return cnt
