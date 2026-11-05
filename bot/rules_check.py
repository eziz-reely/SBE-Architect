"""Noteikumu pārbaudītājs: nolasa model.json un izmēra mēbeļu attālumus un logu pozīcijas pret zināšanām.
TIKAI PĀRBAUDE: neko nemaina, nepalaiž generate.py, nerada failus.

    python rules_check.py "..\\MĀJAS\\30m2\\MM-30-01\\model.json"        # viens modelis
    python rules_check.py --visi                                      # visi MĀJAS\\*\\*\\model.json
    python rules_check.py <model.json> -v                             # + visi izmērītie attālumi

Smaguma pakāpes:  KĻŪDA  = pārkāpj [MM] noteikumu vai ir ģeometriska kļūda (mēbele ārpus telpas, durvis uz mēbeli)
                  BRĪD.  = zem [MyCabin]/[prakse] sliekšņa
                  INFO   = ziņa, bez vērtējuma
Sliekšņu avoti: zinasanas_mebeles_logi.md (3., 4., 5. nodaļa un papildinājums).
"""
import glob, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAJAS = os.path.join(os.path.dirname(HERE), 'MĀJAS')

# sliekšņi, mm
WIN_PART_MIN = 150       # [prakse] logs vismaz 150 mm no starpsienas (karkasa stabs + aplodas)
WIN_DOOR_MIN = 300       # [prakse] logs vismaz 300 mm no ārdurvīm tajā pašā sienā
WIN_RATIO_MIN = 1 / 8    # [prakse] logu laukums / grīdas laukums (dzīvojamām telpām)
BED_SIDE_MIN = 600       # [prakse] brīva josla gar vienu gultas garo malu
SOFA_KITCHEN_MIN = 700   # [MM]
TABLE_CLEAR_MIN = 700    # [MyCabin/prakse] ap ēdamgaldu (mērķis 800)
PASSAGE_MIN = 800        # [prakse] eja starp mēbelēm
TOILET_SIDE_MIN = 200    # [prakse] no poda malas līdz izlietnei/sienai
DOOR_GAP_MIN = 50        # [MM] mēbele — durvju vērtne


def fbox(f):
    """Mēbeles taisnstūris [x0, y0, x1, y1] vai None (kā generate.fbox)."""
    n, a = f[0], f[1:]
    if n == 'bed' and len(a) > 4 and a[4] in ('n', 's'):      # galvgalis pie ziemeļu/dienvidu sienas: garums pa y
        return [a[0], a[1], a[0] + a[3], a[1] + a[2]]
    if n in ('bed', 'R', 'sofa', 'basin'):
        return [a[0], a[1], a[0] + a[2], a[1] + a[3]]
    if n == 'nightstand': return [a[0], a[1], a[0] + 450, a[1] + 420]
    if n == 'washer': return [a[0], a[1], a[0] + 600, a[1] + 600]
    if n == 'shower': return [a[0], a[1], a[0] + a[2], a[1] + a[2]]
    if n == 'toilet' and len(a) > 3:      # pie sānsienas: [pods, sienas x, centra y, 1, 'e'|'w']
        return [a[0] - 540, a[1] - 215, a[0], a[1] + 215] if a[3] == 'e' else [a[0], a[1] - 215, a[0] + 540, a[1] + 215]
    if n == 'toilet': return [a[0] - 215, min(a[1], a[1] + 540 * a[2]), a[0] + 215, max(a[1], a[1] + 540 * a[2])]
    if n == 'Ci' and a[2] > 100: return [a[0] - a[2], a[1] - a[2], a[0] + a[2], a[1] + a[2]]
    return None


def inside(b, c, tol=1):
    return b[0] >= c[0] - tol and b[1] >= c[1] - tol and b[2] <= c[2] + tol and b[3] <= c[3] + tol


def overlap(a, b):
    return min(a[2], b[2]) - max(a[0], b[0]) > 1 and min(a[3], b[3]) - max(a[1], b[1]) > 1


def gap(a, b):
    """Mazākais attālums starp diviem taisnstūriem (0 ja pārklājas)."""
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy) if dx and dy else max(dx, dy)


def rect(r):
    return [r[0], r[1], r[0] + r[2], r[1] + r[3]]


class Report:
    def __init__(self):
        self.rows = []

    def add(self, level, rule, text, src=''):
        self.rows.append((level, rule, text, src))


def room_of(m, x, y):
    for r in m['rooms']:
        for q in r['r']:
            if q[0] - 1 <= x <= q[0] + q[2] + 1 and q[1] - 1 <= y <= q[1] + q[3] + 1:
                return r, rect(q)
    return None, None


def check(m, verbose=False):
    R = Report()
    W, D = m['W'], m['D']
    furn = [f for f in m['furniture'] if f[0] != 'Ln']
    boxes = [(f, fbox(f)) for f in furn if fbox(f)]
    top = [(f, b) for f, b in boxes if not any(g is not f and gb is not b and inside(b, gb) and (gb[2] - gb[0]) * (gb[3] - gb[1]) > (b[2] - b[0]) * (b[3] - b[1]) for g, gb in boxes)]
    meas = []                               # visi izmērītie lielumi

    # ---------- 1. mēbeles telpā ----------
    for f, b in top:
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        r, rr = room_of(m, cx, cy)
        if not r:
            R.add('KĻŪDA', 'mēbele telpā', f'{f[0]} {[round(v) for v in b]} nav nevienā telpā.', 'ģeometrija')
        elif not inside(b, rr, 30):
            R.add('KĻŪDA', 'mēbele telpā', f"{f[0]} {[round(v) for v in b]} sniedzas ārpus telpas '{r['n']}'.", 'ģeometrija')

    # ---------- 2. durvju vērtnes pret mēbelēm ----------
    for d in m['doors']:
        if d.get('entry'):
            continue
        s = d.get('side', 1)
        w = d['w']
        z = [d['x'], d['y'], d['x'] + w, d['y'] + s * w] if d['o'] == 'h' else [d['x'], d['y'], d['x'] + s * w, d['y'] + w]
        z = [min(z[0], z[2]), min(z[1], z[3]), max(z[0], z[2]), max(z[1], z[3])]
        # vērtne skar tikai tuvāko ceturtdaļloku, tāpēc ar 50 mm rezervi pārbauda visu kvadrātu
        zz = [z[0] - DOOR_GAP_MIN, z[1] - DOOR_GAP_MIN, z[2] + DOOR_GAP_MIN, z[3] + DOOR_GAP_MIN]
        for f, b in top:
            if overlap(zz, b):
                dist = gap(z, b)
                R.add('KĻŪDA' if dist < 1 else 'BRĪD.', 'durvis-mēbele', f"durvju vērtne (x{round(d['x'])},y{round(d['y'])}) un {f[0]} {[round(v) for v in b]}: atstarpe {dist:.0f} mm (jābūt ≥ {DOOR_GAP_MIN}).", '[MM]')

    # ---------- 3. guļamistaba ----------
    for f, b in top:
        if f[0] != 'bed':
            continue
        r, rr = room_of(m, (b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        if not r or 'Guļ' not in r['n']:
            continue
        orient = f[5] if len(f) > 5 else 'w'
        if orient in ('w', 'e'):          # garā ass pa x, galvgalis pie sienas
            sides = [b[1] - rr[1], rr[3] - b[3]]
        else:
            sides = [b[0] - rr[0], rr[2] - b[2]]
        meas.append(f'gulta: brīvā josla pa sāniem {sides[0]:.0f} / {sides[1]:.0f} mm (vērtne nav ieskaitīta)')
        if max(sides) < BED_SIDE_MIN:
            R.add('BRĪD.', 'gulta', f'brīvā josla gar gultu {max(sides):.0f} mm < {BED_SIDE_MIN}.', '[prakse]')
        # naktsgaldiņi
        ns = [bb for ff, bb in top if ff[0] == 'nightstand' and overlap([b[0] - 5, b[1] - 460, b[2] + 5, b[3] + 460], bb)]
        if not ns:
            R.add('INFO', 'gulta', 'naktsgaldiņu nav (nav vietas vai izņemti).', '[MM]')

    # ---------- 4. dzīvojamā istaba ----------
    sofa = next(((f, b) for f, b in top if f[0] == 'sofa'), None)
    tables = [(f, b) for f, b in top if f[0] == 'Ci']
    kitchen = [(f, b) for f, b in top if f[0] == 'R' and max(b[2] - b[0], b[3] - b[1]) >= 1500]
    if sofa and kitchen:
        for kf, kb in kitchen:
            g = gap(sofa[1], kb)
            meas.append(f'dīvāns — virtuves rinda: {g:.0f} mm')
            if g < SOFA_KITCHEN_MIN:
                R.add('KĻŪDA', 'dīvāns-virtuve', f'dīvāns {g:.0f} mm no virtuves fronta (≥ {SOFA_KITCHEN_MIN}).', '[MM]')
    for tf, tb in tables:
        liv, lr = room_of(m, (tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2)
        if not liv or 'Dzīv' not in liv['n']:
            continue
        others = [(f, b) for f, b in top if f is not tf and f[0] in ('R', 'sofa')]
        dists = [(gap(tb, b), f[0]) for f, b in others]
        dists += [(tb[0] - lr[0], 'siena W'), (lr[2] - tb[2], 'siena E'), (tb[1] - lr[1], 'siena N'), (lr[3] - tb[3], 'siena S')]
        for dist, what in dists:
            meas.append(f'galds — {what}: {dist:.0f} mm')
        near = [(dd, w) for dd, w in dists if dd < TABLE_CLEAR_MIN and not w.startswith('siena')]
        for dd, w in near:
            R.add('BRĪD.', 'galds', f'ēdamgalds {dd:.0f} mm no {w} (ap galdu ≥ {TABLE_CLEAR_MIN}, ar krēsliem ~800).', '[MyCabin/prakse]')
        walls = [(dd, w) for dd, w in dists if w.startswith('siena') and dd < 300]
        # galds pie sienas ir pieļaujams (vienā pusē), tikai ziņa
        for dd, w in walls:
            R.add('INFO', 'galds', f'galds {dd:.0f} mm no ({w}); krēsla vieta nav paredzēta.', '[prakse]')

    # ---------- 5. vannasistaba ----------
    toilet = next(((f, b) for f, b in top if f[0] == 'toilet'), None)
    for f, b in top:
        if f[0] == 'toilet':
            continue
    if toilet:
        tf, tb = toilet
        for f, b in top:
            if f[0] in ('basin', 'shower', 'washer'):
                g = gap(tb, b)
                if g < 1e5:
                    meas.append(f'pods — {f[0]}: {g:.0f} mm')
                if f[0] in ('basin', 'shower') and 0 < g < TOILET_SIDE_MIN:
                    R.add('BRĪD.', 'pods', f'pods {g:.0f} mm no {f[0]} (≥ {TOILET_SIDE_MIN} sānos).', '[prakse]')
                if g == 0:
                    R.add('KĻŪDA', 'pods', f'pods pārklājas ar {f[0]}.', 'ģeometrija')
        # pods centrs ≥ 400 no sānu sienas
        side_t = len(tf) > 4
        r, rr = room_of(m, (tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2)
        if rr:
            side = min(tf[2] - rr[1], rr[3] - tf[2]) if side_t else min(tf[1] - rr[0], rr[2] - tf[1])
            meas.append(f'pods: centrs līdz sānu sienai {side:.0f} mm')
            if side < 400:
                R.add('KĻŪDA', 'pods', f'poda centrs {side:.0f} mm no sānu sienas (≥ 400).', '[MM]')
        if side_t:
            z = [tb[0] - 600, tf[2] - 400, tb[0], tf[2] + 400] if tf[4] == 'e' else [tb[2], tf[2] - 400, tb[2] + 600, tf[2] + 400]
        else:
            z = [tf[1] - 400, tb[3], tf[1] + 400, tb[3] + 600] if tf[3] == 1 else [tf[1] - 400, tb[1] - 600, tf[1] + 400, tb[1]]
        for f, b in top:
            if f[0] != 'toilet' and overlap(z, b):
                R.add('KĻŪDA', 'pods', f'{f[0]} traucē apsēsties uz poda (priekšā 800×600 mm).', '[MM]')
    for f, b in top:
        if f[0] != 'washer':
            continue
        free = []
        for nm, z in (('W', [b[0] - 600, b[1], b[0], b[3]]), ('E', [b[2], b[1], b[2] + 600, b[3]]), ('N', [b[0], b[1] - 600, b[2], b[1]]), ('S', [b[0], b[3], b[2], b[3] + 600])):
            r, rr = room_of(m, (z[0] + z[2]) / 2, (z[1] + z[3]) / 2)
            ok = rr is not None and inside(z, rr, 1) and not any(overlap(z, bb) for ff, bb in top if ff is not f)
            free.append((nm, ok))
        meas.append('veļasmašīna: brīva 600 mm josla: ' + ', '.join(n for n, ok in free if ok))
        if not any(ok for _, ok in free):
            R.add('BRĪD.', 'veļasmašīna', 'veļasmašīnai priekšā nav brīvas 600 mm joslas.', '[prakse]')

    # ---------- 6. logi ----------
    wins = m['windows']
    T = min(r['r'][0][0] for r in m['rooms'])
    for w in wins:
        if w['o'] == 'h':
            a0, a1 = w['x'], w['x'] + w['len']
            wall = 'north' if w['y'] == 0 else 'south'
        else:
            a0, a1 = w['y'], w['y'] + w['len']
            wall = 'west' if w['x'] == 0 else 'east'
        cx = (a0 + a1) / 2
        # telpa, kuras ārsienā logs atrodas
        host = None
        for r in m['rooms']:
            for q in r['r']:
                touch = ((wall == 'north' and abs(q[1] - T) < 2) or (wall == 'south' and abs(q[1] + q[3] - (D - T)) < 2) or
                         (wall == 'west' and abs(q[0] - T) < 2) or (wall == 'east' and abs(q[0] + q[2] - (W - T)) < 2))
                lo, hi = (q[0], q[0] + q[2]) if wall in ('north', 'south') else (q[1], q[1] + q[3])
                if touch and lo - 1 <= cx <= hi + 1:
                    host = (r, lo, hi)
        w['_host'] = host
        if not host:
            R.add('KĻŪDA', 'logs', f"logs {wall} {round(a0)}–{round(a1)} neatrodas nevienas telpas ārsienā.", 'ģeometrija')
            continue
        r, lo, hi = host
        left, right = a0 - lo, hi - a1
        meas.append(f"logs {wall} {round(a0)}: {r['n']}: attālums līdz starpsienai {left:.0f} / {right:.0f} mm")
        for side, v in (('kreisā', left), ('labā', right)):
            tol_edge = 40
            if v < -tol_edge:
                R.add('KĻŪDA', 'logs-starpsiena', f"logs {wall} {round(a0)} ({r['n']}) iesniedzas {-v:.0f} mm aiz starpsienas ({side} puse).", 'ģeometrija')
            elif v < WIN_PART_MIN:
                # ja telpa beidzas pie ārsienas stūra, tas ir stūris, ne starpsiena
                corner = (lo <= T + 2) if side == 'kreisā' else (hi >= (W if wall in ('north', 'south') else D) - T - 2)
                R.add('BRĪD.', 'logs-starpsiena' if not corner else 'logs-stūris', f"logs {wall} {round(a0)} ({r['n']}) {v:.0f} mm no {'stūra' if corner else 'starpsienas'} ({side} puse, ≥ {WIN_PART_MIN}).", '[prakse]')
        # ārdurvis tajā pašā sienā
        for d in m['doors']:
            if not d.get('entry'):
                continue
            if wall == 'south' and d['o'] == 'h':
                g = max(a0 - (d['x'] + d['w']), d['x'] - a1)
                meas.append(f"logs {wall} {round(a0)} — ārdurvis: {g:.0f} mm")
                if g < WIN_DOOR_MIN:
                    R.add('BRĪD.', 'logs-durvis', f'logs {wall} {round(a0)} tikai {g:.0f} mm no ārdurvīm (≥ {WIN_DOOR_MIN}).', '[prakse]')
        # augstumi
        if w['sill'] > 0 and (w['head'] - w['sill']) < 400:
            R.add('BRĪD.', 'logs-izmērs', f"logs {wall} {round(a0)} tikai {w['head'] - w['sill']} mm augsts.", '[prakse]')
        if w['head'] > 2100 and w['sill'] < 2000 and w['kind'] != 'parts':
            R.add('INFO', 'logs-augstums', f"logs {wall} {round(a0)}: augša {w['head']} mm (standarts 2100).", '[MM]')

    # logu laukums pret grīdu
    for r in m['rooms']:
        k = 'liv' if 'Dzīv' in r['n'] else 'bed' if 'Guļ' in r['n'] else 'wc' if r['n'] == 'WC' else None
        if not k:
            continue
        area = sum(q[2] * q[3] for q in r['r']) / 1e6
        gl = sum(w['len'] * (w['head'] - w['sill']) for w in wins if w.get('_host') and w['_host'][0] is r) / 1e6
        ratio = gl / area if area else 0
        meas.append(f"{r['n']}: loga laukums {gl:.2f} m² / grīda {area:.1f} m² = 1/{(1 / ratio) if ratio else 0:.1f}")
        if k in ('liv', 'bed') and ratio < WIN_RATIO_MIN:
            R.add('BRĪD.', 'dienasgaisma', f"{r['n']}: logi {gl:.2f} m² no {area:.1f} m² = 1/{(1 / ratio) if ratio else 0:.1f} (≥ 1/8).", '[prakse; LBN jāpārbauda]')
        if gl == 0:
            R.add('KĻŪDA' if k != 'wc' else 'BRĪD.', 'logs-trūkst', f"{r['n']} bez ārsienas loga.", '[prakse]')
    liv_sides = {w['side'] for w in wins if w.get('_host') and 'Dzīv' in w['_host'][0]['n']}
    if len(liv_sides) < 2:
        R.add('BRĪD.', 'dzīvojamā-logi', f"dzīvojamai logi tikai vienā pusē ({', '.join(liv_sides) or 'nav'}); labāk gals + garā siena.", '[MyCabin]')
    # WC logs virs poda
    if toilet:
        wcw = [w for w in wins if w.get('_host') and w['_host'][0]['n'] == 'WC']
        for w in wcw:
            if w['o'] == 'h' and len(toilet[0]) <= 4:
                off = abs((w['x'] + w['len'] / 2) - toilet[0][1])
                meas.append(f'WC logs: centrs {off:.0f} mm no poda ass')
                if off > 300:
                    R.add('INFO', 'WC logs', f'WC logs nav virs poda (nobīde {off:.0f} mm).', '[MM]')
    # virtuve un logs
    for kf, kb in kitchen:
        near = [w for w in wins if (w['o'] == 'h' and w['x'] < kb[2] + 600 and w['x'] + w['len'] > kb[0] - 600 and abs(w['y'] - (kb[1] if kb[1] < D / 2 else kb[3])) < 700)
                or (w['o'] == 'v' and w['y'] < kb[3] + 600 and w['y'] + w['len'] > kb[1] - 600 and abs(w['x'] - (kb[0] if kb[0] < W / 2 else kb[2])) < 700)]
        if not near:
            R.add('INFO', 'virtuve', 'virtuves rinda starpsienas pusē, loga virs darba virsmas nav (pieļaujams, Milla/Sauna tips).', '[MyCabin]')

    # ---------- 7. loft ----------
    lf = m.get('loft') or {}
    if lf.get('rooms'):
        pitch = m['jumts']['pitch']
        eave = m['jumts']['eave']
        tn = math.tan(math.radians(pitch))
        lvl = lf['level']
        for f in lf.get('furniture', []):
            if f[0] != 'bed':
                continue
            bb = fbox(f)
            ys = [bb[1], bb[3]]
            hs = [eave + min(y, D - y) * tn - lvl for y in ys]
            ridge = eave + (D / 2) * tn - lvl
            meas.append(f'loft gulta: jumta augstums virs lofta grīdas pie malām {hs[0]:.0f} / {hs[1]:.0f} mm, kores pusē {ridge:.0f} mm')
            if ridge < 1800:
                R.add('INFO', 'loft', f'loft ir guļvieta: maksimālais augstums {ridge:.0f} mm (< 1800), var tikai gulēt/rāpot. Konkurentu loftiem 1.8+ m.', '[MM/planlib]')
            if min(hs) < 700:
                R.add('BRĪD.', 'loft', f'loft gulta: augstums pie malas {min(hs):.0f} mm (< 700), nav iespējams apsēsties.', '[prakse]')
        lw = lf.get('windows', [])
        if not lw:
            R.add('BRĪD.', 'loft-logs', 'loftam nav loga.', '[prakse]')
        for w in lw:
            if not 2300 <= w['sill'] <= 2800:
                R.add('INFO', 'loft-logs', f"loft logs {w['side']} palodze {w['sill']} mm (parasti 2300–2700).", '[MyCabin/MM]')

    return R, meas


def show(path, verbose):
    m = json.load(open(path, encoding='utf-8'))
    R, meas = check(m, verbose)
    print(f"\n=== {m.get('id', os.path.basename(os.path.dirname(path)))}  {m['W']:.0f} × {m['D']:.0f} mm, kore {m['ievade']['augstums']:.0f}")
    order = {'KĻŪDA': 0, 'BRĪD.': 1, 'INFO': 2}
    for lvl, rule, text, src in sorted(R.rows, key=lambda r: order[r[0]]):
        print(f'  {lvl:6s} [{rule}] {text} {src}')
    n = {k: sum(1 for r in R.rows if r[0] == k) for k in order}
    print(f"  kopā: {n['KĻŪDA']} kļūdas, {n['BRĪD.']} brīdinājumi, {n['INFO']} info")
    if verbose:
        print('  -- izmērītie lielumi --')
        for x in meas:
            print('   ', x)
    return n


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    v = '-v' in sys.argv
    a = [x for x in sys.argv[1:] if not x.startswith('-')]
    if '--visi' in sys.argv:
        a = sorted(glob.glob(os.path.join(MAJAS, '*', '*', 'model.json')))
    if not a:
        raise SystemExit(__doc__)
    for p in a:
        show(p, v)
