"""Ražošanas lapas A3 (horizontāli): 1. lapa = projekta skice, tālāk karkasa plāns, katra ārsiena un starpsiena ar detaļām
un kvadratūru, jumts (spāres), detaļu kopsavilkums un materiālu tāme pa pīrāgiem.

    python karkass_lapas.py <model.json> [izvades.html]

Izvade pēc noklusējuma: <modeļa mape>/rasejumi/<id>_razosana.html (atver pārlūkā, drukā A3 horizontāli vai saglabā PDF).
Rakstlaukumā: modeļa nosaukums, klienta vārds (projekts.klients), datums. Bez ražotāja zīmola.
"""
import datetime
import html
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import karkass as KK  # noqa: E402
import tame as TM  # noqa: E402

PW, PH = 420.0, 297.0
INK, ACC, MUT = '#1f2328', '#2266d8', '#6b7280'
COL = {'bottom_plate': '#b9a27a', 'top_plate': '#b9a27a', 'stud': '#e8d6ae', 'junction': '#e8d6ae', 'junction_rot': '#d9c08e', 'king': '#e8d6ae',
       'jack': '#dcc596', 'cripple': '#efe2c4', 'header': '#c49a5a', 'sill': '#c9b083', 'nogging': '#d8c7a2'}
SCALES = [20, 25, 50, 75, 100, 150, 200]
esc = lambda s: html.escape(str(s))
f0 = lambda v: f'{v:.0f}'
fm2 = lambda v: f'{v:.1f}'.replace('.', ',')


def scale_for(w_mm, h_mm, bw, bh):
    need = max(w_mm / bw, h_mm / bh)
    return next((s for s in SCALES if s >= need), math.ceil(need / 50) * 50)


class Doc:
    def __init__(self, m):
        pr = m.get('projekts') or {}
        ar = pr.get('ar') or {}
        self.model = pr.get('modela_nosaukums') or m.get('nosaukums') or m.get('id')
        self.mid = m.get('id', '')
        self.client = pr.get('klients') or ((ar.get('data') or {}).get('pasutitajs')) or ''
        self.date = (ar.get('tb') or {}).get('date') or pr.get('datums') or datetime.date.today().strftime('%d.%m.%Y')
        self.pages = []

    def frame(self, title, body, sub=''):
        n = len(self.pages) + 1
        tb = (f'<g font-family="Barlow,Arial,sans-serif">'
              f'<rect x="8" y="8" width="{PW - 16}" height="{PH - 16}" fill="none" stroke="{INK}" stroke-width=".5"/>'
              f'<text x="13" y="17" font-size="6" font-weight="700" fill="{INK}">{esc(title)}</text>'
              f'<text x="13" y="22.5" font-size="3.2" fill="{MUT}">{esc(sub)}</text>'
              f'<rect x="8" y="{PH - 20}" width="{PW - 16}" height="12" fill="#f4f5f7" stroke="{INK}" stroke-width=".4"/>'
              + ''.join(f'<text x="{x}" y="{PH - 15.6}" font-size="2.4" fill="{MUT}">{k}</text><text x="{x}" y="{PH - 10.4}" font-size="4" font-weight="600" fill="{INK}">{esc(v)}</text>'
                        for x, k, v in ((13, 'MODEĻA NOSAUKUMS', f'{self.model}  ·  {self.mid}'), (150, 'KLIENTA VĀRDS', self.client or '—'), (265, 'DATUMS', self.date)))
              + f'<line x1="{PW - 40}" y1="{PH - 20}" x2="{PW - 40}" y2="{PH - 8}" stroke="{INK}" stroke-width=".4"/>'
              f'<text x="{PW - 36}" y="{PH - 15.6}" font-size="2.4" fill="{MUT}">LAPA</text><text x="{PW - 36}" y="{PH - 10.4}" font-size="4.4" font-weight="700" fill="{ACC}">{n}/@@N@@</text></g>')
        self.pages.append(f'<section class="pg"><svg viewBox="0 0 {PW} {PH}" xmlns="http://www.w3.org/2000/svg">{tb}{body}</svg></section>')

    def raw(self, inner):
        self.pages.append(f'<section class="pg">{inner}</section>')


def table_svg(x, y, rows, cols, widths, fs=2.6, rh=3.8, head=True):
    """Tabula SVG: rows = saraksts ar šūnām; cols = virsraksti."""
    out = [f'<g font-family="Barlow,Arial,sans-serif" font-size="{fs}" fill="{INK}">']
    W = sum(widths)
    yy = y
    if head:
        out.append(f'<rect x="{x}" y="{yy}" width="{W}" height="{rh + .6}" fill="{INK}"/>')
        cx = x
        for c, w in zip(cols, widths):
            out.append(f'<text x="{cx + 1}" y="{yy + rh - .9}" fill="#fff" font-weight="600">{esc(c)}</text>')
            cx += w
        yy += rh + .6
    for i, r in enumerate(rows):
        if i % 2:
            out.append(f'<rect x="{x}" y="{yy}" width="{W}" height="{rh}" fill="#f2f3f5"/>')
        cx = x
        for j, (c, w) in enumerate(zip(r, widths)):
            num = isinstance(c, (int, float)) or bool(re.fullmatch(r'-?\d+([.,]\d+)?', str(c)))
            tx = cx + w - 1 if num else cx + 1
            anc = ' text-anchor="end"' if num else ''
            out.append(f'<text x="{tx}" y="{yy + rh - 1}"{anc}>{esc(c)}</text>')
            cx += w
        yy += rh
    out.append(f'<line x1="{x}" y1="{yy}" x2="{x + W}" y2="{yy}" stroke="{INK}" stroke-width=".3"/></g>')
    return ''.join(out), yy


def panel_svg(P, x0, y0, bw, bh, chain=True):
    """Paneļa skats no ārpuses mērogā, kas ietilpst lodziņā bw×bh (mm uz lapas). Atgriež (svg, mērogs, apakšas y)."""
    Ht = max(z for _, z in P.top)
    s = scale_for(P.L + 1200, Ht + 900, bw, bh)
    k = 1 / s
    ox = x0 + (bw - P.L * k) / 2
    oy = y0 + 9 + Ht * k                      # grīdas līnija uz lapas
    X = lambda u: ox + u * k
    Y = lambda z: oy - z * k
    g = ['<g font-family="Barlow,Arial,sans-serif">']
    # paneļa kontūra
    pts = [(0, 0)] + list(P.top) + [(P.L, 0)]
    g.append(f'<polygon points="{" ".join(f"{X(u):.2f},{Y(z):.2f}" for u, z in pts)}" fill="#fbfaf7" stroke="{INK}" stroke-width=".35"/>')
    for q in sorted(P.m, key=lambda q: 0 if q['loma'] in ('bottom_plate', 'top_plate') else 1):
        c = COL.get(q['loma'], '#ddd')
        if q['nos'] == 'SLIPAIS':
            continue
        if q['nos'] == 'VERT.SLIPAIS':
            u0, u1 = q['u0'], q['u1']
            pl = 2 * KK.B * math.sqrt(1 + P.slope_at((u0 + u1) / 2) ** 2)
            pp = [(u0, q['z0']), (u1, q['z0']), (u1, P.top_at(u1) - pl), (u0, P.top_at(u0) - pl)]
            g.append(f'<polygon points="{" ".join(f"{X(u):.2f},{Y(z):.2f}" for u, z in pp)}" fill="{c}" stroke="#7a6440" stroke-width=".15"/>')
            continue
        g.append(f'<rect x="{X(q["u0"]):.2f}" y="{Y(q["z1"]):.2f}" width="{max((q["u1"] - q["u0"]) * k, .15):.2f}" height="{max((q["z1"] - q["z0"]) * k, .15):.2f}" fill="{c}" stroke="#7a6440" stroke-width=".15"/>')
    # slīpie augšgulšņi kā josla zem jumta līnijas
    for (u0, z0), (u1, z1) in zip(P.top, P.top[1:]):
        if abs(z1 - z0) > 1:
            kk = math.sqrt(1 + ((z1 - z0) / (u1 - u0)) ** 2)
            pp = [(u0, z0), (u1, z1), (u1, z1 - 2 * KK.B * kk), (u0, z0 - 2 * KK.B * kk)]
            g.append(f'<polygon points="{" ".join(f"{X(u):.2f},{Y(z):.2f}" for u, z in pp)}" fill="{COL["top_plate"]}" stroke="#7a6440" stroke-width=".15"/>')
    # ailas
    for o in P.opens:
        g.append(f'<rect x="{X(o["u0"]):.2f}" y="{Y(o["head"]):.2f}" width="{(o["u1"] - o["u0"]) * k:.2f}" height="{(o["head"] - o["sill"]) * k:.2f}" fill="#eaf1fc" stroke="{ACC}" stroke-width=".3" stroke-dasharray="1 .6"/>')
        cx, cy = X((o['u0'] + o['u1']) / 2), Y((o['head'] + o['sill']) / 2)
        g.append(f'<text x="{cx:.2f}" y="{cy:.2f}" font-size="2.3" text-anchor="middle" fill="{ACC}" font-weight="600">{f0(o["u1"] - o["u0"])}×{f0(o["head"] - o["sill"])}</text>')
        if o['sill'] > 0:
            g.append(f'<text x="{cx:.2f}" y="{cy + 2.8:.2f}" font-size="1.9" text-anchor="middle" fill="{ACC}">parapets {f0(o["sill"])}</text>')
    # izmēri: kopgarums augšā, augstums labajā pusē, statņu ordinātas apakšā
    yt = Y(Ht) - 4
    g.append(f'<line x1="{X(0):.2f}" y1="{yt:.2f}" x2="{X(P.L):.2f}" y2="{yt:.2f}" stroke="{INK}" stroke-width=".2"/>'
             f'<line x1="{X(0):.2f}" y1="{yt - 1:.2f}" x2="{X(0):.2f}" y2="{yt + 1:.2f}" stroke="{INK}" stroke-width=".2"/><line x1="{X(P.L):.2f}" y1="{yt - 1:.2f}" x2="{X(P.L):.2f}" y2="{yt + 1:.2f}" stroke="{INK}" stroke-width=".2"/>'
             f'<text x="{(X(0) + X(P.L)) / 2:.2f}" y="{yt - .8:.2f}" font-size="2.8" text-anchor="middle" font-weight="600">{f0(P.L)}</text>')
    xr = X(P.L) + 4
    hs = sorted({round(P.top[0][1]), round(Ht), round(P.top[-1][1])})
    for i, h in enumerate(hs):
        xx = xr + i * 4
        g.append(f'<line x1="{xx:.2f}" y1="{Y(0):.2f}" x2="{xx:.2f}" y2="{Y(h):.2f}" stroke="{INK}" stroke-width=".2"/>'
                 f'<text transform="translate({xx - .6:.2f} {(Y(0) + Y(h)) / 2:.2f}) rotate(-90)" font-size="2.3" text-anchor="middle">{h}</text>')
    if chain:
        us = sorted({round(q['u0']) for q in P.m if q['nos'].startswith('VERT')})
        yb = Y(0) + 2
        g.append(f'<line x1="{X(0):.2f}" y1="{yb:.2f}" x2="{X(P.L):.2f}" y2="{yb:.2f}" stroke="{INK}" stroke-width=".15"/>')
        last = -9
        for u in us:
            xx = X(u)
            g.append(f'<line x1="{xx:.2f}" y1="{yb - .8:.2f}" x2="{xx:.2f}" y2="{yb + .8:.2f}" stroke="{INK}" stroke-width=".15"/>')
            if xx - last >= 1.9:
                g.append(f'<text transform="translate({xx + .7:.2f} {yb + 1.4:.2f}) rotate(90)" font-size="1.7">{u}</text>')
                last = xx
        bottom = yb + 9
    else:
        bottom = Y(0) + 2
    g.append(f'<text x="{x0 + bw:.2f}" y="{y0 + 3:.2f}" font-size="2.6" text-anchor="end" fill="{MUT}">M 1:{s}</text></g>')
    return ''.join(g), s, bottom


def parts_rows(P):
    return [(n, f'{b}×{h}', g, c) for n, h, b, g, c in KK.cutlist([P])]


def wall_page(D, P):
    g, nn = P.area()
    rows = parts_rows(P)
    nrow = (len(rows) + 1) // 2
    tab_h = 4.6 + 3.9 * nrow
    svg, s, yb = panel_svg(P, 14, 26, 392, PH - 26 - 26 - tab_h - 6)
    cols, w = ('Detaļa', 'Šķērsgr.', 'Garums, mm', 'Gab.'), (34, 18, 20, 11)
    ty = min(yb + 4, PH - 24 - tab_h)
    t1, e1 = table_svg(14, ty, rows[:nrow], cols, w, fs=2.8, rh=3.9)
    t2 = table_svg(14 + sum(w) + 8, ty, rows[nrow:], cols, w, fs=2.8, rh=3.9)[0] if nrow < len(rows) else ''
    kv = (f'<g font-family="Barlow,Arial,sans-serif"><rect x="{PW - 112}" y="{PH - 44}" width="98" height="18" fill="#fff" stroke="{INK}" stroke-width=".4"/>'
          f'<text x="{PW - 108}" y="{PH - 37}" font-size="4.2" font-weight="700">KVADRATŪRA: {fm2(g)} m²</text>'
          f'<text x="{PW - 108}" y="{PH - 31}" font-size="2.8" fill="{MUT}">bez ailām {fm2(nn)} m² · C24 45×{P.D:.0f} · {len(P.m)} detaļas</text></g>')
    warn = ''.join(f'<text x="14" y="{PH - 25 - i * 4}" font-family="Barlow,Arial" font-size="2.6" fill="#b45309">! {esc(w_)}</text>' for i, w_ in enumerate(P.warn[:5]))
    D.frame(f'{P.id}  {"ĀRSIENA" if P.kind == "arsiena" else "STARPSIENA"}', svg + t1 + t2 + kv + warn,
            f'{P.note} · garums {f0(P.L)} mm · skats no {"ārpuses" if P.kind == "arsiena" else "plāna augšas vai kreisās puses"}')


def partitions_pages(D, parts):
    for i in range(0, len(parts), 4):
        grp = parts[i:i + 4]
        body = ''
        for j, P in enumerate(grp):
            x0, y0 = 14 + (j % 2) * 198, 27 + (j // 2) * 124
            svg, s, yb = panel_svg(P, x0, y0 + 4, 112, 100)
            rows = parts_rows(P)[:24]
            t, _ = table_svg(x0 + 116, y0 + 10, rows, ('Detaļa', 'Šķērsgr.', 'Garums', 'Gab.'), (25, 15, 13, 8), fs=2.3, rh=3.2)
            g, nn = P.area()
            body += svg + t + (f'<text x="{x0}" y="{y0 + 4}" font-family="Barlow,Arial" font-size="5" font-weight="700">{P.id}</text>'
                               f'<text x="{x0 + 116}" y="{y0 + 4}" font-family="Barlow,Arial" font-size="2.8" font-weight="700">KVADRATŪRA: {fm2(g)} m²</text>'
                               f'<text x="{x0 + 116}" y="{y0 + 7.6}" font-family="Barlow,Arial" font-size="2.3" fill="{MUT}">bez ailām {fm2(nn)} m² · L {f0(P.L)} · C24 45×{P.D:.0f}</text>')
            if j % 2 == 0:
                body += f'<line x1="{x0 + 194}" y1="{y0}" x2="{x0 + 194}" y2="{y0 + 118}" stroke="#d6d8dc" stroke-width=".3"/>'
        D.frame('STARPSIENAS ' + ', '.join(P.id for P in grp), body, 'skats no plāna augšas vai kreisās puses')


def wrap(t, n):
    out, cur = [], ''
    for w in t.split():
        if len(cur) + len(w) + 1 > n:
            out.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    return out + ([cur] if cur else [])


def plan_page(D, res, m):
    W, Dd = float(m['W']), float(m['D'])
    poly = m.get('poly') or [[0, 0], [W, 0], [W, Dd], [0, Dd]]
    s = scale_for(W + 3000, Dd + 3000, 380, 235)
    k = 1 / s
    ox, oy = 20 + (380 - W * k) / 2, 30 + (235 - Dd * k) / 2
    X = lambda x: ox + x * k
    Y = lambda y: oy + y * k
    g = [f'<g font-family="Barlow,Arial,sans-serif"><polygon points="{" ".join(f"{X(p[0]):.2f},{Y(p[1]):.2f}" for p in poly)}" fill="#f7f7f5" stroke="{MUT}" stroke-width=".25" stroke-dasharray="1.2 .8"/>']
    for P in res['paneli']:
        if P.kind == 'arsiena':
            (ox_, oy_), (dx, dy) = P.o, P.dir
            nx, ny = -dy, dx
            # iekšup vērstā normāle: no fasādes uz iekšu
            cx, cy = ox_ + dx * P.L / 2, oy_ + dy * P.L / 2
            if not _inside(poly, cx + nx * 50, cy + ny * 50):
                nx, ny = -nx, -ny
            pts = [(ox_, oy_), (ox_ + dx * P.L, oy_ + dy * P.L), (ox_ + dx * P.L + nx * P.D, oy_ + dy * P.L + ny * P.D), (ox_ + nx * P.D, oy_ + ny * P.D)]
            g.append(f'<polygon points="{" ".join(f"{X(a):.2f},{Y(b):.2f}" for a, b in pts)}" fill="#e8d6ae" stroke="{INK}" stroke-width=".3"/>')
            lx, ly = cx - nx * 1500, cy - ny * 1500
            g.append(f'<circle cx="{X(lx):.2f}" cy="{Y(ly):.2f}" r="4" fill="#fff" stroke="{ACC}" stroke-width=".5"/><text x="{X(lx):.2f}" y="{Y(ly) + 1.6:.2f}" font-size="4.4" font-weight="700" text-anchor="middle" fill="{ACC}">{P.id}</text>')
            tx, ty = cx - nx * 600, cy - ny * 600
            rot = 0 if abs(dx) > .5 else -90
            g.append(f'<text transform="translate({X(tx):.2f} {Y(ty) + .9:.2f}) rotate({rot})" font-size="2.4" text-anchor="middle">{f0(P.L)}</text>')
            for o in P.opens:
                a = (ox_ + dx * o['u0'], oy_ + dy * o['u0'])
                b = (ox_ + dx * o['u1'], oy_ + dy * o['u1'])
                g.append(f'<line x1="{X(a[0]):.2f}" y1="{Y(a[1]):.2f}" x2="{X(b[0]):.2f}" y2="{Y(b[1]):.2f}" stroke="{ACC}" stroke-width="1.2"/>')
        else:
            hz, c, lo, hi = P.axis
            if hz:
                r = (X(lo), Y(c - P.D / 2), (hi - lo) * k, P.D * k)
            else:
                r = (X(c - P.D / 2), Y(lo), P.D * k, (hi - lo) * k)
            g.append(f'<rect x="{r[0]:.2f}" y="{r[1]:.2f}" width="{r[2]:.2f}" height="{r[3]:.2f}" fill="#efe2c4" stroke="{INK}" stroke-width=".25"/>')
            mx, my = r[0] + r[2] / 2, r[1] + r[3] / 2
            rt = '' if hz else f' transform="rotate(-90 {mx:.2f} {my:.2f})"'
            g.append(f'<text x="{mx:.2f}" y="{my - (1.6 if hz else -.8):.2f}" font-size="2.3" font-weight="700" text-anchor="middle" fill="{INK}"{rt}>{P.id}</text>')
    g.append(f'<text x="{PW - 14}" y="30" font-size="2.6" text-anchor="end" fill="{MUT}">M 1:{s}</text></g>')
    D.frame('KARKASA PLĀNS', ''.join(g), f'ārsienas A… (C24 45×{res["D"]:.0f}), starpsienas S1…; karkasa ārmala {res["off"]:.0f} mm no fasādes')


def _inside(P, x, y):
    c = False
    j = len(P) - 1
    for i in range(len(P)):
        a, b = P[i], P[j]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            c = not c
        j = i
    return c


def roof_page(D, res, m):
    R = res['jumts']
    allp = [p for _, pts, _ in R['planes'] for p in pts]
    x0, x1 = min(p[0] for p in allp), max(p[0] for p in allp)
    y0, y1 = min(p[1] for p in allp), max(p[1] for p in allp)
    s = scale_for(x1 - x0 + 2000, y1 - y0 + 2000, 250, 230)
    k = 1 / s
    ox, oy = 18 + (250 - (x1 - x0) * k) / 2 - x0 * k, 30 + (230 - (y1 - y0) * k) / 2 - y0 * k
    X = lambda x: ox + x * k
    Y = lambda y: oy + y * k
    g = ['<g font-family="Barlow,Arial,sans-serif">']
    poly = R['poly']
    g.append(f'<polygon points="{" ".join(f"{X(p[0]):.2f},{Y(p[1]):.2f}" for p in poly)}" fill="none" stroke="{MUT}" stroke-width=".3" stroke-dasharray="1.2 .8"/>')
    for i, (n, pts, t) in enumerate(R['planes']):
        g.append(f'<polygon points="{" ".join(f"{X(p[0]):.2f},{Y(p[1]):.2f}" for p in pts)}" fill="{["#eef2f8", "#e3eaf5", "#f4efe4", "#efe8d8"][i % 4]}" stroke="{INK}" stroke-width=".4"/>')
        cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        ar = KK._poly_area([(p[0], p[1]) for p in pts]) / math.cos(math.atan(t)) / 1e6
        g.append(f'<text x="{X(cx):.2f}" y="{Y(cy):.2f}" font-size="2.6" text-anchor="middle" font-weight="600">{esc(n)}</text>'
                 f'<text x="{X(cx):.2f}" y="{Y(cy) + 3.4:.2f}" font-size="2.4" text-anchor="middle" fill="{MUT}">{math.degrees(math.atan(t)):.1f}° · {fm2(ar)} m²</text>')
    g.append(f'<text x="{18 + 250:.2f}" y="30" font-size="2.6" text-anchor="end" fill="{MUT}">M 1:{s}</text></g>')
    rows = [(n, f'{b}×{h}', gg, c) for n, h, b, gg, c in KK.spare_list(R, res['DJ'])]
    t, ye = table_svg(282, 32, rows[:40], ('Detaļa', 'Šķērsgr.', 'Garums', 'Gab.'), (34, 16, 14, 10), fs=2.4, rh=3.3)
    tot = sum(r[2] * r[3] for r in rows) / 1000
    kv = (f'<g font-family="Barlow,Arial,sans-serif"><rect x="282" y="{PH - 52}" width="124" height="26" fill="#fff" stroke="{INK}" stroke-width=".4"/>'
          f'<text x="286" y="{PH - 44}" font-size="4.2" font-weight="700">KVADRATŪRA: {fm2(KK.roof_area(R))} m²</text>'
          f'<text x="286" y="{PH - 38}" font-size="2.8" fill="{MUT}">spāres C24 45×{res["DJ"]:.0f} c/c 600 · {len(R["spares"])} gab. · {fm2(tot)} tm</text>'
          f'<text x="286" y="{PH - 32.5}" font-size="2.8" fill="{MUT}">kore {f0(R["ridge"])} mm no ±0,000 (jumta apakša)</text></g>')
    D.frame('JUMTS', ''.join(g) + t + kv, 'jumta plaknes ar pārkari, spāru saraksts (garums pa slīpumu)')


def summary_page(D, res):
    """Kopsavilkums pa detaļu veidiem (garumi katrai detaļai ir sienu lapās)."""
    body = []
    groups = [('Ārsienas', [P for P in res['paneli'] if P.kind == 'arsiena']), ('Starpsienas', [P for P in res['paneli'] if P.kind != 'arsiena'])]
    x = 14
    for title, grp in groups:
        agg, tm = {}, {}
        for n, h, b, gg, c in KK.cutlist(grp):
            a = agg.setdefault((n, b, h), [0, 0.0])
            a[0] += c
            a[1] += gg * c / 1000
            tm[(b, h)] = tm.get((b, h), 0) + gg * c / 1000
        rows = [(n, f'{b}×{h}', v[0], round(v[1], 1)) for (n, b, h), v in sorted(agg.items())]
        body.append(f'<text x="{x}" y="34" font-family="Barlow,Arial" font-size="4" font-weight="700">{title}: {len(grp)} paneļi, {fm2(sum(P.area()[0] for P in grp))} m²</text>')
        t, ye = table_svg(x, 38, rows, ('Detaļa', 'Šķērsgr.', 'Gab.', 'tm'), (34, 17, 12, 14), fs=2.8, rh=3.9)
        r2 = [(f'C24 {b}×{h}', round(v, 1), round(v * b * h / 1e6, 3)) for (b, h), v in sorted(tm.items())]
        t2, _ = table_svg(x, ye + 6, r2, ('Kokmateriāls kopā', 'tm', 'm³'), (51, 12, 14), fs=2.8, rh=3.9)
        body.append(t + t2)
        x += 92
    R = res['jumts']
    sp = KK.spare_list(R, res['DJ'])
    rows = [(n, f'{b}×{h}', sum(c for n2, h2, b2, g2, c in sp if n2 == n), round(sum(g2 * c for n2, h2, b2, g2, c in sp if n2 == n) / 1000, 1)) for n, h, b in sorted({(n, h, b) for n, h, b, g, c in sp})]
    body.append(f'<text x="{x}" y="34" font-family="Barlow,Arial" font-size="4" font-weight="700">Jumts: {fm2(KK.roof_area(R))} m²</text>')
    t3, ye = table_svg(x, 38, rows, ('Detaļa', 'Šķērsgr.', 'Gab.', 'tm'), (34, 17, 12, 14), fs=2.8, rh=3.9)
    stm = sum(r[3] for r in rows)
    t4, _ = table_svg(x, ye + 6, [(f'C24 45×{res["DJ"]:.0f}', round(stm, 1), round(stm * 45 * res['DJ'] / 1e6, 3))], ('Kokmateriāls kopā', 'tm', 'm³'), (51, 12, 14), fs=2.8, rh=3.9)
    body.append(t3 + t4)
    x += 92
    lines = []
    for p in res['piezimes']:
        lines += ['• ' + q if i == 0 else '  ' + q for i, q in enumerate(wrap(p, 62))] + ['']
    body.append(f'<text x="{x}" y="34" font-family="Barlow,Arial" font-size="4" font-weight="700">Pieņēmumi</text>'
                + ''.join(f'<text x="{x}" y="{41 + i * 3.6:.1f}" font-family="Barlow,Arial" font-size="2.5" fill="{MUT}" xml:space="preserve">{esc(q)}</text>' for i, q in enumerate(lines)))
    D.frame('DETAĻU KOPSAVILKUMS', ''.join(body), 'pa detaļu veidiem; katras detaļas garumi un skaits ir sienu un jumta lapās')


def skice_page(D, mp, m):
    lv = os.path.join(os.path.dirname(os.path.abspath(mp)), 'rasejumi', f"{m['id']}_LV.html")
    if not os.path.exists(lv):
        import build_model
        build_model.build(mp, ['LV'])
    src = open(lv, encoding='utf-8').read()
    land = ((m.get('projekts') or {}).get('kompozicija') or {}).get('orient') == 'l'
    w, h = (420, 297) if land else (297, 420)
    sc = min(PW / w, PH / h)
    D.raw(f'<div class="sk"><iframe title="Skice" style="width:{w}mm;height:{h}mm;transform:scale({sc:.4f});transform-origin:0 0;margin-left:{(PW - w * sc) / 2:.1f}mm" '
          f'srcdoc="{html.escape(src, quote=True)}"></iframe></div>')


def build(mp, out=None):
    m = json.load(open(mp, encoding='utf-8'))
    res = KK.generate(m)
    D = Doc(m)
    skice_page(D, mp, m)
    plan_page(D, res, m)
    for P in res['paneli']:
        if P.kind == 'arsiena':
            wall_page(D, P)
    partitions_pages(D, [P for P in res['paneli'] if P.kind != 'arsiena'])
    roof_page(D, res, m)
    summary_page(D, res)
    TM.pages(D, m, res)
    n = len(D.pages)
    css = ('<style>@page{size:420mm 297mm;margin:0}html,body{margin:0;background:#d9dbdf}body{font-family:Barlow,Arial,sans-serif}'
           '.pg{width:420mm;height:297mm;background:#fff;margin:8mm auto;box-shadow:0 1px 6px rgba(0,0,0,.2);overflow:hidden;position:relative;page-break-after:always;break-after:page}'
           '.pg>svg{width:420mm;height:297mm;display:block}.sk{width:420mm;height:297mm;overflow:hidden}.sk iframe{border:0;display:block}'
           '@media print{html,body{background:none}.pg{margin:0;box-shadow:none}}</style>')
    doc = (f'<!doctype html><html lang="lv"><head><meta charset="utf-8"><title>{esc(D.model)} ražošana</title>{css}</head><body>'
           + ''.join(p.replace('@@N@@', str(n)) for p in D.pages) + '</body></html>')
    out = out or os.path.join(os.path.dirname(os.path.abspath(mp)), 'rasejumi', f"{m['id']}_razosana.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(doc)
    return out, n


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('lietošana: python karkass_lapas.py <model.json> [izvades.html]')
        sys.exit(2)
    o, n = build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(f'{o}  ({n} lapas)')
