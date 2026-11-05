"""MM istabu plānotājs: no gabarītiem un istabu skaita uztaisa vairākus reālus, atšķirīgus plānojuma variantus
(II, L, T formas, ar vai bez mansarda), katram pilnu model.json (telpas, durvis, logi, mēbeles, mansards).

Noteikumi: zinasanas_mebeles_logi.md, 10. nodaļa [MM]. Katrs variants tiek pārbaudīts ar rules_check.py
un tiek atdots TIKAI tad, ja tam ir 0 kļūdu un 0 brīdinājumu, un ja izpildās plānotāja [MM] noteikumi.
Klases netiek jauktas: telpu izmēri un plānu tipi nāk tikai no tās pašas klases (lidz60 / virs60) bibliotēkas.
generate.py šis fails nelieto un nemaina. Izvade ir model.json formātā, lai generate.py / build_model.py to varētu lietot.

Koordinātas kā generate.py: x = garums (0 = rietumi), y = platums (0 = ziemeļi), ieeja parasti dienvidos (y = D).

    python planner.py 8570 3500 4000 1 1                      # garums platums kore guļamistabas vannasistabas
    python planner.py 11430 3500 4000 1 1 --loft
    python planner.py 9340 6420 5600 2 1 --forma II,L,T --n 3
    python planner.py 13000 7800 6200 3 2 --out mape          # virs60
Izvade: planner_izvade/<garums>x<platums>x<kore>_<g>g<v>v/V01_.../model.json, plans.svg un pārskats index.html.
"""
import argparse, copy, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import planlib        # noqa: E402
import rules_check    # noqa: E402

CFG = json.load(open(os.path.join(HERE, 'sablons', 'mm-config.json'), encoding='utf-8'))
T = sum(l[1] for l in CFG['layers']['S1']['layers'])          # ārsiena 283,5
t = sum(l[1] for l in CFG['layers']['S2']['layers'])          # starpsiena 195
ROOF_T = sum(l[1] for l in CFG['layers']['J1']['layers'])
P1 = sum(l[1] for l in CFG['layers'].get('P1', {'layers': [['', 164.5]]})['layers'])
PITCH = CFG['roof']['pitch']

# ---------------- [MM] plānotāja noteikumi (zinasanas_mebeles_logi.md, 10. nodaļa) ----------------
R = {
    'door_w': 800, 'entry_w': 1000,      # iekšdurvis / ārdurvis
    'door_corner': 75,                   # durvju aila no perpendikulāras sienas
    'door_gap': 50,                      # vērtnes zona + 50 mm bez mēbelēm
    'door_pass': 600,                    # durvju nevēramajā pusē brīva josla
    'entry_land': 1000,                  # pie ārdurvīm iekšā brīvs 1000 x 1000
    'win_edge': 250,                     # logs no starpsienas / stūra
    'win_door': 400,                     # logs no ārdurvīm tajā pašā sienā
    'win_zone': 700, 'win_side': 50,     # loga zona bez mēbelēm
    'bed_side': 600, 'bed_foot': 500,    # gulta: viena garā mala >= 600 brīva, kājgalis >= 500 līdz mēbelei
    'wardrobe_front': 700, 'kitchen_front': 1000, 'sofa_kitchen': 700,
    'table_clear': 700, 'table_wall': 600, 'basin_front': 600, 'washer_front': 600, 'shower_front': 600,
    'toilet_side': 400, 'toilet_gap': 200, 'toilet_front': (800, 600),
    'hall_d': 1200, 'hall_min': 1000, 'corridor': {'lidz60': 1100, 'virs60': 1200},
    'bed_min_side': {'lidz60': 2400, 'virs60': 2700},
    'bath_min_side': 1500,
    'loft_edge_h': 700, 'loft_ridge_min': 1000,
    # [MM] 05.11.2026 /editbot noteikumi
    'bed_wardrobe_min_m2': 9.0,          # guļamistaba < 9 m²: drēbju skapi neliek
    'hall_pass': 900,                    # skapis priekšnamā/gaitenī drīkst atstāt >= 900 mm brīvu caurgājienu, citādi dzēš vai liek dzīvojamā
    'win_fixed_min': 1100,               # logs līdz zemei un platāks par 1100: neverams (fixed)
    'win_split_min': 1000,               # logs ne līdz zemei un platāks par 1000: daļēji vēramais (fiksēts + labā vērtne vēramā/gāžamā)
    'liv_win_fixed': 900,                # dzīvojamās otrais logs pie virtuves virsmas: 900 plats, fixed
    'basin_shower_gap': 600,             # izlietne un duša: starp tām jāvar paiet garām (>= 600) uz telpas stūri
    'loft_win': (1000, 550),             # standarta mansarda logs (gala fasādē): gāžamais (hopper) 1000 x 550
}
NAME = {'liv': ('Dzīvojamā istaba ar virtuvi', 'Living room with kitchen'), 'hall': ('Priekšnams', 'Entrance hall'),
        'corridor': ('Gaitenis', 'Corridor'), 'bath': ('WC', 'WC'), 'bath2': ('Vannasistaba', 'Bathroom'),
        'wc': ('WC', 'WC'), 'tech': ('Tehniskā telpa', 'Utility room'),
        'bed': ('Guļamistaba', 'Bedroom'), 'bed_s': ('Guļamistaba', 'Bedroom')}


def r1(x):
    return round(float(x), 1)


def ov(a, b, m=0.0):
    """Taisnstūri [x0,y0,x1,y1] pārklājas (m = papildu atstarpe)."""
    return min(a[2], b[2]) - max(a[0], b[0]) > -m + 0.5 and min(a[3], b[3]) - max(a[1], b[1]) > -m + 0.5


def inside(b, c, tol=0.5):
    return b[0] >= c[0] - tol and b[1] >= c[1] - tol and b[2] <= c[2] + tol and b[3] <= c[3] + tol


def gapd(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy) if dx and dy else max(dx, dy)


def box(r):
    return [r[0], r[1], r[0] + r[2], r[1] + r[3]]


class Room:
    def __init__(self, kind, rects, name=None, en=None):
        self.kind, self.rects = kind, [[r1(v) for v in r] for r in rects]
        self.name, self.en = (name, en) if name else NAME[kind]
        self.items, self.doors, self.wins = [], [], []

    @property
    def area(self):
        return sum(r[2] * r[3] for r in self.rects) / 1e6

    def boxes(self):
        return [box(r) for r in self.rects]


# ======================================================================================
# 1. TOPOLOĢIJAS (plāna tipi) un rindu risinātājs
# ======================================================================================
# Telpu izmēru robežas pa klasēm: (vēlamā m2, min m2, max m2, min īsā mala mm). Klases NEJAUC.
SIZE = {
    'lidz60': {'bed': (9.5, 7.0, 12.5, 2400), 'bed_s': (7.8, 6.3, 10.5, 2400), 'bath': (3.8, 2.8, 5.8, 1500),
               'hall': (3.0, 1.6, 6.1, 1100), 'cor': (None, 0, 99, 1000), 'liv': (18.0, 9.0, 30.0, 2900)},
    'virs60': {'bed': (13.0, 10.0, 17.0, 2800), 'bed_s': (10.5, 8.0, 13.0, 2700), 'bath': (5.2, 4.0, 7.2, 1700),
               'hall': (5.5, 3.5, 9.0, 1300), 'cor': (None, 0, 99, 1100), 'liv': (30.0, 21.0, 50.0, 3600)},
}
KIND = {'bed': 'bed', 'bed_s': 'bed_s', 'bath': 'bath', 'hall': 'hall', 'cor': 'corridor', 'liv': 'liv'}


class Lay:
    def __init__(self, forma, topo, W, D, klase, poly=None, recess=None):
        self.forma, self.topo, self.W, self.D, self.klase = forma, topo, W, D, klase
        self.poly, self.recess = poly, recess or {}
        self.rooms, self.links, self.entry, self.loft_x, self.notes = [], [], None, None, []

    def add(self, kind, rects, name=None, en=None):
        self.rooms.append(Room(kind, rects, name, en))
        return len(self.rooms) - 1


def name_beds(L):
    beds = [r for r in L.rooms if r.kind in ('bed', 'bed_s')]
    beds.sort(key=lambda r: -r.area)
    for i, r in enumerate(beds):
        r.name, r.en = ('Guļamistaba', 'Bedroom') if i == 0 else (f'Guļamistaba {i + 1}', f'Bedroom {i + 1}')
    baths = [r for r in L.rooms if r.kind == 'bath']
    baths.sort(key=lambda r: -r.area)
    for i, r in enumerate(baths):
        if len(baths) == 1:
            r.name, r.en = NAME['bath'] if L.klase == 'lidz60' else NAME['bath2']
        else:
            r.name, r.en = ('Vannasistaba', 'Bathroom') if i == 0 else ('WC', 'WC')


def parse(it):
    k, _, sid = it.partition('#')
    return k, (it if sid else None)


def wrange(k, depth, klase, part=False):
    goal, amin, amax, side = SIZE[klase][k]
    if part:                       # dzīvojamās daļa (apvieno ar otru rindu): tikai platums
        return (2000, 99999)
    if depth < side - 1 and k not in ('cor', 'hall'):
        return None
    if k == 'hall' and depth < R['hall_min']:
        return None
    lo = max(side, amin * 1e6 / depth)
    hi = amax * 1e6 / depth
    return (lo, hi) if hi >= lo else None


def solve_rows(x0, x1, rows, klase, fixed=None, step=100, top=3):
    """Telpu platumi rindās. rows = [(y0, y1, [item])]; item 'bed', 'bath', ..., 'liv#1' (# = telpa vairākās rindās,
    tai visās rindās jābūt vienādai x pozīcijai). fixed = {item: (xa, xb)} piespiedu kolonna (L/T mezgls).
    Atgriež labākos [(score, {item_key: [x0, x1, y0, y1]})]."""
    fixed = fixed or {}
    span = {}
    for y0, y1, its in rows:
        for it in its:
            k, sid = parse(it)
            if sid:
                a, b = span.get(sid, (y0, y1))
                span[sid] = (min(a, y0), max(b, y1))
    res = []

    def row_rec(ri, known, acc):
        if ri == len(rows):
            res.append(dict(acc))
            return
        y0, y1, its = rows[ri]
        n = len(its)

        def rec(i, x, kn, cur):
            if len(res) > 60000:
                return
            if i == n:
                if abs(x - t - x1) < 1:
                    row_rec(ri + 1, kn, {**acc, **cur})
                return
            it = its[i]
            k, sid = parse(it)
            depth = (span[sid][1] - span[sid][0]) if sid else (y1 - y0)
            key = sid or f'{it}@{ri}.{i}'
            if sid and sid in kn:
                xa, xb = kn[sid]
                if abs(xa - x) > 1:
                    return
                rec(i + 1, xb + t, kn, {**cur, key: [xa, xb, span[sid][0], span[sid][1]]})
                return
            if it in fixed:
                xa, xb = fixed[it]
                if abs(xa - x) > 1:
                    return
                kn2 = {**kn, sid: (xa, xb)} if sid else kn
                rec(i + 1, xb + t, kn2, {**cur, key: [xa, xb, span[sid][0] if sid else y0, span[sid][1] if sid else y1]})
                return
            wr = wrange(k, depth, klase, part=(k == 'liv' and not sid))
            if not wr:
                return
            lo, hi = wr
            nxt = None
            if i < n - 1:
                kj, sj = parse(its[i + 1])
                if sj and sj in kn:
                    nxt = kn[sj][0]
                elif its[i + 1] in fixed:
                    nxt = fixed[its[i + 1]][0]
            if i == n - 1:
                ws = [x1 - x]
            elif nxt is not None:
                ws = [nxt - t - x]
            else:
                rest_min = 0
                for j in its[i + 1:]:
                    kj, sj = parse(j)
                    if sj and sj in kn:
                        rest_min += kn[sj][1] - kn[sj][0]
                    elif j in fixed:
                        rest_min += fixed[j][1] - fixed[j][0]
                    else:
                        dj = (span[sj][1] - span[sj][0]) if sj else (y1 - y0)
                        rest_min += (wrange(kj, dj, klase, part=(kj == 'liv' and not sj)) or (9e9, 0))[0]
                rest_min += t * (n - i - 1)
                hi2 = min(hi, x1 - x - rest_min)
                if hi2 < lo:
                    return
                goal = SIZE[klase][k][0]
                g = goal * 1e6 / depth if goal else lo
                vals = [lo, hi2, g, g * 0.9, g * 1.1, g * 1.2, g * 0.8, (lo + hi2) / 2]
                st = max(step, (hi2 - lo) / 14)
                v = lo
                while v <= hi2:
                    vals.append(v)
                    v += st
                cand = sorted({round(v / 50) * 50 for v in vals if lo - 1 <= round(v / 50) * 50 <= hi2 + 1})
                ws = cand
            for w in ws:
                if w < lo - 1 or w > hi + 1:
                    continue
                kn2 = {**kn, sid: (x, x + w)} if sid else kn
                rec(i + 1, x + w + t, kn2, {**cur, key: [x, x + w, span[sid][0] if sid else y0, span[sid][1] if sid else y1]})

        rec(0, x0, known, {})

    row_rec(0, {}, {})
    scored = []
    for sol in res:
        s = 0.0
        livA = 0
        for key, (a, b, c, d) in sol.items():
            k = parse(key.split('@')[0])[0]
            A = (b - a) * (d - c) / 1e6
            goal, amin, amax, _ = SIZE[klase][k]
            if k == 'liv':
                livA += A
            elif goal:
                s += ((A - goal) / goal) ** 2
        lg = SIZE[klase]['liv']
        s += 2 * (max(0, (lg[0] - livA) / lg[0])) ** 2 + (5 if livA < lg[1] else 0)
        scored.append((s, sol))
    scored.sort(key=lambda q: q[0])
    return scored[:top] if top else scored[:600]


def build(L, sol, open_hall=True):
    """No risinājuma izveido telpas. Vienas rindas 'liv' (bez #) dažādās rindās apvieno vienā telpā."""
    groups = {}
    for key, (a, b, c, d) in sol.items():
        base = key.split('@')[0]
        k, sid = parse(base)
        gid = sid or (('liv', 'merge') if k == 'liv' else key)
        groups.setdefault(gid, (k, []))[1].append([a, c, b - a, d - c])
    idx = {}
    for gid, (k, rects) in groups.items():
        if k == 'liv' and len(rects) > 1:
            rects.sort(key=lambda r: r[1])
            for i in range(len(rects) - 1):                 # aizpilda starpsienas joslu starp daļām
                up, lo_ = rects[i], rects[i + 1]
                if abs(lo_[1] - (up[1] + up[3]) - t) < 2:
                    if min(up[0] + up[2], lo_[0] + lo_[2]) - max(up[0], lo_[0]) < 1500:
                        return None
                    if up[2] <= lo_[2]:
                        up[3] += t
                    else:
                        lo_[1] -= t; lo_[3] += t
        idx[gid] = L.add(KIND[k], rects)
    # atvērta pāreja priekšnams/gaitenis <-> dzīvojamā (bez sienas, kā MM 30/40)
    if open_hall:
        for i, r in enumerate(L.rooms):
            if r.kind not in ('hall', 'corridor'):
                continue
            for j, q in enumerate(L.rooms):
                if q.kind not in ('liv',) + (('hall',) if r.kind == 'corridor' else ()):
                    continue
                sw = shared_wall(r, q)
                if not sw or sw[3] - sw[2] < 900:
                    continue
                o, p, lo, hi, s = sw
                rr = r.rects[0]
                if o == 'v' and abs(rr[1] - lo) < 1 and abs(rr[1] + rr[3] - hi) < 1:
                    if s == -1: rr[2] += t
                    else: rr[0] -= t; rr[2] += t
                    break
                if o == 'h' and abs(rr[0] - lo) < 1 and abs(rr[0] + rr[2] - hi) < 1:
                    if s == -1: rr[3] += t
                    else: rr[1] -= t; rr[3] += t
                    break
    return idx


def touches(a, b):
    """Telpas a un b saskaras bez sienas (atvērta pāreja)."""
    for ra in a.boxes():
        for rb in b.boxes():
            if (abs(ra[2] - rb[0]) < 1 or abs(rb[2] - ra[0]) < 1) and min(ra[3], rb[3]) - max(ra[1], rb[1]) > 800:
                return True
            if (abs(ra[3] - rb[1]) < 1 or abs(rb[3] - ra[1]) < 1) and min(ra[2], rb[2]) - max(ra[0], rb[0]) > 800:
                return True
    return False


def auto_links(L):
    """Durvju saites: privātā telpa -> priekšnams/gaitenis (vēlams) vai dzīvojamā. False, ja kāda telpa nav sasniedzama."""
    L.links = []
    hubs = [i for i, r in enumerate(L.rooms) if r.kind in ('hall', 'corridor', 'liv')]
    for i, r in enumerate(L.rooms):
        if r.kind in ('bed', 'bed_s', 'bath'):
            cand = []
            for h in hubs:
                sw = shared_wall(r, L.rooms[h])
                if sw and sw[3] - sw[2] >= R['door_w'] + 2 * R['door_corner']:
                    cand.append((0 if L.rooms[h].kind != 'liv' else 1, -(sw[3] - sw[2]), h))
            if not cand:
                return False
            cand.sort()
            L.links.append((i, [c[2] for c in cand]))
    # hubi savā starpā sasniedzami (atvērti vai ar durvīm)
    for i in hubs:
        r = L.rooms[i]
        if r.kind == 'liv':
            continue
        if not any(touches(r, L.rooms[j]) for j in hubs if j != i):
            sw = [(j, shared_wall(r, L.rooms[j])) for j in hubs if j != i]
            sw = [(j, s) for j, s in sw if s and s[3] - s[2] >= R['door_w'] + 150]
            if not sw:
                return False
            L.links.append((sw[0][0], [i]) if L.rooms[sw[0][0]].kind == 'liv' else (i, [sw[0][0]]))
    return True


def ext_ok(L):
    """Katrai dzīvojamai, guļamistabai un sanmezglam ir ārsiena uz ierobežojošā taisnstūra; sanmezglam horizontāla (logs virs poda)."""
    for r in L.rooms:
        sides = [s for q in r.rects for s in ext_sides(L, q)]
        if r.kind in ('liv', 'bed', 'bed_s') and not sides:
            return False
        if r.kind == 'bath' and not any(s[0] in ('north', 'south') and s[2] - s[1] >= 600 + 2 * R['win_edge'] for s in sides):
            return False
        if r.kind == 'liv' and len({s[0] for s in sides}) < 2:
            return False
    return True


def finish(L, entry_kinds=('hall', 'liv')):
    if not ext_ok(L) or not auto_links(L):
        return None
    for k in entry_kinds:
        c = [i for i, r in enumerate(L.rooms) if r.kind == k and entry_options(L, r)]
        if c:
            L.entry = c[0]
            return L
    return None


def templates_II(din, beds, baths, klase):
    """Plānu veidnes II formai pēc iekšējā dziļuma. Katra: (nosaukums, rindas [(daļa, [telpas])], mansarda bloks)."""
    B = ['bed'] + ['bed_s'] * max(beds - 1, 0)
    wet = ['bath'] * max(baths, 1)
    T_ = []
    if din < 4400:                                   # vienmoduļa: telpas rindā, sanmezgls virs priekšnama
        if beds == 0:
            T_ += [('studija ar priekšnamu', [['bath', 'liv#L'], ['hall', 'liv#L']], True),
                   ('studija, sanmezgls galā', [['liv#L', 'bath#W']], False)]
        if beds == 1:
            T_ += [('guļamistaba galā, sanmezgls vidū', [['bed#B', 'bath', 'liv#L'], ['bed#B', 'hall', 'liv#L']], True),
                   ('sanmezgls galā', [['bed#B', 'liv#L', 'bath#W']], False),
                   ('guļamistaba galā, priekšnams pie dzīvojamās', [['bed#B', 'hall', 'liv#L'], ['bed#B', 'bath', 'liv#L']], True)]
        if beds == 2:
            T_ += [('guļamistabas abos galos', [['bed#B', 'bath', 'liv#L', 'bed_s#C'], ['bed#B', 'hall', 'liv#L', 'bed_s#C']], False),
                   ('guļamistabas abos galos, sanmezgls pie otrās', [['bed#B', 'liv#L', 'bath', 'bed_s#C'], ['bed#B', 'liv#L', 'hall', 'bed_s#C']], False),
                   ('guļamistabas blakus', [['bed#B', 'bath', 'bed_s#C', 'liv#L'], ['bed#B', 'hall', 'bed_s#C', 'liv#L']], True)]
        return [(n, rows, lf, 'lin') for n, rows, lf in T_]
    if din <= 6600:                                  # divas joslas
        if beds == 1:
            T_ += [('privātais bloks galā', [['bed', 'liv#L'], wet + ['hall', 'liv#L']], True),
                   ('privātais bloks galā, guļamistaba dienvidos', [wet + ['liv#L'], ['bed', 'hall', 'liv#L']], True),
                   ('josla', [['bed'] + wet + ['liv'], ['hall', 'liv']], False)]
        if beds == 2:
            T_ += [('privātais bloks galā', [['bed', 'bed_s', 'liv#L'], wet + ['hall', 'liv#L']], True),
                   ('privātais bloks galā, istabas pāri', [['bed', 'bath', 'liv#L'], ['bed_s', 'hall', 'liv#L']], True),
                   ('privātais bloks galā, gaitenis pie dzīvojamās', [['bed', 'bed_s', 'liv#L'], wet + ['cor', 'liv#L']], True),
                   ('josla', [['bed', 'bed_s'] + wet + ['liv'], ['hall', 'liv']], False),
                   ('dalītais', [['bed', 'liv#L', 'bed_s'], wet + ['liv#L', 'hall']], False),
                   ('dalītais, sanmezgls ziemeļos', [['bed', 'liv#L'] + wet, ['bed_s', 'liv#L', 'hall']], False)]
        if beds == 3:
            T_ += [('josla', [['bed', 'bed_s', 'bed_s'] + wet[:1] + ['liv'], ['hall', 'liv']], False),
                   ('dalītais', [['bed', 'liv#L', 'bed_s', 'bed_s'], wet[:1] + ['liv#L', 'hall'] + wet[1:]], False)]
        return [(n, rows, lf, 'dbl') for n, rows, lf in T_]
    # ar gaiteni
    if beds >= 1:
        n1 = B[:2] if beds >= 2 else B[:1]
        rest = B[2:] if beds >= 2 else []
        T_ += [('gaitenis, guļamistabas ziemeļos', [n1 + ['liv#L'], ['cor', 'liv#L'], rest + wet + ['hall', 'liv#L']], False),
               ('gaitenis, sanmezgli ziemeļos', [[B[0]] + wet + ['liv#L'], ['cor', 'liv#L'], B[1:] + ['hall', 'liv#L']], False)]
        if beds >= 2:
            T_.append(('gaitenis, vecāku istaba ar sanmezglu', [[B[0], wet[0]] + B[1:2] + ['liv#L'], ['cor', 'liv#L'], B[2:] + wet[1:] + ['hall', 'liv#L']], False))
    return [(n, rows, lf, 'cor') for n, rows, lf in T_]


def topo_II(W, D, beds, baths, klase):
    X0, X1, Y0, Y1 = T, W - T, T, D - T
    din = Y1 - Y0
    out = []
    for name, rows_k, lf, typ in templates_II(din, beds, baths, klase):
        group = []
        splits = []
        if typ == 'lin':
            hd = min(R['hall_d'], max(R['hall_min'], din - 1700 - t))
            if len(rows_k) == 1:
                splits = [[din]]
            else:
                hall_row = 1 if 'hall' in rows_k[1] else 0
                splits = [[din - hd - t, hd]] if hall_row == 1 else [[hd, din - hd - t]]
        elif typ == 'dbl':
            for dn in (3000, 3300, 3600):
                if din - dn - t >= 1700:
                    splits.append([dn, din - dn - t])
        else:
            c = R['corridor'][klase]
            dn = (din - c - 2 * t) / 2
            splits = [[dn, c, din - dn - c - 2 * t]]
        seen = set()
        for sp in splits:
            rows, y = [], Y0
            for h, its in zip(sp, rows_k):
                rows.append((y, y + h, its))
                y += h + t
            for score, sol in solve_rows(X0, X1, rows, klase, top=0):
                L = Lay('II', name, W, D, klase)
                if build(L, sol) is None:
                    continue
                sig = tuple(sorted((r.kind, round(r.rects[0][0] / 300), round(r.rects[0][1] / 300)) for r in L.rooms))
                if sig in seen:
                    continue
                seen.add(sig)
                if True:   # [MM] mansards iespējams, ja dzīvojamā aizņem visu austrumu galu (visu dziļumu)
                    liv = next(r for r in L.rooms if r.kind == 'liv')
                    rs = liv.rects
                    lx = max(r[0] for r in rs)
                    deep = max(r[1] + r[3] for r in rs) - min(r[1] for r in rs)
                    xe = min(r[0] + r[2] for r in rs)
                    full = all(abs(r[0] + r[2] - xe) < 1 for r in rs) and abs(deep - din) < 2 and xe - lx >= 2400   # atvērtais >= 2.4 m
                    opts = []
                    if full and lx > X0 + 2500:          # mansards virs rietumu bloka
                        opts.append(('w', X0, lx - t, xe))
                    if full and X1 - xe > 2500:          # mansards virs austrumu bloka (spoguļattēlā rietumu)
                        opts.append(('e', T, W - xe - t, W - lx))
                    L.loft_x = opts or None
                if finish(L):
                    group.append(L)
                    if len(group) >= 8:
                        break
            if len(group) >= 8:
                break
        out.append((name, group))
    return out


def wing_width(B, klase):
    if klase == 'lidz60':
        return B if B <= 4600 else 4000
    return min(max(0.62 * B, 4500), 6400)


def topo_L(A, B, beds, baths, klase):
    """L: ziemeļu spārns (garums Wb, platums w) + kāja rietumos (līdz Db). Apbūve = A (kā II).
    Mezgls (stūris): sanmezgls ziemeļos virs priekšnama; kāja: viena telpa ar logiem rietumos un galā."""
    w = wing_width(B, klase)
    win = w - 2 * T
    out = []
    if beds < 1 or beds > 3 or baths > 1:
        return out
    hd = min(R['hall_d'], max(R['hall_min'], win - 1700 - t))
    progs = []
    if beds == 1:
        progs += [('L, guļamistaba kājā', 'bed', [['J#bath', 'liv#L'], ['J#hall', 'liv#L']]),
                  ('L, dzīvojamā kājā', 'liv', [['J#bath', 'bed#B'], ['J#hall', 'bed#B']])]
    if beds == 2:
        progs += [('L, guļamistaba kājā', 'bed_s', [['J#bath', 'bed#B', 'liv#L'], ['J#hall', 'bed#B', 'liv#L']]),
                  ('L, dzīvojamā kājā', 'liv', [['J#bath', 'bed#B', 'bed_s#C'], ['J#hall', 'hall', 'bed_s#C']])]
    if beds == 3:
        progs += [('L, guļamistaba kājā', 'bed_s', [['J#bath', 'bed#B', 'bed_s#C', 'liv#L'], ['J#hall', 'bed#B', 'bed_s#C', 'liv#L']])]
    for pname, legk, rows_k in progs:
        g = SIZE[klase][legk]
        group = []
        out.append((pname, group))
        lo_ = max(g[3], g[1] * 1e6 / win)
        hi_ = (g[2] * 1e6 / win) if legk != 'liv' else (g[2] * 0.8e6 / win)
        leg = lo_
        while leg <= hi_ + 1 and len(group) < 8:
            Db = round((w - T + t + leg + T) / 10) * 10
            Wb = round((A * 1e6 / w - Db + w) / 10) * 10
            leg += 300
            if Wb < w + 3000:
                continue
            poly = [[0, 0], [Wb, 0], [Wb, w], [w, w], [w, Db], [0, Db]]
            rec = {'south': [[w, Wb, Db - w]], 'east': [[w, Db, Wb - w]]}
            Y0, Y1 = T, w - T
            rows = [(Y0, Y1 - hd - t, [x.replace('J#', '') for x in rows_k[0]]), (Y1 - hd, Y1, [x.replace('J#', '') for x in rows_k[1]])]
            fixed = {'bath': (T, T + win), 'hall': (T, T + win)}
            n_ok = 0
            for score, sol in solve_rows(T, Wb - T, rows, klase, fixed=fixed, top=0)[:200]:
                L = Lay('L', pname, Wb, Db, klase, poly, rec)
                if build(L, sol, open_hall=True) is None:
                    continue
                L.add(legk, [[T, w - T + t, win, Db - T - (w - T + t)]])
                if finish(L, ('hall', 'liv')):
                    group.append(L)
                    n_ok += 1
                    if n_ok >= 2:
                        break
    return out


def topo_T(A, B, beds, baths, klase):
    """T: šķērsspārns ziemeļos (Wt x w), kāts dienvidos (platums w, var būt nobīdīts no centra). Apbūve = A."""
    w = wing_width(B, klase)
    win = w - 2 * T
    out = []
    if beds < 1 or beds > 3:
        return out
    hd = min(R['hall_d'], max(R['hall_min'], win - 1700 - t))
    progs = []
    if beds == 1:
        progs.append(('T, dzīvojamā kātā', 'liv', [['bed#B', 'J#liv#L', 'bath'], ['bed#B', 'J#liv#L', 'hall']]))
    if beds == 2:
        progs.append(('T, dzīvojamā kātā', 'liv', [['bed#B', 'bath', 'J#liv#L', 'bed_s#C'], ['bed#B', 'hall', 'J#liv#L', 'bed_s#C']]))
        progs.append(('T, guļamistaba kātā', 'bed_s', [['liv#L', 'J#bath', 'bed#B'], ['liv#L', 'J#hall', 'bed#B']]))
    if beds == 3:
        progs.append(('T, dzīvojamā kātā', 'liv', [['bed#B', 'bath', 'J#liv#L', 'bed_s#C', 'bed_s#D'], ['bed#B', 'hall', 'J#liv#L', 'bed_s#C', 'bed_s#D']]))
        progs.append(('T, guļamistaba kātā', 'bed_s', [['liv#L', 'J#bath', 'bed#B', 'bed_s#C'], ['liv#L', 'J#hall', 'hall', 'bed_s#C']]))
    for pname, stemk, rows_k in progs:
        g = SIZE[klase][stemk]
        group = []
        out.append((pname, group))
        lo_ = max(g[3] + 200, (g[1] * 0.5 if stemk == 'liv' else g[1]) * 1e6 / win)
        hi_ = (g[2] * 0.6 if stemk == 'liv' else g[2]) * 1e6 / win
        stem = lo_
        while stem <= hi_ + 1 and len(group) < 8:
            Dt = round((w + stem + T) / 10) * 10
            stem += 400
            Wt = round(((A * 1e6) - (Dt - w) * w) / w / 10) * 10
            if Wt < w + 2 * 2600:
                continue
            c0 = (Wt - w) / 2
            for off in (0, -600, 600, -1200, 1200, -1800, 1800):
                s0 = round((c0 + off) / 10) * 10
                if s0 < 2600 or Wt - s0 - w < 2600:
                    continue
                s1 = s0 + w
                poly = [[0, 0], [Wt, 0], [Wt, w], [s1, w], [s1, Dt], [s0, Dt], [s0, w], [0, w]]
                rec = {'south': [[0, s0, Dt - w], [s1, Wt, Dt - w]], 'east': [[w, Dt, Wt - s1]], 'west': [[w, Dt, s0]]}
                jx = (s0 + T, s1 - T)
                Y0, Y1 = T, w - T
                rows = [(Y0, Y1 - hd - t, [x.replace('J#', '') for x in rows_k[0]]), (Y1 - hd, Y1, [x.replace('J#', '') for x in rows_k[1]])]
                fixed = {x[2:]: jx for rk in rows_k for x in rk if x.startswith('J#')}
                for score, sol in solve_rows(T, Wt - T, rows, klase, fixed=fixed, top=0)[:200]:
                    L = Lay('T', pname, Wt, Dt, klase, poly, rec)
                    if build(L, sol) is None:
                        continue
                    if stemk == 'liv':
                        liv = next(r for r in L.rooms if r.kind == 'liv' and abs(r.rects[0][0] - jx[0]) < 1)
                        liv.rects[0][3] = (Dt - T) - liv.rects[0][1]          # dzīvojamā turpinās kātā
                    else:
                        L.add(stemk, [[jx[0], w - T + t, win, Dt - T - (w - T + t)]])
                    if finish(L, ('hall', 'liv')):
                        group.append(L)
                        break
                if len(group) >= 8:
                    break
    return out


# ======================================================================================
# 2. DURVIS
# ======================================================================================
def shared_wall(a, b):
    """Kopējā starpsiena starp telpu a un b taisnstūriem: (o, coord, lo, hi, a_side) ; a_side = -1 ja a ir pa kreisi/augšā."""
    best = None
    for ra in a.rects:
        for rb in b.rects:
            ax0, ay0, ax1, ay1 = box(ra)
            bx0, by0, bx1, by1 = box(rb)
            for (p, q, s) in ((ax1, bx0, -1), (bx1, ax0, 1)):
                if abs(q - p - t) < 2:
                    lo, hi = max(ay0, by0), min(ay1, by1)
                    if hi - lo > 0 and (not best or hi - lo > best[3] - best[2]):
                        best = ('v', p, lo, hi, s)
            for (p, q, s) in ((ay1, by0, -1), (by1, ay0, 1)):
                if abs(q - p - t) < 2:
                    lo, hi = max(ax0, bx0), min(ax1, bx1)
                    if hi - lo > 0 and (not best or hi - lo > best[3] - best[2]):
                        best = ('h', p, lo, hi, s)
    return best


def door_options(a, b, w):
    """Durvju varianti starp a (privāta, vērtne uz a pusi) un b. Atgriež door dict sarakstu."""
    sw = shared_wall(a, b)
    if not sw:
        return []
    o, p, lo, hi, s = sw
    c = R['door_corner']
    if hi - lo < w + 2 * c:
        return []
    side = -1 if s == -1 else 1        # a ir kreisajā/augšējā pusē: vērtne uz -; citādi uz +
    pos = [lo + c, hi - c - w, (lo + hi - w) / 2]
    out = []
    for i, d0 in enumerate(pos):
        hinge = 's' if i != 1 else 'e'
        if i == 2:
            hinge = 's'
        d = {'x': r1(p), 'y': r1(d0), 'o': 'v', 'hinge': hinge, 'side': side, 'w': w, 'th': t} if o == 'v' else \
            {'x': r1(d0), 'y': r1(p), 'o': 'h', 'hinge': hinge, 'side': side, 'w': w, 'th': t}
        out.append(d)
    return out


def swing_zone(d):
    """Vērtnes kvadrāts telpā [x0,y0,x1,y1] (precīzi pēc cad.js)."""
    x, y, w, th, s = d['x'], d['y'], d['w'], d['th'], d['side']
    if d['o'] == 'h':
        return [x, y + th, x + w, y + th + w] if s > 0 else [x, y - w, x + w, y]
    return [x + th, y, x + th + w, y + w] if s > 0 else [x - w, y, x, y + w]


def pass_zone(d, depth):
    """Brīvā josla durvju otrā pusē (kur vērtne neveras)."""
    x, y, w, th, s = d['x'], d['y'], d['w'], d['th'], d['side']
    if d['o'] == 'h':
        return [x, y - depth, x + w, y] if s > 0 else [x, y + th, x + w, y + th + depth]
    return [x - depth, y, x, y + w] if s > 0 else [x + th, y, x + th + depth, y + w]


def ext_sides(L, r):
    """Taisnstūra r malas, kas ir ārsienā uz ierobežojošā taisnstūra (tikai tur var likt logus): [(side, lo, hi)]."""
    x0, y0, x1, y1 = box(r)
    out = []
    if abs(y0 - T) < 1: out.append(('north', x0, x1))
    if abs(y1 - (L.D - T)) < 1: out.append(('south', x0, x1))
    if abs(x0 - T) < 1: out.append(('west', y0, y1))
    if abs(x1 - (L.W - T)) < 1: out.append(('east', y0, y1))
    return out


def all_ext_sides(L, r):
    """Arī iekšējās fasādes (L/T iekšējais stūris): lieto tikai ārdurvīm."""
    out = ext_sides(L, r)
    if not L.poly:
        return out
    x0, y0, x1, y1 = box(r)
    P = L.poly
    for i in range(len(P)):
        (ax, ay), (bx, by) = P[i], P[(i + 1) % len(P)]
        if ay == by and 0 < ay < L.D:            # horizontāla iekšējā mala
            lo, hi = max(min(ax, bx), x0), min(max(ax, bx), x1)
            if hi - lo > 0 and abs(y1 - (ay - T)) < 1:
                out.append(('south_in', lo, hi, ay))
            if hi - lo > 0 and abs(y0 - (ay + T)) < 1:
                out.append(('north_in', lo, hi, ay))
        if ax == bx and 0 < ax < L.W:
            lo, hi = max(min(ay, by), y0), min(max(ay, by), y1)
            if hi - lo > 0 and abs(x1 - (ax - T)) < 1:
                out.append(('east_in', lo, hi, ax))
            if hi - lo > 0 and abs(x0 - (ax + T)) < 1:
                out.append(('west_in', lo, hi, ax))
    return out


def entry_options(L, room):
    w = R['entry_w']
    out = []
    pref = {'south': 0, 'south_in': 1}      # [MM] ieeja VIENMĒR no dienvidiem
    for r in room.rects:
        for e in sorted([e for e in all_ext_sides(L, r) if e[0] in pref], key=lambda e: pref[e[0]]):
            sd, lo, hi = e[0], e[1], e[2]
            if hi - lo < w + 2 * 300:
                continue
            for d0 in ((lo + hi - w) / 2, lo + 300, hi - 300 - w):
                if sd in ('south', 'north', 'south_in', 'north_in'):
                    y = L.D - T if sd == 'south' else 0 if sd == 'north' else (e[3] - T if sd == 'south_in' else e[3])
                    side = 1 if sd.startswith('south') else -1
                    out.append({'x': r1(d0), 'y': r1(y), 'o': 'h', 'hinge': 's', 'side': side, 'w': w, 'th': T, 'entry': True, '_sd': sd})
                else:
                    x = L.W - T if sd == 'east' else 0 if sd == 'west' else (e[3] - T if sd == 'east_in' else e[3])
                    side = 1 if sd.startswith('east') else -1
                    out.append({'x': r1(x), 'y': r1(d0), 'o': 'v', 'hinge': 's', 'side': side, 'w': w, 'th': T, 'entry': True, '_sd': sd})
    return out


def entry_land(d):
    w, L_ = d['w'], R['entry_land']
    x, y = d['x'], d['y']
    sd = d['_sd']
    if d['o'] == 'h':
        return [x, y - L_, x + w, y] if sd.startswith('south') else [x, y + T, x + w, y + T + L_]
    return [x - L_, y, x, y + w] if sd.startswith('east') else [x + T, y, x + T + L_, y + w]


# ======================================================================================
# 3. LOGI
# ======================================================================================
def win_zone(w, L):
    z, g = R['win_zone'], R['win_side']
    if w['o'] == 'h':
        return [w['x'] - g, T, w['x'] + w['len'] + g, T + z] if w['y'] == 0 else [w['x'] - g, L.D - T - z, w['x'] + w['len'] + g, L.D - T]
    return [T, w['y'] - g, T + z, w['y'] + w['len'] + g] if w['x'] == 0 else [L.W - T - z, w['y'] - g, L.W - T, w['y'] + w['len'] + g]


def make_win(L, side, a0, ln, sill, head, kind, **kw):
    if side == 'north':
        w = {'len': ln, 'sill': sill, 'head': head, 'kind': kind, 'x': r1(a0), 'y': 0, 'o': 'h', 'side': 'north'}
    elif side == 'south':
        w = {'len': ln, 'sill': sill, 'head': head, 'kind': kind, 'x': r1(a0), 'y': r1(L.D - T), 'o': 'h', 'side': 'south'}
    elif side == 'west':
        w = {'len': ln, 'sill': sill, 'head': head, 'kind': kind, 'x': 0, 'y': r1(a0), 'o': 'v', 'out': -1, 'side': 'west'}
    else:
        w = {'len': ln, 'sill': sill, 'head': head, 'kind': kind, 'x': r1(L.W - T), 'y': r1(a0), 'o': 'v', 'out': 1, 'side': 'east'}
    w.update(kw)
    return w


def std_win(L, side, a0, ln, sill, head, **kw):
    """[MM] standarta logu veidi: līdz zemei un > 1100: fixed; ne līdz zemei un > 1000: fiksēts + labā vērtne (vēramā/gāžamā); citādi vēramais/gāžamais."""
    if sill == 0 and ln > R['win_fixed_min']:
        return make_win(L, side, a0, ln, sill, head, 'fixed', **kw)
    if sill > 0 and ln > R['win_split_min']:
        return make_win(L, side, a0, ln, sill, head, 'parts', tilt=True,
                        parts=[{'len': ln / 2, 'kind': 'fixed', 'hinge': 'l'}, {'len': ln / 2, 'kind': 'tilt', 'hinge': 'r'}], **kw)
    return make_win(L, side, a0, ln, sill, head, 'tilt', **kw)


def win_span(w):
    return (w['x'], w['x'] + w['len']) if w['o'] == 'h' else (w['y'], w['y'] + w['len'])


def is_gable(L, side):
    """Gala (īsā) fasāde: II mājai rietumi/austrumi; L/T: arī kājas/kāta gals."""
    if L.forma == 'II':
        return side in ('west', 'east')
    return True


def win_sets(L, room, entry):
    """Logu komplektu varianti telpai (sarakstā labākie vispirms)."""
    k = room.kind
    sides = [(s, lo, hi, ri) for ri, r in enumerate(room.rects) for (s, lo, hi) in ext_sides(L, r)]
    E = R['win_edge']
    area = room.area

    def fits(side, a0, ln, lo, hi):
        if a0 < lo + E - 0.5 or a0 + ln > hi - E + 0.5:
            return False
        if entry and side == 'south' and entry['o'] == 'h':     # rules_check salīdzina visas 'h' ārdurvis ar dienvidu logiem
            if not (a0 >= entry['x'] + entry['w'] + R['win_door'] or a0 + ln <= entry['x'] - R['win_door']):
                return False
        if entry and side in ('north',) and entry['o'] == 'h' and entry['y'] == 0:
            if not (a0 >= entry['x'] + entry['w'] + R['win_door'] or a0 + ln <= entry['x'] - R['win_door']):
                return False
        if entry and side in ('west', 'east') and entry['o'] == 'v' and ((side == 'west') == (entry['x'] == 0)) and entry['_sd'] == side:
            if not (a0 >= entry['y'] + entry['w'] + R['win_door'] or a0 + ln <= entry['y'] - R['win_door']):
                return False
        return True

    def place(side, lo, hi, ln, where):
        free = []
        if where == 'c':
            free = [(lo + hi - ln) / 2]
        elif where == 'lo':
            free = [lo + E + 50]
        elif where == 'kit':
            free = [lo + 600 + 100]          # [MM] 100 mm no virtuves darba virsmas (600 dziļa gar galasienu)
        elif where == 'hi':
            free = [hi - E - 50 - ln]
        else:
            free = [lo + (hi - lo) * where - ln / 2]
        out = []
        for a in free:
            for sh in (0, 300, -300, 600, -600, 900, -900, 1200, -1200):
                if fits(side, a + sh, ln, lo, hi):
                    out.append(round(a + sh))
                    break
        return out

    res = []
    if k == 'liv':
        need = area / 8 * 1e6
        # [MM] lielais stiklojums pēc mājas formas: šaura II -> gala fasāde; plata II -> garā fasāde; L/T -> spārna gals
        din_ = L.D - 2 * T

        def wing_end(q):
            r = room.rects[q[3]]
            return (r[2] <= r[3]) if q[0] in ('north', 'south') else (r[3] <= r[2])
        if L.forma == 'II' and din_ < 4400:
            key = lambda q: (0 if is_gable(L, q[0]) else 1, 0 if q[0] == 'south' else 1, -(q[2] - q[1]))
        elif L.forma == 'II':
            key = lambda q: (0 if q[0] in ('north', 'south') else 1, -(q[2] - q[1]), 0 if q[0] == 'south' else 1)
        else:
            key = lambda q: (0 if wing_end(q) else 1, -(q[2] - q[1]))
        prim = sorted(sides, key=key)
        combos = []
        for g in prim:
            sec = [x for x in sides if x[0] != g[0]]
            for o in sec:
                combos.append((g, o))
            if not sec:
                combos.append((g, None))
        for g, o in combos:
            s, lo, hi, _ = g
            gl = min(2400, (hi - lo) - 2 * (E + 150))
            gl = math.floor(gl / 100) * 100
            if gl < 1200:
                continue
            for a in place(s, lo, hi, gl, 'c'):
                W1 = std_win(L, s, a, gl, 0, 2100)
                got = gl * 2100
                if o:
                    s2, lo2, hi2, _ = o
                    for ln in (R['liv_win_fixed'], 1500, 1200):
                        for where in (('kit', 'lo', 0.3, 'c', 0.7, 'hi') if ln == R['liv_win_fixed'] else ('c', 0.7, 0.3, 'hi', 'lo')):
                            for a2 in place(s2, lo2, hi2, ln, where):
                                w2 = make_win(L, s2, a2, ln, 0, 2100, 'fixed') if ln == R['liv_win_fixed'] else std_win(L, s2, a2, ln, 900, 2100)
                                res.append([W1, w2])
                elif got >= need:
                    res.append([W1])
    elif k in ('bed', 'bed_s'):
        ln = max(900, min(1800, math.ceil(area / 8 * 1e6 / 1200 / 100) * 100))
        pref = sorted(sides, key=lambda s: (0 if not is_gable(L, s[0]) else 1, -(s[2] - s[1])))
        for s, lo, hi, _ in pref:
            for where in ('c', 'lo', 'hi', 0.35, 0.65):
                for a in place(s, lo, hi, ln, where):
                    res.append([std_win(L, s, a, ln, 900, 2100)])
    elif k == 'bath':
        for s, lo, hi, _ in sorted(sides, key=lambda s: 0 if s[0] in ('north', 'south') else 1):
            for where in ('c', 'lo', 'hi', 0.3, 0.7):
                for a in place(s, lo, hi, 600, where):
                    if s in ('north', 'south'):
                        res.append([make_win(L, s, a, 600, 900, 2100, 'tilt')])
                    else:
                        res.append([make_win(L, s, a, 600, 1600, 2100, 'hopper')])
    else:
        res.append([])
    # unikāli
    seen, out = set(), []
    for ws in res:
        key = tuple((w['side'], w['x'], w['y'], w['len']) for w in ws)
        if key not in seen:
            seen.add(key)
            out.append(ws)
    return out


# ======================================================================================
# 4. MĒBELES
# ======================================================================================
class Item:
    def __init__(self, kind, bx, cmds, free=(), exempt=False):
        self.kind, self.box, self.cmds, self.free, self.exempt = kind, [r1(v) for v in bx], cmds, list(free), exempt


def kitchen_items(x, y, ln, wall):
    """Virtuves rinda 600 mm gar sienu wall ('w','e','n','s'), sākot (x,y) = rindas stūris."""
    c = []
    if wall in ('w', 'e'):
        bx = [x, y, x + 600, y + ln]
        lx = x + 570 if wall == 'w' else x + 30
        c.append(['R', r1(x), r1(y), 600, r1(ln)])
        c.append(['Ln', r1(lx), r1(y), r1(lx), r1(y + ln), {'dash': 1}])
        c += [['R', r1(x + 20), r1(y + 20), 560, 560], ['Ln', r1(x + 20), r1(y + 20), r1(x + 580), r1(y + 580), {'sw': 3}],
              ['Ln', r1(x + 580), r1(y + 20), r1(x + 20), r1(y + 580), {'sw': 3}]]
        c += [['R', r1(x + 90), r1(y + 716.5), 420, 560, {'rx': 30}], ['Ci', r1(x + (300 if wall == 'w' else 300)), r1(y + 996.5), 22, {'sw': 3}]]
        if ln >= 1800:
            c.append(['R', r1(x + 40), r1(y + 1316.5), 520, 460, {'rx': 15, 'sw': 4}])
            c += [['Ci', r1(x + cx), r1(y + cy), 75, {'sw': 3}] for cx in (170, 430) for cy in (1426.5, 1666.5)]
        front = [x + 600, y, x + 600 + R['kitchen_front'], y + ln] if wall == 'w' else [x - R['kitchen_front'], y, x, y + ln]
    else:
        bx = [x, y, x + ln, y + 600]
        ly = y + 570 if wall == 'n' else y + 30
        c.append(['R', r1(x), r1(y), r1(ln), 600])
        c.append(['Ln', r1(x), r1(ly), r1(x + ln), r1(ly), {'dash': 1}])
        c += [['R', r1(x + 20), r1(y + 20), 560, 560], ['Ln', r1(x + 20), r1(y + 20), r1(x + 580), r1(y + 580), {'sw': 3}],
              ['Ln', r1(x + 580), r1(y + 20), r1(x + 20), r1(y + 580), {'sw': 3}]]
        c += [['R', r1(x + 716.5), r1(y + 90), 560, 420, {'rx': 30}], ['Ci', r1(x + 996.5), r1(y + 300), 22, {'sw': 3}]]
        if ln >= 1800:
            c.append(['R', r1(x + 1316.5), r1(y + 40), 460, 520, {'rx': 15, 'sw': 4}])
            c += [['Ci', r1(x + cx), r1(y + cy), 75, {'sw': 3}] for cx in (1426.5, 1666.5) for cy in (170, 430)]
        front = [x, y + 600, x + ln, y + 600 + R['kitchen_front']] if wall == 'n' else [x, y - R['kitchen_front'], x + ln, y]
    return Item('kitchen', bx, c, [front])


def along_walls(rb, dx, dy, step=50):
    """Kandidāti (x, y, wall) priekšmetam dx x dy pie katras taisnstūra sienas."""
    x0, y0, x1, y1 = rb
    out = []
    for x in frange(x0, x1 - dx, step):
        out.append((x, y0, 'n'))
        out.append((x, y1 - dy, 's'))
    for y in frange(y0, y1 - dy, step):
        out.append((x0, y, 'w'))
        out.append((x1 - dx, y, 'e'))
    return out


def frange(a, b, s):
    out, v = [], a
    while v <= b + 0.5:
        out.append(v)
        v += s
    if out and out[-1] < b - 0.5:
        out.append(b)
    return out


class Ctx:
    def __init__(self, L, room, blocked, wins, all_wins):
        self.L, self.room, self.blocked, self.wins = L, room, blocked, wins
        self.wz = [(w, win_zone(w, L)) for w in all_wins]
        self.rb = room.boxes()

    def ok(self, it, placed):
        b = it.box
        if not any(inside(b, rb) for rb in self.rb):
            return False
        for z in self.blocked:
            if ov(b, z):
                return False
        for w, z in self.wz:
            if ov(b, z):
                if it.kind == 'toilet':
                    continue
                if it.kind == 'bed' and w['sill'] >= 1200:
                    continue
                if it.kind == 'kitchen' and w['sill'] >= 1000 and (w['head'] - w['sill']) <= 600:   # [MM] tikai mazs horizontāls logs darba virsmas augstumā (1000/600)
                    continue
                if it.kind == 'kitchen':      # [MM] citādi logs >= 100 mm no virtuves virsmas (zonai +50 katrā pusē)
                    z2 = [z[0] - 50, z[1], z[2] + 50, z[3]] if w['o'] == 'h' else [z[0], z[1] - 50, z[2], z[3] + 50]
                    if not ov(b, z2):
                        continue
                if it.kind == 'sofa' and w['o'] == 'v':
                    continue
                return False
        for p in placed:
            if ov(b, p.box):
                return False
            for f in p.free:                      # cita priekšmeta brīvā zona
                if ov(b, f):
                    return False
            for f in it.free:
                if ov(f, p.box):
                    return False
        for f in it.free:
            if not any(inside(f, rb) for rb in self.rb):
                # brīvā zona drīkst iziet tikai durvju ailā; vienkāršoti: jābūt telpā
                return False
        return True


def bed_cands(ctx, bw):
    out = []
    for rb in ctx.rb:
        x0, y0, x1, y1 = rb
        for head in ('w', 'e'):
            bx = x0 if head == 'w' else x1 - 2000
            if x1 - x0 < 2000:
                continue
            for y in frange(y0, y1 - bw, 50):
                b = [bx, y, bx + 2000, y + bw]
                sides = [(y - y0, [bx, y0, bx + 2000, y]), (y1 - y - bw, [bx, y + bw, bx + 2000, y1])]
                good = [z for d, z in sides if d >= R['bed_side']]
                if not good:
                    continue
                foot = [bx + 2000, y, bx + 2000 + R['bed_foot'], y + bw] if head == 'w' else [bx - R['bed_foot'], y, bx, y + bw]
                # brīvā josla: platākā no labajām pusēm (600 mm), kājgalis (ja telpā)
                z = max(good, key=lambda q: q[3] - q[1])
                strip = [z[0], z[1], z[2], z[3]] if z[3] - z[1] <= R['bed_side'] else (
                    [z[0], z[1], z[2], z[1] + R['bed_side']] if z[1] >= y + bw - 1 else [z[0], z[3] - R['bed_side'], z[2], z[3]])
                free = [strip] + ([foot] if inside(foot, rb) else [])
                ex = 0
                cmds = [['bed', r1(bx), r1(y), 2000, bw, head]]
                it = Item('bed', b, cmds, free)
                it.head, it.y0, it.y1, it.hx = head, y0, y1, bx
                # vērtējums: gulta pie sienas pretī logam, centrā
                mid = abs((y + bw / 2) - (y0 + y1) / 2)
                out.append((mid, it))
    out.sort(key=lambda q: q[0])
    return [it for _, it in out]


def wardrobe_cands(ctx, lens=(2400, 2000, 1800, 1600, 1400, 1200)):
    out = []
    for ln in lens:
        for rb in ctx.rb:
            for x, y, wall in along_walls(rb, ln if True else 600, 600, 100):
                if wall in ('n', 's'):
                    b = [x, y, x + ln, y + 600]
                    front = 's' if wall == 'n' else 'n'
                    fz = [x, y + 600, x + ln, y + 600 + R['wardrobe_front']] if wall == 'n' else [x, y - R['wardrobe_front'], x + ln, y]
                    cmd = ['wardrobe', r1(x), r1(y), ln, 600, front]
                else:
                    continue
                out.append(Item('wardrobe', b, [cmd], [fz]))
            for x, y, wall in along_walls(rb, 600, ln, 100):
                if wall in ('w', 'e'):
                    b = [x, y, x + 600, y + ln]
                    front = 'e' if wall == 'w' else 'w'
                    fz = [x + 600, y, x + 600 + R['wardrobe_front'], y + ln] if wall == 'w' else [x - R['wardrobe_front'], y, x, y + ln]
                    out.append(Item('wardrobe', b, [['wardrobe', r1(x), r1(y), 600, ln, front]], [fz]))
    return out


def furnish_bed(ctx, single=False):
    sizes = [900] if single else [1600, 1400]
    best = None
    for bw in sizes:
        for bed in bed_cands(ctx, bw)[:400]:
            if not ctx.ok(bed, []):
                continue
            placed = [bed]
            # naktsgaldiņi pie galvgaļa
            nx = bed.hx if bed.head == 'w' else bed.hx + 2000 - 450
            for ny in (bed.box[1] - 450, bed.box[3] + 30):
                ns = Item('nightstand', [nx, ny, nx + 450, ny + 420], [['nightstand', r1(nx), r1(ny)]])
                if ctx.ok(ns, placed) and not any(ov(ns.box, f) for f in bed.free):
                    placed.append(ns)
            wr = None
            if ctx.room.area >= R['bed_wardrobe_min_m2']:     # [MM] maza guļamistaba: bez skapja
                for w in wardrobe_cands(ctx):
                    if ctx.ok(w, placed):
                        wr = w
                        break
            score = (1 if wr else 0) * 10 + len(placed) + (bw / 1000)
            if wr:
                placed.append(wr)
            if not best or score > best[0]:
                best = (score, placed)
            if (wr or ctx.room.area < R['bed_wardrobe_min_m2']) and len(placed) >= 3:
                return placed
    return best[1] if best else None


def furnish_bath(ctx, wins):
    rbs = ctx.rb
    rb = max(rbs, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    x0, y0, x1, y1 = rb
    hw = [w for w in wins if w['o'] == 'h']
    tcs = []
    fw, fd = R['toilet_front']
    for wy, dr in ((y0, 1), (y1, -1)):
        cxs = list(frange(x0 + R['toilet_side'], x1 - R['toilet_side'], 50))
        for w in hw:          # [MM] pods pēc noklusējuma centrēts zem loga (loga centrs = poda ass)
            if ((w['y'] == 0) == (dr == 1)):
                c = w['x'] + w['len'] / 2
                if x0 + R['toilet_side'] <= c <= x1 - R['toilet_side']:
                    cxs.append(c)
        for cx in cxs:
            centred = any(abs(w['x'] + w['len'] / 2 - cx) <= 25 and ((w['y'] == 0) == (dr == 1)) for w in hw)
            under = any(w['x'] <= cx <= w['x'] + w['len'] and ((w['y'] == 0) == (dr == 1)) for w in hw)
            tb = [cx - 215, min(wy, wy + 540 * dr), cx + 215, max(wy, wy + 540 * dr)]
            fz = [cx - fw / 2, tb[3], cx + fw / 2, tb[3] + fd] if dr == 1 else [cx - fw / 2, tb[1] - fd, cx + fw / 2, tb[1]]
            it = Item('toilet', tb, [['toilet', r1(cx), r1(wy), dr]], [fz])
            it.cx = cx
            tcs.append((0 if centred else 2 if not under else 3, abs(cx - (x0 + R['toilet_side'])), it))
    # [MM] pods pie sānsienas (mugura pret sienu, skatās telpā): rezerves variants, ja centrēts zem loga neder
    for wx, dr in ((x1, 'e'), (x0, 'w')):
        for cy in frange(y0 + R['toilet_side'], y1 - R['toilet_side'], 50):
            tb = [wx - 540, cy - 215, wx, cy + 215] if dr == 'e' else [wx, cy - 215, wx + 540, cy + 215]
            fz = [tb[0] - fd, cy - fw / 2, tb[0], cy + fw / 2] if dr == 'e' else [tb[2], cy - fw / 2, tb[2] + fd, cy + fw / 2]
            it = Item('toilet', tb, [['toilet', r1(wx), r1(cy), 1, dr]], [fz])
            it.cx = cy
            tcs.append((1, abs(cy - (y0 + R['toilet_side'])), it))
    tcs.sort(key=lambda q: (q[0], q[1]))
    for _, _, toi in tcs[:120]:
        if not ctx.ok(toi, []):
            continue
        for sz in (900, 800):
            for (sx, sy) in ((x0, y0), (x1 - sz, y0), (x0, y1 - sz), (x1 - sz, y1 - sz)):
                sb = [sx, sy, sx + sz, sy + sz]
                glass = [d for d, c in (('w', sx > x0 + 1), ('e', sx + sz < x1 - 1), ('n', sy > y0 + 1), ('s', sy + sz < y1 - 1)) if c]
                fr = []
                if 's' in glass: fr = [sx, sy + sz, sx + sz, sy + sz + R['shower_front']]
                elif 'n' in glass: fr = [sx, sy - R['shower_front'], sx + sz, sy]
                elif 'e' in glass: fr = [sx + sz, sy, sx + sz + R['shower_front'], sy + sz]
                elif 'w' in glass: fr = [sx - R['shower_front'], sy, sx, sy + sz]
                sh = Item('shower', sb, [['shower', r1(sx), r1(sy), sz, glass]], [fr] if fr else [])
                if not ctx.ok(sh, [toi]) or gapd(sh.box, toi.box) < R['toilet_gap']:
                    continue
                bcs = along_walls(rb, 500, 450, 50) + [(a, b, w) for a, b, w in along_walls(rb, 450, 500, 50) if w in ('w', 'e')]
                tw = toi.cmds[0][4] if len(toi.cmds[0]) > 4 else None
                if tw:    # [MM] pods pie sānsienas: izlietne gar to pašu sienu blakus podam (praktiskāk)
                    bcs.sort(key=lambda q: 0 if q[2] == tw else 1)
                for bx, by, wall in bcs:
                    if wall in ('n', 's'):
                        bb = [bx, by, bx + 500, by + 450]
                        fz = [bx, by + 450, bx + 500, by + 450 + R['basin_front']] if wall == 'n' else [bx, by - R['basin_front'], bx + 500, by]
                        cmd = ['basin', r1(bx), r1(by), 500, 450, wall]
                    else:
                        bb = [bx, by, bx + 450, by + 500]
                        fz = [bx + 450, by, bx + 450 + R['basin_front'], by + 500] if wall == 'w' else [bx - R['basin_front'], by, bx, by + 500]
                        cmd = ['basin', r1(bx), r1(by), 450, 500, wall]
                    ba = Item('basin', bb, [cmd], [fz])
                    if not ctx.ok(ba, [toi, sh]) or gapd(ba.box, toi.box) < R['toilet_gap']:
                        continue
                    if gapd(ba.box, sh.box) < R['basin_shower_gap']:     # [MM] starp izlietni un dušu jāvar paiet garām
                        continue
                    placed = [toi, sh, ba]
                    for wx, wy2, wall2 in along_walls(rb, 600, 600, 50):
                        fz = {'n': [wx, wy2 + 600, wx + 600, wy2 + 1200], 's': [wx, wy2 - 600, wx + 600, wy2],
                              'w': [wx + 600, wy2, wx + 1200, wy2 + 600], 'e': [wx - 600, wy2, wx, wy2 + 600]}[wall2]
                        wa = Item('washer', [wx, wy2, wx + 600, wy2 + 600], [['washer', r1(wx), r1(wy2)]], [fz])
                        if ctx.ok(wa, placed) and gapd(wa.box, toi.box) >= 1:
                            placed.append(wa)
                            break
                    return placed
    return None


def sofa_cands(ctx):
    out = []
    for rb in ctx.rb:
        x0, y0, x1, y1 = rb
        for sw in (2400, 2200, 2000, 1800, 1600, 1400, 1200):
            if x1 - x0 < sw:
                continue
            for x in frange(x0, x1 - sw, 100):
                ys = [(y0, 'n'), (y1 - 900, 's')] + [(yy, b) for yy in frange(y0 + 700, y1 - 1600, 100) for b in ('n', 's')]
                for y, back in ys:
                    fz = [x, y + 900, x + sw, y + 900 + 700] if back == 'n' else [x, y - 700, x + sw, y]
                    it = Item('sofa', [x, y, x + sw, y + 900], [['sofa', r1(x), r1(y), sw, 900, back]], [fz])
                    wall = y in (y0, y1 - 900)
                    out.append((-sw + (0 if wall else 300), it))
    out.sort(key=lambda q: q[0])
    return [it for _, it in out]


def liv_wardrobe(ctx, k, placed):
    """[MM] skapis dzīvojamā nekad nav 'vienkārši istabā': gar ārsienu (n/s), kreisā mala pret starpsienas galu (istabas kreisā mala)
    vai pret virtuves rindas galu."""
    out = []
    for rb in ctx.rb:
        xs = [rb[0], k.box[2]] + [z[2] for z in ctx.blocked if z[2] > rb[0] and z[1] < rb[3] and z[3] > rb[1] and z[2] - z[0] > 1500]
        for ln in (1200, 1000, 800):
            for rank, x in enumerate(xs):
                for wall, y in (('n', rb[1]), ('s', rb[3] - 600)):
                    b = [x, y, x + ln, y + 600]
                    fz = [x, y + 600, x + ln, y + 600 + R['wardrobe_front']] if wall == 'n' else [x, y - R['wardrobe_front'], x + ln, y]
                    out.append((rank, -ln, Item('wardrobe', b, [['wardrobe', r1(x), r1(y), ln, 600, 's' if wall == 'n' else 'n']], [fz])))
    out.sort(key=lambda q: (q[0], q[1]))
    for _, _, w in out:
        if ctx.ok(w, placed):
            return w
    return None


def furnish_liv(ctx, wet_walls, wardrobe=False):
    out_best = None
    kc = []
    for rb in ctx.rb:
        for ln in (2400, 2100, 1800):
            for x, y, wall in along_walls(rb, ln, 600, 100):
                if wall in ('n', 's'):
                    it = kitchen_items(x, y, ln, wall)
                    pref = 0 if any(abs((y if wall == 'n' else y + 600) - ww) < 300 for ww in wet_walls.get('h', [])) else 1
                    kc.append((pref, -ln, it))
            for x, y, wall in along_walls(rb, 600, ln, 100):
                if wall in ('w', 'e'):
                    it = kitchen_items(x, y, ln, wall)
                    pref = 0 if any(abs((x if wall == 'w' else x + 600) - ww) < 300 for ww in wet_walls.get('v', [])) else 1
                    kc.append((pref, -ln, it))
    # [MM] šaurās mājās virtuve gar iekšējo galasienu (pret priekšnamu/sanmezglu), nevis gar garo ārsienu
    L_ = ctx.L
    narrow = L_.forma == 'II' and (L_.D - 2 * T) < 4400

    def endpref(k):
        if not narrow:
            return 1
        b = k.box
        tall = (b[3] - b[1]) > (b[2] - b[0])
        interior = (b[0] > T + 1 and b[2] < L_.W - T - 1)
        return 0 if (tall and interior) else 1
    kc.sort(key=lambda q: (endpref(q[2]), q[0], q[1]))
    tried = 0
    for _, _, k in kc:
        if not ctx.ok(k, []):
            continue
        tried += 1
        if tried > 40:
            break
        placed = [k]
        if wardrobe:
            wd = liv_wardrobe(ctx, k, placed)
            if wd:
                placed.append(wd)
        so = None
        for s in sofa_cands(ctx):
            if ctx.ok(s, placed) and gapd(s.box, k.box) >= R['sofa_kitchen']:
                so = s
                break
        if so:
            placed.append(so)
        tb = None
        for rad in (450, 400):
            for rb in ctx.rb:
                x0, y0, x1, y1 = rb
                for cx in frange(x0 + rad + R['table_wall'], x1 - rad - R['table_wall'], 100):
                    for cy in frange(y0 + rad + R['table_wall'], y1 - rad - R['table_wall'], 100):
                        b = [cx - rad, cy - rad, cx + rad, cy + rad]
                        it = Item('table', b, [['Ci', r1(cx), r1(cy), rad]], [])
                        if not ctx.ok(it, placed):
                            continue
                        if any(gapd(b, p.box) < R['table_clear'] for p in placed):
                            continue
                        d = gapd(b, k.box)
                        if not tb or d < tb[0]:
                            tb = (d, it)
            if tb:
                break
        if tb:
            placed.append(tb[1])
        score = len(placed) + (1.5 if endpref(k) == 0 else 0)     # [MM] virtuve gar iekšējo galasienu ir svarīgāka par galda ietilpšanu
        if not out_best or score > out_best[0]:
            out_best = (score, placed)
        if score >= 3 and endpref(k) == 0 or (score == 3 and not narrow):
            break
    return out_best[1] if out_best else None


def furnish_hall(ctx):
    for ln in (1600, 1200, 1000, 800):
        for rb in ctx.rb:
            for x, y, wall in along_walls(rb, 600, ln, 100) + along_walls(rb, ln, 600, 100):
                if wall in ('w', 'e'):
                    b = [x, y, x + 600, y + ln]
                    if b[3] - b[1] != ln:
                        continue
                    fz = [x + 600, y, x + 1500, y + ln] if wall == 'w' else [x - 900, y, x, y + ln]
                    it = Item('wardrobe', b, [['wardrobe', r1(x), r1(y), 600, ln, 'e' if wall == 'w' else 'w']], [fz])
                else:
                    b = [x, y, x + ln, y + 600]
                    if b[2] - b[0] != ln:
                        continue
                    fz = [x, y + 600, x + ln, y + 1500] if wall == 'n' else [x, y - 900, x + ln, y]
                    it = Item('wardrobe', b, [['wardrobe', r1(x), r1(y), ln, 600, 's' if wall == 'n' else 'n']], [fz])
                # [MM] skapis nedrīkst noslēgt caurgājienu: šķērsām atlikušais brīvais platums >= 900
                rem = (rb[3] - rb[1]) - (ln if wall in ('w', 'e') else 600)
                if rem < R['hall_pass']:
                    continue
                if ctx.ok(it, []):
                    return [it]
    return []


# ======================================================================================
# 5. MODELIS (model.json) un pārbaude
# ======================================================================================
def eave_of(H, D):
    tanp = math.tan(math.radians(PITCH))
    return H - ROOF_T / math.cos(math.radians(PITCH)) - (D / 2) * tanp


def realize(L, H, loft=False, griesti=2200):
    """Telpas -> durvis -> logi -> mēbeles. Atgriež (model dict, notes) vai (None, iemesls)."""
    rooms = L.rooms
    name_beds(L)
    # ---- durvis ----
    doors, blocked = [], {i: [] for i in range(len(rooms))}
    door_of = {}
    for a, hubs in L.links:
        if isinstance(hubs, int):
            hubs = [hubs]
        opts = []
        for h in hubs:
            opts = door_options(rooms[a], rooms[h], R['door_w'])
            if opts:
                door_of[a] = (h, opts)
                break
        if a not in door_of:
            return None, f'{rooms[a].name}: nav kopējas sienas ar {"/".join(rooms[h].name for h in hubs)} durvīm'
    # ieeja
    ent = entry_options(L, rooms[L.entry])
    if not ent:
        return None, f'{rooms[L.entry].name}: nav ārsienas ārdurvīm'
    # ---- izvēlas durvju pozīcijas un mēbeles telpu pa telpai ----
    order = sorted(range(len(rooms)), key=lambda i: {'bath': 0, 'bed': 1, 'bed_s': 1, 'hall': 2, 'corridor': 3, 'liv': 4}[rooms[i].kind])
    best = None
    for entry in ent[:6]:
        res = _realize_with_entry(L, rooms, door_of, entry, order)
        if res[0]:
            best = res
            break
        best = best or res
    if not best or not best[0]:
        return None, best[1] if best else 'neizdevās'
    doors, wins, items = best[0]
    m = to_model(L, H, doors, wins, items, loft, griesti)
    if m is None:
        return None, 'mansards neder'
    return m, None


def door_block(d):
    """Zonas bez mēbelēm: īstā vērtne + 50 mm un rules_check vērtnes kvadrāts + 50 mm."""
    g = R['door_gap']
    sz = swing_zone(d)
    s, w = d['side'], d['w']
    rc = [d['x'], d['y'], d['x'] + w, d['y'] + s * w] if d['o'] == 'h' else [d['x'], d['y'], d['x'] + s * w, d['y'] + w]
    rc = [min(rc[0], rc[2]), min(rc[1], rc[3]), max(rc[0], rc[2]), max(rc[1], rc[3])]
    return [[z[0] - g, z[1] - g, z[2] + g, z[3] + g] for z in (sz, rc)]


def _realize_with_entry(L, rooms, door_of, entry, order):
    land = entry_land(entry)
    chosen = {}          # telpa -> door dict
    gblock = [land]      # visas durvju zonas (globāli)
    pass_z = []
    items = {}
    wopts = {i: win_sets(L, rooms[i], entry) for i in range(len(rooms))}
    for i in range(len(rooms)):
        if rooms[i].kind in ('liv', 'bed', 'bed_s', 'bath') and not wopts[i]:
            return None, f'{rooms[i].name}: nav ārsienas logam'
    fixed_wins = {}

    def door_ok(d):
        sz = swing_zone(d)
        if any(ov(sz, swing_zone(o)) for o in chosen.values()) or ov(sz, land):
            return False
        if any(ov(sz, p) for p in pass_z):
            return False
        pz = pass_zone(d, R['door_pass'])
        if any(ov(pz, swing_zone(o)) for o in chosen.values()):
            return False
        return True

    # 1) hubu durvis (dzīvojamā/gaitenis -> priekšnams) vispirms
    for i in order:
        if rooms[i].kind in ('liv', 'corridor') and i in door_of:
            h, opts = door_of[i]
            d = next((o for o in opts if door_ok(o)), None)
            if not d:
                return None, f'{rooms[i].name}: durvis uz {rooms[h].name} nesader'
            chosen[i] = d
            gblock += door_block(d)
            pass_z.append(pass_zone(d, R['door_pass']))
    # 2) privātās telpas: durvju pozīcija + logi + mēbeles kopā
    for i in order:
        r = rooms[i]
        if r.kind in ('hall', 'corridor', 'liv'):
            continue
        h, opts = door_of[i]
        ok = False
        for d in opts:
            if not door_ok(d):
                continue
            blocked = gblock + door_block(d) + pass_z
            for ws in wopts[i][:14]:
                ctx = Ctx(L, r, blocked, ws, ws)
                if r.kind in ('bed', 'bed_s'):
                    it = furnish_bed(ctx, single=(r.kind == 'bed_s' and r.area < 8.0))
                    if it and not any(x.kind == 'bed' for x in it):
                        it = None
                elif r.kind == 'bath':
                    it = furnish_bath(ctx, ws)
                else:
                    it = []
                if it is None:
                    continue
                chosen[i] = d
                gblock += door_block(d)
                pass_z.append(pass_zone(d, R['door_pass']))
                fixed_wins[i] = ws
                items[i] = it
                ok = True
                break
            if ok:
                break
        if not ok:
            return None, f'{r.name}: neizdodas izvietot mēbeles (durvis/logi)'
    # 3) hubi: priekšnams, gaitenis, dzīvojamā
    hall_extra = [[b[0] - 1000, b[1], b[2] + 1000, b[3]] for rr in rooms if rr.kind in ('hall', 'corridor') for b in rr.boxes()]   # caurejas josla uz dzīvojamo
    wardrobe_moved = False
    for i in order:
        r = rooms[i]
        if r.kind not in ('hall', 'corridor', 'liv'):
            continue
        done = False
        for ws in (wopts[i][:60] if r.kind == 'liv' else wopts[i][:1]):
            ctx = Ctx(L, r, gblock + pass_z + (hall_extra if r.kind == 'liv' else []), ws, ws)
            if r.kind == 'liv':
                wet = {'h': [], 'v': []}
                for j, rr in enumerate(rooms):
                    if rr.kind == 'bath':
                        sw = shared_wall(r, rr)
                        if sw:
                            wet[sw[0]] += [sw[1], sw[1] + t]
                it = furnish_liv(ctx, wet, wardrobe_moved)
                if not it or not any(x.kind == 'kitchen' for x in it):
                    continue
            elif r.kind == 'hall':
                it = furnish_hall(ctx)
                wardrobe_moved = wardrobe_moved or not it       # [MM] priekšnamā skapja nav: liek dzīvojamā, ja ietilpst
            else:
                it = []
            items[i] = it
            fixed_wins[i] = ws
            done = True
            break
        if not done:
            return None, f'{r.name}: neizdodas izvietot virtuvi/mēbeles'
    doors = [{k: v for k, v in entry.items() if not k.startswith('_')}] + [chosen[i] for i in sorted(chosen)]
    wins = [w for i in sorted(fixed_wins) for w in fixed_wins[i]]
    return (doors, wins, items), None


def stamp_spot(room, items, doors):
    occ = [it.box for it in items] + [swing_zone(d) for d in doors if not d.get('entry')]
    best = None
    for rb in sorted(room.boxes(), key=lambda b: -(b[2] - b[0]) * (b[3] - b[1])):
        x0, y0, x1, y1 = rb
        fw = max(1.0, len(room.name) / 22)     # garš nosaukums = platāka telpas zīme
        for sc, (hw, hh) in ((0.6, (750 * fw, 330)), (0.5, (620 * fw, 280)), (0.45, (560 * fw, 250))):
            for cx in frange(x0 + hw + 50, x1 - hw - 50, 100):
                for cy in frange(y0 + hh + 50, y1 - hh - 50, 100):
                    b = [cx - hw, cy - hh, cx + hw, cy + hh]
                    if not any(ov(b, o, 60) for o in occ):
                        d = abs(cx - (x0 + x1) / 2) + abs(cy - (y0 + y1) / 2)
                        if not best or (sc, -d) > (best[0], -best[3]):
                            best = (sc, cx, cy, d)
            if best:
                return [r1(best[1]), r1(best[2])], best[0]
    rb = room.boxes()[0]
    return [r1((rb[0] + rb[2]) / 2), r1((rb[1] + rb[3]) / 2)], 0.45


def to_model(L, H, doors, wins, items, loft, griesti):
    W, D = L.W, L.D
    rooms = L.rooms
    furn = [c for i in sorted(items) for it in items[i] for c in it.cmds]
    eave = eave_of(H, D)
    A = poly_area(L.poly) / 1e6 if L.poly else W * D / 1e6
    m = {'id': 'MM-PLAN', 'nosaukums': 'MM plāns', 'platiba_grupa': f"{int(round(A / 5) * 5)}m2",
         'ievade': {'garums': W, 'platums': D, 'augstums': H}, 'W': W, 'D': D,
         'jumts': {'forma': 'divslipju', 'pitch': PITCH, 'ov': 0, 'eave': round(eave)},
         'rooms': [{'n': r.name, 'en': r.en, 'r': r.rects} for r in rooms],
         'doors': doors, 'windows': wins, 'furniture': furn}
    if L.poly:
        m['poly'] = L.poly
        m['recess'] = L.recess
        xs = sorted({p[0] for p in L.poly})
        ys = sorted({p[1] for p in L.poly})
        m['axes'] = {'x': [[x, str(i + 1)] for i, x in enumerate(xs)], 'y': [[y, chr(65 + i)] for i, y in enumerate(ys)]}
    else:
        m['axes'] = {'x': [[0, '1'], [W, '2']], 'y': [[0, 'A'], [D, 'B']]}
    sa, ss = {}, {}
    for i, r in enumerate(rooms):
        p, sc = stamp_spot(r, items.get(i, []), doors)
        sa[str(i)], ss[str(i)] = p, sc
    m['stampAt'], m['stampScale'] = sa, ss
    hall = next((i for i, r in enumerate(rooms) if r.kind == 'hall'), None)
    hb = rooms[hall].boxes()[0] if hall is not None else rooms[0].boxes()[0]
    m['levelAt'] = [r1(hb[0] + 300), r1(hb[3] - 300)]
    # iekšējās izmēru ķēdes: viena pa x (ziemeļu josla), pa y katras kolonnas vidū (max 3)
    cols = sorted({r.rects[0][0] for r in rooms})
    m['innerDims'] = [['x', r1(T + 400)]] + [['y', r1(x + 400)] for x in cols[:3]]
    m.update({'wallTags': [], 'sections': [], 'gableWins': [], 'ceiling': griesti, 'planNotes': [], 'projekts': {}})
    m['ceilingNote'] = f'Griestu augstums {griesti} mm.'
    m['winOk'] = [it.box for i in items for it in items[i] if it.kind == 'sofa' and any(ov(it.box, win_zone(w, L)) for w in wins)]
    L.glaz = [w for w in wins if w['sill'] == 0 and w['len'] > R['win_fixed_min']]
    if loft:
        lf = make_loft(L, H, eave, items, doors, wins, griesti)
        if lf is None:
            return None
        m['loft'], m['gableWins'] = lf
        m['ceilingNote'] = f'Griestu augstums zem mansarda {griesti} mm, dzīvojamā istaba atvērta līdz jumtam.'
    m['_planner'] = {'forma': L.forma, 'tips': L.topo, 'klase': L.klase,
                     'apbuve_m2': round(poly_area(L.poly) / 1e6 if L.poly else W * D / 1e6, 1),
                     'telpas': [{'n': r.name, 'm2': round(r.area, 1)} for r in rooms]}
    return m


def poly_area(P):
    return abs(sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P)))) / 2


def make_loft(L, H, eave, items, doors, wins, griesti):
    """Mansards virs privātā bloka viena galā (II forma). Mēģina katru iespējamo galu; austrumu galu rēķina spoguļattēlā."""
    if L.forma != 'II' or not L.loft_x:
        return None
    W = L.W
    for side, x0, rx, vx1 in L.loft_x:
        if side == 'w':
            res = _loft_west(L, eave, griesti, x0, rx, vx1)
            if res:
                return res
            continue
        Lm = copy.copy(L)
        Lm.rooms = []
        for r in L.rooms:
            rm = copy.copy(r)
            rm.rects = [[r1(W - q[0] - q[2]), q[1], q[2], q[3]] for q in r.rects]
            Lm.rooms.append(rm)
        res = _loft_west(Lm, eave, griesti, x0, rx, vx1)
        if res:
            return _mirror_loft(res, W)
    return None


def _mirror_loft(res, W):
    lf, gw = res
    mx = lambda x: r1(W - x)
    for rm in lf['rooms']:
        rm['r'] = [[r1(W - q[0] - q[2]), q[1], q[2], q[3]] for q in rm['r']]
    fs = []
    for f in lf['furniture']:
        f = list(f)
        if f[0] == 'bed':
            f[1] = r1(W - f[1] - f[3]); f[5] = {'w': 'e', 'e': 'w'}.get(f[5], f[5])
        elif f[0] == 'R':
            f[1] = r1(W - f[1] - f[3])
        elif f[0] == 'Ln':
            f[1], f[3] = mx(f[1]), mx(f[3])
        fs.append(f)
    lf['furniture'] = fs
    flip = {'west': 'east', 'east': 'west'}
    for w in lf['windows']:
        w['x'] = r1(W - T) if w['x'] == 0 else 0
        w['out'] = -w['out']
        w['side'] = flip[w['side']]
    for g in gw:
        g['side'] = flip[g['side']]
    lf['stampAt'] = {k: [mx(v[0]), v[1]] for k, v in lf['stampAt'].items()}
    lf['levelAt'] = [mx(lf['levelAt'][0]), lf['levelAt'][1]]
    return lf, gw


def _loft_west(L, eave, griesti, x0, rx, vx1):
    W, D = L.W, L.D
    tn = math.tan(math.radians(PITCH))
    lvl = griesti + P1
    y0, y1 = T, D - T
    ridge = eave + (D / 2) * tn - lvl
    if ridge < R['loft_ridge_min']:
        return None
    hall = next((r for r in L.rooms if r.kind in ('hall', 'corridor') and r.rects[0][0] < rx), None)   # trepes priekšnamā vai gaitenī
    if not hall:
        return None
    hb = hall.boxes()[0]
    lad = 1000
    lx1 = min(rx, hb[2])
    lx0 = lx1 - lad
    if lx0 < hb[0]:
        return None
    # gulta: centrā pa kori; malu augstums >= 700
    bw = 1600
    by = D / 2 - bw / 2
    hs = [eave + min(y, D - y) * tn - lvl for y in (by, by + bw)]
    if min(hs) < R['loft_edge_h']:
        bw = 1400
        by = D / 2 - bw / 2
        hs = [eave + min(y, D - y) * tn - lvl for y in (by, by + bw)]
        if min(hs) < R['loft_edge_h']:
            return None
    bx = x0 if x0 < W / 2 else rx - 2000
    head = 'w' if x0 <= T + 1 else 'e'
    if rx - x0 < 2000 + 300:
        return None
    # trepes priekšnamā pie dzīvojamās gala; priekšnams dienvidos vai ziemeļos
    south = hb[1] >= D / 2
    ly0, ly1 = (hb[1], y1) if south else (y0, hb[3])
    py0, py1 = (y0, hb[1]) if south else (hb[3], y1)        # pilnā loft josla (bez trepju joslas)
    sub = [[r1(x0), r1(py0), r1(rx - x0), r1(py1 - py0)]]
    if lx0 - x0 > 300:
        sub.append([r1(x0), r1(ly0), r1(lx0 - x0), r1(ly1 - ly0)])
    void = ([[r1(rx), y0, r1(vx1 - rx), r1(y1 - y0)]] if rx < vx1 - 1 else []) + [[r1(lx0), r1(ly0), r1(rx - lx0), r1(ly1 - ly0)]]
    rooms = [{'n': 'Mansarda guļvieta', 'en': 'Loft', 'r': sub},
             {'n': 'Atvērts uz 1. stāvu', 'en': 'Open to below', 'void': True, 'r': void}]
    bxx = x0 if head == 'w' else rx - 2000
    if ov([bxx, by, bxx + 2000, by + bw], [lx0 - 300, ly0, rx, ly1]):
        return None        # gulta pa kori iet pāri trepju atverei
    edge = hb[1] if south else hb[3]
    furn = [['bed', r1(bxx), r1(by), 2000, bw, head],
            ['Ln', r1(rx), r1(py0), r1(rx), r1(py1), {'sw': 30}],
            ['Ln', r1(lx0), r1(edge), r1(rx), r1(edge), {'sw': 30}],
            ['R', r1(lx0 + 250), r1(ly0 + 60), 500, r1(ly1 - ly0 - 120)]]
    furn += [['Ln', r1(lx0 + 250), r1(ly0 + 60 + k * 210), r1(lx0 + 750), r1(ly0 + 60 + k * 210), {'sw': 4}] for k in range(1, int((ly1 - ly0 - 120) / 210))]
    if rx < vx1 - 1:
        furn += [['Ln', r1(rx), y0, r1(vx1), r1(y1), {'dash': 1}], ['Ln', r1(vx1), y0, r1(rx), r1(y1), {'dash': 1}]]
    # mansarda logs privātās daļas gala fasādē: [MM] standarts = gāžamais (hopper) 1000 x 550, ar ārējo apmali kā parastiem logiem
    side = 'west' if x0 <= T + 1 else 'east'
    gl, gh = R['loft_win']
    sill = 2700
    while eave + ((D - gl) / 2) * tn < sill + gh + 150 and sill > 2200:
        sill -= 100
    lw = [{'len': gl, 'sill': sill, 'head': sill + gh, 'kind': 'hopper', 'x': 0 if side == 'west' else r1(W - T), 'y': r1((D - gl) / 2), 'o': 'v',
           'out': -1 if side == 'west' else 1, 'side': side}]
    # [MM] otrs mansarda logs dzīvojamās gala fasādē (virs lielā stiklojuma): piecstūra (divas slīpas malas) fixed ar apmali
    lside = 'east' if side == 'west' else 'west'
    liv = next((r for r in L.rooms if r.kind == 'liv'), None)
    pent = None
    if liv and any((b[2] >= W - T - 1) if lside == 'east' else (b[0] <= T + 1) for b in liv.boxes()):
        big = next((w for w in L.glaz if w['side'] == lside), None) if getattr(L, 'glaz', None) else None
        g2 = min(2200, (D - 2 * T) - 700)
        y2 = r1((D - g2) / 2)
        if big:
            g2, y2 = big['len'], big['y']
        while g2 >= 600 and eave + ((D - g2) / 2) * tn < 2900 + 150:
            g2 -= 200
        if g2 >= 600:
            pent = {'len': r1(g2), 'sill': 2300, 'head': 2900, 'kind': 'fixed', 'shape': 'gable', 'x': r1(W - T) if lside == 'east' else 0,
                    'y': y2, 'o': 'v', 'out': 1 if lside == 'east' else -1, 'side': lside}
            lw.append(pent)
    lf = {'level': r1(lvl), 'rooms': rooms, 'doors': [], 'windows': lw, 'furniture': furn,
          'stampAt': {'0': [r1((x0 + rx) / 2), r1(max(y0 + 400, by - 350) if south else min(y1 - 400, by + bw + 350))]}, 'stampScale': {'0': 0.55},
          'levelAt': [r1(x0 + 600), r1(y0 + 400)], 'ceilingNote': ''}
    gw = [{'side': w['side'], 'u0': w['y'], 'u1': r1(w['y'] + w['len']), 'z0': w['sill'],
           **({'shape': 'pent'} if w.get('shape') == 'gable' else {'win': 1, 'z1': w['head'], 'kind': w['kind']})} for w in lw]
    return lf, gw


# ---------------- pārbaudes ----------------
def own_check(m, L):
    """Plānotāja [MM] noteikumi, ko rules_check nemēra (mēbele loga zonā, īstā vērtnes zona, normas)."""
    errs = []
    from rules_check import fbox as rfbox
    W, D = m['W'], m['D']
    boxes = []
    for f in m['furniture']:
        if f[0] == 'wardrobe':
            boxes.append((f, [f[1], f[2], f[1] + f[3], f[2] + f[4]]))
        else:
            b = rfbox(f)
            if b:
                boxes.append((f, b))
    top = [(f, b) for f, b in boxes if not any(g is not f and inside(b, gb) and (gb[2] - gb[0]) * (gb[3] - gb[1]) > (b[2] - b[0]) * (b[3] - b[1]) for g, gb in boxes)]
    for w in m['windows']:
        z = win_zone(w, L)
        for f, b in top:
            if f[0] == 'toilet' or (f[0] == 'bed' and w['sill'] >= 1200) or (f[0] == 'sofa' and w['o'] == 'v'):
                continue
            if f[0] == 'R' and w['sill'] >= 1000 and (w['head'] - w['sill']) <= 600 and 600 in (f[3], f[4]) and max(f[3], f[4]) >= 1800:   # [MM] virtuves darba virsma zem mazā horizontālā loga
                continue
            if f[0] == 'R' and 600 in (f[3], f[4]) and max(f[3], f[4]) >= 1800 and not ov(b, [z[0] - 50, z[1], z[2] + 50, z[3]] if w['o'] == 'h' else [z[0], z[1] - 50, z[2], z[3] + 50]):
                continue
            if ov(b, z):
                errs.append(f"{f[0]} loga zonā ({w['side']} {w['x'] if w['o'] == 'h' else w['y']})")
    for d in m['doors']:
        if d.get('entry'):
            continue
        sz = swing_zone(d)
        sz = [sz[0] - R['door_gap'], sz[1] - R['door_gap'], sz[2] + R['door_gap'], sz[3] + R['door_gap']]
        for f, b in top:
            if ov(b, sz):
                errs.append(f"{f[0]} durvju vērtnes zonā ({d['x']},{d['y']})")
    # telpu normas (tikai tās pašas klases bibliotēka)
    N = planlib.norms(L.klase, 'modulu')['rooms_m2']
    km = {'bed': 'bed', 'bed_s': 'bed', 'bath': 'bath', 'hall': 'hall', 'liv': 'living'}
    notes = []
    for r in L.rooms:
        k = km.get(r.kind)
        if k in N:
            lo, hi, _ = N[k]
            if r.area < lo * 0.85:
                notes.append(f'{r.name} {r.area:.1f} m2 mazāka par {L.klase} bibliotēkas min {lo:g} m2')
            elif r.area > hi * 1.3:
                notes.append(f'{r.name} {r.area:.1f} m2 lielāka par {L.klase} max {hi:g}')
    return errs, notes


def rc_count(m):
    rep, _ = rules_check.check(copy.deepcopy(m))
    n = {'KĻŪDA': [], 'BRĪD.': [], 'INFO': []}
    for lvl, rule, text, src in rep.rows:
        n[lvl].append(f'[{rule}] {text}')
    return n


def signature(m):
    """Plāna "tips" bez spoguļojuma: telpu secība pa x un y."""
    rs = sorted(((r['n'].split(' ')[0], round(r['r'][0][0] / 500), round(r['r'][0][1] / 500)) for r in m['rooms']))
    W = m['W']
    rm = sorted(((r['n'].split(' ')[0], round((W - r['r'][0][0] - r['r'][0][2]) / 500), round(r['r'][0][1] / 500)) for r in m['rooms']))
    return min(tuple(rs), tuple(rm))


# ---------------- [MM] arhitekta vērtējums no konkurentu plāniem ----------------
_KSH = {}


def konk_dalas(klase):
    """Konkurentu (tips modulu, tā pati klase) telpu daļas no kopējās telpu platības: vidējā un 10.-90. procentile."""
    if klase in _KSH:
        return _KSH[klase]
    rows = []
    for m in planlib.load(klase, 'modulu'):
        a = {}
        for r in m.get('rooms', []):
            k = {'hall': 'circ', 'corridor': 'circ'}.get(planlib.kind(r['name']), planlib.kind(r['name']))
            if k in ('living', 'bed', 'bath', 'circ') and r.get('m2'):
                a[k] = a.get(k, 0) + r['m2']
        tot = sum(a.values())
        if tot and 'living' in a:
            rows.append({k: a.get(k, 0) / tot for k in ('living', 'bed', 'bath', 'circ')})
    out = {}
    for k in ('living', 'bed', 'bath', 'circ'):
        v = sorted(r[k] for r in rows)
        out[k] = (sum(v) / len(v), v[int(.1 * (len(v) - 1))], v[int(.9 * (len(v) - 1))]) if v else (0, 0, 1)
    _KSH[klase] = out
    return out


def _room_at(L, x, y):
    for i, r in enumerate(L.rooms):
        if any(q[0] - 1 <= x <= q[2] + 1 and q[1] - 1 <= y <= q[3] + 1 for q in r.boxes()):
            return i
    return None


def _door_rooms(L, d):
    th = d.get('th', t)
    if d['o'] == 'h':
        c = d['x'] + d['w'] / 2
        pts = [(c, d['y'] - 120), (c, d['y'] + th + 120)]
    else:
        c = d['y'] + d['w'] / 2
        pts = [(d['x'] - 120, c), (d['x'] + th + 120, c)]
    return [_room_at(L, *p) for p in pts]


def vertejums(m, klase):
    """[MM] Arhitekta vērtējums (mazāks = labāks) un pamatojums.
    Galvenie kritēriji: dienas/nakts zonas, gaiteņu daudzums, mitrās telpas pie virtuves, dzīvojamās proporcijas,
    ieeja (virs60 caur priekšnamu). Konkurenti tikai kontrolei: neliels sods un piezīme, ne lēmums."""
    L = m['_L']
    km = {'liv': 'living', 'bed': 'bed', 'bed_s': 'bed', 'bath': 'bath', 'bath2': 'bath', 'hall': 'circ', 'corridor': 'circ'}
    a = {}
    for r in L.rooms:
        k = km.get(r.kind)
        if k:
            a[k] = a.get(k, 0) + r.area
    tot = sum(a.values()) or 1
    sc, plus, minus = 0.0, [], []
    # gaiteņi un priekšnams
    circ = a.get('circ', 0) / tot
    lim = .08 if klase == 'lidz60' else .14
    if circ > lim:
        sc += (circ - lim) * 40
        minus.append(f'gaiteņi {a.get("circ", 0):.1f} m² ({circ:.0%})')
    else:
        plus.append(f'maz gaiteņu ({a.get("circ", 0):.1f} m²)' if a.get('circ', 0) > .5 else 'bez gaiteņa')
    # dienas/nakts zonas: guļamistabu durvis tieši dzīvojamā
    kinds = [r.kind for r in L.rooms]
    bad = 0
    for d in m['doors']:
        if d.get('entry'):
            continue
        rs = [kinds[i] if i is not None else None for i in _door_rooms(L, d)]
        if 'liv' in rs and any(k in ('bed', 'bed_s') for k in rs):
            bad += 1
    if bad:
        sc += 1.5 * bad
        minus.append(f"{bad} guļamistab{'as' if bad == 1 else 'u'} durvis ved uz dzīvojamo")
    elif 'bed' in kinds:
        plus.append('guļamistabas atdalītas no dzīvojamās')
    # mitrās telpas pie dzīvojamās (virtuve uz mitrās sienas)
    liv = next((r for r in L.rooms if r.kind == 'liv'), None)
    baths = [r for r in L.rooms if r.kind == 'bath']
    if liv and baths:
        if any(shared_wall(b_, liv) for b_ in baths):
            plus.append('sanmezgls pie virtuves sienas')
        else:
            sc += 1
            minus.append('sanmezgls tālu no virtuves')
    # dzīvojamās proporcijas
    if liv:
        b = liv.boxes()
        w_ = max(q[2] for q in b) - min(q[0] for q in b)
        h_ = max(q[3] for q in b) - min(q[1] for q in b)
        sh, lo_ = min(w_, h_), max(w_, h_)
        if sh < 3000:
            sc += 2
            minus.append(f'dzīvojamā šaura ({sh / 1000:.1f} m)')
        elif lo_ / sh > 2.2:
            sc += 1
            minus.append('dzīvojamā izstiepta')
        else:
            plus.append(f'dzīvojamā {liv.area:.0f} m² labās proporcijās')
    # ieeja
    if klase == 'virs60' and L.entry is not None and L.rooms[L.entry].kind == 'liv':
        sc += 1.5
        minus.append('ieeja tieši dzīvojamā')
    # konkurenti kā kontrole
    K = konk_dalas(klase)
    nm = {'living': 'dzīvojamā', 'bed': 'guļamistabas', 'bath': 'sanmezgli', 'circ': 'gaiteņi'}
    for k, (mu, lo, hi) in K.items():
        d = a.get(k, 0) / tot
        sc += abs(d - mu) * 4
        low, high = d < lo * .9, d > hi * 1.1
        if (k == 'circ' and low) or (k == 'living' and high):
            continue                     # mazāk gaiteņu vai lielāka dzīvojamā nav trūkums
        if low or high:
            sc += 1
            minus.append(f'{nm[k]} {d:.0%} no platības (konkurentiem {lo:.0%}–{hi:.0%})')
    return round(sc, 2), plus, minus


# ======================================================================================
# 6. GALVENĀ FUNKCIJA
# ======================================================================================
def plan(L_mm, B_mm, H, beds=1, baths=1, formas=('II', 'L', 'T'), loft=False, n=4, griesti=2200):
    """loft: False = bez mansarda, True = ar un bez, 'only' = tikai ar mansardu."""
    W, D = float(L_mm), float(B_mm)
    A = W * D / 1e6
    klase = planlib.klase_of(A)
    din = D - 2 * T
    lays = []
    if 'II' in formas:
        lays += topo_II(W, D, beds, baths, klase)
    if 'L' in formas:
        lays += topo_L(A, D, beds, baths, klase)
    if 'T' in formas:
        lays += topo_T(A, D, beds, baths, klase)
    good, rejected = [], []
    seen = set()
    for tname, group in lays:
        if not group:
            rejected.append(f'{tname}: telpas neietilpst (izmēri, durvis vai ārsienas logi)')
            continue
        for lf in ([True] if loft == 'only' else [True, False] if loft else [False]):
            if lf and not any(g.forma == 'II' and g.loft_x for g in group):
                continue
            first_why = None
            for Lay_ in group:
                if lf and not Lay_.loft_x:
                    continue
                L2 = copy.deepcopy(Lay_)
                m, why = realize(L2, H, lf, griesti)
                if m is None:
                    first_why = first_why or why
                    continue
                rc = rc_count(m)
                errs, notes = own_check(m, L2)
                if rc['KĻŪDA'] or rc['BRĪD.'] or errs:
                    first_why = first_why or '; '.join((rc['KĻŪDA'] + rc['BRĪD.'] + errs)[:3])
                    continue
                sig = (signature(m), lf)
                if sig in seen:
                    first_why = first_why or 'tāds pats kā cits variants'
                    continue
                seen.add(sig)
                m['_planner'].update(mansards=lf, rules_check={'kludas': 0, 'bridinajumi': 0, 'info': rc['INFO']}, piezimes=notes + L2.notes)
                m['_L'] = L2
                m['_planner']['vertejums'], m['_planner']['plusi'], m['_planner']['vajas_vietas'] = vertejums(m, klase)
                m.pop('_L')
                good.append(m)
                first_why = None
                break
            if first_why:
                rejected.append(f'{group[0].forma} {tname}{" + mansards" if lf else ""}: {first_why}')
    # [MM] labākie pēc arhitekta vērtējuma; vājos (daudz novirzes no konkurentiem) atmet, ja ir labāki
    good.sort(key=lambda m: m['_planner']['vertejums'])
    if good:
        best = good[0]['_planner']['vertejums']
        for m in [m for m in good if m['_planner']['vertejums'] > best + 6]:
            rejected.append(f"{m['_planner']['forma']} {m['_planner']['tips']}: vājš plāns ({'; '.join(m['_planner']['vajas_vietas']) or 'novirze no konkurentiem'})")
            good.remove(m)
    # līdz n katrai formai
    out, per = [], {}
    for m in good:
        f = m['_planner']['forma']
        if per.get(f, 0) < n:
            per[f] = per.get(f, 0) + 1
            out.append(m)
    out.sort(key=lambda m: m['_planner']['vertejums'])
    for i, m in enumerate(out, 1):
        p = m['_planner']
        p['nr'] = i
        p['loma'] = 'optimālais' if i == 1 else 'alternatīva'
        why = '; '.join(p['plusi'][:3]) or 'vislabākais kopvērtējums'
        if i == 1:
            p['pamatojums'] = f"Izvēlēts, jo {why}." + (f" Vājā vieta: {p['vajas_vietas'][0]}." if p['vajas_vietas'] else '')
        else:
            b0 = out[0]['_planner']
            gain = [x for x in p['plusi'] if x not in b0['plusi']]
            loss = [x for x in p['vajas_vietas'] if x not in b0['vajas_vietas']]
            p['pamatojums'] = ('Alternatīva: ' + ('; '.join(gain[:2]) if gain else 'cits telpu izvietojums') +
                               (f", bet {'; '.join(loss[:2])}" if loss else '') + '.')
        p['nosaukums'] = f"V{i:02d} {p['forma']} {p['tips']}{' + mansards' if p['mansards'] else ''}"
    return out, rejected, klase


# ---------------- priekšskatījums ----------------
COL = {'Guļ': '#efe3cf', 'WC': '#d6e8ef', 'Van': '#d6e8ef', 'Dzī': '#e7efd6', 'Pri': '#eeeeee', 'Gai': '#f3f3f3', 'Teh': '#e3e3e3'}


def svg(m, s=0.05):
    W, D = m['W'], m['D']
    pad = 30
    poly = m.get('poly') or [[0, 0], [W, 0], [W, D], [0, D]]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W * s + 2 * pad:.0f} {D * s + 2 * pad:.0f}" font-family="Arial" font-size="9">',
         f'<polygon points="{" ".join(f"{pad + x * s:.1f},{pad + y * s:.1f}" for x, y in poly)}" fill="#555"/>']
    for r in m['rooms']:
        for x, y, w, h in r['r']:
            o.append(f'<rect x="{pad + x * s:.1f}" y="{pad + y * s:.1f}" width="{w * s:.1f}" height="{h * s:.1f}" fill="{COL.get(r["n"][:3], "#fff")}"/>')
    for f in m['furniture']:
        b = None
        if f[0] == 'wardrobe':
            b = [f[1], f[2], f[1] + f[3], f[2] + f[4]]
        else:
            b = rules_check.fbox(f)
        if b and f[0] != 'Ci' or (f[0] == 'Ci' and f[3] > 100):
            if f[0] == 'Ci':
                o.append(f'<circle cx="{pad + f[1] * s:.1f}" cy="{pad + f[2] * s:.1f}" r="{f[3] * s:.1f}" fill="#fff" stroke="#777"/>')
            elif b:
                o.append(f'<rect x="{pad + b[0] * s:.1f}" y="{pad + b[1] * s:.1f}" width="{(b[2] - b[0]) * s:.1f}" height="{(b[3] - b[1]) * s:.1f}" fill="#fff" stroke="#777" stroke-width=".6"/>')
    for w in m['windows']:
        if w['o'] == 'h':
            o.append(f'<rect x="{pad + w["x"] * s:.1f}" y="{pad + w["y"] * s:.1f}" width="{w["len"] * s:.1f}" height="{T * s:.1f}" fill="#9fd3ff"/>')
        else:
            o.append(f'<rect x="{pad + w["x"] * s:.1f}" y="{pad + w["y"] * s:.1f}" width="{T * s:.1f}" height="{w["len"] * s:.1f}" fill="#9fd3ff"/>')
    for d in m['doors']:
        th = d['th']
        if d['o'] == 'h':
            o.append(f'<rect x="{pad + d["x"] * s:.1f}" y="{pad + d["y"] * s:.1f}" width="{d["w"] * s:.1f}" height="{th * s:.1f}" fill="{"#c33" if d.get("entry") else "#fff"}"/>')
        else:
            o.append(f'<rect x="{pad + d["x"] * s:.1f}" y="{pad + d["y"] * s:.1f}" width="{th * s:.1f}" height="{d["w"] * s:.1f}" fill="{"#c33" if d.get("entry") else "#fff"}"/>')
        if not d.get('entry'):
            z = swing_zone(d)
            o.append(f'<rect x="{pad + z[0] * s:.1f}" y="{pad + z[1] * s:.1f}" width="{(z[2] - z[0]) * s:.1f}" height="{(z[3] - z[1]) * s:.1f}" fill="none" stroke="#c33" stroke-dasharray="2 2" stroke-width=".5"/>')
    for i, r in enumerate(m['rooms']):
        x, y = m['stampAt'][str(i)]
        a = sum(q[2] * q[3] for q in r['r']) / 1e6
        o.append(f'<text x="{pad + x * s:.1f}" y="{pad + y * s:.1f}" text-anchor="middle">{r["n"]}<tspan x="{pad + x * s:.1f}" dy="10">{a:.1f} m²</tspan></text>')
    o.append('</svg>')
    return '\n'.join(o)


def write_out(vs, rejected, klase, args, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cards = []
    for m in vs:
        p = m['_planner']
        d = os.path.join(out_dir, p['nosaukums'].split(' ')[0] + '_' + p['forma'] + ('_mansards' if p['mansards'] else ''))
        os.makedirs(d, exist_ok=True)
        json.dump(m, open(os.path.join(d, 'model.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        sv = svg(m)
        open(os.path.join(d, 'plans.svg'), 'w', encoding='utf-8').write(sv)
        rows = ''.join(f"<tr><td>{r['n']}</td><td>{r['m2']}</td></tr>" for r in p['telpas'])
        cards.append(f"<div class=c><h3>{p['nosaukums']}</h3>{sv}<table>{rows}<tr><td><b>Apbūve</b></td><td><b>{p['apbuve_m2']}</b></td></tr></table>"
                     f"<p><b>{p.get('loma', '').capitalize()}.</b> {p.get('pamatojums', '')}</p>"
                     f"<p>rules_check: 0 kļūdu, 0 brīdinājumu ({len(p['rules_check']['info'])} info) · vērtējums {p.get('vertejums')}</p></div>")
    html = (f"<!doctype html><meta charset=utf-8><title>Plānojuma varianti</title><style>body{{font-family:Arial;margin:16px}}"
            f".c{{display:inline-block;vertical-align:top;width:520px;margin:8px;border:1px solid #ccc;padding:8px}}svg{{width:100%}}"
            f"table{{font-size:12px}}</style><h2>{args} · klase {klase}</h2>{''.join(cards)}"
            f"<h3>Noraidītie (neizturēja noteikumus)</h3><ul>{''.join(f'<li>{x}</li>' for x in rejected)}</ul>")
    open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8').write(html)
    return out_dir


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(description='MM istabu plānotājs')
    ap.add_argument('garums', type=float); ap.add_argument('platums', type=float); ap.add_argument('augstums', type=float)
    ap.add_argument('gulamistabas', type=int, nargs='?', default=1); ap.add_argument('vannasistabas', type=int, nargs='?', default=1)
    ap.add_argument('--forma', default='II,L,T', help='II, L, T (komatiem)')
    ap.add_argument('--loft', action='store_true', help='arī varianti ar mansarda guļvietu (II formai)')
    ap.add_argument('--n', type=int, default=4, help='max variantu skaits katrai formai')
    ap.add_argument('--griesti', type=int, default=2200)
    ap.add_argument('--out', help='izvades mape (noklusējums planner_izvade/...)')
    a = ap.parse_args()
    for x in planlib.check_input(a.garums, a.platums, a.augstums):
        print('! ievade:', x)
    vs, rej, klase = plan(a.garums, a.platums, a.augstums, a.gulamistabas, a.vannasistabas,
                          [f.strip().upper() for f in a.forma.split(',')], a.loft, a.n, a.griesti)
    tag = f"{a.garums:.0f}x{a.platums:.0f}x{a.augstums:.0f}_{a.gulamistabas}g{a.vannasistabas}v"
    out = a.out or os.path.join(HERE, 'planner_izvade', tag)
    print(f'klase {klase}; derīgi varianti: {len(vs)}')
    for m in vs:
        p = m['_planner']
        print(f"  [{p['loma']}] {p['pamatojums']}")
        print(f"  {p['nosaukums']:45s} apbūve {p['apbuve_m2']:5.1f} m2  " + ', '.join(f"{r['n']} {r['m2']}" for r in p['telpas']))
    for r in rej:
        print('  noraidīts:', r)
    print('izvade:', write_out(vs, rej, klase, tag, out))
