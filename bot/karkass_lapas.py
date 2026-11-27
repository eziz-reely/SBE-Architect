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
FONT = 'Barlow,Arial,sans-serif'
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
        lg = (ar.get('tb') or {}).get('logo') or ''
        pl = pr.get('logo') or ''
        self.logo = lg if str(lg).startswith('data:') else (pl if str(pl).startswith('data:') else '')   # uzņēmuma logo (AR rakstlaukumā vai savs skicē)
        self.pages = []

    def frame(self, title, body, sub=''):
        n = len(self.pages) + 1
        tb = (f'<g font-family="Barlow,Arial,sans-serif">'
              f'<rect x="8" y="8" width="{PW - 16}" height="{PH - 16}" fill="none" stroke="{INK}" stroke-width=".5"/>'
              f'<text x="13" y="17" font-size="6" font-weight="700" fill="{INK}">{esc(title)}</text>'
              f'<text x="13" y="22.5" font-size="3.2" fill="{MUT}">{esc(sub)}</text>'
              f'<rect x="8" y="{PH - 20}" width="{PW - 16}" height="12" fill="#f4f5f7" stroke="{INK}" stroke-width=".4"/>'
              + ''.join(f'<text x="{x}" y="{PH - 15.6}" font-size="2.4" fill="{MUT}">{k}</text><text x="{x}" y="{PH - 10.4}" font-size="4" font-weight="600" fill="{INK}">{esc(v)}</text>'
                        for x, k, v in ((46 if self.logo else 13, 'MODEĻA NOSAUKUMS', f'{self.model}  ·  {self.mid}'), (150, 'KLIENTA VĀRDS', self.client or '—'), (265, 'DATUMS', self.date)))
              + (f'<image x="10" y="{PH - 19}" width="32" height="10" href="{self.logo}" preserveAspectRatio="xMinYMid meet"/><line x1="43.5" y1="{PH - 20}" x2="43.5" y2="{PH - 8}" stroke="{INK}" stroke-width=".3"/>' if self.logo else '')
              + f'<line x1="{PW - 40}" y1="{PH - 20}" x2="{PW - 40}" y2="{PH - 8}" stroke="{INK}" stroke-width=".4"/>'
              f'<text x="{PW - 36}" y="{PH - 15.6}" font-size="2.4" fill="{MUT}">LAPA</text><text x="{PW - 36}" y="{PH - 10.4}" font-size="4.4" font-weight="700" fill="{ACC}">{n}/@@N@@</text></g>')
        self.pages.append(f'<section class="pg"><svg viewBox="0 0 {PW} {PH}" xmlns="http://www.w3.org/2000/svg">{tb}{body}</svg></section>')

    def raw(self, inner):
        self.pages.append(f'<section class="pg">{inner}</section>')


def table_svg(x, y, rows, cols, widths, fs=2.6, rh=3.8, head=True, hdr_right=()):
    """Tabula SVG: rows = saraksts ar šūnām; cols = virsraksti."""
    out = [f'<g font-family="{FONT}" font-size="{fs}" fill="{INK}">']
    W = sum(widths)
    yy = y
    if head:
        out.append(f'<rect x="{x}" y="{yy}" width="{W}" height="{rh + .6}" fill="#e6e7ee"/>')
        cx = x
        for j, (c, w) in enumerate(zip(cols, widths)):
            hr = j in hdr_right
            out.append(f'<text x="{cx + w - 1 if hr else cx + 1}" y="{yy + rh - .9}" font-weight="700"{" text-anchor=\"end\"" if hr else ""}>{esc(c)}</text>')
            cx += w
        yy += rh + .6
    for i, r in enumerate(rows):
        if i % 2:
            out.append(f'<rect x="{x}" y="{yy}" width="{W}" height="{rh}" fill="#f3f2f7"/>')
        cx = x
        for j, (c, w) in enumerate(zip(r, widths)):
            num = isinstance(c, (int, float)) or bool(re.fullmatch(r'-?\d{1,3}( \d{3})*([.,]\d+)?|-?\d+([.,]\d+)?', str(c)))
            tx = cx + w - 1 if num else cx + 1
            anc = ' text-anchor="end"' if num else ''
            out.append(f'<text x="{tx}" y="{yy + rh - 1}"{anc}>{esc(c)}</text>')
            cx += w
        yy += rh
    out.append(f'<line x1="{x}" y1="{yy}" x2="{x + W}" y2="{yy}" stroke="{INK}" stroke-width=".3"/></g>')
    return ''.join(out), yy


WALL_PAL = ['#feffaf', '#ffdf8c', '#feb372', '#c4daff', '#d3efc2', '#f6cfe6', '#e1d6f6', '#cdeee8']   # katrai ārsienai savs tonis plānā (Čarnikavas A, B, C, D)
WOOD, LINE_C = '#ffdf8c', '#000000'     # Čarnikavas PDF: visas līnijas melnas, kontūras 0,05 mm


def _dash(x1, y1, x2, y2, w=.15):
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{LINE_C}" stroke-width="{w}" stroke-dasharray="1.3 .8"/>'


def _tick(x, y, horiz=True):
    d = .9
    return (f'<line x1="{x - d:.2f}" y1="{y:.2f}" x2="{x + d:.2f}" y2="{y:.2f}" stroke="{LINE_C}" stroke-width=".18"/>' if not horiz else
            f'<line x1="{x:.2f}" y1="{y - d:.2f}" x2="{x:.2f}" y2="{y + d:.2f}" stroke="{LINE_C}" stroke-width=".18"/>')


def panel_svg(P, x0, y0, bw, bh, chain=True):
    """Paneļa skats no ārpuses (Čarnikavas noformējums: dzeltens koks, melnas līnijas, raustītas izmēru ķēdes).
    Mērogs tiek rēķināts tā, lai panelis ar izmēriem ietilptu lodziņā bw×bh (mm uz lapas) pēc iespējas lielāks.
    Atgriež (svg, mērogs 1:s, apakšas y)."""
    Ht = max(z for _, z in P.top)
    mt, mb, mr, ml = 10.0, (46.0 if chain else 6.0), 20.0, 4.0
    k = min((bw - mr - ml) / P.L, (bh - mt - mb) / Ht)
    s = 1 / k
    ox = x0 + ml + (bw - mr - ml - P.L * k) / 2
    oy = y0 + mt + Ht * k
    X = lambda u: ox + u * k
    Y = lambda z: oy - z * k
    fs, fc = 5.0, 3.2          # Čarnikavas PDF (A3 normēts): galvenie izmēri 4,99 mm, ķēdes koordinātes 3,17 mm
    g = [f'<g font-family="{FONT}">']
    for q in sorted(P.m, key=lambda q: 0 if q['loma'] in ('bottom_plate', 'top_plate') else 1):
        if q['nos'] == 'SLIPAIS' and not q.get('poly'):   # augšgulsnis: zīmē zemāk pa augšmalu
            continue
        if q.get('poly'):   # slīpa pārsedze (frontona slīpais logs)
            g.append(f'<polygon points="{" ".join(f"{X(u):.2f},{Y(z):.2f}" for u, z in q["poly"])}" fill="{WOOD}" stroke="{LINE_C}" stroke-width=".06"/>')
            continue
        if q['nos'] == 'VERT.SLIPAIS':
            u0, u1 = q['u0'], q['u1']
            pl = KK.NT * KK.B * math.sqrt(1 + P.slope_at((u0 + u1) / 2) ** 2)
            pp = [(u0, q['z0']), (u1, q['z0']), (u1, P.top_at(u1) - pl), (u0, P.top_at(u0) - pl)]
            g.append(f'<polygon points="{" ".join(f"{X(u):.2f},{Y(z):.2f}" for u, z in pp)}" fill="{WOOD}" stroke="{LINE_C}" stroke-width=".06"/>')
            continue
        g.append(f'<rect x="{X(q["u0"]):.2f}" y="{Y(q["z1"]):.2f}" width="{max((q["u1"] - q["u0"]) * k, .15):.2f}" height="{max((q["z1"] - q["z0"]) * k, .15):.2f}" fill="{WOOD}" stroke="{LINE_C}" stroke-width=".06"/>')
    for (u0, z0), (u1, z1) in zip(P.top, P.top[1:]):
        if abs(z1 - z0) > 1:
            kk = math.sqrt(1 + ((z1 - z0) / (u1 - u0)) ** 2)
            pp = [(u0, z0), (u1, z1), (u1, z1 - KK.NT * KK.B * kk), (u0, z0 - KK.NT * KK.B * kk)]
            g.append(f'<polygon points="{" ".join(f"{X(u):.2f},{Y(z):.2f}" for u, z in pp)}" fill="{WOOD}" stroke="{LINE_C}" stroke-width=".06"/>')
    # ailu izmēri iekšā ailā: platums pie apakšas, augstums rotēts, parapets
    for o in P.opens:
        w_, h_ = o['u1'] - o['u0'], o['head'] - o['sill']
        yb = Y(o['sill']) - 1.4
        g.append(_dash(X(o['u0']), yb, X(o['u1']), yb) + _tick(X(o['u0']), yb) + _tick(X(o['u1']), yb))
        g.append(f'<text x="{(X(o["u0"]) + X(o["u1"])) / 2:.2f}" y="{yb - 1:.2f}" font-size="{fs}" text-anchor="middle">{f0(w_)}</text>')
        xv = X(o['u1']) - 1.6
        g.append(_dash(xv, Y(o['sill']), xv, Y(o['head'])) + _tick(xv, Y(o['sill']), False) + _tick(xv, Y(o['head']), False))
        wh_, sp_ = o.get('wh'), o.get('sp') or 0
        if o['sill'] <= 0 and wh_ and sp_ and wh_ > sp_:   # logs līdz grīdai: fasādes augstums (piem. 2100) = logs + palodzes profils
            lab = f'{f0(wh_ - sp_)}+{f0(sp_)}'
        else:
            lab, sp_ = (f0(wh_) if wh_ else f0(h_)), 0
        g.append(f'<text transform="translate({xv - 1:.2f} {(Y(o["sill"]) + Y(o["head"])) / 2:.2f}) rotate(-90)" font-size="{fs}" text-anchor="middle">{lab}</text>')
        if wh_ and sp_:
            g.append(f'<text transform="translate({xv - fs * 1.35:.2f} {(Y(o["sill"]) + Y(o["head"])) / 2:.2f}) rotate(-90)" font-size="{fs * .8:.2f}" text-anchor="middle" fill="{MUT}">pārsedze no {f0(o["head"])}</text>')
        if o['sill'] > 0:
            xs = X(o['u0']) + 1.6
            g.append(_dash(xs, Y(0), xs, Y(o['sill'])) + _tick(xs, Y(0), False) + _tick(xs, Y(o['sill']), False))
            g.append(f'<text transform="translate({xs - 1:.2f} {(Y(0) + Y(o["sill"])) / 2:.2f}) rotate(-90)" font-size="{fs}" text-anchor="middle">{f0(o["sill"])}</text>')
    # tīrās atstarpes starp blakus statņiem (ārpus ailām) pie apakšgulšņa
    zg = Y(KK.NB * KK.B + 110)
    vs = sorted((q['u0'], q['u1']) for q in P.m if q['nos'].startswith('VERT') and q['z0'] <= KK.NB * KK.B + 1 and q['z1'] > 1400)
    for (p0, p1), (q0, q1) in zip(vs, vs[1:]):
        gp = q0 - p1
        gf = min(fs, max(fc, gp * k / 2.4))      # tīrās atstarpes teksts līdz 5 mm (Čarnikavā 4,99), mazākam laukumam mazāks
        if gp < 100 or gp * k < fc * 2.4 or any(o['u0'] - KK.B < (p1 + q0) / 2 < o['u1'] + KK.B for o in P.opens):
            continue
        g.append(_dash(X(p1), zg, X(q0), zg) + _tick(X(p1), zg) + _tick(X(q0), zg))
        g.append(f'<text x="{(X(p1) + X(q0)) / 2:.2f}" y="{zg - 1:.2f}" font-size="{gf:.2f}" text-anchor="middle">{f0(gp)}</text>')
    # kopgarums augšā
    yt = Y(Ht) - 4.5
    g.append(_dash(X(0), yt, X(P.L), yt) + _tick(X(0), yt) + _tick(X(P.L), yt))
    g.append(f'<text x="{(X(0) + X(P.L)) / 2:.2f}" y="{yt - 1:.2f}" font-size="{fs}" text-anchor="middle">{f0(P.L)}</text>')
    # augstumi labajā pusē (raustīti paplašinājumi)
    hs = sorted({round(P.top[0][1]), round(Ht), round(P.top[-1][1])})
    for i, h in enumerate(hs):
        xx = X(P.L) + 5 + i * 7
        g.append(_dash(X(P.L) + 1, Y(h), xx + 1.2, Y(h)) + _dash(xx, Y(0), xx, Y(h)) + _tick(xx, Y(0), False) + _tick(xx, Y(h), False))
        g.append(f'<text transform="translate({xx + 3.4:.2f} {(Y(0) + Y(h)) / 2:.2f}) rotate(-90)" font-size="{fs}" text-anchor="middle">{h}</text>')
    if chain:
        us = sorted({round(q['u0']) for q in P.m if q['nos'].startswith('VERT') and q['z0'] <= KK.NB * KK.B + 1 and q['z1'] > 1400 and q['u0'] > 1})   # statņu pozīcijas no 0 punkta (kā Čarnikavā)
        yb = Y(0) + 10
        g.append(_dash(X(0), yb, X(P.L), yb))
        lastx = -1e9
        for u in us:
            g.append(_dash(X(u), Y(0), X(u), yb + 1) + _tick(X(u), yb))
            if X(u) - lastx >= fc * 1.15:      # koordināta rakstīta rotēti pie atzīmes; blīvos mezglos izlaiž
                g.append(f'<text transform="translate({X(u):.2f} {yb + 1.8:.2f}) rotate(90)" font-size="{fc}" dominant-baseline="central">{u}</text>')   # teksts centrēts uz atzīmes līnijas
                lastx = X(u)
        # ailu posmu ķēde: sienas posmi un ailas pa vidu, teksts posma vidū
        ya = yb + 14
        oc = sorted({0, round(P.L)} | {round(o['u0']) for o in P.opens} | {round(o['u1']) for o in P.opens})
        g.append(_dash(X(0), ya, X(P.L), ya))
        for u in oc:
            g.append(_dash(X(u), yb, X(u), ya + 1) + _tick(X(u), ya))
        for u0_, u1_ in zip(oc, oc[1:]):
            xm = X((u0_ + u1_) / 2)
            if (u1_ - u0_) * k >= fs * 3.4:
                g.append(f'<text x="{xm:.2f}" y="{ya - 0.9:.2f}" font-size="{fs}" text-anchor="middle">{u1_ - u0_}</text>')
            elif (u1_ - u0_) * k >= fc * 1.0:
                g.append(f'<text transform="translate({xm:.2f} {ya + 1.8:.2f}) rotate(90)" font-size="{fc}" dominant-baseline="central">{u1_ - u0_}</text>')
        yb2 = ya + 10
        g.append(_dash(X(0), yb2, X(P.L), yb2) + _tick(X(0), yb2) + _tick(X(P.L), yb2) + _dash(X(P.L), Y(0), X(P.L), yb2 + 1))
        g.append(f'<text x="{(X(0) + X(P.L)) / 2:.2f}" y="{yb2 + 3.6:.2f}" font-size="{fs}" text-anchor="middle">{f0(P.L)}</text>')
        bottom = yb2 + 5
    else:
        bottom = Y(0) + 2
    g.append(f'<text x="{x0 + bw:.2f}" y="{y0 + 3:.2f}" font-size="2.4" text-anchor="end" fill="{MUT}">M ≈ 1:{round(s)}</text></g>')
    return ''.join(g), s, bottom


def parts_rows(P):
    return [(n, f'{b}×{h}', g, c) for n, h, b, g, c in KK.cutlist([P])]


# detaļu saraksts pa grupām: loma -> (grupa, nosaukums latviski); komponents = SketchUp definīcijas nosaukums (kā karkass_skp.py)
ROLE_LV = {'bottom_plate': (0, 'Apakšgulsnis'), 'top_plate': (0, 'Augšgulsnis'),
           'stud': (1, 'Statnis'), 'junction': (1, 'Mezgla statnis'), 'junction_rot': (1, 'Pagriezts statnis'), 'ridge': (1, 'Kores mezgls'),
           'king': (2, 'Ailas malas statnis'), 'jack': (2, 'Pārsedzes balsts'), 'cripple': (2, 'Īsstatnis'), 'header': (2, 'Pārsedze'),
           'opening_plate': (2, 'Ailas augšgulsnis'), 'sill': (2, 'Palodzes gulsnis'), 'nogging': (3, 'Šķērsis')}
GROUP_LV = ['GULŠŅI', 'STATŅI', 'AIĻU DETAĻAS', 'ŠĶĒRSIS']


def parts_groups(P):
    """[('H', virsraksts, gab, tm) | ('R', poz, nosaukums, komponents, šķērsgr., garums, gab)] pa grupām, garākās vispirms."""
    agg = {}
    for q in P.m:
        gi, lv = ROLE_LV.get(q['loma'], (3, q['loma']))
        if q['nos'] in ('SLIPAIS', 'VERT.SLIPAIS'):
            lv += ', slīps'
        k = (gi, lv, {'PĀRSEDZE': 'HOR.STATNIS'}.get(q['nos'], q['nos']), f"{int(round(q['b']))}×{int(round(q['h']))}", int(round(q['garums'])))
        agg[k] = agg.get(k, 0) + 1
    out, poz = [], 0
    for gi in sorted({k[0] for k in agg}):
        ks = sorted((k for k in agg if k[0] == gi), key=lambda k: (k[1], -k[4]))
        out.append(('H', GROUP_LV[gi], sum(agg[k] for k in ks), sum(agg[k] * k[4] for k in ks) / 1000))
        for k in ks:
            poz += 1
            out.append(('R', poz, k[1], k[2], k[3], k[4], agg[k]))
    return out


def gtable_svg(x, y, items, compact=False, fs=2.6, rh=3.7):
    """Grupēts detaļu saraksts: grupas virsraksts ar kopsummu (gab., tm), rindās poz., nosaukums, komponents, šķērsgr., garums, gab."""
    cols = ('Detaļa', 'Šķērsgr.', 'Garums', 'Gab.') if compact else ('Poz.', 'Detaļa', 'Komponents', 'Šķērsgr.', 'Garums', 'Gab.')
    widths = (27, 12, 12, 8) if compact else (7, 31, 21, 13, 13, 9)
    W = sum(widths)
    o = [f'<g font-family="{FONT}" font-size="{fs}" fill="{INK}">', f'<rect x="{x}" y="{y}" width="{W}" height="{rh + .6}" fill="#e6e7ee"/>']
    cx = x
    for j, (c, w) in enumerate(zip(cols, widths)):
        r_ = j >= len(cols) - 2 or (not compact and j == 0)
        o.append(f'<text x="{cx + w - 1 if r_ else cx + 1}" y="{y + rh - .9}" font-weight="700"{" text-anchor=\"end\"" if r_ else ""}>{esc(c)}</text>')
        cx += w
    yy, alt = y + rh + .6, 0
    for it in items:
        if it[0] == 'H':
            yy += .8
            o.append(f'<text x="{x + 1}" y="{yy + rh - 1}" font-weight="700" font-size="{fs * .92:.2f}" fill="{ACC}">{esc(it[1])}</text>'
                     f'<text x="{x + W - 1}" y="{yy + rh - 1}" text-anchor="end" font-size="{fs * .88:.2f}" fill="{MUT}">{it[2]} gab. · {fm2(it[3])} tm</text>'
                     f'<line x1="{x}" y1="{yy + rh}" x2="{x + W}" y2="{yy + rh}" stroke="{ACC}" stroke-width=".25"/>')
            yy += rh
            alt = 0
            continue
        _, poz, lv, nos, sec, L, c = it
        if alt % 2:
            o.append(f'<rect x="{x}" y="{yy}" width="{W}" height="{rh}" fill="#f3f2f7"/>')
        alt += 1
        cells = (lv, sec, L, c) if compact else (poz, lv, nos, sec, L, c)
        cx = x
        for j, (v, w) in enumerate(zip(cells, widths)):
            r_ = isinstance(v, int)
            fill = f' fill="{MUT}"' if (not compact and j == 2) else ''
            o.append(f'<text x="{cx + w - 1 if r_ else cx + 1}" y="{yy + rh - 1}"{" text-anchor=\"end\"" if r_ else ""}{fill}>{esc(v)}</text>')
            cx += w
        yy += rh
    o.append(f'<line x1="{x}" y1="{yy}" x2="{x + W}" y2="{yy}" stroke="{INK}" stroke-width=".3"/></g>')
    return ''.join(o), yy, W


def split_groups(items, n):
    """Sadala sarakstu n kolonnās pēc rindu skaita; grupai, kas pārtrūkst, nākamajā kolonnā virsraksts '(turp.)'."""
    per = math.ceil(len(items) / n)
    cols, cur, head = [], [], None
    for it in items:
        if it[0] == 'H':
            head = it
        if len(cur) >= per and len(cols) < n - 1 and it[0] == 'R':
            cols.append(cur)
            cur = [('H', head[1] + ' (turp.)', head[2], head[3])]
        elif len(cur) >= per and len(cols) < n - 1 and it[0] == 'H':
            cols.append(cur)
            cur = []
        cur.append(it)
    cols.append(cur)
    return cols


def wall_page(D, P):
    g, nn = P.area()
    items = parts_groups(P)
    # izkārtojums: izmēģina sarakstu labajā pusē (1 kolonna) un apakšā (2 vai 3 kolonnas); ņem to, kurā rasējums ir lielākais (mazākais 1:s),
    # tad sarakstu palielina (vienmērīgi mērogo), lai tas aizpilda visu atlikušo vietu
    TW, TOP, BOT, RH0, KMAX = 95.0, 34.0, PH - 28, 3.3, 1.6
    TW0 = gtable_svg(0, 0, [], rh=RH0)[2]                        # tabulas platums pie mēroga 1
    h0 = lambda it_: gtable_svg(0, 0, it_, fs=RH0 * .7, rh=RH0)[1]   # tabulas augstums pie mēroga 1
    nw = min(len(P.warn), 5)
    best = None
    for lay in ('right', 3, 2):
        if lay == 'right':
            cand = panel_svg(P, 14, 26, PW - 17 - TW - 14 - 10, BOT - 26 - 8 - 4 * nw)
            cols = [items]
        else:
            cols = split_groups(items, lay)
            th = max(h0(c) for c in cols) + 12
            cand = panel_svg(P, 14, 26, PW - 28, BOT - th - 26 - 14 - 4 * nw)
        if best is None or cand[1] < best[0] - 1e-6:
            best = (cand[1], cand, cols, lay)
    _, (svg, s, yb), cols, lay = best
    if os.environ.get('SBE_LAY_DBG'):
        print(P.id, lay, round(s, 1))
    hd = f'{len(P.m)} detaļas · C24 45×{P.D:.0f}'
    dy_ = 0.0
    if lay == 'right':
        # rasējums aizņem tikai vajadzīgo platumu; saraksts aizpilda pārējo (augstumā līdz kvadratūrai)
        Wd = P.L / s + 24.0
        aw = PW - 17 - min(14 + Wd + 10, PW - 17 - TW)
        kt = max(1.0, min(KMAX, aw / TW0, (BOT - TOP - 24 - 4) / h0(items)))
        TX = PW - 17 - TW0 * kt
        svg, s, yb = panel_svg(P, 14, 26, TX - 14 - 10, BOT - 26 - 8 - 4 * nw)
        tabs = [(TX, TOP)]
        bx0, by0, bx1, by1 = TX - 3, TOP - 7, PW - 14, PH - 28
        head = (f'<text x="{bx0 + 3:.2f}" y="{by0 + 4.6:.2f}" font-family="{FONT}" font-size="3.2" font-weight="700" fill="{INK}">DETAĻU SARAKSTS</text>'
                f'<text x="{bx1 - 3:.2f}" y="{by0 + 4.6:.2f}" font-family="{FONT}" font-size="2.5" text-anchor="end" fill="{MUT}">{hd}</text>')
        KW, kvy = bx1 - bx0 - 6, by1 - 21
        kv = (f'<g font-family="{FONT}"><rect x="{bx0 + 3:.2f}" y="{kvy:.2f}" width="{KW:.2f}" height="18" fill="#fff" stroke="{INK}" stroke-width=".4"/>'
              f'<text x="{bx0 + 7:.2f}" y="{kvy + 7:.2f}" font-size="4.2" font-weight="700">KVADRATŪRA: {fm2(g)} m²</text>'
              f'<text x="{bx0 + 7:.2f}" y="{kvy + 13:.2f}" font-size="2.8" fill="{MUT}">bez ailām {fm2(nn)} m² · {hd}</text></g>')
        wy = PH - 25
    else:
        # saraksts apakšā pa visu platumu; kvadratūra saraksta rāmja virsrakstā
        n = len(cols)
        gap = 5.0
        ytop = yb + 12 + 4 * nw                                   # zem rasējuma (un brīdinājumiem)
        kt = max(1.0, min(KMAX, (PW - 34 - (n - 1) * gap) / (n * TW0), (BOT - ytop - 13) / max(h0(c) for c in cols)))
        th = max(h0(c) for c in cols) * kt
        by1 = BOT
        ty = by1 - 2 - th
        by0 = ty - 12
        dy_ = max(0.0, (by0 - 4 * nw - 10 - yb) / 2)          # rasējumu centrē brīvajā vietā virs saraksta
        cw = TW0 * kt
        tabs = [(17 + i * (cw + gap), ty) for i in range(n)]
        bx0, bx1 = 14, PW - 14
        head = (f'<text x="{bx0 + 3:.2f}" y="{by0 + 7:.2f}" font-family="{FONT}" font-size="3.6" font-weight="700" fill="{INK}">DETAĻU SARAKSTS</text>'
                f'<text x="{bx0 + 46:.2f}" y="{by0 + 7:.2f}" font-family="{FONT}" font-size="2.8" fill="{MUT}">{hd}</text>'
                f'<text x="{bx1 - 3:.2f}" y="{by0 + 7.4:.2f}" font-family="{FONT}" font-size="4.6" font-weight="700" text-anchor="end" fill="{INK}">KVADRATŪRA: {fm2(g)} m²'
                f'<tspan font-size="2.8" font-weight="400" fill="{MUT}">  (bez ailām {fm2(nn)} m²)</tspan></text>'
                f'<line x1="{bx0 + 3:.2f}" y1="{by0 + 10:.2f}" x2="{bx1 - 3:.2f}" y2="{by0 + 10:.2f}" stroke="{INK}" stroke-width=".25"/>')
        kv = ''
        wy = by0 - 3 - 4 * (nw - 1) if nw else PH - 25
    tb = ''.join(f'<g transform="translate({x_:.2f} {y_:.2f}) scale({kt:.4f})">{gtable_svg(0, 0, c, fs=RH0 * .7, rh=RH0)[0]}</g>'
                 for (x_, y_), c in zip(tabs, cols))
    frame = f'<rect x="{bx0:.2f}" y="{by0:.2f}" width="{bx1 - bx0:.2f}" height="{by1 - by0:.2f}" fill="none" stroke="{INK}" stroke-width=".35" rx=".8"/>'
    body = f'<g transform="translate(0 {dy_:.2f})">{svg}</g>{frame}{head}{tb}{kv}'
    warn = ''.join(f'<text x="14" y="{wy + i * 4 if lay != "right" else wy - i * 4}" font-family="Barlow,Arial" font-size="2.6" fill="#b45309">! {esc(w_)}</text>' for i, w_ in enumerate(P.warn[:5]))
    D.frame(f'{P.id}  {"ĀRSIENA" if P.kind == "arsiena" else "STARPSIENA"}', body + warn,
            f'{P.note} · garums {f0(P.L)} mm · skats no {"ārpuses" if P.kind == "arsiena" else "plāna augšas vai kreisās puses"}')


def partitions_pages(D, parts):
    for i in range(0, len(parts), 4):
        grp = parts[i:i + 4]
        body = ''
        for j, P in enumerate(grp):
            x0, y0 = 14 + (j % 2) * 198, 27 + (j // 2) * 124
            svg, s, yb = panel_svg(P, x0, y0 + 4, 112, 100)
            t, _, _ = gtable_svg(x0 + 116, y0 + 10, parts_groups(P)[:30], compact=True, fs=2.2, rh=3.05)
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
    s = math.ceil(max((W + 6400) / 390, (Dd + 6400) / 172) / 5) * 5
    k = 1 / s
    ox, oy = 15 + (390 - W * k) / 2, 28 + (172 - Dd * k) / 2
    X = lambda x: ox + x * k
    Y = lambda y: oy + y * k
    g = [f'<g font-family="Barlow,Arial,sans-serif"><polygon points="{" ".join(f"{X(p[0]):.2f},{Y(p[1]):.2f}" for p in poly)}" fill="none" stroke="none"/>']
    BOX = []       # visu sienu ierobežojošie taisnstūri (mm), lai starpsienu izmēru ķēdes neuzkristu uz citām sienām
    for P in res['paneli']:
        if P.kind == 'arsiena':
            (bx0, by0), (bx1, by1) = P.o, P.dir
            ex_ = [bx0, bx0 + bx1 * P.L]
            ey_ = [by0, by0 + by1 * P.L]
            BOX.append((min(ex_) - P.D, min(ey_) - P.D, max(ex_) + P.D, max(ey_) + P.D) if abs(bx1) > .5 else (min(ex_) - P.D, min(ey_), max(ex_) + P.D, max(ey_)))
        else:
            hz_, c_, lo_, hi_ = P.axis
            BOX.append((lo_, c_ - P.D / 2, hi_, c_ + P.D / 2) if hz_ else (c_ - P.D / 2, lo_, c_ + P.D / 2, hi_))
    LET = []       # ārsienu burtu vietas (lapas mm)
    TXT = []       # jau novietotie izmēru teksti (lapas mm), lai nepārklājas

    def _free(px, py, me):
        return not any(b[0] - 40 <= px <= b[2] + 40 and b[1] - 40 <= py <= b[3] + 40 for b in BOX if b is not me) and _inside(poly, px, py)

    for P in res['paneli']:
        if P.kind == 'arsiena':
            (ox_, oy_), (dx, dy) = P.o, P.dir
            nx, ny = -dy, dx
            cx, cy = ox_ + dx * P.L / 2, oy_ + dy * P.L / 2
            if not _inside(poly, cx + nx * 100, cy + ny * 100):
                nx, ny = -nx, -ny
            ex_, ey_ = -nx, -ny            # uz āru
            pts = [(ox_, oy_), (ox_ + dx * P.L, oy_ + dy * P.L), (ox_ + dx * P.L + nx * P.D, oy_ + dy * P.L + ny * P.D), (ox_ + nx * P.D, oy_ + ny * P.D)]
            wc_ = WALL_PAL[sorted(q.id for q in res['paneli'] if q.kind == 'arsiena').index(P.id) % len(WALL_PAL)]
            g.append(f'<polygon points="{" ".join(f"{X(a_):.2f},{Y(b_):.2f}" for a_, b_ in pts)}" fill="{wc_}" stroke="{LINE_C}" stroke-width=".06"/>')
            for q in P.m:      # statņu šķērsgriezumi (griezums 1,3 m augstumā): pelēki, kā Čarnikavas plānā
                if q['nos'].startswith('VERT') and q['loma'] != 'cripple' and q['z0'] <= 1300 <= q['z1']:
                    o0, o1 = (P.D - q['b'], P.D) if q['loma'] == 'junction_rot' else (0.0, P.D)
                    c4 = [(ox_ + dx * q['u0'] + nx * o0, oy_ + dy * q['u0'] + ny * o0), (ox_ + dx * q['u1'] + nx * o0, oy_ + dy * q['u1'] + ny * o0),
                          (ox_ + dx * q['u1'] + nx * o1, oy_ + dy * q['u1'] + ny * o1), (ox_ + dx * q['u0'] + nx * o1, oy_ + dy * q['u0'] + ny * o1)]
                    g.append(f'<polygon points="{" ".join(f"{X(a_):.2f},{Y(b_):.2f}" for a_, b_ in c4)}" fill="#d6d6d6" stroke="{LINE_C}" stroke-width=".06"/>')
            for o in P.opens:      # ailas: logi gaiši zilā, durvis baltas
                q = [(ox_ + dx * o['u0'], oy_ + dy * o['u0']), (ox_ + dx * o['u1'], oy_ + dy * o['u1'])]
                q += [(q[1][0] + nx * P.D, q[1][1] + ny * P.D), (q[0][0] + nx * P.D, q[0][1] + ny * P.D)]
                g.append(f'<polygon points="{" ".join(f"{X(a_):.2f},{Y(b_):.2f}" for a_, b_ in q)}" fill="#ffffff" stroke="{LINE_C}" stroke-width=".06"/>')
                if o['tips'] != 'durvis':      # logs: stikla līnija ailas vidū (durvis paliek tukšas)
                    m0_, m1_ = ((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2), ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2)
                    g.append(f'<line x1="{X(m0_[0]):.2f}" y1="{Y(m0_[1]):.2f}" x2="{X(m1_[0]):.2f}" y2="{Y(m1_[1]):.2f}" stroke="{LINE_C}" stroke-width=".12"/>')
            vert = abs(dy) > .5
            pt = lambda u, off: (ox_ + dx * u + ex_ * off, oy_ + dy * u + ey_ * off)
            cuts = sorted({0.0, float(P.L)} | {float(o['u0']) for o in P.opens} | {float(o['u1']) for o in P.opens})
            d1, d2 = 450, 950
            for dd, cl in ((d1, cuts), (d2, [0.0, float(P.L)])):
                if dd == d2 and len(cuts) <= 2:
                    continue
                a_, b_ = pt(cl[0], dd), pt(cl[-1], dd)
                g.append(f'<line x1="{X(a_[0]):.2f}" y1="{Y(a_[1]):.2f}" x2="{X(b_[0]):.2f}" y2="{Y(b_[1]):.2f}" stroke="{LINE_C}" stroke-width=".15" stroke-dasharray="1.3 .8"/>')
                for u in cl:
                    e0, e1 = pt(u, 60), pt(u, dd + 80)
                    g.append(f'<line x1="{X(e0[0]):.2f}" y1="{Y(e0[1]):.2f}" x2="{X(e1[0]):.2f}" y2="{Y(e1[1]):.2f}" stroke="{LINE_C}" stroke-width=".15" stroke-dasharray="1.3 .8"/>')
                    tk = pt(u, dd)
                    g.append(f'<line x1="{X(tk[0]) - .9:.2f}" y1="{Y(tk[1]) - .9:.2f}" x2="{X(tk[0]) + .9:.2f}" y2="{Y(tk[1]) + .9:.2f}" stroke="{LINE_C}" stroke-width=".25"/>')
                for u0_, u1_ in zip(cl, cl[1:]):
                    if (u1_ - u0_) * k < 11:
                        continue
                    m_ = pt((u0_ + u1_) / 2, dd + 170)
                    rot = f' transform="rotate(-90 {X(m_[0]):.2f} {Y(m_[1]):.2f})"' if vert else ''
                    g.append(f'<text x="{X(m_[0]):.2f}" y="{Y(m_[1]):.2f}"{rot} font-size="4.99" text-anchor="middle" dominant-baseline="central" fill="{INK}">{f0(u1_ - u0_)}</text>')
            u_l = P.L / 2 if P.L < 5000 else min(P.L * .12, 1100) + 450
            for _try in range(4):          # burti nedrīkst pārklāties
                lx, ly = pt(u_l, 2250)
                if all(math.hypot(X(lx) - a_, Y(ly) - b_) > 14 for a_, b_ in LET):
                    break
                u_l += P.L * .22
            LET.append((X(lx), Y(ly)))      # burts pie sienas kreisā gala (skatoties no ārpuses), aiz izmēru ķēdēm, kā Čarnikavā
            g.append(f'<text x="{X(lx):.2f}" y="{Y(ly):.2f}" font-size="12" font-weight="700" text-anchor="middle" dominant-baseline="central" fill="{wc_}" stroke="{LINE_C}" stroke-width=".35" paint-order="stroke">{P.id}</text>')
        else:
            hz, c, lo, hi = P.axis
            if hz:
                r = (X(lo), Y(c - P.D / 2), (hi - lo) * k, P.D * k)
            else:
                r = (X(c - P.D / 2), Y(lo), P.D * k, (hi - lo) * k)
            g.append(f'<rect x="{r[0]:.2f}" y="{r[1]:.2f}" width="{r[2]:.2f}" height="{r[3]:.2f}" fill="#dea884" stroke="{LINE_C}" stroke-width=".06"/>')
            for q in P.m:
                if q['nos'].startswith('VERT') and q['loma'] != 'cripple' and q['z0'] <= 1300 <= q['z1']:
                    a0, a1 = lo + q['u0'], lo + q['u1']
                    c0_, c1_ = c - P.D / 2, c + P.D / 2           # šķērsvirziens: visa sienas dziļums; pagriezts statnis tikai 45 mm pieslēgtās sienas pusē
                    if q['loma'] == 'junction_rot' and q.get('sd'):
                        c0_, c1_ = (c1_ - q['b'], c1_) if q['sd'] > 0 else (c0_, c0_ + q['b'])
                    rr = (X(a0), Y(c0_), (a1 - a0) * k, (c1_ - c0_) * k) if hz else (X(c0_), Y(a0), (c1_ - c0_) * k, (a1 - a0) * k)
                    g.append(f'<rect x="{rr[0]:.2f}" y="{rr[1]:.2f}" width="{rr[2]:.2f}" height="{rr[3]:.2f}" fill="#d6d6d6" stroke="{LINE_C}" stroke-width=".06"/>')
            me_ = (lo, c - P.D / 2, hi, c + P.D / 2) if hz else (c - P.D / 2, lo, c + P.D / 2, hi)
            cl = sorted({0.0, float(P.L)} | {float(o['u0']) for o in P.opens} | {float(o['u1']) for o in P.opens})
            cl = [u for u in cl if 0 <= u <= P.L]
            def _tbox(u0_, u1_, side_, dd_):       # teksta aizņemtais laukums lapā (mm)
                px, py = (lo + (u0_ + u1_) / 2, c + side_ * (dd_ + 170)) if hz else (c + side_ * (dd_ + 170), lo + (u0_ + u1_) / 2)
                tw, th = len(f0(u1_ - u0_)) * 2.9 + 1.0, 5.6
                return (X(px) - (tw if hz else th) / 2, Y(py) - (th if hz else tw) / 2, X(px) + (tw if hz else th) / 2, Y(py) + (th if hz else tw) / 2)
            hit = lambda a, b: a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
            side_ = None
            for sd_ in (1, -1):           # puse, kur ķēde nekrīt uz citām sienām un tekstiem
                dd_ = P.D / 2 + 330
                segs_ = [(u0_, u1_) for u0_, u1_ in zip(cl, cl[1:]) if (u1_ - u0_) * k >= 11]
                ok_ = all(_free(*((lo + (u0_ + u1_) / 2, c + sd_ * dd_) if hz else (c + sd_ * dd_, lo + (u0_ + u1_) / 2)), me_) for u0_, u1_ in zip(cl, cl[1:]))
                ok_ = ok_ and not any(hit(_tbox(u0_, u1_, sd_, dd_), t_) for u0_, u1_ in segs_ for t_ in TXT)
                if ok_:
                    side_ = sd_
                    break
            if side_ is not None:
                TXT.extend(_tbox(u0_, u1_, side_, P.D / 2 + 330) for u0_, u1_ in zip(cl, cl[1:]) if (u1_ - u0_) * k >= 11)
            if side_ is not None and len(cl) > 1:
                dd_ = P.D / 2 + 330
                A = lambda u, off: (lo + u, c + side_ * off) if hz else (c + side_ * off, lo + u)
                a_, b_ = A(cl[0], dd_), A(cl[-1], dd_)
                g.append(_dash(X(a_[0]), Y(a_[1]), X(b_[0]), Y(b_[1]), .15))
                for u in cl:
                    e0, e1 = A(u, P.D / 2 + 60), A(u, dd_ + 80)
                    g.append(_dash(X(e0[0]), Y(e0[1]), X(e1[0]), Y(e1[1]), .15))
                    tk = A(u, dd_)
                    g.append(f'<line x1="{X(tk[0]) - .9:.2f}" y1="{Y(tk[1]) - .9:.2f}" x2="{X(tk[0]) + .9:.2f}" y2="{Y(tk[1]) + .9:.2f}" stroke="{LINE_C}" stroke-width=".25"/>')
                for u0_, u1_ in zip(cl, cl[1:]):
                    if (u1_ - u0_) * k < (11 if hz else 11):
                        continue
                    m_ = A((u0_ + u1_) / 2, dd_ + 170)
                    rot = '' if hz else f' transform="rotate(-90 {X(m_[0]):.2f} {Y(m_[1]):.2f})"'
                    g.append(f'<text x="{X(m_[0]):.2f}" y="{Y(m_[1]):.2f}"{rot} font-size="4.99" text-anchor="middle" dominant-baseline="central" fill="{INK}">{f0(u1_ - u0_)}</text>')
            # skata virziena bulta un nosaukums (kā Čarnikavā): sienu skata no tās puses, kur izmēru ķēde
            sv_ = side_ if side_ is not None else 1
            al_ = lo + min(330, P.L * .2)                 # bultas vieta gar sienu
            tip_, h_, w_ = P.D / 2 + 40, 200, 170
            def _pp(a_, o_):
                return (X(a_), Y(c + sv_ * o_)) if hz else (X(c + sv_ * o_), Y(a_))
            tri_ = [_pp(al_, tip_), _pp(al_ - w_ / 2, tip_ + h_), _pp(al_ + w_ / 2, tip_ + h_)]
            g.append(f'<polygon points="{" ".join(f"{a_:.2f},{b_:.2f}" for a_, b_ in tri_)}" fill="#dea884" stroke="{LINE_C}" stroke-width=".15"/>'
                     f'<line x1="{_pp(al_ - w_ / 2, tip_ + h_ + 40)[0]:.2f}" y1="{_pp(al_ - w_ / 2, tip_ + h_ + 40)[1]:.2f}" x2="{_pp(al_ + w_ / 2, tip_ + h_ + 40)[0]:.2f}" y2="{_pp(al_ + w_ / 2, tip_ + h_ + 40)[1]:.2f}" stroke="{LINE_C}" stroke-width=".15"/>')
            tx_, ty_ = _pp(al_ + w_ / 2 + 120, tip_ + h_ / 2)
            rt = '' if hz else f' transform="rotate(-90 {tx_:.2f} {ty_:.2f})"'
            g.append(f'<text x="{tx_:.2f}" y="{ty_:.2f}"{rt} font-size="3.2" font-weight="700" text-anchor="start" dominant-baseline="central" fill="#dea884" stroke="{LINE_C}" stroke-width=".22" paint-order="stroke">{P.id}</text>')
    g.append(f'<text x="{PW - 14}" y="30" font-size="2.6" text-anchor="end" fill="{MUT}">M 1:{s}</text></g>')
    g.append(kaste_detail(20, 205, res['D']))
    D.frame('KARKASA PLĀNS', ''.join(g), f'ārsienas A… (C24 45×{res["D"]:.0f}), starpsienas S1…; karkasa ārmala {res["off"]:.0f} mm no fasādes')


def kaste_detail(x0, y0, Dw):
    """Stūra kaste (3 detaļas) griezumā plānā, M 1:10: garās ārsienas gals pie frontona. Detaļas skrūvē kopā un piesledz frontonam."""
    k = .1
    B = KK.B
    bx, by = x0 + 70, y0 + 36                       # kastes augšējais kreisais stūris (lapas mm)
    R = lambda x, y, w, h, fill: f'<rect x="{bx + x * k:.2f}" y="{by + y * k:.2f}" width="{w * k:.2f}" height="{h * k:.2f}" fill="{fill}" stroke="{INK}" stroke-width=".25"/>'
    T = lambda x, y, s_, fs=2.6, a='start', fw=400: f'<text x="{bx + x * k:.2f}" y="{by + y * k:.2f}" font-size="{fs}" text-anchor="{a}" font-weight="{fw}" fill="{INK}">{s_}</text>'
    tot = 2 * B + Dw
    g = [f'<g font-family="{FONT}">',
         T(-600, -300, 'STŪRA KASTE (3 detaļas), GRIEZUMS PLĀNĀ  M 1:10', 3.2, fw=700),
         R(0, -150, Dw, 150, '#ffffb3'), R(-600, B, 600, Dw, '#ffb577'),            # garā ārsiena, fronts (oranžais)
         R(0, 0, Dw, B, '#d4d4d4'), R(0, B, B, Dw, '#d4d4d4'), R(0, B + Dw, Dw, B, '#d4d4d4'),   # kastes 3 detaļas
         R(B, B, Dw - B, Dw, '#ffffb3'),
         T(Dw + 60, 28, '1 – statnis 45×%d' % Dw), T(Dw + 60, B + Dw / 2 + 5, '2 – pagriezts statnis 45×%d' % Dw), T(Dw + 60, B + Dw + 28, '3 – statnis 45×%d' % Dw),
         T(-300, B + Dw / 2 + 4, 'fronts', 2.8, 'middle'), T(Dw / 2, -70, 'ārsiena', 2.8, 'middle'),
         '</g>']
    return ''.join(g)


def _inside(P, x, y):
    c = False
    j = len(P) - 1
    for i in range(len(P)):
        a, b = P[i], P[j]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            c = not c
        j = i
    return c


def _adim(p, q, off, label, fs=2.6):
    """Izmērs gar nogriezni p→q (lapas mm), nobīdīts par off uz augšu (perpendikulāri), teksts paralēli."""
    L = math.dist(p, q) or 1
    ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    nx, ny = uy, -ux
    if ny > 0:
        nx, ny = -nx, -ny
    a, b = (p[0] + nx * off, p[1] + ny * off), (q[0] + nx * off, q[1] + ny * off)
    tk = lambda c: _dash(c[0] - (ux - nx) * .9, c[1] - (uy - ny) * .9, c[0] + (ux - nx) * .9, c[1] + (uy - ny) * .9, .25)
    ang = math.degrees(math.atan2(uy, ux))
    if ang > 90 or ang < -90:
        ang += 180
    return (_dash(p[0], p[1], a[0] + nx, a[1] + ny) + _dash(q[0], q[1], b[0] + nx, b[1] + ny) + _dash(*a, *b) + tk(a) + tk(b)
            + _txt((a[0] + b[0]) / 2 + nx * 1.8, (a[1] + b[1]) / 2 + ny * 1.8, label, fs, rot=ang))


def _poly_s(pts, X, Y, fill, sw=.25, extra=''):
    return f'<polygon points="{" ".join(f"{X(a):.2f},{Y(b):.2f}" for a, b in pts)}" fill="{fill}" stroke="{LINE_C}" stroke-width="{sw}"{extra}/>'


def _txt(x, y, s_, fs=3.4, a='middle', rot=0, fill=None):
    r = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ''
    return f'<text x="{x:.2f}" y="{y:.2f}"{r} font-size="{fs}" text-anchor="{a}" dominant-baseline="central" fill="{fill or INK}">{s_}</text>'


def section_page(D, res, m):
    """Šķērsgriezums (Čarnikavas noformējums): ārsienu karkass, spāres pārī, kore, izmēri."""
    R = res['jumts']
    J = m.get('jumts') or {}
    DK, DJ, off = res['D'], res['DJ'], res['off']
    tan = R['planes'][0][2]
    span = (2 * (float(R['ridge']) - float(J.get('eave') or 2600)) / tan) if len(R['planes']) > 2 else float(m['D'])   # L jumtam: galvenā spārna plātums no kores augstuma
    th = math.atan(tan)
    eave = float(J.get('eave') or 2600)
    oN = -min(p[1] for p in R['planes'][0][1]) if R['planes'][0][1] else 0
    oS = max(p[1] for p in R['planes'][1][1]) - span if len(R['planes']) > 1 else oN
    oN, oS = max(oN, 0), max(oS, 0)
    hr = float(R['ridge']) if len(R['planes']) > 2 else eave + tan * span / 2
    xs0, xs1 = -oN, span + oS
    W_ = xs1 - xs0
    mt, mb, mr, ml = 12.0, 30.0, 30.0, 8.0
    k = min((390 - ml - mr) / W_, (PH - 26 - 26 - mt - mb) / (hr + 400))
    ox = 15 + ml + (390 - ml - mr - W_ * k) / 2 - xs0 * k
    gy = 26 + mt + (hr + 400) * k + 4        # z = 0 līnija uz lapas ... apakšā 400 mm zem grīdas
    X = lambda u: ox + u * k
    Y = lambda z: gy - (z + 400) * k
    g = [f'<g font-family="{FONT}">']
    # zeme un grīda
    g.append(f'<line x1="{X(xs0 - 600):.2f}" y1="{Y(-400):.2f}" x2="{X(xs1 + 600):.2f}" y2="{Y(-400):.2f}" stroke="{LINE_C}" stroke-width=".5"/>')
    # sienas (karkass): gulšņi 2×45, augšgulsnis 1×45, statņi; augšgulsnis ZP = spāres apakša karkasa ārmalā + iezāģis
    zp = res.get('zp') or eave + off * tan + res.get('seat', KK.SEAT)
    for x_in in (off, span - off - DK):
        g.append(_poly_s([(x_in, 0), (x_in + DK, 0), (x_in + DK, zp), (x_in, zp)], X, Y, WOOD, .3))
        for z0, z1 in ((0, 2 * KK.B), (zp - KK.NT * KK.B, zp)):
            g.append(_poly_s([(x_in, z0), (x_in + DK, z0), (x_in + DK, z1), (x_in, z1)], X, Y, WOOD, .3))
    # spāres: iezāģis 50 mm uz augšgulšņa; bez pārkares gals vertikāls karkasa ārmalā, ar pārkari spāre iet ārā; korē vertikāls zāģējums
    c = math.cos(th)
    dz = DJ / c
    sc = res.get('seat', KK.SEAT) / tan
    for side, oo in (('N', oN), ('S', oS)):
        zb = lambda x: eave + tan * x                         # spāres apakša (x no fasādes uz iekšu)
        pl = ([(-oo, zb(-oo)), (off, zb(off))] if oo > 1 else []) + [(off, zp), (off + sc, zp), (span / 2, hr), (span / 2, hr + dz), (-oo if oo > 1 else off, zb(-oo if oo > 1 else off) + dz)]
        if side == 'S':
            pl = [(span - x, z) for x, z in pl]
        g.append(_poly_s(pl, X, Y, WOOD, .3))
    # izmēri
    yb = Y(-400) + 7
    g.append(_dash(X(xs0), yb, X(xs1), yb) + _tick(X(xs0), yb) + _tick(X(xs1), yb))
    for u in (xs0, 0, span, xs1):
        g.append(_dash(X(u), Y(-400), X(u), yb + 1))
    g.append((_txt((X(xs0) + X(0)) / 2, yb + 3, f0(oN), 3.4) if oN > 1 else '') + _txt((X(0) + X(span)) / 2, yb + 3, f0(span), 3.8) + (_txt((X(span) + X(xs1)) / 2, yb + 3, f0(oS), 3.4) if oS > 1 else ''))
    yb2 = yb + 8
    g.append(_dash(X(xs0), yb2, X(xs1), yb2) + _tick(X(xs0), yb2) + _tick(X(xs1), yb2) + _dash(X(xs0), Y(-400), X(xs0), yb2 + 1) + _dash(X(xs1), Y(-400), X(xs1), yb2 + 1))
    g.append(_txt((X(xs0) + X(xs1)) / 2, yb2 + 3, f0(W_), 3.8))
    xr = X(xs1) + 8
    for i, (zz, lab) in enumerate(((eave, f0(eave)), (hr, f0(hr)))):
        xx = xr + i * 8
        g.append(_dash(X(xs1) + 1, Y(zz), xx + 1.5, Y(zz)) + _dash(xx, Y(0), xx, Y(zz)) + _tick(xx, Y(0), False) + _tick(xx, Y(zz), False))
        g.append(_txt(xx + 3.6, (Y(0) + Y(zz)) / 2, lab, 3.6, rot=-90))
    g.append(_txt(X(span / 2) + 4, Y(hr) + 12, f'{math.degrees(th):.0f}°', 3.8, 'start'))
    g.append(f'<text x="{PW - 14:.2f}" y="30" font-size="2.6" text-anchor="end" fill="{MUT}">M ≈ 1:{round(1 / k)}</text></g>')
    note = ('L formas jumtam parādīts galvenā spārna griezums (plātums no kores augstuma)' if len(R['planes']) > 2 else '')
    D.frame('ŠĶĒRSGRIEZUMS', ''.join(g), f'ārsienu karkass C24 45×{DK:.0f}, spāres C24 45×{DJ:.0f}, jumta slīpums {math.degrees(th):.0f}°' + (' · ' + note if note else ''))


def _clip_line(poly, p0, d):
    """Taisne p0 + t·d (d vienības vektors) nogriezta ar izliektu daudzstūri: (t0, t1) vai None (Cyrus-Beck)."""
    t0, t1 = -1e9, 1e9
    n = len(poly)
    sgn = 1 if sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n)) > 0 else -1
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        nx, ny = ey * sgn, -ex * sgn            # uz āru
        num = nx * (a[0] - p0[0]) + ny * (a[1] - p0[1])
        den = nx * d[0] + ny * d[1]
        if abs(den) < 1e-9:
            if num < 0:
                return None
            continue
        t = num / den
        if den > 0:
            t1 = min(t1, t)
        else:
            t0 = max(t0, t)
    return (t0, t1) if t0 < t1 else None


def roof_page(D, res, m):
    """Jumta lapa (Čarnikavas noformējums): spāru plāns ar c/c 600, viena spāre ar leņķi un garumu, saraksts, kvadratūra."""
    R = res['jumts']
    DJ = res['DJ']
    allp = [p for _, pts, _ in R['planes'] for p in pts]
    x0, x1 = min(p[0] for p in allp), max(p[0] for p in allp)
    y0, y1 = min(p[1] for p in allp), max(p[1] for p in allp)
    bw, bh = 255.0, 215.0
    s = math.ceil(max((x1 - x0 + 3200) / bw, (y1 - y0 + 2400) / bh) / 5) * 5
    k = 1 / s
    ox, oy = 16 + 22 + (bw - (x1 - x0) * k) / 2 - x0 * k, 30 + 10 + (bh - (y1 - y0) * k) / 2 - y0 * k
    X = lambda x: ox + x * k
    Y = lambda y: oy + y * k
    g = [f'<g font-family="{FONT}">']
    labs = []
    for i, (n, pts, t) in enumerate(R['planes']):
        p2 = [(p[0], p[1]) for p in pts]
        g.append(_poly_s(p2, X, Y, '#ffffff', .45))
        # krituma virziens no 3D punktiem: z(x, y) = a + gx·x + gy·y
        A = pts[0]
        gx = gy = 0.0
        for q in pts[1:]:
            for r_ in pts[1:]:
                dx1, dy1, dz1 = q[0] - A[0], q[1] - A[1], q[2] - A[2]
                dx2, dy2, dz2 = r_[0] - A[0], r_[1] - A[1], r_[2] - A[2]
                det = dx1 * dy2 - dx2 * dy1
                if abs(det) > 1e-6:
                    gx, gy = (dz1 * dy2 - dz2 * dy1) / det, (dx1 * dz2 - dx2 * dz1) / det
                    break
            else:
                continue
            break
        gl = math.hypot(gx, gy) or 1
        d = (-gx / gl, -gy / gl)                 # uz leju (pa spārēm)
        nrm = (-d[1], d[0])
        cxs = [p[0] * nrm[0] + p[1] * nrm[1] for p in p2]
        s0, s1 = min(cxs), max(cxs)
        pos = s0 + 22
        while pos < s1 and not (R.get('rafs3d') or (0, 0))[1]:   # vecais zīmējums tikai, ja nav jumta paneļu (zemāk)
            base = (nrm[0] * pos, nrm[1] * pos)
            c_ = _clip_line(p2, (base[0] - d[0] * 40000, base[1] - d[1] * 40000), d)
            if c_:
                a_ = (base[0] + d[0] * (c_[0] - 40000), base[1] + d[1] * (c_[0] - 40000))
                b_ = (base[0] + d[0] * (c_[1] - 40000), base[1] + d[1] * (c_[1] - 40000))
                g.append(f'<line x1="{X(a_[0]):.2f}" y1="{Y(a_[1]):.2f}" x2="{X(b_[0]):.2f}" y2="{Y(b_[1]):.2f}" stroke="{LINE_C}" stroke-width="{max(45 * k, .35) + .22:.2f}"/>'
                         f'<line x1="{X(a_[0]):.2f}" y1="{Y(a_[1]):.2f}" x2="{X(b_[0]):.2f}" y2="{Y(b_[1]):.2f}" stroke="{WOOD}" stroke-width="{max(45 * k, .35):.2f}"/>')
            pos += KK.SPARE_CC
        cx, cy = sum(p[0] for p in p2) / len(p2), sum(p[1] for p in p2) / len(p2)
        labs.append(_txt(X(cx), Y(cy), f'{esc(n)} · {math.degrees(math.atan(t)):.0f}°', 3.0, fill=INK))
    for r in (R.get('rafs3d') or (0, []))[1]:   # jumta paneļi: spāres un kores dēļi plānā (tie paši, kas 3D un SketchUp)
        ss = [q[0] for q in r['poly']]
        w_ = r.get('w') or KK.B
        o_, d_, n_ = r['o'], r['d'], r['n']
        P4 = [(o_[0] + d_[0] * a + n_[0] * b, o_[1] + d_[1] * a + n_[1] * b) for a, b in ((min(ss), 0), (max(ss), 0), (max(ss), w_), (min(ss), w_))]
        g.append(_poly_s(P4, X, Y, WOOD, .22))
    g.extend(labs)
    # kopējie izmēri
    yt = Y(y0) - 6
    g.append(_dash(X(x0), yt, X(x1), yt) + _tick(X(x0), yt) + _tick(X(x1), yt) + _dash(X(x0), Y(y0) - 1, X(x0), yt - 1) + _dash(X(x1), Y(y0) - 1, X(x1), yt - 1))
    g.append(_txt((X(x0) + X(x1)) / 2, yt - 2.2, f0(x1 - x0), 3.8))
    xl = X(x0) - 7
    g.append(_dash(xl, Y(y0), xl, Y(y1)) + _tick(xl, Y(y0), False) + _tick(xl, Y(y1), False) + _dash(X(x0) - 1, Y(y0), xl - 1, Y(y0)) + _dash(X(x0) - 1, Y(y1), xl - 1, Y(y1)))
    g.append(_txt(xl - 2.4, (Y(y0) + Y(y1)) / 2, f0(y1 - y0), 3.8, rot=-90))
    # viena spāre: leņķis, garums pa slīpumu
    if R['spares']:
        L0 = R['spares'][0][1]
        th = math.atan(R['planes'][0][2])
        sx, sy, sk = 292.0, 46.0, min(100 / (L0 * math.cos(th)), 40 / (L0 * math.sin(th) + 300))
        A = (sx, sy + L0 * math.sin(th) * sk)
        Bp = (sx + L0 * math.cos(th) * sk, sy)
        nn = (-math.sin(th), -math.cos(th))
        pts = [A, Bp, (Bp[0] + nn[0] * DJ * sk, Bp[1] + nn[1] * DJ * sk), (A[0] + nn[0] * DJ * sk, A[1] + nn[1] * DJ * sk)]
        rp = next((r['poly'] for r in (R.get('rafs3d') or (0, []))[1] if r.get('loma') != 'ridge_beam' and len(r['poly']) > 4), None)
        if rp:   # īstais spāres profils (tas pats, kas 3D un SketchUp): iezāģis 50 uz augšgulšņa, gali vertikāli
            sa, za = min(q[0] for q in rp), min(q[1] for q in rp)
            Lh, Hh = max(q[0] for q in rp) - sa, max(q[1] for q in rp) - za
            sk = min(96 / Lh, 44 / Hh)
            PX = lambda q: (sx + (q[0] - sa) * sk, sy + 48 - (q[1] - za) * sk)
            pts = [PX(q) for q in rp]
            A, Bp = PX((sa, za)), PX((sa + Lh, za + Hh))
            st = next(((a_, b_) for a_, b_ in zip(rp, rp[1:]) if abs(a_[1] - b_[1]) < .5 and b_[0] > a_[0]), None)   # iezāģa horizontālā daļa
            if st:   # mezgls lielākā mērogā: spāre uz augšgulšņa ar iezāģi (vertikāli 50, horizontāli kas sanāk)
                sw_, zp_ = st[0][0], st[0][1]
                hc = st[1][0] - st[0][0]
                SV = res.get('seat', KK.SEAT)
                tg = SV / (hc or 1)
                bx, by, bwd = 368.0, 112.0, 42.0
                s_lo, s_hi = sw_ - 260, sw_ + 300
                kz = bwd / (s_hi - s_lo)
                zlo, zhi = zp_ - 330, zp_ + (s_hi - sw_) * tg + DJ * math.sqrt(1 + tg * tg) + 20
                bh_ = (zhi - zlo) * kz
                MX = lambda q: (bx + (q[0] - s_lo) * kz, by + bh_ - (q[1] - zlo) * kz)
                cid = f'cl{id(rp) % 100000}'
                dd = [f'<clipPath id="{cid}"><rect x="{bx}" y="{by}" width="{bwd}" height="{bh_:.2f}"/></clipPath><g clip-path="url(#{cid})">']
                Dw = res['D']
                for z0_, z1_ in ((zp_ - KK.B, zp_), (zlo - 10, zp_ - KK.B)):   # augšgulsnis un statnis zem tā (sienas karkass no ārmalas)
                    q = [MX((sw_, z0_)), MX((sw_ + Dw, z0_)), MX((sw_ + Dw, z1_)), MX((sw_, z1_))]
                    dd.append(f'<polygon points="{" ".join(f"{a_:.2f},{b_:.2f}" for a_, b_ in q)}" fill="{WOOD if z1_ == zp_ else "#f3e2b5"}" stroke="{LINE_C}" stroke-width=".25"/>')
                dd.append(f'<polygon points="{" ".join(f"{a_:.2f},{b_:.2f}" for a_, b_ in (MX(q) for q in rp))}" fill="{WOOD}" stroke="{LINE_C}" stroke-width=".3"/>')
                a1_, a2_ = MX((sw_, zp_ - SV)), MX((sw_ + hc, zp_))
                dd.append(_dash(*MX((sw_ - 200, zp_ - SV - 200 * tg)), *a1_) + _dash(*a1_, *a2_))   # spāres apakšas līnija līdz iezāģim
                dd.append('</g>')
                p0, p1 = MX((sw_, zp_)), MX((sw_, zp_ - SV))
                dd.append(_dash(p0[0] - 3, p0[1], p0[0] - 1, p0[1]) + _dash(p0[0] - 3, p1[1], p0[0] - 1, p1[1]) + _dash(p0[0] - 2, p0[1], p0[0] - 2, p1[1]))
                dd.append(_txt(p0[0] - 4.5, (p0[1] + p1[1]) / 2, f'{SV:.0f}', 2.8, 'end'))
                h0, h1 = MX((sw_, zp_)), MX((sw_ + hc, zp_))
                dd.append(_dash(h0[0], h0[1] - 3, h1[0], h1[1] - 3) + _tick(h0[0], h0[1] - 3) + _tick(h1[0], h1[1] - 3))
                dd.append(_txt((h0[0] + h1[0]) / 2, h0[1] - 5, f'{hc:.0f}', 2.8))
                dd.append(f'<rect x="{bx}" y="{by}" width="{bwd}" height="{bh_:.2f}" fill="none" stroke="{INK}" stroke-width=".3"/>')
                dd.append(_txt(bx + bwd / 2, by + bh_ + 4, (f'iezāģis {SV:.0f} vertikāli uz augšgulšņa' if SV <= KK.SEAT + .5 else f'bez pārkares: guļ uz {hc:.0f}') + f' · M 1:{round(1 / kz)}', 2.4))
                dd.append(_txt(bx + bwd / 2, by - 3, 'MEZGLS: SPĀRE UZ SIENAS', 2.8))
                g.append(''.join(dd))
            g.append(f'<polygon points="{" ".join(f"{a_:.2f},{b_:.2f}" for a_, b_ in pts)}" fill="{WOOD}" stroke="{LINE_C}" stroke-width=".3"/>')
            if st:   # mēri kā lietotāja paraugā: gar spāri (pārkare, līdz korei, kopā), horizontālās projekcijas, iezāģis 50 / horizontālā daļa
                sm = max(q[0] for q in rp)
                t0 = max((q for q in rp if abs(q[0] - sa) < .5), key=lambda q: q[1])
                t1 = max((q for q in rp if abs(q[0] - sm) < .5), key=lambda q: q[1])
                tz = lambda sv: t0[1] + (t1[1] - t0[1]) * (sv - t0[0]) / ((t1[0] - t0[0]) or 1)
                sw2 = st[0][0]
                ov_ = sw2 - sa > 1
                tw = (sw2, tz(sw2))
                dd = []
                wl, wr = PX((sw2, st[0][1])), PX((sw2 + res['D'], st[0][1] - 350))   # sienas karkass zem spāres
                dd.append(f'<rect x="{wl[0]:.2f}" y="{wl[1]:.2f}" width="{wr[0] - wl[0]:.2f}" height="{wr[1] - wl[1]:.2f}" fill="#f3e2b5" stroke="{LINE_C}" stroke-width=".25"/>')
                if ov_:
                    dd.append(_adim(PX(t0), PX(tw), 4, f0(math.dist(t0, tw))))
                if ov_:
                    dd.append(_adim(PX(tw), PX(t1), 4, f0(math.dist(tw, t1))))
                dd.append(_adim(PX(t0), PX(t1), 9 if ov_ else 5, f0(math.dist(t0, t1))))
                yb = wr[1] + 4
                for a_, b_ in ([(sa, sw2)] if ov_ else []) + [(sw2, sm)]:
                    xa, xb = PX((a_, 0))[0], PX((b_, 0))[0]
                    dd.append(_dash(xa, yb, xb, yb) + _tick(xa, yb) + _tick(xb, yb) + _txt((xa + xb) / 2, yb - 1.8, f0(b_ - a_), 2.6))
                sp_ = PX(st[0])
                dd.append(_txt(sp_[0] - 3, sp_[1] + 1.2, f'{res.get("seat", KK.SEAT):.0f}', 2.6, 'end') + _txt(sp_[0] + 1.5, sp_[1] - 2.2, f'{st[1][0] - st[0][0]:.0f}', 2.6, 'start'))
                dd.append(_txt(PX((sm, 0))[0] - 2, sy - 6, f'{math.degrees(math.atan(res.get("seat", KK.SEAT) / ((st[1][0] - st[0][0]) or 1))):.0f}°', 3.4, 'end'))
                g.append(''.join(dd))
            # spāres garums: mēros gar spāri (kopā) un sarakstā
            L0 = None
        else:
            g.append(f'<polygon points="{" ".join(f"{a_:.2f},{b_:.2f}" for a_, b_ in pts)}" fill="{WOOD}" stroke="{LINE_C}" stroke-width=".3"/>')
        if L0 is not None:
            g.append(_dash(A[0], A[1] + 6, Bp[0], A[1] + 6) + _dash(Bp[0], Bp[1], Bp[0], A[1] + 7))
            g.append(_txt((A[0] + Bp[0]) / 2 - 6, (A[1] + Bp[1]) / 2 - 9, f0(L0), 3.8, rot=-math.degrees(th)))
        if L0 is not None:
            g.append(_txt(sx + 8, A[1] - 4, f'{math.degrees(th):.0f}°', 3.8, 'start'))
    rows = [(n, f'{b}×{h}', gg, c) for n, h, b, gg, c in KK.spare_list(R, res['DJ'])]
    t, ye = table_svg(282, 112, rows[:34], ('Detaļa', 'Šķērsgr.', 'Garums', 'Gab.'), (34, 18, 18, 12), fs=2.8, rh=3.8, hdr_right=(2, 3))
    tot = sum(r[2] * r[3] for r in rows) / 1000
    kv = (f'<g font-family="{FONT}"><rect x="282" y="{PH - 52}" width="124" height="26" fill="#fff" stroke="{INK}" stroke-width=".4"/>'
          f'<text x="286" y="{PH - 44}" font-size="4.2" font-weight="700">KVADRATŪRA: {fm2(KK.roof_area(R))} m²</text>'
          f'<text x="286" y="{PH - 38}" font-size="2.8" fill="{MUT}">spāres C24 45×{res["DJ"]:.0f} c/c 600 · {sum(1 for r in (R.get("rafs3d") or (0, []))[1] if r.get("loma") != "ridge_beam") or len(R["spares"])} gab. · {fm2(tot)} tm</text>'
          f'<text x="286" y="{PH - 32.5}" font-size="2.8" fill="{MUT}">kore {f0(R["ridge"])} mm no ±0,000 (jumta apakša)</text></g>')
    g.append(f'<text x="{16 + 22 + bw:.2f}" y="30" font-size="2.6" text-anchor="end" fill="{MUT}">M 1:{s}</text></g>')
    D.frame('JUMTS', ''.join(g) + t + kv, 'spāru plāns ar c/c 600, viena spāre ar slīpumu un garumu, saraksts')


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
    D.raw(f'<div class="sk"><iframe title="Skice" style="pointer-events:none;width:{w}mm;height:{h}mm;transform:scale({sc:.4f});transform-origin:0 0;margin-left:{(PW - w * sc) / 2:.1f}mm" '
          f'srcdoc="{html.escape(src, quote=True)}"></iframe></div>')


FONTI = {'Barlow': 'Barlow,Arial,sans-serif', 'Verdana': 'Verdana,Arial,sans-serif', 'Arial': 'Arial,Helvetica,sans-serif',
         'Sora': 'Sora,Arial,sans-serif', 'Georgia': 'Georgia,serif'}   # ražošanas lapu fonts (model.json projekts.razosanas_fonts)


def build(mp, out=None, cenas=None, profils=''):
    """cenas: {materiāla atslēga: €} no uzņēmuma cenu profila (tame.mat_key); profils: profila nosaukums tāmes kājenē."""
    m = json.load(open(mp, encoding='utf-8'))
    res = KK.generate(m)
    D = Doc(m)
    skice_page(D, mp, m)
    plan_page(D, res, m)
    for P in res['paneli']:
        if P.kind == 'arsiena':
            wall_page(D, P)
    partitions_pages(D, [P for P in res['paneli'] if P.kind != 'arsiena'])
    section_page(D, res, m)
    roof_page(D, res, m)
    summary_page(D, res)
    TM.pages(D, m, res, cenas, profils)
    n = len(D.pages)
    css = ('<style>@page{size:420mm 297mm;margin:0}html,body{margin:0;background:#d9dbdf}body{font-family:Barlow,Arial,sans-serif}'
           '.pg{width:420mm;height:297mm;background:#fff;margin:8mm auto;box-shadow:0 1px 6px rgba(0,0,0,.2);overflow:hidden;position:relative;page-break-after:always;break-after:page}'
           '.pg>svg{width:420mm;height:297mm;display:block}.sk{width:420mm;height:297mm;overflow:hidden}.sk iframe{border:0;display:block}'
           '@media print{html,body{background:none;zoom:1!important}.pg{margin:0;box-shadow:none}}</style>'
           '<script>(function(){var z=1;addEventListener("wheel",function(e){if(!e.ctrlKey&&!e.metaKey)return;e.preventDefault();'   # Ctrl + ritenis: tuvināšana pa peles vietu, cik tuvu vajag
           'var n=Math.min(Math.max(z*Math.exp(-e.deltaY*.01),.15),60),k=n/z,px=e.clientX+scrollX,py=e.clientY+scrollY;document.body.style.zoom=n;z=n;scrollTo(px*k-e.clientX,py*k-e.clientY)},{passive:false})})()</script>')
    doc = (f'<!doctype html><html lang="lv"><head><meta charset="utf-8"><title>{esc(D.model)} ražošana</title>{css}</head><body>'
           + ''.join(p.replace('@@N@@', str(n)) for p in D.pages) + '</body></html>')
    fn = (m.get('projekts') or {}).get('razosanas_fonts')
    fn = fn if fn in FONTI else 'Barlow'
    doc = re.sub(r'Barlow,\s*Arial(,\s*sans-serif)?', FONTI[fn], doc)
    if fn in ('Barlow', 'Sora'):
        doc = doc.replace('</head>', f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={fn}:wght@400;500;600;700&display=swap"></head>', 1)
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
