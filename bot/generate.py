"""MM Homes modeļu bots: no 3 izmēriem uztaisa mājas modeli (model.json) un rasējumu lapu (LV, EN).

Lietošana:  python generate.py <garums mm> <platums mm> <augstums mm> [nosaukums]
Piemērs:    python generate.py 8570 3500 4000
            -> MM System/MĀJAS/30m2/MM-30-01/model.json + rasejumi/MM-30-01_LV.html, MM-30-01_EN.html

Augstums = kores augstums no ±0,000 līdz jumta virsmai.
Tipoloģija (etalons: 30 m² māja): guļamistaba | WC virs priekšnama | dzīvojamā istaba ar virtuvi.
Visi izmēri, logi, durvis un mēbeles tiek aprēķināti no garuma un platuma.

Mansards:   --mansards ja|ne   (noklusējums ja; ne = bez mansarda stāva un mansarda logiem)
Varianti:   --varianti N       plānotājs (planner.py) uztaisa N atšķirīgus plānojumus (II/L/T, ar mansardu tikai II),
            katrs iziet rules_check ar 0 kļūdām un 0 brīdinājumiem, un katram tiek uztaisīta tā pati rasējumu lapa.
            -> MĀJAS/50m2/MM-50-01-V01/model.json + rasejumi/MM-50-01-V01_LV.html ..., kopsavilkums MM-50-01/varianti.html
Piemērs:    python generate.py 14280 3500 5600 --mansards ne --varianti 4
"""
import json, math, os, sys

from build_model import build, HERE

MAJAS = os.path.join(os.path.dirname(HERE), 'MĀJAS')   # MM System\\MĀJAS

CFG = json.load(open(os.path.join(HERE, 'sablons', 'mm-config.json'), encoding='utf-8'))
T = sum(l[1] for l in CFG['layers']['S1']['layers'])      # ārsiena (MM S-04) 283,5
t = sum(l[1] for l in CFG['layers']['S2']['layers'])      # starpsiena 195
ROOF_T = sum(l[1] for l in CFG['layers']['J1']['layers'])  # jumta pīrāgs
PITCH = CFG['roof']['pitch']

HALL_D = 958        # priekšnama dziļums
MIN = {'bed': 2100, 'wc': 1600, 'liv': 2400}
CAP = {'bed': 3600, 'wc': 2600}
SHARE = {'bed': .13, 'wc': .53}  # etalona proporcijas virs minimuma; atlikums dzīvojamai istabai


def fbox(f):
    """Mēbeles aizņemtais taisnstūris [x0, y0, x1, y1] vai None (līnijas)."""
    n, a = f[0], f[1:]
    if n in ('bed', 'R', 'sofa', 'basin'):
        return [a[0], a[1], a[0] + a[2], a[1] + a[3]]
    if n == 'nightstand': return [a[0], a[1], a[0] + 450, a[1] + 420]
    if n == 'washer': return [a[0], a[1], a[0] + 600, a[1] + 600]
    if n == 'shower': return [a[0], a[1], a[0] + a[2], a[1] + a[2]]
    if n == 'toilet': return [a[0] - 215, min(a[1], a[1] + 540 * a[2]), a[0] + 215, max(a[1], a[1] + 540 * a[2])]
    if n == 'Ci' and a[2] > 100: return [a[0] - a[2], a[1] - a[2], a[0] + a[2], a[1] + a[2]]
    if n == 'chair': return [a[0] - 230, a[1] - 230, a[0] + 230, a[1] + 230]
    return None


def window_rule(furn, win, x0, x1, y0, y1, depth=700, gap=50):
    """KLIENTA PROJEKTS 6: logam priekšā (zona = loga platums + 50 mm katrā pusē, 700 mm dziļumā) nav mēbeļu.
    Izņēmumi: gulta zem augsta loga (palodze >= 1200, vēl jāprecizē); logs virs poda; dīvāns ar sānu pret logu."""
    for w in win:
        if w['o'] == 'h':
            z = [w['x'] - gap, y0, w['x'] + w['len'] + gap, y0 + depth] if w['y'] == 0 else [w['x'] - gap, y1 - depth, w['x'] + w['len'] + gap, y1]
        else:
            z = [x0, w['y'] - gap, x0 + depth, w['y'] + w['len'] + gap] if w['x'] == 0 else [x1 - depth, w['y'] - gap, x1, w['y'] + w['len'] + gap]
        for f in furn:
            b = fbox(f)
            if not b or (f[0] == 'bed' and w['sill'] >= 1200) or f[0] == 'toilet':
                continue   # gulta zem augsta loga; virs poda logs drīkst būt
            if f[0] == 'sofa' and (f[5] in ('n', 's')) == (w['o'] == 'v'):
                continue   # dīvāns drīkst būt ar sānu pret logu (atzveltne pie perpendikulāras sienas)
            if b[0] < z[2] and b[2] > z[0] and b[1] < z[3] and b[3] > z[1]:
                raise SystemExit(f"Mēbele {f[0]} {b} ir loga priekšā (logs x {w['x']}, y {w['y']}). Labo generate.py izkārtojumu.")
    return furn


def wc_rule(furn, cx, wy, free=600, half=400):
    """KLIENTA PROJEKTS: uz poda var normāli apsēsties: priekšā brīvs 800 x 600 mm laukums.
    Ja netiek klāt veļasmašīnai, pārbīda izlietni vai veļasmašīnu (pods paliek)."""
    z = [cx - half, wy + 540, cx + half, wy + 540 + free]
    for f in furn:
        b = fbox(f)
        if b and f[0] != 'toilet' and b[0] < z[2] and b[2] > z[0] and b[1] < z[3] and b[3] > z[1]:
            raise SystemExit(f"WC: mēbele {f[0]} {b} traucē apsēsties uz poda. Pārbīdi izlietni vai veļasmašīnu.")


def r1(x):
    return round(x, 1)


def model(L, B, H, mid=None, projekts=None):
    W, D = float(L), float(B)
    x0, x1, y0, y1 = T, W - T, T, D - T
    din = y1 - y0
    net = (x1 - x0) - 2 * t
    extra = net - sum(MIN.values())
    if extra < 0:
        raise SystemExit(f'Māja par īsu: vajag vismaz {sum(MIN.values()) + 2 * t + 2 * T:.0f} mm garumu')
    bed = min(CAP['bed'], MIN['bed'] + extra * SHARE['bed'])
    wc = min(CAP['wc'], MIN['wc'] + extra * SHARE['wc'])
    liv = net - bed - wc
    bx0, bx1 = x0, x0 + bed
    wx0, wx1 = bx1 + t, bx1 + t + wc
    lx0, lx1 = wx1 + t, x1
    hy0 = y1 - HALL_D            # priekšnama augša
    wy1 = hy0 - t                # WC apakša
    tanp = math.tan(math.radians(PITCH))
    eave = H - ROOF_T / math.cos(math.radians(PITCH)) - (D / 2) * tanp

    rooms = [
        {'n': 'Dzīvojamā istaba ar virtuvi', 'en': 'Living room with kitchen', 'r': [[r1(lx0), y0, r1(liv), r1(din)]]},
        {'n': 'Guļamistaba', 'en': 'Bedroom', 'r': [[bx0, y0, r1(bed), r1(din)]]},
        {'n': 'WC', 'en': 'WC', 'r': [[r1(wx0), y0, r1(wc), r1(wy1 - y0)]]},
        {'n': 'Priekšnams', 'en': 'Entrance hall', 'r': [[r1(wx0), r1(hy0), r1(lx0 - wx0), HALL_D]]},
    ]
    door_w = 1000
    doors = [
        {'x': r1(lx0 - 250 - door_w), 'y': y1, 'o': 'h', 'hinge': 's', 'side': 1, 'w': door_w, 'th': T, 'entry': True},
        {'x': r1(bx1), 'y': r1(hy0 + 75), 'o': 'v', 'hinge': 'e', 'side': -1, 'w': 800, 'th': t},
        {'x': r1(wx0 + 171.5), 'y': r1(wy1), 'o': 'h', 'hinge': 's', 'side': -1, 'w': 800, 'th': t},
    ]
    gl = min(2200, din - 700)
    win = [
        {'len': 900, 'sill': 900, 'head': 2100, 'kind': 'tilt', 'x': r1((bx0 + bx1) / 2 - 450 + 150), 'y': y1, 'o': 'h', 'side': 'south'},
        {'len': 900, 'sill': 900, 'head': 2100, 'kind': 'tilt', 'x': r1(lx0 + .74 * liv - 450), 'y': y1, 'o': 'h', 'side': 'south'},
        {'len': 600, 'sill': 900, 'head': 2100, 'kind': 'tilt', 'x': r1(wx0 + 400 - 300), 'y': 0, 'o': 'h', 'side': 'north'},   # WC logs virs poda
        {'len': 1200, 'sill': 1600, 'head': 2100, 'kind': 'hopper', 'x': 0, 'y': r1((D - 1200) / 2), 'o': 'v', 'out': -1, 'side': 'west'},
        {'len': gl, 'sill': 0, 'head': 2100, 'kind': 'parts', 'tilt': True, 'x': x1, 'y': r1((D - gl) / 2), 'o': 'v', 'out': 1, 'side': 'east',
         'parts': [{'len': gl / 2, 'kind': 'fixed', 'hinge': 'l'}, {'len': gl / 2, 'kind': 'tilt', 'hinge': 'r'}]},
    ]
    # mēbeles (KLIENTA PROJEKTS 6: neviena mēbele logam priekšā un nepieskaras tā malām)
    w5 = win[3]
    bed_y = w5['y'] + w5['len'] + 50 - 1400 - 30   # gulta zem augstā loga, naktsgaldiņi ārpus loga zonas
    door_y = doors[1]['y']                         # guļamistabas durvis: gulta beidzas 50 mm pirms vērtnes
    bed_y = max(y0 + 470, min(bed_y, y1 - 1400 - 470, door_y - 50 - 1400))
    k_len = min(1800, din - 1100)
    KITCHEN_GAP = 700                               # dīvāns vismaz 700 mm no virtuves fronta
    sofa_x = lx0 + 600 + KITCHEN_GAP
    sofa_w = min(2400, x1 - 100 - sofa_x)          # ar sānu līdz logam, 100 mm no sienas
    furn = [
        ['bed', x0, r1(bed_y), 2000, 1400, 'w'],
        ['nightstand', x0, r1(bed_y - 450)],
    ] + ([['nightstand', x0, r1(bed_y + 1430)]] if bed_y + 1430 + 420 <= door_y - 50 else []) + [
        ['toilet', r1(wx0 + 400), y0, 1],          # pods: centrs 400 mm no sānu sienas
        ['basin', r1(wx0 + 850), y0, 500, 450, 'n'] if wx0 + 1350 + 50 <= wx1 - 900 else ['basin', r1(wx0 + 1100), r1(wy1 - 450), 500, 450, 's'],
        ['shower', r1(wx1 - 900), y0, 900, ['w', 's']],
        ['washer', r1(wx1 - 600), r1(y0 + 950)],
        ['R', r1(lx0), y0, 600, k_len],
        ['Ln', r1(lx0 + 570), y0, r1(lx0 + 570), r1(y0 + k_len), {'dash': 1}],
        ['R', r1(lx0 + 20), r1(y0 + 20), 560, 560],
        ['Ln', r1(lx0 + 20), r1(y0 + 20), r1(lx0 + 580), r1(y0 + 580), {'sw': 3}],
        ['Ln', r1(lx0 + 580), r1(y0 + 20), r1(lx0 + 20), r1(y0 + 580), {'sw': 3}],
        ['R', r1(lx0 + 90), r1(y0 + 716.5), 420, 560, {'rx': 30}],
        ['Ci', r1(lx0 + 300), r1(y0 + 996.5), 22, {'sw': 3}],
        ['R', r1(lx0 + 40), r1(y0 + 1316.5), 520, 460, {'rx': 15, 'sw': 4}],
    ] + [['Ci', r1(lx0 + cx), r1(y0 + cy), 75, {'sw': 3}] for cx in (170, 430) for cy in (1426.5, 1666.5)] + [
        ['sofa', r1(sofa_x), y0, r1(sofa_w), 900, 'n'],
        ['Ci', r1(sofa_x + 400), r1(y0 + 1500), 400],
    ]
    if din < 2000 + 900:   # naktsgaldiņi neietilpst
        furn = [f for f in furn if f[0] != 'nightstand']
    small_liv = liv < 2700
    if small_liv:          # maza dzīvojamā istaba: bez galda
        furn = [f for f in furn if not (f[0] == 'Ci' and f[3] == 400)]
    if sofa_w < 1200:      # dīvāns neietilpst ar 700 mm no virtuves
        furn = [f for f in furn if f[0] != 'sofa']
    small_wc = wc < 2200
    if small_wc:           # šaurā WC veļasmašīna neietilpst
        furn = [f for f in furn if f[0] != 'washer']
    furn = window_rule(furn, win, x0, x1, y0, y1)
    wc_rule(furn, wx0 + 400, y0)

    # mansards: guļvieta virs guļamistabas, WC un priekšnama; virs dzīvojamās istabas atvērts līdz jumtam
    CEIL1 = int((projekts or {}).get('griesti') or 2200)   # 1. stāva griesti zem mansarda
    lvl = CEIL1 + sum(l[1] for l in CFG['layers'].get('P1', {'layers': [['', 164.5]]})['layers'])
    rx = wx1                                      # margas līnija
    lad = 1000                                    # kāpņu (trepju) atvere virs priekšnama
    loft = {
        'level': round(lvl, 1),
        'rooms': [
            {'n': 'Mansarda guļvieta', 'en': 'Loft', 'r': [[x0, y0, r1(rx - x0), r1(hy0 - y0)], [x0, r1(hy0), r1(rx - lad - x0), HALL_D]]},
            {'n': 'Atvērts uz 1. stāvu', 'en': 'Open to below', 'void': True, 'r': [[r1(rx), y0, r1(x1 - rx), r1(din)], [r1(rx - lad), r1(hy0), lad, HALL_D]]},
        ],
        'doors': [],
        'windows': [
            {'len': 600, 'sill': 2700, 'head': 3100, 'kind': 'tilt', 'x': 0, 'y': r1((D - 600) / 2), 'o': 'v', 'out': -1, 'side': 'west'},
            {'len': gl, 'sill': 2300, 'head': 2900, 'kind': 'fixed', 'x': x1, 'y': r1((D - gl) / 2), 'o': 'v', 'out': 1, 'side': 'east'},
        ],
        'furniture': [
            ['bed', x0, r1(y0 + (hy0 - y0 - 1600) / 2), 2000, 1600, 'w'],
            ['Ln', r1(rx), y0, r1(rx), r1(hy0), {'sw': 30}],
            ['Ln', r1(rx - lad), r1(hy0), r1(rx), r1(hy0), {'sw': 30}],
            ['Ln', r1(rx), y0, x1, y1, {'dash': 1}],
            ['Ln', x1, y0, r1(rx), y1, {'dash': 1}],
            ['R', r1(rx - lad + 250), r1(hy0 + 60), 500, r1(HALL_D - 120)],
        ] + [['Ln', r1(rx - lad + 250), r1(hy0 + 60 + k * 210), r1(rx - lad + 750), r1(hy0 + 60 + k * 210), {'sw': 4}] for k in range(1, 4)],
        'stampAt': {'0': [r1((x0 + rx - lad) / 2), r1((hy0 + y1) / 2)]},
        'stampScale': {'0': .6},
        'levelAt': [r1(x0 + 2400), r1(y0 + 500)],
        'ceilingNote': '',
    }
    gable_wins = [{'side': 'west', 'u0': r1((D - 600) / 2), 'u1': r1((D + 600) / 2), 'z0': 2700},
                  {'side': 'east', 'u0': r1((D - gl) / 2), 'u1': r1((D + gl) / 2), 'z0': 2300}]

    area = W * D / 1e6
    grp = f"{int(round(area / 5.0) * 5)}m2"
    root = os.path.join(MAJAS, grp)
    if not mid:
        n = 1
        while os.path.exists(os.path.join(root, f"MM-{grp[:-2]}-{n:02d}")):
            n += 1
        mid = f"MM-{grp[:-2]}-{n:02d}"
    m = {
        'id': mid, 'nosaukums': mid.replace('MM-', 'MM ', 1), 'platiba_grupa': grp,
        'ievade': {'garums': W, 'platums': D, 'augstums': H},
        'W': W, 'D': D, 'jumts': {'forma': 'divslipju', 'pitch': PITCH, 'ov': 0, 'eave': round(eave)},
        'rooms': rooms, 'doors': doors, 'windows': win, 'furniture': furn,
        'axes': {'x': [[0, '1'], [W, '2']], 'y': [[0, 'A'], [D, 'B']]},
        'stampAt': {'0': [r1(lx0 + liv / 2 + 100), r1(y1 - 700)] if small_liv else [r1(lx0 + liv / 2 + 250), r1(y1 - 650)], '1': [r1(bx0 + 800), r1(y1 - 436.5)],
                    '2': [r1(wx1 - 450), r1(wy1 - 350)] if small_wc else [r1(wx0 + 1150), r1(y0 + 900)], '3': [r1(lx0 - 1023.5), r1(y1 - 456.5)]},
        'stampScale': {'0': .6, '1': .6, '2': .45, '3': .55},
        'levelAt': [r1(wx0 + 571.5), r1(y1 - 456.5)],
        'innerDims': [['x', r1(y0 + 1330)], ['y', r1(bx0 + 1700)], ['y', r1(lx0 + 1100)]], 'wallTags': [], 'sections': [], 'gableWins': gable_wins, 'loft': loft,
        'ceiling': CEIL1, 'ceilingNote': f'Griestu augstums zem mansarda {CEIL1} mm, dzīvojamā istaba atvērta līdz jumtam.', 'planNotes': [],
        'projekts': projekts or {},
        'winOk': [fbox(f) for f in furn if f[0] == 'sofa'],   # dīvāns ar sānu pret logu: pārbaude to atļauj
    }
    d = os.path.join(root, mid)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'model.json')
    json.dump(m, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return p


def next_id(grp):
    root = os.path.join(MAJAS, grp)
    n = 1
    while os.path.exists(os.path.join(root, f"MM-{grp[:-2]}-{n:02d}")):
        n += 1
    return f"MM-{grp[:-2]}-{n:02d}"


def bez_mansarda(p):
    """--mansards ne: noņem mansarda stāvu un tā gala logus no etalona modeļa."""
    m = json.load(open(p, encoding='utf-8'))
    m.pop('loft', None)
    m['gableWins'] = []
    g = m.get('ceiling')
    m['ceilingNote'] = f'Griestu augstums {g} mm.' if g else ''
    json.dump(m, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return p


def auto_telpas(A):
    """[MM] guļamistabu / vannasistabu skaits pēc apbūves laukuma, ja nav norādīts."""
    beds = 1 if A < 45 else 2 if A < 75 else 3
    return beds, (2 if A >= 100 else 1)


def variants(L, B, H, n, mansards, projekts, beds=None, baths=None, formas=('II', 'L', 'T'), mid=None):
    """Plānotāja varianti -> model.json katram (tas pats formāts kā model()), atgriež ceļus."""
    import planner
    A = L * B / 1e6
    b0, v0 = auto_telpas(A)
    griesti = int((projekts or {}).get('griesti') or 2200)
    tries = [beds] if beds else [b for b in (b0, b0 - 1, b0 + 1) if b >= 1]
    vs = rej = None
    for b in tries:
        vs, rej, klase = planner.plan(L, B, H, b, baths or v0, formas, 'only' if mansards else False, n, griesti)
        if vs:
            break
    if not vs:
        raise SystemExit('Plānotājs neatrada nevienu variantu, kas iztur noteikumus:\n  ' + '\n  '.join(rej or []))
    # [MM] V01 = optimālais (arhitekta vērtējums), tālāk alternatīvas pēc vērtējuma
    pick = vs[:n]
    grp = pick[0]['platiba_grupa']
    base = mid or next_id(grp)
    root = os.path.join(MAJAS, grp, base)            # kopsavilkums varianti.html (mape arī rezervē numuru)
    os.makedirs(root, exist_ok=True)
    paths, cards = [], []
    for i, m in enumerate(pick, 1):
        vid = f"{base}-V{i:02d}"
        pm = m['_planner']
        m.update(id=vid, nosaukums=vid.replace('MM-', 'MM ', 1), projekts=dict(projekts or {}))
        m['planNotes'] = m.get('planNotes') or []
        d = os.path.join(MAJAS, grp, vid)            # blakus mapes MM-xx-nn-V01 ... (viz.py atrod pēc id)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, 'model.json')
        json.dump(m, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        paths.append(p)
        rows = ''.join(f"<tr><td>{r['n']}</td><td>{r['m2']}</td></tr>" for r in pm['telpas'])
        links = ' '.join(f'<a href="../{vid}/rasejumi/{vid}_{lg}.html">{lg}</a>' for lg in ('LV', 'EN'))
        cards.append(f"<div class=c><h3>{vid}: {pm['forma']} {pm['tips']}{' + mansards' if pm['mansards'] else ''}</h3>"
                     f"{planner.svg(m)}<table>{rows}<tr><td><b>Apbūve</b></td><td><b>{pm['apbuve_m2']}</b></td></tr></table>"
                     f"<p><b>{'Optimālais' if i == 1 else 'Alternatīva'}.</b> {pm.get('pamatojums', '')}</p>"
                     f"<p>rules_check: 0 kļūdu, 0 brīdinājumu · vērtējums {pm.get('vertejums')} (mazāks = labāks) · rasējumi: {links}</p></div>")
        print(f"{vid} {'OPTIMĀLAIS' if i == 1 else 'alternatīva'}: {pm['forma']} {pm['tips']}. {pm.get('pamatojums', '')}")
    open(os.path.join(root, 'varianti.html'), 'w', encoding='utf-8').write(
        f"<!doctype html><meta charset=utf-8><title>{base} varianti</title><style>body{{font-family:Arial;margin:16px}}"
        f".c{{display:inline-block;vertical-align:top;width:520px;margin:8px;border:1px solid #ccc;padding:8px}}svg{{width:100%}}"
        f"table{{font-size:12px}}</style><h2>{base} · {L:.0f}×{B:.0f}×{H:.0f} · klase {klase}"
        f"{' · ar mansardu' if mansards else ''}</h2>{''.join(cards)}"
        f"<h3>Noraidītie (neizturēja noteikumus)</h3><ul>{''.join(f'<li>{x}</li>' for x in rej)}</ul>")
    if mansards and len(pick) < n:
        print(f'PIEZĪME: ar mansardu atrasti {len(pick)} varianti (mansards pagaidām tikai II formai).')
    return paths


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='MM Homes modeļu bots (KLIENTA PROJEKTS)')
    ap.add_argument('garums', type=float); ap.add_argument('platums', type=float); ap.add_argument('augstums', type=float)
    ap.add_argument('id', nargs='?')
    ap.add_argument('--adrese', help='objekta adrese, rindas atdalītas ar |')
    ap.add_argument('--rev', help='revīzijas nr, piem. 00')
    ap.add_argument('--rev-apraksts', help='revīzijas apraksts')
    ap.add_argument('--raditajs', action='append', default=[], help='papildu rādītājs rakstlaukumā "Nosaukums=Vērtība", var atkārtot')
    ap.add_argument('--nosaukums', help='modeļa nosaukums rakstlaukumā, piem. Freya')
    ap.add_argument('--skp', action='store_true', help='uztaisa SketchUp 3D modeli (3d/<id>.dae + <id>_skp.rb + .obj), skat. skp.py')
    ap.add_argument('--piragi', choices=['ja', 'ne'], default='ne', help='pīrāgu (sienu) biezumi ar mēriem lapā; noklusējums ne (nerādīt)')
    ap.add_argument('--tonis', choices=['peleks', 'koks', 'sarkans', 'zals', 'balts'], help='fasādes tonis (sablons/tex), noklusējums peleks')
    ap.add_argument('--pamati', choices=['stabveida', 'platne'], help='pamatu veids, noklusējums stabveida')
    ap.add_argument('--cokols', choices=['RAL 9005', 'RAL 7016'], help='stabveida pamatu metāla cokola tonis, noklusējums RAL 9005')
    ap.add_argument('--atmosfera', help='vizualizāciju atmosfēra (mm-config.json atmosferas), noklusējums pēc modeļa numura')
    ap.add_argument('--bez-adreses', action='store_true', help='rakstlaukumā bez objekta adreses')
    ap.add_argument('--valodas', default='LV,EN', help='lapas valodas, piem. LV vai LV,EN')
    ap.add_argument('--griesti', type=int, help='1. stāva griestu augstums mm, noklusējums 2200; 0 = nerādīt piezīmēs')
    ap.add_argument('--piezime', action='append', default=[], help='papildu piezīme par projektu rakstlaukumā, var atkārtot')
    ap.add_argument('--viz', action='store_true', help='pēc rasējumiem uzreiz uztaisīt Gemini vizualizācijas (3 toņi)')
    ap.add_argument('--faze', default='klients', choices=['klients', 'razosana'])
    ap.add_argument('--mansards', default='ja', choices=['ja', 'ne'], help='vai mājai ir mansarda stāvs (noklusējums ja)')
    ap.add_argument('--varianti', type=int, default=0, help='N > 0: plānotājs uztaisa N plānojuma variantus, katram sava lapa')
    ap.add_argument('--gulamistabas', type=int, help='variantiem: guļamistabu skaits (noklusējums pēc laukuma)')
    ap.add_argument('--vannas', type=int, help='variantiem: vannasistabu skaits (noklusējums pēc laukuma)')
    ap.add_argument('--forma', default='II,L,T', help='variantiem: formas II, L, T (komatiem)')
    a = ap.parse_args()
    if a.atmosfera and a.atmosfera not in CFG['atmosferas']:
        raise SystemExit('Nezināma atmosfēra: %s. Ir: %s' % (a.atmosfera, ', '.join(CFG['atmosferas'])))
    if a.faze != 'klients':
        raise SystemExit('Ražošanas projekta fāze vēl nav uztaisīta, pagaidām tikai --faze klients.')
    pr = {k: v for k, v in {'faze': a.faze, 'revizija': a.rev, 'rev_apraksts': a.rev_apraksts,
                            'adrese': [] if a.bez_adreses else (a.adrese.split('|') if a.adrese else None),
                            'cokols': a.cokols, 'atmosfera': a.atmosfera,
                            'raditaji': [r.split('=', 1) for r in a.raditajs] or None,
                            'piezimes': a.piezime or None, 'modela_nosaukums': a.nosaukums, 'tonis': a.tonis, 'pamati': a.pamati,
                            'griesti': a.griesti, 'piragi': a.piragi}.items() if v is not None and (v != [] or k == 'adrese')}
    import planlib   # zināšanu bibliotēka: tikai brīdinājumi, noformējumu nemaina
    for x in planlib.check_input(a.garums, a.platums, a.augstums):
        print('BRĪDINĀJUMS:', x)
    # [MM] Mājas (kores) augstums ir no grīdas paneļa APAKŠAS; arhitektūras atzīmes ir no ±0,000 (grīdas pīrāga augšas).
    # Stabveida pamatiem ģeometrijai kore virs ±0,000 = augstums − grīdas pīrāgs (G1); platnei grīdas paneļa nav.
    pam = a.pamati or CFG['projekts'].get('pamati', 'stabveida')
    flT = sum(l[1] for l in CFG['layers']['G1']['layers']) if pam == 'stabveida' else 0
    H0 = math.ceil(a.augstums - flT)   # 4000 - 275,5 = +3,725 (veselā mm)
    if a.varianti > 0:
        ps = variants(a.garums, a.platums, H0, a.varianti, a.mansards == 'ja', pr, a.gulamistabas, a.vannas,
                      tuple(f.strip().upper() for f in a.forma.split(',')), a.id)
    else:
        p = model(a.garums, a.platums, H0, a.id, pr)
        ps = [bez_mansarda(p) if a.mansards == 'ne' else p]
    for p in ps:   # model.json: ievade.augstums = klienta kores augstums (no paneļa apakšas), augstums_0 = kore virs ±0,000
        mj = json.load(open(p, encoding='utf-8'))
        mj['ievade'] = {**mj.get('ievade', {}), 'augstums': a.augstums, 'augstums_0': H0}
        json.dump(mj, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if a.skp:
        from skp import main as skp_main
        for p in ps:
            for o in skp_main(p):
                print(o)
    from ref import main as ref_main   # 3D references bildes Gemini vizualizācijām (visi toņi)
    for p in ps:
        for x in planlib.check_model(p):
            print('BRĪDINĀJUMS:', x)
        print(p)
        for o in build(p, [x.strip().upper() for x in a.valodas.split(',')]):
            print(o)
        if json.load(open(p, encoding='utf-8')).get('poly'):
            print('PIEZĪME: L/T formai 3D references un vizualizācijas vēl netiek taisītas (ref.py zina tikai taisnstūri).')
            continue
        for o in ref_main(p, list(CFG['toni'])):
            print(o)
        if a.viz:
            from viz import run as viz_run
            for o in viz_run(json.load(open(p, encoding='utf-8'))['id']):
                print(o)
    if len(ps) > 1:
        print(os.path.join(os.path.dirname(os.path.dirname(ps[0])), a.id or ps[0].split(os.sep)[-2].rsplit('-V', 1)[0], 'varianti.html'))
