"""Materiālu tāme pa pīrāgiem konkrētam projektam: daudzums (m², m³, tm), rezerve un pirkšanas daudzums veikala vienībās
(loksnes, ruļļi, latu gabali). Cenas nāk no uzņēmuma cenu profila (uznemums.json "cenu_profili", cena par pirkšanas vienību);
bez profila cenu kolonnas paliek tukšas aizpildīšanai ar roku.

Pīrāgi = projekta slāņi (mm-config.json + projekts.piragi_layers), laukumi un kokmateriāli no karkass.py.
Slāņu tips (3. lauks): h apdare, m membrāna, a latojums, i karkass ar siltumizolāciju, o plātne (OSB, durelis), k ģipškartons.

    python tame.py <model.json>
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import karkass as KK  # noqa: E402

LOKSNE = {'osb': (2500, 1250), 'durel': (2500, 1250), 'gips': (1200, 2600)}
RULLIS_M2 = 75.0          # membrāna 1,5 × 50 m
LATA_M = 4.2              # latas / dēļa garums pirkšanai
REZ = {'m': 15, 'h': 10, 'a': 8, 'i': 5, 'o': 10, 'k': 10, '': 5}


def _size(name, t):
    q = re.search(r'(\d{2,3})\s*[x×]\s*(\d{2,3})', name)
    return (int(q.group(1)), int(q.group(2))) if q else (int(round(t)) or 25, 50)


def _poly_area(P):
    return KK._poly_area(P) / 1e6


def section_rows(key, title, layers, A_out, A_in, ctx):
    """Rindas vienai konstrukcijai. A_out: laukums ārpus karkasa (fasāde/jumta virsma), A_in: iekšpuses laukums (m²)."""
    rows = []
    i_idx = next((j for j, l in enumerate(layers) if (len(l) > 2 and l[2] == 'i')), None)
    n_out_a = 0
    for j, l in enumerate(layers):
        name, t = str(l[0]), float(l[1] or 0)
        kind = l[2] if len(l) > 2 else ''
        low = name.lower()
        outside = i_idx is not None and j < i_idx
        A = A_out if outside else A_in
        if kind == 'n':
            continue
        if kind == 'm' or (t == 0 and re.search(r'membr|izolācij|barjer|siet', low)):
            q = A * (1 + REZ['m'] / 100)
            if 'siet' in low:
                rows.append((name, '', A, 'm²', REZ['m'], math.ceil(q), 'm²'))
            else:
                rows.append((name, 'rullis 1,5×50 m', A, 'm²', REZ['m'], math.ceil(q / RULLIS_M2), 'rullis'))
            continue
        if kind == 'i':
            tm, m3 = ctx['timber'].get(key, (0, 0))
            b, h = 45, int(round(t))
            if tm:
                lab = {'J1': 'spāres', 'G1': 'grīdas sijas c/c 600'}.get(key, 'karkass (statņi, gulšņi, pārsedzes)')
                rows.append((f'C24 {b}×{h} {lab}', f'{b}×{h}', round(tm, 1), 'tm', REZ['i'], math.ceil(tm * (1 + REZ['i'] / 100)), 'tm (garumi pēc saraksta)' if key in ('S1', 'S2') else 'tm'))
                rows.append(('', '  tilpums', round(m3, 3), 'm³', REZ['i'], round(m3 * (1 + REZ['i'] / 100), 2), 'm³'))
            iso = A_in * t / 1000 * (1 - 45 / 600)
            rows.append((re.sub(r'^.*?,\s*', '', name) if ',' in name else f'Siltumizolācija {t:.0f} mm', f'{t:.0f} mm', round(iso, 2), 'm³', REZ['i'],
                         round(iso * (1 + REZ['i'] / 100), 2), f'm³ ({A_in * (1 + REZ["i"] / 100):.1f} m²)'.replace('.', ',')))
            continue
        if kind == 'a' or re.search(r'latoj|lata|instalācij', low):
            b, h = _size(name, t)
            if outside:
                n_out_a += 1
            hint = 'hor' in low and 650 or 'vert' in low and 600 or 0
            cc = ctx['cc'](key, outside, n_out_a, hint)
            tm = ctx['vert_tm'] if (key == 'J1' and outside and ('vert' in low or n_out_a == 2) and ctx.get('vert_tm')) else A / (cc / 1000)
            q = tm * (1 + REZ['a'] / 100)
            rows.append((name, f'{b}×{h}, c/c {cc}' if not (key == 'J1' and outside and ('vert' in low or n_out_a == 2)) else f'{b}×{h}, pa spārēm', round(tm, 1), 'tm', REZ['a'],
                         math.ceil(q / LATA_M), 'gab. ' + f'{LATA_M:g} m'.replace('.', ',')))
            continue
        if kind in ('o', 'k') or re.search(r'osb|durel|ģips|gips', low):
            sh = 'gips' if (kind == 'k' or re.search(r'ģips|gips', low)) else ('durel' if 'durel' in low else 'osb')
            w, hh = LOKSNE[sh]
            mult = 2 if re.search(r'2\s*kārt', low) else 1
            q = A * mult * (1 + REZ[kind or 'o'] / 100)
            rows.append((name, f'loksne {w}×{hh}', round(A * mult, 1), 'm²', REZ[kind or 'o'], math.ceil(q / (w * hh / 1e6)), 'loksne'))
            continue
        if kind == 'h' or re.search(r'apdar|dēlis|vagon|segum', low):
            q = A * (1 + REZ['h'] / 100)
            rows.append((name, f'{t:g} mm'.replace('.', ','), round(A, 1), 'm²', REZ['h'], math.ceil(q), 'm²'))
            continue
        if re.search(r'vainag', low):
            b, h = _size(name, t)
            tm = ctx['perim']
            rows.append((name, f'{b}×{h}', round(tm, 1), 'tm', 5, math.ceil(tm * 1.05 / LATA_M), 'gab. ' + f'{LATA_M:g} m'.replace('.', ',')))
            continue
        if re.search(r'lent', low):
            if not ctx['lent_tm'].get(key):
                continue
            rows.append((name, '', round(ctx['lent_tm'].get(key, 0), 1), 'tm', 10, math.ceil(ctx['lent_tm'].get(key, 0) * 1.1), 'tm'))
            continue
        rows.append((name, f'{t:g} mm'.replace('.', ','), round(A, 1), 'm²', 5, math.ceil(A * 1.05), 'm²'))
    return rows


def compute(m, res):
    LY = res['slani']
    ext = [P for P in res['paneli'] if P.kind == 'arsiena']
    prt = [P for P in res['paneli'] if P.kind != 'arsiena']
    A_ext_g = sum(P.area()[0] for P in ext)
    A_ext = sum(P.area()[1] for P in ext)
    A_prt = sum(P.area()[1] for P in prt)
    poly = m.get('poly') or [[0, 0], [m['W'], 0], [m['W'], m['D']], [0, m['D']]]
    A_floor = _poly_area(poly)
    perim = sum(math.hypot(poly[(i + 1) % len(poly)][0] - poly[i][0], poly[(i + 1) % len(poly)][1] - poly[i][1]) for i in range(len(poly))) / 1000
    R = res['jumts']
    A_roof = KK.roof_area(R)
    pitch = float((m.get('jumts') or {}).get('pitch') or 30)
    A_roof_in = A_floor / math.cos(math.radians(pitch))

    def tm_of(panels):
        tm = m3 = 0.0
        for n, h, b, g, c in KK.cutlist(panels):
            tm += g * c / 1000
            m3 += g * c * h * b / 1e9
        return tm, m3
    sp = KK.spare_list(R, res['DJ'])
    sp_tm = sum(g * c for _, _, _, g, c in sp) / 1000
    span = min(float(m['W']), float(m['D']))
    joist_tm = A_floor / 0.6 * 1.0
    timber = {'S1': tm_of(ext), 'S2': tm_of(prt), 'J1': (sp_tm, sp_tm * 45 * res['DJ'] / 1e6), 'G1': (joist_tm, joist_tm * 45 * 195 / 1e6)}

    def cc(key, outside, n, hint):
        if key == 'S1':
            return hint or (650 if n == 1 else 600) if outside else 410
        if key == 'J1':
            return 350 if outside else 400
        if key == 'G1':
            return 400
        return 600
    ctx = {'timber': timber, 'cc': cc, 'perim': perim, 'vert_tm': sp_tm, 'lent_tm': {'G1': perim, 'J1': 0}}
    c_ = lambda v: f'{v:.1f}'.replace('.', ',')
    secs = [('S1', LY['S1']['name'], A_ext, A_ext, f'ārsienas: fasāde {c_(A_ext_g)} m², bez ailām {c_(A_ext)} m²'),
            ('S2', LY['S2']['name'] + ' (abas puses)', A_prt, A_prt, f'starpsienas: {c_(A_prt)} m² (viena puse, bez ailām)'),
            ('G1', LY['G1']['name'], A_floor, A_floor, f'grīda: {c_(A_floor)} m², perimetrs {c_(perim)} m'),
            ('J1', LY['J1']['name'], A_roof, A_roof_in, f'jumts: virsma {c_(A_roof)} m² (ar pārkari), siltinātā daļa ~{c_(A_roof_in)} m²')]
    out = []
    for key, title, Ao, Ai, note in secs:
        if key not in LY:
            continue
        out.append((key, title, note, section_rows(key, title, LY[key]['layers'], Ao, Ai, ctx)))
    tot_tm = sum(v[0] for v in timber.values())
    tot_m3 = sum(v[1] for v in timber.values())
    return {'sekcijas': out, 'kokmateriali': (tot_tm, tot_m3), 'laukumi': {'arsienas': A_ext, 'starpsienas': A_prt, 'grida': A_floor, 'jumts': A_roof}}


def mat_key(r):
    """Materiāla atslēga cenu profilam (cena par pirkšanas vienību): C24 kokmateriāls pēc šķērsgriezuma (tm), latas pēc profila (gab.),
    siltumizolācija pēc nosaukuma (m³, neatkarīgi no biezuma), pārējais: nosaukums | izmērs | vienība."""
    unit = re.sub(r'\s*\(.*\)$', '', r[6])
    q = re.match(r'C24\s+(\d+)\s*[x×]\s*(\d+)', r[0])
    if q and r[3] == 'tm' and unit.startswith('tm'):
        return f'c24 {q.group(1)}x{q.group(2)}|tm'
    q = re.match(r'(\d+)×(\d+)', r[1])
    if unit.startswith('gab') and q:
        return f'lata {q.group(1)}x{q.group(2)}|{unit}'
    if unit == 'm³':
        return re.sub(r'\s+', ' ', f'{r[0]}|m³'.lower()).strip()
    return re.sub(r'\s+', ' ', f'{r[0]}|{r[1]}|{unit}'.lower()).strip()


def materials(T):
    """Unikālie tāmes materiāli (cenu profila rediģēšanai): [{key, nosaukums, izmers, vieniba, daudzums}]."""
    out = {}
    for _, _, _, rows in T['sekcijas']:
        for r in rows:
            if not r[0]:
                continue
            k = mat_key(r)
            q = r[5] if isinstance(r[5], (int, float)) else 0
            if k in out:
                out[k]['daudzums'] += q
            else:
                b = k.split('|')[0]
                if k.startswith('c24 ') and k.endswith('|tm'):
                    nm, iz = 'C24 kokmateriāls', b[4:].replace('x', '×')
                elif k.startswith('lata '):
                    nm, iz = 'Lata / dēlis', b[5:].replace('x', '×')
                elif k.endswith('|m³'):
                    nm, iz = r[0], ''
                else:
                    nm, iz = r[0], r[1]
                out[k] = {'key': k, 'nosaukums': nm, 'izmers': iz, 'vieniba': k.split('|')[-1], 'daudzums': q}
    return list(out.values())


def clean_prices(c):
    """{atslēga: cena} → tikai pozitīvi skaitļi (pieņem arī "12,5")."""
    out = {}
    for k, v in (c or {}).items():
        try:
            f = float(str(v).replace(',', '.').replace(' ', ''))
        except ValueError:
            continue
        if f > 0:
            out[str(k)] = f
    return out


def _eur(v):
    s = f'{v:,.2f}'.replace(',', ' ').replace('.', ',')
    return s


def _fmt(v):
    if isinstance(v, float):
        return f'{v:.2f}'.rstrip('0').rstrip(',.').replace('.', ',') if abs(v) < 100 else f'{v:.1f}'.replace('.', ',')
    return v


def pages(D, m, res, cenas=None, profils=''):
    """Tāmes lapas karkass_lapas Doc objektā (A3). cenas: {materiāla atslēga: € par pirkšanas vienību} no cenu profila; bez cenas ailes paliek tukšas."""
    from karkass_lapas import table_svg, PH, PW, INK, MUT, ACC, esc
    T = compute(m, res)
    cols = ('Nr.', 'Materiāls', 'Izmērs / profils', 'Aprēķins', 'Vien.', 'Rez. %', 'Pirkt', 'Pirkšanas vienība', 'Cena / vien., €', 'Summa, €')
    widths = (10, 108, 44, 22, 12, 13, 18, 50, 28, 26)
    blocks = []
    nr = 0
    cenas = clean_prices(cenas)
    total, n_bez, sec_tot = 0.0, 0, []
    for key, title, note, rows in T['sekcijas']:
        body, st = [], 0.0
        for r in rows:
            pc = sm = ''
            if r[0]:
                nr += 1
                c = cenas.get(mat_key(r))
                if c is not None and isinstance(r[5], (int, float)):
                    v = c * r[5]
                    st += v
                    pc, sm = _eur(c), _eur(v)
                else:
                    n_bez += 1
            body.append((str(nr) if r[0] else '', r[0] or r[1], r[1] if r[0] else '', _fmt(r[2]), r[3], r[4], _fmt(r[5]) if isinstance(r[5], float) else r[5], r[6], pc, sm))
        if cenas:
            body.append(('', 'Kopā sadaļā', '', '', '', '', '', '', '', _eur(st)))
        total += st
        sec_tot.append((title, st))
        blocks.append((title, note, body))
    pages_, cur, y = [], [], 0
    for b in blocks:
        h = 10 + 4.4 * (len(b[2]) + 1)
        if cur and y + h > 212:
            pages_.append(cur)
            cur, y = [], 0
        cur.append(b)
        y += h
    if cur:
        pages_.append(cur)
    for pi, grp in enumerate(pages_):
        g, yy = [], 30
        for title, note, body in grp:
            g.append(f'<text x="14" y="{yy + 4}" font-family="Barlow,Arial" font-size="4.6" font-weight="700" fill="{INK}">{esc(title)}</text>'
                     f'<text x="{PW - 14}" y="{yy + 4}" font-family="Barlow,Arial" font-size="2.8" text-anchor="end" fill="{MUT}">{esc(note)}</text>')
            t, yy = table_svg(14, yy + 6, body, cols, widths, fs=3.0, rh=4.4)
            g.append(t)
            yy += 6
        if pi == len(pages_) - 1:
            tm, m3 = T['kokmateriali']
            g.append(f'<g font-family="Barlow,Arial"><rect x="14" y="{PH - 46}" width="{PW - 28}" height="20" fill="#f4f7fd" stroke="{ACC}" stroke-width=".4"/>'
                     f'<text x="19" y="{PH - 38}" font-size="4" font-weight="700" fill="{INK}">Kokmateriāli kopā (C24): {tm:.0f} tm · {m3:.2f} m³</text>'.replace(f'{m3:.2f}', f'{m3:.2f}'.replace('.', ','))
                     + f'<text x="19" y="{PH - 31.5}" font-size="2.8" fill="{MUT}">Daudzumi pēc projekta ģeometrijas; pirkšanas daudzums noapaļots uz augšu (loksnes, ruļļi, latu gabali {str(LATA_M).replace(".", ",")} m). '
                     + (f'Cenas: profils „{esc(profils)}” (bez PVN, par pirkšanas vienību); summa = pirkt × cena.' + (f' {n_bez} pozīcijām cenas nav.' if n_bez else '') if cenas else 'Cenu kolonnas aizpildāmas; summa = pirkt × cena.') + '</text>'
                     + (f'<text x="{PW - 19}" y="{PH - 38}" font-size="4" font-weight="700" text-anchor="end" fill="{INK}">KOPĀ: {_eur(total)} €' + (' *' if n_bez else '') + '</text>'
                        f'<text x="{PW - 19}" y="{PH - 31.5}" font-size="2.8" text-anchor="end" fill="{MUT}">' + esc(' · '.join(f'{t.split(" ")[0]} {_eur(v)}' for t, v in sec_tot)) + '</text>'
                        if cenas else f'<text x="{PW - 19}" y="{PH - 38}" font-size="4" font-weight="700" text-anchor="end" fill="{INK}">KOPĀ: ________ €</text>') + '</g>')
        D.frame('MATERIĀLU TĀME' + (f' ({pi + 1}/{len(pages_)})' if len(pages_) > 1 else ''), ''.join(g),
                'pa pīrāgiem (slāņi no ārpuses uz iekšu); daudzums, rezerve un pirkšanas daudzums')


if __name__ == '__main__':
    mdl = json.load(open(sys.argv[1], encoding='utf-8'))
    T = compute(mdl, KK.generate(mdl))
    for key, title, note, rows in T['sekcijas']:
        print(f'== {title}  ({note})')
        for r in rows:
            print('   ', ' | '.join(str(_fmt(c)) for c in r))
    print('Kokmateriāli: %.0f tm, %.2f m³' % T['kokmateriali'])
